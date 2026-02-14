"""FeedbackAggregator — ExecutionResult → FeedbackData 변환."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional, Protocol

from src.feedback.contracts import (
    FeedbackData,
    FeedbackSummary,
    MarketContext,
    TickRecord,
    DEFAULT_FEEDBACK_SUMMARY,
)
from src.feedback.impact import estimate_market_impact_bps
from src.feedback.quality import calculate_execution_quality_score
from src.feedback.slippage import calculate_slippage_bps


# ---------------------------------------------------------------------------
# Protocol: DB Adapter
# ---------------------------------------------------------------------------

class FeedbackDBAdapter(Protocol):
    """피드백 저장소 프로토콜."""

    def store_feedback(self, feedback: FeedbackData) -> None: ...

    def fetch_feedback_summary(
        self, symbol: str, lookback_days: int,
    ) -> Optional[FeedbackSummary]: ...


# ---------------------------------------------------------------------------
# Noop DB Adapter (테스트용)
# ---------------------------------------------------------------------------

class NoopFeedbackDB:
    """테스트용 No-op DB adapter."""

    def __init__(self) -> None:
        self.stored: list[FeedbackData] = []

    def store_feedback(self, feedback: FeedbackData) -> None:
        self.stored.append(feedback)

    def fetch_feedback_summary(
        self, symbol: str, lookback_days: int,
    ) -> Optional[FeedbackSummary]:
        return None


# ---------------------------------------------------------------------------
# FeedbackAggregator
# ---------------------------------------------------------------------------

class FeedbackAggregator:
    """실행 데이터 → 피드백 데이터 변환."""

    def __init__(
        self,
        db: FeedbackDBAdapter,
        *,
        feedback_repo: Any = None,
    ) -> None:
        self._db = db
        self._repo = feedback_repo  # FeedbackRepository (TimescaleDB)

    def aggregate(
        self,
        *,
        symbol: str,
        order_id: str,
        execution_start: datetime,
        execution_end: datetime,
        decision_price: Decimal,
        avg_fill_price: Decimal,
        filled_qty: Decimal,
        original_qty: Decimal,
        partial_fill_ratio: float,
        avg_fill_latency_ms: float,
        strategy_tag: str = "",
        order_type: str = "",
        ticks: list[TickRecord] | None = None,
        market: MarketContext | None = None,
    ) -> FeedbackData:
        """ExecutionResult 정보로부터 FeedbackData를 생성한다."""
        _market = market or MarketContext()
        _ticks = ticks or []

        slippage_bps = calculate_slippage_bps(decision_price, avg_fill_price)

        quality_score = calculate_execution_quality_score(
            total_slippage_bps=slippage_bps,
            partial_fill_ratio=partial_fill_ratio,
            avg_fill_latency_ms=avg_fill_latency_ms,
        )

        impact_bps = estimate_market_impact_bps(
            order_qty=filled_qty,
            avg_daily_volume=_market.avg_daily_volume,
            spread_bps=_market.spread_bps,
        )

        feedback = FeedbackData(
            symbol=symbol,
            execution_start=execution_start,
            execution_end=execution_end,
            feedback_generated_at=datetime.now(timezone.utc),
            scalp_ticks=_ticks,
            total_slippage_bps=slippage_bps,
            avg_fill_latency_ms=avg_fill_latency_ms,
            partial_fill_ratio=partial_fill_ratio,
            total_filled_qty=filled_qty,
            avg_fill_price=avg_fill_price,
            volatility_at_execution=_market.volatility,
            spread_at_execution=_market.spread_bps,
            depth_at_execution=_market.depth,
            execution_quality_score=quality_score,
            market_impact_bps=impact_bps,
            strategy_tag=strategy_tag,
            order_type=order_type,
            original_qty=original_qty,
        )
        return feedback

    def aggregate_and_store(
        self, **kwargs,
    ) -> FeedbackData:
        """aggregate + store (TimescaleDB primary, JSONL fallback)."""
        feedback = self.aggregate(**kwargs)
        if self._repo is not None:
            try:
                import asyncio
                loop = asyncio.get_running_loop()
                loop.create_task(self._repo.store(feedback))
            except (RuntimeError, Exception):
                self._db.store_feedback(feedback)
        else:
            self._db.store_feedback(feedback)
        return feedback

    def get_summary(
        self, symbol: str, lookback_days: int = 30,
    ) -> FeedbackSummary:
        """종목별 피드백 요약 조회 (없으면 기본값)."""
        summary = self._db.fetch_feedback_summary(symbol, lookback_days)
        return summary if summary is not None else DEFAULT_FEEDBACK_SUMMARY

    async def get_summary_async(
        self,
        symbol: str,
        strategy_tag: Optional[str] = None,
        lookback_hours: int = 24,
    ) -> FeedbackSummary:
        """비동기 요약 조회 (TimescaleDB 우선)."""
        if self._repo is not None:
            try:
                if strategy_tag:
                    return await self._repo.fetch_summary_by_strategy(
                        symbol, strategy_tag, lookback_hours,
                    )
                return await self._repo.fetch_summary(symbol, lookback_hours)
            except Exception:
                pass
        summary = self._db.fetch_feedback_summary(symbol, max(lookback_hours // 24, 1))
        return summary if summary is not None else DEFAULT_FEEDBACK_SUMMARY
