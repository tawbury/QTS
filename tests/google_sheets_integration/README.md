# Google Sheets Integration Tests

이 폴더는 Google Sheets 통합 기능에 대한 테스트 파일들을 포함합니다.

## 테스트 파일

### `test_repositories.py`
- 기본 Repository 기능 테스트
- Portfolio 및 Performance 리포지토리 기본 동작 검증
- Google Sheets 연동 기본 기능 테스트

### `test_enhanced_repositories.py`
- Enhanced Repository 기능 테스트 (이전 버전)
- 스키마 기반 기능 초기 테스트

### `test_enhanced_repositories_fixed.py`
- Enhanced Repository 기능 테스트 (수정 버전)
- 스키마 기반 기능 완전 테스트
- Google Sheets API 연동 및 데이터 업데이트 검증

## 테스트 실행 방법

```bash
# 기본 리포지토리 테스트
python tests/google_sheets_integration/test_repositories.py

# 스키마 기반 리포지토리 테스트
python tests/google_sheets_integration/test_enhanced_repositories_fixed.py
```

## 테스트 환경 요구사항

- Google Sheets API 인증 설정
- `.env` 파일에 `GOOGLE_SHEET_KEY` 및 `GOOGLE_CREDENTIALS_FILE` 설정
- 필요한 Python 패키지 설치:
  ```bash
  pip install gspread google-api-python-client python-dotenv
  ```

## 테스트 내용

1. **Schema Loader 테스트**
   - 스키마 파일 로드 및 파싱
   - 시트 설정 및 필드 매핑 확인

2. **Portfolio Repository 테스트**
   - KPI Overview 업데이트 및 조회
   - 스키마 기반 필드 매핑 동작 검증

3. **Performance Repository 테스트**
   - KPI Summary 업데이트 및 조회
   - 스키마 기반 필드 매핑 동작 검증

4. **Google Sheets 연동 테스트**
   - 실제 시트 접속 및 데이터 업데이트
   - API 제한 및 에러 핸들링 검증
