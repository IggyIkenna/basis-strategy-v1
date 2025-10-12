"""
Data Provider Component

Provides market data (prices, rates, indices) to all components with hourly alignment enforcement.

Key Principles:
- Hourly alignment: For backtest ALL data must be on the hour UTC timezone (minute=0, second=0)
- Mode-aware loading: Only load data needed for the mode
- Per-exchange data: Track separate prices per CEX (Binance ≠ Bybit ≠ OKX)
- Backtest: Load from CSV files
- Live: Query from WebSocket/REST APIs

Does NOT:
- Calculate anything (pure data access)
- Track state (stateless lookups)
- Make decisions (just provides data)
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime, timezone
import re

from ...core.error_codes.error_code_registry import get_error_info, ErrorCodeInfo

logger = logging.getLogger(__name__)


class DataProviderError(Exception):
    """Custom exception for data provider errors with error codes."""
    
    def __init__(self, error_code: str, message: str = None, **kwargs):
        self.error_code = error_code
        error_info = get_error_info(error_code)
        
        if error_info:
            self.component = error_info.component
            self.severity = error_info.severity
            self.description = error_info.description
            self.resolution = error_info.resolution
            
            # Use provided message or default from error code
            self.message = message or error_info.message
        else:
            # Fallback if error code not found
            self.component = "DATA"
            self.severity = "HIGH"
            self.message = message or f"Unknown error: {error_code}"
        
        # Add any additional context
        self.context = kwargs
        
        # Create the full error message
        full_message = f"{error_code}: {self.message}"
        if self.context:
            context_str = ", ".join([f"{k}={v}" for k, v in self.context.items()])
            full_message += f" ({context_str})"
        
        super().__init__(full_message)


def _parse_timestamp_robust(timestamp_series):
    """Robust timestamp parsing that handles various formats."""
    # Check if these look like Unix timestamps (10 digits) first
    if timestamp_series.dtype in ['int64', 'float64']:
        try:
            # Check if first value looks like Unix timestamp (10 digits)
            first_val = int(timestamp_series.iloc[0])
            if 1000000000 <= first_val <= 9999999999:  # Unix timestamp range
                return pd.to_datetime(timestamp_series, unit='s', utc=True)
        except BaseException:
            pass

    try:
        # First try standard pandas parsing
        return pd.to_datetime(timestamp_series, utc=True)
    except BaseException:
        try:
            # Clean up malformed timestamps (remove Z if +00:00 is present)
            cleaned = timestamp_series.str.replace(
                r'\+00:00Z$', '+00:00', regex=True)
            return pd.to_datetime(cleaned, utc=True)
        except BaseException:
            try:
                # Try ISO8601 format
                return pd.to_datetime(
                    timestamp_series, format='ISO8601', utc=True)
            except BaseException:
                # Last resort: try mixed format
                return pd.to_datetime(
                    timestamp_series, format='mixed', utc=True)


def _validate_data_file(
        file_path: Path,
        required_start_date: str = None,
        required_end_date: str = None,
        timestamp_column: str = "timestamp",
        strict_date_range: bool = True) -> pd.DataFrame:
    """Validate data file exists and has required date range."""
    if not file_path.exists():
        raise DataProviderError(
            'DATA-001',
            file_path=str(file_path)
        )

    # Handle CSV files with comments
    try:
        df = pd.read_csv(file_path, comment='#')
    except Exception as e:
        raise DataProviderError(
            'DATA-002',
            message=f"Failed to parse CSV file: {e}",
            file_path=str(file_path)
        )
    
    if df.empty:
        raise DataProviderError(
            'DATA-003',
            message="Data file is empty",
            file_path=str(file_path)
        )

    # Check if timestamp column exists
    if timestamp_column not in df.columns:
        raise DataProviderError(
            'DATA-010',
            message=f"Missing required column: {timestamp_column}",
            file_path=str(file_path),
            available_columns=list(df.columns)
        )

    # Parse timestamps
    try:
        df['timestamp'] = _parse_timestamp_robust(df[timestamp_column])
        df = df.set_index('timestamp').sort_index()
    except Exception as e:
        raise DataProviderError(
            'DATA-002',
            message=f"Failed to parse timestamps: {e}",
            file_path=str(file_path),
            timestamp_column=timestamp_column
        )

    # Validate date range (only if strict_date_range is True)
    if strict_date_range:
        # Use provided dates or fall back to environment variables
        if required_start_date is None or required_end_date is None:
            import os
            required_start_date = required_start_date or os.getenv('BASIS_DATA_START_DATE')
            required_end_date = required_end_date or os.getenv('BASIS_DATA_END_DATE')
            
            if not required_start_date or not required_end_date:
                raise DataProviderError(
                    'DATA-013',
                    file_path=str(file_path),
                    missing_vars='BASIS_DATA_START_DATE' if not required_start_date else 'BASIS_DATA_END_DATE'
                )
        
        start_date = pd.Timestamp(required_start_date, tz='UTC')
        end_date = pd.Timestamp(required_end_date, tz='UTC')

        # Allow 1 hour tolerance for start date
        if df.index.min() > start_date + pd.Timedelta(hours=1):
            raise DataProviderError(
                'DATA-004',
                message="Data file starts too late",
                file_path=str(file_path),
                file_start=df.index.min(),
                required_start=start_date + pd.Timedelta(hours=1)
            )

        if df.index.max() < end_date:
            raise DataProviderError(
                'DATA-004',
                message="Data file ends too early",
                file_path=str(file_path),
                file_end=df.index.max(),
                required_end=end_date
            )

    return df


class DataProvider:
    """Provides market data with hourly alignment enforcement."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DataProvider, cls).__new__(cls)
        return cls._instance

    def __init__(
            self,
            data_dir: str,
            mode: str,
            config: Optional[Dict] = None,
            backtest_start_date: Optional[str] = None,
            backtest_end_date: Optional[str] = None):
        """
        Initialize data provider.

        Args:
            data_dir: Path to data directory (e.g., 'data/')
            mode: Strategy mode ('pure_lending', 'eth_leveraged', etc.)
            config: Configuration dictionary
            backtest_start_date: Start date for backtest validation (YYYY-MM-DD format)
            backtest_end_date: End date for backtest validation (YYYY-MM-DD format)
        """
        self.data_dir = Path(data_dir)
        self.mode = mode
        self.config = config or {}
        self.data = {}
        self.backtest_start_date = backtest_start_date
        self.backtest_end_date = backtest_end_date
        self._data_loaded = False

        # Historical data provider is always for backtest mode
        # No data loading at initialization - data loaded on-demand via load_data_for_backtest()
        logger.info(f"DataProvider initialized for mode: {mode} (data will be loaded on-demand)")

    def load_data_for_backtest(self, mode: str, start_date: str, end_date: str):
        """
        Load data on-demand for backtest with date range validation.
        
        Args:
            mode: Strategy mode ('pure_lending', 'eth_leveraged', etc.)
            start_date: Start date for backtest (YYYY-MM-DD format)
            end_date: End date for backtest (YYYY-MM-DD format)
            
        Raises:
            DataProviderError: If date range validation fails or data loading fails
        """
        # Update instance attributes
        self.mode = mode
        self.backtest_start_date = start_date
        self.backtest_end_date = end_date
        
        # Validate date range against available data range
        self._validate_backtest_dates(start_date, end_date)
        
        # Load data for the specific mode
        self._load_data_for_mode()
        
        # Validate hourly alignment
        self._validate_timestamps()
        
        # Mark data as loaded
        self._data_loaded = True
        
        logger.info(f"Data loaded for backtest: mode={mode}, start={start_date}, end={end_date}, datasets={len(self.data)}")

    def _validate_backtest_dates(self, start_date: str = None, end_date: str = None):
        """Validate backtest dates against available data range from environment variables."""
        import os
        
        # Use provided dates or instance attributes
        request_start = start_date or self.backtest_start_date
        request_end = end_date or self.backtest_end_date
        
        if not request_start or not request_end:
            raise DataProviderError(
                'DATA-014',
                message="Backtest start_date and end_date must be provided",
                start_date=request_start,
                end_date=request_end
            )
        
        # Get available data range from environment variables
        data_start_date = os.getenv('BASIS_DATA_START_DATE')
        data_end_date = os.getenv('BASIS_DATA_END_DATE')
        
        if not data_start_date or not data_end_date:
            raise DataProviderError(
                'DATA-013',
                message="BASIS_DATA_START_DATE and BASIS_DATA_END_DATE must be set",
                backtest_start_date=request_start,
                backtest_end_date=request_end,
                missing_vars='BASIS_DATA_START_DATE' if not data_start_date else 'BASIS_DATA_END_DATE'
            )
        
        try:
            # Convert to pandas timestamps for comparison
            data_start = pd.Timestamp(data_start_date, tz='UTC')
            data_end = pd.Timestamp(data_end_date, tz='UTC')
            backtest_start = pd.Timestamp(request_start, tz='UTC')
            backtest_end = pd.Timestamp(request_end, tz='UTC')
            
            # Validate backtest dates are within available data range
            if backtest_start < data_start:
                raise DataProviderError(
                    'DATA-011',
                    backtest_start_date=backtest_start.date(),
                    data_start_date=data_start.date(),
                    available_range=f"{data_start.date()} to {data_end.date()}"
                )
            
            if backtest_end > data_end:
                raise DataProviderError(
                    'DATA-011',
                    backtest_end_date=backtest_end.date(),
                    data_end_date=data_end.date(),
                    available_range=f"{data_start.date()} to {data_end.date()}"
                )
            
            logger.info(f"✅ Backtest dates validated: {backtest_start.date()} to {backtest_end.date()} (within data range: {data_start.date()} to {data_end.date()})")
            
        except DataProviderError:
            # Re-raise our custom errors as-is
            raise
        except Exception as e:
            # Handle other exceptions (like invalid date format)
            raise DataProviderError(
                'DATA-003',
                message=f"Invalid date format in backtest dates: {e}",
                backtest_start_date=self.backtest_start_date,
                backtest_end_date=self.backtest_end_date
            )

    def _load_data_for_mode(self):
        """
        Load only data needed for the specified mode.
        
        This method follows the canonical principle of mode-aware loading:
        - Load only data required by the strategy mode
        - Fail fast if required data files are missing
        - Use data_requirements from config to determine what to load
        
        Mode-specific data loading:
        - pure_lending: USDT rates, gas costs, execution costs
        - btc_basis: BTC spot, BTC futures, BTC funding rates, gas costs, execution costs
        - eth_leveraged: ETH spot, weETH rates, WETH rates, weETH oracle, staking yields, gas costs, execution costs
        - usdt_market_neutral: All ETH leveraged data plus ETH futures, ETH funding rates
        - all_data: Load all available data (for comprehensive backtesting)
        """
        logger.info(f"🔄 Loading data for mode: {self.mode}")
        
        try:
            # Always load core data required by all modes
            self._load_gas_costs()
            self._load_execution_costs()
            self._load_execution_costs_lookup()
            
            if self.mode == 'all_data':
                # Load all data for comprehensive backtesting
                self._load_all_available_data()
            elif self.mode == 'pure_lending':
                self._load_aave_rates('USDT')
                self._load_gas_costs()
                self._load_execution_costs()
            elif self.mode == 'btc_basis':
                self._load_spot_prices('BTC')
                self._load_futures_data('BTC', ['binance', 'bybit', 'okx'])
                self._load_funding_rates('BTC', ['binance', 'bybit', 'okx'])
            elif self.mode in ['eth_leveraged', 'usdt_market_neutral']:
                # Validate required configuration at startup (fail-fast)
                required_keys = ['lst_type', 'rewards_mode', 'hedge_venues']
                for key in required_keys:
                    if key not in self.config:
                        raise KeyError(f"Missing required configuration: {key}")
                
                # AAVE data
                lst_type = self.config['lst_type']
                self._load_aave_rates(lst_type)  # weETH or wstETH
                self._load_aave_rates('WETH')
                self._load_oracle_prices(lst_type)
                
                # Staking data (weETH restaking only)
                if self.config['rewards_mode'] != 'base_only':
                    self._load_seasonal_rewards()  # EIGEN + ETHFI distributions
                
                # Protocol token prices (for KING unwrapping)
                self._load_protocol_token_prices('EIGEN')
                self._load_protocol_token_prices('ETHFI')
                
                # If USDT mode, need CEX data
                if self.mode == 'usdt_market_neutral':
                    self._load_spot_prices('ETH')  # Binance spot = our ETH/USDT oracle
                    self._load_futures_data('ETH', self.config['hedge_venues'])
                    self._load_funding_rates('ETH', self.config['hedge_venues'])
            else:
                logger.warning(f"Unknown mode '{self.mode}', loading minimal data")
                self._load_aave_rates('USDT')  # Minimal fallback
            
            logger.info(f"✅ Data loaded successfully for mode: {self.mode}")
            
            # Validate data requirements
            self._validate_data_requirements()
            
        except Exception as e:
            logger.error(f"❌ Failed to load data for mode '{self.mode}': {e}")
            raise ValueError(f"Data loading failed for mode '{self.mode}': {e}")

    def _load_all_available_data(self):
        """
        Load all available data for comprehensive backtesting.
        
        This method is used when mode='all_data' to load all available data files.
        """
        logger.info("🔄 Loading ALL available data for comprehensive backtesting...")
        
        # Load AAVE data for all assets
        self._load_aave_rates('USDT')
        self._load_aave_rates('WETH') 
        self._load_aave_rates('weETH')
        self._load_aave_risk_parameters()
        
        # Load spot prices for all assets and venues
        self._load_spot_prices('ETH')  # ETH/USDT on Binance
        self._load_spot_prices('BTC')  # BTC/USDT on Binance
        self._load_spot_prices_bybit('ETH')    # ETH on Bybit
        self._load_spot_prices_bybit('BTC')    # BTC on Bybit
        self._load_spot_prices_okx('BTC')      # BTC on OKX (proxied from Binance)
        
        # Load futures data for all assets and venues
        self._load_futures_data('ETH', ['binance', 'bybit', 'okx'])
        self._load_futures_data('BTC', ['binance', 'bybit', 'okx'])
        # Note: OKX futures data proxied from Binance due to API issues
        
        # Load funding rates for all venues and assets
        self._load_funding_rates('ETH', ['binance', 'bybit', 'okx'])
        self._load_funding_rates('BTC', ['binance', 'bybit', 'okx'])
        
        # Load LST-specific data
        self._load_oracle_prices('weETH')
        self._load_oracle_prices('wstETH')
        self._load_lst_market_prices('weETH')
        self._load_lst_market_prices('wstETH')
        
        # Load protocol token prices
        self._load_protocol_token_prices('EIGEN')
        self._load_protocol_token_prices('ETHFI')
        
        # Load staking yields
        self._load_staking_yields()
        
        # Load seasonal rewards data
        self._load_seasonal_rewards()
        
        # Load venue-specific risk parameters
        self.get_bybit_margin_requirements()
        self.get_binance_margin_requirements()
        self.get_okx_margin_requirements()
        
        logger.info("✅ ALL available data loaded successfully")

    def _validate_data_at_startup(self):
        """
        Phase 2: Validate all loaded data at startup.
        
        Validates:
        - All required data files exist and were loaded
        - Data coverage for the required date range (BASIS_DATA_START_DATE to BASIS_DATA_END_DATE)
        - Data quality (no missing values, valid timestamps)
        - Data synchronization across venues
        
        Fails fast if any validation errors are found.
        """
        logger.info("🔍 Validating all loaded data...")
        
        try:
            # Get required date range from environment variables
            import os
            start_date = os.getenv('BASIS_DATA_START_DATE')
            end_date = os.getenv('BASIS_DATA_END_DATE')
            
            if not start_date or not end_date:
                raise ValueError("BASIS_DATA_START_DATE and BASIS_DATA_END_DATE must be set")
            
            start_ts = pd.Timestamp(start_date, tz='UTC')
            end_ts = pd.Timestamp(end_date, tz='UTC')
            
            # Validate each loaded dataset (using actual dataset keys)
            required_datasets = [
                'gas_costs', 'execution_costs', 'usdt_rates', 'weth_rates', 
                'weeth_rates', 'aave_risk_params', 'eth_spot_binance', 'btc_spot_binance'
            ]
            
            missing_datasets = []
            invalid_datasets = []
            
            for dataset_name in required_datasets:
                if dataset_name not in self.data:
                    missing_datasets.append(dataset_name)
                    continue
                
                data = self.data[dataset_name]
                
                # Skip non-time-series data (like risk parameters)
                if not isinstance(data, pd.DataFrame) or data.index.name != 'timestamp':
                    continue
                    
                # Validate date coverage
                data_start = data.index.min()
                data_end = data.index.max()
                
                # Allow 1 hour tolerance for start date (as in _validate_data_file)
                if data_start > start_ts + pd.Timedelta(hours=1):
                    invalid_datasets.append(f"{dataset_name}: starts too late ({data_start} > {start_ts + pd.Timedelta(hours=1)})")
                
                if data_end < end_ts:
                    invalid_datasets.append(f"{dataset_name}: ends too early ({data_end} < {end_ts})")
                
                # Validate data quality
                if data.isnull().any().any():
                    invalid_datasets.append(f"{dataset_name}: contains null values")
            
            # Report validation results
            if missing_datasets:
                raise ValueError(f"Missing required datasets: {missing_datasets}")
            
            if invalid_datasets:
                raise ValueError(f"Invalid datasets: {invalid_datasets}")
            
            logger.info(f"✅ Data validation passed for {len(self.data)} datasets")
            logger.info(f"📊 Data coverage: {start_ts} to {end_ts}")
            
        except Exception as e:
            logger.error(f"❌ Data validation failed: {e}")
            raise ValueError(f"Data validation failed: {e}")

    # REMOVED: _load_data_for_mode() method - Phase 2: Historical provider always loads ALL data
    # Mode-specific data loading is now handled by LiveDataProvider for live mode
    # Historical provider focuses on comprehensive data loading for all modes at startup
    def get_health_status(self) -> Dict[str, Any]:
        """Get data provider health status with error codes and structured logging."""
        health_status = {
            'status': 'healthy',
            'datasets_loaded': len(self.data),
            'missing_datasets': [],
            'errors': [],
            'warnings': []
        }
        
        # Check for critical missing datasets
        critical_datasets = [
            'gas_costs',
            'execution_costs', 
            'execution_costs_lookup',
            'aave_risk_params'
        ]
        
        for dataset in critical_datasets:
            if dataset not in self.data:
                error_msg = f"Critical dataset missing: {dataset}"
                health_status['errors'].append({
                    'code': 'DATA-001',
                    'message': error_msg,
                    'dataset': dataset
                })
                health_status['missing_datasets'].append(dataset)
                health_status['status'] = 'unhealthy'
        
        # Check for important missing datasets (warnings)
        important_datasets = [
            'usdt_rates',
            'eth_spot_binance',
            'btc_spot_binance'
        ]
        
        for dataset in important_datasets:
            if dataset not in self.data:
                warning_msg = f"Important dataset missing: {dataset}"
                health_status['warnings'].append({
                    'code': 'DATA-005',
                    'message': warning_msg,
                    'dataset': dataset
                })
        
        # Log structured errors if any
        if health_status['errors']:
            for error in health_status['errors']:
                logger.error(
                    f"DATA-{error['code']}: {error['message']}",
                    extra={
                        'error_code': error['code'],
                        'dataset': error['dataset'],
                        'component': 'data_provider'
                    }
                )
        
        # Log structured warnings if any
        if health_status['warnings']:
            for warning in health_status['warnings']:
                logger.warning(
                    f"DATA-{warning['code']}: {warning['message']}",
                    extra={
                        'error_code': warning['code'],
                        'dataset': warning['dataset'],
                        'component': 'data_provider'
                    }
                )
        
        return health_status
    
    def _load_venue_risk_parameters(self):
        """Load venue-specific risk parameters."""
        # Load Bybit margin requirements
        try:
            bybit_margin = self.get_bybit_margin_requirements()
            self.data['bybit_margin_requirements'] = bybit_margin
        except Exception as e:
            logger.warning(f"Failed to load Bybit margin requirements: {e}")
        
        # Load Binance margin requirements
        try:
            binance_margin = self.get_binance_margin_requirements()
            self.data['binance_margin_requirements'] = binance_margin
        except Exception as e:
            logger.warning(f"Failed to load Binance margin requirements: {e}")
        
        # Load OKX margin requirements
        try:
            okx_margin = self.get_okx_margin_requirements()
            self.data['okx_margin_requirements'] = okx_margin
        except Exception as e:
            logger.warning(f"Failed to load OKX margin requirements: {e}")

    def _validate_data_requirements(self):
        """Validate all required data is loaded based on mode config.

        Uses data_requirements list from mode config with name mapping.
        Returns True if all requirements are met, False otherwise.
        """
        # Get data requirements from config
        required_data = getattr(self.config, 'data_requirements', [])

        if not required_data:
            logger.warning(
                f"No data_requirements specified for mode '{self.mode}'")
            return True  # No requirements means validation passes

        # Name mapping: config name → internal data key
        name_mapping = {
            'eth_prices': 'eth_spot_binance',
            'btc_prices': 'btc_spot_binance',
            'weeth_prices': 'weeth_oracle',
            'wsteth_prices': 'wsteth_oracle',
            'usdt_prices': 'usdt_spot_binance',
            'aave_lending_rates': ['weeth_rates', 'wsteth_rates', 'weth_rates', 'usdt_rates'],
            'staking_rewards': 'staking_yields',
            'eigen_rewards': 'seasonal_rewards',
            'ethfi_rewards': 'seasonal_rewards',
            'funding_rates': ['binance_funding', 'bybit_funding', 'okx_funding'],
            'gas_costs': 'gas_costs',
            'execution_costs': 'execution_costs',
            'aave_risk_params': 'aave_risk_params',  # NEW!
            # NEW!
            'lst_market_prices': ['weeth_market_price', 'wsteth_market_price'],
            # NEW!
            'protocol_token_prices': ['eigen_eth_price', 'eigen_usdt_price', 'ethfi_eth_price', 'ethfi_usdt_price']
        }

        missing_data = []
        for requirement in required_data:
            mapped_keys = name_mapping.get(requirement)
            if mapped_keys:
                if isinstance(mapped_keys, list):
                    # Check if at least one exists
                    if not any(
                        key in self.data or hasattr(
                            self,
                            key.replace(
                                '_',
                                '')) for key in mapped_keys):
                        missing_data.append(requirement)
                else:
                    # Check single key
                    if mapped_keys not in self.data and not hasattr(
                            self, mapped_keys):
                        missing_data.append(requirement)
            else:
                # Unknown requirement
                logger.warning(f"Unknown data requirement: {requirement}")
                # Treat unknown requirements as missing
                missing_data.append(requirement)

        if missing_data:
            logger.error(
                f"Missing required data for mode '{self.mode}': {missing_data}")
            return False

        logger.info(
            f"✅ All data requirements satisfied for mode '{self.mode}'")
        return True

    def _load_aave_rates(self, asset: str):
        """Load AAVE rates with hourly validation."""
        # Hardcoded file paths (as agreed)
        file_map = {
            'weeth': 'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_weETH_rates_2024-05-12_2025-09-18_hourly.csv',
            'wsteth': 'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_wstETH_rates_2024-05-12_2025-09-18_hourly.csv',
            'weth': 'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_WETH_rates_2024-01-01_2025-09-18_hourly.csv',
            'usdt': 'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_USDT_rates_2024-01-01_2025-09-18_hourly.csv'}

        # Normalize asset name to lowercase for lookup
        asset_key = asset.lower()
        if asset_key not in file_map:
            raise ValueError(f"Unknown AAVE asset: {asset}")

        file_path = self.data_dir / file_map[asset_key]
        df = _validate_data_file(file_path)

        # Validate hourly alignment
        if not all(df.index.minute == 0):
            raise ValueError(f"{asset} rates: Timestamps must be on the hour!")

        self.data[f'{asset.lower()}_rates'] = df
        logger.info(f"Loaded {asset} rates: {len(df)} records")

    def _load_spot_prices(self, asset: str):
        """
        Load spot prices for asset with strict validation.
        
        Note: OKX spot data is proxied from Binance due to OKX API failures
        for OHLCV data retrieval. Only OKX funding rates are real (not proxied).
        """
        if asset == 'ETH':
            # Use Binance spot as our ETH/USDT oracle (primary oracle for ETH
            # vs USDT)
            file_path = self.data_dir / \
                'market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv'
            df = _validate_data_file(file_path)
            self.data['eth_spot_binance'] = df
            logger.info(f"Loaded ETH spot prices: {len(df)} records")
        elif asset == 'BTC':
            file_path = self.data_dir / \
                'market_data/spot_prices/btc_usd/binance_BTCUSDT_1h_2024-01-01_2025-09-30.csv'
            df = _validate_data_file(file_path)
            self.data['btc_spot_binance'] = df
            logger.info(f"Loaded BTC spot prices: {len(df)} records")
        else:
            raise ValueError(f"Unknown asset for spot prices: {asset}")
    
    def _load_spot_prices_bybit(self, asset: str):
        """
        Load Bybit spot prices for asset.
        
        Args:
            asset: Asset symbol ('ETH' or 'BTC')
        """
        if asset == 'ETH':
            file_path = self.data_dir / 'market_data/spot_prices/eth_usd/bybit_ETHUSDT_spot_1h_2024-01-01_2025-09-26.csv'
        elif asset == 'BTC':
            file_path = self.data_dir / 'market_data/spot_prices/btc_usd/bybit_BTCUSDT_spot_1h_2024-01-01_2025-09-30.csv'
        else:
            raise ValueError(f"Unknown asset for Bybit spot prices: {asset}")
        
        df = _validate_data_file(file_path)
        self.data[f'{asset.lower()}_spot_bybit'] = df
        logger.info(f"Loaded {asset} Bybit spot prices: {len(df)} records")
    
    def _load_spot_prices_okx(self, asset: str):
        """
        Load OKX spot prices for asset (proxied from Binance).
        
        Note: OKX spot data is proxied from Binance due to OKX API failures
        for OHLCV data retrieval.
        
        Args:
            asset: Asset symbol ('ETH' or 'BTC')
        """
        if asset == 'ETH':
            # Use Binance data as proxy for OKX
            file_path = self.data_dir / 'market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv'
        elif asset == 'BTC':
            # Use Binance data as proxy for OKX
            file_path = self.data_dir / 'market_data/spot_prices/btc_usd/binance_BTCUSDT_1h_2024-01-01_2025-09-30.csv'
        else:
            raise ValueError(f"Unknown asset for OKX spot prices: {asset}")
        
        df = _validate_data_file(file_path)
        self.data[f'{asset.lower()}_spot_okx'] = df
        logger.info(f"Loaded {asset} OKX spot prices (proxied from Binance): {len(df)} records")

    def _load_futures_data(self, asset: str, venues: List[str]):
        """
        Load futures data for asset across venues with strict validation.
        
        Note: OKX futures data is proxied from Binance due to OKX API failures
        for OHLCV data retrieval. This affects both spot and futures data.
        Only OKX funding rates are real (not proxied).
        """
        for venue in venues:
            if venue == 'okx':
                # OKX data is proxied from Binance - don't try to load OKX files
                logger.info(f"OKX {asset} futures data will be proxied from Binance")
                continue
            
            # Handle different date ranges for different assets and venues
            if asset == 'BTC':
                file_path = self.data_dir / \
                    f'market_data/derivatives/futures_ohlcv/{venue}_{asset}USDT_perp_1h_2024-01-01_2025-09-30.csv'
            elif asset == 'ETH':
                file_path = self.data_dir / \
                    f'market_data/derivatives/futures_ohlcv/{venue}_{asset}USDT_perp_1h_2024-01-01_2025-09-26.csv'
            else:
                file_path = self.data_dir / \
                    f'market_data/derivatives/futures_ohlcv/{venue}_{asset}USDT_perp_1h_2024-01-01_2025-09-30.csv'

            try:
                df = _validate_data_file(file_path)
                self.data[f'{venue}_futures'] = df
                logger.info(f"Loaded {venue} {asset} futures: {len(df)} records")
            except FileNotFoundError:
                # For non-OKX venues, missing data is an error
                raise
        
        # After loading all non-OKX venues, set up OKX proxies
        for venue in venues:
            if venue == 'okx':
                if 'binance_futures' in self.data:
                    self.data[f'{venue}_futures'] = self.data['binance_futures']
                    logger.info(f"Using Binance {asset} futures as OKX proxy")
                else:
                    logger.warning(f"Binance {asset} futures not loaded yet, skipping OKX proxy")

    def _load_funding_rates(self, asset: str, venues: List[str]):
        """Load funding rates for asset across venues with strict validation."""
        if venues is None:
            venues = ['binance', 'bybit', 'okx']  # Default venues
        for venue in venues:
            # Handle different date ranges for different venues and assets
            if venue == 'okx' and asset == 'BTC':
                file_path = self.data_dir / \
                    f'market_data/derivatives/funding_rates/{venue}_{asset}USDT_funding_rates_2024-05-01_2025-09-07.csv'
                df = _validate_data_file(
                    file_path,
                    timestamp_column="funding_timestamp",
                    strict_date_range=False)
            elif venue == 'okx' and asset == 'ETH':
                file_path = self.data_dir / \
                    f'market_data/derivatives/funding_rates/{venue}_{asset}USDT_funding_rates_2024-05-01_2025-09-07.csv'
                df = _validate_data_file(
                    file_path,
                    timestamp_column="funding_timestamp",
                    strict_date_range=False)
            else:
                # Handle different date ranges for different assets
                if asset == 'BTC':
                    file_path = self.data_dir / \
                        f'market_data/derivatives/funding_rates/{venue}_{asset}USDT_funding_rates_2024-01-01_2025-09-30.csv'
                else:
                    file_path = self.data_dir / \
                        f'market_data/derivatives/funding_rates/{venue}_{asset}USDT_funding_rates_2024-01-01_2025-09-26.csv'
                df = _validate_data_file(
                    file_path, timestamp_column="funding_timestamp")

            self.data[f'{venue}_funding'] = df
            logger.info(
                f"Loaded {venue} {asset} funding rates: {len(df)} records")

    def _load_oracle_prices(self, lst_type: str):
        """Load LST/ETH oracle prices."""
        if lst_type.lower() == 'weeth':
            file_path = self.data_dir / \
                'protocol_data/aave/oracle/weETH_ETH_oracle_2024-01-01_2025-09-18.csv'
        elif lst_type.lower() == 'wsteth':
            file_path = self.data_dir / \
                'protocol_data/aave/oracle/wstETH_ETH_oracle_2024-01-01_2025-09-18.csv'
        else:
            raise ValueError(f"Unknown LST type for oracle: {lst_type}")

        df = _validate_data_file(file_path)
        self.data[f'{lst_type.lower()}_oracle'] = df
        logger.info(f"Loaded {lst_type} oracle prices: {len(df)} records")

    def _load_lst_market_prices(self, lst_type: str):
        """Load LST/ETH market prices from DEX data (Curve, Uniswap).

        Purpose: Monitor market vs oracle price deviation
        Files:
        - data/market_data/spot_prices/lst_eth_ratios/curve_weETHWETH_1h_2024-05-12_2025-09-27.csv
        - data/market_data/spot_prices/lst_eth_ratios/uniswapv3_wstETHWETH_1h_2024-05-12_2025-09-27.csv

        Used by: RiskMonitor for oracle vs market price deviation alerts
        """
        if lst_type.lower() == 'weeth':
            file_path = self.data_dir / \
                'market_data/spot_prices/lst_eth_ratios/curve_weETHWETH_1h_2024-05-12_2025-09-27.csv'
        elif lst_type.lower() == 'wsteth':
            file_path = self.data_dir / \
                'market_data/spot_prices/lst_eth_ratios/uniswapv3_wstETHWETH_1h_2024-05-12_2025-09-27.csv'
        else:
            raise ValueError(f"Unknown LST type for market prices: {lst_type}")

        df = _validate_data_file(file_path, strict_date_range=False)
        # Data already has 'price' column, no need to rename
        self.data[f'{lst_type.lower()}_market_price'] = df
        logger.info(f"Loaded {lst_type} market prices: {len(df)} records")

    def _load_aave_risk_parameters(self):
        """Load AAVE v3 risk parameters from JSON.

        File: data/protocol_data/aave/risk_params/aave_v3_risk_parameters.json

        Contains:
        - Standard mode: LTV limits, liquidation thresholds, liquidation bonuses
        - E-mode: Higher LTV, lower bonuses for correlated assets
        - Reserve factors

        Used by: RiskMonitor liquidation simulation
        """
        import json

        file_path = self.data_dir / \
            'protocol_data/aave/risk_params/aave_v3_risk_parameters.json'

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required AAVE risk parameters not found: {file_path}")

        # Load JSON and map structure to expected format
        with open(file_path, 'r') as f:
            raw_data = json.load(f)

        # Extract individual assets from pairs and reserve factors
        individual_assets = set(raw_data['reserve_factors'].keys())

        # Add assets from pairs (extract from pair names like 'weETH_WETH' ->
        # 'weETH', 'WETH')
        for pair in raw_data['emode']['ltv_limits'].keys():
            if '_' in pair:
                assets = pair.split('_')
                individual_assets.update(assets)

        # Create individual asset parameters (use average values from pairs)
        def create_individual_asset_params(pair_data):
            individual_params = {}
            for asset in individual_assets:
                # Find pairs containing this asset and use average values
                values = []
                for pair, value in pair_data.items():
                    if asset in pair:
                        values.append(value)
                if values:
                    individual_params[asset] = sum(values) / len(values)
                else:
                    # For assets not in pairs (like USDT), use default values
                    if asset == 'USDT':
                        # Default liquidation threshold
                        # TODO-REFACTOR: This hardcodes LTV value instead of using config
                        # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - No Hardcoded Values
                        # Fix: Add to config YAML and load from config
                        individual_params[asset] = 0.85  # WRONG - hardcoded LTV value
                    else:
                        # TODO-REFACTOR: This hardcodes LTV value instead of using config
                        # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - No Hardcoded Values
                        # Fix: Add to config YAML and load from config
                        individual_params[asset] = 0.80  # WRONG - hardcoded default LTV
            return individual_params

        # Map structure to expected format
        aave_risk_params = {
            'emode': {
                'liquidation_thresholds': raw_data['emode']['liquidation_thresholds'],
                # Map ltv_limits to max_ltv_limits
                'max_ltv_limits': raw_data['emode']['ltv_limits'],
                'liquidation_bonus': raw_data['emode']['liquidation_bonus'],
                # Add eligible_pairs
                'eligible_pairs': list(raw_data['emode']['ltv_limits'].keys())
            },
            'normal_mode': {  # Map standard to normal_mode
                'liquidation_thresholds': raw_data['standard']['liquidation_thresholds'],
                # Map ltv_limits to max_ltv_limits
                'max_ltv_limits': raw_data['standard']['ltv_limits'],
                'liquidation_bonus': raw_data['standard']['liquidation_bonus'],
                # Add eligible_pairs
                'eligible_pairs': list(raw_data['standard']['ltv_limits'].keys())
            },
            'reserve_factors': raw_data['reserve_factors'],
            'metadata': {  # Add metadata
                'source': 'aave_v3_risk_parameters.json',
                # Use 'created' instead of 'loaded_at'
                'created': pd.Timestamp.now().isoformat(),
                'description': 'AAVE v3 risk parameters for liquidation simulation',
                'version': 'v3'
            }
        }

        # Add individual asset parameters to both modes for backward
        # compatibility
        for mode in ['emode', 'normal_mode']:
            aave_risk_params[mode]['liquidation_thresholds'].update(create_individual_asset_params(
                raw_data[mode if mode == 'emode' else 'standard']['liquidation_thresholds']))
            aave_risk_params[mode]['max_ltv_limits'].update(create_individual_asset_params(
                raw_data[mode if mode == 'emode' else 'standard']['ltv_limits']))
            aave_risk_params[mode]['liquidation_bonus'].update(create_individual_asset_params(
                raw_data[mode if mode == 'emode' else 'standard']['liquidation_bonus']))

        # Store in data dictionary
        self.data['aave_risk_params'] = aave_risk_params
        self.aave_risk_params = aave_risk_params  # Keep for backward compatibility

        logger.info(
            f"Loaded AAVE risk parameters: eMode liquidation threshold={aave_risk_params['emode']['liquidation_thresholds']}")

    def _validate_data_requirements(self):
        """Validate all required data is loaded based on mode config.
        
        Uses data_requirements list from mode config with name mapping.
        """
        # Get data requirements from config (fail-fast)
        if 'data_requirements' not in self.config:
            raise KeyError("Missing required configuration: data_requirements")
        required_data = self.config['data_requirements']
        
        if not required_data:
            logger.info("No data requirements specified in config, skipping validation")
            return
        
        # Name mapping: config name → internal data key
        name_mapping = {
            'eth_prices': 'eth_spot_binance',
            'btc_prices': 'btc_spot_binance',
            'weeth_prices': 'weeth_oracle',
            'wsteth_prices': 'wsteth_oracle',
            'aave_lending_rates': ['weeth_rates', 'wsteth_rates', 'weth_rates', 'usdt_rates'],
            'staking_rewards': 'staking_yields',
            'eigen_rewards': 'seasonal_rewards',
            'ethfi_rewards': 'seasonal_rewards',
            'funding_rates': ['binance_funding', 'bybit_funding', 'okx_funding'],
            'gas_costs': 'gas_costs',
            'execution_costs': 'execution_costs',
            'aave_risk_params': 'aave_risk_params',
            'lst_market_prices': ['weeth_market_price', 'wsteth_market_price']
        }
        
        missing_data = []
        for requirement in required_data:
            mapped_keys = name_mapping.get(requirement)
            if mapped_keys:
                if isinstance(mapped_keys, list):
                    # Check if at least one exists
                    if not any(key in self.data or hasattr(self, key.replace('_', '')) for key in mapped_keys):
                        missing_data.append(requirement)
                else:
                    # Check single key
                    if mapped_keys not in self.data and not hasattr(self, mapped_keys.replace('_', '')):
                        missing_data.append(requirement)
        
        if missing_data:
            raise DataProviderError(
                'DATA-004',
                message=f"Missing required data for mode '{self.mode}': {missing_data}",
                missing_data=missing_data,
                mode=self.mode
            )
        
        logger.info(f"✅ All data requirements satisfied for mode '{self.mode}'")

    def _load_protocol_token_prices(self, token: str):
        """Load protocol token prices (KING/EIGEN/ETHFI) for KING token unwrapping.

        File: data/market_data/spot_prices/protocol_tokens/

        Contains:
        - EIGEN/ETH prices from Uniswap V3
        - ETHFI/ETH prices from Uniswap V3
        - EIGEN/USDT prices from Binance
        - ETHFI/USDT prices from Binance

        Used by: KING token unwrapping functionality
        """
        if token.lower() == 'eigen':
            # Load EIGEN prices from both Uniswap and Binance
            uniswap_file = self.data_dir / \
                'market_data/spot_prices/protocol_tokens/uniswapv3_EIGENWETH_1h_2024-10-05_2025-09-27.csv'
            binance_file = self.data_dir / \
                'market_data/spot_prices/protocol_tokens/binance_EIGENUSDT_1h_2024-10-05_2025-09-30.csv'

            if uniswap_file.exists():
                df_uniswap = _validate_data_file(
                    uniswap_file, strict_date_range=False)
                # EIGEN/ETH price (uniswap has 'close' column)
                df_uniswap['price'] = df_uniswap['close']
                self.data['eigen_eth_price'] = df_uniswap
                logger.info(
                    f"Loaded EIGEN/ETH prices: {len(df_uniswap)} records")

            if binance_file.exists():
                df_binance = _validate_data_file(
                    binance_file, strict_date_range=False)
                # Data already has 'price' column, no need to rename
                self.data['eigen_usdt_price'] = df_binance
                logger.info(
                    f"Loaded EIGEN/USDT prices: {len(df_binance)} records")

        elif token.lower() == 'ethfi':
            # Load ETHFI prices from both Uniswap and Binance
            uniswap_file = self.data_dir / \
                'market_data/spot_prices/protocol_tokens/uniswapv3_ETHFIWETH_1h_2024-04-01_2025-09-27.csv'
            binance_file = self.data_dir / \
                'market_data/spot_prices/protocol_tokens/binance_ETHFIUSDT_1h_2024-06-01_2025-09-30.csv'

            if uniswap_file.exists():
                df_uniswap = _validate_data_file(
                    uniswap_file, strict_date_range=False)
                # ETHFI/ETH price (uniswap has 'close' column)
                df_uniswap['price'] = df_uniswap['close']
                self.data['ethfi_eth_price'] = df_uniswap
                logger.info(
                    f"Loaded ETHFI/ETH prices: {len(df_uniswap)} records")

            if binance_file.exists():
                df_binance = _validate_data_file(
                    binance_file, strict_date_range=False)
                # Data already has 'price' column, no need to rename
                self.data['ethfi_usdt_price'] = df_binance
                logger.info(
                    f"Loaded ETHFI/USDT prices: {len(df_binance)} records")

        elif token.lower() == 'king':
            # KING token data not yet available - placeholder for future
            # implementation
            logger.warning(
                "KING token price data not available - placeholder for future implementation")
            # TODO: Add KING token price loading when data becomes available

        else:
            raise ValueError(f"Unknown protocol token: {token}")

    def _load_staking_yields(self):
        """Load staking yields data."""
        # Try multiple possible filenames for staking yields
        possible_paths = [
            self.data_dir /
            'protocol_data/staking/base_staking_yields_2024-01-01_2025-09-18_hourly.csv',
            self.data_dir /
            'protocol_data/staking/base_yields/weeth_oracle_yields_2024-01-01_2025-09-18.csv',
            self.data_dir /
            'protocol_data/staking/base_staking_yields_2024-01-01_2025-09-18.csv']

        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break

        if not file_path:
            raise FileNotFoundError(
                f"Required staking yields data not found in any expected location: {possible_paths}")

        df = _validate_data_file(file_path)
        self.data['staking_yields'] = df
        logger.info(f"Loaded staking yields: {len(df)} records")

    def _load_seasonal_rewards(self):
        """Load seasonal rewards data with strict validation."""
        file_path = self.data_dir / \
            'protocol_data/staking/restaking_final/etherfi_seasonal_rewards_2024-01-01_2025-09-18.csv'
        # Seasonal rewards has period_start/period_end instead of timestamp
        df = _validate_data_file(file_path, timestamp_column="period_start")
        self.data['seasonal_rewards'] = df
        logger.info(f"Loaded seasonal rewards: {len(df)} records")

    def _load_gas_costs(self):
        """Load gas costs data with strict validation."""
        # Try enhanced version first, fall back to regular version
        enhanced_path = self.data_dir / \
            'blockchain_data/gas_prices/ethereum_gas_prices_enhanced_2024-01-01_2025-09-26.csv'
        regular_path = self.data_dir / \
            'blockchain_data/gas_prices/ethereum_gas_prices_2024-01-01_2025-09-26.csv'

        if enhanced_path.exists():
            file_path = enhanced_path
        else:
            file_path = regular_path

        df = _validate_data_file(file_path)
        self.data['gas_costs'] = df
        logger.info(f"Loaded gas costs: {len(df)} records")
    
    # REMOVED: All _create_minimal_* methods - Phase 2: Use real data files only
    # These methods violated the fail-fast policy by creating dummy data
    # All data must come from actual CSV/JSON files in the data/ directory
    # Methods removed: _create_minimal_gas_costs, _create_minimal_execution_costs,
    # _create_minimal_aave_rates, _create_minimal_aave_risk_parameters
    
    def _load_execution_costs(self):
        """Load execution costs data with strict validation."""
        file_path = self.data_dir / 'execution_costs/execution_cost_simulation_results.csv'
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required execution costs data not found: {file_path}")

        df = pd.read_csv(file_path)
        if df.empty:
            raise ValueError(f"Execution costs file is empty: {file_path}")

        # Execution costs are lookup tables, not time series
        # Store as DataFrame but mark it as non-time-series
        df._is_time_series = False
        self.data['execution_costs'] = df
        logger.info(f"Loaded execution costs: {len(df)} records")

        # Also load the execution costs lookup table for backtesting
        self._load_execution_costs_lookup()

    def _load_execution_costs_lookup(self):
        """Load execution costs lookup table for backtesting."""
        import json

        file_path = self.data_dir / 'execution_costs/lookup_tables/execution_costs_lookup.json'
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

    def _validate_timestamps(self):
        """Ensure ALL data is on the hour."""
        for key, df in self.data.items():
            if not isinstance(df, pd.DataFrame):
                continue

            # Skip non-time-series data (like execution costs lookup tables)
            if hasattr(df, '_is_time_series') and not df._is_time_series:
                continue

            if not df.index.name == 'timestamp':
                raise ValueError(f"{key}: Index must be 'timestamp'")

            # Check hourly alignment
            if not all(df.index.minute == 0):
                bad_timestamps = df.index[df.index.minute != 0]
                raise ValueError(
                    f"{key}: {len(bad_timestamps)} timestamps not on the hour!\n"
                    f"First bad timestamp: {bad_timestamps[0]}")

            if not all(df.index.second == 0):
                raise ValueError(f"{key}: Timestamps must have second=0")

            # Check UTC timezone
            if df.index.tz is None:
                raise ValueError(
                    f"{key}: Timestamps must be UTC timezone-aware")

            logger.info(f"✅ {key}: {len(df)} hourly timestamps validated")

    def validate_data_synchronization(self):
        """Validate all data sources have overlapping periods."""
        ranges = {}
        for key, df in self.data.items():
            if isinstance(df, pd.DataFrame) and hasattr(df, 'index'):
                # Skip non-time-series data
                if hasattr(df, '_is_time_series') and not df._is_time_series:
                    continue
                # Only include DatetimeIndex data
                if isinstance(df.index, pd.DatetimeIndex):
                    ranges[key] = (df.index.min(), df.index.max())

        if not ranges:
            logger.warning(
                "No time series data found for synchronization validation")
            return {'common_start': None, 'common_end': None}

        # Find common period
        common_start = max(r[0] for r in ranges.values())
        common_end = min(r[1] for r in ranges.values())

        logger.info(f"Common data period: {common_start} to {common_end}")

        # Warn about gaps
        for key, df in self.data.items():
            if not isinstance(df, pd.DataFrame) or not hasattr(df, 'index'):
                continue

            expected = pd.date_range(common_start, common_end, freq='H')
            actual = df.index
            missing = expected.difference(actual)

            if len(missing) > 0:
                logger.warning(
                    f"{key}: {len(missing)} missing hours in common period")

        return {'common_start': common_start, 'common_end': common_end}

    def get_spot_price(self, asset: str, timestamp: pd.Timestamp) -> float:
        """Get spot price at timestamp (asof lookup)."""
        if asset == 'ETH':
            data = self.data.get('eth_spot_binance')  # Our ETH/USDT oracle
        elif asset == 'BTC':
            data = self.data.get('btc_spot_binance')
        else:
            raise ValueError(f"Unknown asset: {asset}")

        if data is None:
            raise ValueError(f"No spot price data for {asset}")

        ts = data.index.asof(timestamp)
        if pd.isna(ts):
            ts = data.index[0]  # Fallback to first

        return data.loc[ts, 'open']  # Use candle open (start of hour)

    def get_futures_price(
            self,
            asset: str,
            venue: str,
            timestamp: pd.Timestamp) -> float:
        """
        Get futures price for specific exchange.

        CRITICAL: Each exchange has different prices!
        """
        data_key = f'{venue.lower()}_futures'

        if data_key not in self.data:
            # OKX might not have data, use Binance as proxy
            logger.warning(
                f"{venue} futures data not available, using binance proxy")
            data_key = 'binance_futures'

        data = self.data[data_key]
        ts = data.index.asof(timestamp)
        if pd.isna(ts):
            ts = data.index[0]

        return data.loc[ts, 'open']  # Open price for entry, close for mark

    def get_aave_index(self, asset: str, index_type: str,
                       timestamp: pd.Timestamp) -> float:
        """
        Get AAVE liquidity or borrow index.

        CRITICAL: Indices in our data are NORMALIZED (~1.0, not 1e27)!
        """
        data_key = f'{asset.lower()}_rates'
        data = self.data[data_key]

        ts = data.index.asof(timestamp)
        if pd.isna(ts):
            ts = data.index[0]

        if index_type == 'liquidity':
            return data.loc[ts, 'liquidityIndex']  # Already normalized ~1.0
        elif index_type == 'borrow':
            # Already normalized ~1.0
            return data.loc[ts, 'variableBorrowIndex']

        # NO division by 1e27 needed (data already normalized!)
        raise ValueError(f"Unknown index type: {index_type}")

    def get_oracle_price(
            self,
            lst_type: str,
            timestamp: pd.Timestamp) -> float:
        """Get LST/ETH oracle price from AAVE oracles (for staked spread tracking)."""
        data_key = f'{lst_type.lower()}_oracle'
        data = self.data[data_key]

        ts = data.index.asof(timestamp)
        if pd.isna(ts):
            ts = data.index[0]

        return data.loc[ts, 'oracle_price_eth']  # weETH/ETH or wstETH/ETH

    def get_lst_market_price(
            self,
            lst_type: str,
            timestamp: pd.Timestamp) -> float:
        """Get LST/ETH market price from DEX data."""
        data_key = f'{lst_type.lower()}_market_price'
        data = self.data[data_key]

        ts = data.index.asof(timestamp)
        if pd.isna(ts):
            ts = data.index[0]

        return data.loc[ts, 'price']  # Market price from DEX

    def get_aave_risk_params(self) -> Dict[str, Any]:
        """Get AAVE risk parameters for liquidation simulation."""
        if 'aave_risk_params' not in self.data:
            raise ValueError(
                "AAVE risk parameters not loaded. Call _load_aave_risk_parameters() first.")
        return self.data['aave_risk_params']

    def get_protocol_token_price(
            self,
            token: str,
            timestamp: pd.Timestamp,
            price_type: str = 'eth') -> float:
        """Get protocol token price (KING/EIGEN/ETHFI) for KING token unwrapping.

        Args:
            token: Token name ('eigen', 'ethfi', 'king')
            timestamp: Timestamp for price lookup
            price_type: Price type ('eth' for ETH price, 'usdt' for USDT price)

        Returns:
            Token price in specified currency
        """
        if token.lower() == 'eigen':
            if price_type.lower() == 'eth':
                data_key = 'eigen_eth_price'
            elif price_type.lower() == 'usdt':
                data_key = 'eigen_usdt_price'
            else:
                raise ValueError(f"Unknown price type for EIGEN: {price_type}")
        elif token.lower() == 'ethfi':
            if price_type.lower() == 'eth':
                data_key = 'ethfi_eth_price'
            elif price_type.lower() == 'usdt':
                data_key = 'ethfi_usdt_price'
            else:
                raise ValueError(f"Unknown price type for ETHFI: {price_type}")
        elif token.lower() == 'king':
            # KING token data not yet available
            raise ValueError("KING token price data not available")
        else:
            raise ValueError(f"Unknown protocol token: {token}")

        if data_key not in self.data:
            raise ValueError(
                f"Protocol token price data not loaded: {data_key}")

        data = self.data[data_key]
        ts = data.index.asof(timestamp)
        if pd.isna(ts):
            ts = data.index[0]

        return data.loc[ts, 'price']

    def get_execution_cost(
            self,
            pair: str,
            notional: float,
            venue: str,
            trade_type: str) -> float:
        """Get execution cost in basis points."""
        if 'execution_costs' not in self.data:
            # Default execution costs if data not available
            return 5.0  # 5 bps default

        df = self.data['execution_costs']

        # Lookup by pair, size bucket, venue type
        size_bucket = self._get_size_bucket(notional)

        # Filter by criteria (removed trade_type filter - column doesn't exist in data)
        filtered = df[
            (df['pair'] == pair) &
            (df['size_bucket'] == size_bucket) &
            (df['venue_type'] == venue)
        ]

        if len(filtered) == 0:
            # Try with just pair and size bucket
            filtered = df[
                (df['pair'] == pair) &
                (df['size_bucket'] == size_bucket)
            ]

        if len(filtered) == 0:
            # Fallback to default
            logger.debug(
                f"Execution cost lookup failed for {pair}, {size_bucket}, {venue}, {trade_type}")
            return 5.0

        return filtered.iloc[0]['execution_cost_bps']

    def _get_size_bucket(self, notional: float) -> str:
        """Get size bucket for execution cost lookup."""
        if notional < 10000:
            return 'small'
        else:
            return 'large'  # Simplified: only small and large buckets

    def get_gas_cost(self, operation: str, timestamp: pd.Timestamp) -> float:
        """Get gas cost for operation in ETH."""
        if 'gas_costs' not in self.data:
            # Default gas costs if data not available
            return 0.001  # 0.001 ETH default

        data = self.data['gas_costs']
        ts = data.index.asof(timestamp)
        if pd.isna(ts):
            ts = data.index[0]

        # Map operation to gas cost column
        operation_map = {
            'CREATE_LST': 'CREATE_LST_eth',
            'COLLATERAL_SUPPLIED': 'COLLATERAL_SUPPLIED_eth',
            'BORROW': 'BORROW_eth',
            'REPAY': 'REPAY_eth',
            'WITHDRAW': 'WITHDRAW_eth'
        }

        try:
            column = operation_map[operation]
        except KeyError:
            column = 'gas_price_avg_gwei'
        return data.loc[ts, column]

    def get_market_data_snapshot(self, timestamp: pd.Timestamp = None) -> Dict:
        """Get complete market data snapshot for timestamp (backtest mode only)."""
        # Historical data provider only handles backtest mode
        if timestamp is None:
            raise ValueError("Timestamp required for backtest mode")

        snapshot = {
            'timestamp': timestamp,
        }

        # Spot prices
        try:
            snapshot['eth_usd_price'] = self.get_spot_price('ETH', timestamp)
        except BaseException:
            snapshot['eth_usd_price'] = None

        try:
            snapshot['btc_usd_price'] = self.get_spot_price('BTC', timestamp)
        except BaseException:
            snapshot['btc_usd_price'] = None

        # AAVE rates (if available)
        for asset in ['weeth', 'wsteth', 'weth', 'usdt']:
            rates_key = f'{asset}_rates'
            if rates_key in self.data:
                try:
                    data = self.data[rates_key]
                    ts = data.index.asof(timestamp)
                    if not pd.isna(ts):
                        row = data.loc[ts]
                        snapshot[f'{asset}_supply_apy'] = row.get(
                            'liquidity_apy', 0)
                        snapshot[f'{asset}_liquidity_index'] = row.get(
                            'liquidityIndex', 1.0)
                        snapshot[f'{asset}_growth_factor'] = row.get(
                            'liquidity_growth_factor', 1.0)
                        snapshot[f'{asset}_borrow_apy'] = row.get(
                            'borrow_apy', 0)
                        snapshot[f'{asset}_borrow_index'] = row.get(
                            'variableBorrowIndex', 1.0)
                        snapshot[f'{asset}_borrow_growth_factor'] = row.get(
                            'borrow_growth_factor', 1.0)
                except BaseException:
                    pass
        
        # USDT liquidity index (for pure lending mode)
        if 'usdt_rates' in self.data:
            try:
                data = self.data['usdt_rates']
                ts = data.index.asof(timestamp)
                if not pd.isna(ts):
                    snapshot['usdt_liquidity_index'] = data.loc[ts, 'liquidityIndex']
                    logger.debug(f"Data Provider: USDT liquidity index at {timestamp} = {snapshot['usdt_liquidity_index']}")
                else:
                    # TODO-REFACTOR: This hardcodes liquidity_index instead of using proper data provider
                    # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - No Hardcoded Values
                    # Fix: Use proper data provider method or fail gracefully
                    snapshot['usdt_liquidity_index'] = 1.0  # WRONG - hardcoded value
                    logger.debug(f"Data Provider: No USDT data for {timestamp}, using default 1.0")
            except Exception as e:
                # TODO-REFACTOR: This hardcodes liquidity_index instead of using proper data provider
                # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - No Hardcoded Values
                # Fix: Use proper data provider method or fail gracefully
                snapshot['usdt_liquidity_index'] = 1.0  # WRONG - hardcoded value
                logger.warning(f"Data Provider: Error getting USDT liquidity index: {e}")
        else:
            # TODO-REFACTOR: This hardcodes liquidity_index instead of using proper data provider
            # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - No Hardcoded Values
            # Fix: Use proper data provider method or fail gracefully
            snapshot['usdt_liquidity_index'] = 1.0  # WRONG - hardcoded value
            logger.warning(f"Data Provider: No usdt_rates data loaded, using default 1.0")
        
        # Futures prices (per exchange)
        for venue in ['binance', 'bybit', 'okx']:
            futures_key = f'{venue}_futures'
            if futures_key in self.data:
                try:
                    snapshot[f'{venue}_eth_perp'] = self.get_futures_price(
                        'ETH', venue, timestamp)
                except BaseException:
                    snapshot[f'{venue}_eth_perp'] = None

        # Funding rates (per exchange)
        for venue in ['binance', 'bybit', 'okx']:
            funding_key = f'{venue}_funding'
            if funding_key in self.data:
                try:
                    data = self.data[funding_key]
                    ts = data.index.asof(timestamp)
                    if not pd.isna(ts):
                        snapshot[f'{venue}_funding_rate'] = data.loc[ts,
                                                                     'funding_rate']
                except BaseException:
                    # TODO-REFACTOR: Funding rate data missing - should fail fast with error code
                    # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - No Hardcoded Values
                    # Fix: Fail fast with error code, don't use hardcoded values
                    raise ValueError(f"Funding rate data not available for {venue} at timestamp {timestamp}")

        # Gas costs
        try:
            if 'gas_costs' in self.data:
                data = self.data['gas_costs']
                ts = data.index.asof(timestamp)
                if not pd.isna(ts):
                    snapshot['gas_price_gwei'] = data.loc[ts,
                                                          'gas_price_avg_gwei']
                else:
                    # TODO-REFACTOR: Gas price data missing - should fail fast with error code
                    # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - No Hardcoded Values
                    # Fix: Fail fast with error code, don't use hardcoded values
                    raise ValueError(f"Gas price data not available for timestamp {timestamp}")
            else:
                # TODO-REFACTOR: Gas costs data not loaded - should fail fast with error code
                # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - No Hardcoded Values
                # Fix: Fail fast with error code, don't use hardcoded values
                raise ValueError("Gas costs data not loaded in data provider")
        except BaseException as e:
            # TODO-REFACTOR: Gas price data access failed - should fail fast with error code
            # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - No Hardcoded Values
            # Fix: Fail fast with error code, don't use hardcoded values
            raise ValueError(f"Failed to access gas price data: {e}")

        return snapshot

    # REMOVED: All live mode methods - Phase 2: Historical data provider only handles backtest mode
    # Live mode is handled by LiveDataProvider via data_provider_factory.py
    # Methods removed: _get_live_market_data_snapshot, _init_live_data_sources,
    # get_spot_price_live, get_aave_index_live, get_futures_price_live
    
    # ============================================================================
    # VENUE DATA LOADING METHODS
    # ============================================================================
    
    
    def get_bybit_margin_requirements(self) -> Dict[str, float]:
        """Load Bybit margin requirements from data."""
        try:
            data_path = self.data_dir / "market_data" / "derivatives" / "risk_params" / "bybit_margin_requirements.json"
            if not data_path.exists():
                raise FileNotFoundError(f"Bybit margin requirements file not found: {data_path}")
            
            import json
            with open(data_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Bybit margin requirements: {e}")
            raise ValueError(f"Failed to load Bybit margin requirements: {e}")
    
    def get_binance_margin_requirements(self) -> Dict[str, float]:
        """Load Binance margin requirements from data."""
        try:
            data_path = self.data_dir / "market_data" / "derivatives" / "risk_params" / "binance_margin_requirements.json"
            if not data_path.exists():
                raise FileNotFoundError(f"Binance margin requirements file not found: {data_path}")
            
            import json
            with open(data_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Binance margin requirements: {e}")
            raise ValueError(f"Failed to load Binance margin requirements: {e}")
    
    def get_okx_margin_requirements(self) -> Dict[str, float]:
        """Load OKX margin requirements from data."""
        try:
            data_path = self.data_dir / "market_data" / "derivatives" / "risk_params" / "okx_margin_requirements.json"
            if not data_path.exists():
                raise FileNotFoundError(f"OKX margin requirements file not found: {data_path}")
            
            import json
            with open(data_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load OKX margin requirements: {e}")
            raise ValueError(f"Failed to load OKX margin requirements: {e}")
    
    def get_venue_margin_requirements(self, venue: str) -> Dict[str, float]:
        """Get margin requirements for a specific venue."""
        venue = venue.lower()
        if venue == 'bybit':
            return self.get_bybit_margin_requirements()
        elif venue == 'binance':
            return self.get_binance_margin_requirements()
        elif venue == 'okx':
            return self.get_okx_margin_requirements()
        else:
            raise ValueError(f"Unknown venue: {venue}. Supported venues: bybit, binance, okx")