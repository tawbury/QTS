"""
UI Contract 단일 빌더.

Pipeline 종료 시 UI Contract는 **이 빌더에서만** 생성한다.
다른 모듈에서 UI Contract 구조를 직접 만들거나 수정하지 않는다.

참조: docs/arch/UI_Contract_Schema.md §4
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .contract_schema import UIContractVersion

_log = logging.getLogger(__name__)


class UIContractBuilder:
    """
    UI Contract 단일 팩토리.

    ETEDA 종료 후 한 번만 호출하여 전체 UI Contract dict를 생성한다.
    """

    @staticmethod
    def build(
        *,
        account: Dict[str, Any],
        symbols: List[Dict[str, Any]],
        pipeline_status: Dict[str, Any],
        performance: Optional[Dict[str, Any]] = None,
        risk: Optional[Dict[str, Any]] = None,
        meta_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Pipeline 종료 시 사용하는 단일 진입점.

        Args:
            account: 계좌 블록 (total_equity, daily_pnl 등, §3.1)
            symbols: 종목별 블록 리스트 (§3.2)
            pipeline_status: pipeline_state(필수), last_cycle_duration, last_error_code, cycle_timestamp (§3.5)
            performance: 선택, §3.3
            risk: 선택, §3.4
            meta_overrides: contract_version/timestamp 외 메타 덮어쓰기 (qts_version, broker_connected 등)

        Returns:
            UI Contract 루트 dict (account, symbols, performance, risk, pipeline_status, meta)

        Raises:
            ValueError: 필수 필드 누락 시 (total_equity, pipeline_state, symbols 존재)
        """
        # 필수 검증
        if not isinstance(account, dict):
            raise ValueError("account must be a dict")
        if "total_equity" not in account:
            raise ValueError("account must contain total_equity")
        if not isinstance(pipeline_status, dict) or not pipeline_status.get("pipeline_state"):
            raise ValueError("pipeline_status must contain pipeline_state")
        if not isinstance(symbols, list):
            raise ValueError("symbols must be a list")

        now = datetime.now(timezone.utc).isoformat()
        meta: Dict[str, Any] = {
            "contract_version": UIContractVersion,
            "timestamp": now,
        }
        if meta_overrides:
            meta.update({k: v for k, v in meta_overrides.items() if v is not None})

        result: Dict[str, Any] = {
            "account": _sanitize_account(account),
            "symbols": [_sanitize_symbol(s) for s in symbols],
            "pipeline_status": _sanitize_pipeline_status(pipeline_status, now),
            "meta": meta,
        }

        if performance is not None:
            result["performance"] = _sanitize_performance(performance)
        if risk is not None:
            result["risk"] = _sanitize_risk(risk)

        _log.debug("UIContractBuilder built contract version=%s", meta.get("contract_version"))
        return result


def _sanitize_account(raw: Dict[str, Any]) -> Dict[str, Any]:
    """§3.1 필드만 추출, NaN/None 표시 규칙 적용."""
    out: Dict[str, Any] = {}
    for key in ("total_equity", "daily_pnl", "realized_pnl", "unrealized_pnl", "exposure_pct"):
        v = raw.get(key)
        if v is not None and (not isinstance(v, float) or v == v):  # exclude NaN
            out[key] = v
        elif key in ("total_equity", "daily_pnl"):
            out[key] = 0.0 if v is None else v
    return out


def _sanitize_symbol(raw: Dict[str, Any]) -> Dict[str, Any]:
    """§3.2 필드만 추출."""
    keys = (
        "symbol", "price", "qty", "exposure_value", "unrealized_pnl",
        "strategy_signal", "risk_approved", "final_qty",
    )
    return {k: raw[k] for k in keys if k in raw and raw[k] is not None}


def _sanitize_pipeline_status(raw: Dict[str, Any], default_ts: str) -> Dict[str, Any]:
    """§3.5 필드 정리, cycle_timestamp 기본값."""
    out: Dict[str, Any] = {
        "pipeline_state": raw.get("pipeline_state", "IDLE"),
        "cycle_timestamp": raw.get("cycle_timestamp") or default_ts,
    }
    for key in ("last_cycle_duration", "last_error_code"):
        if key in raw and raw[key] is not None:
            out[key] = raw[key]
    return out


def _sanitize_performance(raw: Dict[str, Any]) -> Dict[str, Any]:
    """§3.3 필드만 추출."""
    keys = ("daily_pnl_curve", "mdd", "cagr", "win_rate", "strategy_performance_table")
    return {k: raw[k] for k in keys if k in raw and raw[k] is not None}


def _sanitize_risk(raw: Dict[str, Any]) -> Dict[str, Any]:
    """§3.4 필드만 추출."""
    keys = ("exposure_limit_pct", "current_exposure_pct", "risk_warnings", "rejected_signals")
    return {k: raw[k] for k in keys if k in raw and raw[k] is not None}
