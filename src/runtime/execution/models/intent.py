from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass(frozen=True)
class ExecutionIntent:
    """
    QTS Execution Intent

    - Decision 결과를 실행 계층으로 전달하기 위한 구조적 표현
    - API / Broker / 실계좌 개념과 완전히 분리됨
    - Phase 1에서는 '의도 전달'만 담당
    """

    intent_id: str
    symbol: str
    side: str              # BUY / SELL
    quantity: float
    intent_type: str       # MARKET / LIMIT / NOOP 등
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
