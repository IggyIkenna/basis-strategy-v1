"""
Unit tests for ConfigManager - Configuration loading and validation
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import sys
import yaml

# Add the backend src to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend" / "src"))

from basis_strategy_v1.infrastructure.config.config_manager import ConfigManager, get_config_manager
from basis_strategy_v1.infrastructure.config.models import ConfigurationValidationError


class TestConfigLoadingValidation:
    """Test configuration loading and validation functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear any existing instance
        ConfigManager._instance = None
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create test environment files
        self._create_test_env_files()
        
        # Create test configuration files
        self._create_test_config_files()
    
    def teardown_method(self):
        """Clean up test environment."""
        # Clear environment variables
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_') or key in ['HEALTH_CHECK_INTERVAL', 'HEALTH_CHECK_ENDPOINT']:
                del os.environ[key]
        
        # Clear singleton instance
        ConfigManager._instance = None
    
    def _create_test_env_files(self):
        """Create test environment files."""
        # Create env.unified
        unified_content = """# Base environment variables
BASIS_ENVIRONMENT=
BASIS_DEPLOYMENT_MODE=
BASIS_DEPLOYMENT_MACHINE=
BASIS_DATA_DIR=
BASIS_DATA_MODE=
BASIS_RESULTS_DIR=
BASIS_DEBUG=
BASIS_LOG_LEVEL=
BASIS_EXECUTION_MODE=
BASIS_DATA_START_DATE=
BASIS_DATA_END_DATE=
HEALTH_CHECK_INTERVAL=
HEALTH_CHECK_ENDPOINT=
BASIS_API_PORT=
BASIS_API_HOST=
BASIS_API_CORS_ORIGINS=
"""
        (self.temp_path / "env.unified").write_text(unified_content)
        
        # Create env.dev
        dev_content = """# Development environment
BASIS_ENVIRONMENT=dev
BASIS_DEPLOYMENT_MODE=local
BASIS_DEPLOYMENT_MACHINE=local_mac
BASIS_DATA_DIR=/test/data
BASIS_DATA_MODE=csv
BASIS_RESULTS_DIR=/test/results
BASIS_DEBUG=true
BASIS_LOG_LEVEL=DEBUG
BASIS_EXECUTION_MODE=backtest
BASIS_DATA_START_DATE=2024-01-01
BASIS_DATA_END_DATE=2024-12-31
HEALTH_CHECK_INTERVAL=30s
HEALTH_CHECK_ENDPOINT=/health
BASIS_API_PORT=8001
BASIS_API_HOST=0.0.0.0
BASIS_API_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
"""
        (self.temp_path / "env.dev").write_text(dev_content)
    
    def _create_test_config_files(self):
        """Create test configuration files."""
        # Create configs directory structure
        (self.temp_path / "configs" / "modes").mkdir(parents=True)
        (self.temp_path / "configs" / "venues").mkdir(parents=True)
        (self.temp_path / "configs" / "share_classes").mkdir(parents=True)
        
        # Create test mode config
        mode_config = {
            "mode": "pure_lending_usdt",  # Use valid mode name
            "share_class": "USDT",
            "asset": "USDT",
            "enable_market_impact": True,
            "lending_enabled": True,
            "staking_enabled": False,
            "basis_trade_enabled": False,
            "borrowing_enabled": False,
            "leverage_enabled": False,
            "rewards_mode": "base_only",
            "position_deviation_threshold": 0.05,
            "margin_ratio_target": 1.0,
            "target_apy": 0.05,
            "time_throttle_interval": 60,
            "data_requirements": ["usdt_prices", "aave_lending_rates"],
            "event_logger": {
                "log_path": "./logs",
                "log_format": "json",
                "log_level": "INFO",
                "event_categories": {
                    "data": ["data_loaded", "data_updated", "data_error"],
                    "risk": ["risk_breach", "risk_warning", "risk_calculation"],
                    "event": ["event_logged", "event_filtered", "event_exported"],
                    "business": ["trade_executed", "position_updated", "strategy_decision"]
                },
                "event_logging_settings": {
                    "buffer_size": 10000,
                    "export_format": "both",
                    "async_logging": True,
                    "compression": False
                },
                "log_retention_policy": {
                    "retention_days": 30,
                    "max_file_size_mb": 100,
                    "rotation_frequency": "daily",
                    "compression_after_days": 7
                },
                "logging_requirements": {
                    "structured_logging": True,
                    "correlation_ids": True,
                    "performance_metrics": True,
                    "error_tracking": True
                },
                "event_filtering": {
                    "filter_by_level": True,
                    "filter_by_category": True,
                    "exclude_patterns": [],
                    "include_patterns": ["*"]
                }
            }
        }
        (self.temp_path / "configs" / "modes" / "pure_lending_usdt.yaml").write_text(yaml.dump(mode_config))
        
        # Create test venue config
        venue_config = {
            "venue": "binance",  # Use valid venue name
            "type": "cex",
            "max_leverage": 10.0,
            "min_order_size_usd": 10.0
        }
        (self.temp_path / "configs" / "venues" / "binance.yaml").write_text(yaml.dump(venue_config))
        
        # Create test share class config
        share_class_config = {
            "share_class": "USDT",
            "type": "stable",
            "base_currency": "USDT",
            "supported_strategies": ["pure_lending_usdt"],  # Use valid strategy name
            "leverage_supported": True
        }
        (self.temp_path / "configs" / "share_classes" / "usdt_stable.yaml").write_text(yaml.dump(share_class_config))
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_config_loading_success(self, mock_path):
        """Test successful configuration loading with Pydantic validation."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Set environment variables
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        os.environ['BASIS_DEPLOYMENT_MODE'] = 'local'
        os.environ['BASIS_DEPLOYMENT_MACHINE'] = 'local_mac'
        os.environ['BASIS_DATA_DIR'] = '/test/data'
        os.environ['BASIS_DATA_MODE'] = 'csv'
        os.environ['BASIS_RESULTS_DIR'] = '/test/results'
        os.environ['BASIS_DEBUG'] = 'true'
        os.environ['BASIS_LOG_LEVEL'] = 'DEBUG'
        os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
        os.environ['BASIS_DATA_START_DATE'] = '2024-01-01'
        os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
        os.environ['HEALTH_CHECK_INTERVAL'] = '30s'
        os.environ['HEALTH_CHECK_ENDPOINT'] = '/health'
        os.environ['BASIS_API_PORT'] = '8001'
        os.environ['BASIS_API_HOST'] = '0.0.0.0'
        os.environ['BASIS_API_CORS_ORIGINS'] = 'http://localhost:3000,http://localhost:5173'
        
        # Create config manager
        config_manager = ConfigManager()
        
        # Verify configurations are loaded and validated
        assert 'pure_lending_usdt' in config_manager.get_available_strategies()
        assert 'binance' in config_manager.config_cache['venues']
        assert 'usdt_stable' in config_manager.config_cache['share_classes']
        
        # Verify Pydantic validation worked
        mode_config = config_manager.get_mode_config('pure_lending_usdt')
        assert mode_config['mode'] == 'pure_lending_usdt'
        assert mode_config['share_class'] == 'USDT'
        assert mode_config['target_apy'] == 0.05
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_invalid_yaml_fails(self, mock_path):
        """Test that invalid YAML files cause validation failure."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Create invalid YAML file
        (self.temp_path / "configs" / "modes" / "invalid.yaml").write_text("invalid: yaml: content: [")
        
        # Set environment variables
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        os.environ['BASIS_DEPLOYMENT_MODE'] = 'local'
        os.environ['BASIS_DEPLOYMENT_MACHINE'] = 'local_mac'
        os.environ['BASIS_DATA_DIR'] = '/test/data'
        os.environ['BASIS_DATA_MODE'] = 'csv'
        os.environ['BASIS_RESULTS_DIR'] = '/test/results'
        os.environ['BASIS_DEBUG'] = 'true'
        os.environ['BASIS_LOG_LEVEL'] = 'DEBUG'
        os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
        os.environ['BASIS_DATA_START_DATE'] = '2024-01-01'
        os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
        os.environ['HEALTH_CHECK_INTERVAL'] = '30s'
        os.environ['HEALTH_CHECK_ENDPOINT'] = '/health'
        os.environ['BASIS_API_PORT'] = '8001'
        os.environ['BASIS_API_HOST'] = '0.0.0.0'
        os.environ['BASIS_API_CORS_ORIGINS'] = 'http://localhost:3000,http://localhost:5173'
        
        # Should fail with YAML parsing error
        with pytest.raises(ValueError, match="Failed to parse mode configuration"):
            ConfigManager()
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_missing_required_fields_fails(self, mock_path):
        """Test that missing required fields cause validation failure."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Create config with missing required fields
        invalid_mode_config = {
            "mode": "invalid_mode",
            "share_class": "USDT"
            # Missing required fields
        }
        (self.temp_path / "configs" / "modes" / "invalid_mode.yaml").write_text(yaml.dump(invalid_mode_config))
        
        # Set environment variables
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        os.environ['BASIS_DEPLOYMENT_MODE'] = 'local'
        os.environ['BASIS_DEPLOYMENT_MACHINE'] = 'local_mac'
        os.environ['BASIS_DATA_DIR'] = '/test/data'
        os.environ['BASIS_DATA_MODE'] = 'csv'
        os.environ['BASIS_RESULTS_DIR'] = '/test/results'
        os.environ['BASIS_DEBUG'] = 'true'
        os.environ['BASIS_LOG_LEVEL'] = 'DEBUG'
        os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
        os.environ['BASIS_DATA_START_DATE'] = '2024-01-01'
        os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
        os.environ['HEALTH_CHECK_INTERVAL'] = '30s'
        os.environ['HEALTH_CHECK_ENDPOINT'] = '/health'
        os.environ['BASIS_API_PORT'] = '8001'
        os.environ['BASIS_API_HOST'] = '0.0.0.0'
        os.environ['BASIS_API_CORS_ORIGINS'] = 'http://localhost:3000,http://localhost:5173'
        
        # Should fail with Pydantic validation error
        with pytest.raises(ValueError, match="Mode configuration validation failed"):
            ConfigManager()
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_fail_fast_config_access(self, mock_path):
        """Test fail-fast behavior for configuration access."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Set environment variables
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        os.environ['BASIS_DEPLOYMENT_MODE'] = 'local'
        os.environ['BASIS_DEPLOYMENT_MACHINE'] = 'local_mac'
        os.environ['BASIS_DATA_DIR'] = '/test/data'
        os.environ['BASIS_DATA_MODE'] = 'csv'
        os.environ['BASIS_RESULTS_DIR'] = '/test/results'
        os.environ['BASIS_DEBUG'] = 'true'
        os.environ['BASIS_LOG_LEVEL'] = 'DEBUG'
        os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
        os.environ['BASIS_DATA_START_DATE'] = '2024-01-01'
        os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
        os.environ['HEALTH_CHECK_INTERVAL'] = '30s'
        os.environ['HEALTH_CHECK_ENDPOINT'] = '/health'
        os.environ['BASIS_API_PORT'] = '8001'
        os.environ['BASIS_API_HOST'] = '0.0.0.0'
        os.environ['BASIS_API_CORS_ORIGINS'] = 'http://localhost:3000,http://localhost:5173'
        
        # Create config manager
        config_manager = ConfigManager()
        
        # Test fail-fast access for missing mode
        with pytest.raises(KeyError, match="Mode 'nonexistent' not found"):
            config_manager.get_mode_config('nonexistent')
        
        # Test fail-fast access for missing venue
        with pytest.raises(KeyError, match="Venue 'nonexistent' not found"):
            config_manager.get_venue_config('nonexistent')
        
        # Test fail-fast access for missing share class
        with pytest.raises(KeyError, match="Share class 'nonexistent' not found"):
            config_manager.get_share_class_config('nonexistent')


if __name__ == "__main__":
    pytest.main([__file__])
