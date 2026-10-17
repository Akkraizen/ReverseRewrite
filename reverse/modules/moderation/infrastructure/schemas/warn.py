from datetime import datetime

from sqlalchemy import BigInteger, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from reverse.infrastructure.data.types import UtcDateTime
from reverse.modules.moderation.domain.entities.validation import MAX_REASON_LENGTH
from reverse.modules.moderation.infrastructure.schemas.base import ModerationBase


class WarnSchema(ModerationBase):
    __tablename__ = "warns"
    __table_args__ = (Index("ix_warns_guild_id_target_id", "guild_id", "target_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[int] = mapped_column(BigInteger)
    target_id: Mapped[int] = mapped_column(BigInteger)
    moderator_id: Mapped[int] = mapped_column(BigInteger)
    reason: Mapped[str] = mapped_column(String(MAX_REASON_LENGTH))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime)
    expires_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
