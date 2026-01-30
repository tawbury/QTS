# Phase 7 — Safety/Risk: Tests & Alerting

## 목표

- Fail-Safe/Guardrail/Anomaly 조건을 테스트 가능하게 만들고, 운영자 알림(최소 수준)을 정의한다.

## 근거

- `docs/arch/10_Testability_Architecture.md`
- `docs/arch/07_FailSafe_Architecture.md`

## 작업

- [ ] Safety Layer 테스트 시나리오 정의
  - [ ] 데이터 손상/브로커 오류/리스크 초과/시스템 자원 이슈
- [ ] 알림(Notifier) 최소 규격 정의
- [ ] 코드 품질 개선(필수)
  - [ ] 테스트 가능한 구조(순수 함수/의존성 주입)를 우선 적용

## 완료 조건

- [ ] 대표 Fail-Safe 조건이 자동 테스트로 재현된다.
