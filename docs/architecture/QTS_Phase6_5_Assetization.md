
---

# QTS Phase 6.5 Assetization

**Operational Safety · Data Retention · ops-Ready Boundary**

* **File:** `QTS/docs/architecture/QTS_Phase6_5_Assetization.md`
* **Version:** v1.0.0
* **Status:** Assetized
* **Prerequisite:** Phase 6 Assetization 완료

---

## 1. 문서의 목적

본 문서는 QTS Phase 6.5에서 확정된 설계·구현·검증 결과를
**변경 불가한 자산(Asset)** 으로 고정하기 위해 작성된다.

이 문서는 다음을 수행한다.

* Phase 6.5의 역할과 경계를 명확히 기록한다
* 운영 안전성 확보를 위해 채택된 구조를 고정한다
* 이후 페이즈에서 침범해서는 안 되는 기준선을 제공한다

본 문서는 Phase 6.5 종료 이후에도 **참조 기준 문서로 유지**된다.

---

## 2. Phase 6.5의 위치 정의

Phase 6.5는 QTS 전체 로드맵에서 다음 위치를 갖는다.

| Phase         | 역할                     |
| ------------- | ---------------------- |
| Phase 6       | Core 판단 구조 확정          |
| **Phase 6.5** | **운영 안전성 최소 완결**       |
| Phase 7       | Portfolio / Capital 확장 |

Phase 6.5는 기능 확장이 아닌,
**Core 완성 이후의 운영 안정성 봉인 단계**다.

---

## 3. Phase 6.5의 목적

Phase 6.5의 목적은 다음 한 문장으로 정의된다.

> **“QTS Core를 장시간 무인 실행해도 구조적으로 망가지지 않게 만든다.”**

이를 위해 Phase 6.5는 다음을 전제로 한다.

* 판단 구조를 확장하지 않는다
* 전략·리스크·실행 로직을 변경하지 않는다
* ops는 Core를 감싸는 보조 레이어로만 존재한다

---

## 4. 핵심 설계 원칙

### 4.1 Core 판단 구조 불변

* Strategy / Risk / Execution 구조는 Phase 6 기준으로 고정된다
* ops는 판단을 수행하지 않는다
* ops 장애는 Core 판단 흐름에 영향을 주지 않는다

---

### 4.2 Backup-First Retention Automation

* 데이터 삭제는 **항상 백업 성공 이후에만 허용**된다
* 백업 실패 시 삭제는 절대 발생하지 않는다
* 사람 승인 없는 무인 운영을 전제로 한다

이 원칙은 정책이 아니라 **코드 레벨에서 강제**된다.

---

### 4.3 ops 비주도 원칙

* ops는 선택적으로 연결 가능한 레이어다
* ops가 없어도 QTS Core는 정상 실행되어야 한다
* ops는 Core의 판단 책임을 가지지 않는다

---

## 5. Phase 6.5 구현 구조

### 5.1 ops/maintenance 전용 안전 레이어

Phase 6.5에서는 기존 ops 구조와 명확히 분리된
**전용 maintenance 레이어**를 도입하였다.

```
src/
└─ ops/
   ├─ maintenance/
   │  ├─ backup/
   │  │  └─ runner.py
   │  ├─ retention/
   │  │  ├─ policy.py
   │  │  └─ scanner.py
   │  ├─ cleanup/
   │  │  └─ executor.py
   │  ├─ coordinator.py
   │  └─ __init__.py
   ├─ logs/
   │  └─ maintenance/
   │     └─ cleanup.log
```

이 레이어는 다음 특성을 가진다.

* Phase 6.5 전용
* Core 및 기존 ops 레이어 미침범
* Phase 7 이후에도 구조 변경 없이 유지

---

## 6. 자동화 흐름 정의

Phase 6.5 자동화는 단일 진입점과 고정된 흐름을 가진다.

```
backup → retention(scan only) → cleanup
```

### 6.1 Backup

* 모든 자동화의 선행 조건
* 백업 실패 시 이후 단계는 의미를 갖지 않는다

### 6.2 Retention

* 만료 대상 **산출만 수행**
* 실제 삭제는 수행하지 않는다

### 6.3 Cleanup

* backup 성공 조건 하에서만 실행
* 실패 시 데이터는 보존된다
* 모든 결과는 고정 로그 경로에 기록된다

---

## 7. 로그 및 아티팩트 고정

* 로그 경로는 다음으로 고정된다

```
src/ops/logs/maintenance/cleanup.log
```

* 루트 로그 생성 금지
* 임시 디렉토리 생성 금지
* 모든 실행 결과는 재현 가능해야 한다

---

## 8. 테스트 및 검증 기준

Phase 6.5는 다음 조건을 만족하는 테스트를 통해 검증되었다.

1. 백업 실패 시 삭제 미발생
2. 중복 실행 시 결과 안정성 유지
3. 클린업 로그 경로 고정
4. ops 미연결 상태에서도 Core 테스트 영향 없음

모든 테스트는 다음 구조 하에서 수행된다.

```
tests/
└─ ops/
   ├─ maintenance/
   ├─ decision/
   └─ e2e/
```

---

## 9. Phase 6.5 종료 시 QTS 상태

Phase 6.5 종료 시점의 QTS는 다음 상태에 도달한다.

* 장시간 무인 실행 가능한 Core
* 데이터 손실 위험이 제거된 자동화 구조
* ops 장애로부터 독립된 판단 흐름
* Phase 7 확장을 위한 안정적인 기반 확보

---

## 10. Phase 6.5 종료 선언

Phase 6.5는
**QTS를 “돌려도 되는 시스템”으로 만드는 마지막 안전 단계**다.

이 페이즈의 목표는
더 많은 기능이 아니라
**망가지지 않는 운영**이며,

정의된 모든 기준은 충족되었다.

**QTS Phase 6.5는 여기서 종료된다.**

---
