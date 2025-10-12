"""
ML Directional Strategy Manager

Implements ML-driven directional trading strategy with long/short perp positions
based on ML predictions. Uses 5-minute intervals with take-profit and stop-loss orders.

Architecture:
- Inherits from BaseStrategyManager (5-action interface)
- ML signal-driven position sizing
- Perp futures execution with TP/SL orders
- 5-minute rebalancing intervals

Reference: docs/MODES.md - ML Directional Strategy Mode
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Strategy Manager Architecture
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd

from .base_strategy_manager import BaseStrategyManager, StrategyAction

logger = logging.getLogger(__name__)


class MLDirectionalStrategyManager(BaseStrategyManager):
    """ML-driven directional strategy manager for perp futures trading."""
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, event_engine, data_provider):
        """
        Initialize ML directional strategy manager.
        
        Args:
            config: Strategy configuration with ML parameters
            risk_monitor: Risk monitor instance
            position_monitor: Position monitor instance
            event_engine: Event engine instance
            data_provider: Data provider for ML predictions and OHLCV
        """
        super().__init__(config, risk_monitor, position_monitor, event_engine)
        
        # ML-specific configuration
        self.ml_config = config.get('ml_config', {})
        self.signal_threshold = self.ml_config.get('signal_threshold', 0.65)
        self.max_position_size = self.ml_config.get('max_position_size', 1.0)
        self.candle_interval = self.ml_config.get('candle_interval', '5min')
        
        # Data provider for ML predictions
        self.data_provider = data_provider
        
        # Current position state
        self.current_position = None  # 'long', 'short', or None
        self.current_signal = None    # Last ML signal
        self.current_confidence = 0.0
        
        # TODO: ML data files required at data/market_data/ml/ and data/ml_data/predictions/
        # TODO: Set BASIS_ML_API_TOKEN environment variable for live mode
        
        logger.info(f"MLDirectionalStrategyManager initialized for {self.asset} (threshold: {self.signal_threshold})")
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position based on ML signal and current equity.
        
        Args:
            current_equity: Current equity in share class currency
            
        Returns:
            Target position dictionary
        """
        try:
            # Get current timestamp from event engine
            current_timestamp = self.event_engine.get_current_timestamp()
            
            # Get ML prediction for current timestamp
            ml_prediction = self._get_ml_prediction(current_timestamp)
            if not ml_prediction:
                logger.warning("No ML prediction available - maintaining current position")
                return self._get_current_position_dict()
            
            signal = ml_prediction['signal']
            confidence = ml_prediction['confidence']
            
            # Check if signal meets confidence threshold
            if confidence < self.signal_threshold:
                logger.info(f"Signal confidence {confidence} below threshold {self.signal_threshold} - no action")
                return self._get_current_position_dict()
            
            # Calculate position size (100% of equity for directional strategy)
            position_size = current_equity * self.max_position_size
            
            # Determine target position based on signal
            if signal == 'long':
                target_position = {
                    f'{self.asset}-PERP': position_size,  # Long position
                    'USDT': 0.0  # No USDT balance needed for perp
                }
            elif signal == 'short':
                target_position = {
                    f'{self.asset}-PERP': -position_size,  # Short position
                    'USDT': 0.0  # No USDT balance needed for perp
                }
            else:  # 'neutral' or 'hold'
                # If new signal matches current position, hold
                if signal == 'hold' and self.current_position:
                    logger.info("Hold signal matches current position - no action")
                    return self._get_current_position_dict()
                else:
                    # Close position
                    target_position = {
                        f'{self.asset}-PERP': 0.0,
                        'USDT': current_equity
                    }
            
            # Update current state
            self.current_position = signal if signal in ['long', 'short'] else None
            self.current_signal = signal
            self.current_confidence = confidence
            
            logger.info(f"Target position calculated: {target_position} (signal: {signal}, confidence: {confidence})")
            return target_position
            
        except Exception as e:
            logger.error(f"Failed to calculate target position: {e}")
            return self._get_current_position_dict()
    
    def entry_full(self, equity: float) -> StrategyAction:
        """
        Enter full position based on ML signal.
        
        Args:
            equity: Available equity for position
            
        Returns:
            Strategy action for full position entry
        """
        try:
            current_timestamp = self.event_engine.get_current_timestamp()
            ml_prediction = self._get_ml_prediction(current_timestamp)
            
            if not ml_prediction or ml_prediction['confidence'] < self.signal_threshold:
                logger.info("No valid ML signal for entry - skipping")
                return StrategyAction(
                    action_type="entry_full",
                    target_amount=0.0,
                    target_currency=self.asset,
                    instructions=[]
                )
            
            signal = ml_prediction['signal']
            if signal not in ['long', 'short']:
                logger.info(f"Signal {signal} not suitable for entry - skipping")
                return StrategyAction(
                    action_type="entry_full",
                    target_amount=0.0,
                    target_currency=self.asset,
                    instructions=[]
                )
            
            # Calculate position size
            position_size = equity * self.max_position_size
            
            # Create execution instructions
            instructions = []
            if signal == 'long':
                instructions.append({
                    'action': 'open_perp_long',
                    'symbol': f'{self.asset}-PERP',
                    'amount': position_size,
                    'take_profit': ml_prediction.get('take_profit'),
                    'stop_loss': ml_prediction.get('stop_loss')
                })
            elif signal == 'short':
                instructions.append({
                    'action': 'open_perp_short',
                    'symbol': f'{self.asset}-PERP',
                    'amount': position_size,
                    'take_profit': ml_prediction.get('take_profit'),
                    'stop_loss': ml_prediction.get('stop_loss')
                })
            
            logger.info(f"Entry full action: {signal} position of {position_size} {self.asset}")
            
            return StrategyAction(
                action_type="entry_full",
                target_amount=position_size,
                target_currency=self.asset,
                instructions=instructions,
                atomic=True
            )
            
        except Exception as e:
            logger.error(f"Failed to create entry_full action: {e}")
            return StrategyAction(
                action_type="entry_full",
                target_amount=0.0,
                target_currency=self.asset,
                instructions=[]
            )
    
    def entry_partial(self, equity_delta: float) -> StrategyAction:
        """
        Scale up position based on ML signal.
        
        Args:
            equity_delta: Additional equity available
            
        Returns:
            Strategy action for partial position entry
        """
        # For ML directional strategy, partial entry is same as full entry
        # since we always use 100% of available equity
        return self.entry_full(equity_delta)
    
    def exit_full(self, equity: float) -> StrategyAction:
        """
        Exit entire position.
        
        Args:
            equity: Current equity to exit
            
        Returns:
            Strategy action for full position exit
        """
        try:
            # Get current position from position monitor
            position_snapshot = self.position_monitor.get_position_snapshot()
            perp_positions = position_snapshot.get('perp_positions', {})
            
            instructions = []
            for venue, positions in perp_positions.items():
                for symbol, position in positions.items():
                    if symbol == f'{self.asset}-PERP' and position != 0:
                        instructions.append({
                            'action': 'close_perp',
                            'symbol': symbol,
                            'amount': abs(position),
                            'venue': venue
                        })
            
            if not instructions:
                logger.info("No perp positions to exit")
                return StrategyAction(
                    action_type="exit_full",
                    target_amount=0.0,
                    target_currency=self.asset,
                    instructions=[]
                )
            
            logger.info(f"Exit full action: closing {len(instructions)} perp positions")
            
            return StrategyAction(
                action_type="exit_full",
                target_amount=equity,
                target_currency=self.asset,
                instructions=instructions,
                atomic=True
            )
            
        except Exception as e:
            logger.error(f"Failed to create exit_full action: {e}")
            return StrategyAction(
                action_type="exit_full",
                target_amount=0.0,
                target_currency=self.asset,
                instructions=[]
            )
    
    def exit_partial(self, equity_delta: float) -> StrategyAction:
        """
        Scale down position.
        
        Args:
            equity_delta: Equity to reduce from position
            
        Returns:
            Strategy action for partial position exit
        """
        # For ML directional strategy, partial exit is same as full exit
        # since we always use 100% of available equity
        return self.exit_full(equity_delta)
    
    def sell_dust(self, dust_tokens: Dict[str, float]) -> StrategyAction:
        """
        Convert non-share-class tokens to share class currency.
        
        Args:
            dust_tokens: Dictionary of dust token amounts
            
        Returns:
            Strategy action for dust conversion
        """
        # For ML directional strategy, no dust conversion needed
        # since we only trade perp futures
        return StrategyAction(
            action_type="sell_dust",
            target_amount=0.0,
            target_currency=self.asset,
            instructions=[]
        )
    
    def _get_ml_prediction(self, timestamp: pd.Timestamp) -> Optional[Dict]:
        """
        Get ML prediction for timestamp.
        
        Args:
            timestamp: Timestamp for prediction
            
        Returns:
            ML prediction dictionary or None
        """
        try:
            # Check if ML data is available
            if not self._ml_data_enabled():
                logger.warning("ML data not enabled - returning None")
                return None
            
            # Get ML prediction from canonical data structure
            data = self.data_provider.get_data(timestamp)
            prediction = data.get('ml_data', {}).get('predictions', {}).get(self.asset)
            if not prediction:
                logger.warning(f"No ML prediction available for {timestamp}")
                return None
            
            return prediction
            
        except Exception as e:
            logger.error(f"Failed to get ML prediction: {e}")
            return None
    
    def _ml_data_enabled(self) -> bool:
        """Check if ML data is configured for this strategy mode."""
        data_requirements = self.config.get('data_requirements', [])
        return 'ml_predictions' in data_requirements
    
    def _get_current_position_dict(self) -> Dict[str, float]:
        """Get current position as dictionary."""
        try:
            position_snapshot = self.position_monitor.get_position_snapshot()
            perp_positions = position_snapshot.get('perp_positions', {})
            
            # Sum up all perp positions across venues
            total_perp_position = 0.0
            for venue, positions in perp_positions.items():
                for symbol, position in positions.items():
                    if symbol == f'{self.asset}-PERP':
                        total_perp_position += position
            
            return {
                f'{self.asset}-PERP': total_perp_position,
                'USDT': 0.0
            }
            
        except Exception as e:
            logger.error(f"Failed to get current position: {e}")
            return {
                f'{self.asset}-PERP': 0.0,
                'USDT': 0.0
            }
