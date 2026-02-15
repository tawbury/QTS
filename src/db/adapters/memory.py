"""
인메모리 데이터 소스 어댑터.

테스트 및 로컬 개발용. 모든 데이터를 dict에 보관.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from src.db.contracts import (
    DecisionLogEntry,
    HealthStatus,
    LedgerEntry,
    OHLCV,
    Position,
    TickData,
)
from src.db.adapters.interface import DataSourceAdapter
from src.feedback.contracts import FeedbackData


class InMemoryAdapter(DataSourceAdapter):
    """인메모리 데이터 소스."""

    def __init__(self) -> None:
        self._positions: dict[str, Position] = {}
        self._ledger: list[LedgerEntry] = []
        self._ohlcv: list[OHLCV] = []
        self._ticks: list[TickData] = []
        self._execution_logs: list[dict] = []
        self._feedbacks: list[FeedbackData] = []
        self._decision_logs: list[DecisionLogEntry] = []

    async def fetch_positions(self) -> list[Position]:
        return list(self._positions.values())

    async def fetch_position(self, symbol: str) -> Optional[Position]:
        return self._positions.get(symbol)

    async def update_position(
        self, symbol: str, qty: Decimal, avg_price: Decimal
    ) -> bool:
        existing = self._positions.get(symbol)
        self._positions[symbol] = Position(
            symbol=symbol,
            qty=qty,
            avg_price=avg_price,
            market=existing.market if existing else "",
            exposure_value=existing.exposure_value if existing else Decimal("0"),
            exposure_pct=existing.exposure_pct if existing else Decimal("0"),
            unrealized_pnl=existing.unrealized_pnl if existing else Decimal("0"),
        )
        return True

    async def append_ledger(self, entry: LedgerEntry) -> bool:
        self._ledger.append(entry)
        return True

    async def fetch_ledger(
        self,
        symbol: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[LedgerEntry]:
        result = self._ledger
        if symbol:
            result = [e for e in result if e.symbol == symbol]
        if start:
            result = [e for e in result if e.timestamp >= start]
        if end:
            result = [e for e in result if e.timestamp < end]
        result = sorted(result, key=lambda e: e.timestamp, reverse=True)
        return result[:limit]

    async def fetch_ohlcv(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> list[OHLCV]:
        return [
            o
            for o in self._ohlcv
            if o.symbol == symbol and start <= o.time < end
        ]

    async def fetch_tick_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> list[TickData]:
        return [
            t
            for t in self._ticks
            if t.symbol == symbol and start <= t.time < end
        ]

    async def store_execution_log(
        self,
        order_id: str,
        symbol: str,
        stage: str,
        latency_ms: float,
        success: bool,
        error_code: Optional[str] = None,
    ) -> bool:
        """실행 로그 저장."""
        self._execution_logs.append({
            "time": datetime.now(timezone.utc),
            "order_id": order_id,
            "symbol": symbol,
            "stage": stage,
            "latency_ms": latency_ms,
            "success": success,
            "error_code": error_code,
        })
        return True

    async def fetch_execution_logs(
        self,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        order_id: Optional[str] = None,
        limit: int = 1000,
    ) -> list[dict]:
        """실행 로그 조회."""
        logs = self._execution_logs
        if order_id:
            logs = [log for log in logs if log["order_id"] == order_id]
        if start:
            logs = [log for log in logs if log["time"] >= start]
        if end:
            logs = [log for log in logs if log["time"] < end]
        logs = sorted(logs, key=lambda x: x["time"], reverse=True)
        return logs[:limit]

    async def store_feedback(self, feedback: FeedbackData) -> bool:
        """피드백 데이터 저장."""
        self._feedbacks.append(feedback)
        return True

    async def fetch_feedback_summary(
        self, symbol: str, lookback_hours: int = 24
    ) -> dict:
        """시간 기반 롤링 피드백 집계."""
        matching = [f for f in self._feedbacks if f.symbol == symbol]
        if not matching:
            return {}
        return {
            "avg_slippage_bps": sum(f.total_slippage_bps for f in matching) / len(matching),
            "avg_market_impact_bps": sum(f.market_impact_bps for f in matching) / len(matching),
            "avg_quality_score": sum(f.execution_quality_score for f in matching) / len(matching),
            "avg_fill_latency_ms": sum(f.avg_fill_latency_ms for f in matching) / len(matching),
            "avg_fill_ratio": sum(f.partial_fill_ratio for f in matching) / len(matching),
            "sample_count": len(matching),
        }

    async def store_decision_log(self, entry: DecisionLogEntry) -> bool:
        """의사결정 로그 저장."""
        self._decision_logs.append(entry)
        return True

    async def health_check(self) -> HealthStatus:
        start = time.monotonic()
        _ = len(self._positions)
        latency = (time.monotonic() - start) * 1000
        return HealthStatus(
            healthy=True, source="in_memory", latency_ms=latency
        )

    # 테스트 헬퍼
    def seed_position(self, position: Position) -> None:
        """테스트용 포지션 삽입."""
        self._positions[position.symbol] = position

    def seed_ohlcv(self, data: list[OHLCV]) -> None:
        """테스트용 OHLCV 삽입."""
        self._ohlcv.extend(data)

    def seed_ticks(self, data: list[TickData]) -> None:
        """테스트용 틱 데이터 삽입."""
        self._ticks.extend(data)
