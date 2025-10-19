"""
Unit tests for LogDirectoryManager.

Tests log directory structure creation and metadata.
"""
import pytest
from pathlib import Path
import json
from backend.src.basis_strategy_v1.infrastructure.logging.log_directory_manager import (
    LogDirectoryManager
)

class TestLogDirectoryManager:
    """Test log directory management."""
    
    def test_create_run_logs(self, tmp_path):
        """Test log directory creation."""
        log_dir = LogDirectoryManager.create_run_logs(
            correlation_id="test123",
            pid=12345,
            mode="pure_lending_usdt",
            strategy="pure_lending",
            capital=10000.0,
            base_dir=tmp_path
        )
        
        # Verify directory structure
        assert log_dir.exists()
        assert (log_dir / "events").exists()
        assert (log_dir / "metadata.json").exists()
        
        # Verify parent metadata file exists
        assert (log_dir.parent / "run_metadata.json").exists()
        
        # Verify directory path structure
        expected_path = tmp_path / "test123" / "12345"
        assert log_dir == expected_path
    
    def test_metadata_contents(self, tmp_path):
        """Test metadata file contents."""
        log_dir = LogDirectoryManager.create_run_logs(
            correlation_id="test123",
            pid=12345,
            mode="pure_lending_usdt",
            strategy="pure_lending",
            capital=10000.0,
            base_dir=tmp_path
        )
        
        # Read metadata file
        metadata_file = log_dir / "metadata.json"
        assert metadata_file.exists()
        
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        # Verify required fields
        assert metadata["correlation_id"] == "test123"
        assert metadata["pid"] == 12345
        assert metadata["mode"] == "pure_lending_usdt"
        assert metadata["strategy"] == "pure_lending"
        assert metadata["initial_capital"] == 10000.0
        assert "start_time" in metadata
        assert "log_directory" in metadata
        assert "events_directory" in metadata
    
    def test_directory_permissions(self, tmp_path):
        """Test directory has correct permissions."""
        log_dir = LogDirectoryManager.create_run_logs(
            correlation_id="test123",
            pid=12345,
            mode="pure_lending_usdt",
            strategy="pure_lending",
            capital=10000.0,
            base_dir=tmp_path
        )
        
        # Verify directories are writable
        assert log_dir.is_dir()
        assert (log_dir / "events").is_dir()
        
        # Test that we can write to the directory
        test_file = log_dir / "test_write.txt"
        test_file.write_text("test")
        assert test_file.exists()
        test_file.unlink()  # Clean up

# TODO: Add tests for:
# - multiple runs with same correlation_id
# - invalid parameters
# - cleanup functionality
