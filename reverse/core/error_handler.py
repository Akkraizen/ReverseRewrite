from discord import Embed
from discord.ext.commands import MissingRequiredArgument, Context, CommandError, BadArgument, \
    MissingPermissions, CommandNotFound, BotMissingPermissions
from loguru import logger

from reverse.config.strings import ErrorStrings
from reverse.structure.singleton import Singleton
from reverse.utils.embeds import build_error_embed

error_strings = ErrorStrings()


class ErrorHandler(Singleton):
    async def handle_error(self, ctx: Context, exception: CommandError):
        description = error_strings.UNEXPECTED
        if isinstance(exception, MissingRequiredArgument): #Отсутсвие требуемых агрументов
            description = error_strings.MISSING_REQUIRED_ARGUMENTS
        elif isinstance(exception, BadArgument): #Плохие вргументы
            description = error_strings.BAD_ARGUMENT
        elif isinstance(exception, MissingPermissions): #Отсутствие требуемых разрешений
            description = error_strings.MISSING_PERMISSIONS
        elif isinstance(exception, KeyError):
            description = error_strings.NOT_FOUND
        elif isinstance(exception, CommandNotFound):
            pass
        elif isinstance(exception, BotMissingPermissions): #Отсутствие требуемых разрешений у бота
            description = error_strings.BOT_MISSING_PERMISSIONS
        else:
            logger.exception(exception)
        embed = build_error_embed(description)

        await ctx.send(embed=embed)
        await ctx.message.add_reaction('❌')