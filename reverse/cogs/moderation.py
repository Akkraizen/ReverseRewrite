import discord
from discord.ext import commands
from discord.ext.commands import Context, Cog, command

from reverse.config.strings import HelpStrings
from reverse.core.reverse_bot import ReverseBot

strings = HelpStrings()

class Moderation(Cog):
    def __init__(self, bot: ReverseBot):
        self.__bot = bot

    @command(name='mute', help=strings.help_MUTE, description=strings.help_MUTE_long, aliases=[])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(administrator=True)
    async def mute(self, ctx: Context, member: discord.Member, amount: str, *, reason: str = None):
        ...

    @command(name='ban', help=strings.help_BAN, description=strings.help_BAN_long, aliases=[])
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: Context, member: discord.Member, *, reason=None):
       ...

    @command(name='unmute', help=strings.help_UNMUTE, description=strings.help_UNMUTE_long, aliases=[])
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx: Context, member: discord.Member):
        ...

    @command(name='unban', help=strings.help_UNBAN, description=strings.help_UNBAN_long, aliases=[])
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: Context, member: discord.User):
        ...

    @command(name='clear', help=strings.help_CLEAR, description=strings.help_CLEAR_long, aliases=[])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: Context, amount: int, member: discord.Member = None):
        ...

    @command(name='kick', help=strings.help_KICK, description=strings.help_KICK_long, aliases=[])
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: Context, member: discord.Member, reason=None):
        ...

    @command(name='setnick', help=strings.help_SETNICK, description=strings.help_SETNICK_long, aliases=[])
    @commands.has_permissions(manage_nicknames=True)
    async def setnick(self, ctx: Context, member: discord.Member, *, newnick: str):
        ...

    @command(name='role', help=strings.help_MEMBER_ROLE, description=strings.help_MEMBER_ROLE_long, aliases=[])
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx: Context, role: discord.Role, member: discord.Member):
        ...

    @command(name='mutes', help=strings.help_MUTES, description=strings.help_MUTES_long)
    @commands.has_permissions(moderate_members=True)
    async def mutes(self, ctx: Context):
        ...

async def setup(bot: ReverseBot):
    await bot.add_cog(Moderation(bot))