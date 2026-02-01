from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional

from app.execution.models.order_request import OrderRequest
from app.execution.models.order_response import OrderResponse


@dataclass(frozen=True)
class OrderQuery:
    broker_order_id: str


class OrderAdapter(Protocol):
    """
    Phase 3 Contract.
    - 책임: 주문/조회 요청 구성 + 외부 호출 + 응답 파싱
    - 금지: 토큰 관리, 재시도 정책, 실행 판단(리스크/전략)
    """

    def place_order(self, req: OrderRequest) -> OrderResponse:
        ...

    def get_order(self, query: OrderQuery) -> OrderResponse:
        ...

    def cancel_order(self, query: OrderQuery) -> OrderResponse:
        ...
