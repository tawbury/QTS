"""
자본 풀 상태 영속화 레이어.

JSONL 기반으로 풀 상태를 저장/로드한다.
매 사이클마다 전체 상태를 append하여 히스토리를 보존한다.

근거: docs/arch/sub/14_Capital_Flow_Architecture.md §6.1
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional

from src.capital.contracts import (
    CapitalPoolContract,
    PoolId,
    PoolState,
)

_LOG = logging.getLogger(__name__)


def _decimal_default(obj):
    """JSON 직렬화를 위한 Decimal 변환."""
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _pool_to_dict(pool: CapitalPoolContract) -> dict:
    """CapitalPoolContract → dict."""
    return {
        "pool_id": pool.pool_id.value,
        "total_capital": str(pool.total_capital),
        "invested_capital": str(pool.invested_capital),
        "reserved_capital": str(pool.reserved_capital),
        "realized_pnl": str(pool.realized_pnl),
        "unrealized_pnl": str(pool.unrealized_pnl),
        "accumulated_profit": str(pool.accumulated_profit),
        "allocation_pct": str(pool.allocation_pct),
        "target_allocation_pct": str(pool.target_allocation_pct),
        "pool_state": pool.pool_state.value,
        "last_promotion_at": pool.last_promotion_at.isoformat() if pool.last_promotion_at else None,
        "lock_reason": pool.lock_reason,
    }


def _dict_to_pool(d: dict) -> CapitalPoolContract:
    """dict → CapitalPoolContract."""
    last_promo = None
    if d.get("last_promotion_at"):
        last_promo = datetime.fromisoformat(d["last_promotion_at"])

    return CapitalPoolContract(
        pool_id=PoolId(d["pool_id"]),
        total_capital=Decimal(d["total_capital"]),
        invested_capital=Decimal(d.get("invested_capital", "0")),
        reserved_capital=Decimal(d.get("reserved_capital", "0")),
        realized_pnl=Decimal(d.get("realized_pnl", "0")),
        unrealized_pnl=Decimal(d.get("unrealized_pnl", "0")),
        accumulated_profit=Decimal(d.get("accumulated_profit", "0")),
        allocation_pct=Decimal(d.get("allocation_pct", "0")),
        target_allocation_pct=Decimal(d.get("target_allocation_pct", "0")),
        pool_state=PoolState(d.get("pool_state", "ACTIVE")),
        last_promotion_at=last_promo,
        lock_reason=d.get("lock_reason", ""),
    )


class CapitalPoolRepository:
    """풀 상태 JSONL 영속화."""

    def __init__(self, storage_path: Path) -> None:
        self._path = Path(storage_path)

    def load_pool_states(self) -> Optional[dict[PoolId, CapitalPoolContract]]:
        """최신 풀 상태 로드. 파일 없거나 비어있으면 None."""
        if not self._path.exists():
            return None

        last_line = None
        try:
            with self._path.open("r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        last_line = stripped
        except Exception:
            _LOG.warning("Failed to read pool states file")
            return None

        if not last_line:
            return None

        try:
            record = json.loads(last_line)
            pools_data = record.get("pools", {})
            pools: dict[PoolId, CapitalPoolContract] = {}
            for pool_id_str, pool_dict in pools_data.items():
                pool_dict["pool_id"] = pool_id_str
                pool = _dict_to_pool(pool_dict)
                pools[pool.pool_id] = pool
            return pools if pools else None
        except (json.JSONDecodeError, KeyError, ValueError):
            _LOG.warning("Corrupt pool state record, returning None")
            return None

    def save_pool_states(self, pools: dict[PoolId, CapitalPoolContract]) -> None:
        """풀 상태를 JSONL에 append."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pools": {
                pid.value: _pool_to_dict(pool)
                for pid, pool in pools.items()
            },
        }
        line = json.dumps(record, default=_decimal_default, ensure_ascii=False)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def create_default_pools(
        self, total_equity: Decimal
    ) -> dict[PoolId, CapitalPoolContract]:
        """초기 풀 생성 (100% Scalp). 저장 후 반환."""
        pools = {
            PoolId.SCALP: CapitalPoolContract(
                pool_id=PoolId.SCALP,
                total_capital=total_equity,
                allocation_pct=Decimal("1.00"),
                target_allocation_pct=Decimal("1.00"),
            ),
            PoolId.SWING: CapitalPoolContract(
                pool_id=PoolId.SWING,
                total_capital=Decimal("0"),
                allocation_pct=Decimal("0.00"),
                target_allocation_pct=Decimal("0.00"),
            ),
            PoolId.PORTFOLIO: CapitalPoolContract(
                pool_id=PoolId.PORTFOLIO,
                total_capital=Decimal("0"),
                allocation_pct=Decimal("0.00"),
                target_allocation_pct=Decimal("0.00"),
            ),
        }
        self.save_pool_states(pools)
        return pools
