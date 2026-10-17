from collections.abc import Collection
from typing import override

from reverse.infrastructure.data.mapper import Mapper
from reverse.infrastructure.data.repository import RecordNotFound
from reverse.modules.moderation.domain.entities.ban import Ban
from reverse.modules.moderation.domain.ports.ban_port import BanStoragePort
from reverse.modules.moderation.infrastructure.repository.ban_repository import BanRepository
from reverse.modules.moderation.infrastructure.schemas.ban import BanSchema


class BanStorageAdapter(BanStoragePort, Mapper[Ban, BanSchema]):
    def __init__(self, repository: BanRepository) -> None:
        self._repository = repository

    @override
    def _to_schema(self, domain: Ban) -> BanSchema:
        schema = BanSchema(
            guild_id=domain.guild_id,
            target_id=domain.target_id,
            moderator_id=domain.moderator_id,
            reason=domain.reason,
            created_at=domain.created_at,
            revoked_at=domain.revoked_at,
        )
        if domain.id is not None:
            schema.id = domain.id
        return schema

    @override
    def _to_domain(self, schema: BanSchema) -> Ban:
        return Ban(
            id=schema.id,
            guild_id=schema.guild_id,
            target_id=schema.target_id,
            moderator_id=schema.moderator_id,
            reason=schema.reason,
            created_at=schema.created_at,
            revoked_at=schema.revoked_at,
        )

    @override
    async def find_all_by_guild_id(self, guild_id: int) -> Collection[Ban]:
        entities = await self._repository.find_all(guild_id=guild_id)
        return list(map(self._to_domain, entities))

    @override
    async def find_active_by_guild_id(self, guild_id: int) -> Collection[Ban]:
        entities = await self._repository.find_all(guild_id=guild_id, revoked_at=None)
        return list(map(self._to_domain, entities))

    @override
    async def find_all_by_user_id(self, guild_id: int, id: int) -> Collection[Ban]:
        entities = await self._repository.find_all(guild_id=guild_id, target_id=id)
        return list(map(self._to_domain, entities))

    @override
    async def save(self, ban: Ban) -> Ban:
        entity = self._to_schema(ban)
        if ban.id is None:
            return self._to_domain(await self._repository.insert(entity))
        saved = await self._repository.update(entity)
        if saved is None:
            raise RecordNotFound(f"Ban #{ban.id} in guild {ban.guild_id} no longer exists")
        return self._to_domain(saved)

    @override
    async def save_all(self, bans: Collection[Ban]) -> Collection[Ban]:
        if any(ban.id is None for ban in bans):
            raise ValueError("save_all only updates existing bans")
        return [self._to_domain(saved) for saved in await self._repository.update_all(list(map(self._to_schema, bans)))]
