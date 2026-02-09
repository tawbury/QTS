"""
Health check 항목 정의 (Phase 9 — Monitoring & Alerts).

- Google Sheets 연결, Repository health, Broker heartbeat, ETEDA loop latency
- 각 항목은 콜러블로 주입; 모니터링 로직은 런타임을 직접 import 하지 않음.
- 근거: docs/arch/09_Ops_Automation_Architecture.md, 07_FailSafe_Architecture.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Union

_log = logging.getLogger("src.automation.health")


# ----- Health check result -----


@dataclass
class HealthCheckResult:
    """Single health check result."""

    ok: bool
    name: str
    message: str
    latency_ms: Optional[float] = None
    meta: Dict[str, Any] = field(default_factory=dict)


# ----- Check names (Health check 항목 정의) -----

CHECK_GOOGLE_SHEETS = "google_sheets"
CHECK_REPOSITORY_HEALTH = "repository_health"
CHECK_BROKER_HEARTBEAT = "broker_heartbeat"
CHECK_ETEDA_LOOP_LATENCY = "eteda_loop_latency"


# ----- Health check protocol -----


class HealthCheck(Protocol):
    """Single health check. Returns HealthCheckResult."""

    def __call__(self) -> HealthCheckResult:
        ...


# ----- Health monitor -----


def _run_check(name: str, fn: Union[Callable[[], HealthCheckResult], Callable[[], bool], Callable[[], tuple[bool, str]]]) -> HealthCheckResult:
    """Run one check; normalize return to HealthCheckResult."""
    try:
        out = fn()
        if isinstance(out, HealthCheckResult):
            return out
        if isinstance(out, tuple) and len(out) >= 2:
            ok, msg = out[0], str(out[1])
            return HealthCheckResult(ok=ok, name=name, message=msg)
        if isinstance(out, bool):
            return HealthCheckResult(ok=out, name=name, message="ok" if out else "check failed")
        return HealthCheckResult(ok=False, name=name, message=f"unexpected return: {type(out)}")
    except Exception as e:
        _log.warning("Health check %s raised: %s", name, e, exc_info=True)
        return HealthCheckResult(ok=False, name=name, message=str(e))


class HealthMonitor:
    """
    Run registered health checks and report results.

    Boundary: checks are callables; no direct runtime import.
    On any failed check, call alert_channel.send_critical so 치명적 장애가 운영자에게 전달.
    """

    def __init__(self, alert_channel: Optional[Any] = None) -> None:
        self._checks: List[tuple[str, Callable[[], HealthCheckResult]]] = []
        self._alert_channel = alert_channel

    def add_check(
        self,
        name: str,
        fn: Union[HealthCheck, Callable[[], HealthCheckResult], Callable[[], bool], Callable[[], tuple[bool, str]]],
    ) -> "HealthMonitor":
        """Register a health check. Returns self for chaining."""
        def runner() -> HealthCheckResult:
            return _run_check(name, fn)
        self._checks.append((name, runner))
        return self

    def run_checks(self) -> List[HealthCheckResult]:
        """Run all checks and return results. On failure, send critical alert if channel set."""
        results: List[HealthCheckResult] = []
        for name, fn in self._checks:
            r = fn()
            results.append(r)
            if not r.ok and self._alert_channel is not None and hasattr(self._alert_channel, "send_critical"):
                self._alert_channel.send_critical(f"[{r.name}] {r.message}")
        return results
