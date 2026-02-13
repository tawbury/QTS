"""
하이브리드 데이터 소스 어댑터 (Dual-Write).

근거: docs/arch/sub/18_Data_Layer_Architecture.md §4.4, §5
- 쓰기: primary + secondary 동시 (primary 실패 시 에러)
- 읽기: primary 우선, 실패 시 secondary fallback
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Optional

from src.db.contracts import (
    HealthStatus,
    LedgerEntry,
    OHLCV,
    Position,
    TickData,
)
from src.db.adapters.interface import DataSourceAdapter

logger = logging.getLogger(__name__)


class HybridAdapter(DataSourceAdapter):
    """Dual-Write 하이브리드 어댑터."""

    def __init__(
        self,
        primary: DataSourceAdapter,
        secondary: DataSourceAdapter,
    ) -> None:
        self._primary = primary
        self._secondary = secondary

    async def fetch_positions(self) -> list[Position]:
        try:
            return await self._primary.fetch_positions()
        except Exception as e:
            logger.warning("Primary fetch_positions failed: %s, fallback", e)
            return await self._secondary.fetch_positions()

    async def fetch_position(self, symbol: str) -> Optional[Position]:
        try:
            return await self._primary.fetch_position(symbol)
        except Exception as e:
            logger.warning("Primary fetch_position failed: %s, fallback", e)
            return await self._secondary.fetch_position(symbol)

    async def update_position(
        self, symbol: str, qty: Decimal, avg_price: Decimal
    ) -> bool:
        # Primary는 필수
        primary_ok = await self._primary.update_position(symbol, qty, avg_price)
        # Secondary는 best-effort
        try:
            await self._secondary.update_position(symbol, qty, avg_price)
        except Exception as e:
            logger.warning("Secondary update_position failed: %s", e)
        return primary_ok

    async def append_ledger(self, entry: LedgerEntry) -> bool:
        primary_ok = await self._primary.append_ledger(entry)
        try:
            await self._secondary.append_ledger(entry)
        except Exception as e:
            logger.warning("Secondary append_ledger failed: %s", e)
        return primary_ok

    async def fetch_ledger(
        self,
        symbol: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[LedgerEntry]:
        try:
            return await self._primary.fetch_ledger(symbol, start, end, limit)
        except Exception as e:
            logger.warning("Primary fetch_ledger failed: %s, fallback", e)
            return await self._secondary.fetch_ledger(symbol, start, end, limit)

    async def fetch_ohlcv(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> list[OHLCV]:
        try:
            return await self._primary.fetch_ohlcv(symbol, start, end, interval)
        except Exception as e:
            logger.warning("Primary fetch_ohlcv failed: %s, fallback", e)
            return await self._secondary.fetch_ohlcv(
                symbol, start, end, interval
            )

    async def fetch_tick_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> list[TickData]:
        try:
            return await self._primary.fetch_tick_data(symbol, start, end)
        except Exception as e:
            logger.warning("Primary fetch_tick_data failed: %s, fallback", e)
            return await self._secondary.fetch_tick_data(symbol, start, end)

    async def store_execution_log(
        self,
        order_id: str,
        symbol: str,
        stage: str,
        latency_ms: float,
        success: bool,
        error_code: Optional[str] = None,
    ) -> bool:
        """실행 로그 저장 — primary에 위임."""
        return await self._primary.store_execution_log(
            order_id, symbol, stage, latency_ms, success, error_code
        )

    async def fetch_execution_logs(
        self,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        order_id: Optional[str] = None,
        limit: int = 1000,
    ) -> list[dict]:
        """실행 로그 조회 — primary 우선, 실패 시 secondary fallback."""
        try:
            return await self._primary.fetch_execution_logs(
                start=start, end=end, order_id=order_id, limit=limit
            )
        except Exception as e:
            logger.warning(
                "Primary fetch_execution_logs failed: %s, fallback", e
            )
            return await self._secondary.fetch_execution_logs(
                start=start, end=end, order_id=order_id, limit=limit
            )

    async def health_check(self) -> HealthStatus:
        start = time.monotonic()
        p = await self._primary.health_check()
        s = await self._secondary.health_check()
        latency = (time.monotonic() - start) * 1000
        healthy = p.healthy  # primary 기준
        error = ""
        if not p.healthy:
            error = f"primary: {p.error}"
        if not s.healthy:
            error += f" secondary: {s.error}"
        return HealthStatus(
            healthy=healthy,
            source="hybrid",
            latency_ms=latency,
            error=error.strip(),
        )

    async def verify_consistency(
        self,
    ) -> list[str]:
        """Primary vs Secondary 포지션 일관성 검증 (§5.3)."""
        mismatches: list[str] = []
        primary_positions = await self._primary.fetch_positions()
        secondary_positions = await self._secondary.fetch_positions()

        secondary_map = {p.symbol: p for p in secondary_positions}
        for pp in primary_positions:
            sp = secondary_map.get(pp.symbol)
            if not sp:
                mismatches.append(f"Missing in secondary: {pp.symbol}")
            elif pp.qty != sp.qty or pp.avg_price != sp.avg_price:
                mismatches.append(
                    f"Mismatch {pp.symbol}: "
                    f"primary({pp.qty}, {pp.avg_price}) vs "
                    f"secondary({sp.qty}, {sp.avg_price})"
                )

        for sp in secondary_positions:
            if sp.symbol not in {p.symbol for p in primary_positions}:
                mismatches.append(f"Missing in primary: {sp.symbol}")

        return mismatches
