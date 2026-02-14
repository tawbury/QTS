"""
Strategy contracts for scalp/swing strategy split.

Defines config dataclasses and utility functions for strategy tag identification.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .multiplexer.strategy_multiplexer import StrategyIntent


@dataclass
class ScalpConfig:
    """Scalp strategy parameters (Config_Scalp sheet)."""

    # GOLDEN_CROSS
    short_ma_period: int = 5
    long_ma_period: int = 20
    signal_threshold: float = 0.01

    # RSI
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0

    # BOLLINGER_BANDS
    bb_period: int = 20
    bb_std_dev: float = 2.0

    # EXECUTION
    max_position_pct: float = 0.01
    split_strategy: str = "TWAP"
    max_slippage_pct: float = 0.003

    # TIMEFRAME
    primary_timeframe: str = "1m"
    analysis_timeframe: str = "5m"


@dataclass
class SwingConfig:
    """Swing strategy parameters (Config_Swing sheet)."""

    # MARKET_FILTERS
    min_market_cap: float = 1e12
    min_avg_volume: int = 100000
    sector_filter: str = ""

    # STRATEGY_PARAMETERS
    trend_period: int = 60
    entry_threshold: float = 0.05
    exit_threshold: float = 0.03
    holding_period_min: int = 3
    holding_period_max: int = 30

    # RISK_MANAGEMENT
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.10
    max_position_pct: float = 0.05
    max_concurrent: int = 5


def get_strategy_tag(strategy_intent: StrategyIntent) -> str:
    """strategy_name prefix-based strategy type identification."""
    name = strategy_intent.strategy_name.lower()
    if name.startswith("scalp"):
        return "scalp"
    elif name.startswith("swing"):
        return "swing"
    return "scalp"  # default fallback
