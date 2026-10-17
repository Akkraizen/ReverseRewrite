from pathlib import Path
from typing import override

from arc import GatewayClient, GatewayPlugin
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reverse.application.plugin import Plugin
from reverse.application.translator import Translator
from reverse.modules.moderation.api.commands import build_plugin
from reverse.modules.moderation.application.moderation_facade import ModerationFacade
from reverse.modules.moderation.application.services.ban_service import BanService
from reverse.modules.moderation.application.services.clear_service import ClearService
from reverse.modules.moderation.application.services.kick_service import KickService
from reverse.modules.moderation.application.services.mute_service import MuteService
from reverse.modules.moderation.application.services.warn_service import WarnService
from reverse.modules.moderation.infrastructure.adapters.ban_storage import BanStorageAdapter
from reverse.modules.moderation.infrastructure.adapters.discord_gateway import DiscordModerationGateway
from reverse.modules.moderation.infrastructure.adapters.mute_storage import MuteStorageAdapter
from reverse.modules.moderation.infrastructure.adapters.warn_storage import WarnStorageAdapter
from reverse.modules.moderation.infrastructure.repository.ban_repository import BanRepository
from reverse.modules.moderation.infrastructure.repository.mute_repository import MuteRepository
from reverse.modules.moderation.infrastructure.repository.warn_repository import WarnRepository

LOCALES = Path(__file__).parent / "locales"


def _own_user_id(client: GatewayClient) -> int | None:
    me = client.app.get_me()
    return int(me.id) if me is not None else None


class ModerationPlugin(Plugin):
    _gateway: DiscordModerationGateway

    def __init__(self, sessions: async_sessionmaker[AsyncSession], translator: Translator) -> None:
        self._sessions = sessions
        self._translator = translator
        self._client: GatewayClient | None = None
        self._plugin: GatewayPlugin | None = None

    @override
    def install(self, client: GatewayClient) -> None:
        if self._client is not None:
            return

        self._gateway = DiscordModerationGateway(client.rest)
        bans = self._build_bans()
        mutes = self._build_mutes()
        warns = self._build_warns(mutes)
        facade = self._build_facade(
            bans=bans, mutes=mutes, warns=warns, kicks=KickService(self._gateway), clears=ClearService(self._gateway)
        )

        self._plugin = build_plugin(facade, self._translator, lambda: _own_user_id(client))
        if self._plugin is not None:
            client.add_plugin(self._plugin)
        self._client = client

    @override
    async def close(self) -> None:
        if self._client is not None and self._plugin is not None:
            self._client.remove_plugin(self._plugin)
        self._client = self._plugin = None

    def _build_bans(self) -> BanService:
        return BanService(storage=BanStorageAdapter(BanRepository(self._sessions)), gateway=self._gateway)

    def _build_mutes(self) -> MuteService:
        return MuteService(storage=MuteStorageAdapter(MuteRepository(self._sessions)), gateway=self._gateway)

    def _build_warns(self, mutes: MuteService) -> WarnService:
        return WarnService(storage=WarnStorageAdapter(WarnRepository(self._sessions)), mutes_port=mutes)

    def _build_facade(
        self, bans: BanService, mutes: MuteService, warns: WarnService, kicks: KickService, clears: ClearService
    ) -> ModerationFacade:
        return ModerationFacade(warn_port=warns, ban_port=bans, mute_port=mutes, kick_port=kicks, clear_port=clears)
