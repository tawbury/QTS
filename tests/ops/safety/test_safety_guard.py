"""
Phase 7 — Safety Guard (Fail-Safe 조건) 테스트.

대표 시나리오: 데이터 손상(FS001/FS010), Transform NaN(FS020), 리스크 오류(FS030),
브로커 오류(FS040), Equity<=0(FS050), Position-Ledger 불일치(FS070), Guardrail(GR030).
순수 함수/의존성 주입 구조로 테스트 가능.
"""
from __future__ import annotations

import pytest

from ops.safety import (
    check_act_safety,
    check_decide_safety,
    check_evaluate_safety,
    check_extract_safety,
    check_transform_safety,
)


class TestExtractSafety:
    """데이터 손상 / 스키마 불일치 — FS001, FS010."""

    def test_schema_mismatch_returns_fs001(self):
        r = check_extract_safety(schema_allowed=False, schema_reason="version_mismatch")
        assert r is not None
        assert r.code == "FS001"
        assert r.level == "FAIL_SAFE"
        assert r.blocked is True
        assert r.stage == "Extract"

    def test_raw_data_incomplete_returns_fs010(self):
        r = check_extract_safety(raw_data_complete=False)
        assert r is not None
        assert r.code == "FS010"
        assert r.blocked is True

    def test_extract_ok_returns_none(self):
        r = check_extract_safety(schema_allowed=True, raw_data_complete=True)
        assert r is None


class TestTransformSafety:
    """Transform NaN / Equity / Position-Ledger — FS020, FS050, FS070."""

    def test_nan_or_inf_returns_fs020(self):
        r = check_transform_safety(has_nan_or_inf=True)
        assert r is not None
        assert r.code == "FS020"
        assert r.blocked is True
        assert r.stage == "Transform"

    def test_equity_not_positive_returns_fs050(self):
        r = check_transform_safety(equity_positive=False)
        assert r is not None
        assert r.code == "FS050"
        assert r.blocked is True

    def test_position_ledger_inconsistent_returns_fs070(self):
        r = check_transform_safety(position_ledger_consistent=False)
        assert r is not None
        assert r.code == "FS070"
        assert r.blocked is True

    def test_transform_ok_returns_none(self):
        r = check_transform_safety()
        assert r is None


class TestEvaluateSafety:
    """리스크 계산 오류 — FS030."""

    def test_risk_not_ok_returns_fs030(self):
        r = check_evaluate_safety(risk_ok=False, risk_error_message="calc_error")
        assert r is not None
        assert r.code == "FS030"
        assert r.blocked is True
        assert r.stage == "Evaluate"

    def test_evaluate_ok_returns_none(self):
        r = check_evaluate_safety(risk_ok=True)
        assert r is None


class TestDecideSafety:
    """Guardrail — GR030, G_EXE_QTY_NONPOSITIVE, GR040."""

    def test_risk_not_approved_returns_gr030(self):
        r = check_decide_safety(risk_approved=False)
        assert r is not None
        assert r.code == "GR030"
        assert r.level == "GUARDRAIL"
        assert r.blocked is True

    def test_final_qty_not_positive_returns_guardrail(self):
        r = check_decide_safety(final_qty_positive=False)
        assert r is not None
        assert r.code == "G_EXE_QTY_NONPOSITIVE"
        assert r.blocked is True

    def test_price_info_inconsistent_returns_gr040(self):
        r = check_decide_safety(price_info_consistent=False)
        assert r is not None
        assert r.code == "GR040"
        assert r.blocked is True

    def test_decide_ok_returns_none(self):
        r = check_decide_safety()
        assert r is None


class TestActSafety:
    """브로커/실행 오류 — FS040."""

    def test_broker_not_ok_returns_fs040(self):
        r = check_act_safety(broker_ok=False)
        assert r is not None
        assert r.code == "FS040"
        assert r.blocked is True
        assert r.stage == "Act"

    def test_execution_result_incomplete_returns_fs040(self):
        r = check_act_safety(execution_result_complete=False)
        assert r is not None
        assert r.code == "FS040"
        assert r.blocked is True

    def test_consecutive_failures_exceeds_max_returns_fs040(self):
        r = check_act_safety(consecutive_failures=3, max_failures=3)
        assert r is not None
        assert r.code == "FS040"
        assert r.blocked is True
        assert r.meta.get("consecutive_failures") == 3

    def test_act_ok_returns_none(self):
        r = check_act_safety(broker_ok=True, execution_result_complete=True, consecutive_failures=0)
        assert r is None
