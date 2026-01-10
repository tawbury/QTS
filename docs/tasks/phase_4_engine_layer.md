# Phase 4 Tasks - Engine Layer

**상태: ⚪ 미정리**

## 개요
Engine Layer는 QTS의 "두뇌(BRAIN)"에 해당하는 핵심 계층입니다. ScalpEngine/SwingEngine 구조와 Config → Engine 입력 계약, Strategy 실행 책임 경계가 정리되지 않은 상태입니다.

## 미구현 태스크 목록

### 4.1 Engine Architecture Design
- [ ] ScalpEngine 상세 설계
  - [ ] 단기·고회전 매매 로직 구조
  - [ ] 기술적 지표 기반 신호 생성 체계
  - [ ] 시간 기반 청산 로직 설계
  - [ ] 단건 손실 제어 메커니즘
- [ ] SwingEngine 상세 설계
  - [ ] 중장기·저회전 매매 로직 구조
  - [ ] 펀더멘턀/밸류에이션 기반 분석 체계
  - [ ] 시장/섹터/종목 필터링 로직
  - [ ] 포트폴리오 레벨 리스크 모니터링

### 4.2 Core Engine Integration
- [ ] Trading Engine 재설계
  - [ ] ScalpEngine/SwingEngine 신호 수신 체계
  - [ ] 전략별 주문 실행 로직
  - [ ] 브로커 API 연동 인터페이스
- [ ] Risk Engine 설계
  - [ ] 전략별 리스크 평가 체계
  - [ ] 포지션 노출도 계산 로직
  - [ ] Kill Switch 연동 방식
- [ ] Portfolio Engine 설계
  - [ ] 전략별 포트폴리오 관리 로직
  - [ ] 수량/비중 조정 알고리즘
- [ ] Performance Engine 설계
  - [ ] 전략별 성과 분석 체계
  - [ ] 실시간 손익 계산 로직

### 4.3 Data Contract & Interface
- [ ] Config → Engine 입력 계약 설계
  - [ ] Unified Config 전달 체계
  - [ ] Config_Local 보호 규칙 적용
  - [ ] 전략별 Config 분리 처리

#### Config → Engine Input Contract 명세
- 모든 엔진은 오직 Unified Config를 통해서만 설정을 수신한다.
- Config 해석 로직은 개별 엔진에 구현되지 않으며, TASK_431_ConfigToEngine_InputContract_Design에 정의된 규칙을 따른다.
- [ ] Engine 간 통신 인터페이스 설계
  - [ ] Strategy → Risk 신호 전달
  - [ ] Risk → Trading 승인/거부 체계
  - [ ] Portfolio → Trading 수량 조정
- [ ] Engine → Pipeline 출력 계약 설계

### 4.4 Strategy Execution Framework
- [ ] Strategy 실행 책임 경계 확정
- [ ] 다중 전략 동시 실행 체계 설계
- [ ] 전략 간 충돌 처리 로직
- [ ] Strategy Template 표준화

#### Strategy 실행 책임 경계 명세
- ScalpEngine과 SwingEngine은 오직 의사결정(신호 생성)만 책임진다.
- 전략 엔진은 절대 주문을 실행하지 않으며, 실행 권한은 ETEDA Act 단계를 통한 Trading Engine에만 존재한다.

### 4.5 Engine Testing Framework
- [ ] 단위 테스트 프레임워크 설계
- [ ] Engine 간 통합 테스트 케이스
- [ ] Mock Data 기반 테스트 환경
- [ ] 성능 테스트 기준 마련

## 다음 Phase 연결 포인트
- **Execution Pipeline (ETEDA)**와의 연동 필요 (Phase 5)
- **Safety & Risk Core**와의 책임 경계 확정 (Phase 7)
- **Multi-Broker Integration**과의 연동 방식 결정 (Phase 8)

## 선행 조건
- Phase 3 Local Config 구현 완료
- Phase 1 Schema 매핑 안정화

## 비고
- **가장 중요한 미정리 영역**
- 다른 모든 Phase의 핵심 의존 대상
- 설계 완료 후 구현 복잡도 높음
