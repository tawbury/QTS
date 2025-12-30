from __future__ import annotations

"""
event_bus.py

Observer-Core에서 생성된 PatternRecord를
"어디로 보낼지"를 관리하는 전달 계층(Event Bus)

초보자 가이드
- Observer는 기록을 '직접 저장'하지 않는다.
- Observer는 EventBus에게 "이 기록을 처리해줘"라고 맡긴다.
- EventBus는 여러 Sink(출력 대상)에게 전달할 수 있다.

Phase F 규칙:
- Observer 이벤트 로그는 '운영 자산'으로 간주된다.
- 모든 Observer JSONL 로그는 paths.py가 정의한
  canonical observer asset directory에 저장된다.
- event_bus.py는 더 이상 프로젝트 루트나
  실제 파일 시스템 구조를 추론하지 않는다.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Iterable, List

from .pattern_record import PatternRecord
from paths import observer_asset_dir, observer_asset_file


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

    Phase F 규칙:
    - Observer 로그는 '운영 자산'이다.
    - 실제 저장 경로는 paths.py가 유일하게 결정한다.

    출력 경로:
    observer_asset_dir() / {filename}
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
        # Phase F: 경로 책임은 paths.py 단일 SSoT
        # --------------------------------------------------
        self.base_dir = observer_asset_dir()
        self.file_path = observer_asset_file(filename)

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
