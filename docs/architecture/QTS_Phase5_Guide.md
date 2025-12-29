
---

# QTS Phase 5 Guide (초석 문서)

**Strategy Entry · Risk Calculation · Execution Expansion 기준**

- **File:** `QTS/docs/architecture/QTS_Phase5_Guide.md`
    
- **Version:** v0.1.0
    
- **Status:** Draft (Phase 5 초석 문서)
    
- **Prerequisite:** Phase 4 Assetization 완료
    

---

## 1. Phase 5의 목적

Phase 5의 목적은 다음 한 문장으로 요약된다.

> **“Phase 4에서 고정된 실행 기반 위에  
> 전략 판단과 리스크 계산을 ‘처음으로’ 연결한다.”**

Phase 5는  
자동 매매의 **시작점**이며,  
QTS가 **판단하는 시스템**으로 진입하는 최초 단계다.

---

## 2. Phase 5의 위치 정의

|Phase|정의|
|---|---|
|Phase 3|단일 Execution Route 고정|
|Phase 4|Loop · State · Risk Entry|
|**Phase 5**|**Strategy + Risk Calculation**|
|Phase 6|전략 다중화 및 안정화|

---

## 3. Phase 5에서 새로 허용되는 것

Phase 5부터 다음이 **처음으로 허용**된다.

- 전략 판단 로직 도입
    
- 신호 기반 Intent 생성
    
- Risk 계산 로직 구현
    
- Risk Gate 내부 로직 확장
    
- 상태 기반 실행 제어
    

---

## 4. Phase 5에서 여전히 금지되는 것

아래 항목은 Phase 5에서도 금지된다.

- 고빈도 스케줄링
    
- 포트폴리오 리밸런싱
    
- 멀티 브로커 동시 운용
    
- 성능 최적화 목적의 복잡화
    

---

## 5. Phase 5 핵심 설계 원칙

### 5.1 Strategy는 Execution을 모른다

- Strategy는 Intent만 생성
    
- Execution Loop / Route는 Strategy를 참조하지 않음
    

### 5.2 Risk는 차단과 계산을 모두 수행

- Phase 4: 차단만
    
- Phase 5: 계산 + 차단
    

### 5.3 Loop는 그대로 유지

- Phase 4 Loop 수정 최소화
    
- Strategy는 Loop 외부에서 주입
    

---

## 6. Phase 5 예상 신규 레이어

```
src/runtime/
├─ strategy/
│  ├─ interfaces/
│  │  └─ strategy.py
│  └─ simple_strategy.py
│
├─ risk/
│  ├─ calculators/
│  │  └─ base_risk_calculator.py
│  └─ gates/
│     └─ calculated_risk_gate.py
```

---

## 7. Phase 5 테스트 방향

- Strategy 단위 테스트
    
- Risk 계산 단위 테스트
    
- Phase 4 Loop + Strategy 통합 테스트
    
- 실주문 금지 유지
    

---

## 8. Phase 5 종료 예고 (Gate F · 예고)

Phase 5는 다음이 충족되면 종료된다.

1. Strategy → Intent 흐름 구현
    
2. Risk 계산 결과가 Gate에 반영
    
3. Loop 수정 없이 전략 실행 가능
    
4. Phase 4 테스트 전부 유지
    

---

## 9. 최종 선언 (초석)

> Phase 5는  
> **QTS가 ‘판단을 시작하는 최초의 단계’**다.
> 
> 그러나 Phase 5의 성공 기준은  
> 수익이 아니라 **구조적 일관성**이다.

---
