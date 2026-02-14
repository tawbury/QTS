"""
ExecutionIntent ↔ OrderRequest Bridge (META-240523-03).

Arch §3, broker/README §3: "브릿지: Intent→Request, Response→ExecutionResponse 변환"
- OrderAdapter와 BrokerEngine 사이의 공통 변환기(Transformer).
- 키움/KIS 등 어떤 브로커가 추가되어도 이 로직이 중복되지 않도록 단일 책임.
- Protocol-Driven: OrderAdapter를 감싸 BrokerEngine.submit_intent 계약을 제공.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.shared.timezone_utils import now_kst

from src.provider.models.intent import ExecutionIntent
from src.provider.models.order_request import OrderRequest, OrderSide, OrderType
from src.provider.models.order_response import OrderResponse, OrderStatus
from src.provider.models.response import ExecutionResponse

if TYPE_CHECKING:
    from src.provider.clients.broker.order_base import OrderAdapter


# ----- Intent → OrderRequest 변환 -----


def intent_to_order_request(
    intent: ExecutionIntent,
    *,
    dry_run: bool = False,
) -> Optional[OrderRequest]:
    """
    ExecutionIntent → OrderRequest 변환.

    NOOP(intent_type, quantity<=0)인 경우 None 반환.
    """
    if intent.intent_type.upper() in ("NOOP", ""):
        return None
    qty = int(intent.quantity)
    if qty <= 0:
        return None

    side = OrderSide.BUY if intent.side.upper() == "BUY" else OrderSide.SELL
    order_type = (
        OrderType.LIMIT
        if intent.intent_type.upper() == "LIMIT"
        else OrderType.MARKET
    )
    limit_price: Optional[float] = None
    if order_type == OrderType.LIMIT and intent.metadata:
        limit_price = intent.metadata.get("limit_price")
        if limit_price is not None:
            limit_price = float(limit_price)

    return OrderRequest(
        symbol=intent.symbol.strip(),
        side=side,
        qty=qty,
        order_type=order_type,
        limit_price=limit_price,
        client_order_id=intent.intent_id,
        dry_run=dry_run,
    )


def order_response_to_execution_response(
    order_resp: OrderResponse,
    intent: ExecutionIntent,
    broker_id: str,
) -> ExecutionResponse:
    """
    OrderResponse → ExecutionResponse 변환.

    OrderStatus.accepted/filled/partially_filled → accepted=True.
    그 외 → accepted=False.
    """
    accepted = order_resp.status in (
        OrderStatus.ACCEPTED,
        OrderStatus.FILLED,
        OrderStatus.PARTIALLY_FILLED,
    )
    message = order_resp.message or (
        "accepted" if accepted else str(order_resp.status.value.lower())
    )
    if order_resp.broker_order_id:
        message = f"{message} | order_id={order_resp.broker_order_id}"

    return ExecutionResponse(
        intent_id=intent.intent_id,
        accepted=accepted,
        broker=broker_id,
        message=message,
        timestamp=now_kst(),
    )


# ----- OrderAdapter → BrokerEngine 브릿지 어댑터 -----


class OrderAdapterToBrokerEngineAdapter:
    """
    OrderAdapter를 BrokerEngine.submit_intent 계약으로 감싸는 브릿지.

    - Stateless: 어댑터·TokenCache 참조만 보유.
    - KIS/Kiwoom 등 OrderAdapter가 동일한 경로로 LiveBroker에 주입 가능.
    - create_broker_for_execution(live_allowed, adapter=this) 사용.
    """

    def __init__(
        self,
        order_adapter: "OrderAdapter",
        *,
        broker_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> None:
        self._order_adapter = order_adapter
        self._dry_run = dry_run
        self._broker_id = broker_id or getattr(
            order_adapter, "broker_id", "unknown"
        )

    def submit_intent(self, intent: ExecutionIntent) -> ExecutionResponse:
        """
        ExecutionIntent → OrderRequest 변환 후 place_order 호출.
        OrderResponse → ExecutionResponse 변환 반환.
        """
        req = intent_to_order_request(intent, dry_run=self._dry_run)
        if req is None:
            return ExecutionResponse(
                intent_id=intent.intent_id,
                accepted=False,
                broker=self._broker_id,
                message="NOOP: invalid intent (qty<=0 or intent_type=NOOP)",
                timestamp=now_kst(),
            )

        order_resp = self._order_adapter.place_order(req)
        return order_response_to_execution_response(
            order_resp, intent, self._broker_id
        )
