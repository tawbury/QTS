"""
src/pipeline/adapters/ops_decision_to_intent.py 계약 테스트.

테스트 대상:
- OpsDecisionToIntentAdapter: ops decision → QTS ExecutionIntent 변환
- 입력 계약: dict 또는 JSON string
- 출력 계약: OpsDecisionParseResult (intent + raw)
"""
import json
import pytest
from src.pipeline.adapters.ops_decision_to_intent import (
    OpsDecisionToIntentAdapter,
    OpsDecisionParseResult,
)


@pytest.fixture
def adapter():
    return OpsDecisionToIntentAdapter()


class TestOpsDecisionToIntentAdapter:
    """OpsDecisionToIntentAdapter 계약 테스트."""

    def test_valid_dict_payload(self, adapter):
        payload = {"symbol": "005930", "side": "BUY", "quantity": 10}
        result = adapter.from_payload(payload)
        assert isinstance(result, OpsDecisionParseResult)
        assert result.intent.symbol == "005930"
        assert result.intent.side == "BUY"
        assert result.intent.quantity == 10.0

    def test_valid_json_string_payload(self, adapter):
        payload = json.dumps({"symbol": "005930", "side": "SELL", "qty": 5})
        result = adapter.from_payload(payload)
        assert result.intent.symbol == "005930"
        assert result.intent.side == "SELL"
        assert result.intent.quantity == 5.0

    def test_alternative_key_ticker(self, adapter):
        payload = {"ticker": "035420", "side": "BUY", "quantity": 1}
        result = adapter.from_payload(payload)
        assert result.intent.symbol == "035420"

    def test_alternative_key_qty(self, adapter):
        payload = {"symbol": "005930", "side": "BUY", "qty": 3}
        result = adapter.from_payload(payload)
        assert result.intent.quantity == 3.0

    def test_invalid_side_becomes_noop(self, adapter):
        payload = {"symbol": "005930", "side": "INVALID", "quantity": 10}
        result = adapter.from_payload(payload)
        assert result.intent.intent_type == "NOOP"

    def test_zero_quantity_becomes_noop(self, adapter):
        payload = {"symbol": "005930", "side": "BUY", "quantity": 0}
        result = adapter.from_payload(payload)
        assert result.intent.intent_type == "NOOP"

    def test_negative_quantity_becomes_noop(self, adapter):
        payload = {"symbol": "005930", "side": "BUY", "quantity": -5}
        result = adapter.from_payload(payload)
        assert result.intent.intent_type == "NOOP"

    def test_missing_symbol_raises(self, adapter):
        payload = {"side": "BUY", "quantity": 10}
        with pytest.raises(KeyError, match="missing required key"):
            adapter.from_payload(payload)

    def test_missing_side_raises(self, adapter):
        payload = {"symbol": "005930", "quantity": 10}
        with pytest.raises(KeyError, match="missing required key"):
            adapter.from_payload(payload)

    def test_missing_quantity_raises(self, adapter):
        payload = {"symbol": "005930", "side": "BUY"}
        with pytest.raises(KeyError, match="missing required key"):
            adapter.from_payload(payload)

    def test_empty_string_raises(self, adapter):
        with pytest.raises(ValueError, match="empty string"):
            adapter.from_payload("")

    def test_invalid_json_raises(self, adapter):
        with pytest.raises(ValueError, match="not valid JSON"):
            adapter.from_payload("{bad json")

    def test_non_dict_json_raises(self, adapter):
        with pytest.raises(ValueError, match="must be an object"):
            adapter.from_payload("[1, 2, 3]")

    def test_unsupported_type_raises(self, adapter):
        with pytest.raises(TypeError, match="unsupported payload type"):
            adapter.from_payload(12345)

    def test_intent_has_uuid(self, adapter):
        payload = {"symbol": "005930", "side": "BUY", "quantity": 1}
        result = adapter.from_payload(payload)
        assert result.intent.intent_id is not None
        assert len(result.intent.intent_id) > 0

    def test_raw_preserved(self, adapter):
        payload = {"symbol": "005930", "side": "BUY", "quantity": 1, "extra": "data"}
        result = adapter.from_payload(payload)
        assert "extra" in result.raw

    def test_keys_normalized_to_lowercase(self, adapter):
        payload = {"SYMBOL": "005930", "Side": "BUY", "Quantity": 10}
        result = adapter.from_payload(payload)
        assert result.intent.symbol == "005930"

    def test_intent_metadata_source(self, adapter):
        payload = {"symbol": "005930", "side": "BUY", "quantity": 1}
        result = adapter.from_payload(payload)
        assert result.intent.metadata["source"] == "ops"

    def test_intent_type_default_noop(self, adapter):
        payload = {"symbol": "005930", "side": "BUY", "quantity": 1}
        result = adapter.from_payload(payload)
        assert result.intent.intent_type == "NOOP"

    def test_explicit_intent_type(self, adapter):
        payload = {"symbol": "005930", "side": "BUY", "quantity": 1, "intent_type": "MARKET"}
        result = adapter.from_payload(payload)
        assert result.intent.intent_type == "MARKET"
