"""
Kiwoom REST API Request/Response normalization (META-240523-03).

KIS payload_mapping.py 패턴 준수:
- Request: OrderRequest → Kiwoom REST payload (au10002 등).
- Response: Kiwoom 응답 → OrderResponse (QTS 표준).
- OrderStatus: broker status/return_code → OrderStatus.
- Error → Fail-Safe (Arch 5.3, 8.1): FS040~FS042.

키움 REST API 스펙 (openapi.kiwoom.com/guide/apiguide):
- 주문: POST /api/dostk/ordr, Header api-id: kt10000(매수)/kt10001(매도).
- Body: dmst_stex_tp(KRX/NXT/SOR), stk_cd, ord_qty, ord_uv, trde_tp(0:보통,3:시장가,5:조건부지정가 등).
- return_code: 0=성공, return_msg, ord_no(주문번호).
"""

from __future__ import annotations

from runtime.execution.models.order_request import OrderRequest, OrderSide, OrderType
from runtime.execution.models.order_response import OrderResponse, OrderStatus


# ----- Request normalization (openapi.kiwoom.com 기준) -----
# api-id: kt10000=매수, kt10001=매도 (Header). Body는 stk_cd, ord_uv, trde_tp, dmst_stex_tp.

API_ID_BUY = "kt10000"
API_ID_SELL = "kt10001"

# trde_tp: 0=보통, 3=시장가, 5=조건부지정가, 81=장마감시간외, 6/7=최유리/최우선 등
ORDER_TYPE_TO_TRDE_TP: dict[OrderType, str] = {
    OrderType.MARKET: "3",   # 시장가
    OrderType.LIMIT: "0",    # 지정가(보통)
}

# dmst_stex_tp: 국내거래소구분 KRX/NXT/SOR
DMST_STEX_TP_DEFAULT = "KRX"


def build_kiwoom_order_payload(
    req: OrderRequest,
    *,
    acnt_no: str = "",
    market: str = DMST_STEX_TP_DEFAULT,
) -> dict:
    """
    OrderRequest → Kiwoom REST 주문 Body + _api_id.

    openapi.kiwoom.com: stk_cd, ord_qty, ord_uv, trde_tp, dmst_stex_tp.
    _api_id는 Client에서 Header api-id로 사용 후 제거.
    """
    dmst = market if market in ("KRX", "NXT", "SOR") else DMST_STEX_TP_DEFAULT
    ord_uv = "0" if req.order_type == OrderType.MARKET else str(int(req.limit_price or 0))
    payload: dict = {
        "_api_id": API_ID_BUY if req.side == OrderSide.BUY else API_ID_SELL,
        "dmst_stex_tp": dmst,
        "stk_cd": req.symbol.strip(),
        "ord_qty": str(req.qty),
        "ord_uv": ord_uv,
        "trde_tp": ORDER_TYPE_TO_TRDE_TP.get(req.order_type, "3"),
    }
    if acnt_no:
        payload["acnt_no"] = acnt_no
    if req.client_order_id:
        payload["client_order_id"] = req.client_order_id
    return payload


# ----- Response normalization -----
# Kiwoom REST: return_code=0 성공. ord_no(주문번호), return_msg.

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
            raw.get("ord_no") or raw.get("order_no") or raw.get("order_id"),
            raw.get("return_msg") or raw.get("message") or "rejected",
        )

    order_id = raw.get("ord_no") or raw.get("order_no") or raw.get("order_id") or raw.get("output", {}).get("ord_no")
    if isinstance(order_id, dict):
        order_id = order_id.get("ord_no") or order_id.get("order_no")
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

    broker_order_id = raw.get("ord_no") or raw.get("order_no") or raw.get("order_id") or (raw.get("output") or {}).get("ord_no")
    if isinstance(broker_order_id, dict):
        broker_order_id = broker_order_id.get("ord_no") or broker_order_id.get("order_no")
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
