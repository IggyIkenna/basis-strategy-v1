"""
ML USDT Directional Strategy Implementation

Implements ML-driven directional USDT trading strategy using 5-minute interval signals
to generate long/short positions. Uses machine learning predictions for entry/exit signals
while taking full directional USDT exposure.

Reference: docs/specs/strategies/09_ML_USDT_DIRECTIONAL_STRATEGY.md
Reference: docs/MODES.md - ML USDT Directional Strategy Mode
Reference: docs/specs/5B_BASE_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any
import logging
import pandas as pd

from .base_strategy_manager import BaseStrategyManager, StrategyAction

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)


class MLUSDTDirectionalStrategy(BaseStrategyManager):
    """
    ML USDT Directional Strategy - ML-driven directional USDT trading.
    
    Strategy Overview:
    - Uses ML predictions for entry/exit signals
    - Takes full directional USDT exposure
    - 5-minute interval signal processing
    - Stop-loss and take-profit management
    - Target APY: 15-30% (moderate risk, moderate reward)
    """
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, event_engine, data_provider=None):
        """
        Initialize ML USDT directional strategy.
        
        Args:
            config: Strategy configuration
            risk_monitor: Risk monitor instance
            position_monitor: Position monitor instance
            event_engine: Event engine instance
            data_provider: Data provider instance (required for ML strategies)
        """
        super().__init__(config, risk_monitor, position_monitor, event_engine)
        
        # Store data provider for ML predictions
        self.data_provider = data_provider
        
        # Validate required configuration at startup (fail-fast)
        required_keys = ['signal_threshold', 'max_position_size', 'stop_loss_pct', 'take_profit_pct']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        # ML-specific configuration (fail-fast access)
        self.signal_threshold = config['signal_threshold']  # 0.70 default (higher for USDT)
        self.max_position_size = config['max_position_size']  # Max position size
        self.stop_loss_pct = config['stop_loss_pct']  # Stop loss percentage
        self.take_profit_pct = config['take_profit_pct']  # Take profit percentage
        
        # ML model state
        self.ml_model = None
        self.last_prediction = None
        self.last_signal = None
        
        logger.info(f"MLUSDTDirectionalStrategy initialized with signal threshold: {self.signal_threshold}")
    
    def make_strategy_decision(self, timestamp, trigger_source: str, market_data: Dict, exposure_data: Dict, risk_assessment: Dict) -> StrategyAction:
        """
        Make ML USDT directional strategy decision based on market conditions and ML predictions.
        
        ML USDT Directional Strategy Logic:
        - Get ML predictions from data provider
        - Analyze signal confidence and direction
        - Check risk management (stop-loss, take-profit)
        - Generate appropriate instructions for USDT directional positions
        """
        try:
            # Log strategy decision start
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message=f"Making ML USDT directional strategy decision triggered by {trigger_source}",
                data={
                    'trigger_source': trigger_source,
                    'strategy_type': self.__class__.__name__,
                    'timestamp': str(timestamp)
                },
                level=LogLevel.INFO
            )
            
            # Get current equity and positions
            current_equity = exposure_data.get('total_exposure', 0.0)
            current_positions = exposure_data.get('positions', {})
            
            # Get ML predictions from data provider
            ml_predictions = self._get_ml_predictions(market_data)
            
            # USDT-specific market analysis
            usdt_price = market_data.get('prices', {}).get('USDT', 1.0)  # USDT should be ~1.0
            usdt_perp_price = market_data.get('prices', {}).get('USDT_PERP', 1.0)
            
            # Risk assessment
            liquidation_risk = risk_assessment.get('liquidation_risk', 0.0)
            margin_ratio = risk_assessment.get('cex_margin_ratio', 1.0)
            
            # ML USDT Directional Strategy Decision Logic
            if ml_predictions is None:
                # No ML predictions available - maintain current position
                return self.sell_dust({})
            
            # Check risk management first
            if self._should_exit_for_risk_management(usdt_price, current_positions, ml_predictions):
                return self.exit_full(current_equity)
            
            # Check ML signal for entry/exit
            if ml_predictions['confidence'] > self.signal_threshold:
                signal = ml_predictions['signal']
                
                if signal == 'long' and not self._has_long_position(current_positions):
                    # Enter long position
                    return self.entry_full(current_equity)
                elif signal == 'short' and not self._has_short_position(current_positions):
                    # Enter short position
                    return self.entry_full(current_equity)
                elif signal == 'neutral' and self._has_any_position(current_positions):
                    # Exit position
                    return self.exit_full(current_equity)
            
            # Default: maintain current position
            return self.sell_dust({})
                
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'method': 'make_strategy_decision',
                    'trigger_source': trigger_source,
                    'strategy_type': self.__class__.__name__
                }
            )
            logger.error(f"Error in ML USDT directional strategy decision: {e}")
            # Return safe default action
            return self.sell_dust({})
    
    def _get_ml_predictions(self, market_data: Dict) -> Dict:
        """Get ML predictions from data provider."""
        try:
            if self.data_provider is None:
                return None
            
            # Get ML predictions from data provider
            # This would be implemented based on the actual ML model integration
            ml_predictions = self.data_provider.get_ml_predictions('usdt_directional')
            
            if ml_predictions is None:
                return None
            
            return {
                'signal': ml_predictions.get('signal', 'neutral'),
                'confidence': ml_predictions.get('confidence', 0.0),
                'sd': ml_predictions.get('sd', 0.02),  # Default 2% standard deviation
                'timestamp': ml_predictions.get('timestamp', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting ML predictions: {e}")
            return None
    
    def _should_exit_for_risk_management(self, current_price: float, current_positions: Dict, ml_predictions: Dict) -> bool:
        """Check if we should exit position for risk management."""
        try:
            current_position = current_positions.get('btc_perp_position', 0.0)  # USDT-margined BTC perps
            
            if current_position == 0:
                return False
            
            # Calculate stop-loss and take-profit from standard deviation
            stop_loss, take_profit = self._calculate_stop_loss_take_profit(
                current_price, ml_predictions.get('sd', 0.02), ml_predictions.get('signal', 'neutral')
            )
            
            # Check stop-loss and take-profit
            if current_position > 0:  # Long position
                if current_price <= stop_loss:
                    return True
                if current_price >= take_profit:
                    return True
            elif current_position < 0:  # Short position
                if current_price >= stop_loss:
                    return True
                if current_price <= take_profit:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking risk management: {e}")
            return False
    
    def _calculate_stop_loss_take_profit(self, current_price: float, sd: float, signal: str) -> tuple:
        """
        Calculate stop-loss and take-profit levels based on standard deviation.
        
        Args:
            current_price: Current BTC price
            sd: Standard deviation (as decimal, e.g., 0.02 for 2%)
            signal: Trading signal ('long', 'short', 'neutral')
            
        Returns:
            Tuple of (stop_loss, take_profit)
        """
        if signal == 'long':
            stop_loss = current_price * (1 - 2 * sd)    # 2x SD stop loss
            take_profit = current_price * (1 + 3 * sd)  # 3x SD take profit
        elif signal == 'short':
            stop_loss = current_price * (1 + 2 * sd)    # 2x SD stop loss
            take_profit = current_price * (1 - 3 * sd)  # 3x SD take profit
        else:  # neutral
            stop_loss = 0.0
            take_profit = 0.0
        
        return stop_loss, take_profit
    
    def _has_long_position(self, current_positions: Dict) -> bool:
        """Check if we have a long position."""
        return current_positions.get('btc_perp_position', 0.0) > 0  # USDT-margined BTC perps
    
    def _has_short_position(self, current_positions: Dict) -> bool:
        """Check if we have a short position."""
        return current_positions.get('btc_perp_position', 0.0) < 0  # USDT-margined BTC perps
    
    def _has_any_position(self, current_positions: Dict) -> bool:
        """Check if we have any position."""
        return current_positions.get('btc_perp_position', 0.0) != 0  # USDT-margined BTC perps
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position for ML USDT directional strategy.
        
        Args:
            current_equity: Current equity in share class currency
            
        Returns:
            Dictionary of target positions by token/venue
        """
        try:
            # For ML directional strategy, we use the full equity for directional exposure
            usdt_target = current_equity * self.max_position_size
            
            return {
                'usdt_perp_position': usdt_target,
                'btc_balance': current_equity - usdt_target
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate target position: {e}")
            return {'usdt_perp_position': 0.0, 'btc_balance': current_equity}
    
    def entry_full(self, equity: float) -> StrategyAction:
        """Enter full ML USDT directional position."""
        try:
            # Log action start
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message=f"Executing entry_full action with equity={equity}",
                data={
                    'action': 'entry_full',
                    'equity': equity,
                    'strategy_type': self.__class__.__name__
                },
                level=LogLevel.INFO
            )
            
            # Calculate target position
            target_position = self.calculate_target_position(equity)
            
            # Generate instructions for ML USDT directional trading
            instructions = [
                {
                    'type': 'cex_trade',
                    'venue': 'binance',
                    'action': 'buy' if self.last_signal == 'long' else 'sell',
                    'symbol': 'USDTUSDT_PERP',
                    'amount': target_position['usdt_perp_position']
                }
            ]
            
            return StrategyAction(
                action_type='entry_full',
                target_amount=equity,
                target_currency='USDT',
                instructions=instructions,
                atomic=True
            )
            
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'action': 'entry_full',
                    'equity': equity
                }
            )
            logger.error(f"Error in entry_full: {e}")
            return StrategyAction(
                action_type='entry_full',
                target_amount=0.0,
                target_currency='USDT',
                instructions=[],
                atomic=False
            )
    
    def entry_partial(self, equity_delta: float) -> StrategyAction:
        """Enter partial ML USDT directional position."""
        try:
            # Log action start
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message=f"Executing entry_partial action with equity_delta={equity_delta}",
                data={
                    'action': 'entry_partial',
                    'equity_delta': equity_delta,
                    'strategy_type': self.__class__.__name__
                },
                level=LogLevel.INFO
            )
            
            # Calculate partial position
            partial_position = equity_delta * self.max_position_size
            
            instructions = [
                {
                    'type': 'cex_trade',
                    'venue': 'binance',
                    'action': 'buy' if self.last_signal == 'long' else 'sell',
                    'symbol': 'USDTUSDT_PERP',
                    'amount': partial_position
                }
            ]
            
            return StrategyAction(
                action_type='entry_partial',
                target_amount=equity_delta,
                target_currency='USDT',
                instructions=instructions,
                atomic=True
            )
            
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'action': 'entry_partial',
                    'equity_delta': equity_delta
                }
            )
            logger.error(f"Error in entry_partial: {e}")
            return StrategyAction(
                action_type='entry_partial',
                target_amount=0.0,
                target_currency='USDT',
                instructions=[],
                atomic=False
            )
    
    def exit_full(self, equity: float) -> StrategyAction:
        """Exit full ML USDT directional position."""
        try:
            # Log action start
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message=f"Executing exit_full action with equity={equity}",
                data={
                    'action': 'exit_full',
                    'equity': equity,
                    'strategy_type': self.__class__.__name__
                },
                level=LogLevel.INFO
            )
            
            instructions = [
                {
                    'type': 'cex_trade',
                    'venue': 'binance',
                    'action': 'close_position',
                    'symbol': 'USDTUSDT_PERP',
                    'amount': 'all'
                }
            ]
            
            return StrategyAction(
                action_type='exit_full',
                target_amount=equity,
                target_currency='USDT',
                instructions=instructions,
                atomic=True
            )
            
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'action': 'exit_full',
                    'equity': equity
                }
            )
            logger.error(f"Error in exit_full: {e}")
            return StrategyAction(
                action_type='exit_full',
                target_amount=0.0,
                target_currency='USDT',
                instructions=[],
                atomic=False
            )
    
    def exit_partial(self, equity_delta: float) -> StrategyAction:
        """Exit partial ML USDT directional position."""
        try:
            # Log action start
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message=f"Executing exit_partial action with equity_delta={equity_delta}",
                data={
                    'action': 'exit_partial',
                    'equity_delta': equity_delta,
                    'strategy_type': self.__class__.__name__
                },
                level=LogLevel.INFO
            )
            
            # Calculate partial exit amount
            partial_exit = equity_delta * self.max_position_size
            
            instructions = [
                {
                    'type': 'cex_trade',
                    'venue': 'binance',
                    'action': 'close_position',
                    'symbol': 'USDTUSDT_PERP',
                    'amount': partial_exit
                }
            ]
            
            return StrategyAction(
                action_type='exit_partial',
                target_amount=equity_delta,
                target_currency='USDT',
                instructions=instructions,
                atomic=True
            )
            
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'action': 'exit_partial',
                    'equity_delta': equity_delta
                }
            )
            logger.error(f"Error in exit_partial: {e}")
            return StrategyAction(
                action_type='exit_partial',
                target_amount=0.0,
                target_currency='USDT',
                instructions=[],
                atomic=False
            )
    
    def sell_dust(self, dust_tokens: Dict[str, float]) -> StrategyAction:
        """Sell dust tokens for ML USDT directional strategy."""
        try:
            # Log action start
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message=f"Executing sell_dust action with dust_tokens={dust_tokens}",
                data={
                    'action': 'sell_dust',
                    'dust_tokens': dust_tokens,
                    'strategy_type': self.__class__.__name__
                },
                level=LogLevel.INFO
            )
            
            # For ML directional strategy, dust management is minimal
            # Just maintain current position
            instructions = []
            
            return StrategyAction(
                action_type='sell_dust',
                target_amount=0.0,
                target_currency='USDT',
                instructions=instructions,
                atomic=False
            )
            
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'action': 'sell_dust',
                    'dust_tokens': dust_tokens
                }
            )
            logger.error(f"Error in sell_dust: {e}")
            return StrategyAction(
                action_type='sell_dust',
                target_amount=0.0,
                target_currency='USDT',
                instructions=[],
                atomic=False
            )
