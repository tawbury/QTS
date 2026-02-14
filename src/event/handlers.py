"""
이벤트 핸들러 인터페이스 및 기본 구현.

근거: docs/arch/sub/17_Event_Priority_Architecture.md §5
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine

from src.event.contracts import Event, EventType

logger = logging.getLogger(__name__)

# 핸들러 콜백 타입
EventCallback = Callable[[Event], Coroutine[Any, Any, None]]


class EventHandler(ABC):
    """이벤트 핸들러 추상 클래스."""

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """단일 이벤트 처리."""
        ...

    async def handle_batch(self, events: list[Event]) -> None:
        """배치 이벤트 처리. 기본: 순차 처리."""
        for event in events:
            await self.handle(event)


class CallbackHandler(EventHandler):
    """콜백 기반 핸들러. 함수를 핸들러로 래핑."""

    def __init__(self, callback: EventCallback, name: str = "") -> None:
        self._callback = callback
        self._name = name or callback.__name__

    async def handle(self, event: Event) -> None:
        await self._callback(event)

    def __repr__(self) -> str:
        return f"CallbackHandler({self._name})"


class TypeFilterHandler(EventHandler):
    """특정 EventType만 처리하는 필터 핸들러."""

    def __init__(
        self, delegate: EventHandler, event_types: set[EventType]
    ) -> None:
        self._delegate = delegate
        self._event_types = event_types

    async def handle(self, event: Event) -> None:
        if event.event_type in self._event_types:
            await self._delegate.handle(event)

    async def handle_batch(self, events: list[Event]) -> None:
        filtered = [e for e in events if e.event_type in self._event_types]
        if filtered:
            await self._delegate.handle_batch(filtered)


class LoggingHandler(EventHandler):
    """디버그용 로깅 핸들러."""

    def __init__(self, level: int = logging.DEBUG) -> None:
        self._level = level

    async def handle(self, event: Event) -> None:
        logger.log(
            self._level,
            "Event: type=%s priority=%s source=%s id=%s",
            event.event_type.value,
            event.priority.name,
            event.source,
            event.event_id[:8],
        )
