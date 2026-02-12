"""Safety State ↔ Event Priority ↔ Operating State 통합 테스트."""
import pytest

from src.event.contracts import DegradationLevel, EventPriority, EventType, create_event
from src.event.dispatcher import EventDispatcher, SAFETY_TO_DEGRADATION
from src.safety.state import SafetyState, SafetyStateManager
from src.state.contracts import OperatingState, TransitionMetrics
from src.state.operating_state import OperatingStateManager


class TestSafetyEventIntegration:
    """Safety State → Event Degradation 연동."""

    def test_safety_normal_all_events_allowed(self):
        dispatcher = EventDispatcher()
        dispatcher.apply_safety_state(SafetyState.NORMAL)
        assert dispatcher.degradation_level == DegradationLevel.NORMAL
        for p in EventPriority:
            assert dispatcher.is_priority_allowed(p)

    def test_safety_warning_p3_paused(self):
        dispatcher = EventDispatcher()
        dispatcher.apply_safety_state(SafetyState.WARNING)
        assert dispatcher.degradation_level == DegradationLevel.P3_PAUSED
        assert dispatcher.is_priority_allowed(EventPriority.P2_MEDIUM)
        assert not dispatcher.is_priority_allowed(EventPriority.P3_LOW)

    def test_safety_fail_p2_p3_paused(self):
        dispatcher = EventDispatcher()
        dispatcher.apply_safety_state(SafetyState.FAIL)
        assert dispatcher.degradation_level == DegradationLevel.P2_P3_PAUSED
        assert dispatcher.is_priority_allowed(EventPriority.P1_HIGH)
        assert not dispatcher.is_priority_allowed(EventPriority.P2_MEDIUM)

    def test_safety_lockdown_critical_only(self):
        dispatcher = EventDispatcher()
        dispatcher.apply_safety_state(SafetyState.LOCKDOWN)
        assert dispatcher.degradation_level == DegradationLevel.CRITICAL_ONLY
        assert dispatcher.is_priority_allowed(EventPriority.P0_CRITICAL)
        assert not dispatcher.is_priority_allowed(EventPriority.P1_HIGH)

    @pytest.mark.asyncio
    async def test_p0_always_dispatched(self):
        """P0 이벤트는 어떤 성능 저하 레벨에서도 디스패치됨."""
        dispatcher = EventDispatcher()
        event = create_event(EventType.EMERGENCY_STOP)
        for safety in SafetyState:
            dispatcher.apply_safety_state(safety)
            result = await dispatcher.dispatch(event)
            assert result is True, f"P0 should be dispatched in {safety}"


class TestSafetyOperatingIntegration:
    """Safety State → Operating State 연동."""

    def test_safety_fail_forces_defensive(self):
        safety_mgr = SafetyStateManager()
        op_mgr = OperatingStateManager(initial_state=OperatingState.AGGRESSIVE)

        # Safety: FAIL 적용
        safety_mgr.apply_fail_safe("FS001")
        assert safety_mgr.current_state == SafetyState.FAIL

        # Operating: DEFENSIVE 강제 전환
        result = op_mgr.apply_safety_override(safety_mgr.current_state)
        assert result.applied
        assert op_mgr.current_state == OperatingState.DEFENSIVE

    def test_safety_lockdown_preserves_state(self):
        """LOCKDOWN 시 Operating State는 보존됨 (Safety Layer가 트레이딩 중단)."""
        op_mgr = OperatingStateManager(initial_state=OperatingState.BALANCED)

        result = op_mgr.apply_safety_override(SafetyState.LOCKDOWN)
        assert not result.applied
        assert op_mgr.current_state == OperatingState.BALANCED

    def test_lockdown_release_conservative_from_aggressive(self):
        """AGGRESSIVE에서 LOCKDOWN 해제 시 BALANCED로 복귀."""
        op_mgr = OperatingStateManager(initial_state=OperatingState.AGGRESSIVE)
        result = op_mgr.on_lockdown_release()
        assert result.applied
        assert op_mgr.current_state == OperatingState.BALANCED


class TestFullCascade:
    """Safety → Event + Operating 전체 캐스케이드."""

    @pytest.mark.asyncio
    async def test_safety_fail_cascades(self):
        """Safety FAIL → Event P2_P3_PAUSED + Operating DEFENSIVE."""
        safety_mgr = SafetyStateManager()
        dispatcher = EventDispatcher()
        op_mgr = OperatingStateManager(initial_state=OperatingState.BALANCED)

        # Safety 이벤트: FAIL
        safety_mgr.apply_fail_safe("FS_TEST")

        # Event 시스템 연동
        dispatcher.apply_safety_state(safety_mgr.current_state)
        assert dispatcher.degradation_level == DegradationLevel.P2_P3_PAUSED

        # Operating 시스템 연동
        op_mgr.apply_safety_override(safety_mgr.current_state)
        assert op_mgr.current_state == OperatingState.DEFENSIVE

        # P0는 처리됨
        p0 = create_event(EventType.FILL_CONFIRMED)
        assert await dispatcher.dispatch(p0) is True

        # P2는 차단됨
        p2 = create_event(EventType.STRATEGY_EVALUATE)
        assert await dispatcher.dispatch(p2) is False

    @pytest.mark.asyncio
    async def test_recovery_restores_normal(self):
        """Safety 복구 → 모든 시스템 정상화."""
        safety_mgr = SafetyStateManager()
        dispatcher = EventDispatcher()

        # FAIL → 복구
        safety_mgr.apply_fail_safe("FS_TEST")
        dispatcher.apply_safety_state(safety_mgr.current_state)
        assert dispatcher.degradation_level == DegradationLevel.P2_P3_PAUSED

        safety_mgr.request_recovery()
        dispatcher.apply_safety_state(safety_mgr.current_state)
        assert dispatcher.degradation_level == DegradationLevel.NORMAL
        assert dispatcher.is_priority_allowed(EventPriority.P3_LOW)
