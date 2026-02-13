"""
Event System 브릿지 어댑터.

런타임 의존성(Safety Layer)을 Event 시스템에 연결하는 어댑터.
근거: docs/arch/sub/17_Event_Priority_Architecture.md §7.2
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from src.event.contracts import DegradationLevel
from src.safety.state import SafetyState

logger = logging.getLogger(__name__)

# Safety State → Degradation Level 매핑 (§7.2)
_SAFETY_TO_DEGRADATION: dict[SafetyState, DegradationLevel] = {
    SafetyState.NORMAL: DegradationLevel.NORMAL,
    SafetyState.WARNING: DegradationLevel.P3_PAUSED,
    SafetyState.FAIL: DegradationLevel.P2_P3_PAUSED,
    SafetyState.LOCKDOWN: DegradationLevel.CRITICAL_ONLY,
}


class SafetyEventBridge:
    """Safety Layer → EventDispatcher 성능 저하 레벨 연동.

    Safety Layer의 pipeline_state() 값을 EventDispatcher의
    degradation level로 변환하여 적용한다.
    """

    def __init__(
        self,
        event_dispatcher: Any,
        safety_layer: Optional[Any] = None,
    ) -> None:
        self._dispatcher = event_dispatcher
        self._safety = safety_layer
        self._last_state: Optional[SafetyState] = None

    def sync(self) -> None:
        """Safety Layer 현재 상태를 EventDispatcher에 동기화.

        매 ETEDA 사이클 시작 시 호출하여 상태를 갱신한다.
        상태가 변경되지 않았으면 호출을 무시한다.
        """
        if self._safety is None or self._dispatcher is None:
            return

        try:
            pipeline_state = self._safety.pipeline_state()
            safety_state = _parse_safety_state(pipeline_state)

            if safety_state == self._last_state:
                return

            self._last_state = safety_state
            self._dispatcher.apply_safety_state(safety_state)
            logger.info(
                "SafetyEventBridge: synced %s → %s",
                safety_state.value,
                _SAFETY_TO_DEGRADATION[safety_state].value,
            )
        except Exception:
            logger.warning("SafetyEventBridge sync failed (non-blocking)")


def _parse_safety_state(pipeline_state: str) -> SafetyState:
    """pipeline_state 문자열을 SafetyState로 변환."""
    normalized = pipeline_state.upper()
    try:
        return SafetyState(normalized)
    except ValueError:
        return SafetyState.NORMAL
