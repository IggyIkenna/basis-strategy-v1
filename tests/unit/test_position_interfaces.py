"""
Unit tests for position interfaces.

Tests position interface creation, initialization, and basic functionality.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock
import os

from backend.src.basis_strategy_v1.core.interfaces.base_position_interface import BasePositionInterface
from backend.src.basis_strategy_v1.core.interfaces.cex_position_interface import CEXPositionInterface
from backend.src.basis_strategy_v1.core.interfaces.onchain_position_interface import OnChainPositionInterface
from backend.src.basis_strategy_v1.core.interfaces.transfer_position_interface import TransferPositionInterface


class TestBasePositionInterface:
    """Test base position interface functionality."""
    
    def test_base_interface_initialization(self):
        """Test base position interface initialization."""
        config = {'test': 'config'}
        
        # Create a concrete implementation for testing
        class TestPositionInterface(BasePositionInterface):
            async def get_positions(self, timestamp):
                return {}
            
            async def get_balance(self, asset, timestamp):
                return 0.0
            
            async def get_position_history(self, start_time, end_time):
                return []
        
        interface = TestPositionInterface('test_venue', 'backtest', config)
        
        assert interface.venue == 'test_venue'
        assert interface.execution_mode == 'backtest'
        assert interface.config == config
    
    def test_validate_timestamp(self):
        """Test timestamp validation."""
        class TestPositionInterface(BasePositionInterface):
            async def get_positions(self, timestamp):
                return {}
            
            async def get_balance(self, asset, timestamp):
                return 0.0
            
            async def get_position_history(self, start_time, end_time):
                return []
        
        interface = TestPositionInterface('test_venue', 'backtest', {})
        
        # Valid timestamp
        valid_timestamp = pd.Timestamp('2024-01-01')
        interface._validate_timestamp(valid_timestamp)  # Should not raise
        
        # Invalid timestamp types
        with pytest.raises(ValueError):
            interface._validate_timestamp("2024-01-01")
        
        with pytest.raises(ValueError):
            interface._validate_timestamp(pd.NaT)
    
    def test_validate_asset(self):
        """Test asset validation."""
        class TestPositionInterface(BasePositionInterface):
            async def get_positions(self, timestamp):
                return {}
            
            async def get_balance(self, asset, timestamp):
                return 0.0
            
            async def get_position_history(self, start_time, end_time):
                return []
        
        interface = TestPositionInterface('test_venue', 'backtest', {})
        
        # Valid asset
        interface._validate_asset('USDT')  # Should not raise
        
        # Invalid asset types
        with pytest.raises(ValueError):
            interface._validate_asset(123)
        
        with pytest.raises(ValueError):
            interface._validate_asset('')
    
    def test_get_interface_status(self):
        """Test interface status retrieval."""
        class TestPositionInterface(BasePositionInterface):
            async def get_positions(self, timestamp):
                return {}
            
            async def get_balance(self, asset, timestamp):
                return 0.0
            
            async def get_position_history(self, start_time, end_time):
                return []
        
        interface = TestPositionInterface('test_venue', 'backtest', {})
        status = interface.get_interface_status()
        
        assert status['venue'] == 'test_venue'
        assert status['execution_mode'] == 'backtest'
        assert status['interface_type'] == 'position'
        assert status['status'] == 'healthy'


class TestCEXPositionInterface:
    """Test CEX position interface functionality."""
    
    @patch.dict(os.environ, {'BASIS_ENVIRONMENT': 'dev'})
    def test_cex_interface_initialization(self):
        """Test CEX position interface initialization."""
        config = {'test': 'config'}
        
        interface = CEXPositionInterface('binance', 'backtest', config)
        
        assert interface.venue == 'binance'
        assert interface.execution_mode == 'backtest'
        assert interface.config == config
        assert interface.client is None  # No client in backtest mode
    
    @patch.dict(os.environ, {'BASIS_ENVIRONMENT': 'dev'})
    def test_get_credentials(self):
        """Test credential retrieval for CEX venues."""
        config = {'test': 'config'}
        
        # Test Binance credentials
        interface = CEXPositionInterface('binance', 'backtest', config)
        credentials = interface._get_credentials('binance')
        assert 'api_key' in credentials
        assert 'secret' in credentials
        
        # Test Bybit credentials
        interface = CEXPositionInterface('bybit', 'backtest', config)
        credentials = interface._get_credentials('bybit')
        assert 'api_key' in credentials
        assert 'secret' in credentials
        
        # Test OKX credentials
        interface = CEXPositionInterface('okx', 'backtest', config)
        credentials = interface._get_credentials('okx')
        assert 'api_key' in credentials
        assert 'secret' in credentials
        assert 'passphrase' in credentials
        
        # Test unsupported venue
        with pytest.raises(ValueError):
            interface._get_credentials('unsupported')
    
    @pytest.mark.asyncio
    async def test_get_simulated_positions(self):
        """Test simulated position retrieval."""
        config = {'test': 'config'}
        interface = CEXPositionInterface('binance', 'backtest', config)
        
        timestamp = pd.Timestamp('2024-01-01')
        positions = await interface.get_positions(timestamp)
        
        assert positions['venue'] == 'binance'
        assert positions['timestamp'] == timestamp
        assert positions['execution_mode'] == 'backtest'
        assert 'spot_balances' in positions
        assert 'perp_positions' in positions
    
    @pytest.mark.asyncio
    async def test_get_simulated_balance(self):
        """Test simulated balance retrieval."""
        config = {'test': 'config'}
        interface = CEXPositionInterface('binance', 'backtest', config)
        
        timestamp = pd.Timestamp('2024-01-01')
        balance = await interface.get_balance('USDT', timestamp)
        
        assert isinstance(balance, float)
        assert balance >= 0
    
    @pytest.mark.asyncio
    async def test_get_simulated_position_history(self):
        """Test simulated position history retrieval."""
        config = {'test': 'config'}
        interface = CEXPositionInterface('binance', 'backtest', config)
        
        start_time = pd.Timestamp('2024-01-01')
        end_time = pd.Timestamp('2024-01-02')
        history = await interface.get_position_history(start_time, end_time)
        
        assert isinstance(history, list)
        if history:
            assert history[0]['venue'] == 'binance'


class TestOnChainPositionInterface:
    """Test OnChain position interface functionality."""
    
    @patch.dict(os.environ, {'BASIS_ENVIRONMENT': 'dev'})
    def test_onchain_interface_initialization(self):
        """Test OnChain position interface initialization."""
        config = {'test': 'config'}
        
        interface = OnChainPositionInterface('aave', 'backtest', config)
        
        assert interface.venue == 'aave'
        assert interface.execution_mode == 'backtest'
        assert interface.config == config
        assert interface.client is None  # No client in backtest mode
    
    @patch.dict(os.environ, {'BASIS_ENVIRONMENT': 'dev'})
    def test_get_credentials(self):
        """Test credential retrieval for OnChain venues."""
        config = {'test': 'config'}
        
        # Test AAVE credentials
        interface = OnChainPositionInterface('aave', 'backtest', config)
        credentials = interface._get_credentials('aave')
        assert 'rpc_url' in credentials
        assert 'private_key' in credentials
        
        # Test Lido credentials
        interface = OnChainPositionInterface('lido', 'backtest', config)
        credentials = interface._get_credentials('lido')
        assert 'rpc_url' in credentials
        assert 'private_key' in credentials
        
        # Test unsupported venue
        with pytest.raises(ValueError):
            interface._get_credentials('unsupported')
    
    @pytest.mark.asyncio
    async def test_get_simulated_positions_aave(self):
        """Test simulated position retrieval for AAVE."""
        config = {'test': 'config'}
        interface = OnChainPositionInterface('aave', 'backtest', config)
        
        timestamp = pd.Timestamp('2024-01-01')
        positions = await interface.get_positions(timestamp)
        
        assert positions['venue'] == 'aave'
        assert positions['timestamp'] == timestamp
        assert positions['execution_mode'] == 'backtest'
        assert 'supply_positions' in positions
        assert 'borrow_positions' in positions
    
    @pytest.mark.asyncio
    async def test_get_simulated_positions_lido(self):
        """Test simulated position retrieval for Lido."""
        config = {'test': 'config'}
        interface = OnChainPositionInterface('lido', 'backtest', config)
        
        timestamp = pd.Timestamp('2024-01-01')
        positions = await interface.get_positions(timestamp)
        
        assert positions['venue'] == 'lido'
        assert positions['timestamp'] == timestamp
        assert positions['execution_mode'] == 'backtest'
        assert 'staked_eth' in positions
        assert 'steth_balance' in positions
    
    @pytest.mark.asyncio
    async def test_get_simulated_positions_etherfi(self):
        """Test simulated position retrieval for EtherFi."""
        config = {'test': 'config'}
        interface = OnChainPositionInterface('etherfi', 'backtest', config)
        
        timestamp = pd.Timestamp('2024-01-01')
        positions = await interface.get_positions(timestamp)
        
        assert positions['venue'] == 'etherfi'
        assert positions['timestamp'] == timestamp
        assert positions['execution_mode'] == 'backtest'
        assert 'staked_eth' in positions
        assert 'weeth_balance' in positions
        assert 'eigen_balance' in positions
        assert 'king_balance' in positions


class TestTransferPositionInterface:
    """Test Transfer position interface functionality."""
    
    @patch.dict(os.environ, {'BASIS_ENVIRONMENT': 'dev'})
    def test_transfer_interface_initialization(self):
        """Test Transfer position interface initialization."""
        config = {'test': 'config'}
        
        interface = TransferPositionInterface('wallet', 'backtest', config)
        
        assert interface.venue == 'wallet'
        assert interface.execution_mode == 'backtest'
        assert interface.config == config
        assert interface.client is None  # No client in backtest mode
    
    @patch.dict(os.environ, {'BASIS_ENVIRONMENT': 'dev'})
    def test_get_credentials(self):
        """Test credential retrieval for wallet venue."""
        config = {'test': 'config'}
        interface = TransferPositionInterface('wallet', 'backtest', config)
        
        credentials = interface._get_credentials('wallet')
        assert 'wallet_address' in credentials
        assert 'private_key' in credentials
        assert 'rpc_url' in credentials
        
        # Test unsupported venue
        with pytest.raises(ValueError):
            interface._get_credentials('unsupported')
    
    @pytest.mark.asyncio
    async def test_get_simulated_positions(self):
        """Test simulated position retrieval."""
        config = {'test': 'config'}
        interface = TransferPositionInterface('wallet', 'backtest', config)
        
        timestamp = pd.Timestamp('2024-01-01')
        positions = await interface.get_positions(timestamp)
        
        assert positions['venue'] == 'wallet'
        assert positions['timestamp'] == timestamp
        assert positions['execution_mode'] == 'backtest'
        assert 'wallet_balances' in positions
    
    @pytest.mark.asyncio
    async def test_get_simulated_balance(self):
        """Test simulated balance retrieval."""
        config = {'test': 'config'}
        interface = TransferPositionInterface('wallet', 'backtest', config)
        
        timestamp = pd.Timestamp('2024-01-01')
        balance = await interface.get_balance('USDT', timestamp)
        
        assert isinstance(balance, float)
        assert balance >= 0
    
    @pytest.mark.asyncio
    async def test_get_simulated_position_history(self):
        """Test simulated position history retrieval."""
        config = {'test': 'config'}
        interface = TransferPositionInterface('wallet', 'backtest', config)
        
        start_time = pd.Timestamp('2024-01-01')
        end_time = pd.Timestamp('2024-01-02')
        history = await interface.get_position_history(start_time, end_time)
        
        assert isinstance(history, list)
        if history:
            assert history[0]['venue'] == 'wallet'


class TestPositionInterfaceIntegration:
    """Test position interface integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_multiple_venues_simulation(self):
        """Test multiple venue position simulation."""
        config = {'test': 'config'}
        
        # Create interfaces for different venues
        cex_interface = CEXPositionInterface('binance', 'backtest', config)
        onchain_interface = OnChainPositionInterface('aave', 'backtest', config)
        transfer_interface = TransferPositionInterface('wallet', 'backtest', config)
        
        timestamp = pd.Timestamp('2024-01-01')
        
        # Get positions from all venues
        cex_positions = await cex_interface.get_positions(timestamp)
        onchain_positions = await onchain_interface.get_positions(timestamp)
        transfer_positions = await transfer_interface.get_positions(timestamp)
        
        # Verify all positions have correct structure
        assert cex_positions['venue'] == 'binance'
        assert onchain_positions['venue'] == 'aave'
        assert transfer_positions['venue'] == 'wallet'
        
        # Verify all are in backtest mode
        assert cex_positions['execution_mode'] == 'backtest'
        assert onchain_positions['execution_mode'] == 'backtest'
        assert transfer_positions['execution_mode'] == 'backtest'
    
    def test_interface_status_consistency(self):
        """Test that all interfaces return consistent status format."""
        config = {'test': 'config'}
        
        interfaces = [
            CEXPositionInterface('binance', 'backtest', config),
            OnChainPositionInterface('aave', 'backtest', config),
            TransferPositionInterface('wallet', 'backtest', config)
        ]
        
        for interface in interfaces:
            status = interface.get_interface_status()
            
            # Verify status structure
            assert 'venue' in status
            assert 'execution_mode' in status
            assert 'interface_type' in status
            assert 'status' in status
            
            # Verify values
            assert status['interface_type'] == 'position'
            assert status['status'] == 'healthy'
            assert status['execution_mode'] == 'backtest'
