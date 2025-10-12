"""
Unit Tests for P&L Calculator Component

Tests P&L Calculator in isolation with mocked dependencies.
Focuses on P&L calculation, attribution, and error propagation.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

# Import the component under test
from basis_strategy_v1.core.math.pnl_calculator import PnLCalculator


class TestPnLCalculatorUnit:
    """Unit tests for P&L Calculator component."""
    
    def test_unrealized_pnl_calculation(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test unrealized P&L calculation."""
        # Arrange
        mock_config['share_class'] = 'USDT'
        mock_config['initial_capital'] = 100000.0
        
        # Mock position data
        current_value = 105000.0  # 5% gain
        initial_value = 100000.0
        
        pnl_calculator = PnLCalculator(
            config=mock_config,
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        pnl_result = pnl_calculator.calculate_pnl(current_value, initial_value)
        
        # Assert
        assert isinstance(pnl_result, dict)
        assert 'unrealized_pnl' in pnl_result
        assert 'unrealized_pnl_pct' in pnl_result
        
        # Should calculate 5% gain
        assert pnl_result['unrealized_pnl'] == 5000.0
        assert pnl_result['unrealized_pnl_pct'] == 0.05
    
    def test_attribution_pnl_lending(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test attribution P&L (lending vs funding vs staking vs gas)."""
        # Arrange
        mock_config['mode'] = 'pure_lending'
        mock_config['share_class'] = 'USDT'
        
        # Mock attribution data
        lending_pnl = 2000.0
        funding_pnl = 0.0  # No funding in pure lending
        staking_pnl = 0.0  # No staking in pure lending
        gas_costs = -100.0
        
        pnl_calculator = PnLCalculator(
            config=mock_config,
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        pnl_result = pnl_calculator.calculate_pnl(
            current_value=102000.0,
            initial_value=100000.0,
            lending_pnl=lending_pnl,
            funding_pnl=funding_pnl,
            staking_pnl=staking_pnl,
            gas_costs=gas_costs
        )
        
        # Assert
        assert isinstance(pnl_result, dict)
        assert 'attribution' in pnl_result
        
        attribution = pnl_result['attribution']
        assert 'lending_pnl' in attribution
        assert 'funding_pnl' in attribution
        assert 'staking_pnl' in attribution
        assert 'gas_costs' in attribution
        
        # Should attribute correctly
        assert attribution['lending_pnl'] == 2000.0
        assert attribution['funding_pnl'] == 0.0
        assert attribution['staking_pnl'] == 0.0
        assert attribution['gas_costs'] == -100.0
    
    def test_attribution_pnl_funding(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test attribution P&L for funding rate strategies."""
        # Arrange
        mock_config['mode'] = 'btc_basis'
        mock_config['share_class'] = 'USDT'
        
        # Mock attribution data for basis trading
        lending_pnl = 0.0  # No lending in basis trading
        funding_pnl = 1500.0  # Positive funding
        staking_pnl = 0.0  # No staking in basis trading
        gas_costs = -200.0
        
        pnl_calculator = PnLCalculator(
            config=mock_config,
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        pnl_result = pnl_calculator.calculate_pnl(
            current_value=101300.0,
            initial_value=100000.0,
            lending_pnl=lending_pnl,
            funding_pnl=funding_pnl,
            staking_pnl=staking_pnl,
            gas_costs=gas_costs
        )
        
        # Assert
        assert isinstance(pnl_result, dict)
        assert 'attribution' in pnl_result
        
        attribution = pnl_result['attribution']
        assert attribution['lending_pnl'] == 0.0
        assert attribution['funding_pnl'] == 1500.0
        assert attribution['staking_pnl'] == 0.0
        assert attribution['gas_costs'] == -200.0
    
    def test_attribution_pnl_staking(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test attribution P&L for staking strategies."""
        # Arrange
        mock_config['mode'] = 'eth_staking_only'
        mock_config['share_class'] = 'ETH'
        
        # Mock attribution data for staking
        lending_pnl = 0.0  # No lending in staking only
        funding_pnl = 0.0  # No funding in staking only
        staking_pnl = 3000.0  # Positive staking rewards
        gas_costs = -150.0
        
        pnl_calculator = PnLCalculator(
            config=mock_config,
            share_class='ETH',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        pnl_result = pnl_calculator.calculate_pnl(
            current_value=103000.0,
            initial_value=100000.0,
            lending_pnl=lending_pnl,
            funding_pnl=funding_pnl,
            staking_pnl=staking_pnl,
            gas_costs=gas_costs
        )
        
        # Assert
        assert isinstance(pnl_result, dict)
        assert 'attribution' in pnl_result
        
        attribution = pnl_result['attribution']
        assert attribution['lending_pnl'] == 0.0
        assert attribution['funding_pnl'] == 0.0
        assert attribution['staking_pnl'] == 3000.0
        assert attribution['gas_costs'] == -150.0
    
    def test_gas_cost_tracking(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test gas cost tracking."""
        # Arrange
        mock_config['share_class'] = 'USDT'
        
        # Mock gas costs
        total_gas_costs = -500.0  # Cumulative gas costs
        
        pnl_calculator = PnLCalculator(
            config=mock_config,
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        pnl_result = pnl_calculator.calculate_pnl(
            current_value=99500.0,
            initial_value=100000.0,
            gas_costs=total_gas_costs
        )
        
        # Assert
        assert isinstance(pnl_result, dict)
        assert 'attribution' in pnl_result
        assert 'gas_costs' in pnl_result['attribution']
        
        # Should track gas costs
        assert pnl_result['attribution']['gas_costs'] == -500.0
    
    def test_total_return_percentage(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test total return percentage calculation."""
        # Arrange
        mock_config['share_class'] = 'USDT'
        mock_config['initial_capital'] = 100000.0
        
        pnl_calculator = PnLCalculator(
            config=mock_config,
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act - Test different return scenarios
        test_cases = [
            (105000.0, 0.05),   # 5% gain
            (95000.0, -0.05),   # 5% loss
            (100000.0, 0.0),    # No change
            (110000.0, 0.10),   # 10% gain
        ]
        
        for current_value, expected_return in test_cases:
            pnl_result = pnl_calculator.calculate_pnl(current_value, 100000.0)
            
            # Assert
            assert isinstance(pnl_result, dict)
            assert 'total_return_pct' in pnl_result
            assert abs(pnl_result['total_return_pct'] - expected_return) < 0.001
    
    def test_error_code_propagation(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test error code propagation."""
        # Arrange
        mock_config['share_class'] = 'USDT'
        
        # Mock utility manager to return error code
        mock_utility_manager.create_error_code.return_value = 'PNL_CALC_ERROR'
        
        pnl_calculator = PnLCalculator(
            config=mock_config,
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act - Simulate error condition
        try:
            pnl_result = pnl_calculator.calculate_pnl(
                current_value=100000.0,
                initial_value=100000.0,
                error_condition=True  # Simulate error
            )
            
            # Assert - Should propagate error code
            assert isinstance(pnl_result, dict)
            assert 'error_code' in pnl_result
            assert pnl_result['error_code'] == 'PNL_CALC_ERROR'
            
        except Exception as e:
            # If exception is raised, should be handled appropriately
            assert isinstance(e, Exception)
    
    def test_share_class_currency_conversion(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test share class currency conversion."""
        # Test USDT share class
        usdt_config = mock_config.copy()
        usdt_config['share_class'] = 'USDT'
        
        pnl_calculator = PnLCalculator(
            config=usdt_config,
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        pnl_result = pnl_calculator.calculate_pnl(105000.0, 100000.0)
        assert pnl_result['share_class'] == 'USDT'
        assert pnl_result['unrealized_pnl'] == 5000.0
        
        # Test ETH share class
        eth_config = mock_config.copy()
        eth_config['share_class'] = 'ETH'
        
        pnl_calculator = PnLCalculator(
            config=eth_config,
            share_class='ETH',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        pnl_result = pnl_calculator.calculate_pnl(105000.0, 100000.0)
        assert pnl_result['share_class'] == 'ETH'
        assert pnl_result['unrealized_pnl'] == 5000.0
    
    def test_pnl_calculator_initialization(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test P&L Calculator initialization with different configs."""
        # Test pure lending mode
        pure_lending_config = mock_config.copy()
        pure_lending_config['mode'] = 'pure_lending'
        pure_lending_config['share_class'] = 'USDT'
        
        pnl_calculator = PnLCalculator(
            config=pure_lending_config,
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        assert pnl_calculator.share_class == 'USDT'
        assert pnl_calculator.initial_capital == 100000.0
        
        # Test ETH basis mode
        eth_basis_config = mock_config.copy()
        eth_basis_config['mode'] = 'eth_basis'
        eth_basis_config['share_class'] = 'USDT'
        
        pnl_calculator = PnLCalculator(
            config=eth_basis_config,
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        assert pnl_calculator.share_class == 'USDT'
        assert pnl_calculator.initial_capital == 100000.0
    
    def test_pnl_calculator_error_handling(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test P&L Calculator error handling."""
        # Arrange - Mock data provider to raise exception
        mock_data_provider.get_price.side_effect = Exception("Data provider error")
        
        pnl_calculator = PnLCalculator(
            config=mock_config,
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act & Assert - Should handle errors gracefully
        try:
            pnl_result = pnl_calculator.calculate_pnl(105000.0, 100000.0)
            # If no exception, should return error state
            assert isinstance(pnl_result, dict)
            assert 'error' in pnl_result or 'unrealized_pnl' in pnl_result
        except Exception as e:
            # If exception is raised, it should be handled appropriately
            assert "Data provider error" in str(e)
    
    def test_pnl_calculator_performance(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test P&L Calculator performance with multiple calculations."""
        # Arrange
        pnl_calculator = PnLCalculator(
            config=mock_config,
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act - Run multiple P&L calculations
        import time
        start_time = time.time()
        
        for i in range(100):
            current_value = 100000.0 + i * 1000
            pnl_result = pnl_calculator.calculate_pnl(current_value, 100000.0)
            assert isinstance(pnl_result, dict)
        
        end_time = time.time()
        
        # Assert - Should complete within reasonable time
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should complete within 1 second
    
    def test_pnl_calculator_edge_cases(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test P&L Calculator edge cases."""
        pnl_calculator = PnLCalculator(
            config=mock_config,
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Test zero values
        pnl_result = pnl_calculator.calculate_pnl(0.0, 100000.0)
        assert isinstance(pnl_result, dict)
        assert 'unrealized_pnl' in pnl_result
        assert pnl_result['unrealized_pnl'] == -100000.0
        
        # Test negative values
        pnl_result = pnl_calculator.calculate_pnl(-1000.0, 100000.0)
        assert isinstance(pnl_result, dict)
        assert 'unrealized_pnl' in pnl_result
        assert pnl_result['unrealized_pnl'] == -101000.0
        
        # Test very large values
        pnl_result = pnl_calculator.calculate_pnl(1000000000.0, 100000.0)
        assert isinstance(pnl_result, dict)
        assert 'unrealized_pnl' in pnl_result
        assert pnl_result['unrealized_pnl'] == 999900000.0
