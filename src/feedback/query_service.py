"""FeedbackQueryService - 다차원 피드백 분석 쿼리.

근거: docs/02-design/features/eteda-db-feedback-loop.design.md D-03
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from src.feedback.contracts import FeedbackSummary

logger = logging.getLogger(__name__)


class FeedbackQueryService:
    """다차원 피드백 분석 쿼리."""

    def __init__(self, pool: Any) -> None:
        self._pool = pool  # asyncpg.Pool

    async def get_hourly_slippage_pattern(
        self,
        symbol: str,
        days: int = 7,
    ) -> dict[int, float]:
        """시간대별(0~23) 평균 슬리피지 분포."""
        rows = await self._pool.fetch(
            """
            SELECT
                EXTRACT(HOUR FROM time)::int AS hour,
                AVG(slippage_bps) AS avg_slippage
            FROM feedback_data
            WHERE symbol = $1
              AND time >= NOW() - make_interval(days => $2)
            GROUP BY hour
            ORDER BY hour
            """,
            symbol,
            days,
        )
        return {int(r["hour"]): float(r["avg_slippage"]) for r in rows}

    async def get_strategy_comparison(
        self,
        symbol: str,
        lookback_hours: int = 24,
    ) -> dict[str, FeedbackSummary]:
        """전략별 피드백 비교 (SCALP vs SWING)."""
        rows = await self._pool.fetch(
            """
            SELECT
                strategy_tag,
                AVG(slippage_bps) AS avg_slippage_bps,
                AVG(impact_bps) AS avg_impact_bps,
                AVG(quality_score) AS avg_quality_score,
                AVG(fill_latency_ms) AS avg_fill_latency_ms,
                AVG(fill_ratio) AS avg_fill_ratio,
                COUNT(*) AS sample_count
            FROM feedback_data
            WHERE symbol = $1
              AND time >= NOW() - make_interval(hours => $2)
              AND strategy_tag != ''
            GROUP BY strategy_tag
            ORDER BY strategy_tag
            """,
            symbol,
            lookback_hours,
        )
        result: dict[str, FeedbackSummary] = {}
        for r in rows:
            result[r["strategy_tag"]] = FeedbackSummary(
                avg_slippage_bps=float(r["avg_slippage_bps"]),
                avg_market_impact_bps=float(r["avg_impact_bps"]),
                avg_quality_score=float(r["avg_quality_score"]),
                avg_fill_latency_ms=float(r["avg_fill_latency_ms"]),
                avg_fill_ratio=float(r["avg_fill_ratio"]),
                sample_count=int(r["sample_count"]),
            )
        return result

    async def get_quality_trend(
        self,
        symbol: str,
        days: int = 7,
    ) -> list[dict]:
        """일별 품질 점수 추이."""
        rows = await self._pool.fetch(
            """
            SELECT
                time_bucket('1 day', time) AS day,
                AVG(quality_score) AS avg_quality,
                AVG(slippage_bps) AS avg_slippage,
                COUNT(*) AS sample_count
            FROM feedback_data
            WHERE symbol = $1
              AND time >= NOW() - make_interval(days => $2)
            GROUP BY day
            ORDER BY day
            """,
            symbol,
            days,
        )
        return [
            {
                "day": r["day"].isoformat(),
                "avg_quality": float(r["avg_quality"]),
                "avg_slippage": float(r["avg_slippage"]),
                "sample_count": int(r["sample_count"]),
            }
            for r in rows
        ]

    async def get_degradation_alert(
        self,
        symbol: str,
    ) -> Optional[dict]:
        """최근 1시간 vs 일평균 비교 → 열화 경고.

        최근 1시간 슬리피지가 일평균의 1.5배 이상이면 경고.
        """
        row = await self._pool.fetchrow(
            """
            WITH recent AS (
                SELECT AVG(slippage_bps) AS avg_slippage, COUNT(*) AS cnt
                FROM feedback_data
                WHERE symbol = $1
                  AND time >= NOW() - INTERVAL '1 hour'
            ),
            daily AS (
                SELECT AVG(slippage_bps) AS avg_slippage, COUNT(*) AS cnt
                FROM feedback_data
                WHERE symbol = $1
                  AND time >= NOW() - INTERVAL '24 hours'
            )
            SELECT
                r.avg_slippage AS recent_slippage,
                r.cnt AS recent_count,
                d.avg_slippage AS daily_slippage,
                d.cnt AS daily_count
            FROM recent r, daily d
            """,
            symbol,
        )
        if row is None:
            return None

        recent_count = row["recent_count"] or 0
        daily_count = row["daily_count"] or 0

        if recent_count < 3 or daily_count < 5:
            return None

        recent_slippage = float(row["recent_slippage"] or 0)
        daily_slippage = float(row["daily_slippage"] or 0)

        if daily_slippage <= 0:
            return None

        ratio = recent_slippage / daily_slippage
        if ratio >= 1.5:
            return {
                "symbol": symbol,
                "alert_type": "SLIPPAGE_DEGRADATION",
                "recent_slippage_bps": round(recent_slippage, 2),
                "daily_slippage_bps": round(daily_slippage, 2),
                "degradation_ratio": round(ratio, 2),
                "recent_sample_count": recent_count,
            }
        return None
