from discord.ext import commands
import discord
import os

token = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!",intents=intents)

bot.load_extension('cogs.maincog')
cog = bot.get_cog('MainCog')
for c in cog.get_commands():
    print(c.name)
print(cog.get_commands())

@bot.event
async def on_ready():
    print(f'{bot.user} id ready !')


@bot.command()
@commands.is_owner()
async def r(ctx):
    bot.reload_extension('cogs.maincog')
    await ctx.channel.send("Cogs reloaded successfully !")

bot.run(token)
