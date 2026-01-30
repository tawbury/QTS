"""
Real broker smoke tests (Phase 8). Opt-in only.

Minimal scenarios: Buy, Sell, Cancel, Partial fill.
Run with: pytest -m real_broker tests/runtime/broker/test_kis_real_broker_smoke.py
Or set QTS_RUN_REAL_BROKER=1 and implement skip logic in conftest.
"""

from __future__ import annotations

import pytest


@pytest.mark.real_broker
def test_real_broker_buy_scenario():
    """Minimal: single buy order accepted (real broker smoke)."""
    pytest.skip("Real broker smoke: enable with -m real_broker and real KIS env; use dry_run or paper account")


@pytest.mark.real_broker
def test_real_broker_sell_scenario():
    """Minimal: single sell order accepted (real broker smoke)."""
    pytest.skip("Real broker smoke: enable with -m real_broker and real KIS env; use dry_run or paper account")


@pytest.mark.real_broker
def test_real_broker_cancel_scenario():
    """Minimal: place then cancel (real broker smoke)."""
    pytest.skip("Real broker smoke: enable with -m real_broker and real KIS env; use dry_run or paper account")


@pytest.mark.real_broker
def test_real_broker_partial_fill_scenario():
    """Minimal: get_order returns partial fill (real broker smoke)."""
    pytest.skip("Real broker smoke: enable with -m real_broker and real KIS env; use dry_run or paper account")
