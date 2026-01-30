"""
KIS Order Adapter: OrderRequest → KIS payload, KIS response → OrderResponse.

Contract (Phase 8): docs/arch/08_Broker_Integration_Architecture.md
- Request normalization: BUY/SELL, order_type, market code via payload_mapping.
- Response normalization: ExecutionResult (OrderResponse) via payload_mapping.
- Broker dependency: KISOrderClientProtocol (place_order / get_order / cancel_order).
"""

from __future__ import annotations

from typing import Any, Protocol

from runtime.broker.adapters.base_adapter import BaseBrokerAdapter
from runtime.broker.kis.payload_mapping import (
    build_kis_order_payload,
    parse_kis_place_response,
    raw_to_order_response,
)
from runtime.broker.order_base import OrderQuery
from runtime.execution.models.order_request import OrderRequest
from runtime.execution.models.order_response import OrderResponse, OrderStatus


class KISOrderClientProtocol(Protocol):
    """
    Contract for KIS order API (place / get / cancel).

    Implemented by a broker client that performs HTTP calls to KIS.
    KISBrokerAdapter (auth-only) does not implement this; use a dedicated
    order client or mock in tests.
    """

    def place_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send order. Returns raw dict with ok, order_id/ord_no, message."""
        ...

    def get_order(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get order status. Params: order_id or broker_order_id. Returns raw KIS response."""
        ...

    def cancel_order(self, params: dict[str, Any]) -> dict[str, Any]:
        """Cancel order. Params: order_id. Returns raw dict with ok, message."""
        ...


class KISOrderAdapter(BaseBrokerAdapter):
    """Normalizes OrderRequest → KIS payload and KIS response → OrderResponse."""

    @property
    def broker_id(self) -> str:
        return "kis"

    def __init__(self, broker: KISOrderClientProtocol, *, cano: str = "", acnt_prdt_cd: str = "01") -> None:
        self._broker = broker
        self._cano = cano
        self._acnt_prdt_cd = acnt_prdt_cd

    def place_order(self, req: OrderRequest) -> OrderResponse:
        if req.dry_run:
            return OrderResponse(
                status=OrderStatus.ACCEPTED,
                broker_order_id="VIRTUAL-ORDER-ID",
                message="dry_run accepted",
                raw={"dry_run": True},
            )

        payload = build_kis_order_payload(
            req,
            cano=self._cano,
            acnt_prdt_cd=self._acnt_prdt_cd,
        )
        resp = self._broker.place_order(payload)

        status, broker_order_id, message = parse_kis_place_response(resp)
        if status == OrderStatus.REJECTED:
            return OrderResponse(status=status, broker_order_id=broker_order_id, message=message, raw=resp)
        return OrderResponse(
            status=status,
            broker_order_id=broker_order_id,
            message=message,
            raw=resp,
        )

    def get_order(self, query: OrderQuery) -> OrderResponse:
        resp = self._broker.get_order({"order_id": query.broker_order_id})
        return raw_to_order_response(resp, default_broker_order_id=query.broker_order_id)

    def cancel_order(self, query: OrderQuery) -> OrderResponse:
        resp = self._broker.cancel_order({"order_id": query.broker_order_id})
        ok = resp.get("ok", False)
        if isinstance(ok, str):
            ok = ok.lower() in ("true", "1", "ok", "success")
        return OrderResponse(
            status=OrderStatus.CANCELED if ok else OrderStatus.UNKNOWN,
            broker_order_id=query.broker_order_id,
            message=resp.get("message") or resp.get("msg"),
            raw=resp,
        )
