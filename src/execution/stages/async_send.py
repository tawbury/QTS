"""Stage 3: AsyncSend — 비동기 주문 전송."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.execution.contracts import (
    ExecutionAlert,
    OrderAck,
    SendResult,
    SplitOrder,
    SplitOrderStatus,
)


@runtime_checkable
class AsyncBrokerProtocol(Protocol):
    """비동기 브로커 인터페이스."""

    async def send_order(
        self, symbol: str, side: str, qty: int, price: float | None, order_type: str
    ) -> OrderAck: ...

    async def cancel_order(self, order_id: str) -> bool: ...


class AsyncSendStage:
    """비동기 주문 전송 단계."""

    def __init__(self, broker: AsyncBrokerProtocol, max_retries: int = 3) -> None:
        self.broker = broker
        self.max_retries = max_retries

    async def execute(self, splits: list[SplitOrder]) -> tuple[SendResult, list[ExecutionAlert]]:
        alerts: list[ExecutionAlert] = []
        sent_orders: list[SplitOrder] = []
        sent_count = 0
        failed_count = 0

        for split in splits:
            success = await self._send_single(split)
            if success:
                sent_count += 1
                sent_orders.append(split)
            else:
                failed_count += 1

        if sent_count == 0 and failed_count > 0:
            alerts.append(ExecutionAlert(
                code="FS090",
                severity="FAIL_SAFE",
                message=f"All {failed_count} orders failed to send",
                stage="SENDING",
            ))

        return SendResult(
            sent_count=sent_count,
            failed_count=failed_count,
            orders=sent_orders,
        ), alerts

    async def _send_single(self, split: SplitOrder) -> bool:
        for attempt in range(self.max_retries):
            try:
                price_val = float(split.price) if split.price is not None else None
                ack = await self.broker.send_order(
                    symbol=split.symbol,
                    side=split.side.value,
                    qty=split.qty,
                    price=price_val,
                    order_type=split.price_type.value,
                )
                if ack.accepted:
                    split.status = SplitOrderStatus.SENT
                    split.broker_order_id = ack.order_id
                    return True
            except Exception:
                continue

        split.status = SplitOrderStatus.FAILED
        return False
