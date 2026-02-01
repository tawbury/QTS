from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class OrderStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class OrderResponse:
    status: OrderStatus
    broker_order_id: Optional[str] = None
    message: Optional[str] = None

    filled_qty: int = 0
    avg_fill_price: Optional[float] = None

    # Broker raw payload is allowed ONLY as opaque debug info
    raw: Optional[Dict[str, Any]] = None
