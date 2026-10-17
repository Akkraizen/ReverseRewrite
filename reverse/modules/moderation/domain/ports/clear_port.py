from dataclasses import dataclass
from typing import Protocol

from reverse.modules.moderation.domain.entities.message import MessageFilter
from reverse.modules.moderation.domain.entities.participant import Participant


@dataclass(frozen=True, slots=True)
class ClearOutcome:
    deleted: int
    reached_old: bool


class ClearInputPort(Protocol):
    async def clear(
        self,
        guild_owner_id: int,
        channel_id: int,
        moderator: Participant,
        amount: int,
        message_filter: MessageFilter,
    ) -> ClearOutcome: ...
