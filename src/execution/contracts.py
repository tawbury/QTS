"""Scalp Execution 데이터 계약."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional

from src.provider.models.order_request import OrderSide, OrderType


# ---------------------------------------------------------------------------
# Execution State Machine
# ---------------------------------------------------------------------------

class ExecutionState(str, Enum):
    """실행 상태 머신 (10 states)."""

    INIT = "INIT"
    PRECHECK = "PRECHECK"
    SPLITTING = "SPLITTING"
    SENDING = "SENDING"
    MONITORING = "MONITORING"
    ADJUSTING = "ADJUSTING"
    ESCAPING = "ESCAPING"
    COMPLETE = "COMPLETE"
    ESCAPED = "ESCAPED"
    FAILED = "FAILED"


TERMINAL_STATES = frozenset({
    ExecutionState.COMPLETE,
    ExecutionState.ESCAPED,
    ExecutionState.FAILED,
})

STATE_TRANSITIONS: dict[ExecutionState, list[ExecutionState]] = {
    ExecutionState.INIT: [ExecutionState.PRECHECK],
    ExecutionState.PRECHECK: [ExecutionState.SPLITTING, ExecutionState.FAILED, ExecutionState.ESCAPING],
    ExecutionState.SPLITTING: [ExecutionState.SENDING, ExecutionState.FAILED, ExecutionState.ESCAPING],
    ExecutionState.SENDING: [ExecutionState.MONITORING, ExecutionState.FAILED, ExecutionState.ESCAPING],
    ExecutionState.MONITORING: [ExecutionState.COMPLETE, ExecutionState.ADJUSTING, ExecutionState.ESCAPING],
    ExecutionState.ADJUSTING: [ExecutionState.MONITORING, ExecutionState.ESCAPING],
    ExecutionState.ESCAPING: [ExecutionState.ESCAPED],
    ExecutionState.COMPLETE: [],
    ExecutionState.ESCAPED: [],
    ExecutionState.FAILED: [],
}

STAGE_TIMEOUTS_MS: dict[str, int] = {
    "PRECHECK": 5_000,
    "SPLITTING": 1_000,
    "SENDING": 10_000,
    "MONITORING": 60_000,
    "ADJUSTING": 30_000,
    "ESCAPING": 30_000,
}


# ---------------------------------------------------------------------------
# Split Strategies
# ---------------------------------------------------------------------------

class SplitStrategy(str, Enum):
    """주문 분할 전략."""

    SINGLE = "SINGLE"
    TWAP = "TWAP"
    VWAP = "VWAP"
    ICEBERG = "ICEBERG"


# ---------------------------------------------------------------------------
# Order Decision (Pipeline Input)
# ---------------------------------------------------------------------------

@dataclass
class OrderDecision:
    """ETEDA Decide → Execution 파이프라인 입력."""

    symbol: str
    side: OrderSide
    qty: int
    price: Optional[Decimal] = None
    order_type: OrderType = OrderType.LIMIT
    strategy_id: str = ""
    urgency: str = "NORMAL"  # NORMAL / URGENT
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if self.qty <= 0:
            raise ValueError(f"qty must be positive, got {self.qty}")
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("LIMIT order requires price")


# ---------------------------------------------------------------------------
# Split Order
# ---------------------------------------------------------------------------

class SplitOrderStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


@dataclass
class SplitOrder:
    """분할 주문."""

    split_id: str
    parent_order_id: str
    sequence: int
    symbol: str
    side: OrderSide
    qty: int
    price: Optional[Decimal] = None
    price_type: OrderType = OrderType.LIMIT
    status: SplitOrderStatus = SplitOrderStatus.PENDING
    broker_order_id: str = ""
    filled_qty: int = 0
    avg_fill_price: Optional[Decimal] = None
    scheduled_time: Optional[datetime] = None
    max_wait_ms: int = 5_000

    @property
    def remaining_qty(self) -> int:
        return self.qty - self.filled_qty

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            SplitOrderStatus.FILLED,
            SplitOrderStatus.CANCELLED,
            SplitOrderStatus.FAILED,
        )


# ---------------------------------------------------------------------------
# Fill Event
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FillEvent:
    """체결 이벤트."""

    order_id: str
    symbol: str
    side: OrderSide
    filled_qty: int
    filled_price: Decimal
    cumulative_qty: int = 0
    remaining_qty: int = 0
    fee: Decimal = Decimal("0")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Broker Protocol
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OrderAck:
    """주문 접수 응답."""

    accepted: bool
    order_id: str = ""
    reject_reason: str = ""


@dataclass(frozen=True)
class ModifyAck:
    """주문 수정 응답."""

    accepted: bool
    order_id: str = ""
    reject_reason: str = ""


@dataclass(frozen=True)
class CancelAck:
    """주문 취소 응답."""

    accepted: bool
    order_id: str = ""
    reject_reason: str = ""


# ---------------------------------------------------------------------------
# Stage Results
# ---------------------------------------------------------------------------

@dataclass
class PreCheckResult:
    """PreCheck 결과."""

    passed: bool
    reason: str = ""
    order: Optional[OrderDecision] = None
    adjusted_qty: Optional[int] = None


@dataclass
class SplitResult:
    """OrderSplit 결과."""

    strategy: SplitStrategy
    splits: list[SplitOrder] = field(default_factory=list)

    @property
    def total_qty(self) -> int:
        return sum(s.qty for s in self.splits)


@dataclass
class SendResult:
    """AsyncSend 결과."""

    sent_count: int = 0
    failed_count: int = 0
    orders: list[SplitOrder] = field(default_factory=list)


@dataclass
class MonitorResult:
    """PartialFillMonitor 결과."""

    status: str = "COMPLETE"  # COMPLETE / TIMEOUT / PARTIAL / NEEDS_ADJUSTMENT
    filled_qty: int = 0
    remaining_qty: int = 0
    fills: list[FillEvent] = field(default_factory=list)


@dataclass
class AdjustAction:
    """가격 조정 액션."""

    action: str  # PRICE_IMPROVE / CONVERT_MARKET / REDUCE_QTY / WAIT
    order: Optional[SplitOrder] = None
    new_price: Optional[Decimal] = None
    new_qty: Optional[int] = None


@dataclass
class AdjustResult:
    """AdaptiveAdjust 결과."""

    adjustments: list[AdjustAction] = field(default_factory=list)


@dataclass
class EscapeResult:
    """EmergencyEscape 결과."""

    success: bool
    reason: str
    cancelled_count: int = 0
    liquidation_qty: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Execution Result (Pipeline Output)
# ---------------------------------------------------------------------------

@dataclass
class ExecutionResult:
    """파이프라인 최종 결과."""

    state: ExecutionState
    order_id: str
    symbol: str
    side: OrderSide
    requested_qty: int
    filled_qty: int = 0
    avg_fill_price: Optional[Decimal] = None
    splits_count: int = 0
    alerts: list[ExecutionAlert] = field(default_factory=list)
    escape_result: Optional[EscapeResult] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def fill_rate(self) -> float:
        if self.requested_qty == 0:
            return 0.0
        return self.filled_qty / self.requested_qty


# ---------------------------------------------------------------------------
# Execution Alert
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExecutionAlert:
    """실행 안전 알림."""

    code: str  # FS090-095 or GR060-064
    severity: str  # FAIL_SAFE / GUARDRAIL / WARNING
    message: str
    stage: str = ""


# ---------------------------------------------------------------------------
# Slippage / Split Config
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SlippageConfig:
    """슬리피지 설정."""

    max_slippage_pct: Decimal = Decimal("0.005")
    price_improve_step_pct: Decimal = Decimal("0.001")
    max_adjustment_rounds: int = 3
    adjust_interval_ms: int = 1_000


@dataclass(frozen=True)
class SplitConfig:
    """분할 설정."""

    min_split_qty: int = 100
    max_splits: int = 20
    default_strategy: SplitStrategy = SplitStrategy.SINGLE
    twap_num_buckets: int = 5
    iceberg_visible_pct: Decimal = Decimal("0.3")


# ---------------------------------------------------------------------------
# Execution Context
# ---------------------------------------------------------------------------

@dataclass
class ExecutionContext:
    """실행 컨텍스트 (파이프라인 전체에서 공유)."""

    order: OrderDecision
    state: ExecutionState = ExecutionState.INIT
    splits: list[SplitOrder] = field(default_factory=list)
    fills: list[FillEvent] = field(default_factory=list)
    alerts: list[ExecutionAlert] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stage_start_time: Optional[datetime] = None
    adjustment_count: int = 0

    @property
    def total_filled_qty(self) -> int:
        return sum(f.filled_qty for f in self.fills)

    @property
    def pending_orders(self) -> list[SplitOrder]:
        return [s for s in self.splits if s.status == SplitOrderStatus.SENT]

    @property
    def has_position(self) -> bool:
        return self.total_filled_qty > 0

    def add_alert(self, alert: ExecutionAlert) -> None:
        self.alerts.append(alert)
