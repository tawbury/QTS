"""
test_performance_metrics.py

Unit tests for Observer performance metrics collection.

ROLE & BOUNDARY DECLARATION:
- THIS IS NOT Observer-Core testing
- Layer: Unit testing for performance metrics utility
- Ownership: Observer performance metrics testing
- Access: Test suite ONLY
- Must NOT test: Observer-Core behavior, strategy logic, decision flow

This test validates performance metrics collection without affecting
Observer behavior or introducing decision logic.

SAFETY CONFIRMATION:
- Tests do NOT affect Observer responsibilities
- Tests do NOT introduce decision logic
- Tests do NOT alter Snapshot/PatternRecord
- Tests do NOT enable Scalp adaptive behavior

Constraints from Observer_Architecture.md:
- Observer does NOT make trading decisions
- Observer does NOT generate tags/labels
- Observer does NOT modify snapshots

Constraints from observer_scalp_task_08_testing_infrastructure.md:
- Unit tests for new meta field functionality
- Additive test changes only
- No strategy testing in Observer tests
"""

import unittest
import time
from unittest.mock import patch
from datetime import datetime, timezone

from src.ops.observer.performance_metrics import (
    PerformanceMetrics,
    LatencyTimer,
    get_metrics,
    reset_metrics
)


class TestPerformanceMetrics(unittest.TestCase):
    """Test PerformanceMetrics class functionality."""
    
    def setUp(self):
        """Reset metrics before each test."""
        reset_metrics()
    
    def tearDown(self):
        """Clean up metrics after each test."""
        reset_metrics()
    
    def test_metrics_initialization(self):
        """Test PerformanceMetrics initializes with default values."""
        metrics = PerformanceMetrics()
        
        # Check initial state
        self.assertEqual(metrics.get_snapshot_count(), 0)
        self.assertEqual(metrics.get_buffer_depth(), 0.0)
        self.assertGreater(metrics.get_uptime_seconds(), 0.0)
    
    def test_counter_increment(self):
        """Test counter metrics increment correctly."""
        metrics = PerformanceMetrics()
        
        # Test single increment
        metrics.increment_counter("test_counter")
        summary = metrics.get_metrics_summary()
        self.assertEqual(summary["counters"]["test_counter"], 1)
        
        # Test multiple increments
        metrics.increment_counter("test_counter", 5)
        summary = metrics.get_metrics_summary()
        self.assertEqual(summary["counters"]["test_counter"], 6)
    
    def test_gauge_setting(self):
        """Test gauge metrics set correctly."""
        metrics = PerformanceMetrics()
        
        # Test gauge setting
        metrics.set_gauge("test_gauge", 42.5)
        summary = metrics.get_metrics_summary()
        self.assertEqual(summary["gauges"]["test_gauge"], 42.5)
        
        # Test gauge override
        metrics.set_gauge("test_gauge", 100.0)
        summary = metrics.get_metrics_summary()
        self.assertEqual(summary["gauges"]["test_gauge"], 100.0)
    
    def test_timing_recording(self):
        """Test timing metrics record correctly."""
        metrics = PerformanceMetrics()
        
        # Record some timing data
        metrics.record_timing("test_timing", 10.5)
        metrics.record_timing("test_timing", 15.0)
        metrics.record_timing("test_timing", 8.2)
        
        summary = metrics.get_metrics_summary()
        timing_stats = summary["timing_stats"]["test_timing"]
        
        self.assertEqual(timing_stats["count"], 3)
        self.assertEqual(timing_stats["latest_ms"], 8.2)
        self.assertAlmostEqual(timing_stats["avg_ms"], 11.233333333, places=5)
        self.assertEqual(timing_stats["min_ms"], 8.2)
        self.assertEqual(timing_stats["max_ms"], 15.0)
    
    def test_timing_history_limit(self):
        """Test timing history respects max_history limit."""
        metrics = PerformanceMetrics(max_history=3)
        
        # Add more timing records than limit
        for i in range(5):
            metrics.record_timing("test_timing", float(i))
        
        summary = metrics.get_metrics_summary()
        timing_stats = summary["timing_stats"]["test_timing"]
        
        # Should only keep latest 3 records
        self.assertEqual(timing_stats["count"], 3)
        self.assertEqual(timing_stats["min_ms"], 2.0)
        self.assertEqual(timing_stats["max_ms"], 4.0)
    
    def test_thread_safety(self):
        """Test metrics are thread-safe."""
        import threading
        
        metrics = PerformanceMetrics()
        results = []
        
        def increment_counter():
            for _ in range(100):
                metrics.increment_counter("thread_test")
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=increment_counter)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify final count
        summary = metrics.get_metrics_summary()
        self.assertEqual(summary["counters"]["thread_test"], 500)


class TestLatencyTimer(unittest.TestCase):
    """Test LatencyTimer context manager."""
    
    def setUp(self):
        """Reset metrics before each test."""
        reset_metrics()
    
    def tearDown(self):
        """Clean up metrics after each test."""
        reset_metrics()
    
    def test_latency_timer_basic(self):
        """Test LatencyTimer measures duration correctly."""
        with LatencyTimer("test_operation"):
            time.sleep(0.01)  # Sleep for 10ms
        
        metrics = get_metrics()
        summary = metrics.get_metrics_summary()
        timing_stats = summary["timing_stats"]["test_operation"]
        
        self.assertEqual(timing_stats["count"], 1)
        self.assertGreater(timing_stats["latest_ms"], 8.0)  # Should be around 10ms
        self.assertLess(timing_stats["latest_ms"], 20.0)   # But not too high
    
    def test_latency_timer_exception_handling(self):
        """Test LatencyTimer records timing even when exception occurs."""
        try:
            with LatencyTimer("test_exception"):
                time.sleep(0.01)
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected exception
        
        metrics = get_metrics()
        summary = metrics.get_metrics_summary()
        timing_stats = summary["timing_stats"]["test_exception"]
        
        # Should still record timing despite exception
        self.assertEqual(timing_stats["count"], 1)
        self.assertGreater(timing_stats["latest_ms"], 8.0)
    
    def test_latency_timer_nested(self):
        """Test nested LatencyTimer instances."""
        with LatencyTimer("outer_operation"):
            time.sleep(0.01)
            with LatencyTimer("inner_operation"):
                time.sleep(0.01)
        
        metrics = get_metrics()
        summary = metrics.get_metrics_summary()
        
        outer_stats = summary["timing_stats"]["outer_operation"]
        inner_stats = summary["timing_stats"]["inner_operation"]
        
        # Both should be recorded
        self.assertEqual(outer_stats["count"], 1)
        self.assertEqual(inner_stats["count"], 1)
        
        # Outer should take longer than inner
        self.assertGreater(outer_stats["latest_ms"], inner_stats["latest_ms"])


class TestGlobalMetrics(unittest.TestCase):
    """Test global metrics instance management."""
    
    def tearDown(self):
        """Clean up metrics after each test."""
        reset_metrics()
    
    def test_get_metrics_singleton(self):
        """Test get_metrics returns same instance."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()
        
        self.assertIs(metrics1, metrics2)
    
    def test_reset_metrics(self):
        """Test reset_metrics creates new instance."""
        metrics1 = get_metrics()
        metrics1.increment_counter("test")
        
        reset_metrics()
        metrics2 = get_metrics()
        
        self.assertIsNot(metrics1, metrics2)
        self.assertEqual(metrics2.get_snapshot_count(), 0)


class TestMetricsSummary(unittest.TestCase):
    """Test metrics summary generation."""
    
    def setUp(self):
        """Set up metrics with sample data."""
        reset_metrics()
        self.metrics = get_metrics()
        
        # Add sample data
        self.metrics.increment_counter("snapshots_processed", 100)
        self.metrics.set_gauge("buffer_depth", 25.5)
        self.metrics.record_timing("processing", 10.0)
        self.metrics.record_timing("processing", 15.0)
    
    def tearDown(self):
        """Clean up metrics after each test."""
        reset_metrics()
    
    def test_summary_structure(self):
        """Test metrics summary has correct structure."""
        summary = self.metrics.get_metrics_summary()
        
        # Check required fields
        self.assertIn("timestamp", summary)
        self.assertIn("uptime_seconds", summary)
        self.assertIn("counters", summary)
        self.assertIn("gauges", summary)
        self.assertIn("timing_stats", summary)
        
        # Check timestamp format
        timestamp = datetime.fromisoformat(summary["timestamp"].replace('Z', '+00:00'))
        self.assertIsInstance(timestamp, datetime)
    
    def test_summary_content(self):
        """Test metrics summary contains correct data."""
        summary = self.metrics.get_metrics_summary()
        
        # Check counters
        self.assertEqual(summary["counters"]["snapshots_processed"], 100)
        
        # Check gauges
        self.assertEqual(summary["gauges"]["buffer_depth"], 25.5)
        
        # Check timing stats
        timing_stats = summary["timing_stats"]["processing"]
        self.assertEqual(timing_stats["count"], 2)
        self.assertEqual(timing_stats["latest_ms"], 15.0)
        self.assertEqual(timing_stats["avg_ms"], 12.5)
        self.assertEqual(timing_stats["min_ms"], 10.0)
        self.assertEqual(timing_stats["max_ms"], 15.0)


if __name__ == '__main__':
    unittest.main()
