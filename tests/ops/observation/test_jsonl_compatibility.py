#!/usr/bin/env python3
"""
Test to verify JSONL backward compatibility.
"""

import sys
import os
import json
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_jsonl_backward_compatibility():
    """Test that old JSONL data can still be read with new meta fields."""
    print("Testing JSONL backward compatibility...")
    
    try:
        from ops.observer.snapshot import ObservationSnapshot, Meta, Context, Observation
        print("✓ Imports successful")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Create old-style snapshot data (without extended meta fields)
    old_snapshot_data = {
        "meta": {
            "timestamp": "2025-01-01T00:00:00.000Z",
            "timestamp_ms": 1704067200000,
            "session_id": "test_session",
            "run_id": "test_run",
            "mode": "DEV",
            "observer_version": "v1.0.0",
        },
        "context": {
            "source": "market",
            "stage": "raw",
            "symbol": "TEST",
            "market": "KRX",
        },
        "observation": {
            "inputs": {
                "price": {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
                "volume": 1000,
                "timestamp": "2025-01-01T00:00:00.000Z",
            },
            "computed": {},
            "state": {},
        },
    }
    
    # Test 1: Create Meta from old data
    print("\nTest 1: Create Meta from old data")
    try:
        old_meta_dict = old_snapshot_data["meta"]
        
        # Create Meta with old data (should work with new fields as None)
        meta = Meta(**old_meta_dict)
        
        # Check old fields
        assert meta.timestamp == "2025-01-01T00:00:00.000Z"
        assert meta.timestamp_ms == 1704067200000
        assert meta.session_id == "test_session"
        assert meta.run_id == "test_run"
        assert meta.mode == "DEV"
        assert meta.observer_version == "v1.0.0"
        
        # Check new fields are None
        assert meta.iteration_id is None
        assert meta.loop_interval_ms is None
        assert meta.latency_ms is None
        assert meta.tick_source is None
        assert meta.buffer_depth is None
        assert meta.flush_reason is None
        
        print("✓ Meta creation from old data test passed")
    except Exception as e:
        print(f"✗ Meta creation from old data test failed: {e}")
        return False
    
    # Test 2: Create full ObservationSnapshot from old data
    print("\nTest 2: Create ObservationSnapshot from old data")
    try:
        # Create components
        meta = Meta(**old_snapshot_data["meta"])
        context = Context(**old_snapshot_data["context"])
        observation = Observation(**old_snapshot_data["observation"])
        
        # Create snapshot
        snapshot = ObservationSnapshot(
            meta=meta,
            context=context,
            observation=observation,
        )
        
        # Check that snapshot is valid
        assert snapshot.meta.timestamp == "2025-01-01T00:00:00.000Z"
        assert snapshot.context.source == "market"
        assert snapshot.observation.inputs["price"]["open"] == 100.0
        
        print("✓ ObservationSnapshot creation from old data test passed")
    except Exception as e:
        print(f"✗ ObservationSnapshot creation from old data test failed: {e}")
        return False
    
    # Test 3: JSONL round-trip compatibility
    print("\nTest 3: JSONL round-trip compatibility")
    try:
        # Create new-style snapshot with extended fields
        from ops.observer.inputs.mock_market_data_provider import MockMarketDataProvider
        from ops.runtime.observer_runner import ObserverRunner
        
        mock_provider = MockMarketDataProvider()
        runner = ObserverRunner(provider=mock_provider, interval_sec=0.1, max_iterations=1)
        
        snapshots = []
        runner._observer.on_snapshot = snapshots.append
        
        runner.run()
        
        new_snapshot = snapshots[0]
        
        # Convert to dict and back to JSONL
        new_snapshot_dict = new_snapshot.to_dict()
        jsonl_line = json.dumps(new_snapshot_dict)
        
        # Parse back from JSONL
        parsed_dict = json.loads(jsonl_line)
        
        # Recreate snapshot from parsed data
        parsed_meta = Meta(**parsed_dict["meta"])
        parsed_context = Context(**parsed_dict["context"])
        parsed_observation = Observation(**parsed_dict["observation"])
        
        parsed_snapshot = ObservationSnapshot(
            meta=parsed_meta,
            context=parsed_context,
            observation=parsed_observation,
        )
        
        # Check that extended fields are preserved
        assert parsed_snapshot.meta.iteration_id is not None
        assert parsed_snapshot.meta.tick_source == "loop"
        assert parsed_snapshot.meta.latency_ms is not None
        
        print("✓ JSONL round-trip compatibility test passed")
    except Exception as e:
        print(f"✗ JSONL round-trip compatibility test failed: {e}")
        return False
    
    # Test 4: Mixed old and new data in same file
    print("\nTest 4: Mixed old and new data compatibility")
    try:
        # Create temporary JSONL file with mixed data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            # Write old-style snapshot
            json.dump(old_snapshot_data, f)
            f.write('\n')
            
            # Write new-style snapshot
            new_snapshot_dict = snapshots[0].to_dict()
            json.dump(new_snapshot_dict, f)
            f.write('\n')
            
            temp_file = f.name
        
        # Read and parse both snapshots
        parsed_snapshots = []
        with open(temp_file, 'r') as f:
            for line in f:
                data = json.loads(line.strip())
                
                # Parse meta (should work for both old and new)
                meta = Meta(**data["meta"])
                context = Context(**data["context"])
                observation = Observation(**data["observation"])
                
                snapshot = ObservationSnapshot(
                    meta=meta,
                    context=context,
                    observation=observation,
                )
                
                parsed_snapshots.append(snapshot)
        
        # Check we have both snapshots
        assert len(parsed_snapshots) == 2
        
        # Check old snapshot (first one)
        old_parsed = parsed_snapshots[0]
        assert old_parsed.meta.iteration_id is None
        assert old_parsed.meta.tick_source is None
        
        # Check new snapshot (second one)
        new_parsed = parsed_snapshots[1]
        assert new_parsed.meta.iteration_id is not None
        assert new_parsed.meta.tick_source == "loop"
        
        # Clean up
        os.unlink(temp_file)
        
        print("✓ Mixed old and new data compatibility test passed")
    except Exception as e:
        print(f"✗ Mixed old and new data compatibility test failed: {e}")
        return False
    
    print("\n✓ All JSONL backward compatibility tests passed!")
    return True

if __name__ == "__main__":
    success = test_jsonl_backward_compatibility()
    sys.exit(0 if success else 1)
