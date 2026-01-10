#!/usr/bin/env python3
"""
Simple validation script for hybrid trigger implementation.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_hybrid_trigger_basic():
    """Basic test of hybrid trigger functionality."""
    print("Testing hybrid trigger implementation...")
    
    try:
        from ops.observer.inputs.mock_market_data_provider import MockMarketDataProvider
        from ops.observer.tick_events import MockTickEventProvider
        from ops.runtime.observer_runner import ObserverRunner
        print("✓ Imports successful")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Test 1: Hybrid mode disabled
    print("\nTest 1: Hybrid mode disabled")
    try:
        mock_provider = MockMarketDataProvider()
        tick_provider = MockTickEventProvider()
        
        runner = ObserverRunner(
            provider=mock_provider,
            interval_sec=0.1,
            max_iterations=1,
            hybrid_mode=False,
            tick_provider=tick_provider,
        )
        
        # Mock observer to capture snapshots
        snapshots = []
        runner._observer.on_snapshot = snapshots.append
        
        runner.run()
        
        assert len(snapshots) == 1, f"Expected 1 snapshot, got {len(snapshots)}"
        assert tick_provider._tick_count == 0, f"Expected 0 tick events, got {tick_provider._tick_count}"
        print("✓ Hybrid mode disabled test passed")
    except Exception as e:
        print(f"✗ Hybrid mode disabled test failed: {e}")
        return False
    
    # Test 2: Hybrid mode enabled
    print("\nTest 2: Hybrid mode enabled")
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
        
        assert len(snapshots) >= 1, f"Expected at least 1 snapshot, got {len(snapshots)}"
        assert tick_provider._tick_count >= 1, f"Expected at least 1 tick event, got {tick_provider._tick_count}"
        print("✓ Hybrid mode enabled test passed")
    except Exception as e:
        print(f"✗ Hybrid mode enabled test failed: {e}")
        return False
    
    # Test 3: No tick provider with hybrid mode
    print("\nTest 3: No tick provider with hybrid mode")
    try:
        mock_provider = MockMarketDataProvider()
        
        runner = ObserverRunner(
            provider=mock_provider,
            interval_sec=0.1,
            max_iterations=1,
            hybrid_mode=True,
            tick_provider=None,
        )
        
        # Mock observer to capture snapshots
        snapshots = []
        runner._observer.on_snapshot = snapshots.append
        
        runner.run()
        
        assert len(snapshots) == 1, f"Expected 1 snapshot, got {len(snapshots)}"
        print("✓ No tick provider test passed")
    except Exception as e:
        print(f"✗ No tick provider test failed: {e}")
        return False
    
    print("\n✓ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_hybrid_trigger_basic()
    sys.exit(0 if success else 1)
