#!/usr/bin/env python3
"""
Sheet Config 로딩 테스트 (Mock 기반).

- load_sheet_config(project_root, scope, client=None) 인터페이스 및 실패 시나리오 검증.
- CI 기본 실행: Mock client/Repository 사용. 실 시트 연동은 live_sheets 마커.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.qts.core.config.sheet_config import (
    load_sheet_config,
    validate_sheet_config_entries,
    _scope_to_sheet_name,
)
from src.qts.core.config.config_models import ConfigScope, ConfigEntry, ConfigLoadResult
from src.qts.core.config.config_constants import (
    COL_CATEGORY,
    COL_SUB_CATEGORY,
    COL_KEY,
    COL_VALUE,
    COL_DESCRIPTION,
    COL_TAG,
)


class TestSheetConfigScope:
    """Scope·시트명 매핑 및 invalid scope."""

    def test_scope_to_sheet_name_scalp(self):
        assert _scope_to_sheet_name(ConfigScope.SCALP) == "Config_Scalp"

    def test_scope_to_sheet_name_swing(self):
        assert _scope_to_sheet_name(ConfigScope.SWING) == "Config_Swing"

    def test_load_sheet_config_invalid_scope_returns_ok_false(self):
        """Scope가 SCALP/SWING이 아니면 ok=False, error 메시지."""
        project_root = Path(".")
        result = load_sheet_config(project_root, ConfigScope.LOCAL, client=None)
        assert result.ok is False
        assert result.entries == []
        assert result.error and "Invalid scope" in result.error
        assert result.scope == ConfigScope.LOCAL


class TestSheetConfigWithMockClient:
    """Mock client·Repository를 사용한 load_sheet_config 검증."""

    @pytest.fixture
    def mock_sheet_records(self):
        return [
            {
                COL_CATEGORY: "RISK",
                COL_SUB_CATEGORY: "LIMITS",
                COL_KEY: "MAX_POSITION",
                COL_VALUE: "10",
                COL_DESCRIPTION: "Max position count",
                COL_TAG: "STABLE",
            },
        ]

    def test_load_sheet_config_scalp_with_mock_client(self, mock_sheet_records):
        """SCALP scope + Mock client → ok=True, entries 반환."""
        mock_client = Mock()
        mock_client.spreadsheet_id = "test_sheet_id"
        mock_repo = Mock()
        mock_repo.get_all = AsyncMock(return_value=mock_sheet_records)
        with patch(
            "src.db.repositories.config_scalp_repository.ConfigScalpRepository",
            return_value=mock_repo,
        ), patch(
            "src.db.repositories.config_swing_repository.ConfigSwingRepository",
            return_value=mock_repo,
        ):
            result = load_sheet_config(Path("."), ConfigScope.SCALP, client=mock_client)
        assert result.ok is True
        assert result.scope == ConfigScope.SCALP
        assert len(result.entries) == 1
        assert result.entries[0].category == "RISK"
        assert result.entries[0].key == "MAX_POSITION"
        assert result.entries[0].value == "10"

    def test_load_sheet_config_swing_with_mock_client(self, mock_sheet_records):
        """SWING scope + Mock client → ok=True, entries 반환."""
        mock_client = Mock()
        mock_client.spreadsheet_id = "test_sheet_id"
        mock_repo = Mock()
        mock_repo.get_all = AsyncMock(return_value=mock_sheet_records)
        with patch(
            "src.db.repositories.config_scalp_repository.ConfigScalpRepository",
            return_value=mock_repo,
        ), patch(
            "src.db.repositories.config_swing_repository.ConfigSwingRepository",
            return_value=mock_repo,
        ):
            result = load_sheet_config(Path("."), ConfigScope.SWING, client=mock_client)
        assert result.ok is True
        assert result.scope == ConfigScope.SWING
        assert len(result.entries) == 1
        assert result.entries[0].key == "MAX_POSITION"


class TestSheetConfigClientInjection:
    """client 주입 시 GoogleSheetsClient 미생성 검증."""

    def test_load_sheet_config_with_client_does_not_create_client(self):
        """client가 주입되면 GoogleSheetsClient()가 호출되지 않음."""
        mock_client = Mock()
        mock_client.spreadsheet_id = "sid"
        mock_repo = Mock()
        mock_repo.get_all = AsyncMock(return_value=[])
        with patch(
            "src.db.google_sheets_client.GoogleSheetsClient",
        ) as mock_gs_client, patch(
            "src.db.repositories.config_scalp_repository.ConfigScalpRepository",
            return_value=mock_repo,
        ), patch(
            "src.db.repositories.config_swing_repository.ConfigSwingRepository",
            return_value=mock_repo,
        ):
            load_sheet_config(Path("."), ConfigScope.SCALP, client=mock_client)
        mock_gs_client.assert_not_called()


class TestValidateSheetConfigEntries:
    """validate_sheet_config_entries 검증."""

    def test_validate_success(self):
        entries = [
            ConfigEntry(
                category="C", subcategory="S", key="K", value="V",
                description="D", tag="T",
            ),
        ]
        ok, err = validate_sheet_config_entries(entries)
        assert ok is True
        assert err == ""

    def test_validate_empty_category_fails(self):
        entries = [
            ConfigEntry(
                category="", subcategory="S", key="K", value="V",
                description="D", tag="T",
            ),
        ]
        ok, err = validate_sheet_config_entries(entries)
        assert ok is False
        assert "category" in err.lower()
