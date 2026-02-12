"""운영 상태 계약 테스트."""
import pytest

from src.state.contracts import (
    OperatingState,
    StateProperties,
    STATE_PROPERTIES,
    TransitionMetrics,
)


class TestOperatingState:
    """OperatingState enum 테스트."""

    def test_three_states(self):
        assert len(OperatingState) == 3

    def test_values(self):
        assert OperatingState.AGGRESSIVE == "AGGRESSIVE"
        assert OperatingState.BALANCED == "BALANCED"
        assert OperatingState.DEFENSIVE == "DEFENSIVE"


class TestStateProperties:
    """StateProperties 테스트."""

    def test_all_states_have_properties(self):
        for state in OperatingState:
            assert state in STATE_PROPERTIES

    def test_aggressive_properties(self):
        props = STATE_PROPERTIES[OperatingState.AGGRESSIVE]
        assert props.scalp_allocation_range == (0.60, 0.80)
        assert props.risk_tolerance_multiplier == 1.2
        assert props.entry_signal_threshold == 0.6
        assert props.max_positions == 20
        assert props.max_daily_trades == 50
        assert props.rebalancing_enabled is False
        assert props.new_entry_enabled is True
        assert props.scalp_engine_active is True

    def test_balanced_properties(self):
        props = STATE_PROPERTIES[OperatingState.BALANCED]
        assert props.risk_tolerance_multiplier == 1.0
        assert props.entry_signal_threshold == 0.7
        assert props.max_positions == 15
        assert props.rebalancing_enabled is True
        assert props.new_entry_enabled is True

    def test_defensive_properties(self):
        props = STATE_PROPERTIES[OperatingState.DEFENSIVE]
        assert props.scalp_allocation_range == (0.05, 0.15)
        assert props.portfolio_allocation_range == (0.60, 0.80)
        assert props.risk_tolerance_multiplier == 0.5
        assert props.entry_signal_threshold == 0.9
        assert props.max_positions == 10
        assert props.max_daily_trades == 10
        assert props.new_entry_enabled is False
        assert props.scalp_engine_active is False
        assert props.swing_engine_active is True

    def test_allocation_ranges_sum_to_one(self):
        """각 상태의 배분 범위 중간값 합이 대략 1.0."""
        for state, props in STATE_PROPERTIES.items():
            mid_sum = (
                sum(props.scalp_allocation_range) / 2
                + sum(props.swing_allocation_range) / 2
                + sum(props.portfolio_allocation_range) / 2
            )
            assert 0.95 <= mid_sum <= 1.05, f"{state}: midpoint sum = {mid_sum}"


class TestTransitionMetrics:
    """TransitionMetrics 테스트."""

    def test_defaults(self):
        m = TransitionMetrics()
        assert m.drawdown_pct == 0.0
        assert m.vix == 0.0
        assert m.consecutive_scalp_losses == 0
        assert m.market_circuit_breaker is False

    def test_custom_values(self):
        m = TransitionMetrics(drawdown_pct=0.08, vix=28, daily_loss_pct=0.03)
        assert m.drawdown_pct == 0.08
        assert m.vix == 28
