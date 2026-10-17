import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///reverse.db"

_ASYNC_DRIVERS = {
    "sqlite": "sqlite+aiosqlite",
    "postgresql": "postgresql+asyncpg",
    "postgres": "postgresql+asyncpg",
}


class SettingsError(ValueError):
    pass


def _required(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        raise SettingsError(f"Environment variable `{key}` is not set.")
    return value


def database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip() or DEFAULT_DATABASE_URL
    scheme, separator, rest = url.partition("://")
    if not separator:
        raise SettingsError(f"DATABASE_URL `{url}` is not a valid SQLAlchemy URL.")
    return f"{_ASYNC_DRIVERS.get(scheme, scheme)}://{rest}"


@dataclass(frozen=True, slots=True)
class Settings:
    token: str = field(repr=False)
    database_url: str = field(repr=False)
    log_dir: Path

    @classmethod
    def from_env(cls) -> Self:
        return cls(
            token=_required("TOKEN"),
            database_url=database_url(),
            log_dir=Path(os.getenv("LOG_DIR", "").strip() or "logs"),
        )


@dataclass(frozen=True, slots=True)
class EmbedColors:
    info: int = 0x5865F2
    success: int = 0x57F287
    warning: int = 0xFEE75C
    error: int = 0xED4245


EMBED_COLORS = EmbedColors()
