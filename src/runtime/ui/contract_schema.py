"""
UI Contract 스키마 및 버전 상수.

Pipeline 종료 시 생성되는 UI Contract의 버전과 구조 타입을 정의한다.
스키마 상세: docs/arch/UI_Contract_Schema.md
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


# 스키마 문서와 동기화 (UI_Contract_Schema.md §1)
UIContractVersion = "1.0.0"


class AccountBlock(TypedDict, total=False):
    """Account-level 필드 (§3.1)."""
    total_equity: float
    daily_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    exposure_pct: float


class SymbolBlock(TypedDict, total=False):
    """Symbol-level 필드 (§3.2)."""
    symbol: str
    price: float
    qty: float
    exposure_value: float
    unrealized_pnl: float
    strategy_signal: str
    risk_approved: bool
    final_qty: float


class PerformanceBlock(TypedDict, total=False):
    """Performance 블록 (§3.3)."""
    daily_pnl_curve: List[float]
    mdd: float
    cagr: float
    win_rate: float
    strategy_performance_table: Any


class RiskBlock(TypedDict, total=False):
    """Risk 블록 (§3.4)."""
    exposure_limit_pct: float
    current_exposure_pct: float
    risk_warnings: List[str]
    rejected_signals: List[Any]


class PipelineStatusBlock(TypedDict, total=False):
    """Pipeline status 블록 (§3.5)."""
    pipeline_state: str
    last_cycle_duration: float
    last_error_code: str
    cycle_timestamp: str


class MetaBlock(TypedDict, total=False):
    """Meta 블록 (§3.6)."""
    contract_version: str
    schema_version: str
    qts_version: str
    broker_connected: bool
    timestamp: str


class UIContract(TypedDict, total=False):
    """UI Contract 루트 (§2)."""
    account: AccountBlock
    symbols: List[SymbolBlock]
    performance: PerformanceBlock
    risk: RiskBlock
    pipeline_status: PipelineStatusBlock
    meta: MetaBlock


def get_expected_contract_version() -> str:
    """렌더링 측에서 기대하는 Contract 버전."""
    return UIContractVersion
