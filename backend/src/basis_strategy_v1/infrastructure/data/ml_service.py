"""
ML Service Component

Provides ML predictions for CeFi strategies in both backtest and live modes.
Handles ML signals independently from position-based data.

Key Principles:
- Separate from position data: ML signals are auxiliary, not position-based
- Mode-agnostic: Same interface for backtest and live modes
- Config-driven: ML signals configured separately from position_subscriptions
- Fallback: Graceful degradation when ML service unavailable
"""

import os
import logging
import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class MLService:
    """Separate service for ML predictions (both historical and live)."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ML service.
        
        Args:
            config: Configuration dictionary with ml_config section
        """
        self.config = config
        self.ml_config = config.get('ml_config', {})
        self.model_endpoint = self.ml_config.get('model_endpoint')
        self.api_key = os.getenv('ML_API_KEY')
        self.data_dir = config.get('data_dir', 'data')
        
        # ML signals configuration
        self.signals = self.ml_config.get('signals', ['btc_direction', 'eth_volatility'])
        
        logger.info(f"MLService initialized with signals: {self.signals}")
    
    def get_predictions(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """
        Get ML predictions for backtest mode.
        
        Args:
            timestamp: Timestamp for prediction
            
        Returns:
            Dictionary of ML predictions
        """
        try:
            predictions = {}
            
            for signal in self.signals:
                if signal == 'btc_direction':
                    predictions[signal] = self._get_btc_direction_prediction(timestamp)
                elif signal == 'eth_volatility':
                    predictions[signal] = self._get_eth_volatility_prediction(timestamp)
                else:
                    logger.warning(f"Unknown ML signal: {signal}")
                    predictions[signal] = 0.0
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting ML predictions: {e}")
            # Return default predictions
            return {signal: 0.0 for signal in self.signals}
    
    async def get_live_predictions(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """
        Get real-time ML predictions for live mode.
        
        Args:
            timestamp: Timestamp for prediction
            
        Returns:
            Dictionary of ML predictions
        """
        try:
            if self.model_endpoint and self.api_key:
                return await self._call_ml_api(timestamp)
            else:
                logger.warning("ML API not configured, using default predictions")
                return {signal: 0.0 for signal in self.signals}
                
        except Exception as e:
            logger.error(f"Error getting live ML predictions: {e}")
            return {signal: 0.0 for signal in self.signals}
    
    def _get_btc_direction_prediction(self, timestamp: pd.Timestamp) -> float:
        """Get BTC direction prediction from CSV data."""
        try:
            # Look for BTC predictions in the data directory
            csv_pattern = Path(self.data_dir) / 'ml_data' / 'predictions' / 'btc_predictions*.csv'
            csv_files = list(Path(self.data_dir).glob('ml_data/predictions/btc_predictions*.csv'))
            
            if not csv_files:
                logger.warning(f"BTC predictions CSV not found: {csv_pattern}")
                return 0.0
            
            # Use the most recent file
            csv_path = max(csv_files, key=lambda x: x.stat().st_mtime)
            
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            
            # Use asof lookup for nearest timestamp
            nearest_idx = df.index.asof(timestamp)
            if pd.isna(nearest_idx):
                logger.warning(f"No BTC prediction data for timestamp: {timestamp}")
                return 0.0
            
            prediction = df.loc[nearest_idx, 'direction']
            return float(prediction)
            
        except Exception as e:
            logger.error(f"Error getting BTC direction prediction: {e}")
            return 0.0
    
    def _get_eth_volatility_prediction(self, timestamp: pd.Timestamp) -> float:
        """Get ETH volatility prediction from CSV data."""
        try:
            # Look for ETH volatility predictions in the data directory
            csv_pattern = Path(self.data_dir) / 'ml_data' / 'predictions' / 'eth_volatility*.csv'
            csv_files = list(Path(self.data_dir).glob('ml_data/predictions/eth_volatility*.csv'))
            
            if not csv_files:
                logger.warning(f"ETH volatility CSV not found: {csv_pattern}")
                return 0.0
            
            # Use the most recent file
            csv_path = max(csv_files, key=lambda x: x.stat().st_mtime)
            
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            
            # Use asof lookup for nearest timestamp
            nearest_idx = df.index.asof(timestamp)
            if pd.isna(nearest_idx):
                logger.warning(f"No ETH volatility data for timestamp: {timestamp}")
                return 0.0
            
            prediction = df.loc[nearest_idx, 'volatility']
            return float(prediction)
            
        except Exception as e:
            logger.error(f"Error getting ETH volatility prediction: {e}")
            return 0.0
    
    async def _call_ml_api(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Call ML API for live predictions."""
        try:
            import aiohttp
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'timestamp': timestamp.isoformat(),
                'signals': self.signals
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.model_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=5.0
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('predictions', {})
                    else:
                        logger.error(f"ML API error: {response.status}")
                        return {signal: 0.0 for signal in self.signals}
                        
        except Exception as e:
            logger.error(f"Error calling ML API: {e}")
            return {signal: 0.0 for signal in self.signals}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get ML service health status."""
        try:
            # Check if CSV files exist for backtest mode
            csv_files_exist = True
            for signal in self.signals:
                if signal == 'btc_direction':
                    csv_files = list(Path(self.data_dir).glob('ml_data/predictions/btc_predictions*.csv'))
                elif signal == 'eth_volatility':
                    csv_files = list(Path(self.data_dir).glob('ml_data/predictions/eth_volatility*.csv'))
                else:
                    continue
                
                if not csv_files:
                    csv_files_exist = False
                    break
            
            # Check API configuration for live mode
            api_configured = bool(self.model_endpoint and self.api_key)
            
            return {
                'status': 'healthy' if (csv_files_exist or api_configured) else 'unhealthy',
                'csv_files_exist': csv_files_exist,
                'api_configured': api_configured,
                'signals': self.signals,
                'model_endpoint': self.model_endpoint
            }
            
        except Exception as e:
            logger.error(f"Error getting ML service health: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
