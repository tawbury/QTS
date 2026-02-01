# Phase 8 — Broker Integration: Tests (Mock vs Real)

## 목표

- Mock 브로커/실 브로커 테스트 경계를 명확히 하고 회귀 테스트 기반을 만든다.

## 근거

- `docs/arch/10_Testability_Architecture.md`
- 코드:
  - `src/runtime/execution/brokers/mock_broker.py`

## 작업

- [x] Mock 브로커 사용 범위 확정
  - [x] 프로덕션 경로: create_broker_for_execution() 사용 → LiveBroker/NoopBroker만, MockBroker 미반환
- [x] 실 브로커 테스트 전략 정의
  - [x] 최소 시나리오(Buy/Sell/Cancel/Partial fill): README 및 test_kis_real_broker_smoke.py, @pytest.mark.real_broker
- [x] 코드 품질 개선(필수)
  - [x] 테스트: DummyKISBroker 제거, conftest.MockKISOrderClient 공용 픽스처로 통일 (예시 구현 의존 제거)

## 완료 조건

- [x] Mock 기반 회귀 테스트와 실 브로커 스모크 테스트가 마커/경로로 분리되어 있다.
