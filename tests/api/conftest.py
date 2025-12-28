import os
import pytest
from dotenv import load_dotenv
from pathlib import Path


# 프로젝트 루트 기준 .env 로드
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def pytest_collection_modifyitems(config, items):
    if os.getenv("QTS_API_TEST") != "1":
        skip_marker = pytest.mark.skip(reason="QTS_API_TEST not enabled")
        for item in items:
            item.add_marker(skip_marker)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "api_exploration: real broker api exploration tests (Phase 1.5 only)"
    )
