from __future__ import annotations

import pytest

from ops.observer.analysis.adapters.signal_to_decision_adapter import (
    SignalDecisionAdapter,
)

from ops.decision_pipeline.pipeline.runner import DecisionPipelineRunner


def test_phase14_signal_to_decision_adapter_single_signal_roundtrip():
    """
    Phase 14 E2E (Adapter Boundary) Test

    Purpose:
    - Verify that a single Signal can be adapted and consumed by
      the decision_pipeline without any modification to the pipeline.
    """

    # ------------------------------------------------------------------
    # GIVEN: a single, minimal Signal (tick-like)
    # ------------------------------------------------------------------
    signal = {
        "symbol": "005930",
        "market": "KOSPI",
        "captured_at": "2025-01-01T09:00:00Z",
        "build_id": "test-build-001",
        "source": "replay",

        # extra fields (must survive in meta)
        "price": 72000,
        "volume": 1200,
        "bid": 71900,
        "ask": 72100,
        "raw_tick": {"foo": "bar"},
    }

    adapter = SignalDecisionAdapter()

    # ------------------------------------------------------------------
    # WHEN: adapt Signal -> Decision Input
    # ------------------------------------------------------------------
    decision_input = adapter.adapt(signal)

    # ------------------------------------------------------------------
    # THEN (1): structural expectations
    # ------------------------------------------------------------------
    assert isinstance(decision_input, dict)

    # required identifiers must be exposed at top-level
    assert decision_input["symbol"] == "005930"
    assert decision_input["market"] == "KOSPI"
    assert decision_input["captured_at"] == "2025-01-01T09:00:00Z"
    assert decision_input["build_id"] == "test-build-001"
    assert decision_input["source"] == "replay"

    # meta must exist and preserve original data
    assert "meta" in decision_input
    assert decision_input["meta"]["price"] == 72000
    assert decision_input["meta"]["raw_tick"]["foo"] == "bar"

    # ------------------------------------------------------------------
    # THEN (2): decision_pipeline consumption test
    # ------------------------------------------------------------------
    runner = DecisionPipelineRunner()

    # This must NOT raise.
    # Result meaning is irrelevant for Phase 14.
    result = runner.run(decision_input)

    assert result is not None
