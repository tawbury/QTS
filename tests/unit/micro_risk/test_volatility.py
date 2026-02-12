"""Volatility Kill-Switch Rule 테스트."""
from decimal import Decimal

import pytest

from src.micro_risk.contracts import (
    ActionType,
    MarketData,
    PositionShadow,
    VolatilityKillSwitchConfig,
)
from src.micro_risk.rules.volatility import VolatilityKillSwitchRule


def _make_shadow(qty=100) -> PositionShadow:
    return PositionShadow(
        symbol="005930", qty=qty,
        avg_price=Decimal("75000"), current_price=Decimal("75000"),
    )


class TestKillLevel:
    def test_vix_kill(self):
        rule = VolatilityKillSwitchRule(VolatilityKillSwitchConfig())
        md = MarketData(vix=Decimal("45"))
        action = rule.evaluate(_make_shadow(), md)
        assert action is not None
        assert action.action_type == ActionType.KILL_SWITCH
        assert action.symbol == "ALL"

    def test_realized_vol_kill(self):
        rule = VolatilityKillSwitchRule(VolatilityKillSwitchConfig())
        md = MarketData(realized_volatility=Decimal("0.09"))
        action = rule.evaluate(_make_shadow(), md)
        assert action is not None
        assert action.action_type == ActionType.KILL_SWITCH

    def test_exact_kill_level(self):
        rule = VolatilityKillSwitchRule(VolatilityKillSwitchConfig())
        md = MarketData(vix=Decimal("40"))
        action = rule.evaluate(_make_shadow(), md)
        assert action is not None
        assert action.action_type == ActionType.KILL_SWITCH


class TestCriticalLevel:
    def test_vix_critical(self):
        rule = VolatilityKillSwitchRule(VolatilityKillSwitchConfig())
        md = MarketData(vix=Decimal("32"))
        action = rule.evaluate(_make_shadow(), md)
        assert action is not None
        assert action.action_type == ActionType.PARTIAL_EXIT
        assert action.payload["qty"] == 50  # 100 * 0.5

    def test_realized_vol_critical(self):
        rule = VolatilityKillSwitchRule(VolatilityKillSwitchConfig())
        md = MarketData(realized_volatility=Decimal("0.06"))
        action = rule.evaluate(_make_shadow(), md)
        assert action is not None
        assert action.action_type == ActionType.PARTIAL_EXIT


class TestWarningLevel:
    def test_vix_warning_no_action(self):
        rule = VolatilityKillSwitchRule(VolatilityKillSwitchConfig())
        md = MarketData(vix=Decimal("26"))
        action = rule.evaluate(_make_shadow(), md)
        # Warning: log only, no action
        assert action is None

    def test_below_warning_no_action(self):
        rule = VolatilityKillSwitchRule(VolatilityKillSwitchConfig())
        md = MarketData(vix=Decimal("20"))
        action = rule.evaluate(_make_shadow(), md)
        assert action is None


class TestEdgeCases:
    def test_small_qty_no_partial(self):
        rule = VolatilityKillSwitchRule(VolatilityKillSwitchConfig())
        md = MarketData(vix=Decimal("32"))
        action = rule.evaluate(_make_shadow(qty=1), md)
        # int(1 * 0.5) = 0 → no partial exit
        assert action is None

    def test_custom_config(self):
        config = VolatilityKillSwitchConfig(
            vix_kill_level=Decimal("50"),
            vix_critical_level=Decimal("35"),
        )
        rule = VolatilityKillSwitchRule(config)
        md = MarketData(vix=Decimal("36"))
        action = rule.evaluate(_make_shadow(), md)
        assert action.action_type == ActionType.PARTIAL_EXIT
