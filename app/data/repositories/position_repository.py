"""Position Repository — Mock 구현 (local-only)."""
from __future__ import annotations
from typing import Any, List
import asyncio


class PositionRepository:
    """포지션 리포지토리. Mock: 빈 목록 반환."""

    def __init__(self, client: Any, spreadsheet_id: str):
        self._client = client
        self._sid = spreadsheet_id

    async def get_all(self) -> List[dict]:
        return []
