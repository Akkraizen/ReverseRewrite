from collections.abc import AsyncIterator, Collection
from datetime import datetime
from typing import override

from hikari import BulkDeleteError, ForbiddenError, Message, NotFoundError
from hikari.api import RESTClient

from reverse.modules.moderation.domain.entities.message import ChannelMessage
from reverse.modules.moderation.domain.ports.moderation_gateway import (
    DiscordBan,
    ModerationActionForbidden,
    ModerationGateway,
)


def _to_message(message: Message) -> ChannelMessage:
    return ChannelMessage(
        id=int(message.id),
        author_id=int(message.author.id),
        author_is_bot=message.author.is_bot,
        content=message.content or "",
        created_at=message.created_at,
        has_attachments=bool(message.attachments),
        is_pinned=message.is_pinned,
    )


class DiscordModerationGateway(ModerationGateway):
    def __init__(self, rest: RESTClient) -> None:
        self._rest = rest

    @override
    async def ban(self, guild_id: int, user_id: int, reason: str) -> None:
        try:
            await self._rest.ban_user(guild_id, user_id, reason=reason)
        except ForbiddenError as error:
            raise ModerationActionForbidden(str(error)) from error

    @override
    async def unban(self, guild_id: int, user_id: int, reason: str) -> bool:
        try:
            await self._rest.unban_user(guild_id, user_id, reason=reason)
        except NotFoundError:
            return False
        except ForbiddenError as error:
            raise ModerationActionForbidden(str(error)) from error
        return True

    @override
    async def fetch_ban(self, guild_id: int, user_id: int) -> DiscordBan | None:
        try:
            ban = await self._rest.fetch_ban(guild_id, user_id)
        except NotFoundError:
            return None
        except ForbiddenError as error:
            raise ModerationActionForbidden(str(error)) from error
        return DiscordBan(user_id=int(ban.user.id), reason=ban.reason)

    @override
    async def fetch_bans(self, guild_id: int) -> Collection[DiscordBan]:
        try:
            return [
                DiscordBan(user_id=int(ban.user.id), reason=ban.reason) async for ban in self._rest.fetch_bans(guild_id)
            ]
        except ForbiddenError as error:
            raise ModerationActionForbidden(str(error)) from error

    @override
    async def timeout(self, guild_id: int, user_id: int, until: datetime, reason: str) -> None:
        await self._edit_timeout(guild_id, user_id, until, reason)

    @override
    async def remove_timeout(self, guild_id: int, user_id: int, reason: str) -> None:
        await self._edit_timeout(guild_id, user_id, None, reason)

    @override
    async def fetch_timeout(self, guild_id: int, user_id: int) -> datetime | None:
        member = await self._rest.fetch_member(guild_id, user_id)
        return member.communication_disabled_until()

    @override
    async def kick(self, guild_id: int, user_id: int, reason: str) -> None:
        try:
            await self._rest.kick_user(guild_id, user_id, reason=reason)
        except ForbiddenError as error:
            raise ModerationActionForbidden(str(error)) from error

    @override
    async def iter_messages(self, channel_id: int) -> AsyncIterator[ChannelMessage]:
        try:
            async for message in self._rest.fetch_messages(channel_id):
                yield _to_message(message)
        except ForbiddenError as error:
            raise ModerationActionForbidden(str(error)) from error

    @override
    async def delete_messages(self, channel_id: int, message_ids: Collection[int], reason: str) -> None:
        try:
            await self._rest.delete_messages(channel_id, message_ids, reason=reason)
        except ForbiddenError as error:
            raise ModerationActionForbidden(str(error)) from error
        except BulkDeleteError as error:
            if isinstance(error.__cause__, ForbiddenError):
                raise ModerationActionForbidden(str(error)) from error
            raise

    async def _edit_timeout(self, guild_id: int, user_id: int, until: datetime | None, reason: str) -> None:
        try:
            await self._rest.edit_member(guild_id, user_id, communication_disabled_until=until, reason=reason)
        except ForbiddenError as error:
            raise ModerationActionForbidden(str(error)) from error
