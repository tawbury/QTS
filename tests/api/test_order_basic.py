import pytest

pytestmark = pytest.mark.api_exploration


def test_kis_order_basic():
    pytest.skip(
        "Order API requires runtime-issued access token. "
        "Observed in Phase 1.5; executed in Phase 2."
    )
