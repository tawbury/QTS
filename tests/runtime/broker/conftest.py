"""
Broker test fixtures (Phase 8).

- MockKISOrderClient: KISOrderClientProtocol 구현, 회귀 테스트용.
- real_broker 마커: 실 브로커 스모크는 opt-in (pytest -m "" 시 제외).
"""

from __future__ import annotations

from typing import Any, Dict

import pytest


# ----- KIS Order Client mock (contract-compliant) -----


class MockKISOrderClient:
    """
    KISOrderClientProtocol 구현. 예시 구현이 아닌 계약 준수 테스트 더블.

    - place_order(payload) -> dict
    - get_order(params) -> dict
    - cancel_order(params) -> dict
    """

    def __init__(
        self,
        *,
        place_order_ok: bool = True,
        place_order_id: str = "MOCK-ORD-001",
        get_order_status: str = "accepted",
        get_order_filled_qty: int = 0,
        cancel_ok: bool = True,
        raise_on_place_order: bool = False,
    ) -> None:
        self.place_order_ok = place_order_ok
        self.place_order_id = place_order_id
        self.get_order_status = get_order_status
        self.get_order_filled_qty = get_order_filled_qty
        self.cancel_ok = cancel_ok
        self.raise_on_place_order = raise_on_place_order

    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.raise_on_place_order:
            raise AssertionError("dry_run should not call broker")
        if not self.place_order_ok:
            return {"ok": False, "message": "rejected"}
        return {
            "ok": True,
            "order_id": self.place_order_id,
            "ord_no": self.place_order_id,
            "message": "accepted",
        }

    def get_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": self.get_order_status,
            "order_id": params.get("order_id"),
            "filled_qty": self.get_order_filled_qty,
            "avg_fill_price": None,
        }

    def cancel_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": self.cancel_ok, "message": "canceled" if self.cancel_ok else "failed"}


@pytest.fixture
def mock_kis_order_client() -> MockKISOrderClient:
    """Contract-compliant KIS order client for regression tests."""
    return MockKISOrderClient()


@pytest.fixture
def mock_kis_order_client_reject() -> MockKISOrderClient:
    """Client that rejects place_order (for error-path tests)."""
    return MockKISOrderClient(place_order_ok=False)
