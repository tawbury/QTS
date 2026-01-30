# Google Sheets Integration Tests

이 폴더는 Google Sheets 통합 기능에 대한 테스트 파일들을 포함합니다.

## 테스트 파일

### `test_repositories.py`
- Enhanced Portfolio / Performance 리포지토리 기능 테스트 (실제 인터페이스: `EnhancedPortfolioRepository`, `EnhancedPerformanceRepository`)
- **실 스프레드시트 연동은 env 설정 시에만 실행** (CI에서는 스킵 가능)

### `test_base_repository.py`
- BaseSheetRepository 추상 메서드·초기화 검증 (Mock 기반)

### `test_repository_manager.py`
- RepositoryManager 등록/조회/캐시/헬스체크 (Mock 기반)

### `test_enhanced_repositories_fixed.py`
- 스키마 기반 Enhanced Repository 완전 테스트
- Google Sheets API 연동 및 데이터 업데이트 검증 (env 설정 시)

### `test_google_sheets_client.py`
- 위치: `tests/runtime/data/test_google_sheets_client.py`
- GoogleSheetsClient 예외 타입·생성자·ValidationError 시나리오 (Mock 기반, CI 기본 실행)
- 실 API 연동: `pytest -m live_sheets` 또는 env 설정 시에만 실행

## 테스트 실행 방법

```bash
# Mock 기반 단위/통합 테스트 (CI 기본, 실 API 불필요)
pytest tests/google_sheets_integration/ tests/runtime/data/test_google_sheets_client.py -v -m "not live_sheets"

# 실 스프레드시트 연동 테스트 (env 설정 시에만)
python tests/google_sheets_integration/test_repositories.py
python tests/google_sheets_integration/test_enhanced_repositories_fixed.py
```

## 테스트 환경 요구사항

- **Mock 기반:** Google Sheets API/인증 불필요. CI에서 기본 실행.
- **실 연동:** `.env`에 `GOOGLE_SHEET_KEY`, `GOOGLE_CREDENTIALS_FILE` 설정. **CI에서는 서비스 계정 키를 저장소에 넣지 않음** — env 미설정 시 실 연동 테스트 스킵.
- 패키지: `gspread`, `google-api-python-client`, `python-dotenv`

## 실패 시 원인 분리

- **인증:** `AuthenticationError` / credentials 누락·만료
- **네트워크:** `APIError`, `RateLimitError` / 타임아웃·429
- **스키마 불일치:** `ValidationError`, 필수 필드 `ValueError` / 헤더·컬럼 불일치

상세 범위·시나리오: `docs/tasks/phases/Phase_01_Schema_Sheet_Mapping/Repository_Integration_Test_Scope.md`
