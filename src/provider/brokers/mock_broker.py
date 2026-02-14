"""MockBroker — 테스트 전용 Broker.

quantity > 0이면 수용, 아니면 거부. 프로덕션 경로에서 절대 사용 금지.
"""

from __future__ import annotations

from src.provider.interfaces.broker import BrokerEngine
from src.provider.models.intent import ExecutionIntent
from src.provider.models.response import ExecutionResponse


class MockBroker(BrokerEngine):
    """테스트 전용 Mock Broker. quantity > 0이면 accepted=True."""

    NAME = "mock-broker"

    def submit_intent(self, intent: ExecutionIntent) -> ExecutionResponse:
        accepted = (intent.quantity or 0) > 0
        return ExecutionResponse(
            intent_id=intent.intent_id,
            accepted=accepted,
            broker=self.NAME,
            message="mock accepted" if accepted else "mock rejected: qty <= 0",
        )
