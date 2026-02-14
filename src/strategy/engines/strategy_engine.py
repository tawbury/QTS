"""
Strategy Engine

Engine I/O Contract: execute(data) — data.operation; output {success, data|error, execution_time}.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional

from .base_engine import BaseEngine
from ...qts.core.config.config_models import UnifiedConfig
from ...shared.timezone_utils import now_kst


class StrategyEngine(BaseEngine):
    """
    Strategy Engine
    
    Executes trading strategies to generate signals based on market data and portfolio state.
    """
    
    def __init__(self, config: UnifiedConfig):
        """
        Initialize StrategyEngine
        
        Args:
            config: Unified Configuration object
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("StrategyEngine created")

    async def initialize(self) -> bool:
        """Initialize resources"""
        self.logger.info("Initializing StrategyEngine...")
        self._update_state(is_running=False)
        return True

    async def start(self) -> bool:
        """Start the engine"""
        self.logger.info("Starting StrategyEngine...")
        self._update_state(is_running=True)
        return True

    async def stop(self) -> bool:
        """Stop the engine"""
        self.logger.info("Stopping StrategyEngine...")
        self._update_state(is_running=False)
        return True
        
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute engine operation (Engine I/O Contract aligned with ETEDA).
        operation 'calculate_signal' => data: market_data, position_data.
        """
        start_time = now_kst()
        try:
            operation = data.get("operation")
            if operation == "calculate_signal":
                market_data = data.get("market_data") or data.get("market") or {}
                position_data = data.get("position_data") or data.get("position")
                pos = position_data if isinstance(position_data, dict) else {}
                result = self.calculate_signal(market_data, pos)
                execution_time = (now_kst() - start_time).total_seconds()
                self._update_metrics(execution_time, success=True)
                return {"success": True, "data": result, "execution_time": execution_time}
            execution_time = (now_kst() - start_time).total_seconds()
            self._update_metrics(execution_time, success=False)
            return {"success": False, "error": f"Unknown operation: {operation}", "execution_time": execution_time}
        except Exception as e:
            execution_time = (now_kst() - start_time).total_seconds()
            self._update_metrics(execution_time, success=False)
            self._update_state(self.state.is_running, error=str(e))
            return {"success": False, "error": str(e), "execution_time": execution_time}

    def _get_target_symbols(self) -> set:
        """VTS 검증 대상 종목 목록 반환"""
        raw = self.config.get_flat("VTS_TARGET_SYMBOLS", "005930")
        return set(s.strip() for s in raw.split(",") if s.strip())

    def _calculate_buy_qty(self, price: float) -> int:
        """기준 자산 대비 1% 한도로 매수 수량 계산"""
        if price <= 0:
            return 0
        base_equity = float(self.config.get_flat("BASE_EQUITY", "10000000"))
        max_per_stock = base_equity * 0.01
        return max(1, int(max_per_stock / price))

    def _hold_signal(self, symbol: str, price: float, market_data: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """HOLD 신호 생성 헬퍼"""
        return {
            'symbol': symbol,
            'action': 'HOLD',
            'qty': 0,
            'weight': 0.0,
            'price': price,
            'timestamp': market_data.get('timestamp'),
            'reason': reason,
        }

    def calculate_signal(self, market_data: Dict[str, Any], position_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate trading signal

        Args:
            market_data: Canonical market data (Price, Volume, etc.)
            position_data: Current position info for the symbol (None if no position)

        Returns:
            Dict[str, Any]: Signal dictionary (e.g., {'action': 'BUY', 'qty': 10, 'reason': 'RSI < 30'})
        """
        symbol = market_data.get('symbol')
        price_val = market_data.get('price', 0.0)
        close_price = float(price_val.get('close', 0.0)) if isinstance(price_val, dict) else float(price_val or 0.0)

        pos = position_data if isinstance(position_data, dict) else {}
        current_qty = pos.get('quantity', 0) if pos else 0

        # VTS 검증용: 목표 종목 필터
        target_symbols = self._get_target_symbols()
        if symbol not in target_symbols:
            return self._hold_signal(symbol, close_price, market_data, 'Not in target list')

        # 포지션 없으면 BUY (VTS 검증 목적)
        if current_qty == 0:
            buy_qty = self._calculate_buy_qty(close_price)
            if buy_qty > 0:
                self.logger.info(f"[VTS] BUY signal: {symbol} qty={buy_qty} @ {close_price}")
                return {
                    'symbol': symbol,
                    'action': 'BUY',
                    'qty': buy_qty,
                    'weight': 1.0,
                    'price': close_price,
                    'timestamp': market_data.get('timestamp'),
                    'reason': f'VTS test: No position, buy {buy_qty} @ {close_price}',
                }

        return self._hold_signal(symbol, close_price, market_data, 'Position exists or no signal')
