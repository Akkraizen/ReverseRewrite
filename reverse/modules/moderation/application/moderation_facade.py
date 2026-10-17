from collections.abc import Collection
from datetime import datetime, timedelta
from typing import override

from reverse.modules.moderation.domain.entities.ban import Ban
from reverse.modules.moderation.domain.entities.message import MessageFilter
from reverse.modules.moderation.domain.entities.mute import Mute
from reverse.modules.moderation.domain.entities.participant import ModerationPermission, Participant
from reverse.modules.moderation.domain.entities.warn import Warn
from reverse.modules.moderation.domain.ports.ban_port import ActiveBan, BanInputPort, BanOutcome, UnbanOutcome
from reverse.modules.moderation.domain.ports.clear_port import ClearInputPort, ClearOutcome
from reverse.modules.moderation.domain.ports.kick_port import KickInputPort
from reverse.modules.moderation.domain.ports.mute_port import MuteInputPort, MuteOutcome, MuteStatus, UnmuteOutcome
from reverse.modules.moderation.domain.ports.warn_port import WarnInputPort, WarnOutcome


class ModerationFacade(WarnInputPort, BanInputPort, MuteInputPort, KickInputPort, ClearInputPort):
    def __init__(
        self,
        warn_port: WarnInputPort,
        ban_port: BanInputPort,
        mute_port: MuteInputPort,
        kick_port: KickInputPort,
        clear_port: ClearInputPort,
    ) -> None:
        self._warn_port = warn_port
        self._ban_port = ban_port
        self._mute_port = mute_port
        self._kick_port = kick_port
        self._clear_port = clear_port

    @override
    async def add_warn(
        self,
        guild_id: int,
        guild_owner_id: int,
        moderator: Participant,
        target: Participant,
        reason: str,
        until: datetime | None = None,
    ) -> WarnOutcome:
        return await self._warn_port.add_warn(guild_id, guild_owner_id, moderator, target, reason, until)

    @override
    async def remove_warn(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant, warn_id: int
    ) -> Warn | None:
        return await self._warn_port.remove_warn(guild_id, guild_owner_id, moderator, target, warn_id)

    @override
    async def get_warns(self, guild_id: int, user_id: int) -> Collection[Warn]:
        return await self._warn_port.get_warns(guild_id, user_id)

    @override
    async def clear_warns(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant
    ) -> Collection[Warn]:
        return await self._warn_port.clear_warns(guild_id, guild_owner_id, moderator, target)

    @override
    async def ban(
        self,
        guild_id: int,
        guild_owner_id: int,
        moderator: Participant,
        target: Participant,
        reason: str,
        required: ModerationPermission = ModerationPermission.BAN,
    ) -> BanOutcome:
        return await self._ban_port.ban(guild_id, guild_owner_id, moderator, target, reason, required)

    @override
    async def mute(
        self,
        guild_id: int,
        guild_owner_id: int,
        moderator: Participant,
        target: Participant,
        reason: str,
        duration: timedelta,
        required: ModerationPermission = ModerationPermission.MUTE,
    ) -> MuteOutcome:
        return await self._mute_port.mute(guild_id, guild_owner_id, moderator, target, reason, duration, required)

    @override
    async def unban(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant, reason: str
    ) -> UnbanOutcome:
        return await self._ban_port.unban(guild_id, guild_owner_id, moderator, target, reason)

    @override
    async def get_bans(self, guild_id: int, user_id: int | None = None) -> Collection[Ban]:
        return await self._ban_port.get_bans(guild_id, user_id)

    @override
    async def get_active_bans(self, guild_id: int) -> Collection[ActiveBan]:
        return await self._ban_port.get_active_bans(guild_id)

    @override
    async def get_active_ban(self, guild_id: int, user_id: int) -> ActiveBan | None:
        return await self._ban_port.get_active_ban(guild_id, user_id)

    @override
    async def on_banned(self, guild_id: int, user_id: int, moderator_id: int, reason: str | None) -> Ban | None:
        return await self._ban_port.on_banned(guild_id, user_id, moderator_id, reason)

    @override
    async def on_unbanned(self, guild_id: int, user_id: int) -> Collection[Ban]:
        return await self._ban_port.on_unbanned(guild_id, user_id)

    @override
    async def unmute(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant, reason: str
    ) -> UnmuteOutcome:
        return await self._mute_port.unmute(guild_id, guild_owner_id, moderator, target, reason)

    @override
    async def get_mutes(self, guild_id: int, user_id: int) -> Collection[Mute]:
        return await self._mute_port.get_mutes(guild_id, user_id)

    @override
    async def get_mute_status(self, guild_id: int, user_id: int) -> MuteStatus | None:
        return await self._mute_port.get_mute_status(guild_id, user_id)

    @override
    async def on_timed_out(
        self, guild_id: int, user_id: int, moderator_id: int, reason: str | None, until: datetime
    ) -> Mute | None:
        return await self._mute_port.on_timed_out(guild_id, user_id, moderator_id, reason, until)

    @override
    async def on_timeout_lifted(self, guild_id: int, user_id: int) -> Collection[Mute]:
        return await self._mute_port.on_timeout_lifted(guild_id, user_id)

    @override
    async def kick(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant, reason: str
    ) -> None:
        await self._kick_port.kick(guild_id, guild_owner_id, moderator, target, reason)

    @override
    async def clear(
        self,
        guild_owner_id: int,
        channel_id: int,
        moderator: Participant,
        amount: int,
        message_filter: MessageFilter,
    ) -> ClearOutcome:
        return await self._clear_port.clear(guild_owner_id, channel_id, moderator, amount, message_filter)
