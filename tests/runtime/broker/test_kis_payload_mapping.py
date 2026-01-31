"""
Tests for KIS request/response normalization (Phase 8).

- Request: OrderRequest → KIS payload (BUY/SELL, order_type, market).
- Response: KIS raw → OrderResponse (ExecutionResult).
"""

from __future__ import annotations

import pytest

from runtime.broker.kis.payload_mapping import (
    DEFAULT_BROKER_ERROR_SAFETY,
    KIS_ERROR_TO_SAFETY,
    MARKET_DEFAULT,
    ORDER_TYPE_TO_KIS,
    SIDE_TO_KIS,
    build_kis_order_payload,
    map_broker_error_to_safety,
    parse_kis_order_response,
    parse_kis_place_response,
    raw_to_order_response,
)
from runtime.execution.models.order_request import OrderRequest, OrderSide, OrderType
from runtime.execution.models.order_response import OrderStatus


# ----- Request normalization -----


def test_side_to_kis_mapping():
    assert SIDE_TO_KIS[OrderSide.BUY] == "02"
    assert SIDE_TO_KIS[OrderSide.SELL] == "01"


def test_order_type_to_kis_mapping():
    assert ORDER_TYPE_TO_KIS[OrderType.MARKET] == "01"
    assert ORDER_TYPE_TO_KIS[OrderType.LIMIT] == "00"


def test_build_kis_order_payload_buy_market():
    req = OrderRequest(
        symbol="005930",
        side=OrderSide.BUY,
        qty=10,
        order_type=OrderType.MARKET,
    )
    payload = build_kis_order_payload(req)
    assert payload["PDNO"] == "005930"
    assert payload["ORD_QTY"] == "10"
    assert payload["SLL_BUY_DVSN"] == "02"
    assert payload["ORD_DVRN"] == "01"
    assert payload["ORD_UNPR"] == "0"
    assert payload["market"] == MARKET_DEFAULT


def test_build_kis_order_payload_sell_limit():
    req = OrderRequest(
        symbol="005930",
        side=OrderSide.SELL,
        qty=5,
        order_type=OrderType.LIMIT,
        limit_price=70000.0,
    )
    payload = build_kis_order_payload(req)
    assert payload["SLL_BUY_DVSN"] == "01"
    assert payload["ORD_DVRN"] == "00"
    assert payload["ORD_UNPR"] == "70000"


def test_build_kis_order_payload_with_account():
    req = OrderRequest(symbol="AAPL", side=OrderSide.BUY, qty=1, order_type=OrderType.MARKET)
    payload = build_kis_order_payload(req, cano="12345", acnt_prdt_cd="01")
    assert payload["CANO"] == "12345"
    assert payload["ACNT_PRDT_CD"] == "01"


# ----- Response normalization (place) -----


def test_parse_kis_place_response_ok():
    raw = {"ok": True, "order_id": "ORD-123", "message": "accepted"}
    status, order_id, msg = parse_kis_place_response(raw)
    assert status == OrderStatus.ACCEPTED
    assert order_id == "ORD-123"
    assert msg == "accepted"


def test_parse_kis_place_response_rejected():
    raw = {"ok": False, "message": "insufficient balance"}
    status, order_id, msg = parse_kis_place_response(raw)
    assert status == OrderStatus.REJECTED
    assert msg == "insufficient balance"


def test_parse_kis_place_response_ord_no():
    raw = {"ok": True, "ord_no": "KIS-456"}
    status, order_id, _ = parse_kis_place_response(raw)
    assert status == OrderStatus.ACCEPTED
    assert order_id == "KIS-456"


# ----- Response normalization (get_order → OrderResponse) -----


def test_parse_kis_order_response_filled():
    raw = {"status": "filled", "order_id": "O1", "filled_qty": 10, "avg_fill_price": 50000.0}
    parsed = parse_kis_order_response(raw)
    assert parsed["status"] == OrderStatus.FILLED
    assert parsed["broker_order_id"] == "O1"
    assert parsed["filled_qty"] == 10
    assert parsed["avg_fill_price"] == 50000.0


def test_parse_kis_order_response_ord_qty_rltv_prc():
    """Arch 5.2: ord_qty→qty, rltv_prc→avg_price."""
    raw = {"ord_stt": "filled", "ord_no": "O2", "tot_ccld_qty": 5, "rltv_prc": 72000.0}
    parsed = parse_kis_order_response(raw)
    assert parsed["status"] == OrderStatus.FILLED
    assert parsed["filled_qty"] == 5
    assert parsed["avg_fill_price"] == 72000.0


def test_parse_kis_order_response_accepted():
    raw = {"status": "accepted", "order_id": "O3", "filled_qty": 0}
    parsed = parse_kis_order_response(raw)
    assert parsed["status"] == OrderStatus.ACCEPTED
    assert parsed["filled_qty"] == 0


def test_raw_to_order_response():
    raw = {"status": "filled", "order_id": "O4", "filled_qty": 3, "avg_fill_price": 100.5}
    resp = raw_to_order_response(raw)
    assert resp.status == OrderStatus.FILLED
    assert resp.broker_order_id == "O4"
    assert resp.filled_qty == 3
    assert resp.avg_fill_price == 100.5
    assert resp.raw is raw


def test_raw_to_order_response_default_broker_order_id():
    raw = {"status": "pending"}  # no order_id
    resp = raw_to_order_response(raw, default_broker_order_id="QUERY-ID")
    assert resp.broker_order_id == "QUERY-ID"


# ----- Broker error → Fail-Safe (Arch 5.3, 8.1) -----


def test_kis_error_to_safety_mapping():
    assert KIS_ERROR_TO_SAFETY.get(1001) == "FS040"
    assert KIS_ERROR_TO_SAFETY.get("1001") == "FS040"
    assert KIS_ERROR_TO_SAFETY.get(3005) == "FS041"
    assert KIS_ERROR_TO_SAFETY.get("3005") == "FS041"
    assert KIS_ERROR_TO_SAFETY.get("timeout") == "FS042"
    assert KIS_ERROR_TO_SAFETY.get("TIMEOUT") == "FS042"


def test_map_broker_error_to_safety_1001():
    code, msg = map_broker_error_to_safety(1001)
    assert code == "FS040"
    assert "1001" in msg


def test_map_broker_error_to_safety_3005():
    code, msg = map_broker_error_to_safety("3005")
    assert code == "FS041"
    assert "3005" in msg


def test_map_broker_error_to_safety_timeout():
    code, msg = map_broker_error_to_safety("timeout")
    assert code == "FS042"


def test_map_broker_error_to_safety_from_raw():
    code, msg = map_broker_error_to_safety(raw={"error_code": 3005})
    assert code == "FS041"
    code2, _ = map_broker_error_to_safety(raw={"rt_cd": "1001"})
    assert code2 == "FS040"


def test_map_broker_error_to_safety_unknown_default_fs040():
    code, msg = map_broker_error_to_safety(9999)
    assert code == DEFAULT_BROKER_ERROR_SAFETY
    assert code == "FS040"
    code2, _ = map_broker_error_to_safety(raw={"msg": "unknown"})
    assert code2 == "FS040"
