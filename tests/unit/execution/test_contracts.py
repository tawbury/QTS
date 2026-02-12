"""Execution 계약 테스트."""
from decimal import Decimal

import pytest

from src.execution.contracts import (
    CancelAck,
    ExecutionAlert,
    ExecutionContext,
    ExecutionResult,
    ExecutionState,
    FillEvent,
    ModifyAck,
    MonitorResult,
    OrderAck,
    OrderDecision,
    PreCheckResult,
    SendResult,
    SlippageConfig,
    SplitConfig,
    SplitOrder,
    SplitOrderStatus,
    SplitResult,
    SplitStrategy,
    STATE_TRANSITIONS,
    STAGE_TIMEOUTS_MS,
    TERMINAL_STATES,
)
from src.provider.models.order_request import OrderSide, OrderType


class TestExecutionState:
    def test_all_states_exist(self):
        assert len(ExecutionState) == 10

    def test_terminal_states(self):
        assert ExecutionState.COMPLETE in TERMINAL_STATES
        assert ExecutionState.ESCAPED in TERMINAL_STATES
        assert ExecutionState.FAILED in TERMINAL_STATES
        assert len(TERMINAL_STATES) == 3

    def test_transitions_defined_for_all(self):
        for state in ExecutionState:
            assert state in STATE_TRANSITIONS

    def test_terminal_states_have_no_transitions(self):
        for s in TERMINAL_STATES:
            assert STATE_TRANSITIONS[s] == []

    def test_timeouts_defined(self):
        assert STAGE_TIMEOUTS_MS["PRECHECK"] == 5_000
        assert STAGE_TIMEOUTS_MS["MONITORING"] == 60_000


class TestOrderDecision:
    def test_valid_limit_order(self):
        od = OrderDecision(
            symbol="005930", side=OrderSide.BUY, qty=100,
            price=Decimal("75000"), order_type=OrderType.LIMIT,
        )
        assert od.qty == 100
        assert od.order_id  # UUID generated

    def test_valid_market_order(self):
        od = OrderDecision(
            symbol="005930", side=OrderSide.SELL, qty=50,
            order_type=OrderType.MARKET,
        )
        assert od.price is None

    def test_zero_qty_raises(self):
        with pytest.raises(ValueError, match="qty must be positive"):
            OrderDecision(symbol="005930", side=OrderSide.BUY, qty=0)

    def test_negative_qty_raises(self):
        with pytest.raises(ValueError):
            OrderDecision(symbol="005930", side=OrderSide.BUY, qty=-10)

    def test_limit_without_price_raises(self):
        with pytest.raises(ValueError, match="LIMIT order requires price"):
            OrderDecision(
                symbol="005930", side=OrderSide.BUY, qty=100,
                order_type=OrderType.LIMIT, price=None,
            )


class TestSplitOrder:
    def test_remaining_qty(self):
        s = SplitOrder(
            split_id="a", parent_order_id="b", sequence=1,
            symbol="005930", side=OrderSide.BUY, qty=100,
            filled_qty=30,
        )
        assert s.remaining_qty == 70

    def test_is_terminal(self):
        s = SplitOrder(
            split_id="a", parent_order_id="b", sequence=1,
            symbol="005930", side=OrderSide.BUY, qty=100,
            status=SplitOrderStatus.FILLED,
        )
        assert s.is_terminal

    def test_pending_not_terminal(self):
        s = SplitOrder(
            split_id="a", parent_order_id="b", sequence=1,
            symbol="005930", side=OrderSide.BUY, qty=100,
        )
        assert not s.is_terminal


class TestSplitStrategy:
    def test_strategies(self):
        assert SplitStrategy.SINGLE == "SINGLE"
        assert SplitStrategy.TWAP == "TWAP"
        assert SplitStrategy.VWAP == "VWAP"
        assert SplitStrategy.ICEBERG == "ICEBERG"


class TestFillEvent:
    def test_frozen(self):
        fe = FillEvent(
            order_id="ord1", symbol="005930", side=OrderSide.BUY,
            filled_qty=50, filled_price=Decimal("75000"),
        )
        assert fe.filled_qty == 50
        with pytest.raises(AttributeError):
            fe.filled_qty = 100  # type: ignore[misc]


class TestAcks:
    def test_order_ack(self):
        ack = OrderAck(accepted=True, order_id="123")
        assert ack.accepted
        assert ack.order_id == "123"

    def test_modify_ack(self):
        ack = ModifyAck(accepted=False, reject_reason="PRICE_OUT_OF_RANGE")
        assert not ack.accepted

    def test_cancel_ack(self):
        ack = CancelAck(accepted=True)
        assert ack.accepted


class TestExecutionContext:
    def test_total_filled_qty(self):
        od = OrderDecision(
            symbol="005930", side=OrderSide.BUY, qty=100,
            price=Decimal("75000"),
        )
        ctx = ExecutionContext(order=od)
        ctx.fills.append(FillEvent(
            order_id="a", symbol="005930", side=OrderSide.BUY,
            filled_qty=30, filled_price=Decimal("75000"),
        ))
        ctx.fills.append(FillEvent(
            order_id="b", symbol="005930", side=OrderSide.BUY,
            filled_qty=20, filled_price=Decimal("75100"),
        ))
        assert ctx.total_filled_qty == 50

    def test_has_position(self):
        od = OrderDecision(
            symbol="005930", side=OrderSide.BUY, qty=100,
            price=Decimal("75000"),
        )
        ctx = ExecutionContext(order=od)
        assert not ctx.has_position
        ctx.fills.append(FillEvent(
            order_id="a", symbol="005930", side=OrderSide.BUY,
            filled_qty=1, filled_price=Decimal("75000"),
        ))
        assert ctx.has_position

    def test_pending_orders(self):
        od = OrderDecision(
            symbol="005930", side=OrderSide.BUY, qty=100,
            price=Decimal("75000"),
        )
        ctx = ExecutionContext(order=od)
        s1 = SplitOrder(
            split_id="a", parent_order_id="b", sequence=1,
            symbol="005930", side=OrderSide.BUY, qty=50,
            status=SplitOrderStatus.SENT,
        )
        s2 = SplitOrder(
            split_id="c", parent_order_id="b", sequence=2,
            symbol="005930", side=OrderSide.BUY, qty=50,
            status=SplitOrderStatus.FILLED,
        )
        ctx.splits = [s1, s2]
        assert len(ctx.pending_orders) == 1


class TestExecutionResult:
    def test_fill_rate(self):
        r = ExecutionResult(
            state=ExecutionState.COMPLETE,
            order_id="a", symbol="005930", side=OrderSide.BUY,
            requested_qty=100, filled_qty=75,
        )
        assert r.fill_rate == 0.75

    def test_fill_rate_zero_qty(self):
        r = ExecutionResult(
            state=ExecutionState.FAILED,
            order_id="a", symbol="005930", side=OrderSide.BUY,
            requested_qty=0,
        )
        assert r.fill_rate == 0.0


class TestConfigs:
    def test_slippage_defaults(self):
        c = SlippageConfig()
        assert c.max_slippage_pct == Decimal("0.005")
        assert c.max_adjustment_rounds == 3

    def test_split_defaults(self):
        c = SplitConfig()
        assert c.min_split_qty == 100
        assert c.max_splits == 20

    def test_execution_alert(self):
        a = ExecutionAlert(code="FS090", severity="FAIL_SAFE", message="test")
        assert a.code == "FS090"
