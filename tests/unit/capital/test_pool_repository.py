"""capital/pool_repository.py 단위 테스트 — CapitalPoolRepository."""
import json
from decimal import Decimal

import pytest

from src.capital.contracts import CapitalPoolContract, PoolId, PoolState
from src.capital.pool_repository import CapitalPoolRepository


def _make_pools(**overrides) -> dict[PoolId, CapitalPoolContract]:
    """테스트용 풀 상태 생성."""
    defaults = {
        PoolId.SCALP: CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("10000000"),
            invested_capital=Decimal("2500000"),
            allocation_pct=Decimal("0.40"),
            target_allocation_pct=Decimal("0.40"),
        ),
        PoolId.SWING: CapitalPoolContract(
            pool_id=PoolId.SWING,
            total_capital=Decimal("8000000"),
            allocation_pct=Decimal("0.32"),
            target_allocation_pct=Decimal("0.35"),
        ),
        PoolId.PORTFOLIO: CapitalPoolContract(
            pool_id=PoolId.PORTFOLIO,
            total_capital=Decimal("7000000"),
            allocation_pct=Decimal("0.28"),
            target_allocation_pct=Decimal("0.25"),
        ),
    }
    defaults.update(overrides)
    return defaults


class TestCapitalPoolRepositorySave:
    def test_save_creates_file(self, tmp_path):
        path = tmp_path / "pool_states.jsonl"
        repo = CapitalPoolRepository(path)
        repo.save_pool_states(_make_pools())
        assert path.exists()

    def test_save_appends_lines(self, tmp_path):
        path = tmp_path / "pool_states.jsonl"
        repo = CapitalPoolRepository(path)
        repo.save_pool_states(_make_pools())
        repo.save_pool_states(_make_pools())
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_save_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "nested" / "dir" / "pool_states.jsonl"
        repo = CapitalPoolRepository(path)
        repo.save_pool_states(_make_pools())
        assert path.exists()

    def test_save_decimal_precision(self, tmp_path):
        path = tmp_path / "pool_states.jsonl"
        repo = CapitalPoolRepository(path)
        pools = _make_pools()
        pools[PoolId.SCALP].total_capital = Decimal("12345678.9012")
        repo.save_pool_states(pools)

        record = json.loads(path.read_text().strip())
        scalp_data = record["pools"]["SCALP"]
        assert scalp_data["total_capital"] == "12345678.9012"


class TestCapitalPoolRepositoryLoad:
    def test_load_nonexistent_returns_none(self, tmp_path):
        path = tmp_path / "nonexistent.jsonl"
        repo = CapitalPoolRepository(path)
        assert repo.load_pool_states() is None

    def test_load_empty_returns_none(self, tmp_path):
        path = tmp_path / "pool_states.jsonl"
        path.touch()
        repo = CapitalPoolRepository(path)
        assert repo.load_pool_states() is None

    def test_load_returns_latest(self, tmp_path):
        path = tmp_path / "pool_states.jsonl"
        repo = CapitalPoolRepository(path)

        # 첫 번째 저장
        pools1 = _make_pools()
        pools1[PoolId.SCALP].total_capital = Decimal("5000000")
        repo.save_pool_states(pools1)

        # 두 번째 저장
        pools2 = _make_pools()
        pools2[PoolId.SCALP].total_capital = Decimal("9999999")
        repo.save_pool_states(pools2)

        loaded = repo.load_pool_states()
        assert loaded is not None
        assert loaded[PoolId.SCALP].total_capital == Decimal("9999999")

    def test_load_all_pool_ids(self, tmp_path):
        path = tmp_path / "pool_states.jsonl"
        repo = CapitalPoolRepository(path)
        repo.save_pool_states(_make_pools())

        loaded = repo.load_pool_states()
        assert loaded is not None
        assert set(loaded.keys()) == {PoolId.SCALP, PoolId.SWING, PoolId.PORTFOLIO}

    def test_load_preserves_fields(self, tmp_path):
        path = tmp_path / "pool_states.jsonl"
        repo = CapitalPoolRepository(path)
        pools = _make_pools()
        pools[PoolId.SCALP].invested_capital = Decimal("3000000")
        pools[PoolId.SCALP].reserved_capital = Decimal("500000")
        pools[PoolId.SCALP].accumulated_profit = Decimal("1200000")
        pools[PoolId.SCALP].pool_state = PoolState.PAUSED
        repo.save_pool_states(pools)

        loaded = repo.load_pool_states()
        assert loaded is not None
        scalp = loaded[PoolId.SCALP]
        assert scalp.invested_capital == Decimal("3000000")
        assert scalp.reserved_capital == Decimal("500000")
        assert scalp.accumulated_profit == Decimal("1200000")
        assert scalp.pool_state == PoolState.PAUSED

    def test_load_skips_corrupt_lines(self, tmp_path):
        path = tmp_path / "pool_states.jsonl"
        repo = CapitalPoolRepository(path)
        repo.save_pool_states(_make_pools())

        # 손상 라인 추가
        with path.open("a") as f:
            f.write("NOT_JSON\n")
            f.write("\n")

        # 최신 유효 라인 반환 (실제로는 손상 라인이 마지막이므로 None)
        loaded = repo.load_pool_states()
        # 마지막 줄이 corrupt이므로 None 반환
        assert loaded is None

    def test_load_after_corrupt_then_valid(self, tmp_path):
        path = tmp_path / "pool_states.jsonl"
        repo = CapitalPoolRepository(path)
        repo.save_pool_states(_make_pools())

        with path.open("a") as f:
            f.write("NOT_JSON\n")

        # 새 유효 라인 추가
        pools2 = _make_pools()
        pools2[PoolId.SCALP].total_capital = Decimal("8888888")
        repo.save_pool_states(pools2)

        loaded = repo.load_pool_states()
        assert loaded is not None
        assert loaded[PoolId.SCALP].total_capital == Decimal("8888888")


class TestCapitalPoolRepositoryDefault:
    def test_create_default_pools(self, tmp_path):
        path = tmp_path / "pool_states.jsonl"
        repo = CapitalPoolRepository(path)
        pools = repo.create_default_pools(Decimal("25000000"))

        assert pools[PoolId.SCALP].total_capital == Decimal("25000000")
        assert pools[PoolId.SWING].total_capital == Decimal("0")
        assert pools[PoolId.PORTFOLIO].total_capital == Decimal("0")
        assert pools[PoolId.SCALP].allocation_pct == Decimal("1.00")

    def test_create_default_saves_file(self, tmp_path):
        path = tmp_path / "pool_states.jsonl"
        repo = CapitalPoolRepository(path)
        repo.create_default_pools(Decimal("10000000"))
        assert path.exists()

        loaded = repo.load_pool_states()
        assert loaded is not None
        assert loaded[PoolId.SCALP].total_capital == Decimal("10000000")


class TestCapitalPoolRepositoryRoundTrip:
    def test_save_and_load_cycle(self, tmp_path):
        path = tmp_path / "pool_states.jsonl"
        repo = CapitalPoolRepository(path)

        for i in range(5):
            pools = _make_pools()
            pools[PoolId.SCALP].total_capital = Decimal(str(10000000 + i * 100000))
            repo.save_pool_states(pools)

        loaded = repo.load_pool_states()
        assert loaded is not None
        assert loaded[PoolId.SCALP].total_capital == Decimal("10400000")

        lines = path.read_text().strip().split("\n")
        assert len(lines) == 5
