from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Union

from runtime.execution.interfaces.broker import BrokerEngine
from runtime.execution.models.response import ExecutionResponse
from runtime.pipeline.adapters.ops_decision_to_intent import (
    OpsDecisionToIntentAdapter,
    JsonLike,
)


@dataclass(frozen=True)
class ExecutionRouteResult:
    """
    Phase 1 pipeline output:
    - raw ops payload (normalized dict)
    - response from broker engine
    """
    ops_payload: Dict[str, Any]
    response: ExecutionResponse


class ExecutionRoute:
    """
    Phase 1 Execution Route

    Input:
    - ops decision output (dict or json string)

    Flow:
    ops_payload -> ExecutionIntent -> BrokerEngine -> ExecutionResponse

    Constraints:
    - No ops import
    - No API calls
    - Synchronous and deterministic
    """

    def __init__(self, broker: BrokerEngine, adapter: OpsDecisionToIntentAdapter | None = None) -> None:
        self._broker = broker
        self._adapter = adapter or OpsDecisionToIntentAdapter()

    def run_once(self, ops_payload: JsonLike) -> ExecutionRouteResult:
        parsed = self._adapter.from_payload(ops_payload)
        response = self._broker.submit_intent(parsed.intent)
        return ExecutionRouteResult(ops_payload=parsed.raw, response=response)
