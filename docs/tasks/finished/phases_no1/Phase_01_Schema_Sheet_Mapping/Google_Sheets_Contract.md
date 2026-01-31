# Google Sheets Client & Repository 계약

Schema/Repository/Google Sheets Client 경로와 I/O 계약(필드·헤더·타입·예외)을 코드 기준으로 고정한다.

**근거:** `docs/arch/01_Schema_Auto_Architecture.md`, `docs/arch/04_Data_Contract_Spec.md`

---

## 1. GoogleSheetsClient 사용 계약

### 1.1 단일 진입점

- **경로:** `src/runtime/data/google_sheets_client.py`
- **인증/스프레드시트/워크시트 접근**은 모두 `GoogleSheetsClient` 인스턴스를 통한다.
- **생성:** `GoogleSheetsClient(credentials_path=None, spreadsheet_id=None)`  
  - 미지정 시 환경변수: `GOOGLE_CREDENTIALS_FILE`, `GOOGLE_SHEET_KEY`  
  - 둘 다 없으면 `ValueError` 발생.
- **API:**  
  - `authenticate()` — 인증 수행 (async)  
  - `get_sheet_data(range_name)` — 범위 raw 데이터 (async)  
  - `update_sheet_data(range_name, values)` — 범위 갱신 (async)  
  - `append_sheet_data(range_name, values)` — 범위 추가 (async)  
  - `clear_sheet_data(range_name)` — 범위 비우기 (async)  
  - `get_worksheet_by_title(title)` — 워크시트 객체 (async)  
  - `health_check()` — 연결 상태 (async)

### 1.2 예외 타입 및 호출자 처리 기준

| 예외 | 발생 상황 | 호출자 처리 |
|------|-----------|-------------|
| `ValueError` | `credentials_path` 또는 `spreadsheet_id` 미설정 | 초기화 전에 env/설정 확인 |
| `AuthenticationError` | 401, 인증 파일 오류 | 재인증 또는 설정 수정 후 재시도 |
| `APIError` | 403/404, 기타 HTTP 오류, 갱신/추가/삭제 실패 | status_code로 403/404 구분, 로그 후 상위 전파 또는 사용자 알림 |
| `RateLimitError` | 429 (API 제한 초과) | `retry_after` 참고하여 대기 후 재시도; 내부적으로 이미 제한적 재시도 수행 |
| `ValidationError` | 빈 데이터로 update/append 호출 | 호출 전에 values 비어 있지 않음 보장 |

- **재시도:** `get_sheet_data`는 429/일부 오류에 대해 내부 재시도(max_retries, exponential backoff) 수행.  
- **호출자:** 위 예외를 catch하여 로깅/재시도/사용자 메시지 중 하나로 처리한다.  
- **문서:** 본 절이 “실패 시 예외/에러 반환 규칙”의 SSoT이다.

---

## 2. Repository 공통 계약 (BaseSheetRepository)

### 2.1 경로 및 역할

- **경로:** `src/runtime/data/repositories/base_repository.py`
- **역할:** 시트 단위 CRUD, 헤더·행 매핑, 캐시의 공통 규칙.

### 2.2 Range / Headers / Row 규칙

- **Range:** `range_name = f"{sheet_name}!A:Z"` (기본). 헤더·데이터 모두 A~Z 열 사용.
- **헤더:** `header_row`(기본 1) 행을 헤더로 사용. `get_headers()`로 헤더 리스트 조회.
- **데이터 행:** `header_row + 1` 행부터 데이터. `get_all()` 등은 `get_headers()` → `get_sheet_data(sheet!A{header_row+1}:Z)` → `_row_to_dict(row, headers)`로 매핑.
- **Row ↔ Dict 변환:**  
  - `_row_to_dict(row, headers)`: 행 리스트를 헤더 순서에 맞춰 dict로 변환. 빈 문자열 → None, "true"/"false" → bool, 숫자 문자열 → int/float.  
  - `_dict_to_row(data, headers)`: dict를 헤더 순서의 행 리스트로 변환.  
- **동일 규칙:** 모든 시트 리포지토리는 위 “Range/Headers/Row Mapping” 규칙을 따른다.

### 2.3 CRUD / 헤더 / 캐시 동작

- **CRUD:** `get_all`, `get_by_id`, `create`, `update`, `delete`, `exists`는 추상 메서드. 서브클래스가 시트 구조에 맞게 구현.
- **헤더:** `get_headers()`는 첫 조회 시 클라이언트로 헤더 행을 읽고 `_headers_cache`에 저장. 이후 동일 인스턴스에서는 캐시 반환.
- **캐시 초기화:** `clear_cache()` 호출 시 `_headers_cache` 초기화. 시트 구조 변경 시 호출자 책임.

### 2.4 헤더 누락/컬럼 변경 시 Fail-Safe 수준

| 상황 | 동작 | 수준 |
|------|------|------|
| 헤더 행 조회 실패 (API/예외) | `get_headers()` → 빈 리스트 `[]` 반환, 예외는 로그만 | **Fail-Soft**: 에러로 상위 전파하지 않음 |
| 헤더가 비어 있음 | `get_headers()` → `[]` | **Fail-Soft** |
| `get_all()` 등에서 headers 비어 있음 | 빈 리스트 `[]` 반환 (데이터 없음으로 처리) | **Fail-Soft** |
| 시트 컬럼 추가/삭제/이동 | 기존 헤더 캐시로 매핑 → 컬럼 불일치 가능. 호출자가 `clear_cache()` 후 재조회하면 새 구조 반영 | **자동 복구**: 캐시 무효화 후 재접근 시 복구 |
| 필수 필드 누락 (create/update 시) | 서브클래스 `_validate_required_fields()` → `ValueError` | **에러**: 호출자에게 명시적 실패 반환 |

- **정리:** 헤더/시트 접근 실패는 **에러로 던지지 않고** 빈 결과로 완화; 스키마/필수 필드 검증은 **에러**로 처리한다.

---

## 3. RepositoryManager

- **경로:** `src/runtime/data/repository_manager.py`
- **역할:** `GoogleSheetsClient` 한 개 공유, 시트별 `BaseSheetRepository` 인스턴스 생성·캐싱.
- **생성:** `client` 미지정 시 `get_google_sheets_client()`로 싱글톤 클라이언트 사용.
- **리포지토리 생성:** `get_repository(sheet_name)` 시 해당 시트명에 등록된 `BaseSheetRepository` 서브클래스로 `(client, spreadsheet_id, sheet_name)` 전달.

---

## 4. 코드 품질 (정합화 결과)

- **Client:** 인증/스프레드시트/워크시트 접근은 `GoogleSheetsClient` 단일 진입점만 사용.
- **Repository:** Range/Headers/Row 규칙은 `BaseSheetRepository` + `_row_to_dict`/`_dict_to_row`에 일원화; 서브클래스는 동일 규칙 준수.
- **불필요 파일:** `repository_base.py`는 미사용(삭제 권장). `base_repository.py`가 유일한 베이스.

---

## 5. 완료 조건 충족

- [x] Repository가 동일한 “Range/Headers/Row Mapping” 규칙을 따른다.
- [x] 실패 시 예외/에러 반환 규칙이 문서화되어 있다. (본 문서 §1.2, §2.4)
