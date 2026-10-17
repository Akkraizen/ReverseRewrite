from collections.abc import Collection
from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reverse.infrastructure.data.repository import RecordNotFound, Repository
from reverse.infrastructure.data.transaction import current_session, transactional, use_session
from reverse.modules.moderation.infrastructure.schemas.ban import BanSchema


class BanRepository(Repository[BanSchema, int]):
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    @override
    async def find(self, id: int, **filters: object) -> BanSchema | None:
        async with use_session(self._sessions) as session:
            return await session.scalar(select(BanSchema).filter_by(id=id, **filters))

    @override
    async def find_all(self, **filters: object) -> Collection[BanSchema]:
        async with use_session(self._sessions) as session:
            result = await session.scalars(select(BanSchema).filter_by(**filters).order_by(BanSchema.id))
            return list(result)

    @override
    @transactional
    async def insert(self, entity: BanSchema) -> BanSchema:
        session = current_session()
        session.add(entity)
        await session.flush()
        return entity

    @override
    @transactional
    async def update(self, entity: BanSchema) -> BanSchema | None:
        session = current_session()
        query = select(BanSchema).filter_by(id=entity.id, guild_id=entity.guild_id).with_for_update()
        if await session.scalar(query) is None:
            return None
        merged = await session.merge(entity)
        await session.flush()
        return merged

    @transactional
    async def update_all(self, entities: Collection[BanSchema]) -> list[BanSchema]:
        updated: list[BanSchema] = []
        for entity in entities:
            saved = await self.update(entity)
            if saved is None:
                raise RecordNotFound(f"Ban #{entity.id} in guild {entity.guild_id} no longer exists")
            updated.append(saved)
        return updated

    @override
    @transactional
    async def delete(self, id: int, **filters: object) -> BanSchema | None:
        session = current_session()
        entity = await session.scalar(select(BanSchema).filter_by(id=id, **filters))
        if entity is None:
            return None
        await session.delete(entity)
        await session.flush()
        return entity

    @override
    @transactional
    async def delete_all(self, **filters: object) -> Collection[BanSchema]:
        session = current_session()
        entities = list(await session.scalars(select(BanSchema).filter_by(**filters).order_by(BanSchema.id)))
        for entity in entities:
            await session.delete(entity)
        await session.flush()
        return entities

    @override
    async def exists(self, id: int, **filters: object) -> bool:
        async with use_session(self._sessions) as session:
            found = await session.scalar(select(BanSchema.id).filter_by(id=id, **filters).limit(1))
            return found is not None
