from collections.abc import Iterable
from datetime import datetime, timedelta

import hikari
from arc import (
    BoolParams,
    GatewayContext,
    GatewayPlugin,
    IntParams,
    MemberParams,
    Option,
    StrParams,
    UserParams,
    slash_command,
)
from hikari import ApplicationContextType, Embed, MessageFlag, Permissions
from loguru import logger

from reverse.application.translator import Translation, Translator
from reverse.infrastructure.discord.utils.embeds import build_embed, build_listing
from reverse.infrastructure.discord.utils.formatting import mention, timestamp
from reverse.infrastructure.discord.utils.interactions import guild_of, reply
from reverse.modules.moderation.api.listeners import UserIdProvider, include_listeners
from reverse.modules.moderation.api.participants import to_participant
from reverse.modules.moderation.application.moderation_facade import ModerationFacade
from reverse.modules.moderation.application.services.clock import Clock, utc_now
from reverse.modules.moderation.domain.entities.ban import Ban
from reverse.modules.moderation.domain.entities.message import MessageFilter
from reverse.modules.moderation.domain.entities.participant import Participant
from reverse.modules.moderation.domain.entities.validation import InvalidRecord
from reverse.modules.moderation.domain.entities.warn import Warn
from reverse.modules.moderation.domain.policies.clear_policy import MAX_CLEAR_AMOUNT
from reverse.modules.moderation.domain.policies.moderation_policy import (
    BotTargetException,
    GuildOwnerTargetException,
    InvalidAmountException,
    InvalidDurationException,
    MissingPermissionException,
    ModerationDeniedException,
    RoleHierarchyException,
    SelfModerationException,
)
from reverse.modules.moderation.domain.policies.mute_policy import MAX_MUTE_DURATION
from reverse.modules.moderation.domain.policies.warn_policy import MAX_WARN_DAYS
from reverse.modules.moderation.domain.ports.ban_port import ActiveBan
from reverse.modules.moderation.domain.ports.moderation_gateway import ModerationActionForbidden
from reverse.modules.moderation.domain.ports.warn_port import WarnOutcome
from reverse.settings import EMBED_COLORS as COLOURS

DENIAL_KEYS: dict[type[ModerationDeniedException], str] = {
    MissingPermissionException: "denied.missing_permission",
    SelfModerationException: "denied.self_moderation",
    BotTargetException: "denied.bot_target",
    GuildOwnerTargetException: "denied.guild_owner_target",
    RoleHierarchyException: "denied.role_hierarchy",
    InvalidDurationException: "denied.invalid_duration",
    InvalidAmountException: "denied.invalid_amount",
}
FORBIDDEN = "errors.forbidden"

GUILD_ONLY = [ApplicationContextType.GUILD]
MODERATE = Permissions.MODERATE_MEMBERS
BAN = Permissions.BAN_MEMBERS
KICK = Permissions.KICK_MEMBERS
MANAGE_MESSAGES = Permissions.MANAGE_MESSAGES


def _moderator(ctx: GatewayContext, guild_id: int, roles: Iterable[hikari.Role]) -> Participant:
    assert ctx.member is not None
    return to_participant(guild_id, ctx.member, roles, ctx.member.permissions)


async def _parties(ctx: GatewayContext, target: hikari.Member) -> tuple[int, int, Participant, Participant]:
    guild_id, guild = await guild_of(ctx)
    roles = guild.get_roles().values()
    return guild_id, int(guild.owner_id), _moderator(ctx, guild_id, roles), to_participant(guild_id, target, roles)


async def _user_parties(ctx: GatewayContext, target: hikari.User) -> tuple[int, int, Participant, Participant]:
    guild_id, guild = await guild_of(ctx)
    moderator = _moderator(ctx, guild_id, guild.get_roles().values())
    return guild_id, int(guild.owner_id), moderator, Participant(int(target.id), is_bot=target.is_bot)


def _saved(t: Translation, embed: Embed, persisted: bool) -> Embed:
    if not persisted:
        embed.colour = COLOURS.warning
        embed.set_footer(t("common.not_persisted"))
    return embed


def _listing(t: Translation, title: str, header: str, lines: list[str]) -> Embed:
    history, overflow = t("common.history"), lambda hidden: t("common.more", count=hidden)
    return build_listing(title, header, lines, history=history, overflow=overflow)


def _state(t: Translation, active: bool) -> str:
    return "" if active else t("common.inactive")


def _record(t: Translation, record: Warn | Ban, now: datetime) -> str:
    return t(
        "common.record",
        id=record.id,
        created=timestamp(record.created_at),
        moderator=mention(record.moderator_id),
        reason=record.reason,
        state=_state(t, record.is_active(now)),
    )


def _describe_active_ban(t: Translation, active: ActiveBan) -> str:
    user = mention(active.user_id)
    if active.ban is None:
        reason = active.reason or t("common.no_reason")
        return t("ban.outside_record", user=user, reason=reason, outside=t("common.outside_bot"))
    ban = active.ban
    created, moderator = timestamp(ban.created_at), mention(ban.moderator_id)
    return t("ban.active_record", user=user, id=ban.id, created=created, moderator=moderator, reason=ban.reason)


def _describe_warn(t: Translation, target: hikari.Member, outcome: WarnOutcome) -> Embed:
    title = t("warn.title", id=outcome.warn.id)
    embed = build_embed(title, t("warn.issued", member=target.mention), COLOURS.warning)
    embed.add_field(t("common.reason"), outcome.warn.reason)
    embed.add_field(t("warn.active"), f"{outcome.active_warns}/{outcome.limit}", inline=True)
    if outcome.mute is not None:
        until = timestamp(outcome.mute.mute.expires_at)
        key = "warn.limit_muted" if outcome.persisted else "warn.limit_muted_kept"
        embed.add_field(t("warn.limit_reached"), t(key, until=until))
        _saved(t, embed, outcome.mute.persisted)
    elif outcome.mute_error is not None:
        embed.colour = COLOURS.error
        cause = t(FORBIDDEN) if isinstance(outcome.mute_error, ModerationActionForbidden) else t("errors.unexpected")
        embed.add_field(t("warn.limit_reached"), t("warn.limit_mute_failed", forbidden=cause))
    if not outcome.persisted:
        _saved(t, embed, persisted=False)
    return embed


def build_plugin(
    moderation: ModerationFacade,
    translator: Translator,
    own_user_id: UserIdProvider = lambda: None,
    clock: Clock = utc_now,
) -> GatewayPlugin:
    plugin = GatewayPlugin("moderation")
    include_listeners(plugin, moderation, own_user_id, clock)

    def texts(ctx: GatewayContext) -> Translation:
        return translator.bind(str(ctx.locale))

    d = translator.bind(translator.default_locale)
    member_option = MemberParams(d("options.member"))
    user_option = UserParams(d("options.user"))
    reason_option = StrParams(d("options.reason"), max_length=256)

    @plugin.include
    @slash_command("warn", d("commands.warn.description"), invocation_contexts=GUILD_ONLY, default_permissions=MODERATE)
    async def warn(
        ctx: GatewayContext,
        member: Option[hikari.Member, member_option],
        reason: Option[str, reason_option],
        days: Option[int | None, IntParams(d("commands.warn.options.days"), min=1, max=MAX_WARN_DAYS)] = None,
    ) -> None:
        until = clock() + timedelta(days=days) if days is not None else None
        outcome = await moderation.add_warn(*await _parties(ctx, member), reason, until)
        await reply(ctx, _describe_warn(texts(ctx), member, outcome))

    @plugin.include
    @slash_command(
        "unwarn", d("commands.unwarn.description"), invocation_contexts=GUILD_ONLY, default_permissions=MODERATE
    )
    async def unwarn(
        ctx: GatewayContext,
        member: Option[hikari.Member, member_option],
        warn_id: Option[int, IntParams(d("commands.unwarn.options.warn_id"))],
    ) -> None:
        t = texts(ctx)
        removed = await moderation.remove_warn(*await _parties(ctx, member), warn_id)
        if removed is None:
            text = t("warn.not_found", member=member.mention, id=warn_id)
            await reply(ctx, build_embed(t("warn.not_found_title"), text, COLOURS.error), ephemeral=True)
        else:
            text = t("warn.removed", member=member.mention, id=warn_id)
            await reply(ctx, build_embed(t("warn.removed_title"), text, COLOURS.success))

    @plugin.include
    @slash_command(
        "warns", d("commands.warns.description"), invocation_contexts=GUILD_ONLY, default_permissions=MODERATE
    )
    async def list_warns(ctx: GatewayContext, member: Option[hikari.Member, member_option]) -> None:
        assert ctx.guild_id is not None
        t = texts(ctx)
        records = await moderation.get_warns(int(ctx.guild_id), int(member.id))
        if not records:
            text = t("warn.none", member=member.mention)
            await reply(ctx, build_embed(t("warn.list_title"), text), ephemeral=True)
            return
        now = clock()
        lines = [_record(t, w, now) for w in records]
        header = t("warn.member", member=member.mention)
        await reply(ctx, _listing(t, t("warn.list_title"), header, lines), ephemeral=True)

    @plugin.include
    @slash_command(
        "clearwarns", d("commands.clearwarns.description"), invocation_contexts=GUILD_ONLY, default_permissions=MODERATE
    )
    async def clear_warns(ctx: GatewayContext, member: Option[hikari.Member, member_option]) -> None:
        t = texts(ctx)
        removed = await moderation.clear_warns(*await _parties(ctx, member))
        text = t("warn.cleared", member=member.mention, count=len(removed))
        await reply(ctx, build_embed(t("warn.cleared_title"), text, COLOURS.success))

    @plugin.include
    @slash_command(
        "mute",
        d("commands.mute.description"),
        invocation_contexts=GUILD_ONLY,
        default_permissions=MODERATE,
    )
    async def mute(
        ctx: GatewayContext,
        member: Option[hikari.Member, member_option],
        minutes: Option[
            int, IntParams(d("commands.mute.options.minutes"), min=1, max=MAX_MUTE_DURATION // timedelta(minutes=1))
        ],
        reason: Option[str, reason_option],
    ) -> None:
        t = texts(ctx)
        outcome = await moderation.mute(*await _parties(ctx, member), reason, timedelta(minutes=minutes))
        text = t("mute.issued", member=member.mention, until=timestamp(outcome.mute.expires_at))
        embed = build_embed(t("mute.title"), text, COLOURS.warning)
        embed.add_field(t("common.reason"), outcome.mute.reason)
        await reply(ctx, _saved(t, embed, outcome.persisted))

    @plugin.include
    @slash_command(
        "unmute", d("commands.unmute.description"), invocation_contexts=GUILD_ONLY, default_permissions=MODERATE
    )
    async def unmute(
        ctx: GatewayContext, member: Option[hikari.Member, member_option], reason: Option[str, reason_option]
    ) -> None:
        t = texts(ctx)
        outcome = await moderation.unmute(*await _parties(ctx, member), reason)
        embed = build_embed(t("mute.removed_title"), t("mute.removed", member=member.mention), COLOURS.success)
        await reply(ctx, _saved(t, embed, outcome.persisted))

    @plugin.include
    @slash_command(
        "mutes", d("commands.mutes.description"), invocation_contexts=GUILD_ONLY, default_permissions=MODERATE
    )
    async def list_mutes(ctx: GatewayContext, member: Option[hikari.Member, member_option]) -> None:
        assert ctx.guild_id is not None
        t = texts(ctx)
        await ctx.defer(flags=MessageFlag.EPHEMERAL)
        guild_id, user_id = int(ctx.guild_id), int(member.id)
        status = await moderation.get_mute_status(guild_id, user_id)
        if status is None:
            header = t("mute.not_muted", member=member.mention)
        else:
            reason = status.mute.reason if status.mute is not None else t("common.outside_bot")
            header = t("mute.muted", member=member.mention, until=timestamp(status.until), reason=reason)
        now = clock()
        lines = [
            t(
                "mute.record",
                id=m.id,
                created=timestamp(m.created_at),
                moderator=mention(m.moderator_id),
                until=timestamp(m.expires_at),
                reason=m.reason,
                state=_state(t, m.is_active(now)),
            )
            for m in await moderation.get_mutes(guild_id, user_id)
        ]
        await reply(ctx, _listing(t, t("mute.status_title"), header, lines), ephemeral=True)

    @plugin.include
    @slash_command("ban", d("commands.ban.description"), invocation_contexts=GUILD_ONLY, default_permissions=BAN)
    async def ban(
        ctx: GatewayContext, member: Option[hikari.Member, member_option], reason: Option[str, reason_option]
    ) -> None:
        t = texts(ctx)
        outcome = await moderation.ban(*await _parties(ctx, member), reason)
        embed = build_embed(t("ban.title"), t("ban.banned", user=member.mention), COLOURS.error)
        embed.add_field(t("common.reason"), outcome.ban.reason)
        await reply(ctx, _saved(t, embed, outcome.persisted))

    @plugin.include
    @slash_command("unban", d("commands.unban.description"), invocation_contexts=GUILD_ONLY, default_permissions=BAN)
    async def unban(
        ctx: GatewayContext, user: Option[hikari.User, user_option], reason: Option[str, reason_option]
    ) -> None:
        t = texts(ctx)
        outcome = await moderation.unban(*await _user_parties(ctx, user), reason)
        if not outcome.was_banned:
            embed = build_embed(t("ban.removed_title"), t("ban.not_banned", user=user.mention), COLOURS.error)
            await reply(ctx, embed, ephemeral=True)
            return
        embed = build_embed(t("ban.removed_title"), t("ban.removed", user=user.mention), COLOURS.success)
        await reply(ctx, _saved(t, embed, outcome.persisted))

    @plugin.include
    @slash_command("bans", d("commands.bans.description"), invocation_contexts=GUILD_ONLY, default_permissions=BAN)
    async def list_bans(
        ctx: GatewayContext,
        user: Option[hikari.User | None, UserParams(d("commands.bans.options.user"))] = None,
    ) -> None:
        assert ctx.guild_id is not None
        t = texts(ctx)
        guild_id = int(ctx.guild_id)
        await ctx.defer(flags=MessageFlag.EPHEMERAL)
        if user is None:
            active = await moderation.get_active_bans(guild_id)
            if not active:
                await reply(ctx, build_embed(t("ban.active_title"), t("ban.none_active")), ephemeral=True)
                return
            embed = _listing(t, t("ban.active_title"), "", [_describe_active_ban(t, ban) for ban in active])
            await reply(ctx, embed, ephemeral=True)
            return

        active_ban = await moderation.get_active_ban(guild_id, int(user.id))
        header = t("ban.banned" if active_ban is not None else "ban.not_banned", user=user.mention)
        if active_ban is not None and active_ban.ban is None:
            header += f" {t('common.outside_bot')}"
        now = clock()
        lines = [_record(t, b, now) for b in await moderation.get_bans(guild_id, int(user.id))]
        await reply(ctx, _listing(t, t("ban.list_title"), header, lines), ephemeral=True)

    @plugin.include
    @slash_command("kick", d("commands.kick.description"), invocation_contexts=GUILD_ONLY, default_permissions=KICK)
    async def kick(
        ctx: GatewayContext, member: Option[hikari.Member, member_option], reason: Option[str, reason_option]
    ) -> None:
        t = texts(ctx)
        await moderation.kick(*await _parties(ctx, member), reason)
        embed = build_embed(t("kick.title"), t("kick.issued", member=member.mention), COLOURS.warning)
        embed.add_field(t("common.reason"), reason.strip())
        await reply(ctx, embed)

    @plugin.include
    @slash_command(
        "clear", d("commands.clear.description"), invocation_contexts=GUILD_ONLY, default_permissions=MANAGE_MESSAGES
    )
    async def clear(
        ctx: GatewayContext,
        amount: Option[int, IntParams(d("commands.clear.options.amount"), min=1, max=MAX_CLEAR_AMOUNT)],
        user: Option[hikari.User | None, UserParams(d("commands.clear.options.user"))] = None,
        bots: Option[bool, BoolParams(d("commands.clear.options.bots"))] = False,
        contains: Option[str | None, StrParams(d("commands.clear.options.contains"), max_length=100)] = None,
        links: Option[bool, BoolParams(d("commands.clear.options.links"))] = False,
        attachments: Option[bool, BoolParams(d("commands.clear.options.attachments"))] = False,
    ) -> None:
        t = texts(ctx)
        guild_id, guild = await guild_of(ctx)
        moderator = _moderator(ctx, guild_id, guild.get_roles().values())
        message_filter = MessageFilter(
            author_id=int(user.id) if user is not None else None,
            bots_only=bots,
            contains=contains,
            links_only=links,
            attachments_only=attachments,
        )
        await ctx.defer(flags=MessageFlag.EPHEMERAL)
        outcome = await moderation.clear(int(guild.owner_id), int(ctx.channel_id), moderator, amount, message_filter)
        text = t("clear.deleted", count=outcome.deleted) if outcome.deleted else t("clear.nothing")
        if outcome.reached_old:
            text += "\n" + t("clear.reached_old")
        await reply(ctx, build_embed(t("clear.title"), text, COLOURS.success), ephemeral=True)

    @plugin.set_error_handler
    async def on_error(ctx: GatewayContext, error: Exception) -> None:
        t = texts(ctx)
        match error:
            case ModerationDeniedException():
                key = DENIAL_KEYS.get(type(error), "errors.unexpected")
                text = t(key, days=MAX_MUTE_DURATION.days, amount=MAX_CLEAR_AMOUNT)
            case ModerationActionForbidden():
                text = t(FORBIDDEN)
            case InvalidRecord():
                text = t("errors.invalid_record")
            case _:
                logger.opt(exception=error).error("Moderation command /{} failed", ctx.command.name)
                text = t("errors.unexpected")
        await reply(ctx, build_embed(t("errors.title"), text, COLOURS.error), ephemeral=True)

    return plugin
