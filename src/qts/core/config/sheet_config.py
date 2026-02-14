"""
Sheet 기반 Config 로딩 (Config_Scalp / Config_Swing).

- ConfigScalpRepository / ConfigSwingRepository를 사용해 시트 데이터 조회.
- SCALP/SWING 스코프별 로딩 경로·실패 처리: docs/arch/13_Config_3분할_Architecture.md
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from .config_constants import (
    COL_CATEGORY,
    COL_DESCRIPTION,
    COL_KEY,
    COL_SUB_CATEGORY,
    COL_TAG,
    COL_VALUE,
    SHEET_NAME_CONFIG_SCALP,
    SHEET_NAME_CONFIG_SWING,
)
from .config_models import ConfigEntry, ConfigLoadResult, ConfigScope

if TYPE_CHECKING:
    from src.db.google_sheets_client import GoogleSheetsClient


def _scope_to_sheet_name(scope: ConfigScope) -> str:
    """ConfigScope -> 시트 이름 (SCALP -> Config_Scalp, SWING -> Config_Swing)."""
    if scope == ConfigScope.SCALP:
        return SHEET_NAME_CONFIG_SCALP
    if scope == ConfigScope.SWING:
        return SHEET_NAME_CONFIG_SWING
    raise ValueError(f"Invalid scope for sheet config: {scope}. Use SCALP or SWING.")


async def _load_sheet_config_async(
    scope: ConfigScope,
    client: Optional["GoogleSheetsClient"] = None,
) -> ConfigLoadResult:
    """
    Config_Scalp 또는 Config_Swing 시트를 Repository로 조회.

    client가 없으면 GoogleSheetsClient()로 생성 후 authenticate() 호출.
    client가 주입되면 그대로 사용(호출자가 인증 완료한 상태로 전달).

    실패 케이스:
    - 시트 미존재(404): ok=False, error에 시트명 포함
    - 인증 실패: ok=False, error에 Authentication 메시지
    - 필드/파싱 오류: ok=False, error에 행/필드 정보
    """
    sheet_name = _scope_to_sheet_name(scope)

    from src.db.google_sheets_client import APIError, AuthenticationError, GoogleSheetsClient
    from src.db.repositories.config_scalp_repository import ConfigScalpRepository
    from src.db.repositories.config_swing_repository import ConfigSwingRepository

    try:
        if client is None:
            client = GoogleSheetsClient()
            await client.authenticate()
        spreadsheet_id = client.spreadsheet_id

        if scope == ConfigScope.SCALP:
            repo = ConfigScalpRepository(client, spreadsheet_id)
        else:
            repo = ConfigSwingRepository(client, spreadsheet_id)

        records = await repo.get_all()
    except ImportError as e:
        return ConfigLoadResult(
            ok=False,
            scope=scope,
            entries=[],
            error=f"Google Sheets client or repository not available: {e}",
            source_path=sheet_name,
        )
    except AuthenticationError as e:
        return ConfigLoadResult(
            ok=False,
            scope=scope,
            entries=[],
            error=f"Authentication failed for sheet config: {e}",
            source_path=sheet_name,
        )
    except APIError as e:
        msg = str(e)
        if getattr(e, "status_code", None) == 404:
            msg = f"Sheet not found: '{sheet_name}' (404)"
        return ConfigLoadResult(
            ok=False,
            scope=scope,
            entries=[],
            error=f"Sheet config load failed: {msg}",
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

    entries: List[ConfigEntry] = []
    for idx, rec in enumerate(records):
        try:
            entry = ConfigEntry(
                category=str(rec.get(COL_CATEGORY) or ""),
                subcategory=str(rec.get(COL_SUB_CATEGORY) or ""),
                key=str(rec.get(COL_KEY) or ""),
                value=str(rec.get(COL_VALUE) or ""),
                description=str(rec.get(COL_DESCRIPTION) or ""),
                tag=str(rec.get(COL_TAG) or ""),
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


def load_sheet_config(
    project_root: Path,
    scope: ConfigScope,
    client: Optional["GoogleSheetsClient"] = None,
) -> ConfigLoadResult:
    """
    Config_Scalp 또는 Config_Swing을 Google Sheet(Repository)에서 로드.

    - Sheet = Scope: Config_Scalp / Config_Swing 시트 이름으로 스코프 구분.
    - 구현: ConfigScalpRepository / ConfigSwingRepository 사용.
    - client가 주입되면 해당 인스턴스 사용(호출부·매니저와 시그니처 정합); 없으면 env 기반 생성.

    실패 처리:
    - 시트 미존재(404): ok=False
    - 인증 실패: ok=False
    - 필드 누락/파싱 오류: ok=False, error에 위치 정보

    Args:
        project_root: 프로젝트 루트 (Sheet ID가 env/주입 client에서 로드되므로 호출부 호환용)
        scope: ConfigScope.SCALP 또는 ConfigScope.SWING
        client: 선택. GoogleSheetsClient 인스턴스(인증 완료). None이면 env 기반 생성.

    Returns:
        ConfigLoadResult (scope=SCALP|SWING)
    """
    if scope not in (ConfigScope.SCALP, ConfigScope.SWING):
        return ConfigLoadResult(
            ok=False,
            scope=scope,
            entries=[],
            error=f"Invalid scope for sheet config: {scope}. Must be SCALP or SWING.",
            source_path=None,
        )

    return asyncio.run(_load_sheet_config_async(scope, client))


def validate_sheet_config_entries(entries: List[ConfigEntry]) -> tuple[bool, str]:
    """
    Config_Scalp/Swing 엔트리 필수 필드 검증.

    - category, subcategory, key 비어 있으면 안 됨.
    - value는 비어 있어도 됨.
    """
    for idx, entry in enumerate(entries):
        if not entry.category.strip():
            return False, f"Entry {idx}: category is empty"
        if not entry.subcategory.strip():
            return False, f"Entry {idx}: subcategory is empty"
        if not entry.key.strip():
            return False, f"Entry {idx}: key is empty"
    return True, ""
