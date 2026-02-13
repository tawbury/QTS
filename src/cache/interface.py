"""
캐시 클라이언트 추상 인터페이스.

근거: docs/arch/sub/19_Caching_Architecture.md §4
- Hash 기반 데이터 접근 (hset/hgetall)
- TTL 기반 자동 만료
- Pipeline (배치) 지원
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.db.contracts import HealthStatus


class CacheClient(ABC):
    """캐시 클라이언트 추상 인터페이스."""

    @abstractmethod
    async def get(self, key: str) -> Optional[dict[str, str]]:
        """Hash 데이터 조회. 없거나 만료 시 None."""

    @abstractmethod
    async def set(
        self, key: str, mapping: dict[str, str], ttl: float
    ) -> bool:
        """Hash 데이터 저장 + TTL 설정."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """키 삭제."""

    @abstractmethod
    async def get_many(
        self, keys: list[str]
    ) -> dict[str, Optional[dict[str, str]]]:
        """다수의 키 일괄 조회 (Pipeline)."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """키 존재 여부."""

    @abstractmethod
    async def zadd(self, key: str, mapping: dict[str, float], ttl: Optional[float] = None) -> int:
        """Sorted Set 추가. mapping: {member: score}"""
        ...

    @abstractmethod
    async def zrevrange(self, key: str, start: int, stop: int, withscores: bool = False) -> list:
        """Sorted Set 상위 조회 (내림차순)."""
        ...

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """캐시 서비스 상태 확인."""
