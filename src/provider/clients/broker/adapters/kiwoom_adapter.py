"""
Kiwoom broker adapter (META-240523-03).

Arch §2.2, §10.1: KIS와 동일한 OrderAdapter 계약 준수.
Protocol-Driven: OrderClientProtocol 주입으로 실제 API 호출부 분리 → 테스트 용이성.
"""

from __future__ import annotations

from typing import Optional

from src.provider.clients.broker.adapters.base_adapter import BaseBrokerAdapter
from src.provider.clients.broker.adapters.protocols import OrderClientProtocol
from src.provider.clients.broker.kiwoom.payload_mapping import (
    build_kiwoom_order_payload,
    parse_kiwoom_place_response,
    raw_to_order_response,
)
from src.provider.clients.broker.order_base import OrderQuery
from src.provider.models.order_request import OrderRequest
from src.provider.models.order_response import OrderResponse, OrderStatus


class KiwoomOrderAdapter(BaseBrokerAdapter):
    """
    Kiwoom order adapter (Protocol-Driven).

    Same contract as KIS: place_order, get_order, cancel_order.
    client 주입 시 payload_mapping으로 Kiwoom REST API 호출.
    client 미주입 시 스텁(테스트/개발용).
    """

    def __init__(
        self,
        client: Optional[OrderClientProtocol] = None,
        *,
        acnt_no: str = "",
        market: str = "0",
    ) -> None:
        self._client = client
        self._acnt_no = acnt_no
        self._market = market

    @property
    def broker_id(self) -> str:
        return "kiwoom"

    def name(self) -> str:
        return "Kiwoom"

    def place_order(self, req: OrderRequest) -> OrderResponse:
        if req.dry_run:
            return self._dry_run_response("KIWOOM-VIRTUAL")
        if self._client is None:
            return self._stub_rejected()
        payload = build_kiwoom_order_payload(
            req, acnt_no=self._acnt_no, market=self._market
        )
        resp = self._client.place_order(payload)
        status, broker_order_id, message = parse_kiwoom_place_response(resp)
        if status == OrderStatus.REJECTED:
            return OrderResponse(
                status=status,
                broker_order_id=broker_order_id,
                message=message,
                raw=resp,
            )
        return OrderResponse(
            status=status,
            broker_order_id=broker_order_id,
            message=message,
            raw=resp,
        )

    def get_order(self, query: OrderQuery) -> OrderResponse:
        if self._client is None:
            return self._stub_unknown(query)
        resp = self._client.get_order({"order_id": query.broker_order_id})
        return raw_to_order_response(resp, default_broker_order_id=query.broker_order_id)

    def cancel_order(self, query: OrderQuery) -> OrderResponse:
        if self._client is None:
            return self._stub_unknown(query)
        resp = self._client.cancel_order({"order_id": query.broker_order_id})
        return_code = resp.get("return_code", -1)
        if isinstance(return_code, str) and return_code.isdigit():
            return_code = int(return_code)
        ok = return_code == 0
        return OrderResponse(
            status=OrderStatus.CANCELED if ok else OrderStatus.UNKNOWN,
            broker_order_id=query.broker_order_id,
            message=resp.get("return_msg") or resp.get("message"),
            raw=resp,
        )
