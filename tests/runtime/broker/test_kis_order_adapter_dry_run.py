from __future__ import annotations

from runtime.broker.kis.order_adapter import KISOrderAdapter
from runtime.execution.models.order_request import OrderRequest, OrderSide, OrderType
from runtime.execution.models.order_response import OrderStatus


class DummyKISBroker:
    def place_order(self, payload):
        raise AssertionError("dry_run should not call broker")

    def get_order(self, payload):
        return {"status": "accepted", "filled_qty": 0}

    def cancel_order(self, payload):
        return {"ok": True, "message": "canceled"}


def test_kis_order_adapter_dry_run_accepts_without_broker_call():
    adapter = KISOrderAdapter(DummyKISBroker())
    req = OrderRequest(
        symbol="005930",
        side=OrderSide.BUY,
        qty=1,
        order_type=OrderType.MARKET,
        dry_run=True,
    )
    resp = adapter.place_order(req)
    assert resp.status == OrderStatus.ACCEPTED
    assert resp.raw and resp.raw.get("dry_run") is True
