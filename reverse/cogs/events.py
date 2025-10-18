import discord
from discord.ext import commands
from discord.ext.commands.cog import Cog

from reverse.core.reverse_bot import ReverseBot


class Events(Cog):
    def __init__(self, bot: ReverseBot):
        self.bot: ReverseBot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(
            activity=discord.Streaming(
                name=f'<r.help>',
                url='https://www.twitch.tv/rf'
            )
        )

async def setup(bot: ReverseBot):
    await bot.add_cog(Events(bot))