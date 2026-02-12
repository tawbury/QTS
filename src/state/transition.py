"""
운영 상태 전환 규칙 엔진.

근거: docs/arch/sub/18_System_State_Promotion_Architecture.md §3
- AGGRESSIVE → BALANCED: Any 조건 (drawdown>5%, vix>25, losses>5, daily_loss>2%)
- BALANCED → DEFENSIVE: Any 조건 (drawdown>10%, vix>30, circuit breaker, safety WARNING+)
- DEFENSIVE → BALANCED: All 조건 (drawdown<5%, vix<20, profitable 3일+, safety NORMAL, 5일+)
- BALANCED → AGGRESSIVE: All 조건 (cagr>target, vix<15, growth>10%, win_rate>60%, 10일+)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from src.safety.state import SafetyState
from src.state.contracts import OperatingState, TransitionMetrics


class TransitionRule(ABC):
    """상태 전환 규칙 추상 클래스."""

    from_state: OperatingState
    to_state: OperatingState

    @abstractmethod
    def evaluate(
        self,
        metrics: TransitionMetrics,
        safety_state: SafetyState,
        state_duration_days: float,
    ) -> bool:
        """전환 조건 충족 여부. True면 전환 필요."""
        ...

    @abstractmethod
    def reason(self, metrics: TransitionMetrics) -> str:
        """전환 사유."""
        ...


class AggressiveToBalanced(TransitionRule):
    """AGGRESSIVE → BALANCED (Any 조건 충족 시)."""

    from_state = OperatingState.AGGRESSIVE
    to_state = OperatingState.BALANCED

    def evaluate(
        self,
        metrics: TransitionMetrics,
        safety_state: SafetyState,
        state_duration_days: float,
    ) -> bool:
        return (
            metrics.drawdown_pct > 0.05
            or metrics.vix > 25
            or metrics.consecutive_scalp_losses > 5
            or metrics.daily_loss_pct > 0.02
        )

    def reason(self, metrics: TransitionMetrics) -> str:
        reasons: list[str] = []
        if metrics.drawdown_pct > 0.05:
            reasons.append(f"drawdown={metrics.drawdown_pct:.1%}")
        if metrics.vix > 25:
            reasons.append(f"vix={metrics.vix}")
        if metrics.consecutive_scalp_losses > 5:
            reasons.append(f"consecutive_losses={metrics.consecutive_scalp_losses}")
        if metrics.daily_loss_pct > 0.02:
            reasons.append(f"daily_loss={metrics.daily_loss_pct:.1%}")
        return "AGGRESSIVE→BALANCED: " + ", ".join(reasons)


class BalancedToDefensive(TransitionRule):
    """BALANCED → DEFENSIVE (Any 조건 충족 시)."""

    from_state = OperatingState.BALANCED
    to_state = OperatingState.DEFENSIVE

    def evaluate(
        self,
        metrics: TransitionMetrics,
        safety_state: SafetyState,
        state_duration_days: float,
    ) -> bool:
        return (
            metrics.drawdown_pct > 0.10
            or metrics.vix > 30
            or metrics.market_circuit_breaker
            or safety_state in (SafetyState.WARNING, SafetyState.FAIL)
        )

    def reason(self, metrics: TransitionMetrics) -> str:
        reasons: list[str] = []
        if metrics.drawdown_pct > 0.10:
            reasons.append(f"drawdown={metrics.drawdown_pct:.1%}")
        if metrics.vix > 30:
            reasons.append(f"vix={metrics.vix}")
        if metrics.market_circuit_breaker:
            reasons.append("market_circuit_breaker")
        return "BALANCED→DEFENSIVE: " + ", ".join(reasons)


class DefensiveToBalanced(TransitionRule):
    """DEFENSIVE → BALANCED (All 조건 충족 시)."""

    from_state = OperatingState.DEFENSIVE
    to_state = OperatingState.BALANCED

    def evaluate(
        self,
        metrics: TransitionMetrics,
        safety_state: SafetyState,
        state_duration_days: float,
    ) -> bool:
        return (
            metrics.drawdown_pct < 0.05
            and metrics.vix < 20
            and metrics.consecutive_profitable_days >= 3
            and safety_state == SafetyState.NORMAL
            and state_duration_days >= 5
        )

    def reason(self, metrics: TransitionMetrics) -> str:
        return (
            f"DEFENSIVE→BALANCED: drawdown={metrics.drawdown_pct:.1%}, "
            f"vix={metrics.vix}, profitable_days={metrics.consecutive_profitable_days}"
        )


class BalancedToAggressive(TransitionRule):
    """BALANCED → AGGRESSIVE (All 조건 충족 시)."""

    from_state = OperatingState.BALANCED
    to_state = OperatingState.AGGRESSIVE

    def evaluate(
        self,
        metrics: TransitionMetrics,
        safety_state: SafetyState,
        state_duration_days: float,
    ) -> bool:
        return (
            metrics.cagr > metrics.target_cagr
            and metrics.vix < 15
            and metrics.capital_growth_pct > 0.10
            and metrics.win_rate_30d > 0.60
            and state_duration_days >= 10
        )

    def reason(self, metrics: TransitionMetrics) -> str:
        return (
            f"BALANCED→AGGRESSIVE: cagr={metrics.cagr:.1%}, "
            f"vix={metrics.vix}, growth={metrics.capital_growth_pct:.1%}, "
            f"win_rate={metrics.win_rate_30d:.1%}"
        )


# 모든 전환 규칙 목록 (평가 순서 = 위험 전환 우선)
ALL_TRANSITION_RULES: list[TransitionRule] = [
    BalancedToDefensive(),  # 위험: 먼저 평가
    AggressiveToBalanced(),
    DefensiveToBalanced(),
    BalancedToAggressive(),
]


@dataclass(frozen=True)
class HysteresisConfig:
    """Hysteresis 설정 (§3.3)."""

    min_duration_days: int


# 상태별 Hysteresis (§3.3)
HYSTERESIS: dict[OperatingState, HysteresisConfig] = {
    OperatingState.AGGRESSIVE: HysteresisConfig(min_duration_days=7),
    OperatingState.BALANCED: HysteresisConfig(min_duration_days=5),
    OperatingState.DEFENSIVE: HysteresisConfig(min_duration_days=3),
}

COOLDOWN_HOURS = 24
CONFIRMATION_CYCLES = 2  # 조건 2시간 연속 유지


def find_applicable_rule(
    current_state: OperatingState,
    metrics: TransitionMetrics,
    safety_state: SafetyState,
    state_duration_days: float,
) -> Optional[TransitionRule]:
    """현재 상태에서 충족되는 전환 규칙 찾기.

    위험 전환(→DEFENSIVE, →BALANCED) 우선 평가.
    """
    for rule in ALL_TRANSITION_RULES:
        if rule.from_state != current_state:
            continue
        if rule.evaluate(metrics, safety_state, state_duration_days):
            return rule
    return None
