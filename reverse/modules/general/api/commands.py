from datetime import timedelta

from arc import GatewayContext, GatewayPlugin, slash_command
from hikari import Embed

from reverse.application.translator import Translation, Translator
from reverse.infrastructure.discord.utils.embeds import build_embed
from reverse.infrastructure.discord.utils.interactions import reply
from reverse.modules.general.domain.ports.latency_port import LatencyGatewayPort


def _milliseconds(t: Translation, latency: timedelta | None) -> str:
    if latency is None:
        return t("ping.unknown")
    return t("ping.milliseconds", value=round(latency / timedelta(milliseconds=1)))


def describe_ping(t: Translation, rest: timedelta, gateway: timedelta | None) -> Embed:
    embed = build_embed(t("ping.title"))
    embed.add_field(t("ping.rest"), _milliseconds(t, rest), inline=True)
    embed.add_field(t("ping.gateway"), _milliseconds(t, gateway), inline=True)
    return embed


def build_plugin(latency: LatencyGatewayPort, translator: Translator) -> GatewayPlugin:
    plugin = GatewayPlugin("general")
    d = translator.bind(translator.default_locale)

    @plugin.include
    @slash_command("ping", d("commands.ping.description"))
    async def ping(ctx: GatewayContext) -> None:
        rest = await latency.rest_latency()
        embed = describe_ping(translator.bind(str(ctx.locale)), rest, latency.gateway_latency())
        await reply(ctx, embed)

    return plugin
