from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ..config.config_models import UnifiedConfig
from ..engines.portfolio_engine import PortfolioEngine
from ..engines.performance_engine import PerformanceEngine
from ..engines.strategy_engine import StrategyEngine
from ..data.google_sheets_client import GoogleSheetsClient
from ..data.repositories.position_repository import PositionRepository
from ..data.repositories.enhanced_portfolio_repository import EnhancedPortfolioRepository
from ..data.repositories.t_ledger_repository import T_LedgerRepository
from ..data.repositories.history_repository import HistoryRepository
from ..data.repositories.enhanced_performance_repository import EnhancedPerformanceRepository


class ETEDARunner:
    """
    ETEDA Pipeline Runner

    Executes the Extract-Transform-Evaluate-Decide-Act pipeline.
    """

    def __init__(
        self,
        config: UnifiedConfig
    ) -> None:
        self._log = logging.getLogger("ETEDARunner")
        self._config = config
        
        # GoogleSheetsClient 초기화
        self._sheets_client = GoogleSheetsClient()
        
        # 리포지토리 초기화
        self._position_repo = PositionRepository(self._sheets_client)
        self._portfolio_repo = EnhancedPortfolioRepository(self._sheets_client)
        self._t_ledger_repo = T_LedgerRepository(self._sheets_client)
        self._history_repo = HistoryRepository(self._sheets_client)
        self._performance_repo = EnhancedPerformanceRepository(self._sheets_client)
        
        # 엔진 초기화 (리포지토리 주입)
        self._portfolio_engine = PortfolioEngine(
            config=config,
            position_repo=self._position_repo,
            portfolio_repo=self._portfolio_repo,
            t_ledger_repo=self._t_ledger_repo
        )
        self._performance_engine = PerformanceEngine(
            config=config,
            history_repo=self._history_repo,
            performance_repo=self._performance_repo
        )
        self._strategy_engine = StrategyEngine(config=config)

    async def run_once(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the pipeline once based on the provided snapshot (Trigger).
        
        Args:
            snapshot: Observer snapshot containing market data
            
        Returns:
            Dict[str, Any]: Pipeline result
        """
        try:
            # 1. Extract
            market_data = self._extract(snapshot)
            if not market_data:
                return {"status": "skipped", "reason": "no_market_data"}
                
            # 2. Transform
            # Fetch position data for context
            symbol = market_data.get("symbol")
            positions = await self._portfolio_engine.get_positions()
            # Find position for this symbol (simple match for now)
            position_data = next((p for p in positions if p.symbol == symbol), None)
            
            transformed_data = self._transform(market_data, position_data)

            # 3. Evaluate
            signal = self._evaluate(transformed_data)

            # 4. Decide
            decision = self._decide(signal)

            # 5. Act
            act_result = await self._act(decision)

            # Log/Emit result
            result = {
                "timestamp": snapshot.get("meta", {}).get("timestamp"),
                "symbol": symbol,
                "signal": signal,
                "decision": decision,
                "act_result": act_result
            }
            
            self._log.info(f"Pipeline Result: {result}")
            return result
            
        except Exception as e:
            self._log.error(f"Pipeline execution failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _extract(self, snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract relevant data from snapshot"""
        # Snapshot structure matches observation.inputs
        obs = snapshot.get("observation", {})
        inputs = obs.get("inputs", {})
        
        if not inputs or "price" not in inputs:
            return None
            
        symbol = snapshot.get("context", {}).get("symbol")
        
        return {
            "symbol": symbol,
            "price": inputs["price"],
            "volume": inputs.get("volume"),
            "timestamp": snapshot.get("meta", {}).get("timestamp_ms")
        }

    def _transform(self, market_data: Dict[str, Any], position_data: Any) -> Dict[str, Any]:
        """Normalize data for strategy"""
        return {
            "market": market_data,
            "position": position_data
        }

    def _evaluate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate signal via StrategyEngine"""
        return self._strategy_engine.calculate_signal(
            data["market"], 
            data["position"]
        )

    def _decide(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Risk Logic (Validation)"""
        # Placeholder for Risk Gate
        # If signal is not HOLD, check limits
        
        decision = signal.copy()
        decision["approved"] = True
        decision["reason"] = "Risk checks passed (Placeholder)"
        
        return decision

    async def _act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the decision"""
        action = decision.get("action", "HOLD")
        
        if action == "HOLD" or not decision.get("approved"):
            return {"status": "skipped", "action": "HOLD"}

        # Check RUN_MODE
        # For now, we assume PAPER mode if not explicitly set to LIVE logic
        # You might want to read this from self._config in the future
        run_mode = "PAPER" 
        
        if run_mode == "PAPER":
            self._log.info(f"[PAPER ORDER] Action: {action}, Symbol: {decision.get('symbol')}")
            return {"status": "executed", "mode": "PAPER", "details": decision}
        
        return {"status": "skipped", "reason": "LIVE mode not implemented"}
