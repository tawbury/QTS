아래는 **12번 문서: QTS_Architecture_Summary.md  
(QTS 아키텍처 서머리 문서)**  
**완성본(v1.0.0)** 이다.

이 문서는 1~11번 아키텍처 문서의 핵심 내용을 통합·요약해  
QTS 전체 구조를 단일 문서로 빠르게 이해하도록 설계된  
QTS 아키텍처 시스템의 공식 요약 문서(Executive Summary)이다.

---

# ============================================================

# QTS Architecture Summary

# ============================================================

Version: v1.0.0  
Status: Summary Document (Final)  
Author: 타우  
Last Updated: 2025-12-12

문서 목적:  
이 문서는 QTS 자동매매 시스템의 전체 구조, 설계 철학, 데이터 흐름, 엔진 상호작용,  
안전성 시스템, 브로커 연동, UI 구조, 운영 및 테스트 체계 등  
모든 아키텍처 문서의 핵심 내용을 빠르게 이해할 수 있도록 정리한 통합 요약 문서이다.

QTS는 **데이터 중심·계약 기반·안전성 우선·자동화 우선** 원칙 위에서 설계된  
고신뢰 자동매매 플랫폼이며, 본 문서는 그 전체의 지도를 제공한다.

---

# **1. What is QTS? (QTS란 무엇인가)**

## **1.1 QTS 정의**

QTS(Qualitative Trading System)는  
**시트 기반 데이터 입력 + Python 기반 엔진 + 브로커 API + 자동화 레이어**를 통합한  
완전 자동 운용 매매 시스템이다.

---

## **1.2 시스템의 목적**

1. 반복 가능한 자동매매 실행
    
2. 데이터 정합성 중심 운용
    
3. 위험 통제 기반 의사결정
    
4. Fail-Safe 중심의 안정성 확보
    
5. 확장 가능한 구조 제공
    

---

## **1.3 QTS가 해결하는 문제**

- 사람 기반 감정 매매 제거
    
- 데이터 오류 자동 감지
    
- 브로커 불안정성 대응
    
- 위험/노출 관리 자동화
    
- UI·로그·리포트 자동화
    
- 오류 발생 시 자동 보호(Fail-Safe)
    

---

## **1.4 시스템의 주요 철학**

- **Contract-Driven Architecture**
    
- **Schema First**
    
- **Zero-Formula UI**
    
- **Full Automation**
    
- **Fail-Safe Default**
    
- **Human Override 최소화**
    

---

## **1.5 QTS 구성 요소 요약**

- **Core Layer**
    
- **Data Layer**
    
- **Engine Layer**
    
- **ETEDA Pipeline**
    
- **Broker Layer**
    
- **UI Layer**
    
- **Safety Layer**
    
- **Ops/Automation Layer**
    
- **Testability Layer**
    

---

## **1.6 관련 문서**

- **Main Architecture**: [00_Architecture.md](./00_Architecture.md)
- **Schema Automation**: [01_Schema_Auto_Architecture.md](./01_Schema_Auto_Architecture.md)
- **Engine Core**: [02_Engine_Core_Architecture.md](./02_Engine_Core_Architecture.md)
- **ETEDA Pipeline**: [03_Pipeline_ETEDA_Architecture.md](./03_Pipeline_ETEDA_Architecture.md)
- **Data Contract**: [04_Data_Contract_Spec.md](./04_Data_Contract_Spec.md)
- **UI Architecture**: [06_UI_Architecture.md](./06_UI_Architecture.md)
- **Fail-Safe & Safety**: [07_FailSafe_Architecture.md](./07_FailSafe_Architecture.md)
- **Broker Integration**: [08_Broker_Integration_Architecture.md](./08_Broker_Integration_Architecture.md)
- **Ops & Automation**: [09_Ops_Automation_Architecture.md](./09_Ops_Automation_Architecture.md)
- **Testability**: [10_Testability_Architecture.md](./10_Testability_Architecture.md)
- **Change Management**: [11_Architecture_Change_Management.md](./11_Architecture_Change_Management.md)
- **Config 3분할**: [13_Config_3분할_Architecture.md](./13_Config_3분할_Architecture.md)

**Sub-Architecture Extensions (v1.1.0):**
- **Capital Flow**: [sub/14_Capital_Flow_Architecture.md](./sub/14_Capital_Flow_Architecture.md)
- **Scalp Execution**: [sub/15_Scalp_Execution_Micro_Architecture.md](./sub/15_Scalp_Execution_Micro_Architecture.md)
- **Micro Risk Loop**: [sub/16_Micro_Risk_Loop_Architecture.md](./sub/16_Micro_Risk_Loop_Architecture.md)
- **Event Priority**: [sub/17_Event_Priority_Architecture.md](./sub/17_Event_Priority_Architecture.md)
- **System State & Promotion**: [sub/18_System_State_Promotion_Architecture.md](./sub/18_System_State_Promotion_Architecture.md)

---

# **2. QTS Architecture Overview**

## **2.1 전체 시스템 레이어 요약**

```
Core Layer
  ├─ Config Architecture
  ├─ Schema Automation Engine
  ├─ Logging/Monitoring Core

Data Layer
  ├─ 10+1 시트 구조 (Google 10 + Config_Local 1: Portfolio, Position, RawData 등)
  ├─ Raw → Calc Contract 변환
  ├─ Dividend Local/Git DB

Engine Layer
  ├─ Strategy / Risk / Portfolio / Trading / Performance Engines

ETEDA Pipeline
  ├─ Extract → Transform → Evaluate → Decide → Act

Broker Layer
  ├─ Broker Adapter / Execution Flow / Error Normalization

UI Layer
  ├─ Zero-Formula 기반 R_Dash

Safety Layer
  ├─ Fail-Safe / Guardrail / Anomaly / Safety State Machine

Ops & Automation Layer
  ├─ Auto-Check / Auto-Sync / Scheduler / 보고서 / 백업

Testability Layer
  ├─ Unit → Engine → Pipeline → E2E → Regression
```

---

## **2.2 Layer 간 관계**

- ETEDA는 Engine Layer와 Data Layer의 중심 허브
    
- Safety는 모든 Layer의 오류를 감지하는 상위 보호 계층
    
- Ops/Automation은 시스템의 지속성 유지
    
- Broker Layer는 ETEDA Act 단계의 실행 기반
    
- UI Layer는 사용자의 모니터링 포털 역할
    

---

## **2.3 아키텍처 핵심 설계 원칙**

- Modular
    
- Deterministic
    
- Predictable
    
- Data-Driven
    
- Safety-First
    
- Full Automation
    

---

# **3. ETEDA Pipeline – QTS의 심장부**

## **3.1 개요**

ETEDA는 QTS의 모든 계산·판단·실행을 담당하는 5단계 자동매매 파이프라인이다.

---

## **3.2 5단계 요약**

1. **Extract**
    

- RawDataContract 로드
    
- 종목/가격/잔고/배당 데이터 수집
    

2. **Transform**
    

- Exposure/PnL/Signal 계산
    
- CalcDataContract 생성
    

3. **Evaluate**
    

- Strategy/Risk 판단
    
- 승인/거부/경계 판단
    

4. **Decide**
    

- 매매 결정(OrderDecision) 생성
    

5. **Act**
    

- Broker Adapter로 주문 실행
    
- ExecutionResult → T_Ledger 반영
    

---

## **3.3 ETEDA 입력/출력 핵심**

- 입력: Raw Contract
    
- 출력: Calc Contract, Engine Outputs, ExecutionResult
    

---

## **3.4 안정성 요소**

- 단일 사이클 오류 → Fail-Safe 발동
    
- Cycle Time Monitoring
    
- 파이프라인 단계별 독립성 유지
    

---

# **4. Core Layer Summary**

## **4.1 Config Architecture 요약**

- 모든 설정값은 Config 시트에서 관리
    
- Danger 태그는 UI 숨김 처리
    
- Python은 Key 기반 접근
    

---

## **4.2 Schema Automation Engine 요약**

- Sheets 구조가 변해도 엔진 수정 없이 자동 매핑
    
- Column/Row 변경 자동 감지
    
- Schema.json 자동 생성
    

---

## **4.3 Logging & Monitoring 요약**

- ETEDA Cycle Log
    
- Engine Log
    
- Safety Log
    
- Execution Log
    
- Performance Log
    

---

# **5. Data Layer Summary**

## **5.1 10+1 시트 구조 개요**

Google 10: Portfolio, Performance, R_Dash, Dividend, T_Ledger, History, Strategy, Position, Config_Swing, Config_Scalp. 로컬 1: Config_Local.

---

## **5.2 Raw → Calc 흐름 요약**

RawDataContract  
→ Exposure/PnL 계산  
→ CalcDataContract 생성

---

## **5.3 Exposure 구조 요약**

- Symbol Exposure
    
- Account Exposure
    
- Total Exposure
    

---

## **5.4 Dividend Local/Git DB 요약**

- Git 기반 버전 관리
    
- 배당 정보 정확성 확보
    
- ETL 단계에서 자동 로드
    

---

## **5.5 Update Mode Architecture 요약**

- Manual Update
    
- Auto Update
    
- Sync Mode
    

---

# **6. Engine Layer Summary**

각 엔진은 입력과 출력이 명확한 Contract 기반으로 동작한다.

## **6.1 Strategy Engine**

- 신호 생성
    
- confidence 값 제공
    

## **6.2 Risk Engine**

- 승인/거부/경계 판단
    
- Exposure, Drawdown, PnL 기반
    

## **6.3 Portfolio Engine**

- 수량 계산
    
- 포트폴리오 구성
    

## **6.4 Trading Engine**

- 주문 생성
    
- 가격·수량·타입 계산
    

## **6.5 Performance Engine**

- 손익/PnL 계산
    
- 장기 성과 분석
    

---

# **7. Broker Integration Summary**

## **7.1 Broker Adapter Layer**

- 공통 인터페이스 제공
    
- API 차이 Normalization
    

---

## **7.2 Multi-Broker Architecture**

- 한국투자증권 → 기본 브로커
    
- 키움증권 등 확장 지원 예정
    

---

## **7.3 주문 처리 요약**

OrderDecision  
→ BrokerOrder  
→ ExecutionResult  
→ Ledger 기록

---

## **7.4 Error Normalization**

브로커 오류를 Fail-Safe 코드(FS040 등)로 표준화.

---

## **7.5 ExecutionResult 요약**

- filled_qty
    
- avg_price
    
- status
    
- slippage
    

---

# **8. UI Layer Summary**

## **8.1 Zero-Formula UI 개념**

- 수식 없음
    
- Python Contract 기반
    
- 변경 안정성 확보
    

---

## **8.2 R_Dash 요약**

- 포트폴리오
    
- 리스크
    
- 손익
    
- Safety 상태
    
- ETEDA 요약
    

---

## **8.3 UI Contract 요약**

Python에서 생성한 JSON을 기반으로 RDash 렌더링.

---

## **8.4 Pipeline State 표시**

pipeline_state = NORMAL / FAIL / LOCKDOWN 등 표시.

---

# **9. Safety Layer Summary**

## **9.1 Fail-Safe 개념**

데이터/브로커/계산 오류 발생 시 즉시 시스템 보호.

---

## **9.2 Guardrail 개념**

경고 레벨 조건:

- Exposure 초과
    
- PnL 급변
    

---

## **9.3 Anomaly Detection**

- 가격 급변
    
- PnL 급변
    
- Pipeline 지연
    
- Position Drift
    

---

## **9.4 Safety State Model**

```
NORMAL → WARNING → FAIL → LOCKDOWN
```

---

## **9.5 ETEDA와 Safety 관계**

ETEDA 내부 오류 → Safety Layer가 즉시 Fail-Safe 호출.

---

# **10. Ops & Automation Summary**

## **10.1 Manual Ops Workflow**

장전 점검 → 장중 모니터링 → 장후 보고.

---

## **10.2 Auto-Check / Auto-Sync**

- 구조 점검
    
- 데이터 검증
    
- 잔고 동기화
    
- Git Sync
    

---

## **10.3 Auto-Report / Auto-Backup**

- Daily Report
    
- Exposure/PnL Summary
    
- Snapshot 백업
    

---

## **10.4 Scheduler 요약**

- Cron-like 구조
    
- Market Open/Close 자동 인식
    

---

## **10.5 Health Check 요약**

Broker/ETEDA/UI/Safety 전반 점검 및 Health Score 생성.

---

# **11. Testability Summary**

## **11.1 Test Layers 요약**

- Unit
    
- Engine
    
- Contract
    
- Integration (ETEDA)
    
- Broker
    
- Safety
    
- UI
    
- Ops
    
- End-to-End
    
- Regression
    

---

## **11.2 주요 테스트 요약**

- Fail-Safe Trigger Test
    
- ExecutionResult Test
    
- Pipeline Timing Test
    
- Schema/Contract Version Test
    
- Strategy/Risk 검증
    

---

## **11.3 End-to-End 개요**

RawData  
→ Engine  
→ Pipeline  
→ Broker  
→ Ledger  
→ UI  
까지 전 과정을 단일 테스트로 검증.

---

## **11.4 Regression Test 요약**

버전 변경 시 전체 기능 회귀 테스트 수행.

---

# **12. Architecture Change Management Summary**

## **12.1 변경 관리 핵심 요약**

- 변경 전 영향 분석
    
- 변경 후 테스트 필수
    
- 문서/버전 업데이트 필수
    

---

## **12.2 변경 유형 요약**

Schema / Engine / ETEDA / UI / Safety / Ops / Broker

---

## **12.3 영향 분석 요약**

각 변경은

- 데이터
    
- 엔진
    
- 파이프라인
    
- UI
    
- Safety
    

등 전체 계층 검토 필요.

---

## **12.4 버전 관리 요약**

Semantic Versioning 적용:

- Major
    
- Minor
    
- Patch
    

---

## **12.5 배포 요약**

- Stage 테스트
    
- Production 배포
    
- Rollback 전략
    
- 배포 후 Safety Log/ETEDA Log 모니터링
    

---

# **13. QTS Master Diagram Set**

다이어그램 요약(실제 이미지는 별도 문서에서 관리):

- 전체 시스템 아키텍처
    
- ETEDA Pipeline
    
- Engine Interaction Map
    
- Safety State Machine
    
- Broker Execution Flow
    
- UI Rendering Flow
    

---

# **14. QTS Glossary (핵심 용어)**

- **Contract**: Layer 간 데이터 규격
    
- **Schema**: 시트 구조 정의
    
- **Fail-Safe**: 즉시 중단 및 보호 절차
    
- **Guardrail**: 경계 기반 위험 통제
    
- **ETEDA**: QTS 자동매매 파이프라인
    
- **ExecutionResult**: 주문 체결 결과
    
- **Position Drift**: 실제 포지션과 시트 포지션 불일치
    
- **Pipeline State**: NORMAL/FAIL/LOCKDOWN
    

---

# **15. Appendix**

## **15.1 Architecture 문서 구성도**

1. Main Architecture
    
2. Core Layer Architecture
    
3. Data Layer Architecture
    
4. Engine Layer Architecture
    
5. Pipeline Architecture
    
6. Broker Architecture
    
7. Safety Architecture
    
8. UI Architecture
    
9. Ops Architecture
    
10. Testability Architecture
    
11. Change Management Architecture
    
12. Summary Architecture
    

---

## **15.2 문서 버전 요약표**

|문서|버전|
|---|---|
|Main Architecture|v1.0.0|
|Core Layer|v1.0.0|
|Data Layer|v1.0.0|
|Engine Layer|v1.0.0|
|Pipeline Architecture|v1.0.0|
|Broker Architecture|v1.0.0|
|Safety Architecture|v1.0.0|
|UI Architecture|v1.0.0|
|Ops Architecture|v1.0.0|
|Testability Architecture|v1.0.0|
|Change Management|v1.0.0|
|Summary Architecture|v1.0.0|

---

## **15.3 RACI 요약 (간단 역할 매트릭스)**

- Author: 타우
    
- Reviewer: 미래 협업 엔지니어
    
- System Owner: QTS Core
    

---

## **15.4 설계 원칙 요약**

- Deterministic
    
- Modular
    
- Contract-Driven
    
- Safety-First
    
- Zero-Formula
    
- Automation
    

---

## **15.5 QTS 개발·운영 주기 요약**

설계 → 개발 → 테스트 → 배포 → 모니터링 → 개선 → 문서 업데이트.

---

**QTS Architecture Summary v1.0.0 — 완료됨**

---

모든 12개 메인/서브 아키텍처 문서가 **v1.0.0 풀세트로 완성됨**.

이제 다음 중 어떤 단계로 갈까?

1. **12개 문서 전체 검수 및 통합 품질 점검**
    
2. **QTS 메인 아키텍처 PDF/Notion 정리본 생성**
    
3. **QTS 아키텍처 다이어그램 세트 제작(ImageFX/도식)**
    
4. **v1.1 업데이트 계획 로드맵 생성**
    

원하는 방향을 알려줘.