"""
SwingStrategyEngine — Config_Swing 기반 스윙 전략 엔진.

StrategyLike Protocol 준수 (strategy_id, name, is_enabled).
StrategyMultiplexer.collect(snapshot) 호환: generate_intents(snapshot) 시그니처.
"""
from __future__ import annotations

import logging
from typing import Any, Optional, Sequence

from ..interfaces.strategy import Intent, MarketContext, ExecutionContext
from ..contracts import SwingConfig

_log = logging.getLogger(__name__)


class SwingStrategyEngine:
    """Config_Swing sheet 기반 스윙 전략 엔진."""

    def __init__(self, config_repo: Any = None) -> None:
        self._config_repo = config_repo
        self._config = SwingConfig()
        self._enabled = True

    @property
    def strategy_id(self) -> str:
        return "swing_main"

    @property
    def name(self) -> str:
        return "swing_trend"

    def is_enabled(self) -> bool:
        return self._enabled

    async def load_config(self) -> None:
        """Config_Swing repository에서 파라미터 로드."""
        if self._config_repo is None:
            return
        try:
            mf = await self._config_repo.get_market_filters()
            self._config.min_market_cap = float(mf.get("MIN_MARKET_CAP", self._config.min_market_cap))
            self._config.min_avg_volume = int(mf.get("MIN_AVG_VOLUME", self._config.min_avg_volume))
            self._config.sector_filter = str(mf.get("SECTOR_FILTER", self._config.sector_filter))

            sp = await self._config_repo.get_strategy_parameters()
            self._config.trend_period = int(sp.get("TREND_PERIOD", self._config.trend_period))
            self._config.entry_threshold = float(sp.get("ENTRY_THRESHOLD", self._config.entry_threshold))
            self._config.exit_threshold = float(sp.get("EXIT_THRESHOLD", self._config.exit_threshold))
            self._config.holding_period_min = int(sp.get("HOLDING_PERIOD_MIN", self._config.holding_period_min))
            self._config.holding_period_max = int(sp.get("HOLDING_PERIOD_MAX", self._config.holding_period_max))

            rm = await self._config_repo.get_risk_management()
            self._config.stop_loss_pct = float(rm.get("STOP_LOSS_PCT", self._config.stop_loss_pct))
            self._config.take_profit_pct = float(rm.get("TAKE_PROFIT_PCT", self._config.take_profit_pct))
            self._config.max_position_pct = float(rm.get("MAX_POSITION_PCT", self._config.max_position_pct))
            self._config.max_concurrent = int(rm.get("MAX_CONCURRENT", self._config.max_concurrent))

            _log.info("SwingStrategyEngine config loaded from Config_Swing sheet")
        except Exception as e:
            _log.warning("Config_Swing load failed, using defaults: %s", e)

    def generate_intents(self, snapshot: Any) -> Sequence[Intent]:
        """StrategyMultiplexer 호환: snapshot = (MarketContext, ExecutionContext)."""
        try:
            market, execution = snapshot
        except (TypeError, ValueError):
            return []

        if not self._passes_market_filter(market):
            return []

        # 포지션 보유 시 청산 조건 우선 평가
        if execution.position_qty > 0:
            exit_intent = self._check_exit_conditions(market, execution)
            if exit_intent is not None:
                return [exit_intent]
            return []

        # 추세 기반 진입 평가
        entry_intent = self._evaluate_trend(market, execution)
        if entry_intent is not None:
            return [entry_intent]

        return []

    def _passes_market_filter(self, market: MarketContext) -> bool:
        """시장 필터 통과 여부. 실제 시가총액/거래량 데이터 확장 후 정밀화."""
        return market.price > 0

    def _evaluate_trend(
        self, market: MarketContext, execution: ExecutionContext
    ) -> Optional[Intent]:
        """추세 분석 기반 진입 판단. 실제 추세 데이터 확장 후 구현."""
        if execution.position_qty <= 0 and market.price > 0:
            qty = self._calculate_qty(market.price, execution.cash)
            if qty > 0:
                return Intent(
                    symbol=market.symbol,
                    side="BUY",
                    qty=qty,
                    reason="[swing] trend_entry",
                )
        return None

    def _check_exit_conditions(
        self, market: MarketContext, execution: ExecutionContext
    ) -> Optional[Intent]:
        """손절/익절 조건 확인. 실제 PnL 데이터 확장 후 구현."""
        return None

    def _calculate_qty(self, price: float, available_capital: float) -> int:
        """SwingConfig.max_position_pct 기반 수량 계산."""
        if price <= 0:
            return 0
        max_amount = available_capital * self._config.max_position_pct
        return max(0, int(max_amount / price))
