"""
Phase 7 — Safety/Risk: Safety State Machine & Lockdown.

근거: docs/arch/07_FailSafe_Architecture.md §6
- Safety 상태: NORMAL / WARNING / FAIL / LOCKDOWN (명시적 상수, 암묵적 플래그 없음)
- 전이 규칙: NORMAL → WARNING → FAIL → LOCKDOWN; FAIL/LOCKDOWN → NORMAL (복구 조건 시)
- Lockdown: Fail-Safe 2회 연속 시 자동 Lockdown; 운영자 승인 시에만 해제
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

# --- Safety States (Arch §6.1) ---


class SafetyState(str, Enum):
    """Safety 상태. pipeline_state와 동일 값 사용 (UI Contract §3.5)."""

    NORMAL = "NORMAL"
    WARNING = "WARNING"
    FAIL = "FAIL"
    LOCKDOWN = "LOCKDOWN"


# --- 전이 규칙 (Arch §6.2, §6.4) ---

# 허용 전이: (from_state, event) -> to_state
# event: "anomaly" | "fail_safe" | "guardrail" | "recovery"
_TRANSITIONS: Dict[tuple[SafetyState, str], SafetyState] = {
    (SafetyState.NORMAL, "anomaly"): SafetyState.WARNING,
    (SafetyState.NORMAL, "fail_safe"): SafetyState.FAIL,
    (SafetyState.WARNING, "anomaly"): SafetyState.WARNING,
    (SafetyState.WARNING, "fail_safe"): SafetyState.FAIL,
    (SafetyState.WARNING, "guardrail"): SafetyState.WARNING,
    (SafetyState.FAIL, "recovery"): SafetyState.NORMAL,
    (SafetyState.LOCKDOWN, "recovery"): SafetyState.NORMAL,
}

# Lockdown 진입: FAIL 상태에서 fail_safe 2회 연속 시 (Arch §6.4)
LOCKDOWN_CONSECUTIVE_FAIL_THRESHOLD = 2


@dataclass
class StateTransitionResult:
    """한 번의 전이 시도 결과."""

    from_state: SafetyState
    to_state: SafetyState
    event: str
    applied: bool  # True면 실제로 전이됨
    reason: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SafetyStateManager:
    """
    Safety 상태 머신. 상태 전이를 암묵적 플래그가 아닌 명시적 이벤트로만 수행.

    - apply_anomaly(): 이상 징후 → WARNING (NORMAL/WARNING 유지)
    - apply_fail_safe(code): Fail-Safe 발생 → FAIL; 연속 2회 시 LOCKDOWN
    - apply_guardrail(): Guardrail 발생 → WARNING 유지 (상태 변경 없을 수 있음)
    - request_recovery(operator_approved): FAIL/LOCKDOWN → NORMAL (LOCKDOWN은 operator_approved=True 필요)
    """

    _state: SafetyState = field(default=SafetyState.NORMAL, repr=False)
    _consecutive_fail_safe_count: int = field(default=0, repr=False)
    _last_fail_safe_code: Optional[str] = field(default=None, repr=False)

    @property
    def current_state(self) -> SafetyState:
        return self._state

    @property
    def pipeline_state(self) -> str:
        """UI Contract pipeline_state와 동일 값."""
        return self._state.value

    @property
    def consecutive_fail_safe_count(self) -> int:
        return self._consecutive_fail_safe_count

    @property
    def last_fail_safe_code(self) -> Optional[str]:
        return self._last_fail_safe_code

    @property
    def is_trading_allowed(self) -> bool:
        """거래 허용 여부. NORMAL/WARNING은 True, FAIL/LOCKDOWN은 False (Arch §1.4, §6.1)."""
        return self._state in (SafetyState.NORMAL, SafetyState.WARNING)

    @property
    def is_lockdown(self) -> bool:
        return self._state == SafetyState.LOCKDOWN

    def _apply_transition(self, event: str, operator_approved: bool = False) -> StateTransitionResult:
        key = (self._state, event)
        to_state = _TRANSITIONS.get(key)
        if to_state is None:
            return StateTransitionResult(
                from_state=self._state,
                to_state=self._state,
                event=event,
                applied=False,
                reason=f"no_transition_for_{self._state.value}_{event}",
            )
        if event == "recovery" and self._state == SafetyState.LOCKDOWN and not operator_approved:
            return StateTransitionResult(
                from_state=self._state,
                to_state=self._state,
                event=event,
                applied=False,
                reason="lockdown_requires_operator_approval",
                meta={"operator_approved": operator_approved},
            )
        prev = self._state
        self._state = to_state
        if to_state == SafetyState.NORMAL:
            self._consecutive_fail_safe_count = 0
            self._last_fail_safe_code = None
        return StateTransitionResult(
            from_state=prev,
            to_state=to_state,
            event=event,
            applied=True,
            meta={"operator_approved": operator_approved} if event == "recovery" else {},
        )

    def apply_anomaly(self, code: Optional[str] = None) -> StateTransitionResult:
        """이상 징후 적용. NORMAL→WARNING, WARNING 유지 (Arch §5.3)."""
        return self._apply_transition("anomaly")

    def apply_guardrail(self, code: Optional[str] = None) -> StateTransitionResult:
        """Guardrail 적용. 현재 규칙에서는 상태 유지(명시적 전이 없을 수 있음)."""
        # WARNING 유지 등; 전이 테이블에만 guardrail→WARNING 있음
        return self._apply_transition("guardrail")

    def apply_fail_safe(self, code: str) -> StateTransitionResult:
        """
        Fail-Safe 적용.
        - NORMAL/WARNING → FAIL
        - 이미 FAIL인 상태에서 다시 호출 시 연속 횟수 증가; 2회 이상이면 LOCKDOWN (Arch §6.4)
        """
        if self._state == SafetyState.FAIL:
            self._consecutive_fail_safe_count += 1
            self._last_fail_safe_code = code
            if self._consecutive_fail_safe_count >= LOCKDOWN_CONSECUTIVE_FAIL_THRESHOLD:
                self._state = SafetyState.LOCKDOWN
                return StateTransitionResult(
                    from_state=SafetyState.FAIL,
                    to_state=SafetyState.LOCKDOWN,
                    event="fail_safe",
                    applied=True,
                    reason="consecutive_fail_safe_lockdown",
                    meta={
                        "code": code,
                        "consecutive_count": self._consecutive_fail_safe_count,
                        "threshold": LOCKDOWN_CONSECUTIVE_FAIL_THRESHOLD,
                    },
                )
            return StateTransitionResult(
                from_state=SafetyState.FAIL,
                to_state=SafetyState.FAIL,
                event="fail_safe",
                applied=True,
                reason="consecutive_fail_safe_count_incremented",
                meta={"code": code, "consecutive_count": self._consecutive_fail_safe_count},
            )
        # NORMAL or WARNING → FAIL
        prev = self._state
        self._state = SafetyState.FAIL
        self._consecutive_fail_safe_count = 1
        self._last_fail_safe_code = code
        return StateTransitionResult(
            from_state=prev,
            to_state=SafetyState.FAIL,
            event="fail_safe",
            applied=True,
            meta={"code": code},
        )

    def request_recovery(self, operator_approved: bool = False) -> StateTransitionResult:
        """
        복구 요청.
        - FAIL → NORMAL: 조건 충족 시 (수동 복귀)
        - LOCKDOWN → NORMAL: 운영자 승인 시에만 (Arch §6.2)
        """
        return self._apply_transition("recovery", operator_approved=operator_approved)

    def snapshot(self) -> Dict[str, Any]:
        """현재 상태 스냅샷 (로깅/UI용)."""
        return {
            "pipeline_state": self.pipeline_state,
            "consecutive_fail_safe_count": self._consecutive_fail_safe_count,
            "last_fail_safe_code": self._last_fail_safe_code,
            "is_trading_allowed": self.is_trading_allowed,
            "is_lockdown": self.is_lockdown,
        }


def allowed_transitions() -> Dict[str, list[str]]:
    """문서/검증용: 상태별 허용 전이 이벤트."""
    by_state: Dict[str, list[str]] = {
        s.value: [] for s in SafetyState
    }
    for (from_s, event), to_s in _TRANSITIONS.items():
        by_state[from_s.value].append(event)
    return by_state
