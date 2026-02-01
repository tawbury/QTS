#!/usr/bin/env python3
"""
Google Sheets 연동 통합 테스트

.env의 GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_KEY를 사용해 실제 시트에 접근.
env 미설정 시 스킵. 시트 미존재(404) 시 빈 리스트 또는 스킵 처리.
"""

import os
import time
import pytest
from pathlib import Path

# .env 로드 (conftest에서도 로드하지만 여기서 명시)
try:
    from dotenv import load_dotenv
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


def _skip_if_no_sheets_env():
    """GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_KEY 없으면 스킵."""
    creds = os.getenv("GOOGLE_CREDENTIALS_FILE")
    key = os.getenv("GOOGLE_SHEET_KEY")
    if not creds or not key:
        pytest.skip(
            "Google Sheets env not set: set GOOGLE_CREDENTIALS_FILE and GOOGLE_SHEET_KEY in .env"
        )
    if not Path(creds).expanduser().exists():
        pytest.skip(f"Credentials file not found: {creds}")


@pytest.mark.live_sheets
@pytest.mark.asyncio
async def test_strategy_repository_live_sheets():
    """Strategy 리포지토리: .env 기반 실제 시트 get_all (연동 검증)."""
    _skip_if_no_sheets_env()
    from runtime.data.google_sheets_client import GoogleSheetsClient
    from runtime.data.repositories.strategy_repository import StrategyRepository

    for attempt in range(3):
        try:
            client = GoogleSheetsClient()
            await client.authenticate()
            repo = StrategyRepository(client, client.spreadsheet_id)
            rows = await repo.get_all()
            assert isinstance(rows, list)
            return
        except Exception as e:
            if "429" in str(e) and "Quota exceeded" in str(e) and attempt < 2:
                time.sleep(60)
                continue
            if "404" in str(e) or "not found" in str(e).lower():
                pytest.skip(f"Sheet Strategy not present in spreadsheet: {e}")
            raise


@pytest.mark.live_sheets
@pytest.mark.asyncio
async def test_repository_manager_health_check_live_sheets():
    """RepositoryManager: .env 기반 client 연동 후 health_check (Data Layer 통합 검증)."""
    _skip_if_no_sheets_env()
    from runtime.data.google_sheets_client import GoogleSheetsClient
    from runtime.data.repository_manager import RepositoryManager, register_all_base_repositories

    for attempt in range(3):
        try:
            client = GoogleSheetsClient()
            await client.authenticate()
            manager = RepositoryManager(client)
            register_all_base_repositories(manager)
            health = await manager.health_check()
            assert "status" in health
            assert "client" in health
            assert health["client"].get("status") == "healthy"
            assert "Strategy" in health.get("registered_classes", [])
            return
        except Exception as e:
            if "429" in str(e) and "Quota exceeded" in str(e) and attempt < 2:
                time.sleep(60)
                continue
            raise
