# Config Sheet 로딩 실패 시 운영 체크 (Phase 2 §2.2)

설정 로딩(Config_Local + Config_Scalp/Config_Swing) 실패 시나리오와 대응 절차.  
**근거**: Phase 10 Exit Criteria §2.2, [13_Config_3분할_Architecture.md](../../../arch/13_Config_3분할_Architecture.md)

---

## 1. 실패 시나리오 및 반환

| 시나리오 | 발생 위치 | 반환/동작 | 호출자 확인 |
|----------|-----------|-----------|-------------|
| **시트 미존재 (404)** | Sheet Config 로딩 | `ConfigLoadResult(ok=False, error="Sheet not found: 'Config_Scalp' (404)" 등)` | `load_sheet_config` → `result.ok` / `result.error` |
| **인증 실패** | `GoogleSheetsClient().authenticate()` | `ConfigLoadResult(ok=False, error="Authentication failed for sheet config: ...")` | env `GOOGLE_CREDENTIALS_FILE`, `GOOGLE_SHEET_KEY` 및 서비스 계정 키 유효성 |
| **필드/파싱 오류** | 시트 행 → `ConfigEntry` 변환 시 | `ConfigLoadResult(ok=False, error="Failed to parse sheet '...' row N: ...")` | 시트 컬럼(CATEGORY, SUB_CATEGORY, KEY, VALUE 등) 구조 및 타입 |
| **Config_Local 로드 실패** | `load_unified_config` 1단계 | `ConfigMergeResult(ok=False, error="Failed to load Config_Local: ...")` | `config/local/config_local.json` 존재·JSON 형식 |
| **Invalid scope** | `load_sheet_config(scope=LOCAL)` | `ConfigLoadResult(ok=False, error="Invalid scope ...")` | scope는 SCALP 또는 SWING만 사용 |

---

## 2. 대응 절차 (운영)

1. **404 (시트 없음)**  
   - 스프레드시트에 `Config_Scalp` / `Config_Swing` 시트 존재 여부 확인.  
   - `GOOGLE_SHEET_KEY`(또는 주입된 client의 spreadsheet_id)가 올바른 스프레드시트인지 확인.

2. **인증 실패**  
   - `GOOGLE_CREDENTIALS_FILE` 경로·파일 유효성 확인.  
   - 서비스 계정 키가 해당 스프레드시트에 대한 접근 권한을 갖는지 확인.

3. **파싱 오류**  
   - 해당 시트의 헤더/행이 `CATEGORY | SUB_CATEGORY | KEY | VALUE | DESCRIPTION | TAG` 구조인지 확인.  
   - doc: [13_Config_3분할_Architecture.md](../../../arch/13_Config_3분할_Architecture.md) §2.2.

4. **Unified Config 실패**  
   - `load_unified_config` 실패 시 `result.error`에 Local 실패 또는 Sheet 실패 원인이 포함됨.  
   - Local 우선: 먼저 Config_Local 파일 경로·형식 해결 후, Sheet 쪽 404/인증/파싱 순으로 점검.

---

## 3. Health check 연계

- Sheet Config 단독 헬스체크는 `GoogleSheetsClient.health_check()` 및 시트 접근으로 간접 확인.  
- 실 시트 연동 시: `live_sheets` 마커 또는 env 설정 후 스모크 실행.  
- CI 기본: Mock 기반 `tests/config/test_sheet_config.py`로 인터페이스·실패 반환 검증.
