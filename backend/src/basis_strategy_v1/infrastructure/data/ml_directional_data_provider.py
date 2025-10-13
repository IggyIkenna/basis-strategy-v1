"""
ML Directional Data Provider - Canonical Architecture Implementation

Mode-specific data provider for ML directional strategies implementing the canonical
architecture pattern with standardized data structure.

Reference: docs/CODE_STRUCTURE_PATTERNS.md - Mode-Specific DataProvider Example
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 8 (Data Provider Architecture)
"""

import pandas as pd
from typing import Dict, Any, List
import logging
import os

from .base_data_provider import BaseDataProvider

logger = logging.getLogger(__name__)


class MLDirectionalDataProvider(BaseDataProvider):
    """Data provider for ML directional modes implementing canonical architecture."""
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        """Initialize ML directional data provider."""
        super().__init__(execution_mode, config)
        
        # Set available data types for this mode
        self.available_data_types = [
            'ml_ohlcv_5min',      # 5-minute OHLCV bars
            'ml_predictions',     # ML signals (long/short/neutral + TP/SL)
            'btc_usd_prices',     # For PnL calculation (BTC mode)
            'eth_usd_prices',     # For PnL calculation (ETH mode)
            'usdt_usd_prices',    # For PnL calculation (USDT mode)
            'gas_costs',
            'execution_costs'
        ]
        
        # Initialize data storage (will be loaded on-demand)
        self.data = {}
        self._data_loaded = False
        
        # ML-specific configuration
        self.asset = config.get('asset', 'BTC')
        self.share_class = config.get('share_class', 'BTC')
        
        # TODO: ML data files required at data/market_data/ml/ and data/ml_data/predictions/
        # TODO: Set BASIS_ML_API_TOKEN environment variable for live mode
        
        logger.info(f"MLDirectionalDataProvider initialized for {execution_mode} mode (asset: {self.asset})")
    
    def _validate_data_requirements(self, data_requirements: List[str]) -> None:
        """
        Validate that this provider can satisfy all data requirements.
        
        Args:
            data_requirements: List of required data types
            
        Raises:
            ValueError: If any requirements cannot be satisfied
        """
        missing_requirements = []
        for requirement in data_requirements:
            if requirement not in self.available_data_types:
                missing_requirements.append(requirement)
        
        if missing_requirements:
            raise ValueError(
                f"MLDirectionalDataProvider cannot satisfy requirements: {missing_requirements}. "
                f"Available: {self.available_data_types}"
            )
        
        logger.info(f"Data requirements validated: {data_requirements}")
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Return standardized data structure for ML directional mode.
        
        Args:
            timestamp: Timestamp for data retrieval
            
        Returns:
            Standardized data structure dictionary
        """
        # Load data on-demand if not already loaded
        if not self._data_loaded:
            self._load_data()
        
        return {
            'market_data': {
                'prices': {
                    self.asset: self._get_asset_price(timestamp),
                    'USDT': 1.0  # Always 1.0
                },
                'rates': {}  # No funding rates for directional strategies
            },
            'protocol_data': {
                'aave_indexes': {},  # No AAVE for ML directional
                'oracle_prices': {},  # No oracle prices for ML directional
                'perp_prices': self._get_perp_prices(timestamp),
                'risk_params': {}  # No AAVE risk params for ML directional
            },
            'staking_data': {},  # No staking for ML directional
            'execution_data': {
                'wallet_balances': {},
                'smart_contract_balances': {},
                'cex_spot_balances': {},
                'cex_derivatives_balances': {},
                'gas_costs': self._get_gas_costs(timestamp),
                'execution_costs': self._get_execution_costs(timestamp)
            },
            'ml_data': {  # NEW SECTION
                'predictions': self._get_ml_predictions(timestamp),
                'ohlcv': self._get_ml_ohlcv_data(timestamp),
                'model_status': self._get_ml_model_status(timestamp)
            }
        }
    
    def get_timestamps(self, start_date: str, end_date: str) -> List[pd.Timestamp]:
        """
        Get available timestamps for backtest period (5-minute intervals).
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of timestamps (5-minute intervals)
        """
        # For ML strategies, use 5-minute intervals
        return pd.date_range(start_date, end_date, freq='5min').tolist()
    
    def load_data(self) -> None:
        """Load all required data for backtest mode."""
        if self.execution_mode == 'backtest':
            self._load_backtest_data()
        else:
            # Live mode - no data loading needed
            pass
        
        self._data_loaded = True
        logger.info("ML directional data loaded successfully")
    
    def _load_backtest_data(self) -> None:
        """Load historical data for backtest mode."""
        data_dir = self.config.get('data_dir', 'data')
        
        # Load asset prices
        price_file = f"{data_dir}/market_data/{self.asset.lower()}_usd_prices.csv"
        if os.path.exists(price_file):
            self.data['asset_prices'] = pd.read_csv(price_file)
            self.data['asset_prices']['timestamp'] = pd.to_datetime(self.data['asset_prices']['timestamp'])
        
        # Load gas costs
        gas_file = f"{data_dir}/execution_costs/gas_costs.csv"
        if os.path.exists(gas_file):
            self.data['gas_costs'] = pd.read_csv(gas_file)
            self.data['gas_costs']['timestamp'] = pd.to_datetime(self.data['gas_costs']['timestamp'])
        
        # Load execution costs
        exec_file = f"{data_dir}/execution_costs/execution_costs.csv"
        if os.path.exists(exec_file):
            self.data['execution_costs'] = pd.read_csv(exec_file)
            self.data['execution_costs']['timestamp'] = pd.to_datetime(self.data['execution_costs']['timestamp'])
        
        logger.info(f"Loaded backtest data for ML directional strategy (asset: {self.asset})")
    
    def _get_asset_price(self, timestamp: pd.Timestamp) -> float:
        """Get asset price at timestamp."""
        if 'asset_prices' in self.data:
            df = self.data['asset_prices']
            closest_idx = df['timestamp'].sub(timestamp).abs().idxmin()
            return float(df.loc[closest_idx, 'price'])
        
        # Fallback prices for testing
        if self.asset == 'BTC':
            return 50000.0
        elif self.asset == 'ETH':
            return 3000.0
        elif self.asset == 'USDT':
            return 1.0
        else:
            return 1.0
    
    def _get_perp_prices(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get perp prices at timestamp."""
        # For ML directional strategies, perp prices same as spot
        asset_price = self._get_asset_price(timestamp)
        return {
            f'{self.asset}-PERP': asset_price
        }
    
    def _get_gas_costs(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get gas costs at timestamp."""
        if 'gas_costs' in self.data:
            df = self.data['gas_costs']
            closest_idx = df['timestamp'].sub(timestamp).abs().idxmin()
            cost = df.loc[closest_idx, 'cost']
            return {
                'binance_perp': cost,
                'bybit_perp': cost,
                'okx_perp': cost
            }
        return {
            'binance_perp': 0.0001,
            'bybit_perp': 0.0001,
            'okx_perp': 0.0001
        }
    
    def _get_execution_costs(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get execution costs at timestamp."""
        if 'execution_costs' in self.data:
            df = self.data['execution_costs']
            closest_idx = df['timestamp'].sub(timestamp).abs().idxmin()
            cost = df.loc[closest_idx, 'cost']
            return {
                'binance_perp': cost,
                'bybit_perp': cost,
                'okx_perp': cost
            }
        return {
            'binance_perp': 0.0001,
            'bybit_perp': 0.0001,
            'okx_perp': 0.0001
        }
    
    # ============================================================================
    # ML Data Provider Methods (Override BaseDataProvider)
    # ============================================================================
    # TODO: ML data files required at data/market_data/ml/ and data/ml_data/predictions/
    # TODO: Set BASIS_ML_API_TOKEN environment variable for live mode
    
    def _load_ml_ohlcv(self, timestamp: pd.Timestamp, symbol: str) -> Dict:
        """
        Load ML OHLCV data from CSV file (backtest mode).
        
        Args:
            timestamp: Timestamp for data
            symbol: Trading symbol (e.g., 'BTC', 'ETH', 'USDT')
            
        Returns:
            OHLCV dictionary
            
        Raises:
            FileNotFoundError: If ML data file not found
        """
        # Check if file exists
        file_path = f"{self.config.get('data_dir', 'data')}/market_data/ml/ohlcv_5min_{symbol.lower()}.csv"
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ML OHLCV data not found: {file_path}")
        
        # Load CSV and find closest timestamp
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Find closest timestamp (within 5 minutes)
        time_diff = (df['timestamp'] - timestamp).abs()
        closest_idx = time_diff.idxmin()
        
        if time_diff.iloc[closest_idx] > pd.Timedelta(minutes=5):
            raise ValueError(f"No OHLCV data within 5 minutes of {timestamp}")
        
        row = df.iloc[closest_idx]
        return {
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
            'volume': float(row['volume'])
        }
    
    def _load_ml_prediction(self, timestamp: pd.Timestamp, symbol: str) -> Dict:
        """
        Load ML prediction from CSV file (backtest) or API (live).
        
        Args:
            timestamp: Timestamp for prediction
            symbol: Trading symbol
            
        Returns:
            Prediction dictionary
        """
        if self.execution_mode == 'backtest':
            return self._load_ml_prediction_from_csv(timestamp, symbol)
        elif self.execution_mode == 'live':
            return self._fetch_ml_prediction_from_api(timestamp, symbol)
        else:
            raise ValueError(f"Unknown execution mode: {self.execution_mode}")
    
    def _load_ml_prediction_from_csv(self, timestamp: pd.Timestamp, symbol: str) -> Dict:
        """
        Load ML prediction from CSV file (backtest mode).
        
        Args:
            timestamp: Timestamp for prediction
            symbol: Trading symbol
            
        Returns:
            Prediction dictionary
            
        Raises:
            FileNotFoundError: If ML prediction file not found
        """
        # Check if file exists
        file_path = f"{self.config.get('data_dir', 'data')}/ml_data/predictions/{symbol.lower()}_predictions.csv"
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ML prediction data not found: {file_path}")
        
        # Load CSV and find closest timestamp
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Find closest timestamp (within 5 minutes)
        time_diff = (df['timestamp'] - timestamp).abs()
        closest_idx = time_diff.idxmin()
        
        if time_diff.iloc[closest_idx] > pd.Timedelta(minutes=5):
            raise ValueError(f"No prediction data within 5 minutes of {timestamp}")
        
        row = df.iloc[closest_idx]
        return {
            'signal': str(row['signal']),
            'confidence': float(row['confidence']),
            'sd': float(row['sd'])
        }
    
    def _fetch_ml_prediction_from_api(self, timestamp: pd.Timestamp, symbol: str) -> Dict:
        """
        Fetch ML prediction from external API (live mode).
        
        Args:
            timestamp: Timestamp for prediction
            symbol: Trading symbol
            
        Returns:
            Prediction dictionary with graceful fallback
        """
        # Check if API token is configured
        api_token = os.getenv('BASIS_ML_API_TOKEN')
        if not api_token:
            logger.warning("BASIS_ML_API_TOKEN not set - returning neutral signal")
            return {'signal': 'neutral', 'confidence': 0.0, 'take_profit': 0.0, 'stop_loss': 0.0}
        
        # TODO: Load API config from configs/venues/ml_inference_api.yaml
        api_url = "https://ml-inference-api.example.com/v1/predictions"
        
        try:
            import requests
            response = requests.post(
                api_url,
                headers={'Authorization': f"Bearer {api_token}"},
                json={'symbol': symbol, 'timestamp': timestamp.isoformat()},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Validate response structure
            required_fields = ['signal', 'confidence', 'sd']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing field in API response: {field}")
            
            return {
                'signal': str(result['signal']),
                'confidence': float(result['confidence']),
                'sd': float(result['sd'])
            }
            
        except Exception as e:
            logger.error(f"ML API call failed: {e}")
            # Graceful degradation - return neutral signal
            return {'signal': 'neutral', 'confidence': 0.0, 'sd': 0.02}
    
    def _get_ml_predictions(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Get ML predictions at timestamp."""
        try:
            prediction = self._load_ml_prediction(timestamp, self.asset)
            return {
                self.asset: prediction
            }
        except Exception as e:
            logger.warning(f"ML prediction not available (data not implemented yet): {e}")
            # Return neutral prediction when ML data is not available
            return {
                self.asset: {
                    'signal': 'neutral', 
                    'confidence': 0.0,
                    'sd': 0.02,
                    'note': 'ML data not implemented yet - using neutral signal'
                }
            }
    
    def _get_ml_ohlcv_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Get ML OHLCV data at timestamp."""
        try:
            ohlcv = self._load_ml_ohlcv(timestamp, self.asset)
            return {
                self.asset: ohlcv
            }
        except Exception as e:
            logger.warning(f"ML OHLCV not available (data not implemented yet): {e}")
            # Return empty dict when ML OHLCV data is not available
            return {}
    
    def _get_ml_model_status(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Get ML model status at timestamp."""
        return {
            'model_version': 'v1.0.0',
            'last_updated': timestamp.isoformat(),
            'status': 'active'
        }
