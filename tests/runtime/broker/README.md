# Broker Tests: Mock vs Real (Phase 8)

## 목표

- Mock 브로커 회귀 테스트와 실 브로커 스모크 테스트 경계 명확화
- 프로덕션 경로에서 Mock 미사용 보장

## Mock 브로커 사용 범위

- **MockBroker** (`runtime.execution.brokers.MockBroker`): **테스트 전용**. 프로덕션/메인/실행 루프에서 사용 금지.
- **생성 규칙**: 프로덕션 경로는 `create_broker_for_execution(live_allowed, adapter)` 사용. 이 함수는 `LiveBroker` 또는 `NoopBroker`만 반환하며 `MockBroker`는 반환하지 않음.
- **구성/모드**: `ExecutionMode`(PAPER/LIVE) 및 `LiveGateDecision.live_allowed`에 따라 어댑터 주입 여부 결정; 브로커 선택은 위 팩토리로 일원화.

## 실 브로커 테스트 전략

- **기본**: CI/일반 `pytest` 실행 시 **Mock 기반 회귀 테스트만** 실행 (실 브로커 호출 없음).
- **실 브로커 스모크**: `@pytest.mark.real_broker`로 표시. opt-in 실행:
  - `pytest -m real_broker`
  - 또는 `QTS_RUN_REAL_BROKER=1` 등 환경으로 선택 실행 (conftest에서 스킵 해제 가능)

### 최소 시나리오 (실 브로커 스모크)

| 시나리오 | 설명 | 비고 |
|---------|------|------|
| Buy     | 매수 주문 1건 성공 | dry_run 또는 모의계좌 권장 |
| Sell    | 매도 주문 1건 성공 | 동일 |
| Cancel  | 주문 접수 후 취소 | 동일 |
| Partial fill | 부분 체결 조회 | get_order 응답 정규화 검증 |

실 브로커 테스트는 `tests/runtime/broker/test_kis_real_broker_smoke.py`에 정의하며, 기본적으로 스킵되거나 환경 변수/마커로만 실행.

## 테스트 구조

- **conftest.py**: `MockKISOrderClient` (KISOrderClientProtocol 계약 준수), fixture. 예시 구현이 아닌 계약 기반 테스트 더블.
- **test_*_dry_run.py**, **test_*_payload_mapping.py**: Mock/단위 회귀 테스트 (실 브로커 미호출).
- **test_*_real_broker_smoke.py**: `@pytest.mark.real_broker` 스모크 (opt-in).

## 완료 조건

- Mock 기반 회귀 테스트와 실 브로커 스모크 테스트가 마커/경로로 분리되어 있음.
- 프로덕션 경로는 `create_broker_for_execution()` 사용으로 Mock 브로커가 선택되지 않음.
