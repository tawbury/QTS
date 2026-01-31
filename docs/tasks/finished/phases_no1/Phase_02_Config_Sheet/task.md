# Phase 2 — Config Architecture (Sheet)

## 목표

- Sheet 기반 Config 로딩 경로를 현재 코드(`GoogleSheetsClient` + Repository)에 맞게 정합화
- Local/Sheet 머지 규칙을 SSOT로 고정

## 근거

- `docs/arch/13_Config_3분할_Architecture.md`
- `docs/Roadmap.md`
- 코드:
  - `src/runtime/config/config_loader.py`
  - `src/runtime/config/sheet_config.py`
  - `src/runtime/config/config_constants.py`
  - `src/runtime/data/google_sheets_client.py`
  - `src/runtime/data/repositories/config_scalp_repository.py`
  - `src/runtime/data/repositories/config_swing_repository.py`

## 작업

- [x] Sheet Config 로딩 정합성 확보
  - [x] `sheet_config.py`의 Client/Repository 사용 방식이 실제 구현과 일치하도록 정리 (ConfigScalpRepository / ConfigSwingRepository 사용)
  - [x] SCALP/SWING 스코프별 로딩 경로/실패 처리 기준 정의 → [Config_Loading_Path_and_Failures.md](./Config_Loading_Path_and_Failures.md)
- [x] 머지 규칙(우선순위) 고정
  - [x] Local immutable 규칙 문서/코드 반영 (`config_loader.py` docstring, `_merge_configs` 주석에 SSOT 참조)
- [x] 코드 품질 개선(필수)
  - [x] Config 로딩 경로 매직 스트링 축소 (`config_constants.py` 도입, `local_config`/`sheet_config`에서 상수 사용)

## 완료 조건

- [x] `load_unified_config`가 정상적으로 LOCAL + (SCALP|SWING)을 병합한다.
- [x] 실패 케이스(시트 미존재/필드 누락/인증 실패)가 일관되게 처리된다.
