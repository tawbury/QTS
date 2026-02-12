"""
이벤트 디스패처.

근거: docs/arch/sub/17_Event_Priority_Architecture.md §5, §6
- Strict priority: P0 → P1 → P2 → P3 순서
- P0 이벤트가 있으면 나머지 대기
- Safety State 연동 성능 저하 레벨
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from src.event.config import EventConfig
from src.event.contracts import (
    DegradationLevel,
    Event,
    EventPriority,
)
from src.event.handlers import EventHandler
from src.event.queue import EventQueue, create_queue
from src.safety.state import SafetyState

logger = logging.getLogger(__name__)

# Safety State → Degradation Level 매핑 (§7.2)
SAFETY_TO_DEGRADATION: dict[SafetyState, DegradationLevel] = {
    SafetyState.NORMAL: DegradationLevel.NORMAL,
    SafetyState.WARNING: DegradationLevel.P3_PAUSED,
    SafetyState.FAIL: DegradationLevel.P2_P3_PAUSED,
    SafetyState.LOCKDOWN: DegradationLevel.CRITICAL_ONLY,
}

# 성능 저하 레벨에서 허용되는 우선순위 (§7.1)
_ALLOWED_PRIORITIES: dict[DegradationLevel, set[EventPriority]] = {
    DegradationLevel.NORMAL: {
        EventPriority.P0_CRITICAL,
        EventPriority.P1_HIGH,
        EventPriority.P2_MEDIUM,
        EventPriority.P3_LOW,
    },
    DegradationLevel.P3_PAUSED: {
        EventPriority.P0_CRITICAL,
        EventPriority.P1_HIGH,
        EventPriority.P2_MEDIUM,
    },
    DegradationLevel.P2_P3_PAUSED: {
        EventPriority.P0_CRITICAL,
        EventPriority.P1_HIGH,
    },
    DegradationLevel.CRITICAL_ONLY: {
        EventPriority.P0_CRITICAL,
    },
}


class EventDispatcher:
    """이벤트 라우팅 및 핸들러 관리.

    - dispatch(): 이벤트를 우선순위별 큐로 라우팅
    - start()/stop(): 비동기 컨슈머 태스크 관리
    - 성능 저하 레벨에 따라 저우선순위 이벤트 차단
    """

    def __init__(self, config: Optional[EventConfig] = None) -> None:
        self._config = config or EventConfig()
        self._queues: dict[EventPriority, EventQueue] = {}
        self._handlers: dict[EventPriority, list[EventHandler]] = {
            p: [] for p in EventPriority
        }
        self._degradation_level = DegradationLevel.NORMAL
        self._running = False
        self._tasks: list[asyncio.Task[None]] = []
        self._dispatch_count: int = 0
        self._reject_count: int = 0

        # 큐 초기화
        for priority, qc in self._config.queue_configs.items():
            self._queues[priority] = create_queue(qc)

    @property
    def degradation_level(self) -> DegradationLevel:
        return self._degradation_level

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def dispatch_count(self) -> int:
        return self._dispatch_count

    @property
    def reject_count(self) -> int:
        return self._reject_count

    def set_degradation_level(self, level: DegradationLevel) -> None:
        """성능 저하 레벨 수동 설정."""
        if level != self._degradation_level:
            logger.info(
                "Degradation level: %s → %s",
                self._degradation_level.value,
                level.value,
            )
            self._degradation_level = level

    def apply_safety_state(self, safety_state: SafetyState) -> None:
        """Safety State에 따른 성능 저하 레벨 자동 설정 (§7.2)."""
        level = SAFETY_TO_DEGRADATION[safety_state]
        self.set_degradation_level(level)

    def register_handler(
        self, priority: EventPriority, handler: EventHandler
    ) -> None:
        """핸들러 등록."""
        self._handlers[priority].append(handler)

    def is_priority_allowed(self, priority: EventPriority) -> bool:
        """현재 성능 저하 레벨에서 해당 우선순위가 허용되는지."""
        return priority in _ALLOWED_PRIORITIES[self._degradation_level]

    async def dispatch(self, event: Event) -> bool:
        """이벤트를 적절한 큐로 라우팅.

        Returns:
            True: 큐에 성공적으로 추가됨
            False: 성능 저하로 인해 차단됨
        """
        if not self.is_priority_allowed(event.priority):
            self._reject_count += 1
            return False

        queue = self._queues.get(event.priority)
        if queue is None:
            logger.warning("No queue for priority %s", event.priority.name)
            self._reject_count += 1
            return False

        result = await queue.put(event)
        if result:
            self._dispatch_count += 1
        return result

    async def start(self) -> None:
        """디스패처 시작: 각 우선순위별 컨슈머 태스크 생성."""
        if self._running:
            return
        self._running = True
        logger.info("EventDispatcher starting")

        # P0: 전용 컨슈머 (1개, strict priority)
        self._tasks.append(
            asyncio.create_task(
                self._consume_p0(), name="event-consumer-p0"
            )
        )
        # P1: 배치 컨슈머
        self._tasks.append(
            asyncio.create_task(
                self._consume_batch(EventPriority.P1_HIGH),
                name="event-consumer-p1",
            )
        )
        # P2: 배치 컨슈머
        self._tasks.append(
            asyncio.create_task(
                self._consume_batch(EventPriority.P2_MEDIUM),
                name="event-consumer-p2",
            )
        )
        # P3: 배치 컨슈머
        self._tasks.append(
            asyncio.create_task(
                self._consume_batch(EventPriority.P3_LOW),
                name="event-consumer-p3",
            )
        )

    async def stop(self) -> None:
        """디스패처 중지 (graceful shutdown)."""
        if not self._running:
            return
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("EventDispatcher stopped")

    async def _consume_p0(self) -> None:
        """P0 전용 컨슈머: 이벤트 하나씩 즉시 처리."""
        queue = self._queues[EventPriority.P0_CRITICAL]
        while self._running:
            event = await queue.get(timeout_ms=100)
            if event is None:
                continue
            await self._handle_event(EventPriority.P0_CRITICAL, event)

    async def _consume_batch(self, priority: EventPriority) -> None:
        """배치 컨슈머: 설정된 배치 크기/타임아웃으로 처리."""
        queue = self._queues[priority]
        qc = self._config.queue_configs[priority]
        while self._running:
            if not self.is_priority_allowed(priority):
                await asyncio.sleep(0.5)
                continue

            events = await queue.get_batch(
                max_count=qc.batch_size,
                timeout_ms=qc.batch_timeout_ms or 100,
            )
            if not events:
                continue
            await self._handle_batch(priority, events)

    async def _handle_event(
        self, priority: EventPriority, event: Event
    ) -> None:
        """단일 이벤트를 등록된 핸들러들에게 전달."""
        for handler in self._handlers[priority]:
            try:
                await handler.handle(event)
            except Exception:
                logger.exception(
                    "Handler error: priority=%s event=%s",
                    priority.name,
                    event.event_type.value,
                )

    async def _handle_batch(
        self, priority: EventPriority, events: list[Event]
    ) -> None:
        """배치 이벤트를 등록된 핸들러들에게 전달."""
        for handler in self._handlers[priority]:
            try:
                await handler.handle_batch(events)
            except Exception:
                logger.exception(
                    "Handler batch error: priority=%s count=%d",
                    priority.name,
                    len(events),
                )

    def queue_stats(self) -> dict[str, dict[str, int | float]]:
        """큐 상태 통계."""
        stats: dict[str, dict[str, int | float]] = {}
        for priority, queue in self._queues.items():
            stats[priority.name] = {
                "size": queue.size(),
                "capacity": queue.capacity,
                "utilization": round(queue.utilization(), 4),
            }
        return stats
