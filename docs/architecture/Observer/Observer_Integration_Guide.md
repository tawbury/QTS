
---

# QTS Observer 연동 개발 가이드

_(Decision 중심 최소 루트 기준)_

---

## 1. 문서의 목적과 전제

본 문서는 현재 QTS 프로젝트의 실제 폴더 구조와 메인 아키텍처를 근거로 하여, **Observer 프로젝트를 QTS 메인 시스템과 연동하기 위한 최소 개발 루트**를 정의한다.

이 가이드는 다음을 전제로 한다.

- QTS는 이미 **Observer → Decision 중심 구조**를 채택하고 있다.
    
- 실매매, 브로커 연동, 포트폴리오 운용은 **현재 범위에 포함되지 않는다**.
    
- 본 가이드의 목표는 “완성”이 아니라 **구조적으로 올바른 연결 상태를 확보하는 것**이다.
    
- Phase 15에서 검증된 Observer의 역할과 책임은 유지된다.
    

---

## 2. 현재 QTS 구조의 핵심 해석

### 2.1 구조적 중심축

현재 QTS의 구조적 중심은 다음 두 영역이다.

1. **ops/observer/**
    
    - 시장·시계열 데이터를 관측하고
        
    - 분석·신호·패턴을 생성하며
        
    - Snapshot 단위로 외부로 전달하는 역할
        
2. **ops/decision_pipeline/**
    
    - Observer가 전달한 Snapshot을 입력으로 받아
        
    - ETEDA(Act 제외) 흐름에 따라
        
    - “판단 결과”를 생성하는 책임 계층
        

즉, QTS는 이미 다음과 같은 흐름을 전제로 설계되어 있다.

```
Market / Data
   ↓
Observer (snapshot)
   ↓
Decision Pipeline (ETED[A-])
   ↓
Execution Stub (noop)
```

이 구조는 **실행을 제외한 자동매매의 모든 핵심 판단 계층이 이미 준비된 상태**임을 의미한다.

---

## 3. Observer의 QTS 내 역할 정의

### 3.1 Observer의 책임 범위

Observer는 QTS 내에서 다음 책임만을 가진다.

- 외부 데이터(틱, 현재가, 시계열)를 수신한다.
    
- Validation / Guard를 거쳐 Snapshot을 생성한다.
    
- EventBus를 통해 Snapshot을 하위 소비자에게 전달한다.
    

Observer는 다음을 **절대 수행하지 않는다**.

- 매매 판단
    
- 조건식 점수화
    
- 전략 선택
    
- 실행 여부 결정
    

이 책임 분리는 이미 `ops/observer/observer.py` 및 관련 계약 구조에 반영되어 있다.

---

### 3.2 Snapshot의 위상

`ops/observer/snapshot.py`에서 정의되는 Snapshot은:

- **관측 결과의 최소 단위**
    
- QTS Decision Pipeline이 소비하는 **유일한 입력 계약**
    

Snapshot은 “의미 해석 결과”가 아니라 **관측과 분석의 결과 묶음**이며,  
의사결정의 책임은 전적으로 Decision Pipeline에 있다.

---

## 4. Decision Pipeline의 위치와 역할

### 4.1 Decision Pipeline의 책임

`src/ops/decision_pipeline/`은 QTS 메인 시스템의 판단 코어다.

이 계층은 다음을 수행한다.

- Observer Snapshot을 입력으로 수신
    
- Extract → Transform → Evaluate → Decide 단계 수행
    
- 실행을 수반하지 않는 **결정 결과** 생성
    

실행 단계는 명시적으로 제외되어 있으며, 이는 구조적으로 다음 폴더에서 보장된다.

```
ops/decision_pipeline/execution_stub/
```

여기서 제공되는 `noop_executor`는 **실행이 존재하지 않음을 명확히 선언하는 구조적 장치**다.

---

### 4.2 ETEDA 구조 해석 (Act 제외)

현재 QTS의 ETEDA 구조는 다음과 같이 고정된다.

- Extract: Snapshot 구조 해석
    
- Transform: 판단용 정규화
    
- Evaluate: 조건·신호·판단 평가
    
- Decide: “행동 여부” 결정 (행동은 없음)
    
- Act: **존재하지만 실행되지 않음**
    

이는 QTS가 “결정 시스템”으로서 완결성을 갖추었음을 의미한다.

---

## 5. Observer → Decision 연결 기준

### 5.1 연결 방식의 원칙

Observer와 Decision Pipeline의 연결은 다음 원칙을 따른다.

- Observer는 Decision Pipeline의 내부 구조를 알지 못한다.
    
- Decision Pipeline은 Observer의 구현 상세를 알지 못한다.
    
- 양쪽은 **계약(Snapshot / DecisionSnapshot)** 으로만 연결된다.
    

이 원칙은 이미 다음 구조로 반영되어 있다.

```
ops/
 ├─ observer/
 │   └─ snapshot.py
 │
 └─ decision_pipeline/
     └─ contracts/
         └─ decision_snapshot.py
```

---

### 5.2 실제 연결 지점

실제 연결은 Runtime 계층에서 수행된다.

```
ops/runtime/
 ├─ observer_runner.py
 └─ debug_runner.py
```

이 Runner들은 다음 역할을 가진다.

- Observer 인스턴스 생성
    
- EventBus 구성
    
- Snapshot 소비자(Decision Pipeline Runner) 연결
    
- 실행 환경 제어 (mock / debug / maintenance)
    

즉, **Observer와 Decision을 직접 결합하지 않고 Runtime에서 결합**하는 구조다.

---

## 6. 현재 단계에서 구현해야 할 것과 하지 말아야 할 것

### 6.1 반드시 유지해야 할 것

- Observer → Snapshot → Decision Pipeline 흐름
    
- execution_stub 기반의 “비실행 결정 구조”
    
- EventBus를 통한 비결합 이벤트 전달
    
- tests/ops/e2e 및 decision pipeline smoke 테스트
    

---

### 6.2 지금 단계에서 추가 구현이 불필요한 것

- 브로커 어댑터
    
- 주문 모델
    
- 실계좌 연동
    
- 포트폴리오 엔진
    
- 리스크 엔진 확장
    
- 전략 점수화 고도화
    

이 요소들은 **Decision 결과가 실제로 의미를 갖는 시점 이후**에만 필요하다.

---

## 7. 테스트 기준

현재 QTS에서의 테스트 기준은 다음과 같다.

- Observer 단독 테스트:  
    `tests/ops/observation/*`
    
- Decision Pipeline 단독 테스트:  
    `tests/ops/decision/test_pipeline_smoke.py`
    
- Observer → Decision 연계 테스트:  
    `tests/ops/e2e/test_phase7_decision_pipeline.py`
    

이 테스트들이 모두 통과한다면,  
**Observer와 QTS Core의 연결은 구조적으로 완료된 상태**로 간주한다.

---

## 8. 이 가이드의 종료 선언

본 가이드의 범위는 다음 시점에서 종료된다.

- Observer Snapshot이 Decision Pipeline에 정상적으로 유입되고
    
- ETEDA(Act 제외) 전 구간을 통과하며
    
- 결정 결과가 생성되고
    
- 어떠한 실행도 발생하지 않는 것이 보장될 때
    

이 상태는 **“QTS가 관측 기반 판단 시스템으로서 준비 완료”** 상태를 의미한다.

이후 단계(브로커, 실매매, 포트폴리오)는  
본 가이드와 **완전히 분리된 새로운 설계 문서**에서 다룬다.

---

## 최종 요약

- 현재 QTS 구조는 이미 Observer 연동을 전제로 설계되어 있다.
    
- Phase 15는 그 설계를 실데이터 관점에서 검증한 단계였다.
    
- 이제 QTS는 **Observer를 입력으로 받는 Decision 시스템**으로서 충분히 자립적이다.
    
- 추가 확장은 “필요해지는 시점”에만 설계한다.
    

이 문서는 그 상태를 **구조적으로 고정**하기 위한 기준 문서다.