from typing import override

from reverse.modules.moderation.domain.entities.participant import ModerationPermission, Participant
from reverse.modules.moderation.domain.entities.validation import normalize_reason
from reverse.modules.moderation.domain.policies.moderation_policy import ensure_can_moderate
from reverse.modules.moderation.domain.ports.kick_port import KickInputPort
from reverse.modules.moderation.domain.ports.moderation_gateway import ModerationGateway


class KickService(KickInputPort):
    def __init__(self, gateway: ModerationGateway) -> None:
        self._gateway = gateway

    @override
    async def kick(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant, reason: str
    ) -> None:
        ensure_can_moderate(guild_owner_id, moderator, target, ModerationPermission.KICK)
        await self._gateway.kick(guild_id, target.id, normalize_reason(reason))
