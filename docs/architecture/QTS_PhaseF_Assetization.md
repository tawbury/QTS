알겠습니다. 요청하신 대로 **이번 Phase F 세션을 공식적으로 종료**하고,
**의도적으로 발생한 테스트 실패까지 포함하여 “사후 참조 가능한 종료 자산화 문서”**를 아래에 정리합니다.

이 문서는 **차후 재개·확장 시 판단 근거로 그대로 사용 가능**하도록 작성되었습니다.

---

# QTS_PhaseF_Assetization.md

**Phase F – Observer Output Canonicalization & Schema-Aware Closure**

---

## 1. Phase F 개요

### Phase 목적

Phase F의 목적은 QTS Observer 계열에서 생성되는 **모든 JSON / JSONL 산출물의 위치·의미·책임을 구조적으로 고정**하고,
“더 이상 설계·구현할 것이 없음을 코드와 테스트로 증명”하는 것이었다.

핵심 목표는 다음과 같다.

* Observer 출력은 **운영 자산(asset)** 이다
* 출력 경로는 **단일 기준(Single Source of Truth)** 으로 관리된다
* `data/` 영역은 더 이상 Observer 로그를 보관하지 않는다
* 실행·테스트·리플레이 경로가 모두 동일한 정책을 따른다

---

## 2. 최종 아키텍처 결정 사항 (확정)

### 2.1 Observer 출력 경로 정책

| 항목                       | 결정                         |
| ------------------------ | -------------------------- |
| Observer JSON / JSONL 위치 | `config/observer/`         |
| data/observer 사용         | **금지 (deprecated)**        |
| 경로 해석 책임                 | `paths.py` 단일 SSoT         |
| 파일 생성 주체                 | `EventBus + JsonlFileSink` |
| Runner의 파일 책임            | 없음 (완전 제거)                 |

---

### 2.2 paths.py 변경 사항

* `observer_asset_dir()`
* `observer_asset_file(filename)`

를 신설하여 Observer 계열 산출물은 반드시 해당 함수 경유로 접근하도록 강제.

기존 `observer_data_dir()`는 **호환성 목적의 deprecated API**로만 유지.

---

## 3. 수정·정리된 주요 코드 영역

### 3.1 EventBus / JsonlFileSink

* 프로젝트 루트 추론 코드 제거
* `Path(__file__).parents[...]` 완전 제거
* paths.py 의존으로 경로 책임 이관

결과:

* EventBus는 **출력 정책을 모른다**
* Sink는 **경로 정책을 해석하지 않는다**

---

### 3.2 ObserverRunner (중요)

기존:

* Runner가 `data/observer/market_observation.jsonl` 직접 생성

수정 후:

* Runner는 오직 `JsonlFileSink("market_observation.jsonl")`만 생성
* 실제 파일 위치는 paths.py가 결정
* 직접 file open / write 코드 **완전 제거**

---

### 3.3 테스트 코드 정리

* Phase 4/11/12/13/14 테스트 중

  * 하드코딩된 `data/observer` 경로 전면 제거
  * 모든 입력 JSONL은 `observer_asset_file()` 기반으로 접근

---

## 4. 테스트 결과 요약 (중요)

### 4.1 최종 테스트 실행 결과

```text
pytest tests/ops/observation -v
→ 5 passed, 1 warning
```

```text
python tests/ops/replay/run_step1_smoke.py
→ 정상 종료, market_observation.jsonl 생성
```

### 4.2 생성된 파일 (의도된 결과)

`config/observer/`:

* `observer_test.jsonl`
* `market_observation.jsonl`

`data/observer/`:

* **비어 있음 (의도된 상태)**

---

## 5. “의도적으로 발생한 테스트 실패”에 대한 기록

### 5.1 발생한 실패

* `test_phase11_pipeline_smoke.py`
* 입력 파일을 `data/observer/observer_test.jsonl`에서 찾도록 되어 있어 실패

### 5.2 실패 원인 분석

* Phase F에서 Observer 로그 위치를 **의도적으로 config/observer로 이동**
* 기존 테스트는 Phase F 이전 정책을 전제로 작성됨
* 사용자가 `data/observer`를 비운 상태에서 실행 → 실패 발생

### 5.3 조치 결과

* 테스트 코드를 `observer_asset_file("observer_test.jsonl")` 기반으로 수정
* 수정 후 동일 테스트 **PASS 확인**

### 5.4 이 실패의 의미

이 실패는 다음을 증명한다.

* Phase F 정책이 **실제로 강제되고 있음**
* Legacy 경로 의존성이 테스트로 정확히 탐지됨
* 설계 변경이 “문서 수준”이 아닌 “실제 동작”으로 반영됨

👉 **실패는 오류가 아니라 검증 수단이었다.**

---

## 6. Phase F 종료 조건 충족 여부

| 항목                  | 상태 |
| ------------------- | -- |
| Observer 로그 경로 단일화  | 충족 |
| data/observer 완전 배제 | 충족 |
| Runner 직접 출력 제거     | 충족 |
| 테스트·실행 경로 일관성       | 충족 |
| “더 만들 것 없음” 증명      | 충족 |

---

## 7. 향후 참고 가이드 (차후 작업 시)

### Observer 로그가 보이지 않을 때

* `config/observer/` 확인
* `paths.py` 변경 여부 우선 검토

### 테스트 실패 시

* 입력 JSONL 경로가 `observer_asset_file()`를 경유하는지 확인

### Phase G / 차기 Phase 진입 시

* Observer 계열은 **확장 대상 아님**
* 변경 발생 시 반드시 Change Management 문서 경유 필요

---

## 8. Phase F 종료 선언

본 문서를 기준으로 **QTS Phase F는 종료 상태로 선언**한다.
Observer 출력, 경로 정책, 실행·테스트 정합성은 모두 고정되었으며,
향후 변경은 Phase F 범위를 벗어나는 아키텍처 변경으로 간주한다.

---

원하시면 다음 중 하나로 바로 이어갈 수 있습니다.

* Phase G(또는 Phase 16) 초석 문서 작성
* Phase F 요약본(1페이지 내) 별도 생성
* Change Management 기준 문서에 Phase F 반영

다음 방향을 지시해 주세요.
