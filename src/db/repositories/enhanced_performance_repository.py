"""Enhanced Performance Repository — Mock 구현 (local-only)."""
from __future__ import annotations
from typing import Any, Dict


class EnhancedPerformanceRepository:
    """Enhanced Performance 리포지토리. Mock."""

    def __init__(self, client: Any, spreadsheet_id: str, project_root: Any = None):
        self._client = client
        self._sid = spreadsheet_id
        self._project_root = project_root
