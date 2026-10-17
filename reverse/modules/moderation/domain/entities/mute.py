from dataclasses import dataclass, replace
from datetime import datetime
from typing import Self

from reverse.modules.moderation.domain.entities.validation import InvalidRecord, normalize_reason, require_aware


@dataclass(frozen=True, slots=True, kw_only=True)
class Mute:
    guild_id: int
    target_id: int
    moderator_id: int
    reason: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason", normalize_reason(self.reason))
        require_aware("created_at", self.created_at)
        require_aware("expires_at", self.expires_at)
        require_aware("revoked_at", self.revoked_at)
        if self.expires_at <= self.created_at:
            raise InvalidRecord("A mute must expire after it was created.")

    def is_active(self, now: datetime) -> bool:
        return self.revoked_at is None and self.expires_at > now

    def revoke(self, now: datetime) -> Self:
        return replace(self, revoked_at=now)
