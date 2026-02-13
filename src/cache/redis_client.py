"""
Redis 캐시 클라이언트.

근거: docs/arch/sub/19_Caching_Architecture.md §7
- redis.asyncio 기반
- ConnectionPool 관리
- hset/hgetall Hash 작업
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

from src.cache.contracts import CacheConfig
from src.cache.interface import CacheClient
from src.db.contracts import HealthStatus

logger = logging.getLogger(__name__)


class RedisCacheClient(CacheClient):
    """Redis 기반 캐시 클라이언트."""

    def __init__(self, config: Optional[CacheConfig] = None) -> None:
        self._config = config or CacheConfig()
        self._redis: Any = None  # redis.asyncio.Redis

    async def connect(self) -> None:
        """Redis 연결 + ConnectionPool 생성."""
        try:
            import redis.asyncio as aioredis
        except ImportError as e:
            raise ImportError(
                "redis[asyncio] is required for RedisCacheClient. "
                "Install with: pip install redis"
            ) from e

        pool = aioredis.ConnectionPool(
            host=self._config.host,
            port=self._config.port,
            db=self._config.db,
            password=self._config.password or None,
            max_connections=self._config.max_connections,
            decode_responses=True,
            socket_connect_timeout=self._config.socket_connect_timeout_ms / 1000,
            socket_timeout=self._config.socket_timeout_ms / 1000,
            socket_keepalive=True,
        )
        self._redis = aioredis.Redis(connection_pool=pool)
        logger.info("Redis connection pool created")

    async def close(self) -> None:
        """Redis 연결 종료."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None
            logger.info("Redis connection closed")

    def _ensure_connected(self) -> None:
        if self._redis is None:
            raise RuntimeError(
                "Redis not connected. Call connect() first."
            )

    async def get(self, key: str) -> Optional[dict[str, str]]:
        self._ensure_connected()
        data = await self._redis.hgetall(key)
        return data if data else None

    async def set(
        self, key: str, mapping: dict[str, str], ttl: float
    ) -> bool:
        self._ensure_connected()
        await self._redis.hset(key, mapping=mapping)
        # TTL이 1초 미만이면 pexpire 사용 (밀리초)
        if ttl < 1:
            await self._redis.pexpire(key, int(ttl * 1000))
        else:
            await self._redis.expire(key, int(ttl))
        return True

    async def delete(self, key: str) -> bool:
        self._ensure_connected()
        result = await self._redis.delete(key)
        return result > 0

    async def get_many(
        self, keys: list[str]
    ) -> dict[str, Optional[dict[str, str]]]:
        self._ensure_connected()
        pipe = self._redis.pipeline()
        for key in keys:
            pipe.hgetall(key)
        results = await pipe.execute()
        return {
            key: (result if result else None)
            for key, result in zip(keys, results)
        }

    async def exists(self, key: str) -> bool:
        self._ensure_connected()
        return bool(await self._redis.exists(key))

    async def zadd(self, key: str, mapping: dict[str, float], ttl: Optional[float] = None) -> int:
        try:
            result = await self._redis.zadd(key, mapping)
            if ttl is not None:
                if ttl < 1:
                    await self._redis.pexpire(key, int(ttl * 1000))
                else:
                    await self._redis.expire(key, int(ttl))
            return result
        except Exception as e:
            logger.error("Redis zadd failed: %s", e)
            return 0

    async def zrevrange(self, key: str, start: int, stop: int, withscores: bool = False) -> list:
        try:
            return await self._redis.zrevrange(key, start, stop, withscores=withscores)
        except Exception as e:
            logger.error("Redis zrevrange failed: %s", e)
            return []

    async def flush_all(self) -> bool:
        """전체 캐시 삭제 (Emergency Only)."""
        try:
            await self._redis.flushdb()
            logger.warning("All cache flushed (Redis)")
            return True
        except Exception as e:
            logger.error("Redis flush_all failed: %s", e)
            return False

    async def health_check(self) -> HealthStatus:
        if self._redis is None:
            return HealthStatus(
                healthy=False,
                source="redis",
                error="not_connected",
            )
        try:
            start = time.monotonic()
            await self._redis.ping()
            latency = (time.monotonic() - start) * 1000
            return HealthStatus(
                healthy=True, source="redis", latency_ms=latency
            )
        except Exception as e:
            return HealthStatus(
                healthy=False, source="redis", error=str(e)
            )
