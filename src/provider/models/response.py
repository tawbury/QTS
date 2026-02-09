"""
ExecutionResponse Contract (Broker Layer → Engine)

docs/arch/04_Data_Contract_Spec.md 및 02_Engine_Core_Architecture §7 참조.
BrokerEngine가 ExecutionIntent 수신 후 반환; 체결/주문 상세는 별도 OrderResponse.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.shared.timezone_utils import now_kst


@dataclass(frozen=True)
class ExecutionResponse:
    """
    Execution Response (Contract)

    - Broker Engine이 ExecutionIntent를 수신했음을 명시적으로 응답
    - 필수 필드: intent_id, accepted, broker, message, timestamp
    - 체결/주문 상세는 OrderResponse 등 별도 모델
    """

    intent_id: str
    accepted: bool
    broker: str
    message: str
    timestamp: datetime = field(default_factory=now_kst)
