"""
ExecutionIntent Contract (Engine ↔ Broker Layer)

docs/arch/04_Data_Contract_Spec.md 및 02_Engine_Core_Architecture §7 참조.
Trading Engine → BrokerEngine 전달용; API/실계좌와 분리된 구조적 표현.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from src.shared.timezone_utils import now_kst


@dataclass(frozen=True)
class ExecutionIntent:
    """
    QTS Execution Intent (Contract)

    - Decision 결과를 실행 계층으로 전달하기 위한 구조적 표현
    - API / Broker / 실계좌 개념과 완전히 분리됨
    - 필수 필드: intent_id, symbol, side(BUY/SELL), quantity, intent_type(MARKET/LIMIT/NOOP)
    """

    intent_id: str
    symbol: str
    side: str              # BUY / SELL
    quantity: float
    intent_type: str       # MARKET / LIMIT / NOOP 등
    created_at: datetime = field(default_factory=now_kst)
    metadata: Dict[str, Any] = field(default_factory=dict)
