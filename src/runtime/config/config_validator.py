"""
Config Validator

UnifiedConfig 객체가 필수 키들을 포함하는지 검증합니다.
"""

from __future__ import annotations

from typing import List, Optional, Set
from .config_models import UnifiedConfig


# 필수 Config 키 정의 (get_flat()로 조회 가능해야 함)
REQUIRED_KEYS: Set[str] = {
    # Loop Control
    "INTERVAL_MS",
    "ERROR_BACKOFF_MS",
    "ERROR_BACKOFF_MAX_RETRIES",

    # Execution Mode
    "RUN_MODE",
    "LIVE_ENABLED",
    "trading_enabled",

    # Safety
    "PIPELINE_PAUSED",
    "KS_ENABLED",

    # Broker
    "BASE_EQUITY",
}


class ConfigValidationError(Exception):
    """Config validation failed"""
    pass


def validate_config(config: UnifiedConfig, required_keys: Optional[Set[str]] = None) -> None:
    """
    UnifiedConfig 검증.

    Args:
        config: 검증할 UnifiedConfig 인스턴스
        required_keys: 필수 키 집합 (None이면 REQUIRED_KEYS 사용)

    Raises:
        ConfigValidationError: 필수 키가 누락된 경우
    """
    keys_to_check = required_keys or REQUIRED_KEYS
    missing_keys: List[str] = []

    for key in keys_to_check:
        value = config.get_flat(key)
        if value is None:
            missing_keys.append(key)

    if missing_keys:
        raise ConfigValidationError(
            f"Missing required config keys: {', '.join(missing_keys)}"
        )


def validate_config_with_fallback(config: UnifiedConfig, required_keys: Optional[Set[str]] = None) -> bool:
    """
    UnifiedConfig 검증 (예외 발생하지 않음).

    Args:
        config: 검증할 UnifiedConfig 인스턴스
        required_keys: 필수 키 집합 (None이면 REQUIRED_KEYS 사용)

    Returns:
        bool: 검증 성공 여부
    """
    try:
        validate_config(config, required_keys)
        return True
    except ConfigValidationError:
        return False
