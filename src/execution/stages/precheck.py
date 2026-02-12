"""Stage 1: PreCheck — 주문 실행 전 전제 조건 검증."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.execution.contracts import (
    ExecutionAlert,
    OrderDecision,
    PreCheckResult,
)
from src.safety.state import SafetyState


class PreCheckStage:
    """PreCheck 단계 — 5가지 검증 항목."""

    def execute(
        self,
        order: OrderDecision,
        *,
        available_capital: Decimal = Decimal("0"),
        broker_connected: bool = True,
        market_open: bool = True,
        safety_state: SafetyState = SafetyState.NORMAL,
        existing_position_qty: int = 0,
        max_position_qty: int = 10_000,
        daily_trade_count: int = 0,
        daily_trade_limit: int = 100,
    ) -> tuple[PreCheckResult, list[ExecutionAlert]]:
        alerts: list[ExecutionAlert] = []

        # 1. Safety 상태 확인
        if safety_state in (SafetyState.FAIL, SafetyState.LOCKDOWN):
            alerts.append(ExecutionAlert(
                code="FS090",
                severity="FAIL_SAFE",
                message=f"Safety state is {safety_state.value}, execution blocked",
                stage="PRECHECK",
            ))
            return PreCheckResult(passed=False, reason="SAFETY_BLOCKED"), alerts

        # 2. 포지션 유효성 (중복 주문/한도 체크)
        if existing_position_qty + order.qty > max_position_qty:
            return PreCheckResult(passed=False, reason="POSITION_LIMIT_EXCEEDED"), alerts

        # 3. 자본 가용성
        estimated_cost = Decimal(str(order.qty)) * (order.price or Decimal("0"))
        adjusted_qty: Optional[int] = None
        if estimated_cost > 0 and available_capital < estimated_cost:
            if available_capital > 0 and order.price and order.price > 0:
                adjusted_qty = int(available_capital / order.price)
                if adjusted_qty <= 0:
                    return PreCheckResult(passed=False, reason="INSUFFICIENT_CAPITAL"), alerts
                alerts.append(ExecutionAlert(
                    code="GR061",
                    severity="GUARDRAIL",
                    message=f"Capital insufficient, qty reduced {order.qty} → {adjusted_qty}",
                    stage="PRECHECK",
                ))
            else:
                return PreCheckResult(passed=False, reason="INSUFFICIENT_CAPITAL"), alerts

        # 4. 브로커 연결
        if not broker_connected:
            return PreCheckResult(passed=False, reason="BROKER_DISCONNECTED"), alerts

        # 5. 시장 상태
        if not market_open:
            return PreCheckResult(passed=False, reason="MARKET_CLOSED"), alerts

        # 6. 일일 거래 한도
        if daily_trade_count >= daily_trade_limit:
            alerts.append(ExecutionAlert(
                code="GR062",
                severity="GUARDRAIL",
                message=f"Daily trade limit reached ({daily_trade_limit})",
                stage="PRECHECK",
            ))
            return PreCheckResult(passed=False, reason="DAILY_LIMIT_REACHED"), alerts

        return PreCheckResult(
            passed=True,
            order=order,
            adjusted_qty=adjusted_qty,
        ), alerts
