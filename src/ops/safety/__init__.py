"""
Phase 7 — Safety/Risk: Fail-Safe, Guardrail, Anomaly 코드 및 Guard 집약 API.

- codes: Fail-Safe(FS*), Guardrail(GR*, G_EXE_*), Anomaly(AN*) 코드 테이블
- guard: 단계별 Safety 체크(Extract/Transform/Evaluate/Decide/Act) 및 SafetyResult
- state: Safety State Machine (NORMAL/WARNING/FAIL/LOCKDOWN) 및 Lockdown 절차
- notifier: Safety 이벤트 알림 최소 규격 (SafetyEvent, SafetyNotifier, NoOp/InMemory)
- layer: SafetyLayer 파사드 (Kill Switch, Safe Mode, 자동 복구, PipelineSafetyHook)
"""
from __future__ import annotations

from .codes import (
    ANOMALY_TABLE,
    ETEDA_STAGE,
    FAIL_SAFE_TABLE,
    GUARDRAIL_TABLE,
    CodeInfo,
    codes_by_stage,
    get_anomaly_info,
    get_code_info,
    get_failsafe_info,
    get_guardrail_info,
    message_for,
)
from .guard import (
    SafetyResult,
    check_act_safety,
    check_decide_safety,
    check_evaluate_safety,
    check_extract_safety,
    check_transform_safety,
    safety_result_from_guard_code,
)
from .state import (
    LOCKDOWN_CONSECUTIVE_FAIL_THRESHOLD,
    SafetyState,
    SafetyStateManager,
    StateTransitionResult,
    allowed_transitions,
)
from .notifier import (
    SafetyEvent,
    SafetyNotifier,
    NoOpNotifier,
    InMemoryNotifier,
    default_message_template,
)
from .layer import SafetyLayer

__all__ = [
    # codes
    "ETEDA_STAGE",
    "FAIL_SAFE_TABLE",
    "GUARDRAIL_TABLE",
    "ANOMALY_TABLE",
    "CodeInfo",
    "codes_by_stage",
    "get_failsafe_info",
    "get_guardrail_info",
    "get_anomaly_info",
    "get_code_info",
    "message_for",
    # guard
    "SafetyResult",
    "check_extract_safety",
    "check_transform_safety",
    "check_evaluate_safety",
    "check_decide_safety",
    "check_act_safety",
    "safety_result_from_guard_code",
    # state
    "SafetyState",
    "SafetyStateManager",
    "StateTransitionResult",
    "LOCKDOWN_CONSECUTIVE_FAIL_THRESHOLD",
    "allowed_transitions",
    # notifier
    "SafetyEvent",
    "SafetyNotifier",
    "NoOpNotifier",
    "InMemoryNotifier",
    "default_message_template",
    # layer
    "SafetyLayer",
]
