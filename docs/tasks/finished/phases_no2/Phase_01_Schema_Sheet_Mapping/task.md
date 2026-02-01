# Phase 1 — Schema & Sheet Mapping (로드맵 기준 Task)

## 목표

- 데이터 레이어/리포지토리/매니저/Runner 간 **인터페이스 정합성 확보**
- Google Sheets 클라이언트·시트 리포지토리·스키마 로더의 **생성자 시그니처/호출 경로**를 실제 코드와 문서에 맞게 정합화
- Phase 10 Exit Criteria 충족 시 Roadmap 상태 ✅ 전환

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — Phase 1, Section 3 (다음 우선순위)
- [Phase Exit Criteria](../../../tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md) §4.1
- 코드: `src/runtime/data/google_sheets_client.py`, `src/runtime/data/repositories/`, `src/runtime/config/schema_loader.py`, `src/runtime/schema/`
- 아키텍처: `docs/arch/01_Schema_Auto_Architecture.md`, `docs/arch/04_Data_Contract_Spec.md`, `docs/arch/sub/18_Data_Layer_Architecture.md`

---

## Roadmap Section 2 — Phase 1 업무

| 업무 | 상태 | 완료 시 |
|------|------|--------|
| Google Sheets 클라이언트 모듈 | ✅ | 호출부/매니저와 시그니처 정합 (Google_Sheets_Contract.md, src/runtime/data/README.md) |
| 시트 리포지토리(포지션/레저/히스토리 등) | ✅ | 동일 Range/Headers/Row 규칙, health_check (Contract §2, BaseSheetRepository) |
| 스키마 로더/레지스트리 | ✅ | 문서·코드 일치 (Wiring README, get_schema_loader) |

---

## Wiring 요약 (현행)

| 컴포넌트 | 생성자/진입점 | 비고 |
|----------|----------------|------|
| `GoogleSheetsClient` | `(credentials_path=None, spreadsheet_id=None)` env fallback | ETEDARunner: config 주입 또는 생성. sheet_config/RepositoryManager: 무인자 또는 주입 |
| `BaseSheetRepository` | `(client, spreadsheet_id, sheet_name, header_row=1)` | Range: `{sheet_name}!A:Z`, 헤더 행 공통. `health_check()` 제공 |
| `RepositoryManager` | `(client=None)` → `initialize()` 시 `get_google_sheets_client()` | `get_repository(sheet_name)` 시 client·spreadsheet_id·sheet_name 전달 |
| `SchemaLoader` | `(project_root: Path)`, `get_schema_loader(project_root)` | 스키마 경로: `project_root / "config" / "schema" / "credentials.json"` |

---

## 미결 사항

| 미결 항목 | 진행 단계 | 비고 |
|-----------|-----------|------|
| GoogleSheetsClient 호출부 시그니처 정합 | ✅ 완료 | ETEDARunner·sheet_config·RepositoryManager 연동 일치. 예외 규칙: Google_Sheets_Contract.md §1.2 |
| Repository Range/Headers/Row 규칙 검증 | ✅ 완료 | BaseSheetRepository 공통 규칙. Google_Sheets_Contract.md §2, repositories/README.md |
| 실패 시 예외/에러 반환 규칙 문서화 | ✅ 완료 | Google_Sheets_Contract.md §1.2, §2.4 (APIError, AuthenticationError, ValidationError 등) |
| tests/google_sheets_integration·runtime/data CI 정합 | ✅ 완료 | Mock 기반 테스트 통과. test_google_sheets_client 예외·생성자 검증 포함 |
| 아키텍처/스펙 문서와 구현 일치 | ✅ 완료 | 01_Schema_Auto, 04_Data_Contract_Spec, 18_Data_Layer 및 Contract 문서와 일치 |
| 진입점/wiring README 정리 | ✅ 완료 | src/runtime/data/README.md (진입점·생성자·호출 경로) |

---

## 작업 (체크리스트)

- [x] **인터페이스 정합성**
  - [x] `GoogleSheetsClient`와 호출부/매니저 생성자 시그니처 통일 또는 adapter 문서화 (Google_Sheets_Contract.md, data/README.md)
  - [x] Repository가 동일한 “Range/Headers/Row Mapping” 규칙을 따르는지 검증 (Contract §2, BaseSheetRepository)
  - [x] 실패 시 예외/에러 반환 규칙 문서화 (Google_Sheets_Contract.md §1.2, §2.4)
- [x] **테스트**
  - [x] `tests/google_sheets_integration/`, `tests/runtime/data/` 해당 테스트가 현재 인터페이스와 일치하고 CI 통과
  - [x] Contract/스키마 검증 테스트 포함 (예외 타입·생성자·ValidationError 등)
- [x] **문서**
  - [x] 해당 Phase 아키텍처/스펙 문서가 현재 구현과 일치 (01_Schema_Auto, 04_Data_Contract_Spec, 18_Data_Layer, Google_Sheets_Contract)
  - [x] 진입점/wiring(호출 경로, 생성자 주입) 문서 또는 README 정리 (src/runtime/data/README.md)

---

## 완료 조건 (Exit Criteria)

- [x] 필수 테스트 통과 (Phase 10 Exit Criteria §2.1) — `pytest tests/google_sheets_integration/ tests/runtime/data/ -v -m "not live_sheets and not real_broker"`
- [x] 해당 Phase 운영 체크 문서화(실 시트 연동 시) (§2.2) — health_check·live_sheets 마커 정책: Google_Sheets_Contract, data/README.md
- [x] 문서 SSOT 반영 (§2.3) — Contract·Wiring README·아키텍처 문서 반영
- [x] Roadmap Phase 1 비고(“생성자 시그니처 불일치”) 해소 — 시그니처·예외·wiring 문서화로 정합
