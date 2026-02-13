"""Capital Guardrails & Fail-Safe 테스트."""
from decimal import Decimal

import pytest

from src.capital.contracts import CapitalPoolContract, PoolId, PoolState
from src.capital.guardrails import (
    check_abnormal_capital_change,
    check_allocation_sum,
    check_daily_transfer_limit,
    check_drift,
    check_max_allocation,
    check_min_allocation,
    check_negative_pool_capital,
    check_pool_mdd_critical,
    check_pool_state_mismatch,
    check_total_capital_zero,
    check_transfer_exceeds_available,
    run_all_guardrails,
)


def _make_pools(**overrides) -> dict[PoolId, CapitalPoolContract]:
    """기본 풀 셋 생성."""
    pools = {
        PoolId.SCALP: CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("4000000"),
            allocation_pct=Decimal("0.40"),
            target_allocation_pct=Decimal("0.40"),
        ),
        PoolId.SWING: CapitalPoolContract(
            pool_id=PoolId.SWING,
            total_capital=Decimal("3500000"),
            allocation_pct=Decimal("0.35"),
            target_allocation_pct=Decimal("0.35"),
        ),
        PoolId.PORTFOLIO: CapitalPoolContract(
            pool_id=PoolId.PORTFOLIO,
            total_capital=Decimal("2500000"),
            allocation_pct=Decimal("0.25"),
            target_allocation_pct=Decimal("0.25"),
        ),
    }
    return pools


class TestGR050AllocationSum:
    """GR050: 배분 합계 검증."""

    def test_valid_sum(self):
        pools = _make_pools()
        assert check_allocation_sum(pools) is None

    def test_invalid_sum(self):
        pools = _make_pools()
        pools[PoolId.SCALP].allocation_pct = Decimal("0.50")
        # sum = 0.50 + 0.35 + 0.25 = 1.10
        alert = check_allocation_sum(pools)
        assert alert is not None
        assert alert.code == "GR050"


class TestGR051MinAllocation:
    """GR051: 최소 비율 미달."""

    def test_all_ok(self):
        pools = _make_pools()
        total = Decimal("10000000")
        alerts = check_min_allocation(pools, total)
        assert len(alerts) == 0

    def test_scalp_below_min(self):
        pools = _make_pools()
        pools[PoolId.SCALP].total_capital = Decimal("100000")  # 1% < 5%
        total = Decimal("10000000")
        alerts = check_min_allocation(pools, total)
        assert any(a.code == "GR051" and a.pool_id == PoolId.SCALP for a in alerts)


class TestGR052MaxAllocation:
    """GR052: 최대 비율 초과."""

    def test_all_ok(self):
        pools = _make_pools()
        total = Decimal("10000000")
        alerts = check_max_allocation(pools, total)
        assert len(alerts) == 0

    def test_scalp_above_max(self):
        pools = _make_pools()
        pools[PoolId.SCALP].total_capital = Decimal("9000000")  # 90% > 80%
        total = Decimal("10000000")
        alerts = check_max_allocation(pools, total)
        assert any(a.code == "GR052" and a.pool_id == PoolId.SCALP for a in alerts)


class TestGR053TransferExceedsAvailable:
    """GR053: 이전액 > 가용 자본."""

    def test_ok(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("10000000"),
        )
        assert check_transfer_exceeds_available(pool, Decimal("5000000")) is None

    def test_exceeds(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("10000000"),
            invested_capital=Decimal("8000000"),  # available = 2M
        )
        alert = check_transfer_exceeds_available(pool, Decimal("5000000"))
        assert alert is not None
        assert alert.code == "GR053"


class TestGR055Drift:
    """GR055: 드리프트 검증."""

    def test_no_drift(self):
        pools = _make_pools()
        total = Decimal("10000000")
        alerts = check_drift(pools, total)
        assert len(alerts) == 0

    def test_with_drift(self):
        pools = _make_pools()
        pools[PoolId.SCALP].total_capital = Decimal("6000000")  # 60% vs 40% target
        total = Decimal("10000000")
        alerts = check_drift(pools, total)
        assert any(a.code == "GR055" for a in alerts)


class TestFS080TotalCapitalZero:
    """FS080: 총 자본 <= 0."""

    def test_positive(self):
        assert check_total_capital_zero(Decimal("10000000")) is None

    def test_zero(self):
        alert = check_total_capital_zero(Decimal("0"))
        assert alert is not None
        assert alert.code == "FS080"
        assert alert.severity == "CRITICAL"

    def test_negative(self):
        alert = check_total_capital_zero(Decimal("-1000"))
        assert alert is not None
        assert alert.code == "FS080"


class TestFS081NegativePoolCapital:
    """FS081: 풀 자본 음수."""

    def test_all_positive(self):
        pools = _make_pools()
        alerts = check_negative_pool_capital(pools)
        assert len(alerts) == 0

    def test_negative_pool(self):
        pools = _make_pools()
        pools[PoolId.SWING].total_capital = Decimal("-500000")
        alerts = check_negative_pool_capital(pools)
        assert len(alerts) == 1
        assert alerts[0].code == "FS081"
        assert alerts[0].pool_id == PoolId.SWING


class TestFS082PoolMDD:
    """FS082: 풀 MDD > 20%."""

    def test_below_threshold(self):
        assert check_pool_mdd_critical(PoolId.SCALP, 0.15) is None

    def test_above_threshold(self):
        alert = check_pool_mdd_critical(PoolId.SCALP, 0.25)
        assert alert is not None
        assert alert.code == "FS082"
        assert alert.severity == "CRITICAL"


class TestGR054DailyTransferLimit:
    """GR054: 일일 자본 이동 한도."""

    def test_within_limit(self):
        assert check_daily_transfer_limit(
            Decimal("500000"), Decimal("10000000")
        ) is None

    def test_exceeds_limit(self):
        alert = check_daily_transfer_limit(
            Decimal("2000000"), Decimal("10000000")
        )
        assert alert is not None
        assert alert.code == "GR054"
        assert alert.severity == "WARNING"

    def test_zero_equity(self):
        assert check_daily_transfer_limit(
            Decimal("100"), Decimal("0")
        ) is None


class TestFS083AbnormalCapitalChange:
    """FS083: 비정상 자본 변동."""

    def test_normal_change(self):
        assert check_abnormal_capital_change(
            Decimal("10200000"), Decimal("10000000")
        ) is None  # 2% < 5%

    def test_abnormal_change(self):
        alert = check_abnormal_capital_change(
            Decimal("8000000"), Decimal("10000000")
        )
        assert alert is not None
        assert alert.code == "FS083"
        assert alert.severity == "CRITICAL"

    def test_zero_previous(self):
        assert check_abnormal_capital_change(
            Decimal("10000000"), Decimal("0")
        ) is None


class TestFS084PoolStateMismatch:
    """FS084: 풀 합계 ≠ 총 자본."""

    def test_match(self):
        pools = _make_pools()
        total = Decimal("10000000")
        assert check_pool_state_mismatch(pools, total) is None

    def test_mismatch(self):
        pools = _make_pools()
        # sum = 4M + 3.5M + 2.5M = 10M, but total = 12M
        alert = check_pool_state_mismatch(pools, Decimal("12000000"))
        assert alert is not None
        assert alert.code == "FS084"
        assert alert.severity == "CRITICAL"

    def test_within_tolerance(self):
        pools = _make_pools()
        # sum = 10M, total = 10000500 (within 1000 tolerance)
        assert check_pool_state_mismatch(
            pools, Decimal("10000500")
        ) is None


class TestRunAllGuardrails:
    """전체 가드레일 실행."""

    def test_healthy_pools(self):
        pools = _make_pools()
        total = Decimal("10000000")
        alerts = run_all_guardrails(pools, total)
        assert len(alerts) == 0

    def test_mixed_issues(self):
        pools = _make_pools()
        pools[PoolId.SWING].total_capital = Decimal("-100")
        total = Decimal("10000000")
        alerts = run_all_guardrails(pools, total)
        # FS081 (negative) + FS084 (mismatch) + GR051 (swing below min) + etc
        codes = {a.code for a in alerts}
        assert "FS081" in codes

    def test_with_previous_total_fs083(self):
        pools = _make_pools()
        total = Decimal("10000000")
        alerts = run_all_guardrails(
            pools, total, previous_total=Decimal("20000000")
        )
        codes = {a.code for a in alerts}
        assert "FS083" in codes
