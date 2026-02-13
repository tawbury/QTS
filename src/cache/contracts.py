"""
캐시 레이어 계약.

근거: docs/arch/sub/19_Caching_Architecture.md §3, §5
- 6가지 캐시 타입 및 TTL
- CacheStats 히트율 추적
- CacheConfig 설정
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CacheType(str, Enum):
    """캐시 데이터 타입 (§3)."""

    PRICE = "price"  # 100ms TTL
    POSITION = "position"  # 1s TTL
    ORDERBOOK = "orderbook"  # 50ms TTL
    RISK = "risk"  # 5s TTL
    ORDER = "order"  # 60s TTL
    STRATEGY = "strategy"  # 60s TTL


CACHE_TTL: dict[CacheType, float] = {
    CacheType.PRICE: 0.1,
    CacheType.POSITION: 1.0,
    CacheType.ORDERBOOK: 0.05,
    CacheType.RISK: 5.0,
    CacheType.ORDER: 60.0,
    CacheType.STRATEGY: 60.0,
}


# 캐시 키 프리픽스 (§3 Redis Key 패턴)
CACHE_KEY_PREFIX: dict[CacheType, str] = {
    CacheType.PRICE: "price",
    CacheType.POSITION: "pos",
    CacheType.ORDERBOOK: "book",
    CacheType.RISK: "risk",
    CacheType.ORDER: "ord",
    CacheType.STRATEGY: "strat",
}


def cache_key(cache_type: CacheType, identifier: str) -> str:
    """캐시 키 생성. 예: price:005930"""
    prefix = CACHE_KEY_PREFIX[cache_type]
    return f"{prefix}:{identifier}"


@dataclass
class CacheStats:
    """캐시 히트/미스 통계 (§8.1)."""

    hit_count: int = 0
    miss_count: int = 0
    error_count: int = 0

    @property
    def total(self) -> int:
        return self.hit_count + self.miss_count

    @property
    def hit_rate(self) -> float:
        return self.hit_count / self.total if self.total > 0 else 0.0

    def record_hit(self) -> None:
        self.hit_count += 1

    def record_miss(self) -> None:
        self.miss_count += 1

    def record_error(self) -> None:
        self.error_count += 1


@dataclass(frozen=True)
class CacheConfig:
    """캐시 설정 (§9.1)."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""
    max_connections: int = 50
    socket_timeout_ms: int = 100
    socket_connect_timeout_ms: int = 500
    circuit_breaker_threshold: int = 5
    circuit_breaker_recovery_s: int = 60
