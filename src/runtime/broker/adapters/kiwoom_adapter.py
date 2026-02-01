"""
Kiwoom broker adapter (META-240523-03).

Arch §2.2, §10.1: KIS와 동일한 OrderAdapter 계약 준수.
Protocol-Driven: KiwoomOrderClientProtocol 주입으로 실제 API 호출부 분리 → 테스트 용이성.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol

from runtime.broker.adapters.base_adapter import BaseBrokerAdapter
from runtime.broker.kiwoom.payload_mapping import (
    build_kiwoom_order_payload,
    parse_kiwoom_place_response,
    raw_to_order_response,
)
from runtime.broker.order_base import OrderQuery
from runtime.execution.models.order_request import OrderRequest
from runtime.execution.models.order_response import OrderResponse, OrderStatus


class KiwoomOrderClientProtocol(Protocol):
    """
    키움 REST API 주문 호출 계약 (KISOrderClientProtocol 패턴).

    MockKiwoomOrderClient로 테스트 시 실제 API 호출 없음.
    """

    def place_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        """주문 전송. raw dict 반환 (return_code, order_no, return_msg 등)."""
        ...

    def get_order(self, params: dict[str, Any]) -> dict[str, Any]:
        """주문 조회. params: order_id 등."""
        ...

    def cancel_order(self, params: dict[str, Any]) -> dict[str, Any]:
        """주문 취소. params: order_id."""
        ...


class KiwoomOrderAdapter(BaseBrokerAdapter):
    """
    Kiwoom order adapter (Protocol-Driven).

    Same contract as KIS: place_order, get_order, cancel_order.
    client 주입 시 payload_mapping으로 Kiwoom REST API 호출.
    client 미주입 시 스텁(테스트/개발용).
    """

    def __init__(
        self,
        client: Optional[KiwoomOrderClientProtocol] = None,
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
            return OrderResponse(
                status=OrderStatus.ACCEPTED,
                broker_order_id="KIWOOM-VIRTUAL",
                message="dry_run accepted (kiwoom)",
                raw={"dry_run": True, "broker": "kiwoom"},
            )
        if self._client is None:
            return OrderResponse(
                status=OrderStatus.REJECTED,
                message="Kiwoom client not configured (stub mode)",
                raw={"broker": "kiwoom", "stub": True},
            )

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
            return OrderResponse(
                status=OrderStatus.UNKNOWN,
                broker_order_id=query.broker_order_id,
                message="Kiwoom client not configured (stub mode)",
                raw={"broker": "kiwoom", "stub": True},
            )
        resp = self._client.get_order({"order_id": query.broker_order_id})
        return raw_to_order_response(resp, default_broker_order_id=query.broker_order_id)

    def cancel_order(self, query: OrderQuery) -> OrderResponse:
        if self._client is None:
            return OrderResponse(
                status=OrderStatus.UNKNOWN,
                broker_order_id=query.broker_order_id,
                message="Kiwoom client not configured (stub mode)",
                raw={"broker": "kiwoom", "stub": True},
            )
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
