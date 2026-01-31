"""
Execution Mode 통합 정의

이 모듈은 QTS 시스템의 실행 모드를 정의합니다.

두 가지 관점의 실행 모드를 제공합니다:
1. PipelineMode: ETEDA 파이프라인 단계 (VIRTUAL → SIM → REAL)
2. TradingMode: 거래 실행 모드 (PAPER / LIVE)

Mapping:
    VIRTUAL → (validation only, no trading)
    SIM     → PAPER
    REAL    → LIVE

Usage:
    # Runtime 거래 실행
    from runtime.config.execution_mode import ExecutionMode  # = TradingMode

    # Pipeline 실행 모드
    from runtime.config.execution_mode import PipelineMode

    # 변환
    from runtime.config.execution_mode import pipeline_to_trading_mode
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PipelineMode(str, Enum):
    """
    ETEDA 파이프라인 실행 모드.

    - VIRTUAL: 검증만 수행, 부작용 없음 (거래 실행 안함)
    - SIM: 시뮬레이션/페이퍼 실행 (모의 거래)
    - REAL: 실거래 실행

    전환은 Config + Guard 통과 시에만 허용됩니다.
    """

    VIRTUAL = "VIRTUAL"
    SIM = "SIM"
    REAL = "REAL"


class TradingMode(str, Enum):
    """
    거래 실행 모드.

    - PAPER: 모의 거래 (시뮬레이션)
    - LIVE: 실거래

    LIVE 모드 활성화에는 추가 인증(ACK)이 필요합니다.
    """

    PAPER = "PAPER"
    LIVE = "LIVE"


def pipeline_to_trading_mode(pipeline_mode: PipelineMode) -> Optional[TradingMode]:
    """
    PipelineMode를 TradingMode로 변환합니다.

    Args:
        pipeline_mode: ETEDA 파이프라인 실행 모드

    Returns:
        TradingMode 또는 None (VIRTUAL인 경우 거래 없음)

    Mapping:
        VIRTUAL → None (거래 실행 안함)
        SIM     → PAPER
        REAL    → LIVE
    """
    mapping = {
        PipelineMode.VIRTUAL: None,
        PipelineMode.SIM: TradingMode.PAPER,
        PipelineMode.REAL: TradingMode.LIVE,
    }
    return mapping.get(pipeline_mode)


def trading_to_pipeline_mode(trading_mode: TradingMode) -> PipelineMode:
    """
    TradingMode를 PipelineMode로 변환합니다.

    Args:
        trading_mode: 거래 실행 모드

    Returns:
        PipelineMode

    Mapping:
        PAPER → SIM
        LIVE  → REAL
    """
    mapping = {
        TradingMode.PAPER: PipelineMode.SIM,
        TradingMode.LIVE: PipelineMode.REAL,
    }
    return mapping[trading_mode]


# ============================================================
# Runtime Backward Compatibility
# ============================================================
# Runtime에서의 ExecutionMode는 TradingMode를 사용
ExecutionMode = TradingMode


@dataclass(frozen=True)
class LiveGateDecision:
    """LIVE 거래 허용 여부 결정 결과."""
    mode: ExecutionMode
    live_allowed: bool
    reason: str


def decide_execution_mode(
    sheet_execution_mode: str | None,
    sheet_live_enabled: str | None,
    env_live_ack: str | None,
    *,
    required_ack: str = "I_UNDERSTAND_LIVE_TRADING",
) -> LiveGateDecision:
    """
    Decide whether LIVE execution is allowed.

    Rules (AND for LIVE):
    1) sheet_execution_mode == "LIVE"
    2) sheet_live_enabled truthy ("1", "true", "yes", "on")
    3) env_live_ack matches required_ack exactly

    Default: PAPER
    """
    mode_raw = (sheet_execution_mode or "").strip().upper()
    enabled_raw = (sheet_live_enabled or "").strip().lower()

    if mode_raw != ExecutionMode.LIVE.value:
        return LiveGateDecision(
            mode=ExecutionMode.PAPER,
            live_allowed=False,
            reason="mode_not_live",
        )

    truthy = {"1", "true", "yes", "on", "y"}
    if enabled_raw not in truthy:
        return LiveGateDecision(
            mode=ExecutionMode.LIVE,
            live_allowed=False,
            reason="live_enabled_false",
        )

    if (env_live_ack or "").strip() != required_ack:
        return LiveGateDecision(
            mode=ExecutionMode.LIVE,
            live_allowed=False,
            reason="ack_missing_or_invalid",
        )

    return LiveGateDecision(
        mode=ExecutionMode.LIVE,
        live_allowed=True,
        reason="live_allowed",
    )


__all__ = [
    "PipelineMode",
    "TradingMode",
    "ExecutionMode",
    "LiveGateDecision",
    "decide_execution_mode",
    "pipeline_to_trading_mode",
    "trading_to_pipeline_mode",
]
