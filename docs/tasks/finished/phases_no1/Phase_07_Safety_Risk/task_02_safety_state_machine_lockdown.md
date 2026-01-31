# Phase 7 — Safety/Risk: Safety State Machine & Lockdown

## 목표

- Safety 상태(NORMAL/WARNING/FAIL/LOCKDOWN)를 상태 머신으로 고정하고, Lockdown 절차를 명확히 한다.

## 근거

- `docs/arch/07_FailSafe_Architecture.md` §6

## 작업

- [x] Safety State Manager 구현 범위 확정
  - [x] 상태 전이 조건/이벤트 정의
- [x] Lockdown/Recovery 절차 정의
  - [x] 자동 복구 vs 운영자 개입 기준
- [x] 코드 품질 개선(필수)
  - [x] 상태 전이가 “암묵적 플래그”로 존재하지 않도록 명시화

## 구현 요약

| 자산 | 위치 | 설명 |
|------|------|------|
| Safety 상태 | `src/ops/safety/state.py` | `SafetyState`: NORMAL, WARNING, FAIL, LOCKDOWN (pipeline_state와 동일 값) |
| 상태 머신 | `SafetyStateManager` | `apply_anomaly`, `apply_fail_safe(code)`, `apply_guardrail`, `request_recovery(operator_approved)` |
| 전이 규칙 | `_TRANSITIONS` / `allowed_transitions()` | NORMAL→WARNING(anomaly), NORMAL/WARNING→FAIL(fail_safe), FAIL→NORMAL(recovery), LOCKDOWN→NORMAL(recovery, operator_approved만) |
| Lockdown 진입 | `apply_fail_safe` | FAIL 상태에서 Fail-Safe 2회 연속 시 자동 LOCKDOWN (`LOCKDOWN_CONSECUTIVE_FAIL_THRESHOLD=2`) |
| Lockdown 해제 | `request_recovery(operator_approved=True)` | LOCKDOWN → NORMAL은 운영자 승인 시에만; FAIL → NORMAL은 수동 복귀 시 |

### Lockdown/Recovery 절차 (문서·코드 일치)

- **진입**: Fail-Safe 발생 시 NORMAL/WARNING → FAIL; 이미 FAIL인 상태에서 Fail-Safe 재발 시 연속 횟수 증가, 2회 이상이면 LOCKDOWN.
- **해제**: FAIL → NORMAL: `request_recovery(operator_approved=True)` 또는 `False` 모두 허용(수동 복귀). LOCKDOWN → NORMAL: `request_recovery(operator_approved=True)` 만 허용.

## 완료 조건

- [x] Lockdown 진입/해제 조건이 문서/코드 모두에서 일치한다.
