# tests/ops/observation/test_buffer_flush.py

import pytest
import tempfile
import os
import json
import time
from unittest.mock import Mock, patch

from ops.observer.buffer_flush import BufferConfig, SnapshotBuffer, BufferedRecord
from ops.observer.buffered_sink import BufferedJsonlFileSink
from ops.observer.pattern_record import PatternRecord
from ops.observer.snapshot import build_snapshot, utc_now_ms


class TestBufferConfig:
    """Test BufferConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = BufferConfig()
        
        assert config.flush_interval_ms == 1000.0
        assert config.max_buffer_size == 10000
        assert config.enable_buffering is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = BufferConfig(
            flush_interval_ms=500.0,
            max_buffer_size=5000,
            enable_buffering=False,
        )
        
        assert config.flush_interval_ms == 500.0
        assert config.max_buffer_size == 5000
        assert config.enable_buffering is False


class TestSnapshotBuffer:
    """Test SnapshotBuffer implementation."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl')
        self.temp_file.close()
        self.file_path = self.temp_file.name
        
        self.config = BufferConfig(
            flush_interval_ms=100.0,  # Fast flush for testing
            max_buffer_size=100,
            enable_buffering=True,
        )
        
        self.buffer = SnapshotBuffer(self.config, self.file_path)
    
    def teardown_method(self):
        """Cleanup test environment."""
        if self.buffer._running:
            self.buffer.stop()
        
        if os.path.exists(self.file_path):
            os.unlink(self.file_path)
    
    def create_test_record(self, symbol: str = "TEST") -> PatternRecord:
        """Create a test PatternRecord."""
        snapshot = build_snapshot(
            session_id="test_session",
            mode="TEST",
            source="market",
            stage="raw",
            inputs={"price": 100.0, "volume": 1000},
            symbol=symbol,
        )
        
        return PatternRecord(
            snapshot=snapshot,
            regime_tags={},
            condition_tags=[],
            outcome_labels={},
            metadata={"test": True},
        )
    
    def test_buffer_start_stop(self):
        """Test buffer start and stop functionality."""
        assert not self.buffer._running
        
        self.buffer.start()
        assert self.buffer._running
        assert self.buffer._flush_thread is not None
        
        self.buffer.stop()
        assert not self.buffer._running
    
    def test_buffer_disabled(self):
        """Test buffer when buffering is disabled."""
        config = BufferConfig(enable_buffering=False)
        buffer = SnapshotBuffer(config, self.file_path)
        
        buffer.start()  # Should not start anything
        assert not buffer._running
        
        record = self.create_test_record()
        buffer.add_record(record)  # Should write directly
        
        # Check file was written
        with open(self.file_path, 'r') as f:
            content = f.read()
            assert len(content) > 0
        
        buffer.stop()
    
    def test_add_record_to_buffer(self):
        """Test adding records to buffer."""
        self.buffer.start()
        
        record = self.create_test_record()
        initial_buffer_size = len(self.buffer._buffer)
        
        self.buffer.add_record(record)
        
        assert len(self.buffer._buffer) == initial_buffer_size + 1
        
        # Check buffered record metadata
        buffered_record = self.buffer._buffer[-1]
        assert isinstance(buffered_record, BufferedRecord)
        assert buffered_record.record == record
        assert buffered_record.received_at_ms > 0
        assert buffered_record.buffer_depth_at_time == initial_buffer_size
        
        self.buffer.stop()
    
    def test_time_based_flush(self):
        """Test time-based flush mechanism."""
        self.buffer.start()
        
        # Add multiple records
        records = [self.create_test_record(f"SYM{i}") for i in range(3)]
        for record in records:
            self.buffer.add_record(record)
        
        # Wait for flush to occur (flush_interval_ms = 100ms)
        time.sleep(0.2)
        
        # Check buffer is flushed
        assert len(self.buffer._buffer) == 0
        
        # Check file contains records
        with open(self.file_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 3
            
            # Check metadata was updated
            for line in lines:
                data = json.loads(line.strip())
                assert data['metadata']['buffer_depth'] is not None
                assert data['metadata']['flush_reason'] == "time_based"
        
        self.buffer.stop()
    
    def test_flush_on_stop(self):
        """Test that remaining records are flushed on stop."""
        self.buffer.start()
        
        # Add records
        records = [self.create_test_record(f"SYM{i}") for i in range(2)]
        for record in records:
            self.buffer.add_record(record)
        
        # Stop without waiting for time-based flush
        self.buffer.stop()
        
        # Check file contains records
        with open(self.file_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
        
        # Check metadata was updated
        for line in lines:
            data = json.loads(line.strip())
            assert data['metadata']['buffer_depth'] is not None
            assert data['metadata']['flush_reason'] == "time_based"
    
    def test_buffer_size_limit(self):
        """Test buffer size limit safety mechanism."""
        config = BufferConfig(
            flush_interval_ms=10000.0,  # Very long flush interval
            max_buffer_size=3,  # Small buffer for testing
            enable_buffering=True,
        )
        buffer = SnapshotBuffer(config, self.file_path)
        buffer.start()
        
        # Add records up to limit
        records = [self.create_test_record(f"SYM{i}") for i in range(5)]
        for record in records:
            buffer.add_record(record)
        
        # Buffer should have been flushed due to size limit
        assert len(buffer._buffer) < 5
        
        buffer.stop()
    
    def test_get_buffer_stats(self):
        """Test buffer statistics."""
        self.buffer.start()
        
        stats = self.buffer.get_buffer_stats()
        
        assert 'buffer_size' in stats
        assert 'max_buffer_size' in stats
        assert 'flush_interval_ms' in stats
        assert 'last_flush_ms' in stats
        assert 'running' in stats
        assert 'time_since_last_flush_ms' in stats
        
        assert stats['running'] is True
        assert stats['buffer_size'] == 0
        assert stats['max_buffer_size'] == 100
        
        # Add a record and check stats
        record = self.create_test_record()
        self.buffer.add_record(record)
        
        stats = self.buffer.get_buffer_stats()
        assert stats['buffer_size'] == 1
        
        self.buffer.stop()


class TestBufferedJsonlFileSink:
    """Test BufferedJsonlFileSink implementation."""
    
    def setup_method(self):
        """Setup test environment."""
        self.filename = "test_buffered.jsonl"
        self.sink = BufferedJsonlFileSink(
            self.filename,
            flush_interval_ms=100.0,
            max_buffer_size=100,
            enable_buffering=True,
        )
    
    def teardown_method(self):
        """Cleanup test environment."""
        if self.sink._started:
            self.sink.stop()
        
        # Clean up test file
        from paths import observer_asset_file
        file_path = observer_asset_file(self.filename)
        if os.path.exists(file_path):
            os.unlink(file_path)
    
    def create_test_record(self, symbol: str = "TEST") -> PatternRecord:
        """Create a test PatternRecord."""
        snapshot = build_snapshot(
            session_id="test_session",
            mode="TEST",
            source="market",
            stage="raw",
            inputs={"price": 100.0, "volume": 1000},
            symbol=symbol,
        )
        
        return PatternRecord(
            snapshot=snapshot,
            regime_tags={},
            condition_tags=[],
            outcome_labels={},
            metadata={"test": True},
        )
    
    def test_sink_start_stop(self):
        """Test sink start and stop."""
        assert not self.sink._started
        
        self.sink.start()
        assert self.sink._started
        assert self.sink._buffer is not None
        
        self.sink.stop()
        assert not self.sink._started
    
    def test_publish_record(self):
        """Test publishing a record."""
        self.sink.start()
        
        record = self.create_test_record()
        self.sink.publish(record)
        
        # Wait for flush
        time.sleep(0.2)
        
        # Check file was created and contains record
        from paths import observer_asset_file
        file_path = observer_asset_file(self.filename)
        assert os.path.exists(file_path)
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            data = json.loads(lines[0].strip())
            assert data['metadata']['buffer_depth'] is not None
            assert data['metadata']['flush_reason'] == "time_based"
        
        self.sink.stop()
    
    def test_auto_start(self):
        """Test that sink auto-starts when publishing."""
        record = self.create_test_record()
        
        # Publish without explicit start
        self.sink.publish(record)
        
        # Should have auto-started
        assert self.sink._started
        
        # Wait for flush
        time.sleep(0.2)
        
        # Check file was created
        from paths import observer_asset_file
        file_path = observer_asset_file(self.filename)
        assert os.path.exists(file_path)
        
        self.sink.stop()
    
    def test_get_buffer_stats(self):
        """Test getting buffer statistics from sink."""
        self.sink.start()
        
        stats = self.sink.get_buffer_stats()
        
        assert 'buffering_enabled' in stats
        assert stats['buffering_enabled'] is True
        assert 'buffer_size' in stats
        
        self.sink.stop()
        
        stats = self.sink.get_buffer_stats()
        assert stats['buffering_enabled'] is False


class TestBufferIntegration:
    """Test buffer integration with ObserverRunner."""
    
    def test_observer_runner_with_buffer(self):
        """Test ObserverRunner with buffering enabled."""
        from ops.observer.inputs.mock_market_data_provider import MockMarketDataProvider
        from ops.runtime.observer_runner import ObserverRunner
        
        mock_provider = MockMarketDataProvider()
        
        runner = ObserverRunner(
            provider=mock_provider,
            interval_sec=0.05,  # Fast interval for testing
            max_iterations=3,
            enable_buffering=True,
            flush_interval_ms=200.0,  # Fast flush
        )
        
        # Mock observer to capture snapshots
        snapshots = []
        runner._observer.on_snapshot = snapshots.append
        
        runner.run()
        
        # Check snapshots were generated
        assert len(snapshots) == 3
        
        # Check buffer stats
        stats = runner.get_buffer_stats()
        assert stats['buffering_enabled'] is True
        
        # Check file was created
        from paths import observer_asset_file
        file_path = observer_asset_file("market_observation.jsonl")
        assert os.path.exists(file_path)
        
        # Check file contents
        with open(file_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 3
            
            # Check metadata
            for line in lines:
                data = json.loads(line.strip())
                assert data['metadata']['buffer_depth'] is not None
                assert data['metadata']['flush_reason'] == "time_based"
        
        # Cleanup
        if os.path.exists(file_path):
            os.unlink(file_path)
    
    def test_observer_runner_without_buffer(self):
        """Test ObserverRunner with buffering disabled."""
        from ops.observer.inputs.mock_market_data_provider import MockMarketDataProvider
        from ops.runtime.observer_runner import ObserverRunner
        
        mock_provider = MockMarketDataProvider()
        
        runner = ObserverRunner(
            provider=mock_provider,
            interval_sec=0.05,
            max_iterations=2,
            enable_buffering=False,
        )
        
        # Mock observer to capture snapshots
        snapshots = []
        runner._observer.on_snapshot = snapshots.append
        
        runner.run()
        
        # Check snapshots were generated
        assert len(snapshots) == 2
        
        # Check buffer stats
        stats = runner.get_buffer_stats()
        assert stats['buffering_enabled'] is False
        
        # Check file was created with direct writes
        from paths import observer_asset_file
        file_path = observer_asset_file("market_observation.jsonl")
        assert os.path.exists(file_path)
        
        # Check file contents
        with open(file_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
            
            # Check metadata for direct writes
            for line in lines:
                data = json.loads(line.strip())
                assert data['metadata']['buffer_depth'] == 0
                assert data['metadata']['flush_reason'] == "direct"
        
        # Cleanup
        if os.path.exists(file_path):
            os.unlink(file_path)
