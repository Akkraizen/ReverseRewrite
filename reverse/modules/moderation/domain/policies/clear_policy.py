from datetime import timedelta

from reverse.modules.moderation.domain.policies.moderation_policy import InvalidAmountException

MAX_CLEAR_AMOUNT = 100
MAX_MESSAGE_AGE = timedelta(days=14) - timedelta(minutes=5)
SCAN_LIMIT = 500


def ensure_valid_clear_amount(amount: int) -> None:
    if not 0 < amount <= MAX_CLEAR_AMOUNT:
        raise InvalidAmountException()
