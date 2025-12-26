from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from src.ops.decision_pipeline.contracts.order_decision import OrderDecision
from src.ops.decision_pipeline.contracts.execution_hint import ExecutionHint
from .execution_context import ExecutionContext


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """
    ExecutionResult

    실행 계층 결과 계약.
    Phase 7에서는 항상 "NOOP" 결과를 반환한다.
    """

    status: str  # NOOP / REJECTED / SUBMITTED / ERROR (확장 대비)
    executed: bool
    message: Optional[str] = None

    # 확장 대비: broker_order_id, filled_qty, avg_price 등을 이후 추가 가능


class IExecution(Protocol):
    """
    IExecution

    실행 계층 인터페이스(계약).
    - Phase 7: NoopExecutor만 존재하며 실행은 발생하지 않는다.
    - Phase 8+: 실제 executor가 이 인터페이스를 구현할 수 있다.
    """

    def execute(
        self,
        *,
        order: OrderDecision,
        hint: ExecutionHint,
        context: ExecutionContext,
    ) -> ExecutionResult:
        ...
