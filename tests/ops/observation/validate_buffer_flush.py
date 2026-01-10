#!/usr/bin/env python3
"""
Validation script for time-based buffer and flush implementation.
"""

import sys
import os
import time
import tempfile
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def validate_buffer_flush():
    """Validate buffer and flush implementation."""
    print("Validating time-based buffer and flush implementation...")
    
    try:
        from ops.observer.buffer_flush import BufferConfig, SnapshotBuffer
        from ops.observer.buffered_sink import BufferedJsonlFileSink
        from ops.observer.inputs.mock_market_data_provider import MockMarketDataProvider
        from ops.runtime.observer_runner import ObserverRunner
        from ops.observer.pattern_record import PatternRecord
        from ops.observer.snapshot import build_snapshot
        from paths import observer_asset_file
        print("✓ Imports successful")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Test 1: Basic buffer functionality
    print("\nTest 1: Basic buffer functionality")
    try:
        # Create temporary file for testing
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl')
        temp_file.close()
        file_path = temp_file.name
        
        config = BufferConfig(
            flush_interval_ms=100.0,  # Fast flush for testing
            max_buffer_size=100,
            enable_buffering=True,
        )
        
        buffer = SnapshotBuffer(config, file_path)
        buffer.start()
        
        # Create test record
        snapshot = build_snapshot(
            session_id="test_session",
            mode="TEST",
            source="market",
            stage="raw",
            inputs={"price": 100.0, "volume": 1000},
        )
        
        record = PatternRecord(
            snapshot=snapshot,
            regime_tags={},
            condition_tags=[],
            outcome_labels={},
            metadata={"test": True},
        )
        
        # Add record to buffer
        buffer.add_record(record)
        
        # Check buffer has record
        assert len(buffer._buffer) == 1, "Buffer should contain 1 record"
        
        # Wait for flush
        time.sleep(0.2)
        
        # Check buffer is flushed
        assert len(buffer._buffer) == 0, "Buffer should be empty after flush"
        
        # Check file contains record
        with open(file_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1, "File should contain 1 line"
            
            data = json.loads(lines[0].strip())
            assert data['metadata']['buffer_depth'] is not None, "buffer_depth should be populated"
            assert data['metadata']['flush_reason'] == "time_based", "flush_reason should be time_based"
        
        buffer.stop()
        os.unlink(file_path)
        
        print("✓ Basic buffer functionality test passed")
    except Exception as e:
        print(f"✗ Basic buffer functionality test failed: {e}")
        return False
    
    # Test 2: Buffered sink integration
    print("\nTest 2: Buffered sink integration")
    try:
        sink = BufferedJsonlFileSink(
            "test_buffered.jsonl",
            flush_interval_ms=100.0,
            max_buffer_size=100,
            enable_buffering=True,
        )
        
        sink.start()
        
        # Create and publish record
        snapshot = build_snapshot(
            session_id="test_session",
            mode="TEST",
            source="market",
            stage="raw",
            inputs={"price": 100.0, "volume": 1000},
        )
        
        record = PatternRecord(
            snapshot=snapshot,
            regime_tags={},
            condition_tags=[],
            outcome_labels={},
            metadata={"test": True},
        )
        
        sink.publish(record)
        
        # Wait for flush
        time.sleep(0.2)
        
        # Check file was created
        file_path = observer_asset_file("test_buffered.jsonl")
        assert os.path.exists(file_path), "Output file should exist"
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1, "File should contain 1 line"
            
            data = json.loads(lines[0].strip())
            assert data['metadata']['buffer_depth'] is not None, "buffer_depth should be populated"
            assert data['metadata']['flush_reason'] == "time_based", "flush_reason should be time_based"
        
        sink.stop()
        os.unlink(file_path)
        
        print("✓ Buffered sink integration test passed")
    except Exception as e:
        print(f"✗ Buffered sink integration test failed: {e}")
        return False
    
    # Test 3: ObserverRunner with buffering
    print("\nTest 3: ObserverRunner with buffering")
    try:
        mock_provider = MockMarketDataProvider()
        
        runner = ObserverRunner(
            provider=mock_provider,
            interval_sec=0.05,  # Fast interval
            max_iterations=3,
            enable_buffering=True,
            flush_interval_ms=200.0,  # Fast flush
            sink_filename="test_runner_buffered.jsonl",
        )
        
        # Mock observer to capture snapshots
        snapshots = []
        runner._observer.on_snapshot = snapshots.append
        
        runner.run()
        
        # Wait a bit more for buffer to flush
        time.sleep(0.3)
        
        # Check snapshots were generated
        assert len(snapshots) == 3, f"Expected 3 snapshots, got {len(snapshots)}"
        
        # Check buffer stats
        stats = runner.get_buffer_stats()
        assert stats['buffering_enabled'] is True, "Buffering should be enabled"
        
        # Check file was created
        file_path = observer_asset_file("test_runner_buffered.jsonl")
        print(f"Expected file path: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        print(f"Directory contents: {os.listdir(os.path.dirname(file_path))}")
        
        assert os.path.exists(file_path), "Output file should exist"
        
        # Check file contents
        with open(file_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 3, f"Expected 3 lines in file, got {len(lines)}"
            
            # Check metadata for all records
            for line in lines:
                data = json.loads(line.strip())
                assert data['metadata']['buffer_depth'] is not None, "buffer_depth should be populated"
                assert data['metadata']['flush_reason'] == "time_based", "flush_reason should be time_based"
        
        # Cleanup
        os.unlink(file_path)
        
        print("✓ ObserverRunner with buffering test passed")
    except Exception as e:
        print(f"✗ ObserverRunner with buffering test failed: {e}")
        return False
    
    # Test 4: ObserverRunner without buffering (direct write)
    print("\nTest 4: ObserverRunner without buffering")
    try:
        mock_provider = MockMarketDataProvider()
        
        runner = ObserverRunner(
            provider=mock_provider,
            interval_sec=0.05,
            max_iterations=2,
            enable_buffering=False,
            sink_filename="test_runner_direct.jsonl",
        )
        
        # Mock observer to capture snapshots
        snapshots = []
        runner._observer.on_snapshot = snapshots.append
        
        runner.run()
        
        # Check snapshots were generated
        assert len(snapshots) == 2, f"Expected 2 snapshots, got {len(snapshots)}"
        
        # Check buffer stats
        stats = runner.get_buffer_stats()
        assert stats['buffering_enabled'] is False, "Buffering should be disabled"
        
        # Check file was created
        file_path = observer_asset_file("test_runner_direct.jsonl")
        assert os.path.exists(file_path), "Output file should exist"
        
        # Check file contents
        with open(file_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2, f"Expected 2 lines in file, got {len(lines)}"
            
            # Check metadata for direct writes
            for line in lines:
                data = json.loads(line.strip())
                assert data['metadata']['buffer_depth'] == 0, "buffer_depth should be 0 for direct writes"
                assert data['metadata']['flush_reason'] == "direct", "flush_reason should be direct"
        
        # Cleanup
        os.unlink(file_path)
        
        print("✓ ObserverRunner without buffering test passed")
    except Exception as e:
        print(f"✗ ObserverRunner without buffering test failed: {e}")
        return False
    
    # Test 5: Buffer timing verification
    print("\nTest 5: Buffer timing verification")
    try:
        config = BufferConfig(
            flush_interval_ms=150.0,  # 150ms flush interval
            max_buffer_size=100,
            enable_buffering=True,
        )
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl')
        temp_file.close()
        file_path = temp_file.name
        
        buffer = SnapshotBuffer(config, file_path)
        buffer.start()
        
        # Add record and measure time to flush
        start_time = time.time()
        
        snapshot = build_snapshot(
            session_id="test_session",
            mode="TEST",
            source="market",
            stage="raw",
            inputs={"price": 100.0, "volume": 1000},
        )
        
        record = PatternRecord(
            snapshot=snapshot,
            regime_tags={},
            condition_tags=[],
            outcome_labels={},
            metadata={"test": True},
        )
        
        buffer.add_record(record)
        
        # Wait for flush
        while len(buffer._buffer) > 0 and time.time() - start_time < 1.0:
            time.sleep(0.01)
        
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        
        # Should flush within reasonable time (flush_interval_ms + tolerance)
        assert elapsed_ms < 300.0, f"Flush took too long: {elapsed_ms}ms"
        assert len(buffer._buffer) == 0, "Buffer should be empty after flush"
        
        buffer.stop()
        os.unlink(file_path)
        
        print(f"✓ Buffer timing verification passed (flush in {elapsed_ms:.1f}ms)")
    except Exception as e:
        print(f"✗ Buffer timing verification test failed: {e}")
        return False
    
    print("\n✓ All buffer and flush validation tests passed!")
    return True

if __name__ == "__main__":
    success = validate_buffer_flush()
    sys.exit(0 if success else 1)
