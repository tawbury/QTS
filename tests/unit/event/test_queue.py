"""이벤트 큐 구현 테스트."""
import asyncio

import pytest

from src.event.config import QueueConfig
from src.event.contracts import (
    Event,
    EventPriority,
    EventType,
    OverflowPolicy,
    create_event,
)
from src.event.queue import (
    BoundedQueue,
    CollapsingQueue,
    RingBuffer,
    SamplingQueue,
    create_queue,
)


def _make_event(
    event_type: EventType = EventType.FILL_CONFIRMED,
) -> Event:
    return create_event(event_type, source="test")


@pytest.fixture
def p0_config() -> QueueConfig:
    return QueueConfig(
        priority=EventPriority.P0_CRITICAL,
        capacity=5,
        overflow_policy=OverflowPolicy.BLOCK,
    )


@pytest.fixture
def p1_config() -> QueueConfig:
    return QueueConfig(
        priority=EventPriority.P1_HIGH,
        capacity=5,
        overflow_policy=OverflowPolicy.DROP_OLDEST,
        batch_size=3,
        batch_timeout_ms=10,
    )


@pytest.fixture
def p2_config() -> QueueConfig:
    return QueueConfig(
        priority=EventPriority.P2_MEDIUM,
        capacity=5,
        overflow_policy=OverflowPolicy.COLLAPSE,
    )


@pytest.fixture
def p3_config() -> QueueConfig:
    return QueueConfig(
        priority=EventPriority.P3_LOW,
        capacity=5,
        overflow_policy=OverflowPolicy.SAMPLE,
        sample_rate=0.5,
    )


class TestBoundedQueue:
    """P0 BoundedQueue 테스트."""

    @pytest.mark.asyncio
    async def test_put_and_get(self, p0_config: QueueConfig):
        q = BoundedQueue(p0_config)
        event = _make_event()
        await q.put(event)
        assert q.size() == 1
        result = await q.get()
        assert result is not None
        assert result.event_id == event.event_id
        assert q.size() == 0

    @pytest.mark.asyncio
    async def test_get_empty_returns_none(self, p0_config: QueueConfig):
        q = BoundedQueue(p0_config)
        result = await q.get(timeout_ms=10)
        assert result is None

    @pytest.mark.asyncio
    async def test_capacity(self, p0_config: QueueConfig):
        q = BoundedQueue(p0_config)
        assert q.capacity == 5

    @pytest.mark.asyncio
    async def test_is_full(self, p0_config: QueueConfig):
        q = BoundedQueue(p0_config)
        for _ in range(5):
            await q.put(_make_event())
        assert q.is_full()

    @pytest.mark.asyncio
    async def test_utilization(self, p0_config: QueueConfig):
        q = BoundedQueue(p0_config)
        assert q.utilization() == 0.0
        await q.put(_make_event())
        assert q.utilization() == pytest.approx(0.2)


class TestRingBuffer:
    """P1 RingBuffer 테스트."""

    @pytest.mark.asyncio
    async def test_drop_oldest_on_overflow(self, p1_config: QueueConfig):
        q = RingBuffer(p1_config)
        events = []
        for i in range(7):  # capacity=5, 2개 초과
            e = _make_event(EventType.PRICE_TICK)
            events.append(e)
            await q.put(e)
        assert q.size() == 5
        assert q.dropped_count == 2
        # 가장 오래된 2개가 드롭되었으므로 첫 번째 get은 3번째 이벤트
        result = await q.get()
        assert result is not None
        assert result.event_id == events[2].event_id

    @pytest.mark.asyncio
    async def test_get_batch(self, p1_config: QueueConfig):
        q = RingBuffer(p1_config)
        for _ in range(3):
            await q.put(_make_event(EventType.PRICE_TICK))
        batch = await q.get_batch(max_count=2, timeout_ms=10)
        assert len(batch) == 2
        assert q.size() == 1


class TestCollapsingQueue:
    """P2 CollapsingQueue 테스트."""

    @pytest.mark.asyncio
    async def test_collapse_same_type(self, p2_config: QueueConfig):
        q = CollapsingQueue(p2_config)
        e1 = create_event(EventType.STRATEGY_EVALUATE, payload={"v": 1})
        e2 = create_event(EventType.STRATEGY_EVALUATE, payload={"v": 2})
        await q.put(e1)
        await q.put(e2)
        # 같은 타입이므로 1개로 병합
        assert q.size() == 1
        assert q.collapsed_count == 1
        result = await q.get()
        assert result is not None
        assert result.payload["v"] == 2  # 최신 값

    @pytest.mark.asyncio
    async def test_different_types_not_collapsed(self, p2_config: QueueConfig):
        q = CollapsingQueue(p2_config)
        await q.put(create_event(EventType.STRATEGY_EVALUATE))
        await q.put(create_event(EventType.RISK_EVALUATE))
        assert q.size() == 2
        assert q.collapsed_count == 0

    @pytest.mark.asyncio
    async def test_capacity_overflow(self, p2_config: QueueConfig):
        q = CollapsingQueue(p2_config)
        # 용량=5, 서로 다른 6개 타입 넣기
        types = [
            EventType.STRATEGY_EVALUATE,
            EventType.RISK_EVALUATE,
            EventType.PORTFOLIO_EVALUATE,
            EventType.INDICATOR_UPDATE,
            EventType.SIGNAL_GENERATED,
            EventType.ETEDA_CYCLE_START,
        ]
        for t in types:
            await q.put(create_event(t))
        assert q.size() == 5  # capacity 유지


class TestSamplingQueue:
    """P3 SamplingQueue 테스트."""

    @pytest.mark.asyncio
    async def test_basic_put_get(self, p3_config: QueueConfig):
        q = SamplingQueue(p3_config)
        event = _make_event(EventType.LOG_WRITE)
        result = await q.put(event)
        assert result is True
        got = await q.get()
        assert got is not None

    @pytest.mark.asyncio
    async def test_sampling_on_overflow(self, p3_config: QueueConfig):
        """용량 초과 시 일부 이벤트가 샘플링 아웃됨."""
        q = SamplingQueue(p3_config)
        # 용량(5)을 채운 후 추가 시도
        for _ in range(5):
            await q.put(_make_event(EventType.LOG_WRITE))
        assert q.is_full()

        # 50개 더 넣기 (sample_rate=0.5이므로 ~절반 드롭)
        for _ in range(50):
            await q.put(_make_event(EventType.LOG_WRITE))
        assert q.sampled_out_count > 0


class TestCreateQueue:
    """create_queue 팩토리 테스트."""

    def test_creates_bounded_for_block(self, p0_config: QueueConfig):
        q = create_queue(p0_config)
        assert isinstance(q, BoundedQueue)

    def test_creates_ring_for_drop_oldest(self, p1_config: QueueConfig):
        q = create_queue(p1_config)
        assert isinstance(q, RingBuffer)

    def test_creates_collapsing_for_collapse(self, p2_config: QueueConfig):
        q = create_queue(p2_config)
        assert isinstance(q, CollapsingQueue)

    def test_creates_sampling_for_sample(self, p3_config: QueueConfig):
        q = create_queue(p3_config)
        assert isinstance(q, SamplingQueue)
