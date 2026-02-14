"""
Metrics collector tests (Phase 9 — Logging & Monitoring Core).

- MetricsSnapshot, MetricsCollector inc/set_gauge/snapshot.
- register_engine/system/business_collector and snapshot merge.
"""

from __future__ import annotations

import pytest

from src.monitoring.metrics_collector import (
    MetricsCollector,
    MetricsSnapshot,
)


def test_metrics_snapshot_to_dict():
    s = MetricsSnapshot(counters={"a": 1}, gauges={"x": 1.0})
    d = s.to_dict()
    assert d["counters"] == {"a": 1}
    assert d["gauges"] == {"x": 1.0}
    assert "ts" in d


def test_metrics_collector_inc():
    c = MetricsCollector()
    c.inc("orders")
    c.inc("orders", 2)
    snap = c.snapshot()
    assert snap.counters["orders"] == 3


def test_metrics_collector_set_gauge():
    c = MetricsCollector()
    c.set_gauge("latency_ms", 10.5)
    c.set_gauge("latency_ms", 20.0)
    snap = c.snapshot()
    assert snap.gauges["latency_ms"] == 20.0


def test_metrics_collector_snapshot_empty():
    c = MetricsCollector()
    snap = c.snapshot()
    assert snap.counters == {}
    assert snap.gauges == {}
    assert snap.ts >= 0


def test_metrics_collector_register_engine_collector():
    c = MetricsCollector()
    c.inc("manual", 1)
    c.register_engine_collector(lambda: {"counters": {"engine_ops": 5}, "gauges": {"engine_latency": 1.0}})
    snap = c.snapshot()
    assert snap.counters["manual"] == 1
    assert snap.counters["engine_ops"] == 5
    assert snap.gauges["engine_latency"] == 1.0


def test_metrics_collector_register_system_collector():
    c = MetricsCollector()
    c.register_system_collector(lambda: {"gauges": {"cpu_pct": 50.0, "memory_mb": 128.0}})
    snap = c.snapshot()
    assert snap.gauges["cpu_pct"] == 50.0
    assert snap.gauges["memory_mb"] == 128.0


def test_metrics_collector_register_business_collector():
    c = MetricsCollector()
    c.register_business_collector(lambda: {"gauges": {"pnl": 100.5, "volume": 1000.0}})
    snap = c.snapshot()
    assert snap.gauges["pnl"] == 100.5
    assert snap.gauges["volume"] == 1000.0


def test_metrics_collector_collector_exception_logged():
    c = MetricsCollector()
    c.set_gauge("ok", 1.0)
    c.register_engine_collector(lambda: (_ for _ in ()).throw(ValueError("bad")))
    snap = c.snapshot()
    assert snap.gauges["ok"] == 1.0
    assert "ok" in snap.gauges
