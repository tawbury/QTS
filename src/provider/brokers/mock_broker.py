"""
Mock Broker — tests only.

Production path MUST NOT use MockBroker. Use create_broker_for_execution()
which returns LiveBroker or NoopBroker only. MockBroker is for pytest and
test doubles only; never instantiate in main/execution_loop/production wiring.
"""
from __future__ import annotations

from src.provider.interfaces.broker import BrokerEngine
from src.provider.models.intent import ExecutionIntent
from src.provider.models.response import ExecutionResponse


class MockBroker(BrokerEngine):
    """
    Mock Broker (tests only).

    - 규칙 기반 응답
    - 외부 시스템과 절대 통신하지 않음
    - 프로덕션 경로에서 사용 금지: create_broker_for_execution() 사용
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
