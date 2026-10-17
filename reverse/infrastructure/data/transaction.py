from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from functools import wraps
from types import CoroutineType
from typing import Any, Concatenate, Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SessionOwner(Protocol):
    _sessions: async_sessionmaker[AsyncSession]


_current: ContextVar[tuple[async_sessionmaker[AsyncSession], AsyncSession] | None] = ContextVar(
    "current_session", default=None
)


def current_session() -> AsyncSession:
    current = _current.get()
    if current is None:
        raise RuntimeError("No active transaction: call this from a @transactional method.")
    return current[1]


@asynccontextmanager
async def use_session(factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    current = _current.get()
    if current is not None and current[0] is factory:
        yield current[1]
        return
    async with factory() as session:
        yield session


def transactional[Owner: SessionOwner, **P, Result](
    operation: Callable[Concatenate[Owner, P], CoroutineType[Any, Any, Result]],
) -> Callable[Concatenate[Owner, P], CoroutineType[Any, Any, Result]]:
    @wraps(operation)
    async def wrapped(owner: Owner, /, *args: P.args, **kwargs: P.kwargs) -> Result:
        factory = owner._sessions
        current = _current.get()
        if current is not None and current[0] is factory:
            return await operation(owner, *args, **kwargs)

        async with factory(expire_on_commit=False) as session, session.begin():
            token = _current.set((factory, session))
            try:
                return await operation(owner, *args, **kwargs)
            finally:
                _current.reset(token)

    return wrapped
