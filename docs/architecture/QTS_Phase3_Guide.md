
---

# QTS Phase 3 Guide

**Order Adapter & Execution Route Integration 기준 문서 (초석 문서)**

* **File:** `QTS/docs/architecture/QTS_Phase3_Guide.md`
* **Version:** v1.0.0
* **Status:** **Enforcing (Phase 3 기준 문서)**
* **Scope:** QTS Phase 3 (Order Adapter & Execution Route Integration)
* **Input Asset:**

  * `QTS_Phase2_Assetization.md`
  * Phase 2 산출 코드 (BrokerAdapter / TokenCache)
* **Prepared At:** 2025-12-28

---

## 1. 문서의 목적

본 문서는 Phase 3에서 수행될 **주문·조회 API 연동 및 Execution Route 연결**의
범위, 책임 경계, 금지 사항을 사전에 고정하기 위해 작성되었다.

Phase 3의 목적은 다음 한 문장으로 요약된다.

> **“Phase 2에서 고정된 인증·연결 구조를 사용하여,
> QTS가 단독으로 실행 가능한 주문 흐름을 완성하고,
> 주문·조회 API를 Adapter로 확장하여
> Runtime Execution Route에 연결하되,
> ops는 주체가 아닌 ‘연결 가능한 외부 계층’으로만 취급한다.”**

본 문서는 Phase 3 전 기간 동안
**Single Source of Truth**로 사용된다.

---

## 2. Phase 3의 위치 정의

* Phase 1: 설계 및 스켈레톤 고정
* Phase 1.5: 실 API 관측 및 자산화
* Phase 2: 인증 및 Runtime 연결
* **Phase 3: 주문·조회 Adapter 및 Execution Route 연결**

Phase 3은 **“QTS 단독 실행 가능성이 최초로 확보되는 단계”**이나,
아직 자동 매매 단계는 아니다.

---

## 3. Phase 3의 핵심 산출물

Phase 3에서 반드시 확보해야 할 산출물은 다음과 같다.

1. Order Adapter 인터페이스 (Contract)

   * 주문 조회
   * 주문 요청
   * 주문 결과 수신

2. KIS Order Adapter (최소 구현)

   * 실주문 / 모의주문 구분
   * Execution Stub 연동

3. Runtime Execution Route 연결

   * Intent → Broker Order Request
   * Order Response → Runtime 모델 매핑

4. 주문 흐름 통합 테스트

   * 실주문 제외
   * Mock / Virtual Executor 기반

---

## 4. Phase 3 범위 정의

### 4.1 포함 범위

* Order Adapter 인터페이스 정의
* KIS 주문/조회 API 최소 연동
* Runtime Execution Route 사용
* Intent → Order 변환 로직
* 주문 응답 모델 고정
* 통합 테스트(E2E, 실주문 제외)

---

### 4.2 제외 범위 (강제)

아래 항목은 Phase 3에서 **절대 수행하지 않는다**.

* 자동 매매 루프
* 주문 분할 / 최적화
* 전략 평가 로직 고도화
* 리스크 엔진 본격 연동
* ops 자동화 확장
* 멀티 브로커 동시 지원

해당 항목은 Phase 4 이후의 책임이다.

---

## 5. 책임 분리 (Phase 2 계약 상속)

### 5.1 Adapter 책임

* 주문/조회 요청 구성
* 외부 브로커 API 호출
* 응답 수신 및 파싱
* Runtime에 결과 전달

❌ 토큰 관리
❌ 실행 판단
❌ 재시도 정책 보유

---

### 5.2 Runtime 책임

* Execution Route 관리
* Intent → Adapter 호출
* Order Response 상태 반영
* 실패/중단 판단

❌ 인증 파라미터 관리
❌ 주문 로직 자체 판단

---

## 6. Phase 3 폴더 구조 기준 (초안)

Phase 3에서는 아래 구조가 **추가**된다.
(기존 Phase 2 구조 수정 없음)

```
src/runtime/
├─ broker/
│  ├─ base.py              # Phase 2 (유지)
│  ├─ order_base.py        # Phase 3 Order Adapter 인터페이스
│  └─ kis/
│     ├─ adapter.py        # Phase 2 (유지)
│     └─ order_adapter.py # Phase 3 KIS 주문 Adapter
│
├─ execution/
│  ├─ interfaces/
│  │  └─ order_executor.py
│  └─ models/
│     ├─ order_request.py
│     └─ order_response.py
```

---

## 7. 테스트 전략

### 7.1 테스트 위치

```
tests/runtime/execution/
tests/runtime/broker/
```

* Adapter 단위 테스트
* Execution Route 통합 테스트
* Mock / Virtual Executor 우선 사용

---

### 7.2 테스트 원칙

* 실주문 기본 제외
* 실패 응답도 정상 시나리오로 테스트
* Execution Route 단절 시 명확한 실패 보장

---

## 8. Phase 3 종료 기준 (Gate D)

Phase 3는 다음 조건을 모두 만족할 경우 종료한다.

1. Order Adapter 인터페이스가 고정됨
2. KIS 주문/조회 API 최소 연동 성공
3. Intent → Order → Response 흐름 검증
4. Phase 2 계약 무변경 보장
5. 자동 매매 루프 미존재 확인

---

## 9. Phase 4 이관 규칙

Phase 3 종료 후:

* Phase 4에서 자동 매매 루프 및 리스크 제어 착수
* Phase 3 코드는 **사용 대상**이나 **수정 대상은 아님**

---

## 10. 최종 선언

> **Phase 3은 QTS 단독 실행 가능성을 확보하는 단계다.**
> Phase 3은 자동화가 아니다.
> Phase 3은 ops 없이도 성립해야 하며,
> Phase 4의 실패를 예방하기 위해 존재한다.

---

### 판단 요약

* **방향 변경 없음**
* **목표 축소/확대 없음**
* **문서-현실 간 불일치만 제거**

---
