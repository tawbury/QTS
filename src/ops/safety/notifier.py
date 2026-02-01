"""
Phase 7 — Safety Notifier 최소 규격.

근거: docs/arch/07_FailSafe_Architecture.md §9
- Safety 로그 구조: timestamp, safety_code, level, message, pipeline_state, meta (§9.1)
- Fail-Safe 알림: 메시지 템플릿 기반 표준화 (§9.3)
- 의존성 주입: Notifier를 주입하여 테스트 시 NoOp/InMemory 사용 가능
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from shared.timezone_utils import now_kst, Protocol


# --- Safety 이벤트 (Arch §9.1) ---


@dataclass(frozen=True)
class SafetyEvent:
    """Safety 로그/알림용 이벤트. §9.1 필드와 동일."""

    timestamp: str  # ISO format
    safety_code: str
    level: str  # WARNING | FAIL
    message: str
    pipeline_state: str
    meta: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def now(
        cls,
        safety_code: str,
        level: str,
        message: str,
        pipeline_state: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> SafetyEvent:
        ts = now_kst().isoformat()
        return cls(
            timestamp=ts,
            safety_code=safety_code,
            level=level,
            message=message,
            pipeline_state=pipeline_state,
            meta=meta or {},
        )


# --- 메시지 템플릿 (§9.3 표준화) ---


def default_message_template(event: SafetyEvent) -> str:
    """Fail-Safe/Guardrail 알림용 표준 메시지. Slack/Telegram/Email 등에 동일 적용."""
    parts = [
        f"[{event.level}] {event.safety_code}",
        event.message,
        f"pipeline_state={event.pipeline_state}",
    ]
    if event.meta:
        extra = " ".join(f"{k}={v}" for k, v in sorted(event.meta.items()) if v is not None)
        if extra:
            parts.append(extra)
    return " | ".join(parts)


# --- Notifier 프로토콜 (의존성 주입용) ---


class SafetyNotifier(Protocol):
    """Safety 이벤트 알림 최소 규격. 구현체: NoOp, InMemory, Slack/Telegram/Email 등."""

    def notify(self, event: SafetyEvent) -> None:
        """이벤트 기록/알림 전송."""
        ...


# --- 기본 구현체 ---


class NoOpNotifier:
    """아무 동작 없음. 기본값 및 테스트용."""

    def notify(self, event: SafetyEvent) -> None:
        pass


class InMemoryNotifier:
    """이벤트를 메모리에 누적. 테스트/검증용."""

    def __init__(self) -> None:
        self.events: List[SafetyEvent] = []

    def notify(self, event: SafetyEvent) -> None:
        self.events.append(event)

    def clear(self) -> None:
        self.events.clear()

    def last_event(self) -> Optional[SafetyEvent]:
        return self.events[-1] if self.events else None
