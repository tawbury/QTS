"""
Multi-Broker Adapter Pattern: base interface (Phase 8).

Arch: docs/arch/08_Broker_Integration_Architecture.md §2.3, §3, §10.1.
- 표준화된 Broker Interface: OrderAdapter 계약 + broker_id.
- 모든 브로커 어댑터는 BaseBrokerAdapter를 상속하여 동일 계약 준수.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from runtime.broker.order_base import OrderAdapter, OrderQuery
from runtime.execution.models.order_request import OrderRequest
from runtime.execution.models.order_response import OrderResponse


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

    @abstractmethod
    def place_order(self, req: OrderRequest) -> OrderResponse:
        ...

    @abstractmethod
    def get_order(self, query: OrderQuery) -> OrderResponse:
        ...

    @abstractmethod
    def cancel_order(self, query: OrderQuery) -> OrderResponse:
        ...
