"""
Integration tests for position monitor live workflow.

Tests end-to-end position monitoring workflow with position interfaces.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock
import os

from backend.src.basis_strategy_v1.core.components.position_monitor import PositionMonitor
from backend.src.basis_strategy_v1.core.interfaces.execution_interface_factory import ExecutionInterfaceFactory
from backend.src.basis_strategy_v1.core.interfaces.cex_position_interface import CEXPositionInterface
from backend.src.basis_strategy_v1.core.interfaces.onchain_position_interface import OnChainPositionInterface
from backend.src.basis_strategy_v1.core.interfaces.transfer_position_interface import TransferPositionInterface


class TestPositionMonitorLiveWorkflow:
    """Test end-to-end position monitor live workflow."""
    
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
    
    @patch.dict(os.environ, {'BASIS_EXECUTION_MODE': 'live'})
    def test_end_to_end_live_position_workflow(self):
        """Test complete end-to-end live position monitoring workflow."""
        # Create execution interface factory
        factory = ExecutionInterfaceFactory()
        
        # Create position monitor with factory
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            factory
        )
        
        # Verify position interfaces were created
        assert len(position_monitor.position_interfaces) > 0
        assert 'wallet' in position_monitor.position_interfaces
        assert 'binance' in position_monitor.position_interfaces
        assert 'bybit' in position_monitor.position_interfaces
        assert 'aave' in position_monitor.position_interfaces
        assert 'lido' in position_monitor.position_interfaces
        
        # Verify interface types
        assert isinstance(position_monitor.position_interfaces['wallet'], TransferPositionInterface)
        assert isinstance(position_monitor.position_interfaces['binance'], CEXPositionInterface)
        assert isinstance(position_monitor.position_interfaces['bybit'], CEXPositionInterface)
        assert isinstance(position_monitor.position_interfaces['aave'], OnChainPositionInterface)
        assert isinstance(position_monitor.position_interfaces['lido'], OnChainPositionInterface)
        
        # Verify all interfaces are in live mode
        for interface in position_monitor.position_interfaces.values():
            assert interface.execution_mode == 'live'
    
    @patch.dict(os.environ, {'BASIS_EXECUTION_MODE': 'backtest'})
    def test_end_to_end_backtest_position_workflow(self):
        """Test complete end-to-end backtest position monitoring workflow."""
        # Create execution interface factory
        factory = ExecutionInterfaceFactory()
        
        # Create position monitor with factory
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            factory
        )
        
        # Verify position interfaces were created
        assert len(position_monitor.position_interfaces) > 0
        
        # Verify all interfaces are in backtest mode
        for interface in position_monitor.position_interfaces.values():
            assert interface.execution_mode == 'backtest'
    
    @patch.dict(os.environ, {'BASIS_EXECUTION_MODE': 'live'})
    def test_live_position_retrieval_workflow(self):
        """Test live position retrieval workflow."""
        # Create execution interface factory
        factory = ExecutionInterfaceFactory()
        
        # Create position monitor with factory
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            factory
        )
        
        # Mock the position interfaces to return realistic data
        for venue, interface in position_monitor.position_interfaces.items():
            if venue == 'wallet':
                interface.get_positions = AsyncMock(return_value={
                    'venue': 'wallet',
                    'wallet_balances': {'USDT': 1000.0, 'ETH': 1.0}
                })
            elif venue in ['binance', 'bybit']:
                interface.get_positions = AsyncMock(return_value={
                    'venue': venue,
                    'spot_balances': {'USDT': 500.0},
                    'perp_positions': {}
                })
            elif venue in ['aave', 'lido']:
                interface.get_positions = AsyncMock(return_value={
                    'venue': venue,
                    'positions': {'aUSDT': 200.0} if venue == 'aave' else {'stETH': 0.5}
                })
        
        # Mock the calculation methods
        with patch.object(position_monitor, '_calculate_total_positions') as mock_calc_total, \
             patch.object(position_monitor, '_calculate_position_metrics') as mock_calc_metrics, \
             patch.object(position_monitor, '_calculate_position_by_category') as mock_calc_category, \
             patch.object(position_monitor, '_update_last_positions') as mock_update:
            
            mock_calc_total.return_value = {'USDT': 1700.0, 'ETH': 1.0}
            mock_calc_metrics.return_value = {'total_value': 2000.0}
            mock_calc_category.return_value = {'wallet': 1000.0, 'cex': 1000.0, 'onchain': 200.0}
            
            # Get positions
            timestamp = pd.Timestamp('2024-01-01')
            positions = position_monitor.get_real_positions(timestamp)
            
            # Verify result structure
            assert positions['timestamp'] == timestamp
            assert positions['execution_mode'] == 'live'
            assert 'total_positions' in positions
            assert 'position_metrics' in positions
            assert 'position_by_category' in positions
            assert 'wallet_positions' in positions
            assert 'smart_contract_positions' in positions
            assert 'cex_spot_positions' in positions
            assert 'cex_derivatives_positions' in positions
            
            # Verify calculation methods were called
            mock_calc_total.assert_called_once()
            mock_calc_metrics.assert_called_once()
            mock_calc_category.assert_called_once()
            mock_update.assert_called_once()
    
    @patch.dict(os.environ, {'BASIS_EXECUTION_MODE': 'live'})
    def test_live_position_retrieval_with_errors(self):
        """Test live position retrieval workflow with interface errors."""
        # Create execution interface factory
        factory = ExecutionInterfaceFactory()
        
        # Create position monitor with factory
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            factory
        )
        
        # Mock some interfaces to fail
        for venue, interface in position_monitor.position_interfaces.items():
            if venue == 'binance':
                interface.get_positions = AsyncMock(side_effect=Exception("API Error"))
            elif venue == 'wallet':
                interface.get_positions = AsyncMock(return_value={
                    'venue': 'wallet',
                    'wallet_balances': {'USDT': 1000.0}
                })
            else:
                interface.get_positions = AsyncMock(return_value={
                    'venue': venue,
                    'positions': {}
                })
        
        # Mock the calculation methods
        with patch.object(position_monitor, '_calculate_total_positions') as mock_calc_total, \
             patch.object(position_monitor, '_calculate_position_metrics') as mock_calc_metrics, \
             patch.object(position_monitor, '_calculate_position_by_category') as mock_calc_category, \
             patch.object(position_monitor, '_update_last_positions') as mock_update:
            
            mock_calc_total.return_value = {'USDT': 1000.0}
            mock_calc_metrics.return_value = {'total_value': 1000.0}
            mock_calc_category.return_value = {'wallet': 1000.0, 'cex': 0.0, 'onchain': 0.0}
            
            # Get positions (should handle errors gracefully)
            timestamp = pd.Timestamp('2024-01-01')
            positions = position_monitor.get_real_positions(timestamp)
            
            # Verify result structure (should still work despite errors)
            assert positions['timestamp'] == timestamp
            assert positions['execution_mode'] == 'live'
            assert 'total_positions' in positions
            assert 'position_metrics' in positions
            assert 'position_by_category' in positions
    
    @patch.dict(os.environ, {'BASIS_EXECUTION_MODE': 'backtest'})
    def test_backtest_position_retrieval_workflow(self):
        """Test backtest position retrieval workflow."""
        # Create execution interface factory
        factory = ExecutionInterfaceFactory()
        
        # Create position monitor with factory
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            factory
        )
        
        # Mock the simulated positions method
        mock_simulated_positions = {
            'timestamp': pd.Timestamp('2024-01-01'),
            'total_positions': {'USDT': 1000.0, 'ETH': 1.0},
            'execution_mode': 'backtest'
        }
        
        with patch.object(position_monitor, '_get_simulated_positions', return_value=mock_simulated_positions):
            timestamp = pd.Timestamp('2024-01-01')
            positions = position_monitor.get_real_positions(timestamp)
            
            assert positions == mock_simulated_positions
            position_monitor._get_simulated_positions.assert_called_once_with(timestamp)
    
    def test_factory_position_interface_creation_integration(self):
        """Test factory position interface creation integration."""
        # Test individual interface creation
        config = {'test': 'config'}
        
        # Test CEX interface creation
        cex_interface = ExecutionInterfaceFactory.create_position_interface(
            'binance', 'live', config
        )
        assert isinstance(cex_interface, CEXPositionInterface)
        assert cex_interface.venue == 'binance'
        assert cex_interface.execution_mode == 'live'
        
        # Test OnChain interface creation
        onchain_interface = ExecutionInterfaceFactory.create_position_interface(
            'aave', 'live', config
        )
        assert isinstance(onchain_interface, OnChainPositionInterface)
        assert onchain_interface.venue == 'aave'
        assert onchain_interface.execution_mode == 'live'
        
        # Test Transfer interface creation
        transfer_interface = ExecutionInterfaceFactory.create_position_interface(
            'wallet', 'live', config
        )
        assert isinstance(transfer_interface, TransferPositionInterface)
        assert transfer_interface.venue == 'wallet'
        assert transfer_interface.execution_mode == 'live'
    
    def test_factory_batch_position_interface_creation_integration(self):
        """Test factory batch position interface creation integration."""
        config = {'test': 'config'}
        venues = ['binance', 'aave', 'wallet']
        
        # Create multiple interfaces
        interfaces = ExecutionInterfaceFactory.get_position_interfaces(
            venues, 'live', config
        )
        
        # Verify all interfaces were created
        assert len(interfaces) == 3
        assert 'binance' in interfaces
        assert 'aave' in interfaces
        assert 'wallet' in interfaces
        
        # Verify interface types
        assert isinstance(interfaces['binance'], CEXPositionInterface)
        assert isinstance(interfaces['aave'], OnChainPositionInterface)
        assert isinstance(interfaces['wallet'], TransferPositionInterface)
        
        # Verify all are in live mode
        for interface in interfaces.values():
            assert interface.execution_mode == 'live'
    
    def test_position_monitor_initialization_sequence_integration(self):
        """Test position monitor initialization sequence integration."""
        # Test that factory is created first, then position monitor
        factory = ExecutionInterfaceFactory()
        
        # Verify factory is ready
        assert factory is not None
        
        # Create position monitor with factory
        position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            factory
        )
        
        # Verify position monitor was initialized with factory
        assert position_monitor.execution_interface_factory == factory
        assert len(position_monitor.position_interfaces) > 0
        
        # Verify all position interfaces are properly initialized
        for venue, interface in position_monitor.position_interfaces.items():
            assert interface is not None
            assert interface.venue == venue
            assert interface.config == self.config
    
    def test_position_monitor_backward_compatibility_integration(self):
        """Test position monitor backward compatibility integration."""
        # Test without factory (backward compatibility)
        position_monitor_no_factory = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            None
        )
        
        assert position_monitor_no_factory.execution_interface_factory is None
        assert position_monitor_no_factory.position_interfaces == {}
        
        # Test with factory (new functionality)
        factory = ExecutionInterfaceFactory()
        position_monitor_with_factory = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            factory
        )
        
        assert position_monitor_with_factory.execution_interface_factory == factory
        assert len(position_monitor_with_factory.position_interfaces) > 0
    
    def test_venue_configuration_integration(self):
        """Test venue configuration integration."""
        # Test with different venue configurations
        config_with_cex_only = {
            'component_config': {
                'position_monitor': {
                    'initial_balances': {
                        'cex_accounts': ['binance', 'bybit', 'okx'],
                        'perp_positions': []
                    }
                }
            }
        }
        
        factory = ExecutionInterfaceFactory()
        position_monitor = PositionMonitor(
            config_with_cex_only,
            self.data_provider,
            self.utility_manager,
            factory
        )
        
        # Verify only CEX venues and wallet are created
        expected_venues = {'binance', 'bybit', 'okx', 'wallet'}
        actual_venues = set(position_monitor.position_interfaces.keys())
        assert actual_venues == expected_venues
        
        # Verify all are CEX interfaces except wallet
        for venue, interface in position_monitor.position_interfaces.items():
            if venue == 'wallet':
                assert isinstance(interface, TransferPositionInterface)
            else:
                assert isinstance(interface, CEXPositionInterface)
    
    def test_execution_mode_consistency_integration(self):
        """Test execution mode consistency across all components."""
        # Test backtest mode
        with patch.dict(os.environ, {'BASIS_EXECUTION_MODE': 'backtest'}):
            factory = ExecutionInterfaceFactory()
            position_monitor = PositionMonitor(
                self.config,
                self.data_provider,
                self.utility_manager,
                factory
            )
            
            # Verify all interfaces are in backtest mode
            for interface in position_monitor.position_interfaces.values():
                assert interface.execution_mode == 'backtest'
        
        # Test live mode
        with patch.dict(os.environ, {'BASIS_EXECUTION_MODE': 'live'}):
            factory = ExecutionInterfaceFactory()
            position_monitor = PositionMonitor(
                self.config,
                self.data_provider,
                self.utility_manager,
                factory
            )
            
            # Verify all interfaces are in live mode
            for interface in position_monitor.position_interfaces.values():
                assert interface.execution_mode == 'live'
