"""
Minimal Scheduler (Phase 9 — Ops/Automation).

- Interval 기반 최소 구현 + 실패 백오프.
- 스케줄 대상: Pipeline 실행, Broker heartbeat, Dashboard update, Backup/Maintenance
  (대상은 콜러블로 주입; 스케줄러는 런타임 로직을 침범하지 않음).
- 근거: docs/arch/09_Ops_Automation_Architecture.md
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

_log = logging.getLogger("src.automation.scheduler")


# ----- Schedule target names (스케줄 대상 정의) -----
TARGET_PIPELINE = "pipeline"
TARGET_BROKER_HEARTBEAT = "broker_heartbeat"
TARGET_DASHBOARD_UPDATE = "dashboard_update"
TARGET_BACKUP_MAINTENANCE = "backup_maintenance"


@dataclass
class ScheduleTarget:
    """
    Single schedule target: name, interval(ms), callable, backoff.

    fn: sync or async callable () -> Any. Scheduler invokes only; no runtime internals.
    """

    name: str
    interval_ms: int
    fn: Union[Callable[[], Any], Callable[[], Awaitable[Any]]]
    error_backoff_ms: int = 5000
    max_consecutive_errors: int = 3


def _clamp_interval(ms: int, lo: int = 100, hi: int = 3600_000) -> int:
    return max(lo, min(ms, hi))


async def _run_one(target: ScheduleTarget) -> bool:
    """Run one target; return True on success, False on failure."""
    try:
        out = target.fn()
        if asyncio.iscoroutine(out):
            await out
        return True
    except Exception as e:
        _log.warning("Scheduler target %s failed: %s", target.name, e, exc_info=True)
        return False


class MinimalScheduler:
    """
    Minimal interval-based scheduler with failure backoff.

    Boundary: only invokes registered callables; does not import or depend on
    runtime pipeline/eteda internals. Caller injects Pipeline runner, heartbeat, etc.

    Run/Stop/Error rules:
    - Run: start() runs the loop until should_stop() returns True.
    - Stop: set should_stop or call stop(); loop exits after current cycle.
    - Error: per-target consecutive errors; after max_consecutive_errors the target
      is skipped for one backoff period, then retried. Loop continues for other targets.
    """

    def __init__(
        self,
        *,
        should_stop: Optional[Callable[[], bool]] = None,
    ) -> None:
        self._targets: List[ScheduleTarget] = []
        self._should_stop = should_stop or (lambda: False)
        self._consecutive_errors: Dict[str, int] = {}
        self._last_run: Dict[str, float] = {}
        self._stopped = False

    def add_target(
        self,
        name: str,
        interval_ms: int,
        fn: Union[Callable[[], Any], Callable[[], Awaitable[Any]]],
        error_backoff_ms: int = 5000,
        max_consecutive_errors: int = 3,
    ) -> "MinimalScheduler":
        """Register a schedule target. Returns self for chaining."""
        self._targets.append(
            ScheduleTarget(
                name=name,
                interval_ms=_clamp_interval(interval_ms),
                fn=fn,
                error_backoff_ms=max(500, min(error_backoff_ms, 60_000)),
                max_consecutive_errors=max(0, min(max_consecutive_errors, 20)),
            )
        )
        self._consecutive_errors[name] = 0
        self._last_run[name] = 0.0
        return self

    def stop(self) -> None:
        """Signal the loop to exit after current cycle."""
        self._stopped = True

    def _due_targets(self, now: float) -> List[ScheduleTarget]:
        due = []
        for t in self._targets:
            last = self._last_run.get(t.name, 0.0)
            if now - last >= (t.interval_ms / 1000.0):
                due.append(t)
        return due

    async def run(self) -> None:
        """
        Run the scheduler loop until should_stop() or stop().

        Each cycle: run all due targets; on failure apply backoff and skip until
        backoff elapsed; then re-run. Loop sleeps for the minimum interval among targets.
        """
        if not self._targets:
            _log.warning("MinimalScheduler.run() called with no targets")
            return

        min_interval_sec = min(t.interval_ms for t in self._targets) / 1000.0
        _log.info("Scheduler started with %s targets, min_interval_sec=%s", len(self._targets), min_interval_sec)

        while not self._stopped and not self._should_stop():
            now = time.monotonic()
            due = self._due_targets(now)

            for target in due:
                if self._stopped or self._should_stop():
                    break
                errors = self._consecutive_errors.get(target.name, 0)
                if errors >= target.max_consecutive_errors:
                    _log.debug("Target %s skipped (max errors %s)", target.name, target.max_consecutive_errors)
                    continue
                ok = await _run_one(target)
                self._last_run[target.name] = time.monotonic()
                if ok:
                    self._consecutive_errors[target.name] = 0
                else:
                    self._consecutive_errors[target.name] = errors + 1
                    await asyncio.sleep(target.error_backoff_ms / 1000.0)

            if self._stopped or self._should_stop():
                break
            await asyncio.sleep(min_interval_sec)

        _log.info("Scheduler loop exited (stopped=%s)", self._stopped)
