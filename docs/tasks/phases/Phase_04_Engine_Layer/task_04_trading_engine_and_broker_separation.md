# Phase 4 — Engine Layer: Trading Engine Implementation

## 목표

- 아키텍처 문서 수정에 따른 4대 엔진 구조 완성
- Broker Layer와의 명확한 분리 및 ExecutionIntent/Response Contract 구현

## 근거

- `docs/arch/00_Architecture.md` 수정 내용 반영
- 현재 Trading Engine이 누락되어 있음
- Broker Layer와의 책임 분리 필요

## 작업

- [ ] Trading Engine 구현 여부 재검토
  - [ ] 현재 Broker Layer로 충분한지 판단
  - [ ] 별도 Trading Engine이 필요하다면 BaseEngine 상속으로 구현
- [ ] ExecutionIntent/Response Contract 명세화
  - [ ] `src/runtime/execution/models/intent.py` 구조 검토
  - [ ] `src/runtime/execution/models/response.py` 구조 검토
- [ ] Broker Engine 인터페이스 구현 검증
  - [ ] `src/runtime/execution/interfaces/broker.py` 완성도 확인
  - [ ] LiveBroker/MockBroker/NoopBroker 패턴 구현 확인

## 완료 조건

- [ ] 4대 엔진(Strategy, Risk, Portfolio, Performance) 구조가 명확히 정의됨
- [ ] Broker Layer와의 ExecutionIntent/Response Contract가 표준화됨
- [ ] Engine Layer가 아키텍처 문서와 일치함
