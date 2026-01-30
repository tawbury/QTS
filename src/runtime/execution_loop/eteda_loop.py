"""
ETEDA 반복 실행 루프 (Phase 5 – Trigger & Loop Control).

- Scheduler는 ETEDA 외부에 위치; 본 모듈은 "주기 실행 + 안전 중단/백오프"만 담당.
- ETEDA 단계(Extract/Transform/Evaluate/Decide/Act)는 Runner 내부에만 존재하며,
  루프는 오직 runner.run_once(snapshot) 호출만 수행(단계 책임 침범 없음).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, Optional, Protocol, Union


class ETEDARunnerLike(Protocol):
    def run_once(self, snapshot: Dict[str, Any]) -> Awaitable[Dict[str, Any]]: ...


from runtime.config.config_models import UnifiedConfig
from runtime.execution_loop.eteda_loop_policy import (
    ETEDALoopPolicy,
    ETEDALoopShouldStop,
    default_should_stop_from_config,
)


_log = logging.getLogger("ETEDALoop")


SnapshotSource = Union[
    Callable[[], Dict[str, Any]],
    Callable[[], Awaitable[Dict[str, Any]]],
]


def _default_snapshot() -> Dict[str, Any]:
    """interval 전용 트리거: 최소 스냅샷(Runner의 Extract가 추가 데이터를 가져올 수 있음)."""
    import time
    return {"trigger": "interval", "meta": {"timestamp_ms": int(time.time() * 1000)}}


async def _get_snapshot(source: SnapshotSource) -> Dict[str, Any]:
    out = source()
    if asyncio.iscoroutine(out):
        return await out
    return out


async def run_eteda_loop(
    runner: ETEDARunnerLike,
    config: UnifiedConfig,
    *,
    policy: Optional[ETEDALoopPolicy] = None,
    should_stop: Optional[ETEDALoopShouldStop] = None,
    snapshot_source: Optional[SnapshotSource] = None,
) -> None:
    """
    ETEDA 반복 실행. run_once만 호출하며, Extract/Transform/Evaluate/Decide/Act 로직은 Runner에 위임.

    Args:
        runner: ETEDARunner(또는 run_once(snapshot)를 갖는 객체).
        config: UnifiedConfig (INTERVAL_MS, PIPELINE_PAUSED, ERROR_BACKOFF_*).
        policy: 없으면 Config로부터 생성.
        should_stop: 없으면 Config의 PIPELINE_PAUSED로 생성.
        snapshot_source: 없으면 interval 전용 최소 스냅샷 사용.
    """
    policy = policy or ETEDALoopPolicy.from_config(config)
    stop_fn = should_stop or default_should_stop_from_config(config)
    snapshot_fn = snapshot_source or _default_snapshot
    consecutive_errors = 0

    while True:
        if stop_fn():
            _log.info("ETEDA loop stopped (should_stop=True)")
            break

        try:
            snapshot = await _get_snapshot(snapshot_fn)
            result = await runner.run_once(snapshot)
            consecutive_errors = 0
            status = result.get("status")
            if status == "error":
                _log.warning("run_once returned error: %s", result.get("error"))
            elif status:
                _log.debug("run_once status=%s", status)
        except Exception as e:
            consecutive_errors += 1
            _log.exception("ETEDA run_once failed (consecutive=%s): %s", consecutive_errors, e)
            if consecutive_errors > policy.error_backoff_max_retries:
                _log.error("ETEDA loop stopping after max consecutive errors")
                break
            await asyncio.sleep(policy.error_backoff_ms / 1000.0)

        if stop_fn():
            _log.info("ETEDA loop stopped (should_stop=True)")
            break

        await asyncio.sleep(policy.interval_ms / 1000.0)
