# scripts/ — 유틸리티 스크립트

QTS 프로젝트 운영·검증용 스크립트입니다.

## 스크립트

| 스크립트 | 용도 |
|----------|------|
| **check_r_dash_sheets.py** | R_Dash 시트 구조·데이터 검증. `.env`의 `GOOGLE_CREDENTIALS_FILE`, `GOOGLE_SHEET_KEY` 사용 |

## 실행

```bash
# 프로젝트 루트에서
python scripts/check_r_dash_sheets.py
```

**환경 요구**: Google Sheets 연동 시 `.env` 설정 필요.
