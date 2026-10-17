from arc import GatewayContext
from hikari import Embed, Guild, MessageFlag


async def reply(ctx: GatewayContext, embed: Embed, *, ephemeral: bool = False) -> None:
    await ctx.respond(embed=embed, flags=MessageFlag.EPHEMERAL if ephemeral else MessageFlag.NONE)


async def guild_of(ctx: GatewayContext) -> tuple[int, Guild]:
    assert ctx.guild_id is not None and ctx.member is not None
    return int(ctx.guild_id), ctx.get_guild() or await ctx.client.rest.fetch_guild(ctx.guild_id)
