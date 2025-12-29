
---

# QTS Phase 6 Guide

**Strategy Multiplexing · Risk Hardening · Execution Stability**

- **File:** `QTS/docs/architecture/QTS_Phase6_Guide.md`
    
- **Version:** v0.1.0
    
- **Status:** Draft (Phase 6 초석 문서)
    
- **Prerequisite:** Phase 5 Assetization 완료
    

---

## 1. Phase 6의 목적

Phase 6의 목적은 다음 한 문장으로 정의된다.

> **“단일 전략·단일 리스크 정책으로 고정된 Phase 5 구조를  
> ‘확장 가능한 판단 시스템’으로 진화시킨다.”**

Phase 6은 자동매매의 확장이 아니라,  
**판단 구조의 안정화와 다중화**를 목표로 한다.

---

## 2. Phase 6의 위치 정의

|Phase|역할|
|---|---|
|Phase 4|Execution Loop 안정화|
|Phase 5|Strategy + Risk 최초 연결|
|**Phase 6**|**Strategy 다중화 + Risk 고도화**|
|Phase 7|Portfolio Risk / Capital Allocation|

Phase 6은 **전략을 늘리는 첫 단계**이지만,  
운영 최적화 단계는 아니다.

---

## 3. Phase 6에서 허용되는 확장

Phase 6부터 다음 항목이 허용된다.

### 3.1 Strategy Multiplexing

- 복수 Strategy 동시 등록
    
- Strategy 간 독립적 Intent 생성
    
- Strategy 식별자(id / name) 도입
    
- Strategy 단위 Enable / Disable
    

### 3.2 Risk Hardening

- RiskCalculator 정책 세분화
    
- Strategy별 Risk 정책 적용
    
- RiskGate 단계화 (Warn / Reduce / Block)
    
- 보수적 기본값 적용
    

### 3.3 Intent Arbitration (제한적)

- 동일 Symbol에 대한 Intent 충돌 정리
    
- 동일 Side 중복 Intent 병합
    
- 상충 Intent 단순 규칙 기반 처리
    

---

## 4. Phase 6에서 금지되는 것

다음 항목은 Phase 6에서도 금지된다.

- 포트폴리오 리밸런싱
    
- 자본 배분 최적화
    
- 성과 기반 전략 선택
    
- 고빈도 스케줄링
    
- 실전 수익 검증 중심 설계
    

Phase 6은 **구조 안정화 페이즈**다.

---

## 5. 핵심 설계 원칙

### 5.1 Strategy는 서로를 모른다

- Strategy 간 직접 참조 금지
    
- 공통 상태 공유 금지
    
- Strategy 간 통신은 오직 상위 조정자만 수행
    

---

### 5.2 Risk는 Strategy 단위를 존중한다

- RiskCalculator는 Strategy Context를 인지할 수 있다
    
- 단, Execution Context는 여전히 알지 못한다
    
- Strategy별 Risk 설정 가능
    

---

### 5.3 Execution Loop는 그대로 유지된다

- Phase 4에서 고정된 Loop 수정 최소화
    
- Phase 6은 Loop 외부에서만 확장
    
- Loop는 “허용된 Intent 집합”만 처리
    

---

## 6. Phase 6 예상 신규 레이어

```
src/runtime/
├─ strategy/
│  ├─ interfaces/
│  │  └─ strategy.py
│  ├─ registry/
│  │  └─ strategy_registry.py
│  ├─ multiplexer/
│  │  └─ strategy_multiplexer.py
│  └─ simple_strategy.py
│
├─ risk/
│  ├─ calculators/
│  │  ├─ base_risk_calculator.py
│  │  └─ strategy_risk_calculator.py
│  ├─ gates/
│  │  └─ staged_risk_gate.py
│  └─ policies/
│     └─ risk_policy.py
```

---

## 7. Phase 6 테스트 방향

Phase 6 테스트는 **확장 안정성 증명**이 목적이다.

### 7.1 Strategy 테스트

- 다중 Strategy 등록/해제 테스트
    
- Strategy별 Intent 독립성 검증
    
- Strategy 실패가 전체를 깨지 않음
    

### 7.2 Risk 테스트

- Strategy별 Risk 정책 적용 테스트
    
- Risk 단계별 동작 테스트 (Reduce / Block)
    
- 기존 Phase 5 Risk 테스트 유지
    

### 7.3 통합 테스트

- Multi-Strategy → Intent 집합 생성
    
- RiskGate 통과 후 Loop 진입
    
- Phase 4 Loop 무수정 상태 유지
    

---

## 8. Phase 6 종료 기준 (Gate G)

Phase 6은 다음 조건이 충족되면 종료된다.

1. 복수 Strategy 동시 운용 가능
    
2. Strategy별 Risk 정책 적용 가능
    
3. Intent 충돌이 단순 규칙으로 해소됨
    
4. Phase 5 테스트 전부 유지
    
5. Runtime 전체 회귀 테스트 통과
    

---

## 9. Phase 6의 성공 기준

Phase 6의 성공은 다음으로 판단한다.

- 전략 수가 늘어나도 구조가 흔들리지 않는다
    
- 리스크 정책이 복잡해져도 Gate가 단일 진입점이다
    
- Execution Loop는 여전히 단순하다
    

---

## 10. 최종 선언 (초석)

> Phase 6은  
> **QTS가 ‘확장 가능한 판단 시스템’임을 증명하는 단계**다.
> 
> 이 페이즈의 목표는  
> 더 많은 수익이 아니라  
> **더 많은 전략을 견딜 수 있는 구조**다.

---
