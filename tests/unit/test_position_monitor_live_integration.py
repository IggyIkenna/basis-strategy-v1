"""
Unit tests for Position Monitor live integration.

Tests Position Monitor integration with position interfaces for live position monitoring.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock
import os

from backend.src.basis_strategy_v1.core.components.position_monitor import PositionMonitor
from backend.src.basis_strategy_v1.core.interfaces.execution_interface_factory import ExecutionInterfaceFactory


class TestPositionMonitorLiveIntegration:
    """Test Position Monitor live integration functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'component_config': {
                'position_monitor': {
                    'initial_balances': {
                        'cex_accounts': ['binance', 'bybit'],
                        'perp_positions': ['aave', 'lido']
                    }
                }
            }
        }
        self.data_provider = Mock()
        self.utility_manager = Mock()
        self.execution_interface_factory = Mock(spec=ExecutionInterfaceFactory)
    
    def test_position_monitor_initialization_with_factory(self):
        """Test Position Monitor initialization with execution interface factory."""
        # Mock position interfaces
        mock_position_interfaces = {
            'binance': Mock(),
            'bybit': Mock(),
            'aave': Mock(),
            'lido': Mock(),
            'wallet': Mock()
        }
        
        self.execution_interface_factory.get_position_interfaces.return_value = mock_position_interfaces
        
        # Create Position Monitor
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            self.execution_interface_factory
        )
        
        # Verify initialization
        assert position_monitor.execution_interface_factory == self.execution_interface_factory
        assert position_monitor.position_interfaces == mock_position_interfaces
        
        # Verify factory was called
        self.execution_interface_factory.get_position_interfaces.assert_called_once()
    
    def test_position_monitor_initialization_without_factory(self):
        """Test Position Monitor initialization without execution interface factory."""
        # Create Position Monitor without factory
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            None
        )
        
        # Verify initialization
        assert position_monitor.execution_interface_factory is None
        assert position_monitor.position_interfaces == {}
    
    def test_get_enabled_venues(self):
        """Test enabled venues extraction from config."""
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            None
        )
        
        venues = position_monitor._get_enabled_venues()
        
        # Should include CEX venues, OnChain venues, and wallet
        expected_venues = ['binance', 'bybit', 'aave', 'lido', 'wallet']
        assert set(venues) == set(expected_venues)
    
    def test_get_enabled_venues_empty_config(self):
        """Test enabled venues with empty config."""
        empty_config = {'component_config': {'position_monitor': {}}}
        
        position_monitor = PositionMonitor(
            empty_config,
            self.data_provider,
            self.utility_manager,
            None
        )
        
        venues = position_monitor._get_enabled_venues()
        
        # Should only include wallet
        assert venues == ['wallet']
    
    def test_get_execution_mode(self):
        """Test execution mode retrieval."""
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            None
        )
        
        # Test default mode
        with patch.dict(os.environ, {}, clear=True):
            mode = position_monitor._get_execution_mode()
            assert mode == 'backtest'
        
        # Test live mode
        with patch.dict(os.environ, {'BASIS_EXECUTION_MODE': 'live'}):
            mode = position_monitor._get_execution_mode()
            assert mode == 'live'
    
    @patch.dict(os.environ, {'BASIS_EXECUTION_MODE': 'backtest'})
    def test_get_real_positions_backtest_mode(self):
        """Test get_real_positions in backtest mode."""
        # Mock position interfaces
        mock_position_interfaces = {
            'binance': Mock(),
            'wallet': Mock()
        }
        
        self.execution_interface_factory.get_position_interfaces.return_value = mock_position_interfaces
        
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            self.execution_interface_factory
        )
        
        # Mock the simulated positions method
        mock_simulated_positions = {
            'timestamp': pd.Timestamp('2024-01-01'),
            'total_positions': {'USDT': 1000.0},
            'execution_mode': 'backtest'
        }
        
        with patch.object(position_monitor, '_get_simulated_positions', return_value=mock_simulated_positions):
            timestamp = pd.Timestamp('2024-01-01')
            positions = position_monitor.get_real_positions(timestamp)
            
            assert positions == mock_simulated_positions
            position_monitor._get_simulated_positions.assert_called_once_with(timestamp)
    
    @patch.dict(os.environ, {'BASIS_EXECUTION_MODE': 'live'})
    def test_get_real_positions_live_mode_with_interfaces(self):
        """Test get_real_positions in live mode with position interfaces."""
        # Mock position interfaces
        mock_position_interfaces = {
            'binance': Mock(),
            'wallet': Mock()
        }
        
        self.execution_interface_factory.get_position_interfaces.return_value = mock_position_interfaces
        
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            self.execution_interface_factory
        )
        
        # Mock the live positions method
        mock_live_positions = {
            'timestamp': pd.Timestamp('2024-01-01'),
            'total_positions': {'USDT': 1000.0},
            'execution_mode': 'live'
        }
        
        with patch.object(position_monitor, '_get_live_positions', return_value=mock_live_positions):
            timestamp = pd.Timestamp('2024-01-01')
            positions = position_monitor.get_real_positions(timestamp)
            
            assert positions == mock_live_positions
            position_monitor._get_live_positions.assert_called_once_with(timestamp)
    
    @patch.dict(os.environ, {'BASIS_EXECUTION_MODE': 'live'})
    def test_get_real_positions_live_mode_without_interfaces(self):
        """Test get_real_positions in live mode without position interfaces."""
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            None  # No factory, so no interfaces
        )
        
        # Mock the simulated positions method (fallback)
        mock_simulated_positions = {
            'timestamp': pd.Timestamp('2024-01-01'),
            'total_positions': {'USDT': 1000.0},
            'execution_mode': 'backtest'
        }
        
        with patch.object(position_monitor, '_get_simulated_positions', return_value=mock_simulated_positions):
            timestamp = pd.Timestamp('2024-01-01')
            positions = position_monitor.get_real_positions(timestamp)
            
            assert positions == mock_simulated_positions
            position_monitor._get_simulated_positions.assert_called_once_with(timestamp)
    
    @patch.dict(os.environ, {'BASIS_EXECUTION_MODE': 'live'})
    def test_get_live_positions_success(self):
        """Test successful live position retrieval."""
        # Mock position interfaces with async methods
        mock_binance_interface = Mock()
        mock_binance_interface.get_positions = AsyncMock(return_value={
            'venue': 'binance',
            'spot_balances': {'USDT': 1000.0},
            'perp_positions': {}
        })
        
        mock_wallet_interface = Mock()
        mock_wallet_interface.get_positions = AsyncMock(return_value={
            'venue': 'wallet',
            'wallet_balances': {'ETH': 1.0}
        })
        
        mock_position_interfaces = {
            'binance': mock_binance_interface,
            'wallet': mock_wallet_interface
        }
        
        self.execution_interface_factory.get_position_interfaces.return_value = mock_position_interfaces
        
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            self.execution_interface_factory
        )
        
        # Mock the aggregate method
        mock_aggregated_positions = {
            'timestamp': pd.Timestamp('2024-01-01'),
            'total_positions': {'USDT': 1000.0, 'ETH': 1.0},
            'execution_mode': 'live'
        }
        
        with patch.object(position_monitor, '_aggregate_venue_positions', return_value=mock_aggregated_positions):
            timestamp = pd.Timestamp('2024-01-01')
            positions = position_monitor._get_live_positions(timestamp)
            
            assert positions == mock_aggregated_positions
            
            # Verify interfaces were called
            mock_binance_interface.get_positions.assert_called_once_with(timestamp)
            mock_wallet_interface.get_positions.assert_called_once_with(timestamp)
    
    @patch.dict(os.environ, {'BASIS_EXECUTION_MODE': 'live'})
    def test_get_live_positions_interface_error(self):
        """Test live position retrieval with interface error."""
        # Mock position interfaces with one failing
        mock_binance_interface = Mock()
        mock_binance_interface.get_positions = AsyncMock(side_effect=Exception("API Error"))
        
        mock_wallet_interface = Mock()
        mock_wallet_interface.get_positions = AsyncMock(return_value={
            'venue': 'wallet',
            'wallet_balances': {'ETH': 1.0}
        })
        
        mock_position_interfaces = {
            'binance': mock_binance_interface,
            'wallet': mock_wallet_interface
        }
        
        self.execution_interface_factory.get_position_interfaces.return_value = mock_position_interfaces
        
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            self.execution_interface_factory
        )
        
        # Mock the aggregate method
        mock_aggregated_positions = {
            'timestamp': pd.Timestamp('2024-01-01'),
            'total_positions': {'ETH': 1.0},
            'execution_mode': 'live'
        }
        
        with patch.object(position_monitor, '_aggregate_venue_positions', return_value=mock_aggregated_positions):
            timestamp = pd.Timestamp('2024-01-01')
            positions = position_monitor._get_live_positions(timestamp)
            
            assert positions == mock_aggregated_positions
            
            # Verify both interfaces were called (even though one failed)
            mock_binance_interface.get_positions.assert_called_once_with(timestamp)
            mock_wallet_interface.get_positions.assert_called_once_with(timestamp)
    
    def test_aggregate_venue_positions(self):
        """Test venue position aggregation."""
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            None
        )
        
        # Mock venue positions
        venue_positions = {
            'wallet': {
                'wallet_balances': {'USDT': 1000.0, 'ETH': 1.0}
            },
            'binance': {
                'spot_balances': {'USDT': 500.0},
                'perp_positions': {'ETHUSDT': {'size': 0.5}}
            },
            'aave': {
                'supply_positions': {'aUSDT': 200.0},
                'borrow_positions': {'variableDebtWETH': 0.1}
            }
        }
        
        # Mock the calculation methods
        with patch.object(position_monitor, '_calculate_total_positions') as mock_calc_total, \
             patch.object(position_monitor, '_calculate_position_metrics') as mock_calc_metrics, \
             patch.object(position_monitor, '_calculate_position_by_category') as mock_calc_category, \
             patch.object(position_monitor, '_update_last_positions') as mock_update:
            
            mock_calc_total.return_value = {'USDT': 1700.0, 'ETH': 1.0}
            mock_calc_metrics.return_value = {'total_value': 2000.0}
            mock_calc_category.return_value = {'wallet': 1000.0, 'cex': 500.0, 'onchain': 200.0}
            
            timestamp = pd.Timestamp('2024-01-01')
            result = position_monitor._aggregate_venue_positions(venue_positions, timestamp)
            
            # Verify result structure
            assert result['timestamp'] == timestamp
            assert result['execution_mode'] == 'live'
            assert 'total_positions' in result
            assert 'position_metrics' in result
            assert 'position_by_category' in result
            assert 'wallet_positions' in result
            assert 'smart_contract_positions' in result
            assert 'cex_spot_positions' in result
            assert 'cex_derivatives_positions' in result
            
            # Verify calculation methods were called
            mock_calc_total.assert_called_once()
            mock_calc_metrics.assert_called_once()
            mock_calc_category.assert_called_once()
            mock_update.assert_called_once()
    
    def test_aggregate_venue_positions_empty(self):
        """Test venue position aggregation with empty positions."""
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            None
        )
        
        # Empty venue positions
        venue_positions = {}
        
        # Mock the calculation methods
        with patch.object(position_monitor, '_calculate_total_positions') as mock_calc_total, \
             patch.object(position_monitor, '_calculate_position_metrics') as mock_calc_metrics, \
             patch.object(position_monitor, '_calculate_position_by_category') as mock_calc_category, \
             patch.object(position_monitor, '_update_last_positions') as mock_update:
            
            mock_calc_total.return_value = {}
            mock_calc_metrics.return_value = {}
            mock_calc_category.return_value = {}
            
            timestamp = pd.Timestamp('2024-01-01')
            result = position_monitor._aggregate_venue_positions(venue_positions, timestamp)
            
            # Verify result structure
            assert result['timestamp'] == timestamp
            assert result['execution_mode'] == 'live'
            assert result['wallet_positions'] == {}
            assert result['smart_contract_positions'] == {}
            assert result['cex_spot_positions'] == {}
            assert result['cex_derivatives_positions'] == {}
    
    def test_initialize_position_interfaces_success(self):
        """Test successful position interface initialization."""
        # Mock position interfaces
        mock_position_interfaces = {
            'binance': Mock(),
            'wallet': Mock()
        }
        
        self.execution_interface_factory.get_position_interfaces.return_value = mock_position_interfaces
        
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            self.execution_interface_factory
        )
        
        # Verify initialization
        assert position_monitor.position_interfaces == mock_position_interfaces
        
        # Verify factory was called with correct parameters
        self.execution_interface_factory.get_position_interfaces.assert_called_once()
        call_args = self.execution_interface_factory.get_position_interfaces.call_args
        assert set(call_args[0][0]) == {'binance', 'bybit', 'aave', 'lido', 'wallet'}  # venues
        assert call_args[0][1] == 'backtest'  # execution_mode
        assert call_args[0][2] == self.config  # config
    
    def test_initialize_position_interfaces_error(self):
        """Test position interface initialization with error."""
        # Mock factory to raise exception
        self.execution_interface_factory.get_position_interfaces.side_effect = Exception("Factory Error")
        
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            self.execution_interface_factory
        )
        
        # Verify error handling
        assert position_monitor.position_interfaces == {}
    
    def test_get_real_positions_error_handling(self):
        """Test error handling in get_real_positions."""
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            None
        )
        
        # Mock _get_simulated_positions to raise exception
        with patch.object(position_monitor, '_get_simulated_positions', side_effect=Exception("Position Error")):
            timestamp = pd.Timestamp('2024-01-01')
            
            with pytest.raises(Exception, match="Position Error"):
                position_monitor.get_real_positions(timestamp)


class TestPositionMonitorBackwardCompatibility:
    """Test Position Monitor backward compatibility."""
    
    def test_backward_compatibility_without_factory(self):
        """Test that Position Monitor works without execution interface factory."""
        config = {
            'component_config': {
                'position_monitor': {
                    'initial_balances': {
                        'cex_accounts': ['binance'],
                        'perp_positions': ['aave']
                    }
                }
            }
        }
        
        data_provider = Mock()
        utility_manager = Mock()
        
        # Create Position Monitor without factory (backward compatibility)
        position_monitor = PositionMonitor(
            config,
            data_provider,
            utility_manager,
            None  # No factory
        )
        
        # Should still work
        assert position_monitor.execution_interface_factory is None
        assert position_monitor.position_interfaces == {}
        
        # Should fall back to simulated positions
        with patch.object(position_monitor, '_get_simulated_positions') as mock_sim:
            mock_sim.return_value = {'test': 'positions'}
            
            timestamp = pd.Timestamp('2024-01-01')
            positions = position_monitor.get_real_positions(timestamp)
            
            assert positions == {'test': 'positions'}
            mock_sim.assert_called_once_with(timestamp)
    
    def test_backward_compatibility_with_factory(self):
        """Test that Position Monitor works with execution interface factory."""
        config = {
            'component_config': {
                'position_monitor': {
                    'initial_balances': {
                        'cex_accounts': ['binance'],
                        'perp_positions': ['aave']
                    }
                }
            }
        }
        
        data_provider = Mock()
        utility_manager = Mock()
        execution_interface_factory = Mock(spec=ExecutionInterfaceFactory)
        
        # Mock position interfaces
        mock_position_interfaces = {
            'binance': Mock(),
            'aave': Mock(),
            'wallet': Mock()
        }
        execution_interface_factory.get_position_interfaces.return_value = mock_position_interfaces
        
        # Create Position Monitor with factory
        position_monitor = PositionMonitor(
            config,
            data_provider,
            utility_manager,
            execution_interface_factory
        )
        
        # Should work with factory
        assert position_monitor.execution_interface_factory == execution_interface_factory
        assert position_monitor.position_interfaces == mock_position_interfaces
