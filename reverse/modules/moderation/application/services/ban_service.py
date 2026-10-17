from collections.abc import Collection
from datetime import datetime
from typing import override

from loguru import logger

from reverse.modules.moderation.application.services.clock import Clock, utc_now
from reverse.modules.moderation.domain.entities.ban import Ban
from reverse.modules.moderation.domain.entities.participant import ModerationPermission, Participant
from reverse.modules.moderation.domain.entities.validation import external_reason, normalize_reason
from reverse.modules.moderation.domain.policies.moderation_policy import ensure_can_moderate
from reverse.modules.moderation.domain.ports.ban_port import (
    ActiveBan,
    BanInputPort,
    BanOutcome,
    BanStoragePort,
    UnbanOutcome,
)
from reverse.modules.moderation.domain.ports.moderation_gateway import ModerationGateway


class BanService(BanInputPort):
    def __init__(self, storage: BanStoragePort, gateway: ModerationGateway, clock: Clock = utc_now) -> None:
        self._storage = storage
        self._gateway = gateway
        self._clock = clock

    @override
    async def ban(
        self,
        guild_id: int,
        guild_owner_id: int,
        moderator: Participant,
        target: Participant,
        reason: str,
        required: ModerationPermission = ModerationPermission.BAN,
    ) -> BanOutcome:
        ensure_can_moderate(guild_owner_id, moderator, target, required)
        ban = Ban(
            guild_id=guild_id,
            target_id=target.id,
            moderator_id=moderator.id,
            reason=reason,
            created_at=self._clock(),
        )
        await self._gateway.ban(guild_id, target.id, ban.reason)
        try:
            return BanOutcome(ban=await self._storage.save(ban), persisted=True)
        except Exception:
            logger.exception("Ban of {} in guild {} applied but not saved", target.id, guild_id)
            return BanOutcome(ban=ban, persisted=False)

    @override
    async def unban(
        self, guild_id: int, guild_owner_id: int, moderator: Participant, target: Participant, reason: str
    ) -> UnbanOutcome:
        ensure_can_moderate(guild_owner_id, moderator, target, ModerationPermission.BAN)
        was_banned = await self._gateway.unban(guild_id, target.id, normalize_reason(reason))
        now = self._clock()
        try:
            active = await self._active_records(guild_id, target.id, now)
        except Exception:
            logger.exception("Unban of {} in guild {} applied but not saved", target.id, guild_id)
            return UnbanOutcome(revoked=[], persisted=False, was_banned=was_banned)
        revoked, persisted = await self._revoke(active, now)
        return UnbanOutcome(revoked=revoked, persisted=persisted, was_banned=was_banned)

    @override
    async def get_bans(self, guild_id: int, user_id: int | None = None) -> Collection[Ban]:
        if user_id is None:
            return await self._storage.find_all_by_guild_id(guild_id)
        return await self._storage.find_all_by_user_id(guild_id, user_id)

    @override
    async def get_active_bans(self, guild_id: int) -> Collection[ActiveBan]:
        in_discord = {ban.user_id: ban for ban in await self._gateway.fetch_bans(guild_id)}
        now = self._clock()
        active = [ban for ban in await self._storage.find_active_by_guild_id(guild_id) if ban.is_active(now)]
        await self._revoke([ban for ban in active if ban.target_id not in in_discord], now)
        records = {ban.target_id: ban for ban in active}
        return [ActiveBan(user_id, ban.reason, records.get(user_id)) for user_id, ban in in_discord.items()]

    @override
    async def get_active_ban(self, guild_id: int, user_id: int) -> ActiveBan | None:
        in_discord = await self._gateway.fetch_ban(guild_id, user_id)
        now = self._clock()
        active = await self._active_records(guild_id, user_id, now)
        if in_discord is None:
            await self._revoke(active, now)
            return None
        return ActiveBan(user_id, in_discord.reason, active[-1] if active else None)

    async def _active_records(self, guild_id: int, user_id: int, now: datetime) -> list[Ban]:
        return [ban for ban in await self._storage.find_all_by_user_id(guild_id, user_id) if ban.is_active(now)]

    async def _revoke(self, bans: Collection[Ban], now: datetime) -> tuple[list[Ban], bool]:
        if not bans:
            return [], True
        try:
            return list(await self._storage.save_all([ban.revoke(now) for ban in bans])), True
        except Exception:
            logger.exception("Could not revoke ban records {}", [ban.id for ban in bans])
            return [], False

    @override
    async def on_banned(self, guild_id: int, user_id: int, moderator_id: int, reason: str | None) -> Ban | None:
        now = self._clock()
        if await self._active_records(guild_id, user_id, now):
            return None
        ban = Ban(
            guild_id=guild_id,
            target_id=user_id,
            moderator_id=moderator_id,
            reason=external_reason(reason),
            created_at=now,
        )
        return await self._storage.save(ban)

    @override
    async def on_unbanned(self, guild_id: int, user_id: int) -> Collection[Ban]:
        now = self._clock()
        revoked, _ = await self._revoke(await self._active_records(guild_id, user_id, now), now)
        return revoked
