from collections.abc import Collection
from typing import override

from reverse.infrastructure.data.mapper import Mapper
from reverse.infrastructure.data.repository import RecordNotFound
from reverse.modules.moderation.domain.entities.mute import Mute
from reverse.modules.moderation.domain.ports.mute_port import MuteStoragePort
from reverse.modules.moderation.infrastructure.repository.mute_repository import MuteRepository
from reverse.modules.moderation.infrastructure.schemas.mute import MuteSchema


class MuteStorageAdapter(MuteStoragePort, Mapper[Mute, MuteSchema]):
    def __init__(self, repository: MuteRepository) -> None:
        self._repository = repository

    @override
    def _to_schema(self, domain: Mute) -> MuteSchema:
        schema = MuteSchema(
            guild_id=domain.guild_id,
            target_id=domain.target_id,
            moderator_id=domain.moderator_id,
            reason=domain.reason,
            created_at=domain.created_at,
            expires_at=domain.expires_at,
            revoked_at=domain.revoked_at,
        )
        if domain.id is not None:
            schema.id = domain.id
        return schema

    @override
    def _to_domain(self, schema: MuteSchema) -> Mute:
        return Mute(
            id=schema.id,
            guild_id=schema.guild_id,
            target_id=schema.target_id,
            moderator_id=schema.moderator_id,
            reason=schema.reason,
            created_at=schema.created_at,
            expires_at=schema.expires_at,
            revoked_at=schema.revoked_at,
        )

    @override
    async def find_all_by_user_id(self, guild_id: int, id: int) -> Collection[Mute]:
        entities = await self._repository.find_all(guild_id=guild_id, target_id=id)
        return list(map(self._to_domain, entities))

    @override
    async def save(self, mute: Mute) -> Mute:
        entity = self._to_schema(mute)
        if mute.id is None:
            return self._to_domain(await self._repository.insert(entity))
        saved = await self._repository.update(entity)
        if saved is None:
            raise RecordNotFound(f"Mute #{mute.id} in guild {mute.guild_id} no longer exists")
        return self._to_domain(saved)
