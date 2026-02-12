"""Stage 4: PartialFillMonitor — 부분 체결 모니터링."""
from __future__ import annotations

from decimal import Decimal

from src.execution.contracts import (
    ExecutionAlert,
    FillEvent,
    MonitorResult,
    SplitOrder,
    SplitOrderStatus,
)


class FillMonitorStage:
    """부분 체결 모니터링 단계 (동기 시뮬레이션)."""

    def __init__(self, timeout_ms: int = 60_000) -> None:
        self.timeout_ms = timeout_ms

    def process_fills(
        self, orders: list[SplitOrder], fill_events: list[FillEvent]
    ) -> tuple[MonitorResult, list[ExecutionAlert]]:
        """주어진 체결 이벤트를 집계하여 모니터링 결과 반환.

        실제 런타임에서는 async로 이벤트를 대기하지만,
        테스트 가능성을 위해 동기 집계 방식으로 구현.
        """
        alerts: list[ExecutionAlert] = []
        total_qty = sum(o.qty for o in orders)
        filled_qty = 0

        # 체결 이벤트 → 주문 매핑
        fill_map: dict[str, list[FillEvent]] = {}
        for fe in fill_events:
            fill_map.setdefault(fe.order_id, []).append(fe)

        # 주문별 체결 집계
        for order in orders:
            order_fills = fill_map.get(order.broker_order_id, [])
            order_filled = sum(f.filled_qty for f in order_fills)
            order.filled_qty = order_filled

            if order_filled >= order.qty:
                order.status = SplitOrderStatus.FILLED
                if order_fills:
                    total_cost = sum(
                        Decimal(str(f.filled_qty)) * f.filled_price for f in order_fills
                    )
                    order.avg_fill_price = total_cost / Decimal(str(order_filled))
            elif order_filled > 0:
                order.status = SplitOrderStatus.PARTIALLY_FILLED

            filled_qty += order_filled

        remaining = total_qty - filled_qty

        if remaining == 0:
            status = "COMPLETE"
        elif filled_qty > 0 and remaining > 0:
            status = "PARTIAL"
        else:
            status = "NEEDS_ADJUSTMENT"

        if remaining > 0 and filled_qty == 0:
            alerts.append(ExecutionAlert(
                code="GR064",
                severity="GUARDRAIL",
                message=f"No fills received for {total_qty} shares",
                stage="MONITORING",
            ))

        return MonitorResult(
            status=status,
            filled_qty=filled_qty,
            remaining_qty=remaining,
            fills=fill_events,
        ), alerts
