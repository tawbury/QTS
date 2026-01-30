"""
Minimal Scheduler tests (Phase 9).

- add_target, run loop, should_stop, stop(), error backoff.
"""

from __future__ import annotations

import asyncio
import pytest

from ops.automation.scheduler import (
    TARGET_BACKUP_MAINTENANCE,
    TARGET_BROKER_HEARTBEAT,
    TARGET_DASHBOARD_UPDATE,
    TARGET_PIPELINE,
    MinimalScheduler,
)


@pytest.mark.asyncio
async def test_scheduler_empty_run_exits():
    s = MinimalScheduler()
    await s.run()
    # no targets -> exits immediately


@pytest.mark.asyncio
async def test_scheduler_stops_on_should_stop():
    runs = []

    def task():
        runs.append(1)
        return None

    stop_flag = [False]

    def should_stop():
        return stop_flag[0]

    s = MinimalScheduler(should_stop=should_stop)
    s.add_target("t1", 100, task)

    async def stop_soon():
        await asyncio.sleep(0.05)
        stop_flag[0] = True

    await asyncio.gather(s.run(), stop_soon())
    assert len(runs) >= 1


@pytest.mark.asyncio
async def test_scheduler_stop_method():
    runs = []

    def task():
        runs.append(1)
        return None

    s = MinimalScheduler()
    s.add_target("t1", 50, task)

    async def stop_after():
        await asyncio.sleep(0.1)
        s.stop()

    await asyncio.gather(s.run(), stop_after())
    assert len(runs) >= 1


@pytest.mark.asyncio
async def test_scheduler_target_names_defined():
    assert TARGET_PIPELINE == "pipeline"
    assert TARGET_BROKER_HEARTBEAT == "broker_heartbeat"
    assert TARGET_DASHBOARD_UPDATE == "dashboard_update"
    assert TARGET_BACKUP_MAINTENANCE == "backup_maintenance"


@pytest.mark.asyncio
async def test_scheduler_invokes_callable():
    invoked = []

    def fn():
        invoked.append(1)

    s = MinimalScheduler(should_stop=lambda: len(invoked) >= 2)
    s.add_target("t1", 20, fn)
    await s.run()
    assert len(invoked) >= 2


@pytest.mark.asyncio
async def test_scheduler_async_callable():
    invoked = []

    async def fn():
        invoked.append(1)
        await asyncio.sleep(0)

    s = MinimalScheduler(should_stop=lambda: len(invoked) >= 2)
    s.add_target("t1", 20, fn)
    await s.run()
    assert len(invoked) >= 2


@pytest.mark.asyncio
async def test_scheduler_failure_backoff_continues_loop():
    runs = []
    fail_count = [0]

    def fn():
        runs.append(1)
        fail_count[0] += 1
        if fail_count[0] <= 2:
            raise RuntimeError("simulated")
        return None

    s = MinimalScheduler(should_stop=lambda: len(runs) >= 4)
    s.add_target("t1", 30, fn, error_backoff_ms=20, max_consecutive_errors=5)
    await s.run()
    assert len(runs) >= 3
