"""
Phase 7 — ETEDA Pipeline Safety Hook (Protocol).

runtime은 ops를 import하지 않음. 호출부(main/execution_loop)가 ops.safety.SafetyLayer를
이 프로토콜로 주입하여 ETEDA와 Safety Layer 연동.
근거: docs/arch/07_FailSafe_Architecture.md §1.5, §7
"""
from __future__ import annotations

from typing import Protocol


class PipelineSafetyHook(Protocol):
    """
    Safety Layer 연동용 최소 인터페이스.
    구현체: ops.safety.SafetyLayer
    """

    def should_run(self) -> bool:
        """파이프라인 1회 실행 허용 여부 (Kill Switch, Safe Mode, pipeline_state 반영)."""
        ...

    def record_fail_safe(self, code: str, message: str, stage: str) -> None:
        """Fail-Safe 발생 시 기록 (상태 전이, 알림)."""
        ...

    def pipeline_state(self) -> str:
        """현재 pipeline_state (NORMAL/WARNING/FAIL/LOCKDOWN). UI Contract §3.5."""
        ...
