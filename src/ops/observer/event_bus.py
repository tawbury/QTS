from __future__ import annotations

"""
event_bus.py

Observer-Core에서 생성된 PatternRecord를
"어디로 보낼지"를 관리하는 전달 계층(Event Bus)

초보자 가이드
- Observer는 기록을 '직접 저장'하지 않는다.
- Observer는 EventBus에게 "이 기록을 처리해줘"라고 맡긴다.
- EventBus는 여러 Sink(출력 대상)에게 전달할 수 있다.

현재 Phase 2에서는:
- 출력 대상(Sink)은 JSONL 파일 하나뿐이다.
- 구조는 향후 DB / API / 스트리밍으로 확장 가능하다.
"""

import json
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Iterable, List

from .pattern_record import PatternRecord


logger = logging.getLogger(__name__)


# ============================================================
# Sink Interface
# ============================================================

class SnapshotSink(ABC):
    """
    SnapshotSink 인터페이스

    역할:
    - PatternRecord를 받아서 "어딘가에 저장하거나 전달"한다.

    예시:
    - JsonlFileSink  → 파일에 저장
    - DbSink         → DB에 저장 (미래)
    - ApiSink        → 외부 API 전송 (미래)

    Observer / EventBus는
    Sink의 내부 구현을 알 필요가 없다.
    """

    @abstractmethod
    def publish(self, record: PatternRecord) -> None:
        """
        record 하나를 처리한다.
        구현체에서 파일 저장 / DB 저장 등을 수행한다.
        """
        raise NotImplementedError


# ============================================================
# File Sink (Append-only JSONL)
# ============================================================

class JsonlFileSink(SnapshotSink):
    """
    PatternRecord를 JSONL 형식으로 파일에 저장하는 Sink

    저장 규칙:
    - append-only (기존 내용 수정 없음)
    - 1 PatternRecord = 1 JSON line
    - 실행 위치(CWD)에 상관없이 항상 동일한 경로 사용

    출력 경로:
    <PROJECT_ROOT>/data/observer/{filename}
    """

    def __init__(
        self,
        filename: str = "observer.jsonl",
    ) -> None:
        """
        filename:
        - 저장할 JSONL 파일 이름
        - 예: observer.jsonl / observer_test.jsonl
        """

        # --------------------------------------------------
        # 프로젝트 루트 계산
        # --------------------------------------------------
        # event_bus.py 위치 기준으로 상위 디렉터리를 탐색한다.
        #
        # 예시 구조:
        #   project_root/
        #     ├─ src/
        #     │   └─ ops/observer/event_bus.py
        #     └─ data/observer/
        #
        # parents[3] → project_root
        self.project_root = Path(__file__).resolve().parents[3]

        self.base_dir = self.project_root / "data" / "observer"
        self.file_path = self.base_dir / filename

        # 출력 디렉터리 자동 생성
        self.base_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "JsonlFileSink initialized",
            extra={"file_path": str(self.file_path)},
        )

    def publish(self, record: PatternRecord) -> None:
        """
        PatternRecord 1개를 파일에 한 줄(JSON)로 저장한다.
        """
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(record.to_dict(), ensure_ascii=False) + "\n"
                )
        except Exception:
            # 파일 기록 실패는 Observer 전체를 멈추지 않는다.
            logger.exception(
                "JsonlFileSink publish failed",
                extra={"file_path": str(self.file_path)},
            )


# ============================================================
# Event Bus
# ============================================================

class EventBus:
    """
    EventBus

    역할:
    - Observer로부터 PatternRecord를 전달받는다.
    - 등록된 모든 Sink에게 record를 전달한다.

    장점:
    - Observer는 출력 대상(파일/DB/네트워크)을 모른다.
    - Sink를 추가해도 Observer 코드는 바뀌지 않는다.
    """

    def __init__(self, sinks: Iterable[SnapshotSink]) -> None:
        """
        sinks:
        - PatternRecord를 처리할 Sink들의 목록
        - 보통 1개(JsonlFileSink)만 사용
        """
        self._sinks: List[SnapshotSink] = list(sinks)

    def dispatch(self, record: PatternRecord) -> None:
        """
        PatternRecord를 모든 Sink에 전달한다.
        """
        for sink in self._sinks:
            try:
                sink.publish(record)
            except Exception:
                # Sink 하나의 오류가 전체 파이프라인을 깨지 않도록 보호
                logger.exception(
                    "Unexpected exception from SnapshotSink",
                    extra={"sink": sink.__class__.__name__},
                )
