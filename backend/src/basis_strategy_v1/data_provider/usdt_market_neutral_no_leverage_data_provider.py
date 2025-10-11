"""
USDT Market Neutral No Leverage Data Provider

Provides data for USDT market neutral strategy without leverage (staking + hedging only).

Data Requirements:
- eth_prices: ETH/USDT spot prices (Binance)
- weeth_prices: weETH/ETH oracle prices (AAVE)
- eth_futures: ETH futures prices (all venues)
- funding_rates: ETH funding rates (all venues)
- staking_rewards: Base staking yields
- gas_costs: Ethereum gas prices
- execution_costs: Execution cost models

Reference: configs/modes/usdt_market_neutral_no_leverage.yaml
Reference: docs/specs/09_DATA_PROVIDER.md
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, List

from .base_data_provider import BaseDataProvider
from ..infrastructure.data.historical_data_provider import _validate_data_file, DataProviderError

logger = logging.getLogger(__name__)


class USDTMarketNeutralNoLeverageDataProvider(BaseDataProvider):
    """Data provider for USDT market neutral no leverage strategy"""
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        super().__init__(execution_mode, config)
        self.available_data_types = [
            'eth_prices',
            'weeth_prices',
            'eth_futures',
            'funding_rates',
            'staking_rewards',
            'gas_costs',
            'execution_costs'
        ]
        self.lst_type = config.get('lst_type', 'weeth')
        self.hedge_venues = config.get('hedge_venues', ['binance', 'bybit', 'okx'])
        self.data = {}
    
    def validate_data_requirements(self, data_requirements: List[str]) -> None:
        """
        Validate that this provider can satisfy data requirements.
        
        Args:
            data_requirements: List of required data types
            
        Raises:
            ValueError: If provider cannot satisfy requirements
        """
        unsupported = set(data_requirements) - set(self.available_data_types)
        if unsupported:
            raise ValueError(
                f"USDTMarketNeutralNoLeverageDataProvider cannot satisfy requirements: {unsupported}. "
                f"Available: {self.available_data_types}"
            )
        
        logger.info(f"✅ USDTMarketNeutralNoLeverageDataProvider can satisfy all requirements: {data_requirements}")
    
    def load_data(self) -> None:
        """Load all required data for USDT market neutral no leverage strategy."""
        logger.info(f"🔄 Loading data for USDT market neutral no leverage strategy...")
        
        try:
            # Load ETH spot prices
            self._load_eth_spot_prices()
            
            # Load LST oracle prices
            self._load_lst_oracle_prices()
            
            # Load ETH futures data for all venues
            self._load_eth_futures_data()
            
            # Load ETH funding rates for all venues
            self._load_eth_funding_rates()
            
            # Load staking rewards
            self._load_staking_rewards()
            
            # Load gas costs
            self._load_gas_costs()
            
            # Load execution costs
            self._load_execution_costs()
            
            # Validate all data requirements are satisfied
            self._validate_loaded_data()
            
            self._data_loaded = True
            logger.info(f"✅ USDT market neutral no leverage data loaded successfully: {len(self.data)} datasets")
            
        except Exception as e:
            logger.error(f"❌ Failed to load USDT market neutral no leverage data: {e}")
            raise DataProviderError('DATA-004', message=f"USDT market neutral no leverage data loading failed: {e}")
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Return standardized data structure for USDT market neutral no leverage strategy.
        
        Args:
            timestamp: Timestamp for data query
            
        Returns:
            Standardized data structure with market_data and protocol_data
        """
        if not self._data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        data = self._get_standardized_structure(timestamp)
        
        # Market data - ETH spot prices
        if 'eth_spot_binance' in self.data:
            eth_data = self.data['eth_spot_binance']
            ts = eth_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['market_data']['prices']['ETH'] = eth_data.loc[ts, 'open']
        
        # Market data - ETH futures prices per venue
        for venue in self.hedge_venues:
            futures_key = f'{venue}_futures'
            if futures_key in self.data:
                futures_data = self.data[futures_key]
                ts = futures_data.index.asof(timestamp)
                if not pd.isna(ts):
                    data['market_data']['futures_prices'][f'eth_{venue}'] = futures_data.loc[ts, 'open']
        
        # Market data - ETH funding rates per venue
        for venue in self.hedge_venues:
            funding_key = f'{venue}_funding'
            if funding_key in self.data:
                funding_data = self.data[funding_key]
                ts = funding_data.index.asof(timestamp)
                if not pd.isna(ts):
                    data['market_data']['funding_rates'][f'eth_{venue}'] = funding_data.loc[ts, 'funding_rate']
        
        # Protocol data - LST oracle prices
        if f'{self.lst_type.lower()}_oracle' in self.data:
            oracle_data = self.data[f'{self.lst_type.lower()}_oracle']
            ts = oracle_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['protocol_data']['oracle_prices'][self.lst_type.lower()] = oracle_data.loc[ts, 'oracle_price_eth']
        
        # Protocol data - staking rewards
        if 'staking_yields' in self.data:
            staking_data = self.data['staking_yields']
            ts = staking_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['protocol_data']['staking_rewards']['base_staking'] = staking_data.loc[ts, 'yield']
        
        # Execution data - gas costs
        if 'gas_costs' in self.data:
            gas_data = self.data['gas_costs']
            ts = gas_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['execution_data']['gas_costs']['stake'] = gas_data.loc[ts, 'CREATE_LST_eth']
                data['execution_data']['gas_costs']['unstake'] = gas_data.loc[ts, 'WITHDRAW_eth']
                data['execution_data']['gas_costs']['spot_trade'] = gas_data.loc[ts, 'gas_price_avg_gwei']
        
        return data
    
    def _load_eth_spot_prices(self) -> None:
        """Load ETH spot prices from Binance."""
        file_path = Path(self.data_dir) / 'market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv'
        
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, 'ETH spot prices')
        
        self.data['eth_spot_binance'] = df
        logger.info(f"Loaded ETH spot prices: {len(df)} records")
    
    def _load_lst_oracle_prices(self) -> None:
        """Load LST oracle prices."""
        if self.lst_type.lower() == 'weeth':
            file_path = Path(self.data_dir) / 'protocol_data/aave/oracle/weETH_ETH_oracle_2024-01-01_2025-09-18.csv'
        elif self.lst_type.lower() == 'wsteth':
            file_path = Path(self.data_dir) / 'protocol_data/aave/oracle/wstETH_ETH_oracle_2024-01-01_2025-09-18.csv'
        else:
            raise ValueError(f"Unknown LST type: {self.lst_type}")
        
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, f'{self.lst_type} oracle prices')
        
        self.data[f'{self.lst_type.lower()}_oracle'] = df
        logger.info(f"Loaded {self.lst_type} oracle prices: {len(df)} records")
    
    def _load_eth_futures_data(self) -> None:
        """Load ETH futures data for all venues."""
        for venue in self.hedge_venues:
            if venue == 'okx':
                # OKX data is proxied from Binance
                logger.info(f"OKX ETH futures data will be proxied from Binance")
                continue
            
            file_path = Path(self.data_dir) / f'market_data/derivatives/futures_ohlcv/{venue}_ETHUSDT_perp_1h_2024-01-01_2025-09-26.csv'
            
            df = _validate_data_file(file_path)
            self._validate_timestamp_alignment(df, f'{venue} ETH futures')
            
            self.data[f'{venue}_futures'] = df
            logger.info(f"Loaded {venue} ETH futures: {len(df)} records")
        
        # Set up OKX proxy from Binance
        if 'binance_futures' in self.data:
            self.data['okx_futures'] = self.data['binance_futures']
            logger.info("Using Binance ETH futures as OKX proxy")
    
    def _load_eth_funding_rates(self) -> None:
        """Load ETH funding rates for all venues."""
        for venue in self.hedge_venues:
            if venue == 'okx':
                # OKX funding rates have different date range
                file_path = Path(self.data_dir) / f'market_data/derivatives/funding_rates/{venue}_ETHUSDT_funding_rates_2024-05-01_2025-09-07.csv'
                df = _validate_data_file(
                    file_path,
                    timestamp_column="funding_timestamp",
                    strict_date_range=False
                )
            else:
                file_path = Path(self.data_dir) / f'market_data/derivatives/funding_rates/{venue}_ETHUSDT_funding_rates_2024-01-01_2025-09-26.csv'
                df = _validate_data_file(
                    file_path,
                    timestamp_column="funding_timestamp"
                )
            
            self._validate_timestamp_alignment(df, f'{venue} ETH funding rates')
            self.data[f'{venue}_funding'] = df
            logger.info(f"Loaded {venue} ETH funding rates: {len(df)} records")
    
    def _load_staking_rewards(self) -> None:
        """Load staking rewards data."""
        # Try multiple possible filenames for staking yields
        possible_paths = [
            Path(self.data_dir) / 'protocol_data/staking/base_staking_yields_2024-01-01_2025-09-18_hourly.csv',
            Path(self.data_dir) / 'protocol_data/staking/base_yields/weeth_oracle_yields_2024-01-01_2025-09-18.csv',
            Path(self.data_dir) / 'protocol_data/staking/base_staking_yields_2024-01-01_2025-09-18.csv'
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            raise DataProviderError('DATA-001', file_path=str(possible_paths[0]))
        
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, 'staking yields')
        
        self.data['staking_yields'] = df
        logger.info(f"Loaded staking yields: {len(df)} records")
    
    def _load_gas_costs(self) -> None:
        """Load gas costs data."""
        # Try enhanced version first, fall back to regular version
        enhanced_path = Path(self.data_dir) / 'blockchain_data/gas_prices/ethereum_gas_prices_enhanced_2024-01-01_2025-09-26.csv'
        regular_path = Path(self.data_dir) / 'blockchain_data/gas_prices/ethereum_gas_prices_2024-01-01_2025-09-26.csv'
        
        if enhanced_path.exists():
            file_path = enhanced_path
        else:
            file_path = regular_path
        
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, 'gas costs')
        
        self.data['gas_costs'] = df
        logger.info(f"Loaded gas costs: {len(df)} records")
    
    def _load_execution_costs(self) -> None:
        """Load execution costs data."""
        file_path = Path(self.data_dir) / 'execution_costs/execution_cost_simulation_results.csv'
        
        if not file_path.exists():
            raise DataProviderError('DATA-001', file_path=str(file_path))
        
        df = pd.read_csv(file_path)
        if df.empty:
            raise DataProviderError('DATA-003', message="Execution costs file is empty", file_path=str(file_path))
        
        # Execution costs are lookup tables, not time series
        df._is_time_series = False
        self.data['execution_costs'] = df
        logger.info(f"Loaded execution costs: {len(df)} records")
    
    def _validate_loaded_data(self) -> None:
        """Validate all required data is loaded."""
        required_data = [
            'eth_spot_binance',
            f'{self.lst_type.lower()}_oracle',
            'staking_yields',
            'gas_costs',
            'execution_costs'
        ]
        
        # Check futures and funding data for each venue
        for venue in self.hedge_venues:
            required_data.append(f'{venue}_futures')
            required_data.append(f'{venue}_funding')
        
        missing_data = [key for key in required_data if key not in self.data]
        
        if missing_data:
            raise DataProviderError(
                'DATA-004',
                message=f"Missing required data for USDT market neutral no leverage: {missing_data}",
                missing_data=missing_data,
                mode=self.mode
            )
        
        logger.info("✅ All USDT market neutral no leverage data requirements satisfied")
