"""GoogleSheetsAdapter 단위 테스트."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import pytest
import pytest_asyncio

from src.db.adapters.google_sheets import GoogleSheetsAdapter, _safe_decimal
from src.db.contracts import LedgerEntry, Position


class FakeRepo:
    """테스트용 가짜 리포지토리."""

    def __init__(self, rows: list[dict] | None = None) -> None:
        self._rows = rows or []
        self._appended: list[dict] = []
        self._upserted: list[dict] = []

    async def get_all(self) -> list[dict]:
        return list(self._rows)

    async def get_by_id(self, id_val: str) -> Optional[dict]:
        for row in self._rows:
            if row.get("symbol") == id_val:
                return row
        return None

    async def get_by_symbol(self, symbol: str) -> list[dict]:
        return [r for r in self._rows if r.get("symbol") == symbol]

    async def upsert_position(self, data: dict) -> None:
        self._upserted.append(data)

    async def append_trade(self, data: dict) -> None:
        self._appended.append(data)


class FakeRepositoryManager:
    """테스트용 가짜 RepositoryManager."""

    def __init__(self) -> None:
        self._repos: dict[str, FakeRepo] = {}

    def set_repo(self, name: str, repo: FakeRepo) -> None:
        self._repos[name] = repo

    async def get_repository(self, name: str):
        return self._repos[name]

    async def health_check(self) -> dict:
        return {"status": "healthy"}


@pytest.fixture
def rm() -> FakeRepositoryManager:
    return FakeRepositoryManager()


@pytest_asyncio.fixture
async def adapter(rm: FakeRepositoryManager) -> GoogleSheetsAdapter:
    return GoogleSheetsAdapter(rm)


class TestSafeDecimal:
    """_safe_decimal 유틸리티."""

    def test_normal_value(self):
        assert _safe_decimal("100.5") == Decimal("100.5")

    def test_comma_separated(self):
        assert _safe_decimal("1,234,567") == Decimal("1234567")

    def test_none_returns_default(self):
        assert _safe_decimal(None) == Decimal("0")

    def test_empty_string(self):
        assert _safe_decimal("") == Decimal("0")

    def test_invalid_value(self):
        assert _safe_decimal("abc") == Decimal("0")

    def test_whitespace(self):
        assert _safe_decimal("  ") == Decimal("0")


class TestFetchPositions:
    """포지션 조회."""

    @pytest.mark.asyncio
    async def test_empty(self, rm, adapter):
        rm.set_repo("Position", FakeRepo([]))
        positions = await adapter.fetch_positions()
        assert positions == []

    @pytest.mark.asyncio
    async def test_single_position(self, rm, adapter):
        rm.set_repo("Position", FakeRepo([{
            "symbol": "005930",
            "qty": "100",
            "avg_price_current_currency": "75000",
            "market": "KOSPI",
            "market_value_krw": "7500000",
            "unrealized_pnl_krw": "50000",
        }]))
        positions = await adapter.fetch_positions()
        assert len(positions) == 1
        p = positions[0]
        assert p.symbol == "005930"
        assert p.qty == Decimal("100")
        assert p.avg_price == Decimal("75000")
        assert p.market == "KOSPI"

    @pytest.mark.asyncio
    async def test_fetch_position_by_symbol(self, rm, adapter):
        rm.set_repo("Position", FakeRepo([
            {"symbol": "005930", "qty": "100", "avg_price_current_currency": "75000"},
            {"symbol": "AAPL", "qty": "50", "avg_price_current_currency": "180"},
        ]))
        pos = await adapter.fetch_position("AAPL")
        assert pos is not None
        assert pos.symbol == "AAPL"
        assert pos.qty == Decimal("50")

    @pytest.mark.asyncio
    async def test_fetch_nonexistent(self, rm, adapter):
        rm.set_repo("Position", FakeRepo([]))
        pos = await adapter.fetch_position("NOPE")
        assert pos is None


class TestUpdatePosition:
    """포지션 업데이트."""

    @pytest.mark.asyncio
    async def test_update_calls_upsert(self, rm, adapter):
        repo = FakeRepo()
        rm.set_repo("Position", repo)
        ok = await adapter.update_position("005930", Decimal("200"), Decimal("76000"))
        assert ok is True
        assert len(repo._upserted) == 1
        assert repo._upserted[0]["symbol"] == "005930"
        assert repo._upserted[0]["qty"] == "200"


class TestLedger:
    """원장 조회/추가."""

    @pytest.mark.asyncio
    async def test_append_ledger(self, rm, adapter):
        repo = FakeRepo()
        rm.set_repo("T_Ledger", repo)
        entry = LedgerEntry(
            timestamp=datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            symbol="005930",
            side="BUY",
            qty=Decimal("50"),
            price=Decimal("75000"),
            amount=Decimal("3750000"),
            fee=Decimal("1000"),
            strategy_tag="SCALP",
            order_id="ORD001",
            broker="KIS",
        )
        ok = await adapter.append_ledger(entry)
        assert ok is True
        assert len(repo._appended) == 1
        assert repo._appended[0]["symbol"] == "005930"
        assert repo._appended[0]["side"] == "BUY"

    @pytest.mark.asyncio
    async def test_fetch_ledger_all(self, rm, adapter):
        rm.set_repo("T_Ledger", FakeRepo([
            {
                "timestamp": "2026-01-15T10:00:00+00:00",
                "symbol": "005930",
                "side": "BUY",
                "qty": "50",
                "price": "75000",
                "amount_krw": "3750000",
                "fee_tax": "1000",
                "strategy": "SCALP",
                "order_id": "ORD001",
                "broker": "KIS",
            },
        ]))
        entries = await adapter.fetch_ledger()
        assert len(entries) == 1
        assert entries[0].symbol == "005930"
        assert entries[0].side == "BUY"

    @pytest.mark.asyncio
    async def test_fetch_ledger_bad_timestamp_skipped(self, rm, adapter):
        rm.set_repo("T_Ledger", FakeRepo([
            {"timestamp": "", "symbol": "A", "side": "BUY"},
            {"timestamp": "invalid", "symbol": "B", "side": "BUY"},
        ]))
        entries = await adapter.fetch_ledger()
        assert len(entries) == 0

    @pytest.mark.asyncio
    async def test_fetch_ledger_bad_side_skipped(self, rm, adapter):
        rm.set_repo("T_Ledger", FakeRepo([
            {"timestamp": "2026-01-15T10:00:00", "symbol": "A", "side": "HOLD"},
        ]))
        entries = await adapter.fetch_ledger()
        assert len(entries) == 0


class TestUnsupportedOperations:
    """미지원 연산."""

    @pytest.mark.asyncio
    async def test_ohlcv_not_supported(self, adapter):
        now = datetime.now(timezone.utc)
        with pytest.raises(NotImplementedError):
            await adapter.fetch_ohlcv("A", now, now)

    @pytest.mark.asyncio
    async def test_tick_data_not_supported(self, adapter):
        now = datetime.now(timezone.utc)
        with pytest.raises(NotImplementedError):
            await adapter.fetch_tick_data("A", now, now)


class TestHealthCheck:
    """헬스체크."""

    @pytest.mark.asyncio
    async def test_healthy(self, rm, adapter):
        hs = await adapter.health_check()
        assert hs.healthy
        assert hs.source == "google_sheets"

    @pytest.mark.asyncio
    async def test_unhealthy(self):
        class FailRM:
            async def health_check(self):
                raise ConnectionError("sheets down")
            async def get_repository(self, name):
                raise ConnectionError("sheets down")

        adapt = GoogleSheetsAdapter(FailRM())
        hs = await adapt.health_check()
        assert not hs.healthy
        assert "sheets down" in hs.error
