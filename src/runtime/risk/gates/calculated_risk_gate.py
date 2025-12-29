from __future__ import annotations

from dataclasses import dataclass

from ..calculators.base_risk_calculator import RiskCalculator, RiskResult
from ...strategy.interfaces.strategy import Intent, MarketContext, ExecutionContext


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    adjusted_intent: Intent | None
    risk: RiskResult


class CalculatedRiskGate:
    def __init__(self, calculator: RiskCalculator, max_risk_score: float = 0.7):
        self.calculator = calculator
        self.max_risk_score = max_risk_score

    def apply(self, intent: Intent, market: MarketContext, execution: ExecutionContext) -> GateDecision:
        # 1. 원본 intent 기준 Risk 계산
        risk = self.calculator.evaluate(intent, market, execution)

        if not risk.allowed:
            return GateDecision(False, None, risk)

        # 2. qty 조정
        adjusted_qty = min(intent.qty, risk.max_qty_allowed)
        if adjusted_qty <= 0:
            return GateDecision(
                False,
                None,
                RiskResult(False, risk.risk_score, 0, "qty_adjusted_to_zero"),
            )

        adjusted_intent = intent
        if adjusted_qty != intent.qty:
            adjusted_intent = Intent(
                symbol=intent.symbol,
                side=intent.side,
                qty=adjusted_qty,
                reason=f"{intent.reason}|qty_adjusted",
            )

        # 3. 🔑 조정된 qty 기준으로 risk_score 재계산
        adjusted_order_value = adjusted_qty * market.price
        adjusted_risk_score = min(
            1.0,
            adjusted_order_value / max(execution.cash, 1.0),
        )

        # 4. 최종 risk_score 기준 Gate 판단
        if adjusted_risk_score > self.max_risk_score:
            return GateDecision(
                False,
                None,
                RiskResult(
                    False,
                    adjusted_risk_score,
                    adjusted_qty,
                    "risk_score_exceeded",
                ),
            )

        return GateDecision(True, adjusted_intent, risk)
