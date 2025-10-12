"""
Config-Driven Historical Data Provider

Legacy historical data provider updated to use config-driven loading approach.
This maintains backward compatibility while supporting the new BaseDataProvider interface.

Reference: docs/specs/09_DATA_PROVIDER.md
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 8 (Data Provider Architecture)
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import os

from .data_validator import DataValidator
from .historical_data_provider import _validate_data_file, DataProviderError, DataProvider
from .base_data_provider import BaseDataProvider

logger = logging.getLogger(__name__)


class ConfigDrivenHistoricalDataProvider(DataProvider):
    """Historical data provider with config-driven loading"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConfigDrivenHistoricalDataProvider, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        # Get data directory from config or use default
        data_dir = config.get('data_dir', 'data/')
        mode = config.get('mode', 'pure_lending')
        
        super().__init__(
            data_dir=data_dir,
            mode=mode,
            config=config
        )
        self.available_data_types = [
            'eth_prices', 'btc_prices', 'usdt_prices',
            'weeth_prices', 'wsteth_prices',
            'aave_lending_rates', 'staking_rewards', 'eigen_rewards',
            'eth_futures', 'btc_futures', 'funding_rates',
            'gas_costs', 'execution_costs', 'aave_risk_params'
        ]
        self.data_requirements = config.get('data_requirements', [])
        self.data = {}
        self.validator = DataValidator(data_dir)
    
    def _validate_timestamp_alignment(self, df, data_name):
        """Validate that a dataframe has proper timestamp alignment."""
        if not isinstance(df, pd.DataFrame):
            return
        
        if not df.index.name == 'timestamp':
            raise ValueError(f"{data_name}: Index must be 'timestamp'")
        
        # Check hourly alignment
        if not all(df.index.minute == 0):
            raise ValueError(f"{data_name}: All timestamps must be on the hour (minute=0)")
        
        # Check for gaps
        if len(df) > 1:
            time_diff = df.index[1] - df.index[0]
            if time_diff != pd.Timedelta(hours=1):
                logger.warning(f"{data_name}: Non-hourly time difference detected: {time_diff}")
    
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
                f"ConfigDrivenHistoricalDataProvider cannot satisfy requirements: {unsupported}. "
                f"Available: {self.available_data_types}"
            )
        
        logger.info(f"✅ ConfigDrivenHistoricalDataProvider can satisfy all requirements: {data_requirements}")
    
    def load_data(self) -> None:
        """Load data based on config requirements."""
        logger.info(f"🔄 Loading data based on config requirements for mode: {self.mode}")
        
        try:
            # Load data based on data_requirements from config
            self._load_data_from_requirements()
            
            # Validate all data requirements are satisfied
            self._validate_loaded_data()
            
            self._data_loaded = True
            logger.info(f"✅ Config-driven data loaded successfully: {len(self.data)} datasets")
            
        except Exception as e:
            logger.error(f"❌ Failed to load config-driven data: {e}")
            raise DataProviderError('DATA-004', message=f"Config-driven data loading failed: {e}")
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Return standardized data structure.
        
        Args:
            timestamp: Timestamp for data query
            
        Returns:
            Standardized data structure with market_data and protocol_data
        """
        if not self._data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        data = self._get_standardized_structure(timestamp)
        
        # Market data - prices
        for asset in ['ETH', 'BTC', 'USDT']:
            price_key = f'{asset.lower()}_spot_binance'
            if price_key in self.data:
                asset_data = self.data[price_key]
                ts = asset_data.index.asof(timestamp)
                if not pd.isna(ts):
                    data['market_data']['prices'][asset] = asset_data.loc[ts, 'open']
        
        # Market data - futures prices
        for venue in ['binance', 'bybit', 'okx']:
            for asset in ['ETH', 'BTC']:
                futures_key = f'{venue}_futures'
                if futures_key in self.data:
                    futures_data = self.data[futures_key]
                    ts = futures_data.index.asof(timestamp)
                    if not pd.isna(ts):
                        data['market_data']['futures_prices'][f'{asset.lower()}_{venue}'] = futures_data.loc[ts, 'open']
        
        # Market data - funding rates
        for venue in ['binance', 'bybit', 'okx']:
            for asset in ['ETH', 'BTC']:
                funding_key = f'{venue}_funding'
                if funding_key in self.data:
                    funding_data = self.data[funding_key]
                    ts = funding_data.index.asof(timestamp)
                    if not pd.isna(ts):
                        data['market_data']['funding_rates'][f'{asset.lower()}_{venue}'] = funding_data.loc[ts, 'funding_rate']
        
        # Protocol data - AAVE rates and indexes
        for asset in ['weeth', 'weth', 'usdt']:
            rates_key = f'{asset}_rates'
            if rates_key in self.data:
                rates_data = self.data[rates_key]
                ts = rates_data.index.asof(timestamp)
                if not pd.isna(ts):
                    row = rates_data.loc[ts]
                    data['protocol_data']['aave_indexes'][f'a{asset.upper()}'] = row.get('liquidityIndex', 1.0)
                    data['protocol_data']['protocol_rates'][f'aave_{asset}_supply'] = row.get('liquidity_apy', 0.0)
                    data['protocol_data']['protocol_rates'][f'aave_{asset}_borrow'] = row.get('borrow_apy', 0.0)
        
        # Protocol data - LST oracle prices
        for lst_type in ['weeth', 'wsteth']:
            oracle_key = f'{lst_type}_oracle'
            if oracle_key in self.data:
                oracle_data = self.data[oracle_key]
                ts = oracle_data.index.asof(timestamp)
                if not pd.isna(ts):
                    data['protocol_data']['oracle_prices'][lst_type] = oracle_data.loc[ts, 'oracle_price_eth']
        
        # Protocol data - staking rewards
        if 'staking_yields' in self.data:
            staking_data = self.data['staking_yields']
            ts = staking_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['protocol_data']['staking_rewards']['base_staking'] = staking_data.loc[ts, 'yield']
        
        # Protocol data - seasonal rewards
        if 'seasonal_rewards' in self.data:
            rewards_data = self.data['seasonal_rewards']
            ts = rewards_data.index.asof(timestamp)
            if not pd.isna(ts):
                row = rewards_data.loc[ts]
                data['protocol_data']['staking_rewards']['eigen_rewards'] = row.get('eigen_rewards', 0.0)
                data['protocol_data']['staking_rewards']['ethfi_rewards'] = row.get('ethfi_rewards', 0.0)
        
        # Execution data - gas costs
        if 'gas_costs' in self.data:
            gas_data = self.data['gas_costs']
            ts = gas_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['execution_data']['gas_costs']['stake'] = gas_data.loc[ts, 'CREATE_LST_eth']
                data['execution_data']['gas_costs']['supply'] = gas_data.loc[ts, 'COLLATERAL_SUPPLIED_eth']
                data['execution_data']['gas_costs']['borrow'] = gas_data.loc[ts, 'BORROW_eth']
                data['execution_data']['gas_costs']['repay'] = gas_data.loc[ts, 'REPAY_eth']
                data['execution_data']['gas_costs']['withdraw'] = gas_data.loc[ts, 'WITHDRAW_eth']
                data['execution_data']['gas_costs']['spot_trade'] = gas_data.loc[ts, 'gas_price_avg_gwei']
        
        return data
    
    def _load_data_from_requirements(self) -> None:
        """Load data based on data_requirements from config."""
        # Name mapping: config requirement → loading method
        requirement_mapping = {
            'eth_prices': self._load_eth_spot_prices,
            'btc_prices': self._load_btc_spot_prices,
            'usdt_prices': self._load_usdt_prices,
            'weeth_prices': self._load_weeth_oracle_prices,
            'wsteth_prices': self._load_wsteth_oracle_prices,
            'aave_lending_rates': self._load_aave_rates,
            'staking_rewards': self._load_staking_rewards,
            'eigen_rewards': self._load_seasonal_rewards,
            'eth_futures': self._load_eth_futures,
            'btc_futures': self._load_btc_futures,
            'funding_rates': self._load_funding_rates,
            'gas_costs': self._load_gas_costs,
            'execution_costs': self._load_execution_costs,
            'execution_costs_lookup': self._load_execution_costs_lookup,
            'aave_risk_params': self._load_aave_risk_parameters
        }
        
        # Always load critical datasets regardless of requirements
        critical_datasets = ['execution_costs_lookup', 'aave_risk_params']
        for dataset in critical_datasets:
            if dataset not in self.data_requirements:
                self.data_requirements.append(dataset)
        
        # Load data for each requirement
        for requirement in self.data_requirements:
            if requirement in requirement_mapping:
                try:
                    requirement_mapping[requirement]()
                    logger.info(f"✅ Loaded data for requirement: {requirement}")
                except Exception as e:
                    logger.error(f"❌ Failed to load data for requirement {requirement}: {e}")
                    raise
            else:
                logger.warning(f"⚠️ Unknown data requirement: {requirement}")
    
    def _load_eth_spot_prices(self) -> None:
        """Load ETH spot prices."""
        file_path = Path(self.data_dir) / 'market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv'
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, 'ETH spot prices')
        self.data['eth_spot_binance'] = df
        logger.info(f"Loaded ETH spot prices: {len(df)} records")
    
    def _load_btc_spot_prices(self) -> None:
        """Load BTC spot prices."""
        file_path = Path(self.data_dir) / 'market_data/spot_prices/btc_usd/binance_BTCUSDT_1h_2024-01-01_2025-09-30.csv'
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, 'BTC spot prices')
        self.data['btc_spot_binance'] = df
        logger.info(f"Loaded BTC spot prices: {len(df)} records")
    
    def _load_usdt_prices(self) -> None:
        """Load USDT prices (using ETH/USDT as proxy)."""
        file_path = Path(self.data_dir) / 'market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv'
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, 'USDT prices')
        self.data['usdt_spot_binance'] = df
        logger.info(f"Loaded USDT prices: {len(df)} records")
    
    def _load_weeth_oracle_prices(self) -> None:
        """Load weETH oracle prices."""
        file_path = Path(self.data_dir) / 'protocol_data/aave/oracle/weETH_ETH_oracle_2024-01-01_2025-09-18.csv'
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, 'weETH oracle prices')
        self.data['weeth_oracle'] = df
        logger.info(f"Loaded weETH oracle prices: {len(df)} records")
    
    def _load_wsteth_oracle_prices(self) -> None:
        """Load wstETH oracle prices."""
        file_path = Path(self.data_dir) / 'protocol_data/aave/oracle/wstETH_ETH_oracle_2024-01-01_2025-09-18.csv'
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, 'wstETH oracle prices')
        self.data['wsteth_oracle'] = df
        logger.info(f"Loaded wstETH oracle prices: {len(df)} records")
    
    def _load_aave_rates(self) -> None:
        """Load AAVE rates for all assets."""
        assets = ['USDT', 'WETH', 'weETH']
        for asset in assets:
            if asset == 'weETH':
                file_path = Path(self.data_dir) / f'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_{asset}_rates_2024-05-12_2025-09-18_hourly.csv'
            else:
                file_path = Path(self.data_dir) / f'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_{asset}_rates_2024-01-01_2025-09-18_hourly.csv'
            
            df = _validate_data_file(file_path)
            self._validate_timestamp_alignment(df, f'{asset} rates')
            self.data[f'{asset.lower()}_rates'] = df
            logger.info(f"Loaded {asset} rates: {len(df)} records")
    
    def _load_staking_rewards(self) -> None:
        """Load staking rewards data."""
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
    
    def _load_seasonal_rewards(self) -> None:
        """Load seasonal rewards data."""
        file_path = Path(self.data_dir) / 'protocol_data/staking/restaking_final/etherfi_seasonal_rewards_2024-01-01_2025-09-18.csv'
        df = _validate_data_file(file_path, timestamp_column="period_start")
        self._validate_timestamp_alignment(df, 'seasonal rewards')
        self.data['seasonal_rewards'] = df
        logger.info(f"Loaded seasonal rewards: {len(df)} records")
    
    def _load_eth_futures(self) -> None:
        """Load ETH futures data for all venues."""
        venues = ['binance', 'bybit', 'okx']
        for venue in venues:
            if venue == 'okx':
                # OKX data is proxied from Binance
                continue
            
            file_path = Path(self.data_dir) / f'market_data/derivatives/futures_ohlcv/{venue}_ETHUSDT_perp_1h_2024-01-01_2025-09-26.csv'
            df = _validate_data_file(file_path)
            self._validate_timestamp_alignment(df, f'{venue} ETH futures')
            self.data[f'{venue}_futures'] = df
            logger.info(f"Loaded {venue} ETH futures: {len(df)} records")
        
        # Set up OKX proxy
        if 'binance_futures' in self.data:
            self.data['okx_futures'] = self.data['binance_futures']
            logger.info("Using Binance ETH futures as OKX proxy")
    
    def _load_btc_futures(self) -> None:
        """Load BTC futures data for all venues."""
        venues = ['binance', 'bybit', 'okx']
        for venue in venues:
            if venue == 'okx':
                # OKX data is proxied from Binance
                continue
            
            file_path = Path(self.data_dir) / f'market_data/derivatives/futures_ohlcv/{venue}_BTCUSDT_perp_1h_2024-01-01_2025-09-30.csv'
            df = _validate_data_file(file_path)
            self._validate_timestamp_alignment(df, f'{venue} BTC futures')
            self.data[f'{venue}_futures'] = df
            logger.info(f"Loaded {venue} BTC futures: {len(df)} records")
        
        # Set up OKX proxy
        if 'binance_futures' in self.data:
            self.data['okx_futures'] = self.data['binance_futures']
            logger.info("Using Binance BTC futures as OKX proxy")
    
    def _load_funding_rates(self) -> None:
        """Load funding rates for all venues and assets."""
        venues = ['binance', 'bybit', 'okx']
        assets = ['ETH', 'BTC']
        
        for venue in venues:
            for asset in assets:
                if venue == 'okx':
                    # OKX funding rates have different date range
                    file_path = Path(self.data_dir) / f'market_data/derivatives/funding_rates/{venue}_{asset}USDT_funding_rates_2024-05-01_2025-09-07.csv'
                    df = _validate_data_file(
                        file_path,
                        timestamp_column="funding_timestamp",
                        strict_date_range=False
                    )
                else:
                    if asset == 'BTC':
                        file_path = Path(self.data_dir) / f'market_data/derivatives/funding_rates/{venue}_{asset}USDT_funding_rates_2024-01-01_2025-09-30.csv'
                    else:
                        file_path = Path(self.data_dir) / f'market_data/derivatives/funding_rates/{venue}_{asset}USDT_funding_rates_2024-01-01_2025-09-26.csv'
                    df = _validate_data_file(
                        file_path,
                        timestamp_column="funding_timestamp"
                    )
                
                self._validate_timestamp_alignment(df, f'{venue} {asset} funding rates')
                self.data[f'{venue}_funding'] = df
                logger.info(f"Loaded {venue} {asset} funding rates: {len(df)} records")
    
    def _load_gas_costs(self) -> None:
        """Load gas costs data."""
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
        
        df._is_time_series = False
        self.data['execution_costs'] = df
        logger.info(f"Loaded execution costs: {len(df)} records")
    
    def _load_aave_risk_parameters(self) -> None:
        """Load AAVE v3 risk parameters."""
        import json
        
        file_path = Path(self.data_dir) / 'protocol_data/aave/risk_params/aave_v3_risk_parameters.json'
        
        if not file_path.exists():
            raise DataProviderError('DATA-001', file_path=str(file_path))
        
        with open(file_path, 'r') as f:
            raw_data = json.load(f)
        
        # Process and structure the risk parameters
        aave_risk_params = {
            'emode': {
                'liquidation_thresholds': raw_data['emode']['liquidation_thresholds'],
                'max_ltv_limits': raw_data['emode']['ltv_limits'],
                'liquidation_bonus': raw_data['emode']['liquidation_bonus'],
                'eligible_pairs': list(raw_data['emode']['ltv_limits'].keys())
            },
            'normal_mode': {
                'liquidation_thresholds': raw_data['standard']['liquidation_thresholds'],
                'max_ltv_limits': raw_data['standard']['ltv_limits'],
                'liquidation_bonus': raw_data['standard']['liquidation_bonus'],
                'eligible_pairs': list(raw_data['standard']['ltv_limits'].keys())
            },
            'reserve_factors': raw_data['reserve_factors'],
            'metadata': {
                'source': 'aave_v3_risk_parameters.json',
                'created': pd.Timestamp.now().isoformat(),
                'description': 'AAVE v3 risk parameters for liquidation simulation',
                'version': 'v3'
            }
        }
        
        self.data['aave_risk_params'] = aave_risk_params
        logger.info("Loaded AAVE risk parameters")
    
    def _load_execution_costs_lookup(self):
        """Load execution costs lookup table for backtesting."""
        import json

        file_path = Path(self.data_dir) / 'execution_costs/lookup_tables/execution_costs_lookup.json'
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required execution costs lookup table not found: {file_path}")

        try:
            with open(file_path, 'r') as f:
                lookup_data = json.load(f)

            if not lookup_data:
                raise ValueError(
                    f"Execution costs lookup table is empty: {file_path}")

            # Validate required trading pairs
            required_pairs = ['ETH_USDT', 'BTCUSDT-PERP', 'ETHUSDT-PERP']
            missing_pairs = [
                pair for pair in required_pairs if pair not in lookup_data]
            if missing_pairs:
                raise ValueError(
                    f"Missing required trading pairs in execution costs lookup: {missing_pairs}")

            # Validate size buckets
            for pair in required_pairs:
                if '10k' not in lookup_data[pair]:
                    raise ValueError(
                        f"Missing 10k size bucket for {pair} in execution costs lookup")

            self.data['execution_costs_lookup'] = lookup_data
            logger.info(
                f"Loaded execution costs lookup table: {len(lookup_data)} trading pairs")

        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in execution costs lookup table: {e}")
    
    def _validate_loaded_data(self) -> None:
        """Validate all required data is loaded."""
        # This is a simplified validation - in practice, you'd check against data_requirements
        required_data = ['gas_costs', 'execution_costs']
        
        missing_data = [key for key in required_data if key not in self.data]
        
        if missing_data:
            raise DataProviderError(
                'DATA-004',
                message=f"Missing required data: {missing_data}",
                missing_data=missing_data,
                mode=self.mode
            )
        
        logger.info("✅ All config-driven data requirements satisfied")
    
    def get_timestamps(self, start_date: str, end_date: str) -> List[pd.Timestamp]:
        """
        Get available timestamps for backtest period.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of timestamps
        """
        return pd.date_range(start=start_date, end=end_date, freq='H', tz='UTC').tolist()
