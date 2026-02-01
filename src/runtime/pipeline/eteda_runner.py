from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from ..config.config_models import UnifiedConfig
from .safety_hook import PipelineSafetyHook
from ..config.execution_mode import ExecutionMode, decide_execution_mode
from ..execution.interfaces.broker import BrokerEngine
from ..execution.models.intent import ExecutionIntent
from ..execution.models.response import ExecutionResponse
from ..engines.portfolio_engine import PortfolioEngine
from ..engines.performance_engine import PerformanceEngine
from ..engines.strategy_engine import StrategyEngine
from ..data.google_sheets_client import GoogleSheetsClient
from ..data.repositories.position_repository import PositionRepository
from ..data.repositories.enhanced_portfolio_repository import EnhancedPortfolioRepository
from ..data.repositories.t_ledger_repository import T_LedgerRepository
from ..data.repositories.history_repository import HistoryRepository
from ..data.repositories.enhanced_performance_repository import EnhancedPerformanceRepository


def _default_project_root() -> Path:
    try:
        from shared.paths import project_root
        return project_root()
    except ImportError:
        return Path.cwd()


class ETEDARunner:
    """
    ETEDA Pipeline Runner

    Executes the Extract-Transform-Evaluate-Decide-Act pipeline.

    Dependency injection contract:
    - config: UnifiedConfig (required). Config keys: RUN_MODE, LIVE_ENABLED, SPREADSHEET_ID, CREDENTIALS_PATH (optional; env fallback).
    - sheets_client: optional. If None, created from config/env.
    - project_root: optional. If None, resolved via paths.project_root() or cwd.
    - broker: optional BrokerEngine. If provided, Act 단계에서 ExecutionIntent → submit_intent → ExecutionResponse Contract 사용.
    - safety_hook: optional PipelineSafetyHook. If provided, run_once 시작 시 should_run() 확인, Act 단계 Broker Fail-Safe 시 record_fail_safe() 호출.
    """

    def __init__(
        self,
        config: UnifiedConfig,
        *,
        sheets_client: Optional[GoogleSheetsClient] = None,
        project_root: Optional[Path] = None,
        broker: Optional[BrokerEngine] = None,
        safety_hook: Optional[PipelineSafetyHook] = None,
    ) -> None:
        self._log = logging.getLogger("ETEDARunner")
        self._config = config
        self._project_root = project_root if project_root is not None else _default_project_root()

        # GoogleSheetsClient: inject or create from Config contract (SPREADSHEET_ID, CREDENTIALS_PATH; env fallback)
        if sheets_client is not None:
            self._sheets_client = sheets_client
        else:
            spreadsheet_id = config.get_flat("SPREADSHEET_ID") or os.getenv("GOOGLE_SHEET_KEY")
            credentials_path = config.get_flat("CREDENTIALS_PATH") or os.getenv("GOOGLE_CREDENTIALS_FILE")
            self._sheets_client = GoogleSheetsClient(
                credentials_path=credentials_path,
                spreadsheet_id=spreadsheet_id,
            )
        sid = self._sheets_client.spreadsheet_id

        # Repositories: spreadsheet_id from client; sheet names from repo classes (single responsibility)
        self._position_repo = PositionRepository(self._sheets_client, sid)
        self._portfolio_repo = EnhancedPortfolioRepository(self._sheets_client, sid, self._project_root)
        self._t_ledger_repo = T_LedgerRepository(self._sheets_client, sid)
        self._history_repo = HistoryRepository(self._sheets_client, sid)
        self._performance_repo = EnhancedPerformanceRepository(self._sheets_client, sid, self._project_root)
        
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
        self._broker = broker
        self._safety_hook = safety_hook

    async def run_once(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the pipeline once based on the provided snapshot (Trigger).
        
        Args:
            snapshot: Observer snapshot containing market data
            
        Returns:
            Dict[str, Any]: Pipeline result
        """
        try:
            # Safety Hook: Kill Switch / pipeline_state 확인 (Phase 7)
            if self._safety_hook is not None and not self._safety_hook.should_run():
                return {
                    "status": "skipped",
                    "reason": "safety",
                    "pipeline_state": self._safety_hook.pipeline_state(),
                }
            # 1. Extract
            market_data = self._extract(snapshot)
            if not market_data:
                return {"status": "skipped", "reason": "no_market_data"}
                
            # 2. Transform
            # Fetch position data for context
            symbol = market_data.get("symbol")
            try:
                positions = await self._portfolio_engine.get_positions()
                # Find position for this symbol (simple match for now)
                position_data = next((p for p in positions if p.symbol == symbol), None)
            except Exception as e:
                self._log.warning(f"Failed to fetch position data for {symbol}: {e}")
                position_data = None

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
            if self._safety_hook is not None:
                result["pipeline_state"] = self._safety_hook.pipeline_state()
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
        """
        Execute the decision. Act Input = decision (action, symbol, qty/final_qty, approved).
        Act Output = ExecutionResponse Contract as dict (status, intent_id, accepted, broker, message).
        broker 주입 시 ExecutionIntent → BrokerEngine.submit_intent() → ExecutionResponse 반환.
        """
        action = decision.get("action", "HOLD")

        if action == "HOLD" or not decision.get("approved"):
            return {"status": "skipped", "action": "HOLD"}

        # Guard/Fail-Safe 연계: Config로 Act 비활성화 시 run_once 없이 skip
        if self._config.get_flat("trading_enabled") in ("0", "false", "False"):
            return {"status": "skipped", "reason": "trading_enabled=False"}
        if self._config.get_flat("KILLSWITCH_STATUS") in ("ON", "ACTIVE", "1", "true"):
            return {"status": "skipped", "reason": "kill_switch"}
        if self._config.get_flat("PIPELINE_PAUSED") in ("1", "true", "True"):
            return {"status": "skipped", "reason": "pipeline_paused"}
        if self._config.get_flat("safe_mode") in ("1", "true", "True"):
            return {"status": "skipped", "reason": "safe_mode"}

        gate = decide_execution_mode(
            sheet_execution_mode=self._config.get_flat("RUN_MODE"),
            sheet_live_enabled=self._config.get_flat("LIVE_ENABLED"),
            env_live_ack=os.environ.get("QTS_LIVE_ACK"),
        )

        if gate.mode != ExecutionMode.PAPER and not (gate.mode == ExecutionMode.LIVE and gate.live_allowed):
            return {"status": "skipped", "reason": gate.reason}

        # Broker 주입 시 ExecutionIntent → submit_intent → ExecutionResponse Contract 사용
        if self._broker is not None:
            try:
                intent = ExecutionIntent(
                    intent_id=str(uuid.uuid4()),
                    symbol=str(decision.get("symbol", "")),
                    side=str(action).upper(),
                    quantity=float(decision.get("qty") or decision.get("final_qty") or 0),
                    intent_type="MARKET",
                    metadata={"decision": decision, "mode": gate.mode.value},
                )
                resp = self._broker.submit_intent(intent)
                # Phase 7: Broker Fail-Safe(ConsecutiveFailureGuard) 시 Safety Layer 기록
                if not resp.accepted and resp.broker == "failsafe" and self._safety_hook is not None:
                    self._safety_hook.record_fail_safe("FS040", resp.message or "blocked: consecutive failures exceeded", "Act")
                ts = getattr(resp.timestamp, "isoformat", lambda: str(resp.timestamp))()
                out = {
                    "status": "executed" if resp.accepted else "rejected",
                    "intent_id": resp.intent_id,
                    "accepted": resp.accepted,
                    "broker": resp.broker,
                    "message": resp.message,
                    "timestamp": ts,
                    "mode": gate.mode.value,
                }
                self._log.info(f"[{gate.mode.value}] Act result: {out}")
                return out
            except Exception as e:
                self._log.exception("Act submit_intent failed: %s", e)
                return {"status": "error", "error": str(e), "mode": gate.mode.value}

        # broker 미주입: 기존 동작(로그만, Contract 없음)
        self._log.info(f"[{gate.mode.value}] Action: {action}, Symbol: {decision.get('symbol')}")
        return {"status": "executed", "mode": gate.mode.value, "details": decision}
