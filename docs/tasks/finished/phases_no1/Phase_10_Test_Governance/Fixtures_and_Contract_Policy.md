# Phase 10 — Fixtures & Contract 테스트 정책

> **목표**: Raw/Calc/Engine/UI Contract 구조를 fixture 기반으로 검증하여 회귀를 방지한다.  
> **근거**: [docs/arch/10_Testability_Architecture.md](../../../arch/10_Testability_Architecture.md), [04_Data_Contract_Spec.md](../../../arch/04_Data_Contract_Spec.md)

---

## 1. Fixture 형식·버전 정책

### 1.1 위치

- **Contract/Engine 검증용**: `tests/fixtures/contracts/` (Python 모듈 또는 JSON)
- **계층별 fixture**: 해당 테스트 디렉터리 내 `conftest.py` 또는 `_fixtures.py`에 두어도 됨. 단, **Contract 구조 검증**용 최소 fixture는 `tests/fixtures/contracts/`에 두어 단일 소스로 유지.

### 1.2 형식

- **Python dict/상수**: Contract가 Python dataclass·TypedDict인 경우 `tests/fixtures/contracts.py`(또는 `contracts/__init__.py`)에 최소 유효 dict를 상수로 정의. 테스트에서 import 후 `from_dict()`·생성자에 넘겨 **구조 정합성**만 검증.
- **JSON 파일**: Raw/Calc 등 스키마가 문서·외부 도구와 공유되는 경우 `tests/fixtures/contracts/*.json` 사용. 파일명에 버전 포함 가능(예: `raw_contract_v1.json`).

### 1.3 버전

- Fixture는 **Contract 버전과 동기화**한다.
  - UI Contract: `meta.contract_version`(예: `1.0.0`)과 문서 [UI_Contract_Schema.md](../../../arch/UI_Contract_Schema.md) §1 버전 정책 준수.
  - 기타 Contract: [04_Data_Contract_Spec.md](../../../arch/04_Data_Contract_Spec.md) §1.4 (Major/Minor/Patch) 준수.
- **Contract 필드 추가/삭제/이름 변경** 시 해당 fixture와 **Contract validation 테스트**를 함께 수정한다. 테스트가 곧 “허용된 구조”의 스냅샷이 되도록 유지.

### 1.4 규칙 요약

| 항목 | 규칙 |
|------|------|
| 위치 | Contract 검증용: `tests/fixtures/contracts/` 또는 `tests/fixtures/contracts.py` |
| 형식 | Python dict 상수 또는 JSON. 코드와 동일 구조 사용. |
| 버전 | Contract 스펙 버전과 맞춤. 변경 시 fixture·테스트 동시 수정. |
| 최소성 | 검증 목적의 “최소 유효 샘플”만 유지. 불필요한 필드 축소. |

---

## 2. Contract Validation 테스트 설계 (조기 감지)

### 2.1 원칙

- **Contract 변경이 있으면 해당 테스트가 즉시 깨지도록** 설계한다.
  - 필수 필드 삭제/이름 변경 → fixture 또는 `from_dict()`/생성자 호출 실패, 또는 “필수 키 집합” assertion 실패.
  - 필수 필드 추가 → fixture에 없으면 `from_dict()` 실패 또는 “필수 키 집합” assertion 실패(테스트에서 기대 집합을 명시).

### 2.2 테스트 위치

- `tests/contracts/test_contract_validation.py` (또는 `tests/contracts/` 하위에 계약별로 분리).

### 2.3 검증 방식

1. **필수 키/필드 존재**: Contract 타입의 필수 필드명을 나열한 “기대 집합”과 실제 타입(dataclass `fields`, TypedDict `__annotations__` 등) 또는 직렬화 결과(`to_dict()` 키)를 비교.
2. **Fixture 기반 round-trip**: 최소 fixture dict → `from_dict()` 또는 생성자 → `to_dict()`(또는 직렬화) → 키 집합이 기대와 일치하는지 검증. Contract에 필드가 추가/삭제되면 기대 집합 또는 fixture를 수정해야 통과.
3. **UI Contract**: 루트 필수 블록(`account`, `symbols`, `pipeline_status`, `meta`) 및 `meta.contract_version` 존재·타입 검증. `get_expected_contract_version()`와 fixture의 `contract_version` 일치 검증.

### 2.4 유지보수

- 새 Contract 추가 시: 해당 Contract용 최소 fixture + “필수 키/필드” 검증 테스트 추가.
- Contract 스펙 버전 업 시: fixture와 기대 집합을 스펙에 맞게 수정한 뒤 테스트를 통과시킨다. **테스트 실패 = 스펙 변경이 테스트에 반영되지 않았음**을 의미하도록 유지.

---

## 3. 완료 조건

- [x] Fixture 형식/버전 정책이 문서로 정의되어 있다.
- [x] Contract validation 테스트가 추가되어, Contract 구조 변경 시 테스트가 실패한다(조기 감지).
- [x] Contract 회귀가 자동으로 감지된다(pytest 실행으로 확인).

---

**문서 버전**: 1.0  
**최종 갱신**: 2026-01-31
