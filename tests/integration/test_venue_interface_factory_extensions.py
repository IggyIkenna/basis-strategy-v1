"""
Integration tests for Venue Interface Factory extensions.

Tests end-to-end venue interface factory position monitoring extensions.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
import os

from backend.src.basis_strategy_v1.core.interfaces.venue_interface_factory import VenueInterfaceFactory
from backend.src.basis_strategy_v1.core.interfaces.cex_position_interface import CEXPositionInterface
from backend.src.basis_strategy_v1.core.interfaces.onchain_position_interface import OnChainPositionInterface
from backend.src.basis_strategy_v1.core.interfaces.transfer_position_interface import TransferPositionInterface


class TestVenueInterfaceFactoryExtensions:
    """Test Venue Interface Factory position monitoring extensions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'component_config': {
                'position_monitor': {
                    'initial_balances': {
                        'cex_accounts': ['binance', 'bybit', 'okx'],
                        'perp_positions': ['aave', 'morpho', 'lido', 'etherfi']
                    }
                }
            }
        }
    
    def test_factory_position_interface_creation_all_venues(self):
        """Test factory position interface creation for all supported venues."""
        # Test all CEX venues
        cex_venues = ['binance', 'bybit', 'okx']
        for venue in cex_venues:
            interface = VenueInterfaceFactory.create_venue_position_interface(
                venue, 'live', self.config
            )
            assert isinstance(interface, CEXPositionInterface)
            assert interface.venue == venue
            assert interface.execution_mode == 'live'
            assert interface.config == self.config
        
        # Test all OnChain venues
        onchain_venues = ['aave', 'morpho', 'lido', 'etherfi']
        for venue in onchain_venues:
            interface = VenueInterfaceFactory.create_venue_position_interface(
                venue, 'live', self.config
            )
            assert isinstance(interface, OnChainPositionInterface)
            assert interface.venue == venue
            assert interface.execution_mode == 'live'
            assert interface.config == self.config
        
        # Test Transfer venue
        transfer_venue = 'wallet'
        interface = VenueInterfaceFactory.create_venue_position_interface(
            transfer_venue, 'live', self.config
        )
        assert isinstance(interface, TransferPositionInterface)
        assert interface.venue == transfer_venue
        assert interface.execution_mode == 'live'
        assert interface.config == self.config
    
    def test_factory_batch_position_interface_creation_all_venues(self):
        """Test factory batch position interface creation for all supported venues."""
        all_venues = ['binance', 'bybit', 'okx', 'aave', 'morpho', 'lido', 'etherfi', 'wallet']
        
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            all_venues, 'live', self.config
        )
        
        # Verify all interfaces were created
        assert len(interfaces) == len(all_venues)
        for venue in all_venues:
            assert venue in interfaces
            assert interfaces[venue] is not None
        
        # Verify interface types
        cex_venues = ['binance', 'bybit', 'okx']
        for venue in cex_venues:
            assert isinstance(interfaces[venue], CEXPositionInterface)
        
        onchain_venues = ['aave', 'morpho', 'lido', 'etherfi']
        for venue in onchain_venues:
            assert isinstance(interfaces[venue], OnChainPositionInterface)
        
        assert isinstance(interfaces['wallet'], TransferPositionInterface)
        
        # Verify all are in live mode
        for interface in interfaces.values():
            assert interface.execution_mode == 'live'
            assert interface.config == self.config
    
    def test_factory_position_interface_creation_backtest_mode(self):
        """Test factory position interface creation in backtest mode."""
        venues = ['binance', 'aave', 'wallet']
        
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'backtest', self.config
        )
        
        # Verify all interfaces were created
        assert len(interfaces) == 3
        for venue in venues:
            assert venue in interfaces
            assert interfaces[venue] is not None
        
        # Verify all are in backtest mode
        for interface in interfaces.values():
            assert interface.execution_mode == 'backtest'
            assert interface.config == self.config
    
    def test_factory_position_interface_creation_with_unsupported_venues(self):
        """Test factory position interface creation with unsupported venues."""
        venues = ['binance', 'unsupported_venue', 'aave', 'another_unsupported']
        
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'live', self.config
        )
        
        # Verify all venues are in the result
        assert len(interfaces) == 4
        for venue in venues:
            assert venue in interfaces
        
        # Verify supported venues work
        assert isinstance(interfaces['binance'], CEXPositionInterface)
        assert isinstance(interfaces['aave'], OnChainPositionInterface)
        
        # Verify unsupported venues are None
        assert interfaces['unsupported_venue'] is None
        assert interfaces['another_unsupported'] is None
    
    def test_factory_position_interface_creation_empty_venues(self):
        """Test factory position interface creation with empty venue list."""
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            [], 'live', self.config
        )
        
        # Verify empty result
        assert len(interfaces) == 0
        assert interfaces == {}
    
    def test_factory_position_interface_creation_mixed_modes(self):
        """Test factory position interface creation with mixed execution modes."""
        venues = ['binance', 'aave', 'wallet']
        
        # Test backtest mode
        backtest_interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'backtest', self.config
        )
        
        # Test live mode
        live_interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'live', self.config
        )
        
        # Verify both modes work
        assert len(backtest_interfaces) == 3
        assert len(live_interfaces) == 3
        
        # Verify mode consistency
        for interface in backtest_interfaces.values():
            assert interface.execution_mode == 'backtest'
        
        for interface in live_interfaces.values():
            assert interface.execution_mode == 'live'
    
    def test_factory_position_interface_creation_config_preservation(self):
        """Test that config is properly preserved across all interfaces."""
        custom_config = {
            'test': 'value',
            'nested': {'key': 'value'},
            'component_config': {
                'position_monitor': {
                    'initial_balances': {
                        'cex_accounts': ['binance'],
                        'perp_positions': ['aave']
                    }
                }
            }
        }
        
        venues = ['binance', 'aave', 'wallet']
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'live', custom_config
        )
        
        # Verify config is preserved in all interfaces
        for interface in interfaces.values():
            assert interface.config == custom_config
    
    def test_factory_position_interface_creation_individual_vs_batch_consistency(self):
        """Test consistency between individual and batch interface creation."""
        venues = ['binance', 'aave', 'wallet']
        
        # Create interfaces individually
        individual_interfaces = {}
        for venue in venues:
            individual_interfaces[venue] = VenueInterfaceFactory.create_venue_position_interface(
                venue, 'live', self.config
            )
        
        # Create interfaces in batch
        batch_interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'live', self.config
        )
        
        # Verify consistency
        assert len(individual_interfaces) == len(batch_interfaces)
        for venue in venues:
            individual_interface = individual_interfaces[venue]
            batch_interface = batch_interfaces[venue]
            
            # Verify same type
            assert type(individual_interface) == type(batch_interface)
            
            # Verify same properties
            assert individual_interface.venue == batch_interface.venue
            assert individual_interface.execution_mode == batch_interface.execution_mode
            assert individual_interface.config == batch_interface.config
    
    def test_factory_position_interface_creation_venue_type_classification(self):
        """Test that venues are correctly classified by type."""
        # Test CEX venue classification
        cex_venues = ['binance', 'bybit', 'okx']
        for venue in cex_venues:
            interface = VenueInterfaceFactory.create_venue_position_interface(
                venue, 'live', self.config
            )
            assert isinstance(interface, CEXPositionInterface)
            assert interface.venue == venue
        
        # Test OnChain venue classification
        onchain_venues = ['aave', 'morpho', 'lido', 'etherfi']
        for venue in onchain_venues:
            interface = VenueInterfaceFactory.create_venue_position_interface(
                venue, 'live', self.config
            )
            assert isinstance(interface, OnChainPositionInterface)
            assert interface.venue == venue
        
        # Test Transfer venue classification
        transfer_venue = 'wallet'
        interface = VenueInterfaceFactory.create_venue_position_interface(
            transfer_venue, 'live', self.config
        )
        assert isinstance(interface, TransferPositionInterface)
        assert interface.venue == transfer_venue
    
    def test_factory_position_interface_creation_error_handling(self):
        """Test error handling in factory position interface creation."""
        # Test unsupported venue in individual creation
        with pytest.raises(ValueError, match="Unsupported venue for position monitoring"):
            VenueInterfaceFactory.create_venue_position_interface(
                'unsupported_venue', 'live', self.config
            )
        
        # Test unsupported venue in batch creation (should not raise, but return None)
        venues = ['binance', 'unsupported_venue', 'aave']
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'live', self.config
        )
        
        # Verify supported venues work
        assert isinstance(interfaces['binance'], CEXPositionInterface)
        assert isinstance(interfaces['aave'], OnChainPositionInterface)
        
        # Verify unsupported venue is None
        assert interfaces['unsupported_venue'] is None
    
    def test_factory_position_interface_creation_environment_consistency(self):
        """Test that factory works consistently across different environments."""
        # Test with different environment variables
        with patch.dict(os.environ, {'BASIS_ENVIRONMENT': 'dev'}):
            interface = VenueInterfaceFactory.create_venue_position_interface(
                'binance', 'live', self.config
            )
            assert isinstance(interface, CEXPositionInterface)
            assert interface.venue == 'binance'
        
        with patch.dict(os.environ, {'BASIS_ENVIRONMENT': 'staging'}):
            interface = VenueInterfaceFactory.create_venue_position_interface(
                'binance', 'live', self.config
            )
            assert isinstance(interface, CEXPositionInterface)
            assert interface.venue == 'binance'
        
        with patch.dict(os.environ, {'BASIS_ENVIRONMENT': 'production'}):
            interface = VenueInterfaceFactory.create_venue_position_interface(
                'binance', 'live', self.config
            )
            assert isinstance(interface, CEXPositionInterface)
            assert interface.venue == 'binance'
    
    def test_factory_position_interface_creation_credential_handling(self):
        """Test that factory properly handles credentials for different venues."""
        # Test CEX venue credentials
        cex_interface = VenueInterfaceFactory.create_venue_position_interface(
            'binance', 'live', self.config
        )
        credentials = cex_interface._get_credentials('binance')
        assert 'api_key' in credentials
        assert 'secret' in credentials
        
        # Test OnChain venue credentials
        onchain_interface = VenueInterfaceFactory.create_venue_position_interface(
            'aave', 'live', self.config
        )
        credentials = onchain_interface._get_credentials('aave')
        assert 'rpc_url' in credentials
        assert 'private_key' in credentials
        
        # Test Transfer venue credentials
        transfer_interface = VenueInterfaceFactory.create_venue_position_interface(
            'wallet', 'live', self.config
        )
        credentials = transfer_interface._get_credentials('wallet')
        assert 'wallet_address' in credentials
        assert 'private_key' in credentials
        assert 'rpc_url' in credentials
    
    def test_factory_position_interface_creation_interface_status(self):
        """Test that all created interfaces return consistent status."""
        venues = ['binance', 'aave', 'wallet']
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            venues, 'live', self.config
        )
        
        # Verify all interfaces return consistent status
        for interface in interfaces.values():
            status = interface.get_interface_status()
            
            # Verify status structure
            assert 'venue' in status
            assert 'execution_mode' in status
            assert 'interface_type' in status
            assert 'status' in status
            
            # Verify values
            assert status['interface_type'] == 'position'
            assert status['status'] == 'healthy'
            assert status['execution_mode'] == 'live'
    
    def test_factory_position_interface_creation_performance(self):
        """Test that factory can handle multiple venue creation efficiently."""
        # Test with many venues
        many_venues = ['binance', 'bybit', 'okx', 'aave', 'morpho', 'lido', 'etherfi', 'wallet']
        
        # Create interfaces
        interfaces = VenueInterfaceFactory.get_venue_position_interfaces(
            many_venues, 'live', self.config
        )
        
        # Verify all were created
        assert len(interfaces) == len(many_venues)
        for venue in many_venues:
            assert venue in interfaces
            assert interfaces[venue] is not None
        
        # Verify all are properly initialized
        for interface in interfaces.values():
            assert interface.execution_mode == 'live'
            assert interface.config == self.config
            assert interface.get_interface_status()['status'] == 'healthy'
