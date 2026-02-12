"""Trailing Stop Rule 테스트."""
from decimal import Decimal

import pytest

from src.micro_risk.contracts import (
    ActionType,
    MarketData,
    PositionShadow,
    TrailingStopConfig,
)
from src.micro_risk.rules.trailing_stop import (
    TrailingStopRule,
    calculate_trailing_stop_price,
    should_activate_trailing_stop,
)


def _make_shadow(
    price=Decimal("75000"), pnl_pct=Decimal("0"), highest=None,
    trailing_active=False, trailing_price=Decimal("0"),
) -> PositionShadow:
    s = PositionShadow(
        symbol="005930", qty=100,
        avg_price=price, current_price=price,
    )
    s.unrealized_pnl_pct = pnl_pct
    if highest is not None:
        s.highest_price_since_entry = highest
    s.trailing_stop_active = trailing_active
    s.trailing_stop_price = trailing_price
    return s


class TestActivation:
    def test_activate_on_profit(self):
        shadow = _make_shadow(pnl_pct=Decimal("0.02"))
        config = TrailingStopConfig(activation_profit_pct=Decimal("0.01"))
        assert should_activate_trailing_stop(shadow, config) is True

    def test_no_activate_below_threshold(self):
        shadow = _make_shadow(pnl_pct=Decimal("0.005"))
        config = TrailingStopConfig(activation_profit_pct=Decimal("0.01"))
        assert should_activate_trailing_stop(shadow, config) is False

    def test_no_activate_already_active(self):
        shadow = _make_shadow(pnl_pct=Decimal("0.02"), trailing_active=True)
        config = TrailingStopConfig()
        assert should_activate_trailing_stop(shadow, config) is False


class TestCalculation:
    def test_basic_calculation(self):
        shadow = _make_shadow(highest=Decimal("76000"))
        config = TrailingStopConfig(trail_distance_pct=Decimal("0.005"))
        stop = calculate_trailing_stop_price(shadow, config)
        # 76000 * (1 - 0.005) = 75620
        assert stop == Decimal("75620.000")

    def test_min_distance(self):
        shadow = _make_shadow(highest=Decimal("76000"))
        config = TrailingStopConfig(
            trail_distance_pct=Decimal("0.001"),
            min_trail_distance=Decimal("500"),
        )
        stop = calculate_trailing_stop_price(shadow, config)
        # 76000 * 0.999 = 75924, 76000-500 = 75500 → max(75924, 75500) = 75924
        assert stop == Decimal("75924.000")

    def test_ratchet(self):
        shadow = _make_shadow(
            highest=Decimal("76000"),
            trailing_active=True,
            trailing_price=Decimal("75800"),
        )
        config = TrailingStopConfig(
            trail_distance_pct=Decimal("0.005"),
            ratchet_only=True,
        )
        stop = calculate_trailing_stop_price(shadow, config)
        # 76000*0.995 = 75620; max(75620, 75800) = 75800
        assert stop == Decimal("75800")

    def test_no_ratchet(self):
        shadow = _make_shadow(
            highest=Decimal("76000"),
            trailing_active=True,
            trailing_price=Decimal("75800"),
        )
        config = TrailingStopConfig(
            trail_distance_pct=Decimal("0.005"),
            ratchet_only=False,
        )
        stop = calculate_trailing_stop_price(shadow, config)
        # Without ratchet: 76000*0.995 = 75620
        assert stop == Decimal("75620.000")


class TestTrailingStopRule:
    def test_activation_returns_adjust(self):
        shadow = _make_shadow(pnl_pct=Decimal("0.02"), highest=Decimal("76500"))
        rule = TrailingStopRule(TrailingStopConfig())
        md = MarketData()
        action = rule.evaluate(shadow, md)
        assert action is not None
        assert action.action_type == ActionType.TRAILING_STOP_ADJUST
        assert shadow.trailing_stop_active is True

    def test_stop_hit(self):
        shadow = _make_shadow(
            trailing_active=True, trailing_price=Decimal("75500"),
        )
        shadow.current_price = Decimal("75400")
        rule = TrailingStopRule(TrailingStopConfig())
        action = rule.evaluate(shadow, MarketData())
        assert action is not None
        assert action.action_type == ActionType.FULL_EXIT
        assert action.payload["reason"] == "TRAILING_STOP_HIT"

    def test_adjust_upward(self):
        shadow = _make_shadow(
            trailing_active=True, trailing_price=Decimal("75000"),
            highest=Decimal("76000"),
        )
        shadow.current_price = Decimal("76000")
        rule = TrailingStopRule(TrailingStopConfig(
            trail_distance_pct=Decimal("0.005"),
        ))
        action = rule.evaluate(shadow, MarketData())
        assert action is not None
        assert action.action_type == ActionType.TRAILING_STOP_ADJUST
        assert action.payload["new_stop"] > Decimal("75000")

    def test_no_action_inactive(self):
        shadow = _make_shadow(pnl_pct=Decimal("0.005"))
        rule = TrailingStopRule(TrailingStopConfig())
        action = rule.evaluate(shadow, MarketData())
        assert action is None

    def test_no_adjust_if_same_stop(self):
        shadow = _make_shadow(
            trailing_active=True,
            trailing_price=Decimal("75620"),
            highest=Decimal("76000"),
        )
        shadow.current_price = Decimal("75800")
        config = TrailingStopConfig(
            trail_distance_pct=Decimal("0.005"),
            ratchet_only=True,
        )
        rule = TrailingStopRule(config)
        action = rule.evaluate(shadow, MarketData())
        # new_stop = 76000*0.995=75620, same as current → no adjust
        assert action is None
