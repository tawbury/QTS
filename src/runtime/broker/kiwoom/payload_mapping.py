"""
Kiwoom REST API Request/Response normalization (META-240523-03).

KIS payload_mapping.py 패턴 준수:
- Request: OrderRequest → Kiwoom REST payload (au10002 등).
- Response: Kiwoom 응답 → OrderResponse (QTS 표준).
- OrderStatus: broker status/return_code → OrderStatus.
- Error → Fail-Safe (Arch 5.3, 8.1): FS040~FS042.

키움 REST API 스펙 (openapi.kiwoom.com):
- return_code: 0=성공, 그 외 오류.
- return_msg: 응답 메시지.
- 주문 API(au10002 등) 실제 필드명은 공식 스펙 기준으로 정교화 필요.
"""

from __future__ import annotations

from runtime.execution.models.order_request import OrderRequest, OrderSide, OrderType
from runtime.execution.models.order_response import OrderResponse, OrderStatus


# ----- Request normalization (KIS 대비) -----
# Kiwoom REST API 필드명은 공식 스펙 확인 후 조정.

SIDE_TO_KIWOOM: dict[OrderSide, str] = {
    OrderSide.BUY: "2",   # 매수 (키움 REST 스펙 확인)
    OrderSide.SELL: "1",  # 매도
}

ORDER_TYPE_TO_KIWOOM: dict[OrderType, str] = {
    OrderType.MARKET: "00",  # 시장가
    OrderType.LIMIT: "03",   # 지정가 (스펙 확인)
}

MARKET_DEFAULT = "0"  # 0:장내, 1:장외 등 (스펙 확인)


def build_kiwoom_order_payload(
    req: OrderRequest,
    *,
    acnt_no: str = "",
    market: str = MARKET_DEFAULT,
) -> dict:
    """
    OrderRequest → Kiwoom REST order API payload.

    키움 REST API(au10002 등) 필드명에 맞춤.
    실제 스펙 확정 시 필드명·코드값 정교화 필요.
    """
    payload: dict = {
        "stock_cd": req.symbol,
        "ord_qty": str(req.qty),
        "sell_buy_gubun": SIDE_TO_KIWOOM[req.side],
        "ord_gubun": ORDER_TYPE_TO_KIWOOM[req.order_type],
        "ord_prc": "0" if req.order_type == OrderType.MARKET else str(int(req.limit_price or 0)),
        "market_gubun": market,
    }
    if acnt_no:
        payload["acnt_no"] = acnt_no
    if req.client_order_id:
        payload["client_order_id"] = req.client_order_id
    return payload


# ----- Response normalization -----
# Kiwoom REST: return_code=0 성공. status/order_no 등 필드명은 스펙 확인.

KIWOOM_STATUS_TO_ORDER_STATUS: dict[str, OrderStatus] = {
    "0": OrderStatus.ACCEPTED,
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
    "error": OrderStatus.REJECTED,
}

# ----- Broker error code → Fail-Safe (Arch 5.3, 8.1) -----
# 키움 REST: return_code != 0 또는 HTTP 에러.
# Open API 음수 코드 참조 (REST는 다를 수 있음): -300 입력오류, -307 전송실패, -308 과부하.
# KIS와 동일 FS040~FS042 대응.
KIWOOM_ERROR_TO_SAFETY: dict[str | int, str] = {
    # return_code 기반 (양수)
    "1": "FS040",
    1: "FS040",
    "2": "FS040",
    2: "FS040",
    # Open API 음수 코드 참조 (REST API 스펙 확정 시 보완)
    "-300": "FS040",   # 입력값오류
    -300: "FS040",
    "-301": "FS040",   # 계좌비밀번호
    -301: "FS040",
    "-307": "FS040",   # 주문전송실패
    -307: "FS040",
    "-308": "FS042",   # 주문전송과부하 → 주문 지연
    -308: "FS042",
    "-500": "FS040",   # 종목코드오류
    -500: "FS040",
    "timeout": "FS042",
    "TIMEOUT": "FS042",
}
DEFAULT_KIWOOM_ERROR_SAFETY = "FS040"


def map_broker_error_to_safety(
    broker_code: str | int | None = None,
    raw: dict | None = None,
) -> tuple[str, str]:
    """
    키움 브로커 에러 코드 → QTS Fail-Safe 코드 매핑.

    Caller: record_fail_safe(safety_code, message, "Act").
    """
    code = broker_code
    if code is None and raw:
        code = (
            raw.get("return_code")
            or raw.get("error_code")
            or raw.get("code")
            or raw.get("rt_cd")
        )
    if code is not None and isinstance(code, str) and code.lstrip("-").isdigit():
        code = int(code)
    safety = (
        KIWOOM_ERROR_TO_SAFETY.get(code, DEFAULT_KIWOOM_ERROR_SAFETY)
        if code is not None
        else DEFAULT_KIWOOM_ERROR_SAFETY
    )
    msg = f"[{safety}] broker_error (kiwoom)"
    if code is not None:
        msg += f" | broker_code={code}"
    if raw and raw.get("return_msg"):
        msg += f" | {raw['return_msg']}"
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


def parse_kiwoom_place_response(raw: dict) -> tuple[OrderStatus, str | None, str | None]:
    """
    Kiwoom place_order raw response → status, broker_order_id, message.

    return_code=0 → 성공. order_no 등 필드명은 스펙 확인.
    """
    return_code = raw.get("return_code", -1)
    if isinstance(return_code, str) and return_code.isdigit():
        return_code = int(return_code)

    if return_code != 0:
        return (
            OrderStatus.REJECTED,
            raw.get("order_no") or raw.get("order_id"),
            raw.get("return_msg") or raw.get("message") or "rejected",
        )

    order_id = raw.get("order_no") or raw.get("order_id") or raw.get("output", {}).get("order_no")
    if isinstance(order_id, dict):
        order_id = order_id.get("order_no")
    msg = raw.get("return_msg") or raw.get("message") or "accepted"
    return OrderStatus.ACCEPTED, (str(order_id) if order_id is not None else None), msg


def parse_kiwoom_order_response(raw: dict) -> dict:
    """Kiwoom get_order raw response → OrderResponse 필드 dict."""
    raw_status = (
        str(raw.get("status") or raw.get("ord_stt") or raw.get("return_code") or "")
    ).lower()
    if isinstance(raw.get("output"), dict):
        raw_status = raw_status or str(raw["output"].get("ord_stt", "")).lower()
    status = KIWOOM_STATUS_TO_ORDER_STATUS.get(raw_status, OrderStatus.UNKNOWN)

    broker_order_id = raw.get("order_no") or raw.get("order_id") or (raw.get("output") or {}).get("order_no")
    if isinstance(broker_order_id, dict):
        broker_order_id = broker_order_id.get("order_no")
    if broker_order_id is not None:
        broker_order_id = str(broker_order_id)

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
    message = raw.get("return_msg") or raw.get("message")

    return {
        "status": status,
        "broker_order_id": broker_order_id,
        "filled_qty": filled_qty,
        "avg_fill_price": avg_fill_price,
        "message": message,
        "raw": raw,
    }


def raw_to_order_response(raw: dict, *, default_broker_order_id: str | None = None) -> OrderResponse:
    """Kiwoom get_order-style raw dict → OrderResponse."""
    parsed = parse_kiwoom_order_response(raw)
    return OrderResponse(
        status=parsed["status"],
        broker_order_id=parsed["broker_order_id"] or default_broker_order_id,
        message=parsed["message"],
        filled_qty=parsed["filled_qty"],
        avg_fill_price=parsed["avg_fill_price"],
        raw=parsed["raw"],
    )
