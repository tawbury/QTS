"""
UI Contract 렌더러 입출력 테스트 (Phase 6 §2.1).

Zero-Formula 렌더러: Contract 블록 → List[List[Any]] (값만, 수식 없음).
docs/arch/06_UI_Architecture.md, UI_Contract_Schema.md.

NOTE: UI 모듈(runtime.ui.*)이 src/로 마이그레이션되지 않아 전체 skip 처리.
"""

import pytest

pytestmark = pytest.mark.skip(reason="UI modules not yet migrated to src/")


class TestRendererOutputShape:
    """렌더러 출력: List[List[Any]], 헤더 + 데이터 행."""

    def test_render_account_summary_returns_list_of_lists(self):
        account = {"total_equity": 1000000.0, "daily_pnl": 5000.0}
        out = render_account_summary(account)
        assert isinstance(out, list)
        assert len(out) >= 1
        assert all(isinstance(row, list) for row in out)
        assert "total_equity" in (out[0] if out else [])

    def test_render_account_summary_empty_returns_headers_and_placeholder_row(self):
        out = render_account_summary({})
        assert isinstance(out, list)
        assert len(out) == 2
        assert out[0] and out[1]

    def test_render_pipeline_status_returns_list_of_lists(self):
        ps = {"pipeline_state": "IDLE", "last_cycle_duration": 1.5}
        out = render_pipeline_status(ps)
        assert isinstance(out, list)
        assert len(out) >= 2
        assert "pipeline_state" in (out[0] if out else [])

    def test_render_meta_block_returns_list_of_lists(self):
        meta = {"contract_version": "1.0.0", "timestamp": "2025-01-01T00:00:00Z"}
        out = render_meta_block(meta)
        assert isinstance(out, list)
        assert len(out) >= 2
        assert "contract_version" in (out[0] if out else [])

    def test_render_risk_monitor_none_returns_headers_and_placeholder(self):
        out = render_risk_monitor(None)
        assert isinstance(out, list)
        assert len(out) == 2

    def test_render_performance_none_returns_headers_and_placeholder(self):
        out = render_performance(None)
        assert isinstance(out, list)
        assert len(out) == 2

    def test_render_symbol_detail_empty_returns_headers_only(self):
        out = render_symbol_detail([])
        assert isinstance(out, list)
        assert len(out) == 1
        assert "symbol" in (out[0] if out else [])

    def test_render_symbol_detail_with_items_returns_headers_plus_rows(self):
        symbols = [{"symbol": "AAPL", "price": 180.0, "qty": 10}]
        out = render_symbol_detail(symbols)
        assert isinstance(out, list)
        assert len(out) == 2
        assert out[1][0] == "AAPL" or out[1][0] == 180.0 or out[1][0] == 10


class TestUIContractBuilder:
    """UIContractBuilder.build 필수 필드·출력 구조."""

    def test_build_produces_required_root_keys(self):
        contract = UIContractBuilder.build(
            account={"total_equity": 0.0, "daily_pnl": 0.0},
            symbols=[],
            pipeline_status={"pipeline_state": "IDLE"},
        )
        assert "account" in contract
        assert "symbols" in contract
        assert "pipeline_status" in contract
        assert "meta" in contract
        assert contract["meta"].get("contract_version") == get_expected_contract_version()

    def test_build_missing_total_equity_raises(self):
        with pytest.raises(ValueError, match="total_equity"):
            UIContractBuilder.build(
                account={"daily_pnl": 0.0},
                symbols=[],
                pipeline_status={"pipeline_state": "IDLE"},
            )

    def test_build_missing_pipeline_state_raises(self):
        with pytest.raises(ValueError, match="pipeline_state"):
            UIContractBuilder.build(
                account={"total_equity": 0.0, "daily_pnl": 0.0},
                symbols=[],
                pipeline_status={},
            )
