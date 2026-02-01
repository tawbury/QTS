# app/execution/clients/broker — Multi-Broker Integration

Broker 실행 계층·어댑터(KIS/Kiwoom)·생성 팩토리 경로 정리. **근거**: [08_Broker_Integration_Architecture.md](../../../../../docs/arch/08_Broker_Integration_Architecture.md)

---

## 1. 실행 계층 (Execution)

| 컴포넌트 | 경로 | 진입점 | 비고 |
|----------|------|--------|------|
| **BrokerEngine** (Protocol) | `app/execution/interfaces/broker.BrokerEngine` | `submit_intent(ExecutionIntent) -> ExecutionResponse` | ETEDARunner·TradingEngine·ExecutionRoute에서 사용 |
| **Broker 생성** | `app/execution/brokers.create_broker_for_execution(live_allowed, adapter)` | live_allowed·adapter 있으면 LiveBroker(adapter), 없으면 NoopBroker | **MockBroker는 테스트 전용** |
| **LiveBroker** | `app/execution/brokers/live_broker.LiveBroker` | `LiveBroker(adapter, max_consecutive_failures=3)` | ConsecutiveFailureGuard 연동 |
| **NoopBroker / MockBroker** | `app/execution/brokers/` | NoopBroker: 항상 거절. MockBroker: 테스트 전용 | 프로덕션에서 사용 금지 |

---

## 2. 어댑터·클라이언트 (app/execution/clients/broker)

| 컴포넌트 | 경로 | 진입점 | 비고 |
|----------|------|--------|------|
| **Auth** | `app/execution/clients/broker/base`, `app/execution/clients/broker/kis/adapter` | `authenticate() -> AccessTokenPayload` | TokenCache 갱신 |
| **Order 어댑터** | `app/execution/clients/broker/adapters/` (KISOrderAdapter, KiwoomOrderAdapter) | `place_order(OrderRequest)->OrderResponse` | client(KISClient/KiwoomClient) 주입 |
| **KIS 페이로드/매핑** | `app/execution/clients/broker/kis/payload_mapping` | `build_kis_order_payload`, `parse_kis_place_response`, `map_broker_error_to_safety` | 에러→Fail-Safe(FS040 등) |
| **키움 페이로드/매핑** | `app/execution/clients/broker/kiwoom/payload_mapping` | `build_kiwoom_order_payload`, `parse_kiwoom_place_response` | KIWOOM_ERROR_TO_SAFETY |

---

## 3. ExecutionIntent ↔ OrderRequest 브릿지

- **브릿지**: `app/execution/intent_to_order_bridge.py`
  - `intent_to_order_request()`, `order_response_to_execution_response()`
  - `OrderAdapterToBrokerEngineAdapter`: OrderAdapter를 BrokerEngine.submit_intent 계약으로 감싸 LiveBroker에 주입
- **wiring 예시**:
  ```python
  from app.execution.intent_to_order_bridge import OrderAdapterToBrokerEngineAdapter
  from app.execution.clients.broker.adapters import get_broker, get_broker_for_config
  from app.execution.brokers import create_broker_for_execution

  order_adapter = get_broker("kis", client=kis_client, acnt_no="...", acnt_prdt_cd="01")
  bridge = OrderAdapterToBrokerEngineAdapter(order_adapter, broker_id="kis", dry_run=False)
  broker = create_broker_for_execution(live_allowed=True, adapter=bridge)
  ```

---

## 4. 테스트 경로

- **Mock 기본**: `pytest tests/runtime/broker/ -v -m "not real_broker"`
- **실 브로커 스모크 (opt-in)**: `@pytest.mark.real_broker`, `QTS_RUN_REAL_BROKER=1`
- **테스트 구조**: `tests/runtime/broker/README.md`

---

## 5. 실 주문/rollback 운영 체크

실거래·실 API 연동 시 스모크/검증·롤백 정책: `docs/tasks/phases/Phase_08_Broker_Integration/실_주문_rollback_운영_체크.md`
