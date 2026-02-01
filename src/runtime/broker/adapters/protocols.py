"""
Order client protocol: 공통 주문 API 계약 (Phase 8).

KIS/Kiwoom 클라이언트가 동일한 place_order / get_order / cancel_order 시그니처를 따르도록 정의.
adapters에서 타입 힌트 및 테스트용 Mock에 사용.
"""

from __future__ import annotations

from typing import Any, Protocol


class OrderClientProtocol(Protocol):
    """
    브로커 주문 API 계약 (KIS/Kiwoom 공통).

    place_order(get_order, cancel_order) 시그니처가 동일하므로
    KISClient, KiwoomClient, Mock 클라이언트가 이 Protocol을 구현.
    """

    def place_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        """주문 전송. raw dict 반환 (broker별 필드: rt_cd/return_code, order_no/ODNO 등)."""
        ...

    def get_order(self, params: dict[str, Any]) -> dict[str, Any]:
        """주문 조회. params: order_id 등. raw dict 반환."""
        ...

    def cancel_order(self, params: dict[str, Any]) -> dict[str, Any]:
        """주문 취소. params: order_id. raw dict 반환."""
        ...
