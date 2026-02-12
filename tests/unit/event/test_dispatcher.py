"""이벤트 디스패처 테스트."""
import asyncio

import pytest

from src.event.config import EventConfig
from src.event.contracts import (
    DegradationLevel,
    EventPriority,
    EventType,
    create_event,
)
from src.event.dispatcher import (
    SAFETY_TO_DEGRADATION,
    EventDispatcher,
)
from src.event.handlers import CallbackHandler
from src.safety.state import SafetyState


@pytest.fixture
def dispatcher() -> EventDispatcher:
    return EventDispatcher()


class TestDegradationMapping:
    """Safety State → Degradation Level 매핑 테스트."""

    def test_normal_to_normal(self):
        assert SAFETY_TO_DEGRADATION[SafetyState.NORMAL] == DegradationLevel.NORMAL

    def test_warning_to_p3_paused(self):
        assert SAFETY_TO_DEGRADATION[SafetyState.WARNING] == DegradationLevel.P3_PAUSED

    def test_fail_to_p2_p3_paused(self):
        assert SAFETY_TO_DEGRADATION[SafetyState.FAIL] == DegradationLevel.P2_P3_PAUSED

    def test_lockdown_to_critical_only(self):
        assert SAFETY_TO_DEGRADATION[SafetyState.LOCKDOWN] == DegradationLevel.CRITICAL_ONLY


class TestEventDispatcher:
    """EventDispatcher 테스트."""

    @pytest.mark.asyncio
    async def test_dispatch_p0_event(self, dispatcher: EventDispatcher):
        event = create_event(EventType.FILL_CONFIRMED)
        result = await dispatcher.dispatch(event)
        assert result is True
        assert dispatcher.dispatch_count == 1

    @pytest.mark.asyncio
    async def test_dispatch_rejected_in_critical_only(self, dispatcher: EventDispatcher):
        dispatcher.set_degradation_level(DegradationLevel.CRITICAL_ONLY)
        # P0 허용
        p0 = create_event(EventType.FILL_CONFIRMED)
        assert await dispatcher.dispatch(p0) is True
        # P1 차단
        p1 = create_event(EventType.PRICE_TICK)
        assert await dispatcher.dispatch(p1) is False
        assert dispatcher.reject_count == 1

    @pytest.mark.asyncio
    async def test_dispatch_p3_paused(self, dispatcher: EventDispatcher):
        dispatcher.set_degradation_level(DegradationLevel.P3_PAUSED)
        # P2 허용
        p2 = create_event(EventType.STRATEGY_EVALUATE)
        assert await dispatcher.dispatch(p2) is True
        # P3 차단
        p3 = create_event(EventType.LOG_WRITE)
        assert await dispatcher.dispatch(p3) is False

    @pytest.mark.asyncio
    async def test_apply_safety_state(self, dispatcher: EventDispatcher):
        dispatcher.apply_safety_state(SafetyState.LOCKDOWN)
        assert dispatcher.degradation_level == DegradationLevel.CRITICAL_ONLY

    @pytest.mark.asyncio
    async def test_handler_receives_event(self, dispatcher: EventDispatcher):
        received: list = []

        async def on_event(event):
            received.append(event)

        handler = CallbackHandler(on_event, name="test")
        dispatcher.register_handler(EventPriority.P0_CRITICAL, handler)

        await dispatcher.start()
        event = create_event(EventType.FILL_CONFIRMED)
        await dispatcher.dispatch(event)
        await asyncio.sleep(0.2)  # 컨슈머가 처리할 시간
        await dispatcher.stop()

        assert len(received) == 1
        assert received[0].event_id == event.event_id

    @pytest.mark.asyncio
    async def test_queue_stats(self, dispatcher: EventDispatcher):
        await dispatcher.dispatch(create_event(EventType.FILL_CONFIRMED))
        stats = dispatcher.queue_stats()
        assert "P0_CRITICAL" in stats
        assert stats["P0_CRITICAL"]["size"] == 1

    @pytest.mark.asyncio
    async def test_start_stop(self, dispatcher: EventDispatcher):
        assert not dispatcher.is_running
        await dispatcher.start()
        assert dispatcher.is_running
        await dispatcher.stop()
        assert not dispatcher.is_running

    @pytest.mark.asyncio
    async def test_priority_allowed(self, dispatcher: EventDispatcher):
        assert dispatcher.is_priority_allowed(EventPriority.P0_CRITICAL)
        assert dispatcher.is_priority_allowed(EventPriority.P3_LOW)
        dispatcher.set_degradation_level(DegradationLevel.CRITICAL_ONLY)
        assert dispatcher.is_priority_allowed(EventPriority.P0_CRITICAL)
        assert not dispatcher.is_priority_allowed(EventPriority.P1_HIGH)
