from discord.ext import commands

class DevCog(commands.Cog, name='Dev', command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='loadcog', brief='Loads a cog.', aliases=['load'])
    @commands.is_owner()
    async def load_cog(self, ctx, cog: str):
        try:
            await self.bot.load_extension('cogs.'+cog)
        except Exception as error:
            await ctx.send(f'Unable to load cog `{cog}`.')
            await ctx.send(f'Error: `{error}`')
        else:
            await ctx.send(f'Loaded cog `{cog}`.')

    @commands.command(name='unloadcog', brief='Unloads a cog.', aliases=['unload'])
    @commands.is_owner()
    async def unload_cog(self, ctx, cog: str):
        try:
            await self.bot.unload_extension('cogs.'+cog)
        except Exception as error:
            await ctx.send(f'Unable to unload cog `{cog}`.')
            await ctx.send(f'Error: `{error}`')
        else:
            await ctx.send(f'Unloaded cog `{cog}`.')

    @commands.command(name='reloadcog', brief='Reloads a cog.', aliases=['reload'])
    @commands.is_owner()
    async def reload_cog(self, ctx, cog: str):
        try:
            await self.bot.reload_extension('cogs.'+cog)
        except Exception as error:
            await ctx.send(f'Unable to reload cog `{cog}`.')
            await ctx.send(f'Error: `{error}`')
        else:
            await ctx.send(f'Reloaded cog `{cog}`.')

    @commands.command(name='logout', brief='Logs the bot out.', aliases=['quit'])
    @commands.is_owner()
    async def logout(self, ctx):
        # self.data["bot"]["login"] = 0
        # await ctx.invoke(self.bot.get_command('export'))
        await ctx.send('zzz...')
        await self.bot.logout()

async def setup(bot):
    await bot.add_cog(DevCog(bot))