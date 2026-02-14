"""
데이터 레이어 계약.

근거: docs/arch/sub/18_Data_Layer_Architecture.md §3, §4
- Position, LedgerEntry, OHLCV, TickData 데이터 모델
- HealthStatus 공통 상태 모델
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal, Optional


@dataclass(frozen=True)
class Position:
    """포지션 데이터 (§3.1.1)."""

    symbol: str
    qty: Decimal
    avg_price: Decimal
    market: str = ""
    exposure_value: Decimal = Decimal("0")
    exposure_pct: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    updated_at: Optional[datetime] = None

    def to_cache_dict(self) -> dict[str, str]:
        """캐시 저장용 dict 변환."""
        return {
            "symbol": self.symbol,
            "qty": str(self.qty),
            "avg_price": str(self.avg_price),
            "market": self.market,
            "exposure_value": str(self.exposure_value),
            "exposure_pct": str(self.exposure_pct),
            "unrealized_pnl": str(self.unrealized_pnl),
            "updated_at": (
                str(int(self.updated_at.timestamp() * 1000))
                if self.updated_at
                else ""
            ),
        }

    @classmethod
    def from_cache_dict(cls, data: dict[str, str]) -> Position:
        """캐시 dict에서 Position 복원."""
        updated_at = None
        if data.get("updated_at"):
            ts_ms = int(data["updated_at"])
            updated_at = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        return cls(
            symbol=data["symbol"],
            qty=Decimal(data["qty"]),
            avg_price=Decimal(data["avg_price"]),
            market=data.get("market", ""),
            exposure_value=Decimal(data.get("exposure_value", "0")),
            exposure_pct=Decimal(data.get("exposure_pct", "0")),
            unrealized_pnl=Decimal(data.get("unrealized_pnl", "0")),
            updated_at=updated_at,
        )


@dataclass(frozen=True)
class LedgerEntry:
    """거래 원장 항목 (§3.1.2)."""

    timestamp: datetime
    symbol: str
    side: Literal["BUY", "SELL"]
    qty: Decimal
    price: Decimal
    amount: Decimal
    fee: Decimal = Decimal("0")
    strategy_tag: str = ""
    order_id: str = ""
    broker: str = ""
    id: Optional[int] = None


@dataclass(frozen=True)
class OHLCV:
    """OHLCV 봉 데이터 (§3.2.2)."""

    time: datetime
    symbol: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


@dataclass(frozen=True)
class TickData:
    """틱 데이터 (§3.2.1)."""

    time: datetime
    symbol: str
    price: Decimal
    volume: int
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    source: str = ""


@dataclass(frozen=True)
class HealthStatus:
    """데이터 소스/캐시 상태."""

    healthy: bool
    source: str
    latency_ms: float = 0.0
    error: str = ""
