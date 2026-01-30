"""
Contract 검증용 최소 유효 fixture (SSoT).

Contract 구조 변경 시 이 fixture와 tests/contracts/test_contract_validation.py를
함께 수정하여 조기 감지한다.
Policy: docs/tasks/phases/Phase_10_Test_Governance/Fixtures_and_Contract_Policy.md
"""
from __future__ import annotations

from typing import Any, Dict

# ---------------------------------------------------------------------------
# UI Contract (docs/arch/UI_Contract_Schema.md, runtime.ui.contract_schema)
# ---------------------------------------------------------------------------

UI_CONTRACT_REQUIRED_ROOT_KEYS = frozenset({"account", "symbols", "pipeline_status", "meta"})
UI_CONTRACT_META_REQUIRED_KEYS = frozenset({"contract_version", "timestamp"})

MINIMAL_UI_CONTRACT: Dict[str, Any] = {
    "account": {"total_equity": 0.0, "daily_pnl": 0.0},
    "symbols": [],
    "pipeline_status": {"pipeline_state": "IDLE"},
    "meta": {"contract_version": "1.0.0", "timestamp": "2025-01-01T00:00:00Z"},
}

# ---------------------------------------------------------------------------
# OrderDecision (ops.decision_pipeline.contracts.order_decision)
# ---------------------------------------------------------------------------

ORDER_DECISION_REQUIRED_KEYS = frozenset({"action", "symbol", "qty", "order_type", "limit_price", "reason"})

MINIMAL_ORDER_DECISION_DICT: Dict[str, Any] = {
    "action": "NONE",
    "symbol": None,
    "qty": None,
    "order_type": "NONE",
    "limit_price": None,
    "reason": None,
}

# ---------------------------------------------------------------------------
# ExecutionHint (ops.decision_pipeline.contracts.execution_hint)
# ---------------------------------------------------------------------------

EXECUTION_HINT_REQUIRED_KEYS = frozenset({"intended", "broker", "account", "constraints", "note"})

MINIMAL_EXECUTION_HINT_DICT: Dict[str, Any] = {
    "intended": False,
    "broker": None,
    "account": None,
    "constraints": {},
    "note": None,
}
