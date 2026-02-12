"""Stage 5: AdaptiveAdjust — 적응적 가격 조정."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.execution.contracts import (
    AdjustAction,
    AdjustResult,
    ExecutionAlert,
    SlippageConfig,
    SplitOrder,
    SplitOrderStatus,
)


class AdaptiveAdjustStage:
    """미체결 주문의 가격/수량 조정."""

    def __init__(self, config: Optional[SlippageConfig] = None) -> None:
        self.config = config or SlippageConfig()

    def execute(
        self,
        unfilled_orders: list[SplitOrder],
        *,
        best_bid: Optional[Decimal] = None,
        best_ask: Optional[Decimal] = None,
        adjustment_round: int = 0,
    ) -> tuple[AdjustResult, list[ExecutionAlert]]:
        alerts: list[ExecutionAlert] = []
        adjustments: list[AdjustAction] = []

        if adjustment_round >= self.config.max_adjustment_rounds:
            alerts.append(ExecutionAlert(
                code="FS094",
                severity="FAIL_SAFE",
                message=f"Max adjustment rounds ({self.config.max_adjustment_rounds}) reached",
                stage="ADJUSTING",
            ))
            return AdjustResult(adjustments=adjustments), alerts

        for order in unfilled_orders:
            if order.is_terminal:
                continue

            action = self._decide_action(order, best_bid, best_ask)

            if action.action == "PRICE_IMPROVE" and action.new_price is not None:
                slippage = self._calc_slippage(order, action.new_price)
                if slippage > self.config.max_slippage_pct:
                    alerts.append(ExecutionAlert(
                        code="GR063",
                        severity="GUARDRAIL",
                        message=f"Slippage {slippage} exceeds max {self.config.max_slippage_pct}",
                        stage="ADJUSTING",
                    ))
                    action = AdjustAction(action="WAIT", order=order)

            adjustments.append(action)

        return AdjustResult(adjustments=adjustments), alerts

    def _decide_action(
        self,
        order: SplitOrder,
        best_bid: Optional[Decimal],
        best_ask: Optional[Decimal],
    ) -> AdjustAction:
        if order.price is None:
            return AdjustAction(action="WAIT", order=order)

        if order.side.value == "BUY" and best_ask is not None:
            new_price = min(
                order.price * (1 + self.config.price_improve_step_pct),
                best_ask,
            )
            return AdjustAction(
                action="PRICE_IMPROVE", order=order, new_price=new_price
            )

        if order.side.value == "SELL" and best_bid is not None:
            new_price = max(
                order.price * (1 - self.config.price_improve_step_pct),
                best_bid,
            )
            return AdjustAction(
                action="PRICE_IMPROVE", order=order, new_price=new_price
            )

        return AdjustAction(action="WAIT", order=order)

    def _calc_slippage(self, order: SplitOrder, new_price: Decimal) -> Decimal:
        if order.price is None or order.price == 0:
            return Decimal("0")
        return abs(new_price - order.price) / order.price
