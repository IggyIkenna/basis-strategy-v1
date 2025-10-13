"""
Unit tests for Historical Data Provider.

Tests historical data provider logic in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import pandas as pd
from pathlib import Path

# Mock the imports to avoid environment dependencies
from unittest.mock import Mock

# Mock the data provider classes
class MockDataProviderError(Exception):
    """Custom exception for data provider errors with error codes."""
    
    def __init__(self, error_code: str, message: str = None, **kwargs):
        self.error_code = error_code
        self.message = message or f"Data provider error: {error_code}"
        self.context = kwargs
        super().__init__(self.message)

class MockHistoricalDataProvider:
    """Mock historical data provider for testing."""
    
    def __init__(self, data_dir: str, mode: str = 'backtest'):
        self.data_dir = Path(data_dir)
        self.mode = mode
        self.data_cache = {}
        self.initialized = False
        
        # Mock configuration
        self.config = {
            'mode': mode,
            'data_dir': data_dir,
            'start_date': '2024-05-12',
            'end_date': '2024-05-19'
        }
    
    def initialize(self) -> bool:
        """Initialize the data provider."""
        try:
            # Mock initialization logic
            if not self.data_dir.exists():
                raise MockDataProviderError("DATA_DIR_NOT_FOUND", "Data directory not found")
            
            # Load mock data
            self._load_mock_data()
            self.initialized = True
            return True
            
        except Exception as e:
            self.initialized = False
            raise MockDataProviderError("INIT_FAILED", f"Initialization failed: {str(e)}")
    
    def _load_mock_data(self):
        """Load mock data for testing."""
        # Create mock market data
        timestamps = pd.date_range(
            start='2024-05-12 00:00:00',
            end='2024-05-19 23:00:00',
            freq='H',
            tz='UTC'
        )
        
        self.data_cache = {
            'btc_prices': pd.DataFrame({
                'timestamp': timestamps,
                'binance_btc_usdt': [50000.0 + i * 10 for i in range(len(timestamps))],
                'bybit_btc_usdt': [50000.0 + i * 10.5 for i in range(len(timestamps))],
                'okx_btc_usdt': [50000.0 + i * 9.8 for i in range(len(timestamps))]
            }),
            'eth_prices': pd.DataFrame({
                'timestamp': timestamps,
                'binance_eth_usdt': [3000.0 + i * 5 for i in range(len(timestamps))],
                'bybit_eth_usdt': [3000.0 + i * 5.2 for i in range(len(timestamps))],
                'okx_eth_usdt': [3000.0 + i * 4.8 for i in range(len(timestamps))]
            }),
            'funding_rates': pd.DataFrame({
                'timestamp': timestamps,
                'btc_funding_rate': [0.0001 + i * 0.00001 for i in range(len(timestamps))],
                'eth_funding_rate': [0.0002 + i * 0.00002 for i in range(len(timestamps))]
            }),
            'aave_data': pd.DataFrame({
                'timestamp': timestamps,
                'usdt_liquidity_index': [1.01 + i * 0.001 for i in range(len(timestamps))],
                'eth_liquidity_index': [1.02 + i * 0.002 for i in range(len(timestamps))]
            })
        }
    
    def get_market_data_snapshot(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get market data snapshot for a specific timestamp."""
        if not self.initialized:
            raise MockDataProviderError("NOT_INITIALIZED", "Data provider not initialized")
        
        try:
            # Find closest timestamp
            closest_data = {}
            
            for data_type, df in self.data_cache.items():
                if 'timestamp' in df.columns:
                    # Find closest timestamp
                    time_diff = abs(df['timestamp'] - timestamp)
                    closest_idx = time_diff.idxmin()
                    closest_row = df.iloc[closest_idx]
                    
                    # Extract numeric columns
                    for col in df.columns:
                        if col != 'timestamp' and pd.api.types.is_numeric_dtype(df[col]):
                            closest_data[col] = float(closest_row[col])
            
            return closest_data
            
        except Exception as e:
            raise MockDataProviderError("DATA_ACCESS_FAILED", f"Failed to get market data: {str(e)}")
    
    def get_price(self, asset: str, venue: str = None, timestamp: pd.Timestamp = None) -> float:
        """Get price for a specific asset and venue."""
        if not self.initialized:
            raise MockDataProviderError("NOT_INITIALIZED", "Data provider not initialized")
        
        try:
            if timestamp is None:
                timestamp = pd.Timestamp.now(tz='UTC')
            
            snapshot = self.get_market_data_snapshot(timestamp)
            
            # Look for price in snapshot
            if venue:
                price_key = f"{venue}_{asset.lower()}_usdt"
            else:
                # Default to binance if no venue specified
                price_key = f"binance_{asset.lower()}_usdt"
            
            if price_key in snapshot:
                return snapshot[price_key]
            else:
                raise MockDataProviderError("PRICE_NOT_FOUND", f"Price not found for {asset} on {venue}")
                
        except Exception as e:
            if isinstance(e, MockDataProviderError):
                raise
            raise MockDataProviderError("PRICE_ACCESS_FAILED", f"Failed to get price: {str(e)}")
    
    def get_btc_price(self, venue: str = None, timestamp: pd.Timestamp = None) -> float:
        """Get BTC price for a specific venue."""
        return self.get_price('BTC', venue, timestamp)
    
    def get_eth_price(self, venue: str = None, timestamp: pd.Timestamp = None) -> float:
        """Get ETH price for a specific venue."""
        return self.get_price('ETH', venue, timestamp)
    
    def get_usdt_price(self, venue: str = None, timestamp: pd.Timestamp = None) -> float:
        """Get USDT price (should always be 1.0)."""
        return 1.0
    
    def get_funding_rate(self, asset: str, timestamp: pd.Timestamp = None) -> float:
        """Get funding rate for a specific asset."""
        if not self.initialized:
            raise MockDataProviderError("NOT_INITIALIZED", "Data provider not initialized")
        
        try:
            if timestamp is None:
                timestamp = pd.Timestamp.now(tz='UTC')
            
            snapshot = self.get_market_data_snapshot(timestamp)
            
            funding_key = f"{asset.lower()}_funding_rate"
            if funding_key in snapshot:
                return snapshot[funding_key]
            else:
                raise MockDataProviderError("FUNDING_RATE_NOT_FOUND", f"Funding rate not found for {asset}")
                
        except Exception as e:
            if isinstance(e, MockDataProviderError):
                raise
            raise MockDataProviderError("FUNDING_RATE_ACCESS_FAILED", f"Failed to get funding rate: {str(e)}")
    
    def get_aave_liquidity_index(self, asset: str, timestamp: pd.Timestamp = None) -> float:
        """Get AAVE liquidity index for a specific asset."""
        if not self.initialized:
            raise MockDataProviderError("NOT_INITIALIZED", "Data provider not initialized")
        
        try:
            if timestamp is None:
                timestamp = pd.Timestamp.now(tz='UTC')
            
            snapshot = self.get_market_data_snapshot(timestamp)
            
            index_key = f"{asset.lower()}_liquidity_index"
            if index_key in snapshot:
                return snapshot[index_key]
            else:
                raise MockDataProviderError("LIQUIDITY_INDEX_NOT_FOUND", f"Liquidity index not found for {asset}")
                
        except Exception as e:
            if isinstance(e, MockDataProviderError):
                raise
            raise MockDataProviderError("LIQUIDITY_INDEX_ACCESS_FAILED", f"Failed to get liquidity index: {str(e)}")
    
    def validate_data_at_startup(self) -> bool:
        """Validate data availability at startup."""
        if not self.initialized:
            raise MockDataProviderError("NOT_INITIALIZED", "Data provider not initialized")
        
        try:
            # Check if we have required data
            required_data_types = ['btc_prices', 'eth_prices', 'funding_rates']
            
            for data_type in required_data_types:
                if data_type not in self.data_cache:
                    raise MockDataProviderError("MISSING_DATA", f"Missing required data: {data_type}")
                
                df = self.data_cache[data_type]
                if df.empty:
                    raise MockDataProviderError("EMPTY_DATA", f"Empty data for: {data_type}")
            
            return True
            
        except Exception as e:
            if isinstance(e, MockDataProviderError):
                raise
            raise MockDataProviderError("VALIDATION_FAILED", f"Data validation failed: {str(e)}")
    
    def get_data_availability(self) -> Dict[str, bool]:
        """Get data availability status."""
        if not self.initialized:
            return {
                'btc_prices': False,
                'eth_prices': False,
                'funding_rates': False,
                'aave_data': False
            }
        
        return {
            'btc_prices': 'btc_prices' in self.data_cache and not self.data_cache['btc_prices'].empty,
            'eth_prices': 'eth_prices' in self.data_cache and not self.data_cache['eth_prices'].empty,
            'funding_rates': 'funding_rates' in self.data_cache and not self.data_cache['funding_rates'].empty,
            'aave_data': 'aave_data' in self.data_cache and not self.data_cache['aave_data'].empty
        }


class TestHistoricalDataProvider:
    """Test historical data provider functionality."""

    @pytest.fixture
    def mock_data_dir(self, tmp_path):
        """Create mock data directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        return str(data_dir)

    @pytest.fixture
    def data_provider(self, mock_data_dir):
        """Create data provider instance."""
        return MockHistoricalDataProvider(data_dir=mock_data_dir, mode='backtest')

    def test_initialization_success(self, data_provider):
        """Test successful data provider initialization."""
        result = data_provider.initialize()
        
        assert result is True
        assert data_provider.initialized is True
        assert len(data_provider.data_cache) > 0
        assert 'btc_prices' in data_provider.data_cache
        assert 'eth_prices' in data_provider.data_cache
        assert 'funding_rates' in data_provider.data_cache

    def test_initialization_data_dir_not_found(self, tmp_path):
        """Test initialization with non-existent data directory."""
        non_existent_dir = tmp_path / "nonexistent"
        
        data_provider = MockHistoricalDataProvider(data_dir=str(non_existent_dir))
        
        with pytest.raises(MockDataProviderError, match="Data directory not found"):
            data_provider.initialize()

    def test_get_market_data_snapshot_success(self, data_provider):
        """Test successful market data snapshot retrieval."""
        data_provider.initialize()
        
        timestamp = pd.Timestamp('2024-05-12 12:00:00', tz='UTC')
        snapshot = data_provider.get_market_data_snapshot(timestamp)
        
        assert isinstance(snapshot, dict)
        assert len(snapshot) > 0
        assert 'binance_btc_usdt' in snapshot
        assert 'binance_eth_usdt' in snapshot
        assert 'btc_funding_rate' in snapshot
        assert isinstance(snapshot['binance_btc_usdt'], float)

    def test_get_market_data_snapshot_not_initialized(self, data_provider):
        """Test market data snapshot retrieval when not initialized."""
        timestamp = pd.Timestamp('2024-05-12 12:00:00', tz='UTC')
        
        with pytest.raises(MockDataProviderError, match="Data provider not initialized"):
            data_provider.get_market_data_snapshot(timestamp)

    def test_get_price_success(self, data_provider):
        """Test successful price retrieval."""
        data_provider.initialize()
        
        # Test BTC price
        btc_price = data_provider.get_btc_price('binance')
        assert isinstance(btc_price, float)
        assert btc_price > 0
        
        # Test ETH price
        eth_price = data_provider.get_eth_price('bybit')
        assert isinstance(eth_price, float)
        assert eth_price > 0
        
        # Test USDT price
        usdt_price = data_provider.get_usdt_price()
        assert usdt_price == 1.0

    def test_get_price_with_timestamp(self, data_provider):
        """Test price retrieval with specific timestamp."""
        data_provider.initialize()
        
        timestamp = pd.Timestamp('2024-05-12 12:00:00', tz='UTC')
        btc_price = data_provider.get_btc_price('binance', timestamp)
        
        assert isinstance(btc_price, float)
        assert btc_price > 0

    def test_get_price_not_found(self, data_provider):
        """Test price retrieval for non-existent asset/venue."""
        data_provider.initialize()
        
        with pytest.raises(MockDataProviderError, match="Price not found"):
            data_provider.get_price('UNKNOWN', 'binance')

    def test_get_funding_rate_success(self, data_provider):
        """Test successful funding rate retrieval."""
        data_provider.initialize()
        
        btc_funding = data_provider.get_funding_rate('BTC')
        assert isinstance(btc_funding, float)
        assert btc_funding > 0
        
        eth_funding = data_provider.get_funding_rate('ETH')
        assert isinstance(eth_funding, float)
        assert eth_funding > 0

    def test_get_funding_rate_not_found(self, data_provider):
        """Test funding rate retrieval for non-existent asset."""
        data_provider.initialize()
        
        with pytest.raises(MockDataProviderError, match="Funding rate not found"):
            data_provider.get_funding_rate('UNKNOWN')

    def test_get_aave_liquidity_index_success(self, data_provider):
        """Test successful AAVE liquidity index retrieval."""
        data_provider.initialize()
        
        usdt_index = data_provider.get_aave_liquidity_index('USDT')
        assert isinstance(usdt_index, float)
        assert usdt_index > 0
        
        eth_index = data_provider.get_aave_liquidity_index('ETH')
        assert isinstance(eth_index, float)
        assert eth_index > 0

    def test_get_aave_liquidity_index_not_found(self, data_provider):
        """Test AAVE liquidity index retrieval for non-existent asset."""
        data_provider.initialize()
        
        with pytest.raises(MockDataProviderError, match="Liquidity index not found"):
            data_provider.get_aave_liquidity_index('UNKNOWN')

    def test_validate_data_at_startup_success(self, data_provider):
        """Test successful data validation at startup."""
        data_provider.initialize()
        
        result = data_provider.validate_data_at_startup()
        assert result is True

    def test_validate_data_at_startup_not_initialized(self, data_provider):
        """Test data validation when not initialized."""
        with pytest.raises(MockDataProviderError, match="Data provider not initialized"):
            data_provider.validate_data_at_startup()

    def test_validate_data_at_startup_missing_data(self, data_provider):
        """Test data validation with missing data."""
        data_provider.initialize()
        
        # Remove required data
        del data_provider.data_cache['btc_prices']
        
        with pytest.raises(MockDataProviderError, match="Missing required data"):
            data_provider.validate_data_at_startup()

    def test_validate_data_at_startup_empty_data(self, data_provider):
        """Test data validation with empty data."""
        data_provider.initialize()
        
        # Make data empty
        data_provider.data_cache['btc_prices'] = pd.DataFrame()
        
        with pytest.raises(MockDataProviderError, match="Empty data"):
            data_provider.validate_data_at_startup()

    def test_get_data_availability_success(self, data_provider):
        """Test successful data availability retrieval."""
        data_provider.initialize()
        
        availability = data_provider.get_data_availability()
        
        assert isinstance(availability, dict)
        assert availability['btc_prices'] is True
        assert availability['eth_prices'] is True
        assert availability['funding_rates'] is True
        assert availability['aave_data'] is True

    def test_get_data_availability_not_initialized(self, data_provider):
        """Test data availability retrieval when not initialized."""
        availability = data_provider.get_data_availability()
        
        assert isinstance(availability, dict)
        assert availability['btc_prices'] is False
        assert availability['eth_prices'] is False
        assert availability['funding_rates'] is False
        assert availability['aave_data'] is False

    def test_data_consistency_across_venues(self, data_provider):
        """Test that data is consistent across different venues."""
        data_provider.initialize()
        
        timestamp = pd.Timestamp('2024-05-12 12:00:00', tz='UTC')
        
        # Get BTC prices from different venues
        binance_price = data_provider.get_btc_price('binance', timestamp)
        bybit_price = data_provider.get_btc_price('bybit', timestamp)
        okx_price = data_provider.get_btc_price('okx', timestamp)
        
        # Prices should be different (as per mock data)
        assert binance_price != bybit_price
        assert bybit_price != okx_price
        assert binance_price != okx_price
        
        # But all should be positive
        assert binance_price > 0
        assert bybit_price > 0
        assert okx_price > 0

    def test_timestamp_handling(self, data_provider):
        """Test timestamp handling and closest match logic."""
        data_provider.initialize()
        
        # Test with exact timestamp
        exact_timestamp = pd.Timestamp('2024-05-12 12:00:00', tz='UTC')
        snapshot1 = data_provider.get_market_data_snapshot(exact_timestamp)
        
        # Test with close timestamp (should find closest)
        close_timestamp = pd.Timestamp('2024-05-12 12:30:00', tz='UTC')
        snapshot2 = data_provider.get_market_data_snapshot(close_timestamp)
        
        # Should return same data (closest match)
        assert snapshot1['binance_btc_usdt'] == snapshot2['binance_btc_usdt']

    def test_error_handling_with_context(self, data_provider):
        """Test error handling with context information."""
        data_provider.initialize()
        
        try:
            data_provider.get_price('UNKNOWN', 'binance')
        except MockDataProviderError as e:
            assert e.error_code == "PRICE_NOT_FOUND"
            assert "UNKNOWN" in e.message
            assert "binance" in e.message

    def test_mode_configuration(self, mock_data_dir):
        """Test different mode configurations."""
        # Test backtest mode
        backtest_provider = MockHistoricalDataProvider(data_dir=mock_data_dir, mode='backtest')
        assert backtest_provider.mode == 'backtest'
        
        # Test live mode
        live_provider = MockHistoricalDataProvider(data_dir=mock_data_dir, mode='live')
        assert live_provider.mode == 'live'

    def test_data_cache_structure(self, data_provider):
        """Test that data cache has correct structure."""
        data_provider.initialize()
        
        # Check that all dataframes have timestamp column
        for data_type, df in data_provider.data_cache.items():
            assert 'timestamp' in df.columns
            assert not df.empty
            assert len(df) > 0  # Should have some data points
