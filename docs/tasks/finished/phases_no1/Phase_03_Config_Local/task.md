# Phase 3 — Config Architecture (Local)

## 목표

- Local Config 경로를 운영 기준으로 안정화하고, 보조 설정(예: dividend DB)까지 일관된 로깅/에러 처리로 정리

## 근거

- `docs/Roadmap.md`
- 코드:
  - `config/local/config_local.json`
  - `src/runtime/config/local_config.py`
  - `src/runtime/config/dividend_config.py`
  - `src/runtime/config/config_constants.py`

## 작업

- [x] Local Config 운영 안전성 점검
  - [x] 파일 누락/UTF-8 BOM/잘못된 JSON 처리에 대한 사용자 친화적 오류 메시지 정리 (`local_config.py`: 한글 안내, 줄/열 정보, 로깅)
- [x] 코드 품질 개선(필수)
  - [x] `dividend_config.py`의 `print(...)` 제거 후 로깅으로 통일 (`_LOG.error`/`_LOG.warning`)
  - [x] 예외 처리/반환 타입 규칙을 `local_config.py`와 유사한 수준으로 맞춤 (ConfigLoadResult, utf-8-sig, 친화적 JSON 오류 메시지, 경로 상수 사용)

## 완료 조건

- [x] 로컬 설정 로딩 실패 시 로깅/예외 규칙이 일관적이다.
- [x] 배당 DB 기능도 동일한 운영 품질(로그/오류 처리)을 만족한다.
