from __future__ import annotations

from runtime.risk.calculators.base_risk_calculator import SimpleRiskCalculator
from runtime.risk.gates.calculated_risk_gate import CalculatedRiskGate
from runtime.strategy.interfaces.strategy import Intent, MarketContext, ExecutionContext


def test_calculated_risk_gate_blocks_when_risk_disallows() -> None:
    calc = SimpleRiskCalculator()
    gate = CalculatedRiskGate(calculator=calc, max_risk_score=0.7)

    market = MarketContext(symbol="TEST", price=100.0)
    execution = ExecutionContext(position_qty=0, cash=50.0)  # BUY 불가

    intent = Intent(symbol="TEST", side="BUY", qty=1, reason="unit_test")

    decision = gate.apply(intent=intent, market=market, execution=execution)

    assert decision.allowed is False
    assert decision.adjusted_intent is None
    assert decision.risk.allowed is False


def test_calculated_risk_gate_blocks_when_risk_score_exceeds_threshold() -> None:
    calc = SimpleRiskCalculator()
    # risk_score를 쉽게 넘기기 위해 threshold를 낮게
    gate = CalculatedRiskGate(calculator=calc, max_risk_score=0.1)

    market = MarketContext(symbol="TEST", price=100.0)
    execution = ExecutionContext(position_qty=0, cash=1_000.0)

    intent = Intent(symbol="TEST", side="BUY", qty=2, reason="unit_test")  # order_value=200 -> risk_score=0.2

    decision = gate.apply(intent=intent, market=market, execution=execution)

    assert decision.allowed is False
    assert decision.adjusted_intent is None
    assert decision.risk.allowed is False
    assert "risk_score_exceeded" in decision.risk.reason


def test_calculated_risk_gate_adjusts_qty_down_to_max_allowed() -> None:
    calc = SimpleRiskCalculator()
    gate = CalculatedRiskGate(calculator=calc, max_risk_score=0.99)

    market = MarketContext(symbol="TEST", price=100.0)
    execution = ExecutionContext(position_qty=0, cash=250.0)  # max_qty_allowed = 2

    intent = Intent(symbol="TEST", side="BUY", qty=5, reason="unit_test")

    decision = gate.apply(intent=intent, market=market, execution=execution)

    assert decision.allowed is True
    assert decision.adjusted_intent is not None
    assert decision.adjusted_intent.qty == 2
    assert "qty_adjusted" in decision.adjusted_intent.reason


def test_calculated_risk_gate_blocks_if_qty_adjusted_to_zero() -> None:
    calc = SimpleRiskCalculator()
    gate = CalculatedRiskGate(calculator=calc, max_risk_score=0.99)

    market = MarketContext(symbol="TEST", price=100.0)
    execution = ExecutionContext(position_qty=0, cash=0.0)  # max_qty_allowed = 0

    intent = Intent(symbol="TEST", side="BUY", qty=1, reason="unit_test")

    decision = gate.apply(intent=intent, market=market, execution=execution)

    assert decision.allowed is False
    assert decision.adjusted_intent is None
    assert decision.risk.allowed is False
