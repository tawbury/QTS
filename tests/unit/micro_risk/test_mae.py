"""MAE Rule 테스트."""
from decimal import Decimal

import pytest

from src.micro_risk.contracts import (
    ActionType,
    MAEConfig,
    MarketData,
    PositionShadow,
)
from src.micro_risk.rules.mae import MAERule


def _make_shadow(mae_pct=Decimal("0"), qty=100) -> PositionShadow:
    s = PositionShadow(
        symbol="005930", qty=qty,
        avg_price=Decimal("75000"), current_price=Decimal("75000"),
    )
    s.mae_pct = mae_pct
    return s


class TestMAEFullExit:
    def test_threshold_exceeded(self):
        shadow = _make_shadow(mae_pct=Decimal("-0.025"))
        rule = MAERule(MAEConfig(position_mae_threshold_pct=Decimal("0.02")))
        action = rule.evaluate(shadow, MarketData())
        assert action is not None
        assert action.action_type == ActionType.FULL_EXIT
        assert action.payload["reason"] == "MAE_THRESHOLD_EXCEEDED"

    def test_exact_threshold(self):
        shadow = _make_shadow(mae_pct=Decimal("-0.02"))
        rule = MAERule(MAEConfig(position_mae_threshold_pct=Decimal("0.02")))
        action = rule.evaluate(shadow, MarketData())
        assert action is not None
        assert action.action_type == ActionType.FULL_EXIT

    def test_below_threshold_no_action(self):
        shadow = _make_shadow(mae_pct=Decimal("-0.01"))
        rule = MAERule(MAEConfig(position_mae_threshold_pct=Decimal("0.02")))
        action = rule.evaluate(shadow, MarketData())
        assert action is None


class TestMAEPartialExit:
    def test_partial_threshold(self):
        shadow = _make_shadow(mae_pct=Decimal("-0.016"))
        rule = MAERule(MAEConfig(
            position_mae_threshold_pct=Decimal("0.02"),
            partial_exit_at_pct=Decimal("0.015"),
            partial_exit_ratio=Decimal("0.50"),
        ))
        action = rule.evaluate(shadow, MarketData())
        assert action is not None
        assert action.action_type == ActionType.PARTIAL_EXIT
        assert action.payload["qty"] == 50  # 100 * 0.5

    def test_partial_below_threshold(self):
        shadow = _make_shadow(mae_pct=Decimal("-0.010"))
        rule = MAERule(MAEConfig(
            partial_exit_at_pct=Decimal("0.015"),
        ))
        action = rule.evaluate(shadow, MarketData())
        assert action is None

    def test_full_takes_precedence(self):
        shadow = _make_shadow(mae_pct=Decimal("-0.03"))
        rule = MAERule(MAEConfig(
            position_mae_threshold_pct=Decimal("0.02"),
            partial_exit_at_pct=Decimal("0.015"),
        ))
        action = rule.evaluate(shadow, MarketData())
        assert action.action_type == ActionType.FULL_EXIT


class TestMAEEdgeCases:
    def test_zero_mae(self):
        shadow = _make_shadow(mae_pct=Decimal("0"))
        rule = MAERule(MAEConfig())
        assert rule.evaluate(shadow, MarketData()) is None

    def test_positive_mae(self):
        shadow = _make_shadow(mae_pct=Decimal("0.01"))
        rule = MAERule(MAEConfig())
        assert rule.evaluate(shadow, MarketData()) is None

    def test_small_qty_no_partial(self):
        shadow = _make_shadow(mae_pct=Decimal("-0.016"), qty=1)
        rule = MAERule(MAEConfig(
            position_mae_threshold_pct=Decimal("0.02"),
            partial_exit_at_pct=Decimal("0.015"),
            partial_exit_ratio=Decimal("0.50"),
        ))
        action = rule.evaluate(shadow, MarketData())
        # int(1 * 0.5) = 0, no partial exit
        assert action is None
