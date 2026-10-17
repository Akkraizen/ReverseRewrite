from collections.abc import Iterable

from hikari import Member, Permissions, Role

from reverse.modules.moderation.domain.entities.participant import ModerationPermission, Participant

PERMISSION_FLAGS = {
    ModerationPermission.MODERATE: Permissions.MODERATE_MEMBERS,
    ModerationPermission.MUTE: Permissions.MODERATE_MEMBERS,
    ModerationPermission.BAN: Permissions.BAN_MEMBERS,
    ModerationPermission.KICK: Permissions.KICK_MEMBERS,
    ModerationPermission.MANAGE_MESSAGES: Permissions.MANAGE_MESSAGES,
}


def to_participant(
    guild_id: int, member: Member, guild_roles: Iterable[Role], channel_permissions: Permissions | None = None
) -> Participant:
    roles = {int(role.id): role for role in guild_roles}
    member_roles = [roles[role_id] for role_id in (guild_id, *member.role_ids) if role_id in roles]

    granted = channel_permissions
    if granted is None:
        granted = Permissions.NONE
        for role in member_roles:
            granted |= role.permissions
    if granted & Permissions.ADMINISTRATOR:
        permissions = frozenset(ModerationPermission)
    else:
        permissions = frozenset(permission for permission, needed in PERMISSION_FLAGS.items() if granted & needed)

    return Participant(
        id=int(member.id),
        top_role_position=max((role.position for role in member_roles), default=0),
        permissions=permissions,
        is_bot=member.is_bot,
    )
