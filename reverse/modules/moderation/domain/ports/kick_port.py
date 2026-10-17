from typing import Protocol

from reverse.modules.moderation.domain.entities.participant import Participant


class KickInputPort(Protocol):
    async def kick(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant, reason: str
    ) -> None: ...
