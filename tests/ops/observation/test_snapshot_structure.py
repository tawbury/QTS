#!/usr/bin/env python3
"""
Test to verify that loop and tick snapshots have identical structures.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_snapshot_structure_identity():
    """Test that loop and tick snapshots have identical structures."""
    print("Testing snapshot structure identity...")
    
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
    
    # Run with auto-generated ticks
    runner.run(auto_generate_test_ticks=True)
    
    # Verify we have snapshots
    assert len(snapshots) >= 2, f"Expected at least 2 snapshots, got {len(snapshots)}"
    print(f"✓ Generated {len(snapshots)} snapshots")
    
    # Analyze snapshot structures
    loop_snapshots = []
    tick_snapshots = []
    
    for snapshot in snapshots:
        timestamp = snapshot.observation.inputs.get("timestamp", "")
        if "mock_tick" in timestamp:
            tick_snapshots.append(snapshot)
        else:
            loop_snapshots.append(snapshot)
    
    assert len(loop_snapshots) >= 1, f"Expected at least 1 loop snapshot, got {len(loop_snapshots)}"
    assert len(tick_snapshots) >= 1, f"Expected at least 1 tick snapshot, got {len(tick_snapshots)}"
    print(f"✓ Found {len(loop_snapshots)} loop snapshots and {len(tick_snapshots)} tick snapshots")
    
    # Compare structures
    loop_snapshot = loop_snapshots[0]
    tick_snapshot = tick_snapshots[0]
    
    # Check type identity
    assert type(loop_snapshot) == type(tick_snapshot), "Snapshot types should be identical"
    print("✓ Snapshot types are identical")
    
    # Check attribute presence
    loop_attrs = set(dir(loop_snapshot))
    tick_attrs = set(dir(tick_snapshot))
    
    common_attrs = loop_attrs & tick_attrs
    missing_in_tick = loop_attrs - tick_attrs
    missing_in_loop = tick_attrs - loop_attrs
    
    assert missing_in_tick == set(), f"Tick snapshot missing attributes: {missing_in_tick}"
    assert missing_in_loop == set(), f"Loop snapshot missing attributes: {missing_in_loop}"
    print("✓ All attributes are present in both snapshot types")
    
    # Check core structure
    core_attrs = ['meta', 'context', 'observation']
    for attr in core_attrs:
        assert hasattr(loop_snapshot, attr), f"Loop snapshot missing {attr}"
        assert hasattr(tick_snapshot, attr), f"Tick snapshot missing {attr}"
        assert type(getattr(loop_snapshot, attr)) == type(getattr(tick_snapshot, attr)), f"Type mismatch for {attr}"
    
    print("✓ Core structures are identical")
    
    # Check observation structure
    loop_obs = loop_snapshot.observation
    tick_obs = tick_snapshot.observation
    
    # Check dataclass fields
    import dataclasses
    loop_fields = set(f.name for f in dataclasses.fields(loop_obs))
    tick_fields = set(f.name for f in dataclasses.fields(tick_obs))
    
    assert loop_fields == tick_fields, f"Observation fields differ: loop={loop_fields}, tick={tick_fields}"
    print("✓ Observation structures are identical")
    
    # Check field types
    for field_name in loop_fields:
        loop_field_type = type(getattr(loop_obs, field_name))
        tick_field_type = type(getattr(tick_obs, field_name))
        assert loop_field_type == tick_field_type, f"Type mismatch for observation field {field_name}"
    
    print("✓ Observation field types are identical")
    
    # Check that no decision logic is present
    for snapshot in snapshots:
        # Check that snapshot is pure data (no decision fields)
        decision_fields = ['decision', 'signal', 'action', 'trade', 'order']
        for field in decision_fields:
            assert not hasattr(snapshot, field), f"Snapshot should not have {field} field"
    
    print("✓ No decision logic present in snapshots")
    
    print("\n✓ All structure identity tests passed!")
    return True

if __name__ == "__main__":
    success = test_snapshot_structure_identity()
    sys.exit(0 if success else 1)
