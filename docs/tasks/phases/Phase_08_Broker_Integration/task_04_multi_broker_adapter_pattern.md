# Phase 8 — Broker Integration: Multi-Broker Adapter Pattern

## 목표

- Multi-Broker 확장 가능한 Adapter Pattern 구현
- Broker Engine Interface 표준화 완성

## 근거

- 현재 KIS(한국투자증권) 어댑터만 있고 확장성 구조 부족
- Broker Adapter 패턴이 제대로 구현되지 않음
- 아키텍처 문서의 Multi-Broker 확장 원칙 구현 필요

## 작업

- [ ] Broker Adapter Pattern 설계
  - [ ] `src/runtime/broker/adapters/base_adapter.py` 구현
  - [ ] 표준화된 Broker Interface 정의
  - [ ] Adapter 등록 및 선택 메커니즘 구현
- [ ] Kiwoom Broker Adapter 구현
  - [ ] `src/runtime/broker/adapters/kiwoom_adapter.py` 구현
  - [ ] KIS Adapter와의 호환성 확보
- [ ] Multi-Broker 지원 강화
  - [ ] Broker 선택 및 전환 로직 구현
  - [ ] Broker별 Fail-Safe 정책 적용
  - [ ] Load Balancing 및 Fallback 전략
- [ ] Broker Configuration Management
  - [ ] Config 시트 기반 Broker 설정 관리
  - [ ] 동적 Broker 전환 기능

## 완료 조건

- [ ] Multi-Broker Adapter Pattern이 구현됨
- [ ] KIS, Kiwoom Broker가 모두 지원됨
- [ ] Broker 확장이 용이한 구조가 확보됨
