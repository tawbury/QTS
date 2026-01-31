# Phase 8 — Broker Integration: Order Status & Error Mapping

## 목표

- 브로커 상태/오류 코드를 표준 상태로 매핑하고 Fail-Safe와 연계

## 근거

- `docs/arch/08_Broker_Integration_Architecture.md`
- `docs/arch/07_FailSafe_Architecture.md`

## 작업

- [x] OrderStatus 매핑 규칙 확정
  - [x] `payload_mapping.KIS_STATUS_TO_ORDER_STATUS` (Arch 5.4, 6.5) 단일 정의
- [x] 브로커 오류 코드 → Fail-Safe/Guardrail 트리거 규칙 정의
  - [x] `KIS_ERROR_TO_SAFETY`: 1001→FS040, 3005→FS041, timeout→FS042 (Arch 5.3, 8.1)
  - [x] `map_broker_error_to_safety(broker_code, raw)` 및 트리거 규칙 문서화 (caller가 record_fail_safe 호출)
- [x] 코드 품질 개선(필수)
  - [x] 매핑 로직 단일 모듈 집약: `src/runtime/broker/kis/payload_mapping.py` (status + error)

## 완료 조건

- [x] 상태/오류 매핑이 단일 규칙으로 유지된다.
