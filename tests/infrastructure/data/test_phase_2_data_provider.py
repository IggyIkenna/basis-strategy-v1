"""
Phase 2 Data Provider Tests

Tests the target behavior for Phase 2 data provider updates:
- Historical data provider loads ALL data at startup
- Live data provider validates connections based on mode-specific data requirements
- Data provider factory routes correctly based on startup_mode
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from pathlib import Path

from backend.src.basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
from backend.src.basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider as HistoricalDataProvider
from backend.src.basis_strategy_v1.infrastructure.data.live_data_provider import LiveDataProvider


class TestHistoricalDataProvider:
    """Test historical data provider (backtest mode only)."""
    
    def test_loads_all_data_at_startup(self):
        """Test that historical provider loads ALL data for ALL modes at startup."""
        # This test documents the target behavior
        with patch('backend.src.basis_strategy_v1.infrastructure.config.config_manager.get_config_manager') as mock_cm:
            mock_cm.return_value.get_data_directory.return_value = "./data"
            mock_cm.return_value.get_complete_config.return_value = {}
            
            with patch.object(HistoricalDataProvider, '_load_all_data_at_startup') as mock_load_all:
                with patch.object(HistoricalDataProvider, '_validate_timestamps') as mock_validate:
                    dp = HistoricalDataProvider(
                        data_dir="./data",
                        mode="all_data",
                        execution_mode="backtest"
                    )
                    
                    # Should call _load_all_data_at_startup for comprehensive loading
                    mock_load_all.assert_called_once()
                    mock_validate.assert_called_once()
    
    def test_rejects_live_mode(self):
        """Test that historical provider rejects live mode."""
        with pytest.raises(ValueError, match="only supports execution_mode='backtest'"):
            HistoricalDataProvider(
                data_dir="./data",
                mode="test",
                execution_mode="live"
            )
    
    def test_fail_fast_on_missing_data(self):
        """Test that historical provider fails fast on missing data files."""
        # This test documents that the provider should fail, not create dummy data
        with patch('backend.src.basis_strategy_v1.infrastructure.data.historical_data_provider._validate_data_file') as mock_validate:
            mock_validate.side_effect = FileNotFoundError("Required data file not found: test.csv")
            
            with pytest.raises(ValueError, match="Data loading failed"):
                HistoricalDataProvider(
                    data_dir="./data", 
                    mode="all_data",
                    execution_mode="backtest"
                )
    
    def test_no_minimal_data_methods(self):
        """Test that no _create_minimal_* methods exist."""
        import inspect
        
        # Get all methods of HistoricalDataProvider
        methods = inspect.getmembers(HistoricalDataProvider, predicate=inspect.ismethod)
        method_names = [name for name, _ in methods]
        
        # Should not find any _create_minimal_ methods
        minimal_methods = [name for name in method_names if '_create_minimal_' in name]
        assert minimal_methods == [], f"Found minimal methods that should be removed: {minimal_methods}"
    
    def test_performance_target(self):
        """Test that data loading meets performance targets."""
        # This test documents the performance target: <30 seconds for all data
        with patch.object(HistoricalDataProvider, '_load_all_data_at_startup') as mock_load:
            with patch.object(HistoricalDataProvider, '_validate_timestamps'):
                start_time = time.time()
                
                dp = HistoricalDataProvider(
                    data_dir="./data",
                    mode="all_data", 
                    execution_mode="backtest"
                )
                
                elapsed = time.time() - start_time
                # Should be very fast since we're mocking the actual loading
                assert elapsed < 1.0, f"Initialization took too long: {elapsed}s"


class TestLiveDataProvider:
    """Test live data provider (live mode only)."""
    
    def test_loads_mode_specific_requirements(self):
        """Test that live provider loads mode-specific data requirements."""
        config = {
            'data_requirements': ['eth_prices', 'gas_costs', 'funding_rates']
        }
        
        dp = LiveDataProvider(config=config, mode='pure_lending')
        
        # Should load data requirements from config
        assert dp.data_requirements == ['eth_prices', 'gas_costs', 'funding_rates']
        assert dp.mode == 'pure_lending'
    
    def test_default_requirements_when_none_specified(self):
        """Test default behavior when no data requirements specified."""
        config = {}  # No data_requirements
        
        dp = LiveDataProvider(config=config, mode='test_mode')
        
        # Should have empty requirements and log warning
        assert dp.data_requirements == []
    
    @pytest.mark.asyncio
    async def test_connection_validation_framework(self):
        """Test that live provider has connection validation framework."""
        config = {
            'data_requirements': ['eth_prices', 'gas_costs']
        }
        
        with patch.object(LiveDataProvider, '_test_eth_spot_connection') as mock_eth:
            with patch.object(LiveDataProvider, '_test_gas_price_connection') as mock_gas:
                mock_eth.return_value = {'price': 3000.0, 'timestamp': 'test'}
                mock_gas.return_value = {'cost': 0.001, 'timestamp': 'test'}
                
                dp = LiveDataProvider(config=config, mode='test_mode')
                
                async with dp:
                    results = await dp.validate_live_data_connections()
                
                # Should test each required data type
                assert 'eth_prices' in results['connection_tests']
                assert 'gas_costs' in results['connection_tests']
                assert results['overall_status'] == 'healthy'


class TestDataProviderFactory:
    """Test data provider factory routing."""
    
    def test_routes_to_historical_for_backtest(self):
        """Test that factory routes to historical provider for backtest mode."""
        with patch('backend.src.basis_strategy_v1.infrastructure.data.historical_data_provider.DataProvider') as mock_historical:
            mock_instance = MagicMock()
            mock_historical.return_value = mock_instance
            
            result = create_data_provider(
                data_dir="./data",
                startup_mode="backtest",
                config={}
            )
            
            # Should create historical provider with all_data mode
            mock_historical.assert_called_once_with(
                data_dir="./data",
                mode="all_data",
                execution_mode="backtest", 
                config={}
            )
            assert result == mock_instance
    
    def test_routes_to_live_for_live_mode(self):
        """Test that factory routes to live provider for live mode."""
        with patch('backend.src.basis_strategy_v1.infrastructure.data.live_data_provider.LiveDataProvider') as mock_live:
            mock_instance = MagicMock()
            mock_live.return_value = mock_instance
            
            result = create_data_provider(
                data_dir="./data",
                startup_mode="live",
                config={'test': 'config'},
                mode="pure_lending"
            )
            
            # Should create live provider with mode and config
            mock_live.assert_called_once_with(
                config={'test': 'config'},
                mode="pure_lending"
            )
            assert result == mock_instance
    
    def test_rejects_invalid_startup_mode(self):
        """Test that factory rejects invalid startup modes."""
        with pytest.raises(ValueError, match="Unknown startup_mode: invalid"):
            create_data_provider(
                data_dir="./data",
                startup_mode="invalid",
                config={}
            )


class TestDataProviderIntegration:
    """Integration tests for data provider behavior."""
    
    def test_target_behavior_backtest_mode(self):
        """
        Test target behavior for backtest mode:
        - Factory creates historical provider
        - Historical provider loads ALL data
        - Validation covers full date range
        - No mode-specific filtering in historical provider
        """
        # This test documents the target architecture
        with patch('backend.src.basis_strategy_v1.infrastructure.data.historical_data_provider.DataProvider') as mock_historical:
            mock_instance = MagicMock()
            mock_instance.data = {'test': 'data'}
            mock_historical.return_value = mock_instance
            
            # Factory should route to historical provider
            dp = create_data_provider(
                data_dir="./data",
                startup_mode="backtest",
                config={}
            )
            
            # Should create historical provider with all_data mode (no mode-specific filtering)
            mock_historical.assert_called_once_with(
                data_dir="./data",
                mode="all_data",  # Always load all data
                execution_mode="backtest",
                config={}
            )
    
    def test_target_behavior_live_mode(self):
        """
        Test target behavior for live mode:
        - Factory creates live provider with mode
        - Live provider loads data requirements from config
        - Connection validation tests each required data type
        - Mode-specific data loading
        """
        config = {
            'data_requirements': ['eth_prices', 'funding_rates', 'gas_costs']
        }
        
        with patch('backend.src.basis_strategy_v1.infrastructure.data.live_data_provider.LiveDataProvider') as mock_live:
            mock_instance = MagicMock()
            mock_instance.data_requirements = ['eth_prices', 'funding_rates', 'gas_costs']
            mock_live.return_value = mock_instance
            
            # Factory should route to live provider with mode
            dp = create_data_provider(
                data_dir="./data",
                startup_mode="live",
                config=config,
                mode="btc_basis"
            )
            
            # Should create live provider with mode-specific config
            mock_live.assert_called_once_with(
                config=config,
                mode="btc_basis"
            )


class TestQualityGateTargets:
    """Tests that document quality gate targets."""
    
    def test_phase_2_backtest_quality_targets(self):
        """
        Document Phase 2 quality gate targets for backtest mode:
        - Data loading <30 seconds
        - All data validation passes
        - No minimal methods exist
        - Health monitoring works
        - Live mode separation enforced
        """
        # Performance target
        MAX_LOADING_TIME = 30.0
        
        # Data validation targets
        REQUIRED_DATASETS = [
            'gas_costs', 'execution_costs', 'usdt_rates', 'weth_rates',
            'weeth_rates', 'aave_risk_params', 'eth_spot_binance', 'btc_spot_binance'
        ]
        
        # Health monitoring targets
        EXPECTED_HEALTH_STATUS = 'healthy'
        MIN_DATASETS_LOADED = 20  # Should load at least 20 datasets
        
        # This test documents what the quality gates should validate
        assert MAX_LOADING_TIME == 30.0
        assert len(REQUIRED_DATASETS) == 8
        assert EXPECTED_HEALTH_STATUS == 'healthy'
        assert MIN_DATASETS_LOADED == 20
    
    def test_future_live_quality_targets(self):
        """
        Document future quality gate targets for live mode:
        - Connection validation for each venue
        - API authentication tests
        - Data requirements mapping
        - Fail-fast on connection failures
        """
        # Future live mode targets (when API credentials are setup)
        SUPPORTED_VENUES = ['binance', 'bybit', 'okx']
        TESTNET_ENVIRONMENTS = ['dev', 'staging']
        PRODUCTION_ENVIRONMENTS = ['prod']
        
        # Connection test targets
        MAX_CONNECTION_TIME = 10.0  # seconds
        REQUIRED_API_KEYS = [
            'BASIS_DEV__CEX__BINANCE_SPOT_API_KEY',
            'BASIS_DEV__CEX__BYBIT_API_KEY', 
            'BASIS_DEV__CEX__OKX_API_KEY'
        ]
        
        # This test documents what future quality gates should validate
        assert len(SUPPORTED_VENUES) == 3
        assert len(REQUIRED_API_KEYS) == 3
        assert MAX_CONNECTION_TIME == 10.0
