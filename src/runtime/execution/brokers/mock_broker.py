from __future__ import annotations

from runtime.execution.interfaces.broker import BrokerEngine
from runtime.execution.models.intent import ExecutionIntent
from runtime.execution.models.response import ExecutionResponse


class MockBroker(BrokerEngine):
    """
    Mock Broker

    - 규칙 기반 응답
    - 외부 시스템과 절대 통신하지 않음
    """

    NAME = "mock-broker"

    def submit_intent(self, intent: ExecutionIntent) -> ExecutionResponse:
        accepted = intent.quantity > 0

        return ExecutionResponse(
            intent_id=intent.intent_id,
            accepted=accepted,
            broker=self.NAME,
            message="Mock execution accepted" if accepted else "Invalid quantity",
        )
