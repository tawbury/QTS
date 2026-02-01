from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from ...strategy.multiplexer.strategy_multiplexer import StrategyIntent
from ..calculators.strategy_risk_calculator import StrategyRiskCalculator
from ..policies.risk_policy import RiskStage


@dataclass(frozen=True)
class StagedGateEvent:
    strategy_id: str
    stage: RiskStage
    reason: str


class StagedRiskGate:
    """
    Phase 6: RiskGate 단계화(Warn/Reduce/Block).
    - 입력: StrategyIntent (Strategy Context 포함)
    - 출력: 허용된 StrategyIntent 목록 + 이벤트 로그
    """

    def __init__(self, calculator: StrategyRiskCalculator) -> None:
        self._calc = calculator

    def filter(self, intents: List[StrategyIntent]) -> tuple[List[StrategyIntent], List[StagedGateEvent]]:
        allowed: List[StrategyIntent] = []
        events: List[StagedGateEvent] = []

        for si in intents:
            rr = self._calc.evaluate(strategy_id=si.strategy_id, intent=si.intent)

            if rr.stage == RiskStage.BLOCK or rr.allowed_qty <= 0:
                events.append(StagedGateEvent(si.strategy_id, rr.stage, rr.reason))
                continue

            if rr.stage in (RiskStage.WARN, RiskStage.REDUCE):
                events.append(StagedGateEvent(si.strategy_id, rr.stage, rr.reason))

            new_intent = si.intent
            # REDUCE거나 WARN cap인 경우 qty 반영(보수적으로 동일 처리)
            if rr.allowed_qty is not None:
                new_intent = self._calc.apply_qty(si.intent, rr.allowed_qty)

            allowed.append(StrategyIntent(si.strategy_id, si.strategy_name, new_intent))

        return allowed, events

    def unwrap_for_loop(self, allowed: List[StrategyIntent]) -> List[Any]:
        """
        Execution Loop는 Intent list만 받도록 유지한다.
        """
        return [x.intent for x in allowed]
