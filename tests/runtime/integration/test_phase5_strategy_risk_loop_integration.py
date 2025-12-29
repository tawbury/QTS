from __future__ import annotations

from dataclasses import dataclass
from typing import List

from runtime.strategy.simple_strategy import SimpleStrategy
from runtime.strategy.interfaces.strategy import MarketContext, ExecutionContext, Intent
from runtime.risk.calculators.base_risk_calculator import SimpleRiskCalculator
from runtime.risk.gates.calculated_risk_gate import CalculatedRiskGate


@dataclass
class Phase5OrchestratorResult:
    produced_intents: List[Intent]
    allowed_intents: List[Intent]


class Phase5Orchestrator:
    """
    Phase 5 통합 테스트를 위한 '얇은 오케스트레이터'.
    - Strategy → intents
    - RiskGate → allowed intents
    - (Phase 4 Loop는 여기서 호출하거나, 외부에서 allowed intents를 받아 실행)
    """

    def __init__(self, strategy: SimpleStrategy, gate: CalculatedRiskGate):
        self.strategy = strategy
        self.gate = gate

    def run_once(self, market: MarketContext, execution: ExecutionContext) -> Phase5OrchestratorResult:
        produced = list(self.strategy.generate_intents(market=market, execution=execution))

        allowed: List[Intent] = []
        for intent in produced:
            decision = self.gate.apply(intent=intent, market=market, execution=execution)
            if decision.allowed and decision.adjusted_intent is not None:
                allowed.append(decision.adjusted_intent)

        return Phase5OrchestratorResult(produced_intents=produced, allowed_intents=allowed)


def test_phase5_strategy_risk_connection_smoke() -> None:
    """
    (A) 최소 통합 테스트:
    - Strategy → Intent
    - Risk 계산 + Gate 반영
    - 결과로 allowed_intents가 생성되는지 확인

    이 테스트는 Phase 4 Loop를 몰라도,
    Phase 5가 '구조적으로 연결 가능함'을 증명한다.
    """
    strategy = SimpleStrategy(buy_below=100.0, sell_above=110.0, qty=5)
    calc = SimpleRiskCalculator()
    gate = CalculatedRiskGate(calculator=calc, max_risk_score=0.99)

    orch = Phase5Orchestrator(strategy=strategy, gate=gate)

    market = MarketContext(symbol="TEST", price=99.0)        # BUY 유도
    execution = ExecutionContext(position_qty=0, cash=250.0) # max_qty_allowed=2

    result = orch.run_once(market=market, execution=execution)

    assert len(result.produced_intents) == 1
    assert result.produced_intents[0].side == "BUY"

    # Gate에서 qty가 2로 조정되어야 함
    assert len(result.allowed_intents) == 1
    assert result.allowed_intents[0].qty == 2


def test_phase5_integration_hook_for_phase4_loop_placeholder() -> None:
    """
    (B) Phase 4 Loop에 실제로 연결하는 통합 테스트 자리.

    아래 TODO의 import 및 호출부를 당신의 Phase 4 Loop 엔트리에 맞게 연결하면,
    'Loop 수정 없이 전략 실행 가능'을 테스트로 증명할 수 있다.

    이 테스트는 지금 상태에서는 "연결 포인트 스켈레톤"만 제공한다.
    """
    strategy = SimpleStrategy(buy_below=100.0, sell_above=110.0, qty=1)
    calc = SimpleRiskCalculator()
    gate = CalculatedRiskGate(calculator=calc, max_risk_score=0.99)

    orch = Phase5Orchestrator(strategy=strategy, gate=gate)

    market = MarketContext(symbol="TEST", price=99.0)
    execution = ExecutionContext(position_qty=0, cash=10_000.0)

    result = orch.run_once(market=market, execution=execution)
    assert result.allowed_intents  # 최소 1개 허용 intent가 있어야 함

    # ------------------------------------------------------------------
    # TODO: Phase 4 Loop 엔트리로 연결
    #
    # 예시(가정):
    # from runtime.execution_loop.execution_loop import ExecutionLoop
    # loop = ExecutionLoop(...)
    # loop.process_intents(result.allowed_intents)  # 또는 loop.step(intents=...)
    #
    # assert ... (실주문 금지 환경에서 에러 없이 종료되었는지)
    # ------------------------------------------------------------------
    assert True
