"""
Phase 7 — Safety State Machine & Lockdown 테스트.

전이: NORMAL→WARNING(anomaly), NORMAL/WARNING→FAIL(fail_safe),
FAIL 2회 연속→LOCKDOWN, FAIL/LOCKDOWN→NORMAL(recovery).
"""
from __future__ import annotations

import pytest

from ops.safety import (
    LOCKDOWN_CONSECUTIVE_FAIL_THRESHOLD,
    SafetyState,
    SafetyStateManager,
    allowed_transitions,
)


class TestSafetyStateManagerTransitions:
    def test_initial_state_is_normal(self):
        m = SafetyStateManager()
        assert m.current_state == SafetyState.NORMAL
        assert m.pipeline_state == "NORMAL"
        assert m.is_trading_allowed is True
        assert m.is_lockdown is False

    def test_anomaly_normal_to_warning(self):
        m = SafetyStateManager()
        r = m.apply_anomaly("AN001")
        assert r.applied is True
        assert r.to_state == SafetyState.WARNING
        assert m.current_state == SafetyState.WARNING
        assert m.is_trading_allowed is True  # WARNING still allows trading per Arch

    def test_fail_safe_normal_to_fail(self):
        m = SafetyStateManager()
        r = m.apply_fail_safe("FS040")
        assert r.applied is True
        assert r.to_state == SafetyState.FAIL
        assert m.current_state == SafetyState.FAIL
        assert m.is_trading_allowed is False
        assert m.consecutive_fail_safe_count == 1
        assert m.last_fail_safe_code == "FS040"

    def test_fail_safe_warning_to_fail(self):
        m = SafetyStateManager()
        m.apply_anomaly("AN001")
        r = m.apply_fail_safe("FS001")
        assert r.applied is True
        assert r.to_state == SafetyState.FAIL
        assert m.current_state == SafetyState.FAIL

    def test_consecutive_fail_safe_enters_lockdown(self):
        m = SafetyStateManager()
        m.apply_fail_safe("FS040")
        r = m.apply_fail_safe("FS050")
        assert r.applied is True
        assert r.to_state == SafetyState.LOCKDOWN
        assert m.current_state == SafetyState.LOCKDOWN
        assert m.is_lockdown is True
        assert m.is_trading_allowed is False
        assert m.consecutive_fail_safe_count >= LOCKDOWN_CONSECUTIVE_FAIL_THRESHOLD

    def test_recovery_fail_to_normal(self):
        m = SafetyStateManager()
        m.apply_fail_safe("FS040")
        r = m.request_recovery(operator_approved=False)
        assert r.applied is True
        assert r.to_state == SafetyState.NORMAL
        assert m.current_state == SafetyState.NORMAL
        assert m.consecutive_fail_safe_count == 0

    def test_recovery_lockdown_without_approval_stays_lockdown(self):
        m = SafetyStateManager()
        m.apply_fail_safe("FS040")
        m.apply_fail_safe("FS050")
        assert m.current_state == SafetyState.LOCKDOWN
        r = m.request_recovery(operator_approved=False)
        assert r.applied is False
        assert m.current_state == SafetyState.LOCKDOWN
        assert r.reason == "lockdown_requires_operator_approval"

    def test_recovery_lockdown_with_approval_to_normal(self):
        m = SafetyStateManager()
        m.apply_fail_safe("FS040")
        m.apply_fail_safe("FS050")
        r = m.request_recovery(operator_approved=True)
        assert r.applied is True
        assert r.to_state == SafetyState.NORMAL
        assert m.current_state == SafetyState.NORMAL
        assert m.is_trading_allowed is True

    def test_snapshot_contains_pipeline_state(self):
        m = SafetyStateManager()
        m.apply_fail_safe("FS001")
        snap = m.snapshot()
        assert snap["pipeline_state"] == "FAIL"
        assert snap["is_trading_allowed"] is False
        assert snap["last_fail_safe_code"] == "FS001"


class TestAllowedTransitions:
    def test_normal_has_anomaly_and_fail_safe(self):
        t = allowed_transitions()
        assert "anomaly" in t["NORMAL"]
        assert "fail_safe" in t["NORMAL"]

    def test_fail_and_lockdown_have_recovery(self):
        t = allowed_transitions()
        assert "recovery" in t["FAIL"]
        assert "recovery" in t["LOCKDOWN"]
