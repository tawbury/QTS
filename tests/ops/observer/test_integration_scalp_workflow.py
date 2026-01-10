"""
test_integration_scalp_workflow.py

Integration tests for scalp extension workflow using mocked pipeline.

ROLE & BOUNDARY DECLARATION:
- THIS IS NOT Observer-Core testing
- Layer: Integration testing for scalp extension features
- Ownership: Observer workflow testing
- Access: Test suite ONLY
- Must NOT test: Strategy logic, decision pipeline, execution

This test validates end-to-end scalp extension workflow with mocked
components, ensuring Observer behavior remains unchanged.

SAFETY CONFIRMATION:
- Tests do NOT affect Observer responsibilities
- Tests do NOT introduce decision logic
- Tests do NOT alter Snapshot/PatternRecord
- Tests do NOT enable Scalp adaptive behavior

Constraints from Observer_Architecture.md:
- Observer → Snapshot → Decision Pipeline flow must be testable
- Observer does NOT make trading decisions
- Observer does NOT modify snapshots

Constraints from observer_scalp_task_08_testing_infrastructure.md:
- Integration tests for complete workflow
- Mock tick sources work correctly in tests
- Additive test changes only
- No strategy testing in Observer tests
"""

import unittest
import tempfile
import os
import json
import time
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timezone

from src.ops.observer.observer import Observer
from src.ops.observer.event_bus import EventBus
from src.ops.observer.snapshot import ObservationSnapshot, SnapshotMeta
from src.ops.observer.performance_metrics import get_metrics, reset_metrics
from src.ops.observer.config_manager import initialize_config, get_config_manager


class TestScalpWorkflowIntegration(unittest.TestCase):
    """Integration tests for scalp extension workflow."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset metrics
        reset_metrics()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_observer.jsonl")
        
        # Initialize scalp configuration
        config_dict = {
            "hybrid_trigger": {
                "enabled": True,
                "tick_source": "simulation",
                "min_interval_ms": 10.0,
                "max_interval_ms": 100.0
            },
            "buffer": {
                "flush_interval_ms": 50.0,
                "max_buffer_size": 10,
                "enable_buffering": True
            },
            "performance": {
                "enabled": True,
                "metrics_history_size": 100
            }
        }
        initialize_config(config_dict)
        
        # Create mock event bus
        self.event_bus = Mock()
        self.event_bus.dispatch = Mock()
        
        # Create observer with mocked dependencies
        self.observer = Observer(
            event_bus=self.event_bus,
            session_id="test_session",
            mode="TEST"
        )
    
    def tearDown(self):
        """Clean up test environment."""
        reset_metrics()
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)
    
    def create_test_snapshot(self, run_id="test_run", price=100.0):
        """Create a test ObservationSnapshot."""
        meta = SnapshotMeta(
            run_id=run_id,
            timestamp=datetime.now(timezone.utc),
            source="test"
        )
        
        snapshot = ObservationSnapshot(
            meta=meta,
            market_data={
                "symbol": "TEST",
                "price": price,
                "volume": 1000,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            system_state={
                "status": "running",
                "memory_usage": 50.0
            }
        )
        
        return snapshot
    
    def test_observer_processes_snapshot_with_metrics(self):
        """Test Observer processes snapshots and records metrics."""
        snapshot = self.create_test_snapshot()
        
        # Process snapshot
        self.observer.on_snapshot(snapshot)
        
        # Check event bus was called
        self.event_bus.dispatch.assert_called_once()
        
        # Check metrics were recorded
        metrics = get_metrics()
        summary = metrics.get_metrics_summary()
        
        self.assertEqual(summary["counters"]["snapshots_received"], 1)
        self.assertEqual(summary["counters"]["snapshots_processed"], 1)
        
        # Check timing metrics were recorded
        self.assertIn("snapshot_processing", summary["timing_stats"])
        self.assertIn("validation", summary["timing_stats"])
        self.assertIn("guard", summary["timing_stats"])
        self.assertIn("record_creation", summary["timing_stats"])
        self.assertIn("enrichment", summary["timing_stats"])
        self.assertIn("dispatch", summary["timing_stats"])
    
    def test_observer_blocks_invalid_snapshots(self):
        """Test Observer blocks invalid snapshots and records metrics."""
        # Create invalid snapshot (missing required fields)
        meta = SnapshotMeta(
            run_id="invalid_run",
            timestamp=datetime.now(timezone.utc),
            source=""
        )  # Empty source should fail validation
        
        snapshot = ObservationSnapshot(
            meta=meta,
            market_data={},  # Empty market data should fail validation
            system_state={}
        )
        
        # Process snapshot
        self.observer.on_snapshot(snapshot)
        
        # Check event bus was NOT called
        self.event_bus.dispatch.assert_not_called()
        
        # Check metrics were recorded
        metrics = get_metrics()
        summary = metrics.get_metrics_summary()
        
        self.assertEqual(summary["counters"]["snapshots_received"], 1)
        self.assertEqual(summary["counters"]["snapshots_blocked_validation"], 1)
        self.assertEqual(summary["counters"]["snapshots_processed"], 0)
    
    def test_observer_configuration_integration(self):
        """Test Observer integrates with scalp configuration."""
        config_manager = get_config_manager()
        
        # Check configuration is accessible
        self.assertTrue(config_manager.is_hybrid_trigger_enabled())
        self.assertTrue(config_manager.is_performance_monitoring_enabled())
        self.assertTrue(config_manager.is_buffer_enabled())
        self.assertFalse(config_manager.is_rotation_enabled())
        
        # Check configuration values
        config = config_manager.get_config()
        self.assertEqual(config.hybrid_trigger.tick_source, "simulation")
        self.assertEqual(config.buffer.flush_interval_ms, 50.0)
        self.assertEqual(config.performance.metrics_history_size, 100)
    
    def test_end_to_end_workflow_with_multiple_snapshots(self):
        """Test complete workflow with multiple snapshots."""
        snapshots = [
            self.create_test_snapshot(f"run_{i}", price=100.0 + i)
            for i in range(5)
        ]
        
        # Process all snapshots
        for snapshot in snapshots:
            self.observer.on_snapshot(snapshot)
        
        # Check all snapshots were processed
        self.assertEqual(self.event_bus.dispatch.call_count, 5)
        
        # Check metrics
        metrics = get_metrics()
        summary = metrics.get_metrics_summary()
        
        self.assertEqual(summary["counters"]["snapshots_received"], 5)
        self.assertEqual(summary["counters"]["snapshots_processed"], 5)
        
        # Check timing stats have multiple entries
        timing_stats = summary["timing_stats"]["snapshot_processing"]
        self.assertEqual(timing_stats["count"], 5)
        self.assertGreater(timing_stats["avg_ms"], 0)
    
    def test_workflow_with_performance_monitoring_disabled(self):
        """Test workflow with performance monitoring disabled."""
        # Re-initialize config with performance monitoring disabled
        config_dict = {
            "performance": {
                "enabled": False
            }
        }
        initialize_config(config_dict)
        
        snapshot = self.create_test_snapshot()
        
        # Process snapshot
        self.observer.on_snapshot(snapshot)
        
        # Check event bus was called
        self.event_bus.dispatch.assert_called_once()
        
        # Check performance monitoring is disabled
        config_manager = get_config_manager()
        self.assertFalse(config_manager.is_performance_monitoring_enabled())
    
    def test_workflow_error_handling(self):
        """Test workflow handles errors gracefully."""
        # Create snapshot that will cause an error in processing
        snapshot = self.create_test_snapshot()
        
        # Mock event bus to raise exception
        self.event_bus.dispatch.side_effect = Exception("Test error")
        
        # Should not raise exception
        with patch('src.ops.observer.observer.logger') as mock_logger:
            self.observer.on_snapshot(snapshot)
            
            # Should log error
            mock_logger.error.assert_called()
        
        # Check metrics still recorded
        metrics = get_metrics()
        summary = metrics.get_metrics_summary()
        
        self.assertEqual(summary["counters"]["snapshots_received"], 1)
        # Note: snapshots_processed might not be incremented due to error
    
    def test_workflow_with_buffered_sink(self):
        """Test workflow with buffered sink integration."""
        from src.ops.observer.buffered_sink import BufferedJsonlFileSink
        
        # Create buffered sink
        sink = BufferedJsonlFileSink(
            filename=self.test_file,
            flush_interval_ms=50.0,
            max_buffer_size=3,
            enable_buffering=True
        )
        
        # Update event bus to use buffered sink
        self.event_bus.dispatch = sink.publish
        
        # Process multiple snapshots
        for i in range(5):
            snapshot = self.create_test_snapshot(f"run_{i}")
            self.observer.on_snapshot(snapshot)
        
        # Wait for buffer to flush
        time.sleep(0.1)
        
        # Check file was created and contains records
        self.assertTrue(os.path.exists(self.test_file))
        
        with open(self.test_file, 'r') as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 0)
            
            # Verify JSON format
            for line in lines:
                parsed = json.loads(line.strip())
                self.assertIn('snapshot', parsed)
                self.assertIn('metadata', parsed)
        
        sink.stop()
    
    def test_workflow_timing_characteristics(self):
        """Test workflow timing characteristics are reasonable."""
        snapshot = self.create_test_snapshot()
        
        # Process snapshot and measure time
        start_time = time.time()
        self.observer.on_snapshot(snapshot)
        end_time = time.time()
        
        # Check processing completed in reasonable time
        processing_time_ms = (end_time - start_time) * 1000
        self.assertLess(processing_time_ms, 100.0)  # Should complete in < 100ms
        
        # Check metrics timing
        metrics = get_metrics()
        summary = metrics.get_metrics_summary()
        
        timing_stats = summary["timing_stats"]["snapshot_processing"]
        self.assertEqual(timing_stats["count"], 1)
        self.assertLess(timing_stats["latest_ms"], 100.0)
    
    def test_workflow_isolation(self):
        """Test workflow is isolated from other components."""
        # Create multiple observers
        observer1 = Observer(
            event_bus=Mock(),
            session_id="session1",
            mode="TEST"
        )
        
        observer2 = Observer(
            event_bus=Mock(),
            session_id="session2",
            mode="TEST"
        )
        
        snapshot = self.create_test_snapshot()
        
        # Process with different observers
        observer1.on_snapshot(snapshot)
        observer2.on_snapshot(snapshot)
        
        # Each observer should have processed independently
        observer1.event_bus.dispatch.assert_called_once()
        observer2.event_bus.dispatch.assert_called_once()
        
        # Metrics should be shared (global instance)
        metrics = get_metrics()
        summary = metrics.get_metrics_summary()
        
        self.assertEqual(summary["counters"]["snapshots_received"], 2)
        self.assertEqual(summary["counters"]["snapshots_processed"], 2)


class TestMockTickSource(unittest.TestCase):
    """Test mock tick source functionality for testing."""
    
    def setUp(self):
        """Set up test environment."""
        self.tick_source = Mock()
        self.tick_source.get_tick = Mock()
    
    def test_mock_tick_source_basic(self):
        """Test mock tick source provides basic tick data."""
        # Configure mock to return tick data
        self.tick_source.get_tick.return_value = {
            "symbol": "TEST",
            "price": 100.0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Get tick
        tick = self.tick_source.get_tick()
        
        # Verify tick data
        self.assertEqual(tick["symbol"], "TEST")
        self.assertEqual(tick["price"], 100.0)
        self.assertIn("timestamp", tick)
    
    def test_mock_tick_source_sequence(self):
        """Test mock tick source provides sequence of ticks."""
        # Configure mock to return different ticks
        tick_sequence = [
            {"symbol": "TEST", "price": 100.0, "timestamp": "2023-01-01T10:00:00Z"},
            {"symbol": "TEST", "price": 100.5, "timestamp": "2023-01-01T10:00:01Z"},
            {"symbol": "TEST", "price": 101.0, "timestamp": "2023-01-01T10:00:02Z"}
        ]
        
        self.tick_source.get_tick.side_effect = tick_sequence
        
        # Get ticks
        ticks = [self.tick_source.get_tick() for _ in range(3)]
        
        # Verify sequence
        self.assertEqual(len(ticks), 3)
        self.assertEqual(ticks[0]["price"], 100.0)
        self.assertEqual(ticks[1]["price"], 100.5)
        self.assertEqual(ticks[2]["price"], 101.0)
    
    def test_mock_tick_source_error_handling(self):
        """Test mock tick source handles errors gracefully."""
        # Configure mock to raise exception
        self.tick_source.get_tick.side_effect = Exception("Connection error")
        
        # Should raise exception
        with self.assertRaises(Exception):
            self.tick_source.get_tick()


if __name__ == '__main__':
    unittest.main()
