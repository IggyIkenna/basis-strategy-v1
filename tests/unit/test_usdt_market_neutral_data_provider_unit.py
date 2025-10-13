"""
Unit tests for USDT Market Neutral Data Provider.

Tests the USDT market neutral data provider component in isolation with mocked dependencies.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from basis_strategy_v1.infrastructure.data.usdt_market_neutral_data_provider import USDTMarketNeutralDataProvider


class TestUSDTMarketNeutralDataProvider:
    """Test USDT Market Neutral Data Provider component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for USDT market neutral data provider."""
        return {
            'mode': 'usdt_market_neutral',
            'data_dir': 'test_data',
            'asset': 'ETH',
            'share_class': 'USDT',
            'data_requirements': ['eth_prices', 'weeth_prices', 'funding_rates']
        }
    
    @pytest.fixture
    def mock_data_provider(self, mock_config):
        """Create USDT market neutral data provider with mocked dependencies."""
        provider = USDTMarketNeutralDataProvider('backtest', mock_config)
        return provider
    
    def test_initialization(self, mock_config):
        """Test USDT market neutral data provider initialization."""
        provider = USDTMarketNeutralDataProvider('backtest', mock_config)
        
        assert provider.execution_mode == 'backtest'
        assert 'eth_prices' in provider.available_data_types
        assert 'weeth_prices' in provider.available_data_types
        assert 'funding_rates' in provider.available_data_types
        assert 'aave_lending_rates' in provider.available_data_types
        assert 'staking_rewards' in provider.available_data_types
        assert not provider._data_loaded
    
    def test_validate_data_requirements_success(self, mock_data_provider):
        """Test successful data requirements validation."""
        requirements = ['eth_prices', 'weeth_prices', 'funding_rates']
        
        # Should not raise any exception
        mock_data_provider.validate_data_requirements(requirements)
    
    def test_validate_data_requirements_failure(self, mock_data_provider):
        """Test data requirements validation with missing requirements."""
        requirements = ['eth_prices', 'invalid_requirement']
        
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
            
            # Check protocol data structure
            assert 'aave_indexes' in data['protocol_data']
            assert 'perp_prices' in data['protocol_data']
            assert 'risk_params' in data['protocol_data']
            
            # Check staking data structure
            assert 'rewards' in data['staking_data']
            assert 'eigen_rewards' in data['staking_data']
            
            # Check execution data structure
            assert 'wallet_balances' in data['execution_data']
            assert 'smart_contract_balances' in data['execution_data']
            assert 'cex_derivatives_balances' in data['execution_data']
            assert 'gas_costs' in data['execution_data']
            assert 'execution_costs' in data['execution_data']
    
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
        assert 'aave_rates' in mock_data_provider.data
        assert 'aave_indexes' in mock_data_provider.data
        assert 'perp_prices' in mock_data_provider.data
        assert 'staking_rewards' in mock_data_provider.data
        assert 'gas_costs' in mock_data_provider.data
        assert 'execution_costs' in mock_data_provider.data
    
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
    
    def test_get_aave_eth_rate_with_data(self, mock_data_provider):
        """Test AAVE ETH supply rate retrieval with loaded data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # Mock loaded data
        mock_data_provider.data = {
            'aave_rates': pd.DataFrame({
                'timestamp': [timestamp],
                'eth_supply_rate': [0.035]
            })
        }
        
        rate = mock_data_provider._get_aave_eth_rate(timestamp)
        assert rate == 0.035
    
    def test_get_aave_eth_rate_fallback(self, mock_data_provider):
        """Test AAVE ETH supply rate fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        rate = mock_data_provider._get_aave_eth_rate(timestamp)
        assert rate == 0.03  # Default 3%
    
    def test_get_aave_indexes_with_data(self, mock_data_provider):
        """Test AAVE indexes retrieval with loaded data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # Mock loaded data
        mock_data_provider.data = {
            'aave_indexes': pd.DataFrame({
                'timestamp': [timestamp],
                'aETH': [1.06],
                'variableDebtWETH': [1.03]
            })
        }
        
        indexes = mock_data_provider._get_aave_indexes(timestamp)
        
        assert 'aETH' in indexes
        assert 'variableDebtWETH' in indexes
        assert indexes['aETH'] == 1.06
        assert indexes['variableDebtWETH'] == 1.03
    
    def test_get_aave_indexes_fallback(self, mock_data_provider):
        """Test AAVE indexes fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        indexes = mock_data_provider._get_aave_indexes(timestamp)
        
        assert 'aETH' in indexes
        assert indexes['aETH'] == 1.05  # Fallback value
    
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
    
    def test_get_risk_params(self, mock_data_provider):
        """Test AAVE risk parameters retrieval."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        risk_params = mock_data_provider._get_risk_params(timestamp)
        
        assert 'ltv' in risk_params
        assert 'liquidation_threshold' in risk_params
        assert 'liquidation_bonus' in risk_params
        assert risk_params['ltv'] == 0.8
        assert risk_params['liquidation_threshold'] == 0.85
        assert risk_params['liquidation_bonus'] == 0.05
    
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
    
    def test_get_eigen_rewards_with_data(self, mock_data_provider):
        """Test EIGEN rewards retrieval with loaded data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # Mock loaded data
        mock_data_provider.data = {
            'eigen_rewards': pd.DataFrame({
                'timestamp': [timestamp],
                'eigen_rewards': [0.0003]
            })
        }
        
        rewards = mock_data_provider._get_eigen_rewards(timestamp)
        
        assert 'EIGEN' in rewards
        assert rewards['EIGEN'] == 0.0003
    
    def test_get_eigen_rewards_fallback(self, mock_data_provider):
        """Test EIGEN rewards fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        rewards = mock_data_provider._get_eigen_rewards(timestamp)
        
        assert 'EIGEN' in rewards
        assert rewards['EIGEN'] == 0.0001  # Fallback value
    
    def test_get_wallet_balances(self, mock_data_provider):
        """Test wallet balances retrieval."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        balances = mock_data_provider._get_wallet_balances(timestamp)
        
        assert 'ETH' in balances
        assert 'weETH' in balances
        assert 'aWeETH' in balances
        assert 'variableDebtWETH' in balances
        assert 'USDT' in balances
        assert 'EIGEN' in balances
        assert 'KING' in balances
        assert balances['USDT'] == 1000.0  # Default USDT balance
    
    def test_get_smart_contract_balances(self, mock_data_provider):
        """Test smart contract balances retrieval."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        balances = mock_data_provider._get_smart_contract_balances(timestamp)
        
        assert 'aave' in balances
        assert 'etherfi' in balances
        assert 'aETH' in balances['aave']
        assert 'variableDebtWETH' in balances['aave']
        assert 'weETH' in balances['etherfi']
    
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
        assert 'supply' in gas_costs
        assert 'borrow' in gas_costs
        assert 'stake' in gas_costs
        assert 'trade' in gas_costs
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
        
        assert 'aave_supply' in exec_costs
        assert 'aave_borrow' in exec_costs
        assert 'binance_perp' in exec_costs
        assert 'bybit_perp' in exec_costs
        assert 'okx_perp' in exec_costs
        assert 'etherfi_stake' in exec_costs
        assert exec_costs['aave_supply'] == 0.0002
    
    def test_get_execution_costs_fallback(self, mock_data_provider):
        """Test execution costs fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        exec_costs = mock_data_provider._get_execution_costs(timestamp)
        
        assert 'aave_supply' in exec_costs
        assert exec_costs['aave_supply'] == 0.0001  # Fallback value
    
    def test_load_ml_ohlcv_from_csv(self, mock_data_provider):
        """Test loading ML OHLCV data from CSV file."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch('basis_strategy_v1.infrastructure.data.usdt_market_neutral_data_provider.pd.read_csv') as mock_read_csv:
            mock_df = pd.DataFrame({
                'timestamp': [timestamp],
                'open': [3000.0],
                'high': [3100.0],
                'low': [2900.0],
                'close': [3050.0],
                'volume': [100.0]
            })
            mock_read_csv.return_value = mock_df
            
            with patch('basis_strategy_v1.infrastructure.data.usdt_market_neutral_data_provider.os.path.exists', return_value=True):
                ohlcv = mock_data_provider._load_ml_ohlcv(timestamp, 'ETH')
                
                assert ohlcv['open'] == 3000.0
                assert ohlcv['close'] == 3050.0
                assert ohlcv['volume'] == 100.0
    
    def test_load_ml_ohlcv_file_not_found(self, mock_data_provider):
        """Test ML OHLCV loading when file not found."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch('basis_strategy_v1.infrastructure.data.usdt_market_neutral_data_provider.os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="ML OHLCV data not found"):
                mock_data_provider._load_ml_ohlcv(timestamp, 'ETH')
    
    def test_load_ml_prediction_from_csv(self, mock_data_provider):
        """Test loading ML prediction from CSV file."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch('basis_strategy_v1.infrastructure.data.usdt_market_neutral_data_provider.pd.read_csv') as mock_read_csv:
            mock_df = pd.DataFrame({
                'timestamp': [timestamp],
                'signal': ['long'],
                'confidence': [0.8],
                'take_profit': [3200.0],
                'stop_loss': [2800.0]
            })
            mock_read_csv.return_value = mock_df
            
            with patch('basis_strategy_v1.infrastructure.data.usdt_market_neutral_data_provider.os.path.exists', return_value=True):
                prediction = mock_data_provider._load_ml_prediction_from_csv(timestamp, 'ETH')
                
                assert prediction['signal'] == 'long'
                assert prediction['confidence'] == 0.8
                assert prediction['take_profit'] == 3200.0
    
    def test_load_ml_prediction_file_not_found(self, mock_data_provider):
        """Test ML prediction loading when file not found."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch('basis_strategy_v1.infrastructure.data.usdt_market_neutral_data_provider.os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="ML prediction data not found"):
                mock_data_provider._load_ml_prediction_from_csv(timestamp, 'ETH')
    
    def test_fetch_ml_prediction_from_api_with_token(self, mock_data_provider):
        """Test fetching ML prediction from API with valid token."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.dict('os.environ', {'BASIS_ML_API_TOKEN': 'test_token'}):
            with patch('basis_strategy_v1.infrastructure.data.usdt_market_neutral_data_provider.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.json.return_value = {
                    'signal': 'long',
                    'confidence': 0.8,
                    'take_profit': 3200.0,
                    'stop_loss': 2800.0
                }
                mock_response.raise_for_status.return_value = None
                mock_post.return_value = mock_response
                
                prediction = mock_data_provider._fetch_ml_prediction_from_api(timestamp, 'ETH')
                
                assert prediction['signal'] == 'long'
                assert prediction['confidence'] == 0.8
                mock_post.assert_called_once()
    
    def test_fetch_ml_prediction_from_api_no_token(self, mock_data_provider):
        """Test fetching ML prediction from API without token."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.dict('os.environ', {}, clear=True):
            prediction = mock_data_provider._fetch_ml_prediction_from_api(timestamp, 'ETH')
            
            assert prediction['signal'] == 'neutral'
            assert prediction['confidence'] == 0.0
    
    def test_fetch_ml_prediction_from_api_failure(self, mock_data_provider):
        """Test fetching ML prediction from API with failure."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.dict('os.environ', {'BASIS_ML_API_TOKEN': 'test_token'}):
            with patch('basis_strategy_v1.infrastructure.data.usdt_market_neutral_data_provider.requests.post') as mock_post:
                mock_post.side_effect = Exception("API Error")
                
                prediction = mock_data_provider._fetch_ml_prediction_from_api(timestamp, 'ETH')
                
                assert prediction['signal'] == 'neutral'
                assert prediction['confidence'] == 0.0
    
    def test_load_ml_prediction_backtest_mode(self, mock_data_provider):
        """Test ML prediction loading in backtest mode."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.object(mock_data_provider, '_load_ml_prediction_from_csv', return_value={'signal': 'long'}) as mock_csv:
            prediction = mock_data_provider._load_ml_prediction(timestamp, 'ETH')
            
            mock_csv.assert_called_once_with(timestamp, 'ETH')
            assert prediction['signal'] == 'long'
    
    def test_load_ml_prediction_live_mode(self, mock_config):
        """Test ML prediction loading in live mode."""
        provider = USDTMarketNeutralDataProvider('live', mock_config)
        
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.object(provider, '_fetch_ml_prediction_from_api', return_value={'signal': 'long'}) as mock_api:
            prediction = provider._load_ml_prediction(timestamp, 'ETH')
            
            mock_api.assert_called_once_with(timestamp, 'ETH')
            assert prediction['signal'] == 'long'
    
    def test_load_ml_prediction_invalid_mode(self, mock_config):
        """Test ML prediction loading with invalid execution mode."""
        provider = USDTMarketNeutralDataProvider('invalid', mock_config)
        
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with pytest.raises(ValueError, match="Unknown execution mode"):
            provider._load_ml_prediction(timestamp, 'ETH')
    
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
        for data_type in ['eth_prices', 'weeth_prices', 'funding_rates', 'aave_rates', 
                         'aave_indexes', 'perp_prices', 'staking_rewards', 'gas_costs', 'execution_costs']:
            assert data_type in mock_data_provider.data
            df = mock_data_provider.data[data_type]
            assert isinstance(df, pd.DataFrame)
            assert 'timestamp' in df.columns
            assert len(df) == 100  # Should have 100 rows of test data
