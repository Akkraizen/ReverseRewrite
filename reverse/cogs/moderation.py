import discord
from discord import HTTPException, Embed, Forbidden
from discord.ext import commands
from discord.ext.commands import Context, Cog, command
from datetime import datetime, timedelta

from reverse.config.colors import Colors
from reverse.config.strings import HelpStrings
from reverse.core.reverse_bot import ReverseBot
from reverse.utils.converter import TimeConverter
from reverse.utils.embeds import build_until_ready_embed

strings = HelpStrings()

class Moderation(Cog):
    def __init__(self, bot: ReverseBot):
        self.__bot = bot
        self.__config = bot.config
        self.__colors = Colors()

    @command(name='mute', help=strings.help_MUTE, description=strings.help_MUTE_long, aliases=[])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(administrator=True)
    async def mute(self, ctx: Context, member: discord.Member, amount: str, *, reason: str = None):
        bot = ctx.guild.get_member(self.__bot.user.id)
        times_start = datetime.today()
        if member == ctx.message.author:
            await ctx.send(f'{ctx.message.author.mention}, удачи Тебе в этом деле...')
            await ctx.message.add_reaction('❌')
            return None
        elif member == self.__bot.user:
            await ctx.send(f'{ctx.message.author.mention}, не пытайся... Иначе я сам тебя замучу')
            await ctx.message.add_reaction('❌')
            return None
        elif member.id in self.__config.developers:
            await ctx.send(f'{ctx.message.author.mention}, не советую этого делать...')
            await ctx.message.add_reaction('❌')
            return None
        elif member.timed_out_until:
            await ctx.send(f'{ctx.message.author.mention} Этот пользователь уже замучен!')
            await ctx.message.add_reaction('❌')
            return None
        elif ctx.author.top_role < member.top_role:
            await ctx.send(f'{ctx.message.author.mention}, Вы не можете замутить того, кто выше вас по роли!')
            await ctx.message.add_reaction('❌')
            return None
        elif member.guild_permissions.administrator:
            await ctx.send(f'{ctx.message.author.mention}, Вы не можете замутить Администратора!')
            await ctx.message.add_reaction('❌')
            return None
        elif bot.top_role.position <= member.top_role.position:
            await ctx.send(f'{ctx.message.author.mention}, Я не могу замутить того, кто выше меня или равен мне по роли!')
            await ctx.message.add_reaction('❌')
            return None

        emb = Embed(title=f'**System — Mute**', color=self.__colors.red)
        emb.add_field(name='Ответственный модератор:', value=ctx.author.mention, inline=False)
        emb.add_field(name='Нарушитель:', value=member.mention, inline=False)
        emb.set_footer(text=f'{ctx.guild} | {times_start.strftime("%Y.%m.%d, %H:%M")}')

        time = await TimeConverter().convert(context=ctx, argument=amount)
        if time <= 60:
            emb.add_field(name='Длительность:', value='{}с'.format(time))
        elif time <= 3600:
            time2 = round(time / 60)
            emb.add_field(name='Длительность:', value='{}м'.format(time2))
        elif time <= 86400:
            time2 = round(time / 3600)
            emb.add_field(name='Длительность:', value='{}ч'.format(time2))
        elif time >= 86400:
            time2 = round(time / 86400)
            emb.add_field(name='Длительность:', value='{}д'.format(time2))
        if reason is None:
            emb.add_field(name='Причина:', value='Не указано', inline=False)
        else:
            emb.add_field(name='Причина:', value=reason, inline=False)
        await member.timeout(timedelta(seconds=time), reason=reason)
        await ctx.message.add_reaction('✅')
        await ctx.send(embed=emb)
        # TODO: Add audit logs
        # channel = ctx.message.guild.get_channel(data[str(ctx.guild.id)]['audit_channel_punish'])
        #if channel is None:
        #    return
        #await channel.send(embed=emb)
        return None

    @command(name='ban', help=strings.help_BAN, description=strings.help_BAN_long, aliases=[])
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: Context, member: discord.Member, *, reason=None):
        bot = ctx.guild.get_member(self.__bot.user.id)
        times_start = datetime.today()
        if member == ctx.message.author:
            await ctx.send(f'{ctx.message.author.mention}, удачи Тебе в этом деле...')
            await ctx.message.add_reaction('❌')
            return None
        elif member == self.__bot.user:
            await ctx.send(f'{ctx.message.author.mention}, не пытайся... Иначе я сам тебя забаню')
            await ctx.message.add_reaction('❌')
            return None
        elif member.id in self.__config.developers:
            await ctx.send(f'{ctx.message.author.mention}, не советую этого делать...')
            await ctx.message.add_reaction('❌')
            return None
        elif ctx.author.top_role.position < member.top_role.position:
            await ctx.send(f'{ctx.message.author.mention}, Вы не можете замутить того, кто выше Вас по роли!')
            await ctx.message.add_reaction('❌')
            return None
        elif bot.top_role.position <= member.top_role.position:
            await ctx.send(f'{ctx.message.author.mention}, Я не могу забанить того, кто выше меня или равен мне по роли!')
            await ctx.message.add_reaction('❌')
            return None
        # elif mute_role in member.roles:
        #    await ctx.send(f'{ctx.message.author.mention} Этот пользователь уже замучен!')
        #    await ctx.message.add_reaction('❌')
        bans = ctx.guild.bans()
        if member not in bans:
            await ctx.send(f'{ctx.message.author.mention}, Этот пользователь уже забанен...')
            await ctx.message.add_reaction('❌')
            return None
        emb_user = discord.Embed(title='**System — Ban**', color=self.__colors.red)
        emb_user.add_field(name='**Ответственный модератор:**', value=ctx.author.mention, inline=False)
        emb_user.add_field(name='**Причина:**', value=reason, inline=False)
        emb_user.set_footer(text=f'{ctx.guild} | {times_start.strftime("%Y.%m.%d, %H:%M")}')

        emb = discord.Embed(title=f'**System — Ban**', color=self.__colors.red)
        emb.add_field(name='Ответственный модератор:', value=ctx.author.mention, inline=False)
        emb.add_field(name='Нарушитель:', value=member.mention, inline=False)
        emb.set_footer(text=f'{ctx.guild} | {times_start.strftime("%Y.%m.%d, %H:%M")}')
        if reason is None:
            emb.add_field(name='Причина:', value='Не указано', inline=False)
        else:
            emb.add_field(name='Причина:', value=f'{reason}', inline=False)
        await ctx.guild.ban(user=member, reason=reason, delete_message_days=7)
        await ctx.message.add_reaction('✅')
        await ctx.send(embed=emb)
        # TODO: Add audit logs
        # channel = ctx.message.guild.get_channel(data[str(ctx.guild.id)]['audit_channel_punish'])
        # if channel is None:
        #     pass
        # elif channel is not None:
        #     await channel.send(embed=emb)
        try:
            await member.send(embed=emb_user)
        except HTTPException:
            pass
        return None

    @command(name='unmute', help=strings.help_UNMUTE, description=strings.help_UNMUTE_long, aliases=[])
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx: Context, member: discord.Member):
        times_start = datetime.datetime.today()
        bot = ctx.guild.get_member(self.__bot.user.id)
        if bot.top_role.position <= member.top_role.position:
            await ctx.send(f'{ctx.message.author.mention}, Я не могу размутить того, кто выше меня или равен мне по роли!')
            await ctx.message.add_reaction('❌')
            return None
        if not member.timed_out_until:
            await ctx.send(f'{ctx.message.author.mention}, этот пользователь не замучен!')
            await ctx.message.add_reaction('❌')
            return None
        embed = discord.Embed(
            title='**System - unmute**',
            description=f' Пользователь-{member.mention} размучен',
            color=self.__colors.red
        )
        embed.add_field(
            name='Ответственный модератор:',
            value=ctx.author.mention,
            inline=False
        )
        embed.set_footer(text=f'{ctx.guild} | {times_start.strftime("%Y.%m.%d, %H:%M")}')
        await member.timeout(None)
        await ctx.send(embed=embed)
        await ctx.message.add_reaction('✅')
        # TODO: Add audit logs
        # channel = ctx.message.guild.get_channel(data[str(ctx.guild.id)]['audit_channel_punish'])
        # if channel is None:
        #     pass
        # elif channel is not None:
        #     await channel.send(embed=embed)
        return None


    @command(name='unban', help=strings.help_UNBAN, description=strings.help_UNBAN_long, aliases=[])
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: Context, member: discord.User):
        times_start = datetime.today()
        bans = ctx.guild.bans()
        if member in bans:
            await ctx.send(f'{ctx.message.author.mention}, этот пользователь не забанен!')
            await ctx.message.add_reaction('❌')
            return None
        embed = discord.Embed(
            title='**System - Unban**',
            description=f' Пользователь-{member.mention} разбанен',
            color=self.__colors.red
        )
        embed.add_field(
            name='Ответственный модератор:',
            value=ctx.author.mention,
            inline=False
        )
        embed.set_footer(text=f'{ctx.guild} | {times_start.strftime("%Y.%m.%d, %H:%M")}')
        await ctx.guild.unban(user=member, reason=None)
        await ctx.send(embed=embed)
        await ctx.message.add_reaction('✅')
        # TODO: add audit logs
        # if channel is None:
        #     return
        # await channel.send(embed=embed)
        return None


    @command(name='clear', help=strings.help_CLEAR, description=strings.help_CLEAR_long, aliases=[])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: Context, amount: int, member: discord.Member = None):
        clr_embed_1 = discord.Embed(
            title='Очистка сообщений...',
            description=f'[▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬] 0%',
            color=self.__colors.red
        )
        clr_embed_2 = discord.Embed(
            title='Очистка проведена успешно!',
            description=f'[[▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬](https://example.com/ "")] 100%\nБыло удалено {amount} сообщений',
            color=self.__colors.red
        )
        # if amount is None:
        #    await ctx.message.add_reaction('✅')
        #    await ctx.channel.purge()
        #    if channel is None:
        #        pass
        #    elif channel is not None:
        #        await channel.send(embed=clr_embed_2)
        # else:
        if member is None:
            clr_msg = await ctx.send(embed=clr_embed_1)
            await ctx.message.add_reaction('✅')
            await ctx.channel.purge(limit=amount, check=lambda m: m.author != self.__bot.user)
            await clr_msg.edit(embed=clr_embed_2)
            return None
        clr_embed_1.add_field(name='Участник:', value=member.mention, inline=False)
        clr_embed_2.add_field(name='Участник:', value=member.mention, inline=False)
        await ctx.message.add_reaction('✅')
        await ctx.channel.purge(limit=amount, check=lambda m: m.author == member)
        await ctx.send(embed=clr_embed_2)
        # TODO: Add audit logs
        #channel = ctx.message.guild.get_channel(data[str(ctx.guild.id)]['audit_channel_punish'])
        #if channel is None:
        #    pass
        #elif channel is not None:
        #    await channel.send(embed=clr_embed_2)
        return None

    @command(name='kick', help=strings.help_KICK, description=strings.help_KICK_long, aliases=[])
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: Context, member: discord.Member, reason=None):
        if ctx.author.top_role < member.top_role:
            await ctx.send(f'{ctx.message.author.mention}, Вы не можете кикнуть того, кто выше вас по роли!')
            await ctx.message.add_reaction('❌')
            return None
        elif member.id in self.__config.developers:
            await ctx.send(f'{ctx.message.author.mention}, не советую этого делать...')
            await ctx.message.add_reaction('❌')
            return None
        elif member is ctx.author:
            await ctx.send(f'{ctx.message.author.mention}, удачи Тебе в этом деле...')
            await ctx.message.add_reaction('❌')
        elif member == self.__bot.user:
            await ctx.send(f'{ctx.message.author.mention}, Я тебя щас сам кикну')
            await ctx.message.add_reaction('❌')
        emb_user = discord.Embed(title='**System - Kick**', color=self.__colors.red)
        emb_user.add_field(name='**Ответственный модератор:**', value=ctx.author.mention, inline=False)
        emb_user.add_field(name='**Причина:**', value=reason, inline=False)
        emb_user.set_footer(text=f'{ctx.guild} | {datetime.today().strftime("%Y.%m.%d, %H:%M")}')
        emb = discord.Embed(
            title='**System - Kick**',
            description=f'Пользователь {member.mention} был кикнут!',
            color=self.__colors.red
        )
        emb.add_field(
            name='Ответственный модератор:',
            value=f'{ctx.author.mention}',
            inline=False
        )
        if reason is None:
            emb.add_field(
                name='Причина:',
                value='Отсутсвует',
                inline=False
            )
        else:
            emb.add_field(
                name='Причина:',
                value=f'{reason}',
                inline=False
            )
        await member.kick(reason=reason)
        await ctx.send(embed=emb)
        await ctx.message.add_reaction('✅')
        # TODO: Add audit logs
        #channel = ctx.message.guild.get_channel(data[str(ctx.guild.id)]['audit_channel_punish'])
        #if channel is None:
        #    pass
        #elif channel is not None:
        #    await channel.send(embed=emb)
        try:
            await member.send(embed=emb_user)
        except Forbidden:
            pass
        return None

    @command(name='setnick', help=strings.help_SETNICK, description=strings.help_SETNICK_long, aliases=[])
    @commands.has_permissions(manage_nicknames=True)
    async def setnick(self, ctx: Context, member: discord.Member, *, newnick: str):
        bot = ctx.guild.get_member(self.__bot.user.id)

        if ctx.author.top_role.position <= member.top_role.position:
            await ctx.send(
                f'{ctx.message.author.mention}, Я не могу изменить ник того, кто выше вас или равен вам по роли!')
            return await ctx.message.add_reaction('❌')
        if bot.top_role.position <= member.top_role.position:
            await ctx.send(
                f'{ctx.message.author.mention}, Я не могу изменить ник того, кто выше вас или равен вам по роли!')
            return await ctx.message.add_reaction('❌')
        await member.edit(nick = newnick)
        await ctx.send(f'Имя участника {member.mention} успешно изменен на `{newnick}`')
        return None

    @command(name='role', help=strings.help_MEMBER_ROLE, description=strings.help_MEMBER_ROLE_long, aliases=[])
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx: Context, role: discord.Role, member: discord.Member):
        if role.position >= ctx.author.top_role.position:
            await ctx.message.add_reaction('❌')
            await ctx.send('Вы не можете выдать роль выше вашей')
            return None
        if role not in member.roles:
            await member.add_roles(role)
            await ctx.message.add_reaction('✅')
            await ctx.send(f'Участнику {member.mention} была добавлена роль `{role.name}`')
            return None
        await member.remove_roles(role)
        await ctx.message.add_reaction('✅')
        await ctx.send(f'У участника {member.mention} была убрана роль `{role.name}`')
        return None

    @command(name='mutes', help=strings.help_MUTES, description=strings.help_MUTES_long)
    @commands.has_permissions(moderate_members=True)
    async def mutes(self, ctx: Context):
        pages = [{}]
        embed = build_until_ready_embed()
        mute_message = await ctx.send(embed=embed)
        mutes = ''
        pos = 0
        for member in ctx.guild.members:
            if member.timed_out_until:
                if len(list(pages[-1])) >= 10:
                    pages.append({})
                mutes += f'{pos} - {member.mention}\n'
                pos += 1
        if not pos:
            mutes += 'Отсутствуют'
        mute_embed = discord.Embed(
            title=f'Муты {ctx.guild.name}',
            description=f'{mutes}',
            color=self.__colors.red
        )
        mute_embed.set_footer(text=f'{ctx.guild} | {datetime.today().strftime("%Y.%m.%d, %H:%M")}')
        await mute_message.edit(embed=mute_embed)

async def setup(bot: ReverseBot):
    await bot.add_cog(Moderation(bot))