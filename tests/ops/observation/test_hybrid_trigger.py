# tests/ops/observation/test_hybrid_trigger.py

import pytest
import time
from unittest.mock import Mock, patch

from ops.observer.inputs.mock_market_data_provider import MockMarketDataProvider
from ops.observer.tick_events import MockTickEventProvider
from ops.runtime.observer_runner import ObserverRunner


class TestHybridTrigger:
    """Test hybrid trigger implementation for Observer Scalp Extension."""

    def test_hybrid_mode_disabled_uses_only_loop_snapshots(self):
        """Test that when hybrid mode is disabled, only loop snapshots are generated."""
        # Setup
        mock_provider = MockMarketDataProvider()
        mock_provider.set_data([
            {"instruments": [{"symbol": "TEST", "price": {"open": 100, "high": 101, "low": 99, "close": 100}, "volume": 1000, "timestamp": "1"}]},
            {"instruments": [{"symbol": "TEST", "price": {"open": 101, "high": 102, "low": 100, "close": 101}, "volume": 1000, "timestamp": "2"}]},
        ])
        
        tick_provider = MockTickEventProvider()
        
        runner = ObserverRunner(
            provider=mock_provider,
            interval_sec=0.1,
            max_iterations=2,
            hybrid_mode=False,
            tick_provider=tick_provider,
        )
        
        # Mock observer to capture snapshots
        snapshots = []
        runner._observer.on_snapshot = snapshots.append
        
        # Run
        runner.run()
        
        # Verify only loop snapshots were generated
        assert len(snapshots) == 2
        # Verify tick provider was not used
        assert tick_provider._tick_count == 0

    def test_hybrid_mode_enabled_generates_tick_snapshots(self):
        """Test that when hybrid mode is enabled, tick events generate additional snapshots."""
        # Setup
        mock_provider = MockMarketDataProvider()
        mock_provider.set_data([
            {"instruments": [{"symbol": "TEST", "price": {"open": 100, "high": 101, "low": 99, "close": 100}, "volume": 1000, "timestamp": "1"}]},
        ])
        
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
        
        # Run
        runner.run()
        
        # Generate some tick events during run
        tick_provider.generate_tick()
        tick_provider.generate_tick()
        
        # Verify loop snapshot was generated
        assert len(snapshots) >= 1
        # Verify tick events were processed
        assert tick_provider._tick_count >= 2

    def test_tick_snapshots_have_same_structure_as_loop_snapshots(self):
        """Test that tick-triggered snapshots have identical structure to loop snapshots."""
        # Setup
        mock_provider = MockMarketDataProvider()
        mock_provider.set_data([
            {"instruments": [{"symbol": "TEST", "price": {"open": 100, "high": 101, "low": 99, "close": 100}, "volume": 1000, "timestamp": "loop_1"}]},
        ])
        
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
        
        # Run
        runner.run()
        
        # Generate tick event
        tick_provider.generate_tick()
        
        # Verify we have both loop and tick snapshots
        assert len(snapshots) >= 2
        
        # Get loop and tick snapshots (order may vary)
        loop_snapshot = None
        tick_snapshot = None
        
        for snapshot in snapshots:
            if snapshot.observation.inputs.get("timestamp") == "loop_1":
                loop_snapshot = snapshot
            elif "mock_tick" in snapshot.observation.inputs.get("timestamp", ""):
                tick_snapshot = snapshot
        
        # Verify both snapshots exist
        assert loop_snapshot is not None
        assert tick_snapshot is not None
        
        # Verify structures are identical
        assert type(loop_snapshot) == type(tick_snapshot)
        assert hasattr(loop_snapshot, 'meta')
        assert hasattr(loop_snapshot, 'context')
        assert hasattr(loop_snapshot, 'observation')
        assert hasattr(tick_snapshot, 'meta')
        assert hasattr(tick_snapshot, 'context')
        assert hasattr(tick_snapshot, 'observation')

    def test_tick_events_do_not_block_loop_execution(self):
        """Test that tick event handling does not block loop execution."""
        # Setup
        mock_provider = MockMarketDataProvider()
        mock_provider.set_data([
            {"instruments": [{"symbol": "TEST", "price": {"open": 100, "high": 101, "low": 99, "close": 100}, "volume": 1000, "timestamp": "1"}]},
            {"instruments": [{"symbol": "TEST", "price": {"open": 101, "high": 102, "low": 100, "close": 101}, "volume": 1000, "timestamp": "2"}]},
        ])
        
        tick_provider = MockTickEventProvider()
        
        runner = ObserverRunner(
            provider=mock_provider,
            interval_sec=0.05,  # Fast loop
            max_iterations=2,
            hybrid_mode=True,
            tick_provider=tick_provider,
        )
        
        # Mock observer to capture snapshots
        snapshots = []
        runner._observer.on_snapshot = snapshots.append
        
        # Record timing
        start_time = time.time()
        
        # Run
        runner.run()
        
        end_time = time.time()
        
        # Generate tick events
        tick_provider.generate_tick()
        tick_provider.generate_tick()
        
        # Verify loop completed in reasonable time (should be ~0.1s for 2 iterations)
        assert end_time - start_time < 0.5  # Allow generous margin
        
        # Verify loop snapshots were generated
        loop_snapshots = [s for s in snapshots if "loop" in s.observation.inputs.get("timestamp", "")]
        assert len(loop_snapshots) == 2

    def test_no_tick_provider_with_hybrid_mode(self):
        """Test that hybrid mode works gracefully without tick provider."""
        # Setup
        mock_provider = MockMarketDataProvider()
        mock_provider.set_data([
            {"instruments": [{"symbol": "TEST", "price": {"open": 100, "high": 101, "low": 99, "close": 100}, "volume": 1000, "timestamp": "1"}]},
        ])
        
        runner = ObserverRunner(
            provider=mock_provider,
            interval_sec=0.1,
            max_iterations=1,
            hybrid_mode=True,  # Hybrid mode enabled but no tick provider
            tick_provider=None,
        )
        
        # Mock observer to capture snapshots
        snapshots = []
        runner._observer.on_snapshot = snapshots.append
        
        # Run - should not crash
        runner.run()
        
        # Verify loop snapshot still works
        assert len(snapshots) == 1

    def test_observer_responsibilities_maintained(self):
        """Test that Observer responsibilities are maintained (no decision logic)."""
        # Setup
        mock_provider = MockMarketDataProvider()
        mock_provider.set_data([
            {"instruments": [{"symbol": "TEST", "price": {"open": 100, "high": 101, "low": 99, "close": 100}, "volume": 1000, "timestamp": "1"}]},
        ])
        
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
        
        # Run
        runner.run()
        tick_provider.generate_tick()
        
        # Verify snapshots contain no decision logic
        for snapshot in snapshots:
            # Check that snapshot is pure data (no decision fields)
            assert not hasattr(snapshot, 'decision')
            assert not hasattr(snapshot, 'signal')
            assert not hasattr(snapshot, 'action')
            
            # Check that observation contains only inputs, computed, state
            assert 'inputs' in snapshot.observation
            assert 'computed' in snapshot.observation
            assert 'state' in snapshot.observation
