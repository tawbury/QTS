from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

from ..qts.core.config.config_models import UnifiedConfig
from .safety_hook import PipelineSafetyHook
from ..qts.core.config.execution_mode import ExecutionMode, decide_execution_mode
from ..provider.interfaces.broker import BrokerEngine
from ..provider.models.intent import ExecutionIntent
from ..provider.models.response import ExecutionResponse
from ..strategy.engines.portfolio_engine import PortfolioEngine
from ..strategy.engines.performance_engine import PerformanceEngine
from ..strategy.engines.strategy_engine import StrategyEngine
from ..db.repositories.position_repository import PositionRepository
from ..db.repositories.enhanced_portfolio_repository import EnhancedPortfolioRepository
from ..db.repositories.t_ledger_repository import T_LedgerRepository
from ..db.repositories.history_repository import HistoryRepository
from ..db.repositories.enhanced_performance_repository import EnhancedPerformanceRepository
from ..db.trade_recorder import TradeRecorder
from ..feedback.aggregator import FeedbackAggregator
from ..feedback.contracts import FeedbackSummary
from ..capital.contracts import CapitalPoolContract, PoolId
from ..capital.engine import CapitalEngine, CapitalEngineInput, CapitalEngineOutput
from ..capital.pool_repository import CapitalPoolRepository
from ..safety.state import SafetyState

# Optional: Execution Pipeline integration
try:
    from ..execution.pipeline import ExecutionPipeline
    from ..execution.contracts import (
        OrderDecision as ExecOrderDecision,
        ExecutionContext as ExecPipelineCtx,
        ExecutionResult,
        FillEvent as ExecFillEvent,
        SplitOrderStatus,
    )
    from ..execution.stages.async_send import AsyncSendStage
    from ..execution.broker_adapter import BrokerEngineAdapter
    from ..provider.models.order_request import OrderSide, OrderType
    _HAS_EXECUTION_PIPELINE = True
except ImportError:
    _HAS_EXECUTION_PIPELINE = False

# Optional: Risk Gate integration
try:
    from ..risk.gates.calculated_risk_gate import CalculatedRiskGate
    from ..strategy.interfaces.strategy import (
        Intent as StrategyIntent,
        MarketContext as StrategyMarketCtx,
        ExecutionContext as StrategyExecCtx,
    )
    _HAS_RISK_GATE = True
except ImportError:
    _HAS_RISK_GATE = False


def _default_project_root() -> Path:
    try:
        from src.shared.paths import project_root
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
    - feedback_aggregator: optional FeedbackAggregator. If provided, Act 결과를 피드백 데이터로 수집하고 다음 사이클 Strategy 보정에 활용.
    - capital_engine: optional CapitalEngine. If provided, Transform 후 풀 배분 결정, Evaluate에서 자본 제약 적용.
    - capital_pool_repo: optional CapitalPoolRepository. If provided, 풀 상태 로드/저장.
    - risk_gate: optional CalculatedRiskGate. If provided, Decide에서 Risk Gate 적용 (qty 조정, risk_score 평가).
    - execution_pipeline: optional ExecutionPipeline. If provided, Act에서 6단계 실행 파이프라인 위임.
    """

    def __init__(
        self,
        config: UnifiedConfig,
        *,
        sheets_client: Optional[Any] = None,
        project_root: Optional[Path] = None,
        broker: Optional[BrokerEngine] = None,
        safety_hook: Optional[PipelineSafetyHook] = None,
        feedback_aggregator: Optional[FeedbackAggregator] = None,
        capital_engine: Optional[CapitalEngine] = None,
        capital_pool_repo: Optional[CapitalPoolRepository] = None,
        risk_gate: Optional[Any] = None,
        execution_pipeline: Optional[Any] = None,
        micro_risk_loop: Optional[Any] = None,
        event_dispatcher: Optional[Any] = None,
    ) -> None:
        self._log = logging.getLogger("ETEDARunner")
        self._config = config
        self._project_root = project_root if project_root is not None else _default_project_root()

        # GoogleSheetsClient: inject or create from Config contract (SPREADSHEET_ID, CREDENTIALS_PATH; env fallback)
        if sheets_client is not None:
            self._sheets_client = sheets_client
        else:
            try:
                from ..db.google_sheets_client import GoogleSheetsClient
            except ImportError:
                raise ImportError(
                    "GoogleSheetsClient required for production. Use --local-only with MockSheetsClient."
                )
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
        self._trade_recorder = TradeRecorder()
        
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
        self._feedback_agg = feedback_aggregator
        self._capital_engine = capital_engine
        self._pool_repo = capital_pool_repo
        self._risk_gate = risk_gate
        self._execution_pipeline = execution_pipeline
        self._micro_risk = micro_risk_loop
        self._event_dispatcher = event_dispatcher

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
            # 0.5 Event: ETEDA_CYCLE_START (P2, §6.1)
            self._emit_event("ETEDA_CYCLE_START", "ETEDA_SCHEDULER")

            # 1. Extract
            market_data = self._extract(snapshot)
            if not market_data:
                return {"status": "skipped", "reason": "no_market_data"}

            # 1.5 Capital Pool 로드 + Engine 평가 (Fire-and-Forget)
            pool_states, capital_decision = self._load_and_evaluate_capital()

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

            # 2.5 Feedback Summary 조회 (Fire-and-Forget)
            feedback_summary = self._get_feedback_summary(symbol)

            transformed_data = self._transform(market_data, position_data)

            # 3. Evaluate (+ Feedback 보정 + Capital 제약)
            signal = self._evaluate(
                transformed_data,
                feedback_summary=feedback_summary,
                capital_decision=capital_decision,
            )

            # 4. Decide
            decision = self._decide(signal)

            # 5. Act
            act_result = await self._act(decision)

            # 6. Feedback Collection (Fire-and-Forget)
            self._collect_feedback(decision, act_result)

            # 6.5 Capital Pool 갱신 (Fire-and-Forget)
            self._update_capital_after_act(pool_states, decision, act_result)

            # 6.6 Micro Risk Loop 포지션 동기화 (Fire-and-Forget, §6.2)
            self._sync_to_micro_risk(decision, act_result)

            # 6.7 Event: Act 결과 발행 (P0, §6.1)
            self._emit_act_events(act_result)

            # 6.8 Event: METRIC_RECORD (P3)
            self._emit_event("METRIC_RECORD", "ETEDA", payload={
                "symbol": symbol,
                "action": decision.get("action"),
                "status": act_result.get("status"),
            })

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
        """Extract relevant data from snapshot.

        Operating State를 함께 추출하여 이후 단계에 전파한다.
        근거: docs/arch/sub/18_System_State_Promotion_Architecture.md §6.2
        """
        # Snapshot structure matches observation.inputs
        obs = snapshot.get("observation", {})
        inputs = obs.get("inputs", {})

        if not inputs or "price" not in inputs:
            return None

        symbol = snapshot.get("context", {}).get("symbol")

        # Operating State 추출 (§6.2: Extract에서 상태 전파)
        operating_state, _ = self._get_operating_state_properties()

        return {
            "symbol": symbol,
            "price": inputs["price"],
            "volume": inputs.get("volume"),
            "timestamp": snapshot.get("meta", {}).get("timestamp_ms"),
            "operating_state": operating_state.value,
        }

    def _transform(self, market_data: Dict[str, Any], position_data: Any) -> Dict[str, Any]:
        """Normalize data for strategy"""
        return {
            "market": market_data,
            "position": position_data
        }

    def _get_operating_state_properties(self) -> tuple:
        """현재 OperatingState 및 속성을 로드한다.

        근거: docs/arch/sub/18_System_State_Promotion_Architecture.md §6.2
        """
        from ..state.contracts import OperatingState, STATE_PROPERTIES
        state_str = self._config.get_flat("OPERATING_STATE", "BALANCED")
        try:
            state = OperatingState(state_str)
        except ValueError:
            state = OperatingState.BALANCED
        return state, STATE_PROPERTIES[state]

    def _evaluate(
        self,
        data: Dict[str, Any],
        *,
        feedback_summary: Optional[FeedbackSummary] = None,
        capital_decision: Optional[CapitalEngineOutput] = None,
    ) -> Dict[str, Any]:
        """Generate signal via StrategyEngine + Operating State 필터링 + Feedback 보정 + Capital 제약.

        근거: docs/arch/sub/18_System_State_Promotion_Architecture.md §6.2
        - DEFENSIVE 상태 시 Scalp 비활성화
        - entry_signal_threshold 미달 신호 필터링
        """
        market = data.get("market", {})
        price = market.get("price")
        symbol = market.get("symbol")

        self._log.info(
            f"[_evaluate] Evaluating {symbol} @ {price} | Vol: {market.get('volume')} | Time: {market.get('timestamp')}"
        )

        # Operating State 로드 및 엔진 활성화 결정
        operating_state, state_props = self._get_operating_state_properties()

        # DEFENSIVE 상태에서 Scalp Engine 비활성화 (§6.2)
        if not state_props.scalp_engine_active:
            self._log.info(f"[State] Scalp engine inactive in {operating_state.value} state")
            return {
                "symbol": symbol,
                "price": price,
                "action": "HOLD",
                "signal": "NONE",
                "reason": f"SCALP_DISABLED_IN_{operating_state.value}",
                "operating_state": operating_state.value,
            }

        signal = self._strategy_engine.calculate_signal(
            data["market"],
            data["position"],
        )

        # 신호 임계값 필터링: confidence < entry_signal_threshold → HOLD
        signal_confidence = signal.get("weight", signal.get("confidence", 1.0))
        if signal.get("action") != "HOLD" and signal_confidence < state_props.entry_signal_threshold:
            self._log.info(
                f"[State] Signal confidence {signal_confidence:.2f} < threshold {state_props.entry_signal_threshold} "
                f"in {operating_state.value} → HOLD"
            )
            signal = signal.copy()
            signal["action"] = "HOLD"
            signal["reason"] = f"BELOW_STATE_THRESHOLD({operating_state.value})"
            signal["operating_state"] = operating_state.value
            signal["filtered_confidence"] = signal_confidence
            return signal

        signal = signal.copy() if not isinstance(signal, dict) else signal
        signal["operating_state"] = operating_state.value

        if (
            feedback_summary is not None
            and feedback_summary.sample_count >= 5
            and signal.get("action") != "HOLD"
        ):
            try:
                signal = self._apply_feedback_adjustments(signal, feedback_summary)
            except Exception:
                self._log.warning("Feedback adjustment failed, using original signal")

        # Capital 제약 (Fire-and-Forget)
        if capital_decision is not None and signal.get("action") != "HOLD":
            try:
                signal = self._apply_capital_constraint(signal, capital_decision)
            except Exception:
                self._log.warning("Capital constraint failed, using original signal")

        return signal

    def _decide(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Risk Logic + Operating State 기반 결정 오버라이드.

        근거: docs/arch/sub/18_System_State_Promotion_Architecture.md §6.3
        - DEFENSIVE 상태에서 신규 진입(BUY) 차단
        - 리밸런싱 주문이 신규 진입보다 우선
        - Micro Risk frozen 종목 신규 진입 차단 (§5.4)

        risk_gate 주입 시 CalculatedRiskGate를 통해 qty 조정 및 risk_score 평가.
        미주입 시 기존 Placeholder 동작 유지.
        """
        decision = signal.copy()

        # Operating State 기반 결정 오버라이드 (§6.3)
        _, state_props = self._get_operating_state_properties()

        # DEFENSIVE 상태에서 신규 진입 차단
        if not state_props.new_entry_enabled and decision.get("action") in ("BUY",):
            self._log.info(
                f"[Decide] New entry blocked in {decision.get('operating_state', 'DEFENSIVE')} state"
            )
            decision["action"] = "HOLD"
            decision["approved"] = False
            decision["reason"] = "NEW_ENTRY_BLOCKED_IN_DEFENSIVE_STATE"
            return decision

        # Micro Risk frozen 종목 신규 진입 차단 (P1-5, §5.4)
        symbol = decision.get("symbol")
        if (
            self._micro_risk is not None
            and symbol
            and decision.get("action") in ("BUY",)
            and hasattr(self._micro_risk, "is_entry_blocked")
            and self._micro_risk.is_entry_blocked(symbol)
        ):
            self._log.info(
                f"[Decide] Entry blocked for frozen symbol: {symbol}"
            )
            decision["action"] = "HOLD"
            decision["approved"] = False
            decision["reason"] = f"FROZEN_BY_MICRO_RISK({symbol})"
            return decision

        if self._risk_gate is not None and decision.get("action") != "HOLD":
            gate_result = self._apply_risk_gate(decision)
            if gate_result is not None:
                return gate_result

        decision["approved"] = True
        decision["reason"] = "Risk checks passed"
        return decision

    def _apply_risk_gate(self, decision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """CalculatedRiskGate 적용. 실패 시 None 반환 (fallback to 기존 로직)."""
        if not _HAS_RISK_GATE:
            return None
        try:
            intent = StrategyIntent(
                symbol=decision.get("symbol", ""),
                side=str(decision.get("action", "BUY")).upper(),
                qty=int(decision.get("qty") or decision.get("final_qty") or 0),
                reason=decision.get("strategy", "scalp"),
            )
            market = StrategyMarketCtx(
                symbol=decision.get("symbol", ""),
                price=float(decision.get("price", 0)),
            )
            exec_ctx = StrategyExecCtx(
                position_qty=int(decision.get("position_qty", 0)),
                cash=float(decision.get("available_cash", 100_000_000)),
            )

            gate_decision = self._risk_gate.apply(intent, market, exec_ctx)

            result = decision.copy()
            result["risk_evaluated"] = True
            result["risk_score"] = gate_decision.risk.risk_score

            if not gate_decision.allowed:
                result["approved"] = False
                result["reason"] = f"Risk gate blocked: {gate_decision.risk.reason}"
                self._log.info(f"[Decide] Risk gate blocked: {gate_decision.risk.reason}")
                return result

            if gate_decision.adjusted_intent is not None:
                result["qty"] = gate_decision.adjusted_intent.qty
                result["risk_qty_adjusted"] = True

            result["approved"] = True
            result["reason"] = "Risk gate passed"
            return result
        except Exception:
            self._log.warning("Risk gate evaluation failed, falling back to default")
            return None

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
        ks_val = str(self._config.get_flat("KS_ENABLED", "false")).lower()
        if ks_val in ("on", "active"):
            return {"status": "skipped", "reason": "kill_switch"}
        if self._config.get_flat("PIPELINE_PAUSED") in ("1", "true", "True"):
            return {"status": "skipped", "reason": "pipeline_paused"}
        failsafe_val = str(self._config.get_flat("FAILSAFE_ENABLED", "false")).lower()
        if failsafe_val in ("active", "on"):
            return {"status": "skipped", "reason": "safe_mode"}

        gate = decide_execution_mode(
            sheet_execution_mode=self._config.get_flat("RUN_MODE"),
            sheet_live_enabled=self._config.get_flat("LIVE_ENABLED"),
            env_live_ack=os.environ.get("QTS_LIVE_ACK"),
        )

        if gate.mode != ExecutionMode.PAPER and not (gate.mode == ExecutionMode.LIVE and gate.live_allowed):
            return {"status": "skipped", "reason": gate.reason}

        # ExecutionPipeline 위임 (주입 시)
        if self._execution_pipeline is not None and self._broker is not None and _HAS_EXECUTION_PIPELINE:
            try:
                pipeline_result = await self._act_via_pipeline(decision, gate)
                if pipeline_result is not None:
                    return pipeline_result
            except Exception as e:
                self._log.warning(f"Execution pipeline failed, falling back to direct broker: {e}")

        # Broker 주입 시 ExecutionIntent → submit_intent → ExecutionResponse Contract 사용 (fallback)
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
                self._trade_recorder.record_trade(out)
                # Google Sheets T_Ledger 기록 (실패해도 매매 결과에 영향 없음)
                await self._record_to_sheets(out, decision)
                return out
            except Exception as e:
                self._log.exception("Act submit_intent failed: %s", e)
                return {"status": "error", "error": str(e), "mode": gate.mode.value}

        # broker 미주입: 기존 동작(로그만, Contract 없음)
        self._log.info(f"[{gate.mode.value}] Action: {action}, Symbol: {decision.get('symbol')}")
        out = {"status": "executed", "mode": gate.mode.value, "details": decision}
        # Google Sheets T_Ledger 기록 (broker 미주입 시에도 기록)
        await self._record_to_sheets(out, decision)
        return out

    def _get_feedback_summary(self, symbol: Optional[str]) -> Optional[FeedbackSummary]:
        """종목별 Feedback Summary 조회 (Fire-and-Forget)."""
        if self._feedback_agg is None or not symbol:
            return None
        try:
            summary = self._feedback_agg.get_summary(symbol, lookback_days=30)
            if summary.sample_count > 0:
                self._log.info(
                    f"[Feedback] {symbol}: sample={summary.sample_count}, "
                    f"slippage={summary.avg_slippage_bps:.1f}bps, "
                    f"quality={summary.avg_quality_score:.3f}"
                )
            return summary
        except Exception:
            self._log.warning(f"Feedback summary fetch failed for {symbol}")
            return None

    def _apply_feedback_adjustments(
        self,
        signal: Dict[str, Any],
        summary: FeedbackSummary,
    ) -> Dict[str, Any]:
        """FeedbackSummary 기반 신호 보정.

        적용 항목:
        1. 진입가 슬리피지 보정
        2. 시장 충격 기반 수량 조정
        3. 실행 품질 기반 신뢰도 보정
        """
        from ..feedback.strategy_enhancer import (
            adjust_confidence,
            adjust_qty_for_market_impact,
            calculate_adjusted_entry_price,
        )

        adjusted = signal.copy()
        price = signal.get("price", 0)
        qty = signal.get("qty", 0)
        side = signal.get("action", "BUY")

        # 1. 슬리피지 보정 진입가
        if price and price > 0:
            adj_price = calculate_adjusted_entry_price(
                Decimal(str(price)),
                summary.avg_slippage_bps,
                side,
            )
            adjusted["adjusted_entry_price"] = float(adj_price)

        # 2. 시장 충격 기반 수량 조정
        if qty and qty > 0:
            adj_qty = adjust_qty_for_market_impact(
                Decimal(str(qty)),
                summary.avg_market_impact_bps,
                max_acceptable_impact_bps=20.0,
            )
            adjusted["adjusted_qty"] = int(adj_qty)

        # 3. 신뢰도 보정
        raw_confidence = signal.get("weight", 1.0)
        adjusted["confidence"] = adjust_confidence(
            raw_confidence, summary.avg_quality_score,
        )

        # 4. 보정 메타데이터
        adjusted["feedback_applied"] = True
        adjusted["feedback_sample_count"] = summary.sample_count
        adjusted["feedback_avg_slippage_bps"] = summary.avg_slippage_bps
        adjusted["feedback_avg_quality_score"] = summary.avg_quality_score

        self._log.info(
            f"[Feedback] {signal.get('symbol')}: "
            f"price {price}->{adjusted.get('adjusted_entry_price', price)}, "
            f"qty {qty}->{adjusted.get('adjusted_qty', qty)}, "
            f"confidence {raw_confidence:.2f}->{adjusted['confidence']:.2f}"
        )

        return adjusted

    def _collect_feedback(
        self,
        decision: Dict[str, Any],
        act_result: Dict[str, Any],
    ) -> None:
        """Act 결과로부터 FeedbackData 생성 및 저장.

        Fire-and-Forget: 실패해도 파이프라인에 영향 없음.
        """
        if self._feedback_agg is None:
            return
        if not act_result.get("accepted") and act_result.get("status") != "executed":
            return
        try:
            symbol = decision.get("symbol", "")
            price = decision.get("price", 0)
            qty = decision.get("qty", 0) or decision.get("final_qty", 0)
            now = datetime.now(timezone.utc)

            self._feedback_agg.aggregate_and_store(
                symbol=symbol,
                order_id=act_result.get("intent_id", ""),
                execution_start=now,
                execution_end=now,
                decision_price=Decimal(str(price)),
                avg_fill_price=Decimal(str(price)),
                filled_qty=Decimal(str(qty)),
                original_qty=Decimal(str(qty)),
                partial_fill_ratio=0.0 if act_result.get("accepted") else 1.0,
                avg_fill_latency_ms=0.0,
                strategy_tag=decision.get("strategy", ""),
                order_type=decision.get("order_type", "MARKET"),
            )
            self._log.info(f"Feedback collected for {symbol}")
        except Exception:
            self._log.exception("Feedback collection failed (non-blocking)")

    # --- Capital Engine Integration ---

    def _load_and_evaluate_capital(
        self,
    ) -> tuple[Optional[dict[PoolId, CapitalPoolContract]], Optional[CapitalEngineOutput]]:
        """Capital Pool 로드 + Engine 평가. Fire-and-Forget."""
        if self._capital_engine is None or self._pool_repo is None:
            return None, None
        try:
            pool_states = self._pool_repo.load_pool_states()
            if pool_states is None:
                return None, None

            total_equity = sum(p.total_capital for p in pool_states.values())

            operating_state_str = self._config.get_flat("OPERATING_STATE", "BALANCED")
            from ..state.contracts import OperatingState
            operating_state = OperatingState(operating_state_str)

            safety_state = SafetyState.NORMAL
            if self._safety_hook is not None:
                ps = self._safety_hook.pipeline_state()
                if ps in ("LOCKDOWN", "lockdown"):
                    safety_state = SafetyState.LOCKDOWN
                elif ps in ("FAIL", "fail"):
                    safety_state = SafetyState.FAIL

            # 풀별 성과 메트릭 수집
            perf_metrics = self._collect_pool_performance_metrics()

            input_ = CapitalEngineInput(
                total_equity=total_equity,
                operating_state=operating_state,
                pool_states=pool_states,
                performance_metrics=perf_metrics,
                safety_state=safety_state,
            )
            decision = self._capital_engine.evaluate(input_)

            for alert in decision.alerts:
                if alert.severity == "CRITICAL":
                    self._log.error(f"[Capital] {alert.code}: {alert.message}")
                else:
                    self._log.warning(f"[Capital] {alert.code}: {alert.message}")

            self._log.info(
                f"[Capital] Evaluated: rebalancing={decision.rebalancing_required}, "
                f"promotions={len(decision.pending_promotions)}, "
                f"demotions={len(decision.pending_demotions)}, "
                f"blocked={decision.transfers_blocked}"
            )

            # evaluate() 결과에서 pending transfers가 있으면 자동 실행
            if not decision.transfers_blocked:
                all_transfers = decision.pending_promotions + decision.pending_demotions
                if all_transfers:
                    executed = self._capital_engine.execute_transfers(pool_states, all_transfers)
                    if executed:
                        # 프로모션 후 누적 수익 차감
                        for transfer in executed:
                            from src.capital.pool import reset_accumulated_profit
                            from_pool = pool_states.get(transfer.from_pool)
                            if from_pool and transfer.reason == "PROFIT_THRESHOLD_EXCEEDED":
                                reset_accumulated_profit(from_pool, transfer.amount)
                        # 풀 상태 저장
                        self._pool_repo.save_pool_states(pool_states)
                        self._log.info(f"[Capital] Executed {len(executed)} transfers")

            return pool_states, decision
        except Exception:
            self._log.warning("Capital evaluation failed (non-blocking)")
            return None, None

    def _collect_pool_performance_metrics(self) -> dict:
        """풀별 성과 메트릭 수집."""
        from src.capital.contracts import PerformanceMetrics, PoolId
        metrics: dict[PoolId, PerformanceMetrics] = {}
        try:
            # PerformanceEngine에서 메트릭 조회 시도
            # 조회 실패 시 기본값 사용
            for pool_id in PoolId:
                metrics[pool_id] = PerformanceMetrics()
        except Exception:
            pass
        return metrics

    def _apply_capital_constraint(
        self,
        signal: Dict[str, Any],
        capital_decision: CapitalEngineOutput,
    ) -> Dict[str, Any]:
        """풀 자본 제약 적용. Safety LOCKDOWN 시 HOLD 전환."""
        adjusted = signal.copy()

        if capital_decision.transfers_blocked:
            adjusted["action"] = "HOLD"
            adjusted["capital_blocked"] = True
            adjusted["capital_blocked_reason"] = "Safety state: transfers blocked"
            self._log.warning("[Capital] Transfers blocked → HOLD")
            return adjusted

        adjusted["capital_evaluated"] = True
        return adjusted

    def _update_capital_after_act(
        self,
        pool_states: Optional[dict[PoolId, CapitalPoolContract]],
        decision: Dict[str, Any],
        act_result: Dict[str, Any],
    ) -> None:
        """Act 결과로 풀 invested_capital 갱신. Fire-and-Forget."""
        if self._pool_repo is None or pool_states is None:
            return
        if act_result.get("status") != "executed":
            return
        try:
            action = decision.get("action", "HOLD")
            price = Decimal(str(decision.get("price", 0)))
            qty = Decimal(str(decision.get("qty") or decision.get("final_qty") or 0))
            fill_amount = price * qty

            if fill_amount <= 0:
                return

            # 현재 Scalp Pool 기준 (향후 전략 태그로 풀 분기)
            scalp_pool = pool_states.get(PoolId.SCALP)
            if scalp_pool is None:
                return

            if action == "BUY":
                scalp_pool.invested_capital += fill_amount
            elif action == "SELL":
                scalp_pool.invested_capital -= fill_amount
                if scalp_pool.invested_capital < Decimal("0"):
                    scalp_pool.invested_capital = Decimal("0")
            else:
                return

            self._pool_repo.save_pool_states(pool_states)
            self._log.info(f"[Capital] Pool updated: {action} {fill_amount}")
        except Exception:
            self._log.warning("Capital pool update failed (non-blocking)")

    async def _record_to_sheets(self, act_result: Dict[str, Any], decision: Dict[str, Any]) -> None:
        """
        Act 결과를 Google Sheets T_Ledger에 기록.

        시트 기록 실패 시에도 매매 결과에 영향을 주지 않도록 에러 격리.
        """
        try:
            trade_data = {
                "timestamp": act_result.get("timestamp"),
                "symbol": decision.get("symbol", ""),
                "side": decision.get("action", ""),
                "qty": decision.get("qty") or decision.get("final_qty", ""),
                "price": decision.get("price", ""),
                "intent_id": act_result.get("intent_id", ""),
                "broker": act_result.get("broker", ""),
                "strategy": decision.get("strategy", ""),
                "mode": act_result.get("mode", ""),
            }
            await self._t_ledger_repo.append_trade(trade_data)
            self._log.info(f"Recorded trade to T_Ledger sheet: {trade_data.get('intent_id', 'N/A')}")
        except Exception as e:
            self._log.warning(f"Failed to record trade to T_Ledger sheet (non-fatal): {e}")

    # --- Micro Risk Loop Integration (§6.2) ---

    def _sync_to_micro_risk(
        self,
        decision: Dict[str, Any],
        act_result: Dict[str, Any],
    ) -> None:
        """Act 결과를 Micro Risk Loop에 동기화. Fire-and-Forget."""
        if self._micro_risk is None:
            return
        if act_result.get("status") != "executed":
            return
        try:
            symbol = decision.get("symbol")
            if not symbol:
                return
            price = decision.get("price", 0)
            qty = decision.get("qty") or decision.get("final_qty") or 0
            self._micro_risk.sync_from_main({
                symbol: {
                    "qty": int(qty),
                    "avg_price": float(price),
                    "current_price": float(price),
                    "unrealized_pnl": 0.0,
                    "unrealized_pnl_pct": 0.0,
                }
            })
            self._log.info(f"[MicroRisk] Position synced: {symbol} qty={qty}")
        except Exception:
            self._log.warning("Micro Risk sync failed (non-blocking)")

    # --- Event Dispatcher Integration (§6.1) ---

    def _emit_event(
        self,
        event_type_str: str,
        source: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """이벤트 발행. Fire-and-Forget."""
        if self._event_dispatcher is None:
            return
        try:
            from src.event.contracts import EventType, create_event
            event_type = EventType(event_type_str)
            event = create_event(event_type, source=source, payload=payload)
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._event_dispatcher.dispatch(event))
            except RuntimeError:
                # 이벤트 루프 없을 때 무시
                pass
        except Exception:
            self._log.debug("Event emit failed: %s (non-blocking)", event_type_str)

    def _emit_act_events(self, act_result: Dict[str, Any]) -> None:
        """Act 결과를 P0 이벤트로 발행."""
        if self._event_dispatcher is None:
            return
        status = act_result.get("status")
        if status == "executed":
            self._emit_event("FILL_CONFIRMED", "BROKER", payload={
                "intent_id": act_result.get("intent_id"),
                "broker": act_result.get("broker"),
            })
        elif status == "rejected":
            self._emit_event("ORDER_REJECTED", "BROKER", payload={
                "intent_id": act_result.get("intent_id"),
                "message": act_result.get("message"),
            })

    # --- Execution Pipeline Integration ---

    async def _act_via_pipeline(self, decision: Dict[str, Any], gate: Any) -> Optional[Dict[str, Any]]:
        """6단계 ExecutionPipeline 실행. 실패 시 None (fallback to 직접 broker 호출)."""
        action_str = str(decision.get("action", "BUY")).upper()
        qty = int(decision.get("qty") or decision.get("final_qty") or 0)
        if qty <= 0:
            return None

        price_val = decision.get("price")
        price = Decimal(str(price_val)) if price_val else None

        # OrderDecision 생성
        order = ExecOrderDecision(
            symbol=str(decision.get("symbol", "")),
            side=OrderSide.BUY if action_str == "BUY" else OrderSide.SELL,
            qty=qty,
            price=price,
            order_type=OrderType.MARKET,
            strategy_id=decision.get("strategy", "scalp"),
        )
        ctx = ExecPipelineCtx(order=order)

        # Safety State
        safety_state = SafetyState.NORMAL
        if self._safety_hook is not None:
            ps = self._safety_hook.pipeline_state()
            if ps in ("LOCKDOWN", "lockdown"):
                safety_state = SafetyState.LOCKDOWN

        available_capital = Decimal(str(decision.get("available_cash", 100_000_000)))

        # Stage 1: PreCheck
        if not self._execution_pipeline.run_precheck(
            ctx, available_capital=available_capital, safety_state=safety_state
        ):
            result = self._execution_pipeline.build_result(ctx)
            return self._execution_result_to_dict(result, gate)

        # Stage 2: Split
        if not self._execution_pipeline.run_split(ctx):
            result = self._execution_pipeline.build_result(ctx)
            return self._execution_result_to_dict(result, gate)

        # Stage 3: AsyncSend
        adapter = BrokerEngineAdapter(self._broker)
        send_stage = AsyncSendStage(adapter)
        send_result, send_alerts = await send_stage.execute(ctx.splits)
        ctx.alerts.extend(send_alerts)

        if not self._execution_pipeline.process_send_results(
            ctx, send_result.sent_count, send_result.failed_count
        ):
            result = self._execution_pipeline.build_result(ctx)
            return self._execution_result_to_dict(result, gate)

        # Stage 4: Fill 처리 (동기 브로커 → 즉시 체결 가정)
        fill_events = self._create_fill_events_from_sends(ctx, send_result)
        self._execution_pipeline.process_fills(ctx, fill_events)

        # Build Result
        result = self._execution_pipeline.build_result(ctx)
        out = self._execution_result_to_dict(result, gate)

        self._log.info(f"[Pipeline] {result.state.value}: filled={result.filled_qty}/{result.requested_qty}")
        self._trade_recorder.record_trade(out)
        await self._record_to_sheets(out, decision)

        return out

    def _execution_result_to_dict(self, result: Any, gate: Any) -> Dict[str, Any]:
        """ExecutionResult → act_result dict 변환."""
        is_complete = getattr(result, "state", None) and result.state.value == "COMPLETE"
        return {
            "status": "executed" if is_complete else "failed",
            "intent_id": result.order_id,
            "accepted": is_complete,
            "broker": getattr(self._broker, "NAME", "unknown"),
            "message": (
                f"Pipeline: {result.state.value}, "
                f"filled={result.filled_qty}/{result.requested_qty}"
            ),
            "mode": gate.mode.value,
            "pipeline_state": result.state.value,
            "filled_qty": result.filled_qty,
            "requested_qty": result.requested_qty,
            "avg_fill_price": float(result.avg_fill_price) if result.avg_fill_price else None,
            "splits_count": result.splits_count,
            "alerts": [
                {"code": a.code, "severity": a.severity, "message": a.message}
                for a in result.alerts
            ],
            "execution_pipeline_used": True,
        }

    def _create_fill_events_from_sends(self, ctx: Any, send_result: Any) -> list:
        """동기 브로커 전송 성공 → FillEvent 생성."""
        fills = []
        for split in send_result.orders:
            if split.status == SplitOrderStatus.SENT:
                fills.append(ExecFillEvent(
                    order_id=split.broker_order_id or split.split_id,
                    symbol=split.symbol,
                    side=split.side,
                    filled_qty=split.qty,
                    filled_price=split.price or ctx.order.price or Decimal("0"),
                ))
        return fills
