# Phase 5 Tasks - Execution Pipeline (ETEDA)

**상태: ⚪ 미정리**

## 개요
Execution Pipeline은 QTS의 모든 매매 프로세스를 통제하는 핵심 파이프라인입니다. ETEDA(Extract → Transform → Evaluate → Decide → Act) 흐름, Trigger/Schedule, Data Flow 연결이 정리되지 않은 상태입니다.

## 미구현 태스크 목록

### 5.1 ETEDA Pipeline Core Design
- [ ] Extract 단계 설계
  - [ ] 데이터 소스 추상화 계층
  - [ ] 실시간 데이터 수집 체계
  - [ ] 데이터 품질 검증 로직
- [ ] Transform 단계 설계
  - [ ] 데이터 정규화 처리
  - [ ] Schema 기반 데이터 변환
  - [ ] Engine 입력 포맷 변환
- [ ] Evaluate 단계 설계
  - [ ] ScalpEngine/SwingEngine 실행 체계
  - [ ] Risk Engine 평가 흐름
  - [ ] Portfolio Engine 계산 통합
- [ ] Decide 단계 설계
  - [ ] 최종 의사결정 로직
  - [ ] Safety Layer 연동 체계
  - [ ] 실행/보류/중단 결정 메커니즘
- [ ] Act 단계 설계
  - [ ] Trading Engine 실행 통제
  - [ ] 브로커 호출 관리
  - [ ] 결과 처리 및 피드백 루프

### 5.2 Pipeline Orchestration
- [ ] Pipeline 스케줄러 설계
  - [ ] 실행 주기 관리 (Config 기반)
  - [ ] 실시간/배치 모드 전환
  - [ ] 우선순위 기반 실행 큐
- [ ] Trigger 시스템 설계
  - [ ] 시간 기반 트리거
  - [ ] 이벤트 기반 트리거
  - [ ] 수동 실행 인터페이스
- [ ] Pipeline 상태 관리
  - [ ] 실행 상태 추적
  - [ ] 실패 처리 및 재시도
  - [ ] 병렬 실행 제어

#### Trigger/Schedule 소유권 명세
- ETEDA는 자체 스케줄링을 수행하지 않는다.
- ETEDA 실행은 Ops Layer(Event Scheduler)에 의해 외부에서 트리거된다.
- 수동 및 자동 트리거 모두 허용되지만, 항상 외부에서 발생한다.

### 5.3 Data Flow Integration
- [ ] Engine Layer 연동 설계
  - [ ] Engine 입력 데이터 준비
  - [ ] Engine 출력 데이터 수집
  - [ ] Engine 간 데이터 전달 체계
- [ ] Config 연동 설계
  - [ ] Pipeline 설정 관리
  - [ ] 동적 Config 변경 반영
  - [ ] Config 충돌 처리
- [ ] Data Layer 연동 설계
  - [ ] 실시간 데이터 읽기
  - [ ] 결과 데이터 쓰기
  - [ ] T_Ledger 자동 갱신

#### Data Flow 명세
- Engine 간 통신 및 Engine-to-Pipeline 출력은 다음을 통해 처리된다:
  - TASK_432_EngineToEngine_Communication_Interface_Design
  - TASK_433_EngineToPipeline_OutputContract_Design
- ETEDA는 실행 순서를 조정하지만, 인터페이스 포맷을 정의하지는 않는다.

### 5.4 Pipeline Monitoring & Control
- [ ] Pipeline 실행 모니터링
  - [ ] 단계별 실행 시간 측정
  - [ ] 병목 지점 감지
  - [ ] 실시간 상태 대시보드
- [ ] Pipeline 제어 인터페이스
  - [ ] 일시 중지/재개 기능
  - [ ] 단계별 건너뛰기 기능
  - [ ] 비상 정지 기능
- [ ] Pipeline 로깅 시스템
  - [ ] 상세 실행 로그
  - [ ] 에러 추적 로그
  - [ ] 성능 분석 로그

### 5.5 Pipeline Testing & Validation
- [ ] Pipeline 단위 테스트
  - [ ] 각 단계별 테스트 케이스
  - [ ] Mock Engine 기반 테스트
  - [ ] 데이터 흐름 검증
- [ ] Pipeline 통합 테스트
  - [ ] 전체 흐름 테스트
  - [ ] 엔진 연동 테스트
  - [ ] 장애 상황 시뮬레이션
- [ ] Pipeline 성능 테스트
  - [ ] 처리량 테스트
  - [ ] 지연 시간 테스트
  - [ ] 동시 실행 테스트

## 다음 Phase 연결 포인트
- **Engine Layer** 구현 완료 필수 (Phase 4)
- **Safety & Risk Core**와의 연동 필요 (Phase 7)
- **Dashboard/Visualization**에 상태 전달 (Phase 6)

## 선행 조건
- Phase 4 Engine Layer 설계 완료
- Phase 3 Config Architecture 안정화

## 비고
- **ETEDA 원칙 준수가 핵심**
- 모든 엔진을 통제하는 상위 레이어
- 실패 처리 및 회복 메커니즘 중요
