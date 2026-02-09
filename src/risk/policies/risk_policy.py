from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RiskStage(str, Enum):
    WARN = "warn"
    REDUCE = "reduce"
    BLOCK = "block"


@dataclass(frozen=True)
class RiskPolicy:
    """
    Phase 6: Strategy 단위 정책을 담는다.
    기본값은 보수적으로.
    """
    max_order_qty: int = 1
    stage: RiskStage = RiskStage.WARN
    reduce_to_qty: int = 1

    def __post_init__(self) -> None:
        if self.max_order_qty < 0:
            raise ValueError("max_order_qty must be >= 0")
        if self.reduce_to_qty < 0:
            raise ValueError("reduce_to_qty must be >= 0")
