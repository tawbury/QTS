"""
Intent-to-Order Bridge tests (META-240523-03).
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from runtime.execution.intent_to_order_bridge import (
    OrderAdapterToBrokerEngineAdapter,
    intent_to_order_request,
    order_response_to_execution_response,
)
from runtime.execution.models.intent import ExecutionIntent
from runtime.execution.models.order_request import OrderRequest, OrderSide, OrderType
from runtime.execution.models.order_response import OrderResponse, OrderStatus
from runtime.execution.models.response import ExecutionResponse


def test_intent_to_order_request_noop_returns_none():
    intent = ExecutionIntent(
        intent_id="i1",
        symbol="005930",
        side="BUY",
        quantity=0,
        intent_type="NOOP",
    )
    assert intent_to_order_request(intent) is None


def test_intent_to_order_request_market_buy():
    intent = ExecutionIntent(
        intent_id="i1",
        symbol="005930",
        side="BUY",
        quantity=10,
        intent_type="MARKET",
    )
    req = intent_to_order_request(intent, dry_run=True)
    assert req is not None
    assert req.symbol == "005930"
    assert req.side == OrderSide.BUY
    assert req.qty == 10
    assert req.order_type == OrderType.MARKET
    assert req.dry_run is True
    assert req.client_order_id == "i1"


def test_intent_to_order_request_limit_sell():
    intent = ExecutionIntent(
        intent_id="i2",
        symbol="000660",
        side="SELL",
        quantity=5,
        intent_type="LIMIT",
        metadata={"limit_price": 50000.0},
    )
    req = intent_to_order_request(intent, dry_run=False)
    assert req is not None
    assert req.side == OrderSide.SELL
    assert req.order_type == OrderType.LIMIT
    assert req.limit_price == 50000.0


def test_order_response_to_execution_response_accepted():
    intent = ExecutionIntent(
        intent_id="i1",
        symbol="005930",
        side="BUY",
        quantity=10,
        intent_type="MARKET",
    )
    order_resp = OrderResponse(
        status=OrderStatus.ACCEPTED,
        broker_order_id="ORD-123",
        message="accepted",
    )
    exec_resp = order_response_to_execution_response(order_resp, intent, "kis")
    assert exec_resp.accepted is True
    assert exec_resp.broker == "kis"
    assert exec_resp.intent_id == "i1"


def test_order_response_to_execution_response_rejected():
    intent = ExecutionIntent(
        intent_id="i1",
        symbol="005930",
        side="BUY",
        quantity=10,
        intent_type="MARKET",
    )
    order_resp = OrderResponse(
        status=OrderStatus.REJECTED,
        message="rejected",
    )
    exec_resp = order_response_to_execution_response(order_resp, intent, "kiwoom")
    assert exec_resp.accepted is False
    assert exec_resp.broker == "kiwoom"


def test_order_adapter_to_broker_engine_adapter_noop_intent():
    mock_adapter = MagicMock()
    mock_adapter.broker_id = "kis"
    bridge = OrderAdapterToBrokerEngineAdapter(mock_adapter, broker_id="kis")

    intent = ExecutionIntent(
        intent_id="i1",
        symbol="005930",
        side="BUY",
        quantity=0,
        intent_type="NOOP",
    )
    resp = bridge.submit_intent(intent)

    assert resp.accepted is False
    assert "NOOP" in resp.message
    mock_adapter.place_order.assert_not_called()


def test_order_adapter_to_broker_engine_adapter_place_order():
    mock_adapter = MagicMock()
    mock_adapter.broker_id = "kis"
    mock_adapter.place_order.return_value = OrderResponse(
        status=OrderStatus.ACCEPTED,
        broker_order_id="ORD-456",
        message="ok",
    )
    bridge = OrderAdapterToBrokerEngineAdapter(mock_adapter, broker_id="kis", dry_run=False)

    intent = ExecutionIntent(
        intent_id="i1",
        symbol="005930",
        side="BUY",
        quantity=10,
        intent_type="MARKET",
    )
    resp = bridge.submit_intent(intent)

    assert resp.accepted is True
    assert resp.broker == "kis"
    mock_adapter.place_order.assert_called_once()
    placed_req = mock_adapter.place_order.call_args[0][0]
    assert placed_req.symbol == "005930"
    assert placed_req.qty == 10
    assert placed_req.side == OrderSide.BUY
