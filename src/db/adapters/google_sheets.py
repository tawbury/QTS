"""
Google Sheets 데이터 소스 어댑터.

근거: docs/arch/sub/18_Data_Layer_Architecture.md §4.3
- 기존 GoogleSheetsClient + RepositoryManager를 DataSourceAdapter 인터페이스로 래핑
- 틱 데이터는 미지원 (NotImplementedError)
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from src.db.adapters.interface import DataSourceAdapter
from src.db.contracts import (
    HealthStatus,
    LedgerEntry,
    OHLCV,
    Position,
    TickData,
)

logger = logging.getLogger(__name__)


def _safe_decimal(value: str | None, default: str = "0") -> Decimal:
    """문자열을 안전하게 Decimal로 변환."""
    if not value or str(value).strip() == "":
        return Decimal(default)
    try:
        cleaned = str(value).replace(",", "").strip()
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return Decimal(default)


class GoogleSheetsAdapter(DataSourceAdapter):
    """Google Sheets 기반 DataSourceAdapter 구현.

    기존 RepositoryManager(Position, T_Ledger 리포지토리)를 래핑하여
    DataSourceAdapter 인터페이스를 제공한다.
    """

    def __init__(self, repository_manager) -> None:
        self._rm = repository_manager

    async def fetch_positions(self) -> list[Position]:
        repo = await self._rm.get_repository("Position")
        rows = await repo.get_all()
        return [self._row_to_position(r) for r in rows]

    async def fetch_position(self, symbol: str) -> Optional[Position]:
        repo = await self._rm.get_repository("Position")
        row = await repo.get_by_id(symbol)
        if row is None:
            return None
        return self._row_to_position(row)

    async def update_position(
        self, symbol: str, qty: Decimal, avg_price: Decimal
    ) -> bool:
        repo = await self._rm.get_repository("Position")
        await repo.upsert_position({
            "symbol": symbol,
            "qty": str(qty),
            "avg_price_current_currency": str(avg_price),
        })
        return True

    async def append_ledger(self, entry: LedgerEntry) -> bool:
        repo = await self._rm.get_repository("T_Ledger")
        await repo.append_trade({
            "timestamp": entry.timestamp.isoformat(),
            "symbol": entry.symbol,
            "side": entry.side,
            "qty": str(entry.qty),
            "price": str(entry.price),
            "amount_krw": str(entry.amount),
            "fee_tax": str(entry.fee),
            "strategy": entry.strategy_tag,
            "order_id": entry.order_id,
            "broker": entry.broker,
        })
        return True

    async def fetch_ledger(
        self,
        symbol: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[LedgerEntry]:
        repo = await self._rm.get_repository("T_Ledger")

        if symbol:
            rows = await repo.get_by_symbol(symbol)
        else:
            rows = await repo.get_all()

        entries: list[LedgerEntry] = []
        for r in rows:
            entry = self._row_to_ledger(r)
            if entry is None:
                continue
            if start and entry.timestamp < start:
                continue
            if end and entry.timestamp >= end:
                continue
            entries.append(entry)

        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]

    async def fetch_ohlcv(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> list[OHLCV]:
        # Google Sheets는 OHLCV 시계열 데이터 미지원
        raise NotImplementedError(
            "Google Sheets does not support OHLCV time-series data"
        )

    async def fetch_tick_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> list[TickData]:
        # Google Sheets는 틱 데이터 미지원
        raise NotImplementedError(
            "Google Sheets does not support tick data"
        )

    async def health_check(self) -> HealthStatus:
        start_t = time.monotonic()
        try:
            health = await self._rm.health_check()
            latency = (time.monotonic() - start_t) * 1000
            is_healthy = health.get("status") == "healthy"
            return HealthStatus(
                healthy=is_healthy,
                source="google_sheets",
                latency_ms=latency,
                error="" if is_healthy else health.get("error", "unknown"),
            )
        except Exception as e:
            latency = (time.monotonic() - start_t) * 1000
            return HealthStatus(
                healthy=False,
                source="google_sheets",
                latency_ms=latency,
                error=str(e),
            )

    # --- 변환 헬퍼 ---

    @staticmethod
    def _row_to_position(row: dict) -> Position:
        """Sheets 행 → Position 계약 변환."""
        return Position(
            symbol=str(row.get("symbol", "")),
            qty=_safe_decimal(row.get("qty")),
            avg_price=_safe_decimal(row.get("avg_price_current_currency")),
            market=str(row.get("market", "")),
            exposure_value=_safe_decimal(row.get("market_value_krw")),
            exposure_pct=Decimal("0"),
            unrealized_pnl=_safe_decimal(row.get("unrealized_pnl_krw")),
        )

    @staticmethod
    def _row_to_ledger(row: dict) -> Optional[LedgerEntry]:
        """Sheets 행 → LedgerEntry 계약 변환."""
        ts_str = row.get("timestamp", "")
        if not ts_str:
            return None
        try:
            ts = datetime.fromisoformat(str(ts_str))
        except (ValueError, TypeError):
            return None

        side_raw = str(row.get("side", "")).upper()
        if side_raw not in ("BUY", "SELL"):
            return None

        return LedgerEntry(
            timestamp=ts,
            symbol=str(row.get("symbol", "")),
            side=side_raw,
            qty=_safe_decimal(row.get("qty")),
            price=_safe_decimal(row.get("price")),
            amount=_safe_decimal(row.get("amount_krw")),
            fee=_safe_decimal(row.get("fee_tax")),
            strategy_tag=str(row.get("strategy", "")),
            order_id=str(row.get("order_id", "")),
            broker=str(row.get("broker", "")),
        )
