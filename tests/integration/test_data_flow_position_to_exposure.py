"""
Integration test for Position → Exposure data flow.

Tests the data flow from Position Monitor to Exposure Monitor per WORKFLOW_GUIDE.md.
"""

import pytest
from datetime import datetime, timedelta


class TestDataFlowPositionToExposure:
    """Test Position → Exposure data flow integration."""
    
    def test_position_to_exposure_data_flow(self, real_components, real_data_provider):
        """Test complete data flow from position collection to exposure calculation."""
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        
        # Step 1: Position Monitor collects positions
        positions = position_monitor.collect_positions()
        
        assert positions is not None
        assert len(positions) > 0
        
        # Step 2: Exposure Monitor processes positions
        exposures = exposure_monitor.calculate_exposures(positions)
        
        assert exposures is not None
        assert len(exposures) > 0
        
        # Step 3: Verify data flow integrity
        for exposure in exposures:
            assert "asset" in exposure
            assert "total_exposure" in exposure
            assert "net_delta" in exposure
            assert "venue_breakdown" in exposure
    
    def test_position_state_persistence_to_exposure(self, real_components, real_data_provider):
        """Test that position state persistence flows correctly to exposure calculations."""
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        
        # Step 1: Collect and persist positions
        positions = position_monitor.collect_positions()
        position_monitor.persist_state()
        
        # Step 2: Load persisted state and calculate exposures
        loaded_positions = position_monitor.load_state()
        exposures = exposure_monitor.calculate_exposures(loaded_positions)
        
        # Step 3: Verify consistency
        assert len(positions) == len(loaded_positions)
        assert len(exposures) > 0
        
        # Verify exposure calculations are consistent with position data
        for exposure in exposures:
            asset = exposure["asset"]
            position_sum = sum(pos["size"] for pos in loaded_positions if pos["asset"] == asset)
            assert abs(exposure["total_exposure"] - position_sum) < 0.01  # Allow for rounding
    
    def test_position_venue_aggregation_to_exposure(self, real_components, real_data_provider):
        """Test that position venue aggregation flows correctly to exposure venue breakdown."""
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        
        # Step 1: Collect positions with venue information
        positions = position_monitor.collect_positions()
        
        # Step 2: Calculate exposures with venue breakdown
        exposures = exposure_monitor.calculate_exposures(positions)
        
        # Step 3: Verify venue aggregation
        for exposure in exposures:
            venue_breakdown = exposure["venue_breakdown"]
            assert isinstance(venue_breakdown, dict)
            
            # Verify venue totals match position venue totals
            total_from_venues = sum(venue_breakdown.values())
            assert abs(exposure["total_exposure"] - total_from_venues) < 0.01
    
    def test_position_asset_filtering_to_exposure(self, real_components, real_data_provider):
        """Test that position asset filtering flows correctly to exposure asset filtering."""
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        
        # Step 1: Collect positions for specific asset
        target_asset = "USDT"
        positions = position_monitor.collect_positions()
        filtered_positions = [pos for pos in positions if pos["asset"] == target_asset]
        
        # Step 2: Calculate exposures for filtered positions
        exposures = exposure_monitor.calculate_exposures(filtered_positions)
        
        # Step 3: Verify only target asset appears in exposures
        exposure_assets = [exp["asset"] for exp in exposures]
        assert all(asset == target_asset for asset in exposure_assets)
    
    def test_position_timestamp_flow_to_exposure(self, real_components, real_data_provider):
        """Test that position timestamps flow correctly to exposure timestamps."""
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        
        # Step 1: Collect positions with timestamps
        positions = position_monitor.collect_positions()
        
        # Step 2: Calculate exposures
        exposures = exposure_monitor.calculate_exposures(positions)
        
        # Step 3: Verify timestamp consistency
        for exposure in exposures:
            assert "timestamp" in exposure
            exposure_time = datetime.fromisoformat(exposure["timestamp"])
            
            # Exposure timestamp should be recent (within last minute)
            now = datetime.now()
            time_diff = abs((now - exposure_time).total_seconds())
            assert time_diff < 60  # Within 1 minute
    
    def test_position_error_handling_to_exposure(self, real_components, real_data_provider):
        """Test that position errors are handled correctly in exposure calculations."""
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        
        # Step 1: Simulate position collection error
        with pytest.raises(Exception):
            # This should trigger error handling in position monitor
            invalid_positions = position_monitor.collect_positions(invalid_param=True)
        
        # Step 2: Verify exposure monitor handles empty/invalid positions gracefully
        empty_positions = []
        exposures = exposure_monitor.calculate_exposures(empty_positions)
        
        # Should return empty list or handle gracefully
        assert isinstance(exposures, list)
    
    def test_position_data_validation_to_exposure(self, real_components, real_data_provider):
        """Test that position data validation flows correctly to exposure validation."""
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        
        # Step 1: Collect positions
        positions = position_monitor.collect_positions()
        
        # Step 2: Validate position data structure
        for position in positions:
            assert "asset" in position
            assert "size" in position
            assert "venue" in position
            assert "timestamp" in position
            assert isinstance(position["size"], (int, float))
            assert position["size"] >= 0
        
        # Step 3: Calculate exposures and validate structure
        exposures = exposure_monitor.calculate_exposures(positions)
        
        for exposure in exposures:
            assert "asset" in exposure
            assert "total_exposure" in exposure
            assert "net_delta" in exposure
            assert "venue_breakdown" in exposure
            assert isinstance(exposure["total_exposure"], (int, float))
            assert exposure["total_exposure"] >= 0
    
    def test_position_to_exposure_performance(self, real_components, real_data_provider):
        """Test performance of position to exposure data flow."""
        import time
        
        position_monitor = real_components["position_monitor"]
        exposure_monitor = real_components["exposure_monitor"]
        
        # Step 1: Measure position collection time
        start_time = time.time()
        positions = position_monitor.collect_positions()
        position_time = time.time() - start_time
        
        # Step 2: Measure exposure calculation time
        start_time = time.time()
        exposures = exposure_monitor.calculate_exposures(positions)
        exposure_time = time.time() - start_time
        
        # Step 3: Verify performance is within acceptable limits
        assert position_time < 5.0  # Position collection should be fast
        assert exposure_time < 2.0  # Exposure calculation should be fast
        
        # Step 4: Verify data flow produces results
        assert len(positions) > 0
        assert len(exposures) > 0
