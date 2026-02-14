"""Execution State Machine — 10 states, 전이 규칙, 타임아웃."""
from __future__ import annotations

from datetime import datetime, timezone

from src.execution.contracts import (
    ExecutionAlert,
    ExecutionContext,
    ExecutionState,
    STATE_TRANSITIONS,
    STAGE_TIMEOUTS_MS,
    TERMINAL_STATES,
)


class InvalidTransitionError(Exception):
    """유효하지 않은 상태 전이."""


def can_transition(current: ExecutionState, target: ExecutionState) -> bool:
    """상태 전이 가능 여부 확인."""
    if target == ExecutionState.ESCAPING:
        return current not in TERMINAL_STATES
    return target in STATE_TRANSITIONS.get(current, [])


def transition(ctx: ExecutionContext, target: ExecutionState) -> None:
    """상태 전이 실행."""
    if not can_transition(ctx.state, target):
        raise InvalidTransitionError(
            f"Cannot transition from {ctx.state.value} to {target.value}"
        )
    ctx.state = target
    ctx.stage_start_time = datetime.now(timezone.utc)


def is_terminal(state: ExecutionState) -> bool:
    """종료 상태 여부."""
    return state in TERMINAL_STATES


def check_stage_timeout(ctx: ExecutionContext) -> bool:
    """현재 Stage 타임아웃 확인. True면 타임아웃."""
    if ctx.stage_start_time is None:
        return False

    timeout_ms = STAGE_TIMEOUTS_MS.get(ctx.state.value)
    if timeout_ms is None:
        return False

    elapsed_ms = (
        datetime.now(timezone.utc) - ctx.stage_start_time
    ).total_seconds() * 1_000
    return elapsed_ms > timeout_ms


def handle_stage_timeout(ctx: ExecutionContext) -> ExecutionState:
    """타임아웃 발생 시 다음 상태 결정."""
    if ctx.state == ExecutionState.MONITORING:
        ctx.add_alert(ExecutionAlert(
            code="FS093",
            severity="FAIL_SAFE",
            message="Fill timeout in MONITORING stage",
            stage="MONITORING",
        ))
        return ExecutionState.ADJUSTING

    if ctx.state == ExecutionState.ADJUSTING:
        ctx.add_alert(ExecutionAlert(
            code="FS093",
            severity="FAIL_SAFE",
            message="Adjustment timeout, triggering escape",
            stage="ADJUSTING",
        ))
        return ExecutionState.ESCAPING

    ctx.add_alert(ExecutionAlert(
        code="FS093",
        severity="FAIL_SAFE",
        message=f"Stage {ctx.state.value} timed out",
        stage=ctx.state.value,
    ))
    return ExecutionState.FAILED
