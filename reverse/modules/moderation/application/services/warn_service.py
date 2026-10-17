from asyncio import Lock
from collections.abc import Collection
from datetime import datetime
from typing import override
from weakref import WeakValueDictionary

from loguru import logger

from reverse.modules.moderation.application.services.clock import Clock, utc_now
from reverse.modules.moderation.domain.entities.participant import ModerationPermission, Participant
from reverse.modules.moderation.domain.entities.warn import Warn
from reverse.modules.moderation.domain.policies.moderation_policy import ensure_can_moderate
from reverse.modules.moderation.domain.policies.warn_policy import WarnPolicy
from reverse.modules.moderation.domain.ports.moderation_gateway import ModerationActionForbidden
from reverse.modules.moderation.domain.ports.mute_port import MuteInputPort, MuteOutcome
from reverse.modules.moderation.domain.ports.warn_port import WarnInputPort, WarnOutcome, WarnStoragePort

__all__ = ["WarnOutcome", "WarnService"]


class WarnService(WarnInputPort):
    def __init__(
        self,
        storage: WarnStoragePort,
        mutes_port: MuteInputPort,
        policy: WarnPolicy | None = None,
        clock: Clock = utc_now,
    ) -> None:
        self._storage = storage
        self._mutes_port = mutes_port
        self._policy = policy or WarnPolicy()
        self._clock = clock
        self._locks: WeakValueDictionary[tuple[int, int], Lock] = WeakValueDictionary()

    def _lock(self, guild_id: int, target_id: int) -> Lock:
        lock = self._locks.get((guild_id, target_id))
        if lock is None:
            lock = Lock()
            self._locks[guild_id, target_id] = lock
        return lock

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
        ensure_can_moderate(guild_owner_id, moderator, target, ModerationPermission.MODERATE)
        async with self._lock(guild_id, target.id):
            return await self._add_warn(guild_id, guild_owner_id, moderator, target, reason, until)

    async def _add_warn(
        self,
        guild_id: int,
        guild_owner_id: int,
        moderator: Participant,
        target: Participant,
        reason: str,
        until: datetime | None,
    ) -> WarnOutcome:
        now = self._clock()
        warn = await self._storage.save(
            Warn(
                guild_id=guild_id,
                target_id=target.id,
                moderator_id=moderator.id,
                reason=reason,
                created_at=now,
                expires_at=until,
            )
        )
        warns = await self._storage.find_all_by_user_id(guild_id, target.id)
        active = [w for w in warns if w.is_active(now)]
        limit_reached = self._policy.is_limit_reached(len(active))
        mute: MuteOutcome | None = None
        mute_error: Exception | None = None
        persisted = True
        if limit_reached:
            try:
                mute = await self._escalate(guild_id, guild_owner_id, moderator, target)
            except ModerationActionForbidden as error:
                mute_error = error
            except Exception as error:
                logger.exception("Escalation mute of {} in guild {} failed", target.id, guild_id)
                mute_error = error
            else:
                persisted = await self._revoke(active, now)
        return WarnOutcome(
            warn=warn,
            active_warns=len(active),
            limit=self._policy.limit,
            limit_reached=limit_reached,
            mute=mute,
            mute_error=mute_error,
            persisted=persisted,
        )

    async def _escalate(
        self,
        guild_id: int,
        guild_owner_id: int,
        moderator: Participant,
        target: Participant,
    ) -> MuteOutcome:
        reason = f"Достигнут лимит предупреждений ({self._policy.limit})"
        return await self._mutes_port.mute(
            guild_id,
            guild_owner_id,
            moderator,
            target,
            reason,
            self._policy.mute_duration,
            required=ModerationPermission.MODERATE,
        )

    async def _revoke(self, warns: Collection[Warn], now: datetime) -> bool:
        try:
            for warn in warns:
                await self._storage.save(warn.revoke(now))
        except Exception:
            logger.exception("Could not revoke warn records {}", [warn.id for warn in warns])
            return False
        return True

    @override
    async def remove_warn(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant, warn_id: int
    ) -> Warn | None:
        ensure_can_moderate(guild_owner_id, moderator, target, ModerationPermission.MODERATE)
        warn = await self._storage.find_by_id(guild_id, warn_id)
        if warn is None or warn.target_id != target.id or warn.revoked_at is not None:
            return None
        return await self._storage.save(warn.revoke(self._clock()))

    @override
    async def get_warns(self, guild_id: int, user_id: int) -> Collection[Warn]:
        return await self._storage.find_all_by_user_id(guild_id, user_id)

    @override
    async def clear_warns(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant
    ) -> Collection[Warn]:
        ensure_can_moderate(guild_owner_id, moderator, target, ModerationPermission.MODERATE)
        now = self._clock()
        warns = await self._storage.find_all_by_user_id(guild_id, target.id)
        return [await self._storage.save(warn.revoke(now)) for warn in warns if warn.is_active(now)]
