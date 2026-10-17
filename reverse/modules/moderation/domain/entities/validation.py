from datetime import datetime

MAX_REASON_LENGTH = 256
MISSING_REASON = "Причина не указана"


class InvalidRecord(ValueError):
    pass


def normalize_reason(reason: str) -> str:
    reason = reason.strip()
    if not reason:
        raise InvalidRecord("Reason must not be empty.")
    if len(reason) > MAX_REASON_LENGTH:
        raise InvalidRecord(f"Reason must be at most {MAX_REASON_LENGTH} characters.")
    return reason


def external_reason(reason: str | None) -> str:
    reason = (reason or "").strip()
    return reason[:MAX_REASON_LENGTH] if reason else MISSING_REASON


def require_aware(name: str, value: datetime | None) -> None:
    if value is not None and value.tzinfo is None:
        raise InvalidRecord(f"`{name}` must be timezone-aware.")
