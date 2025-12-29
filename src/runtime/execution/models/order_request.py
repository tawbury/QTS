from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: OrderSide
    qty: int
    order_type: OrderType
    limit_price: Optional[float] = None

    # Runtime-only metadata (no auth, no broker-specific params)
    client_order_id: Optional[str] = None
    dry_run: bool = True  # Phase 3: default True to enforce "no real order" in tests
