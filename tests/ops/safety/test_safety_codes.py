"""
Phase 7 — Safety codes 테스트.

대표 Fail-Safe/Guardrail/Anomaly 코드가 테이블에 정의되어 있고,
codes_by_stage / message_for / get_code_info 가 일관되게 동작하는지 검증.
"""
from __future__ import annotations

import pytest

from ops.safety import (
    ANOMALY_TABLE,
    FAIL_SAFE_TABLE,
    GUARDRAIL_TABLE,
    codes_by_stage,
    get_anomaly_info,
    get_code_info,
    get_failsafe_info,
    get_guardrail_info,
    message_for,
)


class TestSafetyCodesTable:
    """코드 테이블 존재 및 조회."""

    def test_failsafe_table_has_core_codes(self):
        assert "FS001" in FAIL_SAFE_TABLE
        assert "FS010" in FAIL_SAFE_TABLE
        assert "FS020" in FAIL_SAFE_TABLE
        assert "FS030" in FAIL_SAFE_TABLE
        assert "FS040" in FAIL_SAFE_TABLE
        assert "FS050" in FAIL_SAFE_TABLE
        assert "FS070" in FAIL_SAFE_TABLE
        assert "FS080" in FAIL_SAFE_TABLE

    def test_guardrail_table_has_exec_codes(self):
        assert "G_EXE_SYMBOL_EMPTY" in GUARDRAIL_TABLE
        assert "G_EXE_QTY_NONPOSITIVE" in GUARDRAIL_TABLE
        assert "G_EXE_KILLSWITCH_ON" in GUARDRAIL_TABLE
        assert "GR001" in GUARDRAIL_TABLE

    def test_anomaly_table_has_core_codes(self):
        assert "AN001" in ANOMALY_TABLE
        assert "AN010" in ANOMALY_TABLE
        assert "AN020" in ANOMALY_TABLE
        assert "AN050" in ANOMALY_TABLE

    def test_get_failsafe_info(self):
        info = get_failsafe_info("FS001")
        assert info is not None
        assert info.code == "FS001"
        assert info.kind == "FAIL_SAFE"
        assert "Schema" in info.description
        assert info.stage == "Extract"

    def test_get_guardrail_info(self):
        info = get_guardrail_info("G_EXE_KILLSWITCH_ON")
        assert info is not None
        assert info.code == "G_EXE_KILLSWITCH_ON"
        assert info.kind == "GUARDRAIL"
        assert info.stage == "Act"

    def test_get_anomaly_info(self):
        info = get_anomaly_info("AN020")
        assert info is not None
        assert info.code == "AN020"
        assert info.kind == "ANOMALY"

    def test_get_code_info_failsafe_first(self):
        info = get_code_info("FS040")
        assert info is not None
        assert info.kind == "FAIL_SAFE"

    def test_message_for_includes_code_and_description(self):
        msg = message_for("FS001")
        assert "[FS001]" in msg
        assert "Schema" in msg

    def test_message_for_with_meta(self):
        msg = message_for("FS001", {"reason": "version_mismatch"})
        assert "FS001" in msg
        assert "reason" in msg or "version_mismatch" in msg

    def test_codes_by_stage_has_all_eteda_stages(self):
        by_stage = codes_by_stage()
        assert "Extract" in by_stage
        assert "Transform" in by_stage
        assert "Evaluate" in by_stage
        assert "Decide" in by_stage
        assert "Act" in by_stage
        assert "Performance" in by_stage

    def test_extract_stage_has_fs001_fs010(self):
        by_stage = codes_by_stage()
        extract_codes = by_stage["Extract"]
        assert "FS001" in extract_codes
        assert "FS010" in extract_codes

    def test_act_stage_has_fs040_and_guardrail_codes(self):
        by_stage = codes_by_stage()
        act_codes = by_stage["Act"]
        assert "FS040" in act_codes
        assert "G_EXE_SYMBOL_EMPTY" in act_codes
