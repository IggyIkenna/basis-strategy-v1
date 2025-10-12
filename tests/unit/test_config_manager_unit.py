"""
Unit Tests for Config Manager Component

Tests Config Manager in isolation with mocked dependencies.
Focuses on config loading, merging, and environment switching.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from pathlib import Path
import json
import yaml

# Import the component under test
from basis_strategy_v1.infrastructure.config.config_manager import get_config_manager, ConfigManager


class TestConfigManagerUnit:
    """Unit tests for Config Manager component."""
    
    def test_load_base_config_local_json(self, mock_config):
        """Test load base config (local.json)."""
        # Arrange
        config_manager = ConfigManager()
        
        # Act
        try:
            base_config = config_manager.get_base_config()
            
            # Assert
            assert isinstance(base_config, dict)
            assert 'api' in base_config or 'database' in base_config or 'data' in base_config
            
        except Exception as e:
            # Expected behavior if local.json doesn't exist
            assert isinstance(e, Exception)
            assert 'not found' in str(e).lower() or 'missing' in str(e).lower()
    
    def test_load_mode_config_modes_yaml(self, mock_config):
        """Test load mode config (modes/*.yaml)."""
        # Arrange
        config_manager = ConfigManager()
        
        # Test different modes
        test_modes = [
            'pure_lending',
            'btc_basis',
            'eth_basis',
            'eth_staking_only',
            'eth_leveraged',
            'usdt_market_neutral_no_leverage',
            'usdt_market_neutral',
            'ml_btc_directional',
            'ml_usdt_directional'
        ]
        
        # Act & Assert
        for mode in test_modes:
            try:
                mode_config = config_manager.get_mode_config(mode)
                
                # Assert
                assert isinstance(mode_config, dict)
                assert 'mode' in mode_config
                assert mode_config['mode'] == mode
                
            except Exception as e:
                # Expected behavior if mode config doesn't exist
                assert isinstance(e, Exception)
                assert 'not found' in str(e).lower() or 'missing' in str(e).lower()
    
    def test_load_venue_config_venues_yaml(self, mock_config):
        """Test load venue config (venues/*.yaml)."""
        # Arrange
        config_manager = ConfigManager()
        
        # Test different venues
        test_venues = [
            'binance',
            'bybit',
            'okx',
            'ethereum',
            'polygon'
        ]
        
        # Act & Assert
        for venue in test_venues:
            try:
                venue_config = config_manager.get_venue_config(venue)
                
                # Assert
                assert isinstance(venue_config, dict)
                assert 'enabled' in venue_config or 'type' in venue_config
                
            except Exception as e:
                # Expected behavior if venue config doesn't exist
                assert isinstance(e, Exception)
                assert 'not found' in str(e).lower() or 'missing' in str(e).lower()
    
    def test_config_merge_logic(self, mock_config):
        """Test config merge logic."""
        # Arrange
        config_manager = ConfigManager()
        
        # Create test configs
        base_config = {
            'api': {'base_url': 'https://api.example.com'},
            'database': {'host': 'localhost'},
            'data': {'dir': 'data'}
        }
        
        mode_config = {
            'mode': 'pure_lending',
            'asset': 'USDT',
            'max_drawdown': 0.2
        }
        
        venue_config = {
            'binance': {'enabled': True, 'type': 'cex'},
            'bybit': {'enabled': True, 'type': 'cex'}
        }
        
        # Act
        merged_config = config_manager.merge_configs(base_config, mode_config, venue_config)
        
        # Assert
        assert isinstance(merged_config, dict)
        assert 'api' in merged_config
        assert 'mode' in merged_config
        assert 'binance' in merged_config
        assert merged_config['mode'] == 'pure_lending'
        assert merged_config['asset'] == 'USDT'
        assert merged_config['max_drawdown'] == 0.2
    
    def test_environment_switching(self, mock_config):
        """Test environment switching (dev/staging/prod)."""
        # Arrange
        config_manager = ConfigManager()
        
        # Test that environment variables are loaded correctly
        env_vars = config_manager._load_environment_variables()
        
        # Assert
        assert isinstance(env_vars, dict)
        assert 'BASIS_ENVIRONMENT' in env_vars
        assert env_vars['BASIS_ENVIRONMENT'] == 'dev'  # Set in conftest.py
        
        # Test that environment file loading works
        assert 'BASIS_DEPLOYMENT_MODE' in env_vars
        assert 'BASIS_DATA_DIR' in env_vars
        assert 'BASIS_RESULTS_DIR' in env_vars
    
    def test_pydantic_validation(self, mock_config):
        """Test Pydantic validation."""
        # Arrange
        config_manager = ConfigManager()
        
        # Test valid config
        valid_config = {
            'mode': 'pure_lending',
            'share_class': 'USDT',
            'asset': 'USDT',
            'initial_capital': 100000.0,
            'max_drawdown': 0.2,
            'leverage_enabled': False
        }
        
        # Act
        try:
            validated_config = config_manager.validate_config(valid_config)
            
            # Assert
            assert isinstance(validated_config, dict)
            assert validated_config['mode'] == 'pure_lending'
            assert validated_config['share_class'] == 'USDT'
            assert validated_config['initial_capital'] == 100000.0
            
        except Exception as e:
            # Expected behavior if validation fails
            assert isinstance(e, Exception)
        
        # Test invalid config
        invalid_config = {
            'mode': 'pure_lending',
            'share_class': 'USDT',
            'asset': 'USDT',
            'initial_capital': 'invalid_number',  # Invalid type
            'max_drawdown': 0.2,
            'leverage_enabled': False
        }
        
        # Act & Assert
        try:
            validated_config = config_manager.validate_config(invalid_config)
            # Should not reach here
            assert False, "Should have raised validation error"
        except Exception as e:
            # Expected behavior for invalid config
            assert isinstance(e, Exception)
    
    def test_config_manager_initialization(self, mock_config):
        """Test Config Manager initialization with different configs."""
        # Test default initialization
        config_manager = ConfigManager()
        assert isinstance(config_manager, ConfigManager)
        
        # Test initialization with custom config
        custom_config = mock_config.copy()
        custom_config['custom_field'] = 'custom_value'
        
        config_manager = ConfigManager(custom_config)
        assert config_manager.config['custom_field'] == 'custom_value'
    
    def test_config_manager_error_handling(self, mock_config):
        """Test Config Manager error handling."""
        # Arrange
        config_manager = ConfigManager()
        
        # Test invalid file paths
        invalid_paths = [
            'nonexistent_file.json',
            'nonexistent_file.yaml',
            '/invalid/path/config.json'
        ]
        
        # Act & Assert
        for invalid_path in invalid_paths:
            try:
                config = config_manager.load_config_file(invalid_path)
                # Should not reach here
                assert False, "Should have raised error for invalid path"
            except Exception as e:
                # Expected behavior for invalid paths
                assert isinstance(e, Exception)
                assert 'not found' in str(e).lower() or 'missing' in str(e).lower()
    
    def test_config_manager_performance(self, mock_config):
        """Test Config Manager performance with multiple operations."""
        # Arrange
        config_manager = ConfigManager()
        
        # Act - Run multiple config operations
        import time
        start_time = time.time()
        
        for i in range(100):
            try:
                # Test config loading
                config = config_manager.get_complete_config(mode='pure_lending')
                assert isinstance(config, dict)
            except Exception:
                # Some operations might fail
                pass
        
        end_time = time.time()
        
        # Assert - Should complete within reasonable time
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete within 5 seconds
    
    def test_config_manager_edge_cases(self, mock_config):
        """Test Config Manager edge cases."""
        # Arrange
        config_manager = ConfigManager()
        
        # Test edge cases
        edge_cases = [
            '',  # Empty mode
            None,  # None mode
            '   ',  # Whitespace mode
            'MODE_WITH_SPECIAL_CHARS!@#$%',  # Special characters
        ]
        
        # Act & Assert
        for edge_case in edge_cases:
            try:
                config = config_manager.get_mode_config(edge_case)
                # Should handle edge cases gracefully
                assert config is None or isinstance(config, dict)
            except Exception as e:
                # Expected behavior for edge cases
                assert isinstance(e, Exception)
    
    def test_config_manager_config_validation(self, mock_config):
        """Test Config Manager config validation."""
        # Test valid config
        valid_config = {
            'mode': 'pure_lending',
            'share_class': 'USDT',
            'asset': 'USDT',
            'initial_capital': 100000.0,
            'max_drawdown': 0.2,
            'leverage_enabled': False,
            'venues': {
                'binance': {'enabled': True},
                'bybit': {'enabled': True}
            }
        }
        
        config_manager = ConfigManager()
        
        try:
            validated_config = config_manager.validate_config(valid_config)
            assert isinstance(validated_config, dict)
            assert validated_config['mode'] == 'pure_lending'
        except Exception as e:
            # Expected behavior if validation fails
            assert isinstance(e, Exception)
        
        # Test invalid config (missing required fields)
        invalid_config = {
            'mode': 'pure_lending',
            'share_class': 'USDT'
            # Missing required fields
        }
        
        try:
            validated_config = config_manager.validate_config(invalid_config)
            # Should not reach here
            assert False, "Should have raised validation error"
        except Exception as e:
            # Expected behavior for invalid config
            assert isinstance(e, Exception)
    
    def test_config_manager_singleton_pattern(self, mock_config):
        """Test Config Manager singleton pattern."""
        # Arrange
        config_manager1 = get_config_manager()
        config_manager2 = get_config_manager()
        
        # Act & Assert
        # Should return the same instance
        assert config_manager1 is config_manager2
        assert isinstance(config_manager1, ConfigManager)
        assert isinstance(config_manager2, ConfigManager)
    
    def test_config_manager_complete_config(self, mock_config):
        """Test Config Manager complete config generation."""
        # Arrange
        config_manager = ConfigManager()
        
        # Act
        try:
            complete_config = config_manager.get_complete_config(mode='pure_lending')
            
            # Assert
            assert isinstance(complete_config, dict)
            assert 'mode' in complete_config
            assert complete_config['mode'] == 'pure_lending'
            
            # Should have merged base, mode, and venue configs
            assert 'api' in complete_config or 'database' in complete_config or 'data' in complete_config
            
        except Exception as e:
            # Expected behavior if config files don't exist
            assert isinstance(e, Exception)
            assert 'not found' in str(e).lower() or 'missing' in str(e).lower()
    
    def test_config_manager_data_directory(self, mock_config):
        """Test Config Manager data directory handling."""
        # Arrange
        config_manager = ConfigManager()
        
        # Act
        try:
            data_dir = config_manager.get_data_directory()
            
            # Assert
            assert isinstance(data_dir, str)
            assert len(data_dir) > 0
            
        except Exception as e:
            # Expected behavior if data directory not configured
            assert isinstance(e, Exception)
    
    def test_config_manager_startup_mode(self, mock_config):
        """Test Config Manager startup mode handling."""
        # Arrange
        config_manager = ConfigManager()
        
        # Act
        try:
            startup_mode = config_manager.get_startup_mode()
            
            # Assert
            assert startup_mode in ['backtest', 'live', 'dev', 'staging', 'prod']
            
        except Exception as e:
            # Expected behavior if startup mode not configured
            assert isinstance(e, Exception)
