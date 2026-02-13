"""FeedbackBatchScheduler 단위 테스트."""
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import pytest

from src.feedback.batch_scheduler import (
    FeedbackBatchScheduler,
    _parse_datetime,
    _safe_decimal,
)


class FakeAggregator:
    """테스트용 FeedbackAggregator."""

    def __init__(self, *, fail_on: Optional[set[str]] = None) -> None:
        self.calls: list[dict] = []
        self._fail_on = fail_on or set()

    def aggregate_and_store(self, **kwargs) -> None:
        if kwargs.get("symbol") in self._fail_on:
            raise ValueError(f"Aggregation failed for {kwargs['symbol']}")
        self.calls.append(kwargs)


class FakeExecutionStore:
    """테스트용 ExecutionResultStore."""

    def __init__(self, executions: list[dict] | None = None) -> None:
        self._executions = executions or []
        self.call_count = 0

    async def fetch_recent_executions(self, since: datetime) -> list[dict]:
        self.call_count += 1
        return list(self._executions)


class TestHelperFunctions:
    """헬퍼 함수 테스트."""

    def test_safe_decimal_normal(self):
        assert _safe_decimal("123.45") == Decimal("123.45")

    def test_safe_decimal_none(self):
        assert _safe_decimal(None) == Decimal("0")

    def test_safe_decimal_invalid(self):
        assert _safe_decimal("abc") == Decimal("0")

    def test_parse_datetime_none(self):
        assert _parse_datetime(None) is None

    def test_parse_datetime_valid_string(self):
        dt = _parse_datetime("2026-01-15T10:00:00+00:00")
        assert dt is not None
        assert dt.year == 2026

    def test_parse_datetime_datetime_object(self):
        now = datetime.now(timezone.utc)
        assert _parse_datetime(now) is now

    def test_parse_datetime_invalid(self):
        assert _parse_datetime("not-a-date") is None


class TestBatchSchedulerInit:
    """초기화 테스트."""

    def test_defaults(self):
        scheduler = FeedbackBatchScheduler(
            FakeAggregator(), FakeExecutionStore()
        )
        assert scheduler.processed_count == 0
        assert scheduler.error_count == 0
        assert not scheduler.is_running

    def test_custom_interval(self):
        scheduler = FeedbackBatchScheduler(
            FakeAggregator(), FakeExecutionStore(), interval_seconds=30.0
        )
        assert scheduler._interval == 30.0


class TestRunOnce:
    """단건 배치 실행."""

    @pytest.mark.asyncio
    async def test_empty_executions(self):
        agg = FakeAggregator()
        store = FakeExecutionStore([])
        scheduler = FeedbackBatchScheduler(agg, store)

        count = await scheduler.run_once()
        assert count == 0
        assert len(agg.calls) == 0
        assert store.call_count == 1

    @pytest.mark.asyncio
    async def test_single_execution(self):
        agg = FakeAggregator()
        store = FakeExecutionStore([{
            "symbol": "005930",
            "order_id": "ORD001",
            "execution_start": "2026-01-15T10:00:00",
            "execution_end": "2026-01-15T10:00:01",
            "decision_price": "75000",
            "avg_fill_price": "75010",
            "filled_qty": "100",
            "original_qty": "100",
            "partial_fill_ratio": 1.0,
            "avg_fill_latency_ms": 250.0,
            "strategy_tag": "SCALP_RSI",
            "order_type": "LIMIT",
        }])
        scheduler = FeedbackBatchScheduler(agg, store)

        count = await scheduler.run_once()
        assert count == 1
        assert scheduler.processed_count == 1
        assert len(agg.calls) == 1
        assert agg.calls[0]["symbol"] == "005930"

    @pytest.mark.asyncio
    async def test_multiple_executions(self):
        executions = [
            {"symbol": f"SYM{i}", "order_id": f"ORD{i}"}
            for i in range(5)
        ]
        agg = FakeAggregator()
        store = FakeExecutionStore(executions)
        scheduler = FeedbackBatchScheduler(agg, store)

        count = await scheduler.run_once()
        assert count == 5
        assert scheduler.processed_count == 5


class TestRetryLogic:
    """재시도 로직."""

    @pytest.mark.asyncio
    async def test_retry_on_aggregation_failure(self):
        agg = FakeAggregator(fail_on={"FAIL_SYM"})
        store = FakeExecutionStore([
            {"symbol": "OK_SYM", "order_id": "1"},
            {"symbol": "FAIL_SYM", "order_id": "2"},
        ])
        scheduler = FeedbackBatchScheduler(
            agg, store, max_retries_per_execution=2
        )

        count = await scheduler.run_once()
        assert count == 1  # OK_SYM 성공
        assert scheduler.error_count == 1  # FAIL_SYM 실패

    @pytest.mark.asyncio
    async def test_store_fetch_failure(self):
        class FailingStore:
            async def fetch_recent_executions(self, since):
                raise ConnectionError("DB down")

        agg = FakeAggregator()
        scheduler = FeedbackBatchScheduler(agg, FailingStore())

        count = await scheduler.run_once()
        assert count == 0
        assert scheduler.error_count == 1


class TestRunLoop:
    """run() 메인 루프."""

    @pytest.mark.asyncio
    async def test_stop_works(self):
        agg = FakeAggregator()
        store = FakeExecutionStore([])
        scheduler = FeedbackBatchScheduler(
            agg, store, interval_seconds=0.1
        )

        async def stop_after():
            await asyncio.sleep(0.25)
            scheduler.stop()

        task = asyncio.create_task(scheduler.run())
        stopper = asyncio.create_task(stop_after())

        await asyncio.wait_for(
            asyncio.gather(task, stopper), timeout=5.0
        )
        assert not scheduler.is_running

    @pytest.mark.asyncio
    async def test_run_processes_multiple_cycles(self):
        agg = FakeAggregator()
        store = FakeExecutionStore([{"symbol": "A", "order_id": "1"}])
        scheduler = FeedbackBatchScheduler(
            agg, store, interval_seconds=0.05
        )

        async def stop_after():
            await asyncio.sleep(0.2)
            scheduler.stop()

        task = asyncio.create_task(scheduler.run())
        stopper = asyncio.create_task(stop_after())
        await asyncio.wait_for(
            asyncio.gather(task, stopper), timeout=5.0
        )

        # 여러 사이클 동안 여러 번 처리
        assert scheduler.processed_count >= 2
        assert store.call_count >= 2


class TestFieldMapping:
    """ExecutionResult 필드 매핑."""

    @pytest.mark.asyncio
    async def test_fallback_fields(self):
        """intent_id → order_id, strategy → strategy_tag 폴백."""
        agg = FakeAggregator()
        store = FakeExecutionStore([{
            "symbol": "005930",
            "intent_id": "INTENT001",
            "strategy": "MOMENTUM",
        }])
        scheduler = FeedbackBatchScheduler(agg, store)

        await scheduler.run_once()
        assert len(agg.calls) == 1
        assert agg.calls[0]["order_id"] == "INTENT001"
        assert agg.calls[0]["strategy_tag"] == "MOMENTUM"

    @pytest.mark.asyncio
    async def test_defaults_for_missing_fields(self):
        """누락 필드에 대한 기본값."""
        agg = FakeAggregator()
        store = FakeExecutionStore([{"symbol": "TEST"}])
        scheduler = FeedbackBatchScheduler(agg, store)

        await scheduler.run_once()
        assert len(agg.calls) == 1
        call = agg.calls[0]
        assert call["order_type"] == "MARKET"
        assert call["partial_fill_ratio"] == 0
        assert call["avg_fill_latency_ms"] == 0
