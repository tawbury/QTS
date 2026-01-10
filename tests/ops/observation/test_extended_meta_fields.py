#!/usr/bin/env python3
"""
Test to validate extended meta fields implementation.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_extended_meta_fields():
    """Test that extended meta fields are properly populated."""
    print("Testing extended meta fields implementation...")
    
    try:
        from ops.observer.inputs.mock_market_data_provider import MockMarketDataProvider
        from ops.observer.tick_events import MockTickEventProvider
        from ops.runtime.observer_runner import ObserverRunner
        from ops.observer.snapshot import Meta
        print("✓ Imports successful")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Test 1: Loop snapshots have extended meta fields
    print("\nTest 1: Loop snapshots extended meta fields")
    try:
        mock_provider = MockMarketDataProvider()
        
        runner = ObserverRunner(
            provider=mock_provider,
            interval_sec=0.1,
            max_iterations=2,
            hybrid_mode=False,
        )
        
        # Mock observer to capture snapshots
        snapshots = []
        runner._observer.on_snapshot = snapshots.append
        
        runner.run()
        
        assert len(snapshots) == 2, f"Expected 2 snapshots, got {len(snapshots)}"
        
        # Check extended meta fields in loop snapshots
        for i, snapshot in enumerate(snapshots, 1):
            meta = snapshot.meta
            
            # Check required extended fields
            assert meta.iteration_id is not None, f"Loop snapshot {i} missing iteration_id"
            assert meta.loop_interval_ms is not None, f"Loop snapshot {i} missing loop_interval_ms"
            assert meta.latency_ms is not None, f"Loop snapshot {i} missing latency_ms"
            assert meta.tick_source == "loop", f"Loop snapshot {i} has wrong tick_source: {meta.tick_source}"
            
            # Check values
            assert meta.iteration_id == i, f"Loop snapshot {i} has wrong iteration_id: {meta.iteration_id}"
            assert meta.loop_interval_ms == 100.0, f"Loop snapshot {i} has wrong loop_interval_ms: {meta.loop_interval_ms}"
            assert meta.latency_ms >= 0, f"Loop snapshot {i} has negative latency: {meta.latency_ms}"
            
            # Check placeholder fields
            assert meta.buffer_depth is None, f"Loop snapshot {i} should have buffer_depth=None"
            assert meta.flush_reason is None, f"Loop snapshot {i} should have flush_reason=None"
        
        print("✓ Loop snapshots extended meta fields test passed")
    except Exception as e:
        print(f"✗ Loop snapshots extended meta fields test failed: {e}")
        return False
    
    # Test 2: Tick snapshots have extended meta fields
    print("\nTest 2: Tick snapshots extended meta fields")
    try:
        mock_provider = MockMarketDataProvider()
        tick_provider = MockTickEventProvider()
        
        runner = ObserverRunner(
            provider=mock_provider,
            interval_sec=0.1,
            max_iterations=1,
            hybrid_mode=True,
            tick_provider=tick_provider,
        )
        
        # Mock observer to capture snapshots
        snapshots = []
        runner._observer.on_snapshot = snapshots.append
        
        runner.run(auto_generate_test_ticks=True)
        
        # Find tick snapshots (should be generated during run)
        tick_snapshots = [s for s in snapshots if s.meta.tick_source and s.meta.tick_source != "loop"]
        assert len(tick_snapshots) >= 1, f"Expected at least 1 tick snapshot, got {len(tick_snapshots)}"
        
        # Check extended meta fields in tick snapshots
        for snapshot in tick_snapshots:
            meta = snapshot.meta
            
            # Check required extended fields
            assert meta.iteration_id is None, f"Tick snapshot should have iteration_id=None"
            assert meta.loop_interval_ms is None, f"Tick snapshot should have loop_interval_ms=None"
            assert meta.latency_ms is not None, f"Tick snapshot missing latency_ms"
            assert meta.tick_source != "loop", f"Tick snapshot should not have tick_source=loop"
            
            # Check values
            assert meta.latency_ms >= 0, f"Tick snapshot has negative latency: {meta.latency_ms}"
            
            # Check placeholder fields
            assert meta.buffer_depth is None, f"Tick snapshot should have buffer_depth=None"
            assert meta.flush_reason is None, f"Tick snapshot should have flush_reason=None"
        
        print("✓ Tick snapshots extended meta fields test passed")
    except Exception as e:
        print(f"✗ Tick snapshots extended meta fields test failed: {e}")
        return False
    
    # Test 3: Backward compatibility - old snapshots still work
    print("\nTest 3: Backward compatibility")
    try:
        # Test that Meta can be created without extended fields
        old_meta = Meta(
            timestamp="2025-01-01T00:00:00.000Z",
            timestamp_ms=1704067200000,
            session_id="test_session",
            run_id="test_run",
            mode="DEV",
        )
        
        # Check that old fields are still accessible
        assert old_meta.timestamp == "2025-01-01T00:00:00.000Z"
        assert old_meta.timestamp_ms == 1704067200000
        assert old_meta.session_id == "test_session"
        assert old_meta.run_id == "test_run"
        assert old_meta.mode == "DEV"
        assert old_meta.observer_version == "v1.0.0"
        
        # Check that new fields have default values
        assert old_meta.iteration_id is None
        assert old_meta.loop_interval_ms is None
        assert old_meta.latency_ms is None
        assert old_meta.tick_source is None
        assert old_meta.buffer_depth is None
        assert old_meta.flush_reason is None
        
        print("✓ Backward compatibility test passed")
    except Exception as e:
        print(f"✗ Backward compatibility test failed: {e}")
        return False
    
    # Test 4: JSON serialization works
    print("\nTest 4: JSON serialization")
    try:
        mock_provider = MockMarketDataProvider()
        runner = ObserverRunner(provider=mock_provider, interval_sec=0.1, max_iterations=1)
        
        snapshots = []
        runner._observer.on_snapshot = snapshots.append
        
        runner.run()
        
        snapshot = snapshots[0]
        
        # Test to_dict conversion
        snapshot_dict = snapshot.to_dict()
        
        # Check that meta fields are in the dict
        meta_dict = snapshot_dict['meta']
        assert 'iteration_id' in meta_dict
        assert 'loop_interval_ms' in meta_dict
        assert 'latency_ms' in meta_dict
        assert 'tick_source' in meta_dict
        assert 'buffer_depth' in meta_dict
        assert 'flush_reason' in meta_dict
        
        print("✓ JSON serialization test passed")
    except Exception as e:
        print(f"✗ JSON serialization test failed: {e}")
        return False
    
    print("\n✓ All extended meta fields tests passed!")
    return True

if __name__ == "__main__":
    success = test_extended_meta_fields()
    sys.exit(0 if success else 1)
