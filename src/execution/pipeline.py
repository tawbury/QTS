"""Scalp Execution Pipeline Orchestrator."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.execution.contracts import (
    ExecutionContext,
    ExecutionResult,
    ExecutionState,
    FillEvent,
    OrderDecision,
    SplitConfig,
    SlippageConfig,
)
from src.execution.stages.adaptive_adjust import AdaptiveAdjustStage
from src.execution.stages.async_send import AsyncBrokerProtocol
from src.execution.stages.emergency_escape import EmergencyEscapeStage
from src.execution.stages.fill_monitor import FillMonitorStage
from src.execution.stages.order_split import OrderSplitStage
from src.execution.stages.precheck import PreCheckStage
from src.execution.state_machine import (
    InvalidTransitionError,
    is_terminal,
    transition,
)
from src.safety.state import SafetyState


class ExecutionPipeline:
    """6단계 실행 파이프라인 오케스트레이터.

    동기 실행 모드 (테스트 가능성 우선).
    비동기 브로커 호출은 외부에서 결과를 주입하는 방식으로 처리.
    """

    def __init__(
        self,
        split_config: Optional[SplitConfig] = None,
        slippage_config: Optional[SlippageConfig] = None,
    ) -> None:
        self.precheck = PreCheckStage()
        self.splitter = OrderSplitStage(split_config)
        self.fill_monitor = FillMonitorStage()
        self.adjuster = AdaptiveAdjustStage(slippage_config)
        self.escape = EmergencyEscapeStage()

    def run_precheck(
        self,
        ctx: ExecutionContext,
        *,
        available_capital: Decimal = Decimal("100000000"),
        broker_connected: bool = True,
        market_open: bool = True,
        safety_state: SafetyState = SafetyState.NORMAL,
        daily_trade_count: int = 0,
    ) -> bool:
        """Stage 1: PreCheck 실행. 성공 시 True."""
        transition(ctx, ExecutionState.PRECHECK)

        result, alerts = self.precheck.execute(
            ctx.order,
            available_capital=available_capital,
            broker_connected=broker_connected,
            market_open=market_open,
            safety_state=safety_state,
            daily_trade_count=daily_trade_count,
        )
        ctx.alerts.extend(alerts)

        if not result.passed:
            transition(ctx, ExecutionState.FAILED)
            return False

        return True

    def run_split(self, ctx: ExecutionContext) -> bool:
        """Stage 2: OrderSplit 실행."""
        transition(ctx, ExecutionState.SPLITTING)

        result, alerts = self.splitter.execute(ctx.order)
        ctx.alerts.extend(alerts)
        ctx.splits = result.splits

        if not result.splits:
            transition(ctx, ExecutionState.FAILED)
            return False

        return True

    def process_send_results(
        self, ctx: ExecutionContext, sent_count: int, failed_count: int
    ) -> bool:
        """Stage 3 결과 처리 (비동기 전송 결과를 외부에서 주입)."""
        transition(ctx, ExecutionState.SENDING)

        if sent_count == 0 and failed_count > 0:
            from src.execution.contracts import ExecutionAlert
            ctx.alerts.append(ExecutionAlert(
                code="FS090",
                severity="FAIL_SAFE",
                message=f"All {failed_count} sends failed",
                stage="SENDING",
            ))
            transition(ctx, ExecutionState.FAILED)
            return False

        return True

    def process_fills(
        self, ctx: ExecutionContext, fill_events: list[FillEvent]
    ) -> str:
        """Stage 4: Fill 이벤트 처리. 결과 상태 반환."""
        transition(ctx, ExecutionState.MONITORING)

        result, alerts = self.fill_monitor.process_fills(ctx.splits, fill_events)
        ctx.alerts.extend(alerts)
        ctx.fills.extend(fill_events)

        if result.status == "COMPLETE":
            transition(ctx, ExecutionState.COMPLETE)
        return result.status

    def run_adjust(
        self,
        ctx: ExecutionContext,
        *,
        best_bid: Optional[Decimal] = None,
        best_ask: Optional[Decimal] = None,
    ) -> bool:
        """Stage 5: 가격 조정. 성공 시 True (MONITORING 복귀)."""
        transition(ctx, ExecutionState.ADJUSTING)
        ctx.adjustment_count += 1

        result, alerts = self.adjuster.execute(
            [s for s in ctx.splits if not s.is_terminal],
            best_bid=best_bid,
            best_ask=best_ask,
            adjustment_round=ctx.adjustment_count,
        )
        ctx.alerts.extend(alerts)

        # FS094 발생 시 escape
        if any(a.code == "FS094" for a in alerts):
            return False

        return True

    def run_escape(self, ctx: ExecutionContext, reason: str) -> None:
        """Stage 6: Emergency Escape."""
        transition(ctx, ExecutionState.ESCAPING)

        result, alerts = self.escape.execute(ctx, reason)
        ctx.alerts.extend(alerts)

        transition(ctx, ExecutionState.ESCAPED)

    def build_result(self, ctx: ExecutionContext) -> ExecutionResult:
        """최종 실행 결과 생성."""
        filled = ctx.total_filled_qty
        avg_price: Optional[Decimal] = None
        if filled > 0 and ctx.fills:
            total_cost = sum(
                Decimal(str(f.filled_qty)) * f.filled_price for f in ctx.fills
            )
            avg_price = total_cost / Decimal(str(filled))

        return ExecutionResult(
            state=ctx.state,
            order_id=ctx.order.order_id,
            symbol=ctx.order.symbol,
            side=ctx.order.side,
            requested_qty=ctx.order.qty,
            filled_qty=filled,
            avg_fill_price=avg_price,
            splits_count=len(ctx.splits),
            alerts=ctx.alerts,
        )
