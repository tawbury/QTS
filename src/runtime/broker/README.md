# Multi-Broker Integration (Phase 8) — 진입점 및 Wiring

Broker 실행 계층·어댑터(KIS)·생성 팩토리 경로 정리. **근거**: [docs/arch/08_Broker_Integration_Architecture.md](../../../docs/arch/08_Broker_Integration_Architecture.md)

---

## 1. 실행 계층 (Execution)

| 컴포넌트 | 경로 | 진입점 | 비고 |
|----------|------|--------|------|
| **BrokerEngine** (Protocol) | `runtime/execution/interfaces/broker.BrokerEngine` | `submit_intent(ExecutionIntent) -> ExecutionResponse` | ETEDARunner·TradingEngine·ExecutionRoute에서 사용 |
| **Broker 생성** | `runtime/execution/brokers.create_broker_for_execution(live_allowed, adapter)` | live_allowed·adapter 있으면 LiveBroker(adapter), 없으면 NoopBroker. **MockBroker는 반환하지 않음** (테스트 전용) |
| **LiveBroker** | `runtime/execution/brokers/live_broker.LiveBroker` | `LiveBroker(adapter, max_consecutive_failures=3)` | ConsecutiveFailureGuard 연동. failsafe 시 ExecutionResponse(accepted=False, broker="failsafe") |
| **NoopBroker / MockBroker** | `runtime/execution/brokers/` | NoopBroker: 항상 거절. MockBroker: **테스트 전용**, 프로덕션 경로에서 사용 금지 |

---

## 2. 어댑터·Auth (runtime/broker)

| 컴포넌트 | 경로 | 진입점 | 비고 |
|----------|------|--------|------|
| **Auth** | `runtime/broker/base.BrokerAdapter`, `runtime/broker/kis/adapter.KISBrokerAdapter` | `authenticate() -> AccessTokenPayload`. TokenCache 갱신 | 주문 API 없음 |
| **Order 어댑터** | `runtime/broker/adapters/base_adapter.BaseBrokerAdapter`, `runtime/broker/kis/order_adapter.KISOrderAdapter`, `runtime/broker/adapters/kiwoom_adapter.KiwoomOrderAdapter` | `place_order(OrderRequest)->OrderResponse`, `get_order`, `cancel_order`, `broker_id`. KISOrderClientProtocol / KiwoomOrderClientProtocol 주입 |
| **KIS 페이로드/매핑** | `runtime/broker/kis/payload_mapping` | `build_kis_order_payload(OrderRequest)`, `parse_kis_place_response`, `KIS_STATUS_TO_ORDER_STATUS`, `map_broker_error_to_safety` | 에러→Fail-Safe(FS040 등). 1001→FS040, 3005→FS041, timeout→FS042 |
| **키움 페이로드/매핑** | `runtime/broker/kiwoom/payload_mapping` | `build_kiwoom_order_payload(OrderRequest)`, `parse_kiwoom_place_response`, `KIWOOM_STATUS_TO_ORDER_STATUS`, `map_broker_error_to_safety` | 에러→Fail-Safe(FS040~FS042). KIWOOM_ERROR_TO_SAFETY |

---

## 3. ExecutionIntent ↔ OrderRequest 브릿지 (META-240523-03)

- **실행 계층**: ExecutionIntent / ExecutionResponse (Engine ↔ Broker Layer).
- **OrderAdapter**: OrderRequest / OrderResponse (API 계약). KISOrderAdapter, KiwoomOrderAdapter.
- **브릿지**: `runtime/execution/intent_to_order_bridge.py`
  - `intent_to_order_request()`, `order_response_to_execution_response()` — 공통 변환기.
  - `OrderAdapterToBrokerEngineAdapter`: OrderAdapter를 BrokerEngine.submit_intent 계약으로 감싸 LiveBroker에 주입.
- **실제 주문용 wiring 예시**:
  ```python
  from runtime.execution.intent_to_order_bridge import OrderAdapterToBrokerEngineAdapter
  from runtime.broker.adapters import get_broker, get_broker_for_config
  from runtime.execution.brokers import create_broker_for_execution

  order_adapter = get_broker("kis", broker=kis_client, cano="...", acnt_prdt_cd="01")
  bridge = OrderAdapterToBrokerEngineAdapter(order_adapter, broker_id="kis", dry_run=False)
  broker = create_broker_for_execution(live_allowed=True, adapter=bridge)
  ```

---

## 4. 테스트 경로

- **Mock 기본**: `pytest tests/runtime/broker/ -v -m "not real_broker"` — 실 브로커 호출 없음.
- **실 브로커 스모크 (opt-in)**: `@pytest.mark.real_broker`. `pytest -m real_broker` 또는 `QTS_RUN_REAL_BROKER=1`.
- **테스트 구조**: tests/runtime/broker/README.md, conftest(MockKISOrderClient), test_*_dry_run, test_*_payload_mapping, test_*_real_broker_smoke.

---

## 5. 실 주문/rollback 운영 체크

실거래·실 API 연동 시 스모크/검증·롤백 정책: [Phase_08_Broker_Integration/실_주문_rollback_운영_체크.md](../../../docs/tasks/phases/Phase_08_Broker_Integration/실_주문_rollback_운영_체크.md) (§2.2)
