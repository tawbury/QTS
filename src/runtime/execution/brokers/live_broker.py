from __future__ import annotations

from runtime.execution.interfaces.broker import BrokerEngine
from runtime.execution.models.intent import ExecutionIntent
from runtime.execution.models.response import ExecutionResponse

from runtime.execution.failsafe.consecutive_failure_guard import (
    ConsecutiveFailureGuard,
    ConsecutiveFailurePolicy,
)


class LiveBroker(BrokerEngine):
    """
    Live Broker Engine (Phase E)

    - Adapter is injected
    - Fail-safe based on consecutive failures
    - ExecutionResponse contract is strictly preserved
    """

    def __init__(
        self,
        *,
        adapter,
        max_consecutive_failures: int = 3,
    ) -> None:
        self._adapter = adapter
        self._guard = ConsecutiveFailureGuard(
            ConsecutiveFailurePolicy(max_failures=max_consecutive_failures)
        )

    def submit_intent(self, intent: ExecutionIntent) -> ExecutionResponse:
        if self._guard.blocked:
            resp = ExecutionResponse(
                intent_id=getattr(intent, "id", "unknown"),
                accepted=False,
                broker="failsafe",
                message="blocked: consecutive failures exceeded",
            )
            return resp

        resp = self._adapter.submit_intent(intent)

        if resp.accepted:
            self._guard.on_success()
        else:
            self._guard.on_failure()

        return resp
