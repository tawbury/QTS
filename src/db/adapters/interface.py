"""
데이터 소스 어댑터 추상 인터페이스.

근거: docs/arch/sub/18_Data_Layer_Architecture.md §4.1
- fetch_positions, update_position, append_ledger, fetch_ohlcv, fetch_tick_data
- health_check
"""
from __future__ import annotations

from abc import ABC, abstractmethod
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


class DataSourceAdapter(ABC):
    """데이터 소스 추상 인터페이스."""

    @abstractmethod
    async def fetch_positions(self) -> list[Position]:
        """전체 포지션 조회."""

    @abstractmethod
    async def fetch_position(self, symbol: str) -> Optional[Position]:
        """단일 포지션 조회."""

    @abstractmethod
    async def update_position(
        self, symbol: str, qty: Decimal, avg_price: Decimal
    ) -> bool:
        """포지션 업데이트."""

    @abstractmethod
    async def append_ledger(self, entry: LedgerEntry) -> bool:
        """거래 원장 추가."""

    @abstractmethod
    async def fetch_ledger(
        self,
        symbol: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[LedgerEntry]:
        """거래 원장 조회."""

    @abstractmethod
    async def fetch_ohlcv(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> list[OHLCV]:
        """OHLCV 데이터 조회."""

    @abstractmethod
    async def fetch_tick_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> list[TickData]:
        """틱 데이터 조회."""

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """데이터 소스 상태 확인."""
