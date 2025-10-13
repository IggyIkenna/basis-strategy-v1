"""
ML USDT Directional Strategy Implementation

Implements ML-driven directional USDT trading strategy using 5-minute interval signals
to generate long/short positions. Uses machine learning predictions for entry/exit signals
while taking full directional USDT exposure. Uses unified Order/Trade system.

Reference: docs/specs/strategies/09_ML_USDT_DIRECTIONAL_STRATEGY.md
Reference: docs/MODES.md - ML USDT Directional Strategy Mode
Reference: docs/specs/5B_BASE_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any
import logging
import pandas as pd

from .base_strategy_manager import BaseStrategyManager
from ...core.models.order import Order, OrderOperation
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
    
    def make_strategy_decision(self, timestamp: pd.Timestamp, trigger_source: str, market_data: Dict, exposure_data: Dict, risk_assessment: Dict) -> List[Order]:
        """
        Make ML USDT directional strategy decision based on market conditions and ML predictions.
        
        Args:
            timestamp: Current timestamp
            trigger_source: What triggered this decision
            market_data: Current market data
            exposure_data: Current exposure data
            risk_assessment: Risk assessment data
            
        Returns:
            List of Order objects to execute
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
                return self._create_dust_sell_orders({})
            
            # Check risk management first
            if self._should_exit_for_risk_management(usdt_price, current_positions, ml_predictions):
                return self._create_exit_full_orders(current_equity)
            
            # Check ML signal for entry/exit
            if ml_predictions['confidence'] > self.signal_threshold:
                signal = ml_predictions['signal']
                
                if signal == 'long' and not self._has_long_position(current_positions):
                    # Enter long position
                    return self._create_entry_full_orders(current_equity, signal)
                elif signal == 'short' and not self._has_short_position(current_positions):
                    # Enter short position
                    return self._create_entry_full_orders(current_equity, signal)
                elif signal == 'neutral' and self._has_any_position(current_positions):
                    # Exit position
                    return self._create_exit_full_orders(current_equity)
            
            # Default: maintain current position
            return self._create_dust_sell_orders({})
                
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
            return []
    
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
    
    def _get_asset_price(self) -> float:
        """Get current USDT price for testing."""
        # In real implementation, this would get actual price from market data
        return 1.0  # Mock USDT price
    
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
    
    def _create_entry_full_orders(self, equity: float, signal: str) -> List[Order]:
        """
        Create entry full orders for ML USDT directional strategy.
        
        Args:
            equity: Available equity in share class currency
            signal: ML signal ('long' or 'short')
            
        Returns:
            List of Order objects for full entry
        """
        try:
            # Calculate target position
            target_position = self.calculate_target_position(equity)
            
            # Store signal for reference
            self.last_signal = signal
            
            # Calculate take profit and stop loss
            usdt_price = self._get_asset_price()
            stop_loss, take_profit = self._calculate_stop_loss_take_profit(
                usdt_price, 0.02, signal  # 2% standard deviation
            )
            
            # Create USDT perpetual order with risk management
            order = Order(
                venue='binance',
                operation=OrderOperation.PERP_TRADE,
                pair='USDTUSDT',
                side='LONG' if signal == 'long' else 'SHORT',
                amount=target_position['usdt_perp_position'],
                price=usdt_price,
                order_type='market',
                take_profit=take_profit,
                stop_loss=stop_loss,
                execution_mode='sequential',
                strategy_intent='entry_full',
                strategy_id='ml_usdt_directional',
                metadata={
                    'ml_signal': signal,
                    'confidence': 0.8,  # Would come from ML predictions
                    'signal_threshold': self.signal_threshold
                }
            )
            
            return [order]
            
        except Exception as e:
            logger.error(f"Error creating entry full orders: {e}")
            return []
    
    def _create_entry_partial_orders(self, equity_delta: float, signal: str) -> List[Order]:
        """
        Create entry partial orders for ML USDT directional strategy.
        
        Args:
            equity_delta: Additional equity to deploy
            signal: ML signal ('long' or 'short')
            
        Returns:
            List of Order objects for partial entry
        """
        try:
            # Calculate partial position
            partial_position = equity_delta * self.max_position_size
            
            # Store signal for reference
            self.last_signal = signal
            
            # Calculate take profit and stop loss
            usdt_price = self._get_asset_price()
            stop_loss, take_profit = self._calculate_stop_loss_take_profit(
                usdt_price, 0.02, signal  # 2% standard deviation
            )
            
            # Create USDT perpetual order with risk management
            order = Order(
                venue='binance',
                operation=OrderOperation.PERP_TRADE,
                pair='USDTUSDT',
                side='LONG' if signal == 'long' else 'SHORT',
                amount=partial_position,
                price=usdt_price,
                order_type='market',
                take_profit=take_profit,
                stop_loss=stop_loss,
                execution_mode='sequential',
                strategy_intent='entry_partial',
                strategy_id='ml_usdt_directional',
                metadata={
                    'ml_signal': signal,
                    'confidence': 0.8,  # Would come from ML predictions
                    'signal_threshold': self.signal_threshold
                }
            )
            
            return [order]
            
        except Exception as e:
            logger.error(f"Error creating entry partial orders: {e}")
            return []
    
    def _create_exit_full_orders(self, equity: float) -> List[Order]:
        """
        Create exit full orders for ML USDT directional strategy.
        
        Args:
            equity: Total equity to exit
            
        Returns:
            List of Order objects for full exit
        """
        try:
            # Get current position to determine close side
            current_position = self.position_monitor.get_current_position()
            usdt_position = current_position.get('usdt_perp_position', 0.0)
            
            if usdt_position == 0:
                return []  # No position to close
            
            # Determine close side based on current position
            close_side = 'SELL' if usdt_position > 0 else 'BUY'
            
            # Create close position order
            order = Order(
                venue='binance',
                operation=OrderOperation.PERP_TRADE,
                pair='USDTUSDT',
                side=close_side,
                amount=abs(usdt_position),
                order_type='market',
                execution_mode='sequential',
                strategy_intent='exit_full',
                strategy_id='ml_usdt_directional',
                metadata={
                    'close_position': True,
                    'original_position': usdt_position
                }
            )
            
            return [order]
            
        except Exception as e:
            logger.error(f"Error creating exit full orders: {e}")
            return []
    
    def _create_exit_partial_orders(self, equity_delta: float) -> List[Order]:
        """
        Create exit partial orders for ML USDT directional strategy.
        
        Args:
            equity_delta: Equity to remove from position
            
        Returns:
            List of Order objects for partial exit
        """
        try:
            # Get current position to determine close side
            current_position = self.position_monitor.get_current_position()
            usdt_position = current_position.get('usdt_perp_position', 0.0)
            
            if usdt_position == 0:
                return []  # No position to close
            
            # Calculate partial exit amount
            partial_exit = equity_delta * self.max_position_size
            partial_exit = min(partial_exit, abs(usdt_position))  # Don't exceed current position
            
            # Determine close side based on current position
            close_side = 'SELL' if usdt_position > 0 else 'BUY'
            
            # Create close position order
            order = Order(
                venue='binance',
                operation=OrderOperation.PERP_TRADE,
                pair='USDTUSDT',
                side=close_side,
                amount=partial_exit,
                order_type='market',
                execution_mode='sequential',
                strategy_intent='exit_partial',
                strategy_id='ml_usdt_directional',
                metadata={
                    'close_position': True,
                    'partial_exit': True,
                    'original_position': usdt_position
                }
            )
            
            return [order]
            
        except Exception as e:
            logger.error(f"Error creating exit partial orders: {e}")
            return []
    
    def _create_dust_sell_orders(self, dust_tokens: Dict[str, float]) -> List[Order]:
        """
        Create dust sell orders for ML USDT directional strategy.
        
        Args:
            dust_tokens: Dictionary of dust tokens and amounts
            
        Returns:
            List of Order objects for dust selling
        """
        try:
            orders = []
            
            for token, amount in dust_tokens.items():
                if amount > 0 and token != 'USDT':  # USDT is the target asset
                    # Sell dust tokens for USDT
                    orders.append(Order(
                        venue='binance',
                        operation=OrderOperation.SPOT_TRADE,
                        pair=f'{token}/USDT',
                        side='SELL',
                        amount=amount,
                        execution_mode='sequential',
                        strategy_intent='sell_dust',
                        strategy_id='ml_usdt_directional'
                    ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating dust sell orders: {e}")
            return []
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get ML USDT directional strategy information and status.
        
        Returns:
            Dictionary with strategy information
        """
        try:
            base_info = super().get_strategy_info()
            
            # Add ML USDT directional-specific information
            base_info.update({
                'strategy_type': 'ml_usdt_directional',
                'signal_threshold': self.signal_threshold,
                'max_position_size': self.max_position_size,
                'stop_loss_pct': self.stop_loss_pct,
                'take_profit_pct': self.take_profit_pct,
                'description': 'ML-driven directional USDT trading with 5-minute signals using Order/Trade system',
                'order_system': 'unified_order_trade',
                'risk_management': 'take_profit_stop_loss'
            })
            
            return base_info
            
        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                'strategy_type': 'ml_usdt_directional',
                'mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'error': str(e)
            }
