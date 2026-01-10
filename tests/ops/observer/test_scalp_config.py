"""
test_scalp_config.py

Unit tests for scalp extension configuration management.

ROLE & BOUNDARY DECLARATION:
- THIS IS NOT Observer-Core testing
- Layer: Unit testing for configuration management
- Ownership: Observer configuration testing
- Access: Test suite ONLY
- Must NOT test: Observer-Core behavior, strategy logic, decision flow

This test validates configuration loading and validation without affecting
Observer behavior or introducing decision logic.

SAFETY CONFIRMATION:
- Tests do NOT affect Observer responsibilities
- Tests do NOT introduce decision logic
- Tests do NOT alter Snapshot/PatternRecord
- Tests do NOT enable Scalp adaptive behavior

Constraints from Observer_Architecture.md:
- Observer receives configuration for session ID, runtime mode, EventBus sink
- Observer does NOT load strategy configurations

Constraints from observer_scalp_task_08_testing_infrastructure.md:
- Unit tests for new configuration parameters
- Additive test changes only
- No strategy testing in Observer tests
"""

import unittest
from unittest.mock import patch
import logging

from src.ops.observer.scalp_config import (
    HybridTriggerConfig,
    BufferConfig,
    RotationConfig,
    PerformanceConfig,
    ScalpExtensionConfig,
    ConfigValidator,
    load_config_from_dict,
    get_default_config
)


class TestHybridTriggerConfig(unittest.TestCase):
    """Test HybridTriggerConfig dataclass."""
    
    def test_default_values(self):
        """Test HybridTriggerConfig has correct defaults."""
        config = HybridTriggerConfig()
        
        self.assertFalse(config.enabled)
        self.assertEqual(config.tick_source, "websocket")
        self.assertEqual(config.min_interval_ms, 10.0)
        self.assertEqual(config.max_interval_ms, 1000.0)
    
    def test_custom_values(self):
        """Test HybridTriggerConfig accepts custom values."""
        config = HybridTriggerConfig(
            enabled=True,
            tick_source="rest",
            min_interval_ms=5.0,
            max_interval_ms=500.0
        )
        
        self.assertTrue(config.enabled)
        self.assertEqual(config.tick_source, "rest")
        self.assertEqual(config.min_interval_ms, 5.0)
        self.assertEqual(config.max_interval_ms, 500.0)
    
    def test_immutability(self):
        """Test HybridTriggerConfig is immutable (frozen)."""
        config = HybridTriggerConfig()
        
        with self.assertRaises(AttributeError):
            config.enabled = True


class TestBufferConfig(unittest.TestCase):
    """Test BufferConfig dataclass."""
    
    def test_default_values(self):
        """Test BufferConfig has correct defaults."""
        config = BufferConfig()
        
        self.assertEqual(config.flush_interval_ms, 1000.0)
        self.assertEqual(config.max_buffer_size, 10000)
        self.assertTrue(config.enable_buffering)
    
    def test_custom_values(self):
        """Test BufferConfig accepts custom values."""
        config = BufferConfig(
            flush_interval_ms=500.0,
            max_buffer_size=5000,
            enable_buffering=False
        )
        
        self.assertEqual(config.flush_interval_ms, 500.0)
        self.assertEqual(config.max_buffer_size, 5000)
        self.assertFalse(config.enable_buffering)


class TestRotationConfig(unittest.TestCase):
    """Test RotationConfig dataclass."""
    
    def test_default_values(self):
        """Test RotationConfig has correct defaults."""
        config = RotationConfig()
        
        self.assertFalse(config.enabled)
        self.assertEqual(config.window_ms, 3600000)  # 1 hour
        self.assertEqual(config.max_files, 24)
    
    def test_custom_values(self):
        """Test RotationConfig accepts custom values."""
        config = RotationConfig(
            enabled=True,
            window_ms=1800000,  # 30 minutes
            max_files=48
        )
        
        self.assertTrue(config.enabled)
        self.assertEqual(config.window_ms, 1800000)
        self.assertEqual(config.max_files, 48)


class TestPerformanceConfig(unittest.TestCase):
    """Test PerformanceConfig dataclass."""
    
    def test_default_values(self):
        """Test PerformanceConfig has correct defaults."""
        config = PerformanceConfig()
        
        self.assertTrue(config.enabled)
        self.assertEqual(config.metrics_history_size, 1000)
    
    def test_custom_values(self):
        """Test PerformanceConfig accepts custom values."""
        config = PerformanceConfig(
            enabled=False,
            metrics_history_size=500
        )
        
        self.assertFalse(config.enabled)
        self.assertEqual(config.metrics_history_size, 500)


class TestScalpExtensionConfig(unittest.TestCase):
    """Test ScalpExtensionConfig dataclass."""
    
    def test_default_values(self):
        """Test ScalpExtensionConfig has correct defaults."""
        config = ScalpExtensionConfig()
        
        # Check nested configs have defaults
        self.assertFalse(config.hybrid_trigger.enabled)
        self.assertEqual(config.buffer.flush_interval_ms, 1000.0)
        self.assertFalse(config.rotation.enabled)
        self.assertTrue(config.performance.enabled)
    
    def test_custom_values(self):
        """Test ScalpExtensionConfig accepts custom nested configs."""
        hybrid = HybridTriggerConfig(enabled=True)
        buffer = BufferConfig(flush_interval_ms=500.0)
        rotation = RotationConfig(enabled=True)
        performance = PerformanceConfig(enabled=False)
        
        config = ScalpExtensionConfig(
            hybrid_trigger=hybrid,
            buffer=buffer,
            rotation=rotation,
            performance=performance
        )
        
        self.assertTrue(config.hybrid_trigger.enabled)
        self.assertEqual(config.buffer.flush_interval_ms, 500.0)
        self.assertTrue(config.rotation.enabled)
        self.assertFalse(config.performance.enabled)


class TestConfigValidator(unittest.TestCase):
    """Test ConfigValidator class."""
    
    def test_validate_hybrid_trigger_success(self):
        """Test successful hybrid trigger validation."""
        config = HybridTriggerConfig(
            min_interval_ms=10.0,
            max_interval_ms=100.0,
            tick_source="websocket"
        )
        
        # Should not raise exception
        ConfigValidator.validate_hybrid_trigger(config)
    
    def test_validate_hybrid_trigger_invalid_interval(self):
        """Test hybrid trigger validation with invalid interval."""
        config = HybridTriggerConfig(min_interval_ms=-5.0)
        
        with self.assertRaises(ValueError) as cm:
            ConfigValidator.validate_hybrid_trigger(config)
        self.assertIn("must be positive", str(cm.exception))
    
    def test_validate_hybrid_trigger_invalid_range(self):
        """Test hybrid trigger validation with invalid range."""
        config = HybridTriggerConfig(
            min_interval_ms=100.0,
            max_interval_ms=50.0  # Less than min
        )
        
        with self.assertRaises(ValueError) as cm:
            ConfigValidator.validate_hybrid_trigger(config)
        self.assertIn("greater than min_interval_ms", str(cm.exception))
    
    def test_validate_hybrid_trigger_unknown_source(self):
        """Test hybrid trigger validation with unknown tick source."""
        config = HybridTriggerConfig(tick_source="unknown")
        
        with patch('src.ops.observer.scalp_config.logger') as mock_logger:
            # Should not raise exception, but should log warning
            ConfigValidator.validate_hybrid_trigger(config)
            mock_logger.warning.assert_called_with("Unknown tick_source: unknown")
    
    def test_validate_buffer_success(self):
        """Test successful buffer validation."""
        config = BufferConfig(
            flush_interval_ms=1000.0,
            max_buffer_size=10000
        )
        
        # Should not raise exception
        ConfigValidator.validate_buffer(config)
    
    def test_validate_buffer_invalid_flush_interval(self):
        """Test buffer validation with invalid flush interval."""
        config = BufferConfig(flush_interval_ms=-100.0)
        
        with self.assertRaises(ValueError) as cm:
            ConfigValidator.validate_buffer(config)
        self.assertIn("must be positive", str(cm.exception))
    
    def test_validate_buffer_invalid_size(self):
        """Test buffer validation with invalid size."""
        config = BufferConfig(max_buffer_size=0)
        
        with self.assertRaises(ValueError) as cm:
            ConfigValidator.validate_buffer(config)
        self.assertIn("must be positive", str(cm.exception))
    
    def test_validate_rotation_success(self):
        """Test successful rotation validation."""
        config = RotationConfig(
            enabled=True,
            window_ms=3600000,
            max_files=24
        )
        
        # Should not raise exception
        ConfigValidator.validate_rotation(config)
    
    def test_validate_rotation_enabled_no_window(self):
        """Test rotation validation with enabled but no window."""
        config = RotationConfig(enabled=True, window_ms=0)
        
        with self.assertRaises(ValueError) as cm:
            ConfigValidator.validate_rotation(config)
        self.assertIn("must be positive when enabled", str(cm.exception))
    
    def test_validate_rotation_invalid_max_files(self):
        """Test rotation validation with invalid max files."""
        config = RotationConfig(max_files=0)
        
        with self.assertRaises(ValueError) as cm:
            ConfigValidator.validate_rotation(config)
        self.assertIn("must be positive", str(cm.exception))
    
    def test_validate_performance_success(self):
        """Test successful performance validation."""
        config = PerformanceConfig(metrics_history_size=1000)
        
        # Should not raise exception
        ConfigValidator.validate_performance(config)
    
    def test_validate_performance_invalid_history_size(self):
        """Test performance validation with invalid history size."""
        config = PerformanceConfig(metrics_history_size=-100)
        
        with self.assertRaises(ValueError) as cm:
            ConfigValidator.validate_performance(config)
        self.assertIn("must be positive", str(cm.exception))
    
    def test_validate_all_success(self):
        """Test successful validation of all sections."""
        config = ScalpExtensionConfig()
        
        # Should not raise exception
        ConfigValidator.validate_all(config)
    
    def test_validate_all_failure(self):
        """Test validation failure propagates from section."""
        # Create invalid config
        hybrid = HybridTriggerConfig(min_interval_ms=-5.0)
        config = ScalpExtensionConfig(hybrid_trigger=hybrid)
        
        with self.assertRaises(ValueError):
            ConfigValidator.validate_all(config)


class TestConfigLoading(unittest.TestCase):
    """Test configuration loading functions."""
    
    def test_load_config_from_dict_none(self):
        """Test loading config with None dict (defaults)."""
        config = load_config_from_dict(None)
        
        # Should have default values
        self.assertIsInstance(config, ScalpExtensionConfig)
        self.assertFalse(config.hybrid_trigger.enabled)
        self.assertEqual(config.buffer.flush_interval_ms, 1000.0)
    
    def test_load_config_from_dict_empty(self):
        """Test loading config with empty dict (defaults)."""
        config = load_config_from_dict({})
        
        # Should have default values
        self.assertIsInstance(config, ScalpExtensionConfig)
        self.assertFalse(config.hybrid_trigger.enabled)
    
    def test_load_config_from_dict_partial(self):
        """Test loading config with partial dict."""
        config_dict = {
            "hybrid_trigger": {
                "enabled": True,
                "tick_source": "rest"
            },
            "buffer": {
                "flush_interval_ms": 500.0
            }
            # rotation and performance should use defaults
        }
        
        config = load_config_from_dict(config_dict)
        
        # Check custom values
        self.assertTrue(config.hybrid_trigger.enabled)
        self.assertEqual(config.hybrid_trigger.tick_source, "rest")
        self.assertEqual(config.buffer.flush_interval_ms, 500.0)
        
        # Check default values for unspecified sections
        self.assertFalse(config.rotation.enabled)
        self.assertTrue(config.performance.enabled)
    
    def test_load_config_from_dict_full(self):
        """Test loading config with full dict."""
        config_dict = {
            "hybrid_trigger": {
                "enabled": True,
                "tick_source": "simulation",
                "min_interval_ms": 5.0,
                "max_interval_ms": 500.0
            },
            "buffer": {
                "flush_interval_ms": 200.0,
                "max_buffer_size": 5000,
                "enable_buffering": False
            },
            "rotation": {
                "enabled": True,
                "window_ms": 1800000,
                "max_files": 48
            },
            "performance": {
                "enabled": False,
                "metrics_history_size": 2000
            }
        }
        
        config = load_config_from_dict(config_dict)
        
        # Check all values
        self.assertTrue(config.hybrid_trigger.enabled)
        self.assertEqual(config.hybrid_trigger.tick_source, "simulation")
        self.assertEqual(config.hybrid_trigger.min_interval_ms, 5.0)
        self.assertEqual(config.hybrid_trigger.max_interval_ms, 500.0)
        
        self.assertEqual(config.buffer.flush_interval_ms, 200.0)
        self.assertEqual(config.buffer.max_buffer_size, 5000)
        self.assertFalse(config.buffer.enable_buffering)
        
        self.assertTrue(config.rotation.enabled)
        self.assertEqual(config.rotation.window_ms, 1800000)
        self.assertEqual(config.rotation.max_files, 48)
        
        self.assertFalse(config.performance.enabled)
        self.assertEqual(config.performance.metrics_history_size, 2000)
    
    def test_load_config_validation_error(self):
        """Test loading config with validation error falls back to defaults."""
        config_dict = {
            "hybrid_trigger": {
                "min_interval_ms": -5.0  # Invalid
            }
        }
        
        with patch('src.ops.observer.scalp_config.logger') as mock_logger:
            config = load_config_from_dict(config_dict)
            
            # Should log error and use defaults
            mock_logger.error.assert_called()
            mock_logger.warning.assert_called_with("Using default configuration due to loading error")
            
            # Should have default values
            self.assertFalse(config.hybrid_trigger.enabled)
    
    def test_get_default_config(self):
        """Test get_default_config function."""
        config1 = get_default_config()
        config2 = get_default_config()
        
        # Should return equivalent configs
        self.assertEqual(config1.hybrid_trigger.enabled, config2.hybrid_trigger.enabled)
        self.assertEqual(config1.buffer.flush_interval_ms, config2.buffer.flush_interval_ms)


if __name__ == '__main__':
    unittest.main()
