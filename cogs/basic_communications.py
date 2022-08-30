from discord.ext import commands

from utils.print import pretty_print

class BasicCommunication(commands.Cog, name='Events'):
  def __init__(self, bot):
    self.bot = bot
  
  @commands.Cog.listener()
  async def on_ready(self):
    self.bot.owner = (await self.bot.application_info()).owner
    pretty_print('Sportscord is coming off the bench!', 'GO')

  @commands.Cog.listener()
  async def on_message(self, message):
    if message.author == self.bot.user: return

async def setup(bot):
  await bot.add_cog(BasicCommunication(bot))