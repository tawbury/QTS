"""FeedbackRepository - TimescaleDB 기반 피드백 CRUD.

근거: docs/02-design/features/eteda-db-feedback-loop.design.md D-02
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from src.feedback.contracts import FeedbackData, FeedbackSummary, DEFAULT_FEEDBACK_SUMMARY

logger = logging.getLogger(__name__)


class FeedbackRepository:
    """TimescaleDB 기반 피드백 저장/조회."""

    def __init__(self, pool: Any) -> None:
        self._pool = pool  # asyncpg.Pool

    async def store(self, feedback: FeedbackData) -> None:
        """FeedbackData를 feedback_data 테이블에 저장."""
        await self._pool.execute(
            """
            INSERT INTO feedback_data
            (time, symbol, strategy_tag, order_id,
             slippage_bps, quality_score, impact_bps,
             fill_latency_ms, fill_ratio, filled_qty, fill_price,
             original_qty, volatility, spread_bps, depth, order_type)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """,
            feedback.feedback_generated_at,
            feedback.symbol,
            feedback.strategy_tag,
            None,  # order_id (FeedbackData에 없으면 None)
            feedback.total_slippage_bps,
            feedback.execution_quality_score,
            feedback.market_impact_bps,
            feedback.avg_fill_latency_ms,
            feedback.partial_fill_ratio,
            feedback.total_filled_qty,
            feedback.avg_fill_price,
            feedback.original_qty,
            feedback.volatility_at_execution,
            feedback.spread_at_execution,
            feedback.depth_at_execution,
            feedback.order_type,
        )

    async def fetch_summary(
        self,
        symbol: str,
        lookback_hours: int = 24,
    ) -> FeedbackSummary:
        """시간 기반 롤링 피드백 집계."""
        row = await self._pool.fetchrow(
            """
            SELECT
                COALESCE(AVG(slippage_bps), 10.0) AS avg_slippage_bps,
                COALESCE(AVG(impact_bps), 15.0) AS avg_impact_bps,
                COALESCE(AVG(quality_score), 0.75) AS avg_quality_score,
                COALESCE(AVG(fill_latency_ms), 50.0) AS avg_fill_latency_ms,
                COALESCE(AVG(fill_ratio), 0.95) AS avg_fill_ratio,
                COUNT(*) AS sample_count
            FROM feedback_data
            WHERE symbol = $1
              AND time >= NOW() - make_interval(hours => $2)
            """,
            symbol,
            lookback_hours,
        )
        if row is None or row["sample_count"] == 0:
            return DEFAULT_FEEDBACK_SUMMARY
        return FeedbackSummary(
            avg_slippage_bps=float(row["avg_slippage_bps"]),
            avg_market_impact_bps=float(row["avg_impact_bps"]),
            avg_quality_score=float(row["avg_quality_score"]),
            avg_fill_latency_ms=float(row["avg_fill_latency_ms"]),
            avg_fill_ratio=float(row["avg_fill_ratio"]),
            sample_count=int(row["sample_count"]),
        )

    async def fetch_summary_by_strategy(
        self,
        symbol: str,
        strategy_tag: str,
        lookback_hours: int = 24,
    ) -> FeedbackSummary:
        """전략별 피드백 집계."""
        row = await self._pool.fetchrow(
            """
            SELECT
                COALESCE(AVG(slippage_bps), 10.0) AS avg_slippage_bps,
                COALESCE(AVG(impact_bps), 15.0) AS avg_impact_bps,
                COALESCE(AVG(quality_score), 0.75) AS avg_quality_score,
                COALESCE(AVG(fill_latency_ms), 50.0) AS avg_fill_latency_ms,
                COALESCE(AVG(fill_ratio), 0.95) AS avg_fill_ratio,
                COUNT(*) AS sample_count
            FROM feedback_data
            WHERE symbol = $1
              AND strategy_tag = $2
              AND time >= NOW() - make_interval(hours => $3)
            """,
            symbol,
            strategy_tag,
            lookback_hours,
        )
        if row is None or row["sample_count"] == 0:
            return DEFAULT_FEEDBACK_SUMMARY
        return FeedbackSummary(
            avg_slippage_bps=float(row["avg_slippage_bps"]),
            avg_market_impact_bps=float(row["avg_impact_bps"]),
            avg_quality_score=float(row["avg_quality_score"]),
            avg_fill_latency_ms=float(row["avg_fill_latency_ms"]),
            avg_fill_ratio=float(row["avg_fill_ratio"]),
            sample_count=int(row["sample_count"]),
        )

    async def fetch_recent(
        self,
        symbol: str,
        limit: int = 10,
    ) -> list[dict]:
        """최근 N건 raw 데이터."""
        rows = await self._pool.fetch(
            """
            SELECT time, symbol, strategy_tag, slippage_bps,
                   quality_score, impact_bps, fill_latency_ms,
                   fill_ratio, filled_qty, fill_price, order_type
            FROM feedback_data
            WHERE symbol = $1
            ORDER BY time DESC
            LIMIT $2
            """,
            symbol,
            limit,
        )
        return [dict(r) for r in rows]
