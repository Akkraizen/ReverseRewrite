from typing import Union

from discord import Embed
from discord.ext.commands import Context

def __get_audit_channel_id(ctx: Context) -> int:
    # TODO: Implement this
    ...

def send_message(ctx: Context, message: Union[str, Embed]) -> None:
    channel = ctx.guild.get_channel(__get_audit_channel_id(ctx))

    if channel is None:
        return

    if isinstance(message, str):
        channel.send(message)
    else:
        channel.send(embed=message)