"""Stage 6: EmergencyEscape — 긴급 탈출."""
from __future__ import annotations

from src.execution.contracts import (
    EscapeResult,
    ExecutionAlert,
    ExecutionContext,
    SplitOrder,
    SplitOrderStatus,
)


class EmergencyEscapeStage:
    """긴급 탈출 단계 — 미체결 취소 + Safety 통보."""

    def execute(
        self, ctx: ExecutionContext, reason: str
    ) -> tuple[EscapeResult, list[ExecutionAlert]]:
        alerts: list[ExecutionAlert] = []

        # 1. 모든 미체결 주문 취소
        cancelled = self._cancel_pending(ctx.splits)

        # 2. Safety 통보
        alerts.append(ExecutionAlert(
            code="FS092",
            severity="FAIL_SAFE",
            message=f"Emergency escape triggered: {reason}",
            stage="ESCAPING",
        ))

        # 3. ETEDA 일시 정지 필요 여부
        if reason in ("SAFETY_FAIL", "BROKER_DISCONNECT"):
            alerts.append(ExecutionAlert(
                code="FS095",
                severity="FAIL_SAFE",
                message=f"ETEDA suspend recommended: {reason}",
                stage="ESCAPING",
            ))

        return EscapeResult(
            success=True,
            reason=reason,
            cancelled_count=cancelled,
            liquidation_qty=ctx.total_filled_qty,
        ), alerts

    def _cancel_pending(self, splits: list[SplitOrder]) -> int:
        cancelled = 0
        for s in splits:
            if s.status in (SplitOrderStatus.PENDING, SplitOrderStatus.SENT, SplitOrderStatus.PARTIALLY_FILLED):
                s.status = SplitOrderStatus.CANCELLED
                cancelled += 1
        return cancelled
