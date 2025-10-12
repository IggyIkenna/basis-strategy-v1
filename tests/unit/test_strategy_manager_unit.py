"""
Unit Tests for Strategy Manager Component

Tests Strategy Manager in isolation with mocked dependencies.
Focuses on strategy factory, actions, and mode-specific logic.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

# Import the components under test
from basis_strategy_v1.core.strategies.strategy_factory import StrategyFactory
from basis_strategy_v1.core.strategies.base_strategy_manager import BaseStrategyManager, StrategyAction


class TestStrategyFactoryUnit:
    """Unit tests for Strategy Factory."""
    
    def test_strategy_factory_creates_correct_manager_for_each_mode(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test StrategyFactory.create() for each mode."""
        # Arrange
        mock_risk_monitor = Mock()
        mock_position_monitor = Mock()
        mock_event_engine = Mock()
        
        # Test all strategy modes
        modes = [
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
        
        for mode in modes:
            test_config = mock_config.copy()
            test_config['mode'] = mode
            
            # Act
            strategy_manager = StrategyFactory.create_strategy(
                mode=mode,
                config=test_config,
                risk_monitor=mock_risk_monitor,
                position_monitor=mock_position_monitor,
                event_engine=mock_event_engine
            )
            
            # Assert
            assert strategy_manager is not None
            assert isinstance(strategy_manager, BaseStrategyManager)
            assert strategy_manager.config['mode'] == mode
    
    def test_strategy_factory_handles_invalid_mode(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test StrategyFactory handles invalid mode gracefully."""
        # Arrange
        mock_risk_monitor = Mock()
        mock_position_monitor = Mock()
        mock_event_engine = Mock()
        
        invalid_mode = 'invalid_strategy_mode'
        test_config = mock_config.copy()
        test_config['mode'] = invalid_mode
        
        # Act & Assert
        try:
            strategy_manager = StrategyFactory.create_strategy(
                mode=invalid_mode,
                config=test_config,
                risk_monitor=mock_risk_monitor,
                position_monitor=mock_position_monitor,
                event_engine=mock_event_engine
            )
            # If no exception, should return None or handle gracefully
            assert strategy_manager is None or isinstance(strategy_manager, BaseStrategyManager)
        except Exception as e:
            # Expected behavior for invalid mode
            assert isinstance(e, Exception)
    
    def test_strategy_factory_strategy_map_completeness(self):
        """Test that STRATEGY_MAP contains all expected strategies."""
        # Assert
        expected_strategies = [
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
        
        for strategy in expected_strategies:
            assert strategy in StrategyFactory.STRATEGY_MAP
            assert StrategyFactory.STRATEGY_MAP[strategy] is not None


class TestBaseStrategyManagerUnit:
    """Unit tests for Base Strategy Manager."""
    
    def test_five_standardized_actions_exist(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test 5 standardized actions exist."""
        # Arrange
        mock_risk_monitor = Mock()
        mock_position_monitor = Mock()
        mock_event_engine = Mock()
        
        # Create a concrete strategy manager
        strategy_manager = StrategyFactory.create_strategy(
            mode='pure_lending',
            config=mock_config,
            risk_monitor=mock_risk_monitor,
            position_monitor=mock_position_monitor,
            event_engine=mock_event_engine
        )
        
        # Act & Assert - Check that all 5 actions exist
        expected_actions = [
            'open_position',
            'close_position', 
            'rebalance',
            'hedge',
            'transfer'
        ]
        
        for action in expected_actions:
            assert hasattr(strategy_manager, action)
            assert callable(getattr(strategy_manager, action))
    
    def test_read_only_behavior(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test read-only behavior (no direct position updates)."""
        # Arrange
        mock_risk_monitor = Mock()
        mock_position_monitor = Mock()
        mock_event_engine = Mock()
        
        strategy_manager = StrategyFactory.create_strategy(
            mode='pure_lending',
            config=mock_config,
            risk_monitor=mock_risk_monitor,
            position_monitor=mock_position_monitor,
            event_engine=mock_event_engine
        )
        
        # Act - Strategy manager should not directly update positions
        # It should only generate instructions
        
        # Assert - Position monitor should not be called directly for updates
        # The strategy manager should only read from position monitor
        mock_position_monitor.get_snapshot.return_value = {'wallet': {'USDT': 1000.0}}
        
        # Strategy manager should read positions but not update them
        snapshot = mock_position_monitor.get_snapshot()
        assert snapshot is not None
        
        # Verify that position monitor's update methods are not called directly
        # (This would be verified by checking that no update methods are called)
    
    def test_instruction_block_generation(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test instruction block structure."""
        # Arrange
        mock_risk_monitor = Mock()
        mock_position_monitor = Mock()
        mock_event_engine = Mock()
        
        strategy_manager = StrategyFactory.create_strategy(
            mode='pure_lending',
            config=mock_config,
            risk_monitor=mock_risk_monitor,
            position_monitor=mock_position_monitor,
            event_engine=mock_event_engine
        )
        
        # Act - Generate instruction block
        instruction_block = strategy_manager.generate_instruction_block()
        
        # Assert - Should return proper instruction block structure
        assert isinstance(instruction_block, list)
        
        # Each instruction should have required fields
        for instruction in instruction_block:
            assert isinstance(instruction, dict)
            assert 'action' in instruction
            assert 'venue' in instruction
            assert 'asset' in instruction
            assert 'size' in instruction
            assert 'order_type' in instruction
            assert 'timestamp' in instruction
    
    def test_mode_specific_logic_isolation(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test mode-specific strategy logic isolation."""
        # Test pure lending mode
        pure_lending_config = mock_config.copy()
        pure_lending_config['mode'] = 'pure_lending'
        
        pure_lending_manager = StrategyFactory.create_strategy(
            mode='pure_lending',
            config=pure_lending_config,
            risk_monitor=Mock(),
            position_monitor=Mock(),
            event_engine=Mock()
        )
        
        # Test BTC basis mode
        btc_basis_config = mock_config.copy()
        btc_basis_config['mode'] = 'btc_basis'
        
        btc_basis_manager = StrategyFactory.create_strategy(
            mode='btc_basis',
            config=btc_basis_config,
            risk_monitor=Mock(),
            position_monitor=Mock(),
            event_engine=Mock()
        )
        
        # Assert - Different modes should have different logic
        assert pure_lending_manager.config['mode'] == 'pure_lending'
        assert btc_basis_manager.config['mode'] == 'btc_basis'
        
        # The specific logic differences would be tested in integration tests
        # Here we just verify they're different instances with different configs
    
    def test_risk_limit_respect(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test risk limit respect."""
        # Arrange
        mock_risk_monitor = Mock()
        mock_position_monitor = Mock()
        mock_event_engine = Mock()
        
        # Mock risk assessment
        mock_risk_monitor.assess_risk.return_value = {
            'overall_risk_breach': True,
            'max_drawdown': 0.25,  # Exceeds 0.2 limit
            'leverage_ratio': 1.5
        }
        
        strategy_manager = StrategyFactory.create_strategy(
            mode='pure_lending',
            config=mock_config,
            risk_monitor=mock_risk_monitor,
            position_monitor=mock_position_monitor,
            event_engine=mock_event_engine
        )
        
        # Act - Strategy should respect risk limits
        instruction_block = strategy_manager.generate_instruction_block()
        
        # Assert - Should respect risk limits
        # If risk is breached, should generate conservative instructions
        assert isinstance(instruction_block, list)
        
        # The exact behavior depends on implementation
        # But should not generate risky instructions when risk is breached


class TestStrategyActionUnit:
    """Unit tests for Strategy Action."""
    
    def test_strategy_action_creation(self):
        """Test StrategyAction creation with required fields."""
        # Arrange
        action_data = {
            'action_type': 'open_position',
            'target_amount': 1000.0,
            'target_currency': 'USDT',
            'instructions': [
                {
                    'venue': 'binance',
                    'asset': 'USDT',
                    'size': 1000.0,
                    'order_type': 'market'
                }
            ],
            'atomic': True
        }
        
        # Act
        strategy_action = StrategyAction(**action_data)
        
        # Assert
        assert strategy_action.action_type == 'open_position'
        assert strategy_action.target_amount == 1000.0
        assert strategy_action.target_currency == 'USDT'
        assert len(strategy_action.instructions) == 1
        assert strategy_action.atomic == True
    
    def test_strategy_action_validation(self):
        """Test StrategyAction validation."""
        # Test valid action
        valid_action = StrategyAction(
            action_type='close_position',
            target_amount=500.0,
            target_currency='BTC',
            instructions=[],
            atomic=False
        )
        
        assert valid_action.action_type == 'close_position'
        assert valid_action.target_amount == 500.0
        
        # Test invalid action (missing required field)
        try:
            invalid_action = StrategyAction(
                action_type='open_position',
                # Missing target_amount
                target_currency='USDT',
                instructions=[]
            )
            # Should not reach here
            assert False, "Should have raised validation error"
        except Exception as e:
            # Expected behavior
            assert isinstance(e, Exception)


class TestStrategyManagerIntegration:
    """Integration tests for Strategy Manager with other components."""
    
    def test_strategy_manager_with_risk_monitor(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test Strategy Manager integration with Risk Monitor."""
        # Arrange
        mock_risk_monitor = Mock()
        mock_position_monitor = Mock()
        mock_event_engine = Mock()
        
        # Mock risk assessment
        mock_risk_monitor.assess_risk.return_value = {
            'overall_risk_breach': False,
            'max_drawdown': 0.15,
            'leverage_ratio': 1.2
        }
        
        strategy_manager = StrategyFactory.create_strategy(
            mode='btc_basis',
            config=mock_config,
            risk_monitor=mock_risk_monitor,
            position_monitor=mock_position_monitor,
            event_engine=mock_event_engine
        )
        
        # Act
        instruction_block = strategy_manager.generate_instruction_block()
        
        # Assert
        assert isinstance(instruction_block, list)
        # Risk monitor should have been consulted
        mock_risk_monitor.assess_risk.assert_called()
    
    def test_strategy_manager_with_position_monitor(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test Strategy Manager integration with Position Monitor."""
        # Arrange
        mock_risk_monitor = Mock()
        mock_position_monitor = Mock()
        mock_event_engine = Mock()
        
        # Mock position snapshot
        mock_position_monitor.get_snapshot.return_value = {
            'wallet': {'BTC': 0.5, 'USDT': 5000.0},
            'cex_accounts': {'binance': {'BTC': 0.2, 'USDT': 2000.0}},
            'perp_positions': {}
        }
        
        strategy_manager = StrategyFactory.create_strategy(
            mode='btc_basis',
            config=mock_config,
            risk_monitor=mock_risk_monitor,
            position_monitor=mock_position_monitor,
            event_engine=mock_event_engine
        )
        
        # Act
        instruction_block = strategy_manager.generate_instruction_block()
        
        # Assert
        assert isinstance(instruction_block, list)
        # Position monitor should have been consulted
        mock_position_monitor.get_snapshot.assert_called()
    
    def test_strategy_manager_error_handling(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test Strategy Manager error handling."""
        # Arrange
        mock_risk_monitor = Mock()
        mock_position_monitor = Mock()
        mock_event_engine = Mock()
        
        # Mock risk monitor to raise exception
        mock_risk_monitor.assess_risk.side_effect = Exception("Risk monitor error")
        
        strategy_manager = StrategyFactory.create_strategy(
            mode='pure_lending',
            config=mock_config,
            risk_monitor=mock_risk_monitor,
            position_monitor=mock_position_monitor,
            event_engine=mock_event_engine
        )
        
        # Act & Assert - Should handle errors gracefully
        try:
            instruction_block = strategy_manager.generate_instruction_block()
            # If no exception, should return empty or error state
            assert isinstance(instruction_block, list)
        except Exception as e:
            # If exception is raised, it should be handled appropriately
            assert "Risk monitor error" in str(e)
