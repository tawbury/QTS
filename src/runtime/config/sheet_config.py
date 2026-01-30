from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, List

from .config_models import ConfigEntry, ConfigLoadResult, ConfigScope


async def _fetch_sheet_as_rows(sheet_name: str) -> List[List[Any]]:
    """Fetch sheet range A:Z via GoogleSheetsClient (env-based)."""
    from ..data.google_sheets_client import GoogleSheetsClient

    client = GoogleSheetsClient()
    await client.authenticate()
    return await client.get_sheet_data(f"{sheet_name}!A:Z")


def _row_to_dict(row: List[Any], headers: List[str]) -> dict:
    """Map a row list to dict by headers; align with BaseSheetRepository._row_to_dict."""
    result = {}
    for i, header in enumerate(headers):
        value = row[i] if i < len(row) else ""
        if value == "" or value is None:
            result[header] = None
        elif isinstance(value, str) and value.lower() in ("true", "false"):
            result[header] = value.lower() == "true"
        else:
            try:
                s = str(value).strip()
                if "." in s:
                    result[header] = float(s)
                else:
                    result[header] = int(s)
            except (ValueError, TypeError):
                result[header] = value
    return result


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
        # Fetch via GoogleSheetsClient (env: GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_KEY)
        raw_values = asyncio.run(_fetch_sheet_as_rows(sheet_name))

        if not raw_values:
            return ConfigLoadResult(
                ok=True,
                scope=scope,
                entries=[],
                error=None,
                source_path=sheet_name,
            )

        # Index-aligned with row columns (same rule as BaseSheetRepository)
        headers = [str(c).strip() if c else "" for c in raw_values[0]]
        if not any(h for h in headers):
            return ConfigLoadResult(
                ok=True,
                scope=scope,
                entries=[],
                error=None,
                source_path=sheet_name,
            )

        data_rows = raw_values[1:]
        entries: List[ConfigEntry] = []
        for idx, row in enumerate(data_rows):
            row_dict = _row_to_dict(row if isinstance(row, list) else [], headers)
            try:
                entry = ConfigEntry(
                    category=str(row_dict.get("CATEGORY") or ""),
                    subcategory=str(row_dict.get("SUB_CATEGORY") or ""),
                    key=str(row_dict.get("KEY") or ""),
                    value=str(row_dict.get("VALUE") or ""),
                    description=str(row_dict.get("DESCRIPTION") or ""),
                    tag=str(row_dict.get("TAG") or ""),
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
