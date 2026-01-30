# Phase 4 — Engine Layer: Trading Engine Implementation

## 목표

- 아키텍처 문서 수정에 따른 4대 엔진 구조 완성
- Broker Layer와의 명확한 분리 및 ExecutionIntent/Response Contract 구현

## 근거

- `docs/arch/00_Architecture.md` 수정 내용 반영
- 현재 Trading Engine이 누락되어 있음
- Broker Layer와의 책임 분리 필요

## 작업

- [x] Trading Engine 구현 여부 재검토
  - [x] 현재 Broker Layer로 충분한지 판단
  - [x] 별도 Trading Engine이 필요하다면 BaseEngine 상속으로 구현
- [x] ExecutionIntent/Response Contract 명세화
  - [x] `src/runtime/execution/models/intent.py` 구조 검토
  - [x] `src/runtime/execution/models/response.py` 구조 검토
- [x] Broker Engine 인터페이스 구현 검증
  - [x] `src/runtime/execution/interfaces/broker.py` 완성도 확인
  - [x] LiveBroker/MockBroker/NoopBroker 패턴 구현 확인

## 완료 조건

- [x] 4대 엔진(Strategy, Risk, Portfolio, Performance) 구조가 명확히 정의됨
- [x] Broker Layer와의 ExecutionIntent/Response Contract가 표준화됨
- [x] Engine Layer가 아키텍처 문서와 일치함

## 구현 정리

- **Trading Engine**: `src/runtime/engines/trading_engine.py` 추가. BaseEngine 상속, BrokerEngine 주입, `execute(data)` — operation `submit_intent` 시 ExecutionIntent 전달 → BrokerEngine.submit_intent → ExecutionResponse를 표준 출력(success, data, execution_time)으로 반환. Engine Layer와 Broker Layer 분리 유지.
- **ExecutionIntent/Response Contract**: `intent.py`/`response.py` 상단에 Contract 문서(04_Data_Contract_Spec, 02_Engine_Core §7) 참조 및 필수 필드 명시.
- **LiveBroker**: `intent.id` → `intent.intent_id` 수정(버그 픽스).
- **Broker 인터페이스**: BrokerEngine.submit_intent(intent) → ExecutionResponse 유지. MockBroker(quantity>0 수용), NoopBroker(항상 거부), LiveBroker(adapter+guard) 구현 검증.
- **테스트**: `tests/engines/test_trading_engine.py` — Mock/Noop 주입, submit_intent 계약 검증.
