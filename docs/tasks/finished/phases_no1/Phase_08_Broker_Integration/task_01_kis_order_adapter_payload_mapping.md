# Phase 8 — Broker Integration: KIS Order Adapter Payload Mapping

## 목표

- KIS 주문 요청 payload/응답 파싱 규칙을 아키텍처 명세에 맞게 자산화

## 근거

- `docs/arch/08_Broker_Integration_Architecture.md`
- 코드:
  - `src/runtime/broker/adapters/kis_adapter.py`, `src/runtime/broker/kis/payload_mapping.py`

## 작업

- [x] Request Normalization 규칙 구현
  - [x] BUY/SELL/order_type/시장 코드 등 매핑 규칙 확정 (`payload_mapping.py`: SIDE_TO_KIS, ORDER_TYPE_TO_KIS, build_kis_order_payload)
- [x] Response Normalization 규칙 구현
  - [x] ExecutionResult(OrderResponse)로의 변환 규칙 고정 (`parse_kis_place_response`, `parse_kis_order_response`, `raw_to_order_response`)
- [x] 코드 품질 개선(필수)
  - [x] `adapters/kis_adapter.py`에서 KISOrderAdapter, place_order/get_order/cancel_order 정규화. payload_mapping은 kis/ 유지.

## 완료 조건

- [x] 주문 요청/응답 변환 규칙이 문서/코드/테스트에서 일치한다.
