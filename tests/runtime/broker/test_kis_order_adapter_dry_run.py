from __future__ import annotations

from runtime.broker.kis.order_adapter import KISOrderAdapter
from runtime.execution.models.order_request import OrderRequest, OrderSide, OrderType
from runtime.execution.models.order_response import OrderStatus

from tests.runtime.broker.conftest import MockKISOrderClient


def test_kis_order_adapter_dry_run_accepts_without_broker_call():
    # Contract-compliant mock that asserts broker is never called when dry_run=True
    client = MockKISOrderClient(raise_on_place_order=True)
    adapter = KISOrderAdapter(client)
    req = OrderRequest(
        symbol="005930",
        side=OrderSide.BUY,
        qty=1,
        order_type=OrderType.MARKET,
        dry_run=True,
    )
    resp = adapter.place_order(req)
    assert resp.status == OrderStatus.ACCEPTED
    assert resp.raw is not None and resp.raw.get("dry_run") is True
