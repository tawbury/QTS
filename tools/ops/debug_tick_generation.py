#!/usr/bin/env python3
"""
Debug tick generation issue.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_tick_generation():
    """Debug tick generation to understand the issue."""
    print("Debugging tick generation...")
    
    try:
        from ops.observer.inputs.mock_market_data_provider import MockMarketDataProvider
        from ops.observer.tick_events import MockTickEventProvider
        from ops.runtime.observer_runner import ObserverRunner
        print("✓ Imports successful")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Setup
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
    
    print(f"Before run - tick count: {tick_provider._tick_count}")
    print(f"Before run - running: {tick_provider._running}")
    
    # Run with auto-generated ticks
    runner.run(auto_generate_test_ticks=True)
    
    print(f"After run - tick count: {tick_provider._tick_count}")
    print(f"After run - running: {tick_provider._running}")
    print(f"Total snapshots: {len(snapshots)}")
    
    # Print snapshot details
    for i, snapshot in enumerate(snapshots):
        print(f"Snapshot {i}: tick_source={snapshot.meta.tick_source}, iteration_id={snapshot.meta.iteration_id}")
    
    # Try manual tick generation
    print("\nTrying manual tick generation...")
    tick_provider.generate_tick()
    print(f"After manual tick - tick count: {tick_provider._tick_count}")
    print(f"Total snapshots after manual tick: {len(snapshots)}")
    
    return True

if __name__ == "__main__":
    debug_tick_generation()
