# Phase 8 — Broker Integration: Tests (Mock vs Real)

## 목표

- Mock 브로커/실 브로커 테스트 경계를 명확히 하고 회귀 테스트 기반을 만든다.

## 근거

- `docs/arch/10_Testability_Architecture.md`
- 코드:
  - `src/runtime/execution/brokers/mock_broker.py`

## 작업

- [ ] Mock 브로커 사용 범위 확정
  - [ ] 프로덕션 경로에서 사용되지 않도록 안전장치(구성/모드) 정의
- [ ] 실 브로커 테스트 전략 정의
  - [ ] 최소 시나리오(Buy/Sell/Cancel/Partial fill)
- [ ] 코드 품질 개선(필수)
  - [ ] 테스트에서 “예시 구현” 호출에 의존하지 않도록 정리

## 완료 조건

- [ ] Mock 기반 회귀 테스트와 실 브로커 스모크 테스트가 분리되어 있다.
