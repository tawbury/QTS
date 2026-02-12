"""Data Layer + Cache + Event/Safety 통합 테스트."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.cache.circuit_breaker import CircuitBreaker, CircuitState
from src.cache.contracts import CACHE_TTL, CacheType, cache_key
from src.cache.manager import CacheManager
from src.cache.memory import InMemoryCacheClient
from src.db.adapters.hybrid import HybridAdapter
from src.db.adapters.memory import InMemoryAdapter
from src.db.contracts import LedgerEntry, Position
from src.event.contracts import (
    DegradationLevel,
    EventPriority,
    EventType,
    create_event,
)
from src.event.dispatcher import SAFETY_TO_DEGRADATION, EventDispatcher
from src.safety.state import SafetyState
from src.state.contracts import OperatingState


class TestAdapterCacheIntegration:
    """어댑터 + 캐시 통합."""

    @pytest.mark.asyncio
    async def test_cache_aside_full_flow(self):
        """DB 조회 → 캐시 저장 → 캐시 히트 → 캐시 무효화 → DB 재조회."""
        db = InMemoryAdapter()
        db.seed_position(
            Position(
                symbol="005930",
                qty=Decimal("100"),
                avg_price=Decimal("75000"),
            )
        )
        cache = InMemoryCacheClient()
        mgr = CacheManager(client=cache, db=db)

        # 1. 첫 조회 (cache miss → DB)
        pos = await mgr.get_position("005930")
        assert pos is not None
        assert pos.qty == Decimal("100")
        stats = mgr.get_stats(CacheType.POSITION)
        assert stats.miss_count == 1

        # 2. 두 번째 조회 (cache hit)
        pos2 = await mgr.get_position("005930")
        assert pos2 is not None
        assert stats.hit_count == 1

        # 3. 캐시 무효화
        await mgr.invalidate(CacheType.POSITION, "005930")

        # 4. 재조회 (cache miss → DB)
        pos3 = await mgr.get_position("005930")
        assert pos3 is not None
        assert stats.miss_count == 2

    @pytest.mark.asyncio
    async def test_write_through_updates_both(self):
        """Write-Through: DB + 캐시 동시 갱신."""
        db = InMemoryAdapter()
        db.seed_position(
            Position(
                symbol="005930",
                qty=Decimal("100"),
                avg_price=Decimal("75000"),
            )
        )
        cache = InMemoryCacheClient()
        mgr = CacheManager(client=cache, db=db)

        # Write-Through 업데이트
        await mgr.update_position_on_fill(
            "005930", Decimal("200"), Decimal("76000")
        )

        # DB 직접 확인
        db_pos = await db.fetch_position("005930")
        assert db_pos is not None
        assert db_pos.qty == Decimal("200")

        # 캐시 직접 확인
        key = cache_key(CacheType.POSITION, "005930")
        cached = await cache.get(key)
        assert cached is not None
        assert cached["qty"] == "200"


class TestHybridCacheIntegration:
    """HybridAdapter + Cache 통합."""

    @pytest.mark.asyncio
    async def test_hybrid_with_cache(self):
        """Hybrid → CacheManager 조합."""
        primary = InMemoryAdapter()
        secondary = InMemoryAdapter()
        hybrid = HybridAdapter(primary, secondary)

        await hybrid.update_position("A", Decimal("10"), Decimal("50"))

        cache = InMemoryCacheClient()
        mgr = CacheManager(client=cache, db=hybrid)

        pos = await mgr.get_position("A")
        assert pos is not None
        assert pos.qty == Decimal("10")


class TestCircuitBreakerRecovery:
    """Circuit Breaker 복구 시나리오."""

    @pytest.mark.asyncio
    async def test_open_to_closed_recovery(self):
        """OPEN → HALF_OPEN → CLOSED 복구 흐름."""
        db = InMemoryAdapter()
        db.seed_position(
            Position(
                symbol="A", qty=Decimal("10"), avg_price=Decimal("100")
            )
        )

        should_fail = True

        class TemporaryFailCache(InMemoryCacheClient):
            """should_fail=True 동안 실패, False면 정상 동작."""

            async def get(self, key):
                if should_fail:
                    raise ConnectionError("temp fail")
                return await super().get(key)

            async def set(self, key, mapping, ttl):
                if should_fail:
                    raise ConnectionError("temp fail")
                return await super().set(key, mapping, ttl)

        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=0.01)
        mgr = CacheManager(
            client=TemporaryFailCache(), db=db, breaker=breaker
        )

        # get + set 실패로 빠르게 OPEN
        await mgr.get_position("A")
        await mgr.get_position("A")
        assert breaker.state == CircuitState.OPEN

        # 장애 복구
        should_fail = False

        # recovery_timeout 대기
        import time

        time.sleep(0.02)

        # HALF_OPEN에서 성공 → CLOSED
        pos = await mgr.get_position("A")
        assert pos is not None
        assert breaker.state == CircuitState.CLOSED


class TestEventIntegration:
    """Event 시스템 통합."""

    def test_safety_to_degradation_mapping(self):
        """Safety State → Degradation Level 매핑 확인."""
        assert SAFETY_TO_DEGRADATION[SafetyState.NORMAL] == DegradationLevel.NORMAL
        assert SAFETY_TO_DEGRADATION[SafetyState.WARNING] == DegradationLevel.P3_PAUSED
        assert SAFETY_TO_DEGRADATION[SafetyState.FAIL] == DegradationLevel.P2_P3_PAUSED
        assert SAFETY_TO_DEGRADATION[SafetyState.LOCKDOWN] == DegradationLevel.CRITICAL_ONLY

    def test_cache_events_are_p3(self):
        """캐시 관련 이벤트는 P3_LOW."""
        event = create_event(EventType.METRIC_RECORD, source="cache")
        assert event.priority == EventPriority.P3_LOW
        assert event.can_drop

    def test_circuit_breaker_event_is_p0(self):
        """Circuit Breaker OPEN은 P0_CRITICAL 이벤트."""
        event = create_event(
            EventType.BROKER_DISCONNECT,
            source="cache_circuit_breaker",
            payload={"state": "OPEN"},
        )
        assert event.priority == EventPriority.P0_CRITICAL
        assert event.requires_ack


class TestSafetyIntegration:
    """Safety State 통합."""

    @pytest.mark.asyncio
    async def test_cache_works_in_normal_state(self):
        """NORMAL 상태에서 캐시 정상 동작."""
        db = InMemoryAdapter()
        db.seed_position(
            Position(
                symbol="A", qty=Decimal("10"), avg_price=Decimal("100")
            )
        )
        mgr = CacheManager(client=InMemoryCacheClient(), db=db)

        pos = await mgr.get_position("A")
        assert pos is not None

    @pytest.mark.asyncio
    async def test_ledger_through_hybrid(self):
        """안전한 Dual-Write 원장 기록."""
        primary = InMemoryAdapter()
        secondary = InMemoryAdapter()
        hybrid = HybridAdapter(primary, secondary)

        entry = LedgerEntry(
            timestamp=datetime.now(timezone.utc),
            symbol="005930",
            side="BUY",
            qty=Decimal("50"),
            price=Decimal("75000"),
            amount=Decimal("3750000"),
            strategy_tag="SCALP_RSI",
        )
        ok = await hybrid.append_ledger(entry)
        assert ok

        # 양쪽 모두 기록 확인
        p_ledger = await primary.fetch_ledger(symbol="005930")
        s_ledger = await secondary.fetch_ledger(symbol="005930")
        assert len(p_ledger) == 1
        assert len(s_ledger) == 1
        assert p_ledger[0].strategy_tag == "SCALP_RSI"


class TestOperatingStateIntegration:
    """OperatingState 통합 (향후 확장 포인트)."""

    def test_state_properties_available(self):
        """OperatingState 속성이 존재하는지 확인."""
        from src.state.contracts import STATE_PROPERTIES

        for state in OperatingState:
            assert state in STATE_PROPERTIES

    def test_aggressive_scalp_allocation(self):
        """AGGRESSIVE 상태의 scalp 배분 확인."""
        from src.state.contracts import STATE_PROPERTIES

        props = STATE_PROPERTIES[OperatingState.AGGRESSIVE]
        assert props.scalp_allocation_range == (0.60, 0.80)
