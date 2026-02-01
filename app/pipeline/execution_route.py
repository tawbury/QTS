from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from app.execution.interfaces.broker import BrokerEngine
from app.execution.models.response import ExecutionResponse
from app.pipeline.adapters.ops_decision_to_intent import (
    OpsDecisionToIntentAdapter,
    JsonLike,
)


@dataclass(frozen=True)
class ExecutionRouteResult:
    """
    Phase 3 Execution Route output.

    Contains:
    - ops_payload: normalized ops decision payload (raw dict)
    - response: execution-layer response (Order / Execution result)

    This object is a terminal artifact of Phase 3.
    """
    ops_payload: Dict[str, Any]
    response: ExecutionResponse


class ExecutionRoute:
    """
    Phase 3 Execution Route (Enforcing)

    Purpose:
    - Bridge between ops-originated decisions and runtime execution.
    - Provide a deterministic, single-pass execution flow.

    Input:
    - ops decision output (dict or JSON-like payload)

    Flow:
    ops_payload
        -> ExecutionIntent (via OpsDecisionToIntentAdapter)
        -> BrokerEngine (execution abstraction)
        -> ExecutionResponse

    Responsibilities:
    - Payload normalization
    - Intent transformation
    - Delegation to execution engine

    Explicitly forbidden:
    - Importing ops modules
    - Direct API / broker calls
    - Retry, loop, or scheduling logic
    - Risk or strategy judgment

    Notes:
    - This route is intentionally synchronous and stateless.
    - It is a stable boundary and MUST NOT be modified in Phase 4.
    """

    def __init__(
        self,
        broker: BrokerEngine,
        adapter: OpsDecisionToIntentAdapter | None = None,
    ) -> None:
        self._broker = broker
        self._adapter = adapter or OpsDecisionToIntentAdapter()

    def run_once(self, ops_payload: JsonLike) -> ExecutionRouteResult:
        """
        Execute a single deterministic execution pass.

        This method represents the final execution boundary
        established in Phase 3.

        Parameters:
        - ops_payload: raw ops decision payload (dict or json-like)

        Returns:
        - ExecutionRouteResult containing normalized payload and execution response
        """
        parsed = self._adapter.from_payload(ops_payload)
        response = self._broker.submit_intent(parsed.intent)

        return ExecutionRouteResult(
            ops_payload=parsed.raw,
            response=response,
        )
