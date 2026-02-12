"""
자본 흐름 데이터 계약.

근거: docs/arch/sub/14_Capital_Flow_Architecture.md §2, §3, §4
- 3-Track 자본 풀 (Scalp/Swing/Portfolio)
- 풀 상태 계약 (CapitalPoolContract)
- 배분 제약 조건 (AllocationConstraints)
- 프로모션/디모션 기준 (PromotionCriteria, DemotionRule)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional


class PoolId(str, Enum):
    """자본 풀 식별자."""

    SCALP = "SCALP"
    SWING = "SWING"
    PORTFOLIO = "PORTFOLIO"


class PoolState(str, Enum):
    """풀 운영 상태."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    LOCKED = "LOCKED"


@dataclass
class CapitalPoolContract:
    """자본 풀 상태 계약 (§2.2)."""

    pool_id: PoolId
    total_capital: Decimal
    invested_capital: Decimal = Decimal("0")
    reserved_capital: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    accumulated_profit: Decimal = Decimal("0")
    allocation_pct: Decimal = Decimal("0")
    target_allocation_pct: Decimal = Decimal("0")
    pool_state: PoolState = PoolState.ACTIVE
    last_promotion_at: Optional[datetime] = None
    lock_reason: str = ""

    @property
    def available_capital(self) -> Decimal:
        """사용 가능 자본 = 총 자본 - 투자 중 - 예약."""
        return self.total_capital - self.invested_capital - self.reserved_capital

    @property
    def is_active(self) -> bool:
        return self.pool_state == PoolState.ACTIVE

    @property
    def is_locked(self) -> bool:
        return self.pool_state == PoolState.LOCKED

    def is_valid(self) -> bool:
        """풀 상태 유효성 검증."""
        if self.total_capital < 0:
            return False
        if self.invested_capital < 0:
            return False
        if self.reserved_capital < 0:
            return False
        if self.invested_capital + self.reserved_capital > self.total_capital:
            return False
        return True


@dataclass(frozen=True)
class AllocationConstraints:
    """풀별 배분 제약 조건 (§3.3)."""

    min_pct: Decimal
    max_pct: Decimal
    min_amount: Decimal


# 풀별 제약 조건 (§3.3)
POOL_CONSTRAINTS: dict[PoolId, AllocationConstraints] = {
    PoolId.SCALP: AllocationConstraints(
        min_pct=Decimal("0.05"),
        max_pct=Decimal("0.80"),
        min_amount=Decimal("1000000"),
    ),
    PoolId.SWING: AllocationConstraints(
        min_pct=Decimal("0.10"),
        max_pct=Decimal("0.50"),
        min_amount=Decimal("2000000"),
    ),
    PoolId.PORTFOLIO: AllocationConstraints(
        min_pct=Decimal("0.05"),
        max_pct=Decimal("0.80"),
        min_amount=Decimal("3000000"),
    ),
}


@dataclass(frozen=True)
class PromotionCriteria:
    """프로모션 조건 (§4.2, §4.3)."""

    min_accumulated_profit: Decimal
    min_sharpe_ratio: float
    min_win_rate_30d: float = 0.0
    min_trades_30d: int = 0
    max_mdd: float = 1.0
    transfer_ratio: Decimal = Decimal("0.50")
    min_transfer_amount: Decimal = Decimal("100000")
    max_transfer_amount: Decimal = Decimal("10000000")


# Scalp→Swing 프로모션 기준 (§4.2.1)
SCALP_TO_SWING_CRITERIA = PromotionCriteria(
    min_accumulated_profit=Decimal("1000000"),
    min_sharpe_ratio=1.5,
    min_win_rate_30d=0.55,
    min_trades_30d=50,
    max_mdd=0.10,
    transfer_ratio=Decimal("0.50"),
)

# Swing→Portfolio 프로모션 기준 (§4.3.1)
SWING_TO_PORTFOLIO_CRITERIA = PromotionCriteria(
    min_accumulated_profit=Decimal("5000000"),
    min_sharpe_ratio=1.2,
    max_mdd=0.15,
    transfer_ratio=Decimal("0.30"),
)


@dataclass(frozen=True)
class DemotionRule:
    """디모션 규칙 (§4.5)."""

    trigger_mdd: float
    transfer_ratio: Decimal
    trigger_consecutive_losses: int = 0


# 디모션 규칙 (§4.5)
DEMOTION_RULES: dict[str, DemotionRule] = {
    "portfolio_to_swing": DemotionRule(
        trigger_mdd=0.10,
        transfer_ratio=Decimal("0.20"),
    ),
    "swing_to_scalp": DemotionRule(
        trigger_mdd=0.15,
        transfer_ratio=Decimal("0.30"),
        trigger_consecutive_losses=5,
    ),
}


@dataclass(frozen=True)
class PerformanceMetrics:
    """성과 메트릭 (프로모션/디모션 판단용)."""

    sharpe_ratio: float = 0.0
    win_rate_30d: float = 0.0
    trades_30d: int = 0
    mdd_30d: float = 0.0
    mdd_90d: float = 0.0
    consecutive_losses: int = 0
    holding_period_avg: float = 0.0


@dataclass(frozen=True)
class CapitalTransfer:
    """자본 이전 기록 (§4.2.3)."""

    from_pool: PoolId
    to_pool: PoolId
    amount: Decimal
    reason: str
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass(frozen=True)
class CapitalAlert:
    """자본 경고 (§7.1, §7.2)."""

    code: str
    pool_id: Optional[PoolId]
    message: str
    severity: str  # "WARNING" | "CRITICAL"
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
