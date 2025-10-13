"""
Unit tests for USDT Market Neutral No Leverage Data Provider.

Tests the USDT market neutral no leverage data provider component in isolation with mocked dependencies.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from basis_strategy_v1.infrastructure.data.usdt_market_neutral_no_leverage_data_provider import USDTMarketNeutralNoLeverageDataProvider


class TestUSDTMarketNeutralNoLeverageDataProvider:
    """Test USDT Market Neutral No Leverage Data Provider component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for USDT market neutral no leverage data provider."""
        return {
            'mode': 'usdt_market_neutral_no_leverage',
            'data_dir': 'test_data',
            'asset': 'ETH',
            'share_class': 'USDT',
            'data_requirements': ['eth_prices', 'weeth_prices', 'funding_rates']
        }
    
    @pytest.fixture
    def mock_data_provider(self, mock_config):
        """Create USDT market neutral no leverage data provider with mocked dependencies."""
        provider = USDTMarketNeutralNoLeverageDataProvider('backtest', mock_config)
        return provider
    
    def test_initialization(self, mock_config):
        """Test USDT market neutral no leverage data provider initialization."""
        provider = USDTMarketNeutralNoLeverageDataProvider('backtest', mock_config)
        
        assert provider.execution_mode == 'backtest'
        assert 'eth_prices' in provider.available_data_types
        assert 'weeth_prices' in provider.available_data_types
        assert 'eth_futures' in provider.available_data_types
        assert 'funding_rates' in provider.available_data_types
        assert 'staking_rewards' in provider.available_data_types
        assert 'gas_costs' in provider.available_data_types
        assert 'execution_costs' in provider.available_data_types
        # Should NOT include AAVE lending rates (no leverage)
        assert 'aave_lending_rates' not in provider.available_data_types
        assert not provider._data_loaded
    
    def test_validate_data_requirements_success(self, mock_data_provider):
        """Test successful data requirements validation."""
        requirements = ['eth_prices', 'weeth_prices', 'funding_rates', 'staking_rewards']
        
        # Should not raise any exception
        mock_data_provider.validate_data_requirements(requirements)
    
    def test_validate_data_requirements_failure(self, mock_data_provider):
        """Test data requirements validation with missing requirements."""
        requirements = ['eth_prices', 'aave_lending_rates']  # aave_lending_rates not available
        
        with pytest.raises(ValueError, match="cannot satisfy requirements"):
            mock_data_provider.validate_data_requirements(requirements)
    
    def test_get_data_structure(self, mock_data_provider):
        """Test get_data returns correct standardized structure."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.object(mock_data_provider, '_load_data'):
            data = mock_data_provider.get_data(timestamp)
            
            # Check structure
            assert 'market_data' in data
            assert 'protocol_data' in data
            assert 'staking_data' in data
            assert 'execution_data' in data
            
            # Check market data structure
            assert 'prices' in data['market_data']
            assert 'rates' in data['market_data']
            assert 'ETH' in data['market_data']['prices']
            assert 'weETH' in data['market_data']['prices']
            assert 'USDT' in data['market_data']['prices']
            
            # Check protocol data structure (should be minimal for no leverage)
            assert 'aave_indexes' in data['protocol_data']
            assert 'oracle_prices' in data['protocol_data']
            assert 'perp_prices' in data['protocol_data']
            # Should be empty for no leverage mode
            assert data['protocol_data']['aave_indexes'] == {}
            assert data['protocol_data']['oracle_prices'] == {}
            
            # Check staking data structure
            assert 'rewards' in data['staking_data']
            
            # Check execution data structure
            assert 'wallet_balances' in data['execution_data']
            assert 'smart_contract_balances' in data['execution_data']
            assert 'cex_spot_balances' in data['execution_data']
            assert 'cex_derivatives_balances' in data['execution_data']
            assert 'gas_costs' in data['execution_data']
            assert 'execution_costs' in data['execution_data']
            # Should be empty for no leverage mode
            assert data['execution_data']['smart_contract_balances'] == {}
            assert data['execution_data']['cex_spot_balances'] == {}
    
    def test_get_timestamps(self, mock_data_provider):
        """Test timestamp generation for backtest period."""
        start_date = '2024-01-01'
        end_date = '2024-01-02'
        
        timestamps = mock_data_provider.get_timestamps(start_date, end_date)
        
        assert isinstance(timestamps, list)
        assert len(timestamps) > 0
        assert all(isinstance(ts, pd.Timestamp) for ts in timestamps)
        # Should be hourly intervals
        assert timestamps[1] - timestamps[0] == pd.Timedelta(hours=1)
    
    def test_load_data(self, mock_data_provider):
        """Test data loading."""
        mock_data_provider.load_data()
        
        assert mock_data_provider._data_loaded
        assert 'eth_prices' in mock_data_provider.data
        assert 'weeth_prices' in mock_data_provider.data
        assert 'funding_rates' in mock_data_provider.data
        assert 'perp_prices' in mock_data_provider.data
        assert 'staking_rewards' in mock_data_provider.data
        assert 'gas_costs' in mock_data_provider.data
        assert 'execution_costs' in mock_data_provider.data
        # Should NOT include AAVE data (no leverage)
        assert 'aave_rates' not in mock_data_provider.data
        assert 'aave_indexes' not in mock_data_provider.data
    
    def test_get_eth_price_with_data(self, mock_data_provider):
        """Test ETH price retrieval with loaded data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # Mock loaded data
        mock_data_provider.data = {
            'eth_prices': pd.DataFrame({
                'timestamp': [timestamp],
                'price': [3000.0]
            })
        }
        
        price = mock_data_provider._get_eth_price(timestamp)
        assert price == 3000.0
    
    def test_get_eth_price_fallback(self, mock_data_provider):
        """Test ETH price fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        price = mock_data_provider._get_eth_price(timestamp)
        assert price == 3000.0  # Default fallback
    
    def test_get_weeth_price_with_data(self, mock_data_provider):
        """Test weETH price retrieval with loaded data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # Mock loaded data
        mock_data_provider.data = {
            'weeth_prices': pd.DataFrame({
                'timestamp': [timestamp],
                'price': [3005.0]
            })
        }
        
        price = mock_data_provider._get_weeth_price(timestamp)
        assert price == 3005.0
    
    def test_get_weeth_price_fallback(self, mock_data_provider):
        """Test weETH price fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        price = mock_data_provider._get_weeth_price(timestamp)
        assert price == 3000.0  # Default fallback
    
    def test_get_funding_rates_with_data(self, mock_data_provider):
        """Test funding rates retrieval with loaded data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # Mock loaded data
        mock_data_provider.data = {
            'funding_rates': pd.DataFrame({
                'timestamp': [timestamp],
                'binance_eth': [0.0001],
                'bybit_eth': [0.0002],
                'okx_eth': [0.0003]
            })
        }
        
        funding_rates = mock_data_provider._get_funding_rates(timestamp)
        
        assert 'ETH_binance' in funding_rates
        assert 'ETH_bybit' in funding_rates
        assert 'ETH_okx' in funding_rates
        assert funding_rates['ETH_binance'] == 0.0001
        assert funding_rates['ETH_bybit'] == 0.0002
        assert funding_rates['ETH_okx'] == 0.0003
    
    def test_get_funding_rates_fallback(self, mock_data_provider):
        """Test funding rates fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        funding_rates = mock_data_provider._get_funding_rates(timestamp)
        
        assert 'ETH_binance' in funding_rates
        assert funding_rates['ETH_binance'] == 0.0001  # Fallback value
    
    def test_get_perp_prices_with_data(self, mock_data_provider):
        """Test perpetual prices retrieval with loaded data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # Mock loaded data
        mock_data_provider.data = {
            'perp_prices': pd.DataFrame({
                'timestamp': [timestamp],
                'binance_eth_perp': [3001.0],
                'bybit_eth_perp': [3002.0],
                'okx_eth_perp': [3003.0]
            })
        }
        
        perp_prices = mock_data_provider._get_perp_prices(timestamp)
        
        assert 'ETH_binance' in perp_prices
        assert 'ETH_bybit' in perp_prices
        assert 'ETH_okx' in perp_prices
        assert perp_prices['ETH_binance'] == 3001.0
        assert perp_prices['ETH_bybit'] == 3002.0
        assert perp_prices['ETH_okx'] == 3003.0
    
    def test_get_perp_prices_fallback(self, mock_data_provider):
        """Test perpetual prices fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        perp_prices = mock_data_provider._get_perp_prices(timestamp)
        
        assert 'ETH_binance' in perp_prices
        assert perp_prices['ETH_binance'] == 3000.0  # Fallback value
    
    def test_get_staking_rewards_with_data(self, mock_data_provider):
        """Test staking rewards retrieval with loaded data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # Mock loaded data
        mock_data_provider.data = {
            'staking_rewards': pd.DataFrame({
                'timestamp': [timestamp],
                'eth_rewards': [0.002],
                'eigen_rewards': [0.0002]
            })
        }
        
        rewards = mock_data_provider._get_staking_rewards(timestamp)
        
        assert 'ETH' in rewards
        assert 'EIGEN' in rewards
        assert rewards['ETH'] == 0.002
        assert rewards['EIGEN'] == 0.0002
    
    def test_get_staking_rewards_fallback(self, mock_data_provider):
        """Test staking rewards fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        rewards = mock_data_provider._get_staking_rewards(timestamp)
        
        assert 'ETH' in rewards
        assert rewards['ETH'] == 0.001  # Fallback value
    
    def test_get_wallet_balances(self, mock_data_provider):
        """Test wallet balances retrieval."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        balances = mock_data_provider._get_wallet_balances(timestamp)
        
        assert 'ETH' in balances
        assert 'weETH' in balances
        assert 'USDT' in balances
        assert 'EIGEN' in balances
        assert 'KING' in balances
        assert balances['USDT'] == 1000.0  # Default USDT balance
        # Should NOT include AAVE tokens (no leverage)
        assert 'aWeETH' not in balances
        assert 'variableDebtWETH' not in balances
    
    def test_get_cex_derivatives_balances(self, mock_data_provider):
        """Test CEX derivatives balances retrieval."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        balances = mock_data_provider._get_cex_derivatives_balances(timestamp)
        
        assert 'binance' in balances
        assert 'bybit' in balances
        assert 'okx' in balances
        assert 'ETH_PERP' in balances['binance']
        assert 'ETH_PERP' in balances['bybit']
        assert 'ETH_PERP' in balances['okx']
    
    def test_get_gas_costs_with_data(self, mock_data_provider):
        """Test gas costs retrieval with loaded data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # Mock loaded data
        mock_data_provider.data = {
            'gas_costs': pd.DataFrame({
                'timestamp': [timestamp],
                'cost': [0.002]
            })
        }
        
        gas_costs = mock_data_provider._get_gas_costs(timestamp)
        
        assert 'transfer' in gas_costs
        assert 'stake' in gas_costs
        assert 'trade' in gas_costs
        # Should NOT include AAVE operations (no leverage)
        assert 'supply' not in gas_costs
        assert 'borrow' not in gas_costs
        assert gas_costs['transfer'] == 0.002
    
    def test_get_gas_costs_fallback(self, mock_data_provider):
        """Test gas costs fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        gas_costs = mock_data_provider._get_gas_costs(timestamp)
        
        assert 'transfer' in gas_costs
        assert gas_costs['transfer'] == 0.001  # Fallback value
    
    def test_get_execution_costs_with_data(self, mock_data_provider):
        """Test execution costs retrieval with loaded data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # Mock loaded data
        mock_data_provider.data = {
            'execution_costs': pd.DataFrame({
                'timestamp': [timestamp],
                'cost': [0.0002]
            })
        }
        
        exec_costs = mock_data_provider._get_execution_costs(timestamp)
        
        assert 'binance_perp' in exec_costs
        assert 'bybit_perp' in exec_costs
        assert 'okx_perp' in exec_costs
        assert 'etherfi_stake' in exec_costs
        # Should NOT include AAVE operations (no leverage)
        assert 'aave_supply' not in exec_costs
        assert 'aave_borrow' not in exec_costs
        assert exec_costs['binance_perp'] == 0.0002
    
    def test_get_execution_costs_fallback(self, mock_data_provider):
        """Test execution costs fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        exec_costs = mock_data_provider._get_execution_costs(timestamp)
        
        assert 'binance_perp' in exec_costs
        assert exec_costs['binance_perp'] == 0.0001  # Fallback value
    
    def test_error_handling_invalid_timestamp(self, mock_data_provider):
        """Test error handling with invalid timestamp."""
        # Test with None timestamp
        with pytest.raises((TypeError, AttributeError)):
            mock_data_provider.get_data(None)
    
    def test_edge_case_empty_data_requirements(self, mock_data_provider):
        """Test edge case with empty data requirements."""
        # Should not raise exception for empty requirements
        mock_data_provider.validate_data_requirements([])
    
    def test_edge_case_large_timestamp_range(self, mock_data_provider):
        """Test edge case with large timestamp range."""
        start_date = '2020-01-01'
        end_date = '2024-12-31'
        
        timestamps = mock_data_provider.get_timestamps(start_date, end_date)
        
        assert len(timestamps) > 40000  # Should be a large number of hourly intervals
        assert timestamps[0] == pd.Timestamp(start_date)
        assert timestamps[-1] <= pd.Timestamp(end_date)
    
    def test_data_loading_creates_correct_dataframes(self, mock_data_provider):
        """Test that data loading creates properly structured DataFrames."""
        mock_data_provider.load_data()
        
        # Check that all data is properly structured
        for data_type in ['eth_prices', 'weeth_prices', 'funding_rates', 
                         'perp_prices', 'staking_rewards', 'gas_costs', 'execution_costs']:
            assert data_type in mock_data_provider.data
            df = mock_data_provider.data[data_type]
            assert isinstance(df, pd.DataFrame)
            assert 'timestamp' in df.columns
            assert len(df) == 100  # Should have 100 rows of test data
        
        # Should NOT include AAVE data
        assert 'aave_rates' not in mock_data_provider.data
        assert 'aave_indexes' not in mock_data_provider.data
    
    def test_no_leverage_specific_behavior(self, mock_data_provider):
        """Test specific behavior differences for no leverage mode."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.object(mock_data_provider, '_load_data'):
            data = mock_data_provider.get_data(timestamp)
            
            # Protocol data should be minimal
            assert data['protocol_data']['aave_indexes'] == {}
            assert data['protocol_data']['oracle_prices'] == {}
            
            # Execution data should not include AAVE operations
            assert data['execution_data']['smart_contract_balances'] == {}
            assert data['execution_data']['cex_spot_balances'] == {}
            
            # Wallet balances should not include AAVE tokens
            wallet_balances = data['execution_data']['wallet_balances']
            assert 'aWeETH' not in wallet_balances
            assert 'variableDebtWETH' not in wallet_balances
    
    def test_available_data_types_no_leverage(self, mock_data_provider):
        """Test that available data types exclude leverage-related data."""
        available_types = mock_data_provider.available_data_types
        
        # Should include basic data
        assert 'eth_prices' in available_types
        assert 'weeth_prices' in available_types
        assert 'funding_rates' in available_types
        assert 'staking_rewards' in available_types
        
        # Should NOT include leverage-related data
        assert 'aave_lending_rates' not in available_types
        assert 'aave_risk_params' not in available_types
    
    def test_gas_costs_no_leverage_operations(self, mock_data_provider):
        """Test that gas costs only include no-leverage operations."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        gas_costs = mock_data_provider._get_gas_costs(timestamp)
        
        # Should include basic operations
        assert 'transfer' in gas_costs
        assert 'stake' in gas_costs
        assert 'trade' in gas_costs
        
        # Should NOT include leverage operations
        assert 'supply' not in gas_costs
        assert 'borrow' not in gas_costs
    
    def test_execution_costs_no_leverage_operations(self, mock_data_provider):
        """Test that execution costs only include no-leverage operations."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        exec_costs = mock_data_provider._get_execution_costs(timestamp)
        
        # Should include basic operations
        assert 'binance_perp' in exec_costs
        assert 'bybit_perp' in exec_costs
        assert 'okx_perp' in exec_costs
        assert 'etherfi_stake' in exec_costs
        
        # Should NOT include leverage operations
        assert 'aave_supply' not in exec_costs
        assert 'aave_borrow' not in exec_costs
