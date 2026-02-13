"""Feedback Batch Scheduler — 비동기 피드백 수집 배치 잡.

근거: docs/arch/sub/20_Feedback_Loop_Architecture.md §4.2
- 1분마다 실행되는 피드백 집계
- 최근 완료된 ExecutionResult 조회 → FeedbackData 변환 → 저장
- Fail-Safe: 실패해도 매매에 영향 없음
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Protocol

from src.feedback.aggregator import FeedbackAggregator

logger = logging.getLogger(__name__)


class ExecutionResultStore(Protocol):
    """최근 체결 결과 조회 프로토콜."""

    async def fetch_recent_executions(
        self, since: datetime,
    ) -> list[dict]:
        """since 이후 완료된 체결 결과를 반환."""
        ...


class FeedbackBatchScheduler:
    """비동기 피드백 배치 수집 스케줄러.

    asyncio.create_task()로 백그라운드에서 실행.
    interval_seconds 주기로 최근 체결을 조회하여 피드백을 생성한다.

    Usage::

        scheduler = FeedbackBatchScheduler(aggregator, execution_store)
        task = asyncio.create_task(scheduler.run())
        # 종료 시
        scheduler.stop()
        await task
    """

    def __init__(
        self,
        aggregator: FeedbackAggregator,
        execution_store: ExecutionResultStore,
        *,
        interval_seconds: float = 60.0,
        max_retries_per_execution: int = 2,
    ) -> None:
        self._aggregator = aggregator
        self._store = execution_store
        self._interval = interval_seconds
        self._max_retries = max_retries_per_execution
        self._running = False
        self._processed_count = 0
        self._error_count = 0

    @property
    def processed_count(self) -> int:
        return self._processed_count

    @property
    def error_count(self) -> int:
        return self._error_count

    @property
    def is_running(self) -> bool:
        return self._running

    def stop(self) -> None:
        """스케줄러 종료 요청."""
        self._running = False

    async def run(self) -> None:
        """메인 배치 루프. stop() 호출 시 종료."""
        self._running = True
        logger.info("FeedbackBatchScheduler started (interval=%ss)", self._interval)

        while self._running:
            try:
                await self._process_batch()
            except Exception:
                logger.exception("Batch processing cycle failed (non-blocking)")
                self._error_count += 1

            # interval 대기 (1초 단위로 체크하여 stop 반응성 유지)
            waited = 0.0
            while waited < self._interval and self._running:
                await asyncio.sleep(min(1.0, self._interval - waited))
                waited += 1.0

        logger.info(
            "FeedbackBatchScheduler stopped. processed=%d errors=%d",
            self._processed_count,
            self._error_count,
        )

    async def run_once(self) -> int:
        """배치 1회 실행. 처리 건수 반환. 테스트용."""
        return await self._process_batch()

    async def _process_batch(self) -> int:
        """최근 interval 기간의 체결 결과를 피드백으로 변환."""
        since = datetime.now(timezone.utc) - timedelta(seconds=self._interval)

        try:
            executions = await self._store.fetch_recent_executions(since)
        except Exception:
            logger.exception("Failed to fetch recent executions")
            self._error_count += 1
            return 0

        if not executions:
            return 0

        count = 0
        for exec_result in executions:
            for attempt in range(self._max_retries + 1):
                try:
                    self._aggregate_one(exec_result)
                    count += 1
                    break
                except Exception:
                    if attempt == self._max_retries:
                        logger.warning(
                            "Feedback aggregation failed after %d attempts: %s",
                            self._max_retries + 1,
                            exec_result.get("order_id", "?"),
                        )
                        self._error_count += 1

        self._processed_count += count
        if count > 0:
            logger.info("Feedback batch: %d/%d processed", count, len(executions))
        return count

    def _aggregate_one(self, exec_result: dict) -> None:
        """단건 체결 → FeedbackData 변환 및 저장."""
        now = datetime.now(timezone.utc)
        self._aggregator.aggregate_and_store(
            symbol=exec_result.get("symbol", ""),
            order_id=exec_result.get("order_id", exec_result.get("intent_id", "")),
            execution_start=_parse_datetime(exec_result.get("execution_start")) or now,
            execution_end=_parse_datetime(exec_result.get("execution_end")) or now,
            decision_price=_safe_decimal(exec_result.get("decision_price")),
            avg_fill_price=_safe_decimal(exec_result.get("avg_fill_price")),
            filled_qty=_safe_decimal(exec_result.get("filled_qty")),
            original_qty=_safe_decimal(exec_result.get("original_qty")),
            partial_fill_ratio=float(exec_result.get("partial_fill_ratio", 0)),
            avg_fill_latency_ms=float(exec_result.get("avg_fill_latency_ms", 0)),
            strategy_tag=exec_result.get("strategy_tag", exec_result.get("strategy", "")),
            order_type=exec_result.get("order_type", "MARKET"),
        )


def _safe_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _parse_datetime(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None
