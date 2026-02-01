"""
KIS Request/Response normalization and status/error mapping (Phase 8).

Single module for all KIS mapping rules (Arch 08, 07):
- Request: BUY→"02", SELL→"01"; order_type, market code.
- Response: ord_qty→qty, ord_prc→price, rltv_prc→avg_price → OrderResponse.
- OrderStatus: broker status string → OrderStatus (Arch 5.4).
- Broker error code → Fail-Safe code (Arch 5.3, 8.1): 1001→FS040, 3005→FS041, timeout→FS042.
  Caller (e.g. pipeline/guard) should trigger record_fail_safe(safety_code, message, "Act").
"""

from __future__ import annotations

from app.execution.models.order_request import OrderRequest, OrderSide, OrderType
from app.execution.models.order_response import OrderResponse, OrderStatus


# ----- Request normalization (open-trading-api order_cash 기준) -----
# Body: CANO, ACNT_PRDT_CD, PDNO, ORD_DVSN, ORD_QTY, ORD_UNPR, EXCG_ID_DVSN_CD, SLL_TYPE, CNDT_PRIC
# 매수/매도는 tr_id로 구분(0011=매도, 0012=매수). Body에 SLL_BUY_DVSN_CD 없음.

ORDER_TYPE_TO_KIS: dict[OrderType, str] = {
    OrderType.MARKET: "01",
    OrderType.LIMIT: "00",
}

# EXCG_ID_DVSN_CD: 거래소 (KRX 등). market "KR" → "KRX"
EXCG_ID_DVSN_CD_DEFAULT = "KRX"
MARKET_TO_EXCG: dict[str, str] = {"KR": "KRX", "US": "NAS", "": "KRX"}


def build_kis_order_payload(
    req: OrderRequest,
    *,
    cano: str = "",
    acnt_prdt_cd: str = "01",
    market: str = "KR",
) -> dict:
    """
    OrderRequest → KIS order-cash Body (대문자 키) + side(tr_id 선택용).

    open-trading-api: CANO, ACNT_PRDT_CD, PDNO, ORD_DVSN, ORD_QTY, ORD_UNPR,
    EXCG_ID_DVSN_CD, SLL_TYPE, CNDT_PRIC. 매수/매도는 tr_id로 구분.
    """
    excg = MARKET_TO_EXCG.get(market, EXCG_ID_DVSN_CD_DEFAULT)
    payload: dict = {
        "PDNO": req.symbol.strip(),
        "ORD_QTY": str(req.qty),
        "ORD_DVSN": ORDER_TYPE_TO_KIS.get(req.order_type, "00"),
        "ORD_UNPR": "0" if req.order_type == OrderType.MARKET else str(int(req.limit_price or 0)),
        "EXCG_ID_DVSN_CD": excg,
        "SLL_TYPE": "",
        "CNDT_PRIC": "",
        "side": req.side.value.upper(),
        "symbol": req.symbol.strip(),
    }
    if cano:
        payload["CANO"] = cano
    if acnt_prdt_cd:
        payload["ACNT_PRDT_CD"] = acnt_prdt_cd
    return payload


# ----- Response normalization (Arch 5.2, 4.3) -----

# ----- OrderStatus mapping (Arch 5.4, 6.5) -----
# Broker status string → QTS OrderStatus. Single source of truth for status normalization.
KIS_STATUS_TO_ORDER_STATUS: dict[str, OrderStatus] = {
    "accepted": OrderStatus.ACCEPTED,
    "open": OrderStatus.ACCEPTED,
    "pending": OrderStatus.ACCEPTED,
    "filled": OrderStatus.FILLED,
    "partial": OrderStatus.PARTIALLY_FILLED,
    "partially_filled": OrderStatus.PARTIALLY_FILLED,
    "rejected": OrderStatus.REJECTED,
    "cancelled": OrderStatus.CANCELED,
    "canceled": OrderStatus.CANCELED,
    "timeout": OrderStatus.REJECTED,
}

# ----- Broker error code → Fail-Safe (Arch 5.3, 8.1) -----
# 1001 → FS040 (Execution failure), 3005 → FS041 (체결 데이터 누락), timeout → FS042 (주문 지연).
# Trigger rule: when broker returns error, caller should record_fail_safe(safety_code, message, "Act").
KIS_ERROR_TO_SAFETY: dict[str | int, str] = {
    "1001": "FS040",
    1001: "FS040",
    "3005": "FS041",
    3005: "FS041",
    "timeout": "FS042",
    "TIMEOUT": "FS042",
}
DEFAULT_BROKER_ERROR_SAFETY = "FS040"


def map_broker_error_to_safety(
    broker_code: str | int | None = None,
    raw: dict | None = None,
) -> tuple[str, str]:
    """
    Map broker error code to Fail-Safe code and message.

    Arch 5.3: 1001→FS040, 3005→FS041, timeout→FS042.
    Caller should call record_fail_safe(safety_code, message, "Act") when broker fails.

    Args:
        broker_code: Broker error code (e.g. 1001, "3005", "timeout").
        raw: Optional raw response; if broker_code is None, code is taken from raw["error_code"] or raw["code"] or raw["rt_cd"].

    Returns:
        (safety_code, message) e.g. ("FS040", "[FS040] Broker Execution 오류 | broker_code=1001").
    """
    code = broker_code
    if code is None and raw:
        code = raw.get("error_code") or raw.get("code") or raw.get("rt_cd")
    if code is not None and isinstance(code, str) and code.isdigit():
        code = int(code)
    safety = KIS_ERROR_TO_SAFETY.get(code, DEFAULT_BROKER_ERROR_SAFETY) if code is not None else DEFAULT_BROKER_ERROR_SAFETY
    msg = f"[{safety}] broker_error"
    if code is not None:
        msg += f" | broker_code={code}"
    return (safety, msg)


def _parse_int(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _parse_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_kis_place_response(raw: dict) -> tuple[OrderStatus, str | None, str | None]:
    """
    Parse KIS place_order raw response → status, broker_order_id, message.

    open-trading-api: rt_cd (0=성공), msg_cd, msg1, output (ODNO 등).
    """
    rt_cd = raw.get("rt_cd")
    if rt_cd is not None:
        rt_cd = str(rt_cd).strip()
    ok = rt_cd == "0" if rt_cd is not None else raw.get("ok", False)
    if isinstance(ok, str):
        ok = ok.lower() in ("true", "1", "ok", "success")

    output = raw.get("output")
    if isinstance(output, dict):
        order_id = output.get("ODNO") or output.get("ord_no") or output.get("order_no")
    else:
        order_id = raw.get("order_id") or raw.get("ord_no") or raw.get("ODNO")
    if order_id is not None and not isinstance(order_id, str):
        order_id = str(order_id)

    msg = raw.get("msg1") or raw.get("message") or raw.get("msg") or ""

    if not ok:
        return (OrderStatus.REJECTED, order_id, msg or "rejected")
    return (OrderStatus.ACCEPTED, order_id, msg or "accepted")


def parse_kis_order_response(raw: dict) -> dict:
    """
    Parse KIS get_order raw response → fields for OrderResponse (ExecutionResult).

    Arch 5.2: ord_qty→qty, ord_prc→price, rltv_prc→avg_price.
    Returns dict with: status, broker_order_id, filled_qty, avg_fill_price, message, raw.
    """
    # Status mapping (Arch 5.4)
    raw_status = (raw.get("status") or raw.get("ord_stt") or raw.get("output", {}).get("ord_stt") or "").lower()
    if isinstance(raw.get("output"), dict):
        raw_status = raw_status or str(raw["output"].get("ord_stt", "")).lower()
    status = KIS_STATUS_TO_ORDER_STATUS.get(raw_status, OrderStatus.UNKNOWN)

    broker_order_id = raw.get("order_id") or raw.get("ord_no") or (raw.get("output") or {}).get("ord_no")
    if isinstance(broker_order_id, dict):
        broker_order_id = broker_order_id.get("ord_no")
    if broker_order_id is not None:
        broker_order_id = str(broker_order_id)

    # qty / filled (Arch 5.2: ord_qty → qty)
    filled_qty = _parse_int(
        raw.get("filled_qty")
        or raw.get("ord_qty")
        or raw.get("tot_ccld_qty")
        or (raw.get("output") or {}).get("tot_ccld_qty")
    )
    avg_fill_price = _parse_float(
        raw.get("avg_fill_price")
        or raw.get("avg_price")
        or raw.get("rltv_prc")
        or raw.get("ord_prc")
        or (raw.get("output") or {}).get("avg_prc")
    )
    message = raw.get("message") or raw.get("msg")

    return {
        "status": status,
        "broker_order_id": broker_order_id,
        "filled_qty": filled_qty,
        "avg_fill_price": avg_fill_price,
        "message": message,
        "raw": raw,
    }


def raw_to_order_response(raw: dict, *, default_broker_order_id: str | None = None) -> OrderResponse:
    """Build OrderResponse (ExecutionResult contract) from KIS get_order-style raw dict."""
    parsed = parse_kis_order_response(raw)
    return OrderResponse(
        status=parsed["status"],
        broker_order_id=parsed["broker_order_id"] or default_broker_order_id,
        message=parsed["message"],
        filled_qty=parsed["filled_qty"],
        avg_fill_price=parsed["avg_fill_price"],
        raw=parsed["raw"],
    )
