from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class MarketContext:
    symbol: str
    price: float  # Phase 5에서는 최소 입력만


@dataclass(frozen=True)
class ExecutionContext:
    # Loop/State에서 Strategy에 전달 가능한 최소 정보만
    position_qty: int
    cash: float


@dataclass(frozen=True)
class Intent:
    symbol: str
    side: str          # "BUY" | "SELL" (Phase 5 단순화)
    qty: int
    reason: str


class Strategy(Protocol):
    def generate_intents(
        self,
        market: MarketContext,
        execution: ExecutionContext,
    ) -> Sequence[Intent]:
        ...
