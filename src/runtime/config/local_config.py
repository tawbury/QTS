from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .config_models import ConfigEntry, ConfigLoadResult, ConfigScope


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
    config_path = project_root / "config" / "local" / "config_local.json"
    
    if not config_path.exists():
        return ConfigLoadResult(
            ok=False,
            scope=ConfigScope.LOCAL,
            entries=[],
            error=f"Config_Local file not found: {config_path}",
            source_path=str(config_path),
        )
    
    try:
        with open(config_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            return ConfigLoadResult(
                ok=False,
                scope=ConfigScope.LOCAL,
                entries=[],
                error="Config_Local must be a JSON array",
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
                    error=f"Failed to parse Config_Local entry {idx}: {e}",
                    source_path=str(config_path),
                )
        
        return ConfigLoadResult(
            ok=True,
            scope=ConfigScope.LOCAL,
            entries=entries,
            error=None,
            source_path=str(config_path),
        )
    
    except json.JSONDecodeError as e:
        return ConfigLoadResult(
            ok=False,
            scope=ConfigScope.LOCAL,
            entries=[],
            error=f"Invalid JSON in Config_Local: {e}",
            source_path=str(config_path),
        )
    except Exception as e:
        return ConfigLoadResult(
            ok=False,
            scope=ConfigScope.LOCAL,
            entries=[],
            error=f"Failed to load Config_Local: {e}",
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
