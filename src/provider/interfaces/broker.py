from __future__ import annotations

from abc import ABC, abstractmethod

from src.provider.models.intent import ExecutionIntent
from src.provider.models.response import ExecutionResponse


class BrokerEngine(ABC):
    """
    Broker Engine Interface (Phase 1)

    책임:
    - ExecutionIntent 수신
    - 구조적으로 유효한 ExecutionResponse 반환

    금지:
    - 실주문 전송
    - 가격/잔고 조회
    - 상태 저장
    """

    @abstractmethod
    def submit_intent(self, intent: ExecutionIntent) -> ExecutionResponse:
        """
        Submit execution intent to broker layer.

        Phase 1:
        - 반드시 동기적 응답
        - 외부 통신 금지
        """
        raise NotImplementedError
