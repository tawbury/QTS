from __future__ import annotations

from src.risk.calculators.base_risk_calculator import SimpleRiskCalculator
from src.strategy.interfaces.strategy import Intent, MarketContext, ExecutionContext


def test_simple_risk_calculator_buy_allows_when_cash_is_sufficient_and_computes_max_qty() -> None:
    calc = SimpleRiskCalculator()

    market = MarketContext(symbol="TEST", price=100.0)
    execution = ExecutionContext(position_qty=0, cash=350.0)

    intent = Intent(symbol="TEST", side="BUY", qty=2, reason="unit_test")

    risk = calc.evaluate(intent=intent, market=market, execution=execution)

    assert risk.allowed is True
    # 350 // 100 = 3
    assert risk.max_qty_allowed == 3
    assert 0.0 <= risk.risk_score <= 1.0
    assert "buy_affordability_check" in risk.reason


def test_simple_risk_calculator_buy_blocks_when_cash_is_insufficient() -> None:
    calc = SimpleRiskCalculator()

    market = MarketContext(symbol="TEST", price=100.0)
    execution = ExecutionContext(position_qty=0, cash=50.0)

    intent = Intent(symbol="TEST", side="BUY", qty=1, reason="unit_test")

    risk = calc.evaluate(intent=intent, market=market, execution=execution)

    assert risk.allowed is False
    assert risk.max_qty_allowed == 0
    assert 0.0 <= risk.risk_score <= 1.0


def test_simple_risk_calculator_sell_allows_up_to_position_qty() -> None:
    calc = SimpleRiskCalculator()

    market = MarketContext(symbol="TEST", price=100.0)
    execution = ExecutionContext(position_qty=5, cash=0.0)

    intent = Intent(symbol="TEST", side="SELL", qty=3, reason="unit_test")

    risk = calc.evaluate(intent=intent, market=market, execution=execution)

    assert risk.allowed is True
    assert risk.max_qty_allowed == 5
    assert 0.0 <= risk.risk_score <= 1.0
    assert "sell_position_check" in risk.reason


def test_simple_risk_calculator_blocks_when_qty_is_non_positive() -> None:
    calc = SimpleRiskCalculator()

    market = MarketContext(symbol="TEST", price=100.0)
    execution = ExecutionContext(position_qty=0, cash=1_000.0)

    intent = Intent(symbol="TEST", side="BUY", qty=0, reason="unit_test")

    risk = calc.evaluate(intent=intent, market=market, execution=execution)

    assert risk.allowed is False
    assert risk.max_qty_allowed == 0
    assert risk.risk_score == 1.0
    assert "qty_non_positive" in risk.reason
