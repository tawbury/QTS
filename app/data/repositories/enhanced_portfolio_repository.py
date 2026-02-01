"""Enhanced Portfolio Repository — Mock 구현 (local-only)."""
from __future__ import annotations
from typing import Any, Dict


class EnhancedPortfolioRepository:
    """Enhanced Portfolio 리포지토리. Mock: 무조건 성공."""

    def __init__(self, client: Any, spreadsheet_id: str, project_root: Any = None):
        self._client = client
        self._sid = spreadsheet_id
        self._project_root = project_root

    def update_kpi_overview(self, kpi_data: Dict[str, Any]) -> bool:
        return True
