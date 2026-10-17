import math
from datetime import timedelta
from time import perf_counter
from typing import override

from hikari.api import RESTClient
from hikari.traits import ShardAware

from reverse.modules.general.domain.ports.latency_port import LatencyGatewayPort


class DiscordLatencyGatewayAdapter(LatencyGatewayPort):
    def __init__(self, rest: RESTClient, shards: ShardAware) -> None:
        self._rest = rest
        self._shards = shards

    @override
    async def rest_latency(self) -> timedelta:
        started = perf_counter()
        await self._rest.fetch_my_user()
        return timedelta(seconds=perf_counter() - started)

    @override
    def gateway_latency(self) -> timedelta | None:
        latency = self._shards.heartbeat_latency
        return None if math.isnan(latency) else timedelta(seconds=latency)
