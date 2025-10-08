import discord
from discord.ext import commands
from discord.ext.commands.cog import Cog

from reverse.core.ReverseBot import ReverseBot


class Events(Cog):
    def __init__(self, bot: ReverseBot):
        self.bot: ReverseBot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence( #Установление активности
            activity=discord.Streaming( #стрим
                name=f'<r.help>', #имя стрима
                url='https://www.twitch.tv/rf'#ссылка на стрим
            )
        )

async def setup(bot: ReverseBot):
    await bot.add_cog(Events(bot))