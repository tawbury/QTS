"""
이벤트 처리 레이턴시 추적.

근거: docs/arch/sub/17_Event_Priority_Architecture.md §4.2
- P0 p99 < 10ms
- P1 p99 < 50ms
- P2 p99 < 500ms
- P3 best effort
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass
class LatencyStats:
    """레이턴시 통계."""

    count: int = 0
    avg_ms: float = 0.0
    p50_ms: float = 0.0
    p99_ms: float = 0.0
    max_ms: float = 0.0


class LatencyTracker:
    """우선순위별 레이턴시 추적."""

    SLA_LIMITS_MS = {
        0: 10.0,   # P0: < 10ms
        1: 50.0,   # P1: < 50ms
        2: 500.0,  # P2: < 500ms
        3: 5000.0, # P3: best effort
    }

    def __init__(self, window_size: int = 1000) -> None:
        self._windows: dict[int, deque[float]] = {
            i: deque(maxlen=window_size) for i in range(4)
        }

    def record(self, priority: int, latency_ms: float) -> None:
        """레이턴시 기록."""
        if priority in self._windows:
            self._windows[priority].append(latency_ms)

    def get_stats(self, priority: int) -> LatencyStats:
        """통계 조회."""
        window = self._windows.get(priority)
        if not window:
            return LatencyStats()
        sorted_vals = sorted(window)
        n = len(sorted_vals)
        return LatencyStats(
            count=n,
            avg_ms=sum(sorted_vals) / n,
            p50_ms=sorted_vals[n // 2],
            p99_ms=sorted_vals[int(n * 0.99)] if n > 1 else sorted_vals[-1],
            max_ms=sorted_vals[-1],
        )

    def check_sla_violations(self) -> list[dict]:
        """SLA 위반 확인."""
        violations = []
        for priority, limit in self.SLA_LIMITS_MS.items():
            stats = self.get_stats(priority)
            if stats.count > 0 and stats.p99_ms > limit:
                violations.append({
                    "priority": priority,
                    "p99_ms": stats.p99_ms,
                    "limit_ms": limit,
                })
        return violations
