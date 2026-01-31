from __future__ import annotations

import json
from hashlib import sha256
from typing import Any, Dict, Optional, Tuple

from src.ops.decision_pipeline.contracts.order_decision import OrderDecision
from src.ops.decision_pipeline.contracts.execution_hint import ExecutionHint

from .execution_context import ExecutionContext
from .execution_guards import apply_execution_guards
from .execution_mode import ExecutionMode
from .execution_result import ExecutionResult, ExecutionStatus
from .iexecution import IExecution


def _safe_to_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    d = getattr(obj, "__dict__", None)
    if isinstance(d, dict):
        return dict(d)
    return {}


def _fingerprint(order: Any, hint: Any) -> str:
    payload = {"order": _safe_to_dict(order), "hint": _safe_to_dict(hint)}
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return sha256(raw.encode("utf-8")).hexdigest()[:16]


class SimExecutor(IExecution):
    """
    Phase 9: SIM Executor (FINAL)

    - Act stage policy: Guard/Fail-Safe 연계로 apply_execution_guards 사용.
    - ExecutionHint.constraints 를 확장 슬롯으로 사용.
    - 시장 로그/검증용 시뮬레이션만 수행(부작용 없음).
    """

    DEFAULT_SLIPPAGE_RATE = 0.0002

    def execute(
        self,
        *,
        order: OrderDecision,
        hint: ExecutionHint,
        context: ExecutionContext,
    ) -> ExecutionResult:

        decision_id = getattr(order, "decision_id", None) or getattr(order, "id", None) or "UNKNOWN"
        fp = _fingerprint(order, hint)

        # 1) Guard/Fail-Safe 연계 (execution_guards와 동일 정책)
        gd = apply_execution_guards(order=order, context=context)
        if gd.blocked_by:
            return ExecutionResult(
                mode=ExecutionMode.SIM.value,
                status=ExecutionStatus.REJECTED.value,
                executed=False,
                decision_id=str(decision_id),
                order_fingerprint=fp,
                blocked_by=gd.blocked_by,
                reason=gd.reason,
                audit=gd.audit or {},
            )

        # 2) action NONE
        action = getattr(order, "action", None)
        if action in (None, "NONE"):
            return ExecutionResult(
                mode=ExecutionMode.SIM.value,
                status=ExecutionStatus.SKIPPED.value,
                executed=False,
                decision_id=str(decision_id),
                order_fingerprint=fp,
                blocked_by=None,
                reason="action is NONE",
                audit={},
            )

        # 3) reference price (ExecutionHint.constraints)
        ref_price = None
        constraints = getattr(hint, "constraints", {})
        if isinstance(constraints, dict):
            v = constraints.get("reference_price")
            if isinstance(v, (int, float)) and v > 0:
                ref_price = float(v)

        if ref_price is None:
            return ExecutionResult(
                mode=ExecutionMode.SIM.value,
                status=ExecutionStatus.REJECTED.value,
                executed=False,
                decision_id=str(decision_id),
                order_fingerprint=fp,
                blocked_by="G_SIM_NO_REFERENCE_PRICE",
                reason="no reference price",
                audit={},
            )

        # 4) simulate fill
        sim = self._simulate_fill(order, context, ref_price)

        return ExecutionResult(
            mode=ExecutionMode.SIM.value,
            status=ExecutionStatus.ACCEPTED.value,
            executed=True,
            decision_id=str(decision_id),
            order_fingerprint=fp,
            blocked_by=None,
            reason=f"sim {sim['result'].lower()}",
            audit={"simulation": sim},
        )

    def _simulate_fill(
        self,
        order: OrderDecision,
        context: ExecutionContext,
        ref_price: float,
    ) -> Dict[str, Any]:

        action = order.action
        requested_qty = int(order.qty)

        slippage_rate = (
            context.risk_limits.get("slippage_rate", self.DEFAULT_SLIPPAGE_RATE)
            if getattr(context, "risk_limits", None) else self.DEFAULT_SLIPPAGE_RATE
        )

        if action == "BUY":
            fill_price = ref_price * (1 + slippage_rate)
        else:
            fill_price = ref_price * (1 - slippage_rate)

        max_fill_qty = (
            context.risk_limits.get("max_fill_qty", requested_qty)
            if getattr(context, "risk_limits", None) else requested_qty
        )

        fill_qty = min(requested_qty, max_fill_qty)
        result = "PARTIAL" if fill_qty < requested_qty else "FILLED"

        return {
            "action": action,
            "reference_price": ref_price,
            "requested_qty": requested_qty,
            "fill_qty": fill_qty,
            "fill_price": fill_price,
            "result": result,
        }
