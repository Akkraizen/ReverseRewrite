from collections.abc import Collection
from dataclasses import dataclass
from typing import Protocol

from reverse.modules.moderation.domain.entities.ban import Ban
from reverse.modules.moderation.domain.entities.participant import ModerationPermission, Participant


@dataclass(frozen=True, slots=True)
class BanOutcome:
    ban: Ban
    persisted: bool


@dataclass(frozen=True, slots=True)
class UnbanOutcome:
    revoked: Collection[Ban]
    persisted: bool
    was_banned: bool = True


@dataclass(frozen=True, slots=True)
class ActiveBan:
    user_id: int
    reason: str | None
    ban: Ban | None


class BanInputPort(Protocol):
    async def ban(
        self,
        guild_id: int,
        guild_owner_id: int,
        moderator: Participant,
        target: Participant,
        reason: str,
        required: ModerationPermission = ModerationPermission.BAN,
    ) -> BanOutcome: ...
    async def unban(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant, reason: str
    ) -> UnbanOutcome: ...
    async def get_bans(self, guild_id: int, user_id: int | None = None) -> Collection[Ban]: ...

    async def get_active_bans(self, guild_id: int) -> Collection[ActiveBan]: ...

    async def get_active_ban(self, guild_id: int, user_id: int) -> ActiveBan | None: ...

    async def on_banned(self, guild_id: int, user_id: int, moderator_id: int, reason: str | None) -> Ban | None: ...

    async def on_unbanned(self, guild_id: int, user_id: int) -> Collection[Ban]: ...


class BanStoragePort(Protocol):
    async def find_all_by_guild_id(self, guild_id: int) -> Collection[Ban]: ...
    async def find_active_by_guild_id(self, guild_id: int) -> Collection[Ban]: ...

    async def find_all_by_user_id(self, guild_id: int, id: int) -> Collection[Ban]: ...
    async def save(self, ban: Ban) -> Ban: ...
    async def save_all(self, bans: Collection[Ban]) -> Collection[Ban]: ...
