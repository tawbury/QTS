"""
Phase 7 — SafetyLayer 파사드 테스트.

Kill Switch, Safe Mode, should_run, record_fail_safe, pipeline_state, request_recovery.
PipelineSafetyHook 프로토콜 만족 검증.
"""
from __future__ import annotations

import pytest

from src.safety import (
    InMemoryNotifier,
    SafetyLayer,
)


class TestSafetyLayerHook:
    def test_should_run_true_when_normal_and_no_kill_switch(self):
        layer = SafetyLayer(kill_switch=False)
        assert layer.should_run() is True
        assert layer.pipeline_state() == "NORMAL"

    def test_should_run_false_when_kill_switch(self):
        layer = SafetyLayer(kill_switch=True)
        assert layer.should_run() is False
        assert layer.pipeline_state() == "NORMAL"

    def test_should_run_false_after_fail_safe(self):
        layer = SafetyLayer()
        layer.record_fail_safe("FS040", "Broker error", "Act")
        assert layer.should_run() is False
        assert layer.pipeline_state() == "FAIL"

    def test_record_fail_safe_updates_state_and_notifies(self):
        notifier = InMemoryNotifier()
        layer = SafetyLayer(notifier=notifier)
        layer.record_fail_safe("FS001", "Schema mismatch", "Extract")
        assert layer.pipeline_state() == "FAIL"
        assert len(notifier.events) == 1
        assert notifier.events[0].safety_code == "FS001"
        assert notifier.events[0].level == "FAIL"
        assert notifier.events[0].meta.get("stage") == "Extract"

    def test_request_recovery_fail_to_normal(self):
        layer = SafetyLayer()
        layer.record_fail_safe("FS040", "Broker error", "Act")
        assert layer.pipeline_state() == "FAIL"
        ok = layer.request_recovery(operator_approved=False)
        assert ok is True
        assert layer.pipeline_state() == "NORMAL"
        assert layer.should_run() is True

    def test_request_recovery_lockdown_requires_approval(self):
        layer = SafetyLayer()
        layer.record_fail_safe("FS040", "Broker error", "Act")
        layer.record_fail_safe("FS050", "Equity", "Transform")
        assert layer.pipeline_state() == "LOCKDOWN"
        ok = layer.request_recovery(operator_approved=False)
        assert ok is False
        assert layer.pipeline_state() == "LOCKDOWN"
        ok = layer.request_recovery(operator_approved=True)
        assert ok is True
        assert layer.pipeline_state() == "NORMAL"

    def test_snapshot_includes_kill_switch_and_safe_mode(self):
        layer = SafetyLayer(kill_switch=True, safe_mode=True)
        snap = layer.snapshot()
        assert snap["kill_switch"] is True
        assert snap["safe_mode"] is True
        assert "pipeline_state" in snap
