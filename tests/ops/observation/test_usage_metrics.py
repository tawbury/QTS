# tests/ops/observation/test_usage_metrics.py

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ops.observer.usage_metrics import (
    UsageMetricsConfig,
    WindowMetrics,
    UsageMetricsCollector,
    create_usage_metrics_collector,
    create_default_usage_metrics,
)


class TestUsageMetricsConfig:
    """Test usage metrics configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = UsageMetricsConfig()
        
        assert config.window_ms == 60_000
        assert config.enable_metrics is True
        assert config.output_format == 'json'
        assert config.metrics_file is None
        assert config.max_history_windows == 1440
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = UsageMetricsConfig(
            window_ms=30_000,
            enable_metrics=False,
            output_format='structured_log',
            metrics_file='/tmp/metrics.jsonl',
            max_history_windows=720,
        )
        
        assert config.window_ms == 30_000
        assert config.enable_metrics is False
        assert config.output_format == 'structured_log'
        assert config.metrics_file == '/tmp/metrics.jsonl'
        assert config.max_history_windows == 720


class TestWindowMetrics:
    """Test window metrics data structure."""
    
    def test_empty_metrics(self):
        """Test metrics with no data."""
        metrics = WindowMetrics(
            window_start_ms=1000,
            window_end_ms=61000,
        )
        
        assert metrics.snapshots_count == 0
        assert metrics.latency_sum_ms == 0.0
        assert metrics.latency_count == 0
        assert metrics.avg_latency_ms == 0.0
        assert metrics.min_latency_ms is None
        assert metrics.max_latency_ms is None
    
    def test_latency_tracking(self):
        """Test latency measurement tracking."""
        metrics = WindowMetrics(
            window_start_ms=1000,
            window_end_ms=61000,
        )
        
        # Add some latency measurements
        metrics.add_latency(10.5)
        metrics.add_latency(15.2)
        metrics.add_latency(8.7)
        
        assert metrics.latency_count == 3
        assert metrics.latency_sum_ms == 34.4
        assert metrics.avg_latency_ms == pytest.approx(11.47, rel=1e-2)
        assert metrics.min_latency_ms == 8.7
        assert metrics.max_latency_ms == 15.2
    
    def test_buffer_depth_tracking(self):
        """Test buffer depth measurement tracking."""
        metrics = WindowMetrics(
            window_start_ms=1000,
            window_end_ms=61000,
        )
        
        # Add some buffer depth measurements
        metrics.add_buffer_depth(5)
        metrics.add_buffer_depth(10)
        metrics.add_buffer_depth(3)
        
        assert metrics.buffer_depth_count == 3
        assert metrics.buffer_depth_sum == 18.0
        assert metrics.avg_buffer_depth == 6.0
        assert metrics.max_buffer_depth == 10
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = WindowMetrics(
            window_start_ms=1000,
            window_end_ms=61000,
        )
        
        metrics.snapshots_count = 5
        metrics.snapshots_tick_count = 2
        metrics.add_latency(10.0)
        metrics.add_buffer_depth(5)
        metrics.flush_count = 3
        metrics.files_rotated = 1
        metrics.bytes_written = 1024
        metrics.records_written = 5
        
        result = metrics.to_dict()
        
        assert result['window_start_ms'] == 1000
        assert result['window_end_ms'] == 61000
        assert result['snapshots_per_minute'] == 5
        assert result['snapshots_tick_per_minute'] == 2
        assert result['snapshots_loop_per_minute'] == 3  # 5 - 2
        assert result['avg_latency_ms'] == 10.0
        assert result['min_latency_ms'] == 10.0
        assert result['max_latency_ms'] == 10.0
        assert result['flush_count_per_window'] == 3
        assert result['avg_buffer_depth'] == 5.0
        assert result['max_buffer_depth'] == 5
        assert result['files_rotated_per_window'] == 1
        assert result['bytes_written_per_window'] == 1024
        assert result['records_written_per_window'] == 5


class TestUsageMetricsCollector:
    """Test usage metrics collector."""
    
    def test_collector_initialization(self):
        """Test collector initialization."""
        config = UsageMetricsConfig(window_ms=10_000)  # 10 second window
        collector = UsageMetricsCollector(config)
        
        assert collector._config.window_ms == 10_000
        assert collector._current_window is None
        assert len(collector._history) == 0
        assert collector._total_snapshots == 0
        assert collector._total_bytes_written == 0
    
    def test_disabled_metrics(self):
        """Test behavior when metrics are disabled."""
        config = UsageMetricsConfig(enable_metrics=False)
        collector = UsageMetricsCollector(config)
        
        # These should do nothing
        collector.record_snapshot(is_tick=False, latency_ms=10.0)
        collector.record_flush(buffer_depth=5, bytes_written=100, records_written=1)
        collector.record_rotation(files_rotated=1)
        
        # Should return disabled status
        current_metrics = collector.get_current_metrics()
        assert current_metrics['metrics_enabled'] is False
    
    def test_snapshot_recording(self):
        """Test snapshot recording."""
        config = UsageMetricsConfig(window_ms=10_000)
        collector = UsageMetricsCollector(config)
        
        # Record some snapshots
        collector.record_snapshot(is_tick=False, latency_ms=10.5)
        collector.record_snapshot(is_tick=True, latency_ms=8.2)
        collector.record_snapshot(is_tick=False, latency_ms=12.1)
        
        current_metrics = collector.get_current_metrics()
        
        assert current_metrics['metrics_enabled'] is True
        assert current_metrics['total_snapshots'] == 3
        assert current_metrics['current_window']['snapshots_per_minute'] == 3
        assert current_metrics['current_window']['snapshots_tick_per_minute'] == 1
        assert current_metrics['current_window']['snapshots_loop_per_minute'] == 2
        assert current_metrics['current_window']['avg_latency_ms'] == pytest.approx(10.27, rel=1e-2)
    
    def test_flush_recording(self):
        """Test flush operation recording."""
        config = UsageMetricsConfig(window_ms=10_000)
        collector = UsageMetricsCollector(config)
        
        # Record some flush operations
        collector.record_flush(buffer_depth=5, bytes_written=1024, records_written=10)
        collector.record_flush(buffer_depth=8, bytes_written=2048, records_written=20)
        
        current_metrics = collector.get_current_metrics()
        
        assert current_metrics['total_bytes_written'] == 3072
        assert current_metrics['current_window']['flush_count_per_window'] == 2
        assert current_metrics['current_window']['avg_buffer_depth'] == 6.5
        assert current_metrics['current_window']['max_buffer_depth'] == 8
        assert current_metrics['current_window']['bytes_written_per_window'] == 3072
        assert current_metrics['current_window']['records_written_per_window'] == 30
    
    def test_rotation_recording(self):
        """Test rotation recording."""
        config = UsageMetricsConfig(window_ms=10_000)
        collector = UsageMetricsCollector(config)
        
        # Record rotation
        collector.record_rotation(files_rotated=2)
        
        current_metrics = collector.get_current_metrics()
        
        assert current_metrics['current_window']['files_rotated_per_window'] == 2
    
    def test_window_transition(self):
        """Test window transition behavior."""
        config = UsageMetricsConfig(window_ms=100)  # Very short window for testing
        collector = UsageMetricsCollector(config)
        
        # Record in first window
        collector.record_snapshot(is_tick=False, latency_ms=10.0)
        
        # Wait for window to pass
        time.sleep(0.15)  # 150ms > 100ms window
        
        # Record in new window
        collector.record_snapshot(is_tick=True, latency_ms=8.0)
        
        current_metrics = collector.get_current_metrics()
        
        # Should have history from previous window
        assert len(collector._history) == 1
        assert current_metrics['history_windows_count'] == 1
        
        # Current window should only have the second snapshot
        assert current_metrics['current_window']['snapshots_per_minute'] == 1
        assert current_metrics['current_window']['snapshots_tick_per_minute'] == 1
    
    def test_metrics_file_output(self):
        """Test writing metrics to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            metrics_file = Path(temp_dir) / "test_metrics.jsonl"
            config = UsageMetricsConfig(
                window_ms=10_000,
                metrics_file=str(metrics_file)
            )
            collector = UsageMetricsCollector(config)
            
            # Record some activity
            collector.record_snapshot(is_tick=False, latency_ms=10.0)
            collector.record_flush(buffer_depth=5, bytes_written=100, records_written=1)
            
            # Force window completion by creating a new collector with future time
            with patch('ops.observer.usage_metrics.utc_now_ms') as mock_time:
                # Advance time by more than window size
                mock_time.return_value = int(time.time() * 1000) + 15_000
                
                # Trigger window transition
                collector.record_snapshot(is_tick=False, latency_ms=8.0)
            
            # Check that metrics file was created and contains data
            assert metrics_file.exists()
            
            with open(metrics_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 1
                
                # Parse first line (window summary)
                first_line_data = json.loads(lines[0])
                assert 'metric_type' in first_line_data
                assert first_line_data['metric_type'] == 'usage_window_summary'
                assert 'snapshots_per_minute' in first_line_data
    
    def test_finalize(self):
        """Test finalization of metrics collection."""
        config = UsageMetricsConfig(window_ms=10_000)
        collector = UsageMetricsCollector(config)
        
        # Record some activity
        collector.record_snapshot(is_tick=False, latency_ms=10.0)
        collector.record_flush(buffer_depth=5, bytes_written=100, records_written=1)
        
        # Finalize
        collector.finalize()
        
        # Should have moved current window to history
        assert len(collector._history) == 1
        assert collector._current_window is None
    
    def test_factory_functions(self):
        """Test factory functions."""
        # Test create_usage_metrics_collector
        collector1 = create_usage_metrics_collector(window_ms=30_000)
        assert collector1._config.window_ms == 30_000
        assert collector1._config.enable_metrics is True
        
        # Test create_usage_metrics_collector with custom settings
        collector2 = create_usage_metrics_collector(
            window_ms=15_000,
            enable_metrics=False,
            output_format='structured_log'
        )
        assert collector2._config.window_ms == 15_000
        assert collector2._config.enable_metrics is False
        assert collector2._config.output_format == 'structured_log'
        
        # Test create_default_usage_metrics
        collector3 = create_default_usage_metrics()
        assert collector3._config.window_ms == 60_000
        assert collector3._config.enable_metrics is True
        assert collector3._config.output_format == 'json'


class TestUsageMetricsIntegration:
    """Test usage metrics integration scenarios."""
    
    def test_high_frequency_snapshots(self):
        """Test metrics under high-frequency snapshot generation."""
        config = UsageMetricsConfig(window_ms=10_000)
        collector = UsageMetricsCollector(config)
        
        # Simulate high-frequency snapshots
        for i in range(100):
            is_tick = i % 3 == 0  # Every 3rd is a tick
            latency = 5.0 + (i % 10)  # Variable latency 5-14ms
            collector.record_snapshot(is_tick=is_tick, latency_ms=latency)
        
        current_metrics = collector.get_current_metrics()
        
        assert current_metrics['total_snapshots'] == 100
        assert current_metrics['current_window']['snapshots_per_minute'] == 100
        
        # Should have both tick and loop snapshots
        assert current_metrics['current_window']['snapshots_tick_per_minute'] > 0
        assert current_metrics['current_window']['snapshots_loop_per_minute'] > 0
        
        # Latency should be calculated
        assert current_metrics['current_window']['avg_latency_ms'] > 0
        assert current_metrics['current_window']['min_latency_ms'] >= 5.0
        assert current_metrics['current_window']['max_latency_ms'] <= 14.0
    
    def test_buffer_activity_simulation(self):
        """Test metrics during buffer activity simulation."""
        config = UsageMetricsConfig(window_ms=10_000)
        collector = UsageMetricsCollector(config)
        
        # Simulate buffer activity
        buffer_depths = [1, 3, 5, 8, 12, 7, 4, 2, 6, 9]
        bytes_per_flush = [512, 1024, 768, 1536, 2048, 1280, 896, 640, 1152, 1792]
        
        for depth, bytes_written in zip(buffer_depths, bytes_per_flush):
            records_written = bytes_written // 100  # Assume ~100 bytes per record
            collector.record_flush(
                buffer_depth=depth,
                bytes_written=bytes_written,
                records_written=records_written
            )
        
        current_metrics = collector.get_current_metrics()
        
        assert current_metrics['total_bytes_written'] == sum(bytes_per_flush)
        assert current_metrics['current_window']['flush_count_per_window'] == len(buffer_depths)
        assert current_metrics['current_window']['avg_buffer_depth'] == sum(buffer_depths) / len(buffer_depths)
        assert current_metrics['current_window']['max_buffer_depth'] == max(buffer_depths)
        assert current_metrics['current_window']['bytes_written_per_window'] == sum(bytes_per_flush)
    
    def test_rotation_activity(self):
        """Test metrics during rotation activity."""
        config = UsageMetricsConfig(window_ms=10_000)
        collector = UsageMetricsCollector(config)
        
        # Simulate rotation events
        rotation_events = [1, 2, 1, 3, 1, 2]  # Files rotated per event
        
        for files_rotated in rotation_events:
            collector.record_rotation(files_rotated=files_rotated)
        
        current_metrics = collector.get_current_metrics()
        
        assert current_metrics['current_window']['files_rotated_per_window'] == sum(rotation_events)
    
    def test_comprehensive_workload_simulation(self):
        """Test metrics under comprehensive workload simulation."""
        config = UsageMetricsConfig(window_ms=10_000)
        collector = UsageMetricsCollector(config)
        
        # Simulate mixed workload
        for cycle in range(5):
            # Snapshots in this cycle
            for i in range(20):
                is_tick = i % 4 == 0  # Every 4th is tick
                latency = 3.0 + (i % 8)  # 3-10ms latency
                collector.record_snapshot(is_tick=is_tick, latency_ms=latency)
            
            # Buffer flushes in this cycle
            for i in range(3):
                buffer_depth = 2 + i * 2
                bytes_written = 500 + i * 200
                records_written = bytes_written // 80
                collector.record_flush(
                    buffer_depth=buffer_depth,
                    bytes_written=bytes_written,
                    records_written=records_written
                )
            
            # Occasional rotation
            if cycle % 2 == 0:
                collector.record_rotation(files_rotated=1)
        
        current_metrics = collector.get_current_metrics()
        
        # Verify comprehensive metrics
        assert current_metrics['total_snapshots'] == 100  # 5 cycles * 20 snapshots
        assert current_metrics['current_window']['snapshots_per_minute'] == 100
        assert current_metrics['current_window']['flush_count_per_window'] == 15  # 5 cycles * 3 flushes
        assert current_metrics['current_window']['files_rotated_per_window'] == 3  # 3 rotation events
        assert current_metrics['total_bytes_written'] > 0
        assert current_metrics['current_window']['avg_latency_ms'] > 0
        assert current_metrics['current_window']['avg_buffer_depth'] > 0


if __name__ == "__main__":
    pytest.main([__file__])
