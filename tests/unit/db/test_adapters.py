"""InMemoryAdapter + HybridAdapter 테스트."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
import pytest_asyncio

from src.db.adapters.config import ConnectionPoolConfig, DataLayerConfig, DataSourceMode
from src.db.adapters.memory import InMemoryAdapter
from src.db.adapters.hybrid import HybridAdapter
from src.db.contracts import LedgerEntry, OHLCV, Position, TickData


@pytest_asyncio.fixture
async def adapter() -> InMemoryAdapter:
    return InMemoryAdapter()


class TestInMemoryAdapterPositions:
    """InMemoryAdapter 포지션 CRUD."""

    @pytest.mark.asyncio
    async def test_empty_positions(self, adapter: InMemoryAdapter):
        assert await adapter.fetch_positions() == []

    @pytest.mark.asyncio
    async def test_update_and_fetch(self, adapter: InMemoryAdapter):
        await adapter.update_position("005930", Decimal("100"), Decimal("75000"))
        positions = await adapter.fetch_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "005930"
        assert positions[0].qty == Decimal("100")

    @pytest.mark.asyncio
    async def test_fetch_single(self, adapter: InMemoryAdapter):
        await adapter.update_position("A", Decimal("10"), Decimal("50"))
        pos = await adapter.fetch_position("A")
        assert pos is not None
        assert pos.qty == Decimal("10")

    @pytest.mark.asyncio
    async def test_fetch_nonexistent(self, adapter: InMemoryAdapter):
        assert await adapter.fetch_position("NOPE") is None

    @pytest.mark.asyncio
    async def test_update_existing(self, adapter: InMemoryAdapter):
        await adapter.update_position("A", Decimal("10"), Decimal("50"))
        await adapter.update_position("A", Decimal("20"), Decimal("60"))
        pos = await adapter.fetch_position("A")
        assert pos is not None
        assert pos.qty == Decimal("20")
        assert pos.avg_price == Decimal("60")

    @pytest.mark.asyncio
    async def test_seed_position(self, adapter: InMemoryAdapter):
        pos = Position(
            symbol="X", qty=Decimal("5"), avg_price=Decimal("100"), market="KOSPI"
        )
        adapter.seed_position(pos)
        fetched = await adapter.fetch_position("X")
        assert fetched is not None
        assert fetched.market == "KOSPI"


class TestInMemoryAdapterLedger:
    """InMemoryAdapter 원장."""

    @pytest.mark.asyncio
    async def test_append_and_fetch(self, adapter: InMemoryAdapter):
        now = datetime.now(timezone.utc)
        entry = LedgerEntry(
            timestamp=now,
            symbol="005930",
            side="BUY",
            qty=Decimal("50"),
            price=Decimal("75000"),
            amount=Decimal("3750000"),
        )
        assert await adapter.append_ledger(entry)
        ledger = await adapter.fetch_ledger()
        assert len(ledger) == 1
        assert ledger[0].symbol == "005930"

    @pytest.mark.asyncio
    async def test_fetch_with_symbol_filter(self, adapter: InMemoryAdapter):
        now = datetime.now(timezone.utc)
        for sym in ["A", "B", "A"]:
            await adapter.append_ledger(
                LedgerEntry(
                    timestamp=now,
                    symbol=sym,
                    side="BUY",
                    qty=Decimal("1"),
                    price=Decimal("1"),
                    amount=Decimal("1"),
                )
            )
        result = await adapter.fetch_ledger(symbol="A")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_fetch_with_time_range(self, adapter: InMemoryAdapter):
        base = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        for i in range(5):
            await adapter.append_ledger(
                LedgerEntry(
                    timestamp=base + timedelta(hours=i),
                    symbol="A",
                    side="BUY",
                    qty=Decimal("1"),
                    price=Decimal("1"),
                    amount=Decimal("1"),
                )
            )
        result = await adapter.fetch_ledger(
            start=base + timedelta(hours=1),
            end=base + timedelta(hours=3),
        )
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_fetch_with_limit(self, adapter: InMemoryAdapter):
        now = datetime.now(timezone.utc)
        for _ in range(10):
            await adapter.append_ledger(
                LedgerEntry(
                    timestamp=now,
                    symbol="A",
                    side="BUY",
                    qty=Decimal("1"),
                    price=Decimal("1"),
                    amount=Decimal("1"),
                )
            )
        result = await adapter.fetch_ledger(limit=3)
        assert len(result) == 3


class TestInMemoryAdapterTimeSeries:
    """InMemoryAdapter OHLCV/TickData."""

    @pytest.mark.asyncio
    async def test_ohlcv_query(self, adapter: InMemoryAdapter):
        base = datetime(2026, 1, 15, tzinfo=timezone.utc)
        data = [
            OHLCV(
                time=base + timedelta(days=i),
                symbol="A",
                open=Decimal("100"),
                high=Decimal("110"),
                low=Decimal("90"),
                close=Decimal("105"),
                volume=1000,
            )
            for i in range(5)
        ]
        adapter.seed_ohlcv(data)
        result = await adapter.fetch_ohlcv(
            "A", base + timedelta(days=1), base + timedelta(days=3)
        )
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_tick_query(self, adapter: InMemoryAdapter):
        base = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        ticks = [
            TickData(
                time=base + timedelta(seconds=i),
                symbol="A",
                price=Decimal("100"),
                volume=10,
            )
            for i in range(10)
        ]
        adapter.seed_ticks(ticks)
        result = await adapter.fetch_tick_data(
            "A", base + timedelta(seconds=2), base + timedelta(seconds=5)
        )
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_empty_result(self, adapter: InMemoryAdapter):
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        result = await adapter.fetch_ohlcv("X", base, base + timedelta(days=1))
        assert result == []


class TestInMemoryAdapterHealth:
    """InMemoryAdapter 헬스체크."""

    @pytest.mark.asyncio
    async def test_health_check(self, adapter: InMemoryAdapter):
        hs = await adapter.health_check()
        assert hs.healthy
        assert hs.source == "in_memory"


class TestHybridAdapter:
    """HybridAdapter Dual-Write."""

    @pytest.mark.asyncio
    async def test_write_to_both(self):
        primary = InMemoryAdapter()
        secondary = InMemoryAdapter()
        hybrid = HybridAdapter(primary, secondary)

        await hybrid.update_position("A", Decimal("10"), Decimal("50"))

        # 양쪽 모두 기록
        p = await primary.fetch_position("A")
        s = await secondary.fetch_position("A")
        assert p is not None and p.qty == Decimal("10")
        assert s is not None and s.qty == Decimal("10")

    @pytest.mark.asyncio
    async def test_read_from_primary(self):
        primary = InMemoryAdapter()
        secondary = InMemoryAdapter()
        hybrid = HybridAdapter(primary, secondary)

        # primary에만 데이터 넣기
        await primary.update_position("A", Decimal("10"), Decimal("50"))
        pos = await hybrid.fetch_position("A")
        assert pos is not None
        assert pos.qty == Decimal("10")

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self):
        """Primary 실패 시 secondary fallback."""

        class FailingAdapter(InMemoryAdapter):
            async def fetch_positions(self):
                raise RuntimeError("primary down")

        primary = FailingAdapter()
        secondary = InMemoryAdapter()
        secondary.seed_position(
            Position(symbol="B", qty=Decimal("5"), avg_price=Decimal("100"))
        )
        hybrid = HybridAdapter(primary, secondary)

        positions = await hybrid.fetch_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "B"

    @pytest.mark.asyncio
    async def test_verify_consistency_match(self):
        primary = InMemoryAdapter()
        secondary = InMemoryAdapter()
        hybrid = HybridAdapter(primary, secondary)

        await hybrid.update_position("A", Decimal("10"), Decimal("50"))
        mismatches = await hybrid.verify_consistency()
        assert mismatches == []

    @pytest.mark.asyncio
    async def test_verify_consistency_mismatch(self):
        primary = InMemoryAdapter()
        secondary = InMemoryAdapter()
        hybrid = HybridAdapter(primary, secondary)

        await primary.update_position("A", Decimal("10"), Decimal("50"))
        await secondary.update_position("A", Decimal("20"), Decimal("50"))
        mismatches = await hybrid.verify_consistency()
        assert len(mismatches) == 1
        assert "Mismatch A" in mismatches[0]

    @pytest.mark.asyncio
    async def test_health_check(self):
        hybrid = HybridAdapter(InMemoryAdapter(), InMemoryAdapter())
        hs = await hybrid.health_check()
        assert hs.healthy
        assert hs.source == "hybrid"


class TestConfig:
    """설정 테스트."""

    def test_data_source_mode(self):
        assert DataSourceMode.SHEETS_ONLY.value == "SHEETS_ONLY"
        assert DataSourceMode.HYBRID.value == "HYBRID"
        assert DataSourceMode.DB_ONLY.value == "DB_ONLY"

    def test_connection_pool_defaults(self):
        cfg = ConnectionPoolConfig()
        assert cfg.min_connections == 5
        assert cfg.max_connections == 20

    def test_data_layer_config(self):
        cfg = DataLayerConfig(
            mode=DataSourceMode.DB_ONLY,
            db_dsn="postgresql://localhost/qts",
        )
        assert cfg.mode == DataSourceMode.DB_ONLY
        assert "localhost" in cfg.db_dsn
