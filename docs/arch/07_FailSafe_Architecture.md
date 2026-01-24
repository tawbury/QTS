아래는 **7번 문서: QTS_FailSafe_Architecture.md**  
**완성본(v1.0.0)** 이다.

QTS 전체 아키텍처 중 가장 중요한 문서 중 하나이며,  
**자동매매 중단·오류 제어·자산 보호·이상 징후 대응**에 대한  
최종 기준(SSoT) 역할을 수행한다.

---

# ============================================================

# QTS Fail-Safe & Safety Layer Architecture

# ============================================================

Version: v1.0.0  
Status: Architecture Specification (Final)  
Author: 타우  
Last Updated: 2025-12-12

문서 목적:  
QTS 자동매매 시스템에서 안전성을 보장하기 위한  
**Fail-Safe, Guardrail, Anomaly Detection, Safety State Machine**  
전체 아키텍처를 정식 명세한다.  
해당 문서는 QTS의 전반적인 안정성·자산 보호·오류 회피를 위한  
최종 기준 문서이며, ETEDA 파이프라인과 모든 엔진 계층에 적용된다.

---

# **1. Overview**

## **1.1 목적**

Safety Layer는 다음 목표를 수행한다.

1. 시스템 오류가 자산 손실로 이어지지 않도록 보호
    
2. 비정상 데이터·이상 징후 감지
    
3. ETEDA Pipeline 실행 중 위험 판단
    
4. Risk Engine/Trading Engine의 오판 방지
    
5. 자동매매 중지 및 복구 절차 제공
    
6. 운영자에게 즉각적 피드백 제공
    

---

## **1.2 범위**

포함:

- Fail-Safe 조건 및 처리
    
- Guardrail 조건 및 평가 방식
    
- Anomaly Detection 기준
    
- Safety 상태 모델 및 Lockdown 정의
    
- ETEDA 통합 규칙
    
- Safety Logging·Notification
    

제외:

- 브로커 오류 세부 내용(Trading Engine 문서 참고)
    
- UI 세부 디자인 요소
    

---

## **1.3 Safety Layer의 역할**

Safety Layer는 QTS에서 다음 기능을 수행한다.

- **Fail-Safe 조건 감시 및 실행 차단**
    
- **Guardrail 기반 사전 예방 조치 적용**
    
- **이상 징후 감지 및 경고 발행**
    
- **Lockdown 상태로 전환하여 시스템을 보호**
    
- **Safety 로그 및 알림 시스템 관리**
    

---

## **1.4 Fail-Safe / Guardrail / Warning 차이**

|개념|설명|동작|
|---|---|---|
|Warning|이상 징후 감지|UI 경고 표시, 매매는 진행 가능|
|Guardrail|경계 조건 초과|특정 거래 제한 또는 일부 기능 차단|
|Fail-Safe|치명적 오류|ETEDA 중단, 거래 차단, Lockdown 가능|

---

## **1.5 Safety Layer와 ETEDA/Engine 관계**

```
Extract → Safety 체크  
Transform → 계산 오류 감지  
Evaluate → Guardrail/Risk 협업  
Decide → Fail-Safe 여부 최종 판단  
Act → 실행 실패 시 즉시 Fail-Safe  
Performance → 이상 패턴 분석
```

Safety Layer는 ETEDA Pipeline 전 구간을 감시한다.

---

# **2. Safety Layer 주요 구성 요소**

## **2.1 Fail-Safe Engine**

치명적 오류(데이터 손상·계좌 위험·브로커 오류 등)에 반응하는 안전 엔진.

---

## **2.2 Guardrail Engine**

리스크 경계 조건을 평가하여 사전 방지 조치를 수행하는 엔진.

---

## **2.3 Anomaly Detection Engine**

가격·PnL·Exposure·데이터 구조 등에서 비정상 패턴 탐지.

---

## **2.4 Safety State Manager**

Safety 상태(NORMAL/ WARNING/ FAIL/ LOCKDOWN)를 관리하는 상태 머신.

---

## **2.5 Safety Logger & Notifier**

Safety 이벤트 기록 및 알림 전송 담당.

---

# **3. Fail-Safe Architecture**

## **3.1 Fail-Safe 발동 조건**

Fail-Safe는 "치명적 손상 또는 즉각 중단이 필요한 이벤트" 발생 시 발동한다.

### **A. 데이터 손상 계열**

- Schema Version 불일치
    
- 필수 RawData 필드 누락
    
- CalcData NaN/Inf
    
- Position/T_Ledger 불일치
    

### **B. 브로커/주문 계열**

- 주문 거부 반복(N회 이상)
    
- ExecutionResult 필수 필드 누락
    
- Broker 연결 끊김
    

### **C. 리스크 계열**

- Exposure > Exposure Limit * 1.2
    
- Daily Loss > Limit
    
- Equity <= 0
    

### **D. 시스템 계열**

- ETEDA 사이클 시간 과도한 증가
    
- 엔진 Fault 상태 지속
    
- 메모리/자원 부족 감지
    

---

## **3.2 Fail-Safe Trigger → Pipeline 동작 변화**

Fail-Safe 발동 시:

1. ETEDA 즉시 중단
    
2. 거래 전면 차단
    
3. pipeline_state = FAIL
    
4. UI에 강한 붉은색 경고 표시
    
5. Safety Logger 기록 및 알림 송출
    

---

## **3.3 Fail-Safe Code Table**

|코드|설명|
|---|---|
|FS001|SchemaMismatchError|
|FS010|RawData 필수 필드 누락|
|FS020|Transform 단계 NaN 발생|
|FS030|Risk 계산 오류|
|FS040|Broker Execution 오류|
|FS050|Equity <= 0|
|FS060|ETEDA 사이클 시간 초과|
|FS070|Position-Ledger 불일치|
|FS080|시스템 메모리 부족|

---

## **3.4 Fail-Safe 리커버리 전략**

- 우선 조건 검사 후 정상화 여부 판단
    
- Schema 재빌드
    
- RawData 재로드
    
- 브로커 연결 재확인
    
- Equity 확인
    
- Fix 후 pipeline_state = NORMAL로 복귀 가능
    

---

## **3.5 치명적 데이터 오류 처리**

데이터가 손상되면:

- ETEDA 중단
    
- 누락된 데이터 보완 또는 JSON/Sheets를 복구
    
- Safety Layer에서 재검증 후 재개
    

---

## **3.6 Fail-Safe와 Lockdown 차이**

|구분|Fail-Safe|Lockdown|
|---|---|---|
|목적|즉시 중단|확정적 차단|
|상태|pipeline_state=FAIL|pipeline_state=LOCKDOWN|
|매매|즉시 중단|불가(고정)|
|복귀|자동 또는 수동 복귀 가능|운영자 승인 필요|

---

# **4. Guardrail Architecture**

## **4.1 Guardrail 역할**

Fail-Safe보다 한 단계 낮은 수준의 “경계 보호(Soft Protection)” 역할.

- 리스크 임계값 도달 시 거래 제한
    
- 비정상 노출 증가 감지
    
- 전략 신호 중단 또는 조정
    

---

## **4.2 Guardrail Trigger 조건**

- Exposure > Exposure Limit
    
- 특정 종목 Weight > 제한치
    
- Daily Loss > Warning Limit
    
- 신호 충돌(BUY/SELL 동시 발생)
    
- 포지션 없이 SELL 시도
    

---

## **4.3 Guardrail → Evaluate/Decide 단계 개입 방식**

### Strategy → Risk → Portfolio 흐름 중:

- StrategyDecision 조정
    
- RiskDecision 허용 수량 제한
    
- PortfolioDecision final_qty 축소
    

---

## **4.4 Guardrail Code Table**

|코드|설명|
|---|---|
|GR001|Exposure Limit 초과|
|GR010|Symbol Weight 초과|
|GR020|DailyLoss Warning|
|GR030|신호 충돌 감지|
|GR040|포지션 불일치 감지|

---

## **4.5 경계 조건 정의**

예:

```
max_exposure_pct = 0.95
max_symbol_exposure_pct = 0.15
daily_loss_warning_pct = -0.03
```

---

## **4.6 Guardrail 해제 조건**

- Exposure 정상화
    
- 손익 회복
    
- 신호 충돌 사라짐
    
- 정상적인 Position 확인
    

---

# **5. Anomaly Detection Architecture**

## **5.1 이상 감지 대상**

- 가격 급등락
    
- 거래량 이상
    
- DI_DB 빈값 또는 누락
    
- PnL 급변
    
- Exposure 값 튐
    
- Position-Ledger mismatch
    
- ETEDA 사이클 시간 급증
    
- 브로커 응답 지연
    
- 데이터 구조 자체의 변형
    

---

## **5.2 이상치 탐지 알고리즘 개요**

예:

```
price_change_pct > threshold  
daily_pnl_change > threshold  
exposure_value / equity > limit  
cycle_time > expected * 3
```

---

## **5.3 이상 감지 → 상태 변화 흐름**

```
Anomaly Detected  
   ↓  
WARNING 상태  
   ↓  
Guardrail Trigger (조건 충족 시)  
   ↓  
Fail-Safe (치명적 오류 시)
```

---

## **5.4 Anomaly Level**

- Low: 경미한 이상 → Warning
    
- Medium: 중간 수준 이상 → Guardrail
    
- High: 치명적 → Fail-Safe
    

---

## **5.5 Anomaly Code Table**

|코드|설명|
|---|---|
|AN001|가격 급등락|
|AN010|DI_DB 누락|
|AN020|PnL 급변|
|AN030|Ledger inconsistency|
|AN040|ETEDA Cycle Time 급증|
|AN050|Broker 응답 지연|

---

## **5.6 Anomaly UI 표시 규칙**

- 블록 단위 경고 조색
    
- Fail-Safe 수준이면 화면 전체 강조
    
- Warning 상태는 노란색 강조
    

---

# **6. Safety State Model**

## **6.1 Safety States**

|상태|설명|
|---|---|
|NORMAL|정상|
|WARNING|경고 상태|
|FAIL|치명 오류, 매매 중단|
|LOCKDOWN|영구적 차단(운영자 승인 필요)|

---

## **6.2 상태 전이 규칙**

```
NORMAL → WARNING → FAIL → LOCKDOWN
FAIL → NORMAL (수동 복귀 조건 충족 시)
LOCKDOWN → NORMAL (운영자 승인 시)
```

---

## **6.3 구조적 오류 처리**

예:

- Schema mismatch
    
- JSON 구조 불일치
    
- Raw 데이터 손상
    

구조적 오류는 곧바로 FAIL 상태로 진입한다.

---

## **6.4 Lockdown 규칙**

- Fail-Safe 2회 연속 발생 시 자동 Lockdown
    
- 운영자 승인 전까지 거래 불가
    

---

## **6.5 Safe Mode와의 차이**

|항목|Safe Mode|Fail-Safe / Lockdown|
|---|---|---|
|목적|조심 실행|거래 중단|
|ETEDA|Evaluate까지 수행|실행 중단|
|Act|미수행|강제 중단|
|운영자|선택적 활성화|필수 승인 필요|

---

# **7. Safety Layer와 ETEDA 통합**

## **7.1 Extract 단계 Safety 체크**

- 시트 데이터 누락
    
- 스키마 불일치
    
- RawDataContract 생성 실패
    

---

## **7.2 Transform 단계 Safety 체크**

- NaN/Inf 계산 발생
    
- total_equity <= 0
    
- Exposure 계산 오류
    

---

## **7.3 Evaluate 단계 Safety 체크**

- Risk Engine 오류
    
- 대량 신호 충돌
    
- 포트폴리오 수량 음수 발생
    

---

## **7.4 Decide 단계 Safety 체크**

- Risk 승인 불가
    
- final_qty <= 0
    
- Price 정보 불일치
    

---

## **7.5 Act 단계 Safety 체크**

- Broker 응답 오류
    
- ExecutionResult 누락
    
- 주문 실패 반복
    

---

## **7.6 Performance 단계 Safety 체크**

- Equity Curve 튐
    
- MDD 계산 불가
    
- 성과 수치 급등락
    

---

# **8. Risk Engine과의 관계**

## **8.1 Fail-Safe vs Risk Engine 판단 차이**

- Risk Engine = 전략 실행 여부 판단
    
- Fail-Safe = 전체 파이프라인 중단 여부 판단
    

---

## **8.2 Risk 거부 누적 → Guardrail Trigger**

반복적으로 approved=False가 발생하면 Guardrail 개입 가능.

---

## **8.3 Exposure·PnL 판단 공동 역할**

Risk Engine은 비중·손익 중심,  
Safety Layer는 시스템 전체적 안정성 중심.

---

## **8.4 Risk Engine Fail Mode 발생 조건**

- 리스크 계산 오류
    
- 필수 필드 누락
    
- Config 파라미터 오류
    

Risk 오류 → Fail-Safe Escalation.

---

## **8.5 Escalation 흐름**

```
Risk Warning  
 → Guardrail  
 → Fail-Safe  
 → Lockdown
```

---

# **9. Safety Logging & Notification**

## **9.1 Safety 로그 구조**

|필드|설명|
|---|---|
|timestamp|이벤트 시간|
|safety_code|FS/GR/AN 코드|
|level|WARNING/FAIL|
|message|상세 설명|
|pipeline_state|당시 상태|
|meta|추가 정보|

---

## **9.2 기록 규칙**

- Safety 관련 이벤트는 모두 로그 기록
    
- 최근 N개만 UI에 표시
    
- 모든 기록은 JSON 및 파일 로그에도 저장
    

---

## **9.3 Fail-Safe 알림 규칙**

- Slack/Telegram/Email 등
    
- 메시지 템플릿 기반 표준화
    

---

## **9.4 Ops Dashboard Safety Summary**

- 최근 Fail-Safe 목록
    
- 현재 Safety State
    
- 주요 이유(코드 기반) 표시
    

---

# **10. 테스트 전략(Testability)**

## **10.1 Fail-Safe Trigger 테스트**

조건별로 FS001 ~ FS100 테스트.

## **10.2 Guardrail 테스트**

Exposure 초과, 신호 충돌 등 테스트.

## **10.3 Anomaly Detection 테스트**

가격 급변, DI_DB 누락 등.

## **10.4 Lockdown 상태 테스트**

일부러 Fail-Safe 반복 유도하여 Lockdown 전이 확인.

## **10.5 End-to-End Safety 테스트**

전체 ETEDA에 Safety Layer 결합한 통합 테스트.

---

# **11. Appendix**

## **11.1 Fail-Safe 코드 리스트**

FS001 ~ FS100 정식 코드화 위한 초안 테이블 포함.

---

## **11.2 Guardrail 코드 리스트**

GR001 ~ GR200 정식 코드 목록 초안.

---

## **11.3 Anomaly 코드 리스트**

AN001 ~ AN200 목록.

---

## **11.4 Safety Layer State Diagram**

NORMAL → WARNING → FAIL → LOCKDOWN 흐름 다이어그램.

---

## **11.5 대표 시나리오**

1. Broker 응답 없음 → FS040
    
2. Exposure 폭증 → GR001 → FS020
    
3. PnL 급락 → AN020 → WARNING → FAIL
    

---

**QTS Fail-Safe & Safety Architecture v1.0.0 — 완료됨**

---

다음 문서로 넘어갈까?

### 8번 문서 스켈레톤 생성

**QTS_Broker_Integration_Architecture.md**

바로 진행할까?