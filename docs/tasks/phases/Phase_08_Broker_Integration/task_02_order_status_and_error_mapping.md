# Phase 8 — Broker Integration: Order Status & Error Mapping

## 목표

- 브로커 상태/오류 코드를 표준 상태로 매핑하고 Fail-Safe와 연계

## 근거

- `docs/arch/08_Broker_Integration_Architecture.md`
- `docs/arch/07_FailSafe_Architecture.md`

## 작업

- [ ] OrderStatus 매핑 규칙 확정
- [ ] 브로커 오류 코드 → Fail-Safe/Guardrail 트리거 규칙 정의
- [ ] 코드 품질 개선(필수)
  - [ ] 매핑 로직이 코드 곳곳에 흩어지지 않도록 단일 모듈로 집약

## 완료 조건

- [ ] 상태/오류 매핑이 단일 규칙으로 유지된다.
