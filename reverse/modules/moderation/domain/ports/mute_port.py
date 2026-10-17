from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from reverse.modules.moderation.domain.entities.mute import Mute
from reverse.modules.moderation.domain.entities.participant import ModerationPermission, Participant


@dataclass(frozen=True, slots=True)
class MuteOutcome:
    mute: Mute
    persisted: bool


@dataclass(frozen=True, slots=True)
class UnmuteOutcome:
    revoked: Collection[Mute]
    persisted: bool


@dataclass(frozen=True, slots=True)
class MuteStatus:
    until: datetime
    mute: Mute | None


class MuteInputPort(Protocol):
    async def mute(
        self,
        guild_id: int,
        guild_owner_id: int,
        moderator: Participant,
        target: Participant,
        reason: str,
        duration: timedelta,
        required: ModerationPermission = ModerationPermission.MUTE,
    ) -> MuteOutcome: ...
    async def unmute(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant, reason: str
    ) -> UnmuteOutcome: ...
    async def get_mutes(self, guild_id: int, user_id: int) -> Collection[Mute]: ...
    async def get_mute_status(self, guild_id: int, user_id: int) -> MuteStatus | None: ...

    async def on_timed_out(
        self, guild_id: int, user_id: int, moderator_id: int, reason: str | None, until: datetime
    ) -> Mute | None: ...

    async def on_timeout_lifted(self, guild_id: int, user_id: int) -> Collection[Mute]: ...


class MuteStoragePort(Protocol):
    async def find_all_by_user_id(self, guild_id: int, id: int) -> Collection[Mute]: ...
    async def save(self, mute: Mute) -> Mute: ...
