"""
운영 상태 관리자.

근거: docs/arch/sub/18_System_State_Promotion_Architecture.md §2~§6
- Hysteresis (최소 유지 시간, 쿨다운, 2-cycle 확인)
- 수동 오버라이드 (7일 자동 만료)
- Safety State와 직교적 관계 (Safety > Operating)
- 상태 영속성: JSON 파일 저장/복구, JSONL 전환 이력
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from src.safety.state import SafetyState
from src.shared.paths import data_dir
from src.state.contracts import (
    ManualOverride,
    OperatingState,
    OperatingStateSnapshot,
    StateProperties,
    STATE_PROPERTIES,
    TransitionMetrics,
)
from src.state.transition import (
    CONFIRMATION_CYCLES,
    COOLDOWN_HOURS,
    HYSTERESIS,
    find_applicable_rule,
)

logger = logging.getLogger(__name__)


@dataclass
class TransitionResult:
    """전환 시도 결과."""

    from_state: OperatingState
    to_state: OperatingState
    applied: bool
    reason: str
    meta: dict[str, Any] = field(default_factory=dict)


class OperatingStateManager:
    """운영 상태 관리자.

    - evaluate_transition(): 메트릭 기반 전환 평가
    - apply_override(): 수동 오버라이드
    - apply_safety_override(): Safety State에 의한 강제 전환
    """

    def __init__(
        self,
        initial_state: OperatingState = OperatingState.BALANCED,
        state_file: Optional[Path] = None,
    ) -> None:
        self._state = initial_state
        self._previous_state: Optional[OperatingState] = None
        self._transition_timestamp: Optional[datetime] = None
        self._transition_reason: Optional[str] = None
        self._state_entered_at: datetime = datetime.now(timezone.utc)
        self._last_transition_at: Optional[datetime] = None
        self._override: Optional[ManualOverride] = None

        # Hysteresis: 2-cycle 확인용
        self._pending_transition: Optional[tuple[OperatingState, int]] = None

        # 상태 영속성
        self._state_file: Path = state_file or (data_dir() / "operating_state.json")
        self._history_file: Path = self._state_file.parent / "state_history.jsonl"

        # state_file이 명시적으로 지정된 경우에만 저장된 상태를 자동 복구
        if state_file is not None:
            self.load_state()

    @property
    def current_state(self) -> OperatingState:
        return self._state

    @property
    def previous_state(self) -> Optional[OperatingState]:
        return self._previous_state

    @property
    def properties(self) -> StateProperties:
        return STATE_PROPERTIES[self._state]

    @property
    def state_duration_days(self) -> float:
        """현재 상태 유지 기간 (일)."""
        delta = datetime.now(timezone.utc) - self._state_entered_at
        return delta.total_seconds() / 86400

    @property
    def has_override(self) -> bool:
        return self._override is not None

    def evaluate_transition(
        self,
        metrics: TransitionMetrics,
        safety_state: SafetyState,
    ) -> TransitionResult:
        """메트릭 기반 상태 전환 평가.

        Hysteresis 적용:
        1. 현재 상태 최소 유지 시간 확인
        2. 쿨다운 확인 (24시간)
        3. 2-cycle 확인 (조건 2회 연속 충족)
        """
        # 오버라이드 활성 시 자동 전환 차단
        if self._override is not None:
            self._check_override_expiry()
            if self._override is not None:
                return TransitionResult(
                    from_state=self._state,
                    to_state=self._state,
                    applied=False,
                    reason="manual_override_active",
                )

        # 최소 유지 시간 확인 (위험 전환은 예외)
        hysteresis = HYSTERESIS[self._state]
        duration = self.state_duration_days

        rule = find_applicable_rule(
            self._state, metrics, safety_state, duration
        )
        if rule is None:
            self._pending_transition = None
            return TransitionResult(
                from_state=self._state,
                to_state=self._state,
                applied=False,
                reason="no_transition_needed",
            )

        # 위험 전환(→DEFENSIVE)은 Hysteresis 건너뜀
        is_danger_transition = rule.to_state == OperatingState.DEFENSIVE
        if not is_danger_transition:
            if duration < hysteresis.min_duration_days:
                return TransitionResult(
                    from_state=self._state,
                    to_state=self._state,
                    applied=False,
                    reason=f"min_duration_not_met: {duration:.1f}/{hysteresis.min_duration_days}d",
                )

            # 쿨다운 확인
            if self._last_transition_at is not None:
                cooldown_end = self._last_transition_at + timedelta(
                    hours=COOLDOWN_HOURS
                )
                if datetime.now(timezone.utc) < cooldown_end:
                    return TransitionResult(
                        from_state=self._state,
                        to_state=self._state,
                        applied=False,
                        reason="cooldown_period",
                    )

        # 2-cycle 확인 (위험 전환 포함)
        if self._pending_transition is not None:
            pending_state, count = self._pending_transition
            if pending_state == rule.to_state:
                count += 1
            else:
                # 다른 상태로 전환 시도 → 리셋
                count = 1
                pending_state = rule.to_state
        else:
            pending_state = rule.to_state
            count = 1

        if count < CONFIRMATION_CYCLES:
            self._pending_transition = (pending_state, count)
            return TransitionResult(
                from_state=self._state,
                to_state=self._state,
                applied=False,
                reason=f"confirmation_pending: {count}/{CONFIRMATION_CYCLES}",
            )

        # 전환 실행
        return self._apply_transition(rule.to_state, rule.reason(metrics))

    def apply_override(self, override: ManualOverride) -> TransitionResult:
        """수동 오버라이드 적용 (§4.1)."""
        self._override = override
        return self._apply_transition(
            override.override_state,
            f"manual_override: {override.override_reason}",
        )

    def clear_override(self) -> None:
        """수동 오버라이드 해제."""
        if self._override is None:
            return
        revert_state = self._override.auto_revert_state
        self._override = None
        self._apply_transition(revert_state, "override_cleared")

    def apply_safety_override(self, safety_state: SafetyState) -> TransitionResult:
        """Safety State에 의한 강제 전환 (§6.2).

        - FAIL → DEFENSIVE 강제
        - LOCKDOWN → 상태 보존 (트레이딩 중단은 Safety Layer가 담당)
        - LOCKDOWN 해제 시 AGGRESSIVE였으면 BALANCED로 복귀
        """
        if safety_state == SafetyState.FAIL and self._state != OperatingState.DEFENSIVE:
            return self._apply_transition(
                OperatingState.DEFENSIVE,
                "safety_fail_force_defensive",
            )

        return TransitionResult(
            from_state=self._state,
            to_state=self._state,
            applied=False,
            reason="no_safety_override_needed",
        )

    def on_lockdown_release(self) -> TransitionResult:
        """LOCKDOWN 해제 시 보수적 복귀 (§6.3)."""
        if self._state == OperatingState.AGGRESSIVE:
            return self._apply_transition(
                OperatingState.BALANCED,
                "lockdown_release_conservative",
            )
        return TransitionResult(
            from_state=self._state,
            to_state=self._state,
            applied=True,
            reason="lockdown_release_same_state",
        )

    def get_snapshot(self) -> OperatingStateSnapshot:
        """현재 상태 스냅샷."""
        self._check_override_expiry()
        return OperatingStateSnapshot(
            current_state=self._state,
            previous_state=self._previous_state,
            transition_timestamp=self._transition_timestamp,
            transition_reason=self._transition_reason,
            manual_override=self._override is not None,
            override_expiry=(
                self._override.expiry_time if self._override else None
            ),
            state_duration_days=self.state_duration_days,
            properties=self.properties,
        )

    def save_state(self) -> None:
        """현재 상태를 JSON 파일에 저장."""
        payload = {
            "current_state": self._state.value,
            "previous_state": self._previous_state.value if self._previous_state else None,
            "transition_timestamp": (
                self._transition_timestamp.isoformat()
                if self._transition_timestamp
                else None
            ),
            "state_entered_at": self._state_entered_at.isoformat(),
        }
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            self._state_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            logger.warning("상태 파일 저장 실패: %s", self._state_file, exc_info=True)

    def load_state(self) -> None:
        """저장된 상태를 로드하여 복구.

        파일이 없거나 파싱 실패 시 조용히 기본값을 유지한다.
        """
        if not self._state_file.exists():
            return
        try:
            raw = json.loads(self._state_file.read_text(encoding="utf-8"))
            self._state = OperatingState(raw["current_state"])
            self._previous_state = (
                OperatingState(raw["previous_state"])
                if raw.get("previous_state")
                else None
            )
            self._transition_timestamp = (
                datetime.fromisoformat(raw["transition_timestamp"])
                if raw.get("transition_timestamp")
                else None
            )
            self._state_entered_at = (
                datetime.fromisoformat(raw["state_entered_at"])
                if raw.get("state_entered_at")
                else self._state_entered_at
            )
            logger.info("저장된 운영 상태 복구: %s", self._state.value)
        except (json.JSONDecodeError, KeyError, ValueError):
            logger.warning(
                "상태 파일 파싱 실패, 기본값 사용: %s", self._state_file, exc_info=True
            )

    def _log_transition(
        self,
        from_state: OperatingState,
        to_state: OperatingState,
        reason: str,
    ) -> None:
        """전환 이력을 JSONL 로그 파일에 기록 (append-only)."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from_state": from_state.value,
            "to_state": to_state.value,
            "reason": reason,
        }
        try:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            with self._history_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            logger.warning("전환 이력 기록 실패: %s", self._history_file, exc_info=True)

    def _apply_transition(
        self, to_state: OperatingState, reason: str
    ) -> TransitionResult:
        """내부: 상태 전환 실행."""
        prev = self._state
        self._previous_state = prev
        self._state = to_state
        self._transition_timestamp = datetime.now(timezone.utc)
        self._transition_reason = reason
        self._state_entered_at = datetime.now(timezone.utc)
        self._last_transition_at = datetime.now(timezone.utc)
        self._pending_transition = None

        logger.info(
            "Operating state: %s → %s (%s)", prev.value, to_state.value, reason
        )

        # 상태 영속성: 저장 및 이력 기록
        self.save_state()
        self._log_transition(prev, to_state, reason)

        return TransitionResult(
            from_state=prev,
            to_state=to_state,
            applied=True,
            reason=reason,
        )

    def _check_override_expiry(self) -> None:
        """오버라이드 만료 확인."""
        if self._override is None:
            return
        if datetime.now(timezone.utc) >= self._override.expiry_time:
            logger.info("Manual override expired, reverting")
            self.clear_override()
