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
    - Observer hooks are optional (no-op if None)
    - ExecutionResponse contract is strictly preserved
    """

    def __init__(
        self,
        *,
        adapter,
        max_consecutive_failures: int = 3,
        observer=None,
    ) -> None:
        self._adapter = adapter
        self._observer = observer
        self._guard = ConsecutiveFailureGuard(
            ConsecutiveFailurePolicy(max_failures=max_consecutive_failures)
        )

    def submit_intent(self, intent: ExecutionIntent) -> ExecutionResponse:
        from runtime.observer.live_events import emit

        emit(self._observer, "order_intent", {
            "intent_id": getattr(intent, "id", "unknown"),
        })

        if self._guard.blocked:
            resp = ExecutionResponse(
                intent_id=getattr(intent, "id", "unknown"),
                accepted=False,
                broker="failsafe",
                message="blocked: consecutive failures exceeded",
            )
            emit(self._observer, "failsafe_blocked", {
                "intent_id": resp.intent_id,
                "reason": resp.message,
            })
            return resp

        resp = self._adapter.submit_intent(intent)

        emit(self._observer, "order_response", {
            "intent_id": resp.intent_id,
            "accepted": resp.accepted,
            "broker": resp.broker,
            "message": resp.message,
        })

        if resp.accepted:
            self._guard.on_success()
        else:
            self._guard.on_failure()

        return resp
