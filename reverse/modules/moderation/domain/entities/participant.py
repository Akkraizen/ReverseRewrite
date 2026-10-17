from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self


class ModerationPermission(StrEnum):
    MODERATE = "moderate"
    MUTE = "mute"
    BAN = "ban"
    KICK = "kick"
    MANAGE_MESSAGES = "manage_messages"


@dataclass(frozen=True, slots=True)
class Participant:
    id: int
    top_role_position: int = 0
    permissions: frozenset[ModerationPermission] = field(default_factory=frozenset)
    is_bot: bool = False

    def is_self(self, participant: Self) -> bool:
        return self.id == participant.id

    def is_guild_owner(self, guild_owner_id: int) -> bool:
        return self.id == guild_owner_id

    def ranks_at_least(self, participant: Self) -> bool:
        return self.top_role_position >= participant.top_role_position

    def has_permissions(self, permissions: ModerationPermission) -> bool:
        return permissions in self.permissions
