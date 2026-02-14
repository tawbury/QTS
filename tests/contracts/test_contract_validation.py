"""
Contract 구조 검증 테스트 — 조기 감지.

Contract 필드 추가/삭제/이름 변경 시 이 테스트가 실패하도록 설계한다.
Fixture: tests/fixtures/contracts.py
Policy: docs/tasks/phases/Phase_10_Test_Governance/Fixtures_and_Contract_Policy.md
"""
from __future__ import annotations

import dataclasses
import pytest

try:
    from src.qts.core.ui.contract_schema import get_expected_contract_version
except ImportError:
    get_expected_contract_version = None
from src.provider.models.intent import ExecutionIntent
from src.provider.models.response import ExecutionResponse
from src.decision_pipeline.contracts.order_decision import OrderDecision
from src.decision_pipeline.contracts.execution_hint import ExecutionHint

from tests.fixtures.contracts import (
    UI_CONTRACT_REQUIRED_ROOT_KEYS,
    UI_CONTRACT_META_REQUIRED_KEYS,
    MINIMAL_UI_CONTRACT,
    ORDER_DECISION_REQUIRED_KEYS,
    MINIMAL_ORDER_DECISION_DICT,
    EXECUTION_HINT_REQUIRED_KEYS,
    MINIMAL_EXECUTION_HINT_DICT,
)


# ----- ExecutionIntent / ExecutionResponse: dataclass 필드명 고정 -----

EXECUTION_INTENT_FIELD_NAMES = frozenset(
    f.name for f in dataclasses.fields(ExecutionIntent)
)
EXECUTION_RESPONSE_FIELD_NAMES = frozenset(
    f.name for f in dataclasses.fields(ExecutionResponse)
)


class TestExecutionIntentContract:
    """ExecutionIntent Contract 필드 구조 검증."""

    def test_intent_required_fields_exist(self):
        """Contract 필드 추가/삭제 시 실패 — 조기 감지."""
        expected = {"intent_id", "symbol", "side", "quantity", "intent_type", "created_at", "metadata"}
        assert EXECUTION_INTENT_FIELD_NAMES == expected, (
            "ExecutionIntent field set changed; update fixture policy and this test."
        )


class TestExecutionResponseContract:
    """ExecutionResponse Contract 필드 구조 검증."""

    def test_response_required_fields_exist(self):
        """Contract 필드 추가/삭제 시 실패 — 조기 감지."""
        expected = {"intent_id", "accepted", "broker", "message", "timestamp"}
        assert EXECUTION_RESPONSE_FIELD_NAMES == expected, (
            "ExecutionResponse field set changed; update fixture policy and this test."
        )


# ----- OrderDecision: fixture round-trip + to_dict 키 -----

class TestOrderDecisionContract:
    """OrderDecision Contract 구조 검증 (fixture 기반)."""

    def test_order_decision_from_dict_to_dict_keys(self):
        """from_dict(fixture).to_dict() 키 집합이 기대와 일치. 키 변경 시 실패."""
        obj = OrderDecision.from_dict(MINIMAL_ORDER_DECISION_DICT)
        out = obj.to_dict()
        assert set(out.keys()) == ORDER_DECISION_REQUIRED_KEYS, (
            "OrderDecision to_dict() keys changed; update fixtures/contracts.py and this test."
        )

    def test_order_decision_fixture_minimal_valid(self):
        """최소 fixture로 from_dict 성공 (필수 필드만)."""
        obj = OrderDecision.from_dict(MINIMAL_ORDER_DECISION_DICT)
        assert obj.action == "NONE"
        assert obj.symbol is None
        assert obj.qty is None


# ----- ExecutionHint: fixture round-trip + to_dict 키 -----

class TestExecutionHintContract:
    """ExecutionHint Contract 구조 검증 (fixture 기반)."""

    def test_execution_hint_from_dict_to_dict_keys(self):
        """from_dict(fixture).to_dict() 키 집합이 기대와 일치."""
        obj = ExecutionHint.from_dict(MINIMAL_EXECUTION_HINT_DICT)
        out = obj.to_dict()
        assert set(out.keys()) == EXECUTION_HINT_REQUIRED_KEYS, (
            "ExecutionHint to_dict() keys changed; update fixtures/contracts.py and this test."
        )


# ----- UI Contract: 루트/메타 필수 키 + contract_version 일치 -----

@pytest.mark.skipif(
    get_expected_contract_version is None,
    reason="UI modules not yet migrated to src/",
)
class TestUIContract:
    """UI Contract 루트·메타 구조 및 버전 검증."""

    def test_ui_contract_required_root_keys(self):
        """루트 필수 블록 변경 시 실패."""
        assert set(MINIMAL_UI_CONTRACT.keys()) >= UI_CONTRACT_REQUIRED_ROOT_KEYS, (
            "UI Contract required root keys changed; update fixtures/contracts.py and policy."
        )

    def test_ui_contract_meta_required_keys(self):
        """meta 필수 키 변경 시 실패."""
        meta = MINIMAL_UI_CONTRACT.get("meta") or {}
        assert set(meta.keys()) >= UI_CONTRACT_META_REQUIRED_KEYS, (
            "UI Contract meta required keys changed; update fixtures/contracts.py."
        )

    def test_ui_contract_version_matches_expected(self):
        """meta.contract_version이 코드 기대 버전과 일치."""
        expected = get_expected_contract_version()
        meta = MINIMAL_UI_CONTRACT.get("meta") or {}
        assert meta.get("contract_version") == expected, (
            "UI Contract version in fixture does not match get_expected_contract_version(); sync fixture."
        )
