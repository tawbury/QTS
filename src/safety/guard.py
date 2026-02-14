"""
Phase 7 — Safety/Risk: Guardrail & Fail-Safe 집약 API.

Guard/Fail-Safe 판단이 산발적 if문으로 퍼지지 않도록 여기서 집약.
- 코드/조건/메시지는 codes.py 테이블 기반으로 일관 관리.
- ETEDA 단계별 체크 포인트: Extract → Transform → Evaluate → Decide → Act.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .codes import (
    get_code_info,
    message_for,
)

# Re-export for callers that need code tables
from . import codes as safety_codes  # noqa: F401


@dataclass(frozen=True)
class SafetyResult:
    """단일 Safety 체크 결과. blocked=True면 파이프라인 중단/거래 차단."""

    code: str
    level: str  # "FAIL_SAFE" | "GUARDRAIL" | "ANOMALY"
    message: str
    stage: str  # ETEDA stage
    meta: Dict[str, Any]
    blocked: bool  # True면 ETEDA 중단/거래 차단

    def to_log_message(self) -> str:
        return message_for(self.code, self.meta)


# --- Extract 단계 (07_FailSafe_Architecture §7.1) ---


def check_extract_safety(
    *,
    schema_allowed: Optional[bool] = None,
    schema_reason: Optional[str] = None,
    raw_data_complete: bool = True,
) -> Optional[SafetyResult]:
    """
    Extract 단계 Safety 체크.
    - 시트 데이터 누락, 스키마 불일치, RawDataContract 생성 실패 → FS001 / FS010
    """
    if schema_allowed is False:
        return SafetyResult(
            code="FS001",
            level="FAIL_SAFE",
            message=message_for("FS001", {"reason": schema_reason or "schema_mismatch"}),
            stage="Extract",
            meta={"schema_reason": schema_reason or "schema_mismatch"},
            blocked=True,
        )
    if not raw_data_complete:
        return SafetyResult(
            code="FS010",
            level="FAIL_SAFE",
            message=message_for("FS010"),
            stage="Extract",
            meta={"raw_data_complete": False},
            blocked=True,
        )
    return None


# --- Transform 단계 (§7.2) ---


def check_transform_safety(
    *,
    has_nan_or_inf: bool = False,
    equity_positive: bool = True,
    position_ledger_consistent: bool = True,
) -> Optional[SafetyResult]:
    """
    Transform 단계 Safety 체크.
    - NaN/Inf, total_equity <= 0, Position-Ledger 불일치 → FS020 / FS050 / FS070
    """
    if has_nan_or_inf:
        return SafetyResult(
            code="FS020",
            level="FAIL_SAFE",
            message=message_for("FS020"),
            stage="Transform",
            meta={"has_nan_or_inf": True},
            blocked=True,
        )
    if not equity_positive:
        return SafetyResult(
            code="FS050",
            level="FAIL_SAFE",
            message=message_for("FS050"),
            stage="Transform",
            meta={"equity_positive": False},
            blocked=True,
        )
    if not position_ledger_consistent:
        return SafetyResult(
            code="FS070",
            level="FAIL_SAFE",
            message=message_for("FS070"),
            stage="Transform",
            meta={"position_ledger_consistent": False},
            blocked=True,
        )
    return None


# --- Evaluate 단계 (§7.3) ---


def check_evaluate_safety(
    *,
    risk_ok: bool = True,
    risk_error_message: Optional[str] = None,
) -> Optional[SafetyResult]:
    """
    Evaluate 단계 Safety 체크.
    - Risk Engine 오류, 대량 신호 충돌 등 → FS030
    """
    if not risk_ok:
        return SafetyResult(
            code="FS030",
            level="FAIL_SAFE",
            message=message_for("FS030", {"detail": risk_error_message}),
            stage="Evaluate",
            meta={"risk_ok": False, "detail": risk_error_message},
            blocked=True,
        )
    return None


# --- Decide 단계 (§7.4) ---


def check_decide_safety(
    *,
    risk_approved: bool = True,
    final_qty_positive: bool = True,
    price_info_consistent: bool = True,
) -> Optional[SafetyResult]:
    """
    Decide 단계 Safety 체크.
    - Risk 승인 불가, final_qty <= 0, Price 정보 불일치 → Guardrail/Fail-Safe
    """
    if not risk_approved:
        return SafetyResult(
            code="GR030",
            level="GUARDRAIL",
            message=message_for("GR030"),
            stage="Decide",
            meta={"risk_approved": False},
            blocked=True,
        )
    if not final_qty_positive:
        return SafetyResult(
            code="G_EXE_QTY_NONPOSITIVE",
            level="GUARDRAIL",
            message=message_for("G_EXE_QTY_NONPOSITIVE"),
            stage="Decide",
            meta={"final_qty_positive": False},
            blocked=True,
        )
    if not price_info_consistent:
        return SafetyResult(
            code="GR040",
            level="GUARDRAIL",
            message=message_for("GR040"),
            stage="Decide",
            meta={"price_info_consistent": False},
            blocked=True,
        )
    return None


# --- Act 단계 (§7.5) ---


def check_act_safety(
    *,
    broker_ok: bool = True,
    execution_result_complete: bool = True,
    consecutive_failures: int = 0,
    max_failures: int = 3,
) -> Optional[SafetyResult]:
    """
    Act 단계 Safety 체크.
    - Broker 응답 오류, ExecutionResult 누락, 주문 실패 반복 → FS040
    """
    if not broker_ok:
        return SafetyResult(
            code="FS040",
            level="FAIL_SAFE",
            message=message_for("FS040"),
            stage="Act",
            meta={"broker_ok": False},
            blocked=True,
        )
    if not execution_result_complete:
        return SafetyResult(
            code="FS040",
            level="FAIL_SAFE",
            message=message_for("FS040", {"reason": "execution_result_incomplete"}),
            stage="Act",
            meta={"execution_result_complete": False},
            blocked=True,
        )
    if consecutive_failures >= max_failures:
        return SafetyResult(
            code="FS040",
            level="FAIL_SAFE",
            message=message_for(
                "FS040",
                {"consecutive_failures": consecutive_failures, "max_failures": max_failures},
            ),
            stage="Act",
            meta={
                "consecutive_failures": consecutive_failures,
                "max_failures": max_failures,
            },
            blocked=True,
        )
    return None


def safety_result_from_guard_code(
    code: str,
    *,
    stage: str = "Act",
    meta: Optional[Dict[str, Any]] = None,
    blocked: bool = True,
) -> SafetyResult:
    """
    execution_guards 등에서 사용하는 Guard 코드(G_EXE_*)를 SafetyResult로 변환.
    메시지/코드 일관성 유지.
    """
    info = get_code_info(code)
    level = info.kind if info else "GUARDRAIL"
    msg = message_for(code, meta or {})
    return SafetyResult(
        code=code,
        level=level,
        message=msg,
        stage=stage,
        meta=meta or {},
        blocked=blocked,
    )
