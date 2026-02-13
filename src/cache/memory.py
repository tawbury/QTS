"""
인메모리 캐시 클라이언트.

테스트 및 로컬 개발용. TTL 지원.
"""
from __future__ import annotations

import time
from typing import Optional

from src.cache.interface import CacheClient
from src.db.contracts import HealthStatus


class InMemoryCacheClient(CacheClient):
    """인메모리 캐시. TTL 기반 자동 만료."""

    def __init__(self) -> None:
        # key → (mapping, expire_at)
        self._store: dict[str, tuple[dict[str, str], float]] = {}
        self._sorted_sets: dict[str, dict[str, float]] = {}

    async def get(self, key: str) -> Optional[dict[str, str]]:
        entry = self._store.get(key)
        if entry is None:
            return None
        mapping, expire_at = entry
        if time.monotonic() >= expire_at:
            del self._store[key]
            return None
        return dict(mapping)

    async def set(
        self, key: str, mapping: dict[str, str], ttl: float
    ) -> bool:
        expire_at = time.monotonic() + ttl
        self._store[key] = (dict(mapping), expire_at)
        return True

    async def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def get_many(
        self, keys: list[str]
    ) -> dict[str, Optional[dict[str, str]]]:
        result: dict[str, Optional[dict[str, str]]] = {}
        for key in keys:
            result[key] = await self.get(key)
        return result

    async def zadd(self, key: str, mapping: dict[str, float], ttl: Optional[float] = None) -> int:
        if key not in self._sorted_sets:
            self._sorted_sets[key] = {}
        self._sorted_sets[key].update(mapping)
        return len(mapping)

    async def zrevrange(self, key: str, start: int, stop: int, withscores: bool = False) -> list:
        data = self._sorted_sets.get(key, {})
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        sliced = sorted_items[start:stop + 1]
        if withscores:
            return sliced
        return [item[0] for item in sliced]

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def health_check(self) -> HealthStatus:
        return HealthStatus(
            healthy=True, source="in_memory_cache", latency_ms=0.0
        )

    def clear(self) -> None:
        """전체 캐시 삭제."""
        self._store.clear()

    async def flush_all(self) -> bool:
        """전체 캐시 삭제 (async 인터페이스)."""
        self._store.clear()
        return True

    @property
    def size(self) -> int:
        """현재 유효 항목 수 (만료 미제거 포함)."""
        return len(self._store)
