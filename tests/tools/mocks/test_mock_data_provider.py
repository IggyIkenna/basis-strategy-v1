"""
Centralized mock data provider for testing.

This module provides a mock data provider that can be used across all tests
to avoid dependency on real data sources and APIs.
"""

from typing import Dict, Any, Optional, List
from unittest.mock import Mock, AsyncMock
import pandas as pd
from datetime import datetime, timezone
from decimal import Decimal


class MockDataProvider:
    """Mock data provider that returns predefined test data."""
    
    def __init__(self):
        self._setup_mock_data()
    
    def _setup_mock_data(self):
        """Setup mock data for testing."""
        # Base timestamp for all test data
        self.base_timestamp = pd.Timestamp('2024-05-12 12:00:00', tz='UTC')
        
        # Mock price data
        self.mock_prices = {
            'ETH': 3305.20,
            'BTC': 45000.00,
            'USDT': 1.00,
            'weETH': 1.0254,
            'wstETH': 1.0234
        }
        
        # Mock APY data
        self.mock_apys = {
            'aave_supply_weeth': 0.0374,
            'aave_borrow_weeth': 0.0273,
            'aave_supply_weth': 0.0321,
            'aave_borrow_weth': 0.0256,
            'staking_base': 0.0320,
            'eigen_rewards': 0.0080
        }
        
        # Mock index data
        self.mock_indices = {
            'weeth_liquidity_index': 1.0234,
            'weeth_borrow_index': 1.0187,
            'weth_liquidity_index': 1.0198,
            'weth_borrow_index': 1.0156
        }
        
        # Mock funding rates
        self.mock_funding_rates = {
            'binance_eth_perp': 0.0001,
            'bybit_eth_perp': 0.0002,
            'okx_eth_perp': 0.00015,
            'binance_btc_perp': 0.00005,
            'bybit_btc_perp': 0.00008
        }
        
        # Mock gas costs
        self.mock_gas_costs = {
            'standard': 0.001875,
            'fast': 0.002500,
            'slow': 0.001250
        }
        
        # Mock execution costs
        self.mock_execution_costs = {
            'spot_trade': 5.0,
            'futures_trade': 3.0,
            'flash_loan': 10.0,
            'aave_operation': 15.0
        }
    
    async def get_spot_price(self, asset: str, venue: str = 'binance') -> float:
        """Get mock spot price."""
        return self.mock_prices.get(asset, 100.0)
    
    async def get_futures_price(self, asset: str, venue: str = 'binance') -> float:
        """Get mock futures price."""
        base_price = self.mock_prices.get(asset, 100.0)
        # Add small spread for futures
        spread = 0.001 if asset == 'ETH' else 0.0005
        return base_price * (1 + spread)
    
    async def get_oracle_price(self, asset: str) -> float:
        """Get mock oracle price."""
        return self.mock_prices.get(asset, 100.0)
    
    async def get_aave_index(self, asset: str, index_type: str = 'liquidity') -> float:
        """Get mock AAVE index."""
        key = f"{asset.lower()}_{index_type}_index"
        return self.mock_indices.get(key, 1.0)
    
    async def get_aave_apy(self, asset: str, operation: str = 'supply') -> float:
        """Get mock AAVE APY."""
        key = f"aave_{operation}_{asset.lower()}"
        return self.mock_apys.get(key, 0.03)
    
    async def get_staking_apy(self, asset: str = 'ETH') -> float:
        """Get mock staking APY."""
        return self.mock_apys.get('staking_base', 0.032)
    
    async def get_eigen_rewards_apy(self) -> float:
        """Get mock EIGEN rewards APY."""
        return self.mock_apys.get('eigen_rewards', 0.008)
    
    async def get_funding_rate(self, asset: str, venue: str) -> float:
        """Get mock funding rate."""
        key = f"{venue}_{asset.lower()}_perp"
        return self.mock_funding_rates.get(key, 0.0001)
    
    async def get_gas_cost(self, operation: str = 'standard') -> float:
        """Get mock gas cost."""
        return self.mock_gas_costs.get(operation, 0.001875)
    
    async def get_execution_cost(self, operation: str) -> float:
        """Get mock execution cost."""
        return self.mock_execution_costs.get(operation, 5.0)
    
    async def get_market_data_snapshot(self) -> Dict[str, Any]:
        """Get mock market data snapshot."""
        return {
            'timestamp': self.base_timestamp,
            'eth_usd_price': self.mock_prices['ETH'],
            'btc_usd_price': self.mock_prices['BTC'],
            'weeth_usd_price': self.mock_prices['weETH'],
            'weeth_supply_apy': self.mock_apys['aave_supply_weeth'],
            'weeth_borrow_apy': self.mock_apys['aave_borrow_weeth'],
            'weeth_liquidity_index': self.mock_indices['weeth_liquidity_index'],
            'weeth_borrow_index': self.mock_indices['weeth_borrow_index'],
            'staking_apy': self.mock_apys['staking_base'],
            'eigen_rewards_apy': self.mock_apys['eigen_rewards'],
            'gas_price_gwei': 20.0,
            'funding_rates': self.mock_funding_rates,
            'binance_eth_perp': self.mock_prices['ETH'] * 1.001,
            'bybit_eth_perp': self.mock_prices['ETH'] * 1.0008,
            'okx_eth_perp': self.mock_prices['ETH'] * 1.0015
        }
    
    async def get_historical_data(self, 
                                data_type: str, 
                                start_date: datetime, 
                                end_date: datetime,
                                **kwargs) -> pd.DataFrame:
        """Get mock historical data."""
        # Create a simple time series
        date_range = pd.date_range(start=start_date, end=end_date, freq='H')
        
        if data_type == 'eth_prices':
            return pd.DataFrame({
                'timestamp': date_range,
                'price': [self.mock_prices['ETH'] + (i * 0.1) for i in range(len(date_range))],
                'volume': [1000.0] * len(date_range)
            })
        elif data_type == 'btc_prices':
            return pd.DataFrame({
                'timestamp': date_range,
                'price': [self.mock_prices['BTC'] + (i * 1.0) for i in range(len(date_range))],
                'volume': [500.0] * len(date_range)
            })
        elif data_type == 'funding_rates':
            return pd.DataFrame({
                'timestamp': date_range,
                'binance_eth': [self.mock_funding_rates['binance_eth_perp']] * len(date_range),
                'bybit_eth': [self.mock_funding_rates['bybit_eth_perp']] * len(date_range),
                'okx_eth': [self.mock_funding_rates['okx_eth_perp']] * len(date_range)
            })
        else:
            # Default mock data
            return pd.DataFrame({
                'timestamp': date_range,
                'value': [100.0 + (i * 0.01) for i in range(len(date_range))]
            })
    
    async def get_aave_risk_parameters(self) -> Dict[str, Any]:
        """Get mock AAVE risk parameters."""
        return {
            'weETH': {
                'ltv': 0.91,
                'liquidation_threshold': 0.93,
                'liquidation_bonus': 0.05,
                'reserve_factor': 0.10,
                'usage_as_collateral_enabled': True,
                'borrowing_enabled': True,
                'stable_borrow_rate_enabled': False,
                'is_active': True,
                'is_frozen': False
            },
            'WETH': {
                'ltv': 0.80,
                'liquidation_threshold': 0.85,
                'liquidation_bonus': 0.05,
                'reserve_factor': 0.10,
                'usage_as_collateral_enabled': True,
                'borrowing_enabled': True,
                'stable_borrow_rate_enabled': False,
                'is_active': True,
                'is_frozen': False
            }
        }
    
    async def get_lst_market_prices(self) -> Dict[str, float]:
        """Get mock LST market prices."""
        return {
            'weETH/ETH': 1.0254,
            'wstETH/ETH': 1.0234,
            'rETH/ETH': 1.0210
        }
    
    def set_mock_price(self, asset: str, price: float):
        """Set a custom mock price for testing."""
        self.mock_prices[asset] = price
    
    def set_mock_apy(self, key: str, apy: float):
        """Set a custom mock APY for testing."""
        self.mock_apys[key] = apy
    
    def set_mock_funding_rate(self, key: str, rate: float):
        """Set a custom mock funding rate for testing."""
        self.mock_funding_rates[key] = rate
    
    def reset_mock_data(self):
        """Reset all mock data to defaults."""
        self._setup_mock_data()


# Global instance for use in tests
mock_data_provider = MockDataProvider()


def get_mock_data_provider() -> MockDataProvider:
    """Get the global mock data provider instance."""
    return mock_data_provider


def create_mock_data_provider_patch():
    """Create a mock patch for the data provider."""
    from unittest.mock import patch
    
    def mock_get_data_provider():
        return mock_data_provider
    
    return patch('backend.src.basis_strategy_v1.infrastructure.data.historical_data_provider.get_data_provider', mock_get_data_provider)
