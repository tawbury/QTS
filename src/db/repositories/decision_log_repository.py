"""DecisionLogRepository - 의사결정 감사 추적 저장소.

근거: docs/02-design/features/eteda-db-feedback-loop.design.md D-04
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from src.db.contracts import DecisionLogEntry

logger = logging.getLogger(__name__)


class DecisionLogRepository:
    """TimescaleDB 기반 의사결정 감사 추적."""

    def __init__(self, pool: Any) -> None:
        self._pool = pool  # asyncpg.Pool

    async def store(self, entry: DecisionLogEntry) -> None:
        """의사결정 로그 저장."""
        metadata_json = json.dumps(entry.metadata) if entry.metadata else None

        await self._pool.execute(
            """
            INSERT INTO decision_log
            (time, cycle_id, symbol, action, strategy_tag,
             price, qty, signal_confidence, risk_score,
             operating_state, feedback_applied,
             feedback_slippage_bps, feedback_quality_score,
             capital_blocked, approved, reason, act_status, metadata)
            VALUES (NOW(), $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            """,
            entry.cycle_id,
            entry.symbol,
            entry.action,
            entry.strategy_tag,
            entry.price,
            entry.qty,
            entry.signal_confidence,
            entry.risk_score,
            entry.operating_state,
            entry.feedback_applied,
            entry.feedback_slippage_bps,
            entry.feedback_quality_score,
            entry.capital_blocked,
            entry.approved,
            entry.reason,
            entry.act_status,
            metadata_json,
        )

    async def fetch_by_symbol(
        self,
        symbol: str,
        limit: int = 50,
    ) -> list[dict]:
        """종목별 의사결정 이력 조회."""
        rows = await self._pool.fetch(
            """
            SELECT time, cycle_id, symbol, action, strategy_tag,
                   price, qty, signal_confidence, risk_score,
                   operating_state, feedback_applied, approved, reason, act_status
            FROM decision_log
            WHERE symbol = $1
            ORDER BY time DESC
            LIMIT $2
            """,
            symbol,
            limit,
        )
        return [dict(r) for r in rows]

    async def correlate_with_feedback(
        self,
        symbol: str,
        lookback_hours: int = 24,
    ) -> list[dict]:
        """Decision + Feedback JOIN: 의사결정-실행 품질 상관 분석."""
        rows = await self._pool.fetch(
            """
            SELECT
                d.time, d.cycle_id, d.action, d.strategy_tag,
                d.price, d.qty, d.signal_confidence, d.approved, d.reason,
                f.slippage_bps, f.quality_score, f.impact_bps, f.fill_latency_ms
            FROM decision_log d
            LEFT JOIN LATERAL (
                SELECT slippage_bps, quality_score, impact_bps, fill_latency_ms
                FROM feedback_data f
                WHERE f.symbol = d.symbol
                  AND f.time BETWEEN d.time AND d.time + INTERVAL '5 minutes'
                ORDER BY f.time
                LIMIT 1
            ) f ON TRUE
            WHERE d.symbol = $1
              AND d.time >= NOW() - make_interval(hours => $2)
            ORDER BY d.time DESC
            """,
            symbol,
            lookback_hours,
        )
        return [dict(r) for r in rows]
