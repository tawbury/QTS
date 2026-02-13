"""Event Priority System 런타임 통합 테스트.

EventDispatcher 초기화, Safety 연동, ETEDA 이벤트 발행을 검증한다.
근거: docs/arch/sub/17_Event_Priority_Architecture.md §6, §7
"""
from __future__ import annotations

import asyncio

import pytest

from src.event.config import EventConfig
from src.event.contracts import (
    DegradationLevel,
    Event,
    EventPriority,
    EventType,
    create_event,
)
from src.event.dispatcher import EventDispatcher
from src.event.handlers import CallbackHandler, EventHandler
from src.event.bridges import SafetyEventBridge, _parse_safety_state
from src.safety.state import SafetyState


# --- EventDispatcher Lifecycle Tests ---


class TestEventDispatcherLifecycle:
    """EventDispatcher start/stop 테스트."""

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """디스패처 시작/정지."""
        dispatcher = EventDispatcher()
        assert not dispatcher.is_running

        await dispatcher.start()
        assert dispatcher.is_running

        await dispatcher.stop()
        assert not dispatcher.is_running

    @pytest.mark.asyncio
    async def test_dispatch_event(self):
        """이벤트 디스패치."""
        dispatcher = EventDispatcher()
        await dispatcher.start()

        event = create_event(EventType.ETEDA_CYCLE_START, source="test")
        result = await dispatcher.dispatch(event)
        assert result is True
        assert dispatcher.dispatch_count == 1

        await dispatcher.stop()

    @pytest.mark.asyncio
    async def test_dispatch_all_priorities(self):
        """P0-P3 모든 우선순위 이벤트 디스패치."""
        dispatcher = EventDispatcher()
        await dispatcher.start()

        events = [
            create_event(EventType.FILL_CONFIRMED, source="test"),       # P0
            create_event(EventType.PRICE_TICK, source="test"),           # P1
            create_event(EventType.STRATEGY_EVALUATE, source="test"),    # P2
            create_event(EventType.DASHBOARD_UPDATE, source="test"),     # P3
        ]

        for event in events:
            result = await dispatcher.dispatch(event)
            assert result is True

        assert dispatcher.dispatch_count == 4
        await dispatcher.stop()

    @pytest.mark.asyncio
    async def test_queue_stats(self):
        """큐 상태 통계."""
        dispatcher = EventDispatcher()
        stats = dispatcher.queue_stats()
        assert "P0_CRITICAL" in stats
        assert "P1_HIGH" in stats
        assert "P2_MEDIUM" in stats
        assert "P3_LOW" in stats

        for name, s in stats.items():
            assert "size" in s
            assert "capacity" in s
            assert "utilization" in s


# --- Safety State → Degradation Tests ---


class TestSafetyDegradation:
    """Safety State → Degradation Level 매핑 테스트."""

    @pytest.mark.asyncio
    async def test_normal_allows_all(self):
        """NORMAL 상태에서 모든 우선순위 허용."""
        dispatcher = EventDispatcher()
        dispatcher.apply_safety_state(SafetyState.NORMAL)

        assert dispatcher.degradation_level == DegradationLevel.NORMAL
        assert dispatcher.is_priority_allowed(EventPriority.P0_CRITICAL)
        assert dispatcher.is_priority_allowed(EventPriority.P1_HIGH)
        assert dispatcher.is_priority_allowed(EventPriority.P2_MEDIUM)
        assert dispatcher.is_priority_allowed(EventPriority.P3_LOW)

    @pytest.mark.asyncio
    async def test_warning_pauses_p3(self):
        """WARNING 상태에서 P3 차단."""
        dispatcher = EventDispatcher()
        dispatcher.apply_safety_state(SafetyState.WARNING)

        assert dispatcher.degradation_level == DegradationLevel.P3_PAUSED
        assert dispatcher.is_priority_allowed(EventPriority.P0_CRITICAL)
        assert dispatcher.is_priority_allowed(EventPriority.P1_HIGH)
        assert dispatcher.is_priority_allowed(EventPriority.P2_MEDIUM)
        assert not dispatcher.is_priority_allowed(EventPriority.P3_LOW)

    @pytest.mark.asyncio
    async def test_fail_pauses_p2_p3(self):
        """FAIL 상태에서 P2+P3 차단."""
        dispatcher = EventDispatcher()
        dispatcher.apply_safety_state(SafetyState.FAIL)

        assert dispatcher.degradation_level == DegradationLevel.P2_P3_PAUSED
        assert dispatcher.is_priority_allowed(EventPriority.P0_CRITICAL)
        assert dispatcher.is_priority_allowed(EventPriority.P1_HIGH)
        assert not dispatcher.is_priority_allowed(EventPriority.P2_MEDIUM)
        assert not dispatcher.is_priority_allowed(EventPriority.P3_LOW)

    @pytest.mark.asyncio
    async def test_lockdown_critical_only(self):
        """LOCKDOWN 상태에서 P0만 허용."""
        dispatcher = EventDispatcher()
        dispatcher.apply_safety_state(SafetyState.LOCKDOWN)

        assert dispatcher.degradation_level == DegradationLevel.CRITICAL_ONLY
        assert dispatcher.is_priority_allowed(EventPriority.P0_CRITICAL)
        assert not dispatcher.is_priority_allowed(EventPriority.P1_HIGH)
        assert not dispatcher.is_priority_allowed(EventPriority.P2_MEDIUM)
        assert not dispatcher.is_priority_allowed(EventPriority.P3_LOW)

    @pytest.mark.asyncio
    async def test_degradation_rejects_event(self):
        """성능 저하 시 이벤트 차단."""
        dispatcher = EventDispatcher()
        await dispatcher.start()

        dispatcher.apply_safety_state(SafetyState.LOCKDOWN)

        # P0는 통과
        p0 = create_event(EventType.FILL_CONFIRMED, source="test")
        assert await dispatcher.dispatch(p0) is True

        # P2는 차단
        p2 = create_event(EventType.ETEDA_CYCLE_START, source="test")
        assert await dispatcher.dispatch(p2) is False
        assert dispatcher.reject_count == 1

        await dispatcher.stop()


# --- SafetyEventBridge Tests ---


class TestSafetyEventBridge:
    """SafetyEventBridge 연동 테스트."""

    def test_sync_normal(self):
        """NORMAL 상태 동기화."""

        class MockSafety:
            def pipeline_state(self):
                return "NORMAL"

        dispatcher = EventDispatcher()
        bridge = SafetyEventBridge(dispatcher, MockSafety())
        bridge.sync()

        assert dispatcher.degradation_level == DegradationLevel.NORMAL

    def test_sync_lockdown(self):
        """LOCKDOWN 상태 동기화."""

        class MockSafety:
            def pipeline_state(self):
                return "LOCKDOWN"

        dispatcher = EventDispatcher()
        bridge = SafetyEventBridge(dispatcher, MockSafety())
        bridge.sync()

        assert dispatcher.degradation_level == DegradationLevel.CRITICAL_ONLY

    def test_sync_no_change_skips(self):
        """상태 변경 없으면 동기화 건너뛰기."""

        class MockSafety:
            def pipeline_state(self):
                return "NORMAL"

        dispatcher = EventDispatcher()
        bridge = SafetyEventBridge(dispatcher, MockSafety())
        bridge.sync()
        bridge.sync()  # 두 번째 호출은 변경 없으므로 무시

    def test_sync_without_safety(self):
        """Safety Layer 없을 때 에러 없이 통과."""
        dispatcher = EventDispatcher()
        bridge = SafetyEventBridge(dispatcher, None)
        bridge.sync()  # 에러 없이 통과

    def test_parse_safety_state(self):
        """pipeline_state 문자열 파싱."""
        assert _parse_safety_state("NORMAL") == SafetyState.NORMAL
        assert _parse_safety_state("WARNING") == SafetyState.WARNING
        assert _parse_safety_state("FAIL") == SafetyState.FAIL
        assert _parse_safety_state("LOCKDOWN") == SafetyState.LOCKDOWN
        assert _parse_safety_state("normal") == SafetyState.NORMAL
        assert _parse_safety_state("unknown") == SafetyState.NORMAL


# --- Event Handler Integration Tests ---


class TestEventHandlerIntegration:
    """이벤트 핸들러 등록 및 처리 테스트."""

    @pytest.mark.asyncio
    async def test_handler_receives_event(self):
        """핸들러가 이벤트를 수신하는지 확인."""
        received = []

        async def on_event(event: Event):
            received.append(event)

        dispatcher = EventDispatcher()
        handler = CallbackHandler(on_event, name="test_handler")
        dispatcher.register_handler(EventPriority.P2_MEDIUM, handler)

        await dispatcher.start()

        event = create_event(EventType.ETEDA_CYCLE_START, source="test")
        await dispatcher.dispatch(event)

        # 배치 컨슈머가 처리할 시간 대기
        await asyncio.sleep(0.3)

        assert len(received) == 1
        assert received[0].event_type == EventType.ETEDA_CYCLE_START

        await dispatcher.stop()

    @pytest.mark.asyncio
    async def test_p0_handler_immediate(self):
        """P0 핸들러는 즉시 처리."""
        received = []

        async def on_p0(event: Event):
            received.append(event)

        dispatcher = EventDispatcher()
        handler = CallbackHandler(on_p0, name="p0_handler")
        dispatcher.register_handler(EventPriority.P0_CRITICAL, handler)

        await dispatcher.start()

        event = create_event(EventType.FILL_CONFIRMED, source="test")
        await dispatcher.dispatch(event)

        await asyncio.sleep(0.2)

        assert len(received) == 1
        assert received[0].event_type == EventType.FILL_CONFIRMED

        await dispatcher.stop()


# --- ETEDA Event Emission Tests ---


class TestETEDAEventEmission:
    """ETEDA → Event 발행 통합 테스트."""

    @pytest.mark.asyncio
    async def test_create_event_factory(self):
        """create_event 팩토리 함수 검증."""
        # P0 이벤트: requires_ack=True
        p0 = create_event(EventType.FILL_CONFIRMED, source="BROKER")
        assert p0.priority == EventPriority.P0_CRITICAL
        assert p0.requires_ack is True
        assert p0.max_process_time_ms == 10

        # P1 이벤트: can_batch=True
        p1 = create_event(EventType.PRICE_TICK, source="MARKET")
        assert p1.priority == EventPriority.P1_HIGH
        assert p1.can_batch is True

        # P2 이벤트: can_collapse=True
        p2 = create_event(EventType.ETEDA_CYCLE_START, source="SCHEDULER")
        assert p2.priority == EventPriority.P2_MEDIUM
        assert p2.can_collapse is True

        # P3 이벤트: can_drop=True
        p3 = create_event(EventType.METRIC_RECORD, source="MONITOR")
        assert p3.priority == EventPriority.P3_LOW
        assert p3.can_drop is True

    @pytest.mark.asyncio
    async def test_event_type_catalog_completeness(self):
        """모든 EventType에 우선순위 매핑 존재 (§10.1)."""
        from src.event.contracts import EVENT_PRIORITY_MAP
        for event_type in EventType:
            assert event_type in EVENT_PRIORITY_MAP, (
                f"EventType.{event_type.value} has no priority mapping"
            )
