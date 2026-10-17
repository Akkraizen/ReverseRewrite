from typing import override

from reverse.modules.moderation.application.services.clock import Clock, utc_now
from reverse.modules.moderation.domain.entities.message import MessageFilter
from reverse.modules.moderation.domain.entities.participant import ModerationPermission, Participant
from reverse.modules.moderation.domain.policies.clear_policy import (
    MAX_MESSAGE_AGE,
    SCAN_LIMIT,
    ensure_valid_clear_amount,
)
from reverse.modules.moderation.domain.policies.moderation_policy import ensure_has_permission
from reverse.modules.moderation.domain.ports.clear_port import ClearInputPort, ClearOutcome
from reverse.modules.moderation.domain.ports.moderation_gateway import ModerationGateway


class ClearService(ClearInputPort):
    def __init__(self, gateway: ModerationGateway, clock: Clock = utc_now) -> None:
        self._gateway = gateway
        self._clock = clock

    @override
    async def clear(
        self,
        guild_owner_id: int,
        channel_id: int,
        moderator: Participant,
        amount: int,
        message_filter: MessageFilter,
    ) -> ClearOutcome:
        ensure_has_permission(guild_owner_id, moderator, ModerationPermission.MANAGE_MESSAGES)
        ensure_valid_clear_amount(amount)
        oldest_allowed = self._clock() - MAX_MESSAGE_AGE
        found: list[int] = []
        reached_old = False
        scanned = 0
        async for message in self._gateway.iter_messages(channel_id):
            if message.created_at < oldest_allowed:
                reached_old = True
                break
            if message_filter.matches(message):
                found.append(message.id)
                if len(found) == amount:
                    break
            scanned += 1
            if scanned >= SCAN_LIMIT:
                break
        if found:
            await self._gateway.delete_messages(channel_id, found, f"/clear: модератор {moderator.id}")
        return ClearOutcome(deleted=len(found), reached_old=reached_old)
