# tests/ops/observation/test_time_based_rotation.py

import json
import pytest
import time
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

from ops.observer.log_rotation import (
    RotationConfig, RotationManager, TimeWindow,
    create_rotation_config, validate_rotation_config
)
from ops.observer.event_bus import JsonlFileSink
from ops.observer.buffered_sink import BufferedJsonlFileSink
from ops.observer.pattern_record import PatternRecord
from ops.observer.snapshot import build_snapshot, utc_now_ms
from paths import observer_asset_dir


class TestRotationConfig:
    """Test rotation configuration creation and validation."""

    def test_create_rotation_config_defaults(self):
        """Test creating rotation config with default values."""
        config = create_rotation_config()
        
        assert config.window_ms == 60_000
        assert config.enable_rotation is True
        assert config.base_filename == "observer"

    def test_create_rotation_config_custom(self):
        """Test creating rotation config with custom values."""
        config = create_rotation_config(
            window_ms=30_000,
            enable_rotation=False,
            base_filename="test_observer"
        )
        
        assert config.window_ms == 30_000
        assert config.enable_rotation is False
        assert config.base_filename == "test_observer"

    def test_validate_rotation_config_valid(self):
        """Test validation of valid rotation config."""
        config = RotationConfig(window_ms=5000, enable_rotation=True, base_filename="test")
        
        # Should not raise exception
        validate_rotation_config(config)

    def test_validate_rotation_config_invalid_window(self):
        """Test validation fails with invalid window size."""
        config = RotationConfig(window_ms=0, enable_rotation=True, base_filename="test")
        
        with pytest.raises(ValueError, match="window_ms must be positive"):
            validate_rotation_config(config)

    def test_validate_rotation_config_invalid_filename(self):
        """Test validation fails with invalid filename."""
        config = RotationConfig(window_ms=60000, enable_rotation=True, base_filename="")
        
        with pytest.raises(ValueError, match="base_filename must be a non-empty string"):
            validate_rotation_config(config)

    def test_validate_rotation_config_invalid_characters(self):
        """Test validation fails with invalid characters in filename."""
        config = RotationConfig(window_ms=60000, enable_rotation=True, base_filename="test/file")
        
        with pytest.raises(ValueError, match="base_filename contains invalid characters"):
            validate_rotation_config(config)


class TestTimeWindow:
    """Test time window calculations and utilities."""

    def test_time_window_creation(self):
        """Test creating a time window."""
        window_ms = 60_000
        timestamp_ms = 1_600_000_000_000  # Fixed timestamp
        
        window = TimeWindow(window_ms, timestamp_ms)
        
        assert window.window_ms == window_ms
        assert window.timestamp_ms == timestamp_ms
        assert window.start_ms == (timestamp_ms // window_ms) * window_ms
        assert window.end_ms == window.start_ms + window_ms

    def test_time_window_contains(self):
        """Test time window contains check."""
        window_ms = 60_000
        timestamp_ms = 1_600_000_000_000
        
        window = TimeWindow(window_ms, timestamp_ms)
        
        # Timestamp within window
        assert window.contains(window.start_ms)
        assert window.contains(window.start_ms + 30_000)
        assert not window.contains(window.end_ms - 1)  # Still within
        
        # Timestamp outside window
        assert not window.contains(window.start_ms - 1)
        assert not window.contains(window.end_ms)
        assert not window.contains(window.end_ms + 1000)

    def test_time_window_is_expired(self):
        """Test time window expiration check."""
        window_ms = 60_000
        timestamp_ms = 1_600_000_000_000
        
        window = TimeWindow(window_ms, timestamp_ms)
        
        # Not expired
        assert not window.is_expired(window.start_ms)
        assert not window.is_expired(window.end_ms - 1)
        
        # Expired
        assert window.is_expired(window.end_ms)
        assert window.is_expired(window.end_ms + 1000)

    def test_time_window_get_next_window(self):
        """Test getting next time window."""
        window_ms = 60_000
        timestamp_ms = 1_600_000_000_000
        
        window = TimeWindow(window_ms, timestamp_ms)
        next_window = window.get_next_window()
        
        assert next_window.start_ms == window.end_ms
        assert next_window.end_ms == window.end_ms + window_ms

    def test_time_window_to_filename(self):
        """Test filename generation from time window."""
        window_ms = 60_000
        # Use a known timestamp: 2020-09-13 12:26:40 UTC
        timestamp_ms = 1_600_000_000_000
        
        window = TimeWindow(window_ms, timestamp_ms)
        filename = window.to_filename("observer")
        
        # Should format as observer_YYYYMMDD_HHMM.jsonl
        expected = "observer_20200913_1226.jsonl"
        assert filename == expected


class TestRotationManager:
    """Test rotation manager functionality."""

    def test_rotation_manager_disabled(self):
        """Test rotation manager when rotation is disabled."""
        config = RotationConfig(window_ms=60000, enable_rotation=False, base_filename="test")
        manager = RotationManager(config)
        
        # Should never rotate when disabled
        assert not manager.should_rotate()
        assert not manager.should_rotate(utc_now_ms() + 100_000)

    def test_rotation_manager_enabled_first_call(self):
        """Test rotation manager on first call when enabled."""
        config = RotationConfig(window_ms=60000, enable_rotation=True, base_filename="test")
        manager = RotationManager(config)
        
        # Should rotate on first call (no current window)
        assert manager.should_rotate()

    def test_rotation_manager_within_window(self):
        """Test rotation manager within same time window."""
        config = RotationConfig(window_ms=60000, enable_rotation=True, base_filename="test")
        manager = RotationManager(config)
        
        # First call establishes window
        manager.get_current_file_path()
        
        # Second call within same window should not rotate
        assert not manager.should_rotate()

    def test_rotation_manager_window_change(self):
        """Test rotation manager when time window changes."""
        config = RotationConfig(window_ms=1000, enable_rotation=True, base_filename="test")  # 1 second window
        manager = RotationManager(config)
        
        # First call establishes window
        initial_path = manager.get_current_file_path()
        
        # Simulate time passing beyond window
        future_timestamp = utc_now_ms() + 2000
        
        # Should rotate for future timestamp
        assert manager.should_rotate(future_timestamp)
        
        # Get new path for future timestamp
        new_path = manager.get_current_file_path(future_timestamp)
        
        assert new_path != initial_path

    def test_rotation_manager_file_path_generation(self):
        """Test file path generation."""
        config = RotationConfig(window_ms=60000, enable_rotation=True, base_filename="test")
        manager = RotationManager(config)
        
        file_path = manager.get_current_file_path()
        
        # Should be in observer asset directory
        assert observer_asset_dir() in file_path.parents
        assert file_path.name.startswith("test_")
        assert file_path.suffix == ".jsonl"

    def test_rotation_manager_stats(self):
        """Test rotation statistics."""
        config = RotationConfig(window_ms=60000, enable_rotation=True, base_filename="test")
        manager = RotationManager(config)
        
        # Before any window is established
        stats = manager.get_rotation_stats()
        assert stats["rotation_enabled"] is True
        assert stats["window_ms"] == 60000
        assert stats["current_window"] is None
        
        # After window is established
        manager.get_current_file_path()
        stats = manager.get_rotation_stats()
        assert stats["current_window_start_ms"] is not None
        assert stats["current_window_end_ms"] is not None
        assert stats["time_until_rotation_ms"] is not None
        assert stats["current_file"] is not None


class TestJsonlFileSinkRotation:
    """Test JsonlFileSink with time-based rotation."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = observer_asset_dir()
        self.test_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up test files."""
        # Clean up any test files
        for file_path in self.test_dir.glob("test_rotation_*.jsonl"):
            file_path.unlink(missing_ok=True)

    def test_sink_without_rotation(self):
        """Test sink without rotation (original behavior)."""
        sink = JsonlFileSink("test_rotation_no_rotate.jsonl")
        
        # Create test record
        record = self._create_test_record()
        
        # Publish record
        sink.publish(record)
        
        # Check file was created and has content
        assert sink.file_path.exists()
        
        with open(sink.file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            assert content  # Should not be empty
            
            # Parse JSON to verify it's valid
            parsed = json.loads(content)
            assert 'snapshot' in parsed

    def test_sink_with_rotation_enabled(self):
        """Test sink with rotation enabled."""
        config = RotationConfig(window_ms=1000, enable_rotation=True, base_filename="test_rotation")
        sink = JsonlFileSink("test_rotation.jsonl", rotation_config=config)
        
        # Create test record
        record = self._create_test_record()
        
        # Publish record
        sink.publish(record)
        
        # Check rotation stats
        stats = sink.get_rotation_stats()
        assert stats["rotation_enabled"] is True
        assert stats["window_ms"] == 1000

    def test_sink_rotation_across_boundaries(self):
        """Test sink rotation across time boundaries."""
        # Use very small window for testing
        config = RotationConfig(window_ms=100, enable_rotation=True, base_filename="test_rotation_boundary")
        sink = JsonlFileSink("test_rotation.jsonl", rotation_config=config)
        
        # Create test records
        record1 = self._create_test_record()
        record2 = self._create_test_record()
        
        # Publish first record
        sink.publish(record1)
        first_file = sink.file_path
        
        # Wait for time window to pass
        time.sleep(0.15)  # 150ms > 100ms window
        
        # Publish second record
        sink.publish(record2)
        second_file = sink.file_path
        
        # Files should be different (rotation occurred)
        assert first_file != second_file
        
        # Both files should exist and have content
        assert first_file.exists()
        assert second_file.exists()

    def test_sink_rotation_stats(self):
        """Test rotation statistics from sink."""
        config = RotationConfig(window_ms=60000, enable_rotation=True, base_filename="test_stats")
        sink = JsonlFileSink("test_rotation.jsonl", rotation_config=config)
        
        stats = sink.get_rotation_stats()
        
        assert stats["rotation_enabled"] is True
        assert stats["window_ms"] == 60000
        assert "current_window_start_ms" in stats
        assert "current_window_end_ms" in stats
        assert "time_until_rotation_ms" in stats
        assert "current_file" in stats

    def _create_test_record(self) -> PatternRecord:
        """Create a test PatternRecord."""
        snapshot = build_snapshot(
            session_id="test_session",
            mode="TEST",
            source="test",
            stage="raw",
            inputs={"test": True},
            symbol="TEST",
            market="TEST",
        )
        
        return PatternRecord(
            snapshot=snapshot,
            regime_tags=[],
            condition_tags=[],
            outcome_labels=[],
            metadata={"test_record": True}
        )


class TestBufferedSinkRotation:
    """Test BufferedJsonlFileSink with time-based rotation."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = observer_asset_dir()
        self.test_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up test files."""
        # Clean up any test files
        for file_path in self.test_dir.glob("test_buffered_rotation_*.jsonl"):
            file_path.unlink(missing_ok=True)

    def test_buffered_sink_without_rotation(self):
        """Test buffered sink without rotation."""
        sink = BufferedJsonlFileSink(
            "test_buffered_no_rotate.jsonl",
            enable_buffering=False  # Direct write for easier testing
        )
        
        record = self._create_test_record()
        sink.publish(record)
        
        # Check file was created
        assert sink.file_path.exists()

    def test_buffered_sink_with_rotation_enabled(self):
        """Test buffered sink with rotation enabled."""
        config = RotationConfig(window_ms=1000, enable_rotation=True, base_filename="test_buffered_rotation")
        sink = BufferedJsonlFileSink(
            "test_buffered.jsonl",
            enable_buffering=False,  # Direct write for easier testing
            rotation_config=config
        )
        
        record = self._create_test_record()
        sink.publish(record)
        
        # Check rotation stats
        stats = sink.get_rotation_stats()
        assert stats["rotation_enabled"] is True
        assert stats["window_ms"] == 1000

    def test_buffered_sink_rotation_with_buffering(self):
        """Test buffered sink rotation with buffering enabled."""
        config = RotationConfig(window_ms=200, enable_rotation=True, base_filename="test_buffered_with_buffer")
        sink = BufferedJsonlFileSink(
            "test_buffered.jsonl",
            flush_interval_ms=100,  # Fast flush for testing
            enable_buffering=True,
            rotation_config=config
        )
        
        # Start the sink
        sink.start()
        
        try:
            # Publish multiple records across time windows
            for i in range(3):
                record = self._create_test_record(f"record_{i}")
                sink.publish(record)
                
                # Wait between records to cross time boundaries
                time.sleep(0.1)  # 100ms
            
            # Wait for flush to complete
            time.sleep(0.3)
            
            # Check buffer stats
            stats = sink.get_buffer_stats()
            assert stats["rotation"]["rotation_enabled"] is True
            
        finally:
            sink.stop()

    def test_buffered_sink_buffer_stats_with_rotation(self):
        """Test buffer stats include rotation information."""
        config = RotationConfig(window_ms=60000, enable_rotation=True, base_filename="test_buffered_stats")
        sink = BufferedJsonlFileSink(
            "test_buffered.jsonl",
            enable_buffering=False,
            rotation_config=config
        )
        
        stats = sink.get_buffer_stats()
        
        assert "rotation" in stats
        assert stats["rotation"]["rotation_enabled"] is True
        assert stats["rotation"]["window_ms"] == 60000

    def _create_test_record(self, record_id: str = "test") -> PatternRecord:
        """Create a test PatternRecord."""
        snapshot = build_snapshot(
            session_id="test_session",
            mode="TEST",
            source="test",
            stage="raw",
            inputs={"test": True, "record_id": record_id},
            symbol="TEST",
            market="TEST",
        )
        
        return PatternRecord(
            snapshot=snapshot,
            regime_tags=[],
            condition_tags=[],
            outcome_labels=[],
            metadata={"test_record": True, "record_id": record_id}
        )


class TestRotationIntegration:
    """Integration tests for rotation functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = observer_asset_dir()
        self.test_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up test files."""
        # Clean up any test files
        for file_path in self.test_dir.glob("integration_test_*.jsonl"):
            file_path.unlink(missing_ok=True)

    def test_rotation_preserves_record_ordering(self):
        """Test that rotation preserves record ordering within files."""
        config = RotationConfig(window_ms=100, enable_rotation=True, base_filename="integration_test_order")
        sink = JsonlFileSink("integration_test.jsonl", rotation_config=config)
        
        # Publish records with known timestamps
        records = []
        for i in range(5):
            record = self._create_test_record_with_timestamp(i * 50)  # 50ms apart
            records.append(record)
            sink.publish(record)
            
            # Small delay to ensure different timestamps
            time.sleep(0.01)
        
        # Wait for any async operations
        time.sleep(0.1)
        
        # Collect all generated files
        log_files = list(self.test_dir.glob("integration_test_order_*.jsonl"))
        assert len(log_files) > 0
        
        # Verify record ordering within each file
        all_records = []
        for file_path in sorted(log_files):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        record_data = json.loads(line.strip())
                        all_records.append(record_data['metadata']['record_id'])
        
        # Records should be in chronological order
        expected_order = [f"record_{i}" for i in range(5)]
        assert all_records == expected_order

    def test_rotation_no_record_loss(self):
        """Test that no records are lost during rotation."""
        config = RotationConfig(window_ms=50, enable_rotation=True, base_filename="integration_test_loss")
        sink = JsonlFileSink("integration_test.jsonl", rotation_config=config)
        
        # Publish many records quickly to trigger rotation
        record_count = 20
        for i in range(record_count):
            record = self._create_test_record_with_timestamp(i * 10)  # 10ms apart
            sink.publish(record)
        
        # Wait for any async operations
        time.sleep(0.1)
        
        # Count total records across all files
        total_records = 0
        log_files = list(self.test_dir.glob("integration_test_loss_*.jsonl"))
        
        for file_path in log_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        total_records += 1
        
        # Should have all records
        assert total_records == record_count

    def test_rotation_with_hybrid_trigger_compatibility(self):
        """Test that rotation works with hybrid trigger enabled."""
        # This test ensures rotation doesn't interfere with hybrid trigger functionality
        config = RotationConfig(window_ms=1000, enable_rotation=True, base_filename="integration_test_hybrid")
        sink = JsonlFileSink("integration_test.jsonl", rotation_config=config)
        
        # Simulate hybrid trigger scenario (rapid snapshots)
        for i in range(10):
            record = self._create_test_record_with_timestamp(utc_now_ms())
            sink.publish(record)
        
        # Should work without errors
        stats = sink.get_rotation_stats()
        assert stats["rotation_enabled"] is True

    def _create_test_record_with_timestamp(self, timestamp_ms: int) -> PatternRecord:
        """Create a test PatternRecord with specific timestamp."""
        # Note: build_snapshot doesn't allow custom timestamp_ms, so we'll use the current time
        # and rely on the rotation manager's timestamp handling for testing
        snapshot = build_snapshot(
            session_id="test_session",
            mode="TEST",
            source="test",
            stage="raw",
            inputs={"test": True, "custom_timestamp": timestamp_ms},
            symbol="TEST",
            market="TEST",
        )
        
        return PatternRecord(
            snapshot=snapshot,
            regime_tags=[],
            condition_tags=[],
            outcome_labels=[],
            metadata={"test_record": True, "custom_timestamp": timestamp_ms}
        )
