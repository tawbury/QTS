from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ExecutionResponse:
    """
    Execution Response

    - Broker Engine이 ExecutionIntent를 수신했음을
      명시적으로 응답하기 위한 구조
    - 체결 / 주문 개념 없음
    """

    intent_id: str
    accepted: bool
    broker: str
    message: str
    timestamp: datetime = datetime.now(timezone.utc)
