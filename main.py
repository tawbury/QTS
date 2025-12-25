"""
main.py

Observer-Core Phase 2 스모크 테스트용 엔트리 포인트

이 파일의 목적:
- Observer-Core 전체 흐름이 정상 동작하는지 확인
- JSONL 파일이 실제로 생성되는지 확인

주의:
- 이 파일은 예제/테스트 용도다.
- 전략 계산, 실거래, 자동 루프는 포함하지 않는다.
"""

import logging

from ops.observer.snapshot import build_snapshot
from ops.observer.event_bus import EventBus, JsonlFileSink
from ops.observer.observer import Observer


# --------------------------------------------------
# Logging 설정
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)


# --------------------------------------------------
# Sink / EventBus 구성
# --------------------------------------------------
# JsonlFileSink는 프로젝트 루트 기준
# data/observer/observer_test.jsonl 파일을 생성한다.

sink = JsonlFileSink(
    filename="observer_test.jsonl"
)

event_bus = EventBus([sink])


# --------------------------------------------------
# Observer 생성
# --------------------------------------------------
# session_id:
# - 이번 실행 묶음 ID
# - 로그/분석 시 구분용

observer = Observer(
    session_id="test_session",
    mode="DEV",
    event_bus=event_bus,
)

observer.start()


# --------------------------------------------------
# ObservationSnapshot 생성 (권장 방식)
# --------------------------------------------------
# build_snapshot()을 사용하면
# - 시간(timestamp)
# - run_id
# 를 자동으로 생성해준다.

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


# --------------------------------------------------
# Observer에 Snapshot 전달
# --------------------------------------------------
# 이 시점에 observer_test.jsonl 파일에
# 1줄의 JSON 데이터가 append 된다.

observer.on_snapshot(snapshot)

observer.stop()

print("DONE - observer_test.jsonl 파일을 확인하세요.")
