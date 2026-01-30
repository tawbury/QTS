# Phase 5 — ETEDA Pipeline: ExecutionIntent Integration

## 목표

- ETEDA Pipeline의 Act 단계에서 ExecutionIntent/Response Contract 사용하도록 수정
- Broker Layer와의 통합 방식 명확화

## 근거

- `docs/arch/00_Architecture.md` Component Interaction 수정 내용 반영
- `src/runtime/pipeline/eteda_runner.py`의 _act() 메서드 개선 필요
- ExecutionIntent → BrokerEngine → ExecutionResponse 흐름 구현

## 작업

- [ ] ETEDA Runner Act 단계 수정
  - [ ] `_act()` 메서드에서 ExecutionIntent 생성 로직 구현
  - [ ] BrokerEngine.submit_intent() 호출 방식 확정
  - [ ] ExecutionResponse 처리 및 결과 반환
- [ ] Broker Layer 연동 강화
  - [ ] LiveBroker의 ConsecutiveFailureGuard 연동 확인
  - [ ] Fail-Safe 동작 방식 검증
- [ ] Pipeline Contract 명세화
  - [ ] Act 단계의 Input/Output Contract 정의
  - [ ] Error Handling 및 Retry 정책 확정

## 완료 조건

- [ ] ETEDA Pipeline이 ExecutionIntent/Response Contract를 따름
- [ ] Act 단계에서 Broker Layer와 정상적으로 통합됨
- [ ] Fail-Safe 기능이 파이프라인에 내장됨
