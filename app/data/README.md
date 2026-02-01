# Data Layer — 진입점 및 Wiring

Google Sheets 클라이언트·리포지토리·스키마 로더의 **호출 경로 및 생성자 주입** 정리.  
Phase 1 Schema & Sheet Mapping 완료 조건(진입점/wiring 문서화) 충족용.

**계약·예외 규칙**: [docs/tasks/finished/phases_no1/Phase_01_Schema_Sheet_Mapping/Google_Sheets_Contract.md](../../../docs/tasks/finished/phases_no1/Phase_01_Schema_Sheet_Mapping/Google_Sheets_Contract.md)

---

## 1. GoogleSheetsClient

| 항목 | 내용 |
|------|------|
| **경로** | `src/runtime/data/google_sheets_client.py` |
| **생성자** | `GoogleSheetsClient(credentials_path=None, spreadsheet_id=None)` |
| **env fallback** | 미지정 시 `GOOGLE_CREDENTIALS_FILE`, `GOOGLE_SHEET_KEY` 사용. 둘 다 없으면 `ValueError` |
| **단일 인스턴스** | `get_google_sheets_client()` (async) — 싱글톤 반환 |

**호출부**

- **ETEDARunner**: `sheets_client` 미주입 시 `GoogleSheetsClient(credentials_path=..., spreadsheet_id=...)` (config/env 기반)
- **sheet_config** (`_load_sheet_config_async`): `client` 없으면 `GoogleSheetsClient()` 후 `authenticate()`
- **RepositoryManager**: `client` 없으면 `initialize()` 시 `get_google_sheets_client()` 사용

---

## 2. RepositoryManager

| 항목 | 내용 |
|------|------|
| **경로** | `src/runtime/data/repository_manager.py` |
| **생성자** | `RepositoryManager(client=None)` |
| **초기화** | `await manager.initialize()` — client 없을 때만 `get_google_sheets_client()` 호출 |
| **리포지토리 생성** | `get_repository(sheet_name)` 시 `(client, spreadsheet_id, sheet_name)` 전달 |
| **전역 진입점** | `get_repository_manager()` (async) — 싱글톤, 내부에서 `initialize()` 호출 |

---

## 3. BaseSheetRepository (시트 리포지토리 공통)

| 항목 | 내용 |
|------|------|
| **경로** | `src/runtime/data/repositories/base_repository.py` |
| **생성자** | `(client, spreadsheet_id, sheet_name, header_row=1)` |
| **Range** | `{sheet_name}!A:Z`, 헤더 행 `header_row`(기본 1), 데이터 행 `header_row+1`~ |
| **헬스체크** | `health_check()` — RepositoryManager가 모든 등록 리포지토리에 대해 호출 |

상세 Range/Headers/Row 규칙은 [Google_Sheets_Contract.md](../../../docs/tasks/finished/phases_no1/Phase_01_Schema_Sheet_Mapping/Google_Sheets_Contract.md) §2.

---

## 4. SchemaLoader

| 항목 | 내용 |
|------|------|
| **경로** | `src/runtime/config/schema_loader.py` |
| **생성자** | `SchemaLoader(project_root: Path)` |
| **스키마 파일** | `project_root / "config" / "schema" / "credentials.json"` (스키마 정의 JSON) |
| **진입점** | `get_schema_loader(project_root)` — 싱글톤 |

Enhanced 리포지토리(Portfolio, Performance)는 `SchemaBasedRepository`를 통해 `get_schema_loader(project_root)` 사용.

---

## 5. 테스트 경로

- `tests/google_sheets_integration/` — Base/Enhanced 리포지토리, RepositoryManager, SchemaLoader (Mock)
- `tests/runtime/data/` — GoogleSheetsClient 예외·생성자, 신규 리포지토리

기본 실행: `pytest tests/google_sheets_integration/ tests/runtime/data/ -v -m "not live_sheets and not real_broker"`
