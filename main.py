# main.py
from __future__ import annotations

# ============================================================
# Ensure src/ is on sys.path (QTS bootstrap)
# ============================================================

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ============================================================
# Imports
# ============================================================

import logging

from ops.observer.snapshot import build_snapshot
from ops.observer.event_bus import EventBus, JsonlFileSink
from ops.observer.observer import Observer

# ============================================================
# Logging
# ============================================================

logging.basicConfig(level=logging.INFO)

# ============================================================
# Sink / EventBus
# ============================================================

# ⚠️ 주의:
# event_bus.py 기준 기본 파일명은 observer.jsonl 이지만
# 여기서는 테스트 목적이므로 observer_test.jsonl 사용
# 테스트 완료 되어 observer.jsonl로 수정

sink = JsonlFileSink(
    filename="observer.jsonl"
)

event_bus = EventBus([sink])

# ============================================================
# Observer
# ============================================================

observer = Observer(
    session_id="test_session",
    mode="DEV",
    event_bus=event_bus,
)

observer.start()

# ============================================================
# ObservationSnapshot 생성
# ============================================================

snapshot = build_snapshot(
    session_id="test_session",
    mode="DEV",
    source="market",
    stage="raw",
    symbol="TEST",
    market="SIM",
    inputs={
        "price": 100.0,
        "volume": 10,
    },
    computed={},
    state={},
)

# ============================================================
# Observer에 Snapshot 전달
# ============================================================

observer.on_snapshot(snapshot)

observer.stop()

print("DONE - data/observer/observer_test.jsonl 파일을 확인하세요.")
