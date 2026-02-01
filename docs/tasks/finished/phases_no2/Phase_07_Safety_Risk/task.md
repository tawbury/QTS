# Phase 7 — Safety & Risk Core (로드맵 기준 Task)

## 목표

- Risk 구성요소·Ops Safety Guard·Lockdown/Fail-Safe 상태 머신의 **완전판 정의 및 검증**
- Phase 10 Exit Criteria 충족 시 Roadmap 상태 ✅ 전환

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — Phase 7
- [Phase Exit Criteria](../../../tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md) §4.3
- 코드: `src/runtime/risk/`, `src/ops/safety/guard.py`
- 아키텍처: `docs/arch/sub/16_Micro_Risk_Loop_Architecture.md`, `docs/arch/sub/18_System_State_Promotion_Architecture.md`

---

## Roadmap Section 2 — Phase 7 업무

| 업무 | 상태 | 완료 시 |
|------|------|--------|
| Risk 구성요소(계산기/게이트/정책) | ✅ | 테스트·문서 정합 (tests/runtime/risk/, ops/safety/README.md) |
| Ops Safety Guard | ✅ | tests/ops/safety/ 55 passed, wiring·상태 전이 문서화 |
| Lockdown/Fail-Safe 상태 머신(완전판) | ✅ | state.py NORMAL/WARNING/FAIL/LOCKDOWN, _TRANSITIONS, apply_fail_safe(2회→LOCKDOWN), request_recovery(operator_approved). ops/safety/README.md §2 |

---

## Wiring 요약 (현행)

| 컴포넌트 | 진입점 | 비고 |
|----------|--------|------|
| PipelineSafetyHook (Protocol) | `runtime/pipeline/safety_hook.py` | `should_run()`, `record_fail_safe(code, message, stage)`, `pipeline_state()`. ETEDARunner에 주입 |
| SafetyLayer (구현체) | `ops/safety/layer.py` | PipelineSafetyHook 구현. kill_switch, safe_mode, SafetyStateManager, SafetyNotifier. `request_recovery(operator_approved)` |
| SafetyStateManager (상태 머신) | `ops/safety/state.py` | 상태: NORMAL / WARNING / FAIL / LOCKDOWN. 전이: anomaly→WARNING, fail_safe→FAIL, FAIL 2회 연속→LOCKDOWN, recovery→NORMAL(LOCKDOWN은 operator_approved=True 필요) |
| Guard (ETEDA 단계별 체크) | `ops/safety/guard.py` | `check_extract_safety`, `check_transform_safety` 등. SafetyResult(blocked=True면 record_fail_safe 연동) |
| Codes | `ops/safety/codes.py` | FAIL_SAFE_TABLE, GUARDRAIL_TABLE, ANOMALY_TABLE. ETEDA 단계별 코드. `get_code_info`, `message_for` |
| Runtime Risk | `runtime/risk/` | calculators (base, strategy_risk), gates (calculated_risk_gate, staged_risk_gate). Phase 5 오케스트레이터·ETEDA Decide 연동 |
| ETEDA 연동 | ETEDARunner(safety_hook=...) | run_once 시작 시 `should_run()`; Act 단계 Broker failsafe 시 `record_fail_safe("FS040", ...)` |

---

## 미결 사항

| 미결 항목 | 진행 단계 | 비고 |
|-----------|-----------|------|
| 상태 머신 “완전판” 정의 | ✅ 완료 | state.py: SafetyState, _TRANSITIONS, apply_fail_safe(2회→LOCKDOWN), request_recovery(operator_approved). ops/safety/README.md §2 |
| 부분 구현과 갭·검증 테스트 | ✅ 완료 | tests/ops/safety/ 55 passed. Lockdown·recovery(operator_approved) 시나리오 테스트 포함 |
| tests/ops/safety/ 인터페이스 정합 | ✅ 완료 | SafetyLayer·SafetyStateManager·guard 시그니처와 테스트 일치. CI 통과 |
| Fail-Safe/Lockdown 시나리오 문서화 | ✅ 완료 | [FailSafe_Lockdown_운영_체크.md](./FailSafe_Lockdown_운영_체크.md) — 복구 절차, operator_approved 플로우 |
| Safety 진입점·상태 전이 문서화 | ✅ 완료 | src/ops/safety/README.md, 본 task Wiring 요약 |
| Roadmap Phase 7 비고 해소 | ✅ 완료 | 상태 머신 완전판·문서·검증 반영. Exit Criteria §2.1·§2.2·§2.3 충족 |

---

## 작업 (체크리스트)

- [x] **상태 머신 완전판**
  - [x] Lockdown/Fail-Safe 상태 머신 “완전판” 정의(문서·상태 전이·입출력) — state.py, ops/safety/README.md §2
  - [x] 부분 구현과의 갭 정리 및 검증 테스트 — tests/ops/safety/ 55 passed
- [x] **테스트**
  - [x] `tests/ops/safety/` 현재 인터페이스와 일치·통과 (55 passed)
  - [x] Fail-Safe/Lockdown 시나리오 문서화 — [FailSafe_Lockdown_운영_체크.md](./FailSafe_Lockdown_운영_체크.md)
- [x] **문서**
  - [x] Safety 진입점·wiring·상태 전이 문서화 (src/ops/safety/README.md)
  - [x] Roadmap Phase 7 비고(“완전판 확인 필요”) 해소

---

## 완료 조건 (Exit Criteria)

- [x] 필수 테스트 통과 (§2.1) — `pytest tests/ops/safety/ -v`
- [x] 운영 체크(Fail-Safe/Lockdown) (§2.2) — [FailSafe_Lockdown_운영_체크.md](./FailSafe_Lockdown_운영_체크.md)
- [x] 문서 SSOT 반영 (§2.3) — 07_FailSafe_Architecture, ops/safety/README.md, 운영 체크 문서
