"""
Phase 7 — Safety Notifier 최소 규격 테스트.

SafetyEvent 구조, 메시지 템플릿, NoOp/InMemory 구현 검증.
"""
from __future__ import annotations

import pytest

from ops.safety import (
    SafetyEvent,
    InMemoryNotifier,
    NoOpNotifier,
    default_message_template,
)


class TestSafetyEvent:
    def test_event_has_required_fields(self):
        e = SafetyEvent(
            timestamp="2025-01-01T00:00:00+00:00",
            safety_code="FS001",
            level="FAIL",
            message="SchemaMismatchError",
            pipeline_state="FAIL",
            meta={"reason": "version_mismatch"},
        )
        assert e.timestamp == "2025-01-01T00:00:00+00:00"
        assert e.safety_code == "FS001"
        assert e.level == "FAIL"
        assert e.message == "SchemaMismatchError"
        assert e.pipeline_state == "FAIL"
        assert e.meta["reason"] == "version_mismatch"

    def test_event_now_includes_iso_timestamp(self):
        e = SafetyEvent.now(
            safety_code="FS040",
            level="FAIL",
            message="Broker error",
            pipeline_state="FAIL",
        )
        assert e.safety_code == "FS040"
        assert "T" in e.timestamp and "Z" in e.timestamp or "+" in e.timestamp


class TestDefaultMessageTemplate:
    def test_template_includes_code_level_message_state(self):
        e = SafetyEvent(
            timestamp="",
            safety_code="FS001",
            level="FAIL",
            message="SchemaMismatchError",
            pipeline_state="FAIL",
            meta={},
        )
        msg = default_message_template(e)
        assert "FS001" in msg
        assert "FAIL" in msg
        assert "SchemaMismatchError" in msg
        assert "pipeline_state=FAIL" in msg

    def test_template_includes_meta_when_present(self):
        e = SafetyEvent(
            timestamp="",
            safety_code="FS040",
            level="FAIL",
            message="Broker error",
            pipeline_state="FAIL",
            meta={"consecutive_failures": 3},
        )
        msg = default_message_template(e)
        assert "consecutive_failures" in msg or "3" in msg


class TestNoOpNotifier:
    def test_notify_does_not_raise(self):
        n = NoOpNotifier()
        e = SafetyEvent.now("FS001", "FAIL", "test", "FAIL")
        n.notify(e)  # no raise


class TestInMemoryNotifier:
    def test_notify_appends_event(self):
        n = InMemoryNotifier()
        e = SafetyEvent.now("FS001", "FAIL", "test", "FAIL")
        n.notify(e)
        assert len(n.events) == 1
        assert n.events[0].safety_code == "FS001"

    def test_last_event_returns_most_recent(self):
        n = InMemoryNotifier()
        n.notify(SafetyEvent.now("FS001", "FAIL", "a", "FAIL"))
        n.notify(SafetyEvent.now("FS040", "FAIL", "b", "FAIL"))
        last = n.last_event()
        assert last is not None
        assert last.safety_code == "FS040"

    def test_clear_empties_events(self):
        n = InMemoryNotifier()
        n.notify(SafetyEvent.now("FS001", "FAIL", "test", "FAIL"))
        n.clear()
        assert len(n.events) == 0
        assert n.last_event() is None
