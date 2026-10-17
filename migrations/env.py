import asyncio

from alembic import context
from dotenv import load_dotenv
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from reverse.infrastructure.data.base import Base
from reverse.settings import database_url

target_metadata = Base.metadata


def _url() -> str:
    if url := context.config.get_main_option("sqlalchemy.url"):
        return url
    load_dotenv()
    return database_url()


def _configure(**kwargs: object) -> None:
    context.configure(
        target_metadata=target_metadata,
        render_as_batch=_url().startswith("sqlite"),
        compare_type=True,
        **kwargs,  # type: ignore[arg-type]
    )


def run_migrations_offline() -> None:
    _configure(url=_url(), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def _run_sync(connection: Connection) -> None:
    _configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(_url())
    try:
        async with engine.connect() as connection:
            await connection.run_sync(_run_sync)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
