"""
Trading Engine

Engine Layer와 Broker Layer 분리: 주문 의도(ExecutionIntent)를 BrokerEngine에 전달하고
ExecutionResponse를 반환. 아키텍처 §7 Trading Engine — execute() Contract 정합.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from .base_engine import BaseEngine
from ..config.config_models import UnifiedConfig
from ..execution.interfaces.broker import BrokerEngine
from ..execution.models.intent import ExecutionIntent
from ..execution.models.response import ExecutionResponse


def _intent_from_data(data: Dict[str, Any]) -> ExecutionIntent:
    """Build ExecutionIntent from execute() input dict (Contract)."""
    if "intent" in data:
        raw = data["intent"]
        if isinstance(raw, ExecutionIntent):
            return raw
        if isinstance(raw, dict):
            return ExecutionIntent(
                intent_id=str(raw.get("intent_id", "")),
                symbol=str(raw.get("symbol", "")),
                side=str(raw.get("side", "BUY")).upper(),
                quantity=float(raw.get("quantity", 0)),
                intent_type=str(raw.get("intent_type", "NOOP")).upper(),
                metadata=dict(raw.get("metadata", {})),
            )
    # Build from flat keys
    return ExecutionIntent(
        intent_id=str(data.get("intent_id", "")),
        symbol=str(data.get("symbol", "")),
        side=str(data.get("side", "BUY")).upper(),
        quantity=float(data.get("quantity", 0)),
        intent_type=str(data.get("intent_type", "NOOP")).upper(),
        metadata=dict(data.get("metadata", {})),
    )


def _response_to_dict(resp: ExecutionResponse) -> Dict[str, Any]:
    """ExecutionResponse to dict for execute() output contract."""
    return {
        "intent_id": resp.intent_id,
        "accepted": resp.accepted,
        "broker": resp.broker,
        "message": resp.message,
        "timestamp": resp.timestamp.isoformat() if hasattr(resp.timestamp, "isoformat") else str(resp.timestamp),
    }


class TradingEngine(BaseEngine):
    """
    Trading Engine (Engine Layer)

    역할: Decide 결과(ExecutionIntent)를 Broker Layer에 전달하고 ExecutionResponse 반환.
    브로커 API/실주문은 BrokerEngine 구현에 위임; 엔진은 계약만 유지.
    """

    def __init__(self, config: UnifiedConfig, broker: BrokerEngine):
        super().__init__(config)
        self._broker: BrokerEngine = broker
        self.logger.info("TradingEngine created with injected BrokerEngine")

    async def initialize(self) -> bool:
        if not self._broker:
            raise ValueError("BrokerEngine must be provided via constructor")
        self._update_state(is_running=False)
        return True

    async def start(self) -> bool:
        self._update_state(is_running=True)
        return True

    async def stop(self) -> bool:
        self._update_state(is_running=False)
        return True

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = datetime.now()
        try:
            operation = data.get("operation")
            if operation == "submit_intent":
                intent = _intent_from_data(data)
                response = self._broker.submit_intent(intent)
                execution_time = (datetime.now() - start_time).total_seconds()
                self._update_metrics(execution_time, success=True)
                return {
                    "success": True,
                    "data": _response_to_dict(response),
                    "execution_time": execution_time,
                }
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(execution_time, success=False)
            return {
                "success": False,
                "error": f"Unknown operation: {operation}",
                "execution_time": execution_time,
            }
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(execution_time, success=False)
            self._update_state(self.state.is_running, error=str(e))
            return {"success": False, "error": str(e), "execution_time": execution_time}
