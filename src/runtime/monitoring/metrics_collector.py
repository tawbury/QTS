"""
Metrics Collection System (Phase 9 — Logging & Monitoring Core).

- Engine 성능 지표, 시스템 리소스, 비즈니스 지표(손익/거래량) 수집 인터페이스
- in-memory counters/gauges + 스냅샷; 실시간 모니터링/대시보드 연동용
- 근거: docs/arch/09_Ops_Automation_Architecture.md
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

_log = logging.getLogger("runtime.monitoring.metrics_collector")


@dataclass
class MetricsSnapshot:
    """Point-in-time snapshot of metrics for dashboard/monitoring."""

    counters: Dict[str, int] = field(default_factory=dict)
    gauges: Dict[str, float] = field(default_factory=dict)
    ts: float = field(default_factory=time.monotonic)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "ts": self.ts,
        }


class MetricsCollector:
    """
    In-memory metrics collector for engine/system/business indicators.

    - inc(name): increment counter
    - set_gauge(name, value): set gauge
    - snapshot(): return MetricsSnapshot
    - Optional: register_engine_collector(callable) etc. for pull-based metrics
    """

    def __init__(self) -> None:
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._engine_collector: Optional[Callable[[], Dict[str, Any]]] = None
        self._system_collector: Optional[Callable[[], Dict[str, Any]]] = None
        self._business_collector: Optional[Callable[[], Dict[str, Any]]] = None

    def inc(self, name: str, delta: int = 1) -> None:
        self._counters[name] = self._counters.get(name, 0) + delta

    def set_gauge(self, name: str, value: float) -> None:
        self._gauges[name] = value

    def snapshot(self) -> MetricsSnapshot:
        """Current counters/gauges plus optional pull from registered collectors."""
        counters = dict(self._counters)
        gauges = dict(self._gauges)

        if self._engine_collector:
            try:
                data = self._engine_collector()
                if isinstance(data.get("counters"), dict):
                    for k, v in data["counters"].items():
                        counters[k] = v
                if isinstance(data.get("gauges"), dict):
                    gauges.update(data["gauges"])
            except Exception as e:
                _log.warning("Engine metrics collector failed: %s", e)

        if self._system_collector:
            try:
                data = self._system_collector()
                if isinstance(data.get("gauges"), dict):
                    gauges.update(data["gauges"])
            except Exception as e:
                _log.warning("System metrics collector failed: %s", e)

        if self._business_collector:
            try:
                data = self._business_collector()
                if isinstance(data.get("gauges"), dict):
                    gauges.update(data["gauges"])
            except Exception as e:
                _log.warning("Business metrics collector failed: %s", e)

        return MetricsSnapshot(counters=counters, gauges=gauges)

    def register_engine_collector(self, fn: Callable[[], Dict[str, Any]]) -> None:
        """Register callable that returns dict with optional 'counters' and 'gauges'."""
        self._engine_collector = fn

    def register_system_collector(self, fn: Callable[[], Dict[str, Any]]) -> None:
        """Register callable for system resource metrics (e.g. cpu, memory)."""
        self._system_collector = fn

    def register_business_collector(self, fn: Callable[[], Dict[str, Any]]) -> None:
        """Register callable for business metrics (e.g. pnl, volume)."""
        self._business_collector = fn
