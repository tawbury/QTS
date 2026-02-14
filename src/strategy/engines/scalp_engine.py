"""
ScalpStrategyEngine — Config_Scalp 기반 스캘프 전략 엔진.

StrategyLike Protocol 준수 (strategy_id, name, is_enabled).
StrategyMultiplexer.collect(snapshot) 호환: generate_intents(snapshot) 시그니처.
"""
from __future__ import annotations

import logging
from typing import Any, Optional, Sequence

from ..interfaces.strategy import Intent, MarketContext, ExecutionContext
from ..contracts import ScalpConfig

_log = logging.getLogger(__name__)


class ScalpStrategyEngine:
    """Config_Scalp sheet 기반 스캘프 전략 엔진."""

    def __init__(self, config_repo: Any = None) -> None:
        self._config_repo = config_repo
        self._config = ScalpConfig()
        self._enabled = True

    @property
    def strategy_id(self) -> str:
        return "scalp_main"

    @property
    def name(self) -> str:
        return "scalp_golden_cross"

    def is_enabled(self) -> bool:
        return self._enabled

    async def load_config(self) -> None:
        """Config_Scalp repository에서 파라미터 로드."""
        if self._config_repo is None:
            return
        try:
            gc = await self._config_repo.get_golden_cross_parameters()
            self._config.short_ma_period = int(gc.get("SHORT_MA_PERIOD", self._config.short_ma_period))
            self._config.long_ma_period = int(gc.get("LONG_MA_PERIOD", self._config.long_ma_period))
            self._config.signal_threshold = float(gc.get("SIGNAL_THRESHOLD", self._config.signal_threshold))

            rsi = await self._config_repo.get_rsi_parameters()
            self._config.rsi_period = int(rsi.get("RSI_PERIOD", self._config.rsi_period))
            self._config.rsi_oversold = float(rsi.get("RSI_OVERSOLD", self._config.rsi_oversold))
            self._config.rsi_overbought = float(rsi.get("RSI_OVERBOUGHT", self._config.rsi_overbought))

            bb = await self._config_repo.get_bollinger_bands_parameters()
            self._config.bb_period = int(bb.get("BB_PERIOD", self._config.bb_period))
            self._config.bb_std_dev = float(bb.get("BB_STD_DEV", self._config.bb_std_dev))

            exe = await self._config_repo.get_execution_settings()
            self._config.max_position_pct = float(exe.get("MAX_POSITION_PCT", self._config.max_position_pct))
            self._config.split_strategy = str(exe.get("SPLIT_STRATEGY", self._config.split_strategy))
            self._config.max_slippage_pct = float(exe.get("MAX_SLIPPAGE_PCT", self._config.max_slippage_pct))

            tf = await self._config_repo.get_timeframe_settings()
            self._config.primary_timeframe = str(tf.get("PRIMARY_TIMEFRAME", self._config.primary_timeframe))
            self._config.analysis_timeframe = str(tf.get("ANALYSIS_TIMEFRAME", self._config.analysis_timeframe))

            _log.info("ScalpStrategyEngine config loaded from Config_Scalp sheet")
        except Exception as e:
            _log.warning("Config_Scalp load failed, using defaults: %s", e)

    def generate_intents(self, snapshot: Any) -> Sequence[Intent]:
        """StrategyMultiplexer 호환: snapshot = (MarketContext, ExecutionContext)."""
        try:
            market, execution = snapshot
        except (TypeError, ValueError):
            return []

        intents = []

        gc_intent = self._evaluate_golden_cross(market, execution)
        if gc_intent is not None:
            intents.append(gc_intent)

        rsi_intent = self._evaluate_rsi(market, execution)
        if rsi_intent is not None:
            intents.append(rsi_intent)

        bb_intent = self._evaluate_bollinger(market, execution)
        if bb_intent is not None:
            intents.append(bb_intent)

        # 가장 강한 신호 1개 반환
        if intents:
            return [intents[0]]
        return []

    def _evaluate_golden_cross(
        self, market: MarketContext, execution: ExecutionContext
    ) -> Optional[Intent]:
        """Golden Cross 기법 평가. 실제 MA 계산은 시장 데이터 확장 후 구현."""
        if execution.position_qty <= 0 and market.price > 0:
            qty = self._calculate_qty(market.price, execution.cash)
            if qty > 0:
                return Intent(
                    symbol=market.symbol,
                    side="BUY",
                    qty=qty,
                    reason="[scalp] golden_cross_buy",
                )
        return None

    def _evaluate_rsi(
        self, market: MarketContext, execution: ExecutionContext
    ) -> Optional[Intent]:
        """RSI 기법 평가. 실제 RSI 계산은 시장 데이터 확장 후 구현."""
        return None

    def _evaluate_bollinger(
        self, market: MarketContext, execution: ExecutionContext
    ) -> Optional[Intent]:
        """Bollinger Bands 기법 평가. 실제 BB 계산은 시장 데이터 확장 후 구현."""
        return None

    def _calculate_qty(self, price: float, available_capital: float) -> int:
        """ScalpConfig.max_position_pct 기반 수량 계산."""
        if price <= 0:
            return 0
        max_amount = available_capital * self._config.max_position_pct
        return max(0, int(max_amount / price))
