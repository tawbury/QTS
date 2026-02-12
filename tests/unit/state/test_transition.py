"""운영 상태 전환 규칙 테스트."""
import pytest

from src.safety.state import SafetyState
from src.state.contracts import OperatingState, TransitionMetrics
from src.state.transition import (
    AggressiveToBalanced,
    BalancedToAggressive,
    BalancedToDefensive,
    DefensiveToBalanced,
    find_applicable_rule,
)


class TestAggressiveToBalanced:
    """AGGRESSIVE → BALANCED 전환 규칙 (Any)."""

    rule = AggressiveToBalanced()

    def test_drawdown_trigger(self):
        m = TransitionMetrics(drawdown_pct=0.06)
        assert self.rule.evaluate(m, SafetyState.NORMAL, 10.0)

    def test_vix_trigger(self):
        m = TransitionMetrics(vix=26)
        assert self.rule.evaluate(m, SafetyState.NORMAL, 10.0)

    def test_consecutive_losses_trigger(self):
        m = TransitionMetrics(consecutive_scalp_losses=6)
        assert self.rule.evaluate(m, SafetyState.NORMAL, 10.0)

    def test_daily_loss_trigger(self):
        m = TransitionMetrics(daily_loss_pct=0.03)
        assert self.rule.evaluate(m, SafetyState.NORMAL, 10.0)

    def test_no_trigger(self):
        m = TransitionMetrics(drawdown_pct=0.03, vix=20)
        assert not self.rule.evaluate(m, SafetyState.NORMAL, 10.0)

    def test_reason_message(self):
        m = TransitionMetrics(drawdown_pct=0.06, vix=26)
        reason = self.rule.reason(m)
        assert "AGGRESSIVE→BALANCED" in reason
        assert "drawdown" in reason
        assert "vix" in reason


class TestBalancedToDefensive:
    """BALANCED → DEFENSIVE 전환 규칙 (Any)."""

    rule = BalancedToDefensive()

    def test_drawdown_trigger(self):
        m = TransitionMetrics(drawdown_pct=0.12)
        assert self.rule.evaluate(m, SafetyState.NORMAL, 10.0)

    def test_vix_trigger(self):
        m = TransitionMetrics(vix=32)
        assert self.rule.evaluate(m, SafetyState.NORMAL, 10.0)

    def test_circuit_breaker_trigger(self):
        m = TransitionMetrics(market_circuit_breaker=True)
        assert self.rule.evaluate(m, SafetyState.NORMAL, 10.0)

    def test_safety_warning_trigger(self):
        m = TransitionMetrics()
        assert self.rule.evaluate(m, SafetyState.WARNING, 10.0)

    def test_safety_fail_trigger(self):
        m = TransitionMetrics()
        assert self.rule.evaluate(m, SafetyState.FAIL, 10.0)

    def test_no_trigger(self):
        m = TransitionMetrics(drawdown_pct=0.05, vix=20)
        assert not self.rule.evaluate(m, SafetyState.NORMAL, 10.0)


class TestDefensiveToBalanced:
    """DEFENSIVE → BALANCED 전환 규칙 (All)."""

    rule = DefensiveToBalanced()

    def test_all_conditions_met(self):
        m = TransitionMetrics(
            drawdown_pct=0.03,
            vix=15,
            consecutive_profitable_days=5,
        )
        assert self.rule.evaluate(m, SafetyState.NORMAL, 6.0)

    def test_drawdown_too_high(self):
        m = TransitionMetrics(
            drawdown_pct=0.06, vix=15, consecutive_profitable_days=5
        )
        assert not self.rule.evaluate(m, SafetyState.NORMAL, 6.0)

    def test_not_enough_duration(self):
        m = TransitionMetrics(
            drawdown_pct=0.03, vix=15, consecutive_profitable_days=5
        )
        assert not self.rule.evaluate(m, SafetyState.NORMAL, 3.0)

    def test_safety_not_normal(self):
        m = TransitionMetrics(
            drawdown_pct=0.03, vix=15, consecutive_profitable_days=5
        )
        assert not self.rule.evaluate(m, SafetyState.WARNING, 6.0)


class TestBalancedToAggressive:
    """BALANCED → AGGRESSIVE 전환 규칙 (All)."""

    rule = BalancedToAggressive()

    def test_all_conditions_met(self):
        m = TransitionMetrics(
            cagr=0.20,
            target_cagr=0.15,
            vix=12,
            capital_growth_pct=0.15,
            win_rate_30d=0.65,
        )
        assert self.rule.evaluate(m, SafetyState.NORMAL, 12.0)

    def test_vix_too_high(self):
        m = TransitionMetrics(
            cagr=0.20, target_cagr=0.15, vix=16,
            capital_growth_pct=0.15, win_rate_30d=0.65,
        )
        assert not self.rule.evaluate(m, SafetyState.NORMAL, 12.0)

    def test_not_enough_duration(self):
        m = TransitionMetrics(
            cagr=0.20, target_cagr=0.15, vix=12,
            capital_growth_pct=0.15, win_rate_30d=0.65,
        )
        assert not self.rule.evaluate(m, SafetyState.NORMAL, 8.0)


class TestFindApplicableRule:
    """find_applicable_rule 테스트."""

    def test_finds_aggressive_to_balanced(self):
        m = TransitionMetrics(drawdown_pct=0.06)
        rule = find_applicable_rule(
            OperatingState.AGGRESSIVE, m, SafetyState.NORMAL, 10.0
        )
        assert rule is not None
        assert rule.to_state == OperatingState.BALANCED

    def test_finds_balanced_to_defensive(self):
        m = TransitionMetrics(drawdown_pct=0.12)
        rule = find_applicable_rule(
            OperatingState.BALANCED, m, SafetyState.NORMAL, 10.0
        )
        assert rule is not None
        assert rule.to_state == OperatingState.DEFENSIVE

    def test_returns_none_when_no_trigger(self):
        m = TransitionMetrics()
        rule = find_applicable_rule(
            OperatingState.BALANCED, m, SafetyState.NORMAL, 10.0
        )
        assert rule is None

    def test_defensive_no_rule_when_conditions_unmet(self):
        m = TransitionMetrics(drawdown_pct=0.06)  # drawdown > 5%
        rule = find_applicable_rule(
            OperatingState.DEFENSIVE, m, SafetyState.NORMAL, 6.0
        )
        assert rule is None
