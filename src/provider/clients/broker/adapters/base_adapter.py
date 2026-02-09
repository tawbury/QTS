"""
Multi-Broker Adapter Pattern: base interface (Phase 8).

Arch: docs/arch/08_Broker_Integration_Architecture.md §2.3, §3, §10.1.
- 표준화된 Broker Interface: OrderAdapter 계약 + broker_id.
- 모든 브로커 어댑터는 BaseBrokerAdapter를 상속하여 동일 계약 준수.
- dry_run / client 미설정 시 공통 스텁 응답 헬퍼 제공.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.provider.clients.broker.order_base import OrderAdapter, OrderQuery
from src.provider.models.order_request import OrderRequest
from src.provider.models.order_response import OrderResponse, OrderStatus


class BaseBrokerAdapter(OrderAdapter, ABC):
    """
    Standardized broker adapter base (Multi-Broker Pattern).

    Contract:
    - place_order(OrderRequest) -> OrderResponse
    - get_order(OrderQuery) -> OrderResponse
    - cancel_order(OrderQuery) -> OrderResponse
    - broker_id: str (broker identifier for routing/config)
    """

    @property
    @abstractmethod
    def broker_id(self) -> str:
        """Broker identifier (e.g. 'kis', 'kiwoom'). Used for config and routing."""
        ...

    def name(self) -> str:
        """Human-readable broker name; default is broker_id."""
        return self.broker_id

    def _dry_run_response(self, virtual_order_id: str) -> OrderResponse:
        """dry_run=True 시 공통 수락 응답. 서브클래스 place_order에서 사용."""
        return OrderResponse(
            status=OrderStatus.ACCEPTED,
            broker_order_id=virtual_order_id,
            message=f"dry_run accepted ({self.broker_id})",
            raw={"dry_run": True, "broker": self.broker_id},
        )

    def _stub_rejected(self) -> OrderResponse:
        """client 미설정 시 place_order 공통 거절 응답."""
        return OrderResponse(
            status=OrderStatus.REJECTED,
            message=f"{self.name()} client not configured (stub mode)",
            raw={"broker": self.broker_id, "stub": True},
        )

    def _stub_unknown(self, query: OrderQuery) -> OrderResponse:
        """client 미설정 시 get_order/cancel_order 공통 UNKNOWN 응답."""
        return OrderResponse(
            status=OrderStatus.UNKNOWN,
            broker_order_id=query.broker_order_id,
            message=f"{self.name()} client not configured (stub mode)",
            raw={"broker": self.broker_id, "stub": True},
        )

    @abstractmethod
    def place_order(self, req: OrderRequest) -> OrderResponse:
        ...

    @abstractmethod
    def get_order(self, query: OrderQuery) -> OrderResponse:
        ...

    @abstractmethod
    def cancel_order(self, query: OrderQuery) -> OrderResponse:
        ...
