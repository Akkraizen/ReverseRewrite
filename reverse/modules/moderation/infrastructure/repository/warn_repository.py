from collections.abc import Collection
from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reverse.infrastructure.data.repository import Repository
from reverse.infrastructure.data.transaction import current_session, transactional, use_session
from reverse.modules.moderation.infrastructure.schemas.warn import WarnSchema


class WarnRepository(Repository[WarnSchema, int]):
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    @override
    async def find(self, id: int, **filters: object) -> WarnSchema | None:
        async with use_session(self._sessions) as session:
            return await session.scalar(select(WarnSchema).filter_by(id=id, **filters))

    @override
    async def find_all(self, **filters: object) -> Collection[WarnSchema]:
        async with use_session(self._sessions) as session:
            result = await session.scalars(select(WarnSchema).filter_by(**filters).order_by(WarnSchema.id))
            return list(result)

    @override
    @transactional
    async def insert(self, entity: WarnSchema) -> WarnSchema:
        session = current_session()
        session.add(entity)
        await session.flush()
        return entity

    @override
    @transactional
    async def update(self, entity: WarnSchema) -> WarnSchema | None:
        session = current_session()
        query = select(WarnSchema).filter_by(id=entity.id, guild_id=entity.guild_id).with_for_update()
        if await session.scalar(query) is None:
            return None
        merged = await session.merge(entity)
        await session.flush()
        return merged

    @override
    @transactional
    async def delete(self, id: int, **filters: object) -> WarnSchema | None:
        session = current_session()
        entity = await session.scalar(select(WarnSchema).filter_by(id=id, **filters))
        if entity is None:
            return None
        await session.delete(entity)
        await session.flush()
        return entity

    @override
    @transactional
    async def delete_all(self, **filters: object) -> Collection[WarnSchema]:
        session = current_session()
        entities = list(await session.scalars(select(WarnSchema).filter_by(**filters).order_by(WarnSchema.id)))
        for entity in entities:
            await session.delete(entity)
        await session.flush()
        return entities

    @override
    async def exists(self, id: int, **filters: object) -> bool:
        async with use_session(self._sessions) as session:
            found = await session.scalar(select(WarnSchema.id).filter_by(id=id, **filters).limit(1))
            return found is not None
