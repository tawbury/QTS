"""
Config Validator 단위 테스트

목적: UnifiedConfig 검증 로직 테스트
"""

import pytest

from runtime.config.config_models import UnifiedConfig
from runtime.config.config_validator import (
    validate_config,
    validate_config_with_fallback,
    ConfigValidationError,
    REQUIRED_KEYS,
)


class TestConfigValidator:
    """Config Validator 테스트"""

    def test_validate_config_with_all_keys(self):
        """모든 필수 키가 있는 경우 검증 통과"""
        config_map = {f"SYSTEM.TEST.{key}": "value" for key in REQUIRED_KEYS}
        config = UnifiedConfig(config_map=config_map, metadata={})

        # 예외 발생하지 않아야 함
        validate_config(config)

    def test_validate_config_missing_keys(self):
        """필수 키가 누락된 경우 예외 발생"""
        config_map = {
            "SYSTEM.TEST.INTERVAL_MS": "1000",
            # 나머지 키 누락
        }
        config = UnifiedConfig(config_map=config_map, metadata={})

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)

        # 에러 메시지에 누락된 키 포함
        assert "Missing required config keys" in str(exc_info.value)

    def test_validate_config_with_custom_keys(self):
        """사용자 정의 필수 키 검증"""
        config_map = {
            "SYSTEM.TEST.CUSTOM_KEY_1": "value1",
            "SYSTEM.TEST.CUSTOM_KEY_2": "value2",
        }
        config = UnifiedConfig(config_map=config_map, metadata={})

        custom_keys = {"CUSTOM_KEY_1", "CUSTOM_KEY_2"}

        # 예외 발생하지 않아야 함
        validate_config(config, required_keys=custom_keys)

    def test_validate_config_with_fallback_true(self):
        """fallback 버전 - 검증 성공"""
        config_map = {f"SYSTEM.TEST.{key}": "value" for key in REQUIRED_KEYS}
        config = UnifiedConfig(config_map=config_map, metadata={})

        assert validate_config_with_fallback(config) is True

    def test_validate_config_with_fallback_false(self):
        """fallback 버전 - 검증 실패"""
        config_map = {"SYSTEM.TEST.INTERVAL_MS": "1000"}
        config = UnifiedConfig(config_map=config_map, metadata={})

        assert validate_config_with_fallback(config) is False

    def test_get_flat_hierarchical_fallback(self):
        """get_flat()의 계층적 fallback 동작 검증"""
        config_map = {
            "SYSTEM.LOOP.INTERVAL_MS": "1000",
            "SYSTEM.EXECUTION.RUN_MODE": "PAPER",
            "flat_key": "flat_value",
        }
        config = UnifiedConfig(config_map=config_map, metadata={})

        # 계층적 키 조회
        assert config.get_flat("INTERVAL_MS") == "1000"
        assert config.get_flat("RUN_MODE") == "PAPER"

        # Flat 키 조회
        assert config.get_flat("flat_key") == "flat_value"

        # 존재하지 않는 키
        assert config.get_flat("NONEXISTENT") is None
        assert config.get_flat("NONEXISTENT", "default") == "default"

    def test_validate_empty_config(self):
        """빈 Config 검증 - 모든 키 누락"""
        config = UnifiedConfig(config_map={}, metadata={})

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)

        assert "Missing required config keys" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
