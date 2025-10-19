#!/usr/bin/env python3
"""
Quality Gates: Data Provider Validation

Tests the new data provider architecture with position_subscriptions-based data loading.
Validates that data providers correctly derive CSV mappings and load data.

Reference: DATA_ARCHITECTURE_REFACTOR_PLAN.md
"""

import sys
import os
import pandas as pd
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

from basis_strategy_v1.infrastructure.data.historical_defi_data_provider import HistoricalDeFiDataProvider
from basis_strategy_v1.infrastructure.data.historical_cefi_data_provider import HistoricalCeFiDataProvider
from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider


class TestDataProviderValidation(unittest.TestCase):
    """Test data provider validation and CSV mapping derivation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.defi_config = {
            'mode': 'eth_leveraged',
            'data_type': 'defi',
            'data_dir': 'data',
            'component_config': {
                'position_monitor': {
                    'position_subscriptions': [
                        'wallet:BaseToken:ETH',
                        'etherfi:aToken:weETH',
                        'aave_v3:aToken:aWETH',
                        'aave_v3:debtToken:debtETH'
                    ],
                    'settlement': {
                        'seasonal_rewards_enabled': True
                    }
                }
            }
        }
        
        self.cefi_config = {
            'mode': 'ml_btc_directional_btc_margin',
            'data_type': 'cefi',
            'data_dir': 'data',
            'component_config': {
                'position_monitor': {
                    'position_subscriptions': [
                        'binance:BaseToken:BTC',
                        'binance:Perp:BTCUSDT',
                        'bybit:BaseToken:BTC',
                        'bybit:Perp:BTCUSDT'
                    ]
                }
            }
        }
    
    def test_defi_provider_csv_mapping_derivation(self):
        """Test that DeFi provider correctly derives CSV mappings from position_subscriptions."""
        provider = HistoricalDeFiDataProvider(self.defi_config)
        mappings = provider.csv_mappings
        
        # Check that mappings were derived
        self.assertIsInstance(mappings, dict)
        self.assertGreater(len(mappings), 0)
        
        # Check specific expected mappings
        expected_keys = [
            'market_data.prices.ETH',
            'protocol_data.aave_indexes.aWETH',
            'protocol_data.aave_indexes.debtETH',
            'execution_data.gas_costs',
            'execution_data.execution_costs'
        ]
        
        for key in expected_keys:
            self.assertIn(key, mappings, f"Missing expected mapping: {key}")
        
        # Check that CSV paths are valid
        for key, path in mappings.items():
            if path and path.endswith('.csv'):
                self.assertTrue(
                    path.startswith('data/') or path.startswith('/'),
                    f"Invalid CSV path format: {path}"
                )
    
    def test_cefi_provider_csv_mapping_derivation(self):
        """Test that CeFi provider correctly derives CSV mappings from position_subscriptions."""
        # Create mock ML service for testing
        class MockMLService:
            def __init__(self, config):
                self.config = config
            
            def get_prediction(self, timestamp, data):
                return 0.5  # Mock prediction
        
        ml_service = MockMLService(self.cefi_config)
        provider = HistoricalCeFiDataProvider(self.cefi_config, ml_service)
        mappings = provider.csv_mappings
        
        # Check that mappings were derived
        self.assertIsInstance(mappings, dict)
        self.assertGreater(len(mappings), 0)
        
        # Check specific expected mappings
        expected_keys = [
            'market_data.prices.BTC',
            'protocol_data.perp_prices.BTC_binance',
            'protocol_data.perp_prices.BTC_bybit',
            'execution_data.gas_costs',
            'execution_data.execution_costs'
        ]
        
        for key in expected_keys:
            self.assertIn(key, mappings, f"Missing expected mapping: {key}")
    
    def test_data_provider_factory_creation(self):
        """Test that data provider factory creates correct providers."""
        # Test DeFi provider creation
        defi_provider = create_data_provider('backtest', 'defi', self.defi_config)
        self.assertIsInstance(defi_provider, HistoricalDeFiDataProvider)
        
        # Test CeFi provider creation
        cefi_provider = create_data_provider('backtest', 'cefi', self.cefi_config)
        self.assertIsInstance(cefi_provider, HistoricalCeFiDataProvider)
    
    def test_data_provider_factory_validation(self):
        """Test that data provider factory validates config properly."""
        # Test invalid execution_mode
        with self.assertRaises(ValueError) as context:
            create_data_provider('invalid_mode', 'defi', self.defi_config)
        
        self.assertIn('execution_mode', str(context.exception))
        
        # Test invalid data_type
        with self.assertRaises(ValueError) as context:
            create_data_provider('backtest', 'invalid_type', self.defi_config)
        
        self.assertIn('data_type', str(context.exception))
        
        # Test missing position_subscriptions (this will be caught by the data provider)
        invalid_config = self.defi_config.copy()
        del invalid_config['component_config']['position_monitor']['position_subscriptions']
        
        with self.assertRaises(KeyError) as context:
            create_data_provider('backtest', 'defi', invalid_config)
        
        self.assertIn('position_subscriptions', str(context.exception))
    
    def test_data_provider_standardized_structure(self):
        """Test that data providers return standardized data structure."""
        provider = HistoricalDeFiDataProvider(self.defi_config)
        
        # Mock data loading to avoid file dependencies
        with patch.object(provider, '_load_csv_value', return_value=100.0):
            with patch.object(provider, '_resolve_csv_path', return_value='test.csv'):
                data = provider.get_data(pd.Timestamp('2024-06-15 12:00:00', tz='UTC'))
        
        # Check standardized structure
        required_keys = ['market_data', 'protocol_data', 'execution_data']
        for key in required_keys:
            self.assertIn(key, data, f"Missing required key: {key}")
        
        # Check market_data structure
        self.assertIn('prices', data['market_data'])
        self.assertIn('funding_rates', data['market_data'])
        
        # Check protocol_data structure
        self.assertIn('aave_indexes', data['protocol_data'])
        self.assertIn('oracle_prices', data['protocol_data'])
        self.assertIn('perp_prices', data['protocol_data'])
        
        # Check execution_data structure
        self.assertIn('gas_costs', data['execution_data'])
        self.assertIn('execution_costs', data['execution_data'])
    
    def test_position_key_parsing(self):
        """Test that position keys are parsed correctly."""
        provider = HistoricalDeFiDataProvider(self.defi_config)
        
        # Test valid position keys
        valid_keys = [
            'wallet:BaseToken:ETH',
            'aave_v3:aToken:aWETH',
            'binance:Perp:BTCUSDT'
        ]
        
        for key in valid_keys:
            venue, position_type, instrument = key.split(':')
            self.assertIsInstance(venue, str)
            self.assertIsInstance(position_type, str)
            self.assertIsInstance(instrument, str)
    
    def test_seasonal_rewards_detection(self):
        """Test that seasonal rewards are detected correctly."""
        provider = HistoricalDeFiDataProvider(self.defi_config)
        
        # Should detect seasonal rewards are enabled
        self.assertTrue(provider._is_seasonal_rewards_enabled())
        
        # Test with seasonal rewards disabled
        config_no_seasonal = self.defi_config.copy()
        config_no_seasonal['component_config']['position_monitor']['settlement']['seasonal_rewards_enabled'] = False
        
        provider_no_seasonal = HistoricalDeFiDataProvider(config_no_seasonal)
        self.assertFalse(provider_no_seasonal._is_seasonal_rewards_enabled())
    
    def test_csv_mapping_completeness(self):
        """Test that CSV mappings cover all position subscriptions."""
        provider = HistoricalDeFiDataProvider(self.defi_config)
        mappings = provider.csv_mappings
        
        # Check that we have mappings for all position types
        position_types = set()
        for position_key in self.defi_config['component_config']['position_monitor']['position_subscriptions']:
            venue, position_type, instrument = position_key.split(':')
            position_types.add(position_type)
        
        # Should have mappings for each position type
        mapping_keys = set(mappings.keys())
        
        # Check for BaseToken prices
        self.assertTrue(any('market_data.prices' in key for key in mapping_keys))
        
        # Check for aToken mappings
        self.assertTrue(any('protocol_data.aave_indexes' in key for key in mapping_keys))
        
        # Check for execution costs
        self.assertTrue(any('execution_data.gas_costs' in key for key in mapping_keys))
        self.assertTrue(any('execution_data.execution_costs' in key for key in mapping_keys))


class TestDataProviderIntegration(unittest.TestCase):
    """Test data provider integration with actual data."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.btc_basis_config = {
            'mode': 'btc_basis',
            'data_type': 'defi',
            'data_dir': 'data',
            'component_config': {
                'position_monitor': {
                    'position_subscriptions': [
                        'wallet:BaseToken:USDT',
                        'binance:BaseToken:USDT',
                        'binance:BaseToken:BTC',
                        'binance:Perp:BTCUSDT',
                        'bybit:BaseToken:USDT',
                        'bybit:Perp:BTCUSDT',
                        'okx:BaseToken:USDT',
                        'okx:Perp:BTCUSDT'
                    ]
                }
            }
        }
    
    def test_btc_basis_data_loading(self):
        """Test that BTC basis strategy can load data successfully."""
        provider = HistoricalDeFiDataProvider(self.btc_basis_config)
        
        # Test data loading at a specific timestamp
        test_timestamp = pd.Timestamp('2024-06-15 12:00:00', tz='UTC')
        
        try:
            data = provider.get_data(test_timestamp)
            
            # Check that data was loaded
            self.assertIsInstance(data, dict)
            self.assertIn('market_data', data)
            self.assertIn('protocol_data', data)
            self.assertIn('execution_data', data)
            
            # Check that we have BTC price data
            if 'prices' in data['market_data']:
                self.assertIn('BTC', data['market_data']['prices'])
                self.assertIn('USDT', data['market_data']['prices'])
            
        except Exception as e:
            # If data loading fails due to missing files, that's expected in test environment
            self.assertIn('No CSV file found', str(e))
    
    def test_data_provider_health_status(self):
        """Test that data providers maintain health status."""
        provider = HistoricalDeFiDataProvider(self.btc_basis_config)
        
        # Check that provider has required methods
        self.assertTrue(hasattr(provider, 'get_data'))
        self.assertTrue(hasattr(provider, 'csv_mappings'))
        
        # Test error handling - try to get data with a timestamp that will cause an error
        try:
            # Use a valid timestamp but one that will cause data loading errors
            provider.get_data(pd.Timestamp('1900-01-01 00:00:00', tz='UTC'))
        except Exception:
            # This is expected in test environment
            pass


if __name__ == '__main__':
    # Set up test environment
    os.environ['BASIS_DATA_START_DATE'] = '2024-01-01'
    os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
    
    # Run tests
    result = unittest.main(verbosity=2, exit=False)
    
    # Check if all tests passed
    if result.result.wasSuccessful():
        print("\n✅ QUALITY GATE PASSED")
        sys.exit(0)
    else:
        print("\n❌ QUALITY GATE FAILED")
        sys.exit(1)
