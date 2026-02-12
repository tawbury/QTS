"""OperatingStateManager 테스트."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from src.safety.state import SafetyState
from src.state.contracts import (
    ManualOverride,
    OperatingState,
    STATE_PROPERTIES,
    TransitionMetrics,
)
from src.state.operating_state import OperatingStateManager


@pytest.fixture
def manager() -> OperatingStateManager:
    return OperatingStateManager(initial_state=OperatingState.BALANCED)


class TestOperatingStateManager:
    """OperatingStateManager 기본 동작."""

    def test_initial_state(self, manager: OperatingStateManager):
        assert manager.current_state == OperatingState.BALANCED

    def test_properties(self, manager: OperatingStateManager):
        assert manager.properties == STATE_PROPERTIES[OperatingState.BALANCED]

    def test_snapshot(self, manager: OperatingStateManager):
        snap = manager.get_snapshot()
        assert snap.current_state == OperatingState.BALANCED
        assert snap.previous_state is None
        assert snap.manual_override is False

    def test_no_override_initially(self, manager: OperatingStateManager):
        assert not manager.has_override


class TestTransitionEvaluation:
    """전환 평가 테스트."""

    def test_no_transition_normal_metrics(self, manager: OperatingStateManager):
        m = TransitionMetrics()
        result = manager.evaluate_transition(m, SafetyState.NORMAL)
        assert not result.applied
        assert "no_transition_needed" in result.reason

    def test_confirmation_required(self, manager: OperatingStateManager):
        """2-cycle 확인: 첫 번째는 pending, 두 번째에 전환."""
        m = TransitionMetrics(drawdown_pct=0.12)
        # 1st cycle: pending
        r1 = manager.evaluate_transition(m, SafetyState.NORMAL)
        assert not r1.applied
        assert "confirmation_pending" in r1.reason

        # 2nd cycle: 전환 실행
        r2 = manager.evaluate_transition(m, SafetyState.NORMAL)
        assert r2.applied
        assert r2.to_state == OperatingState.DEFENSIVE

    def test_defensive_is_danger_transition(self):
        """→DEFENSIVE 전환은 min_duration 무시 (Hysteresis 건너뜀)."""
        mgr = OperatingStateManager(initial_state=OperatingState.BALANCED)
        # state_entered_at을 방금으로 설정 → duration < min
        m = TransitionMetrics(drawdown_pct=0.12)
        # 1st cycle
        mgr.evaluate_transition(m, SafetyState.NORMAL)
        # 2nd cycle (duration 아직 0일)
        r = mgr.evaluate_transition(m, SafetyState.NORMAL)
        assert r.applied
        assert r.to_state == OperatingState.DEFENSIVE

    def test_aggressive_to_balanced_needs_min_duration(self):
        """AGGRESSIVE→BALANCED는 min_duration(7일) 필요."""
        mgr = OperatingStateManager(initial_state=OperatingState.AGGRESSIVE)
        m = TransitionMetrics(drawdown_pct=0.06)
        # duration < 7일이므로 차단
        r = mgr.evaluate_transition(m, SafetyState.NORMAL)
        assert not r.applied
        assert "min_duration_not_met" in r.reason

    def test_aggressive_to_balanced_after_duration(self):
        """7일 이후 AGGRESSIVE→BALANCED 가능."""
        mgr = OperatingStateManager(initial_state=OperatingState.AGGRESSIVE)
        mgr._state_entered_at = datetime.now(timezone.utc) - timedelta(days=8)
        m = TransitionMetrics(drawdown_pct=0.06)
        # 1st cycle
        mgr.evaluate_transition(m, SafetyState.NORMAL)
        # 2nd cycle
        r = mgr.evaluate_transition(m, SafetyState.NORMAL)
        assert r.applied
        assert r.to_state == OperatingState.BALANCED


class TestManualOverride:
    """수동 오버라이드 테스트."""

    def test_override_changes_state(self, manager: OperatingStateManager):
        override = ManualOverride(
            override_state=OperatingState.DEFENSIVE,
            override_reason="earnings",
            operator_id="tau",
            override_time=datetime.now(timezone.utc),
            expiry_time=datetime.now(timezone.utc) + timedelta(days=3),
            auto_revert_state=OperatingState.BALANCED,
        )
        result = manager.apply_override(override)
        assert result.applied
        assert manager.current_state == OperatingState.DEFENSIVE
        assert manager.has_override

    def test_override_blocks_auto_transition(self, manager: OperatingStateManager):
        override = ManualOverride(
            override_state=OperatingState.DEFENSIVE,
            override_reason="test",
            operator_id="tau",
            override_time=datetime.now(timezone.utc),
            expiry_time=datetime.now(timezone.utc) + timedelta(days=3),
            auto_revert_state=OperatingState.BALANCED,
        )
        manager.apply_override(override)
        m = TransitionMetrics(
            drawdown_pct=0.03, vix=15, consecutive_profitable_days=5
        )
        result = manager.evaluate_transition(m, SafetyState.NORMAL)
        assert not result.applied
        assert "manual_override_active" in result.reason

    def test_override_expiry(self, manager: OperatingStateManager):
        override = ManualOverride(
            override_state=OperatingState.DEFENSIVE,
            override_reason="test",
            operator_id="tau",
            override_time=datetime.now(timezone.utc) - timedelta(days=8),
            expiry_time=datetime.now(timezone.utc) - timedelta(hours=1),
            auto_revert_state=OperatingState.BALANCED,
        )
        manager.apply_override(override)
        # evaluate_transition이 만료를 확인
        m = TransitionMetrics()
        manager.evaluate_transition(m, SafetyState.NORMAL)
        assert not manager.has_override
        assert manager.current_state == OperatingState.BALANCED


class TestSafetyIntegration:
    """Safety State 통합 테스트."""

    def test_safety_fail_forces_defensive(self, manager: OperatingStateManager):
        result = manager.apply_safety_override(SafetyState.FAIL)
        assert result.applied
        assert manager.current_state == OperatingState.DEFENSIVE

    def test_safety_normal_no_override(self, manager: OperatingStateManager):
        result = manager.apply_safety_override(SafetyState.NORMAL)
        assert not result.applied
        assert manager.current_state == OperatingState.BALANCED

    def test_lockdown_release_conservative(self):
        """AGGRESSIVE에서 LOCKDOWN 해제 시 BALANCED로 복귀."""
        mgr = OperatingStateManager(initial_state=OperatingState.AGGRESSIVE)
        result = mgr.on_lockdown_release()
        assert result.applied
        assert mgr.current_state == OperatingState.BALANCED

    def test_lockdown_release_same_state(self, manager: OperatingStateManager):
        """BALANCED에서 LOCKDOWN 해제 시 상태 유지."""
        result = manager.on_lockdown_release()
        assert result.applied
        assert manager.current_state == OperatingState.BALANCED
