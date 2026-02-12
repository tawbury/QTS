"""Micro Risk Loop 데이터 계약.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §2, §3
- PositionShadow: 메인 포지션의 미러링 상태
- PriceFeed: 실시간 가격 틱
- MarketData: 시장 전체 데이터 (VIX, 변동성)
- MicroRiskAction: 리스크 평가 결과 액션
- Config dataclasses: 각 규칙 설정
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Optional


# --- Action Types (§2.5.2) ---

class ActionType(str, Enum):
    """Micro Risk 액션 타입."""

    TRAILING_STOP_ADJUST = "TRAILING_STOP_ADJUST"
    PARTIAL_EXIT = "PARTIAL_EXIT"
    FULL_EXIT = "FULL_EXIT"
    POSITION_FREEZE = "POSITION_FREEZE"
    ETEDA_SUSPEND = "ETEDA_SUSPEND"
    KILL_SWITCH = "KILL_SWITCH"


# 단락 평가 대상: KILL_SWITCH 또는 FULL_EXIT 시 나머지 규칙 스킵
SHORT_CIRCUIT_ACTIONS = frozenset({ActionType.KILL_SWITCH, ActionType.FULL_EXIT})


# --- MicroRiskAction (§2.5.2) ---

@dataclass(frozen=True)
class MicroRiskAction:
    """리스크 규칙 평가 결과 액션."""

    action_type: ActionType
    symbol: str
    payload: dict[str, Any] = field(default_factory=dict)
    priority: str = "P0"


# --- Strategy Type ---

class StrategyType(str, Enum):
    """전략 유형."""

    SCALP = "SCALP"
    SWING = "SWING"
    PORTFOLIO = "PORTFOLIO"


# --- PositionShadow (§2.2.2) ---

@dataclass
class PositionShadow:
    """포지션 섀도우 상태. 메인 포지션의 non-blocking 미러."""

    symbol: str
    qty: int
    avg_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal = Decimal("0")
    unrealized_pnl_pct: Decimal = Decimal("0")

    # Local fields (Micro Loop only)
    entry_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    time_in_trade_sec: int = 0
    highest_price_since_entry: Decimal = Decimal("0")
    lowest_price_since_entry: Decimal = Decimal("0")
    mae_pct: Decimal = Decimal("0")
    mfe_pct: Decimal = Decimal("0")

    trailing_stop_active: bool = False
    trailing_stop_price: Decimal = Decimal("0")
    last_sync_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    strategy: StrategyType = StrategyType.SCALP

    def __post_init__(self) -> None:
        if self.highest_price_since_entry == Decimal("0"):
            self.highest_price_since_entry = self.current_price
        if self.lowest_price_since_entry == Decimal("0"):
            self.lowest_price_since_entry = self.current_price

    def update_extremes(self, price: Decimal) -> None:
        """고가/저가 업데이트 및 MAE/MFE 재계산."""
        if price > self.highest_price_since_entry:
            self.highest_price_since_entry = price
        if price < self.lowest_price_since_entry:
            self.lowest_price_since_entry = price
        self._recalc_mae_mfe()

    def update_pnl(self) -> None:
        """PnL 재계산."""
        if self.avg_price > 0 and self.qty != 0:
            if self.qty > 0:  # Long
                self.unrealized_pnl = (self.current_price - self.avg_price) * self.qty
            else:  # Short
                self.unrealized_pnl = (self.avg_price - self.current_price) * abs(self.qty)
            self.unrealized_pnl_pct = (
                (self.current_price - self.avg_price) / self.avg_price
                if self.qty > 0
                else (self.avg_price - self.current_price) / self.avg_price
            )
        else:
            self.unrealized_pnl = Decimal("0")
            self.unrealized_pnl_pct = Decimal("0")

    def _recalc_mae_mfe(self) -> None:
        """MAE/MFE 재계산."""
        if self.avg_price <= 0:
            return
        if self.qty > 0:  # Long
            self.mae_pct = (self.lowest_price_since_entry - self.avg_price) / self.avg_price
            self.mfe_pct = (self.highest_price_since_entry - self.avg_price) / self.avg_price
        else:  # Short
            self.mae_pct = (self.avg_price - self.highest_price_since_entry) / self.avg_price
            self.mfe_pct = (self.avg_price - self.lowest_price_since_entry) / self.avg_price


# --- PriceFeed (§2.3.2) ---

@dataclass(frozen=True)
class PriceFeed:
    """실시간 가격 틱."""

    symbol: str
    price: Decimal
    bid: Decimal
    ask: Decimal
    volume: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "BROKER_KIS"


# --- MarketData (Volatility) ---

@dataclass
class MarketData:
    """시장 전체 데이터 (변동성 킬스위치용)."""

    vix: Decimal = Decimal("20")
    realized_volatility: Decimal = Decimal("0.02")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# --- Config Dataclasses (§3) ---

@dataclass(frozen=True)
class TrailingStopConfig:
    """트레일링 스탑 설정 (§3.1.2)."""

    activation_profit_pct: Decimal = Decimal("0.01")
    trail_distance_pct: Decimal = Decimal("0.005")
    min_trail_distance: Decimal = Decimal("500")
    ratchet_only: bool = True


@dataclass(frozen=True)
class MAEConfig:
    """MAE 설정 (§3.2.2)."""

    position_mae_threshold_pct: Decimal = Decimal("0.02")
    partial_exit_at_pct: Decimal = Decimal("0.015")
    partial_exit_ratio: Decimal = Decimal("0.50")


@dataclass(frozen=True)
class TimeInTradeConfig:
    """보유 시간 설정 (§3.3.2)."""

    scalp_max_time_sec: int = 3600
    swing_max_time_sec: int = 604800
    portfolio_max_time_sec: Optional[int] = None
    warning_at_pct: Decimal = Decimal("0.80")
    extension_profitable: bool = True
    extension_time_sec: int = 1800

    def get_max_time(self, strategy: StrategyType) -> Optional[int]:
        """전략별 최대 보유 시간."""
        if strategy == StrategyType.SCALP:
            return self.scalp_max_time_sec
        if strategy == StrategyType.SWING:
            return self.swing_max_time_sec
        return self.portfolio_max_time_sec


@dataclass(frozen=True)
class VolatilityKillSwitchConfig:
    """변동성 킬스위치 설정 (§3.4.2)."""

    vix_warning_level: Decimal = Decimal("25")
    vix_critical_level: Decimal = Decimal("30")
    vix_kill_level: Decimal = Decimal("40")
    realized_vol_warning: Decimal = Decimal("0.03")
    realized_vol_critical: Decimal = Decimal("0.05")
    realized_vol_kill: Decimal = Decimal("0.08")
    critical_exit_ratio: Decimal = Decimal("0.50")


@dataclass(frozen=True)
class MicroRiskConfig:
    """Micro Risk Loop 전체 설정."""

    loop_interval_ms: int = 100
    max_positions_monitored: int = 100
    max_consecutive_errors: int = 3
    trailing_stop: TrailingStopConfig = field(default_factory=TrailingStopConfig)
    mae: MAEConfig = field(default_factory=MAEConfig)
    time_in_trade: TimeInTradeConfig = field(default_factory=TimeInTradeConfig)
    volatility: VolatilityKillSwitchConfig = field(default_factory=VolatilityKillSwitchConfig)


# --- MicroRiskAlert ---

@dataclass(frozen=True)
class MicroRiskAlert:
    """Micro Risk 경고/알림."""

    code: str
    message: str
    severity: str = "WARNING"  # WARNING / CRITICAL
    meta: dict[str, Any] = field(default_factory=dict)


# --- Sync Config (§2.2.3) ---

SYNC_FIELDS = frozenset({
    "qty", "avg_price", "current_price",
    "unrealized_pnl", "unrealized_pnl_pct",
})

LOCAL_FIELDS = frozenset({
    "time_in_trade_sec", "highest_price_since_entry",
    "lowest_price_since_entry", "mae_pct", "mfe_pct",
    "trailing_stop_active", "trailing_stop_price",
})
