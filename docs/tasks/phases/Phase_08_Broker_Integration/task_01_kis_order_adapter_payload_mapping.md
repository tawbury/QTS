# Phase 8 — Broker Integration: KIS Order Adapter Payload Mapping

## 목표

- KIS 주문 요청 payload/응답 파싱 규칙을 아키텍처 명세에 맞게 자산화

## 근거

- `docs/arch/08_Broker_Integration_Architecture.md`
- 코드:
  - `src/runtime/broker/kis/order_adapter.py` (TODO 존재)

## 작업

- [ ] Request Normalization 규칙 구현
  - [ ] BUY/SELL/order_type/시장 코드 등 매핑 규칙 확정
- [ ] Response Normalization 규칙 구현
  - [ ] ExecutionResult로의 변환 규칙 고정
- [ ] 코드 품질 개선(필수)
  - [ ] `order_adapter.py`의 TODO/예시 호출(`place_order`, `get_order`)을 실제 메서드 계약으로 정리

## 완료 조건

- [ ] 주문 요청/응답 변환 규칙이 문서/코드/테스트에서 일치한다.
