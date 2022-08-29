import discord
from asyncio import run
from dotenv import load_dotenv
from discord.ext import commands
from os import getenv, listdir
from os.path import isfile, join

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='-', intents=intents)
cogs = [f for f in listdir('./cogs') if isfile(join('./cogs', f))]
for index, item in enumerate(cogs):
  cogs[index] = "cogs." + cogs[index].replace(".py", "")

async def load_cogs():
  for cog in cogs:
    try:
      await bot.load_extension(cog)
    except Exception as error:
      print(f'Cog {cog} cannot be loaded. [{error}]')

if __name__ == '__main__':
  run(load_cogs())

  bot.run(getenv('TOKEN'))
