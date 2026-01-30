"""
Health check & Alerts tests (Phase 9 — Monitoring & Alerts).

- HealthCheckResult, HealthMonitor, check names.
- AlertChannel, LogOnlyAlertChannel, send_critical on failure.
"""

from __future__ import annotations

import logging
import pytest

from ops.automation.health import (
    CHECK_BROKER_HEARTBEAT,
    CHECK_ETEDA_LOOP_LATENCY,
    CHECK_GOOGLE_SHEETS,
    CHECK_REPOSITORY_HEALTH,
    HealthCheckResult,
    HealthMonitor,
)
from ops.automation.alerts import LogOnlyAlertChannel


def test_health_check_result():
    r = HealthCheckResult(ok=True, name="test", message="ok", latency_ms=10.0)
    assert r.ok is True
    assert r.name == "test"
    assert r.latency_ms == 10.0


def test_health_check_names_defined():
    assert CHECK_GOOGLE_SHEETS == "google_sheets"
    assert CHECK_REPOSITORY_HEALTH == "repository_health"
    assert CHECK_BROKER_HEARTBEAT == "broker_heartbeat"
    assert CHECK_ETEDA_LOOP_LATENCY == "eteda_loop_latency"


def test_health_monitor_add_check_returns_self():
    m = HealthMonitor()
    out = m.add_check("t1", lambda: HealthCheckResult(ok=True, name="t1", message="ok"))
    assert out is m


def test_health_monitor_run_checks_returns_results():
    m = HealthMonitor()
    m.add_check("t1", lambda: HealthCheckResult(ok=True, name="t1", message="ok"))
    m.add_check("t2", lambda: HealthCheckResult(ok=False, name="t2", message="fail"))
    results = m.run_checks()
    assert len(results) == 2
    assert results[0].ok is True
    assert results[1].ok is False


def test_health_monitor_accepts_bool_return():
    m = HealthMonitor()
    m.add_check("t1", lambda: True)
    m.add_check("t2", lambda: False)
    results = m.run_checks()
    assert results[0].ok is True
    assert results[1].ok is False


def test_health_monitor_accepts_tuple_return():
    m = HealthMonitor()
    m.add_check("t1", lambda: (True, "ok"))
    m.add_check("t2", lambda: (False, "error"))
    results = m.run_checks()
    assert results[0].ok is True and "ok" in results[0].message
    assert results[1].ok is False and "error" in results[1].message


def test_health_monitor_send_critical_on_failure(caplog):
    caplog.set_level(logging.CRITICAL)
    channel = LogOnlyAlertChannel()
    m = HealthMonitor(alert_channel=channel)
    m.add_check("t1", lambda: HealthCheckResult(ok=False, name="t1", message="critical failure"))
    m.run_checks()
    assert "ALERT CRITICAL" in caplog.text or "critical" in caplog.text.lower()


def test_log_only_alert_channel_send_critical(caplog):
    caplog.set_level(logging.CRITICAL)
    channel = LogOnlyAlertChannel()
    channel.send_critical("test critical message")
    assert "ALERT CRITICAL" in caplog.text
    assert "test critical message" in caplog.text


def test_log_only_alert_channel_send_warning(caplog):
    caplog.set_level(logging.WARNING)
    channel = LogOnlyAlertChannel()
    channel.send_warning("test warning message")
    assert "ALERT WARNING" in caplog.text
    assert "test warning message" in caplog.text
