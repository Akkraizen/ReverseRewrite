from collections.abc import Collection
from datetime import datetime, timedelta
from typing import override

from loguru import logger

from reverse.modules.moderation.application.services.clock import Clock, utc_now
from reverse.modules.moderation.domain.entities.mute import Mute
from reverse.modules.moderation.domain.entities.participant import ModerationPermission, Participant
from reverse.modules.moderation.domain.entities.validation import external_reason, normalize_reason
from reverse.modules.moderation.domain.policies.moderation_policy import ensure_can_moderate
from reverse.modules.moderation.domain.policies.mute_policy import ensure_valid_mute_duration
from reverse.modules.moderation.domain.ports.moderation_gateway import ModerationGateway
from reverse.modules.moderation.domain.ports.mute_port import (
    MuteInputPort,
    MuteOutcome,
    MuteStatus,
    MuteStoragePort,
    UnmuteOutcome,
)


class MuteService(MuteInputPort):
    def __init__(self, storage: MuteStoragePort, gateway: ModerationGateway, clock: Clock = utc_now) -> None:
        self._storage = storage
        self._gateway = gateway
        self._clock = clock

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
        ensure_can_moderate(guild_owner_id, moderator, target, required)
        ensure_valid_mute_duration(duration)
        now = self._clock()
        mute = Mute(
            guild_id=guild_id,
            target_id=target.id,
            moderator_id=moderator.id,
            reason=reason,
            created_at=now,
            expires_at=now + duration,
        )
        await self._gateway.timeout(guild_id, target.id, mute.expires_at, mute.reason)
        try:
            return MuteOutcome(mute=await self._storage.save(mute), persisted=True)
        except Exception:
            logger.exception("Mute of {} in guild {} applied but not saved", target.id, guild_id)
            return MuteOutcome(mute=mute, persisted=False)

    @override
    async def unmute(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant, reason: str
    ) -> UnmuteOutcome:
        ensure_can_moderate(guild_owner_id, moderator, target, ModerationPermission.MUTE)
        await self._gateway.remove_timeout(guild_id, target.id, normalize_reason(reason))
        now = self._clock()
        try:
            active = await self._active_records(guild_id, target.id, now)
        except Exception:
            logger.exception("Unmute of {} in guild {} applied but not saved", target.id, guild_id)
            return UnmuteOutcome(revoked=[], persisted=False)
        revoked, persisted = await self._revoke(active, now)
        return UnmuteOutcome(revoked=revoked, persisted=persisted)

    @override
    async def get_mutes(self, guild_id: int, user_id: int) -> Collection[Mute]:
        return await self._storage.find_all_by_user_id(guild_id, user_id)

    @override
    async def get_mute_status(self, guild_id: int, user_id: int) -> MuteStatus | None:
        until = await self._gateway.fetch_timeout(guild_id, user_id)
        now = self._clock()
        active = await self._active_records(guild_id, user_id, now)
        if until is None or until <= now:
            await self._revoke(active, now)
            return None
        return MuteStatus(until=until, mute=max(active, key=lambda m: m.expires_at, default=None))

    async def _active_records(self, guild_id: int, user_id: int, now: datetime) -> list[Mute]:
        return [mute for mute in await self._storage.find_all_by_user_id(guild_id, user_id) if mute.is_active(now)]

    async def _revoke(self, mutes: Collection[Mute], now: datetime) -> tuple[list[Mute], bool]:
        revoked: list[Mute] = []
        try:
            for mute in mutes:
                revoked.append(await self._storage.save(mute.revoke(now)))
        except Exception:
            logger.exception("Could not revoke mute records {}", [mute.id for mute in mutes])
            return revoked, False
        return revoked, True

    @override
    async def on_timed_out(
        self, guild_id: int, user_id: int, moderator_id: int, reason: str | None, until: datetime
    ) -> Mute | None:
        now = self._clock()
        active = await self._active_records(guild_id, user_id, now)
        if until <= now or any(mute.expires_at == until for mute in active):
            return None
        await self._revoke(active, now)
        mute = Mute(
            guild_id=guild_id,
            target_id=user_id,
            moderator_id=moderator_id,
            reason=external_reason(reason),
            created_at=now,
            expires_at=until,
        )
        return await self._storage.save(mute)

    @override
    async def on_timeout_lifted(self, guild_id: int, user_id: int) -> Collection[Mute]:
        now = self._clock()
        revoked, _ = await self._revoke(await self._active_records(guild_id, user_id, now), now)
        return revoked
