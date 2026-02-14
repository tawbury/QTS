"""
캐시 관리자.

근거: docs/arch/sub/19_Caching_Architecture.md §4, §5, §6
- Cache-Aside 패턴 (§4.1): 캐시 → DB fallback
- Write-Through 패턴 (§4.2): DB + 캐시 동시 갱신
- Circuit Breaker 통합 (§6.2)
- Stale Data Detection (§6.3)
- Manual Invalidation (§5.3)
- Retry Strategy (§6.4)
"""
from __future__ import annotations

import logging
import time
from decimal import Decimal
from typing import Optional

from src.cache.circuit_breaker import CircuitBreaker, CircuitState
from src.cache.contracts import (
    CACHE_TTL,
    CacheStats,
    CacheType,
    cache_key,
)
from src.cache.interface import CacheClient
from src.db.adapters.interface import DataSourceAdapter
from src.db.contracts import Position

logger = logging.getLogger(__name__)


class CacheStaleDataError(Exception):
    """캐시 데이터가 TTL 이상 오래된 경우 (§6.3)."""


def is_stale(cached_data: dict[str, str], threshold_ms: int = 100) -> bool:
    """캐시 데이터 신선도 검사 (§6.3).

    cached_data에 timestamp(unix ms) 필드가 있으면 현재 시각과 비교.
    """
    ts_str = cached_data.get("timestamp") or cached_data.get("updated_at")
    if not ts_str:
        return False
    try:
        timestamp_ms = int(ts_str)
    except (ValueError, TypeError):
        return False
    now_ms = int(time.time() * 1000)
    age_ms = now_ms - timestamp_ms
    return age_ms > threshold_ms


class CacheManager:
    """캐시 관리자. Cache-Aside + Circuit Breaker."""

    def __init__(
        self,
        client: CacheClient,
        db: DataSourceAdapter,
        breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        self._client = client
        self._db = db
        self._breaker = breaker or CircuitBreaker()
        self._stats: dict[CacheType, CacheStats] = {
            ct: CacheStats() for ct in CacheType
        }

    # ── Cache-Aside: Position ──

    async def get_position(self, symbol: str) -> Optional[Position]:
        """Cache-Aside 패턴으로 포지션 조회."""
        key = cache_key(CacheType.POSITION, symbol)
        stats = self._stats[CacheType.POSITION]

        # Circuit Breaker 확인
        if self._breaker.can_execute():
            try:
                cached = await self._client.get(key)
                if cached:
                    stats.record_hit()
                    self._breaker.record_success()
                    return Position.from_cache_dict(cached)
                stats.record_miss()
                self._breaker.record_success()
            except Exception as e:
                logger.warning("Cache get failed: %s", e)
                stats.record_error()
                self._breaker.record_failure()
        else:
            stats.record_miss()

        # DB fallback
        position = await self._db.fetch_position(symbol)
        if position is not None:
            await self._safe_cache_set(
                key,
                position.to_cache_dict(),
                CACHE_TTL[CacheType.POSITION],
            )
        return position

    # ── Write-Through: Position update ──

    async def update_position_on_fill(
        self, symbol: str, qty: Decimal, avg_price: Decimal
    ) -> bool:
        """Write-Through: DB 업데이트 후 캐시 갱신."""
        ok = await self._db.update_position(symbol, qty, avg_price)
        if ok:
            position = await self._db.fetch_position(symbol)
            if position:
                key = cache_key(CacheType.POSITION, symbol)
                await self._safe_cache_set(
                    key,
                    position.to_cache_dict(),
                    CACHE_TTL[CacheType.POSITION],
                )
        return ok

    # ── Real-Time Push: Price ──

    async def push_price(self, symbol: str, data: dict[str, str]) -> bool:
        """Real-Time Push: 캐시에 직접 쓰기 (Market Data Feed)."""
        key = cache_key(CacheType.PRICE, symbol)
        return await self._safe_cache_set(
            key, data, CACHE_TTL[CacheType.PRICE]
        )

    async def get_price(self, symbol: str) -> Optional[dict[str, str]]:
        """Price 캐시 조회. miss = data unavailable (DB fallback 없음)."""
        key = cache_key(CacheType.PRICE, symbol)
        stats = self._stats[CacheType.PRICE]

        if not self._breaker.can_execute():
            stats.record_miss()
            return None

        try:
            cached = await self._client.get(key)
            if cached:
                stats.record_hit()
                self._breaker.record_success()
                return cached
            stats.record_miss()
            self._breaker.record_success()
            return None
        except Exception as e:
            logger.warning("Price cache get failed: %s", e)
            stats.record_error()
            self._breaker.record_failure()
            return None

    # ── Generic cache operations ──

    async def get_cached(
        self, cache_type: CacheType, identifier: str
    ) -> Optional[dict[str, str]]:
        """범용 캐시 조회."""
        key = cache_key(cache_type, identifier)
        stats = self._stats[cache_type]

        if not self._breaker.can_execute():
            stats.record_miss()
            return None

        try:
            cached = await self._client.get(key)
            if cached:
                stats.record_hit()
                self._breaker.record_success()
                return cached
            stats.record_miss()
            self._breaker.record_success()
            return None
        except Exception:
            stats.record_error()
            self._breaker.record_failure()
            return None

    async def set_cached(
        self, cache_type: CacheType, identifier: str, data: dict[str, str]
    ) -> bool:
        """범용 캐시 저장."""
        key = cache_key(cache_type, identifier)
        return await self._safe_cache_set(key, data, CACHE_TTL[cache_type])

    async def invalidate(
        self, cache_type: CacheType, identifier: str
    ) -> bool:
        """캐시 무효화."""
        key = cache_key(cache_type, identifier)
        try:
            return await self._client.delete(key)
        except Exception as e:
            logger.warning("Cache invalidate failed: %s", e)
            return False

    # ── Event-Based Invalidation ──

    async def on_execution_result(self, symbol: str) -> None:
        """주문 체결 이벤트 → Position 캐시 무효화."""
        await self.invalidate(CacheType.POSITION, symbol)

    async def on_strategy_param_changed(self, strategy_id: str) -> None:
        """전략 파라미터 변경 이벤트 → Strategy 캐시 무효화."""
        await self.invalidate(CacheType.STRATEGY, strategy_id)

    async def on_order_update(self, order_id: str) -> None:
        """주문 상태 변경 → Order 캐시 무효화."""
        await self.invalidate(CacheType.ORDER, order_id)

    # ── Stale Data Detection (§6.3) ──

    async def get_price_checked(
        self, symbol: str, stale_threshold_ms: int = 100
    ) -> dict[str, str]:
        """Price 조회 + 신선도 검사. stale 시 CacheStaleDataError.

        근거: docs/arch/sub/19_Caching_Architecture.md §6.3
        """
        cached = await self.get_price(symbol)
        if cached is None:
            raise CacheStaleDataError(f"No price data: {symbol}")
        if is_stale(cached, threshold_ms=stale_threshold_ms):
            logger.warning("Price data for %s is stale (ts=%s)", symbol, cached.get("timestamp"))
            raise CacheStaleDataError(f"Price too old: {symbol}")
        return cached

    # ── Manual Flush (§5.3) ──

    async def flush_all(self) -> bool:
        """전체 캐시 삭제 (Emergency Only, §5.3).

        근거: docs/arch/sub/19_Caching_Architecture.md §5.3
        """
        try:
            if hasattr(self._client, "flush_all"):
                result = await self._client.flush_all()
            else:
                # InMemory 등 flush_all 미지원 클라이언트: 개별 삭제는 불가, False 반환
                logger.warning("Cache client does not support flush_all")
                return False
            logger.warning("All cache flushed manually")
            # 통계 리셋
            for ct in CacheType:
                self._stats[ct] = CacheStats()
            return result
        except Exception as e:
            logger.error("Cache flush failed: %s", e)
            return False

    # ── Retry Helper (§6.4) ──

    async def get_with_retry(
        self, key: str, max_attempts: int = 3, wait_ms: float = 10
    ) -> Optional[dict[str, str]]:
        """캐시 조회 + 재시도 (§6.4).

        근거: docs/arch/sub/19_Caching_Architecture.md §6.4
        """
        import asyncio

        for attempt in range(max_attempts):
            try:
                result = await self._client.get(key)
                self._breaker.record_success()
                return result
            except Exception as e:
                self._breaker.record_failure()
                if attempt == max_attempts - 1:
                    logger.warning("Cache get_with_retry exhausted: %s", e)
                    return None
                await asyncio.sleep(wait_ms / 1000)
        return None

    # ── Stats & State ──

    def get_stats(self, cache_type: CacheType) -> CacheStats:
        return self._stats[cache_type]

    @property
    def circuit_state(self) -> CircuitState:
        return self._breaker.state

    def is_circuit_open(self) -> bool:
        return self._breaker.state == CircuitState.OPEN

    # ── Internal ──

    async def _safe_cache_set(
        self, key: str, mapping: dict[str, str], ttl: float
    ) -> bool:
        """캐시 저장 (실패해도 에러 전파하지 않음)."""
        if not self._breaker.can_execute():
            return False
        try:
            result = await self._client.set(key, mapping, ttl)
            self._breaker.record_success()
            return result
        except Exception as e:
            logger.warning("Cache set failed: %s", e)
            self._breaker.record_failure()
            return False
