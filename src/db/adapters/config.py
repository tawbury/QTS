"""
데이터 레이어 설정.

근거: docs/arch/sub/18_Data_Layer_Architecture.md §5, §6
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DataSourceMode(str, Enum):
    """데이터 소스 모드 (§5.2)."""

    SHEETS_ONLY = "SHEETS_ONLY"
    HYBRID = "HYBRID"
    DB_ONLY = "DB_ONLY"


@dataclass(frozen=True)
class ConnectionPoolConfig:
    """DB 커넥션 풀 설정 (§6.2)."""

    min_connections: int = 5
    max_connections: int = 20
    command_timeout: float = 5.0
    statement_cache_size: int = 100


@dataclass(frozen=True)
class DataLayerConfig:
    """데이터 레이어 전체 설정."""

    mode: DataSourceMode = DataSourceMode.SHEETS_ONLY
    db_dsn: str = ""
    pool: ConnectionPoolConfig = field(default_factory=ConnectionPoolConfig)
