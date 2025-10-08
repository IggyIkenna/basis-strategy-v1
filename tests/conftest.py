"""
Shared fixtures and test configuration for all tests.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import pandas as pd
from datetime import datetime, timezone

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

# Mock infrastructure will be created inline for now


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis_mock = Mock()
    redis_mock.publish = Mock()
    redis_mock.subscribe = Mock()
    redis_mock.get = Mock(return_value=None)
    redis_mock.set = Mock()
    redis_mock.ping = Mock(return_value=True)
    return redis_mock


@pytest.fixture
def mock_data_provider():
    """Create mock data provider."""
    provider = Mock()
    provider.get_spot_price = Mock(return_value=3305.20)
    provider.get_futures_price = Mock(return_value=3306.15)
    provider.get_oracle_price = Mock(return_value=1.0254)
    provider.get_aave_index = Mock(return_value=1.0234)
    provider.get_gas_cost = Mock(return_value=0.001875)
    provider.get_execution_cost = Mock(return_value=5.0)
    provider.get_market_data_snapshot = Mock(return_value={
        'timestamp': pd.Timestamp('2024-05-12 12:00:00', tz='UTC'),
        'eth_usd_price': 3305.20,
        'weeth_supply_apy': 0.0374,
        'weeth_liquidity_index': 1.0234,
        'gas_price_gwei': 20.0
    })
    return provider


@pytest.fixture
def mock_position_monitor():
    """Create mock position monitor."""
    monitor = Mock()
    monitor.update = AsyncMock()
    monitor.get_snapshot = AsyncMock(return_value={
        'balances': {
            'WALLET': {
                'ETH': 10.0,
                'weETH': 5.0,
                'aweETH': 4.5,
                'variableDebtWETH': 3.0
            },
            'binance': {
                'ETH_spot': 10.0,
                'USDT': 50000.0
            },
            'bybit': {
                'ETH_spot': 5.0,
                'USDT': 25000.0
            }
        },
        'derivative_positions': {
            'binance': {
                'ETHUSDT-PERP': {
                    'size': -5.0,
                    'entry_price': 3300.0
                }
            },
            'bybit': {
                'ETHUSDT-PERP': {
                    'size': -3.0,
                    'entry_price': 3305.0
                }
            }
        }
    })
    return monitor


@pytest.fixture
def mock_event_logger():
    """Create mock event logger."""
    logger = Mock()
    logger.log_event = AsyncMock()
    logger.log_atomic_transaction = AsyncMock()
    logger.get_events = AsyncMock(return_value=[])
    logger.export_to_csv = Mock(return_value="test_events.csv")
    return logger


@pytest.fixture
def sample_config():
    """Create sample configuration."""
    return {
        'backtest': {
            'initial_capital': 100000.0,
            'start_date': '2024-01-01T00:00:00Z',
            'end_date': '2024-12-31T23:59:59Z'
        },
        'strategy': {
            'share_class': 'USDT',
            'target_ltv': 0.91,
            'hedge_venues': ['binance', 'bybit', 'okx'],
            'hedge_allocation': {
                'binance': 0.33,
                'bybit': 0.33,
                'okx': 0.34
            },
            'use_flash_loan': True,
            'unwind_mode': 'fast'
        },
        'cex': {
            'binance_spot_api_key': 'test_key',
            'binance_spot_secret': 'test_secret',
            'binance_spot_testnet': True,
            'binance_futures_api_key': 'test_key',
            'binance_futures_secret': 'test_secret',
            'binance_futures_testnet': True,
            'bybit_api_key': 'test_key',
            'bybit_secret': 'test_secret',
            'bybit_testnet': True,
            'okx_api_key': 'test_key',
            'okx_secret': 'test_secret',
            'okx_passphrase': 'test_pass',
            'okx_testnet': True
        },
        'web3': {
            'rpc_url': 'https://eth-mainnet.g.alchemy.com/v2/test-key'
        }
    }


@pytest.fixture
def sample_timestamp():
    """Create sample timestamp."""
    return pd.Timestamp('2024-05-12 12:00:00', tz='UTC')


@pytest.fixture
def sample_balance_changes():
    """Create sample balance changes."""
    return {
        'token_changes': [
            {
                'venue': 'WALLET',
                'token': 'ETH',
                'delta': 5.0,
                'new_balance': 15.0
            },
            {
                'venue': 'WALLET',
                'token': 'weETH',
                'delta': -2.0,
                'new_balance': 3.0
            }
        ],
        'derivative_changes': [
            {
                'venue': 'binance',
                'instrument': 'ETHUSDT-PERP',
                'action': 'OPEN',
                'data': {
                    'size': -5.0,
                    'entry_price': 3300.0
                }
            }
        ]
    }


@pytest.fixture
def sample_event_data():
    """Create sample event data."""
    return {
        'event_type': 'SPOT_TRADE',
        'timestamp': pd.Timestamp('2024-05-12 12:00:00', tz='UTC'),
        'venue': 'binance',
        'pair': 'ETH/USDT',
        'side': 'BUY',
        'amount': 5.0,
        'fill_price': 3305.20,
        'notional_usd': 16526.0,
        'execution_cost_usd': 8.26
    }


@pytest.fixture
def sample_market_data():
    """Create sample market data."""
    return {
        'timestamp': pd.Timestamp('2024-05-12 12:00:00', tz='UTC'),
        'eth_usd_price': 3305.20,
        'weeth_supply_apy': 0.0374,
        'weeth_liquidity_index': 1.0234,
        'weeth_borrow_apy': 0.0273,
        'weeth_borrow_index': 1.0187,
        'gas_price_gwei': 20.0,
        'binance_eth_perp': 3306.15,
        'bybit_eth_perp': 3305.80
    }


@pytest.fixture
def sample_risk_metrics():
    """Create sample risk metrics."""
    return {
        'aave': {
            'ltv': 0.85,
            'health_factor': 1.18,
            'critical': False,
            'warning': False
        },
        'cex_margin': {
            'binance': 0.25,
            'bybit': 0.30,
            'any_critical': False,
            'min_margin_ratio': 0.25
        },
        'delta': {
            'net_delta_eth': 5.0,
            'critical': False,
            'warning': False
        }
    }


@pytest.fixture
def sample_pnl_data():
    """Create sample P&L data."""
    return {
        'balance_pnl': {
            'total_pnl_usd': 2500.0,
            'pnl_attribution': {
                'aave_supply': 1200.0,
                'aave_borrow': -300.0,
                'cex_trading': 800.0,
                'gas_costs': -200.0
            }
        },
        'reconciliation': {
            'balance_vs_attribution_diff': 0.0,
            'within_tolerance': True
        }
    }


# Test data files
@pytest.fixture
def test_data_dir():
    """Get test data directory."""
    return Path(__file__).parent / "fixtures" / "test_data"


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data for testing."""
    return pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='H', tz='UTC'),
        'eth_price': 3300.0,
        'volume': 1000.0,
        'open': 3300.0,
        'high': 3310.0,
        'low': 3290.0,
        'close': 3305.0
    })


# Async test helpers
@pytest.fixture
def async_mock():
    """Create async mock."""
    return AsyncMock()


# Performance test helpers
@pytest.fixture
def performance_threshold():
    """Performance threshold for tests."""
    return {
        'max_execution_time': 5.0,  # seconds
        'max_memory_usage': 100,    # MB
        'min_throughput': 1000      # operations per second
    }


# Test environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables from env.test file."""
    # Load test environment variables from env.test file
    env_test_path = Path(__file__).parent.parent / "backend" / "env.test"
    if env_test_path.exists():
        with open(env_test_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    else:
        # Fallback to hardcoded test environment variables
        test_env_vars = {
            'BASIS_ENVIRONMENT': 'test',
            'BASIS_PRODUCTION__ALCHEMY__PRIVATE_KEY': 'test_key',
            'BASIS_PRODUCTION__ALCHEMY__WALLET_ADDRESS': '0x1234567890123456789012345678901234567890',
            'BASIS_PRODUCTION__ALCHEMY__RPC_URL': 'https://test.rpc.url',
            'BASIS_PRODUCTION__ALCHEMY__NETWORK': 'testnet',
            'BASIS_PRODUCTION__ALCHEMY__CHAIN_ID': '1',
            'BASIS_PRODUCTION__CEX__BINANCE_SPOT_API_KEY': 'test_binance_key',
            'BASIS_PRODUCTION__CEX__BINANCE_SPOT_SECRET': 'test_binance_secret',
            'BASIS_PRODUCTION__CEX__BYBIT_API_KEY': 'test_bybit_key',
            'BASIS_PRODUCTION__CEX__BYBIT_SECRET': 'test_bybit_secret',
            'BASIS_PRODUCTION__CEX__OKX_API_KEY': 'test_okx_key',
            'BASIS_PRODUCTION__CEX__OKX_SECRET': 'test_okx_secret',
            'BASIS_PRODUCTION__CEX__OKX_PASSPHRASE': 'test_okx_passphrase'
        }
        for key, value in test_env_vars.items():
            os.environ[key] = value

# Centralized test infrastructure fixtures
@pytest.fixture
def mock_config_loader():
    """Get the centralized mock config loader."""
    return get_mock_config_loader()


@pytest.fixture
def mock_data_provider():
    """Get the centralized mock data provider."""
    return get_mock_data_provider()


@pytest.fixture
def config_loader_patch():
    """Get a patch for the config loader."""
    return create_mock_config_loader_patch()


@pytest.fixture
def data_provider_patch():
    """Get a patch for the data provider."""
    return create_mock_data_provider_patch()


@pytest.fixture
def test_config():
    """Get a test configuration."""
    return {
        'environment': 'test',
        'execution_mode': 'backtest',
        'debug': True,
        'deployment': 'test',
        'api': {
            'port': 8001,
            'reload': False,
            'host': 'localhost'
        },
        'cache': {
            'type': 'redis',
            'redis_url': 'redis://localhost:6379/1',
            'enabled': True,
            'cache_ttl': 300,
            'session_ttl': 3600
        },
        'database': {
            'type': 'sqlite',
            'url': 'sqlite:///./tests/fixtures/test_data/test_basis_strategy_v1.db'
        },
        'data': {
            'data_dir': './tests/fixtures/test_data',
            'cache_enabled': True,
            'provider': {
                'mode': 'backtest',
                'max_data_age_seconds': 86400,
                'refresh_interval_seconds': 3600
            }
        },
        'monitoring': {
            'log_level': 'DEBUG',
            'enable_metrics': True,
            'enable_tracing': True
        },
        'risk': {
            'mode': 'strict',
            'daily_loss_limit_pct': 0.15,
            'margin_critical_threshold': 0.10,
            'margin_warning_threshold': 0.20,
            'max_position_size_usd': 100
        },
        'live_trading': {
            'enabled': False,
            'read_only': True,
            'max_trade_size_usd': 100,
            'circuit_breaker_enabled': True,
            'emergency_stop_loss_pct': 0.15,
            'heartbeat_timeout_seconds': 300
        },
        'live_testing': {
            'enabled': False,
            'read_only': True,
            'max_trade_size_usd': 100
        },
        'testnet': {
            'enabled': True,
            'network': 'sepolia',
            'confirmation_blocks': 2,
            'max_gas_price_gwei': 20,
            'faucet_url': 'https://sepoliafaucet.com/'
        },
        'cross_network': {
            'log_simulations': True,
            'simulate_transfers': True
        },
        'rates': {
            'use_fixed_rates': True
        },
        'downloaders': {
            'chunk_size_days': 90,
            'retry_attempts': 3,
            'retry_delay': 1.0,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'rate_limits': {
                'bybit': 10,
                'coingecko': 500
            }
        }
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test."""
    yield
    # Cleanup logic here if needed
    pass
