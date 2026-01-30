# Observer 경계 정의 (QTS ↔ Observer)

Observer는 독립 프로젝트로 분리되어 있으며, QTS 본 저장소에는 Observer 구현 코드가 없다.  
본 문서는 **QTS가 Observer 산출물을 소비하는 지점**과 **계약(데이터 형식·경로)**을 정의한다.

**근거:** `docs/arch/09_Ops_Automation_Architecture.md`, `docs/Roadmap.md`

---

## 1. 소비 지점 요약

| 소비처 | 경로 | 계약 요약 |
|--------|------|-----------|
| ETEDA Pipeline | `src/runtime/pipeline/eteda_runner.py` | 스냅샷 dict (Trigger) |
| Decision Pipeline (Extract) | `src/ops/decision_pipeline/pipeline/extract.py` | context dict |
| Retention / Maintenance | `src/ops/retention/`, `src/ops/runtime/maintenance_runner.py` | dataset_root 경로 + 파일 명명 규칙 |

---

## 2. 계약 상세

### 2.1 ETEDA Pipeline 입력 (스냅샷)

- **소비처:** `ETEDARunner.run_once(snapshot)`  
- **의미:** Observer가 전달하는 “판단 없는 관찰/기록” 스냅샷을 트리거로 한 번의 파이프라인 실행.
- **형식:** `Dict[str, Any]`
  - `meta.timestamp`: (권장) 실행 시점 식별
  - `symbol`: (권장) 시장 데이터 심볼
  - 시장/포지션 등 파이프라인에 필요한 필드는 `snapshot` 내부에 포함되어 전달된다고 가정.

코드상 계약은 docstring 기준이며, Observer 측에서는 위 형식을 만족하는 스냅샷을 전달하면 된다.

### 2.2 Decision Pipeline context (Extract)

- **소비처:** `Extractor.extract(context)`  
- **의미:** Observer / Runtime으로부터 전달된 context에서 판단 파이프라인 입력을 추출. 외부 I/O 없음.
- **형식:** `Dict[str, Any]`
  - `inputs`: (선택) 파이프라인 입력
  - `source`: (선택) 출처, 기본 `"unknown"`
  - `session_id`: (선택) 세션 식별

Observer가 이 context 형식으로 데이터를 넘기면 Extract 단계에서 그대로 사용 가능하다.

### 2.3 Retention — Observer 산출물 디렉터리

- **소비처:** `DatasetScanner(dataset_root)`, `RetentionCleaner`, `run_maintenance_automation(dataset_root=..., ...)`  
- **의미:** Observer가 파일로 기록한 데이터셋 디렉터리를 QTS가 스캔·백업·만료 정리한다. Observer 코어는 import하지 않음.
- **경로:** `dataset_root`는 **구성(Config/환경)으로 주입**된다. 본 저장소에는 `config/observer/` 디렉터리가 없으며, 배포/운영 시 외부에서 마운트하거나 설정으로 지정한다.
- **파일 명명 규칙 (Retention 정책 매핑):**
  - 경로/파일명에 `"decision"` 포함 → `decision_snapshot_days` 적용
  - `"pattern"` 포함 → `pattern_record_days` 적용
  - `"raw"` 포함 → `raw_snapshot_days` 적용  
  - 그 외는 보존(삭제 대상 아님).

Observer 측에서는 위 키워드를 포함한 파일명/경로로 산출물을 쓰면 QTS Retention과 호환된다.

---

## 3. QTS 저장소 내 Observer 관련 상태

- **제거된 것:** `src/ops/observer/` (구현은 독립 프로젝트로 이전됨)
- **유지하는 것:**  
  - 위 소비 지점 코드 및 “Observer에서 전달되는 데이터”에 대한 docstring/주석  
  - `src/ops/retention/`: Observer **산출물**만 다루며, Observer 코어는 import하지 않음
- **설정:** `config/observer/`는 본 저장소 기본 구조에 없음. Observer 데이터 경로는 운영/배포 설정으로 제공.

---

## 4. 완료 조건 충족

- [x] QTS에서 Observer 산출물을 소비하는 지점이 확인됨 → ETEDA, Decision Extract, Retention/Maintenance
- [x] 계약이 본 문서에 문서화됨 → 스냅샷/context 형식, dataset_root 및 파일 명명 규칙
- [x] 본 저장소에 Observer 구현 의존성 없음 → `src/ops/observer/` 없음, config/observer 없음
- [x] Observer 관련 dead code는 없음. 남은 참조는 “계약·출처 설명”용 docstring/주석으로 유지
