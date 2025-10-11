"""
Pure Lending Data Provider

Provides data for pure lending strategy (USDT lending without leverage or staking).

Data Requirements:
- usdt_prices: USDT/USD spot prices
- aave_lending_rates: AAVE USDT lending rates and indexes
- gas_costs: Ethereum gas prices
- execution_costs: Execution cost models

Reference: configs/modes/pure_lending.yaml
Reference: docs/specs/09_DATA_PROVIDER.md
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, List
import os

from .base_data_provider import BaseDataProvider
from ..infrastructure.data.data_validator import DataValidator, DataProviderError

logger = logging.getLogger(__name__)


class PureLendingDataProvider(BaseDataProvider):
    """Data provider for pure lending strategy"""
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        super().__init__(execution_mode, config)
        self.available_data_types = [
            'usdt_prices',
            'aave_lending_rates', 
            'gas_costs',
            'execution_costs'
        ]
        self.data = {}
        self.validator = DataValidator(data_dir=self.data_dir)
        
        # Validate initialization
        self.validator.validate_data_provider_initialization('PureLendingDataProvider', config)
    
    def validate_data_requirements(self, data_requirements: List[str]) -> None:
        """
        Validate that this provider can satisfy data requirements.
        
        Args:
            data_requirements: List of required data types
            
        Raises:
            DataProviderError: If provider cannot satisfy requirements
        """
        self.validator.validate_data_requirements(data_requirements, self.available_data_types)
        logger.info(f"✅ PureLendingDataProvider can satisfy all requirements: {data_requirements}")
    
    def load_data(self) -> None:
        """Load all required data for pure lending strategy."""
        logger.info(f"🔄 Loading data for pure lending strategy...")
        
        try:
            # Load USDT prices (using ETH/USDT as proxy for USDT/USD)
            self._load_usdt_prices()
            
            # Load AAVE USDT lending rates
            self._load_aave_usdt_rates()
            
            # Load gas costs
            self._load_gas_costs()
            
            # Load execution costs
            self._load_execution_costs()
            
            # Validate all data requirements are satisfied
            self._validate_loaded_data()
            
            self._data_loaded = True
            logger.info(f"✅ Pure lending data loaded successfully: {len(self.data)} datasets")
            
        except Exception as e:
            logger.error(f"❌ Failed to load pure lending data: {e}")
            raise DataProviderError('DATA-004', message=f"Pure lending data loading failed: {e}")
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Return standardized data structure for pure lending strategy.
        
        Args:
            timestamp: Timestamp for data query
            
        Returns:
            Standardized data structure with market_data and protocol_data
        """
        if not self._data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        data = self._get_standardized_structure(timestamp)
        
        # Market data - USDT prices
        if 'usdt_prices' in self.data:
            usdt_data = self.data['usdt_prices']
            ts = usdt_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['market_data']['prices']['USDT'] = usdt_data.loc[ts, 'open']
        
        # Protocol data - AAVE USDT rates and indexes
        if 'usdt_rates' in self.data:
            rates_data = self.data['usdt_rates']
            ts = rates_data.index.asof(timestamp)
            if not pd.isna(ts):
                row = rates_data.loc[ts]
                data['protocol_data']['aave_indexes']['aUSDT'] = row.get('liquidityIndex', 1.0)
                data['protocol_data']['protocol_rates']['aave_usdt_supply'] = row.get('liquidity_apy', 0.0)
        
        # Execution data - gas costs
        if 'gas_costs' in self.data:
            gas_data = self.data['gas_costs']
            ts = gas_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['execution_data']['gas_costs']['supply'] = gas_data.loc[ts, 'COLLATERAL_SUPPLIED_eth']
                data['execution_data']['gas_costs']['withdraw'] = gas_data.loc[ts, 'WITHDRAW_eth']
        
        return data
    
    def _load_usdt_prices(self) -> None:
        """Load USDT prices (using ETH/USDT as proxy)."""
        # For pure lending, we use ETH/USDT as our USDT price reference
        file_path = Path(self.data_dir) / 'market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv'
        
        # Use comprehensive validation
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        expected_types = {'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'}
        df = self.validator.validate_complete_file(file_path, required_columns, expected_types)
        
        # Store as USDT prices (1/USDT = ETH price)
        self.data['usdt_prices'] = df
        logger.info(f"Loaded USDT prices: {len(df)} records")
    
    def _load_aave_usdt_rates(self) -> None:
        """Load AAVE USDT lending rates and indexes."""
        file_path = Path(self.data_dir) / 'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_USDT_rates_2024-01-01_2025-09-18_hourly.csv'
        
        # Use comprehensive validation
        required_columns = ['timestamp', 'supply_rate', 'borrow_rate', 'liquidity_index', 'variable_borrow_index']
        expected_types = {'supply_rate': 'float', 'borrow_rate': 'float', 'liquidity_index': 'float', 'variable_borrow_index': 'float'}
        df = self.validator.validate_complete_file(file_path, required_columns, expected_types)
        
        self.data['aave_lending_rates'] = df
        logger.info(f"Loaded AAVE USDT rates: {len(df)} records")
    
    def _load_gas_costs(self) -> None:
        """Load gas costs data."""
        # Try enhanced version first, fall back to regular version
        enhanced_path = Path(self.data_dir) / 'blockchain_data/gas_prices/ethereum_gas_prices_enhanced_2024-01-01_2025-09-26.csv'
        regular_path = Path(self.data_dir) / 'blockchain_data/gas_prices/ethereum_gas_prices_2024-01-01_2025-09-26.csv'
        
        if enhanced_path.exists():
            file_path = enhanced_path
        else:
            file_path = regular_path
        
        try:
            # Use basic validation for gas costs (not all columns may be available)
            self.validator.validate_file_existence(file_path)
            df = self.validator.validate_csv_parsing(file_path)
            self.validator.validate_empty_file(df, file_path)
            
            # Only validate columns that exist
            available_columns = df.columns.tolist()
            if 'gas_price_gwei' in available_columns:
                self.data['gas_costs'] = df
                logger.info(f"Loaded gas costs: {len(df)} records")
            else:
                logger.warning(f"Gas costs file missing required columns, skipping: {file_path}")
                self.data['gas_costs'] = pd.DataFrame()  # Empty dataframe
        except Exception as e:
            logger.warning(f"Failed to load gas costs, using empty data: {e}")
            self.data['gas_costs'] = pd.DataFrame()  # Empty dataframe
    
    def _load_execution_costs(self) -> None:
        """Load execution costs data."""
        file_path = Path(self.data_dir) / 'execution_costs/execution_cost_simulation_results.csv'
        
        # Use basic validation for lookup table (not time series)
        self.validator.validate_file_existence(file_path)
        df = self.validator.validate_csv_parsing(file_path)
        self.validator.validate_empty_file(df, file_path)
        
        # Execution costs are lookup tables, not time series
        df._is_time_series = False
        self.data['execution_costs'] = df
        logger.info(f"Loaded execution costs: {len(df)} records")
    
    def _validate_loaded_data(self) -> None:
        """Validate all required data is loaded."""
        required_data = ['usdt_prices', 'aave_lending_rates', 'gas_costs', 'execution_costs']
        missing_data = [key for key in required_data if key not in self.data]
        
        if missing_data:
            raise DataProviderError(
                'DATA-012',
                f"Missing required data for pure lending: {missing_data}",
                {'missing_data': missing_data, 'available_data': list(self.data.keys()), 'mode': self.mode}
            )
        
        logger.info("✅ All pure lending data requirements satisfied")
    
    def get_market_data_snapshot(self, timestamp: pd.Timestamp = None) -> Dict:
        """Get market data snapshot for a specific timestamp."""
        if timestamp is None:
            timestamp = pd.Timestamp.now()
        
        # Get USDT price at timestamp
        usdt_price = self.get_token_price('USDT', timestamp)
        
        # Get AAVE lending rates at timestamp
        aave_rates = self.get_aave_rates(timestamp)
        
        return {
            'timestamp': timestamp,
            'usdt_price': usdt_price,
            'aave_rates': aave_rates,
            'gas_price': self.get_gas_price(timestamp)
        }
    
    def get_aave_rates(self, timestamp: pd.Timestamp) -> Dict:
        """Get AAVE lending rates for a specific timestamp."""
        if 'aave_lending_rates' not in self.data or self.data['aave_lending_rates'].empty:
            return {'supply_rate': 0.0, 'borrow_rate': 0.0, 'liquidity_index': 1.0}
        
        df = self.data['aave_lending_rates'].copy()
        # Find closest timestamp
        df['time_diff'] = abs(pd.to_datetime(df['timestamp']) - pd.to_datetime(timestamp))
        closest_row = df.loc[df['time_diff'].idxmin()]
        
        return {
            'supply_rate': closest_row.get('supply_rate', 0.0),
            'borrow_rate': closest_row.get('borrow_rate', 0.0),
            'liquidity_index': closest_row.get('liquidity_index', 1.0)
        }
    
    def get_gas_price(self, timestamp: pd.Timestamp) -> float:
        """Get gas price for a specific timestamp."""
        if 'gas_costs' not in self.data or self.data['gas_costs'].empty:
            return 20.0  # Default gas price
        
        df = self.data['gas_costs'].copy()
        # Find closest timestamp
        df['time_diff'] = abs(pd.to_datetime(df['timestamp']) - pd.to_datetime(timestamp))
        closest_row = df.loc[df['time_diff'].idxmin()]
        
        return closest_row.get('gas_price_gwei', 20.0)
    
    def get_token_price(self, token: str, timestamp: pd.Timestamp) -> float:
        """Get token price for a specific timestamp."""
        if token == 'USDT':
            return 1.0  # USDT is always $1
        
        # For other tokens, look up in price data
        price_key = f'{token.lower()}_prices'
        if price_key not in self.data or self.data[price_key].empty:
            return 1.0  # Default price
        
        df = self.data[price_key].copy()
        # Find closest timestamp
        df['time_diff'] = abs(pd.to_datetime(df['timestamp']) - pd.to_datetime(timestamp))
        closest_row = df.loc[df['time_diff'].idxmin()]
        
        return closest_row.get('price', 1.0)
