
---

# QTS Phase 4 Assetization

**Execution Loop · Order State · Risk Entry 자산화 문서**

- **File:** `QTS/docs/architecture/QTS_Phase4_Assetization.md`

- **Version:** v1.0.0

- **Status:** Enforced (Assetized)

- **Gate:** E (Closed)

- **Declared At:** 2025-12-29


---

## 1. 문서의 목적

본 문서는 **QTS Phase 4에서 구축된 구조를 ‘자산(asset)’으로 고정**하기 위한 기준 문서다.

Phase 4에서 생성된 모든 코드는

- 실험 코드가 아닌 **재사용 가능한 기반 레이어**이며

- 이후 Phase 5 이상에서 **수정 없이 참조되는 안정 자산**으로 취급된다.


---

## 2. Phase 4 자산 범위 정의

Phase 4 자산은 다음 세 영역으로 구성된다.

### 2.1 Execution Loop Asset

**역할**

- Execution Route를 반복 호출할 수 있는 최소 실행 단위 제공

- 실행 횟수·중단 조건·실행 흐름 제어


**자산 구성**

```
src/runtime/execution_loop/
├─ loop.py
├─ controller.py
└─ policies/
   └─ stop_policy.py
```

**자산 속성**

- 동기적 단일 루프

- 외부 스케줄러 비의존

- 전략·리스크 계산 로직 미포함


---

### 2.2 Order State Asset

**역할**

- Execution 결과를 상태(State)로 해석

- 상태 전이 규칙의 단일 기준 제공


**자산 구성**

```
src/runtime/execution_state/
├─ order_state.py
└─ transition.py
```

**자산 속성**

- 상태 전이는 명시적 Enum 기반

- ExecutionResponse.accepted 기준 최소 전이

- TERMINAL 상태 도달 보장


---

### 2.3 Risk Entry Asset

**역할**

- 실행 흐름 내 리스크 개입 지점 제공

- 계산 없이 차단/허용 구조만 정의


**자산 구성**

```
src/runtime/risk/
├─ interfaces/
│  └─ risk_gate.py
└─ noop_risk_gate.py
```

**자산 속성**

- before_intent / before_route / after_response

- Boolean Gate 방식

- Phase 4에서는 Noop 구현만 허용


---

## 3. 테스트 자산

Phase 4 자산은 **테스트와 함께 자산화**된다.

```
tests/runtime/
├─ execution_state/
│  └─ test_phase4_order_state_transition.py
└─ execution_loop/
   └─ test_phase4_execution_loop_integration.py
```

**테스트 기준**

- 루프 존재 여부

- 상태 전이 발생 여부

- Risk Gate 구조 개입 가능성

- 실주문 경로 미사용


---

## 4. 자산 고정 규칙 (Enforcement Rules)

Phase 4 자산에 대해 다음 규칙을 강제한다.

1. Phase 4 자산은 **기본 수정 금지**

2. 기능 확장은 Phase 5 이상의 레이어에서만 수행

3. 버그 수정이 필요한 경우:

    - 테스트 실패가 근거가 되어야 함

4. Phase 3 Execution Route와 동일하게
    **“호출만 허용, 로직 변경 금지”** 원칙을 적용


---

## 5. Phase 5로의 전달 사항

Phase 5에서는 다음을 전제로 개발한다.

- Execution Loop는 그대로 사용

- Order State는 확장 가능하나 기존 상태 삭제 금지

- Risk Gate는 계산 로직을 “추가”할 수 있으나 인터페이스 유지

- Phase 4 테스트는 **항상 통과 상태 유지**


---

## 6. 자산 선언

> Phase 4의 모든 산출물은
> QTS 자동 매매 시스템의 **기반 실행 자산(Runtime Foundation Asset)** 으로 선언한다.

**QTS Phase 4 Assetization — 완료**

---
