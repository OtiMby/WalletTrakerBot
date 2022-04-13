import requests as r
from discord.ext import commands
import discord
from datetime import datetime
import asyncio
from discord.utils import get


def item_generator(json, key):
    if isinstance(json, dict):
        for k, v in json.items():
            if k == key:
                yield v
            else:
                yield from item_generator(v, key)
    elif isinstance(json, list):
        for item in json:
            yield from item_generator(item, key)


def find(json, key, l=False):
    research = [x for x in item_generator(json, key)]
    if not research:
        return None
    elif l:
        return research
    return research[0]


class MainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.transaction_types = [["Unknown"] * 3, ["Unknown"] * 2, ['createAssociatedAccount', 'Unknown'],
                                  ['Unknown', 'createAssociatedAccount', 'spl-transfer'],
                                  ["createAccount", "Unknown", "createAssociatedAccount", "Unknown", "Unknown"],
                                  ["createAccount", "Unknown", "createAssociatedAccount", "Unknown", "Unknown","Unknown"]]
        self.addresses = {}

    @commands.Cog.listener()
    async def on_ready(self):

        while True:
            for address in self.addresses.copy().keys():
                last_transaction = r.get(
                    f"https://public-api.solscan.io/account/transactions?account={address}&limit=1").json()
                try:
                    if last_transaction[0]['txHash'] != self.addresses[address]['last_shown_transaction'] and \
                            last_transaction[0]['status'] == "Success":
                        last_transaction = last_transaction[0]
                        self.addresses[address]['last_shown_transaction'] = last_transaction['txHash']
                        transaction_type = find(last_transaction, "type", True)
                        print(transaction_type)

                        if transaction_type in self.transaction_types:

                            transaction = r.get(
                                f"https://public-api.solscan.io/transaction/{last_transaction['txHash']}").json()

                            date = datetime.utcfromtimestamp(transaction['blockTime']).strftime('%Y-%m-%d %H:%M:%S')
                            amount = round(find(transaction, "amount") * 10 ** -9, 3)
                            print(transaction_type, amount)

                            token = r.get(
                                f"https://public-api.solscan.io/account/{find(transaction, 'tokenAddress')}").json()
                            name = find(token, "name")
                            image = [i for i in [find(token, 'image'), find(token, 'uri')] if i][0]
                            if "createAccount" in transaction_type:
                                action = "Mint"
                                amount = None

                            else:
                                action = "Buy"
                                buyer = last_transaction["signer"][0]
                                if buyer != address:
                                    action = "Sale"

                        embed = discord.Embed(title=action, colour=0x0036FF)
                        embed.set_footer(text=f"{date} (UTC)")
                        embed.add_field(name='NFT name', value=name, inline=True)
                        if amount:
                            embed.add_field(name='Price', value=f"{amount} SOL", inline=True)
                        embed.set_image(url=image)

                        await self.addresses[address]["channel"].send(embed=embed)
                except:
                    continue

                await asyncio.sleep(.2)
            await asyncio.sleep(1)

    @commands.command(name="add", description="add an address to track")
    async def add(self, ctx, address, name):
        if r.get(f"https://public-api.solscan.io/account/tokens?account={address}").status_code == 200 and address not in self.addresses.keys():
            channel = get(ctx.guild.channels, name=f"{name.lower()}-tracker")
            if channel is None:
                channel = await ctx.guild.create_text_channel(name=f"{name}-tracker",
                                                              category=get(ctx.guild.categories, name="TRACKERS"))

            self.addresses[address] = {'trader_name': name, "last_shown_transaction": None, "channel": channel}
            embed = discord.Embed(title="address added", colour=0x0036FF,
                                  description="The bot will now also track this wallet")
        else:
            embed = discord.Embed(title="Can't add address", colour=0x0036FF,
                                  description="This address doesn't exist")

        return await ctx.channel.send(embed=embed)

    @commands.command(name="show", description="show all tracked addresses")
    async def show(self, ctx):
        embed = discord.Embed(title="Currently tracked wallet",
                              colour=0x0036FF)

        if self.addresses:
            embed.add_field(name='Addresses :', value='\n'.join([address for address in self.addresses.keys()]),
                            inline=True)
            embed.add_field(name='Trader name :',
                            value='\n'.join([self.addresses[address]['trader_name'] for address in self.addresses]),
                            inline=True)

        else:
            embed = discord.Embed(title="Currently tracked wallet", colour=0x0036FF,
                                  description="No wallet is currently tracked !")

        return await ctx.channel.send(embed=embed)

    @commands.command(name="remove", description="delete an address to track")
    async def remove(self, ctx, address):
        del self.addresses[address]

        embed = discord.Embed(title="address deleted",
                              colour=0x0036FF,
                              description="The bot will no longer track this wallet")

        return await ctx.channel.send(embed=embed)

    @commands.command(name="reset", description="clear all tracked address")
    async def reset(self, ctx):
        self.addresses = {}
        for channel in get(ctx.guild.categories, name='TRACKERS').channels:
            await channel.delete()

        embed = discord.Embed(title="All addresses were deleted",
                              colour=0x0036FF,
                              description="The bot will no longer track any wallet")

        return await ctx.channel.send(embed=embed)

    @commands.command(name="test", description="clear all tracked address")
    async def test(self, ctx):
        pass

    @commands.command(name='clear', help='this command will clear msgs')
    async def clear(self, ctx):
        await ctx.channel.purge(limit=1000)


def setup(bot):
    bot.add_cog(MainCog(bot))
