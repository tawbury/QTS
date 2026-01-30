# Phase 7 — Safety/Risk: Guardrail & Fail-Safe Codes

## 목표

- Fail-Safe/Guardrail/Warning 기준을 코드 레벨로 고정하고, 코드 테이블을 유지 가능한 형태로 만든다.

## 근거

- `docs/arch/07_FailSafe_Architecture.md`

## 작업

- [x] Fail-Safe 코드 테이블(예: FS001…)을 코드 자산으로 반영
- [x] 단계별 체크 포인트(Extract/Transform/Evaluate/Decide/Act)에서의 적용 위치 정의
- [x] 코드 품질 개선(필수)
  - [x] Guard/Fail-Safe 판단이 “산발적 if문”으로 퍼지지 않도록 집약

## 구현 요약

| 자산 | 위치 | 설명 |
|------|------|------|
| Fail-Safe/Guardrail/Anomaly 코드 테이블 | `src/ops/safety/codes.py` | `FAIL_SAFE_TABLE`, `GUARDRAIL_TABLE`, `ANOMALY_TABLE`, `codes_by_stage()`, `message_for()` |
| 단계별 Safety 체크 API | `src/ops/safety/guard.py` | `check_extract_safety`, `check_transform_safety`, `check_evaluate_safety`, `check_decide_safety`, `check_act_safety`, `SafetyResult` |
| 적용 위치 | `codes_by_stage()` | ETEDA 단계(Extract/Transform/Evaluate/Decide/Act/Performance)별 적용 코드 목록 |
| execution_guards 연동 | `src/ops/decision_pipeline/execution_stub/execution_guards.py` | Guard 코드(G_EXE_*) 및 메시지를 `ops.safety.message_for()`로 일관 관리 |

## 완료 조건

- [x] Fail-Safe 코드/조건/메시지가 일관된 방식으로 관리된다.
