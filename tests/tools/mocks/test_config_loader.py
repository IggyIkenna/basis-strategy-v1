"""
Centralized mock config loader for testing.

This module provides a mock config loader that can be used across all tests
to avoid dependency on real configuration files and environment variables.
"""

from typing import Dict, Any, Optional
from unittest.mock import Mock
from pathlib import Path


class MockConfigLoader:
    """Mock config loader that returns predefined test configurations."""
    
    def __init__(self):
        self._configs = self._load_test_configs()
    
    def _load_test_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load test configurations."""
        return {
            'test_pure_lending': {
                'mode': 'test_pure_lending',
                'description': 'Test pure lending strategy',
                'lending_enabled': True,
                'staking_enabled': False,
                'basis_trade_enabled': False,
                'leverage_enabled': False,
                'share_class': 'USDT',
                'asset': 'USDT',
                'lst_type': None,
                'rewards_mode': 'base_only',
                'use_flash_loan': False,
                'unwind_mode': 'fast',
                'hedge_venues': [],
                'hedge_allocation': {},
                'margin_ratio_target': 1.0,
                'capital_allocation': {
                    'spot_capital': 1.0,
                    'perp_capital': 0.0,
                    'max_position_size': 0.95
                },
                'target_apy': 0.05,
                'max_drawdown': 0.01,
                'data_requirements': [
                    'aave_lending_rates',
                    'usdt_prices',
                    'gas_costs',
                    'execution_costs'
                ],
                'monitoring': {
                    'health_check_interval': 60,
                    'position_check_interval': 300,
                    'risk_check_interval': 60,
                    'alert_thresholds': {
                        'drawdown_warning': 0.01,
                        'drawdown_critical': 0.015
                    }
                }
            },
            'test_btc_basis': {
                'mode': 'test_btc_basis',
                'description': 'Test BTC basis trading strategy',
                'lending_enabled': False,
                'staking_enabled': False,
                'basis_trade_enabled': True,
                'leverage_enabled': False,
                'share_class': 'USDT',
                'asset': 'BTC',
                'lst_type': None,
                'rewards_mode': 'base_only',
                'use_flash_loan': False,
                'unwind_mode': 'fast',
                'hedge_venues': ['binance', 'bybit'],
                'hedge_allocation': {
                    'binance': 0.5,
                    'bybit': 0.5
                },
                'capital_allocation': {
                    'spot_capital': 0.5,
                    'perp_capital': 0.5,
                    'max_position_size': 0.95
                },
                'margin_ratio_target': 0.8,
                'target_apy': 0.08,
                'max_drawdown': 0.02,
                'data_requirements': [
                    'btc_prices',
                    'btc_futures_prices',
                    'funding_rates',
                    'gas_costs',
                    'execution_costs'
                ],
                'monitoring': {
                    'health_check_interval': 60,
                    'position_check_interval': 300,
                    'risk_check_interval': 60,
                    'alert_thresholds': {
                        'drawdown_warning': 0.01,
                        'drawdown_critical': 0.015
                    }
                }
            },
            'test_eth_leveraged': {
                'mode': 'test_eth_leveraged',
                'description': 'Test ETH leveraged staking strategy',
                'lending_enabled': True,
                'staking_enabled': True,
                'basis_trade_enabled': False,
                'leverage_enabled': True,
                'share_class': 'ETH',
                'asset': 'ETH',
                'lst_type': 'weeth',
                'rewards_mode': 'base_eigen',
                'use_flash_loan': False,
                'unwind_mode': 'slow',
                'hedge_venues': [],
                'hedge_allocation': {},
                'margin_ratio_target': 1.0,
                'max_stake_spread_move': 0.02215,
                'capital_allocation': {
                    'spot_capital': 0.5,
                    'perp_capital': 0.5,
                    'max_position_size': 0.95
                },
                'target_apy': 0.20,
                'max_drawdown': 0.04,
                'data_requirements': [
                    'eth_prices',
                    'weeth_prices',
                    'aave_lending_rates',
                    'staking_rewards',
                    'eigen_rewards',
                    'gas_costs',
                    'execution_costs',
                    'aave_risk_params',
                    'lst_market_prices'
                ],
                'monitoring': {
                    'health_check_interval': 60,
                    'position_check_interval': 300,
                    'risk_check_interval': 60,
                    'alert_thresholds': {
                        'drawdown_warning': 0.01,
                        'drawdown_critical': 0.015
                    }
                }
            },
            'test_eth_staking_only': {
                'mode': 'test_eth_staking_only',
                'description': 'Test ETH staking only strategy',
                'lending_enabled': False,
                'staking_enabled': True,
                'basis_trade_enabled': False,
                'leverage_enabled': False,
                'share_class': 'ETH',
                'asset': 'ETH',
                'lst_type': 'weeth',
                'rewards_mode': 'base_eigen',
                'use_flash_loan': False,
                'unwind_mode': 'slow',
                'hedge_venues': [],
                'hedge_allocation': {},
                'margin_ratio_target': 1.0,
                'max_stake_spread_move': 0.02215,
                'capital_allocation': {
                    'spot_capital': 1.0,
                    'perp_capital': 0.0,
                    'max_position_size': 0.95
                },
                'target_apy': 0.03,
                'max_drawdown': 0.01,
                'data_requirements': [
                    'eth_prices',
                    'weeth_prices',
                    'staking_rewards',
                    'eigen_rewards',
                    'gas_costs',
                    'execution_costs',
                    'lst_market_prices'
                ],
                'monitoring': {
                    'health_check_interval': 60,
                    'position_check_interval': 300,
                    'risk_check_interval': 60,
                    'alert_thresholds': {
                        'drawdown_warning': 0.01,
                        'drawdown_critical': 0.015
                    }
                }
            },
            'test_usdt_market_neutral': {
                'mode': 'test_usdt_market_neutral',
                'description': 'Test USDT market neutral strategy',
                'lending_enabled': True,
                'staking_enabled': True,
                'basis_trade_enabled': True,
                'leverage_enabled': True,
                'share_class': 'USDT',
                'asset': 'ETH',
                'lst_type': 'weeth',
                'rewards_mode': 'base_eigen_seasonal',
                'use_flash_loan': True,
                'unwind_mode': 'fast',
                'hedge_venues': ['binance', 'bybit', 'okx'],
                'hedge_allocation': {
                    'binance': 0.4,
                    'bybit': 0.3,
                    'okx': 0.3
                },
                'margin_ratio_target': 1.0,
                'max_stake_spread_move': 0.02215,
                'capital_allocation': {
                    'spot_capital': 0.5,
                    'perp_capital': 0.5,
                    'max_position_size': 0.95
                },
                'target_apy': 0.15,
                'max_drawdown': 0.04,
                'data_requirements': [
                    'eth_prices',
                    'weeth_prices',
                    'aave_lending_rates',
                    'staking_rewards',
                    'eigen_rewards',
                    'ethfi_rewards',
                    'funding_rates',
                    'gas_costs',
                    'execution_costs',
                    'aave_risk_params',
                    'lst_market_prices'
                ],
                'monitoring': {
                    'health_check_interval': 60,
                    'position_check_interval': 300,
                    'risk_check_interval': 60,
                    'alert_thresholds': {
                        'drawdown_warning': 0.01,
                        'drawdown_critical': 0.015
                    }
                }
            },
            'test_usdt_market_neutral_no_leverage': {
                'mode': 'test_usdt_market_neutral_no_leverage',
                'description': 'Test USDT market neutral no leverage strategy',
                'lending_enabled': False,
                'staking_enabled': True,
                'basis_trade_enabled': True,
                'leverage_enabled': False,
                'share_class': 'USDT',
                'asset': 'ETH',
                'lst_type': 'weeth',
                'rewards_mode': 'base_eigen_seasonal',
                'use_flash_loan': False,
                'unwind_mode': 'fast',
                'hedge_venues': ['binance', 'bybit', 'okx'],
                'hedge_allocation': {
                    'binance': 0.4,
                    'bybit': 0.3,
                    'okx': 0.3
                },
                'margin_ratio_target': 1.0,
                'max_stake_spread_move': 0.02215,
                'capital_allocation': {
                    'spot_capital': 0.5,
                    'perp_capital': 0.5,
                    'max_position_size': 0.95
                },
                'target_apy': 0.08,
                'max_drawdown': 0.02,
                'data_requirements': [
                    'eth_prices',
                    'weeth_prices',
                    'staking_rewards',
                    'eigen_rewards',
                    'funding_rates',
                    'gas_costs',
                    'execution_costs',
                    'lst_market_prices'
                ],
                'monitoring': {
                    'health_check_interval': 60,
                    'position_check_interval': 300,
                    'risk_check_interval': 60,
                    'alert_thresholds': {
                        'drawdown_warning': 0.01,
                        'drawdown_critical': 0.015
                    }
                }
            }
        }
    
    def get_complete_config(self, mode: str) -> Dict[str, Any]:
        """Get complete configuration for a mode."""
        if mode in self._configs:
            return self._configs[mode].copy()
        else:
            # Return default test config if mode not found
            return self._configs['test_pure_lending'].copy()
    
    def get_available_modes(self) -> list:
        """Get list of available test modes."""
        return list(self._configs.keys())
    
    def add_custom_config(self, mode: str, config: Dict[str, Any]):
        """Add a custom test configuration."""
        self._configs[mode] = config.copy()
    
    def clear_custom_configs(self):
        """Clear any custom configurations added during testing."""
        self._configs = self._load_test_configs()


# Global instance for use in tests
mock_config_loader = MockConfigLoader()


def get_mock_config_loader() -> MockConfigLoader:
    """Get the global mock config loader instance."""
    return mock_config_loader


def create_mock_config_loader_patch():
    """Create a mock patch for the config loader."""
    from unittest.mock import patch
    
    def mock_get_config_loader():
        return mock_config_loader
    
    return patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader', mock_get_config_loader)
