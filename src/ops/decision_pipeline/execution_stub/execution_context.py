from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """
    ExecutionContext

    '실행'을 수행하지 않더라도, 실행 레이어가 소비할 수 있는 최소 컨텍스트 계약.
    Phase 7에서는 NoopExecutor가 이 컨텍스트를 받아도 아무것도 하지 않는다.

    Design:
    - broker/account는 Optional (미래 확장 대비)
    - request_id는 트레이싱/로그 상관관계 용도
    - metadata는 확장 필드(스키마 파손 최소화)
    """

    request_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=_utcnow)

    broker: Optional[str] = None
    account: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "created_at": self.created_at.astimezone(timezone.utc).isoformat(),
            "broker": self.broker,
            "account": self.account,
            "metadata": self.metadata,
        }
