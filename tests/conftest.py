# QTS/tests/conftest.py

import sys
from pathlib import Path

import pytest

# --------------------------------------------------
# QTS Project Root Injection (Canonical)
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"

# .env 로드 (실 API 테스트 등에서 GOOGLE_CREDENTIALS_FILE 등 사용)
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

# 프로젝트 루트 (paths.py 등)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# src 패키지
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def pytest_configure(config):
    """Register custom marks (e.g. live_sheets for tests requiring real API)."""
    config.addinivalue_line("markers", "live_sheets: mark test to run only when Google Sheets env is set (skip in CI)")
