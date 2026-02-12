"""이벤트 계약 테스트."""
import pytest

from src.event.contracts import (
    DegradationLevel,
    Event,
    EventPriority,
    EventType,
    EVENT_PRIORITY_MAP,
    OverflowPolicy,
    create_event,
    priority_for,
)


class TestEventPriority:
    """EventPriority enum 테스트."""

    def test_priority_ordering(self):
        """P0 < P1 < P2 < P3 (숫자가 낮을수록 높은 우선순위)."""
        assert EventPriority.P0_CRITICAL < EventPriority.P1_HIGH
        assert EventPriority.P1_HIGH < EventPriority.P2_MEDIUM
        assert EventPriority.P2_MEDIUM < EventPriority.P3_LOW

    def test_priority_values(self):
        assert EventPriority.P0_CRITICAL == 0
        assert EventPriority.P1_HIGH == 1
        assert EventPriority.P2_MEDIUM == 2
        assert EventPriority.P3_LOW == 3


class TestEventType:
    """EventType enum 테스트."""

    def test_all_event_types_have_priority_mapping(self):
        """모든 EventType이 Priority 매핑을 가져야 함."""
        for et in EventType:
            assert et in EVENT_PRIORITY_MAP, f"{et} missing priority mapping"

    def test_p0_events(self):
        p0_types = {
            EventType.FILL_CONFIRMED,
            EventType.FILL_PARTIAL,
            EventType.ORDER_REJECTED,
            EventType.ORDER_CANCELLED,
            EventType.POSITION_UPDATE,
            EventType.EMERGENCY_STOP,
            EventType.BROKER_DISCONNECT,
        }
        for et in p0_types:
            assert priority_for(et) == EventPriority.P0_CRITICAL

    def test_p1_events(self):
        p1_types = {
            EventType.PRICE_TICK,
            EventType.ORDERBOOK_UPDATE,
            EventType.VOLUME_UPDATE,
            EventType.INDEX_UPDATE,
            EventType.VIX_UPDATE,
        }
        for et in p1_types:
            assert priority_for(et) == EventPriority.P1_HIGH

    def test_p2_events(self):
        p2_types = {
            EventType.ETEDA_CYCLE_START,
            EventType.STRATEGY_EVALUATE,
            EventType.RISK_EVALUATE,
            EventType.PORTFOLIO_EVALUATE,
            EventType.INDICATOR_UPDATE,
            EventType.SIGNAL_GENERATED,
        }
        for et in p2_types:
            assert priority_for(et) == EventPriority.P2_MEDIUM

    def test_p3_events(self):
        p3_types = {
            EventType.DASHBOARD_UPDATE,
            EventType.LOG_WRITE,
            EventType.REPORT_GENERATE,
            EventType.NOTIFICATION_SEND,
            EventType.METRIC_RECORD,
        }
        for et in p3_types:
            assert priority_for(et) == EventPriority.P3_LOW


class TestEvent:
    """Event 데이터 계약 테스트."""

    def test_create_event(self):
        event = Event(
            event_type=EventType.FILL_CONFIRMED,
            priority=EventPriority.P0_CRITICAL,
            source="BROKER_KIS",
            payload={"order_id": "ORD123"},
        )
        assert event.event_type == EventType.FILL_CONFIRMED
        assert event.priority == EventPriority.P0_CRITICAL
        assert event.source == "BROKER_KIS"
        assert event.payload["order_id"] == "ORD123"
        assert event.event_id  # UUID 자동 생성

    def test_event_is_frozen(self):
        event = Event(
            event_type=EventType.PRICE_TICK,
            priority=EventPriority.P1_HIGH,
        )
        with pytest.raises(AttributeError):
            event.source = "changed"  # type: ignore[misc]


class TestCreateEvent:
    """create_event 팩토리 테스트."""

    def test_p0_auto_properties(self):
        event = create_event(EventType.FILL_CONFIRMED, source="KIS")
        assert event.priority == EventPriority.P0_CRITICAL
        assert event.requires_ack is True
        assert event.max_process_time_ms == 10

    def test_p1_auto_properties(self):
        event = create_event(EventType.PRICE_TICK)
        assert event.priority == EventPriority.P1_HIGH
        assert event.can_batch is True

    def test_p2_auto_properties(self):
        event = create_event(EventType.STRATEGY_EVALUATE)
        assert event.priority == EventPriority.P2_MEDIUM
        assert event.can_collapse is True

    def test_p3_auto_properties(self):
        event = create_event(EventType.LOG_WRITE)
        assert event.priority == EventPriority.P3_LOW
        assert event.can_drop is True

    def test_payload(self):
        event = create_event(
            EventType.FILL_CONFIRMED,
            payload={"order_id": "ORD456"},
        )
        assert event.payload["order_id"] == "ORD456"


class TestDegradationLevel:
    """DegradationLevel enum 테스트."""

    def test_all_levels(self):
        assert DegradationLevel.NORMAL == "NORMAL"
        assert DegradationLevel.P3_PAUSED == "P3_PAUSED"
        assert DegradationLevel.P2_P3_PAUSED == "P2_P3_PAUSED"
        assert DegradationLevel.CRITICAL_ONLY == "CRITICAL_ONLY"
