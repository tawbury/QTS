"""PreCheck Stage 테스트."""
from decimal import Decimal

import pytest

from src.execution.contracts import OrderDecision
from src.execution.stages.precheck import PreCheckStage
from src.provider.models.order_request import OrderSide, OrderType
from src.safety.state import SafetyState


@pytest.fixture
def stage():
    return PreCheckStage()


@pytest.fixture
def buy_order():
    return OrderDecision(
        symbol="005930", side=OrderSide.BUY, qty=100,
        price=Decimal("75000"), order_type=OrderType.LIMIT,
    )


class TestPreCheckPass:
    def test_all_valid(self, stage, buy_order):
        result, alerts = stage.execute(
            buy_order, available_capital=Decimal("10000000"),
        )
        assert result.passed
        assert result.order is not None

    def test_market_order_pass(self, stage):
        order = OrderDecision(
            symbol="005930", side=OrderSide.BUY, qty=50,
            order_type=OrderType.MARKET,
        )
        result, alerts = stage.execute(
            order, available_capital=Decimal("10000000"),
        )
        assert result.passed


class TestPreCheckSafetyBlock:
    def test_lockdown_blocks(self, stage, buy_order):
        result, alerts = stage.execute(
            buy_order, safety_state=SafetyState.LOCKDOWN,
        )
        assert not result.passed
        assert result.reason == "SAFETY_BLOCKED"
        assert any(a.code == "FS090" for a in alerts)

    def test_fail_blocks(self, stage, buy_order):
        result, alerts = stage.execute(
            buy_order, safety_state=SafetyState.FAIL,
        )
        assert not result.passed

    def test_normal_passes(self, stage, buy_order):
        result, alerts = stage.execute(
            buy_order,
            available_capital=Decimal("10000000"),
            safety_state=SafetyState.NORMAL,
        )
        assert result.passed

    def test_warning_passes(self, stage, buy_order):
        result, alerts = stage.execute(
            buy_order,
            available_capital=Decimal("10000000"),
            safety_state=SafetyState.WARNING,
        )
        assert result.passed


class TestPreCheckCapital:
    def test_insufficient_capital_reduces(self, stage, buy_order):
        result, alerts = stage.execute(
            buy_order, available_capital=Decimal("5000000"),
        )
        # 5M / 75K = 66주로 축소
        assert result.passed
        assert result.adjusted_qty == 66
        assert any(a.code == "GR061" for a in alerts)

    def test_zero_capital_fails(self, stage, buy_order):
        result, alerts = stage.execute(
            buy_order, available_capital=Decimal("0"),
        )
        assert not result.passed
        assert result.reason == "INSUFFICIENT_CAPITAL"


class TestPreCheckBroker:
    def test_disconnected_fails(self, stage, buy_order):
        result, alerts = stage.execute(
            buy_order,
            available_capital=Decimal("10000000"),
            broker_connected=False,
        )
        assert not result.passed
        assert result.reason == "BROKER_DISCONNECTED"


class TestPreCheckMarket:
    def test_closed_fails(self, stage, buy_order):
        result, alerts = stage.execute(
            buy_order,
            available_capital=Decimal("10000000"),
            market_open=False,
        )
        assert not result.passed
        assert result.reason == "MARKET_CLOSED"


class TestPreCheckDailyLimit:
    def test_limit_reached(self, stage, buy_order):
        result, alerts = stage.execute(
            buy_order,
            available_capital=Decimal("10000000"),
            daily_trade_count=100,
            daily_trade_limit=100,
        )
        assert not result.passed
        assert result.reason == "DAILY_LIMIT_REACHED"
        assert any(a.code == "GR062" for a in alerts)


class TestPreCheckPosition:
    def test_position_limit(self, stage, buy_order):
        result, alerts = stage.execute(
            buy_order,
            available_capital=Decimal("10000000"),
            existing_position_qty=9950,
            max_position_qty=10000,
        )
        assert not result.passed
        assert result.reason == "POSITION_LIMIT_EXCEEDED"
