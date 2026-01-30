"""
Config 로딩 경로 상수 (매직 스트링 축소).

- Sheet 이름, 컬럼명, 파일 경로는 SSOT로 본 모듈에서 정의.
- 근거: docs/arch/13_Config_3분할_Architecture.md
"""

# --- Sheet scope names (Sheet = Scope) ---
SHEET_NAME_CONFIG_SCALP = "Config_Scalp"
SHEET_NAME_CONFIG_SWING = "Config_Swing"

# --- Config sheet column headers (권장 컬럼, 현행 호환) ---
COL_CATEGORY = "CATEGORY"
COL_SUB_CATEGORY = "SUB_CATEGORY"
COL_KEY = "KEY"
COL_VALUE = "VALUE"
COL_DESCRIPTION = "DESCRIPTION"
COL_TAG = "TAG"

CONFIG_SHEET_COLUMNS = (
    COL_CATEGORY,
    COL_SUB_CATEGORY,
    COL_KEY,
    COL_VALUE,
    COL_DESCRIPTION,
    COL_TAG,
)

# --- Local config file path (relative to project_root) ---
LOCAL_CONFIG_DIR = "config"
LOCAL_CONFIG_SUBDIR = "local"
LOCAL_CONFIG_FILENAME = "config_local.json"
DIVIDEND_DB_FILENAME = "dividend_db.json"
