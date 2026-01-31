# Phase 5 — ETEDA Pipeline: Wiring (Runner & Dependencies)

## 목표

- `ETEDARunner`와 Engine/Repository 의존성 주입 경로를 정합화

## 근거

- `docs/arch/03_Pipeline_ETEDA_Architecture.md`
- 코드:
  - `src/runtime/pipeline/eteda_runner.py`
  - `src/runtime/data/repository_manager.py`

## 작업

- [x] Runner 의존성 주입 규칙 확정
  - [x] 스프레드시트 ID/시트명/리포지토리 생성 책임 분리
- [x] 코드 품질 개선(필수)
  - [x] Runner 내부에서 “임시 생성/매직 값”을 제거하고 Config 계약으로 통일

## 완료 조건

- [x] Runner가 명확한 입력(snapshot) + Config + Repository/Engine wiring으로 1회 실행 가능하다.

## 구현 요약

- **의존성 주입**: `ETEDARunner(config, *, sheets_client=None, project_root=None)`. `sheets_client` 미주입 시 Config/환경변수(SPREADSHEET_ID, CREDENTIALS_PATH / GOOGLE_SHEET_KEY, GOOGLE_CREDENTIALS_FILE)로 생성. 시트명은 각 리포지토리 클래스 책임.
- **Config 계약**: RUN_MODE, LIVE_ENABLED(시트), QTS_LIVE_ACK(env) → `decide_execution_mode`로 Act 단계 실행 모드 결정. SPREADSHEET_ID, CREDENTIALS_PATH(선택) 클라이언트 생성용.
