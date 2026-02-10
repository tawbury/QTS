import logging
import aiohttp

class APIObserverClient:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.session = None
        self.logger = logging.getLogger("APIObserverClient")

    async def connect(self):
        self.session = aiohttp.ClientSession()
        self.logger.info(f"Connected to Observer API at {self.endpoint}")

    async def disconnect(self):
        if self.session:
            await self.session.close()
            self.logger.info("Disconnected from Observer API")

    async def get_snapshot(self):
        url = f"{self.endpoint}/api/v1/snapshot"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    # 필요한 추가 메서드 구현 가능
