from __future__ import annotations

from runtime.broker.order_base import OrderAdapter, OrderQuery
from runtime.execution.models.order_request import OrderRequest
from runtime.execution.models.order_response import OrderResponse, OrderStatus

# Phase 2 asset (이미 존재한다고 가정)
# - KISBrokerAdapter: HTTP 호출/세션/환경(모의/실) 분기
from runtime.broker.kis.adapter import KISBrokerAdapter


class KISOrderAdapter(OrderAdapter):
    def __init__(self, broker: KISBrokerAdapter) -> None:
        self._broker = broker

    def place_order(self, req: OrderRequest) -> OrderResponse:
        # Phase 3 안전장치: 테스트/기본은 dry_run
        if req.dry_run:
            return OrderResponse(
                status=OrderStatus.ACCEPTED,
                broker_order_id="VIRTUAL-ORDER-ID",
                message="dry_run accepted",
                raw={"dry_run": True},
            )

        # TODO: Phase 1.5/2 자산화 스펙에 맞게 payload 구성
        payload = {
            "symbol": req.symbol,
            "side": req.side.value,
            "qty": req.qty,
            "type": req.order_type.value,
            "limit_price": req.limit_price,
            "client_order_id": req.client_order_id,
        }

        # TODO: 아래 호출은 Phase 2 KISBrokerAdapter의 실제 메서드명에 맞추어 연결
        # resp = self._broker.post("/orders", json=payload)
        resp = self._broker.place_order(payload)  # 예시

        # TODO: 응답 파싱 규칙 자산화 내용 그대로 적용
        ok = bool(resp.get("ok", False))
        if not ok:
            return OrderResponse(
                status=OrderStatus.REJECTED,
                message=resp.get("message", "rejected"),
                raw=resp,
            )

        return OrderResponse(
            status=OrderStatus.ACCEPTED,
            broker_order_id=resp.get("order_id"),
            message=resp.get("message"),
            raw=resp,
        )

    def get_order(self, query: OrderQuery) -> OrderResponse:
        # resp = self._broker.get(f"/orders/{query.broker_order_id}")
        resp = self._broker.get_order({"order_id": query.broker_order_id})  # 예시

        # TODO: KIS 스펙에 맞게 status mapping
        status = OrderStatus.UNKNOWN
        if resp.get("status") in ("accepted", "open"):
            status = OrderStatus.ACCEPTED
        elif resp.get("status") in ("filled",):
            status = OrderStatus.FILLED
        elif resp.get("status") in ("rejected",):
            status = OrderStatus.REJECTED

        return OrderResponse(
            status=status,
            broker_order_id=query.broker_order_id,
            filled_qty=int(resp.get("filled_qty", 0) or 0),
            avg_fill_price=resp.get("avg_fill_price"),
            raw=resp,
        )

    def cancel_order(self, query: OrderQuery) -> OrderResponse:
        # resp = self._broker.post(f"/orders/{query.broker_order_id}/cancel")
        resp = self._broker.cancel_order({"order_id": query.broker_order_id})  # 예시

        ok = bool(resp.get("ok", False))
        return OrderResponse(
            status=OrderStatus.CANCELED if ok else OrderStatus.UNKNOWN,
            broker_order_id=query.broker_order_id,
            message=resp.get("message"),
            raw=resp,
        )
