from collections.abc import Awaitable, Callable
from datetime import datetime

from arc import GatewayPlugin
from hikari import (
    AuditLogChangeKey,
    AuditLogEntryCreateEvent,
    AuditLogEventType,
    BanDeleteEvent,
    Member,
    MemberUpdateEvent,
)
from loguru import logger

from reverse.modules.moderation.application.moderation_facade import ModerationFacade
from reverse.modules.moderation.application.services.clock import Clock

type UserIdProvider = Callable[[], int | None]


def _timed_out(member: Member, now: datetime) -> bool:
    until = member.communication_disabled_until()
    return until is not None and until > now


async def _guarded(name: str, action: Awaitable[object]) -> None:
    try:
        await action
    except Exception:
        logger.exception("Moderation listener {} failed", name)


def include_listeners(
    plugin: GatewayPlugin, moderation: ModerationFacade, own_user_id: UserIdProvider, clock: Clock
) -> None:
    @plugin.listen()
    async def on_audit_log_entry(event: AuditLogEntryCreateEvent) -> None:
        entry = event.entry
        if entry.user_id is None or entry.target_id is None or entry.user_id == own_user_id():
            return
        guild_id, user_id, moderator_id = int(entry.guild_id), int(entry.target_id), int(entry.user_id)
        match entry.action_type:
            case AuditLogEventType.MEMBER_BAN_ADD:
                await _guarded("ban", moderation.on_banned(guild_id, user_id, moderator_id, entry.reason))
            case AuditLogEventType.MEMBER_BAN_REMOVE:
                await _guarded("unban", moderation.on_unbanned(guild_id, user_id))
            case AuditLogEventType.MEMBER_UPDATE:
                for change in entry.changes:
                    if change.key != AuditLogChangeKey.COMMUNICATION_DISABLED_UNTIL:
                        continue
                    until: datetime | None = change.new_value
                    if until is None:
                        await _guarded("timeout", moderation.on_timeout_lifted(guild_id, user_id))
                    else:
                        action = moderation.on_timed_out(guild_id, user_id, moderator_id, entry.reason, until)
                        await _guarded("timeout", action)
            case _:
                pass

    @plugin.listen()
    async def on_ban_delete(event: BanDeleteEvent) -> None:
        await _guarded("unban", moderation.on_unbanned(int(event.guild_id), int(event.user.id)))

    @plugin.listen()
    async def on_member_update(event: MemberUpdateEvent) -> None:
        now = clock()
        old = event.old_member
        if old is None or not _timed_out(old, now) or _timed_out(event.member, now):
            return
        await _guarded("timeout", moderation.on_timeout_lifted(int(event.guild_id), int(event.member.id)))
