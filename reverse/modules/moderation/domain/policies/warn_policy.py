from dataclasses import dataclass
from datetime import timedelta

MAX_WARN_DAYS = 365


@dataclass(frozen=True, slots=True)
class WarnPolicy:
    limit: int = 3
    mute_duration: timedelta = timedelta(days=1)

    def is_limit_reached(self, active_warns: int) -> bool:
        return active_warns >= self.limit
