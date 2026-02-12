"""Time-in-Trade Rule 테스트."""
from decimal import Decimal

import pytest

from src.micro_risk.contracts import (
    ActionType,
    MarketData,
    PositionShadow,
    StrategyType,
    TimeInTradeConfig,
)
from src.micro_risk.rules.time_in_trade import TimeInTradeRule


def _make_shadow(
    time_sec=0, strategy=StrategyType.SCALP, pnl=Decimal("0"),
) -> PositionShadow:
    s = PositionShadow(
        symbol="005930", qty=100,
        avg_price=Decimal("75000"), current_price=Decimal("75000"),
    )
    s.time_in_trade_sec = time_sec
    s.strategy = strategy
    s.unrealized_pnl = pnl
    return s


class TestTimeout:
    def test_scalp_timeout(self):
        shadow = _make_shadow(time_sec=3700)
        rule = TimeInTradeRule(TimeInTradeConfig(scalp_max_time_sec=3600))
        action = rule.evaluate(shadow, MarketData())
        assert action is not None
        assert action.action_type == ActionType.FULL_EXIT
        assert action.payload["reason"] == "TIME_IN_TRADE_EXCEEDED"

    def test_within_time(self):
        shadow = _make_shadow(time_sec=1800)
        rule = TimeInTradeRule(TimeInTradeConfig(scalp_max_time_sec=3600))
        action = rule.evaluate(shadow, MarketData())
        assert action is None

    def test_exact_max_time(self):
        shadow = _make_shadow(time_sec=3600)
        rule = TimeInTradeRule(TimeInTradeConfig(scalp_max_time_sec=3600))
        action = rule.evaluate(shadow, MarketData())
        assert action is not None


class TestExtension:
    def test_profitable_extends(self):
        shadow = _make_shadow(
            time_sec=4000, pnl=Decimal("50000"),
        )
        rule = TimeInTradeRule(TimeInTradeConfig(
            scalp_max_time_sec=3600,
            extension_profitable=True,
            extension_time_sec=1800,
        ))
        action = rule.evaluate(shadow, MarketData())
        # 3600 + 1800 = 5400, 4000 < 5400 → no exit
        assert action is None

    def test_profitable_extension_exceeded(self):
        shadow = _make_shadow(
            time_sec=5500, pnl=Decimal("50000"),
        )
        rule = TimeInTradeRule(TimeInTradeConfig(
            scalp_max_time_sec=3600,
            extension_time_sec=1800,
        ))
        action = rule.evaluate(shadow, MarketData())
        assert action is not None
        assert action.payload["max_time_sec"] == 5400

    def test_loss_no_extension(self):
        shadow = _make_shadow(
            time_sec=3700, pnl=Decimal("-10000"),
        )
        rule = TimeInTradeRule(TimeInTradeConfig(
            scalp_max_time_sec=3600,
            extension_profitable=True,
            extension_time_sec=1800,
        ))
        action = rule.evaluate(shadow, MarketData())
        assert action is not None  # no extension for loss


class TestStrategy:
    def test_swing_max_time(self):
        shadow = _make_shadow(
            time_sec=700000, strategy=StrategyType.SWING,
        )
        rule = TimeInTradeRule(TimeInTradeConfig())
        action = rule.evaluate(shadow, MarketData())
        assert action is not None

    def test_portfolio_no_limit(self):
        shadow = _make_shadow(
            time_sec=999999, strategy=StrategyType.PORTFOLIO,
        )
        rule = TimeInTradeRule(TimeInTradeConfig())
        action = rule.evaluate(shadow, MarketData())
        assert action is None


class TestWarning:
    def test_warning_state(self):
        shadow = _make_shadow(time_sec=2900)
        rule = TimeInTradeRule(TimeInTradeConfig(
            scalp_max_time_sec=3600,
            warning_at_pct=Decimal("0.80"),
        ))
        assert rule.is_warning(shadow) is True

    def test_no_warning(self):
        shadow = _make_shadow(time_sec=1000)
        rule = TimeInTradeRule(TimeInTradeConfig())
        assert rule.is_warning(shadow) is False
