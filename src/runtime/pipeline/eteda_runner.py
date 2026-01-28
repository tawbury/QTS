from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ..config.config_models import UnifiedConfig
from ..engines.portfolio_engine import PortfolioEngine
from ..engines.strategy_engine import StrategyEngine
from ops.observer.observer import Observer


class ETEDARunner:
    """
    ETEDA Pipeline Runner
    
    Executes the Extract-Transform-Evaluate-Decide-Act pipeline.
    """

    def __init__(
        self, 
        observer: Observer,
        config: UnifiedConfig,
        portfolio_engine: PortfolioEngine,
        strategy_engine: StrategyEngine
    ) -> None:
        self._log = logging.getLogger("ETEDARunner")
        self._observer = observer
        self._config = config
        self._portfolio_engine = portfolio_engine
        self._strategy_engine = strategy_engine

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
