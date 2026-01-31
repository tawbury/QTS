# Safety & Fail-Safe (Phase 7) — 진입점 및 상태 전이

PipelineSafetyHook·SafetyLayer·상태 머신·Guard·Codes 경로 정리. **근거**: [docs/arch/07_FailSafe_Architecture.md](../../../docs/arch/07_FailSafe_Architecture.md) §6, [16_Micro_Risk_Loop_Architecture.md](../../../docs/arch/sub/16_Micro_Risk_Loop_Architecture.md), [18_System_State_Promotion_Architecture.md](../../../docs/arch/sub/18_System_State_Promotion_Architecture.md)

---

## 1. 진입점·Wiring

| 컴포넌트 | 경로 | 진입점 | 비고 |
|----------|------|--------|------|
| **PipelineSafetyHook** (Protocol) | `runtime/pipeline/safety_hook.py` | `should_run()`, `record_fail_safe(code, message, stage)`, `pipeline_state()` | ETEDARunner에 주입 |
| **SafetyLayer** (구현체) | `ops/safety/layer.py` | `SafetyLayer(state_manager=..., notifier=..., kill_switch=..., safe_mode=...)` | PipelineSafetyHook 구현. `request_recovery(operator_approved)` |
| **SafetyStateManager** | `ops/safety/state.py` | `SafetyStateManager()`. `apply_anomaly`, `apply_fail_safe(code)`, `request_recovery(operator_approved)` | 상태: NORMAL/WARNING/FAIL/LOCKDOWN. 전이표: _TRANSITIONS |
| **Guard** | `ops/safety/guard.py` | `check_extract_safety`, `check_transform_safety`, `check_evaluate_safety`, `check_decide_safety`, `check_act_safety` | ETEDA 단계별 체크. blocked 시 record_fail_safe 연동 |
| **Codes** | `ops/safety/codes.py` | `FAIL_SAFE_TABLE`, `GUARDRAIL_TABLE`, `ANOMALY_TABLE`. `get_code_info`, `message_for` | ETEDA 단계별 코드 |
| **Runtime Risk** | `runtime/risk/` | calculators, gates (calculated_risk_gate, staged_risk_gate) | Phase 5 오케스트레이터·ETEDA Decide 연동 |

---

## 2. 상태 전이 (완전판)

| from \\ event | anomaly | fail_safe | guardrail | recovery |
|---------------|---------|-----------|-----------|----------|
| **NORMAL** | WARNING | FAIL | — | — |
| **WARNING** | WARNING | FAIL | WARNING | — |
| **FAIL** | — | FAIL(연속+1); 2회→LOCKDOWN | — | NORMAL |
| **LOCKDOWN** | — | — | — | NORMAL (operator_approved=True만) |

- **Lockdown 진입**: FAIL에서 `apply_fail_safe` 2회 연속 시 LOCKDOWN (LOCKDOWN_CONSECUTIVE_FAIL_THRESHOLD=2).
- **복구**: FAIL → NORMAL: `request_recovery()`. LOCKDOWN → NORMAL: `request_recovery(operator_approved=True)` 필요.

---

## 3. 테스트 경로

- `tests/ops/safety/` — state (전이), layer (should_run, record_fail_safe, request_recovery), guard, codes, notifier.

기본 실행: `pytest tests/ops/safety/ -v`

---

## 4. 운영 체크

Fail-Safe/Lockdown 복구·operator_approved 플로우: [Phase_07_Safety_Risk/FailSafe_Lockdown_운영_체크.md](../../../docs/tasks/phases/Phase_07_Safety_Risk/FailSafe_Lockdown_운영_체크.md) (§2.2)
