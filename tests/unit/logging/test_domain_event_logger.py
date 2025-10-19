"""
Unit tests for DomainEventLogger.

Tests JSONL event file writing and buffering.
"""
import pytest
from pathlib import Path
import json
from backend.src.basis_strategy_v1.infrastructure.logging.domain_event_logger import (
    DomainEventLogger
)
from backend.src.basis_strategy_v1.core.models.domain_events import PositionSnapshot

class TestDomainEventLogger:
    """Test domain event logging."""
    
    def test_log_position_snapshot(self, tmp_path):
        """Test logging position snapshot to JSONL."""
        logger = DomainEventLogger(
            log_dir=tmp_path,
            correlation_id="test123",
            pid=12345
        )
        
        snapshot = PositionSnapshot(
            timestamp="2025-01-15T10:30:00",
            real_utc_time="2025-01-15T10:30:00.123456",
            correlation_id="test123",
            pid=12345,
            positions={"aave:aToken:aUSDT": 10000.0},
            total_value_usd=10000.0,
            position_type="simulated"
        )
        
        logger.log_position_snapshot(snapshot)
        
        # Verify JSONL file created
        events_file = tmp_path / "events" / "positions.jsonl"
        assert events_file.exists()
        
        # Verify content
        with open(events_file) as f:
            line = f.readline()
            event = json.loads(line)
            assert event["correlation_id"] == "test123"
            assert event["pid"] == 12345
            assert event["positions"]["aave:aToken:aUSDT"] == 10000.0
            assert event["total_value_usd"] == 10000.0
            assert event["position_type"] == "simulated"
    
    def test_buffered_writing(self, tmp_path):
        """Test event buffering and flushing."""
        logger = DomainEventLogger(
            log_dir=tmp_path,
            correlation_id="test123",
            pid=12345
        )
        
        # Create multiple snapshots
        snapshots = []
        for i in range(3):
            snapshot = PositionSnapshot(
                timestamp=f"2025-01-15T10:30:{i:02d}",
                real_utc_time=f"2025-01-15T10:30:{i:02d}.123456",
                correlation_id="test123",
                pid=12345,
                positions={"aave:aToken:aUSDT": 10000.0 + i * 1000},
                total_value_usd=10000.0 + i * 1000,
                position_type="simulated"
            )
            snapshots.append(snapshot)
            logger.log_position_snapshot(snapshot)
        
        # Verify all events were written
        events_file = tmp_path / "events" / "positions.jsonl"
        assert events_file.exists()
        
        with open(events_file) as f:
            lines = f.readlines()
            assert len(lines) == 3
            
            for i, line in enumerate(lines):
                event = json.loads(line)
                assert event["total_value_usd"] == 10000.0 + i * 1000
    
    def test_multiple_event_types(self, tmp_path):
        """Test logging different event types."""
        logger = DomainEventLogger(
            log_dir=tmp_path,
            correlation_id="test123",
            pid=12345
        )
        
        # Test position snapshot
        position_snapshot = PositionSnapshot(
            timestamp="2025-01-15T10:30:00",
            real_utc_time="2025-01-15T10:30:00.123456",
            correlation_id="test123",
            pid=12345,
            positions={"aave:aToken:aUSDT": 10000.0},
            total_value_usd=10000.0,
            position_type="simulated"
        )
        logger.log_position_snapshot(position_snapshot)
        
        # Test exposure snapshot
        from backend.src.basis_strategy_v1.core.models.domain_events import ExposureSnapshot
        exposure_snapshot = ExposureSnapshot(
            timestamp="2025-01-15T10:30:00",
            real_utc_time="2025-01-15T10:30:00.123456",
            correlation_id="test123",
            pid=12345,
            net_delta_usd=0.0,
            asset_exposures={"USDT": {"quantity": 10000.0, "usd_value": 10000.0, "percentage": 1.0}},
            total_value_usd=10000.0,
            share_class_value=10000.0
        )
        logger.log_exposure_snapshot(exposure_snapshot)
        
        # Verify both files exist
        positions_file = tmp_path / "events" / "positions.jsonl"
        exposures_file = tmp_path / "events" / "exposures.jsonl"
        
        assert positions_file.exists()
        assert exposures_file.exists()
        
        # Verify content counts
        with open(positions_file) as f:
            position_lines = f.readlines()
            assert len(position_lines) == 1
            
        with open(exposures_file) as f:
            exposure_lines = f.readlines()
            assert len(exposure_lines) == 1

# TODO: Add tests for:
# - all 12 event types
# - buffer overflow
# - concurrent writes
# - error handling
