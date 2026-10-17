from pathlib import Path
from typing import override

from arc import GatewayClient, GatewayPlugin

from reverse.application.plugin import Plugin
from reverse.application.translator import Translator
from reverse.modules.general.api.commands import build_plugin
from reverse.modules.general.infrastructure.adapters.discord_latency import DiscordLatencyGatewayAdapter

LOCALES = Path(__file__).parent / "locales"


class GeneralPlugin(Plugin):
    def __init__(self, translator: Translator) -> None:
        self._translator = translator
        self._client: GatewayClient | None = None
        self._plugin: GatewayPlugin | None = None

    @override
    def install(self, client: GatewayClient) -> None:
        if self._client is not None:
            return
        self._plugin = build_plugin(DiscordLatencyGatewayAdapter(client.rest, client.app), self._translator)
        client.add_plugin(self._plugin)
        self._client = client

    @override
    async def close(self) -> None:
        if self._client is not None and self._plugin is not None:
            self._client.remove_plugin(self._plugin)
        self._client = self._plugin = None
