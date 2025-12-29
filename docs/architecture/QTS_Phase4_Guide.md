
---

# QTS Phase 4 Guide (초석 문서)

**Execution Loop · Order State · Risk Entry 기준 문서**

- **File:** `QTS/docs/architecture/QTS_Phase4_Guide.md`
    
- **Version:** v0.1.0
    
- **Status:** Draft (Phase 4 초석 문서)
    
- **Prerequisite:** Phase 3 Gate D 종료 선언 완료
    
- **Prepared At:** 2025-12-29
    

---

## 1. Phase 4의 목적

Phase 4의 목적은 다음 한 문장으로 요약된다.

> **“Phase 3에서 고정된 단일 Execution Route 위에  
> 실행 반복(Loop), 주문 상태 관리(State),  
> 그리고 리스크 개입의 ‘진입 지점’을 추가한다.”**

Phase 4는 **자동 매매를 ‘시작’하는 단계가 아니라**,  
자동 매매가 **구조적으로 가능해지는 최소 조건을 마련하는 단계**다.

---

## 2. Phase 4의 위치 정의

|Phase|정의|
|---|---|
|Phase 1|설계 및 스켈레톤 고정|
|Phase 1.5|실 API 관측 및 자산화|
|Phase 2|인증 및 Runtime 연결|
|Phase 3|단일 Execution Route 고정|
|**Phase 4**|**Execution Loop + State + Risk Entry**|
|Phase 5|전략 기반 자동 매매 확장|

---

## 3. Phase 4에서 “절대 하지 않는 것” (강제)

아래 항목은 Phase 4에서 **절대 수행하지 않는다.**

- ❌ 전략 성과 최적화
    
- ❌ 주문 분할 / 체결 최적화
    
- ❌ 포트폴리오 리밸런싱
    
- ❌ 멀티 브로커 동시 운용
    
- ❌ 고빈도 루프 / 스케줄러 최적화
    

Phase 4는 **“가능성 확보” 단계**이지  
**“수익 추구” 단계가 아니다.**

---

## 4. Phase 4의 핵심 산출물

Phase 4에서 반드시 확보해야 할 산출물은 다음 4가지다.

### 4.1 Execution Loop (최소 형태)

- ExecutionRoute를 반복 호출할 수 있는 구조
    
- 외부 시간 소스 / 이벤트 소스는 단순화
    
- **동기적 · 단일 루프**로 제한
    

> 핵심: “루프가 존재한다”는 사실 자체

---

### 4.2 Order State Model

- 주문의 상태를 **명시적으로 표현**
    
- 최소 상태 집합 예시:
    
    - CREATED
        
    - SUBMITTED
        
    - ACCEPTED
        
    - REJECTED
        
    - TERMINAL
        

> ExecutionResponse를 “이벤트”로 해석할 수 있어야 함

---

### 4.3 Risk Entry Point (개입 지점만 정의)

- Risk Engine의 **계산 로직은 구현하지 않음**
    
- 다음 지점에 “훅(hook)”만 배치:
    
    - Intent 생성 직전
        
    - ExecutionRoute 호출 직전
        
    - ExecutionResponse 수신 직후
        

> Phase 4의 Risk는 “차단 구조”이지 “판단 구조”가 아님

---

### 4.4 Execution Loop 통합 테스트

- 실주문 제외
    
- Noop / Mock Broker 기반
    
- “루프가 중단 없이 정상 종료되는지”만 검증
    

---

## 5. Phase 4 책임 분리 원칙

### 5.1 Execution Route (Phase 3 고정)

- ❌ 수정 금지
    
- ❌ 로직 추가 금지
    
- ✅ 그대로 호출만 허용
    

---

### 5.2 Execution Loop 책임

- 언제 실행할지
    
- 몇 번 반복할지
    
- 언제 중단할지
    

❌ 주문 판단 ❌ 전략 판단 ❌ 리스크 계산

---

### 5.3 State Layer 책임

- ExecutionResponse → Order State 변환
    
- 상태 전이 규칙 관리
    

❌ 실행 ❌ API 호출

---

### 5.4 Risk Layer 책임 (초기)

- “이 시점에 실행해도 되는가?”의 **구조적 판단**
    
- Boolean / Gate 방식만 허용
    

---

## 6. Phase 4 예상 폴더 구조 (초안)

> 기존 구조 수정 없음, **신규 레이어 추가만 허용**

```
src/runtime/
├─ execution_loop/
│  ├─ loop.py
│  ├─ controller.py
│  └─ policies/
│     └─ stop_policy.py
│
├─ execution_state/
│  ├─ order_state.py
│  └─ transition.py
│
├─ risk/
│  ├─ interfaces/
│  │  └─ risk_gate.py
│  └─ noop_risk_gate.py
```

---

## 7. 테스트 전략 (Phase 4)

### 7.1 테스트 목적

- 루프가 존재하는가
    
- 상태 전이가 발생하는가
    
- Risk Gate가 개입 가능한 구조인가
    

---

### 7.2 테스트 금지 항목

- 수익성 검증 ❌
    
- 체결 정확도 ❌
    
- 전략 우수성 ❌
    

---

## 8. Phase 4 종료 기준 (Gate E · 초안)

Phase 4는 다음 조건을 모두 만족할 경우 종료한다.

1. Execution Loop가 단일 루프로 구현됨
    
2. Order State 전이 테스트 존재
    
3. Risk Gate가 Execution 흐름에 개입 가능
    
4. Phase 3 고정 파일 무수정 보장
    
5. 실주문 경로 미사용
    

---

## 9. Phase 5로의 이관 원칙

Phase 4 종료 후:

- 전략 로직은 Phase 5에서 처음 도입
    
- Phase 4 코드는 “기반 레이어”로 유지
    
- Phase 3 + 4는 **자동 매매 실패 시 원인 분석의 기준선**이 된다
    

---

## 10. 최종 선언 (초석)

> **Phase 4는 자동 매매의 시작이 아니다.**  
> Phase 4는 자동 매매가 “무너지지 않기 위한 구조”를 만드는 단계다.
> 
> Phase 4의 성공은  
> “확장 가능한 실패”를 만드는 데 있다.

---
