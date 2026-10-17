from typing import Protocol

from arc import GatewayClient


class Plugin(Protocol):
    def install(self, client: GatewayClient) -> None: ...
    async def close(self) -> None: ...
