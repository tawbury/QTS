
---

# QTS Phase 6.5 Guide

**Operational Safety · Data Retention · ops-Ready Boundary**

* **File:** `QTS/docs/architecture/QTS_Phase6_5_Guide.md`
* **Version:** v1.0.0
* **Status:** Foundation (Phase 6.5 초석 문서)
* **Prerequisite:** Phase 6 Assetization 완료

---

## 1. Phase 6.5의 목적

Phase 6.5의 목적은 다음 한 문장으로 정의된다.

> **“QTS Core를 장시간 무인 실행해도 구조적으로 망가지지 않게 만든다.”**

Phase 6.5는
판단 구조를 확장하지 않으며,
전략·리스크 로직을 변경하지 않는다.

이 페이즈는 오직 **운영 안전성(Operation Safety)**을 다룬다.

---

## 2. Phase 6.5의 위치 정의

| Phase         | 역할                     |
| ------------- | ---------------------- |
| Phase 6       | 판단 구조 확장 가능성 증명        |
| **Phase 6.5** | **운영 안전성 최소 완결**       |
| Phase 7       | Portfolio / Capital 확장 |

Phase 6.5는 **Core 완성 이후의 보강 단계**이며,
Core 판단 흐름에는 개입하지 않는다.

---

## 3. Phase 6.5의 핵심 원칙

### 3.1 Core 판단 구조 불변

* Strategy / Risk / Execution 구조 수정 금지
* Phase 6에서 확정된 판단 파이프라인 유지
* ops는 Core를 “감싸는 역할”만 수행

---

### 3.2 Backup-First Retention Automation

* 데이터 삭제는 항상 **백업 성공 이후에만 허용**
* 사람 승인 없는 무인 운영 전제
* 실패 시 **보존이 기본값**

> 데이터 손실 가능성이 있는 자동화는 Phase 6.5에서 허용되지 않는다.

---

### 3.3 ops는 주체가 아니다

* ops 미존재 상태에서도 QTS Core는 정상 실행 가능해야 한다
* ops는 **연결 가능(optional)** 상태로만 준비
* ops 장애는 Core 판단에 영향을 주지 않는다

---

## 4. Phase 6.5에서 허용되는 작업 범위

Phase 6.5에서는 다음 항목만 허용된다.

### 4.1 Data Retention & Cleanup

* 만료 데이터 스캔
* 백업 완료 데이터에 한해 자동 삭제
* 클린업 로그 생성 및 고정 위치 기록

---

### 4.2 Automation Safety Test

* backup → retention → cleanup E2E 테스트
* 실패 시 삭제 미발생 검증
* 중복 실행에 대한 안정성 검증(idempotency)

---

### 4.3 Test Structure 정비 (ops 기준)

* `tests/ops/{decision,e2e,maintenance}` 구조 사용
* 신규 테스트는 maintenance부터 해당 구조 채택
* 기존 테스트 재배치는 Phase 6.5 범위 밖

---

### 4.4 Log & Artifact 고정

* 자동화 로그 경로 고정
* 임시 로그 루트 생성 금지
* 실행 결과는 항상 재현 가능해야 함

---

## 5. Phase 6.5에서 금지되는 것들

다음 항목은 Phase 6.5에서도 명시적으로 금지된다.

* 전략 추가 또는 변경
* Risk 정책 조정
* Execution Loop 수정
* ops가 판단을 수행하는 구조
* 성능/효율/속도 최적화
* 데이터 삭제를 전제로 한 설계

Phase 6.5는 **안전성 확보 페이즈**다.

---

## 6. Phase 6.5 예상 작업 레이어

```
src/
├─ ops/
│  ├─ maintenance/
│  │  ├─ backup/
│  │  ├─ retention/
│  │  └─ cleanup/
│  └─ logs/
│
tests/
├─ ops/
│  ├─ maintenance/
│  │  └─ test_automation_e2e.py
│  ├─ decision/
│  └─ e2e/
```

> Core(`src/runtime`) 하위 구조는 변경 대상이 아니다.

---

## 7. Phase 6.5 테스트 방향

Phase 6.5 테스트의 목적은 단 하나다.

> **“자동화가 실패해도 데이터는 살아남는다.”**

### 필수 테스트 조건

1. 백업 실패 시 삭제 미발생
2. 중복 실행 시 결과 안정성 유지
3. 클린업 로그 생성 경로 고정
4. ops 미연결 상태에서도 Core 테스트 영향 없음

---

## 8. Phase 6.5 종료 기준 (Gate H)

Phase 6.5는 다음 조건이 충족되면 종료된다.

1. Backup-first retention 자동화 동작
2. 실패 시 데이터 보존 보장
3. 자동 클린업 로그 고정
4. ops 테스트 구조 확정
5. Phase 6 Core 테스트 전부 유지

---

## 9. Phase 6.5 종료 시 QTS 상태

Phase 6.5 종료 시점의 QTS는 다음 상태에 도달한다.

* 장시간 무인 실행 가능한 Core
* 데이터 손실 위험이 제거된 자동화
* ops 연결 준비 완료 (비주도)
* Phase 7 확장을 위한 안전한 기반 확보

---

## 10. 최종 선언 (초석)

> Phase 6.5는
> **QTS를 “돌려도 되는 시스템”으로 만드는 마지막 안전 단계**다.
>
> 이 페이즈의 목표는
> 더 많은 기능이 아니라
> **망가지지 않는 운영**이다.

---

