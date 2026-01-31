# 실 주문 / Rollback 운영 체크 (Phase 8 §2.2)

실거래·실 API 연동 시 스모크/검증·롤백 정책. **근거**: Phase 10 Exit Criteria §2.2, [docs/arch/08_Broker_Integration_Architecture.md](../../../arch/08_Broker_Integration_Architecture.md)

---

## 1. 실 환경 스모크/검증 정책

- **CI/기본 실행**: 실 브로커 호출 없음. `pytest tests/runtime/broker/ -v -m "not real_broker"` 로 Mock 기반 회귀 테스트만 실행.
- **실 브로커 스모크 (opt-in)**:
  - `@pytest.mark.real_broker` 로 표시. `pytest -m real_broker` 또는 `QTS_RUN_REAL_BROKER=1` 로만 실행.
  - **권장**: dry_run 또는 모의계좌 사용. 실계좌 사용 시 최소 수량·1회성 검증만 수행.
- **최소 시나리오**: Buy 1건, Sell 1건, Cancel 1건, Partial fill 조회. tests/runtime/broker/test_kis_real_broker_smoke.py 에 정의.

---

## 2. 롤백 정책

- **주문 접수 후 취소**: KISOrderAdapter `cancel_order(order_id)` 호출. 실거래 시 주문 접수 직후 검증용 취소는 운영 정책에 따라 수행.
- **Fail-Safe 연동**: 브로커 에러 시 `map_broker_error_to_safety` (payload_mapping) → FS040/FS041/FS042 등. 호출부(Guard/Act)에서 `record_fail_safe(safety_code, message, "Act")` 호출 → Safety 상태 전이(Phase 7).
- **연속 실패**: LiveBroker ConsecutiveFailureGuard 차단 시 추가 주문 차단(ExecutionResponse accepted=False, broker="failsafe"). 복구는 Phase 7 request_recovery 정책.

---

## 3. 영향 범위·문서

- **영향 범위**: 실 주문 실행은 Broker 계층·KIS API만 관여. Config/시트/엔진 결정은 별도. 롤백은 “미체결 주문 취소” 및 “이후 주문 차단(Fail-Safe)” 수준.
- **문서**: 08_Broker_Integration_Architecture, runtime/broker/README.md, tests/runtime/broker/README.md (Mock vs real_broker).
