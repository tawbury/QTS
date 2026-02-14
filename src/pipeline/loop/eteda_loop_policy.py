"""
ETEDA Loop Policy (Phase 5 – Trigger & Loop Control).

근거: docs/arch/03_Pipeline_ETEDA_Architecture.md

정책 요약:
- 트리거: interval 기반 우선(Config INTERVAL_MS). event 기반은 선택(스냅샷 공급).
  병행 시: interval이 주기, event는 스냅샷 소스; run_once 중복 실행 금지(한 사이클당 1회).
- 중단: Config PIPELINE_PAUSED / system_running 또는 외부 should_stop → 즉시 루프 탈출.
- 재시작: 루프는 단일 실행 단위; 재시작 = 새 루프 인스턴스 실행.
- 에러 백오프: run_once 예외 시 ERROR_BACKOFF_MS 만큼 대기 후 재시도;
  ERROR_BACKOFF_MAX_RETRIES 초과 또는 Fail-Safe/Critical 시 루프 중단.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.qts.core.config.config_models import UnifiedConfig


class ETEDALoopShouldStop(Protocol):
    """루프 중단 조건. Config(PIPELINE_PAUSED) 또는 외부 플래그."""

    def __call__(self) -> bool: ...


def default_should_stop_from_config(config: UnifiedConfig) -> ETEDALoopShouldStop:
    """Config의 PIPELINE_PAUSED(truthy)이면 중단."""

    def should_stop() -> bool:
        v = config.get_flat("PIPELINE_PAUSED") or config.get_flat("pipeline_paused")
        if v is None:
            return False
        return str(v).strip().lower() in ("1", "true", "yes", "on")

    return should_stop


@dataclass(frozen=True)
class ETEDALoopPolicy:
    """
    ETEDA 반복 실행 정책.

    - interval_ms: 주기 대기(ms). Config INTERVAL_MS 기본.
    - error_backoff_ms: run_once 예외 후 대기(ms).
    - error_backoff_max_retries: 연속 예외 허용 횟수, 초과 시 루프 중단.
    - no_overlap: True면 한 번에 하나의 run_once만 실행(기본 True).
    """

    interval_ms: int
    error_backoff_ms: int
    error_backoff_max_retries: int
    no_overlap: bool = True

    @classmethod
    def from_config(cls, config: UnifiedConfig) -> "ETEDALoopPolicy":
        interval = config.get_flat("INTERVAL_MS") or config.get_flat("interval_ms")
        interval_ms = int(interval) if interval is not None else 1000
        backoff = config.get_flat("ERROR_BACKOFF_MS") or config.get_flat("error_backoff_ms")
        error_backoff_ms = int(backoff) if backoff is not None else 5000
        max_ret = config.get_flat("ERROR_BACKOFF_MAX_RETRIES")
        error_backoff_max_retries = int(max_ret) if max_ret is not None else 3
        return cls(
            interval_ms=max(100, min(interval_ms, 60_000)),
            error_backoff_ms=max(500, min(error_backoff_ms, 60_000)),
            error_backoff_max_retries=max(0, min(error_backoff_max_retries, 20)),
            no_overlap=True,
        )
