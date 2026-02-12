"""Risk Rule Evaluator 테스트."""
from decimal import Decimal

import pytest

from src.micro_risk.contracts import (
    ActionType,
    MAEConfig,
    MarketData,
    MicroRiskConfig,
    PositionShadow,
    TrailingStopConfig,
    VolatilityKillSwitchConfig,
)
from src.micro_risk.evaluator import RiskRuleEvaluator


def _make_shadow(
    mae_pct=Decimal("0"), pnl_pct=Decimal("0"),
    time_sec=0, trailing_active=False,
) -> PositionShadow:
    s = PositionShadow(
        symbol="005930", qty=100,
        avg_price=Decimal("75000"), current_price=Decimal("75000"),
    )
    s.mae_pct = mae_pct
    s.unrealized_pnl_pct = pnl_pct
    s.time_in_trade_sec = time_sec
    s.trailing_stop_active = trailing_active
    return s


class TestPriorityOrder:
    def test_kill_switch_first(self):
        """Volatility Kill-Switch는 최우선."""
        shadow = _make_shadow(mae_pct=Decimal("-0.03"))
        config = MicroRiskConfig()
        evaluator = RiskRuleEvaluator(config)
        md = MarketData(vix=Decimal("45"))
        actions = evaluator.evaluate(shadow, md)
        assert len(actions) == 1
        assert actions[0].action_type == ActionType.KILL_SWITCH

    def test_mae_before_trailing(self):
        """MAE가 TrailingStop보다 우선."""
        shadow = _make_shadow(
            mae_pct=Decimal("-0.025"),
            pnl_pct=Decimal("0.02"),
            trailing_active=True,
        )
        shadow.trailing_stop_price = Decimal("74000")
        shadow.current_price = Decimal("73000")  # 트레일링 스탑도 히트
        config = MicroRiskConfig()
        evaluator = RiskRuleEvaluator(config)
        actions = evaluator.evaluate(shadow, MarketData())
        # MAE FULL_EXIT → short circuit → trailing 평가 안함
        assert len(actions) == 1
        assert actions[0].action_type == ActionType.FULL_EXIT
        assert actions[0].payload["reason"] == "MAE_THRESHOLD_EXCEEDED"


class TestShortCircuit:
    def test_full_exit_stops_eval(self):
        shadow = _make_shadow(mae_pct=Decimal("-0.025"))
        evaluator = RiskRuleEvaluator(MicroRiskConfig())
        actions = evaluator.evaluate(shadow, MarketData())
        assert len(actions) == 1

    def test_partial_exit_continues(self):
        """PARTIAL_EXIT는 단락 평가 대상 아님."""
        shadow = _make_shadow(mae_pct=Decimal("-0.016"))
        config = MicroRiskConfig(
            mae=MAEConfig(
                position_mae_threshold_pct=Decimal("0.02"),
                partial_exit_at_pct=Decimal("0.015"),
            ),
        )
        evaluator = RiskRuleEvaluator(config)
        actions = evaluator.evaluate(shadow, MarketData())
        # PARTIAL_EXIT → continues to check remaining rules
        assert any(a.action_type == ActionType.PARTIAL_EXIT for a in actions)


class TestNoAction:
    def test_normal_conditions(self):
        shadow = _make_shadow()
        evaluator = RiskRuleEvaluator(MicroRiskConfig())
        actions = evaluator.evaluate(shadow, MarketData())
        assert len(actions) == 0


class TestRuleCount:
    def test_has_four_rules(self):
        evaluator = RiskRuleEvaluator(MicroRiskConfig())
        assert evaluator.rule_count == 4


class TestCombinedScenarios:
    def test_volatility_critical_and_mae(self):
        """Critical VIX + MAE 근접."""
        shadow = _make_shadow(mae_pct=Decimal("-0.016"))
        config = MicroRiskConfig(
            mae=MAEConfig(
                position_mae_threshold_pct=Decimal("0.02"),
                partial_exit_at_pct=Decimal("0.015"),
            ),
        )
        evaluator = RiskRuleEvaluator(config)
        md = MarketData(vix=Decimal("32"))
        actions = evaluator.evaluate(shadow, md)
        # Volatility PARTIAL_EXIT (first) + MAE PARTIAL_EXIT
        assert len(actions) == 2

    def test_trailing_activate_on_profit(self):
        shadow = _make_shadow(pnl_pct=Decimal("0.02"))
        shadow.highest_price_since_entry = Decimal("76500")
        evaluator = RiskRuleEvaluator(MicroRiskConfig())
        actions = evaluator.evaluate(shadow, MarketData())
        assert len(actions) == 1
        assert actions[0].action_type == ActionType.TRAILING_STOP_ADJUST
