"""
Strategy Engine

Engine I/O Contract: execute(data) — data.operation; output {success, data|error, execution_time}.
"""

from __future__ import annotations

import logging
from datetime import datetime
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
        # Always load BasicStrategy for local/dev
        from .basic_strategy import BasicStrategy
        self._strategy = BasicStrategy(config)

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

    def calculate_signal(self, market_data: Dict[str, Any], position_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate trading signal using loaded strategy (BasicStrategy by default)
        """
        return self._strategy.calculate_signal(market_data, position_data)
