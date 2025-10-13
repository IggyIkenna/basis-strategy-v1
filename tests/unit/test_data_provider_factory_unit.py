"""
Unit tests for Data Provider Factory.

Tests data provider factory pattern and provider creation logic in isolation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Mock the imports to avoid environment dependencies
from unittest.mock import Mock

# Mock the data provider classes
class MockBaseDataProvider:
    def __init__(self, data_dir: str, mode: str = 'backtest'):
        self.data_dir = data_dir
        self.mode = mode
        self.initialized = False
    
    def initialize(self) -> bool:
        self.initialized = True
        return True
    
    def get_market_data_snapshot(self, timestamp):
        return {'btc_price': 50000.0, 'eth_price': 3000.0}

class MockHistoricalDataProvider(MockBaseDataProvider):
    def __init__(self, data_dir: str, mode: str = 'backtest'):
        super().__init__(data_dir, mode)
        self.provider_type = 'historical'

class MockLiveDataProvider(MockBaseDataProvider):
    def __init__(self, data_dir: str, mode: str = 'live'):
        super().__init__(data_dir, mode)
        self.provider_type = 'live'

class MockBTCBasisDataProvider(MockBaseDataProvider):
    def __init__(self, data_dir: str, mode: str = 'backtest'):
        super().__init__(data_dir, mode)
        self.provider_type = 'btc_basis'

class MockETHBasisDataProvider(MockBaseDataProvider):
    def __init__(self, data_dir: str, mode: str = 'backtest'):
        super().__init__(data_dir, mode)
        self.provider_type = 'eth_basis'

class MockPureLendingDataProvider(MockBaseDataProvider):
    def __init__(self, data_dir: str, mode: str = 'backtest'):
        super().__init__(data_dir, mode)
        self.provider_type = 'pure_lending'

class MockETHLeveragedDataProvider(MockBaseDataProvider):
    def __init__(self, data_dir: str, mode: str = 'backtest'):
        super().__init__(data_dir, mode)
        self.provider_type = 'eth_leveraged'

class MockETHStakingOnlyDataProvider(MockBaseDataProvider):
    def __init__(self, data_dir: str, mode: str = 'backtest'):
        super().__init__(data_dir, mode)
        self.provider_type = 'eth_staking_only'

class MockUSDTMarketNeutralDataProvider(MockBaseDataProvider):
    def __init__(self, data_dir: str, mode: str = 'backtest'):
        super().__init__(data_dir, mode)
        self.provider_type = 'usdt_market_neutral'

class MockUSDTMarketNeutralNoLeverageDataProvider(MockBaseDataProvider):
    def __init__(self, data_dir: str, mode: str = 'backtest'):
        super().__init__(data_dir, mode)
        self.provider_type = 'usdt_market_neutral_no_leverage'

class MockMLDirectionalDataProvider(MockBaseDataProvider):
    def __init__(self, data_dir: str, mode: str = 'backtest'):
        super().__init__(data_dir, mode)
        self.provider_type = 'ml_directional'

class MockConfigDrivenHistoricalDataProvider(MockBaseDataProvider):
    def __init__(self, data_dir: str, mode: str = 'backtest'):
        super().__init__(data_dir, mode)
        self.provider_type = 'config_driven_historical'

class MockDataValidator:
    def __init__(self):
        self.validated = False
    
    def validate_data(self, data_provider) -> bool:
        self.validated = True
        return True

# Mock the Data Provider Factory
class MockDataProviderFactory:
    """Factory for creating data provider instances based on mode and strategy."""
    
    # Data provider class mapping
    PROVIDER_MAP = {
        'historical': MockHistoricalDataProvider,
        'live': MockLiveDataProvider,
        'btc_basis': MockBTCBasisDataProvider,
        'eth_basis': MockETHBasisDataProvider,
        'pure_lending': MockPureLendingDataProvider,
        'eth_leveraged': MockETHLeveragedDataProvider,
        'eth_staking_only': MockETHStakingOnlyDataProvider,
        'usdt_market_neutral': MockUSDTMarketNeutralDataProvider,
        'usdt_market_neutral_no_leverage': MockUSDTMarketNeutralNoLeverageDataProvider,
        'ml_directional': MockMLDirectionalDataProvider,
        'config_driven_historical': MockConfigDrivenHistoricalDataProvider,
    }
    
    @classmethod
    def create_data_provider(
        cls,
        provider_type: str,
        data_dir: str,
        mode: str = 'backtest',
        config: Dict[str, Any] = None
    ) -> MockBaseDataProvider:
        """Create data provider instance based on type."""
        try:
            # Check if provider type is supported
            if provider_type not in cls.PROVIDER_MAP:
                raise ValueError(f"Unknown data provider type: {provider_type}")
            
            # Get provider class
            provider_class = cls.PROVIDER_MAP[provider_type]
            if provider_class is None:
                raise ValueError(f"Data provider type '{provider_type}' is not yet implemented")
            
            # Create provider instance
            provider = provider_class(data_dir=data_dir, mode=mode)
            
            # Initialize if needed
            if hasattr(provider, 'initialize'):
                provider.initialize()
            
            return provider
            
        except Exception as e:
            raise ValueError(f"Failed to create data provider: {str(e)}")
    
    @classmethod
    def get_supported_provider_types(cls) -> list:
        """Get list of supported data provider types."""
        return [provider_type for provider_type, provider_class in cls.PROVIDER_MAP.items() 
                if provider_class is not None]
    
    @classmethod
    def is_provider_type_supported(cls, provider_type: str) -> bool:
        """Check if data provider type is supported."""
        return provider_type in cls.PROVIDER_MAP and cls.PROVIDER_MAP[provider_type] is not None
    
    @classmethod
    def register_provider_type(cls, provider_type: str, provider_class: type):
        """Register a new data provider class."""
        if not issubclass(provider_class, MockBaseDataProvider):
            raise ValueError(f"Provider class must inherit from MockBaseDataProvider")
        
        cls.PROVIDER_MAP[provider_type] = provider_class


class TestDataProviderFactory:
    """Test data provider factory functionality."""

    @pytest.fixture
    def mock_data_dir(self, tmp_path):
        """Create mock data directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        return str(data_dir)

    def test_create_historical_data_provider(self, mock_data_dir):
        """Test creating historical data provider."""
        provider = MockDataProviderFactory.create_data_provider(
            provider_type='historical',
            data_dir=mock_data_dir,
            mode='backtest'
        )
        
        assert isinstance(provider, MockHistoricalDataProvider)
        assert provider.provider_type == 'historical'
        assert provider.data_dir == mock_data_dir
        assert provider.mode == 'backtest'
        assert provider.initialized is True

    def test_create_live_data_provider(self, mock_data_dir):
        """Test creating live data provider."""
        provider = MockDataProviderFactory.create_data_provider(
            provider_type='live',
            data_dir=mock_data_dir,
            mode='live'
        )
        
        assert isinstance(provider, MockLiveDataProvider)
        assert provider.provider_type == 'live'
        assert provider.data_dir == mock_data_dir
        assert provider.mode == 'live'
        assert provider.initialized is True

    def test_create_btc_basis_data_provider(self, mock_data_dir):
        """Test creating BTC basis data provider."""
        provider = MockDataProviderFactory.create_data_provider(
            provider_type='btc_basis',
            data_dir=mock_data_dir,
            mode='backtest'
        )
        
        assert isinstance(provider, MockBTCBasisDataProvider)
        assert provider.provider_type == 'btc_basis'
        assert provider.data_dir == mock_data_dir
        assert provider.mode == 'backtest'

    def test_create_eth_basis_data_provider(self, mock_data_dir):
        """Test creating ETH basis data provider."""
        provider = MockDataProviderFactory.create_data_provider(
            provider_type='eth_basis',
            data_dir=mock_data_dir,
            mode='backtest'
        )
        
        assert isinstance(provider, MockETHBasisDataProvider)
        assert provider.provider_type == 'eth_basis'
        assert provider.data_dir == mock_data_dir
        assert provider.mode == 'backtest'

    def test_create_pure_lending_data_provider(self, mock_data_dir):
        """Test creating pure lending data provider."""
        provider = MockDataProviderFactory.create_data_provider(
            provider_type='pure_lending',
            data_dir=mock_data_dir,
            mode='backtest'
        )
        
        assert isinstance(provider, MockPureLendingDataProvider)
        assert provider.provider_type == 'pure_lending'
        assert provider.data_dir == mock_data_dir
        assert provider.mode == 'backtest'

    def test_create_eth_leveraged_data_provider(self, mock_data_dir):
        """Test creating ETH leveraged data provider."""
        provider = MockDataProviderFactory.create_data_provider(
            provider_type='eth_leveraged',
            data_dir=mock_data_dir,
            mode='backtest'
        )
        
        assert isinstance(provider, MockETHLeveragedDataProvider)
        assert provider.provider_type == 'eth_leveraged'
        assert provider.data_dir == mock_data_dir
        assert provider.mode == 'backtest'

    def test_create_eth_staking_only_data_provider(self, mock_data_dir):
        """Test creating ETH staking only data provider."""
        provider = MockDataProviderFactory.create_data_provider(
            provider_type='eth_staking_only',
            data_dir=mock_data_dir,
            mode='backtest'
        )
        
        assert isinstance(provider, MockETHStakingOnlyDataProvider)
        assert provider.provider_type == 'eth_staking_only'
        assert provider.data_dir == mock_data_dir
        assert provider.mode == 'backtest'

    def test_create_usdt_market_neutral_data_provider(self, mock_data_dir):
        """Test creating USDT market neutral data provider."""
        provider = MockDataProviderFactory.create_data_provider(
            provider_type='usdt_market_neutral',
            data_dir=mock_data_dir,
            mode='backtest'
        )
        
        assert isinstance(provider, MockUSDTMarketNeutralDataProvider)
        assert provider.provider_type == 'usdt_market_neutral'
        assert provider.data_dir == mock_data_dir
        assert provider.mode == 'backtest'

    def test_create_usdt_market_neutral_no_leverage_data_provider(self, mock_data_dir):
        """Test creating USDT market neutral no leverage data provider."""
        provider = MockDataProviderFactory.create_data_provider(
            provider_type='usdt_market_neutral_no_leverage',
            data_dir=mock_data_dir,
            mode='backtest'
        )
        
        assert isinstance(provider, MockUSDTMarketNeutralNoLeverageDataProvider)
        assert provider.provider_type == 'usdt_market_neutral_no_leverage'
        assert provider.data_dir == mock_data_dir
        assert provider.mode == 'backtest'

    def test_create_ml_directional_data_provider(self, mock_data_dir):
        """Test creating ML directional data provider."""
        provider = MockDataProviderFactory.create_data_provider(
            provider_type='ml_directional',
            data_dir=mock_data_dir,
            mode='backtest'
        )
        
        assert isinstance(provider, MockMLDirectionalDataProvider)
        assert provider.provider_type == 'ml_directional'
        assert provider.data_dir == mock_data_dir
        assert provider.mode == 'backtest'

    def test_create_config_driven_historical_data_provider(self, mock_data_dir):
        """Test creating config driven historical data provider."""
        provider = MockDataProviderFactory.create_data_provider(
            provider_type='config_driven_historical',
            data_dir=mock_data_dir,
            mode='backtest'
        )
        
        assert isinstance(provider, MockConfigDrivenHistoricalDataProvider)
        assert provider.provider_type == 'config_driven_historical'
        assert provider.data_dir == mock_data_dir
        assert provider.mode == 'backtest'

    def test_create_unknown_provider_type_fails(self, mock_data_dir):
        """Test that unknown provider types fail."""
        with pytest.raises(ValueError, match="Unknown data provider type"):
            MockDataProviderFactory.create_data_provider(
                provider_type='unknown_provider',
                data_dir=mock_data_dir,
                mode='backtest'
            )

    def test_get_supported_provider_types(self):
        """Test getting list of supported provider types."""
        supported_types = MockDataProviderFactory.get_supported_provider_types()
        
        expected_types = [
            'historical', 'live', 'btc_basis', 'eth_basis', 'pure_lending',
            'eth_leveraged', 'eth_staking_only', 'usdt_market_neutral',
            'usdt_market_neutral_no_leverage', 'ml_directional',
            'config_driven_historical'
        ]
        
        assert len(supported_types) == len(expected_types)
        for provider_type in expected_types:
            assert provider_type in supported_types

    def test_is_provider_type_supported(self):
        """Test checking if provider types are supported."""
        # Test supported types
        assert MockDataProviderFactory.is_provider_type_supported('historical') is True
        assert MockDataProviderFactory.is_provider_type_supported('live') is True
        assert MockDataProviderFactory.is_provider_type_supported('btc_basis') is True
        assert MockDataProviderFactory.is_provider_type_supported('eth_basis') is True
        assert MockDataProviderFactory.is_provider_type_supported('pure_lending') is True
        assert MockDataProviderFactory.is_provider_type_supported('eth_leveraged') is True
        assert MockDataProviderFactory.is_provider_type_supported('eth_staking_only') is True
        assert MockDataProviderFactory.is_provider_type_supported('usdt_market_neutral') is True
        assert MockDataProviderFactory.is_provider_type_supported('usdt_market_neutral_no_leverage') is True
        assert MockDataProviderFactory.is_provider_type_supported('ml_directional') is True
        assert MockDataProviderFactory.is_provider_type_supported('config_driven_historical') is True
        
        # Test unsupported types
        assert MockDataProviderFactory.is_provider_type_supported('unknown_provider') is False
        assert MockDataProviderFactory.is_provider_type_supported('') is False
        assert MockDataProviderFactory.is_provider_type_supported(None) is False

    def test_register_provider_type_success(self):
        """Test successful provider type registration."""
        class CustomDataProvider(MockBaseDataProvider):
            def __init__(self, data_dir: str, mode: str = 'backtest'):
                super().__init__(data_dir, mode)
                self.provider_type = 'custom_provider'
        
        # Register the custom provider
        MockDataProviderFactory.register_provider_type('custom_provider', CustomDataProvider)
        
        # Verify it's now supported
        assert MockDataProviderFactory.is_provider_type_supported('custom_provider') is True
        
        # Test creating the custom provider
        provider = MockDataProviderFactory.create_data_provider(
            provider_type='custom_provider',
            data_dir='/tmp/test',
            mode='backtest'
        )
        
        assert isinstance(provider, CustomDataProvider)
        assert provider.provider_type == 'custom_provider'

    def test_register_provider_type_invalid_class_fails(self):
        """Test that registering invalid provider class fails."""
        class InvalidProvider:
            pass  # Doesn't inherit from MockBaseDataProvider
        
        with pytest.raises(ValueError, match="Provider class must inherit from MockBaseDataProvider"):
            MockDataProviderFactory.register_provider_type('invalid_provider', InvalidProvider)

    def test_provider_creation_with_different_modes(self, mock_data_dir):
        """Test provider creation with different modes."""
        # Test backtest mode
        backtest_provider = MockDataProviderFactory.create_data_provider(
            provider_type='historical',
            data_dir=mock_data_dir,
            mode='backtest'
        )
        assert backtest_provider.mode == 'backtest'
        
        # Test live mode
        live_provider = MockDataProviderFactory.create_data_provider(
            provider_type='live',
            data_dir=mock_data_dir,
            mode='live'
        )
        assert live_provider.mode == 'live'

    def test_provider_creation_with_config(self, mock_data_dir):
        """Test provider creation with configuration."""
        config = {
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'data_sources': ['binance', 'bybit']
        }
        
        provider = MockDataProviderFactory.create_data_provider(
            provider_type='historical',
            data_dir=mock_data_dir,
            mode='backtest',
            config=config
        )
        
        assert isinstance(provider, MockHistoricalDataProvider)
        assert provider.data_dir == mock_data_dir
        assert provider.mode == 'backtest'

    def test_provider_factory_singleton_behavior(self):
        """Test that provider factory behaves as a singleton-like class."""
        # All calls should return the same class methods
        assert MockDataProviderFactory.get_supported_provider_types() == MockDataProviderFactory.get_supported_provider_types()
        assert MockDataProviderFactory.is_provider_type_supported('historical') == MockDataProviderFactory.is_provider_type_supported('historical')

    def test_provider_creation_error_propagation(self, mock_data_dir):
        """Test that provider creation errors are properly propagated."""
        # Mock a provider class that raises an exception during initialization
        class FailingProvider(MockBaseDataProvider):
            def __init__(self, data_dir: str, mode: str = 'backtest'):
                raise Exception("Initialization failed")
        
        # Temporarily register the failing provider
        original_provider = MockDataProviderFactory.PROVIDER_MAP.get('historical')
        MockDataProviderFactory.PROVIDER_MAP['historical'] = FailingProvider
        
        try:
            with pytest.raises(ValueError, match="Failed to create data provider"):
                MockDataProviderFactory.create_data_provider(
                    provider_type='historical',
                    data_dir=mock_data_dir,
                    mode='backtest'
                )
        finally:
            # Restore original provider
            MockDataProviderFactory.PROVIDER_MAP['historical'] = original_provider

    def test_all_provider_types_implemented(self):
        """Test that all expected provider types are implemented."""
        expected_types = [
            'historical',
            'live',
            'btc_basis',
            'eth_basis',
            'pure_lending',
            'eth_leveraged',
            'eth_staking_only',
            'usdt_market_neutral',
            'usdt_market_neutral_no_leverage',
            'ml_directional',
            'config_driven_historical'
        ]
        
        supported_types = MockDataProviderFactory.get_supported_provider_types()
        
        for provider_type in expected_types:
            assert provider_type in supported_types, f"Provider type '{provider_type}' is not implemented"
            assert MockDataProviderFactory.is_provider_type_supported(provider_type), f"Provider type '{provider_type}' is not supported"

    def test_provider_map_consistency(self):
        """Test that provider map is consistent."""
        provider_map = MockDataProviderFactory.PROVIDER_MAP
        
        # All values should be either None or a valid provider class
        for provider_type, provider_class in provider_map.items():
            if provider_class is not None:
                assert issubclass(provider_class, MockBaseDataProvider), f"Provider class for '{provider_type}' doesn't inherit from MockBaseDataProvider"
        
        # All supported types should have non-None provider classes
        supported_types = MockDataProviderFactory.get_supported_provider_types()
        for provider_type in supported_types:
            assert provider_map[provider_type] is not None, f"Supported type '{provider_type}' has None provider class"
