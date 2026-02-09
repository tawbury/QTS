"""
KIS Order Execution Test Script

Tests order placement for KIS broker in VTS (mock trading) mode.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
_ROOT = Path(__file__).resolve().parents[2]  # tests/integration -> prj_qts
sys.path.insert(0, str(_ROOT / "src"))

from dotenv import load_dotenv
from runtime.config.env_loader import get_broker_config
from runtime.execution.models.order_request import OrderRequest, OrderSide, OrderType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_log = logging.getLogger(__name__)


def test_kis_order_placement():
    """Test KIS order placement (VTS mode)"""
    _log.info("=" * 60)
    _log.info("KIS Order Placement Test (VTS Mode)")
    _log.info("=" * 60)

    try:
        # Load broker config
        broker_config = get_broker_config(broker_type="KIS")
        _log.info(f"Broker Config: {broker_config.broker_type}_{broker_config.trading_mode}")
        _log.info(f"Base URL: {broker_config.base_url}")
        _log.info(f"Account: {broker_config.account_no}")

        # Import KIS components
        from runtime.broker.kis.kis_client import KISClient
        from runtime.broker.adapters.kis_adapter import KISOrderAdapter

        # Create client
        client = KISClient(
            app_key=broker_config.app_key,
            app_secret=broker_config.app_secret,
            base_url=broker_config.base_url,
            account_no=broker_config.account_no,
            acnt_prdt_cd=broker_config.acnt_prdt_cd,
            trading_mode=broker_config.trading_mode,
        )
        _log.info("KISClient initialized successfully")

        # Create adapter
        adapter = KISOrderAdapter(
            client=client,
            acnt_no=broker_config.account_no,
            acnt_prdt_cd=broker_config.acnt_prdt_cd,
        )
        _log.info("KISOrderAdapter initialized successfully")

        # Create test order (Samsung Electronics 삼성전자 005930)
        # MARKET BUY order for 1 share in VTS mode
        _log.info("")
        _log.info("Creating test order: BUY 005930 (Samsung) x 1 share (MARKET)")
        order_request = OrderRequest(
            symbol="005930",
            side=OrderSide.BUY,
            qty=1,
            order_type=OrderType.MARKET,
            limit_price=None,
            dry_run=False,
        )

        # Place order
        _log.info("Placing order via KISOrderAdapter...")
        order_response = adapter.place_order(order_request)

        # Check response
        _log.info("")
        _log.info("Order Response:")
        _log.info(f"  Status: {order_response.status}")
        _log.info(f"  Broker Order ID: {order_response.broker_order_id}")
        _log.info(f"  Message: {order_response.message}")
        _log.info(f"  Raw Response: {order_response.raw}")

        # Verify success
        from runtime.execution.models.order_response import OrderStatus
        if order_response.status == OrderStatus.ACCEPTED:
            _log.info("")
            _log.info("=" * 60)
            _log.info("KIS Order Placement: SUCCESS ✓")
            _log.info(f"Order ID: {order_response.broker_order_id}")
            _log.info("=" * 60)
            return True
        elif order_response.status == OrderStatus.REJECTED:
            _log.warning("")
            _log.warning("=" * 60)
            _log.warning("KIS Order Placement: REJECTED")
            _log.warning(f"Reason: {order_response.message}")
            _log.warning("=" * 60)
            return False
        else:
            _log.warning("")
            _log.warning("=" * 60)
            _log.warning(f"KIS Order Placement: UNKNOWN STATUS ({order_response.status})")
            _log.warning("=" * 60)
            return False

    except Exception as e:
        _log.error(f"KIS Order Placement FAILED: {e}", exc_info=True)
        _log.info("=" * 60)
        return False


def main():
    """Run KIS order placement test"""
    # Load .env file
    env_path = _ROOT / "config" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        _log.info(f".env file loaded from {env_path}")
    else:
        _log.warning(f".env file not found at {env_path}")

    # Run test
    _log.info("")
    success = test_kis_order_placement()

    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
