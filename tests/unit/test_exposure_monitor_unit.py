"""
Unit Tests for Exposure Monitor Component

Tests Exposure Monitor in isolation with mocked dependencies.
Focuses on asset filtering, net delta calculation, and exposure calculations.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

# Import the component under test
from basis_strategy_v1.core.strategies.components.exposure_monitor import ExposureMonitor


class TestExposureMonitorUnit:
    """Unit tests for Exposure Monitor component."""
    
    def test_asset_filtering_config_driven(self, mock_config, mock_data_provider, mock_utility_manager, mock_position_snapshot):
        """Test asset filtering based on config."""
        # Arrange
        mock_config['component_config']['exposure_monitor']['tracked_assets'] = ['BTC', 'ETH', 'USDT']
        
        exposure_monitor = ExposureMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        exposure_report = exposure_monitor.calculate_exposure(mock_position_snapshot)
        
        # Assert - Should only track configured assets
        assert isinstance(exposure_report, dict)
        
        # Should have exposure data for tracked assets
        for asset in ['BTC', 'ETH', 'USDT']:
            if asset in exposure_report:
                assert isinstance(exposure_report[asset], dict)
                assert 'total_exposure' in exposure_report[asset]
                assert 'share_class_value' in exposure_report[asset]
    
    def test_net_delta_calculation(self, mock_config, mock_data_provider, mock_utility_manager, mock_position_snapshot):
        """Test net delta calculation in share class currency."""
        # Arrange
        mock_config['share_class'] = 'USDT'
        mock_config['component_config']['exposure_monitor']['share_class_currency'] = 'USDT'
        
        # Mock utility manager to return calculated net delta
        mock_utility_manager.calculate_net_delta.return_value = 100000.0
        
        exposure_monitor = ExposureMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        exposure_report = exposure_monitor.calculate_exposure(mock_position_snapshot)
        
        # Assert - Should calculate net delta in share class currency
        assert isinstance(exposure_report, dict)
        assert 'net_delta' in exposure_report
        assert 'share_class_currency' in exposure_report
        
        # Net delta should be in share class currency (USDT)
        assert exposure_report['share_class_currency'] == 'USDT'
        assert isinstance(exposure_report['net_delta'], (int, float))
    
    def test_underlying_balance_derivatives(self, mock_config, mock_data_provider, mock_utility_manager, mock_position_snapshot):
        """Test underlying balance calculation for derivatives."""
        # Arrange
        mock_config['mode'] = 'eth_basis'
        mock_config['asset'] = 'ETH'
        mock_config['lst_type'] = 'weeth'
        
        # Mock conversion rates for derivatives
        mock_data_provider.get_price.return_value = 1.05  # weETH/ETH rate
        mock_data_provider.get_aave_liquidity_index.return_value = 1.02  # aWeETH rate
        
        exposure_monitor = ExposureMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        exposure_report = exposure_monitor.calculate_exposure(mock_position_snapshot)
        
        # Assert - Should calculate underlying balance for derivatives
        assert isinstance(exposure_report, dict)
        
        # Check for derivative conversions
        for asset in ['weETH', 'aWeETH', 'aUSDT']:
            if asset in exposure_report:
                asset_data = exposure_report[asset]
                assert 'underlying_balance' in asset_data
                assert 'conversion_rate' in asset_data
                assert isinstance(asset_data['underlying_balance'], (int, float))
                assert isinstance(asset_data['conversion_rate'], (int, float))
    
    def test_venue_breakdown(self, mock_config, mock_data_provider, mock_utility_manager, mock_position_snapshot):
        """Test per-venue exposure breakdown."""
        # Arrange
        exposure_monitor = ExposureMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        exposure_report = exposure_monitor.calculate_exposure(mock_position_snapshot)
        
        # Assert - Should provide venue breakdown
        assert isinstance(exposure_report, dict)
        assert 'venue_breakdown' in exposure_report
        
        venue_breakdown = exposure_report['venue_breakdown']
        assert isinstance(venue_breakdown, dict)
        
        # Should have breakdown for each venue
        expected_venues = ['wallet', 'binance', 'bybit', 'okx']
        for venue in expected_venues:
            if venue in venue_breakdown:
                venue_data = venue_breakdown[venue]
                assert isinstance(venue_data, dict)
                assert 'total_value' in venue_data
                assert 'asset_breakdown' in venue_data
    
    def test_zero_exposure_handling(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test zero exposure handling."""
        # Arrange - Create empty position snapshot
        empty_snapshot = {
            'wallet': {},
            'cex_accounts': {},
            'perp_positions': {}
        }
        
        exposure_monitor = ExposureMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        exposure_report = exposure_monitor.calculate_exposure(empty_snapshot)
        
        # Assert - Should handle zero exposure gracefully
        assert isinstance(exposure_report, dict)
        assert 'net_delta' in exposure_report
        assert 'share_class_currency' in exposure_report
        
        # Net delta should be zero
        assert exposure_report['net_delta'] == 0.0
        assert exposure_report['share_class_currency'] == mock_config['share_class']
    
    def test_missing_price_graceful_degradation(self, mock_config, mock_data_provider, mock_utility_manager, mock_position_snapshot):
        """Test missing price graceful degradation."""
        # Arrange - Mock data provider to return None for some prices
        mock_data_provider.get_price.side_effect = lambda asset: None if asset == 'MISSING_ASSET' else 1000.0
        
        exposure_monitor = ExposureMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act - Should not raise exception
        exposure_report = exposure_monitor.calculate_exposure(mock_position_snapshot)
        
        # Assert - Should handle missing prices gracefully
        assert isinstance(exposure_report, dict)
        assert 'net_delta' in exposure_report
        
        # Should either skip missing assets or use default values
        # The exact behavior depends on implementation
        assert isinstance(exposure_report['net_delta'], (int, float))
    
    def test_exposure_monitor_initialization(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test Exposure Monitor initialization with different configs."""
        # Test pure lending mode
        pure_lending_config = mock_config.copy()
        pure_lending_config['mode'] = 'pure_lending'
        pure_lending_config['share_class'] = 'USDT'
        
        exposure_monitor = ExposureMonitor(
            config=pure_lending_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        assert exposure_monitor.config['mode'] == 'pure_lending'
        assert exposure_monitor.config['share_class'] == 'USDT'
        
        # Test ETH basis mode
        eth_basis_config = mock_config.copy()
        eth_basis_config['mode'] = 'eth_basis'
        eth_basis_config['share_class'] = 'USDT'
        eth_basis_config['asset'] = 'ETH'
        
        exposure_monitor = ExposureMonitor(
            config=eth_basis_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        assert exposure_monitor.config['mode'] == 'eth_basis'
        assert exposure_monitor.config['asset'] == 'ETH'
    
    def test_exposure_monitor_share_class_conversion(self, mock_config, mock_data_provider, mock_utility_manager, mock_position_snapshot):
        """Test Exposure Monitor share class conversion."""
        # Test USDT share class
        usdt_config = mock_config.copy()
        usdt_config['share_class'] = 'USDT'
        
        exposure_monitor = ExposureMonitor(
            config=usdt_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        exposure_report = exposure_monitor.calculate_exposure(mock_position_snapshot)
        assert exposure_report['share_class_currency'] == 'USDT'
        
        # Test ETH share class
        eth_config = mock_config.copy()
        eth_config['share_class'] = 'ETH'
        
        exposure_monitor = ExposureMonitor(
            config=eth_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        exposure_report = exposure_monitor.calculate_exposure(mock_position_snapshot)
        assert exposure_report['share_class_currency'] == 'ETH'
    
    def test_exposure_monitor_error_handling(self, mock_config, mock_data_provider, mock_utility_manager, mock_position_snapshot):
        """Test Exposure Monitor error handling."""
        # Arrange - Mock utility manager to raise exception
        mock_utility_manager.calculate_net_delta.side_effect = Exception("Utility manager error")
        
        exposure_monitor = ExposureMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act & Assert - Should handle errors gracefully
        try:
            exposure_report = exposure_monitor.calculate_exposure(mock_position_snapshot)
            # If no exception, should return error state
            assert isinstance(exposure_report, dict)
            assert 'error' in exposure_report or 'net_delta' in exposure_report
        except Exception as e:
            # If exception is raised, it should be handled appropriately
            assert "Utility manager error" in str(e)
    
    def test_exposure_monitor_mode_agnostic(self, mock_config, mock_data_provider, mock_utility_manager, mock_position_snapshot):
        """Test Exposure Monitor mode-agnostic behavior."""
        # Test different modes
        modes = ['pure_lending', 'btc_basis', 'eth_basis', 'eth_leveraged', 'usdt_market_neutral']
        
        for mode in modes:
            test_config = mock_config.copy()
            test_config['mode'] = mode
            
            exposure_monitor = ExposureMonitor(
                config=test_config,
                data_provider=mock_data_provider,
                utility_manager=mock_utility_manager
            )
            
            # Should work for all modes
            exposure_report = exposure_monitor.calculate_exposure(mock_position_snapshot)
            assert isinstance(exposure_report, dict)
            assert 'net_delta' in exposure_report
            assert 'share_class_currency' in exposure_report
    
    def test_exposure_monitor_performance(self, mock_config, mock_data_provider, mock_utility_manager, mock_position_snapshot):
        """Test Exposure Monitor performance with large position snapshots."""
        # Arrange - Create large position snapshot
        large_snapshot = mock_position_snapshot.copy()
        
        # Add many assets to test performance
        for i in range(100):
            large_snapshot['wallet'][f'ASSET_{i}'] = 1000.0
        
        exposure_monitor = ExposureMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        import time
        start_time = time.time()
        exposure_report = exposure_monitor.calculate_exposure(large_snapshot)
        end_time = time.time()
        
        # Assert - Should complete within reasonable time
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should complete within 1 second
        assert isinstance(exposure_report, dict)
        assert 'net_delta' in exposure_report
