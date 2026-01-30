"""
Phase 7 — Safety/Risk: Fail-Safe, Guardrail, Anomaly 코드 테이블.

근거: docs/arch/07_FailSafe_Architecture.md
- Fail-Safe: 치명적 오류 → ETEDA 중단, 거래 차단
- Guardrail: 경계 조건 초과 → 거래 제한/기능 차단
- Anomaly: 이상 징후 → 경고 표시, 매매 진행 가능
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# ETEDA 단계 (07_FailSafe_Architecture §7)
ETEDA_STAGE = ("Extract", "Transform", "Evaluate", "Decide", "Act", "Performance")

# --- Fail-Safe 코드 테이블 (Arch §3.3) ---
# code -> (description, primary_eteda_stage)
FAIL_SAFE_TABLE: Dict[str, Tuple[str, str]] = {
    "FS001": ("SchemaMismatchError", "Extract"),
    "FS010": ("RawData 필수 필드 누락", "Extract"),
    "FS020": ("Transform 단계 NaN 발생", "Transform"),
    "FS030": ("Risk 계산 오류", "Evaluate"),
    "FS040": ("Broker Execution 오류", "Act"),
    "FS050": ("Equity <= 0", "Transform"),
    "FS060": ("ETEDA 사이클 시간 초과", "Performance"),
    "FS070": ("Position-Ledger 불일치", "Transform"),
    "FS080": ("시스템 메모리 부족", "Performance"),
    "FS081": ("Capital Pool Error (reserved)", "Evaluate"),
    "FS090": ("Scalp Execution Error (reserved)", "Act"),
    "FS100": ("Micro Risk Loop Error (reserved)", "Evaluate"),
}

# --- Guardrail 코드 테이블 (Arch §4.4) ---
GUARDRAIL_TABLE: Dict[str, Tuple[str, str]] = {
    "GR001": ("Exposure Limit 초과", "Evaluate"),
    "GR010": ("Symbol Weight 초과", "Evaluate"),
    "GR020": ("DailyLoss Warning", "Evaluate"),
    "GR030": ("신호 충돌 감지", "Decide"),
    "GR040": ("포지션 불일치 감지", "Decide"),
    "GR050": ("Capital Pool Violation (reserved)", "Evaluate"),
    "GR060": ("Scalp Execution Violation (reserved)", "Act"),
    "GR070": ("Micro Risk Loop Violation (reserved)", "Evaluate"),
    # Execution gate (Act 단계 최종 관문) — execution_guards와 매핑
    "G_EXE_SYMBOL_EMPTY": ("symbol is empty", "Act"),
    "G_EXE_QTY_NONPOSITIVE": ("qty must be positive", "Act"),
    "G_EXE_TRADING_DISABLED": ("trading_enabled is False", "Act"),
    "G_EXE_KILLSWITCH_ON": ("kill_switch is ON", "Act"),
    "G_EXE_ANOMALY": ("anomaly flags present", "Act"),
}

# --- Anomaly 코드 테이블 (Arch §5.5) ---
ANOMALY_TABLE: Dict[str, Tuple[str, str]] = {
    "AN001": ("가격 급등락", "Extract"),
    "AN010": ("종목/가격 데이터 누락", "Extract"),
    "AN020": ("PnL 급변", "Performance"),
    "AN030": ("Ledger inconsistency", "Transform"),
    "AN040": ("ETEDA Cycle Time 급증", "Performance"),
    "AN050": ("Broker 응답 지연", "Act"),
}


@dataclass(frozen=True)
class CodeInfo:
    code: str
    description: str
    stage: str
    kind: str  # "FAIL_SAFE" | "GUARDRAIL" | "ANOMALY"


def get_failsafe_info(code: str) -> Optional[CodeInfo]:
    if code not in FAIL_SAFE_TABLE:
        return None
    desc, stage = FAIL_SAFE_TABLE[code]
    return CodeInfo(code=code, description=desc, stage=stage, kind="FAIL_SAFE")


def get_guardrail_info(code: str) -> Optional[CodeInfo]:
    if code not in GUARDRAIL_TABLE:
        return None
    desc, stage = GUARDRAIL_TABLE[code]
    return CodeInfo(code=code, description=desc, stage=stage, kind="GUARDRAIL")


def get_anomaly_info(code: str) -> Optional[CodeInfo]:
    if code not in ANOMALY_TABLE:
        return None
    desc, stage = ANOMALY_TABLE[code]
    return CodeInfo(code=code, description=desc, stage=stage, kind="ANOMALY")


def get_code_info(code: str) -> Optional[CodeInfo]:
    """Fail-Safe → Guardrail → Anomaly 순으로 조회."""
    return get_failsafe_info(code) or get_guardrail_info(code) or get_anomaly_info(code)


def codes_by_stage() -> Dict[str, List[str]]:
    """ETEDA 단계별 적용 코드 목록 (07_FailSafe_Architecture §7 적용 위치)."""
    by_stage: Dict[str, List[str]] = {s: [] for s in ETEDA_STAGE}
    for code, (_, stage) in FAIL_SAFE_TABLE.items():
        by_stage.setdefault(stage, []).append(code)
    for code, (_, stage) in GUARDRAIL_TABLE.items():
        by_stage.setdefault(stage, []).append(code)
    for code, (_, stage) in ANOMALY_TABLE.items():
        by_stage.setdefault(stage, []).append(code)
    return by_stage


def message_for(code: str, meta: Optional[Dict[str, object]] = None) -> str:
    """코드에 대한 일관된 메시지 생성 (로깅/알림용)."""
    info = get_code_info(code)
    if not info:
        return f"Safety code: {code}"
    base = f"[{code}] {info.description}"
    if meta:
        parts = [f"{k}={v}" for k, v in sorted(meta.items()) if v is not None]
        if parts:
            base += " | " + ", ".join(parts)
    return base
