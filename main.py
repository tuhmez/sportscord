import discord
from asyncio import run
from dotenv import load_dotenv
from discord.ext import commands
from os import getenv, listdir
from os.path import isfile, join

from utils.print import pretty_print

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
      pretty_print(f'Cog loaded: {cog}', 'SETUP')
    except Exception as error:
      pretty_print(f'Cog {cog} cannot be loaded. [{error}]', 'ERR') 

if __name__ == '__main__':
  pretty_print('Sportscord is getting warmed up! Loading cogs...', 'INIT')
  run(load_cogs())

  bot.run(getenv('INPUT_TOKEN'))
