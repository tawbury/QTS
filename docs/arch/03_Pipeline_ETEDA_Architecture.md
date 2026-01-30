아래는 **3번 문서: QTS_Pipeline_ETEDA_Architecture.md**의  
**완성본(v1.0.0)** 이다.

본 문서는 ETEDA 파이프라인 전체를  
“실제 운영 가능한 자동매매 시스템의 실행 엔진” 수준으로  
정밀하게 명세한 아키텍처다.

---

# ============================================================

# QTS ETEDA Pipeline Architecture

# ============================================================

Version: v1.0.0  
Status: Architecture Specification (Final)  
Author: 타우  
Last Updated: 2025-12-12

문서 목적:  
QTS 자동매매 시스템의 핵심 실행 흐름인 **ETEDA Pipeline**  
(Extract → Transform → Evaluate → Decide → Act)의 구조, 역할,  
엔진/데이터/브로커와의 상호작용, 오류 처리, Fail-Safe 연계 규칙을  
정식 아키텍처 명세로 정의한다.

본 문서는 QTS 시스템의 안정성과 일관성을 보장하는  
**최상위 실행 규칙서(Execution Playbook)** 이다.

---

# **1. Overview**

## **1.1 목적**

ETEDA Pipeline을 문서화하는 목적:

1. 자동매매가 어떤 절차로 실행되는지 명확한 기준 제공
    
2. 모든 엔진과 데이터 처리가 ETEDA 순서를 절대 위반하지 않도록 강제
    
3. 실시간 자동매매와 회귀 테스트에서 동일 동작을 보장
    
4. 파이프라인 실패 시 시스템이 안전하게 중단되도록 구조화
    

---

## **1.2 범위**

포함:

- ETEDA 5단계의 논리적/기술적 정의
    
- 단계별 I/O Contract
    
- 오류 처리·Fail-Safe 연계 규칙
    
- 파이프라인 상태 모델
    
- 스케줄링, 반복 실행 구조
    

제외:

- 개별 엔진 구현
    
- 계산 수식 상세 (→ QTS_Python_Calculation_Spec)
    
- Schema Engine 상세 구조 (→ [Schema Architecture](./01_Schema_Auto_Architecture.md))
    

---

## **1.6 관련 문서**

- **Engine Core**: [02_Engine_Core_Architecture.md](./02_Engine_Core_Architecture.md)
- **Data Contract**: [04_Data_Contract_Spec.md](./04_Data_Contract_Spec.md)
- **Schema Automation**: [01_Schema_Auto_Architecture.md](./01_Schema_Auto_Architecture.md)
- **Fail-Safe & Safety**: [07_FailSafe_Architecture.md](./07_FailSafe_Architecture.md)
- **Broker Integration**: [08_Broker_Integration_Architecture.md](./08_Broker_Integration_Architecture.md)
- **Ops & Automation**: [09_Ops_Automation_Architecture.md](./09_Ops_Automation_Architecture.md)

---

## **1.3 ETEDA 설계 배경**

일반적인 자동매매 구현의 문제점:

- 코드 여기저기에서 매매 로직이 흩어져 실행됨
    
- 전략 → 리스크 → 주문 흐름이 일관되지 않음
    
- 오류 발생 시 시스템이 무작위 상태로 남음
    
- UI/시트 업데이트가 매매 흐름을 방해
    

QTS는 이를 해결하기 위해  
**단일하고 불변적인 실행 절차**를 구축했다.

---

## **1.4 Pipeline-Oriented Architecture 철학**

핵심 원칙:

1. **순서가 바뀌면 안 된다.**
    
2. **단계를 건너뛰면 안 된다.**
    
3. **각 단계는 단일 책임(Single Responsibility)을 가진다.**
    
4. **에러는 즉시 단계 내에서 처리하고, 심각하면 전체 중단한다.**
    
5. **엔진은 ETEDA Pipeline 밖에서 직접 호출될 수 없다.**
    

---

## **1.5 ETEDA와 Engine/Data/Safety Layer의 관계**

|Layer|역할|
|---|---|
|Data Layer|Raw/Calc Contracts 제공|
|Schema Engine|Contract 생성|
|Engine Layer|Evaluate 단계에서 각 엔진 실행|
|Safety Layer|모든 단계에서 검증/보호|
|ETEDA Pipeline|전체 실행 절차 통제|

ETEDA는 이 모든 레이어를 “실행 플로우”로 묶는 최상위 제어 구조다.

---

# **2. ETEDA High-Level Flow**

## **2.1 5단계 파이프라인 개요**

```
1. Extract  – 데이터 읽기
2. Transform – 계산/정규화
3. Evaluate – 엔진 평가
4. Decide   – 최종 의사결정
5. Act      – 주문 실행
```

각 단계의 출력은 다음 단계의 입력이 된다.

---

## **2.2 단일 사이클(1 Loop) 개념**

1 Loop = 1회 매매 판단 흐름  
결과:

- BUY / SELL / NONE
    
- 또는 Fail-Safe
    

---

## **2.3 Multi-Cycle Loop 구조**

자동매매는 아래 반복 구조로 실행된다.

```
while system_running:
    run_ETEDA()
    sleep(interval_ms)
```

interval_ms는 Config Sheet에서 제어.

---

## **2.4 Pipeline과 Scheduler의 관계**

Scheduler는 다음 역할을 수행:

- ETEDA 주기 실행
    
- Broker 상태 체크
    
- UI Rendering 실행
    

Scheduler는 ETEDA 외부에서 동작하며  
ETEDA는 Scheduler에 의존하지 않는다.

---

## **2.5 Pipeline과 UI Rendering의 분리 원칙**

UI Rendering은 ETEDA 파이프라인을 방해해서는 안 된다.

따라서:

- ETEDA = 매매 판단
    
- Rendering = 보여주기
    

둘은 완전히 분리한다.

---

# **3. Step 1 – Extract Phase Architecture**

## **3.1 목적**

Extract 단계의 목적:

- 원천 데이터 수집
    
- 스키마 기반 구조 검증
    
- RawData Contract 생성
    

Extract가 실패하면  
**나머지 단계는 실행되지 않는다.**

---

## **3.2 입력 소스**

- Google Sheets (10+1 시트 Layer)
    
- Dividend Local DB / Git DB
    
- Broker 상태 정보 (잔고/포지션)
    
- Config 운영 모드
    

---

## **3.3 Schema Engine 연동 방식**

Extract는 반드시 Schema Automation Engine을 호출한다.

```
schema = load_schema()
raw_data = build_raw_contract(schema)
```

schema_version 불일치 시 Fail-Safe.

---

## **3.4 RawData Contract 생성 규칙**

- 시트의 컬럼/행은 Schema에서 정의된 구조만 사용
    
- 필수 필드 누락 → 오류 처리
    
- Null/NaN 값 정규화
    

---

## **3.5 데이터 정합성 체크 규칙**

예:

- qty < 0 → 오류
    
- date 역순 → 경고
    
- 종목명 누락 → 오류
    
- position과 ledger 합이 불일치 → 경고 또는 오류
    

---

## **3.6 Extract 단계 실패 조건**

- Schema 불일치
    
- 필수 데이터 누락
    
- Raw Contract 생성 실패
    

실패 시 즉시 Fail-Safe.

---

# **4. Step 2 – Transform Phase Architecture**

## **4.1 목적**

Transform 단계는 RawData를 기반으로  
계산된 데이터(CalcDataContract)를 생성하는 단계이다.

---

## **4.2 CalcData Contract 생성 규칙**

주요 계산 항목:

- Exposure
    
- PnL
    
- target_weight
    
- unrealized/realized PnL
    
- 변동성, 이동평균 등 전략 필요값
    
- 계좌 평가금 total_equity
    

계산은 반드시 Python Calculation Spec에 기반한다.

---

## **4.3 핵심 계산 항목**

예:

```
exposure_value = qty * current_price  
exposure_pct = exposure_value / total_equity  
```

계산식 변경 시 스펙 문서 버전 증가 필요.

---

## **4.4 Python Calculation Spec과의 연계**

Transform 단계는 “계산 로직 내장 금지”.

모든 계산은 아래 스펙을 호출하거나 참조:

```
QTS_Python_Calculation_Spec.md
```

---

## **4.5 Transform 단계 성능 고려사항**

- 과도한 반복 계산 금지
    
- 불필요한 지표 계산 금지
    
- 고정 지표 캐싱 처리 가능
    

---

## **4.6 Transform 단계 실패 조건**

- 계산 중 NaN/Inf 발생
    
- required calc field 생성 실패
    
- Raw Contract 데이터 부족
    

실패 시 Fail-Safe.

---

# **5. Step 3 – Evaluate Phase Architecture**

## **5.1 목적**

전략 → 리스크 → 포트폴리오 엔진을 순서대로 평가하여  
**EvaluationResult** 모델을 생성한다.

---

## **5.2 실행 순서 고정**

```
Strategy Engine
→ Risk Engine
→ Portfolio Engine
```

순서가 바뀌면 시스템은 잘못된 판단을 한다.

---

## **5.3 Engine Input/Output Contract 연결 구조**

Evaluate 단계는 Contract를 전달하는 중간 관리자 역할 수행:

```
strategy_result = Strategy.run(...)
risk_result     = Risk.run(strategy_result, ...)
portfolio_result = Portfolio.run(strategy_result, risk_result, ...)
```

---

## **5.4 EvaluationResult 구조**

```python
EvaluationResult = {
  "signal": "BUY",
  "approved": True,
  "recommended_qty": 12,
  "final_qty": 10,
  "reason": "Strategy BUY + Risk OK + Rebalance"
}
```

---

## **5.5 엔진 실패 시 Pipeline 반응 규칙**

- Strategy 실패 → 전체 Evaluate 실패
    
- Risk 실패 → approved = False → 최종 주문 없음
    
- Portfolio 실패 → final_qty = 0
    

---

## **5.6 Safety Layer 연계**

Evaluate 단계에서 다음이 감지되면 Guardrail 또는 Fail-Safe와 연계한다.

- Exposure 비정상
    
- 누락 데이터
    
- 전략 신호 충돌
    
- 리스크 계산 오류
    

---

# **6. Step 4 – Decide Phase Architecture**

## **6.1 목적**

Evaluate 단계에서 도출된 EvaluationResult를 기반으로  
최종 매매 여부를 결정한다.

---

## **6.2 OrderDecision Contract 구조**

```python
OrderDecision = {
  "action": "BUY" | "SELL" | "NONE",
  "qty": final_qty,
  "price_type": "MARKET" | "LIMIT",
  "reason": "..."
}
```

---

## **6.3 Config 반영 규칙**

Config에 다음 값이 있으면 매매 금지:

- trading_enabled = False
    
- safe_mode = True
    
- pipeline_paused = True
    

---

## **6.4 Safe Mode / Lockdown 상태에서의 동작**

- Safe Mode → Evaluate까지 실행, Act는 실행 안 함
    
- Lockdown → Decide에서 자동으로 action = NONE
    

---

## **6.5 No-Trade 조건**

- approved = False
    
- final_qty == 0
    
- signal == NONE/HOLD
    
- 시장 정지/브로커 점검
    

---

## **6.6 Decide 실패 조건**

- Contract 누락
    
- Risk 조건 충돌
    
- 가격 정보 부족
    

---

# **7. Step 5 – Act Phase Architecture**

## **7.1 목적**

Trading Engine을 호출하여  
주문 생성 → 브로커 전송 → ExecutionResult 처리하는 단계.

---

## **7.2 Trading Engine과 BrokerAdapter 연동**

```
adapter = BrokerAdapter(...)
result = TradingEngine.send(order_request)
```

Trading Engine은 브로커 내부 구조를 알지 못한다.

---

## **7.3 주문 → 응답 처리 플로우**

1. Unified Order Model 생성
    
2. BrokerAdapter로 전송
    
3. ExecutionResult 수신
    
4. 결과 정규화
    
5. T_Ledger 업데이트
    
6. Position 업데이트 트리거
    

---

## **7.4 ExecutionResult → T_Ledger 기록 규칙**

기본 필드:

- timestamp
    
- symbol
    
- qty
    
- price
    
- side
    
- amount
    
- fee
    

---

## **7.5 Act 실패 시 Fail-Safe**

- 브로커 응답 불능
    
- 주문 생성 오류
    
- ExecutionResult 필드 누락
    

---

## **7.6 재시도 정책**

```
if temporary_error:
    retry up to N times
else:
    fail immediately
```

---

## **7.7 Scalp Execution Extension (참조)**

For Scalp strategy, Act phase extends into 6-stage micro-architecture:
PreCheck → OrderSplit → AsyncSend → PartialFillMonitor → AdaptiveAdjust → EmergencyEscape

See: [sub/15_Scalp_Execution_Micro_Architecture.md](./sub/15_Scalp_Execution_Micro_Architecture.md)

---

# **8. Pipeline Error Handling & Fail-Safe Integration**

## **8.1 단계별 오류 분류**

- ExtractError
    
- TransformError
    
- StrategyError
    
- RiskError
    
- PortfolioError
    
- DecideError
    
- ActError
    

---

## **8.2 오류 심각도 레벨링**

- Warning
    
- Error
    
- Critical(Error + Fail-Safe Trigger)
    

---

## **8.3 Fail-Safe Trigger 매핑**

예:

- Extract 실패 → FS001
    
- Transform NaN → FS010
    
- Risk 거부(치명적) → FS020
    
- Act 실패 → FS030
    

---

## **8.4 Lockdown 연계 규칙**

Critical Error 2회 이상 연속 → Lockdown 자동 진입.

---

## **8.5 로그/알림 처리 규칙**

모든 에러는:

- 로그 기록
    
- UI 표시
    
- 필요 시 알림 전송(Ops Dashboard 연계)
    

---

# **9. Pipeline State Model**

## **9.1 상태 정의**

|상태|설명|
|---|---|
|IDLE|대기 상태|
|RUNNING|Pipeline 정상 실행|
|SAFE|Safe Mode|
|FAIL|Fail-Safe 발동|
|LOCKDOWN|Act 차단 상태|

---

## **9.2 상태 전이 다이어그램**

예:

```
IDLE → RUNNING → FAIL → LOCKDOWN → IDLE
```

---

## **9.3 상태별 허용 동작**

- SAFE: Evaluate까지 OK, Act 금지
    
- FAIL: 모든 단계 중단
    
- LOCKDOWN: Decide/Act 금지
    

---

## **9.4 Scheduler·Ops Dashboard와 상태 공유 규칙**

- 실행 상태는 R_Dash에 표시
    
- Ops Dashboard는 상태 변경을 실시간 반영
    

---

# **10. Multi-Cycle & Scheduling Architecture**

## **10.1 반복 실행 모델**

```
while True:
  run_ETEDA()
  sleep(interval)
```

---

## **10.2 interval_ms 제어 정책**

조건에 따라 동적 변화 가능:

- 시장 변동성 상승 → 주기 단축
    
- 야간 장외 시간 → 주기 확대
    

---

## **10.3 시간대별 동작 모드**

- 장중: Full Mode
    
- 장후: Monitoring Mode
    
- 점검 시간: Pause Mode
    

---

## **10.4 스케줄 지연 대응**

- 파이프라인 실행 시간 > interval_ms  
    → 스케줄러가 자동 보정 or Warning 발생
    

---

## **10.5 Backtest / Paper / Live 분기**

각 모드별로 Pipeline Runner를 분기 가능:

- Backtest: 시계열 데이터 반복
    
- Paper: 주문 생성 → 시뮬레이션
    
- Live: 실제 브로커 호출
    

---

# **11. Testability – Pipeline Test Architecture**

## **11.1 Step-by-Step ETEDA 테스트**

각 단계 단위로 테스트 가능:

- Extract Test
    
- Transform Test
    
- Evaluate Test
    
- Decide Test
    
- Act Test
    

---

## **11.2 End-to-End Pipeline 테스트**

```
Raw → Transform → Evaluate → Decide → Act
```

모든 흐름을 통합 테스트.

---

## **11.3 시나리오 기반 Pipeline 테스트**

예:

- 급등/급락 시나리오
    
- 데이터 누락 시나리오
    
- 브로커 장애 시나리오
    

---

## **11.4 Regression Test 포함 방법**

ETEDA는 업데이트 전후 결과가 동일해야 한다.

회귀 테스트는 반드시:

- 동일 Raw 데이터
    
- 동일 Contract
    
- 동일 Config  
    조건에서 비교해야 한다.
    

---

## **11.5 Mock Pipeline Runner**

테스트 전용 ETEDA 실행기:

- Mock Raw Contract
    
- Mock Calculations
    
- Mock Engine Outputs
    

Unit Test와 Integration Test 모두 대응 가능.

---

# **12. 운영 관점 Pipeline 규칙**

## **12.1 운영자가 모니터링해야 할 지표**

- Pipeline 성공률
    
- Extract/Transform 지연 시간
    
- Evaluate 오류 발생률
    
- Act 실패율
    
- Fail-Safe 빈도
    

---

## **12.2 장애 발생 시 운영 절차**

1. Fail-Safe 원인 확인
    
2. 시트/데이터/브로커 점검
    
3. Config 또는 Schema 조정
    
4. 매매 재개 승인
    

---

## **12.3 점검/업데이트 시 규칙**

- 파이프라인 중단 후 업데이트
    
- Schema Version 증가 필요 시 즉시 반영
    
- 업데이트 후 반드시 Regression Test 실행
    

---

## **12.4 로그/리포트 연계**

Pipeline 실행 결과는 다음에 기록:

- ETEDA 로그
    
- Performance 리포트
    
- Ops Dashboard
    

---

## **12.5 운영 문서/Runbook와 연계**

본 문서는 Runbook 및 Ops Guide와 연결되어야 한다.

---

# **13. Appendix**

## **13.1 ETEDA 전체 Pseudocode**

```python
def run_ETEDA():
    raw = extract()
    if not raw: return fail_safe()

    calc = transform(raw)
    if not calc: return fail_safe()

    eval = evaluate(calc)
    if not eval: return fail_safe()

    decision = decide(eval)
    if decision.action == "NONE":
        return decision

    execution = act(decision)
    if not execution:
        return fail_safe()

    return execution
```

---

## **13.2 단계별 Input/Output 요약 표**

|단계|Input|Output|
|---|---|---|
|Extract|Sheets, DB|Raw Contract|
|Transform|Raw|Calc Contract|
|Evaluate|Raw/Calc|EvaluationResult|
|Decide|EvaluationResult|OrderDecision|
|Act|OrderDecision|ExecutionResult|

---

## **13.3 에러/상태 코드 목록**

- FS001: Schema Error
    
- FS010: Transform 계산 실패
    
- FS020: Risk 치명 오류
    
- FS030: Trading 실행 실패
    

---

## **13.4 실패 시나리오 & 대응 가이드**

예: Extract 단계에서 Position 데이터 누락 →

- 원인: 시트 정리 중 행 삭제

- 대응: 시트 복원, Schema 재빌드 → 파이프라인 재가동


---

# **14. Event Priority Architecture (참조)**

QTS Event Priority Architecture defines latency isolation across 4 priority levels:
- P0 (Critical): Execution & Fill events - <10ms
- P1 (High): Orderbook/Price updates - <50ms
- P2 (Medium): Strategy evaluation - <500ms
- P3 (Low): UI & Logging - Best effort

See: [sub/17_Event_Priority_Architecture.md](./sub/17_Event_Priority_Architecture.md)

---
