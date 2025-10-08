#!/usr/bin/env python3
"""Test script to debug BTC exposure monitor issue."""

import sys
import os
import pandas as pd
import structlog

# Add backend to path
sys.path.insert(0, '/workspace/backend/src')

# Set up logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def test_btc_exposure_monitor():
    """Test BTC exposure monitor with mock data."""
    try:
        from basis_strategy_v1.core.strategies.components.exposure_monitor import ExposureMonitor
        
        # Create mock position monitor
        class MockPositionMonitor:
            def get_snapshot(self):
                return {
                    'wallet': {
                        'BTC': 0.0,  # No BTC in wallet
                        'USDT': 100000.0
                    },
                    'cex_accounts': {
                        'binance': {
                            'BTC': 0.592242,
                            'USDT': 37770.70
                        },
                        'bybit': {
                            'BTC': 0.444181,
                            'USDT': 28328.03
                        },
                        'okx': {
                            'BTC': 0.444181,
                            'USDT': 28328.03
                        }
                    },
                    'perp_positions': {
                        'binance': {
                            'BTCUSDT': {
                                'size': -0.592242,
                                'entry_price': 50000.0
                            }
                        },
                        'bybit': {
                            'BTCUSDT': {
                                'size': -0.444181,
                                'entry_price': 50000.0
                            }
                        },
                        'okx': {
                            'BTCUSDT': {
                                'size': -0.444181,
                                'entry_price': 50000.0
                            }
                        }
                    }
                }
        
        mock_position_monitor = MockPositionMonitor()
        
        # Create mock data provider
        class MockDataProvider:
            def get_market_data_snapshot(self, timestamp):
                return {
                    'btc_usd_price': 50000.0,
                    'eth_usd_price': 3000.0,
                    'usdt_usd_price': 1.0
                }
        
        mock_data_provider = MockDataProvider()
        
        # Create mock position snapshot with BTC positions
        position_snapshot = {
            'wallet': {
                'BTC': 0.0,  # No BTC in wallet
                'USDT': 100000.0
            },
            'cex_accounts': {
                'binance': {
                    'BTC': 0.592242,
                    'USDT': 37770.70
                },
                'bybit': {
                    'BTC': 0.444181,
                    'USDT': 28328.03
                },
                'okx': {
                    'BTC': 0.444181,
                    'USDT': 28328.03
                }
            },
            'perp_positions': {
                'binance': {
                    'BTCUSDT': {
                        'size': -0.592242,
                        'entry_price': 50000.0
                    }
                },
                'bybit': {
                    'BTCUSDT': {
                        'size': -0.444181,
                        'entry_price': 50000.0
                    }
                },
                'okx': {
                    'BTCUSDT': {
                        'size': -0.444181,
                        'entry_price': 50000.0
                    }
                }
            }
        }
        
        # Create mock market data
        market_data = {
            'btc_usd_price': 50000.0,
            'eth_usd_price': 3000.0,
            'usdt_usd_price': 1.0
        }
        
        # Create exposure monitor
        config = {
            'mode': 'btc_basis',
            'asset': 'BTC',
            'debug_mode': True
        }
        
        exposure_monitor = ExposureMonitor(
            config=config,
            share_class='USDT',
            position_monitor=mock_position_monitor,
            data_provider=mock_data_provider,
            debug_mode=True
        )
        
        # Test calculate_exposure
        timestamp = pd.Timestamp('2024-01-01 00:00:00', tz='UTC')
        
        # Capture logs
        import logging
        logging.basicConfig(level=logging.INFO)
        
        result = exposure_monitor.calculate_exposure(
            timestamp=timestamp,
            position_snapshot=position_snapshot,
            market_data=market_data
        )
        
        print("=== EXPOSURE MONITOR RESULT ===")
        print(f"Result keys: {list(result.keys())}")
        print(f"Exposures: {result.get('exposures', {})}")
        print(f"Exposure keys: {list(result.get('exposures', {}).keys())}")
        
        # Check if BTC is in the exposures
        if 'BTC' in result.get('exposures', {}):
            print("✅ BTC exposure found!")
            btc_exposure = result['exposures']['BTC']
            print(f"BTC exposure details: {btc_exposure}")
        else:
            print("❌ BTC exposure NOT found!")
            print("Available exposures:", list(result.get('exposures', {}).keys()))
        
        return result
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    test_btc_exposure_monitor()