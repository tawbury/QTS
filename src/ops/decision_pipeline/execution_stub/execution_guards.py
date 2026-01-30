from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from ops.safety import message_for

from .execution_context import ExecutionContext

# Act 단계 Guard 코드 (Phase 7 — ops.safety.codes.GUARDRAIL_TABLE와 일치)
G_EXE_SYMBOL_EMPTY = "G_EXE_SYMBOL_EMPTY"
G_EXE_QTY_NONPOSITIVE = "G_EXE_QTY_NONPOSITIVE"
G_EXE_TRADING_DISABLED = "G_EXE_TRADING_DISABLED"
G_EXE_KILLSWITCH_ON = "G_EXE_KILLSWITCH_ON"
G_EXE_ANOMALY = "G_EXE_ANOMALY"


@dataclass(frozen=True, slots=True)
class GuardDecision:
    blocked_by: Optional[str] = None
    reason: Optional[str] = None
    audit: Dict[str, Any] = None  # type: ignore[assignment]


def _guard_block(code: str, audit: Dict[str, Any]) -> GuardDecision:
    """중앙 코드 테이블 기반 메시지로 GuardDecision 반환 (Phase 7 집약)."""
    return GuardDecision(code, message_for(code, audit), audit)


def apply_execution_guards(
    *,
    order: Any,
    context: ExecutionContext,
) -> GuardDecision:
    """
    Execution-level final gate.

    Phase 7: Guard/Fail-Safe 코드는 ops.safety.codes 테이블에서 관리.
    Phase 8 필수 규칙:
    - action NONE -> SKIPPED는 executor에서 처리(여기서는 차단 아님)
    - symbol empty -> REJECTED (G_EXE_SYMBOL_EMPTY)
    - qty <= 0 -> REJECTED (G_EXE_QTY_NONPOSITIVE)
    - trading_enabled False -> REJECTED (G_EXE_TRADING_DISABLED)
    - kill_switch True -> REJECTED (G_EXE_KILLSWITCH_ON)
    - anomaly_flags present -> REJECTED (G_EXE_ANOMALY)
    """

    audit: Dict[str, Any] = {}

    symbol = getattr(order, "symbol", None)
    qty = getattr(order, "qty", None)
    action = getattr(order, "action", None)

    audit.update({"action": action, "symbol": symbol, "qty": qty})

    if not symbol:
        return _guard_block(G_EXE_SYMBOL_EMPTY, audit)

    if qty is None or qty <= 0:
        return _guard_block(G_EXE_QTY_NONPOSITIVE, audit)

    if context.trading_enabled is False:
        audit = {**audit, "trading_enabled": False}
        return _guard_block(G_EXE_TRADING_DISABLED, audit)

    if context.kill_switch is True:
        audit = {**audit, "kill_switch": True}
        return _guard_block(G_EXE_KILLSWITCH_ON, audit)

    if context.anomaly_flags:
        audit = {**audit, "anomaly_flags": list(context.anomaly_flags)}
        return _guard_block(G_EXE_ANOMALY, audit)

    return GuardDecision(None, None, audit)
