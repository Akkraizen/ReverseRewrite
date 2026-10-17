from datetime import timedelta
from typing import Protocol


class LatencyGatewayPort(Protocol):
    async def rest_latency(self) -> timedelta: ...
    def gateway_latency(self) -> timedelta | None: ...
