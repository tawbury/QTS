# Phase 8 — Multi-Broker Integration (로드맵 기준 Task)

## 목표

- Broker 어댑터 베이스/구현(KIS)의 **wiring·테스트·문서 정합**
- Phase 10 Exit Criteria 충족 시 Roadmap 상태 ✅ 전환

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — Phase 8
- [Phase Exit Criteria](../../../tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md) §2.2, §3
- 코드: `src/runtime/broker/`

---

## Roadmap Section 2 — Phase 8 업무

| 업무 | 상태 | 완료 시 |
|------|------|--------|
| Broker 어댑터 베이스/구현(KIS) | ✅ | 테스트(Mock 기본, real_broker opt-in)·문서 정합 (src/runtime/broker/README.md, tests/runtime/broker/README, 실_주문_rollback_운영_체크) |

---

## Wiring 요약 (현행)

| 컴포넌트 | 진입점 | 비고 |
|----------|--------|------|
| BrokerEngine (실행 계층) | `execution/interfaces/broker.BrokerEngine` | `submit_intent(ExecutionIntent) -> ExecutionResponse`. ETEDARunner·TradingEngine·ExecutionRoute에서 사용 |
| Broker 생성 | `execution/brokers.create_broker_for_execution(live_allowed, adapter)` | live_allowed·adapter 있으면 LiveBroker(adapter), 없으면 NoopBroker. MockBroker는 테스트 전용·반환 안 함 |
| LiveBroker | `LiveBroker(adapter, max_consecutive_failures=3)` | adapter는 `submit_intent(ExecutionIntent)->ExecutionResponse` 구현체. ConsecutiveFailureGuard 연동·failsafe 시 ExecutionResponse(accepted=False, broker="failsafe") |
| NoopBroker / MockBroker | 테스트·비실행 경로 | NoopBroker: 항상 거절. MockBroker: 테스트 전용 |
| Auth (Phase 2) | `runtime/broker/base.BrokerAdapter`, `kis/adapter.KISBrokerAdapter` | authenticate() -> AccessTokenPayload. TokenCache 갱신. 주문 API 없음 |
| Order 어댑터 | `runtime/broker/adapters/base_adapter.BaseBrokerAdapter`, `adapters/kis_adapter.KISOrderAdapter` | place_order(OrderRequest)->OrderResponse, get_order, cancel_order, broker_id. client(KISClient) 주입 |
| KIS 페이로드/매핑 | `runtime/broker/kis/payload_mapping` | build_kis_order_payload(OrderRequest), parse_kis_place_response, KIS_STATUS_TO_ORDER_STATUS. 에러→Fail-Safe(FS040 등) 문서화 |

---

## 미결 사항

| 미결 항목 | 진행 단계 | 비고 |
|-----------|-----------|------|
| Broker 어댑터 진입점·DI 경로 문서화 | ✅ 완료 | src/runtime/broker/README.md. ETEDARunner broker 주입, create_broker_for_execution 경로 명시 |
| ExecutionIntent↔OrderRequest 브릿지 | ✅ 완료 | 실행 계층 ExecutionIntent/ExecutionResponse. KISOrderAdapter OrderRequest/OrderResponse. broker/README.md §3 |
| KIS 페이로드/주문 상태/에러 매핑 문서·코드 일치 | ✅ 완료 | payload_mapping (1001→FS040 등). 08_Broker_Integration_Architecture·README §2 |
| tests/runtime/broker Mock·real_broker 분리 | ✅ 완료 | tests/runtime/broker/README: Mock 기본, @pytest.mark.real_broker opt-in. 45 passed (4 deselected) |
| 실 주문/rollback 운영 체크 문서화 | ✅ 완료 | [실_주문_rollback_운영_체크.md](./실_주문_rollback_운영_체크.md) — 스모크/검증·롤백 정책 |
| Roadmap Phase 8 비고 해소 | ✅ 완료 | wiring·테스트·운영 체크 반영. Exit Criteria §2.1·§2.2·§2.3 충족 |

---

## 작업 (체크리스트)

- [x] **어댑터·wiring**
  - [x] Broker 어댑터 진입점·의존성 주입 경로 문서화 (src/runtime/broker/README.md)
  - [x] KIS 페이로드/주문 상태/에러 매핑 문서·코드 일치 (payload_mapping, map_broker_error_to_safety)
- [x] **테스트**
  - [x] `tests/runtime/broker/` — Mock 기본, 실 환경은 `real_broker` 마커로 분리 (§2.2). 45 passed (not real_broker)
  - [x] Contract/주문 스키마 검증 테스트 포함 (test_kis_payload_mapping, test_broker_factory)
- [x] **문서**
  - [x] 실거래/실 API 연동 시 실 환경 스모크/검증 정책 문서화 — [실_주문_rollback_운영_체크.md](./실_주문_rollback_운영_체크.md)
  - [x] Roadmap Phase 8 비고 해소

---

## 완료 조건 (Exit Criteria)

- [x] 필수 테스트 통과 (§2.1) — `pytest tests/runtime/broker/ -v -m "not real_broker"`
- [x] 실 주문/rollback 운영 체크 문서화 (§2.2) — [실_주문_rollback_운영_체크.md](./실_주문_rollback_운영_체크.md)
- [x] 문서 SSOT 반영 (§2.3) — 08_Broker_Integration_Architecture, broker/README.md, tests/runtime/broker/README
