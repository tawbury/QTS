# Config Sheet 로딩 경로 및 실패 처리

SSOT: `docs/arch/13_Config_3분할_Architecture.md`

## 로딩 경로

| 스코프 | 소스 | 구현 |
|--------|------|------|
| LOCAL | 파일 `config/local/config_local.json` | `local_config.load_local_config(project_root)` |
| SCALP | 시트 `Config_Scalp` | `sheet_config.load_sheet_config(project_root, SCALP)` → ConfigScalpRepository |
| SWING | 시트 `Config_Swing` | `sheet_config.load_sheet_config(project_root, SWING)` → ConfigSwingRepository |

Unified: `config_loader.load_unified_config(project_root, SCALP|SWING)` → LOCAL + (SCALP|SWING) 병합, Local 우선.

## 실패 처리

| 케이스 | 처리 |
|--------|------|
| 시트 미존재(404) | `ConfigLoadResult(ok=False, error="Sheet not found: 'Config_*' (404)", ...)` |
| 인증 실패 | `ConfigLoadResult(ok=False, error="Authentication failed for sheet config: ...", ...)` |
| 필드 누락/파싱 오류 | `ConfigLoadResult(ok=False, error="Failed to parse sheet '...' row N: ...", ...)` |
| Local 파일 없음 | `ConfigMergeResult(ok=False, error="Failed to load Config_Local: ...", ...)` |

일관 규칙: 실패 시 `ok=False`, `error`에 원인 포함. 호출부는 `ok`로 성공 여부 판단.
