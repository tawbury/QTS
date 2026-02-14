"""ExecutionLogRepository - 실행 로그 저장소.

근거: docs/02-design/features/eteda-db-feedback-loop.design.md D-05
기존 TimescaleDBAdapter.store_execution_log를 래핑하고 분석 쿼리 추가.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ExecutionLogRepository:
    """실행 로그 저장 및 분석."""

    def __init__(self, pool: Any) -> None:
        self._pool = pool  # asyncpg.Pool

    async def store(
        self,
        order_id: str,
        symbol: str,
        stage: str,
        latency_ms: float,
        success: bool,
        error_code: Optional[str] = None,
    ) -> None:
        """실행 로그 저장."""
        await self._pool.execute(
            """
            INSERT INTO execution_logs
            (time, order_id, symbol, stage, latency_ms, success, error_code)
            VALUES (NOW(), $1, $2, $3, $4, $5, $6)
            """,
            order_id,
            symbol,
            stage,
            latency_ms,
            success,
            error_code,
        )

    async def get_stage_latency_stats(
        self,
        hours: int = 1,
    ) -> dict[str, dict]:
        """스테이지별 P50/P95/P99 지연 시간 통계."""
        rows = await self._pool.fetch(
            """
            SELECT
                stage,
                COUNT(*) AS total,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms) AS p50,
                percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95,
                percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms) AS p99,
                AVG(latency_ms) AS avg_ms
            FROM execution_logs
            WHERE time >= NOW() - make_interval(hours => $1)
            GROUP BY stage
            ORDER BY stage
            """,
            hours,
        )
        return {
            row["stage"]: {
                "total": row["total"],
                "p50": float(row["p50"]),
                "p95": float(row["p95"]),
                "p99": float(row["p99"]),
                "avg_ms": float(row["avg_ms"]),
            }
            for row in rows
        }

    async def get_slow_stages(
        self,
        threshold_ms: float = 100.0,
        hours: int = 1,
    ) -> list[dict]:
        """SLO 위반 탐지 (threshold_ms 초과 건)."""
        rows = await self._pool.fetch(
            """
            SELECT time, order_id, symbol, stage, latency_ms, error_code
            FROM execution_logs
            WHERE time >= NOW() - make_interval(hours => $1)
              AND latency_ms > $2
            ORDER BY latency_ms DESC
            LIMIT 100
            """,
            hours,
            threshold_ms,
        )
        return [dict(r) for r in rows]
