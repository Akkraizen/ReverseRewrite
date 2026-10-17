from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from reverse.modules.moderation.domain.entities.participant import Participant
from reverse.modules.moderation.domain.entities.warn import Warn
from reverse.modules.moderation.domain.ports.mute_port import MuteOutcome


@dataclass(frozen=True, slots=True)
class WarnOutcome:
    warn: Warn
    active_warns: int
    limit: int
    limit_reached: bool
    mute: MuteOutcome | None = None
    mute_error: Exception | None = None
    persisted: bool = True


class WarnInputPort(Protocol):
    async def add_warn(
        self,
        guild_id: int,
        guild_owner_id: int,
        moderator: Participant,
        target: Participant,
        reason: str,
        until: datetime | None = None,
    ) -> WarnOutcome: ...
    async def remove_warn(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant, warn_id: int
    ) -> Warn | None: ...
    async def get_warns(self, guild_id: int, user_id: int) -> Collection[Warn]: ...
    async def clear_warns(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant
    ) -> Collection[Warn]: ...


class WarnStoragePort(Protocol):
    async def find_by_id(self, guild_id: int, id: int) -> Warn | None: ...
    async def find_all_by_user_id(self, guild_id: int, id: int) -> Collection[Warn]: ...
    async def save(self, warn: Warn) -> Warn: ...
