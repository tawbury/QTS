"""상태 머신 전이 규칙 테스트."""
from decimal import Decimal

import pytest

from src.execution.contracts import (
    ExecutionContext,
    ExecutionState,
    OrderDecision,
    TERMINAL_STATES,
)
from src.execution.state_machine import (
    InvalidTransitionError,
    can_transition,
    handle_stage_timeout,
    is_terminal,
    transition,
)
from src.provider.models.order_request import OrderSide, OrderType


def _make_ctx(state: ExecutionState = ExecutionState.INIT) -> ExecutionContext:
    od = OrderDecision(
        symbol="005930", side=OrderSide.BUY, qty=100,
        price=Decimal("75000"),
    )
    ctx = ExecutionContext(order=od)
    ctx.state = state
    return ctx


class TestCanTransition:
    def test_init_to_precheck(self):
        assert can_transition(ExecutionState.INIT, ExecutionState.PRECHECK)

    def test_init_to_splitting_blocked(self):
        assert not can_transition(ExecutionState.INIT, ExecutionState.SPLITTING)

    def test_precheck_to_splitting(self):
        assert can_transition(ExecutionState.PRECHECK, ExecutionState.SPLITTING)

    def test_precheck_to_failed(self):
        assert can_transition(ExecutionState.PRECHECK, ExecutionState.FAILED)

    def test_monitoring_to_complete(self):
        assert can_transition(ExecutionState.MONITORING, ExecutionState.COMPLETE)

    def test_monitoring_to_adjusting(self):
        assert can_transition(ExecutionState.MONITORING, ExecutionState.ADJUSTING)

    def test_adjusting_to_monitoring(self):
        assert can_transition(ExecutionState.ADJUSTING, ExecutionState.MONITORING)

    def test_escaping_to_escaped(self):
        assert can_transition(ExecutionState.ESCAPING, ExecutionState.ESCAPED)

    def test_complete_no_transitions(self):
        for s in ExecutionState:
            assert not can_transition(ExecutionState.COMPLETE, s)

    def test_escaped_no_transitions(self):
        for s in ExecutionState:
            assert not can_transition(ExecutionState.ESCAPED, s)

    def test_failed_no_transitions(self):
        for s in ExecutionState:
            assert not can_transition(ExecutionState.FAILED, s)


class TestEmergencyEscapeFromAnyState:
    """모든 비종료 상태에서 ESCAPING 전이 가능."""

    def test_escape_from_non_terminal(self):
        non_terminal = [s for s in ExecutionState if s not in TERMINAL_STATES]
        for state in non_terminal:
            assert can_transition(state, ExecutionState.ESCAPING), f"Cannot escape from {state}"

    def test_escape_from_terminal_blocked(self):
        for state in TERMINAL_STATES:
            assert not can_transition(state, ExecutionState.ESCAPING)


class TestTransition:
    def test_valid_transition(self):
        ctx = _make_ctx(ExecutionState.INIT)
        transition(ctx, ExecutionState.PRECHECK)
        assert ctx.state == ExecutionState.PRECHECK
        assert ctx.stage_start_time is not None

    def test_invalid_transition_raises(self):
        ctx = _make_ctx(ExecutionState.INIT)
        with pytest.raises(InvalidTransitionError):
            transition(ctx, ExecutionState.COMPLETE)

    def test_emergency_escape_from_sending(self):
        ctx = _make_ctx(ExecutionState.SENDING)
        transition(ctx, ExecutionState.ESCAPING)
        assert ctx.state == ExecutionState.ESCAPING


class TestIsTerminal:
    def test_terminal_states(self):
        assert is_terminal(ExecutionState.COMPLETE)
        assert is_terminal(ExecutionState.ESCAPED)
        assert is_terminal(ExecutionState.FAILED)

    def test_non_terminal(self):
        assert not is_terminal(ExecutionState.INIT)
        assert not is_terminal(ExecutionState.MONITORING)


class TestHandleStageTimeout:
    def test_monitoring_timeout_goes_to_adjusting(self):
        ctx = _make_ctx(ExecutionState.MONITORING)
        next_state = handle_stage_timeout(ctx)
        assert next_state == ExecutionState.ADJUSTING
        assert any(a.code == "FS093" for a in ctx.alerts)

    def test_adjusting_timeout_goes_to_escaping(self):
        ctx = _make_ctx(ExecutionState.ADJUSTING)
        next_state = handle_stage_timeout(ctx)
        assert next_state == ExecutionState.ESCAPING

    def test_other_timeout_goes_to_failed(self):
        ctx = _make_ctx(ExecutionState.PRECHECK)
        next_state = handle_stage_timeout(ctx)
        assert next_state == ExecutionState.FAILED
