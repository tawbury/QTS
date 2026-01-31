"""
Kiwoom broker adapter skeleton (Phase 8).

Arch §2.2, §10.1: KIS와 동일한 OrderAdapter 계약 준수.
Kiwoom API 연동은 추후 구현; 현재는 스켈레톤으로 등록/선택 구조만 확보.
"""

from __future__ import annotations

from runtime.broker.adapters.base_adapter import BaseBrokerAdapter
from runtime.broker.order_base import OrderQuery
from runtime.execution.models.order_request import OrderRequest
from runtime.execution.models.order_response import OrderResponse, OrderStatus


class KiwoomOrderAdapter(BaseBrokerAdapter):
    """
    Kiwoom order adapter (skeleton).

    Same contract as KIS: place_order, get_order, cancel_order.
    Kiwoom API integration to be implemented later; methods return stub/rejected.
    """

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
                message="dry_run accepted (kiwoom stub)",
                raw={"dry_run": True, "broker": "kiwoom"},
            )
        return OrderResponse(
            status=OrderStatus.REJECTED,
            message="Kiwoom adapter not implemented yet",
            raw={"broker": "kiwoom", "stub": True},
        )

    def get_order(self, query: OrderQuery) -> OrderResponse:
        return OrderResponse(
            status=OrderStatus.UNKNOWN,
            broker_order_id=query.broker_order_id,
            message="Kiwoom get_order not implemented yet",
            raw={"broker": "kiwoom", "stub": True},
        )

    def cancel_order(self, query: OrderQuery) -> OrderResponse:
        return OrderResponse(
            status=OrderStatus.UNKNOWN,
            broker_order_id=query.broker_order_id,
            message="Kiwoom cancel_order not implemented yet",
            raw={"broker": "kiwoom", "stub": True},
        )
