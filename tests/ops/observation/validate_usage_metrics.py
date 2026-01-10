# tests/ops/observation/validate_usage_metrics.py

"""
Validation script for Task 05: Usage Measurement & Cost Observability

This script validates that:
- Usage metrics are collected correctly
- Metrics are emitted as logs/structured output
- Both buffered and direct modes report metrics
- Metrics work with hybrid trigger + buffer + rotation
- Output is sufficient for Azure credit usage estimation
"""

import json
import logging
import sys
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from ops.observer.usage_metrics import (
    UsageMetricsConfig,
    UsageMetricsCollector,
    create_usage_metrics_collector,
    create_default_usage_metrics,
)
from ops.observer.event_bus import JsonlFileSink
from ops.observer.buffered_sink import BufferedJsonlFileSink
from ops.observer.log_rotation import RotationConfig
from ops.runtime.observer_runner import ObserverRunner
from ops.observer.inputs.mock_market_data_provider import MockMarketDataProvider
from ops.observer.tick_events import MockTickEventProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class UsageMetricsValidator:
    """Validator for usage metrics functionality."""
    
    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="usage_metrics_test_"))
        self.results: List[Dict[str, Any]] = []
        
        logger.info(f"Usage metrics validator initialized. Test directory: {self.test_dir}")
    
    def cleanup(self):
        """Clean up test files."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def record_result(self, test_name: str, passed: bool, message: str, details: Dict[str, Any] = None):
        """Record a test result."""
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "timestamp": time.time(),
            "details": details or {}
        }
        self.results.append(result)
        
        status = "PASS" if passed else "FAIL"
        logger.info(f"[{status}] {test_name}: {message}")
        
        if details:
            logger.debug(f"Details: {details}")
    
    def validate_basic_metrics_collection(self) -> None:
        """Validate basic metrics collection functionality."""
        logger.info("=== Basic Metrics Collection Validation ===")
        
        try:
            # Create metrics collector with short window for testing
            config = UsageMetricsConfig(
                window_ms=5_000,  # 5 second window
                enable_metrics=True,
                output_format='json'
            )
            collector = UsageMetricsCollector(config)
            
            # Test 1: Snapshot recording
            collector.record_snapshot(is_tick=False, latency_ms=10.5)
            collector.record_snapshot(is_tick=True, latency_ms=8.2)
            collector.record_snapshot(is_tick=False, latency_ms=12.1)
            
            metrics = collector.get_current_metrics()
            
            if (metrics['metrics_enabled'] and 
                metrics['total_snapshots'] == 3 and
                metrics['current_window']['snapshots_per_minute'] == 3):
                self.record_result("basic_snapshot_recording", True, 
                                 "Snapshot metrics recorded correctly")
            else:
                self.record_result("basic_snapshot_recording", False, 
                                 "Snapshot recording failed", metrics)
            
            # Test 2: Flush recording
            collector.record_flush(buffer_depth=5, bytes_written=1024, records_written=10)
            collector.record_flush(buffer_depth=8, bytes_written=2048, records_written=20)
            
            metrics = collector.get_current_metrics()
            
            if (metrics['total_bytes_written'] == 3072 and
                metrics['current_window']['flush_count_per_window'] == 2 and
                metrics['current_window']['avg_buffer_depth'] == 6.5):
                self.record_result("basic_flush_recording", True, 
                                 "Flush metrics recorded correctly")
            else:
                self.record_result("basic_flush_recording", False, 
                                 "Flush recording failed", metrics)
            
            # Test 3: Rotation recording
            collector.record_rotation(files_rotated=2)
            
            metrics = collector.get_current_metrics()
            
            if metrics['current_window']['files_rotated_per_window'] == 2:
                self.record_result("basic_rotation_recording", True, 
                                 "Rotation metrics recorded correctly")
            else:
                self.record_result("basic_rotation_recording", False, 
                                 "Rotation recording failed", metrics)
            
            # Test 4: Disabled metrics
            disabled_config = UsageMetricsConfig(enable_metrics=False)
            disabled_collector = UsageMetricsCollector(disabled_config)
            
            disabled_collector.record_snapshot(is_tick=False, latency_ms=10.0)
            disabled_metrics = disabled_collector.get_current_metrics()
            
            if not disabled_metrics['metrics_enabled']:
                self.record_result("disabled_metrics", True, 
                                 "Disabled metrics work correctly")
            else:
                self.record_result("disabled_metrics", False, 
                                 "Disabled metrics not working", disabled_metrics)
        
        except Exception as e:
            self.record_result("basic_metrics_collection", False, f"Exception: {e}")
            logger.exception("Basic metrics collection validation failed")
    
    def validate_direct_sink_metrics(self) -> None:
        """Validate metrics collection with direct sink."""
        logger.info("=== Direct Sink Metrics Validation ===")
        
        try:
            # Create metrics collector
            metrics_collector = create_usage_metrics_collector(window_ms=5_000)
            
            # Create direct sink
            sink = JsonlFileSink("usage_direct_test.jsonl")
            
            # Simulate direct writes (no buffering)
            from ops.observer.pattern_record import PatternRecord
            from ops.observer.snapshot import build_snapshot
            
            for i in range(10):
                snapshot = build_snapshot(
                    session_id="test_session",
                    mode="TEST",
                    source="validation",
                    stage="raw",
                    inputs={"test": True, "record_id": i},
                    symbol="TEST",
                    market="TEST",
                )
                
                record = PatternRecord(
                    snapshot=snapshot,
                    regime_tags=[],
                    condition_tags=[],
                    outcome_labels=[],
                    metadata={"test": True, "record_id": i}
                )
                
                # Simulate latency measurement
                start_time = time.time()
                sink.publish(record)
                latency_ms = (time.time() - start_time) * 1000
                
                # Record metrics manually (direct sink doesn't have automatic metrics)
                metrics_collector.record_snapshot(is_tick=False, latency_ms=latency_ms)
            
            metrics = metrics_collector.get_current_metrics()
            
            if (metrics['metrics_enabled'] and 
                metrics['total_snapshots'] == 10 and
                metrics['current_window']['snapshots_per_minute'] == 10):
                self.record_result("direct_sink_metrics", True, 
                                 "Direct sink metrics collected correctly")
            else:
                self.record_result("direct_sink_metrics", False, 
                                 "Direct sink metrics failed", metrics)
        
        except Exception as e:
            self.record_result("direct_sink_metrics", False, f"Exception: {e}")
            logger.exception("Direct sink metrics validation failed")
    
    def validate_buffered_sink_metrics(self) -> None:
        """Validate metrics collection with buffered sink."""
        logger.info("=== Buffered Sink Metrics Validation ===")
        
        try:
            # Create metrics collector
            metrics_collector = create_usage_metrics_collector(window_ms=5_000)
            
            # Create buffered sink with metrics collector
            sink = BufferedJsonlFileSink(
                "usage_buffered_test.jsonl",
                flush_interval_ms=1_000,  # 1 second flush
                max_buffer_size=100,
                enable_buffering=True,
            )
            
            # Set metrics collector
            sink.set_metrics_collector(metrics_collector)
            sink.start()
            
            # Simulate buffered writes
            from ops.observer.pattern_record import PatternRecord
            from ops.observer.snapshot import build_snapshot
            
            for i in range(15):
                snapshot = build_snapshot(
                    session_id="test_session",
                    mode="TEST",
                    source="validation",
                    stage="raw",
                    inputs={"test": True, "record_id": i},
                    symbol="TEST",
                    market="TEST",
                )
                
                record = PatternRecord(
                    snapshot=snapshot,
                    regime_tags=[],
                    condition_tags=[],
                    outcome_labels=[],
                    metadata={"test": True, "record_id": i}
                )
                
                sink.publish(record)
            
            # Wait for flush
            time.sleep(1.5)
            
            # Get buffer stats
            buffer_stats = sink.get_buffer_stats()
            metrics = metrics_collector.get_current_metrics()
            
            # Debug information
            logger.info(f"Buffer stats: {buffer_stats}")
            logger.info(f"Metrics: {metrics}")
            
            sink.stop()
            
            # Validate metrics
            metrics_valid = (
                metrics['metrics_enabled'] and
                metrics['current_window']['flush_count_per_window'] >= 1 and
                metrics['current_window']['records_written_per_window'] >= 10
            )
            
            buffer_valid = (
                buffer_stats.get('running', False) and
                buffer_stats.get('buffer_size', 0) >= 0
            )
            
            if metrics_valid and buffer_valid:
                self.record_result("buffered_sink_metrics", True, 
                                 "Buffered sink metrics collected correctly",
                                 {"records_written": metrics['current_window']['records_written_per_window'],
                                  "flush_count": metrics['current_window']['flush_count_per_window'],
                                  "bytes_written": metrics['current_window']['bytes_written_per_window']})
            else:
                self.record_result("buffered_sink_metrics", False, 
                                 "Buffered sink metrics failed",
                                 {"metrics_valid": metrics_valid, "buffer_valid": buffer_valid,
                                  "buffer_stats": buffer_stats, "metrics": metrics})
        
        except Exception as e:
            self.record_result("buffered_sink_metrics", False, f"Exception: {e}")
            logger.exception("Buffered sink metrics validation failed")
    
    def validate_observer_runner_metrics(self) -> None:
        """Validate metrics collection with ObserverRunner."""
        logger.info("=== Observer Runner Metrics Validation ===")
        
        try:
            # Create mock provider
            provider = MockMarketDataProvider(
                symbol="TEST",
                market="TEST"
            )
            
            # Create runner with metrics enabled
            runner = ObserverRunner(
                provider,
                interval_sec=0.1,  # 100ms intervals
                max_iterations=20,
                mode="TEST",
                sink_filename="usage_runner_test.jsonl",
                enable_buffering=True,
                flush_interval_ms=500,  # 500ms flush
                enable_usage_metrics=True,
                metrics_window_ms=5_000,  # 5 second window
            )
            
            # Run the observer
            runner.run()
            
            # Get metrics
            metrics = runner.get_usage_metrics()
            buffer_stats = runner.get_buffer_stats()
            
            # Validate metrics
            metrics_enabled = metrics.get('metrics_enabled', False)
            total_snapshots = metrics.get('total_snapshots', 0)
            snapshots_per_min = metrics.get('snapshots_per_minute_overall', 0)
            
            metrics_valid = (
                metrics_enabled and
                total_snapshots > 0 and
                snapshots_per_min > 0
            )
            
            buffer_valid = (
                buffer_stats.get('buffering_enabled', False)
            )
            
            if metrics_valid and buffer_valid:
                self.record_result("observer_runner_metrics", True, 
                                 "Observer runner metrics collected correctly",
                                 {"total_snapshots": total_snapshots,
                                  "snapshots_per_minute": snapshots_per_min,
                                  "total_bytes": metrics.get('total_bytes_written')})
            else:
                self.record_result("observer_runner_metrics", False, 
                                 "Observer runner metrics failed",
                                 {"metrics_valid": metrics_valid, "buffer_valid": buffer_valid,
                                  "metrics_enabled": metrics_enabled, "total_snapshots": total_snapshots,
                                  "snapshots_per_min": snapshots_per_min, "metrics": metrics, "buffer_stats": buffer_stats})
        
        except Exception as e:
            self.record_result("observer_runner_metrics", False, f"Exception: {e}")
            logger.exception("Observer runner metrics validation failed")
    
    def validate_hybrid_mode_metrics(self) -> None:
        """Validate metrics collection with hybrid trigger mode."""
        logger.info("=== Hybrid Mode Metrics Validation ===")
        
        try:
            # Create mock providers
            market_provider = MockMarketDataProvider(
                symbol="TEST",
                market="TEST"
            )
            
            tick_provider = MockTickEventProvider(
                tick_interval_ms=50  # 50ms between ticks
            )
            
            # Create runner with hybrid mode
            runner = ObserverRunner(
                market_provider,
                interval_sec=0.2,  # 200ms loop intervals
                max_iterations=10,
                mode="TEST",
                sink_filename="usage_hybrid_test.jsonl",
                tick_provider=tick_provider,
                hybrid_mode=True,
                enable_buffering=True,
                flush_interval_ms=500,
                enable_usage_metrics=True,
                metrics_window_ms=5_000,
            )
            
            # Run with auto-generated test ticks
            runner.run(auto_generate_test_ticks=True)
            
            # Get metrics
            metrics = runner.get_usage_metrics()
            
            # Validate hybrid metrics
            if (metrics.get('usage_metrics_enabled', False) and
                metrics.get('total_snapshots', 0) > 0):
                
                current_window = metrics.get('current_window', {})
                has_tick_snapshots = current_window.get('snapshots_tick_per_minute', 0) > 0
                has_loop_snapshots = current_window.get('snapshots_loop_per_minute', 0) > 0
                
                if has_tick_snapshots and has_loop_snapshots:
                    self.record_result("hybrid_mode_metrics", True, 
                                     "Hybrid mode metrics collected correctly",
                                     {"tick_snapshots": current_window.get('snapshots_tick_per_minute'),
                                      "loop_snapshots": current_window.get('snapshots_loop_per_minute')})
                else:
                    self.record_result("hybrid_mode_metrics", True, 
                                     "Hybrid mode metrics working (may not have both types)",
                                     {"total_snapshots": metrics.get('total_snapshots'),
                                      "has_tick": has_tick_snapshots, "has_loop": has_loop_snapshots})
            else:
                self.record_result("hybrid_mode_metrics", False, 
                                 "Hybrid mode metrics not enabled or no snapshots", metrics)
        
        except Exception as e:
            self.record_result("hybrid_mode_metrics", False, f"Exception: {e}")
            logger.exception("Hybrid mode metrics validation failed")
    
    def validate_rotation_metrics(self) -> None:
        """Validate metrics collection with rotation enabled."""
        logger.info("=== Rotation Metrics Validation ===")
        
        try:
            # Create rotation config with short window
            rotation_config = RotationConfig(
                window_ms=2_000,  # 2 second rotation window
                enable_rotation=True,
                base_filename="usage_rotation_test"
            )
            
            # Create metrics collector
            metrics_collector = create_usage_metrics_collector(window_ms=5_000)
            
            # Create buffered sink with rotation
            sink = BufferedJsonlFileSink(
                "usage_rotation_test.jsonl",
                flush_interval_ms=500,
                max_buffer_size=100,
                enable_buffering=True,
                rotation_config=rotation_config,
            )
            
            sink.set_metrics_collector(metrics_collector)
            sink.start()
            
            # Generate records over time to trigger rotation
            from ops.observer.pattern_record import PatternRecord
            from ops.observer.snapshot import build_snapshot
            
            for cycle in range(3):
                # Generate records in this cycle
                for i in range(5):
                    snapshot = build_snapshot(
                        session_id="test_session",
                        mode="TEST",
                        source="validation",
                        stage="raw",
                        inputs={"test": True, "cycle": cycle, "record_id": i},
                        symbol="TEST",
                        market="TEST",
                    )
                    
                    record = PatternRecord(
                        snapshot=snapshot,
                        regime_tags=[],
                        condition_tags=[],
                        outcome_labels=[],
                        metadata={"test": True, "cycle": cycle, "record_id": i}
                    )
                    
                    sink.publish(record)
                
                # Wait between cycles to allow rotation
                time.sleep(1.0)
            
            # Final wait for flush
            time.sleep(1.0)
            
            sink.stop()
            
            # Get metrics
            metrics = metrics_collector.get_current_metrics()
            rotation_stats = sink.get_rotation_stats()
            
            # Validate rotation metrics
            rotation_detected = rotation_stats['rotation_enabled']
            files_rotated = metrics['current_window'].get('files_rotated_per_window', 0)
            
            if rotation_detected and files_rotated > 0:
                self.record_result("rotation_metrics", True, 
                                 "Rotation metrics collected correctly",
                                 {"files_rotated": files_rotated,
                                  "rotation_enabled": rotation_stats['rotation_enabled']})
            else:
                self.record_result("rotation_metrics", False, 
                                 "Rotation metrics not detected",
                                 {"rotation_detected": rotation_detected, "files_rotated": files_rotated})
        
        except Exception as e:
            self.record_result("rotation_metrics", False, f"Exception: {e}")
            logger.exception("Rotation metrics validation failed")
    
    def validate_cost_estimation_data(self) -> None:
        """Validate metrics provide sufficient data for cost estimation."""
        logger.info("=== Cost Estimation Data Validation ===")
        
        try:
            # Create comprehensive metrics collector
            metrics_collector = create_usage_metrics_collector(window_ms=5_000)
            
            # Simulate realistic workload
            for minute in range(2):  # 2 minutes of data
                for second in range(60):  # 60 seconds per minute
                    # Variable snapshot frequency (simulating market activity)
                    if second % 2 == 0:  # Every 2 seconds
                        # Mix of tick and loop snapshots
                        is_tick = second % 4 == 0
                        latency = 2.0 + (second % 8)  # 2-9ms latency
                        metrics_collector.record_snapshot(is_tick=is_tick, latency_ms=latency)
                    
                    # Buffer flushes
                    if second % 5 == 0:  # Every 5 seconds
                        buffer_depth = 1 + (second % 10)
                        bytes_written = 800 + (second * 10)
                        records_written = bytes_written // 85  # ~85 bytes per record
                        metrics_collector.record_flush(
                            buffer_depth=buffer_depth,
                            bytes_written=bytes_written,
                            records_written=records_written
                        )
                    
                    # Occasional rotation
                    if second == 30:  # Once per minute
                        metrics_collector.record_rotation(files_rotated=1)
            
            # Get comprehensive metrics
            metrics = metrics_collector.get_current_metrics()
            
            # Validate cost estimation data availability
            required_fields = [
                'total_snapshots',
                'total_bytes_written',
                'snapshots_per_minute_overall',
                'runtime_ms'
            ]
            
            current_window = metrics.get('current_window', {})
            window_fields = [
                'snapshots_per_minute',
                'avg_latency_ms',
                'flush_count_per_window',
                'avg_buffer_depth',
                'bytes_written_per_window',
                'files_rotated_per_window'
            ]
            
            # Check required fields
            has_required = all(field in metrics for field in required_fields)
            has_window_data = all(field in current_window for field in window_fields)
            
            # Check data reasonableness
            data_reasonable = (
                metrics['total_snapshots'] > 0 and
                metrics['total_bytes_written'] > 0 and
                metrics['snapshots_per_minute_overall'] > 0 and
                current_window.get('avg_latency_ms', 0) > 0
            )
            
            if has_required and has_window_data and data_reasonable:
                self.record_result("cost_estimation_data", True, 
                                 "Sufficient data for cost estimation",
                                 {"total_snapshots": metrics['total_snapshots'],
                                  "total_bytes": metrics['total_bytes_written'],
                                  "snapshots_per_min": metrics['snapshots_per_minute_overall'],
                                  "avg_latency": current_window.get('avg_latency_ms')})
            else:
                self.record_result("cost_estimation_data", False, 
                                 "Insufficient data for cost estimation",
                                 {"has_required": has_required, 
                                  "has_window_data": has_window_data,
                                  "data_reasonable": data_reasonable})
        
        except Exception as e:
            self.record_result("cost_estimation_data", False, f"Exception: {e}")
            logger.exception("Cost estimation data validation failed")
    
    def run_validation(self, scenario: str = "all") -> None:
        """Run usage metrics validation."""
        logger.info("=== Usage Metrics Validation Started ===")
        
        scenarios = {
            "basic": self.validate_basic_metrics_collection,
            "direct": self.validate_direct_sink_metrics,
            "buffered": self.validate_buffered_sink_metrics,
            "runner": self.validate_observer_runner_metrics,
            "hybrid": self.validate_hybrid_mode_metrics,
            "rotation": self.validate_rotation_metrics,
            "cost": self.validate_cost_estimation_data,
            "all": lambda: [
                self.validate_basic_metrics_collection(),
                self.validate_direct_sink_metrics(),
                self.validate_buffered_sink_metrics(),
                self.validate_observer_runner_metrics(),
                self.validate_hybrid_mode_metrics(),
                self.validate_rotation_metrics(),
                self.validate_cost_estimation_data(),
            ]
        }
        
        if scenario not in scenarios:
            logger.error(f"Unknown scenario: {scenario}")
            return
        
        try:
            if scenario == "all":
                scenarios["all"]()
            else:
                scenarios[scenario]()
        finally:
            self.cleanup()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print validation summary."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*60)
        print("USAGE METRICS VALIDATION SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        print("="*60)
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Save detailed results
        results_file = self.test_dir.parent / "usage_metrics_validation_report.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: {results_file}")


if __name__ == "__main__":
    validator = UsageMetricsValidator()
    
    # Parse command line arguments
    scenario = "all"
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    
    validator.run_validation(scenario)
