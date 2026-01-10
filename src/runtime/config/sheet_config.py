from __future__ import annotations

from pathlib import Path
from typing import List

from .config_models import ConfigEntry, ConfigLoadResult, ConfigScope


def load_sheet_config(project_root: Path, scope: ConfigScope) -> ConfigLoadResult:
    """
    Load Config_Scalp or Config_Swing from Google Sheet.
    
    Config_Scalp and Config_Swing are:
    - Google Sheet tabs within a single spreadsheet
    - Sheet name defines scope (Sheet = Scope)
    - Sheet structure and column headers are finalized
    - Sheets are edited manually by operator and treated as read-only by code
    
    Expected columns:
    - CATEGORY
    - SUB_CATEGORY
    - KEY
    - VALUE
    - DESCRIPTION
    - TAG
    
    Args:
        project_root: Project root path
        scope: ConfigScope.SCALP or ConfigScope.SWING
    
    Behavior:
    - Sheet not found -> ok=False
    - Sheet exists but empty (no data rows) -> ok=True with entries=[]
    - Empty config is treated as valid
    
    Returns:
        ConfigLoadResult with scope=SCALP or SWING
    """
    if scope not in (ConfigScope.SCALP, ConfigScope.SWING):
        return ConfigLoadResult(
            ok=False,
            scope=scope,
            entries=[],
            error=f"Invalid scope for sheet config: {scope}. Must be SCALP or SWING.",
            source_path=None,
        )
    
    # Determine sheet name from scope
    sheet_name = f"Config_{scope.value.capitalize()}"
    
    try:
        # Import Google Sheets client (lazy import to avoid dependency if not used)
        from runtime.data.google_sheets_client import GoogleSheetsClient
        
        # Initialize client
        client = GoogleSheetsClient(project_root=project_root)
        
        # Read sheet data
        # Expected: List[Dict[str, str]] with keys matching column headers
        data = client.read_sheet(sheet_name=sheet_name)
        
        if data is None:
            return ConfigLoadResult(
                ok=False,
                scope=scope,
                entries=[],
                error=f"Sheet '{sheet_name}' not found or inaccessible",
                source_path=sheet_name,
            )
        
        # Empty sheet is valid
        if len(data) == 0:
            return ConfigLoadResult(
                ok=True,
                scope=scope,
                entries=[],
                error=None,
                source_path=sheet_name,
            )
        
        # Parse entries
        entries: List[ConfigEntry] = []
        for idx, row in enumerate(data):
            if not isinstance(row, dict):
                return ConfigLoadResult(
                    ok=False,
                    scope=scope,
                    entries=[],
                    error=f"Sheet '{sheet_name}' row {idx} is not a dict",
                    source_path=sheet_name,
                )
            
            try:
                entry = ConfigEntry(
                    category=str(row.get("CATEGORY", "")),
                    subcategory=str(row.get("SUB_CATEGORY", "")),
                    key=str(row.get("KEY", "")),
                    value=str(row.get("VALUE", "")),
                    description=str(row.get("DESCRIPTION", "")),
                    tag=str(row.get("TAG", "")),
                )
                entries.append(entry)
            except Exception as e:
                return ConfigLoadResult(
                    ok=False,
                    scope=scope,
                    entries=[],
                    error=f"Failed to parse sheet '{sheet_name}' row {idx}: {e}",
                    source_path=sheet_name,
                )
        
        return ConfigLoadResult(
            ok=True,
            scope=scope,
            entries=entries,
            error=None,
            source_path=sheet_name,
        )
    
    except ImportError as e:
        return ConfigLoadResult(
            ok=False,
            scope=scope,
            entries=[],
            error=f"Google Sheets client not available: {e}",
            source_path=sheet_name,
        )
    except Exception as e:
        return ConfigLoadResult(
            ok=False,
            scope=scope,
            entries=[],
            error=f"Failed to load sheet '{sheet_name}': {e}",
            source_path=sheet_name,
        )


def validate_sheet_config_entries(entries: List[ConfigEntry]) -> tuple[bool, str]:
    """
    Validate Config_Scalp/Swing entries for required fields.
    
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
