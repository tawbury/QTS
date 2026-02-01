"""
Mock Safety Hook for local-only mode.

PipelineSafetyHook 프로토콜을 구현하지만, 실제 Kill Switch나
Safety Layer 없이 동작합니다.
--local-only 모드에서 Safety 의존성 없이 파이프라인을 테스트할 수 있습니다.
"""

from __future__ import annotations

import logging
from typing import List, Tuple


class MockSafetyHook:
    """
    Mock Safety Hook

    PipelineSafetyHook 프로토콜을 구현하지만,
    실제 Kill Switch나 Safety Layer 없이 동작합니다.
    """

    def __init__(self, initial_state: str = "NORMAL"):
        """
        MockSafetyHook 초기화

        Args:
            initial_state: 초기 pipeline_state (NORMAL/WARNING/FAIL/LOCKDOWN)
        """
        self._state = initial_state
        self._should_run = True
        self._fail_safe_records: List[Tuple[str, str, str]] = []
        self._logger = logging.getLogger(__name__)
        self._logger.info(f"MockSafetyHook initialized (state={initial_state})")

    def should_run(self) -> bool:
        """
        파이프라인 1회 실행 허용 여부.

        Returns:
            bool: 항상 True (mock), 단 set_should_run()으로 변경 가능
        """
        return self._should_run

    def record_fail_safe(self, code: str, message: str, stage: str) -> None:
        """
        Fail-Safe 발생 기록 (로그만 출력).

        Args:
            code: Fail-Safe 코드 (예: FS040)
            message: 메시지
            stage: 발생 단계 (예: Act)
        """
        self._fail_safe_records.append((code, message, stage))
        self._logger.warning(f"[MockSafetyHook] Fail-Safe recorded: {code} - {message} @ {stage}")

        # 상태 전이 시뮬레이션
        if code.startswith("FS"):
            if self._state == "NORMAL":
                self._state = "WARNING"
            elif self._state == "WARNING":
                self._state = "FAIL"

    def pipeline_state(self) -> str:
        """
        현재 pipeline_state 반환.

        Returns:
            str: 현재 상태 (NORMAL/WARNING/FAIL/LOCKDOWN)
        """
        return self._state

    # === 테스트용 메서드 ===

    def set_should_run(self, value: bool) -> None:
        """테스트용: should_run() 반환값 설정"""
        self._should_run = value
        self._logger.debug(f"[MockSafetyHook] set_should_run({value})")

    def set_state(self, state: str) -> None:
        """테스트용: pipeline_state 직접 설정"""
        self._state = state
        self._logger.debug(f"[MockSafetyHook] set_state({state})")

    def get_fail_safe_records(self) -> List[Tuple[str, str, str]]:
        """테스트용: 기록된 Fail-Safe 목록 반환"""
        return list(self._fail_safe_records)

    def clear_records(self) -> None:
        """테스트용: 기록 초기화"""
        self._fail_safe_records.clear()
        self._state = "NORMAL"
        self._should_run = True
        self._logger.debug("[MockSafetyHook] Records cleared, state reset to NORMAL")
