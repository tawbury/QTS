"""
test_buffer_operations.py

Unit tests for Observer buffer and flush operations.

ROLE & BOUNDARY DECLARATION:
- THIS IS NOT Observer-Core testing
- Layer: Unit testing for buffer operations
- Ownership: Observer buffer functionality testing
- Access: Test suite ONLY
- Must NOT test: Observer-Core behavior, strategy logic, decision flow

This test validates buffer and flush mechanisms without affecting
Observer behavior or introducing decision logic.

SAFETY CONFIRMATION:
- Tests do NOT affect Observer responsibilities
- Tests do NOT introduce decision logic
- Tests do NOT alter Snapshot/PatternRecord
- Tests do NOT enable Scalp adaptive behavior

Constraints from Observer_Architecture.md:
- Observer does NOT make trading decisions
- Observer does NOT modify snapshots
- Append-only storage model

Constraints from observer_scalp_task_08_testing_infrastructure.md:
- Unit tests for buffer and flush mechanism
- Additive test changes only
- No strategy testing in Observer tests
"""

import unittest
import tempfile
import os
import json
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.ops.observer.buffer_flush import SnapshotBuffer, BufferedRecord, BufferConfig
from src.ops.observer.pattern_record import PatternRecord
from src.ops.observer.snapshot import ObservationSnapshot, SnapshotMeta


class TestSnapshotBuffer(unittest.TestCase):
    """Test SnapshotBuffer class functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_observer.jsonl")
        
        # Create buffer config
        self.config = BufferConfig(
            flush_interval_ms=100.0,  # Short for testing
            max_buffer_size=5,
            enable_buffering=True
        )
        
        # Create buffer
        self.buffer = SnapshotBuffer(
            config=self.config,
            output_file=self.test_file
        )
    
    def tearDown(self):
        """Clean up test environment."""
        self.buffer.stop()
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)
    
    def create_mock_snapshot(self, run_id="test_run", timestamp=None):
        """Create a mock ObservationSnapshot for testing."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        meta = SnapshotMeta(
            run_id=run_id,
            timestamp=timestamp,
            source="test"
        )
        
        snapshot = ObservationSnapshot(
            meta=meta,
            market_data={"price": 100.0},
            system_state={"status": "running"}
        )
        
        return snapshot
    
    def create_mock_pattern_record(self, snapshot=None):
        """Create a mock PatternRecord for testing."""
        if snapshot is None:
            snapshot = self.create_mock_snapshot()
        
        record = PatternRecord(
            snapshot=snapshot,
            regime_tags={},
            condition_tags=[],
            outcome_labels={},
            metadata={"test": True}
        )
        
        return record
    
    def test_buffer_initialization(self):
        """Test SnapshotBuffer initializes correctly."""
        self.assertEqual(len(self.buffer._buffer), 0)
        self.assertTrue(self.buffer._config.enable_buffering)
        self.assertEqual(self.buffer._config.max_buffer_size, 5)
    
    def test_add_record_buffered(self):
        """Test adding record to buffer."""
        record = self.create_mock_pattern_record()
        
        # Add record
        self.buffer.add_record(record)
        
        # Check buffer contains record
        self.assertEqual(len(self.buffer._buffer), 1)
        
        buffered_record = self.buffer._buffer[0]
        self.assertIsInstance(buffered_record, BufferedRecord)
        self.assertEqual(buffered_record.record, record)
        self.assertIsInstance(buffered_record.received_at_ms, int)
        self.assertEqual(buffered_record.buffer_depth_at_time, 0)  # Was empty when added
    
    def test_add_record_direct_write(self):
        """Test adding record with buffering disabled."""
        # Create buffer with buffering disabled
        config = BufferConfig(enable_buffering=False)
        buffer = SnapshotBuffer(
            config=config,
            output_file=self.test_file
        )
        
        record = self.create_mock_pattern_record()
        
        # Add record
        buffer.add_record(record)
        
        # Buffer should remain empty
        self.assertEqual(len(buffer._buffer), 0)
        
        # File should contain the record
        self.assertTrue(os.path.exists(self.test_file))
        with open(self.test_file, 'r') as f:
            line = f.readline()
            self.assertTrue(len(line) > 0)
    
    def test_buffer_depth_tracking(self):
        """Test buffer depth is tracked correctly."""
        records = [self.create_mock_pattern_record() for _ in range(3)]
        
        # Add records
        for i, record in enumerate(records):
            self.buffer.add_record(record)
            buffered_record = self.buffer._buffer[i]
            self.assertEqual(buffered_record.buffer_depth_at_time, i)
    
    def test_auto_flush_on_max_size(self):
        """Test buffer flushes automatically when max size reached."""
        records = [self.create_mock_pattern_record() for _ in range(5)]
        
        # Add records up to max size
        for record in records:
            self.buffer.add_record(record)
        
        # Buffer should be empty (auto-flushed)
        self.assertEqual(len(self.buffer._buffer), 0)
        
        # File should contain records
        self.assertTrue(os.path.exists(self.test_file))
        with open(self.test_file, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 5)
    
    def test_manual_flush(self):
        """Test manual buffer flush."""
        records = [self.create_mock_pattern_record() for _ in range(2)]
        
        # Add records
        for record in records:
            self.buffer.add_record(record)
        
        # Buffer should contain records
        self.assertEqual(len(self.buffer._buffer), 2)
        
        # Manual flush
        self.buffer._flush_buffer()
        
        # Buffer should be empty
        self.assertEqual(len(self.buffer._buffer), 0)
        
        # File should contain records
        self.assertTrue(os.path.exists(self.test_file))
        with open(self.test_file, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2)
    
    def test_flush_empty_buffer(self):
        """Test flushing empty buffer does nothing."""
        # Buffer is empty initially
        self.assertEqual(len(self.buffer._buffer), 0)
        
        # Flush should not error
        self.buffer._flush_buffer()
        
        # Still empty
        self.assertEqual(len(self.buffer._buffer), 0)
        
        # File should not exist
        self.assertFalse(os.path.exists(self.test_file))
    
    def test_time_based_flush(self):
        """Test time-based automatic flushing."""
        # Create buffer with very short flush interval
        config = BufferConfig(flush_interval_ms=10.0)  # 10ms
        buffer = SnapshotBuffer(
            config=config,
            output_file=self.test_file
        )
        
        try:
            record = self.create_mock_pattern_record()
            buffer.add_record(record)
            
            # Wait for flush interval
            time.sleep(0.05)  # 50ms
            
            # Buffer should be empty (auto-flushed)
            self.assertEqual(len(buffer._buffer), 0)
            
            # File should contain record
            self.assertTrue(os.path.exists(self.test_file))
            
        finally:
            buffer.stop()
    
    def test_buffer_thread_safety(self):
        """Test buffer operations are thread-safe."""
        import threading
        
        records = [self.create_mock_pattern_record(f"thread_{i}") for i in range(10)]
        results = []
        
        def add_record(record):
            self.buffer.add_record(record)
            results.append(len(self.buffer._buffer))
        
        # Add records from multiple threads
        threads = []
        for record in records:
            thread = threading.Thread(target=add_record, args=(record,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All records should be added
        self.assertEqual(len(self.buffer._buffer), 10)
    
    def test_buffer_file_format(self):
        """Test flushed records have correct JSONL format."""
        record = self.create_mock_pattern_record()
        self.buffer.add_record(record)
        
        # Force flush
        self.buffer._flush_buffer()
        
        # Check file format
        with open(self.test_file, 'r') as f:
            line = f.readline().strip()
            
            # Should be valid JSON
            parsed = json.loads(line)
            
            # Should have expected structure
            self.assertIn('snapshot', parsed)
            self.assertIn('regime_tags', parsed)
            self.assertIn('condition_tags', parsed)
            self.assertIn('outcome_labels', parsed)
            self.assertIn('metadata', parsed)
    
    def test_buffer_with_metrics_collector(self):
        """Test buffer with metrics collector."""
        mock_collector = MagicMock()
        
        # Create buffer with metrics collector
        buffer = SnapshotBuffer(
            config=self.config,
            output_file=self.test_file,
            metrics_collector=mock_collector
        )
        
        try:
            record = self.create_mock_pattern_record()
            buffer.add_record(record)
            
            # Check metrics collector was called
            mock_collector.record_buffer_depth.assert_called()
            
            # Force flush
            buffer._flush_buffer()
            
            # Check flush metrics were recorded
            mock_collector.record_flush.assert_called()
            
        finally:
            buffer.stop()
    
    def test_buffer_error_handling(self):
        """Test buffer handles file write errors gracefully."""
        # Create buffer with invalid file path
        invalid_path = "/invalid/path/that/does/not/exist/test.jsonl"
        buffer = SnapshotBuffer(
            config=self.config,
            output_file=invalid_path
        )
        
        try:
            record = self.create_mock_pattern_record()
            
            # Should not raise exception, but should handle error
            with patch('src.ops.observer.buffer_flush.logger') as mock_logger:
                buffer.add_record(record)
                buffer._flush_buffer()
                
                # Should log error
                mock_logger.error.assert_called()
                
        finally:
            buffer.stop()


class TestBufferedRecord(unittest.TestCase):
    """Test BufferedRecord dataclass."""
    
    def test_buffered_record_creation(self):
        """Test BufferedRecord creation."""
        record = MagicMock()
        received_at_ms = 1234567890
        buffer_depth_at_time = 5
        
        buffered = BufferedRecord(
            record=record,
            received_at_ms=received_at_ms,
            buffer_depth_at_time=buffer_depth_at_time
        )
        
        self.assertEqual(buffered.record, record)
        self.assertEqual(buffered.received_at_ms, received_at_ms)
        self.assertEqual(buffered.buffer_depth_at_time, buffer_depth_at_time)


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


if __name__ == '__main__':
    unittest.main()
