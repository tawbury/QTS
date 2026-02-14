"""
Broker API Authentication Test Script

Tests authentication for both KIS and Kiwoom brokers without requiring
full ETEDA pipeline initialization.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
_ROOT = Path(__file__).resolve().parents[2]  # tests/integration -> prj_qts
sys.path.insert(0, str(_ROOT / "src"))

from dotenv import load_dotenv
from src.qts.core.config.env_loader import get_broker_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_log = logging.getLogger(__name__)


def test_kis_auth():
    """Test KIS API authentication"""
    _log.info("=" * 60)
    _log.info("KIS Authentication Test")
    _log.info("=" * 60)

    try:
        # Load broker config
        broker_config = get_broker_config(broker_type="KIS")
        _log.info(f"Broker Config: {broker_config.broker_type}_{broker_config.trading_mode}")
        _log.info(f"Base URL: {broker_config.base_url}")
        _log.info(f"Account: {broker_config.account_no}")

        # Import KISClient
        from src.provider.clients.broker.kis.kis_client import KISClient

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

        # Test OAuth2.0 token acquisition
        _log.info("Testing OAuth2.0 token acquisition...")
        token = client._get_access_token()
        _log.info(f"✓ OAuth2.0 token acquired: {token[:20]}...")

        # Test Hashkey generation
        _log.info("Testing Hashkey generation...")
        test_body = {
            "CANO": broker_config.account_no,
            "ACNT_PRDT_CD": broker_config.acnt_prdt_cd,
            "PDNO": "005930",
            "ORD_QTY": "10",
        }
        hashkey = client._get_hashkey(test_body)
        _log.info(f"✓ Hashkey generated: {hashkey[:20]}...")

        _log.info("=" * 60)
        _log.info("KIS Authentication: SUCCESS")
        _log.info("=" * 60)
        return True

    except Exception as e:
        _log.error(f"KIS Authentication FAILED: {e}", exc_info=True)
        _log.info("=" * 60)
        return False


def test_kiwoom_auth():
    """Test Kiwoom API authentication"""
    _log.info("=" * 60)
    _log.info("Kiwoom Authentication Test")
    _log.info("=" * 60)

    try:
        # Load broker config
        broker_config = get_broker_config(broker_type="KIWOOM")
        _log.info(f"Broker Config: {broker_config.broker_type}_{broker_config.trading_mode}")
        _log.info(f"Base URL: {broker_config.base_url}")
        _log.info(f"Account: {broker_config.account_no}")

        # Import KiwoomClient
        from src.provider.clients.broker.kiwoom.kiwoom_client import KiwoomClient

        # Create client
        client = KiwoomClient(
            app_key=broker_config.app_key,
            app_secret=broker_config.app_secret,
            base_url=broker_config.base_url,
            account_no=broker_config.account_no,
            acnt_prdt_cd=broker_config.acnt_prdt_cd,
        )
        _log.info("KiwoomClient initialized successfully")

        # Test OAuth2.0 token acquisition
        _log.info("Testing OAuth2.0 token acquisition...")
        token = client._get_access_token()
        _log.info(f"✓ OAuth2.0 token acquired: {token[:20]}...")

        # Test signature generation
        _log.info("Testing HMAC-SHA256 signature generation...")
        test_path = "/api/v1/test"
        test_body = {"symbol": "005930", "qty": 10}
        signature = client._make_signature(test_path, test_body)
        _log.info(f"✓ Signature generated: {signature[:20]}...")

        _log.info("=" * 60)
        _log.info("Kiwoom Authentication: SUCCESS")
        _log.info("=" * 60)
        return True

    except Exception as e:
        _log.error(f"Kiwoom Authentication FAILED: {e}", exc_info=True)
        _log.info("=" * 60)
        return False


def main():
    """Run authentication tests for both brokers"""
    # Load .env file
    env_path = _ROOT / "config" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        _log.info(f".env file loaded from {env_path}")
    else:
        _log.warning(f".env file not found at {env_path}")

    results = {}

    # Test KIS
    _log.info("")
    results["KIS"] = test_kis_auth()

    # Test Kiwoom
    _log.info("")
    results["Kiwoom"] = test_kiwoom_auth()

    # Summary
    _log.info("")
    _log.info("=" * 60)
    _log.info("AUTHENTICATION TEST SUMMARY")
    _log.info("=" * 60)
    for broker, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        _log.info(f"{broker:10s}: {status}")
    _log.info("=" * 60)

    # Exit code
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
