from discord.ext import commands
import discord
import os

token = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!",intents=intents)

bot.load_extension('cogs.maincog')
cog = bot.get_cog('MainCog')

@bot.event
async def on_ready():
    print(f'{bot.user} id ready !')


bot.run(token)
