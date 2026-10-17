import re
from dataclasses import dataclass
from datetime import datetime

_LINK = re.compile(r"https?://\S+", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class ChannelMessage:
    id: int
    author_id: int
    author_is_bot: bool
    content: str
    created_at: datetime
    has_attachments: bool = False
    is_pinned: bool = False

    @property
    def has_links(self) -> bool:
        return _LINK.search(self.content) is not None


@dataclass(frozen=True, slots=True)
class MessageFilter:
    author_id: int | None = None
    bots_only: bool = False
    contains: str | None = None
    links_only: bool = False
    attachments_only: bool = False

    def matches(self, message: ChannelMessage) -> bool:
        if message.is_pinned:
            return False
        if self.author_id is not None and message.author_id != self.author_id:
            return False
        if self.bots_only and not message.author_is_bot:
            return False
        if self.contains and self.contains.casefold() not in message.content.casefold():
            return False
        if self.links_only and not message.has_links:
            return False
        return not self.attachments_only or message.has_attachments
