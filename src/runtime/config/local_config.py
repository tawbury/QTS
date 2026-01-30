from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List

from .config_constants import (
    LOCAL_CONFIG_DIR,
    LOCAL_CONFIG_FILENAME,
    LOCAL_CONFIG_SUBDIR,
)
from .config_models import ConfigEntry, ConfigLoadResult, ConfigScope

_LOG = logging.getLogger(__name__)


def _user_friendly_json_error(exc: json.JSONDecodeError) -> str:
    """JSONDecodeError를 사용자 친화적 한 줄 메시지로 변환."""
    msg = f"JSON 형식 오류 (줄 {exc.lineno}, 열 {exc.colno})"
    if getattr(exc, "msg", None):
        msg += f": {exc.msg}"
    if getattr(exc, "doc", None) and getattr(exc, "pos", None) is not None:
        doc = exc.doc or ""
        pos = exc.pos
        snippet = doc[max(0, pos - 20) : pos + 20].replace("\n", " ")
        msg += f" — '{snippet}' 근처를 확인하세요."
    return msg


def load_local_config(project_root: Path) -> ConfigLoadResult:
    """
    Load Config_Local from local file.
    
    Config_Local is:
    - File-based (not Google Sheet)
    - Protected and immutable from strategy perspective
    - Contains system, broker, risk, and safety parameters
    
    File location: config/local/config_local.json
    
    Expected structure:
    [
        {
            "category": "SYSTEM",
            "subcategory": "BROKER",
            "key": "API_ENDPOINT",
            "value": "https://...",
            "description": "...",
            "tag": "..."
        },
        ...
    ]
    
    Behavior:
    - File not found -> ok=False
    - File exists but empty list [] -> ok=True with entries=[]
    - Empty config is treated as valid
    
    Returns:
        ConfigLoadResult with scope=LOCAL
    """
    config_path = project_root / LOCAL_CONFIG_DIR / LOCAL_CONFIG_SUBDIR / LOCAL_CONFIG_FILENAME
    
    if not config_path.exists():
        err = (
            f"Config_Local 파일을 찾을 수 없습니다: {config_path}. "
            f"경로 {LOCAL_CONFIG_DIR}/{LOCAL_CONFIG_SUBDIR}/{LOCAL_CONFIG_FILENAME} 를 확인하세요."
        )
        _LOG.warning("%s", err)
        return ConfigLoadResult(
            ok=False,
            scope=ConfigScope.LOCAL,
            entries=[],
            error=err,
            source_path=str(config_path),
        )
    
    try:
        with open(config_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except OSError as e:
        err = f"Config_Local 파일을 읽을 수 없습니다 (인코딩/경로 확인): {e}"
        _LOG.warning("%s", err)
        return ConfigLoadResult(
            ok=False,
            scope=ConfigScope.LOCAL,
            entries=[],
            error=err,
            source_path=str(config_path),
        )
    except json.JSONDecodeError as e:
        err = f"Config_Local {_user_friendly_json_error(e)}"
        _LOG.warning("%s", err)
        return ConfigLoadResult(
            ok=False,
            scope=ConfigScope.LOCAL,
            entries=[],
            error=err,
            source_path=str(config_path),
        )

    try:
        if not isinstance(data, list):
            return ConfigLoadResult(
                ok=False,
                scope=ConfigScope.LOCAL,
                entries=[],
                error="Config_Local 내용은 JSON 배열이어야 합니다. 최상위가 [...] 형태인지 확인하세요.",
                source_path=str(config_path),
            )
        
        entries: List[ConfigEntry] = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                return ConfigLoadResult(
                    ok=False,
                    scope=ConfigScope.LOCAL,
                    entries=[],
                    error=f"Config_Local entry {idx} is not a dict",
                    source_path=str(config_path),
                )
            
            try:
                entry = ConfigEntry(
                    category=str(item.get("category", "")),
                    subcategory=str(item.get("subcategory", "")),
                    key=str(item.get("key", "")),
                    value=str(item.get("value", "")),
                    description=str(item.get("description", "")),
                    tag=str(item.get("tag", "")),
                )
                entries.append(entry)
            except Exception as e:
                return ConfigLoadResult(
                    ok=False,
                    scope=ConfigScope.LOCAL,
                    entries=[],
                    error=f"Config_Local 항목 {idx} 파싱 실패: {e}. category/subcategory/key 등 필드 형식을 확인하세요.",
                    source_path=str(config_path),
                )
        
        return ConfigLoadResult(
            ok=True,
            scope=ConfigScope.LOCAL,
            entries=entries,
            error=None,
            source_path=str(config_path),
        )
    except Exception as e:
        err = f"Config_Local 로드 중 오류: {e}"
        _LOG.warning("%s", err)
        return ConfigLoadResult(
            ok=False,
            scope=ConfigScope.LOCAL,
            entries=[],
            error=err,
            source_path=str(config_path),
        )


def validate_local_config_entries(entries: List[ConfigEntry]) -> tuple[bool, str]:
    """
    Validate Config_Local entries for required fields.
    
    Rules:
    - category, subcategory, key must be non-empty
    - value may be empty (valid for some configs)
    
    Returns:
        (is_valid, error_message)
    """
    for idx, entry in enumerate(entries):
        if not entry.category.strip():
            return False, f"Entry {idx}: category is empty"
        if not entry.subcategory.strip():
            return False, f"Entry {idx}: subcategory is empty"
        if not entry.key.strip():
            return False, f"Entry {idx}: key is empty"
    
    return True, ""
