
---

# QTS Phase 5 Assetization

**Strategy Entry · Risk Calculation · Execution Control**

- **File:** `QTS/docs/architecture/QTS_Phase5_Assetization.md`
    
- **Version:** v1.0.0
    
- **Status:** Enforced
    
- **Prerequisite:** Phase 4 Assetization 완료
    

---

## 1. Phase 5의 공식 정의

Phase 5는 QTS 실행 아키텍처에  
**전략 판단(Strategy)과 리스크 계산(Risk Calculation)을 최초로 연결한 페이즈**다.

본 페이즈를 통해 QTS는 다음 상태로 전환된다.

> **“단순 실행 시스템” → “판단·계산·제어가 분리된 실행 시스템”**

Phase 5의 성공 기준은 수익이나 성능이 아니라,  
**구조적 일관성과 책임 분리의 완결성**이다.

---

## 2. Phase 5의 위치와 역할

|Phase|역할|
|---|---|
|Phase 3|Execution Route 고정|
|Phase 4|Loop · State · Risk Entry|
|**Phase 5**|**Strategy 판단 + Risk 계산 연결**|
|Phase 6|전략 다중화 및 리스크 고도화|

Phase 5는 자동매매의 “시작점”이지만,  
운영 단계가 아닌 **구조 확립 단계**에 해당한다.

---

## 3. 핵심 구조 자산

### 3.1 Strategy Layer

- Strategy는 **Execution과 Loop를 알지 않는다**
    
- Strategy의 출력은 오직 `Intent`
    
- Strategy는 실행 경로를 직접 호출하지 않는다
    

이를 통해 다음이 보장된다.

- 전략 교체 및 다중화 가능성
    
- Execution Layer의 안정성 유지
    
- 전략 로직의 독립적 테스트 가능
    

---

### 3.2 Risk Calculation Layer

- RiskCalculator는 **계산만 수행**
    
- 차단 여부 판단은 Gate에 위임
    
- 계산 결과는 `RiskResult`로 명시화
    

Risk 계산은 정책이 아니라 **데이터 생성 행위**로 정의된다.

---

### 3.3 Calculated Risk Gate

- RiskGate는 리스크 제어의 단일 진입점이다
    
- 동작 순서는 다음과 같다.
    

1. 원본 Intent 기준 Risk 계산
    
2. 허용 가능한 최대 수량 기준 qty 조정
    
3. **조정된 qty 기준 risk_score 재평가**
    
4. 최종 허용/차단 결정
    

이를 통해 Phase 5의 Risk 정책이 코드와 테스트로 고정된다.

---

## 4. Execution Loop와의 관계

- Phase 4에서 고정된 Execution Loop는 **수정되지 않는다**
    
- Strategy와 Risk는 Loop 외부에서 주입된다
    
- Loop는 허용된 Intent만을 처리한다
    

이 구조로 인해 다음이 보장된다.

- 기존 실행 자산의 무결성 유지
    
- Phase 간 책임 침범 방지
    
- Phase 6 이후 확장의 안정성 확보
    

---

## 5. 테스트 자산화 결과

Phase 5는 다음 테스트 자산을 공식 기준으로 포함한다.

### 5.1 단위 테스트

- Strategy 단위 테스트
    
- RiskCalculator 단위 테스트
    
- RiskGate 정책 테스트
    

### 5.2 통합 테스트

- Strategy → Risk → Gate → Loop 연결 테스트
    
- Phase 4 Loop 무수정 상태 유지 검증
    

### 5.3 회귀 테스트

- `tests/runtime` 전체 테스트 통과
    
- Phase 1~4 기능 무결성 유지 확인
    

이 테스트들은 Phase 6 이후에도 **기준선(Baseline)** 으로 유지된다.

---

## 6. Phase 5에서 고정된 원칙

Phase 5를 통해 다음 원칙이 **변경 불가 기준**으로 확정된다.

1. Strategy는 Execution을 알지 않는다
    
2. Risk 계산과 차단은 분리된다
    
3. Risk 정책은 Gate에서만 제어된다
    
4. Execution Loop는 상위 Phase에서 보호된다
    

---

## 7. Phase 6로의 연결 기준

Phase 6에서는 다음 확장이 허용된다.

- Strategy 다중화
    
- RiskCalculator 정책 세분화
    
- RiskGate 보수화 및 포트폴리오 리스크 확장
    

단, Phase 5에서 확정된 책임 분리와 테스트 기준은 유지되어야 한다.

---

## 8. 결론

Phase 5는 기능 추가 페이즈가 아니다.  
**QTS가 판단을 시작할 수 있는 최소 구조를 완성한 페이즈**다.

QTS는 이제 다음 구조를 갖는다.

> **판단(Strategy) → 계산(Risk) → 제어(Gate) → 실행(Loop)**

이 구조는 테스트로 검증되었으며,  
향후 모든 확장의 기준으로 사용된다.

---
