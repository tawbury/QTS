"""Stage 6: EmergencyEscape — 긴급 탈출."""
from __future__ import annotations

import logging
from typing import Any, Optional

from src.execution.contracts import (
    EscapeResult,
    ExecutionAlert,
    ExecutionContext,
    SplitOrder,
    SplitOrderStatus,
)

logger = logging.getLogger(__name__)


class EmergencyEscapeStage:
    """긴급 탈출 단계 — 미체결 취소 + Safety 통보."""

    def __init__(self, broker_adapter: Optional[Any] = None) -> None:
        self._broker = broker_adapter

    async def execute(
        self, ctx: ExecutionContext, reason: str
    ) -> tuple[EscapeResult, list[ExecutionAlert]]:
        alerts: list[ExecutionAlert] = []

        # 1. 모든 미체결 주문 취소
        cancelled = await self._cancel_pending(ctx.splits)

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

    async def _cancel_pending(self, splits: list[SplitOrder]) -> int:
        cancelled = 0
        for s in splits:
            if s.status in (SplitOrderStatus.PENDING, SplitOrderStatus.SENT, SplitOrderStatus.PARTIALLY_FILLED):
                if self._broker is not None and s.broker_order_id:
                    try:
                        ack = await self._broker.cancel_order(s.broker_order_id)
                        if ack.accepted:
                            s.status = SplitOrderStatus.CANCELLED
                            cancelled += 1
                        else:
                            logger.warning(
                                "브로커 취소 거부: split_id=%s, broker_order_id=%s, reason=%s",
                                s.split_id, s.broker_order_id, ack.reject_reason,
                            )
                            # 거부되어도 로컬 상태는 취소 처리 (긴급 탈출이므로)
                            s.status = SplitOrderStatus.CANCELLED
                            cancelled += 1
                    except Exception:
                        logger.exception(
                            "브로커 취소 중 예외: split_id=%s, broker_order_id=%s",
                            s.split_id, s.broker_order_id,
                        )
                        # 예외 발생해도 로컬 상태는 취소 처리 (긴급 탈출이므로)
                        s.status = SplitOrderStatus.CANCELLED
                        cancelled += 1
                else:
                    # 브로커 어댑터 없거나 broker_order_id 없으면 로컬 상태만 변경
                    s.status = SplitOrderStatus.CANCELLED
                    cancelled += 1
        return cancelled
