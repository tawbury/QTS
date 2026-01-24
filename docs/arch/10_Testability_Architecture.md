아래는 **10번 문서: QTS_Testability_Architecture.md**  
**완성본(v1.0.0)** 이다.

이 문서는 QTS 전체 시스템의 **신뢰성·안전성·확장성**을 지속적으로 확보하기 위한  
정식 테스트 아키텍처이며,  
모든 계층(데이터·엔진·파이프라인·브로커·UI·Ops·Safety)에 걸쳐  
**테스트 가능성(Testability)** 을 체계적으로 보장하는 기준 문서이다.

---

# ============================================================

# QTS Testability Architecture

# ============================================================

Version: v1.0.0  
Status: Architecture Specification (Final)  
Author: 타우  
Last Updated: 2025-12-12

문서 목적:  
QTS 자동매매 시스템의 모든 구성 요소가  
정확하게 동작하고, 장애가 발생해도 빠르게 원인을 파악하고 재현·검증할 수 있도록  
체계적인 Testability 구조를 제공한다.

본 문서는 다음을 보장한다.

- Engine/ETEDA/Broker/Contract/Performance/UI/Automation의 전 계층 테스트 기준
    
- 재현성 있는 테스트 데이터·Mock 구조
    
- 자동 회귀 테스트 체계
    
- Fail-Safe 테스트 환경
    
- 전체 End-to-End 테스트 실행 절차
    

---

# **1. Overview**

## **1.1 목적**

QTS Testability Architecture의 목표:

1. 모든 오류를 빠르게 발견하고 재현 가능하게 만든다.
    
2. 버전 업데이트 시 시스템 전체 일관성을 보장한다.
    
3. 자동매매 시스템의 안정성을 테스트 기반으로 확보한다.
    
4. Mock 기반으로 실계좌 없이 대부분의 기능을 테스트할 수 있게 한다.
    
5. 자동 회귀 테스트(Regression)를 수행하여 버전 증가 시 위험을 최소화한다.
    

---

## **1.2 범위**

포함:

- Unit Test
    
- Engine Test
    
- Contract Test
    
- Pipeline Integration Test
    
- Broker Integration Test
    
- Safety Layer Test
    
- UI Rendering Test
    
- Ops/Automation Test
    
- End-to-End Scenario Test
    
- Regression Test Architecture
    

---

## **1.3 테스트 계층(Test Layers)**

### Layer 1 — Unit Test

단일 모듈·함수(계산 모듈, 파서 등)를 검증.

### Layer 2 — Engine Test

Strategy/Risk/Portfolio/Performance 엔진의 입력/출력 검증.

### Layer 3 — Contract Test

Raw/Calc/Engine I/O/UI Contract 구조 검증.

### Layer 4 — ETEDA Pipeline Integration Test

5단계를 순차적으로 결합하여 테스트.

### Layer 5 — Broker Integration Test

Mock Broker 및 실 브로커 환경에서 주문 흐름 테스트.

### Layer 6 — Safety Layer Test

Fail-Safe/Guardrail/Anomaly 조건 테스트.

### Layer 7 — UI Rendering Test

UI Contract 기반의 표시 검증.

### Layer 8 — Ops/Automation Test

Auto-Check/Auto-Sync/Auto-Report/Scheduler 테스트.

### Layer 9 — End-to-End Test

Strategy → ETEDA → Broker → Ledger → UI까지 전 과정 테스트.

---

## **1.4 QTS Testability 핵심 철학**

1. **모든 기능은 테스트할 수 있어야 한다.**
    
2. **Mock 가능해야 한다.** (브로커·데이터·엔진 모두 mock 가능)
    
3. **테스트는 자동화되어야 한다.**
    
4. **테스트 실패 시 원인을 즉시 파악할 수 있어야 한다.**
    
5. **회귀 테스트는 필수이다.**
    

---

## **1.5 Testing Framework 구성 요소**

- pytest 기반 테스트 실행기
    
- Mock Broker Layer
    
- Test Contracts
    
- Test Data Fixtures
    
- Regression Suite Runner
    
- Test Reporter(HTML/JSON 보고서 생성)
    

---

# **2. Unit Test Architecture**

## **2.1 테스트 대상**

- Exposure 계산 함수
    
- PnL 계산 함수
    
- Risk 계산 함수
    
- JSON/Sheets 파서
    
- 변환 규칙(전처리 함수)
    

---

## **2.2 Unit Test 기준**

- 입력 변화에 따른 출력 예측 가능성
    
- NaN/Inf 발생 테스트
    
- Zero/Negative/Boundary Value Test
    
- Exception 발생 시 동작 테스트
    

---

## **2.3 Mocking 전략**

- Mock Market Price
    
- Mock RawDataContract
    
- Mock Strategy Output
    
- Mock ExecutionResult
    

---

## **2.4 Unit Test Fixtures**

테스트 데이터를 버전 관리하여 Fixture로 저장:

```
fixtures/
  raw_contract_sample.json
  calc_contract_sample.json
  strategy_output_sample.json
  execution_result_sample.json
```

---

## **2.5 Unit Test Coverage 목표**

- 최소 80%
    
- 계산 모듈은 95% 이상
    

---

# **3. Data Layer Test Architecture**

## **3.1 RawDataContract Validation Test**

- 필수 필드 테스트
    
- 타입 테스트
    
- 누락·빈 값 테스트
    

---

## **3.2 CalcDataContract 계산 검증**

- Exposure / PnL / Weight 계산
    
- Portfolio 계산 결과 비교
    
- CalcDataContract Validation
    

---

## **3.3 Symbol/Account Exposure 계산 테스트**

- 종목별 노출
    
- 계좌 전체 노출
    
- Risk Limit 경계값 테스트
    

---

## **3.4 T_Ledger 기록 테스트**

- ExecutionResult → T_Ledger 매핑
    
- Partial Fill 처리 검증
    
- Timestamp 정합성
    

---

## **3.5 Dividend DB 테스트**

- Local/Git DB 로딩
    
- 스키마 정합성 검사
    
- PayDate 처리 테스트
    

---

## **3.6 Schema Version Test**

- Version mismatch → Fail 처리
    
- Schema 변경 후 재빌드 테스트
    

---

# **4. Engine Layer Test Architecture**

## **4.1 Strategy Engine Test**

- Mock RawData → StrategyDecision
    
- signal 충돌 테스트
    
- signal confidence 검증
    

---

## **4.2 Risk Engine Test**

- approved / rejected 정상 동작
    
- 계좌 비중·손익·리스크 경계 테스트
    
- guardrail 조건 테스트
    

---

## **4.3 Portfolio Engine Test**

- final quantity 계산
    
- zero/negative qty 테스트
    
- PortfolioDecision 정합성
    

---

## **4.4 Trading Engine Test**

Broker 연동 없이 논리 레벨 검증:

- 구매 수량 계산
    
- 가격 결정 로직
    
- OrderDecision 생성
    

---

## **4.5 Performance Engine Test**

- PnL/MDD/CAGR 계산
    
- 배당 처리 테스트
    
- 급변 상황 Stress Test
    

---

## **4.6 Engine I/O Contract Test**

전 엔진 출력 Contract 구조 검증.

---

# **5. ETEDA Pipeline Test Architecture**

## **5.1 Step-by-Step 테스트**

각 단계를 단독으로 테스트:

- Extract Test
    
- Transform Test
    
- Evaluate Test
    
- Decide Test
    
- Act Test
    

---

## **5.2 Multi-Cycle Pipeline Test**

- N회(예: 1000 cycles) 반복 테스트
    
- Memory Leak Test
    
- Cycle timing consistency
    

---

## **5.3 ETEDA Cycle Timing Test**

Cycle Duration이 threshold를 넘어가는지 검사.

---

## **5.4 ETEDA Error Handling Test**

의도적으로 오류 주입:

- NaN 발생
    
- Price missing
    
- Position mismatch
    
- Broker failure mock
    

이 때 Fail-Safe 정상 작동 여부 확인.

---

## **5.5 Pipeline Recovery Test**

Fail 후:

- Resume
    
- Restart
    
- Safe Mode
    

테스트.

---

# **6. Broker Integration Test Architecture**

## **6.1 Mock Broker Interface Test**

Mock 기반:

- Buy
    
- Sell
    
- Partial Fill
    
- Cancel
    
- Timeout
    

을 재현하여 테스트.

---

## **6.2 주문 시나리오 테스트**

실제 전략 시나리오 기반으로 주문 흐름 검증.

---

## **6.3 Broker Error Code Mapping Test**

브로커 오류 → FS040~FS049 정확히 매핑 여부 확인.

---

## **6.4 ExecutionResult 정규화 테스트**

브로커별 응답을 ExecutionResult Contract로 변환 테스트.

---

## **6.5 Rate Limit/Timeout 테스트**

지연 발생 → Fail-Safe 적절히 작동 여부 테스트.

---

## **6.6 Multi-Broker Compatibility Test**

각 Broker Adapter가 동일한 인터페이스로 작동하는지 테스트.

---

# **7. Safety Layer Test Architecture**

## **7.1 Fail-Safe Trigger Test**

FS001~FS100 조건별 트리거 테스트.

---

## **7.2 Guardrail Trigger Test**

경계값 초과 → Guardrail 코드 생성 여부.

---

## **7.3 Anomaly Detection Test**

가격·PnL 급변 등 이상 패턴 주입하여 테스트.

---

## **7.4 Safety State Machine Test**

```
NORMAL → WARNING → FAIL → LOCKDOWN
```

전이가 정확히 작동하는지 검증.

---

## **7.5 Fail-Safe → Lockdown Transition Test**

연속 Fail-Safe 발생 시 Lockdown으로 넘어가는지 테스트.

---

## **7.6 Safety Layer End-to-End Test**

ETEDA + Safety Layer 통합 테스트 수행.

---

# **8. UI Layer Test Architecture**

## **8.1 UI Contract Test**

전체 필드 초기화/누락/타입 검증.

---

## **8.2 Rendering Logic Test**

UI가 Contract 기반으로 정확히 표시되는지 검증.

---

## **8.3 UI Freeze 조건 테스트**

Fail-Safe·Lockdown 상태에서 UI 업데이트 차단 확인.

---

## **8.4 Pipeline State UI 반영 테스트**

pipeline_state 표시 정확성 검증.

---

## **8.5 Performance Rendering Test**

Daily PnL Curve, MDD 등 그래프 데이터 검증.

---

## **8.6 R_Dash Layout Integrity Test**

- 셀 변동 없음
    
- 숨김/필터 문제 없음
    
- Zero Formula 유지
    

---

# **9. Ops & Automation Layer Test Architecture**

## **9.1 Auto-Check Engine Test**

- Schema mismatch → Warning/Fail
    
- Broker Heartbeat Fail 테스트
    

---

## **9.2 Auto-Sync Test**

- Position/Ledger 불일치 해결 여부
    
- Dividend DB Git Sync 검증
    

---

## **9.3 Auto-Backup Test**

- JSON Snapshot 정상 생성
    
- Backup 파일 구조 체크
    

---

## **9.4 Auto-Report Test**

- Daily Report 생성
    
- Risk Summary 템플릿 적용
    

---

## **9.5 Scheduler Test**

- 시장 개장/마감 시 타이밍 테스트
    
- Cron-like 동작 테스트
    

---

## **9.6 HealthCheck → Safety 변환 테스트**

Health Score가 낮을 때 Safety 상태가 정확히 변환되는지 검증.

---

# **10. End-to-End Scenario Test Architecture**

## **10.1 Full-Day Simulation Test**

Flow:

1. 장전 점검
    
2. 장중 ETEDA 루프
    
3. Fail-Safe 발생
    
4. 복구
    
5. 장후 보고서 생성
    

---

## **10.2 Fail-Safe 발생 → 복구 → 재개 시나리오**

FS040(브로커 오류) 발생 → Lockdown → 운영자 승인 → 정상 재개.

---

## **10.3 Network Delay 테스트**

지연 → 반복 오류 → Fail-Safe → 재시도 플로우 테스트.

---

## **10.4 Position Drift 테스트**

- Position과 Broker Position 불일치
    
- Auto-Sync 해결 여부 확인
    

---

## **10.5 Strategy → Execution End-to-End**

RawData  
→ Strategy  
→ Risk  
→ Portfolio  
→ Trading  
→ Execution  
→ T_Ledger  
→ UI

전체 흐름을 하나의 테스트로 검증한다.

---

# **11. Regression Test Architecture**

## **11.1 Regression Suite 구성**

- 핵심 모듈
    
- 안전성 기능
    
- 브로커 통합
    
- ETEDA
    
- Safety Layer
    

---

## **11.2 버전 변경 시 회귀 테스트 규칙**

- Schema Version 변경 → Regression 필수
    
- Engine Version 변경 → Pipeline Regression 필수
    

---

## **11.3 Schema/Contract Version Test**

버전 차이 감지 시 Fail-Safe 작동 여부 테스트.

---

## **11.4 Pipeline 변경 시 회귀 테스트**

ETEDA Step 로직 변경 시 Multi-Cycle Regression 수행.

---

## **11.5 Replay 기반 Regression**

과거 T_Ledger를 Replay하여 결과가 동일한지 검증.

---

# **12. Test Data & Mock Architecture**

## **12.1 Mock RawDataContract**

- 종목 수 1~20개 시나리오
    
- 가격 변동/거래량 변화 세트
    

---

## **12.2 Mock CalcDataContract**

Exposure·PnL 계산값 포함 Mock 데이터.

---

## **12.3 Mock Strategy/Risk Output**

다양한 조건(승인/거부/신호 충돌) 기반 Mock 세트.

---

## **12.4 Mock ExecutionResult**

파셜필·정상필·타임아웃 등 다양한 케이스.

---

## **12.5 Mock UI Contract**

UI 렌더링 테스트용 Contract.

---

## **12.6 Test Data Versioning**

Test Data 변경 시 Test Schema Version도 함께 증가.

---

# **13. Test Automation Framework**

## **13.1 pytest 기반 테스트**

pytest를 통해:

- Mark 기반 분류
    
- Fixture 기반 데이터 관리
    

---

## **13.2 CI/CD Pipeline 연동**

Github Actions 또는 GitLab CI를 사용하여  
테스트 자동 실행.

---

## **13.3 자동 커버리지 측정**

Coverage 80% 이상 유지.

---

## **13.4 테스트 로그/리포트 자동 저장**

- HTML 보고서
    
- JSON 테스트 결과
    
- Git 저장
    

---

## **13.5 테스트 실패 시 자동 알림**

Slack/Telegram으로 Critical 테스트 실패 즉시 전송.

---

# **14. Test Failure Handling**

## **14.1 실패 유형 분류**

- Logical Failure
    
- Data Failure
    
- Timing Failure
    
- Broker Failure
    
- Safety Failure
    

---

## **14.2 실패 분석 기준**

- 어떤 Contract가 실패했는가?
    
- 어떤 Engine 단계에서 실패했는가?
    
- Fail-Safe가 올바르게 발동했는가?
    

---

## **14.3 자동 재시도 조건**

네트워크 지연 계열은 자동 재시도 가능.

---

## **14.4 Critical Failure → Fail-Safe Escalation**

테스트 중 Fail-Safe 조건 발생 시  
자동으로 Safety Layer Escalation 확인.

---

## **14.5 자동 디버깅 가이드 생성**

- 오류 필드
    
- 예상 vs 실제 값
    
- 추정 원인
    
- 해결책 제안
    

테스트 실패 시 자동 생성된다.

---

# **15. Appendix**

## **15.1 테스트 케이스 템플릿**

Given / When / Then 구조.

---

## **15.2 Mock 클래스 다이어그램**

Mock RawData / Mock Broker / Mock UI 등 구조 포함.

---

## **15.3 Fixture 예시**

샘플 가격, 샘플 포지션 등 제공.

---

## **15.4 Error Case 샘플**

에러 발생 패턴을 문서로 정리.

---

## **15.5 End-to-End 테스트 다이어그램**

ETEDA 전체 흐름 기반 그래픽.

---

**QTS Testability Architecture v1.0.0 — 완료됨**

---

이제 남은 문서는 마지막 11번:  
**Architecture Change Management(아키텍처 변경 관리)**

스켈레톤 생성해줄까?