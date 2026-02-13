"""
TimescaleDB 데이터 소스 어댑터.

근거: docs/arch/sub/18_Data_Layer_Architecture.md §4.2
- asyncpg 기반 비동기 DB 접근
- 파라미터화된 쿼리 (SQL Injection 방지)
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from src.db.contracts import (
    HealthStatus,
    LedgerEntry,
    OHLCV,
    Position,
    TickData,
)
from src.db.adapters.interface import DataSourceAdapter
from src.db.adapters.config import ConnectionPoolConfig

logger = logging.getLogger(__name__)


class TimescaleDBAdapter(DataSourceAdapter):
    """PostgreSQL + TimescaleDB 어댑터."""

    def __init__(
        self,
        dsn: str,
        pool_config: Optional[ConnectionPoolConfig] = None,
    ) -> None:
        self._dsn = dsn
        self._pool_config = pool_config or ConnectionPoolConfig()
        self._pool: Any = None  # asyncpg.Pool

    async def connect(self) -> None:
        """커넥션 풀 생성."""
        try:
            import asyncpg
        except ImportError as e:
            raise ImportError(
                "asyncpg is required for TimescaleDBAdapter. "
                "Install with: pip install asyncpg"
            ) from e

        self._pool = await asyncpg.create_pool(
            self._dsn,
            min_size=self._pool_config.min_connections,
            max_size=self._pool_config.max_connections,
            command_timeout=self._pool_config.command_timeout,
            statement_cache_size=self._pool_config.statement_cache_size,
        )
        logger.info("TimescaleDB connection pool created")

    async def close(self) -> None:
        """커넥션 풀 종료."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("TimescaleDB connection pool closed")

    def _ensure_pool(self) -> None:
        if self._pool is None:
            raise RuntimeError(
                "Connection pool not initialized. Call connect() first."
            )

    async def fetch_positions(self) -> list[Position]:
        self._ensure_pool()
        rows = await self._pool.fetch(
            """
            SELECT symbol, qty, avg_price, market,
                   exposure_value, exposure_pct, unrealized_pnl, updated_at
            FROM positions ORDER BY symbol
            """
        )
        return [self._row_to_position(r) for r in rows]

    async def fetch_position(self, symbol: str) -> Optional[Position]:
        self._ensure_pool()
        row = await self._pool.fetchrow(
            """
            SELECT symbol, qty, avg_price, market,
                   exposure_value, exposure_pct, unrealized_pnl, updated_at
            FROM positions WHERE symbol = $1
            """,
            symbol,
        )
        return self._row_to_position(row) if row else None

    async def update_position(
        self, symbol: str, qty: Decimal, avg_price: Decimal
    ) -> bool:
        self._ensure_pool()
        await self._pool.execute(
            """
            INSERT INTO positions (symbol, qty, avg_price, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (symbol) DO UPDATE
            SET qty = $2, avg_price = $3, updated_at = NOW()
            """,
            symbol,
            qty,
            avg_price,
        )
        return True

    async def append_ledger(self, entry: LedgerEntry) -> bool:
        self._ensure_pool()
        await self._pool.execute(
            """
            INSERT INTO t_ledger
            (timestamp, symbol, side, qty, price, amount, fee,
             strategy_tag, order_id, broker)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            entry.timestamp,
            entry.symbol,
            entry.side,
            entry.qty,
            entry.price,
            entry.amount,
            entry.fee,
            entry.strategy_tag,
            entry.order_id,
            entry.broker,
        )
        return True

    async def fetch_ledger(
        self,
        symbol: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[LedgerEntry]:
        self._ensure_pool()
        conditions: list[str] = []
        params: list[Any] = []
        idx = 1

        if symbol:
            conditions.append(f"symbol = ${idx}")
            params.append(symbol)
            idx += 1
        if start:
            conditions.append(f"timestamp >= ${idx}")
            params.append(start)
            idx += 1
        if end:
            conditions.append(f"timestamp < ${idx}")
            params.append(end)
            idx += 1

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT id, timestamp, symbol, side, qty, price, amount,
                   fee, strategy_tag, order_id, broker
            FROM t_ledger {where}
            ORDER BY timestamp DESC
            LIMIT ${idx}
        """
        params.append(limit)

        rows = await self._pool.fetch(query, *params)
        return [self._row_to_ledger(r) for r in rows]

    async def fetch_ohlcv(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> list[OHLCV]:
        self._ensure_pool()
        table = "ohlcv_1d" if interval == "1d" else "ohlcv_1m"
        time_col = "time" if interval == "1d" else "bucket"
        rows = await self._pool.fetch(
            f"""
            SELECT {time_col} AS time, symbol, open, high, low, close, volume
            FROM {table}
            WHERE symbol = $1 AND {time_col} >= $2 AND {time_col} < $3
            ORDER BY {time_col}
            """,
            symbol,
            start,
            end,
        )
        return [
            OHLCV(
                time=r["time"],
                symbol=r["symbol"],
                open=Decimal(str(r["open"])),
                high=Decimal(str(r["high"])),
                low=Decimal(str(r["low"])),
                close=Decimal(str(r["close"])),
                volume=r["volume"],
            )
            for r in rows
        ]

    async def fetch_tick_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> list[TickData]:
        self._ensure_pool()
        rows = await self._pool.fetch(
            """
            SELECT time, symbol, price, volume, bid, ask, source
            FROM tick_data
            WHERE symbol = $1 AND time >= $2 AND time < $3
            ORDER BY time
            """,
            symbol,
            start,
            end,
        )
        return [
            TickData(
                time=r["time"],
                symbol=r["symbol"],
                price=Decimal(str(r["price"])),
                volume=r["volume"],
                bid=Decimal(str(r["bid"])) if r["bid"] else None,
                ask=Decimal(str(r["ask"])) if r["ask"] else None,
                source=r["source"] or "",
            )
            for r in rows
        ]

    async def store_execution_log(
        self,
        order_id: str,
        symbol: str,
        stage: str,
        latency_ms: float,
        success: bool,
        error_code: Optional[str] = None,
    ) -> bool:
        """실행 로그 저장."""
        self._ensure_pool()
        await self._pool.execute(
            """INSERT INTO execution_logs
            (time, order_id, symbol, stage, latency_ms, success, error_code)
            VALUES (NOW(), $1, $2, $3, $4, $5, $6)""",
            order_id,
            symbol,
            stage,
            latency_ms,
            success,
            error_code,
        )
        return True

    async def fetch_execution_logs(
        self,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        order_id: Optional[str] = None,
        limit: int = 1000,
    ) -> list[dict]:
        """실행 로그 조회."""
        self._ensure_pool()
        conditions: list[str] = []
        params: list[Any] = []
        idx = 1
        if start:
            conditions.append(f"time >= ${idx}")
            params.append(start)
            idx += 1
        if end:
            conditions.append(f"time < ${idx}")
            params.append(end)
            idx += 1
        if order_id:
            conditions.append(f"order_id = ${idx}")
            params.append(order_id)
            idx += 1
        where = " AND ".join(conditions) if conditions else "TRUE"
        rows = await self._pool.fetch(
            f"SELECT * FROM execution_logs WHERE {where} "
            f"ORDER BY time DESC LIMIT {limit}",
            *params,
        )
        return [dict(r) for r in rows]

    async def initialize_retention_policies(self) -> None:
        """보존 정책 초기화."""
        self._ensure_pool()
        policies = {
            "tick_data": "7 days",
            "execution_logs": "90 days",
        }
        for table, interval in policies.items():
            try:
                await self._pool.execute(
                    f"SELECT add_retention_policy('{table}', "
                    f"INTERVAL '{interval}', if_not_exists => TRUE);"
                )
            except Exception:
                logger.warning(
                    "Failed to add retention policy for %s", table
                )

    async def health_check(self) -> HealthStatus:
        if self._pool is None:
            return HealthStatus(
                healthy=False,
                source="timescaledb",
                error="pool_not_initialized",
            )
        try:
            start = time.monotonic()
            await self._pool.fetchval("SELECT 1")
            latency = (time.monotonic() - start) * 1000
            return HealthStatus(
                healthy=True, source="timescaledb", latency_ms=latency
            )
        except Exception as e:
            return HealthStatus(
                healthy=False, source="timescaledb", error=str(e)
            )

    @staticmethod
    def _row_to_position(row: Any) -> Position:
        return Position(
            symbol=row["symbol"],
            qty=Decimal(str(row["qty"])),
            avg_price=Decimal(str(row["avg_price"])),
            market=row.get("market") or "",
            exposure_value=Decimal(str(row.get("exposure_value") or 0)),
            exposure_pct=Decimal(str(row.get("exposure_pct") or 0)),
            unrealized_pnl=Decimal(str(row.get("unrealized_pnl") or 0)),
            updated_at=row.get("updated_at"),
        )

    @staticmethod
    def _row_to_ledger(row: Any) -> LedgerEntry:
        return LedgerEntry(
            id=row["id"],
            timestamp=row["timestamp"],
            symbol=row["symbol"],
            side=row["side"],
            qty=Decimal(str(row["qty"])),
            price=Decimal(str(row["price"])),
            amount=Decimal(str(row["amount"])),
            fee=Decimal(str(row.get("fee") or 0)),
            strategy_tag=row.get("strategy_tag") or "",
            order_id=row.get("order_id") or "",
            broker=row.get("broker") or "",
        )
