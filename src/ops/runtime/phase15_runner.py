from __future__ import annotations

import logging
import os
from typing import Any, Optional, Type
from uuid import uuid4

from ops.runtime.phase15_current_price_source import build_phase15_source
from ops.runtime.phase15_input_bridge import Phase15InputBridge

log = logging.getLogger("Phase15Runner")


def _configure_logging() -> None:
    # 프로젝트 로깅 체계가 있으면 그걸 쓰고, 없으면 기본만 세팅
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )


def _safety_assertions() -> None:
    """
    Phase 15: 조용한 실패 금지 / 매매 금지.
    """
    trading_enabled = os.getenv("TRADING_ENABLED", "false").lower().strip()
    if trading_enabled in {"1", "true", "yes", "y"}:
        raise RuntimeError("Phase 15 requires TRADING_ENABLED=false (NO TRADING).")


def _import_snapshot_cls() -> Type[Any]:
    """
    ObservationSnapshot 위치 유연 import
    """
    candidates = [
        ("ops.observer.snapshot", "ObservationSnapshot"),
        ("ops.observer.core.snapshot", "ObservationSnapshot"),
        ("ops.observer.observation.snapshot", "ObservationSnapshot"),
    ]

    last_err: Optional[Exception] = None
    for module_name, cls_name in candidates:
        try:
            mod = __import__(module_name, fromlist=[cls_name])
            return getattr(mod, cls_name)
        except Exception as e:
            last_err = e

    raise RuntimeError(
        "ObservationSnapshot import failed. "
        "Create snapshot class or adjust import candidates in phase15_runner.py"
    ) from last_err


def _import_observer() -> Type[Any]:
    """
    Observer 위치 유연 import
    """
    candidates = [
        ("ops.observer.observer", "Observer"),
        ("ops.observer.core.observer", "Observer"),
    ]

    last_err: Optional[Exception] = None
    for module_name, cls_name in candidates:
        try:
            mod = __import__(module_name, fromlist=[cls_name])
            return getattr(mod, cls_name)
        except Exception as e:
            last_err = e

    raise RuntimeError(
        "Observer import failed. Create Observer or adjust import candidates in phase15_runner.py"
    ) from last_err


def _build_phase15_observer(ObserverCls: Type[Any]) -> Any:
    """
    Phase 15 전용 Observer 생성 (정식 생성자 사용)
    - EventBus는 '빈 sink'로 구성 (관찰 전용)
    """
    try:
        from ops.observer.event_bus import EventBus
    except Exception as e:
        raise RuntimeError(
            "EventBus import failed. Phase 15 requires existing Observer infra."
        ) from e

    session_id = f"phase15-{uuid4()}"
    mode = "phase15"

    # Phase 15: 이벤트는 흘리되 소비자는 없음
    event_bus = EventBus(sinks=[])

    return ObserverCls(
        session_id=session_id,
        mode=mode,
        event_bus=event_bus,
    )



def run_phase15_current_price(symbol: str) -> None:
    _configure_logging()
    _safety_assertions()

    SnapshotCls = _import_snapshot_cls()
    ObserverCls = _import_observer()

    # ✅ 여기서 observer를 반드시 생성해야 한다 (누락됐던 핵심)
    observer = _build_phase15_observer(ObserverCls)

    source = build_phase15_source(symbol=symbol)
    bridge = Phase15InputBridge(snapshot_cls=SnapshotCls)

    log.info("Phase 15 start | mode=current_price | symbol=%s", symbol)

    for ev in source.stream():
        try:
            snapshot = bridge.build_snapshot(ev)

            # Observer entrypoint 유연 대응
            if hasattr(observer, "observe"):
                observer.observe(snapshot)
            elif hasattr(observer, "on_snapshot"):
                observer.on_snapshot(snapshot)
            else:
                raise RuntimeError(
                    "Observer has no known entrypoint: observe(snapshot) or on_snapshot(snapshot)"
                )

            # Phase 15 관찰용 최소 로그
            log.info("tick received_at=%s", ev.received_at)

        except Exception:
            # Phase 15 원칙: 조용한 실패 금지
            log.exception("Phase 15 ingest failed")
            raise


if __name__ == "__main__":
    sym = os.getenv("PHASE15_SYMBOL", "005930")
    run_phase15_current_price(symbol=sym)
