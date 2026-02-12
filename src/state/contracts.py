"""
운영 상태 데이터 계약.

근거: docs/arch/sub/18_System_State_Promotion_Architecture.md §2, §3
- AGGRESSIVE/BALANCED/DEFENSIVE 3가지 운영 상태
- 상태별 속성 (자본 배분, 리스크 허용치, 엔진 활성화)
- 전환 메트릭, 수동 오버라이드
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class OperatingState(str, Enum):
    """운영 상태. Safety State와 직교적 관계."""

    AGGRESSIVE = "AGGRESSIVE"
    BALANCED = "BALANCED"
    DEFENSIVE = "DEFENSIVE"


@dataclass(frozen=True)
class StateProperties:
    """각 운영 상태의 속성 (§2.2)."""

    scalp_allocation_range: tuple[float, float]
    swing_allocation_range: tuple[float, float]
    portfolio_allocation_range: tuple[float, float]
    risk_tolerance_multiplier: float
    entry_signal_threshold: float
    max_positions: int
    max_daily_trades: int
    rebalancing_enabled: bool
    new_entry_enabled: bool
    scalp_engine_active: bool
    swing_engine_active: bool


# 상태별 속성 정의 (§2.2)
STATE_PROPERTIES: dict[OperatingState, StateProperties] = {
    OperatingState.AGGRESSIVE: StateProperties(
        scalp_allocation_range=(0.60, 0.80),
        swing_allocation_range=(0.15, 0.30),
        portfolio_allocation_range=(0.05, 0.10),
        risk_tolerance_multiplier=1.2,
        entry_signal_threshold=0.6,
        max_positions=20,
        max_daily_trades=50,
        rebalancing_enabled=False,
        new_entry_enabled=True,
        scalp_engine_active=True,
        swing_engine_active=True,
    ),
    OperatingState.BALANCED: StateProperties(
        scalp_allocation_range=(0.30, 0.50),
        swing_allocation_range=(0.30, 0.40),
        portfolio_allocation_range=(0.20, 0.30),
        risk_tolerance_multiplier=1.0,
        entry_signal_threshold=0.7,
        max_positions=15,
        max_daily_trades=30,
        rebalancing_enabled=True,
        new_entry_enabled=True,
        scalp_engine_active=True,
        swing_engine_active=True,
    ),
    OperatingState.DEFENSIVE: StateProperties(
        scalp_allocation_range=(0.05, 0.15),
        swing_allocation_range=(0.15, 0.25),
        portfolio_allocation_range=(0.60, 0.80),
        risk_tolerance_multiplier=0.5,
        entry_signal_threshold=0.9,
        max_positions=10,
        max_daily_trades=10,
        rebalancing_enabled=True,
        new_entry_enabled=False,
        scalp_engine_active=False,
        swing_engine_active=True,
    ),
}


@dataclass(frozen=True)
class TransitionMetrics:
    """상태 전환 판단에 사용되는 메트릭 (§3.1)."""

    drawdown_pct: float = 0.0
    vix: float = 0.0
    consecutive_scalp_losses: int = 0
    daily_loss_pct: float = 0.0
    market_circuit_breaker: bool = False
    consecutive_profitable_days: int = 0
    cagr: float = 0.0
    target_cagr: float = 0.0
    capital_growth_pct: float = 0.0
    win_rate_30d: float = 0.0


@dataclass(frozen=True)
class ManualOverride:
    """수동 오버라이드 (§4.1). 최대 7일 자동 만료."""

    override_state: OperatingState
    override_reason: str
    operator_id: str
    override_time: datetime
    expiry_time: datetime
    auto_revert_state: OperatingState


@dataclass(frozen=True)
class OperatingStateSnapshot:
    """운영 상태 스냅샷 (로깅/UI용)."""

    current_state: OperatingState
    previous_state: Optional[OperatingState]
    transition_timestamp: Optional[datetime]
    transition_reason: Optional[str]
    manual_override: bool
    override_expiry: Optional[datetime]
    state_duration_days: float
    properties: StateProperties
