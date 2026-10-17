from reverse.modules.moderation.domain.entities.participant import ModerationPermission, Participant


class ModerationDeniedException(Exception): ...


class MissingPermissionException(ModerationDeniedException): ...


class SelfModerationException(ModerationDeniedException): ...


class BotTargetException(ModerationDeniedException): ...


class GuildOwnerTargetException(ModerationDeniedException): ...


class RoleHierarchyException(ModerationDeniedException): ...


class InvalidDurationException(ModerationDeniedException): ...


class InvalidAmountException(ModerationDeniedException): ...


def ensure_can_moderate(
    guild_owner_id: int, moderator: Participant, target: Participant, required: ModerationPermission
) -> None:
    if target.is_self(moderator):
        raise SelfModerationException()
    if target.is_bot:
        raise BotTargetException()
    if target.is_guild_owner(guild_owner_id):
        raise GuildOwnerTargetException()
    if moderator.is_guild_owner(guild_owner_id):
        return
    if target.ranks_at_least(moderator):
        raise RoleHierarchyException()
    if not moderator.has_permissions(required):
        raise MissingPermissionException()


def ensure_has_permission(guild_owner_id: int, moderator: Participant, required: ModerationPermission) -> None:
    if moderator.is_guild_owner(guild_owner_id):
        return
    if not moderator.has_permissions(required):
        raise MissingPermissionException()
