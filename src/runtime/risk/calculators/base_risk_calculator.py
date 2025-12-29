from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ...strategy.interfaces.strategy import Intent, MarketContext, ExecutionContext


@dataclass(frozen=True)
class RiskResult:
    allowed: bool
    risk_score: float          # 0.0(안전) ~ 1.0(위험) 정도의 단순 스케일
    max_qty_allowed: int
    reason: str


class RiskCalculator(Protocol):
    def evaluate(
        self,
        intent: Intent,
        market: MarketContext,
        execution: ExecutionContext,
    ) -> RiskResult:
        ...


class SimpleRiskCalculator(RiskCalculator):
    """
    Phase 5 최소 Risk:
    - BUY는 cash로 가능 수량 산정
    - SELL은 보유 수량까지만
    - risk_score는 단순 비율(예: 주문금액/현금)
    """

    def evaluate(self, intent: Intent, market: MarketContext, execution: ExecutionContext) -> RiskResult:
        if intent.qty <= 0:
            return RiskResult(False, 1.0, 0, "qty_non_positive")

        if intent.side == "BUY":
            if market.price <= 0:
                return RiskResult(False, 1.0, 0, "invalid_price")

            affordable = int(execution.cash // market.price)
            max_allowed = max(0, affordable)
            allowed = max_allowed > 0

            order_value = intent.qty * market.price
            risk_score = min(1.0, order_value / max(execution.cash, 1.0))

            return RiskResult(allowed, risk_score, max_allowed, "buy_affordability_check")

        if intent.side == "SELL":
            max_allowed = max(0, execution.position_qty)
            allowed = max_allowed > 0
            return RiskResult(allowed, 0.2 if allowed else 1.0, max_allowed, "sell_position_check")

        return RiskResult(False, 1.0, 0, "unknown_side")
