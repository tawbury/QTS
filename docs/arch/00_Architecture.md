
# **0. 문서 개요**

QTS Main Architecture는 QTS(Qualitative Trading System)의 전체 구조를  
단일 기준(Single Source of Truth, SSoT)으로 정의하기 위한 상위 문서이다.  
본 문서는 시스템의 설계 철학, 계층별 아키텍처, 데이터 모델, 엔진 구조,  
운영·안전·확장 전략까지 모두 포함하는 **QTS 전체 생태계의 최상위 설계 문서**다.

QTS는 단순 자동매매 프로그램이 아니라,  
데이터 품질·프로세스 제어·리스크 관리·테스트 가능성·운영 효율성까지  
모두 통합적으로 관리되는 **엔터프라이즈급 자동매매 프레임워크**를 목표로 한다.

이를 위해 본 문서는 다음 네 가지 목적을 갖는다.


---

## **0.1 문서 목적**

1. **QTS의 전체 구조를 하나의 일관된 기준(SSoT)으로 정의하기 위함**
    
    - 개발, 운영, 테스트, 유지보수, 리스크관리, Multi-Broker 확장까지  
        모든 작업은 본 문서를 기준으로 이루어진다.
        
2. **데이터·엔진·파이프라인·UI·운영 레이어의 관계 및 의존성을 명확히 규정**
    
    - 총 11개 시트 기반 Data Layer (Google Spreadsheet 10개 + Repo 1개)
        
    - Schema Automation Engine
        
    - ETEDA Execution Pipeline
        
    - Trading/Strategy/Risk/Portfolio 등 Engine Layer
        
    - Zero-Formula UI Layer
        
    - Safety Layer, Ops Layer  
        각각이 어떻게 연결되는지 체계적으로 설명한다.
        
3. **설계 변경 또는 확장 시 충돌을 방지하기 위한 상위 의사결정 기준 제공**
    
    - “설계 원칙을 벗어나는 변경”을 방지
        
    - 브로커 확장, 전략 확장, 시트 구조 변경 발생 시  
        어떤 기준으로 판단해야 하는지 정의한다.
        
4. **QTS가 장기적으로 유지될 수 있는 시스템적 내구성 확보**
    
    - 개발자 교체, 전략 변경, 환경 변경이 발생해도  
        시스템 구조는 붕괴하지 않는 방향으로 설계 철학을 고정한다.
        


---

## **0.2 범위**

본 문서는 다음 범위를 포함한다.

### **포함**

- **QTS 전체 계층(Layer) 아키텍처 정의**
    
- **Data Layer & 11 Sheets 구조 상세**
    
- **Schema Automation Engine의 동작 원리·데이터 플로우·자동 매핑 규칙**
    
- **Trading/Risk/Strategy/Portfolio/Performance 엔진 구조**
    
- **ETEDA Execution Pipeline 설계**
    
- **Zero-Formula UI 구조 및 시각화 흐름**
    
- **리스크·안전장치·예외 처리**
    
- **Multi-Broker 확장 구조**
    
- **운영 자동화 및 테스트 체계**
    
- **아키텍처 변경 관리 프로세스**
    

### **제외**

- 전략의 구체적 수학적 공식  
    (단, Strategy Engine Interface 및 Data Contract는 포함)
    
- 코드 단위 구현 상세  
    (해당 내용은 Engine Spec 또는 Code Repository로 분리)
    
- 브로커 API별 인증/통신 상세 스펙  
  (해당 내용은 Broker Adapter 문서에 별도 관리)
  


---

## **0.3 관련 문서**

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
- **Architecture Summary**: [12_Architecture_Summary.md](./12_Architecture_Summary.md)
- **Config 3분할**: [13_Config_3분할_Architecture.md](./13_Config_3분할_Architecture.md)

---

### **Architecture Extension (v1.1.0)**

Sub-architecture extensions located in `docs/arch/sub/`:
- **Capital Flow**: [sub/14_Capital_Flow_Architecture.md](./sub/14_Capital_Flow_Architecture.md) - L4 Engine Extension
- **Scalp Execution**: [sub/15_Scalp_Execution_Micro_Architecture.md](./sub/15_Scalp_Execution_Micro_Architecture.md) - L5 Pipeline Extension
- **Micro Risk Loop**: [sub/16_Micro_Risk_Loop_Architecture.md](./sub/16_Micro_Risk_Loop_Architecture.md) - L7 Safety Extension
- **Event Priority**: [sub/17_Event_Priority_Architecture.md](./sub/17_Event_Priority_Architecture.md) - Cross-cutting Concern
- **System State & Promotion**: [sub/18_System_State_Promotion_Architecture.md](./sub/18_System_State_Promotion_Architecture.md) - L7 Safety Extension


---

## **0.4 대상 독자**

- **QTS 시스템 개발자**  
    Trading/Risk/Strategy/Schema/Engine 개발 담당자
    
- **시스템 운영 및 모니터링 담당자**
    
- **시트 설계·데이터 관리 담당자**
    
- **전략 연구 및 Backtest 담당자**
    
- **Multi-Broker 확장 설계자**
    

이 문서는 개발자만을 위한 문서가 아니다.  
QTS 전체의 협업 구조가 명확해지도록 모든 이해관계자가 참고하는 기준 문서이다.


---

## **0.5 다른 문서와의 관계**

본 문서는 아래 문서를 상위에서 통제한다.

|문서|역할|종속 관계|
|---|---|---|
|**QTS Main Architecture (본 문서)**|최상위 구조·철학|모든 하위 문서의 기준|
|**Architecture_SubDocs** (Schema / Engine / Pipeline / Autogen)|계층별 상세 설계|본 문서의 Layer Model을 따름|
|**Sheet Spec Docs**|11개 시트 정의|Data Layer Architecture의 영향 아래 있음|
|**Engine Spec Docs**|Trading/Risk/Strategy 엔진 구현 정의|Engine Layer Architecture를 기준으로 작성|
|**Test Spec**|테스트 기준|Testability Architecture에 종속|
|**Ops / Automation Spec**|운영 자동화 기준|Ops Layer Architecture를 기준으로 작성|

모든 문서는 상위 아키텍처 변경 시 재검토되어야 한다.


---

## **0.6 문서 버전 관리 규칙**

- **v1.x** : QTS 구조의 안정화 버전
    
- **v2.x** : 브로커 확장 및 엔진 고도화 이후 적용
    
- **v3.x** : 전략 엔진의 ML/AI 기반 고도화 시점
    
- 모든 하위 문서는 Main Architecture 버전과 연동되며  
    구조 변경이 확정될 경우 동일하게 major version을 증가시킨다.
    


---

## **0.7 문서 사용 방법**

1. **설계·코딩·운영·테스트 전 반드시 본 문서를 먼저 확인**  
    절차가 바뀌지 않도록 중앙 기준을 유지한다.
    
2. **시트 변경 발생 시 → Data Layer Architecture 기준으로 검증**
    
3. **전략 개발 발생 시 → Strategy Engine Interface 기준으로 작성**
    
4. **브로커 확장 시 → Multi-Broker Architecture 우선 검토**
    
5. **실행 파이프라인 문제 발생 시 → ETEDA Pipeline 구조 우선 확인**
    
6. **설계 변경 시 → Architecture Change Management 절차 준수**
    


---

## **0.8 QTS 상위 요약**

QTS는 다음 세 요소를 핵심 정체성으로 갖는다.

1. **Data-Driven System**  
    모든 판단은 11개 시트(구글 스프레드시트 10 + 레포 1) 기반 Data Contract로 결정된다.  
    전략, 리스크, 포트폴리오 모두 데이터 구조에 종속된다.
    
2. **Pipeline-Oriented Execution**  
    트레이딩은 단발성 실행이 아니라  
    ETEDA(Extract → Transform → Evaluate → Decide → Act)의  
    반복 파이프라인으로 설계된다.
    
3. **Multi-Engine Architecture**  
    Strategy, Risk, Portfolio, Performance  
    4대 엔진은 독립적이지만 데이터 계약(Data Contract)로 단단히 연결된다.
    Broker Layer는 별도로 주문 실행을 담당한다.
    
4. **Schema Automation Engine 중심의 자가 회복 구조**  
    시트 구조가 변해도 시스템이 멈추지 않도록  
    스키마 자동 갱신 시스템을 핵심 인프라로 사용한다.
    
5. **Zero-Formula UI**  
    모든 계산은 Python에서 이루어지며  
    시트는 UI 역할만 담당한다.
    


---

# **1. 시스템 철학 및 설계 원칙**

QTS(Qualitative Trading System)는  
“데이터 구조 변화에도 멈추지 않고 스스로 회복하는 자동매매 시스템”을  
핵심 철학으로 두고 설계되었다.

전통적인 자동매매 시스템은 다음과 같은 문제를 가진다:

- 시트/DB 구조가 조금만 변경되어도 전체 프로그램 장애 발생
    
- 전략 추가 시 시스템이 불안정해지는 구조
    
- 엔진 간 의존성이 복잡해 유지보수가 어려움
    
- 테스트 불가능한 구조
    
- 브로커 확장 시 시스템 전체를 다시 짜야 하는 구조
    

QTS는 이러한 기존 문제를 근본적으로 제거하기 위해  
다음 6가지 철학을 기반으로 설계되었다.

---

## **1.1 Philosophy 1 — Data-Driven Architecture**

QTS는 데이터가 설계를 지배하는 시스템이다.

- 모든 엔진은 데이터 계약(Data Contract)을 기준으로 동작한다.
    
- UI는 데이터를 보여주는 역할만 담당한다.
    
- 전략·리스크·포트폴리오 엔진은 시트 기반 데이터 계약을 통해 연결된다.
    
- 시트가 변해도 ‘스키마 자동화 엔진’이 변환·조정하여  
    엔진이 깨지지 않는 구조를 유지한다.
    

핵심 문장:

**설계는 데이터에 종속되며, 데이터 구조의 변경을 시스템이 스스로 받아들인다.**

---

## **1.2 Philosophy 2 — Pipeline-Oriented Execution (ETEDA)**

QTS의 모든 매매 프로세스는 파이프라인으로 통제된다.

ETEDA:

1. Extract
    
2. Transform
    
3. Evaluate
    
4. Decide
    
5. Act
    

이 5단계는 엔진, 데이터, 리스크, 계좌 상태를  
정해진 순서로 절차적으로 처리한다.

- 실행 순서가 어디서도 흐트러지지 않는다.
    
- 엔진 간 명확한 인터페이스가 존재한다.
    
- 각 단계는 독립적으로 테스트 가능하다.
    

핵심 문장:

**매매는 이벤트가 아니라 파이프라인 흐름이다.**

---

## **1.3 Philosophy 3 — Multi-Engine Independence**

QTS는 엔진 기반 구조이다.

각 엔진은 다음 역할을 가진다:

- Strategy Engine: 진입·청산 판단
    
- Risk Engine: 리스크 승인·거부
    
- Portfolio Engine: 보유자산·노출도 계산
    
- Performance Engine: 손익·성과 분석
    
- **Broker Layer**: 주문 실행 및 브로커 API 통합 (Engine이 아닌 별도 Layer)

엔진은 독립적이지만 데이터 계약을 통해 정교하게 연결된다.

핵심 문장:

**엔진은 독립적이지만 고립되지 않는다.**

---

## **1.4 Philosophy 4 — Schema Automation as the System Core**

QTS의 핵심 인프라는 **Schema Automation Engine**이다.

- 시트 구조가 변해도 엔진에 오류가 발생하지 않게 한다.
    
- 좌표 기반이 아닌 “필드 구조 기반”으로 매핑
    
- 스키마 버전 관리 + 자동 갱신 기반
    
- 모든 엔진 로직은 스키마 구조에 종속되어 실행된다.
    

핵심 문장:

**스키마가 바뀌어도 시스템은 멈추지 않는다.**

---

## **1.5 Philosophy 5 — Zero-Formula UI**

QTS UI의 목표는 “데이터 시각화 도구”다.

- 시트에는 계산식이 없다.
    
- 모든 계산은 Python에서만 수행한다.
    
- UI는 파이썬이 전달한 값만 보여준다.
    
- UI 변경으로 엔진이 영향을 받지 않는다.
    

핵심 문장:

**Sheets는 계산도구가 아니라 인터페이스다.**

---

## **1.6 Philosophy 6 — Never Break Design**

QTS는 설계가 가장 중요한 시스템이다.

- 엔진보다 설계가 먼저다.
    
- 문서가 업데이트되지 않으면 시스템도 업데이트되지 않는다.
    
- 설계를 깨는 변경은 금지된다.
    
- 아키텍처를 변경할 경우 절차적 승인 필요.
    

핵심 문장:

**QTS는 설계 중심 시스템이며, 설계를 우회하는 구현은 허용되지 않는다.**

---

# **2. 상위 시스템 아키텍처**

QTS는 다음 네 가지 축을 중심으로 설계된 **멀티 레이어 자동매매 시스템**이다.

1. **Data Layer (총 11개 시트: Google Spreadsheet 10개 + Repo 1개)**
    
2. **Engine Layer (Trading/Strategy/Risk/Portfolio/Performance)**
    
3. **Execution Pipeline Layer (ETEDA)**
    
4. **Ops & Safety Layer (Auto-Recovery, Logging, Monitoring, Fail-Safe)**
    

여기에 Multi-Broker, UI Layer, Schema Automation Engine이 결합되어  
전체 시스템이 하나의 생태계처럼 작동하도록 구성된다.

아래 내용은 QTS 전체 구조를 “숲 → 나무” 순서로 설명하는 상위 개념도다.

---

## **2.1 시스템 개념도(요약)**

텍스트 기반 개념도 (QTS 전체 흐름 요약):

```
                 ┌─────────────────────────────┐
                 │         UI / 시트 레이어     │
                 │    (Zero-Formula Dashboard) │
                 └──────────────┬──────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────┐
│           Data Layer (11 Sheets: GSheet 10 + Repo 1)      │
│ (GSheet) Config_Scalp │ Config_Swing │ Position │ Strategy │
│ (GSheet) T_Ledger │ Dividend │ Portfolio │ Performance │ R_Dash │
│ (GSheet) History                                              │
│ (Repo)   Config_Local                                         │
└───────────────────────┬──────────────────────────────────┘
                        │ Schema Automation Engine
                        ▼
┌──────────────────────────────────────────────────────────┐
│                 Engine Layer (4 Engines)                │
│ Strategy │ Risk │ Portfolio │ Performance                │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│           Execution Pipeline Layer: ETEDA                │
│ Extract → Transform → Evaluate → Decide → Act           │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│                    Broker Layer (Multi-Broker)           │
│     Korea Investment → Kiwoom → Future Brokers...        │
└──────────────────────────────────────────────────────────┘

   + Logging Layer + Monitoring Layer + Fail-Safe Layer (보조)
```

---

## **2.2 Architectural Pillars**

QTS 전체를 지탱하는 세 가지 기둥은 다음과 같다.

### **(1) Data-Driven**

- 11개 시트 구조(Config 3분할 포함)가 시스템의 중심이며  
    엔진, 파이프라인, UI는 이 데이터에 종속된다.
    

### **(2) Pipeline-Oriented (ETEDA)**

- 매매는 이벤트가 아니라 파이프라인이다.
    
- 모든 실행은 ETEDA로 통제된다.
    

### **(3) Engine-Modular**

- Strategy, Risk, Portfolio, Performance  
    4개 엔진이 독립적 모듈로 구성되어 있으며  
    데이터 계약(Data Contract)으로 연결된다.
    
- Broker Layer는 별도 Execution Layer로 주문 실행을 담당한다.
    

---

## **2.3 상위 Layer 모델**

QTS는 아래와 같은 7 Layer 모델로 작동한다.

|Layer|설명|
|---|---|
|**L1. UI Layer**|Zero-formula 기반 Dashboard, R_Dash 시각화|
|**L2. Data Layer**|총 11개 시트(구글 스프레드시트 10 + 레포 1) 기반|
|**L3. Schema Layer**|스키마 자동화 엔진, 데이터 계약, 필드 매핑|
|**L4. Engine Layer**|Strategy/Risk/Portfolio/Performance 엔진 (4대 엔진)|
|**L5. Pipeline Layer**|ETEDA Execution Pipeline|
|**L6. Broker Layer**|한국투자증권 → 키움증권 → 다중 브로커 확장|
|**L7. Ops & Safety Layer**|이상 감지·로그·모니터링·Fail-Safe 구조|

이 구조는 설계 변경 시에도 참조해야 하는 최상위 기준이다.

---

## **2.4 Component Interaction Overview**

### **1) 데이터 → 스키마**

- UI/시트에 입력된 값은 모두 Data Layer에서 출발
    
- Schema Automation Engine이 구조를 읽고 필드를 정의
    
- 모든 엔진에서 참조하는 단일 데이터 계약을 생성
    

### **2) 스키마 → 엔진**

- 전략, 리스크, 포트폴리오 계산은  
    스키마가 제공하는 필드 구조를 기반으로 수행
    
- 엔진은 서로 독립적이지만 스키마를 통해 일관성 유지
    

### **3) 엔진 → 파이프라인 (ETEDA)**

- 엔진 자체는 판단 주체
    
- 파이프라인은 실행 순서와 흐름을 통제하는 감독자 역할
    

### **4) 파이프라인 → 브로커**

- Act 단계에서 ExecutionIntent를 Broker Layer로 전달
    
- BrokerEngine은 ExecutionIntent를 받아 ExecutionResponse 반환
    
- LiveBroker/MockBroker/NoopBroker 패턴으로 Fail-Safe 기능 내장
    
- Multi-Broker Adapter 패턴을 사용하여 브로커 확장 용이
    

### **5) 브로커 → 데이터 업데이트 → 엔진 재반영**

- 체결/주문 결과는 다시 Data Layer로 반영
    
- 다음 ETEDA 사이클에서 이를 다시 평가해 지속 실행
    

---

## **2.5 Why This Architecture? (설계 배경)**

QTS의 설계는 다음 “실전적 문제”를 해결하기 위해 탄생했다.

### 1) 시트 구조 변경 시 프로그램 전체가 깨지는 문제

→ Schema Automation Engine이 자동으로 매핑 수정

### 2) 전략이 여러 개일 때 제어 불가

→ Strategy Engine + Pipeline 통합으로 판단 일원화

### 3) 데이터 품질 문제를 조기에 탐지하지 못함

→ Logging/Monitoring/Core Safety Layer 설계

### 4) 다중 브로커 확장 난이도

→ Broker Adapter Layer 설계

### 5) 실시간 모니터링 부재

→ Zero-Formula UI + Dashboard Block Architecture

---

## **2.6 Architecture Integrity Rules (변경 금지 원칙)**

QTS는 아래 다섯 가지 원칙을 절대 훼손할 수 없다.

1. **Data Layer > Engine Layer > Pipeline Layer 순서가 바뀌면 안 된다.**
    
2. **Zero-formula UI 원칙은 절대 깨지지 않는다.**
    
3. **Schema Automation Engine 없이 엔진이 직접 시트에 접근하면 안 된다.**
    
4. **파이프라인은 반드시 ETEDA 원칙을 따른다.**
    
5. **주문 실행은 반드시 Broker Layer를 통해 ExecutionIntent/Response Contract를 따른다.**
    

이 다섯 가지는 설계 철학의 핵심이자 시스템 안정성의 기반이다.

---

## **2.7 This Chapter as a Foundation**

본 장은 이후 모든 장의 기반이 된다.

- 3장은 Core Layer Architecture
    
- 4장은 Data Layer Architecture
    
- 5장은 Engine Layer Architecture
    
- 6장은 Pipeline Architecture
    
- 7장은 UI Layer Architecture
    
- 8장은 Safety Layer
    
- 9장은 Multi-Broker
    
- 10~12장은 운영/테스트/변경관리
    

즉, 지금 정의한 상위 구조는 이후 모든 문서의 정합성을 보장하기 위한 기준이다.

---

# **3. Core Layer Architecture**

Core Layer는 QTS 전체의 기반이 되는 시스템적 핵심(infrastructure core)이다.  
이 레이어는 엔진이나 전략보다 더 근본적인 역할을 수행하며,  
QTS가 "변경에 강하고, 자체적으로 회복 가능하며, 장기 운영 가능한 구조"를 갖도록 만든다.

QTS의 Core Layer는 아래 3개 요소로 구성된다:

1. **Config Architecture**
    
2. **Schema Automation Engine**
    
3. **Logging & Monitoring Core**
    

이 장에서는 이 세 구성요소가 어떻게 통합되어 동작하는지 설명한다.

---

# **3.1 Config Architecture**

Config Architecture는 QTS 전체 시스템의 "제어탑(Controller Layer)"이다.  
모든 엔진과 파이프라인은 시트 기반 Config 설정을 기준으로 동작하며,  
하드코딩 대신 동적 설정 구조를 통해 운영 유연성과 안정성을 확보한다.

**최신 변경**: Config는 전략별 리스크 분리를 위해 **3개의 Google Sheet로 물리 분리**되었다.  
- `Config_Local`: 시스템/전역 파라미터 (전략 불변)  
- `Config_Scalp`: Scalp 전략 전용 튜닝 파라미터  
- `Config_Swing`: Swing 전략 전용 튜닝 파라미터

---

## **3.1.1 역할 (Role of Config Layer)**

Config Layer는 다음과 같은 세 가지 목적을 가진다.

1. **운영 모드 제어 (백테스트/실거래/시뮬레이션 등)**
    
2. **Global Parameter Management (Local 전용)**
    
    - 주문 가능 여부
        
    - 리스크 한도 (Hard Risk)
        
    - 포트폴리오 목표 비중
        
    - Kill Switch / Fail-safe 정책
        
3. **Strategy-Specific Parameter Management**
    
    - 전략별 진입/청산 규칙 (Scalp/Swing 분리)
        
    - 전략별 리스크 제어 파라미터
        
    - 전략별 포지션/비중 설정
        
4. **Pipeline Behavior Control**
    
    - ETEDA 각 단계의 활성화
        
    - 실행 간격
        
    - Safety Layer 허용 범위
        

**핵심 원칙**: QTS는 엔진이 아닌 **Config 시트가 시스템을 지휘하는 구조**이며,  
**Sheet가 곧 스코프다** (전략 스코프는 Google Sheet 단위로 물리 분리).

---

## **3.1.2 Config Structure (Google Sheets 3분할 기반)**

Config 시트는 **전략별 리스크 분리**를 위해 3개의 Sheet로 구성된다:

|Sheet|역할|스코프|변경 성격|
|---|---|---|---|
|`Config_Local`|System / Global|전략 불변(전역)|낮음(거의 고정)|
|`Config_Scalp`|Strategy Tunable|Scalp 전용|높음(튜닝)|
|`Config_Swing`|Strategy Tunable|Swing 전용|높음(튜닝)|

### 개별 시트 구조:

```
A: CATEGORY
B: SUB_CATEGORY  
C: KEY
D: VALUE
E: DESCRIPTION
F: TAG (DANGER/STABLE/TUNABLE)
```

### 구조적 특징:

- **좌표 기반이 아닌 Key-Value 기반 구조**
    
- CATEGORY/SUB_CATEGORY는 **사람(운영자) 관리 목적**으로 유지
    
- 프로그램은 **KEY**를 유일 식별자로 사용
    
- TAG는 리스크 인지 및 운영 가이드 목적으로 사용
    
- value는 문자열이지만 Python 자동 변환(Type Casting) 사용
    
- description은 엔진 레벨 문서화를 대신함
    

### 예시 역할:

|Sheet|category|key|value|역할|
|---|---|---|---|---|
|Config_Local|risk|max_exposure_pct|40|전역 노출 한도|
|Config_Local|system|trading_enabled|TRUE|시스템 거래 허용|
|Config_Scalp|strategy|rsi_oversold|30|Scalp RSI 과매도 기준|
|Config_Scalp|risk|scalp_max_loss_pct|2|Scalp 단일 손실 한도|
|Config_Swing|strategy|pe_threshold|15|Swing PE 임계값|
|Config_Swing|risk|swing_max_positions|10|Swing 최대 보유 종목수|

---

## **3.1.3 Unified Config Resolution Flow**

전략 실행 시, Unified Config는 아래 순서로 구성된다.

```
Unified_Config(strategy) =
    Load(Config_Local)
  + Load(Config_{Strategy})   # Config_Scalp or Config_Swing
  + Load(Secrets)             # .env / env var
```

### Config Loading Flow:

```
Sheets (3개) → Schema Engine → Config Parser → Unified Config → Engines/Pipeline
```

### 우선순위 규칙:

1. **Secrets 최우선**
    
2. **Config_Local은 보호 영역**이며, 전략 시트가 이를 override 하지 못한다.
    
3. 전략 시트는 전략 내부에서만 유효하다. (Scalp ↔ Swing 교차 영향 없음)
    
### 충돌 규칙 (핵심):

- 동일 KEY가 `Config_Local`과 `Config_{Strategy}`에 동시에 존재할 경우:
    
    - **Config_Local 승**
        
    - 전략 시트 값은 무시된다.
        
- 동일 KEY가 `Config_Scalp`와 `Config_Swing`에 모두 존재할 수 있다:
    
    - 이는 정상이며 "공용(복제)" 정책의 결과다.
        
    - 두 값이 달라도 무방하며, 엔진은 자신의 전략 시트 값만 사용한다.
        
### Config Parser 역할:

- 3개 시트에서 key-value 읽기 및 병합
    
- 우선순위 규칙에 따른 충돌 해결
    
- 타입 변환(bool, int, float, list 등)
    
- Validation 수행 (Local 보호 규칙 검증)
    
- UnifiedConfig 객체 생성
    
- 전략별 엔진(ScalpEngine/SwingEngine)에 설정 주입
    

엔진은 고정 값이 아니라  
**Unified Config가 주입한 값에 따라 결정적(deterministic) 동작**을 수행한다.

---

# **3.2 Schema Automation Engine**

Schema Automation Engine은 QTS 전체의 “중추 신경계”이자  
가장 중요한 기술적 차별성이다.

시트 구조가 변해도 코드 수정 없이 자동 회복되는 구조를 만든다.

---

## **3.2.1 왜 필요한가?**

기존 자동매매 시스템의 가장 큰 문제:

- 컬럼 이동 → 코드 오류
    
- 열 추가/삭제 → 로직 붕괴
    
- 시트 구조 변경 → 재배포 필요
    

QTS는 이를 해결하기 위해  
“스키마가 데이터 변경을 흡수하는 구조”를 채택했다.

---

## **3.2.2 Schema Engine의 핵심 기능**

1. **시트 구조 자동 스캔**
    
2. **Header 기반 필드 정의 자동 생성**
    
3. **좌표 기반 매핑 제거**
    
4. **스키마 버전 관리 (schema_version)**
    
5. **엔진이 참조하는 정규화된 데이터 모델 생성**
    

### 스키마의 형태 (JSON 예시)

```
{
  "sheet_name": "T_Ledger",
  "row_start": 2,
  "columns": {
    "timestamp": "A",
    "symbol": "B",
    "qty": "E",
    ...
  }
}
```

Schema Engine은 **필드명 중심(Field-centric)** 구조로 모든 엔진을 동작시킨다.

---

## **3.2.3 Schema Flow Integration**

전체 흐름:

```
Sheets → Schema Scanner → Schema JSON → Data Contract Model → Engines
```

### Data Contract Model은:

- Strategy Engine의 입력값
    
- Risk Engine의 리스크 계산값
    
- Portfolio Engine의 잔고 계산값
    
- Performance Engine의 손익 분석값
    

모두의 기준이 된다.

---

## **3.2.4 Schema Engine의 핵심 철학**

1. **시트 변경은 장애 이벤트가 아니다 — 자연스러운 운영 이벤트다.**
    
2. **스키마가 엔진보다 먼저 실행된다.**
    
3. **엔진은 스키마를 모르면 단 1mm도 움직이지 않는다.**
    
4. **스키마 없이는 모든 연산이 금지된다.**
    

---

# **3.3 Logging & Monitoring Core**

Logging Layer는 QTS의 “블랙박스”이며  
Monitoring Layer는 시스템의 “대시보드”이다.

---

## **3.3.1 Logging Core**

Logging Core의 목표는 다음과 같다:

- 매매 결정 과정의 모든 단계 기록
    
- ETEDA 단계별 입력/출력 저장
    
- 예외 상황 및 에러 기록
    
- 주문/체결 내역의 실시간 로깅
    
- 전략 판단 기록 (신호의 왜/어떻게)
    

### 예시 로그 모델:

```
{
 "pipeline_step": "Evaluate",
 "strategy_signal": "BUY",
 "symbol": "AAPL",
 "reason": "RSI oversold",
 "timestamp": 1733994100
}
```

---

## **3.3.2 Monitoring Core**

Monitoring Core의 역할:

1. **위험 감지 (Risk Alerts)**
    
2. **비정상 동작 감지 (Anomaly Detection)**
    
3. **포트폴리오 급변 상황 경보**
    
4. **브로커 API 응답 지연 감지**
    
5. **Pipeline Failure 감지**
    

Monitoring Core는 UI Layer(R_Dash 등)와 연결되어  
문제를 실시간으로 보여주는 역할을 한다.

---

## **3.3.3 Fail-Safe Integration**

Fail-Safe Layer의 대표 기능:

- 매매 중단(Safe Mode) 자동 발동
    
- 주문 Lockdown
    
- 계좌 손실 방어 모드(Survival Mode)
    
- 파이프라인 재시작 시도
    
- 스키마 재로드 후 시스템 복구
    

Fail-Safe는 Engine Layer가 아니라  
**Core Layer**에 속하는 이유는 다음 때문이다:

**시스템 안정성은 전략보다 더 상위의 개념이기 때문이다.**

---

# **3.4 Core Layer Summary**

Core Layer는 아래와 같이 정리된다.

|구성 요소|목적|
|---|---|
|**Config Architecture**|시스템 제어 및 전역 파라미터 관리|
|**Schema Automation Engine**|시트 변화 흡수 & 데이터 계약 생성|
|**Logging Core**|모든 매매 의사결정 기록|
|**Monitoring Core**|실시간 시스템 상태 감시|
|**Fail-Safe**|시스템 안정성 확보 및 자동 복구|

Core Layer 없이는  
엔진, 파이프라인, UI, 브로커 확장 모두 불가능하다.

---

# **4. Data Layer 아키텍처**

Data Layer는 QTS의 모든 판단이 시작되는 출발점이다.  
전략, 리스크, 포트폴리오, 파이프라인, UI 모두  
이 레이어가 제공하는 **정규화된 데이터 모델(Data Contract)** 을 기반으로 동작한다.

QTS는 총 **11개 시트(데이터 소스)** 를  
단일 데이터 레이크(Data Lake)처럼 사용하며,  
Schema Automation Engine이 이 구조를 자동 분석하여  
하나의 통합 데이터 모델로 변환한다.

구성 요약:

- Google Spreadsheet 시트 10개
    - `Portfolio`, `Performance`, `R_Dash`, `Dividend`, `T_Ledger`, `History`, `Strategy`, `Position`, `Config_Swing`, `Config_Scalp`
        
- Repo에 포함되는 시트 1개
    - `Config_Local` (전역/보호 영역)

**현재 구현된 리포지토리:**
- `PositionRepository` - Position 시트
- `EnhancedPortfolioRepository` - 포트폴리오 집계
- `T_LedgerRepository` - T_Ledger 시트  
- `HistoryRepository` - History 시트
- `EnhancedPerformanceRepository` - 성과 집계

---

# **4.1 QTS 11-Sheet Data Layer**

11개의 시트는 각각 명확한 역할을 갖고 있으며  
서로 중복되는 책임이 없도록 설계되었다.

아래는 11-Sheet 구조의 전체 개념도다.

```
┌──────────┬────────────────────────────────────────────────────┐
│ Sheet    │ 역할                                               │
├──────────┼────────────────────────────────────────────────────┤
│ Config_Scalp │ Scalp 전략 튜닝 파라미터 (전략 전용)            │
│ Config_Swing │ Swing 전략 튜닝 파라미터 (전략 전용)            │
│ Config_Local │ 시스템 제어 · 전역 파라미터 (전략 불변, Repo)    │
│ Position │ 현재 보유 포지션                                   │
│ Strategy │ 전략 구성값 및 파라미터                              │
│ T_Ledger │ 실시간 거래 원장 (체결/주문 기록)                  │
│ History  │ 전략별 거래 히스토리                               │
│ Dividend │ 배당 데이터(결정 필요: 시트 유지 vs API 자동 수급)   │
│ Portfolio │ 포트폴리오 집계/상태                                │
│ Performance │ 성과/손익 집계                                    │
│ R_Dash   │ UI 대시보드 (Zero-Formula 표시용)                  │
└──────────┴────────────────────────────────────────────────────┘
```

**참고**: Config는 전략별 리스크 분리를 위해 3개의 시트(`Config_Local`, `Config_Scalp`, `Config_Swing`)로 분리되었다.  
이 중 `Config_Local`은 Repo에 포함되며, 나머지 2개는 Google Spreadsheet에 존재한다.

각 시트는 엔진이나 UI가 아니라  
**Schema Automation Engine의 입력값(Input Layer)** 이다.

---

## **4.1.1 시트별 역할**

### **1) Config 시트 (3분할 구조)**

**Config_Local (시스템 제어탑, Repo 포함)**:
시스템 운영 모드와 전역 파라미터를 관리한다. 전략에 의해 override 되지 않는 보호 영역이다.

예:
- trading_enabled
- max_exposure_pct
- kill_switch_enabled
- pipeline_interval_ms

**Config_Scalp (Scalp 전용)**:
Scalp 전략의 튜닝 파라미터를 관리한다. 단기·고회전 실행을 전제로 한다.

예:
- scalp_rsi_oversold
- scalp_max_loss_pct
- scalp_position_limit

**Config_Swing (Swing 전용)**:
Swing 전략의 튜닝 파라미터를 관리한다. 중장기·저회전 실행을 전제로 한다.

예:
- swing_pe_threshold
- swing_max_positions
- swing_sector_filter
    

### **2) Position (현재 포지션)**

현재 보유 종목, 수량, 단가, 평가 금액을 관리한다.

전략·리스크·포트폴리오 엔진의 공통 입력값이다.

### **3) T_Ledger (거래 원장)**

매수/매도 체결 정보  
→ 포트폴리오 엔진 / 성과 엔진이 참조함.

### **4) Dividend (배당 데이터)**

배당락일, 배당금, 배당률 등 분배 관련 데이터.

결정 필요:

1. **Dividend를 Google Spreadsheet 시트로 유지**
    - 운영자가 직접 수정/검증 가능
        
2. **Dividend를 API로 자동 수급**
    - API 수급 + 로컬/깃 캐시(버전 관리)로 운용

### **5) Portfolio / Performance**

Portfolio/Performance는 포트폴리오 상태와 성과/손익 집계를 저장한다.

### **6) History (전략별 거래 기록)**

전략 엔진의 판단과 실제 체결을 연결하는 기록.

### **7) Strategy (전략 파라미터)**

전략 이름, 기간 값, 임계값 등  
전략 엔진의 입력값.

### **8) R_Dash (UI 전용 Layer)**

Zero-Formula UI 구조를 위해  
Python이 계산한 정규화된 출력값만 저장.

---

# **4.2 Update Mode 아키텍처**

QTS Data Layer는 “업데이트 모드”를 통해 데이터 변화를 통제한다.

### Update Mode의 필요성

자동매매 시스템의 가장 큰 실패 요인 중 하나가  
“데이터가 언제/어떻게 업데이트되는지 모른다는 점”이다.

이를 해결하기 위해 QTS는 다음 두 가지 구조를 채택한다:

1. **Manual Update Mode (사용자 갱신)**
    
2. **Auto Update Mode (자동 갱신)**
    

---

## **4.2.1 Manual Update Mode**

사용자가 아래 작업을 직접 수행하는 경우:

- 전략 파라미터 변경
    
- Config 값 변경
    
- 배당 DB 입력
    
- 종목정보 변경
    

Manual Mode는 엔진보다 우선 적용되며,  
Schema Engine은 변경된 시트 구조를 즉시 다시 분석한다.

---

## **4.2.2 Auto Update Mode**

Auto Mode는 Python이 자동으로 시트를 업데이트하는 모드다.

자동 업데이트는 다음 단계에서 발생한다:

- 체결 → Position 업데이트
    
- 손익 계산 → Performance 업데이트
    
- 전략 판단 → History 기록
    
- Pipeline 실행 → R_Dash 업데이트
    

Auto Mode가 작동하는 원칙:

1. **엔진은 직접 시트에 접근하지 않는다.**
    
2. **모든 기록은 Data Contract에 의해 생성된다.**
    
3. **Schema Engine이 필드를 제공한 범위 안에서만 작성 가능하다.**
    

---

## **4.2.3 Mode Integrity Rules**

Update Mode는 QTS 운영 안전성의 핵심이므로  
다음 원칙이 깨지면 Fail-Safe 모드가 작동한다.

1. Data Layer는 오직 Schema Engine을 통해서만 접근 가능
    
2. Update Mode의 흐름이 깨지면 자동 중단
    
3. 수동/자동 업데이트가 충돌하면 중단 후 재동기화 수행
    

---

# **4.3 Data Contracts (Python 계산식 포함)**

Data Contract는 엔진이 사용하는  
**정규화된 데이터 모델의 형태**다.

Data Contract는 두 부분으로 구성된다.

1. **RawData Contract**  
    Schema Engine이 시트에서 추출한 원천 데이터
    
2. **CalcData Contract**  
    Python 엔진이 만든 계산 필드(derived data)
    

---

## **4.3.1 RawData Contract Structure**

예: Position Raw Contract

```
{
 "symbol": "AAPL",
 "qty": 10,
 "avg_price": 158.30,
 "market": "NASDAQ",
 "exposure_usd": 1583.0
}
```

---

## **4.3.2 CalcData Contract Structure**

Python이 만들어내는 계산식 예시:

### Exposure%

```
exposure_pct = (position_value / total_equity) * 100
```

### Unrealized PnL

```
unrealized_pnl = (current_price - avg_price) * qty
```

### Buy/Sell Signal Normalization

```
normalized_signal = 1 if strategy_signal == "BUY" else -1
```

---

## **4.3.3 Contract Integrity Rules**

1. RawData는 시트에서만 온다.
    
2. CalcData는 Python에서만 계산된다.
    
3. Contract는 엔진 간 공유되는 단일 기준이다.
    
4. Contract가 변하면 엔진도 반드시 재검증되어야 한다.
    

---

# **4.4 Dividend 데이터 소스 아키텍처**

배당 데이터는 운용 안정성과 정합성이 중요한 데이터이며, 운영 방식에 따라 데이터 소스 전략이 달라질 수 있다.

결정 필요:

1. **Dividend를 Google Spreadsheet 시트로 유지**
    - 운영자가 직접 수정/검증
        
2. **Dividend를 API로 자동 수급**
    - API 수급 + 로컬/깃 캐시(버전 관리) 조합

---

## **4.4.1 Local Dividend DB**

로컬 디렉토리 저장 (예: `/data/dividend/dividend.json`)

특징:

- 빠른 접근
    
- 즉시 변경 가능
    
- 자동 업데이트 가능
    
- 단일 파일로 가벼운 구조
    

예시:

```
{
 "AAPL": [
   {"ex_date": "2024-02-10", "dividend": 0.24},
   {"ex_date": "2024-05-10", "dividend": 0.24}
 ]
}
```

---

## **4.4.2 Git Dividend DB**

Git으로 관리되는 장기 보관 버전.

특징:

- 배당 데이터의 변경 이력 확인
    
- 다중 기기 간 최신 배포
    
- 회귀 분석 시 과거 배당 데이터 복원 가능
    

Git DB는 운영 환경 배포 시 “기준 데이터셋”으로 사용된다.

---

## **4.4.3 Dividend Flow**

```
Git DB → Local DB → Schema Engine → Dividend Contract → Engines
```

엔진은 배당 Contract만 읽는다.  
시트나 Git 구조는 엔진에 영향을 주지 않는다.

---

# **4.5 Data Layer 요약**

|구성 요소|목적|
|---|---|
|11-Sheet Layer|모든 원천 데이터(구글 스프레드시트 10 + 레포 1)|
|Update Mode 아키텍처|데이터 갱신 통제|
|Data Contract|엔진 입력 기준|
|Dividend 데이터 소스|배당 데이터 공급 및 버전 관리(정책 선택)|

Data Layer는 QTS 전체의 출발점이며  
스키마와 엔진의 기반이 되는 단일 진실의 원천(SSoT)이다.

---

# **5. Engine Layer 아키텍처**

Engine Layer는 QTS의 “두뇌(BRAIN)”에 해당한다.  
모든 판단·승인·계산·실행은 이 계층에서 이루어진다.

QTS 엔진 구조는 전략별 분리를 위해 다음과 같이 구성된다.

**핵심 엔진 (공통)**:
1. Trading Engine
    
2. Risk Engine
    
3. Portfolio Engine
    
4. Performance Engine
    
**전략별 엔진 (2개)**:
5. ScalpEngine (단기·고회전 전용)
    
6. SwingEngine (중장기·저회전 전용)
    
각 엔진은 독립적으로 설계되지만  
**Data Contract → Engine → Pipeline → Broker** 구조를 통해 서로 연결되어  
ETEDA 파이프라인 촉매 역할을 수행한다.

**엔진-시트 1:1 대응**:
- ScalpEngine은 `Config_Local + Config_Scalp (+ Secrets)`를 입력으로 받는다.
- SwingEngine은 `Config_Local + Config_Swing (+ Secrets)`를 입력으로 받는다.

---

# **5.1 ScalpEngine**

ScalpEngine은 QTS의 "단기 판단자(Short-term Decision Maker)"다.  
단기·고회전 매매를 전제로 하며, 기술적 지표와 신호 기반의 빠른 진입/청산 판단을 수행한다.

---

## **5.1.1 역할**

- 기술적 지표 기반 신호 계산 (RSI, MACD, 볼린저 등)
    
- 단기 변동성 기반 진입/청산 시그널 생성
    
- 시간 기반 청산 로직 (타임아웃)
    
- 단건 손실 제어 및 변동성 제한
    
- 최대 포지션 수 및 단건 비중 제한
    
- Config_Scalp 파라미터 반영
    

---

## **5.1.2 입력 / 출력**

입력:

- 가격/종목 정보(브로커/데이터 피드)
    
- Position(현재 보유 상태)
    
- Config_Scalp(Scalp 전용 튜닝 파라미터)
    
- Config_Local(전역 파라미터, 우선 적용)
    
- 실시간 시계열 데이터(필요 시)
    

출력:

- scalp_signal (BUY/SELL/NEUTRAL)
    
- recommended_qty (Scalp 기준)
    
- confidence (선택적)
    
- reason (신호 발생 이유)
    

---

## **5.1.3 ScalpEngine 핵심 알고리즘**

1. 실시간 데이터 수신
    
2. 기술적 지표 계산 (RSI, MACD 등)
    
3. Config_Scalp 기반 신호 생성
    
4. 변동성 및 손실 한도 체크
    
5. 시간 기반 청산 조건 확인
    
6. 최종 신호 결정
    
7. Trading Engine으로 전달
    

Pseudo-code 예시:

```
if risk_approval == True:
    order = build_order(strategy_signal, qty, price)
    execution = broker.send(order)
    t_ledger.record(execution)
```

---

# **5.2 SwingEngine**

SwingEngine은 QTS의 "중장기 판단자(Medium-to-long-term Decision Maker)"다.  
중장기·저회전 매매를 전제로 하며, 펀더멘털/밸류에이션 기반의 신중한 진입/청산 판단을 수행한다.

---

## **5.2.1 역할**

- 펀더멘털/밸류에이션 기반 분석 (P/E, P/B, 배당률 등)
    
- 시장/섹터/종목 필터링
    
- 중장기 추세 기반 신호 생성
    
- 포트폴리오 레벨 리스크 모니터링 (DD/변동성 경계)
    
- 편입 수/비중/랭킹 기반 포트폴리오 구성
    
- Config_Swing 파라미터 반영
    
---

## **5.2.2 입력 / 출력**

입력:

- 가격/종목 정보(브로커/데이터 피드)
    
- Position(현재 보유 상태)
    
- Config_Swing(Swing 전용 튜닝 파라미터)
    
- Config_Local(전역 파라미터, 우선 적용)
    
- History Sheet(과거 거래 히스토리, 필요 시)
    

출력:

- swing_signal (BUY/SELL/NEUTRAL)
    
- recommended_qty (Swing 기준)
    
- confidence (선택적)
    
- reason (신호 발생 이유)
    
---

## **5.2.3 SwingEngine 핵심 알고리즘**

1. 종목 스크리닝 및 필터링
    
2. 펀더멘털/밸류에이션 분석
    
3. Config_Swing 기반 신호 생성
    
4. 포트폴리오 레벨 리스크 체크
    
5. 랭킹/선별 기반 종목 선택
    
6. 최종 신호 결정
    
7. Trading Engine으로 전달

---

# **5.3 Trading Engine**

Trading Engine은 QTS의 "실행자(Executor)"다.  
ScalpEngine/SwingEngine에서 전달된 의사결정을 받고  
이를 실제 주문으로 변환하여 브로커에 전달한다.

---

## **5.3.1 역할**

- 매수/매도 주문 생성
    
- 주문량 계산
    
- 주문 유형(지정가/시장가 등) 적용
    
- 브로커 API 호출
    
- 응답 처리 및 T_Ledger 기록
    
- 실패 시 재시도 로직 적용
    
- Fail-Safe 조건 충족 시 주문 중단(Lockdown)
    

Trading Engine은 "생각"하지 않는다.  
오직 **실행**한다.

---

## **5.3.2 Input / Output (Data Contract 기준)**

Input:

- strategy_signal (ScalpEngine 또는 SwingEngine에서 전달)
    
- risk_approval
    
- portfolio_size_recommendation
    
- price / qty
    
- exposure limit
    

Output:

- 주문 요청(OrderRequest)
    
- 체결 결과(ExecutionReport)
    
- T_Ledger 기록
    

---

## **5.3.3 Trading Engine 핵심 알고리즘**

1. 전략 신호 수신
    
2. 리스크 승인 여부 확인
    
3. 포트폴리오 기준 주문량 결정
    
4. 주문 생성
    
5. 브로커 전송
    
6. 체결 결과 기록
    
7. 포지션 갱신 트리거

---

# **5.4 Risk Engine**

Risk Engine은 “안전 승인(Safety Approver)” 역할을 한다.  
전략 신호가 있어도 리스크에서 허용하지 않으면 주문은 실행되지 않는다.

---

## **5.4.1 역할**

- 포지션 노출도 계산
    
- 현재 계좌 위험도 계산
    
- 공매도 가능 여부 판단(브로커 옵션 기반)
    
- 최대 주문량 제한
    
- 일손실/일익절 조건 감시
    
- 전략별 MaxDrawdown 제한 감시
    

---

## **5.4.2 입력 / 출력**

입력:

- Position Data Contract
    
- Strategy Decision
    
- Exposure Limits
    
- Config Risk Params
    
- 브로커/시장 메타 데이터(거래 단위/최소 단위)
    

출력:

- risk_approval (True/False)
    
- allowed_qty
    
- risk_reason
    

---

## **5.3.3 핵심 계산식 예시**

### Maximum Exposure Check

```
if exposure_pct(symbol) > config.max_exposure_pct:
    return False
```

### Daily Loss Limit Check

```
if daily_pnl < -config.max_daily_loss:
    return False
```

Risk Engine은 “가장 보수적인 판단이 우선”이다.

---

# **5.4 Portfolio Engine**

Portfolio Engine은 QTS의 “자산 관리자(Allocator)”다.  
현재 보유 상태, 노출도, 목표 비중 등을 계산해  
주문량에 영향을 주는 핵심 정보를 제공한다.

---

## **5.4.1 역할**

- 현재 포지션 계산
    
- 종목별/전체 노출 계산
    
- 보유 비중 분석
    
- 목표 포트폴리오 비중 계산
    
- 주문량 추천
    

---

## **5.4.2 Portfolio Size Algorithm**

예시:

```
target_value = total_equity * target_weight(symbol)
current_value = price * qty
recommended_qty = (target_value - current_value) / price
```

Portfolio Engine의 출력은 Trading Engine의 “입력”이 된다.

---

# **5.5 Performance Engine**

Performance Engine은 QTS의 “기록자(Reporter)” 역할이다.  
성과, 손익, 효율성 지표를 정리해서  
Performance와 UI(R_Dash)에 전달한다.

---

## **5.5.1 역할**

- 매매별 손익 기록
    
- 일별 손익 및 누적 손익 계산
    
- 전략 성과 분석
    
- MDD, CAGR, WinRate 등 지표 계산
    
- Performance Report 생성
    

---

## **5.5.2 입력 / 출력**

입력:

- T_Ledger
    
- Position
    
- Dividend
    
- Portfolio
    
- Performance
    

출력:

- PnL Summary
    
- Performance 업데이트
    
- Strategy Performance Report
    
- Dashboard Indicators
    

---

# **5.6 Engine Interactions**

엔진 간 연결은 아래와 같이 흐른다:

```
Strategy → Risk → Portfolio → Trading → Performance
```

단계별 역할:

- Strategy: 판단
    
- Risk: 승인
    
- Portfolio: 수량 조정
    
- Trading: 실행
    
- Performance: 결과 기록
    

이 구조는 ETEDA Pipeline에서 자동 순환된다.

---

# **5.7 Engine Layer 요약**

|엔진|역할|
|---|---|
|Trading|주문 실행|
|Strategy|신호 결정|
|Risk|승인/거부|
|Portfolio|포지션 및 수량 계산|
|Performance|보고서 생성|

Engine Layer는 QTS의 가장 중요한 “업무 판단 계층”이며  
Pipeline Layer와 결합하여 자동매매를 완성한다.

---

# **6. 실행 파이프라인 아키텍처(ETEDA)**

QTS의 자동매매는 **파이프라인(Pipeline)** 개념을 기반으로 설계된다.  
즉, 한 번의 매매는 “신호 → 승인 → 계산 → 실행 → 기록”이라는 연속적 흐름이며  
이 흐름이 깨지지 않도록 통제하는 구조가 필요하다.

이를 위해 QTS는 고정된 5단계 프로세스, **ETEDA Pipeline**을 채택한다.

**E → T → E → D → A  
Extract → Transform → Evaluate → Decide → Act**

이 파이프라인은 엔진, 데이터, 브로커가 뒤섞이지 않도록  
절차적 순서(Procedural Flow)를 강제하며  
시스템 안정성을 담보하는 핵심 아키텍처다.

---

# **6.1 ETEDA 채택 배경**

실전 트레이딩 환경에서 가장 위험한 상황은 다음과 같다:

- 전략 신호만 보고 리스크 검증 없이 실행
    
- 포지션 계산 이전에 주문량이 잘못 들어감
    
- 브로커 장애 시 파이프라인이 망가짐
    
- 일부 단계만 건너뛰어 비정상 매매가 발생
    
- 데이터 불일치(Data Inconsistency) 상태에서 매매 실행
    

QTS는 이를 방지하기 위해  
“단계를 건너뛰는 것을 절대 허용하지 않는 구조”를 설계했다.

각 단계는 독립적이며,  
어떤 단계가 실패하면 전체 파이프라인은 중단된다.

---

# **6.2 ETEDA 5단계 상세 구조**

ETEDA는 아래와 같은 5가지 단계로 구성된다.

```
1. Extract(추출)
2. Transform(변환)
3. Evaluate(평가)
4. Decide(결정)
5. Act(실행)
```

각 단계의 목적은 다음과 같다.

---

## **6.2.1 1단계: 데이터 추출(Extract)**

Extract 단계는 Data Layer의 원천 데이터들을 스키마 기반으로 읽어와  
RawData Contract로 변환하는 단계다.

입력:

- 구글 스프레드시트 시트 10개
    
- 레포 시트 1개(`Config_Local`)
    
- Dividend 데이터 소스(시트 또는 API/캐시)
    
- Broker 계좌 상태(Optional)
    

출력:

- RawDataContract(Position, Strategy, T_Ledger, Config, Portfolio, Performance, Dividend, History, R_Dash…)
    

주요 원칙:

1. 스키마 엔진이 제공한 필드 외 접근 금지
    
2. 데이터 불일치 탐지 시 Fail-Safe로 즉시 전환
    
3. UI(R_Dash)는 Extract 단계에 영향을 주지 않는다
    

Extract는 “정확한 데이터 확보”에 100% 집중하는 단계다.

---

## **6.2.2 Step 2: Transform (정규화 및 계산)**

Transform 단계는 RawData를  
엔진이 사용할 수 있는 CalcData Contract로 변환하는 단계다.

주요 작업:

- 노출도 계산
    
- 계좌 평가금 계산
    
- 전략 입력값 정규화
    
- 포트폴리오 비중 계산
    
- 가격/변동성 조정
    
- 배당 영향 계산
    

출력:

- CalcDataContract(Exposure, PnL, TargetWeight, etc.)
    

Transform 단계는 "계산" 중심이며  
"판단"이 포함되면 안 된다.

---

## **6.2.3 Step 3: Evaluate (엔진 평가 단계)**

Evaluate 단계에서는 엔진 계층이 동작한다.

이 순서가 고정이다:

1. Strategy Engine → 신호 계산
    
2. Risk Engine → 승인/거부
    
3. Portfolio Engine → 주문량 조정
    
4. 결과를 하나의 EvaluationResult 형태로 통합
    

출력:

- EvaluationResult(signal, risk_approval, recommended_qty, reason)
    

핵심 원칙:

- Strategy Engine이 없다면 어떤 판단도 해서는 안 된다.
    
- Risk Engine이 거부하면 매매는 절대 실행되지 않는다.
    
- Portfolio Engine은 계산만 수행, 결정은 하지 않는다.
    

Evaluate는 “판단”의 단계다.

---

## **6.2.4 Step 4: Decide (결정)**

Decide 단계는 파이프라인의 최종 결정을 내린다.

입력:

- EvaluationResult
    
- Config 운영 모드
    
- Safety Layer 상태
    

계산:

- 주문 여부 결정
    
- 주문 유형 결정
    
- 시장 상황 체크
    
- Fail-Safe 조건 검증
    
- 브로커 가능 여부 판단
    

출력:

- OrderDecision(buy/sell/none, qty, price, reason)
    

핵심 원칙:

- Decide 단계는 "Yes/No"를 결정하는 최종 관문이다.
    
- Config에서 trading_enabled=False인 경우 항상 "none"
    
- Safety Layer가 활성화되면 주문은 자동 차단
    

---

## **6.2.5 Step 5: Act (실행)**

Act 단계는 Trading Engine이 브로커와 통신하는 단계다.

작업:

1. 주문 생성
    
2. 한국투자증권 API 전송
    
3. 응답 기록
    
4. 실패 시 재시도
    
5. T_Ledger 기록 업데이트
    
6. 포지션 업데이트 트리거 발생
    

출력:

- ExecutionReport
    
- Updated Position
    
- Updated T_Ledger
    

Act 단계는 시스템에서 “유일하게 실거래가 발생하는 단계”다.

---

# **6.3 ETEDA Flow Diagram (Text Concept)**

```
[Extract]
   ↓
[Transform]
   ↓
[Evaluate]
   ↓
[Decide]
   ↓
[Act]
```

주요 제약:

- 어떤 단계도 건너뛸 수 없다
    
- 출력이 없으면 다음 단계로 이동 불가
    
- 실패 시 Fail-Safe로 분기
    
- 실행 완료 후 Extract로 되돌아가 “루프”를 형성
    

---

# **6.4 Pipeline Error Handling & Fail-Safe Trigger**

ETEDA Pipeline은 “의도한 순서가 깨지는 것”을  
가장 큰 위험 요소로 판단한다.

따라서 아래 상황에서는 즉시 Fail-Safe를 발동한다.

1. Extract 실패 → 데이터 불일치
    
2. Transform 실패 → 계산 오류
    
3. Evaluate 실패 → 전략/리스크/포트폴리오 오류
    
4. Decide 실패 → 주문 불가
    
5. Act 실패 → 브로커 장애
    

Fail-Safe 발동 시의 절차:

```
1. 모든 주문 중단
2. trading_enabled=False 강제
3. 경보 표시 (Monitoring Layer)
4. 사용자 승인 전까지 ETEDA 재개 금지
```

---

# **6.5 Multi-Cycle Pipeline**

ETEDA는 1회 실행 후 종료되는 것이 아니라  
다음 형태로 지속적으로 반복된다:

```
while system_running:
    run_ETEDA()
    sleep(interval_ms)
```

interval_ms는 Config에서 제어한다.  
브로커 트래픽 제한, 전략 업데이트 주기, API 응답 성능 등을 고려하여  
동적으로 조절 가능하다.

---

# **6.6 ETEDA & Engine Interaction**

엔진의 동작은 ETEDA 단계에 정확히 매핑된다.

|ETEDA 단계|엔진 동작|
|---|---|
|Extract|없음(데이터 확보)|
|Transform|Portfolio/Performance 계산 일부|
|Evaluate|Strategy → Risk → Portfolio|
|Decide|Trading Engine 준비·결정|
|Act|Trading Engine 실행|

즉, ETEDA는 엔진을 감싸고 통제하는 상위 레이어다.

---

# **6.7 ETEDA Summary**

|단계|목적|핵심|
|---|---|---|
|Extract|데이터 확보|RawDataContract 생성|
|Transform|계산|CalcDataContract 생성|
|Evaluate|판단|엔진 평가 수행|
|Decide|최종 결정|주문 여부 결정|
|Act|실행|브로커 통신|

ETEDA는 QTS 자동매매의 **심장(Heart)** 으로  
하나라도 빠지면 시스템은 정상 동작할 수 없다.

---

# **7. Sheets/UI Layer Architecture**

QTS의 UI Layer는 Google Sheets를 활용하지만,  
일반적인 스프레드시트와는 전혀 다른 방식으로 사용된다.

전통적인 스프레드시트 기반 시스템이 가진 문제점들:

- 공식이 흐름을 방해하고 디버깅이 어려움
    
- 계산 중복, 데이터 불일치
    
- 구조 변경 시 오류 다발
    
- 시트마다 다른 계산식이 숨어 관리 난이도 증가
    

QTS는 이 문제를 원천 차단하기 위해 다음 철학을 채택한다.

**Sheets는 계산하지 않는다.  
오직 Python이 계산한다.  
Sheets는 보여주기만 한다.**

이를 **Zero-Formula UI Architecture**라 부른다.

---

# **7.1 Zero Formula UI Structure**

Zero-Formula 원칙을 실현하기 위해  
UI Layer는 아래 세 가지 기준을 따른다:

1. **Sheets에는 어떤 계산식도 존재하지 않는다. (100% 제거)**
    
2. **모든 계산은 Python Engine에서 수행된다.**
    
3. **Sheets는 “렌더링 타겟(Rendering Target)” 역할만 한다.**
    

---

## **7.1.1 Zero Formula의 주요 이점**

- 구조 변경 시 엔진 영향 없음
    
- 디버깅·테스트 용이성 극대화
    
- UI 변경이 시스템 안정성을 해치지 않음
    
- 전략/리스크 계산이 UI에 의존하지 않음
    
- Renderer 파이프라인 구축이 용이함
    

---

## **7.1.2 R_Dash Sheet의 역할**

UI 레이어에서 가장 중요한 시트는 **R_Dash**다.  
이 시트는 다음 역할을 담당한다:

- 대시보드 표시
    
- 핵심 지표 렌더링
    
- 엔진 출력값 시각화
    
- 시스템 상태 모니터링
    
- Fail-Safe 상태 표시
    

### 예시 필드:

- Equity
    
- Daily PnL
    
- Exposure %
    
- Strategy Signal
    
- Risk Status
    
- Current Position Summary
    
- System Status (RUNNING / SAFE MODE)
    

R_Dash는 “빌드된 데이터”만 받으며  
어떤 계산도 하지 않는다.

---

# **7.2 Dashboard Block Architecture**

QTS UI는 “Block-Based Dashboard”의 형태를 따른다.  
이 구조는 시각적 모듈을 조합해 원하는 대시보드를 빠르게 구성할 수 있게 한다.

Block 단위 구성 요소 예:

1. **PnL Block**
    
    - Today PnL
        
    - Cumulative PnL
        
2. **Position Block**
    
    - 종목별 노출
        
    - 평가금
        
    - 비중
        
3. **Strategy Block**
    
    - 현재 전략 신호
        
    - Confidence
        
    - 이유(Explanation)
        
4. **Risk Block**
    
    - 노출 위험도
        
    - 주문 승인 상태
        
    - Fail-Safe Trigger
        
5. **System Block**
    
    - Pipeline 상태
        
    - Update Mode
        
    - Broker 연결 상태
        
6. **Performance Block**
    
    - 전략 성과 분석
        
    - 분기별 손익 흐름
        

---

## **7.2.1 Block Rendering Rules**

모든 UI Block는 다음 규칙을 따른다.

1. **Block은 Engine 출력값을 기반으로 한다**
    
2. **Block 간 계산은 존재하지 않는다**
    
3. **Block 간 의존성 없음**
    
4. **Block 추가/제거해도 시스템은 영향받지 않는다**
    
5. **Block은 Python이 완성된 데이터를 전달한 후 표시된다**
    

---

## **7.2.2 Rendering Flow**

Rendering Flow는 다음처럼 정해진 구조로 진행된다.

```
Engine Output  
    ↓  
Renderer (Python)  
    ↓  
UI Contract  
    ↓  
Sheets(R_Dash)
```

UI Contract는 아래 형태를 따른다:

```
{
 "equity": 12800450,
 "daily_pnl": 45000,
 "strategy_signal": "BUY",
 "current_exposure_pct": 31.2,
 "system_status": "RUNNING"
}
```

Sheets는 이 Contract를 단순히 표시한다.

---

# **7.3 UI Rendering Flow**

UI Rendering은 ETEDA Pipeline의 일부로 동작하지 않는다.  
즉, 시스템의 매매 흐름과 UI는 완전히 분리되어 있다.

### 분리 목적:

- UI 오류가 매매에 영향을 주지 않게 하기 위해
    
- ETEDA 파이프라인은 100% 엔진 기준으로만 동작
    

UI Rendering은 별도 프로세스로 설계된다.

---

## **7.3.1 Rendering 주기 (Schedule)**

Rendering은 일반적으로 다음 타이밍에 실행된다:

- ETEDA 파이프라인 종료 후
    
- Config에서 설정한 interval 이후
    
- 사용자가 수동 요청했을 때
    

Rendering 주기는 매매 주기와 다를 수 있다.

예:

- ETEDA: 5초
    
- UI Rendering: 10초
    

이렇게 설계하여 UI 최소화로 시스템 부하를 줄인다.

---

## **7.3.2 Rendering Pipe Steps**

Rendering 프로세스는 아래 흐름으로 실행된다:

1. Engine Output 수집
    
2. UI Contract 생성
    
3. R_Dash 필드 매핑
    
4. Google Sheet 업데이트
    
5. Block별 색상/포맷팅 적용(Optional)
    

---

## **7.3.3 Error Isolation**

UI Rendering 중 오류가 발생해도:

- ETEDA는 중단되지 않는다
    
- 시스템 상태는 영향받지 않는다
    
- Fail-Safe는 발동하지 않는다
    
- Rendering만 잠시 중단될 뿐
    

UI는 “보조 계층”임을 강조한다.

---

# **7.4 Why Sheet-Based UI? (설계 이유)**

엔터프라이즈급 자동매매 시스템에서 UI는 문제를 일으키기 쉽다.  
그러나 Sheets 기반 UI는 다음과 같은 강력한 장점이 있다.

1. **접근성 → 로컬/모바일/원격 접근 가능**
    
2. **빠른 업데이트 → 즉시 반영**
    
3. **시각적 관리 용이**
    
4. **개발 비용 최소화**
    
5. **Python과 연동 쉬움**
    
6. **Logger/Monitoring Layer와 결합하기 좋음**
    

특히 Sheets는 “데이터 대시보드” 역할로는 매우 강력한 플랫폼이다.

---

# **7.5 UI Layer Summary**

|구성 요소|목적|
|---|---|
|Zero-Formula Architecture|UI 오류 방지|
|R_Dash Sheet|대시보드|
|Block Architecture|유연한 UI 구성|
|Rendering Flow|UI–Engine 분리|
|UI Contract|데이터 전달 표준화|

UI Layer는 QTS의 안정성을 해치지 않는 방식으로 설계된 “표현 계층”이며  
엔진·파이프라인 레이어와 완전히 독립적으로 작동한다.

---

# **8. Safety Layer Architecture**

Safety Layer는 QTS 자동매매 시스템의 **마지막 방어선(Last Line of Defense)** 이다.  
전략, 엔진, 데이터가 정상적으로 동작하더라도  
시장·데이터·브로커·시트·네트워크 문제로 인해 오류가 발생할 수 있으며,  
Safety Layer는 이런 상황에서 시스템을 보호하고 자동 복구를 돕는다.

QTS의 Safety Layer는 단일 기능이 아니라  
아래 네 가지 요소가 결합된 종합적 안정성 인프라이다.

1. Fail-Safe Mechanism
    
2. Guardrail Constraints
    
3. Anomaly Detection System
    
4. Execution Lockdown Layer
    
5. Safe Mode Architecture
    

QTS는 설계 철학상 “잘못된 매매를 하는 시스템”이 아니라  
“문제가 발생하면 멈추는 시스템”이다.

---

# **8.1 Safety Layer Overview**

Safety Layer는 다음 시나리오에서 동작한다:

- 데이터 손상 / 누락 / 비정상 값
    
- 전략 엔진 오류
    
- 리스크 엔진 계산 불가
    
- 포트폴리오 계산 실패
    
- 브로커 API 지연/오류
    
- ETEDA 파이프라인 일부 단계 실패
    
- 비정상 주문 발생 가능성 감지
    
- 시트 구조 변경 감지
    

핵심 개념:

**매매 중단은 손실보다 작다.**

---

# **8.2 Fail-Safe Mechanism**

Fail-Safe는 QTS 안전 구조의 중심이다.  
시스템이 다음 중 하나라도 감지하면 즉시 Fail-Safe를 발동한다.

### 발동 조건

1. Extract 단계 데이터 불일치
    
2. Transform 단계 계산 실패
    
3. Evaluate 단계 엔진 오류
    
4. Decide 단계에서 주문 조건 위반
    
5. Act 단계 브로커 통신 실패
    
6. 포지션 음수/이상치 발생
    
7. Exposure 값 비정상
    
8. Config 모드 충돌
    
9. Schema Version 불일치
    
10. UI Contract 파싱 오류(중요하진 않지만 비정상 데이터는 감지)
    

Fail-Safe 발동 순간 수행되는 작업:

```
1. trading_enabled = FALSE 강제 설정
2. 모든 주문 중단
3. Execution Lock 활성화
4. R_Dash에 FAIL 상태 전송
5. 로그에 장애 원인 기록
6. 사용자 수동 승인 전까지 매매 재개 불가
```

Fail-Safe는 설계상 “절대 자동으로 풀리지 않는다”.  
반드시 **사용자 수동 해제**가 필요하다.

---

# **8.3 Guardrail Constraints (보호 장벽)**

Guardrail은 시스템이 위험한 행동을 하지 못하도록 예방하는 구조이다.  
Fail-Safe가 “사고 후 중단”이라면  
Guardrail은 “사고 전 차단”에 가깝다.

### QTS Guardrail 종류

#### 1) 주문량 제한

```
if recommended_qty > max_order_qty:
    block_order()
```

#### 2) 최대 노출 제한

```
if exposure_pct > config.max_exposure_pct:
    block_order()
```

#### 3) 전략 신호 무효화

- 최근 변동성 급등
    
- 특정 시간대 비활성화
    
- 거래량 부족 시 진입 금지
    

#### 4) 브로커 잔고 불일치 보호

- 포지션과 계좌 잔고가 불일치하면 매매 중단
    

#### 5) 시장 휴장/점검 시간 보호

Guardrail은 Fail-Safe보다 “먼저” 작동한다.

---

# **8.4 Anomaly Detection System**

Anomaly Detection은 데이터 이상치를 실시간으로 감지하는 시스템이다.  
다음과 같은 비정상 상태를 탐지하면 이벤트를 발생시킨다.

### 감지 대상

1. 가격 급변 (> 일정 임계값)
    
2. 누락된 데이터(Null / NaN / 빈 배열)
    
3. 음수 노출도
    
4. 평균단가 계산 불가
    
5. T_Ledger 누락 정보
    
6. Strategy 신호 반복 오류
    
7. Risk Engine 승인/거부 응답 불일치
    

Anomaly Detection은 즉시 매매를 중단하지는 않지만  
Fail-Safe Trigger로 연결될 수 있다.

### 구조

```
Data → Pre-Check → Anomaly Rules → Alert / Fail-Safe
```

경고(Warning)는 UI에 표시되고,  
치명적 오류(Critical)는 Fail-Safe로 전환된다.

---

# **8.5 Execution Lockdown Layer**

Execution Lockdown은 다음 상황에서 자동으로 활성화된다:

- Fail-Safe 발동
    
- Guardrail이 여러 번 연속 동작
    
- 브로커 응답 불량 3회 이상
    
- Config 충돌 감지
    
- 데이터 불일치 반복 발생
    

Lockdown 상태에서는 다음이 차단된다:

- 모든 주문
    
- 전략 신호 전달
    
- 파이프라인 Act 단계
    
- 일부 Evaluate 단계
    

### Lockdown Flow

```
Failure Detected → Lockdown ON → trading_enabled=FALSE → Act 단계 중단
```

Lockdown은 사용자 재승인 후 해제된다.

---

# **8.6 Safe Mode Architecture**

Safe Mode는 QTS의 “비상 운영 모드(Emergency Mode)”이다.

아래 상황에서 Safe Mode가 자동 또는 수동으로 활성화될 수 있다:

- 높은 변동성
    
- 브로커 검증 필요
    
- 전략 변경 중
    
- 시트 점검 중
    
- 시장 개장 직후(Option)
    

Safe Mode는 완전 중단이 아닌, “위험 최소화 모드”이다.

### Safe Mode 동작 원칙

1. **매매는 중단되지만 시스템은 계속 모니터링**
    
2. **데이터는 수집되며 리스크 체크는 가능**
    
3. **ETEDA에서 Act 단계만 제외하고 실행 가능 (옵션)**
    
4. **전략/Config 조정 시간 확보**
    

Safe Mode는 Fail-Safe와 달리  
중단이 아니라 “절반 작동(Half-Run)” 모드라고 보면 된다.

---

# **8.7 Safety Layer Integration with ETEDA**

ETEDA Pipeline과 Safety Layer의 관계는 다음과 같다.

|ETEDA 단계|Safety Layer 검사|
|---|---|
|Extract|데이터 불일치 검사|
|Transform|계산 오류 검사|
|Evaluate|전략/리스크/포트폴리오 이상치 검사|
|Decide|Guardrail 적용, Safe Mode 체크|
|Act|Fail-Safe/Lockdown 적용|

즉, 모든 단계에서 Safety Layer가 작동하며  
조금이라도 위험 신호가 감지되면 즉시 중단된다.

---

# **8.8 Safety Layer Summary**

|구성 요소|기능|
|---|---|
|Fail-Safe|치명적 오류 때 시스템 즉시 중단|
|Guardrail|위험 행동 사전 차단|
|Anomaly Detection|비정상 데이터 탐지|
|Lockdown Layer|주문 실행 완전 차단|
|Safe Mode|비상 운영 모드|

QTS Safety Layer는 단순한 안전장치가 아니라  
전략·엔진·데이터·파이프라인 전체를 보호하는  
통합 안정성 인프라이다.

---

# **9. Multi-Broker Architecture**

QTS의 Multi-Broker Architecture는  
**브로커가 시스템의 중심이 되지 않도록 분리(Decoupling)하는 설계**를 목표로 한다.  
브로커는 단지 “실행 채널(Execution Channel)”이며,  
전략·리스크·포트폴리오·파이프라인은 브로커와 독립적으로 유지된다.

이를 위해 QTS는 **Broker Adapter Pattern**과  
**Unified Order Model**,  
**Broker Capability Detection**,  
**Multi-Broker Routing Layer**를 사용한다.

---

# **9.1 Why Multi-Broker? (설계 목적)**

1. **한국투자증권 → 키움증권 → 해외 브로커 확장 대응**
    
2. 브로커 장애 발생 시 백업 경로 제공
    
3. 주문 성공률 개선 및 가격 최적화 가능
    
4. 전략별로 브로커 분배(예: 단기 / 장기 전략 분리)
    
5. 포트폴리오 분산 효과
    
6. 엔진/전략 로직을 브로커 의존성에서 완전히 분리
    

핵심 문장:

**브로커는 바뀔 수 있지만 QTS 구조는 바뀌지 않는다.**

---

# **9.2 Multi-Broker Layer Model**

QTS의 브로커 아키텍처는 다음 4 Layer로 구성된다.

1. **Broker Adapter Layer**
    
2. **Unified Order Model Layer**
    
3. **Broker Capability Layer**
    
4. **Broker Routing Layer**
    

---

# **9.3 Broker Adapter Layer (핵심 구조)**

Broker Adapter Layer는  
“브로커별 API 차이를 감추는 추상화 계층”이다.

브로커 별로 다음 요소를 캡슐화한다:

- 주문 Endpoint
    
- 인증 방식
    
- 응답 구조
    
- 체결 정보 구조
    
- 호가·시세 제공 방식
    
- 주문 가능 단위
    
- 종목코드 규칙
    

모든 브로커는 아래 인터페이스를 구현해야 한다:

```
class BrokerAdapter:
    def send_order(self, order):
        pass

    def get_balance(self):
        pass

    def get_positions(self):
        pass

    def get_price(self, symbol):
        pass
```

Trading Engine은 브로커 이름을 알지 못한다.  
단지 **BrokerAdapter 객체**와 통신할 뿐이다.

---

# **9.4 Unified Order Model**

브로커 별 주문 구조가 다르다면  
엔진이 복잡해지므로, QTS는 단일 주문 모델을 사용한다.

예:

```
OrderRequest:
{
  "symbol": "AAPL",
  "qty": 10,
  "side": "BUY",
  "type": "MARKET",
  "price": None,
  "meta": {...}
}
```

BrokerAdapter는 이 OrderRequest를  
브로커 전용 모델로 변환한다.

한국투자증권 예:

```
{
  "CANO": "00012345",
  "ACNT_PRDT_CD": "01",
  "PDNO": "AAPL",
  "ORD_QTY": "10",
  "ORD_UNPR": "0"
}
```

키움증권 예:

```
{
  "계좌번호": "12345678",
  "비밀번호": "",
  "종목코드": "AAPL",
  "주문수량": 10,
  "주문가격": 0
}
```

즉, 브로커는 다르지만  
**Trading Engine은 동일한 데이터만 사용**한다.

---

# **9.5 Broker Capability Detection**

브로커마다 가능한 기능이 다르기 때문에  
“브로커 기능 맵(Broker Capability Map)”을 유지한다.

예:

```
korea_investment: {
    supports_short: True,
    supports_fractional: False,
    order_limit_per_sec: 5,
    price_tick_size: dynamic
}

kiwoom: {
    supports_short: False,
    supports_fractional: False,
    order_limit_per_sec: 3,
    price_tick_size: dynamic
}
```

Risk Engine과 Trading Engine은 이 정보를 사용하여:

- 주문 가능 여부
    
- 주문 단위
    
- 최소 수량
    
- 호가 규칙
    
- 주문 속도 제한
    

등을 자동으로 조정한다.

---

# **9.6 Multi-Broker Routing Layer**

Routing Layer는  
“최종 주문을 어느 브로커로 보낼지 결정하는 계층”이다.

라우팅 기준:

1. **브로커 정상 상태 여부**
    
2. **시장별 최적 브로커**
    
3. **전략 종류별 브로커 분리**
    
4. **유동성 및 주문 성공률**
    
5. **Fail-Over 구조**
    

Fail-Over 예:

```
if primary_broker_down:
    route_to(secondary_broker)
```

---

# **9.7 Multi-Broker 예외 처리**

아래 상황에서는 즉시 Fail-Safe 또는 Lockdown 발동:

- 두 브로커 모두 다운
    
- 브로커 API 응답 시간 초과
    
- 주문 구조 변동 감지
    
- 호가 단위 규칙 오류
    
- 브로커 계좌 정보 불일치
    

Multi-Broker 구조는 유연성이 크지만  
안전 체계를 더욱 강화해야 한다.

---

# **9.8 Multi-Broker Summary**

|구성 요소|목적|
|---|---|
|Broker Adapter|브로커 종속성 제거|
|Unified Order Model|모든 엔진의 일관된 주문 구조|
|Capability Detection|브로커 제한 자동 반영|
|Routing Layer|브로커 선택 및 Fail-Over|

QTS는 처음부터 멀티 브로커 확장을 고려해 설계되었으며  
브로커 변경이 시스템 전체 변경을 유발하지 않도록  
강력한 추상화 계층을 기반으로 구축되어 있다.

---

# **10. Ops / Automation Layer**

Ops / Automation Layer는 QTS 시스템의  
**운영 안정성, 자동화, 유지보수, 배포, 모니터링**을 담당하는 계층이다.

전략과 엔진만 좋다고 운영이 안정적인 것이 아니라,  
데이터 수집·파이프라인 실행·로그 관리·알림·배포·백업 등이 모두 통합되어야  
현실적인 자동매매 시스템이 완성된다.

Ops Layer는 다음 7가지 구성 요소로 이루어진다:

1. Event Scheduler
    
2. Status Monitor
    
3. Data Sync Manager
    
4. Automation Tasks
    
5. Backup & Versioning Layer
    
6. Deployment Environment Model
    
7. Ops-Control Dashboard
    

---

# **10.1 Event Scheduler**

Event Scheduler는 QTS의 모든 반복 작업을 통제하는 “타임라인 엔진”이다.

### Scheduler가 제어하는 주요 이벤트

1. ETEDA 파이프라인 실행
    
2. UI Rendering 실행
    
3. 스키마 자동 갱신
    
4. Log Rotation
    
5. Daily Report 생성
    
6. 파일 백업
    
7. 브로커 상태 체크(Heartbeat)
    

### Scheduler 기본 구조

```
every interval_ms:
    run_ETEDA()

every 10sec:
    render_UI()

every 1min:
    check_broker_status()

every 1day:
    generate_daily_report()
```

QTS에서는 “시간 기반 이벤트”가 모든 자동화의 중심이다.

---

# **10.2 Status Monitor**

Status Monitor는 시스템 전반의 상태를 실시간으로 수집하고  
Alert 및 Fail-Safe Trigger를 보조하는 모듈이다.

### 모니터링 범위

- 파이프라인 성공/실패 여부
    
- 브로커 연결 상태
    
- ETEDA 지연 시간
    
- 엔진 오류
    
- 데이터 갱신 지연
    
- UI Rendering 실패
    
- Schema Version 불일치
    
- Anomaly Detection 이벤트
    

### Monitor 출력

- UI(R_Dash) 상태 표시
    
- 로그 기록
    
- 알림(슬랙/문자/텔레그램 등)
    
- Fail-Safe Triggers
    

Monitor는 Safety Layer의 “눈(Eyes)” 역할을 한다.

---

# **10.3 Data Sync Manager**

Data Sync Manager는  
Sheets ↔ Python ↔ Local DB 간 데이터 동기화를 책임진다.

역할:

1. 시트 업데이트 감지 → 스키마 엔진 재실행
    
2. Engine Output → R_Dash 반영
    
3. T_Ledger → Position 자동 갱신
    
4. Dividend 데이터 갱신(시트 또는 API/캐시)
    
5. Git DB와 Local DB 간 주기적 동기화
    

Data Sync Manager는 ETEDA와는 별개로 동작하며  
데이터가 “일관된 상태(Consistency)”인지 지속 확인한다.

---

# **10.4 Automation Tasks**

Automation Layer의 핵심 기능은  
“반복적이고 사람이 하기 귀찮은 작업을 자동으로 처리하는 것”이다.

### 자동화 작업 목록

- Daily Report 자동 생성
    
- Weekly/Monthly 성과 리포트 생성
    
- Sheets 포맷팅 자동 적용
    
- UI Block 색상 동적 변경
    
- 백업 자동 스케줄
    
- 데이터 클린업
    
- Log Rotation
    
- Strategy Report 자동 생성
    

사용자는 전략과 리스크에 집중할 수 있도록  
운영 상 반복 작업은 코드가 수행한다.

---

# **10.5 Backup & Versioning Layer**

자동매매 시스템에서 데이터와 설정의 버전 관리가 매우 중요하다.

QTS는 다음 구조로 버전을 유지한다.

1. **Config Snapshot Versioning**
    
2. **Schema Versioning (schema_version)**
    
3. **Dividend DB Git Versioning**
    
4. **Daily Backup(시트/DB/로그)**
    

### Config Snapshot 예:

```
config_snapshot_2025-12-12.json
```

### Backup 구조:

```
/backup
    /daily
    /weekly
    /monthly
```

### 백업 원칙:

- 백업은 운영 중단 없이 실행
    
- ETEDA와 충돌하지 않음
    
- Fail-Safe 발동 시 백업 강제
    
- Git Push를 통한 외부 보관 가능
    

---

# **10.6 Deployment Environment Model**

QTS는 다음 같은 환경에서 배포 운용 가능해야 한다.

|환경|용도|
|---|---|
|Local PC (개발/테스트)|코드 개발 및 시나리오 테스트|
|Cloud VM (Oracle/AWS)|24시간 자동매매 운영|
|GitHub Repo|코드 + 스키마 + DB 관리|
|Sheets (Google Cloud Infra)|UI 및 데이터 관리|
|Docker(Optional)|재현성 높은 배포|

---

## **10.6.1 환경별 고려사항**

### Local 환경:

- Debugging 용이
    
- 전략 개발
    
- 빠른 재시작
    

### Cloud VM:

- UPS 필요 없음
    
- 24시간 매매 운영 가능
    
- 네트워크 안정성 필요
    

### GitHub:

- 스키마/Config/DB 버전관리
    
- 코드 릴리즈 관리
    

---

## **10.6.2 Secrets & Credentials**

브로커 API 계정은 다음 기준을 따른다:

- .env 파일로 분리
    
- 절대 Git에 포함되지 않음
    
- 배포 환경마다 별도 관리
    

---

# **10.7 Ops-Control Dashboard**

Ops-Control Dashboard는 R_Dash와 별도로,  
운영자가 시스템 상태를 한꺼번에 확인할 수 있는 “관리자 전용 UI”이다.

### 주요 표시 항목

- System Status (RUNNING / SAFE MODE / FAIL)
    
- ETEDA 최근 실행 결과
    
- Engine Error Count
    
- Broker Response Time
    
- Exposure Summary
    
- Daily PnL / MDD 상태
    
- Lockdown 상태 여부
    
- Config 주요 값
    

### Ops-Control Dashboard 목적

1. 문제를 조기에 인지
    
2. Fail-Safe 해제 전 상태 점검
    
3. 전략 변경 시 영향 분석
    
4. 운영 안정성 확보
    

Ops-Control Dashboard는 “관리의 중심” 역할을 한다.

---

# **10.8 Ops Layer Summary**

|구성요소|기능|
|---|---|
|Event Scheduler|반복 작업 실행|
|Status Monitor|시스템 상태 감시|
|Data Sync Manager|데이터 일관성 유지|
|Automation Tasks|보고서·백업 자동화|
|Backup & Versioning|안전한 운영 기반|
|Deployment Model|운영 환경 분리|
|Ops-Control Dashboard|운영 UI|

Ops / Automation Layer는 QTS 시스템을 “실제로 운영 가능한” 수준으로 끌어올리는  
매우 중요한 운영 인프라이다.

---

# **11. Testability Architecture**

Testability Architecture는  
QTS 시스템이 **예측 가능하고, 검증 가능하고, 재현 가능한 상태**로 유지되도록 설계된 구조이다.

테스트는 단순히 “코드를 검증하는 과정”이 아니라,  
전략·리스크·포트폴리오·데이터·파이프라인·UI까지 포함한  
전체 시스템 안정성의 핵심 구성 요소다.

QTS는 크게 다음 4가지 테스트 체계를 가진다:

1. Unit Test Layer
    
2. Integration Test Layer
    
3. Scenario Simulation Layer
    
4. Regression Test Layer
    

여기에 추가적으로:

5. Data Consistency Test
    
6. Schema Integrity Test
    
7. Pipeline Step Test
    

까지 통합한다.

---

# **11.1 Why Testability Is Critical in QTS**

자동매매 시스템의 본질적 위험:

- 잘못된 전략 신호
    
- 리스크 계산 오류
    
- 포지션 노출 계산 실패
    
- 브로커 통신 실패
    
- 시트 데이터 불일치
    

테스트가 없으면 이 문제들은 실거래 중에만 발견되며,  
이는 곧 **금전적 손실로 직결되는 구조적 문제**이다.

QTS는 테스트를 단순 지원이 아닌  
**설계 중심 원칙으로 내재화**한다.

---

# **11.2 Unit Test Architecture**

Unit Test는 개별 함수·엔진 단위 테스트다.  
특징:

- 엔진 로직을 독립적으로 검증
    
- 실제 시트 데이터 없이 Raw/Calc Contract Mocking
    
- Risk, Strategy, Portfolio 핵심 함수 단위 테스트
    
- 필수 공식 검증 (Exposure, PnL, 등)
    

### 예: Exposure 계산 테스트

```
assert calc_exposure(10000, 50000) == 20.0
```

### Unit Test의 목표

엔진 코어 로직이 항상 동일하게 작동하도록 보장.

---

# **11.3 Integration Test Architecture**

Integration Test는  
Engine ↔ Pipeline ↔ Data Contract 간 상호작용을 테스트한다.

테스트 순서 예:

```
1) Mock Raw Data 생성
2) Schema Engine 변환
3) Strategy Engine 실행
4) Risk Engine 승인
5) Portfolio 엔진 수량 조정
6) Trading Engine 주문 생성
```

Integration Test는 엔진들이 **하나의 흐름**으로 정상 동작하는지 확인한다.

주요 테스트 항목:

- 전략 신호 생성 → 리스크 승인 일관성
    
- 포트폴리오 엔진의 주문량 조정
    
- Config 파라미터 반영 여부
    
- 주문 생성 후 T_Ledger 반영
    

---

# **11.4 Scenario Simulation Layer**

Scenario Simulation은 “가상 매매 상황”을 구조적으로 테스트한다.

예시 시나리오:

1. **상승 트렌드 테스트 시나리오**
    
2. **급락 테스트 시나리오**
    
3. **데이터 누락 시나리오**
    
4. **전략 신호 오류 시나리오**
    
5. **브로커 장애 시나리오**
    

시나리오 테스트 기본 구조:

```
given historical price data:
  run simulate_ETEDA()
  assert final_position == expected
  assert pnl within expected range
```

Scenario Simulation은 “전략 검증”과 “리스크 검증” 모두에 사용된다.

---

# **11.5 Regression Test Layer**

Regression Test는 시스템 업데이트·버전업 후  
기존 기능이 다시 깨지지 않았는지 검증하는 단계다.

예:

- 스키마 변경 후 기존 엔진이 정상 동작하는가
    
- Strategy 파라미터 변경 후 동일 결과를 내는가
    
- BrokerAdapter 업그레이드 후 주문 구조 동일성 유지되는가
    

Regression Test는 **배포 직전 필수 테스트**이다.

---

# **11.6 Data Consistency Test**

데이터의 정합성은 자동매매의 생명이다.  
QTS는 다음을 테스트한다.

### 테스트 항목:

- Position Sheet ↔ T_Ledger 동기화
    
- 종목/가격 데이터 존재 여부(History 등, 누락 방지)
    
- 배당 DB 구조 및 날짜 유효성
    
- Strategy Sheet 누락 값 검사
    
- Config 값의 타입 유효성
    

### 예시:

```
assert no_null_values_in(Position)
assert valid_schema(StrategySheet)
assert dividend_dates_sorted()
```

Consistency Test는 ETEDA 파이프라인 직전 자동 실행되도록 구성할 수 있다.

---

# **11.7 Schema Integrity Test**

Schema Integrity Test는  
“시트 구조 변경이 시스템을 깨뜨리지 않도록 보장하는 테스트”다.

테스트 항목:

1. 컬럼 이동 후 Schema Engine 자동 매핑 여부 테스트
    
2. 필드 추가/삭제 후 Contract 모델 생성 가능 여부
    
3. schema_version 증가 여부 검사
    
4. Data Contract 재생성 일관성 검사
    

결과적으로:

**시트가 바뀌어도 엔진은 망가지지 않는다.**

이 원칙을 검증하는 핵심 테스트이다.

---

# **11.8 Pipeline Step Test (ETEDA Test)**

ETEDA 각 단계별 테스트가 필수다.

### 테스트 구성:

1. Extract Test
    
2. Transform Test
    
3. Evaluate Test
    
4. Decide Test
    
5. Act Test
    

예: Decide 단계 테스트

```
decision = decide(strategy_signal="BUY",
                  risk_approval=True,
                  recommended_qty=10)

assert decision.action == "BUY"
```

예: Act 단계 테스트

```
mock_broker.send_order() → success
assert T_Ledger updated
```

Pipeline Test는 시스템이 “흐름 기반 구조”를 유지하는지 확인한다.

---

# **11.9 Test Framework Integration**

QTS Testability Architecture는 다음 도구들과 통합 가능하다:

- pytest (Unit/Integration Test)
    
- Jupyter Notebook (Scenario Simulation)
    
- CI/CD 자동 테스트 (GitHub Actions)
    
- Log Replay 테스트 (과거 로그 기반 재현)
    

CI/CD 설정 예:

```
on push:
  run unit tests
  run integration tests
  run regression tests
```

---

# **11.10 Testability Summary**

|테스트 유형|목적|
|---|---|
|Unit Test|엔진 단위 검증|
|Integration Test|엔진 간 상호작용 검증|
|Scenario Simulation|시장 상황 재현 테스트|
|Regression Test|업데이트 후 안정성 보장|
|Data Consistency Test|데이터 무결성 유지|
|Schema Integrity Test|시트 변경 허용|
|Pipeline Step Test|ETEDA 흐름 검증|

**QTS는 테스트 우선(Test-First) 철학을 강제하는 구조이며,  
테스트 불가능한 코드는 설계 자체가 잘못된 것으로 간주한다.**

---

# **12. Architecture Change Management**

Architecture Change Management는  
QTS 시스템의 구조·철학·핵심 동작 원리를 변경할 때 적용되는  
**중앙 통제 프로세스(Central Governance Process)** 이다.

자동매매 시스템은 작은 구조 변경에도  
매매 품질·리스크·전략·데이터 일관성에 대규모 영향을 미치므로  
QTS는 변경 관리를 하나의 독립된 아키텍처 레이어로 다룬다.

---

# **12.1 Why Architecture Change Needs Governance**

다음 위험들을 방지하기 위함이다:

1. 설계 변경 → 전략 오작동
    
2. 시트 구조 변경 → 엔진 실패
    
3. 브로커 확장 → 주문 파이프라인 붕괴
    
4. 신규 기능 추가 → 기존 기능 파손
    
5. 코드 수정을 통한 설계 우회
    
6. 스키마 변경으로 인해 ETEDA 파이프라인 오류 발생
    

핵심 문장:

**설계 변경은 기능 변경보다 훨씬 위험하다.  
따라서 설계 변경은 엄격히 통제되어야 한다.**

---

# **12.2 Architecture Governance 규칙**

QTS는 다음과 같은 원칙 하에 변경 관리가 진행된다.

### 원칙 1 — “아키텍처는 코드보다 상위 레벨이다.”

코드는 설계를 따르며, 설계를 우회하는 구현은 금지된다.

### 원칙 2 — “모든 변경은 문서화되어야 한다.”

설명되지 않은 변경은 허용되지 않는다.

### 원칙 3 — “핵심 철학은 변경할 수 없다.”

- Data-Driven
    
- Pipeline-Oriented
    
- Engine-Modular
    
- Schema-Automation
    
- Zero-Formula UI
    
- Safety-First
    

이는 QTS의 정체성을 구성하므로 변경 불가.

### 원칙 4 — “변경은 테스트를 통과해야 한다.”

테스트 없는 변경은 거부된다.

### 원칙 5 — “모든 변경은 버전 관리된다.”

v1.x → v2.x → v3.x 형태로 단계적 진화.

---

# **12.3 Architecture Change Request (ACR)**

설계를 변경하려면 ACR(Architecture Change Request)을 생성해야 한다.

### ACR 구성 요소:

- 변경 사유(Why?)
    
- 영향 범위(Which Layer?)
    
- 변경 범위(What?)
    
- 변경 전후 구조도(Before/After)
    
- 영향 분석(Data/Engine/Pipeline/UI)
    
- 리스크 평가
    
- 테스트 계획
    
- 롤백 계획
    

ACR은 “문서 기반 승인 프로세스”이다.

---

# **12.4 Architecture Change Approval Flow**

변경 승인(Approval)은 다음 순서로 진행된다:

```
1. ACR 생성
2. 영향 분석 수행
3. 테스트 계획 승인
4. 변경 시나리오 설계
5. 변경 수행
6. Regression Test
7. 문서 업데이트
8. 버전 증가 (Major / Minor)
```

### 승인 기준:

- Safety Layer와 충돌하지 않는가
    
- Zero-Formula 원칙을 위반하지 않는가
    
- Schema Engine과 정합성 유지되는가
    
- ETEDA Pipeline의 순서가 깨지지 않는가
    
- Engine 간 인터페이스가 일관된가
    

---

# **12.5 Version Management Rules**

QTS는 다음 기준으로 버전을 관리한다:

### Major Version (v1 → v2 → v3)

- 핵심 구조 변경
    
- Layer Model 변경
    
- Pipeline Model 수정
    
- Schema 구조 변경
    

### Minor Version (v1.0 → v1.1 → v1.2)

- 엔진 세부 업데이트
    
- UI 개선
    
- Config 파라미터 확장
    
- 파이프라인 옵션 개선
    

### Patch Version (v1.0.0 → v1.0.1)

- 문서 오류 수정
    
- 로그/Alert 메시지 수정
    
- Minor Bug Fix
    

---

# **12.6 Schema Change Management**

스키마 변경은 특히 위험도가 매우 높다.  
따라서 다음 절차를 반드시 따라야 한다.

### 변경 절차:

1. 시트 구조 변경 사전 검토
    
2. Schema Engine 테스트
    
3. Schema Version 증가
    
4. Regression Test 수행
    
5. Data Contract 재생성
    
6. Engine Integration Test
    
7. ETEDA 시뮬레이션
    
8. 안전성 검증 후 반영
    

스키마 변경은 QTS에서 “가장 엄격하게 관리되는 변경”이다.

---

# **12.7 Engine Change Management**

전략/리스크/포트폴리오/트레이딩 엔진 변경 절차:

### 필수 단계:

1. 변경 사유 기록
    
2. Unit Test 작성
    
3. Integration Test
    
4. Regression Test
    
5. UI 영향 여부 확인
    

### 엔진 변경 시 금지사항:

- 평가(Evaluate) 단계 규칙 변경
    
- 리스크 승인 프로세스 우회
    
- 스키마 참조 제거 또는 직접 시트 접근
    
- 파이프라인 흐름 변경
    

엔진 변경은 **파이프라인 및 데이터 모델에 완전히 종속**되어야 한다.

---

# **12.8 Pipeline Change Management**

ETEDA는 설계상 “불변 구조”이다.  
단, 아래 항목만 제한적으로 변경 가능하다:

- Transform 계산 추가
    
- Evaluate 단계에 새 전략 엔진 추가
    
- Decide 단계 조건 확장
    
- Act 단계 재시도 로직 개선
    
- interval_ms 조정
    

절대 금지:

- ETEDA 순서 변경
    
- 단계 생략
    
- 단계 통합
    
- 파이프라인 병렬 실행
    

파이프라인 변경은 전체 시스템 안정성에 직접적인 영향을 준다.

---

# **12.9 Rollback Strategy**

아키텍처 변경이 문제를 일으키면 즉시 롤백해야 한다.

QTS의 롤백 원칙:

1. 변경 이전 버전의 Git Tag 유지
    
2. Config Snapshot 복원
    
3. Schema Version 이전 버전 로드
    
4. Engine 파라미터 복원
    
5. UI Contract 복구
    
6. 백업 데이터 복원
    
7. 파이프라인 재시작
    

Rollback은 운영 안정성을 확보하는 최후의 안전 장치다.

---

# **12.10 Architecture Change Summary**

|항목|설명|
|---|---|
|ACR|아키텍처 변경 요청서|
|Approval Flow|변경 승인 절차|
|Version Rules|버전 증가 기준|
|Schema Change|가장 위험한 변경|
|Engine Change|테스트 기반 변경|
|Pipeline Change|제한적 허용|
|Rollback Strategy|문제 발생 시 복구 플랜|

Architecture Change Management는  
QTS가 “10년 이상 유지 가능한 자동매매 시스템”이 되기 위한  
설계적 안전 장치이자 운영 거버넌스다.

---
아래는 **13장 – Appendix** 전체 본문이다.  
이 장은 QTS 아키텍처 문서에서 다 담기지 않은 핵심 참조자료,  
정의(Definitions), 도메인 용어집(Glossary),  
엔진·파이프라인·스키마의 예제 구조 등을 제공하여  
전체 문서를 실무에서 활용하기 위한 “참조 레이어(Reference Layer)” 역할을 한다.

---

# **13. Appendix**

본 Appendix는 QTS Main Architecture 문서의 보조자료로서,  
개념·용어·예시·샘플 구조 등을 정리하여  
아키텍처 이해 및 실제 구현 과정에서의 활용성을 높이기 위한 목적을 갖는다.

---

# **13.1 Glossary (도메인 용어 정리)**

### **QTS (Qualitative Trading System)**

데이터 중심·파이프라인 중심·스키마 자동화 기반의 엔터프라이즈급 자동매매 시스템.

### **ETEDA Pipeline**

자동매매 실행 흐름: Extract → Transform → Evaluate → Decide → Act.

### **RawData Contract**

시트에서 읽은 원천 데이터 모델.

### **CalcData Contract**

엔진 계산을 통해 도출된 파생 데이터 모델.

### **Evaluation Result**

Strategy → Risk → Portfolio 엔진을 통합한 최종 평가 결과.

### **OrderDecision**

Decide 단계에서 생성되는 “실매매 여부 판단” 결과.

### **Execution Report**

브로커 응답 기반의 체결 결과 데이터.

### **Fail-Safe**

치명적인 시스템 이상 발생 시 즉시 작동하는 안전 모드.

### **Lockdown**

주문 실행을 완전히 차단하는 보호 모드.

### **Schema Automation Engine**

시트 구조 변경을 자동으로 감지·해석·매핑하는 QTS 핵심 엔진.

### **Broker Adapter**

브로커별 API 차이를 숨기고 단일 인터페이스로 통합하는 계층.

---

# **13.2 Example — Data Contract 구조**

### **Position Contract**

```
{
  "symbol": "TSLA",
  "qty": 10,
  "avg_price": 245.72,
  "current_price": 250.10,
  "market": "NASDAQ",
  "exposure_value": 2501.0,
  "exposure_pct": 12.4
}
```

---

### **Strategy Contract**

```
{
  "symbol": "TSLA",
  "signal": "BUY",
  "confidence": 0.82,
  "reason": "RSI oversold + MA crossover",
  "recommended_qty": 5
}
```

---

### **Risk Contract**

```
{
  "risk_approval": true,
  "allowed_qty": 5,
  "limit_reason": null
}
```

---

### **Portfolio Contract**

```
{
  "target_weight": 0.10,
  "current_weight": 0.065,
  "adjust_qty": 4
}
```

---

### **Order Decision Contract**

```
{
  "action": "BUY",
  "qty": 4,
  "price_type": "MARKET",
  "reason": "Strategy BUY + Risk OK + Portfolio Adjust"
}
```

---

# **13.3 Example — Broker Adapter Interface**

```
class BrokerAdapter:
    def authenticate(self):
        pass

    def send_order(self, order_request):
        pass

    def get_positions(self):
        pass

    def get_balance(self):
        pass

    def get_price(self, symbol):
        pass
```

모든 브로커는 이 인터페이스를 기반으로 구현된다.

---

# **13.4 Example — ETEDA Pipeline Pseudocode**

```
def run_ETEDA():
    raw = extract()
    if not raw: fail_safe()

    calc = transform(raw)
    if not calc: fail_safe()

    eval = evaluate(calc)
    if not eval: fail_safe()

    decision = decide(eval)
    if decision.action == "NONE": return

    execution = act(decision)
    if not execution: fail_safe()

    update_reports(execution)
```

---

# **13.5 Example — Schema JSON 구조**

```
{
  "schema_version": "3.6",
  "sheets": {
    "Position": {
      "row_start": 2,
      "columns": {
        "symbol": "A",
        "qty": "B",
        "avg_price": "C",
        "market": "D"
      }
    }
  }
}
```

Schema Engine은 이 구조를 기반으로 Data Contract를 자동 생성한다.

---

# **13.6 Example — Fail-Safe Trigger Mapping**

|Trigger|원인|행동|
|---|---|---|
|FS001|스키마 불일치|Lockdown + trading_enabled=False|
|FS002|파이프라인 단계 실패|Act 중단|
|FS003|브로커 오류|Fail-Safe 발동|
|FS004|데이터 Null/NaN|Evaluate 중단|
|FS005|포지션 음수|시스템 정지|

---

# **13.7 Example — Logging Structure**

```
{
 "timestamp": 1733994100,
 "step": "Evaluate",
 "symbol": "AAPL",
 "strategy_signal": "BUY",
 "risk_approval": true,
 "portfolio_qty": 5,
 "decision": "BUY",
 "execution_price": 180.12
}
```

로그는 디버깅·회귀 테스트·리스크 분석에 필수다.

---

# **13.8 Example — Anomaly Detection Rules**

```
if price_change_pct > 15% within 1min:
    alert("Volatility Spike")

if exposure_pct < 0:
    alert("Negative Exposure")

if missing_fields(raw_data):
    critical("Data Missing")
```

---

# **13.9 Quick Reference Table (요약 참조표)**

### QTS Layer 정리

|Layer|설명|
|---|---|
|UI|Zero-Formula 기반 시각화|
|Data|9 Sheet 데이터 레이어|
|Schema|자동 필드 매핑 엔진|
|Engine|5대 엔진 구조|
|Pipeline|ETEDA 실행 절차|
|Broker|다중 브로커 추상화|
|Ops|운영 관리 자동화|
|Safety|Fail-Safe + Guardrail|

---

# **13.10 Appendix Summary**

Appendix는 QTS 아키텍처의 각 요소를 다시 빠르게 확인하기 위한 레퍼런스이며,  
엔진/파이프라인/스키마/브로커/데이터 구조를  
실제 구현 시 참조할 수 있도록 정리한 보조 문서이다.

---

# **참고 웹페이지**

공식 KIS API 홈페이지 : "https://apiportal.koreainvestment.com/intro"
공식 KIS API 깃페이지 : "https://github.com/koreainvestment/open-trading-api"

---
