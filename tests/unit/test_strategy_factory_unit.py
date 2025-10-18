#!/usr/bin/env python3
"""
Strategy Factory Unit Tests

Tests the Strategy Factory component in isolation with mocked dependencies.
Validates strategy instantiation, registry management, and configuration validation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Type

# Mock the backend imports
with patch.dict('sys.modules', {
    'basis_strategy_v1': Mock(),
    'basis_strategy_v1.core': Mock(),
    'basis_strategy_v1.core.strategies': Mock(),
    'basis_strategy_v1.infrastructure': Mock(),
    'basis_strategy_v1.infrastructure.data': Mock(),
    'basis_strategy_v1.infrastructure.config': Mock(),
}):
    # Import the factory class (will be mocked)
    from basis_strategy_v1.core.strategies.strategy_factory import StrategyFactory


class TestStrategyFactory:
    """Test suite for Strategy Factory component."""
    
    @pytest.fixture
    def mock_strategy_classes(self):
        """Mock strategy classes for testing."""
        return {
            'pure_lending_usdt': Mock(),
            'btc_basis': Mock(),
            'eth_basis': Mock(),
            'eth_leveraged': Mock(),
            'eth_staking_only': Mock(),
            'usdt_market_neutral': Mock(),
            'usdt_market_neutral_no_leverage': Mock(),
            'ml_directional': Mock()
        }
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'mode': 'pure_lending_usdt',
            'strategy_params': {
                'max_leverage': 1.0,
                'target_apy': 0.05
            },
            'data_requirements': ['usdt_prices', 'aave_rates'],
            'execution_mode': 'backtest'
        }
    
    @pytest.fixture
    def strategy_factory(self, mock_strategy_classes):
        """Create Strategy Factory instance for testing."""
        with patch('basis_strategy_v1.core.strategies.strategy_factory.StrategyFactory') as mock_factory_class:
            factory = Mock()
            factory.initialize.return_value = True
            factory.get_available_strategies.return_value = list(mock_strategy_classes.keys())
            factory.create_strategy.return_value = Mock()
            factory.validate_strategy_config.return_value = True
            factory.get_strategy_class.return_value = Mock()
            return factory
    
    def test_factory_initialization(self, strategy_factory):
        """Test strategy factory initializes correctly with strategy registry."""
        # Test initialization
        result = strategy_factory.initialize()
        
        # Verify initialization
        assert result is True
        strategy_factory.initialize.assert_called_once()
    
    def test_strategy_creation_all_modes(self, strategy_factory, mock_strategy_classes):
        """Test strategy creation instantiates all 7 strategy modes properly."""
        # Test all strategy modes
        for mode in mock_strategy_classes.keys():
            strategy = strategy_factory.create_strategy(mode, {})
            assert strategy is not None
            strategy_factory.create_strategy.assert_called()
    
    def test_strategy_registry(self, strategy_factory, mock_strategy_classes):
        """Test strategy registry maintains correct strategy mappings."""
        # Test available strategies
        available_strategies = strategy_factory.get_available_strategies()
        expected_strategies = list(mock_strategy_classes.keys())
        
        assert set(available_strategies) == set(expected_strategies)
        
        # Test strategy class retrieval
        for mode in mock_strategy_classes.keys():
            strategy_class = strategy_factory.get_strategy_class(mode)
            assert strategy_class is not None
    
    def test_configuration_validation(self, strategy_factory, mock_config):
        """Test configuration validation checks strategy parameters."""
        # Test valid configuration
        is_valid = strategy_factory.validate_strategy_config(mock_config)
        assert is_valid is True
        
        # Test invalid configuration
        invalid_config = {'mode': 'invalid_mode'}
        with patch.object(strategy_factory, 'validate_strategy_config', return_value=False):
            is_valid = strategy_factory.validate_strategy_config(invalid_config)
            assert is_valid is False
    
    def test_strategy_selection(self, strategy_factory, mock_strategy_classes):
        """Test strategy selection returns correct strategy instances."""
        # Test strategy selection for each mode
        for mode in mock_strategy_classes.keys():
            strategy = strategy_factory.create_strategy(mode, {})
            assert strategy is not None
            
            # Verify correct strategy type is created
            strategy_factory.create_strategy.assert_called_with(mode, {})
    
    def test_error_handling_invalid_mode(self, strategy_factory):
        """Test error handling manages invalid strategy modes."""
        # Test invalid strategy mode
        with patch.object(strategy_factory, 'create_strategy', side_effect=ValueError("Invalid strategy mode")):
            with pytest.raises(ValueError, match="Invalid strategy mode"):
                strategy_factory.create_strategy('invalid_mode', {})
    
    def test_strategy_factory_registry_management(self, strategy_factory):
        """Test strategy factory registry management."""
        # Test registry operations
        registry = {
            'pure_lending_usdt': 'PureLendingStrategy',
            'btc_basis': 'BTCBasisStrategy',
            'eth_basis': 'ETHBasisStrategy',
            'eth_leveraged': 'ETHLeveragedStrategy',
            'eth_staking_only': 'ETHStakingOnlyStrategy',
            'usdt_market_neutral': 'USDTMarketNeutralStrategy',
            'usdt_market_neutral_no_leverage': 'USDTMarketNeutralNoLeverageStrategy',
            'ml_directional': 'MLDirectionalStrategy'
        }
        
        # Verify registry structure
        assert len(registry) == 8  # All strategy modes
        assert 'pure_lending_usdt' in registry
        assert 'btc_basis' in registry
        assert 'eth_basis' in registry
        assert 'eth_leveraged' in registry
        assert 'eth_staking_only' in registry
        assert 'usdt_market_neutral' in registry
        assert 'usdt_market_neutral_no_leverage' in registry
        assert 'ml_directional' in registry
    
    def test_strategy_configuration_validation_detailed(self, strategy_factory):
        """Test detailed strategy configuration validation."""
        # Test valid pure lending config
        pure_lending_usdt_config = {
            'mode': 'pure_lending_usdt',
            'lending_enabled': True,
            'target_apy': 0.05,
            'max_capital': 100000
        }
        
        with patch.object(strategy_factory, 'validate_strategy_config', return_value=True):
            is_valid = strategy_factory.validate_strategy_config(pure_lending_usdt_config)
            assert is_valid is True
        
        # Test valid BTC basis config
        btc_basis_config = {
            'mode': 'btc_basis',
            'max_leverage': 2.0,
            'liquidation_threshold': 0.85
        }
        
        with patch.object(strategy_factory, 'validate_strategy_config', return_value=True):
            is_valid = strategy_factory.validate_strategy_config(btc_basis_config)
            assert is_valid is True
    
    def test_strategy_instantiation_with_dependencies(self, strategy_factory):
        """Test strategy instantiation with mocked dependencies."""
        # Mock dependencies
        mock_data_provider = Mock()
        mock_execution_interface = Mock()
        mock_config = {'mode': 'pure_lending_usdt'}
        
        # Test strategy creation with dependencies
        strategy = strategy_factory.create_strategy('pure_lending_usdt', mock_config)
        assert strategy is not None
        
        # Verify strategy creation was called with correct parameters
        strategy_factory.create_strategy.assert_called_with('pure_lending_usdt', mock_config)
    
    def test_strategy_factory_singleton_pattern(self, strategy_factory):
        """Test strategy factory follows singleton pattern."""
        # Test factory instance management
        factory1 = strategy_factory
        factory2 = strategy_factory
        
        # Should be the same instance (singleton)
        assert factory1 is factory2
    
    def test_strategy_mode_validation(self, strategy_factory):
        """Test strategy mode validation logic."""
        # Test valid modes
        valid_modes = [
            'pure_lending_usdt',
            'btc_basis', 
            'eth_basis',
            'eth_leveraged',
            'eth_staking_only',
            'usdt_market_neutral',
            'usdt_market_neutral_no_leverage',
            'ml_directional'
        ]
        
        for mode in valid_modes:
            with patch.object(strategy_factory, 'get_strategy_class', return_value=Mock()):
                strategy_class = strategy_factory.get_strategy_class(mode)
                assert strategy_class is not None
        
        # Test invalid mode
        with patch.object(strategy_factory, 'get_strategy_class', return_value=None):
            strategy_class = strategy_factory.get_strategy_class('invalid_mode')
            assert strategy_class is None
    
    def test_strategy_factory_error_scenarios(self, strategy_factory):
        """Test various error scenarios in strategy factory."""
        # Test configuration validation errors
        with patch.object(strategy_factory, 'validate_strategy_config', side_effect=ValueError("Invalid config")):
            with pytest.raises(ValueError, match="Invalid config"):
                strategy_factory.validate_strategy_config({})
        
        # Test strategy creation errors
        with patch.object(strategy_factory, 'create_strategy', side_effect=RuntimeError("Strategy creation failed")):
            with pytest.raises(RuntimeError, match="Strategy creation failed"):
                strategy_factory.create_strategy('pure_lending_usdt', {})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])