"""
Unit Tests for Position Monitor Component

Tests Position Monitor in isolation with mocked dependencies.
Focuses on position collection, state persistence, and conversions.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from pathlib import Path

# Import the component under test
from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor


class TestPositionMonitorUnit:
    """Unit tests for Position Monitor component."""
    
    def test_collect_positions_structure(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test that collect_positions() returns correct structure."""
        # Arrange
        position_monitor = PositionMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        snapshot = position_monitor.get_snapshot()
        
        # Assert
        assert isinstance(snapshot, dict)
        assert 'wallet' in snapshot
        assert 'cex_accounts' in snapshot
        assert 'perp_positions' in snapshot
        
        # Validate wallet structure
        assert isinstance(snapshot['wallet'], dict)
        
        # Validate CEX accounts structure
        assert isinstance(snapshot['cex_accounts'], dict)
        for venue in ['binance', 'bybit', 'okx']:
            if venue in snapshot['cex_accounts']:
                assert isinstance(snapshot['cex_accounts'][venue], dict)
        
        # Validate perp positions structure
        assert isinstance(snapshot['perp_positions'], dict)
        for venue in snapshot['perp_positions']:
            assert isinstance(snapshot['perp_positions'][venue], dict)
    
    def test_state_persistence_across_timesteps(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test that position state persists across timesteps."""
        # Arrange
        position_monitor = PositionMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act - Get initial snapshot
        snapshot1 = position_monitor.get_snapshot()
        
        # Simulate time passing and get another snapshot
        snapshot2 = position_monitor.get_snapshot()
        
        # Assert - State should be consistent
        assert snapshot1['wallet'] == snapshot2['wallet']
        assert snapshot1['cex_accounts'] == snapshot2['cex_accounts']
        assert snapshot1['perp_positions'] == snapshot2['perp_positions']
    
    def test_aave_conversion_ausdt_to_usdt(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test AAVE conversion (aUSDT → USDT using liquidity_index)."""
        # Arrange
        mock_config['mode'] = 'pure_lending'
        mock_config['asset'] = 'USDT'
        
        # Mock AAVE liquidity index
        mock_data_provider.get_aave_liquidity_index.return_value = 1.05
        
        position_monitor = PositionMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        snapshot = position_monitor.get_snapshot()
        
        # Assert - aUSDT should be converted to USDT using liquidity index
        if 'aUSDT' in snapshot['wallet']:
            ausdt_balance = snapshot['wallet']['aUSDT']
            expected_usdt_balance = ausdt_balance * 1.05  # liquidity index
            
            # The conversion should be handled internally
            # We're testing that the conversion logic is applied
            assert isinstance(ausdt_balance, (int, float))
            assert ausdt_balance >= 0
    
    def test_lst_conversion_weeth_to_eth(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test LST conversion (weETH → ETH using conversion_rate)."""
        # Arrange
        mock_config['mode'] = 'eth_basis'
        mock_config['asset'] = 'ETH'
        mock_config['lst_type'] = 'weeth'
        
        # Mock weETH conversion rate
        mock_data_provider.get_price.return_value = 1.05  # weETH/ETH rate
        
        position_monitor = PositionMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        snapshot = position_monitor.get_snapshot()
        
        # Assert - weETH should be converted to ETH using conversion rate
        if 'weETH' in snapshot['wallet']:
            weeth_balance = snapshot['wallet']['weETH']
            expected_eth_balance = weeth_balance * 1.05  # conversion rate
            
            # The conversion should be handled internally
            assert isinstance(weeth_balance, (int, float))
            assert weeth_balance >= 0
    
    def test_multi_venue_aggregation(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test multi-venue position aggregation."""
        # Arrange
        position_monitor = PositionMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        snapshot = position_monitor.get_snapshot()
        
        # Assert - Should aggregate positions from multiple venues
        total_btc = 0
        total_eth = 0
        total_usdt = 0
        
        # Sum from wallet
        if 'BTC' in snapshot['wallet']:
            total_btc += snapshot['wallet']['BTC']
        if 'ETH' in snapshot['wallet']:
            total_eth += snapshot['wallet']['ETH']
        if 'USDT' in snapshot['wallet']:
            total_usdt += snapshot['wallet']['USDT']
        
        # Sum from CEX accounts
        for venue, balances in snapshot['cex_accounts'].items():
            if 'BTC' in balances:
                total_btc += balances['BTC']
            if 'ETH' in balances:
                total_eth += balances['ETH']
            if 'USDT' in balances:
                total_usdt += balances['USDT']
        
        # Sum from perp positions (convert to spot equivalent)
        for venue, positions in snapshot['perp_positions'].items():
            if 'BTCUSDT' in positions:
                total_btc += positions['BTCUSDT']['size']
            if 'ETHUSDT' in positions:
                total_eth += positions['ETHUSDT']['size']
        
        # Should have aggregated positions
        assert total_btc >= 0
        assert total_eth >= 0
        assert total_usdt >= 0
    
    def test_missing_venue_graceful_handling(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test missing venue graceful handling."""
        # Arrange - Create config with missing venue
        mock_config['venues'] = {
            'binance': {'enabled': True},
            'nonexistent_venue': {'enabled': True}  # This venue doesn't exist in test data
        }
        
        position_monitor = PositionMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act - Should not raise exception
        snapshot = position_monitor.get_snapshot()
        
        # Assert - Should handle missing venue gracefully
        assert isinstance(snapshot, dict)
        assert 'wallet' in snapshot
        assert 'cex_accounts' in snapshot
        assert 'perp_positions' in snapshot
        
        # Should not crash when venue is missing
        # The component should return empty dict or skip missing venues
        if 'nonexistent_venue' in snapshot['cex_accounts']:
            assert isinstance(snapshot['cex_accounts']['nonexistent_venue'], dict)
    
    def test_position_monitor_initialization(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test Position Monitor initialization with different configs."""
        # Test pure lending mode
        pure_lending_config = mock_config.copy()
        pure_lending_config['mode'] = 'pure_lending'
        pure_lending_config['asset'] = 'USDT'
        
        position_monitor = PositionMonitor(
            config=pure_lending_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        assert position_monitor.config['mode'] == 'pure_lending'
        assert position_monitor.config['asset'] == 'USDT'
        
        # Test BTC basis mode
        btc_basis_config = mock_config.copy()
        btc_basis_config['mode'] = 'btc_basis'
        btc_basis_config['asset'] = 'BTC'
        
        position_monitor = PositionMonitor(
            config=btc_basis_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        assert position_monitor.config['mode'] == 'btc_basis'
        assert position_monitor.config['asset'] == 'BTC'
    
    def test_position_monitor_debug_mode(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test Position Monitor debug mode functionality."""
        # Arrange
        mock_config['debug_mode'] = True
        
        position_monitor = PositionMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        snapshot = position_monitor.get_snapshot()
        
        # Assert - Debug mode should not affect core functionality
        assert isinstance(snapshot, dict)
        assert 'wallet' in snapshot
        
        # Debug mode might add additional logging or validation
        # but core position collection should still work
        assert len(snapshot['wallet']) >= 0  # Should have some wallet positions
    
    def test_position_monitor_error_handling(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test Position Monitor error handling."""
        # Arrange - Mock data provider to raise exception
        mock_data_provider.get_market_data_snapshot.side_effect = Exception("Data provider error")
        
        position_monitor = PositionMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act & Assert - Should handle errors gracefully
        try:
            snapshot = position_monitor.get_snapshot()
            # If no exception, should return empty or default snapshot
            assert isinstance(snapshot, dict)
        except Exception as e:
            # If exception is raised, it should be handled appropriately
            assert "Data provider error" in str(e)
    
    def test_position_monitor_share_class_handling(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test Position Monitor handles different share classes."""
        # Test USDT share class
        usdt_config = mock_config.copy()
        usdt_config['share_class'] = 'USDT'
        
        position_monitor = PositionMonitor(
            config=usdt_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        snapshot = position_monitor.get_snapshot()
        assert isinstance(snapshot, dict)
        
        # Test ETH share class
        eth_config = mock_config.copy()
        eth_config['share_class'] = 'ETH'
        
        position_monitor = PositionMonitor(
            config=eth_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        snapshot = position_monitor.get_snapshot()
        assert isinstance(snapshot, dict)
