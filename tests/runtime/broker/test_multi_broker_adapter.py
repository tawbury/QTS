"""
Multi-Broker Adapter Pattern tests (Phase 8).

- Registry: register_broker, get_broker, list_broker_ids, has_broker.
- BaseBrokerAdapter: broker_id, place_order/get_order/cancel_order.
- Kiwoom stub: same interface, stub responses.
- BrokerConfig and get_broker_for_config.
"""

from __future__ import annotations

from runtime.broker.adapters import (
    BaseBrokerAdapter,
    BrokerConfig,
    get_broker,
    get_broker_for_config,
    has_broker,
    list_broker_ids,
)
from runtime.broker.adapters.kiwoom_adapter import KiwoomOrderAdapter
from runtime.broker.config import broker_id_from_config
from runtime.broker.order_base import OrderQuery
from runtime.execution.models.order_request import OrderRequest, OrderSide, OrderType
from runtime.execution.models.order_response import OrderStatus


def test_list_broker_ids_includes_kis_and_kiwoom():
    ids = list_broker_ids()
    assert "kis" in ids
    assert "kiwoom" in ids


def test_has_broker():
    assert has_broker("kis") is True
    assert has_broker("kiwoom") is True
    assert has_broker("unknown") is False


def test_get_broker_kiwoom_returns_adapter_with_broker_id():
    adapter = get_broker("kiwoom")
    assert isinstance(adapter, BaseBrokerAdapter)
    assert adapter.broker_id == "kiwoom"
    assert adapter.name() == "Kiwoom"


def test_kiwoom_adapter_dry_run_accepts():
    adapter = KiwoomOrderAdapter()
    req = OrderRequest(
        symbol="005930",
        side=OrderSide.BUY,
        qty=1,
        order_type=OrderType.MARKET,
        dry_run=True,
    )
    resp = adapter.place_order(req)
    assert resp.status == OrderStatus.ACCEPTED
    assert resp.raw and resp.raw.get("broker") == "kiwoom"


def test_kiwoom_adapter_place_order_non_dry_returns_rejected():
    adapter = KiwoomOrderAdapter()
    req = OrderRequest(
        symbol="005930",
        side=OrderSide.BUY,
        qty=1,
        order_type=OrderType.MARKET,
        dry_run=False,
    )
    resp = adapter.place_order(req)
    assert resp.status == OrderStatus.REJECTED
    assert "not implemented" in (resp.message or "").lower()


def test_kiwoom_adapter_get_order_returns_unknown():
    adapter = KiwoomOrderAdapter()
    resp = adapter.get_order(OrderQuery(broker_order_id="ORD-1"))
    assert resp.status == OrderStatus.UNKNOWN
    assert resp.broker_order_id == "ORD-1"


def test_get_broker_kis_requires_broker_arg():
    from tests.runtime.broker.conftest import MockKISOrderClient
    client = MockKISOrderClient()
    adapter = get_broker("kis", broker=client)
    assert adapter.broker_id == "kis"
    assert hasattr(adapter, "place_order")


def test_get_broker_unknown_raises():
    import pytest
    with pytest.raises(KeyError, match="Unknown broker_id"):
        get_broker("unknown_broker")


def test_broker_config_to_kwargs():
    config = BrokerConfig(broker_id="kis", kwargs=(("cano", "12345"),))
    assert config.broker_id == "kis"
    assert config.to_kwargs() == {"cano": "12345"}


def test_get_broker_for_config():
    from tests.runtime.broker.conftest import MockKISOrderClient
    client = MockKISOrderClient()
    config = BrokerConfig(broker_id="kis", kwargs=(("broker", client),))
    adapter = get_broker_for_config(config)
    assert adapter.broker_id == "kis"


def test_broker_id_from_config():
    assert broker_id_from_config(None, None, "kis") == "kis"
    assert broker_id_from_config("KIS", None, "kiwoom") == "kis"
    assert broker_id_from_config(None, "kiwoom", "kis") == "kiwoom"
