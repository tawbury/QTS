from __future__ import annotations

from src.provider.interfaces.broker import BrokerEngine
from src.provider.models.intent import ExecutionIntent
from src.provider.models.response import ExecutionResponse


class NoopBroker(BrokerEngine):
    """
    No-operation Broker

    - Phase 1 기본 Broker
    - 항상 실행을 거부
    - 실매매 구조적 차단 목적
    """

    NAME = "noop-broker"

    def submit_intent(self, intent: ExecutionIntent) -> ExecutionResponse:
        return ExecutionResponse(
            intent_id=intent.intent_id,
            accepted=False,
            broker=self.NAME,
            message="Execution disabled (Phase 1 noop broker)",
        )
