"""
우선순위별 이벤트 큐 구현.

근거: docs/arch/sub/17_Event_Priority_Architecture.md §4
- P0: BoundedQueue (BLOCK)
- P1: RingBuffer (DROP_OLDEST)
- P2: CollapsingQueue (COLLAPSE)
- P3: SamplingQueue (SAMPLE 10%)
"""
from __future__ import annotations

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from collections import deque
from typing import Optional

from src.event.contracts import Event, EventPriority, OverflowPolicy
from src.event.config import QueueConfig

logger = logging.getLogger(__name__)


class EventQueue(ABC):
    """이벤트 큐 추상 인터페이스."""

    def __init__(self, config: QueueConfig) -> None:
        self._config = config

    @property
    def priority(self) -> EventPriority:
        return self._config.priority

    @abstractmethod
    async def put(self, event: Event) -> bool:
        """이벤트 추가. 성공 시 True."""
        ...

    @abstractmethod
    async def get(self, timeout_ms: int = 0) -> Optional[Event]:
        """이벤트 꺼내기. timeout_ms=0이면 즉시 반환."""
        ...

    @abstractmethod
    async def get_batch(self, max_count: int, timeout_ms: int) -> list[Event]:
        """배치로 이벤트 꺼내기."""
        ...

    @abstractmethod
    def size(self) -> int:
        ...

    @property
    def capacity(self) -> int:
        return self._config.capacity

    def is_full(self) -> bool:
        return self.size() >= self.capacity

    def utilization(self) -> float:
        """큐 사용률 (0.0 ~ 1.0)."""
        if self.capacity == 0:
            return 0.0
        return self.size() / self.capacity


class BoundedQueue(EventQueue):
    """P0용: 고정 크기 블로킹 큐 (§4.1).

    오버플로우 시 프로듀서가 대기 (BLOCK 정책).
    P0 이벤트는 절대 드롭하지 않음.
    """

    def __init__(self, config: QueueConfig) -> None:
        super().__init__(config)
        self._queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=config.capacity)

    async def put(self, event: Event) -> bool:
        await self._queue.put(event)  # 블로킹: 큐가 풀이면 대기
        return True

    async def get(self, timeout_ms: int = 0) -> Optional[Event]:
        try:
            if timeout_ms <= 0:
                return self._queue.get_nowait()
            return await asyncio.wait_for(
                self._queue.get(), timeout=timeout_ms / 1000.0
            )
        except (asyncio.QueueEmpty, asyncio.TimeoutError):
            return None

    async def get_batch(self, max_count: int, timeout_ms: int) -> list[Event]:
        # P0는 배치 미사용, 하나씩 처리
        event = await self.get(timeout_ms)
        return [event] if event else []

    def size(self) -> int:
        return self._queue.qsize()


class RingBuffer(EventQueue):
    """P1용: 링 버퍼 (§4.2).

    오버플로우 시 가장 오래된 이벤트 드롭 (DROP_OLDEST 정책).
    시장 데이터는 최신 값이 더 중요.
    """

    def __init__(self, config: QueueConfig) -> None:
        super().__init__(config)
        self._buffer: deque[Event] = deque(maxlen=config.capacity)
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Event()
        self._dropped_count: int = 0

    @property
    def dropped_count(self) -> int:
        return self._dropped_count

    async def put(self, event: Event) -> bool:
        async with self._lock:
            if len(self._buffer) >= self._config.capacity:
                self._dropped_count += 1
                # deque(maxlen=N)이 자동으로 왼쪽(가장 오래된) 제거
            self._buffer.append(event)
            self._not_empty.set()
        return True

    async def get(self, timeout_ms: int = 0) -> Optional[Event]:
        if timeout_ms > 0:
            try:
                await asyncio.wait_for(
                    self._not_empty.wait(), timeout=timeout_ms / 1000.0
                )
            except asyncio.TimeoutError:
                return None

        async with self._lock:
            if not self._buffer:
                self._not_empty.clear()
                return None
            event = self._buffer.popleft()
            if not self._buffer:
                self._not_empty.clear()
            return event

    async def get_batch(self, max_count: int, timeout_ms: int) -> list[Event]:
        if timeout_ms > 0:
            try:
                await asyncio.wait_for(
                    self._not_empty.wait(), timeout=timeout_ms / 1000.0
                )
            except asyncio.TimeoutError:
                pass

        async with self._lock:
            count = min(max_count, len(self._buffer))
            batch = [self._buffer.popleft() for _ in range(count)]
            if not self._buffer:
                self._not_empty.clear()
            return batch

    def size(self) -> int:
        return len(self._buffer)


class CollapsingQueue(EventQueue):
    """P2용: 병합 큐 (§4.3).

    같은 event_type의 이벤트를 병합 (COLLAPSE 정책).
    전략 평가 이벤트는 최신 값으로 대체.
    """

    def __init__(self, config: QueueConfig) -> None:
        super().__init__(config)
        # 순서 보존 + 타입별 최신 값 유지
        self._events: dict[str, Event] = {}  # event_type.value → latest Event
        self._order: list[str] = []  # 삽입 순서
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Event()
        self._collapsed_count: int = 0

    @property
    def collapsed_count(self) -> int:
        return self._collapsed_count

    async def put(self, event: Event) -> bool:
        async with self._lock:
            key = event.event_type.value
            if key in self._events:
                # 기존 이벤트를 최신으로 대체 (collapse)
                self._events[key] = event
                self._collapsed_count += 1
            else:
                if len(self._events) >= self._config.capacity:
                    # 용량 초과 시 가장 오래된 것 제거
                    oldest_key = self._order.pop(0)
                    del self._events[oldest_key]
                self._events[key] = event
                self._order.append(key)
            self._not_empty.set()
        return True

    async def get(self, timeout_ms: int = 0) -> Optional[Event]:
        if timeout_ms > 0:
            try:
                await asyncio.wait_for(
                    self._not_empty.wait(), timeout=timeout_ms / 1000.0
                )
            except asyncio.TimeoutError:
                return None

        async with self._lock:
            if not self._order:
                self._not_empty.clear()
                return None
            key = self._order.pop(0)
            event = self._events.pop(key)
            if not self._order:
                self._not_empty.clear()
            return event

    async def get_batch(self, max_count: int, timeout_ms: int) -> list[Event]:
        if timeout_ms > 0:
            try:
                await asyncio.wait_for(
                    self._not_empty.wait(), timeout=timeout_ms / 1000.0
                )
            except asyncio.TimeoutError:
                pass

        async with self._lock:
            count = min(max_count, len(self._order))
            batch: list[Event] = []
            for _ in range(count):
                key = self._order.pop(0)
                batch.append(self._events.pop(key))
            if not self._order:
                self._not_empty.clear()
            return batch

    def size(self) -> int:
        return len(self._events)


class SamplingQueue(EventQueue):
    """P3용: 샘플링 큐 (§4.4).

    오버플로우 시 일부만 샘플링 (SAMPLE 정책, 기본 10%).
    UI/로깅 이벤트는 일부 누락 허용.
    """

    def __init__(self, config: QueueConfig) -> None:
        super().__init__(config)
        self._queue: asyncio.Queue[Event] = asyncio.Queue(
            maxsize=config.capacity
        )
        self._sample_rate: float = config.sample_rate
        self._sampled_out_count: int = 0

    @property
    def sampled_out_count(self) -> int:
        return self._sampled_out_count

    async def put(self, event: Event) -> bool:
        if self._queue.full():
            # 용량 초과 시 샘플링
            if random.random() > self._sample_rate:
                self._sampled_out_count += 1
                return False
            # 공간 확보: 가장 오래된 것 제거
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass

        try:
            self._queue.put_nowait(event)
            return True
        except asyncio.QueueFull:
            self._sampled_out_count += 1
            return False

    async def get(self, timeout_ms: int = 0) -> Optional[Event]:
        try:
            if timeout_ms <= 0:
                return self._queue.get_nowait()
            return await asyncio.wait_for(
                self._queue.get(), timeout=timeout_ms / 1000.0
            )
        except (asyncio.QueueEmpty, asyncio.TimeoutError):
            return None

    async def get_batch(self, max_count: int, timeout_ms: int) -> list[Event]:
        batch: list[Event] = []
        # 첫 이벤트는 timeout 적용
        first = await self.get(timeout_ms)
        if first:
            batch.append(first)
        # 나머지는 즉시 반환 (있는 만큼)
        while len(batch) < max_count:
            event = await self.get(0)
            if event is None:
                break
            batch.append(event)
        return batch

    def size(self) -> int:
        return self._queue.qsize()


def create_queue(config: QueueConfig) -> EventQueue:
    """QueueConfig에 따른 적절한 큐 생성."""
    factories: dict[OverflowPolicy, type[EventQueue]] = {
        OverflowPolicy.BLOCK: BoundedQueue,
        OverflowPolicy.DROP_OLDEST: RingBuffer,
        OverflowPolicy.COLLAPSE: CollapsingQueue,
        OverflowPolicy.SAMPLE: SamplingQueue,
    }
    cls = factories[config.overflow_policy]
    return cls(config)
