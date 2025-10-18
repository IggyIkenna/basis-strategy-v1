"""
ML BTC Directional Strategy Implementation

Implements ML-driven directional BTC trading strategy using 5-minute interval signals
to generate long/short positions. Uses machine learning predictions for entry/exit signals
while taking full directional BTC exposure. Uses unified Order/Trade system.

Reference: docs/specs/strategies/08_ML_BTC_DIRECTIONAL_STRATEGY.md
Reference: docs/MODES.md - ML BTC Directional Strategy Mode
Reference: docs/specs/5B_BASE_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any
import logging
import pandas as pd

from .base_strategy_manager import BaseStrategyManager, StrategyAction
from ...core.models.order import Order, OrderOperation
from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)


class MLBTCDirectionalStrategy(BaseStrategyManager):
    """
    ML BTC Directional Strategy - ML-driven directional BTC trading.
    
    Strategy Overview:
    - Uses ML predictions for entry/exit signals
    - Takes full directional BTC exposure
    - 5-minute interval signal processing
    - Stop-loss and take-profit management
    - Target APY: 20-40% (high risk, high reward)
    """
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, event_engine, data_provider=None):
        """
        Initialize ML BTC directional strategy.
        
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
        self.signal_threshold = config['signal_threshold']  # 0.65 default
        self.max_position_size = config['max_position_size']  # Max position size
        self.stop_loss_pct = config['stop_loss_pct']  # Stop loss percentage
        self.take_profit_pct = config['take_profit_pct']  # Take profit percentage
        
        # ML model state
        self.ml_model = None
        self.last_prediction = None
        self.last_signal = None
        
        logger.info(f"MLBTCDirectionalStrategy initialized with signal threshold: {self.signal_threshold}")
    
    def make_strategy_decision(self, timestamp: pd.Timestamp, trigger_source: str, market_data: Dict, exposure_data: Dict, risk_assessment: Dict) -> List[Order]:
        """
        Make ML BTC directional strategy decision based on market conditions and ML predictions.
        
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
                message=f"Making ML BTC directional strategy decision triggered by {trigger_source}",
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
            
            # BTC-specific market analysis
            btc_price = market_data.get('prices', {}).get('BTC', 0.0)
            btc_perp_price = market_data.get('prices', {}).get('BTC_PERP', 0.0)
            
            # Risk assessment
            liquidation_risk = risk_assessment.get('liquidation_risk', 0.0)
            margin_ratio = risk_assessment.get('cex_margin_ratio', 1.0)
            
            # ML BTC Directional Strategy Decision Logic
            if ml_predictions is None:
                # No ML predictions available - maintain current position
                return self._create_dust_sell_orders({})
            
            # Check risk management first
            if self._should_exit_for_risk_management(btc_price, current_positions, ml_predictions):
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
            logger.error(f"Error in ML BTC directional strategy decision: {e}")
            return []
    
    def _get_ml_predictions(self, market_data: Dict) -> Dict:
        """Get ML predictions from data provider."""
        try:
            if self.data_provider is None:
                return None
            
            # Get ML predictions from data provider
            # This would be implemented based on the actual ML model integration
            ml_predictions = self.data_provider.get_ml_predictions('btc_directional')
            
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
        """Get current BTC price for testing."""
        # In real implementation, this would get actual price from market data
        return 45000.0  # Mock BTC price
    
    def _should_exit_for_risk_management(self, current_price: float, current_positions: Dict, ml_predictions: Dict) -> bool:
        """Check if we should exit position for risk management."""
        try:
            current_position = current_positions.get('btc_perp_position', 0.0)
            
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
        return current_positions.get('btc_perp_position', 0.0) > 0
    
    def _has_short_position(self, current_positions: Dict) -> bool:
        """Check if we have a short position."""
        return current_positions.get('btc_perp_position', 0.0) < 0
    
    def _has_any_position(self, current_positions: Dict) -> bool:
        """Check if we have any position."""
        return current_positions.get('btc_perp_position', 0.0) != 0
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position for ML BTC directional strategy.
        
        Args:
            current_equity: Current equity in share class currency
            
        Returns:
            Dictionary of target positions by token/venue
        """
        try:
            # For ML directional strategy, we use the full equity for directional exposure
            btc_target = current_equity * self.max_position_size
            
            return {
                'btc_perp_position': btc_target,
                'usdt_balance': current_equity - btc_target
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate target position: {e}")
            return {'btc_perp_position': 0.0, 'usdt_balance': current_equity}
    
    def _create_entry_full_orders(self, equity: float, signal: str) -> List[Order]:
        """
        Create entry full orders for ML BTC directional strategy.
        
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
            btc_price = self._get_asset_price()
            stop_loss, take_profit = self._calculate_stop_loss_take_profit(
                btc_price, 0.02, signal  # 2% standard deviation
            )
            
            # Create BTC perpetual order with risk management
            order = Order(
                venue='binance',
                operation=OrderOperation.PERP_TRADE,
                pair='BTCUSDT',
                side='LONG' if signal == 'long' else 'SHORT',
                amount=target_position['btc_perp_position'],
                price=btc_price,
                order_type='market',
                take_profit=take_profit,
                stop_loss=stop_loss,
                execution_mode='sequential',
                strategy_intent='entry_full',
                strategy_id='ml_btc_directional',
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
        Create entry partial orders for ML BTC directional strategy.
        
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
            btc_price = self._get_asset_price()
            stop_loss, take_profit = self._calculate_stop_loss_take_profit(
                btc_price, 0.02, signal  # 2% standard deviation
            )
            
            # Create BTC perpetual order with risk management
            order = Order(
                venue='binance',
                operation=OrderOperation.PERP_TRADE,
                pair='BTCUSDT',
                side='LONG' if signal == 'long' else 'SHORT',
                amount=partial_position,
                price=btc_price,
                order_type='market',
                take_profit=take_profit,
                stop_loss=stop_loss,
                execution_mode='sequential',
                strategy_intent='entry_partial',
                strategy_id='ml_btc_directional',
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
        Create exit full orders for ML BTC directional strategy.
        
        Args:
            equity: Total equity to exit
            
        Returns:
            List of Order objects for full exit
        """
        try:
            # Get current position to determine close side
            current_position = self.position_monitor.get_current_position()
            btc_position = current_position.get('btc_perp_position', 0.0)
            
            if btc_position == 0:
                return []  # No position to close
            
            # Determine close side based on current position
            close_side = 'SELL' if btc_position > 0 else 'BUY'
            
            # Create close position order
            order = Order(
                venue='binance',
                operation=OrderOperation.PERP_TRADE,
                pair='BTCUSDT',
                side=close_side,
                amount=abs(btc_position),
                order_type='market',
                execution_mode='sequential',
                strategy_intent='exit_full',
                strategy_id='ml_btc_directional',
                metadata={
                    'close_position': True,
                    'original_position': btc_position
                }
            )
            
            return [order]
            
        except Exception as e:
            logger.error(f"Error creating exit full orders: {e}")
            return []
    
    def _create_exit_partial_orders(self, equity_delta: float) -> List[Order]:
        """
        Create exit partial orders for ML BTC directional strategy.
        
        Args:
            equity_delta: Equity to remove from position
            
        Returns:
            List of Order objects for partial exit
        """
        try:
            # Get current position to determine close side
            current_position = self.position_monitor.get_current_position()
            btc_position = current_position.get('btc_perp_position', 0.0)
            
            if btc_position == 0:
                return []  # No position to close
            
            # Calculate partial exit amount
            partial_exit = equity_delta * self.max_position_size
            partial_exit = min(partial_exit, abs(btc_position))  # Don't exceed current position
            
            # Determine close side based on current position
            close_side = 'SELL' if btc_position > 0 else 'BUY'
            
            # Create close position order
            order = Order(
                venue='binance',
                operation=OrderOperation.PERP_TRADE,
                pair='BTCUSDT',
                side=close_side,
                amount=partial_exit,
                order_type='market',
                execution_mode='sequential',
                strategy_intent='exit_partial',
                strategy_id='ml_btc_directional',
                metadata={
                    'close_position': True,
                    'partial_exit': True,
                    'original_position': btc_position
                }
            )
            
            return [order]
            
        except Exception as e:
            logger.error(f"Error creating exit partial orders: {e}")
            return []
    
    def _create_dust_sell_orders(self, dust_tokens: Dict[str, float]) -> List[Order]:
        """
        Create dust sell orders for ML BTC directional strategy.
        
        Args:
            dust_tokens: Dictionary of dust tokens and amounts
            
        Returns:
            List of Order objects for dust selling
        """
        try:
            orders = []
            
            for token, amount in dust_tokens.items():
                if amount > 0 and token != 'BTC':  # BTC is the target asset
                    # Sell dust tokens for BTC
                    orders.append(Order(
                        venue='binance',
                        operation=OrderOperation.SPOT_TRADE,
                        pair=f'{token}/BTC',
                        side='SELL',
                        amount=amount,
                        execution_mode='sequential',
                        strategy_intent='sell_dust',
                        strategy_id='ml_btc_directional'
                    ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating dust sell orders: {e}")
            return []
    
    # Public action methods for backward compatibility
    def entry_full(self, equity: float) -> StrategyAction:
        """Enter full ML BTC directional position - wrapper for Order-based implementation."""
        try:
            orders = self._create_entry_full_orders(equity, 'long')  # Default to long
            # Convert orders to legacy StrategyAction format
            instructions = []
            for order in orders:
                instructions.append({
                    'type': 'order',
                    'venue': order.venue,
                    'operation': order.operation.value,
                    'amount': order.amount,
                    'pair': order.pair,
                    'side': order.side,
                    'execution_mode': order.execution_mode,
                    'take_profit': order.take_profit,
                    'stop_loss': order.stop_loss
                })
            
            return StrategyAction(
                action_type='entry_full',
                target_amount=equity,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'ml_btc_directional',
                    'signal_threshold': self.signal_threshold,
                    'max_position_size': self.max_position_size,
                    'order_system': 'unified_order_trade'
                }
            )
        except Exception as e:
            logger.error(f"Error in entry_full: {e}")
            return StrategyAction(
                action_type='entry_full',
                target_amount=0.0,
                target_currency=self.share_class,
                instructions=[],
                atomic=False,
                metadata={'error': str(e)}
            )
    
    def entry_partial(self, equity_delta: float) -> StrategyAction:
        """Enter partial ML BTC directional position - wrapper for Order-based implementation."""
        try:
            orders = self._create_entry_partial_orders(equity_delta, 'long')  # Default to long
            # Convert orders to legacy StrategyAction format
            instructions = []
            for order in orders:
                instructions.append({
                    'type': 'order',
                    'venue': order.venue,
                    'operation': order.operation.value,
                    'amount': order.amount,
                    'pair': order.pair,
                    'side': order.side,
                    'execution_mode': order.execution_mode,
                    'take_profit': order.take_profit,
                    'stop_loss': order.stop_loss
                })
            
            return StrategyAction(
                action_type='entry_partial',
                target_amount=equity_delta,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'ml_btc_directional',
                    'equity_delta': equity_delta,
                    'signal_threshold': self.signal_threshold,
                    'order_system': 'unified_order_trade'
                }
            )
        except Exception as e:
            logger.error(f"Error in entry_partial: {e}")
            return StrategyAction(
                action_type='entry_partial',
                target_amount=0.0,
                target_currency=self.share_class,
                instructions=[],
                atomic=False,
                metadata={'error': str(e)}
            )
    
    def exit_full(self, equity: float) -> StrategyAction:
        """Exit full ML BTC directional position - wrapper for Order-based implementation."""
        try:
            orders = self._create_exit_full_orders(equity)
            # Convert orders to legacy StrategyAction format
            instructions = []
            for order in orders:
                instructions.append({
                    'type': 'order',
                    'venue': order.venue,
                    'operation': order.operation.value,
                    'amount': order.amount,
                    'pair': order.pair,
                    'side': order.side,
                    'execution_mode': order.execution_mode
                })
            
            return StrategyAction(
                action_type='exit_full',
                target_amount=equity,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'ml_btc_directional',
                    'order_system': 'unified_order_trade'
                }
            )
        except Exception as e:
            logger.error(f"Error in exit_full: {e}")
            return StrategyAction(
                action_type='exit_full',
                target_amount=0.0,
                target_currency=self.share_class,
                instructions=[],
                atomic=False,
                metadata={'error': str(e)}
            )
    
    def exit_partial(self, equity_delta: float) -> StrategyAction:
        """Exit partial ML BTC directional position - wrapper for Order-based implementation."""
        try:
            orders = self._create_exit_partial_orders(equity_delta)
            # Convert orders to legacy StrategyAction format
            instructions = []
            for order in orders:
                instructions.append({
                    'type': 'order',
                    'venue': order.venue,
                    'operation': order.operation.value,
                    'amount': order.amount,
                    'pair': order.pair,
                    'side': order.side,
                    'execution_mode': order.execution_mode
                })
            
            return StrategyAction(
                action_type='exit_partial',
                target_amount=equity_delta,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'ml_btc_directional',
                    'equity_delta': equity_delta,
                    'order_system': 'unified_order_trade'
                }
            )
        except Exception as e:
            logger.error(f"Error in exit_partial: {e}")
            return StrategyAction(
                action_type='exit_partial',
                target_amount=0.0,
                target_currency=self.share_class,
                instructions=[],
                atomic=False,
                metadata={'error': str(e)}
            )
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get ML BTC directional strategy information and status.
        
        Returns:
            Dictionary with strategy information
        """
        try:
            base_info = super().get_strategy_info()
            
            # Add ML BTC directional-specific information
            base_info.update({
                'strategy_type': 'ml_btc_directional',
                'signal_threshold': self.signal_threshold,
                'max_position_size': self.max_position_size,
                'stop_loss_pct': self.stop_loss_pct,
                'take_profit_pct': self.take_profit_pct,
                'description': 'ML-driven directional BTC trading with 5-minute signals using Order/Trade system',
                'order_system': 'unified_order_trade',
                'risk_management': 'take_profit_stop_loss'
            })
            
            return base_info
            
        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                'strategy_type': 'ml_btc_directional',
                'mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'error': str(e)
            }
