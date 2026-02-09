from __future__ import annotations

from typing import Protocol

from src.provider.models.order_request import OrderRequest
from src.provider.models.order_response import OrderResponse


class OrderExecutor(Protocol):
    """
    Runtime responsibility:
    - Execution Route 관리
    - Adapter 호출
    - 결과 상태 반영/실패 판단 (단, Phase 3에서는 '흐름 검증' 중심)
    """

    def execute(self, req: OrderRequest) -> OrderResponse:
        ...
