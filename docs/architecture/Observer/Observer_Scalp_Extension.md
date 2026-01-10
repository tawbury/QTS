
---

# 📄 QTS Observer – Scalping Extension Design (Draft)

## 문서 목적

본 문서는 **QTS Observer-Core의 스켈프(Scalping) 확장을 위한 설계 문서**이다.  
본 문서는 **코드 변경을 요구하지 않으며**,  
향후 Phase 3~5 개발 시 **확장 방향과 경계를 고정**하기 위한 참조 문서로 사용한다.

---

## 1. 현재 Observer-Core 상태 요약 (기준선)

### 1.1 현재 Observer의 역할 (Phase 2 기준)

- ObservationSnapshot 수신
    
- PatternRecord 생성
    
- EventBus를 통한 append-only 로그 기록
    

### 1.2 현재 Observer가 “하지 않는 것”

- 실시간 루프 제어
    
- 판단 / 조건 평가
    
- 실행 / 주문
    
- 데이터 해석
    

👉 **Observer는 순수 데이터 수집기(Data Producer)** 로 고정되어 있다.

---

## 2. 스켈프 Observer의 본질적 요구사항

스켈프용 Observer는 기존 Observer와 **목적이 다르다**.

|항목|기존 Observer|스켈프 Observer|
|---|---|---|
|시간 해상도|초/분 단위|ms ~ 수십 ms|
|데이터 밀도|낮음|매우 높음|
|분석 목적|패턴 누적|즉시성 + 반복 패턴|
|주요 관심사|상태 기록|**변화·간격·반응**|

---

## 3. 스켈프 확장에서 “변하지 않는 것” (고정 선언)

아래 항목은 **절대 변경하지 않는다.**

### 3.1 Observer-Core 구조

- Observer → PatternRecord → EventBus → Sink 구조 유지
    
- Snapshot / PatternRecord 개념 유지
    
- append-only 로그 정책 유지
    

### 3.2 기존 데이터 호환성

- Phase 2에서 쌓인 모든 JSONL 데이터는
    
    - Phase 3~5에서도 그대로 사용 가능해야 한다.
        
- 스켈프 확장은 **추가 필드 방식**으로만 진행한다.
    

---

## 4. 스켈프 확장을 위한 핵심 확장 포인트

### 4.1 Snapshot 확장 (구조 변경 ❌, 필드 추가 ⭕)

#### 추가될 가능성 있는 필드 (예시)

```json
meta: {
  iteration_id: 102341,
  loop_interval_ms: 25,
  latency_ms: 4,
  tick_source: "websocket"
}
```

- iteration_id: 루프 반복 카운터
    
- loop_interval_ms: 목표 루프 주기
    
- latency_ms: 수집 지연
    
- tick_source: 데이터 유입 채널
    

⚠️ 기존 필드 삭제/변경 없음

---

### 4.2 PatternRecord 확장 슬롯 활용

현재 비어 있는 필드들이 **스켈프 확장의 핵심 공간**이다.

|필드|스켈프 활용|
|---|---|
|regime_tags|변동성 구간, 속도 레짐|
|condition_tags|초단기 패턴 태그|
|outcome_labels|즉시 반응 결과|

👉 Phase 2에서 비워둔 판단이  
Phase 4~5에서 **사후 라벨링 방식**으로 채워진다.

---

## 5. 스켈프 Observer의 “역할 경계”

### 5.1 Observer가 여전히 하지 않는 것

- 진입/청산 판단
    
- 주문 실행
    
- 포지션 관리
    

👉 **아무리 스켈프라도 Observer는 판단하지 않는다.**

---

### 5.2 Observer가 추가로 “기록만” 하는 것

- 고빈도 시간 정보
    
- 루프 반복 정보
    
- 데이터 누락/지연 여부
    

---

## 6. 성능/안정성 관점의 확장 전략

### 6.1 단기 전략 (Phase 3~4)

- JSONL 분할 정책 (파일 로테이션)
    
- 메모리 버퍼 → 배치 flush
    
- Sink 비동기화 가능성 검토
    

### 6.2 중장기 전략 (Phase 5 이후)

- Raw tick 저장 vs Feature-only 저장 분리
    
- 샘플링 정책 도입
    
- 고빈도 → 저빈도 압축 파이프라인
    

---

## 7. 단계별 확장 로드맵 (Observer 관점)

|Phase|Observer 변화|
|---|---|
|Phase 2|기본 수집 코어|
|Phase 3|Validation / Guard|
|Phase 4|스켈프용 필드 추가|
|Phase 5|고빈도 최적화|
|Phase 6|분석/학습 파이프라인 연결|

---

## 8. 최종 선언 (중요)

> **스켈프 확장은  
> Observer-Core를 “다시 만드는 작업”이 아니다.**
> 
> **이미 완성된 수집 코어 위에  
> 정보 밀도를 높이는 작업일 뿐이다.**

이 문서는

- 코드 변경의 트리거가 아니라
    
- **변경을 통제하기 위한 기준 문서**다.
    

---
