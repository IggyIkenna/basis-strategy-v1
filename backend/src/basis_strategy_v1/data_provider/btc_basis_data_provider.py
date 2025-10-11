"""
BTC Basis Data Provider

Provides data for BTC basis trading strategy with short side hedging across venues.

Data Requirements:
- btc_prices: BTC/USDT spot prices (Binance)
- btc_futures: BTC futures prices (Binance, Bybit, OKX)
- funding_rates: BTC funding rates (all venues)
- gas_costs: Ethereum gas prices
- execution_costs: Execution cost models

Reference: configs/modes/btc_basis.yaml
Reference: docs/specs/09_DATA_PROVIDER.md
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, List

from .base_data_provider import BaseDataProvider
from ..infrastructure.data.data_validator import DataValidator, DataProviderError

logger = logging.getLogger(__name__)


class BTCBasisDataProvider(BaseDataProvider):
    """Data provider for BTC basis trading strategy"""
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        super().__init__(execution_mode, config)
        self.available_data_types = [
            'btc_prices',
            'btc_futures',
            'funding_rates',
            'gas_costs',
            'execution_costs'
        ]
        self.hedge_venues = config.get('hedge_venues', ['binance', 'bybit', 'okx'])
        self.data = {}
        self.validator = DataValidator(data_dir=self.data_dir)
        
        # Validate initialization
        self.validator.validate_data_provider_initialization('BTCBasisDataProvider', config)
    
    def validate_data_requirements(self, data_requirements: List[str]) -> None:
        """
        Validate that this provider can satisfy data requirements.
        
        Args:
            data_requirements: List of required data types
            
        Raises:
            DataProviderError: If provider cannot satisfy requirements
        """
        self.validator.validate_data_requirements(data_requirements, self.available_data_types)
        logger.info(f"✅ BTCBasisDataProvider can satisfy all requirements: {data_requirements}")
    
    def load_data(self) -> None:
        """Load all required data for BTC basis trading strategy."""
        logger.info(f"🔄 Loading data for BTC basis trading strategy...")
        
        try:
            # Load BTC spot prices
            self._load_btc_spot_prices()
            
            # Load BTC futures data for all venues
            self._load_btc_futures_data()
            
            # Load BTC funding rates for all venues
            self._load_btc_funding_rates()
            
            # Load gas costs
            self._load_gas_costs()
            
            # Load execution costs
            self._load_execution_costs()
            
            # Validate all data requirements are satisfied
            self._validate_loaded_data()
            
            self._data_loaded = True
            logger.info(f"✅ BTC basis data loaded successfully: {len(self.data)} datasets")
            
        except Exception as e:
            logger.error(f"❌ Failed to load BTC basis data: {e}")
            raise DataProviderError('DATA-004', message=f"BTC basis data loading failed: {e}")
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Return standardized data structure for BTC basis trading strategy.
        
        Args:
            timestamp: Timestamp for data query
            
        Returns:
            Standardized data structure with market_data and protocol_data
        """
        if not self._data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        data = self._get_standardized_structure(timestamp)
        
        # Market data - BTC spot prices
        if 'btc_spot_binance' in self.data:
            btc_data = self.data['btc_spot_binance']
            ts = btc_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['market_data']['prices']['BTC'] = btc_data.loc[ts, 'open']
        
        # Market data - BTC futures prices per venue
        for venue in self.hedge_venues:
            futures_key = f'{venue}_futures'
            if futures_key in self.data:
                futures_data = self.data[futures_key]
                ts = futures_data.index.asof(timestamp)
                if not pd.isna(ts):
                    data['market_data']['futures_prices'][f'btc_{venue}'] = futures_data.loc[ts, 'open']
        
        # Market data - BTC funding rates per venue
        for venue in self.hedge_venues:
            funding_key = f'{venue}_funding'
            if funding_key in self.data:
                funding_data = self.data[funding_key]
                ts = funding_data.index.asof(timestamp)
                if not pd.isna(ts):
                    data['market_data']['funding_rates'][f'btc_{venue}'] = funding_data.loc[ts, 'funding_rate']
        
        # Execution data - gas costs
        if 'gas_costs' in self.data:
            gas_data = self.data['gas_costs']
            ts = gas_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['execution_data']['gas_costs']['spot_trade'] = gas_data.loc[ts, 'gas_price_avg_gwei']
        
        return data
    
    def _load_btc_spot_prices(self) -> None:
        """Load BTC spot prices from Binance."""
        file_path = Path(self.data_dir) / 'market_data/spot_prices/btc_usd/binance_BTCUSDT_1h_2024-01-01_2025-09-30.csv'
        
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, 'BTC spot prices')
        
        self.data['btc_spot_binance'] = df
        logger.info(f"Loaded BTC spot prices: {len(df)} records")
    
    def _load_btc_futures_data(self) -> None:
        """Load BTC futures data for all venues."""
        for venue in self.hedge_venues:
            if venue == 'okx':
                # OKX data is proxied from Binance
                logger.info(f"OKX BTC futures data will be proxied from Binance")
                continue
            
            file_path = Path(self.data_dir) / f'market_data/derivatives/futures_ohlcv/{venue}_BTCUSDT_perp_1h_2024-01-01_2025-09-30.csv'
            
            df = _validate_data_file(file_path)
            self._validate_timestamp_alignment(df, f'{venue} BTC futures')
            
            self.data[f'{venue}_futures'] = df
            logger.info(f"Loaded {venue} BTC futures: {len(df)} records")
        
        # Set up OKX proxy from Binance
        if 'binance_futures' in self.data:
            self.data['okx_futures'] = self.data['binance_futures']
            logger.info("Using Binance BTC futures as OKX proxy")
    
    def _load_btc_funding_rates(self) -> None:
        """Load BTC funding rates for all venues."""
        for venue in self.hedge_venues:
            if venue == 'okx':
                # OKX funding rates have different date range
                file_path = Path(self.data_dir) / f'market_data/derivatives/funding_rates/{venue}_BTCUSDT_funding_rates_2024-05-01_2025-09-07.csv'
                df = _validate_data_file(
                    file_path,
                    timestamp_column="funding_timestamp",
                    strict_date_range=False
                )
            else:
                file_path = Path(self.data_dir) / f'market_data/derivatives/funding_rates/{venue}_BTCUSDT_funding_rates_2024-01-01_2025-09-30.csv'
                df = _validate_data_file(
                    file_path,
                    timestamp_column="funding_timestamp"
                )
            
            self._validate_timestamp_alignment(df, f'{venue} BTC funding rates')
            self.data[f'{venue}_funding'] = df
            logger.info(f"Loaded {venue} BTC funding rates: {len(df)} records")
    
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
        required_data = ['btc_spot_binance', 'gas_costs', 'execution_costs']
        
        # Check futures data for each venue
        for venue in self.hedge_venues:
            required_data.append(f'{venue}_futures')
            required_data.append(f'{venue}_funding')
        
        missing_data = [key for key in required_data if key not in self.data]
        
        if missing_data:
            raise DataProviderError(
                'DATA-004',
                message=f"Missing required data for BTC basis: {missing_data}",
                missing_data=missing_data,
                mode=self.mode
            )
        
        logger.info("✅ All BTC basis data requirements satisfied")
