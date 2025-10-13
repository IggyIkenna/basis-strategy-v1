"""
Unit tests for Venue Interface Factory position monitoring extensions.

Tests position interface creation and management functionality.
"""

import pytest
from unittest.mock import Mock, patch
import pandas as pd

from backend.src.basis_strategy_v1.core.interfaces.venue_interface_factory import VenueInterfaceFactory
from backend.src.basis_strategy_v1.core.interfaces.base_position_interface import BasePositionInterface
from backend.src.basis_strategy_v1.core.interfaces.cex_position_interface import CEXPositionInterface
from backend.src.basis_strategy_v1.core.interfaces.onchain_position_interface import OnChainPositionInterface
from backend.src.basis_strategy_v1.core.interfaces.transfer_position_interface import TransferPositionInterface


class TestVenueInterfaceFactoryPositionExtensions:
    """Test Venue Interface Factory position monitoring extensions."""
    
    def test_create_venue_position_interface_cex(self):
        """Test CEX position interface creation."""
        config = {'test': 'config'}
        
        # Test Binance
        interface = VenueInterfaceFactory.create_venue_position_interface(
            'binance', 'backtest', config
        )
        assert isinstance(interface, CEXPositionInterface)
        assert interface.venue == 'binance'
        assert interface.execution_mode == 'backtest'
        
        # Test Bybit
        interface = VenueInterfaceFactory.create_venue_position_interface(
            'bybit', 'backtest', config
        )
        assert isinstance(interface, CEXPositionInterface)
        assert interface.venue == 'bybit'
        
        # Test OKX
        interface = VenueInterfaceFactory.create_venue_position_interface(
            'okx', 'backtest', config
        )
        assert isinstance(interface, CEXPositionInterface)
        assert interface.venue == 'okx'
    
    def test_create_venue_position_interface_onchain(self):
        """Test OnChain position interface creation."""
        config = {'test': 'config'}
        
        # Test AAVE
        interface = VenueInterfaceFactory.create_venue_position_interface(
            'aave', 'backtest', config
        )
        assert isinstance(interface, OnChainPositionInterface)
        assert interface.venue == 'aave'
        assert interface.execution_mode == 'backtest'
        
        # Test Morpho
        interface = VenueInterfaceFactory.create_venue_position_interface(
            'morpho', 'backtest', config
        )
        assert isinstance(interface, OnChainPositionInterface)
        assert interface.venue == 'morpho'
        
        # Test Lido
        interface = VenueInterfaceFactory.create_venue_position_interface(
            'lido', 'backtest', config
        )
        assert isinstance(interface, OnChainPositionInterface)
        assert interface.venue == 'lido'
        
        # Test EtherFi
        interface = VenueInterfaceFactory.create_venue_position_interface(
            'etherfi', 'backtest', config
        )
        assert isinstance(interface, OnChainPositionInterface)
        assert interface.venue == 'etherfi'
    
    def test_create_venue_position_interface_transfer(self):
        """Test Transfer position interface creation."""
        config = {'test': 'config'}
        
        interface = VenueInterfaceFactory.create_venue_position_interface(
            'wallet', 'backtest', config
        )
        assert isinstance(interface, TransferPositionInterface)
        assert interface.venue == 'wallet'
        assert interface.execution_mode == 'backtest'
    
    def test_create_venue_position_interface_unsupported_venue(self):
        """Test error handling for unsupported venues."""
        config = {'test': 'config'}
        
        with pytest.raises(ValueError, match="Unsupported venue for position monitoring"):
            VenueInterfaceFactory.create_venue_position_interface(
                'unsupported_venue', 'backtest', config
            )
    
    def test_create_venue_position_interface_live_mode(self):
        """Test position interface creation in live mode."""
        config = {'test': 'config'}
        
        # Test CEX in live mode
        interface = VenueInterfaceFactory.create_venue_position_interface(
            'binance', 'live', config
        )
        assert isinstance(interface, CEXPositionInterface)
        assert interface.execution_mode == 'live'
        
        # Test OnChain in live mode
        interface = VenueInterfaceFactory.create_venue_position_interface(
            'aave', 'live', config
        )
        assert isinstance(interface, OnChainPositionInterface)
        assert interface.execution_mode == 'live'
        
        # Test Transfer in live mode
        interface = VenueInterfaceFactory.create_venue_position_interface(
            'wallet', 'live', config
        )
        assert isinstance(interface, TransferPositionInterface)
        assert interface.execution_mode == 'live'
    
    def test_get_venue_position_interfaces_single_venue(self):
        """Test position interface creation for single venue."""
        config = {'test': 'config'}
        
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            ['binance'], 'backtest', config
        )
        
        assert len(interfaces) == 1
        assert 'binance' in interfaces
        assert isinstance(interfaces['binance'], CEXPositionInterface)
        assert interfaces['binance'].venue == 'binance'
    
    def test_get_venue_position_interfaces_multiple_venues(self):
        """Test position interface creation for multiple venues."""
        config = {'test': 'config'}
        
        venues = ['binance', 'aave', 'wallet']
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'backtest', config
        )
        
        assert len(interfaces) == 3
        assert 'binance' in interfaces
        assert 'aave' in interfaces
        assert 'wallet' in interfaces
        
        # Verify correct interface types
        assert isinstance(interfaces['binance'], CEXPositionInterface)
        assert isinstance(interfaces['aave'], OnChainPositionInterface)
        assert isinstance(interfaces['wallet'], TransferPositionInterface)
        
        # Verify all are in backtest mode
        for interface in interfaces.values():
            assert interface.execution_mode == 'backtest'
    
    def test_get_venue_position_interfaces_mixed_venues(self):
        """Test position interface creation for mixed venue types."""
        config = {'test': 'config'}
        
        venues = ['binance', 'bybit', 'okx', 'aave', 'morpho', 'lido', 'etherfi', 'wallet']
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'backtest', config
        )
        
        assert len(interfaces) == 8
        
        # Verify CEX venues
        cex_venues = ['binance', 'bybit', 'okx']
        for venue in cex_venues:
            assert venue in interfaces
            assert isinstance(interfaces[venue], CEXPositionInterface)
        
        # Verify OnChain venues
        onchain_venues = ['aave', 'morpho', 'lido', 'etherfi']
        for venue in onchain_venues:
            assert venue in interfaces
            assert isinstance(interfaces[venue], OnChainPositionInterface)
        
        # Verify Transfer venue
        assert 'wallet' in interfaces
        assert isinstance(interfaces['wallet'], TransferPositionInterface)
    
    def test_get_venue_position_interfaces_with_unsupported_venue(self):
        """Test position interface creation with unsupported venue."""
        config = {'test': 'config'}
        
        venues = ['binance', 'unsupported_venue', 'aave']
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'backtest', config
        )
        
        assert len(interfaces) == 3
        assert 'binance' in interfaces
        assert 'unsupported_venue' in interfaces
        assert 'aave' in interfaces
        
        # Verify supported venues work
        assert isinstance(interfaces['binance'], CEXPositionInterface)
        assert isinstance(interfaces['aave'], OnChainPositionInterface)
        
        # Verify unsupported venue is None
        assert interfaces['unsupported_venue'] is None
    
    def test_get_venue_position_interfaces_empty_list(self):
        """Test position interface creation with empty venue list."""
        config = {'test': 'config'}
        
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            [], 'backtest', config
        )
        
        assert len(interfaces) == 0
        assert interfaces == {}
    
    def test_get_venue_position_interfaces_live_mode(self):
        """Test position interface creation in live mode."""
        config = {'test': 'config'}
        
        venues = ['binance', 'aave', 'wallet']
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'live', config
        )
        
        assert len(interfaces) == 3
        
        # Verify all are in live mode
        for interface in interfaces.values():
            assert interface.execution_mode == 'live'
    
    def test_get_venue_position_interfaces_config_preservation(self):
        """Test that config is properly passed to all interfaces."""
        config = {'test': 'config', 'venue_specific': 'value'}
        
        venues = ['binance', 'aave', 'wallet']
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'backtest', config
        )
        
        # Verify config is preserved in all interfaces
        for interface in interfaces.values():
            assert interface.config == config
    
    @patch('backend.src.basis_strategy_v1.core.interfaces.execution_interface_factory.logger')
    def test_get_venue_position_interfaces_logging(self, mock_logger):
        """Test that position interface creation is properly logged."""
        config = {'test': 'config'}
        
        venues = ['binance', 'aave']
        VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'backtest', config
        )
        
        # Verify logging calls
        assert mock_logger.info.call_count >= 2  # At least one log per successful interface
        
        # Check that each venue is logged
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any('binance' in call for call in log_calls)
        assert any('aave' in call for call in log_calls)
    
    @patch('backend.src.basis_strategy_v1.core.interfaces.execution_interface_factory.logger')
    def test_get_venue_position_interfaces_error_logging(self, mock_logger):
        """Test that position interface creation errors are properly logged."""
        config = {'test': 'config'}
        
        venues = ['binance', 'unsupported_venue']
        VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'backtest', config
        )
        
        # Verify error logging
        error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
        assert any('unsupported_venue' in call for call in error_calls)
    
    def test_position_interface_factory_consistency(self):
        """Test that factory methods are consistent with each other."""
        config = {'test': 'config'}
        
        # Test individual creation
        individual_interface = VenueInterfaceFactory.create_venue_position_interface(
            'binance', 'backtest', config
        )
        
        # Test batch creation
        batch_interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            ['binance'], 'backtest', config
        )
        
        # Verify consistency
        assert isinstance(individual_interface, CEXPositionInterface)
        assert isinstance(batch_interfaces['binance'], CEXPositionInterface)
        assert individual_interface.venue == batch_interfaces['binance'].venue
        assert individual_interface.execution_mode == batch_interfaces['binance'].execution_mode
        assert individual_interface.config == batch_interfaces['binance'].config


class TestPositionInterfaceFactoryIntegration:
    """Test position interface factory integration scenarios."""
    
    def test_all_supported_venues(self):
        """Test that all supported venues can be created."""
        config = {'test': 'config'}
        
        # All supported venues
        cex_venues = ['binance', 'bybit', 'okx']
        onchain_venues = ['aave', 'morpho', 'lido', 'etherfi']
        transfer_venues = ['wallet']
        
        all_venues = cex_venues + onchain_venues + transfer_venues
        
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            all_venues, 'backtest', config
        )
        
        # Verify all venues are created successfully
        assert len(interfaces) == len(all_venues)
        for venue in all_venues:
            assert venue in interfaces
            assert interfaces[venue] is not None
        
        # Verify correct interface types
        for venue in cex_venues:
            assert isinstance(interfaces[venue], CEXPositionInterface)
        
        for venue in onchain_venues:
            assert isinstance(interfaces[venue], OnChainPositionInterface)
        
        for venue in transfer_venues:
            assert isinstance(interfaces[venue], TransferPositionInterface)
    
    def test_venue_type_classification(self):
        """Test that venues are correctly classified by type."""
        config = {'test': 'config'}
        
        # Test CEX venue classification
        cex_interface = VenueInterfaceFactory.create_venue_position_interface(
            'binance', 'backtest', config
        )
        assert isinstance(cex_interface, CEXPositionInterface)
        
        # Test OnChain venue classification
        onchain_interface = VenueInterfaceFactory.create_venue_position_interface(
            'aave', 'backtest', config
        )
        assert isinstance(onchain_interface, OnChainPositionInterface)
        
        # Test Transfer venue classification
        transfer_interface = VenueInterfaceFactory.create_venue_position_interface(
            'wallet', 'backtest', config
        )
        assert isinstance(transfer_interface, TransferPositionInterface)
    
    def test_execution_mode_consistency(self):
        """Test that execution mode is consistently applied."""
        config = {'test': 'config'}
        
        # Test backtest mode
        backtest_interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            ['binance', 'aave', 'wallet'], 'backtest', config
        )
        for interface in backtest_interfaces.values():
            assert interface.execution_mode == 'backtest'
        
        # Test live mode
        live_interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            ['binance', 'aave', 'wallet'], 'live', config
        )
        for interface in live_interfaces.values():
            assert interface.execution_mode == 'live'
