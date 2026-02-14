from __future__ import annotations

from dataclasses import dataclass

from src.risk.calculators.strategy_risk_calculator import StrategyRiskCalculator
from src.risk.gates.staged_risk_gate import StagedRiskGate
from src.risk.policies.risk_policy import RiskPolicy, RiskStage
from src.strategy.multiplexer.strategy_multiplexer import StrategyIntent


@dataclass
class DummyIntent:
    symbol: str
    side: str
    qty: int


def test_staged_gate_blocks_when_over_max_in_block_stage():
    calc = StrategyRiskCalculator()
    calc.set_policy("s1", RiskPolicy(max_order_qty=1, stage=RiskStage.BLOCK))

    gate = StagedRiskGate(calc)
    intents = [StrategyIntent("s1", "S1", DummyIntent("A", "BUY", 3))]

    allowed, events = gate.filter(intents)
    assert allowed == []
    assert events[0].stage == RiskStage.BLOCK


def test_staged_gate_reduces_qty_in_reduce_stage():
    calc = StrategyRiskCalculator()
    calc.set_policy("s1", RiskPolicy(max_order_qty=5, stage=RiskStage.REDUCE, reduce_to_qty=2))

    gate = StagedRiskGate(calc)
    intents = [StrategyIntent("s1", "S1", DummyIntent("A", "BUY", 10))]

    allowed, events = gate.filter(intents)
    assert len(allowed) == 1
    assert allowed[0].intent.qty == 2
    assert events[0].stage == RiskStage.REDUCE
