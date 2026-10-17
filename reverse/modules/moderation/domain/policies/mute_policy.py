from datetime import timedelta

from reverse.modules.moderation.domain.policies.moderation_policy import InvalidDurationException

MAX_MUTE_DURATION = timedelta(days=28)


def ensure_valid_mute_duration(duration: timedelta) -> None:
    if not timedelta(0) < duration <= MAX_MUTE_DURATION:
        raise InvalidDurationException()
