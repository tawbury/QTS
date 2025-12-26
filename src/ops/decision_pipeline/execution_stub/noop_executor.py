from __future__ import annotations

from dataclasses import dataclass

from src.ops.decision_pipeline.contracts.order_decision import OrderDecision
from src.ops.decision_pipeline.contracts.execution_hint import ExecutionHint
from .execution_context import ExecutionContext
from .iexecution import ExecutionResult, IExecution


@dataclass(frozen=True, slots=True)
class NoopExecutor(IExecution):
    """
    NoopExecutor

    Phase 7 정책:
    - 실행(Act)은 존재하되, 항상 실행하지 않는다.
    - pipeline은 executor를 호출해도 안전해야 한다.
    """

    reason: str = "Execution intentionally disabled (NOOP)"

    def execute(
        self,
        *,
        order: OrderDecision,
        hint: ExecutionHint,
        context: ExecutionContext,
    ) -> ExecutionResult:
        # Phase 7에서 intended True가 오더라도 실행하지 않는다.
        # (정책 강제: 사람이 잘못 세팅해도 안전)
        _ = order
        _ = hint
        _ = context

        return ExecutionResult(
            status="NOOP",
            executed=False,
            message=self.reason,
        )
