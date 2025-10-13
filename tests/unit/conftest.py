"""
Shared pytest fixtures for unit tests.

Provides mocked dependencies and test data to isolate component testing.
Uses combination of mocks for speed and minimal real data for validation.
"""

import pytest
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock
import sys
import os

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend' / 'src'))


@pytest.fixture
def mock_config():
    """Minimal config with all required fields for component initialization."""
    return {
        'mode': 'pure_lending',
        'share_class': 'USDT',
        'asset': 'USDT',
        'initial_capital': 100000.0,
        'max_drawdown': 0.2,
        'leverage_enabled': False,
        'venues': {
            'binance': {'enabled': True},
            'bybit': {'enabled': True},
            'okx': {'enabled': True}
        },
        'component_config': {
            'risk_monitor': {
                'enabled_risk_types': ['max_drawdown', 'leverage_ratio'],
                'risk_limits': {
                    'max_drawdown': 0.2,
                    'leverage_ratio': 2.0
                }
            },
            'exposure_monitor': {
                'tracked_assets': ['BTC', 'ETH', 'USDT', 'weETH', 'aUSDT'],
                'share_class_currency': 'USDT'
            },
            'position_monitor': {
                'tracked_venues': ['wallet', 'binance', 'bybit', 'okx'],
                'tracked_assets': ['BTC', 'ETH', 'USDT', 'weETH', 'aUSDT']
            }
        },
        'data_dir': 'data',
        'backtest_start_date': '2024-05-12',
        'backtest_end_date': '2024-05-19'
    }


@pytest.fixture
def mock_market_data():
    """Market data snapshot for one timestamp."""
    return {
        'timestamp': pd.Timestamp('2024-05-12 00:00:00'),
        'eth_usd_price': 3000.0,
        'btc_usd_price': 50000.0,
        'usdt_usd_price': 1.0,
        'usdc_usd_price': 1.0,
        'dai_usd_price': 1.0,
        
        # ETH derivatives
        'weeth_eth_oracle': 1.05,          # weETH/ETH oracle price
        'wsteth_eth_oracle': 1.02,         # wstETH/ETH oracle price
        'weeth_liquidity_index': 1.02,     # AAVE liquidity index for aWeETH
        'weth_borrow_index': 1.01,         # AAVE borrow index for debt
        
        # USDT derivatives
        'usdt_liquidity_index': 1.01,      # AAVE liquidity index for aUSDT
        
        # Funding rates
        'btc_funding_rate': 0.0001,        # 0.01% funding rate
        'eth_funding_rate': 0.0002,        # 0.02% funding rate
        
        # Gas costs
        'gas_price_gwei': 20.0,
        'gas_cost_usd': 5.0
    }


@pytest.fixture
def mock_position_snapshot():
    """Comprehensive test position data covering all venues and assets."""
    return {
        'wallet': {
            # Primary assets
            'BTC': 0.5,                    # On-chain wallet BTC
            'ETH': 3.0,                    # On-chain wallet ETH
            'USDT': 5000.0,                # On-chain wallet USDT
            
            # ETH derivatives
            'weETH': 1.0,                  # On-chain wallet weETH
            'wstETH': 0.5,                 # On-chain wallet wstETH
            'aWeETH': 0.3,                 # On-chain wallet aWeETH (AAVE token)
            'variableDebtWETH': 0.1,       # On-chain wallet debt token
            
            # USDT derivatives
            'aUSDT': 1000.0,               # On-chain wallet aUSDT (AAVE token)
            
            # Other assets (should be ignored in most modes)
            'USDC': 2000.0,                # On-chain wallet USDC
            'DAI': 1500.0,                 # On-chain wallet DAI
        },
        'cex_accounts': {
            'binance': {
                'BTC': 0.2,                # CEX spot BTC
                'ETH': 1.0,                # CEX spot ETH
                'USDT': 2000.0,            # CEX spot USDT
                'USDC': 1000.0,            # CEX spot USDC
            },
            'bybit': {
                'BTC': 0.1,                # More CEX spot BTC
                'ETH': 0.5,                # More CEX spot ETH
                'USDT': 1000.0,            # More CEX spot USDT
            },
            'okx': {
                'BTC': 0.05,               # More CEX spot BTC
                'ETH': 0.3,                # More CEX spot ETH
                'USDT': 500.0,             # More CEX spot USDT
            }
        },
        'perp_positions': {
            'binance': {
                'BTCUSDT': {
                    'size': 0.15,          # CEX perp BTC
                    'entry_price': 50000.0
                },
                'ETHUSDT': {
                    'size': 0.8,           # CEX perp ETH
                    'entry_price': 3000.0
                }
            },
            'bybit': {
                'BTCUSDT': {
                    'size': 0.1,           # More CEX perp BTC
                    'entry_price': 50000.0
                },
                'ETHUSDT': {
                    'size': 0.4,           # More CEX perp ETH
                    'entry_price': 3000.0
                }
            }
        }
    }


@pytest.fixture
def mock_data_provider():
    """Mock data provider with test data."""
    mock_provider = Mock()
    
    # Mock market data methods
    mock_provider.get_market_data_snapshot.return_value = {
        'eth_usd_price': 3000.0,
        'btc_usd_price': 50000.0,
        'usdt_usd_price': 1.0,
        'weeth_eth_oracle': 1.05,
        'usdt_liquidity_index': 1.01,
        'btc_funding_rate': 0.0001,
        'eth_funding_rate': 0.0002
    }
    
    # Mock price lookup methods
    mock_provider.get_price.return_value = 3000.0
    mock_provider.get_btc_price.return_value = 50000.0
    mock_provider.get_eth_price.return_value = 3000.0
    mock_provider.get_usdt_price.return_value = 1.0
    
    # Mock AAVE methods
    mock_provider.get_aave_liquidity_index.return_value = 1.01
    mock_provider.get_aave_borrow_index.return_value = 1.01
    
    # Mock funding rate methods
    mock_provider.get_funding_rate.return_value = 0.0001
    
    # Mock data validation
    mock_provider.validate_data_at_startup.return_value = True
    mock_provider.get_data_availability.return_value = {
        'btc_prices': True,
        'eth_prices': True,
        'usdt_prices': True,
        'funding_rates': True,
        'aave_lending_rates': True
    }
    
    return mock_provider


@pytest.fixture
def mock_utility_manager():
    """Mock utility manager for component dependencies."""
    mock_utils = Mock()
    
    # Mock math utilities
    mock_utils.calculate_net_delta.return_value = 0.0
    mock_utils.convert_to_share_class.return_value = 100000.0
    mock_utils.calculate_leverage_ratio.return_value = 1.0
    
    # Mock error handling
    mock_utils.log_error.return_value = None
    mock_utils.create_error_code.return_value = 'TEST_ERROR'
    
    return mock_utils


@pytest.fixture
def real_minimal_data():
    """Load 1 week of real data (2024-05-12 to 2024-05-19) for validation."""
    data_dir = Path(__file__).parent.parent.parent / 'data'
    
    # Check if minimal data exists
    if not data_dir.exists():
        pytest.skip("Data directory not found - skipping real data tests")
    
    # Load minimal dataset for validation
    try:
        from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider
        
        data_provider = DataProvider(
            data_dir=str(data_dir),
            mode='backtest'
        )
        
        # Load just one week of data
        start_date = '2024-05-12'
        end_date = '2024-05-19'
        
        # Validate data availability
        data_provider._validate_data_at_startup()
        
        return {
            'data_provider': data_provider,
            'start_date': start_date,
            'end_date': end_date,
            'available': True
        }
        
    except Exception as e:
        return {
            'data_provider': None,
            'start_date': '2024-05-12',
            'end_date': '2024-05-19',
            'available': False,
            'error': str(e)
        }


@pytest.fixture
def mock_strategy_instructions():
    """Mock strategy instructions for testing execution manager."""
    return [
        {
            'action': 'cex_trade',
            'venue': 'binance',
            'asset': 'BTC',
            'size': 0.1,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        },
        {
            'action': 'wallet_transfer',
            'venue': 'ethereum',
            'asset': 'ETH',
            'size': 1.0,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:01:00')
        }
    ]


@pytest.fixture
def mock_execution_interfaces():
    """Mock execution interfaces for testing execution manager."""
    mock_cex_interface = Mock()
    mock_cex_interface.execute_order.return_value = {
        'status': 'filled',
        'order_id': 'test_order_123',
        'filled_size': 0.1,
        'filled_price': 50000.0,
        'execution_cost': 5.0
    }
    
    mock_onchain_interface = Mock()
    mock_onchain_interface.execute_order.return_value = {
        'status': 'confirmed',
        'tx_hash': '0x1234567890abcdef',
        'gas_used': 100000,
        'gas_cost': 5.0
    }
    
    return {
        'cex': mock_cex_interface,
        'onchain': mock_onchain_interface
    }


@pytest.fixture
def test_timestamp():
    """Standard test timestamp for all tests."""
    return pd.Timestamp('2024-05-12 00:00:00')


@pytest.fixture
def mock_event_logger():
    """Mock event logger for testing component logging."""
    mock_logger = Mock()
    mock_logger.log_event.return_value = None
    mock_logger.log_position_update.return_value = None
    mock_logger.log_execution.return_value = None
    mock_logger.log_error.return_value = None
    
    return mock_logger


# Test data for specific component testing
@pytest.fixture
def btc_basis_config():
    """Config specifically for BTC basis strategy testing."""
    return {
        'mode': 'btc_basis',
        'share_class': 'USDT',
        'asset': 'BTC',
        'initial_capital': 100000.0,
        'max_drawdown': 0.15,
        'leverage_enabled': True,
        'hedge_venues': ['binance', 'bybit', 'okx'],
        'component_config': {
            'risk_monitor': {
                'enabled_risk_types': ['max_drawdown', 'leverage_ratio', 'position_limits'],
                'risk_limits': {
                    'max_drawdown': 0.15,
                    'leverage_ratio': 3.0,
                    'max_position_size': 0.5
                }
            }
        }
    }


@pytest.fixture
def eth_basis_config():
    """Config specifically for ETH basis strategy testing."""
    return {
        'mode': 'eth_basis',
        'share_class': 'USDT',
        'asset': 'ETH',
        'initial_capital': 100000.0,
        'max_drawdown': 0.15,
        'leverage_enabled': True,
        'hedge_venues': ['binance', 'bybit', 'okx'],
        'lst_type': 'weeth',
        'component_config': {
            'risk_monitor': {
                'enabled_risk_types': ['max_drawdown', 'leverage_ratio', 'position_limits'],
                'risk_limits': {
                    'max_drawdown': 0.15,
                    'leverage_ratio': 3.0,
                    'max_position_size': 10.0
                }
            }
        }
    }
