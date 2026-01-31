# Phase 5 — ETEDA Pipeline: ExecutionIntent Integration

## 목표

- ETEDA Pipeline의 Act 단계에서 ExecutionIntent/Response Contract 사용하도록 수정
- Broker Layer와의 통합 방식 명확화

## 근거

- `docs/arch/00_Architecture.md` Component Interaction 수정 내용 반영
- `src/runtime/pipeline/eteda_runner.py`의 _act() 메서드 개선 필요
- ExecutionIntent → BrokerEngine → ExecutionResponse 흐름 구현

## 작업

- [x] ETEDA Runner Act 단계 수정
  - [x] `_act()` 메서드에서 ExecutionIntent 생성 로직 구현
  - [x] BrokerEngine.submit_intent() 호출 방식 확정
  - [x] ExecutionResponse 처리 및 결과 반환
- [x] Broker Layer 연동 강화
  - [x] LiveBroker의 ConsecutiveFailureGuard 연동 확인
  - [x] Fail-Safe 동작 방식 검증
- [x] Pipeline Contract 명세화
  - [x] Act 단계의 Input/Output Contract 정의
  - [x] Error Handling 및 Retry 정책 확정

## 완료 조건

- [x] ETEDA Pipeline이 ExecutionIntent/Response Contract를 따름
- [x] Act 단계에서 Broker Layer와 정상적으로 통합됨
- [x] Fail-Safe 기능이 파이프라인에 내장됨

## 구현 요약

- **ETEDARunner**: `broker: Optional[BrokerEngine] = None` 주입. broker 주입 시 _act에서 decision → ExecutionIntent(intent_id, symbol, side, quantity, intent_type=MARKET) 생성 후 `broker.submit_intent(intent)` 호출, ExecutionResponse를 dict(status, intent_id, accepted, broker, message, timestamp, mode)로 반환. submit_intent 예외 시 status=error 반환.
- **LiveBroker**: ConsecutiveFailureGuard 연동 유지 — 연속 실패 시 accepted=False, broker="failsafe" 반환. ETEDA는 해당 결과를 act_result로 그대로 전달하여 Fail-Safe 내장.
- **Act I/O Contract**: `docs/tasks/phases/Phase_05_ETEDA_Pipeline/act_io_contract.md` — Act Input(decision), ExecutionIntent 매핑, Act Output(ExecutionResponse as dict), Error Handling, Retry 정책(Act 단계 자동 재시도 없음, Broker/Adapter 내부 재시도 위임).
