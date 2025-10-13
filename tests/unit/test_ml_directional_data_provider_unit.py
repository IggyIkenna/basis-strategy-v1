"""
Unit tests for ML Directional Data Provider.

Tests the ML directional data provider component in isolation with mocked dependencies.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from basis_strategy_v1.infrastructure.data.ml_directional_data_provider import MLDirectionalDataProvider


class TestMLDirectionalDataProvider:
    """Test ML Directional Data Provider component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for ML directional data provider."""
        return {
            'mode': 'ml_directional',
            'data_dir': 'test_data',
            'asset': 'BTC',
            'share_class': 'BTC',
            'data_requirements': ['ml_ohlcv_5min', 'ml_predictions', 'btc_usd_prices']
        }
    
    @pytest.fixture
    def mock_data_provider(self, mock_config):
        """Create ML directional data provider with mocked dependencies."""
        with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.os.path.exists', return_value=True):
            with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.pd.read_csv') as mock_read_csv:
                # Mock CSV data
                mock_df = pd.DataFrame({
                    'timestamp': pd.date_range('2024-01-01', periods=10, freq='5min'),
                    'price': [50000.0] * 10
                })
                mock_read_csv.return_value = mock_df
                
                provider = MLDirectionalDataProvider('backtest', mock_config)
                return provider
    
    def test_initialization(self, mock_config):
        """Test ML directional data provider initialization."""
        with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.os.path.exists', return_value=True):
            provider = MLDirectionalDataProvider('backtest', mock_config)
            
            assert provider.execution_mode == 'backtest'
            assert provider.asset == 'BTC'
            assert provider.share_class == 'BTC'
            assert 'ml_ohlcv_5min' in provider.available_data_types
            assert 'ml_predictions' in provider.available_data_types
            assert 'btc_usd_prices' in provider.available_data_types
            assert not provider._data_loaded
    
    def test_initialization_with_different_asset(self, mock_config):
        """Test initialization with different asset configuration."""
        config = mock_config.copy()
        config['asset'] = 'ETH'
        config['share_class'] = 'ETH'
        
        with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.os.path.exists', return_value=True):
            provider = MLDirectionalDataProvider('backtest', config)
            
            assert provider.asset == 'ETH'
            assert provider.share_class == 'ETH'
            assert 'eth_usd_prices' in provider.available_data_types
    
    def test_validate_data_requirements_success(self, mock_data_provider):
        """Test successful data requirements validation."""
        requirements = ['ml_ohlcv_5min', 'ml_predictions', 'btc_usd_prices']
        
        # Should not raise any exception
        mock_data_provider.validate_data_requirements(requirements)
    
    def test_validate_data_requirements_failure(self, mock_data_provider):
        """Test data requirements validation with missing requirements."""
        requirements = ['ml_ohlcv_5min', 'invalid_requirement']
        
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
            assert 'ml_data' in data
            
            # Check market data structure
            assert 'prices' in data['market_data']
            assert 'rates' in data['market_data']
            assert 'BTC' in data['market_data']['prices']
            assert 'USDT' in data['market_data']['prices']
            
            # Check ML data structure
            assert 'predictions' in data['ml_data']
            assert 'ohlcv' in data['ml_data']
            assert 'model_status' in data['ml_data']
    
    def test_get_timestamps(self, mock_data_provider):
        """Test timestamp generation for backtest period."""
        start_date = '2024-01-01'
        end_date = '2024-01-02'
        
        timestamps = mock_data_provider.get_timestamps(start_date, end_date)
        
        assert isinstance(timestamps, list)
        assert len(timestamps) > 0
        assert all(isinstance(ts, pd.Timestamp) for ts in timestamps)
        # Should be 5-minute intervals
        assert timestamps[1] - timestamps[0] == pd.Timedelta(minutes=5)
    
    def test_load_data_backtest_mode(self, mock_data_provider):
        """Test data loading in backtest mode."""
        with patch.object(mock_data_provider, '_load_backtest_data') as mock_load:
            mock_data_provider.load_data()
            
            mock_load.assert_called_once()
            assert mock_data_provider._data_loaded
    
    def test_load_data_live_mode(self, mock_config):
        """Test data loading in live mode."""
        with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.os.path.exists', return_value=True):
            provider = MLDirectionalDataProvider('live', mock_config)
            
            with patch.object(provider, '_load_backtest_data') as mock_load:
                provider.load_data()
                
                # Should not call backtest data loading in live mode
                mock_load.assert_not_called()
                assert provider._data_loaded
    
    def test_get_asset_price_with_data(self, mock_data_provider):
        """Test asset price retrieval with loaded data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # Mock loaded data
        mock_data_provider.data = {
            'asset_prices': pd.DataFrame({
                'timestamp': [timestamp],
                'price': [50000.0]
            })
        }
        
        price = mock_data_provider._get_asset_price(timestamp)
        assert price == 50000.0
    
    def test_get_asset_price_fallback(self, mock_data_provider):
        """Test asset price fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        price = mock_data_provider._get_asset_price(timestamp)
        assert price == 50000.0  # BTC fallback price
    
    def test_get_asset_price_eth_fallback(self, mock_config):
        """Test ETH asset price fallback."""
        config = mock_config.copy()
        config['asset'] = 'ETH'
        
        with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.os.path.exists', return_value=True):
            provider = MLDirectionalDataProvider('backtest', config)
            provider.data = {}
            
            price = provider._get_asset_price(pd.Timestamp('2024-01-01 12:00:00', tz='UTC'))
            assert price == 3000.0  # ETH fallback price
    
    def test_get_perp_prices(self, mock_data_provider):
        """Test perpetual prices retrieval."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.object(mock_data_provider, '_get_asset_price', return_value=50000.0):
            perp_prices = mock_data_provider._get_perp_prices(timestamp)
            
            assert 'BTC-PERP' in perp_prices
            assert perp_prices['BTC-PERP'] == 50000.0
    
    def test_get_gas_costs_with_data(self, mock_data_provider):
        """Test gas costs retrieval with loaded data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # Mock loaded data
        mock_data_provider.data = {
            'gas_costs': pd.DataFrame({
                'timestamp': [timestamp],
                'cost': [0.001]
            })
        }
        
        gas_costs = mock_data_provider._get_gas_costs(timestamp)
        
        assert 'binance_perp' in gas_costs
        assert 'bybit_perp' in gas_costs
        assert 'okx_perp' in gas_costs
        assert gas_costs['binance_perp'] == 0.001
    
    def test_get_gas_costs_fallback(self, mock_data_provider):
        """Test gas costs fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        gas_costs = mock_data_provider._get_gas_costs(timestamp)
        
        assert 'binance_perp' in gas_costs
        assert gas_costs['binance_perp'] == 0.0001  # Fallback value
    
    def test_get_execution_costs_with_data(self, mock_data_provider):
        """Test execution costs retrieval with loaded data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # Mock loaded data
        mock_data_provider.data = {
            'execution_costs': pd.DataFrame({
                'timestamp': [timestamp],
                'cost': [0.0005]
            })
        }
        
        exec_costs = mock_data_provider._get_execution_costs(timestamp)
        
        assert 'binance_perp' in exec_costs
        assert 'bybit_perp' in exec_costs
        assert 'okx_perp' in exec_costs
        assert exec_costs['binance_perp'] == 0.0005
    
    def test_get_execution_costs_fallback(self, mock_data_provider):
        """Test execution costs fallback when no data loaded."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        # No data loaded
        mock_data_provider.data = {}
        
        exec_costs = mock_data_provider._get_execution_costs(timestamp)
        
        assert 'binance_perp' in exec_costs
        assert exec_costs['binance_perp'] == 0.0001  # Fallback value
    
    def test_get_ml_predictions_with_data(self, mock_data_provider):
        """Test ML predictions retrieval with available data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.object(mock_data_provider, '_load_ml_prediction', return_value={
            'signal': 'long',
            'confidence': 0.8,
            'take_profit': 52000.0,
            'stop_loss': 48000.0
        }):
            predictions = mock_data_provider._get_ml_predictions(timestamp)
            
            assert 'BTC' in predictions
            assert predictions['BTC']['signal'] == 'long'
            assert predictions['BTC']['confidence'] == 0.8
    
    def test_get_ml_predictions_fallback(self, mock_data_provider):
        """Test ML predictions fallback when data not available."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.object(mock_data_provider, '_load_ml_prediction', side_effect=FileNotFoundError("No data")):
            predictions = mock_data_provider._get_ml_predictions(timestamp)
            
            assert 'BTC' in predictions
            assert predictions['BTC']['signal'] == 'neutral'
            assert predictions['BTC']['confidence'] == 0.0
            assert 'note' in predictions['BTC']
    
    def test_get_ml_ohlcv_data_with_data(self, mock_data_provider):
        """Test ML OHLCV data retrieval with available data."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.object(mock_data_provider, '_load_ml_ohlcv', return_value={
            'open': 50000.0,
            'high': 51000.0,
            'low': 49000.0,
            'close': 50500.0,
            'volume': 100.0
        }):
            ohlcv_data = mock_data_provider._get_ml_ohlcv_data(timestamp)
            
            assert 'BTC' in ohlcv_data
            assert ohlcv_data['BTC']['open'] == 50000.0
            assert ohlcv_data['BTC']['close'] == 50500.0
    
    def test_get_ml_ohlcv_data_fallback(self, mock_data_provider):
        """Test ML OHLCV data fallback when data not available."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.object(mock_data_provider, '_load_ml_ohlcv', side_effect=FileNotFoundError("No data")):
            ohlcv_data = mock_data_provider._get_ml_ohlcv_data(timestamp)
            
            assert ohlcv_data == {}  # Empty dict when no data
    
    def test_get_ml_model_status(self, mock_data_provider):
        """Test ML model status retrieval."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        status = mock_data_provider._get_ml_model_status(timestamp)
        
        assert 'model_version' in status
        assert 'last_updated' in status
        assert 'status' in status
        assert status['model_version'] == 'v1.0.0'
        assert status['status'] == 'active'
    
    def test_load_ml_ohlcv_from_csv(self, mock_data_provider):
        """Test loading ML OHLCV data from CSV file."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.pd.read_csv') as mock_read_csv:
            mock_df = pd.DataFrame({
                'timestamp': [timestamp],
                'open': [50000.0],
                'high': [51000.0],
                'low': [49000.0],
                'close': [50500.0],
                'volume': [100.0]
            })
            mock_read_csv.return_value = mock_df
            
            ohlcv = mock_data_provider._load_ml_ohlcv(timestamp, 'BTC')
            
            assert ohlcv['open'] == 50000.0
            assert ohlcv['close'] == 50500.0
            assert ohlcv['volume'] == 100.0
    
    def test_load_ml_ohlcv_file_not_found(self, mock_data_provider):
        """Test ML OHLCV loading when file not found."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="ML OHLCV data not found"):
                mock_data_provider._load_ml_ohlcv(timestamp, 'BTC')
    
    def test_load_ml_prediction_from_csv(self, mock_data_provider):
        """Test loading ML prediction from CSV file."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.pd.read_csv') as mock_read_csv:
            mock_df = pd.DataFrame({
                'timestamp': [timestamp],
                'signal': ['long'],
                'confidence': [0.8],
                'take_profit': [52000.0],
                'stop_loss': [48000.0]
            })
            mock_read_csv.return_value = mock_df
            
            prediction = mock_data_provider._load_ml_prediction_from_csv(timestamp, 'BTC')
            
            assert prediction['signal'] == 'long'
            assert prediction['confidence'] == 0.8
            assert prediction['take_profit'] == 52000.0
    
    def test_load_ml_prediction_file_not_found(self, mock_data_provider):
        """Test ML prediction loading when file not found."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="ML prediction data not found"):
                mock_data_provider._load_ml_prediction_from_csv(timestamp, 'BTC')
    
    def test_fetch_ml_prediction_from_api_with_token(self, mock_data_provider):
        """Test fetching ML prediction from API with valid token."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.dict('os.environ', {'BASIS_ML_API_TOKEN': 'test_token'}):
            with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.json.return_value = {
                    'signal': 'long',
                    'confidence': 0.8,
                    'take_profit': 52000.0,
                    'stop_loss': 48000.0
                }
                mock_response.raise_for_status.return_value = None
                mock_post.return_value = mock_response
                
                prediction = mock_data_provider._fetch_ml_prediction_from_api(timestamp, 'BTC')
                
                assert prediction['signal'] == 'long'
                assert prediction['confidence'] == 0.8
                mock_post.assert_called_once()
    
    def test_fetch_ml_prediction_from_api_no_token(self, mock_data_provider):
        """Test fetching ML prediction from API without token."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.dict('os.environ', {}, clear=True):
            prediction = mock_data_provider._fetch_ml_prediction_from_api(timestamp, 'BTC')
            
            assert prediction['signal'] == 'neutral'
            assert prediction['confidence'] == 0.0
    
    def test_fetch_ml_prediction_from_api_failure(self, mock_data_provider):
        """Test fetching ML prediction from API with failure."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.dict('os.environ', {'BASIS_ML_API_TOKEN': 'test_token'}):
            with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.requests.post') as mock_post:
                mock_post.side_effect = Exception("API Error")
                
                prediction = mock_data_provider._fetch_ml_prediction_from_api(timestamp, 'BTC')
                
                assert prediction['signal'] == 'neutral'
                assert prediction['confidence'] == 0.0
    
    def test_load_ml_prediction_backtest_mode(self, mock_data_provider):
        """Test ML prediction loading in backtest mode."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        
        with patch.object(mock_data_provider, '_load_ml_prediction_from_csv', return_value={'signal': 'long'}) as mock_csv:
            prediction = mock_data_provider._load_ml_prediction(timestamp, 'BTC')
            
            mock_csv.assert_called_once_with(timestamp, 'BTC')
            assert prediction['signal'] == 'long'
    
    def test_load_ml_prediction_live_mode(self, mock_config):
        """Test ML prediction loading in live mode."""
        with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.os.path.exists', return_value=True):
            provider = MLDirectionalDataProvider('live', mock_config)
            
            timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
            
            with patch.object(provider, '_fetch_ml_prediction_from_api', return_value={'signal': 'long'}) as mock_api:
                prediction = provider._load_ml_prediction(timestamp, 'BTC')
                
                mock_api.assert_called_once_with(timestamp, 'BTC')
                assert prediction['signal'] == 'long'
    
    def test_load_ml_prediction_invalid_mode(self, mock_config):
        """Test ML prediction loading with invalid execution mode."""
        with patch('basis_strategy_v1.infrastructure.data.ml_directional_data_provider.os.path.exists', return_value=True):
            provider = MLDirectionalDataProvider('invalid', mock_config)
            
            timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
            
            with pytest.raises(ValueError, match="Unknown execution mode"):
                provider._load_ml_prediction(timestamp, 'BTC')
    
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
        
        assert len(timestamps) > 100000  # Should be a large number of 5-minute intervals
        assert timestamps[0] == pd.Timestamp(start_date)
        assert timestamps[-1] <= pd.Timestamp(end_date)
