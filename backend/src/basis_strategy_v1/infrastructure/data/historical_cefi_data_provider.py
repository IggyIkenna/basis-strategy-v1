"""
Historical CeFi Data Provider

Provides CSV-based data for CeFi/ML strategies in backtest mode.
Handles ML strategies with 5min granularity and ML service integration.

Key Principles:
- CSV-based data loading for backtest mode
- Position_subscriptions-based data derivation
- 5min granularity for CeFi strategies
- ML service integration for predictions
- Standardized data structure
"""

import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import glob

from ...core.models.instruments import (
    position_key_to_price_key, 
    position_key_to_oracle_pair,
    validate_instrument_in_registry
)

logger = logging.getLogger(__name__)


class HistoricalCeFiDataProvider:
    """Handles CeFi/ML strategies in backtest mode: ml_btc_directional_btc_margin, ml_btc_directional_usdt_margin"""
    
    def __init__(self, config: Dict[str, Any], ml_service):
        """
        Initialize historical CeFi data provider.
        
        Args:
            config: Configuration dictionary with position_subscriptions
            ml_service: ML service instance for predictions
        """
        self.execution_mode = "backtest"
        self.data_type = "cefi"
        self.granularity = "5min"
        self.config = config
        self.data_dir = config.get('data_dir', 'data')
        self.position_subscriptions = config['component_config']['position_monitor']['position_subscriptions']
        self.csv_mappings = self._derive_csv_mappings()
        self.ml_service = ml_service
        self._data_cache = {}
        
        logger.info(f"HistoricalCeFiDataProvider initialized for {len(self.position_subscriptions)} positions")
    
    def _derive_csv_mappings(self) -> Dict[str, str]:
        """Derive CSV mappings using standardized uppercase keys."""
        mappings = {}
        
        for position_key in self.position_subscriptions:
            # Validate instrument exists
            if not validate_instrument_in_registry(position_key):
                logger.warning(f"Position key not in registry: {position_key}")
            
            venue, position_type, instrument = position_key.split(':')
            
            if position_type == 'BaseToken':
                if instrument == 'USDT':
                    mappings[f'market_data.prices.{instrument}'] = None
                else:
                    # Uppercase key: BTC, ETH
                    mappings[f'market_data.prices.{instrument}'] = \
                        f'data/market_data/spot_prices/{instrument.lower()}_usd/*.csv'
            
            elif position_type == 'Perp':
                # Use uppercase key: BTC_binance
                price_key = position_key_to_price_key(position_key)
                
                if venue != 'okx':
                    mappings[f'protocol_data.perp_prices.{price_key}'] = \
                        f'data/market_data/derivatives/futures_ohlcv/{venue}_{instrument}_perp_1h_*.csv'
                else:
                    # OKX uses Binance data
                    mappings[f'protocol_data.perp_prices.{price_key}'] = \
                        f'data/market_data/derivatives/futures_ohlcv/binance_{instrument}_perp_1h_*.csv'
                
                # Funding rates: uppercase key BTC_binance
                mappings[f'market_data.funding_rates.{price_key}'] = \
                    f'data/market_data/derivatives/funding_rates/{venue}_{instrument}_funding_rates_*.csv'
        
        # Execution costs
        mappings['execution_data.gas_costs'] = \
            'data/blockchain_data/gas_prices/ethereum_gas_prices_enhanced_*.csv'
        mappings['execution_data.execution_costs'] = \
            'data/execution_costs/lookup_tables/execution_costs_lookup.json'
        
        logger.info(f"Derived {len(mappings)} CSV mappings with uppercase keys")
        return mappings
    
    def _extract_base_asset(self, instrument: str) -> str:
        """Extract base asset from perpetual instrument ID."""
        return instrument.replace('USDT', '').replace('USD', '').replace('PERP', '')
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Get data snapshot at timestamp with ML predictions from separate service and caching."""
        try:
            # Create cache key from timestamp
            timestamp_key = str(timestamp)
            
            # Check cache first - avoid repeated CSV loads for same timestamp
            if timestamp_key in self._data_cache:
                logger.debug(f"Cache hit for timestamp {timestamp}")
                return self._data_cache[timestamp_key]
            
            logger.debug(f"Cache miss for timestamp {timestamp}, loading fresh data")
            
            # Load fresh data
            data = self._load_fresh_data(timestamp)
            
            # Cache the data for this timestamp
            self._data_cache[timestamp_key] = data
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting data at {timestamp}: {e}")
            raise
    
    def _load_fresh_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Load fresh data from CSV files and ML service for a given timestamp."""
        data = {
            'timestamp': timestamp,
            'market_data': {
                'prices': {},
                'funding_rates': {}
            },
            'protocol_data': {
                'perp_prices': {},
                'aave_indexes': {},
                'oracle_prices': {},
                'protocol_rates': {},
                'staking_rewards': {},
                'seasonal_rewards': {}
            },
            'execution_data': {
                'gas_costs': {},
                'execution_costs': {}
            },
            'ml_data': {
                'predictions': {}
            }
        }
        
        # Load position-based data
        critical_data_errors = []
        
        for data_key, csv_path in self.csv_mappings.items():
            if csv_path is None:
                # Handle synthetic values
                if 'prices.USDT' in data_key:
                    self._set_nested_value(data, data_key, 1.0)
                continue
            
            try:
                value = self._load_data_value(csv_path, timestamp)
                self._set_nested_value(data, data_key, value)
            except Exception as e:
                # Determine if this is critical data that should cause failure
                is_critical = self._is_critical_data_key(data_key)
                
                if is_critical:
                    error_msg = f"Critical data loading failed for {data_key}: {e}"
                    logger.error(error_msg)
                    critical_data_errors.append(error_msg)
                else:
                    logger.warning(f"Error loading CSV value for {data_key}: {e}")
                    # Set default value for non-critical data
                    if 'prices' in data_key:
                        self._set_nested_value(data, data_key, 0.0)
                    elif 'apy' in data_key or 'rate' in data_key:
                        self._set_nested_value(data, data_key, 0.0)
                    else:
                        self._set_nested_value(data, data_key, 0.0)
        
        # Fail fast if critical data loading failed
        if critical_data_errors:
            error_summary = "; ".join(critical_data_errors)
            raise ValueError(f"Critical data loading failures: {error_summary}")
        
        # Add ML predictions from separate service
        try:
            ml_predictions = self.ml_service.get_predictions(timestamp)
            data['ml_data']['predictions'] = ml_predictions
        except Exception as e:
            logger.warning(f"Error getting ML predictions: {e}")
            data['ml_data']['predictions'] = {}
        
        return data
    
    def _is_critical_data_key(self, data_key: str) -> bool:
        """
        Determine if a data key is critical for strategy execution.
        
        Critical data includes:
        - Market prices for base tokens (USDT, BTC, ETH, etc.)
        - Perpetual prices for derivatives
        - Funding rates for perpetuals
        
        Non-critical data includes:
        - Gas costs (can use defaults)
        - Execution costs (can use defaults)
        - ML predictions (optional)
        """
        # Critical data patterns
        critical_patterns = [
            'market_data.prices.',  # Base token prices
            'protocol_data.perp_prices.',  # Perpetual prices
            'market_data.funding_rates.',  # Perpetual funding rates
        ]
        
        # Check if data key matches any critical pattern
        for pattern in critical_patterns:
            if pattern in data_key:
                return True
        
        # Non-critical data patterns
        non_critical_patterns = [
            'execution_data.gas_costs',
            'execution_data.execution_costs',
            'ml_data.predictions',
        ]
        
        # Check if data key matches any non-critical pattern
        for pattern in non_critical_patterns:
            if pattern in data_key:
                return False
        
        # Default to critical if pattern is not recognized
        logger.warning(f"Unknown data key pattern: {data_key}, treating as critical")
        return True
    
    def clear_cache(self):
        """Clear the data cache to free memory."""
        self._data_cache.clear()
        logger.info("Historical CeFi data cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        return {
            'cache_size': len(self._data_cache),
            'cached_timestamps': list(self._data_cache.keys()),
            'memory_usage_estimate': len(str(self._data_cache))
        }
    
    def _load_data_value(self, data_path: str, timestamp: pd.Timestamp) -> float:
        """Load value from CSV or JSON file at given timestamp."""
        if data_path.endswith('.json'):
            return self._load_json_value(data_path, timestamp)
        else:
            return self._load_csv_value(data_path, timestamp)
    
    def _load_csv_value(self, csv_path: str, timestamp: pd.Timestamp) -> float:
        """Load value from CSV file at given timestamp."""
        # Resolve wildcard path
        actual_path = self._resolve_csv_path(csv_path)
        if not actual_path:
            raise ValueError(f"No CSV file found for pattern: {csv_path}")
        
        # Load CSV, skipping comment lines
        df = pd.read_csv(actual_path, index_col=0, parse_dates=True, comment='#')
        
        # Handle duplicate timestamps by keeping the last occurrence
        if df.index.duplicated().any():
            df = df[~df.index.duplicated(keep='last')]
        
        # Validate date range if backtest dates are available
        if hasattr(self, 'backtest_start_date') and hasattr(self, 'backtest_end_date'):
            if self.backtest_start_date and self.backtest_end_date:
                self.data_validator.validate_backtest_date_range(
                    df, Path(actual_path), self.backtest_start_date, self.backtest_end_date
                )
        
        # Use asof lookup for nearest timestamp
        # Handle timezone mismatch by making timestamp timezone-aware if needed
        if hasattr(df.index, 'tz') and df.index.tz is not None and timestamp.tz is None:
            # Make timestamp timezone-aware to match DataFrame index
            timestamp = timestamp.tz_localize('UTC')
        elif hasattr(df.index, 'tz') and df.index.tz is None and timestamp.tz is not None:
            # Make timestamp timezone-naive to match DataFrame index
            timestamp = timestamp.tz_localize(None)
        
        nearest_idx = df.index.asof(timestamp)
        if pd.isna(nearest_idx):
            # Check if this is execution cost data (non-critical)
            if 'execution_cost' in csv_path:
                logger.warning(f"No execution cost data found for {csv_path} at {timestamp}, using default value")
                return 0.0
            else:
                raise ValueError(f"No data found for {csv_path} at {timestamp}")
        
        # Get the value based on the data type
        value = self._extract_value_from_row(df.loc[nearest_idx], csv_path)
        return float(value)
    
    def _load_json_value(self, json_path: str, timestamp: pd.Timestamp) -> float:
        """Load value from JSON lookup table at given timestamp."""
        import json
        from pathlib import Path
        
        # Resolve path
        actual_path = self._resolve_csv_path(json_path)  # Reuse path resolution logic
        if not actual_path:
            raise ValueError(f"No JSON file found for pattern: {json_path}")
        
        # Load JSON
        with open(actual_path, 'r') as f:
            data = json.load(f)
        
        # For execution costs, we need to find the right entry
        # The JSON structure is: {pair: {size_bucket: {date: cost}}}
        if 'execution_costs_lookup.json' in actual_path:
            # This is execution cost data - return a default value for now
            # The actual lookup logic should be in the execution interface
            logger.debug(f"Execution cost JSON loaded for {timestamp}")
            return 0.0  # Default execution cost
        
        # For other JSON files, implement as needed
        raise ValueError(f"JSON loading not implemented for {json_path}")
    
    def _extract_value_from_row(self, row: pd.Series, csv_path: str) -> Any:
        """
        Extract the correct value from a CSV row based on the file type.
        
        Args:
            row: Pandas Series representing one row of data
            csv_path: Path to the CSV file (used to determine file type)
            
        Returns:
            The appropriate value for the data type
        """
        try:
            # Spot prices files - extract price column
            if 'spot_prices' in csv_path.lower() or 'prices' in csv_path.lower():
                # Look for price-related columns
                price_cols = [col for col in row.index if 'price' in col.lower() and col != 'timestamp']
                if price_cols:
                    return row[price_cols[0]]
                else:
                    # Fallback to first numeric column
                    for col in row.index:
                        if col != 'timestamp' and pd.api.types.is_numeric_dtype(type(row[col])):
                            return row[col]
                    raise ValueError(f"No price column found in spot prices file: {csv_path}")
            
            # Perpetual prices files - extract price column
            elif 'perp' in csv_path.lower() or 'futures' in csv_path.lower():
                # Look for price-related columns (open, high, low, close, etc.)
                price_cols = [col for col in row.index if any(price_type in col.lower() for price_type in ['open', 'high', 'low', 'close', 'price']) and col != 'timestamp']
                if price_cols:
                    return row[price_cols[0]]  # Use first price column (usually 'close')
                else:
                    # Fallback to first numeric column
                    for col in row.index:
                        if col != 'timestamp' and pd.api.types.is_numeric_dtype(type(row[col])):
                            return row[col]
                    raise ValueError(f"No price column found in perpetual prices file: {csv_path}")
            
            # Funding rates files - extract rate column
            elif 'funding' in csv_path.lower():
                # Look for rate-related columns
                rate_cols = [col for col in row.index if 'rate' in col.lower() and col != 'timestamp']
                if rate_cols:
                    return row[rate_cols[0]]
                else:
                    # Fallback to first numeric column
                    for col in row.index:
                        if col != 'timestamp' and pd.api.types.is_numeric_dtype(type(row[col])):
                            return row[col]
                    raise ValueError(f"No rate column found in funding rates file: {csv_path}")
            
            # Gas prices files - extract gas_price_gwei
            elif 'gas' in csv_path.lower() and 'prices' in csv_path.lower():
                if 'gas_price_gwei' in row.index:
                    return row['gas_price_gwei']
                elif 'gas_price_avg_gwei' in row.index:
                    return row['gas_price_avg_gwei']
                else:
                    # Fallback to first numeric column
                    for col in row.index:
                        if col != 'timestamp' and pd.api.types.is_numeric_dtype(type(row[col])):
                            return row[col]
                    raise ValueError(f"No numeric column found in gas prices file: {csv_path}")
            
            # Default: try to find first numeric column
            else:
                for col in row.index:
                    if col != 'timestamp' and pd.api.types.is_numeric_dtype(type(row[col])):
                        return row[col]
                raise ValueError(f"No numeric column found in file: {csv_path}")
                
        except Exception as e:
            logger.error(f"Error extracting value from row in {csv_path}: {e}")
            logger.error(f"Available columns: {list(row.index)}")
            raise
    
    def _resolve_csv_path(self, csv_path: str) -> Optional[str]:
        """Resolve wildcard CSV path to actual file."""
        # Convert relative path to absolute
        if not csv_path.startswith('/'):
            # Check if data_dir already ends with 'data' and csv_path starts with 'data/'
            if self.data_dir.endswith('data') and csv_path.startswith('data/'):
                # Remove 'data/' prefix to avoid double data directory
                csv_path = str(Path(self.data_dir) / csv_path[5:])
            else:
                csv_path = str(Path(self.data_dir) / csv_path)
        
        # Find matching files
        matches = glob.glob(csv_path)
        if not matches:
            return None
        
        # Return the most recent file
        return max(matches, key=lambda x: Path(x).stat().st_mtime)
    
    def _set_nested_value(self, data: Dict, key_path: str, value: Any) -> None:
        """Set nested value in data structure."""
        keys = key_path.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get_timestamps(self, start_date: str, end_date: str) -> List[pd.Timestamp]:
        """Get available timestamps for backtest period."""
        try:
            # Find a sample CSV file to get timestamps
            sample_csv = None
            for csv_path in self.csv_mappings.values():
                if csv_path and csv_path.endswith('.csv'):
                    sample_csv = csv_path
                    break
            
            if not sample_csv:
                raise ValueError("No CSV files found for timestamp extraction")
            
            # Resolve wildcard path
            actual_path = self._resolve_csv_path(sample_csv)
            if not actual_path:
                raise ValueError(f"No CSV file found for pattern: {sample_csv}")
            
            # Load CSV and extract timestamps
            df = pd.read_csv(actual_path, index_col=0, parse_dates=True)
            timestamps = df.index.tolist()
            
            # Filter by date range
            start_ts = pd.Timestamp(start_date, tz='UTC')
            end_ts = pd.Timestamp(end_date, tz='UTC')
            
            filtered_timestamps = [
                ts for ts in timestamps 
                if start_ts <= ts <= end_ts
            ]
            
            logger.info(f"Found {len(filtered_timestamps)} timestamps between {start_date} and {end_date}")
            return filtered_timestamps
            
        except Exception as e:
            logger.error(f"Error getting timestamps: {e}")
            raise
