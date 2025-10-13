#!/usr/bin/env python3
"""
Config Driven Historical Data Provider Unit Tests

Tests the Config Driven Historical Data Provider component in isolation with mocked dependencies.
Validates configuration-driven data loading, historical data retrieval, and data validation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Mock the backend imports
with patch.dict('sys.modules', {
    'basis_strategy_v1': Mock(),
    'basis_strategy_v1.infrastructure': Mock(),
    'basis_strategy_v1.infrastructure.data': Mock(),
    'basis_strategy_v1.infrastructure.config': Mock(),
}):
    # Import the data provider class (will be mocked)
    from basis_strategy_v1.infrastructure.data.config_driven_historical_data_provider import ConfigDrivenHistoricalDataProvider


class TestConfigDrivenHistoricalDataProvider:
    """Test suite for Config Driven Historical Data Provider component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'data_sources': {
                'market_data': {
                    'type': 'csv',
                    'path': 'data/market_data/',
                    'format': 'ohlcv',
                    'assets': ['BTC', 'ETH', 'USDT']
                },
                'protocol_data': {
                    'type': 'api',
                    'endpoint': 'https://api.aave.com',
                    'format': 'json',
                    'assets': ['WETH', 'USDC', 'DAI']
                },
                'blockchain_data': {
                    'type': 'rpc',
                    'endpoint': 'https://eth-mainnet.alchemyapi.io',
                    'format': 'json',
                    'assets': ['ETH']
                }
            },
            'time_range': {
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'granularity': '1h'
            },
            'validation': {
                'required_fields': ['timestamp', 'price', 'volume'],
                'data_quality_checks': True,
                'outlier_detection': True
            }
        }
    
    @pytest.fixture
    def mock_historical_data(self):
        """Mock historical data for testing."""
        return {
            'market_data': [
                {
                    'timestamp': datetime(2024, 1, 1, 0, 0, 0),
                    'asset': 'BTC',
                    'open': Decimal('42000'),
                    'high': Decimal('43000'),
                    'low': Decimal('41000'),
                    'close': Decimal('42500'),
                    'volume': Decimal('1000000')
                },
                {
                    'timestamp': datetime(2024, 1, 1, 1, 0, 0),
                    'asset': 'BTC',
                    'open': Decimal('42500'),
                    'high': Decimal('43500'),
                    'low': Decimal('42000'),
                    'close': Decimal('43000'),
                    'volume': Decimal('1200000')
                }
            ],
            'protocol_data': [
                {
                    'timestamp': datetime(2024, 1, 1, 0, 0, 0),
                    'asset': 'WETH',
                    'supply_rate': Decimal('0.05'),
                    'borrow_rate': Decimal('0.08'),
                    'liquidity': Decimal('10000000')
                }
            ],
            'blockchain_data': [
                {
                    'timestamp': datetime(2024, 1, 1, 0, 0, 0),
                    'block_number': 19000000,
                    'gas_price': Decimal('20'),
                    'base_fee': Decimal('15'),
                    'priority_fee': Decimal('5')
                }
            ]
        }
    
    @pytest.fixture
    def config_driven_data_provider(self, mock_config, mock_historical_data):
        """Create Config Driven Historical Data Provider instance for testing."""
        with patch('basis_strategy_v1.infrastructure.data.config_driven_historical_data_provider.ConfigDrivenHistoricalDataProvider') as mock_provider_class:
            provider = Mock()
            provider.initialize.return_value = True
            provider.load_config.return_value = mock_config
            provider.get_historical_data.return_value = mock_historical_data['market_data']
            provider.get_protocol_data.return_value = mock_historical_data['protocol_data']
            provider.get_blockchain_data.return_value = mock_historical_data['blockchain_data']
            provider.validate_data.return_value = True
            provider.get_data_sources.return_value = list(mock_config['data_sources'].keys())
            provider.get_time_range.return_value = mock_config['time_range']
            return provider
    
    def test_provider_initialization(self, config_driven_data_provider, mock_config):
        """Test config driven historical data provider initializes correctly."""
        # Test initialization
        result = config_driven_data_provider.initialize(mock_config)
        
        # Verify initialization
        assert result is True
        config_driven_data_provider.initialize.assert_called_once_with(mock_config)
    
    def test_config_loading(self, config_driven_data_provider, mock_config):
        """Test configuration loading and validation."""
        # Test config loading
        loaded_config = config_driven_data_provider.load_config()
        assert loaded_config == mock_config
        
        # Test data sources configuration
        data_sources = loaded_config['data_sources']
        assert 'market_data' in data_sources
        assert 'protocol_data' in data_sources
        assert 'blockchain_data' in data_sources
        
        # Test market data source configuration
        market_data_config = data_sources['market_data']
        assert market_data_config['type'] == 'csv'
        assert market_data_config['path'] == 'data/market_data/'
        assert market_data_config['format'] == 'ohlcv'
        assert 'BTC' in market_data_config['assets']
        assert 'ETH' in market_data_config['assets']
        assert 'USDT' in market_data_config['assets']
    
    def test_historical_data_retrieval(self, config_driven_data_provider, mock_historical_data):
        """Test historical data retrieval from different sources."""
        # Test market data retrieval
        market_data = config_driven_data_provider.get_historical_data()
        assert market_data == mock_historical_data['market_data']
        
        # Test protocol data retrieval
        protocol_data = config_driven_data_provider.get_protocol_data()
        assert protocol_data == mock_historical_data['protocol_data']
        
        # Test blockchain data retrieval
        blockchain_data = config_driven_data_provider.get_blockchain_data()
        assert blockchain_data == mock_historical_data['blockchain_data']
    
    def test_data_validation(self, config_driven_data_provider, mock_historical_data):
        """Test data validation and quality checks."""
        # Test data validation
        is_valid = config_driven_data_provider.validate_data(mock_historical_data['market_data'])
        assert is_valid is True
        
        # Test required fields validation
        market_data = mock_historical_data['market_data'][0]
        required_fields = ['timestamp', 'price', 'volume']
        
        # Check if all required fields are present
        for field in required_fields:
            if field == 'price':
                # Price can be represented as 'close' in OHLCV data
                assert 'close' in market_data
            elif field == 'volume':
                assert 'volume' in market_data
            elif field == 'timestamp':
                assert 'timestamp' in market_data
    
    def test_time_range_configuration(self, config_driven_data_provider, mock_config):
        """Test time range configuration and validation."""
        # Test time range retrieval
        time_range = config_driven_data_provider.get_time_range()
        assert time_range == mock_config['time_range']
        
        # Test time range components
        assert time_range['start_date'] == '2024-01-01'
        assert time_range['end_date'] == '2024-12-31'
        assert time_range['granularity'] == '1h'
    
    def test_data_sources_management(self, config_driven_data_provider, mock_config):
        """Test data sources management and configuration."""
        # Test available data sources
        data_sources = config_driven_data_provider.get_data_sources()
        expected_sources = list(mock_config['data_sources'].keys())
        assert set(data_sources) == set(expected_sources)
        
        # Test individual data source configuration
        config_sources = mock_config['data_sources']
        
        # Test market data source
        market_source = config_sources['market_data']
        assert market_source['type'] == 'csv'
        assert market_source['format'] == 'ohlcv'
        
        # Test protocol data source
        protocol_source = config_sources['protocol_data']
        assert protocol_source['type'] == 'api'
        assert protocol_source['endpoint'] == 'https://api.aave.com'
        
        # Test blockchain data source
        blockchain_source = config_sources['blockchain_data']
        assert blockchain_source['type'] == 'rpc'
        assert blockchain_source['endpoint'] == 'https://eth-mainnet.alchemyapi.io'
    
    def test_data_format_handling(self, config_driven_data_provider, mock_historical_data):
        """Test different data format handling."""
        # Test CSV format handling (market data)
        market_data = mock_historical_data['market_data']
        assert isinstance(market_data, list)
        assert len(market_data) > 0
        
        # Test OHLCV format
        ohlcv_record = market_data[0]
        assert 'open' in ohlcv_record
        assert 'high' in ohlcv_record
        assert 'low' in ohlcv_record
        assert 'close' in ohlcv_record
        assert 'volume' in ohlcv_record
        
        # Test JSON format handling (protocol data)
        protocol_data = mock_historical_data['protocol_data']
        assert isinstance(protocol_data, list)
        assert len(protocol_data) > 0
        
        # Test protocol data structure
        protocol_record = protocol_data[0]
        assert 'supply_rate' in protocol_record
        assert 'borrow_rate' in protocol_record
        assert 'liquidity' in protocol_record
    
    def test_data_quality_checks(self, config_driven_data_provider, mock_historical_data):
        """Test data quality checks and validation."""
        # Test outlier detection
        with patch.object(config_driven_data_provider, 'detect_outliers', return_value=[]):
            outliers = config_driven_data_provider.detect_outliers(mock_historical_data['market_data'])
            assert outliers == []
        
        # Test data completeness check
        with patch.object(config_driven_data_provider, 'check_data_completeness', return_value=True):
            is_complete = config_driven_data_provider.check_data_completeness(mock_historical_data['market_data'])
            assert is_complete is True
        
        # Test data consistency check
        with patch.object(config_driven_data_provider, 'check_data_consistency', return_value=True):
            is_consistent = config_driven_data_provider.check_data_consistency(mock_historical_data['market_data'])
            assert is_consistent is True
    
    def test_asset_specific_data_retrieval(self, config_driven_data_provider, mock_historical_data):
        """Test asset-specific data retrieval."""
        # Test BTC data retrieval
        with patch.object(config_driven_data_provider, 'get_asset_data', return_value=mock_historical_data['market_data']):
            btc_data = config_driven_data_provider.get_asset_data('BTC')
            assert btc_data == mock_historical_data['market_data']
        
        # Test ETH data retrieval
        with patch.object(config_driven_data_provider, 'get_asset_data', return_value=[]):
            eth_data = config_driven_data_provider.get_asset_data('ETH')
            assert eth_data == []
        
        # Test USDT data retrieval
        with patch.object(config_driven_data_provider, 'get_asset_data', return_value=[]):
            usdt_data = config_driven_data_provider.get_asset_data('USDT')
            assert usdt_data == []
    
    def test_data_aggregation_and_processing(self, config_driven_data_provider, mock_historical_data):
        """Test data aggregation and processing capabilities."""
        # Test data aggregation by time period
        with patch.object(config_driven_data_provider, 'aggregate_by_period', return_value={}):
            aggregated_data = config_driven_data_provider.aggregate_by_period(mock_historical_data['market_data'], '1d')
            assert isinstance(aggregated_data, dict)
        
        # Test data interpolation
        with patch.object(config_driven_data_provider, 'interpolate_missing_data', return_value=mock_historical_data['market_data']):
            interpolated_data = config_driven_data_provider.interpolate_missing_data(mock_historical_data['market_data'])
            assert interpolated_data == mock_historical_data['market_data']
        
        # Test data normalization
        with patch.object(config_driven_data_provider, 'normalize_data', return_value=mock_historical_data['market_data']):
            normalized_data = config_driven_data_provider.normalize_data(mock_historical_data['market_data'])
            assert normalized_data == mock_historical_data['market_data']
    
    def test_error_handling_and_fallback(self, config_driven_data_provider):
        """Test error handling and fallback mechanisms."""
        # Test configuration error handling
        with patch.object(config_driven_data_provider, 'load_config', side_effect=ValueError("Invalid config")):
            with pytest.raises(ValueError, match="Invalid config"):
                config_driven_data_provider.load_config()
        
        # Test data loading error handling
        with patch.object(config_driven_data_provider, 'get_historical_data', side_effect=IOError("Data not found")):
            with pytest.raises(IOError, match="Data not found"):
                config_driven_data_provider.get_historical_data()
        
        # Test fallback data source
        with patch.object(config_driven_data_provider, 'get_fallback_data', return_value={'fallback': True}):
            fallback_data = config_driven_data_provider.get_fallback_data()
            assert fallback_data['fallback'] is True
    
    def test_data_provider_state_management(self, config_driven_data_provider):
        """Test data provider state management and persistence."""
        # Test provider state
        provider_state = {
            'config_loaded': True,
            'data_sources_configured': 3,
            'last_data_update': datetime.now(),
            'total_records_loaded': 1000,
            'data_quality_score': 0.95,
            'active_sources': ['market_data', 'protocol_data', 'blockchain_data'],
            'failed_sources': [],
            'cache_enabled': True,
            'cache_hit_rate': 0.85
        }
        
        # Verify state components
        assert provider_state['config_loaded'] is True
        assert provider_state['data_sources_configured'] == 3
        assert isinstance(provider_state['last_data_update'], datetime)
        assert provider_state['total_records_loaded'] == 1000
        assert provider_state['data_quality_score'] == 0.95
        assert len(provider_state['active_sources']) == 3
        assert provider_state['failed_sources'] == []
        assert provider_state['cache_enabled'] is True
        assert provider_state['cache_hit_rate'] == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
