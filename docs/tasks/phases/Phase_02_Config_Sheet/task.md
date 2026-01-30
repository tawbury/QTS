# Phase 2 — Config Architecture (Sheet)

## 목표

- Sheet 기반 Config 로딩 경로를 현재 코드(`GoogleSheetsClient`)에 맞게 정합화
- Local/Sheet 머지 규칙을 SSOT로 고정

## 근거

- `docs/arch/13_Config_3분할_Architecture.md`
- `docs/Roadmap.md`
- 코드:
  - `src/runtime/config/config_loader.py`
  - `src/runtime/config/sheet_config.py`
  - `src/runtime/data/google_sheets_client.py`

## 작업

- [ ] Sheet Config 로딩 정합성 확보
  - [ ] `sheet_config.py`의 Client/Repository 사용 방식이 실제 구현과 일치하도록 정리
  - [ ] SCALP/SWING 스코프별 로딩 경로/실패 처리 기준 정의
- [ ] 머지 규칙(우선순위) 고정
  - [ ] Local immutable 규칙이 있다면 문서/코드에 명확히 반영
- [ ] 코드 품질 개선(필수)
  - [ ] Config 로딩 경로에 존재하는 “암묵적 기본값/매직 스트링” 축소

## 완료 조건

- [ ] `load_unified_config`가 정상적으로 LOCAL + (SCALP|SWING)을 병합한다.
- [ ] 실패 케이스(시트 미존재/필드 누락/인증 실패)가 일관되게 처리된다.
