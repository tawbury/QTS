"""
Phase 7 — Safety Layer 파사드.

Kill Switch, Safe Mode, 자동 복구, Notifier 연동.
PipelineSafetyHook 프로토콜을 만족하여 ETEDA Runner에 주입 가능.
근거: docs/arch/07_FailSafe_Architecture.md §1.3, §6.5
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from .notifier import SafetyEvent, SafetyNotifier
from .state import SafetyStateManager


class SafetyLayer:
    """
    Safety Layer 파사드.
    - Kill Switch: True면 should_run() False, 거래 차단.
    - Safe Mode: True면 Act 미수행(ETEDA Runner _act에서 처리); 여기서는 플래그만 보관.
    - 자동 복구: request_recovery(operator_approved)로 FAIL/LOCKDOWN → NORMAL.
    - PipelineSafetyHook 프로토콜: should_run(), record_fail_safe(), pipeline_state().
    """

    def __init__(
        self,
        state_manager: Optional[SafetyStateManager] = None,
        notifier: Optional[SafetyNotifier] = None,
        *,
        kill_switch: bool = False,
        safe_mode: bool = False,
        get_kill_switch: Optional[Callable[[], bool]] = None,
        get_safe_mode: Optional[Callable[[], bool]] = None,
    ) -> None:
        self._state = state_manager or SafetyStateManager()
        self._notifier = notifier
        self._kill_switch = kill_switch
        self._safe_mode = safe_mode
        self._get_kill_switch = get_kill_switch
        self._get_safe_mode = get_safe_mode

    @property
    def state_manager(self) -> SafetyStateManager:
        return self._state

    @property
    def kill_switch(self) -> bool:
        if self._get_kill_switch is not None:
            return self._get_kill_switch()
        return self._kill_switch

    @kill_switch.setter
    def kill_switch(self, value: bool) -> None:
        self._kill_switch = value

    @property
    def safe_mode(self) -> bool:
        if self._get_safe_mode is not None:
            return self._get_safe_mode()
        return self._safe_mode

    @safe_mode.setter
    def safe_mode(self, value: bool) -> None:
        self._safe_mode = value

    # --- PipelineSafetyHook ---

    def should_run(self) -> bool:
        """파이프라인 1회 실행 허용. Kill Switch ON이면 False."""
        if self.kill_switch:
            return False
        return self._state.is_trading_allowed

    def record_fail_safe(self, code: str, message: str, stage: str) -> None:
        """Fail-Safe 기록: 상태 전이 + 알림."""
        self._state.apply_fail_safe(code)
        if self._notifier is not None:
            ev = SafetyEvent.now(
                safety_code=code,
                level="FAIL",
                message=message,
                pipeline_state=self._state.pipeline_state,
                meta={"stage": stage},
            )
            self._notifier.notify(ev)

    def pipeline_state(self) -> str:
        """현재 pipeline_state (UI Contract §3.5)."""
        return self._state.pipeline_state

    # --- 추가 API (자동 복구 등) ---

    def request_recovery(self, operator_approved: bool = False) -> bool:
        """복구 요청. LOCKDOWN은 operator_approved=True 필요. 적용 여부 반환."""
        r = self._state.request_recovery(operator_approved=operator_approved)
        return r.applied

    def apply_safety_result(self, code: str, message: str, stage: str, blocked: bool) -> None:
        """SafetyResult 적용: blocked면 record_fail_safe 호출."""
        if blocked:
            self.record_fail_safe(code, message, stage)

    def snapshot(self) -> dict[str, Any]:
        """현재 상태 스냅샷 (로깅/UI용)."""
        out = self._state.snapshot()
        out["kill_switch"] = self.kill_switch
        out["safe_mode"] = self.safe_mode
        return out
