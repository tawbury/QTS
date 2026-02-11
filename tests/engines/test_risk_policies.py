"""
src/risk/policies/risk_policy.py 단위 테스트.

테스트 대상:
- RiskStage: 리스크 단계 열거형
- RiskPolicy: 리스크 정책 데이터클래스
"""
import pytest
from src.risk.policies.risk_policy import RiskStage, RiskPolicy


class TestRiskStage:
    """RiskStage 열거형 테스트."""

    def test_values(self):
        assert RiskStage.WARN.value == "warn"
        assert RiskStage.REDUCE.value == "reduce"
        assert RiskStage.BLOCK.value == "block"

    def test_is_str_enum(self):
        assert isinstance(RiskStage.WARN, str)

    def test_from_string(self):
        assert RiskStage("warn") == RiskStage.WARN
        assert RiskStage("reduce") == RiskStage.REDUCE
        assert RiskStage("block") == RiskStage.BLOCK


class TestRiskPolicy:
    """RiskPolicy 데이터클래스 테스트."""

    def test_defaults(self):
        policy = RiskPolicy()
        assert policy.max_order_qty == 1
        assert policy.stage == RiskStage.WARN
        assert policy.reduce_to_qty == 1

    def test_custom_values(self):
        policy = RiskPolicy(max_order_qty=10, stage=RiskStage.BLOCK, reduce_to_qty=5)
        assert policy.max_order_qty == 10
        assert policy.stage == RiskStage.BLOCK
        assert policy.reduce_to_qty == 5

    def test_frozen(self):
        policy = RiskPolicy()
        with pytest.raises(AttributeError):
            policy.max_order_qty = 99

    def test_negative_max_order_qty_raises(self):
        with pytest.raises(ValueError, match="max_order_qty must be >= 0"):
            RiskPolicy(max_order_qty=-1)

    def test_negative_reduce_to_qty_raises(self):
        with pytest.raises(ValueError, match="reduce_to_qty must be >= 0"):
            RiskPolicy(reduce_to_qty=-1)

    def test_zero_values_allowed(self):
        policy = RiskPolicy(max_order_qty=0, reduce_to_qty=0)
        assert policy.max_order_qty == 0
        assert policy.reduce_to_qty == 0

    def test_equality(self):
        p1 = RiskPolicy(max_order_qty=5, stage=RiskStage.REDUCE, reduce_to_qty=3)
        p2 = RiskPolicy(max_order_qty=5, stage=RiskStage.REDUCE, reduce_to_qty=3)
        assert p1 == p2

    def test_inequality(self):
        p1 = RiskPolicy(max_order_qty=5)
        p2 = RiskPolicy(max_order_qty=10)
        assert p1 != p2
