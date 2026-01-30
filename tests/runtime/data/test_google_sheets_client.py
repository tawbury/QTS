"""
GoogleSheetsClient 단위/통합 테스트.

- Mock 기반: 생성자·예외 타입·인터페이스 검증 (CI 기본 실행).
- 실 API 연동: live_sheets 마커 또는 env 설정 시에만 실행.
"""

import os
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime.data.google_sheets_client import (
    GoogleSheetsClient,
    GoogleSheetsError,
    AuthenticationError,
    APIError,
    RateLimitError,
    ValidationError,
)


# ---------------------------------------------------------------------------
# 예외 타입 및 생성자 (Mock 없이)
# ---------------------------------------------------------------------------

class TestGoogleSheetsClientExceptions:
    """예외 타입·상속 관계 검증."""

    def test_authentication_error_is_google_sheets_error(self):
        e = AuthenticationError("auth failed")
        assert isinstance(e, GoogleSheetsError)

    def test_api_error_has_status_code(self):
        e = APIError("forbidden", status_code=403)
        assert e.status_code == 403

    def test_rate_limit_error_is_api_error(self):
        e = RateLimitError(retry_after=60)
        assert isinstance(e, APIError)
        assert e.retry_after == 60

    def test_validation_error_has_field(self):
        e = ValidationError("missing field", field="key")
        assert e.field == "key"


class TestGoogleSheetsClientConstructor:
    """생성자 계약: credentials/spreadsheet_id 없으면 ValueError."""

    def test_missing_credentials_raises(self):
        with patch("dotenv.load_dotenv"):
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError, match="credentials"):
                    GoogleSheetsClient(credentials_path=None, spreadsheet_id="id")

    def test_missing_spreadsheet_id_raises(self):
        with patch("dotenv.load_dotenv"):
            with patch.dict(os.environ, {"GOOGLE_CREDENTIALS_FILE": "/tmp/creds.json"}, clear=False):
                with pytest.raises(ValueError, match="spreadsheet"):
                    GoogleSheetsClient(credentials_path="/tmp/creds.json", spreadsheet_id=None)

    def test_env_credentials_and_sheet_key_ok(self):
        with patch("dotenv.load_dotenv"):
            with patch.dict(
                os.environ,
                {"GOOGLE_CREDENTIALS_FILE": "/tmp/c", "GOOGLE_SHEET_KEY": "sid"},
                clear=False,
            ):
                # 실제 파일이 없으면 이후 authenticate()에서 실패하지만 생성은 됨
                client = GoogleSheetsClient()
                assert client.credentials_path == "/tmp/c"
                assert client.spreadsheet_id == "sid"


# ---------------------------------------------------------------------------
# Mock 기반 API 동작 (실 네트워크 없음)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    """Env 주입 후 클라이언트 인스턴스 (service/gspread 미초기화)."""
    with patch.dict(
        os.environ,
        {"GOOGLE_CREDENTIALS_FILE": "/tmp/c", "GOOGLE_SHEET_KEY": "sid"},
        clear=False,
    ):
        return GoogleSheetsClient(credentials_path="/tmp/c", spreadsheet_id="sid")


@pytest.mark.asyncio
async def test_update_sheet_data_empty_values_raises_validation_error(mock_client):
    """빈 values로 update_sheet_data 호출 시 ValidationError."""
    mock_client.service = MagicMock()  # authenticate() 스킵
    with pytest.raises(ValidationError, match="No data"):
        await mock_client.update_sheet_data("Sheet1!A1", [])


@pytest.mark.asyncio
async def test_append_sheet_data_empty_values_raises_validation_error(mock_client):
    """빈 values로 append_sheet_data 호출 시 ValidationError."""
    mock_client.service = MagicMock()  # authenticate() 스킵
    with pytest.raises(ValidationError, match="No data"):
        await mock_client.append_sheet_data("Sheet1!A1", [])


# ---------------------------------------------------------------------------
# 실 스프레드시트 연동 (CI에서는 스킵)
# ---------------------------------------------------------------------------

@pytest.mark.live_sheets
@pytest.mark.skipif(
    not os.getenv("GOOGLE_CREDENTIALS_FILE") or not os.getenv("GOOGLE_SHEET_KEY"),
    reason="GOOGLE_CREDENTIALS_FILE and GOOGLE_SHEET_KEY required for live Sheets tests",
)
@pytest.mark.asyncio
async def test_health_check_live():
    """실 API 연동 시 health_check (env 설정 시에만 실행)."""
    client = GoogleSheetsClient()
    result = await client.health_check()
    assert "status" in result
    assert result["status"] in ("healthy", "unhealthy")
