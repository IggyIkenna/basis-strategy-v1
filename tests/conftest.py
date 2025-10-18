"""
Pytest configuration and fixtures for Basis Strategy v1 tests.

This file sets up common test fixtures and environment variables
required for all tests to run properly.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables for all tests."""
    # Set required environment variables for tests
    test_env_vars = {
        'BASIS_ENVIRONMENT': 'dev',
        'BASIS_DEPLOYMENT_MODE': 'local',
        'BASIS_DATA_DIR': '/tmp/basis_test_data',
        'BASIS_RESULTS_DIR': '/tmp/basis_test_results',
        'BASIS_DEBUG': 'true',
        'BASIS_LOG_LEVEL': 'DEBUG',
        'BASIS_EXECUTION_MODE': 'backtest',
        'BASIS_DATA_START_DATE': '2024-01-01',
        'BASIS_DATA_END_DATE': '2024-12-31',
        'BASIS_LIVE_TRADING__ENABLED': 'false',
        'BASIS_LIVE_TRADING__READ_ONLY': 'true',
    }
    
    # Set environment variables
    for key, value in test_env_vars.items():
        os.environ[key] = value
    
    # Create test directories
    Path(test_env_vars['BASIS_DATA_DIR']).mkdir(parents=True, exist_ok=True)
    Path(test_env_vars['BASIS_RESULTS_DIR']).mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Cleanup - remove test environment variables
    for key in test_env_vars.keys():
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    return {
        'mode': 'pure_lending_usdt',
        'share_class': 'USDT',
        'asset': 'USDT',
        'initial_capital': 100000.0,
        'max_drawdown': 0.2,
        'leverage_enabled': False,
        'venues': {
            'binance': {'enabled': True},
            'bybit': {'enabled': True}
        },
        'component_config': {
            'position_monitor': {
                'update_interval': 60,
                'max_positions': 100
            },
            'exposure_monitor': {
                'update_interval': 60,
                'max_exposures': 50
            },
            'risk_monitor': {
                'update_interval': 60,
                'max_risk_ratio': 0.8
            },
            'pnl_monitor': {
                'attribution_types': ['supply_yield', 'funding_pnl', 'delta_pnl', 'transaction_costs'],
                'reporting_currency': 'USDT',
                'reconciliation_tolerance': 0.02
            }
        }
    }


@pytest.fixture
def mock_data_provider():
    """Mock data provider for tests."""
    mock_provider = pytest.Mock()
    mock_provider.get_market_data.return_value = {
        'timestamp': '2024-01-01T00:00:00Z',
        'price': 50000.0,
        'volume': 1000.0
    }
    return mock_provider


@pytest.fixture
def mock_execution_manager():
    """Mock execution manager for tests."""
    mock_manager = pytest.Mock()
    mock_manager.execute_instruction.return_value = {
        'status': 'success',
        'order_id': 'test_order_123'
    }
    return mock_manager
