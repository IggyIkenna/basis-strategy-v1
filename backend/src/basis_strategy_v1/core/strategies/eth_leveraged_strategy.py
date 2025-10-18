"""
ETH Leveraged Strategy Implementation

Implements ETH leveraged staking strategy with LSTs and optional hedging.
Uses unified Order/Trade system for execution.

Reference: docs/MODES.md - ETH Leveraged Strategy Mode
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any
import logging
import pandas as pd

from .base_strategy_manager import BaseStrategyManager, StrategyAction
from ...core.models.order import Order, OrderOperation
from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)


class ETHLeveragedStrategy(BaseStrategyManager):
    """
    ETH Leveraged Strategy - Leveraged staking with LSTs and optional hedging.
    
    Strategy Overview:
    - Stake ETH via liquid staking protocols
    - Use leverage to increase exposure
    - Optional hedging via short positions
    - Target APY: 20-40%
    """
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, event_engine):
        """
        Initialize ETH leveraged strategy.
        
        Args:
            config: Strategy configuration
            risk_monitor: Risk monitor instance
            position_monitor: Position monitor instance
            event_engine: Event engine instance
        """
        super().__init__(config, risk_monitor, position_monitor, event_engine)
        
        # Validate required configuration at startup (fail-fast)
        required_keys = ['eth_allocation', 'leverage_multiplier', 'lst_type', 'staking_protocol', 'hedge_allocation']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        # ETH leveraged-specific configuration (fail-fast access)
        self.eth_allocation = config['eth_allocation']  # 80% to ETH
        self.leverage_multiplier = config['leverage_multiplier']  # 2x leverage
        self.lst_type = config['lst_type']  # Default LST type
        self.staking_protocol = config['staking_protocol']  # Default protocol
        self.hedge_allocation = config['hedge_allocation']  # No hedging by default
        
        logger.info(f"ETHLeveragedStrategy initialized with {self.eth_allocation*100}% ETH allocation, {self.leverage_multiplier}x leverage")
    
    def make_strategy_decision(self, timestamp: pd.Timestamp, trigger_source: str, market_data: Dict, exposure_data: Dict, risk_assessment: Dict) -> List[Order]:
        """
        Make ETH leveraged strategy decision based on market conditions.
        
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
                message=f"Making ETH leveraged strategy decision triggered by {trigger_source}",
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
            
            # Check if we have any position
            has_position = any(
                current_positions.get(f'{self.lst_type.lower()}_balance', 0.0) > 0 or
                current_positions.get('eth_perpetual_short', 0.0) != 0
                for _ in [1]
            )
            
            # ETH Leveraged Strategy Decision Logic
            if current_equity > 0 and not has_position:
                # Enter full position
                return self._create_entry_full_orders(current_equity)
            elif current_equity > 0 and has_position:
                # Check for dust tokens to sell
                dust_tokens = exposure_data.get('dust_tokens', {})
                if dust_tokens:
                    return self._create_dust_sell_orders(dust_tokens)
                else:
                    # No action needed
                    return []
            else:
                # No equity or exit needed
                return []
                
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'method': 'make_strategy_decision',
                    'trigger_source': trigger_source,
                    'strategy_type': self.__class__.__name__
                }
            )
            logger.error(f"Error in ETH leveraged strategy decision: {e}")
            return []
    
    def _get_asset_price(self) -> float:
        """Get current ETH price for testing."""
        # In real implementation, this would get actual price from market data
        return 3000.0  # Mock ETH price
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position for ETH leveraged strategy.
        
        Args:
            current_equity: Current equity in share class currency
            
        Returns:
            Dictionary of target positions by token/venue
        """
        try:
            # Calculate target allocations with leverage
            leveraged_equity = current_equity * self.leverage_multiplier
            eth_target = leveraged_equity * self.eth_allocation
            hedge_target = leveraged_equity * self.hedge_allocation
            
            # Get current ETH price
            eth_price = self._get_asset_price()
            eth_amount = eth_target / eth_price if eth_price > 0 else 0
            hedge_amount = hedge_target / eth_price if eth_price > 0 else 0
            
            return {
                'eth_balance': 0.0,  # No raw ETH, all staked
                f'{self.lst_type.lower()}_balance': eth_amount,  # Leveraged ETH staked
                'eth_perpetual_short': -hedge_amount,  # Optional hedge position
                f'{self.share_class.lower()}_balance': reserve_target,
                'total_equity': current_equity,
                'leveraged_equity': leveraged_equity
            }
            
        except Exception as e:
            logger.error(f"Error calculating target position: {e}")
            return {
                'eth_balance': 0.0,
                f'{self.lst_type.lower()}_balance': 0.0,
                'eth_perpetual_short': 0.0,
                'total_equity': current_equity,
                'leveraged_equity': current_equity
            }
    
    def _create_entry_full_orders(self, equity: float) -> List[Order]:
        """
        Create entry full orders for ETH leveraged strategy.
        
        Args:
            equity: Available equity in share class currency
            
        Returns:
            List of Order objects for full entry
        """
        try:
            # Calculate target position
            target_position = self.calculate_target_position(equity)
            
            orders = []
            atomic_group_id = f"eth_leveraged_entry_{int(equity)}"
            
            # 1. Buy ETH with leverage (atomic group)
            eth_amount = target_position[f'{self.lst_type.lower()}_balance']
            if eth_amount > 0:
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='BUY',
                    amount=eth_amount,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=1,
                    strategy_intent='entry_full',
                    strategy_id='eth_leveraged',
                    metadata={'leverage': self.leverage_multiplier}
                ))
            
            # 2. Stake ETH to get LST (atomic group)
            if eth_amount > 0:
                orders.append(Order(
                    venue=self.staking_protocol,
                    operation=OrderOperation.STAKE,
                    token_in='ETH',
                    token_out=self.lst_type,
                    amount=eth_amount,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=2,
                    strategy_intent='entry_full',
                    strategy_id='eth_leveraged'
                ))
            
            # 3. Open hedge position if configured (atomic group)
            hedge_amount = target_position['eth_perpetual_short']
            if hedge_amount < 0:
                orders.append(Order(
                    venue='bybit',
                    operation=OrderOperation.PERP_TRADE,
                    pair='ETHUSDT',
                    side='SHORT',
                    amount=abs(hedge_amount),
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=3,
                    strategy_intent='entry_full',
                    strategy_id='eth_leveraged'
                ))
            
            # 4. Maintain reserves (sequential)
            reserve_amount = target_position[f'{self.share_class.lower()}_balance']
            if reserve_amount > 0:
                orders.append(Order(
                    venue='wallet',
                    operation=OrderOperation.TRANSFER,
                    source_venue='wallet',
                    target_venue='wallet',
                    token=self.share_class,
                    amount=reserve_amount,
                    execution_mode='sequential',
                    strategy_intent='reserve',
                    strategy_id='eth_leveraged'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating entry full orders: {e}")
            return []
    
    def _create_entry_partial_orders(self, equity_delta: float) -> List[Order]:
        """
        Create entry partial orders for ETH leveraged strategy.
        
        Args:
            equity_delta: Additional equity to deploy
            
        Returns:
            List of Order objects for partial entry
        """
        try:
            # Calculate proportional allocation with leverage
            leveraged_delta = equity_delta * self.leverage_multiplier
            eth_delta = leveraged_delta * self.eth_allocation
            hedge_delta = leveraged_delta * self.hedge_allocation
            
            # Get current ETH price
            eth_price = self._get_asset_price()
            eth_amount = eth_delta / eth_price if eth_price > 0 else 0
            hedge_amount = hedge_delta / eth_price if eth_price > 0 else 0
            
            orders = []
            atomic_group_id = f"eth_leveraged_partial_{int(equity_delta)}"
            
            # 1. Buy additional ETH with leverage (atomic group)
            if eth_amount > 0:
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='BUY',
                    amount=eth_amount,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=1,
                    strategy_intent='entry_partial',
                    strategy_id='eth_leveraged',
                    metadata={'leverage': self.leverage_multiplier}
                ))
            
            # 2. Stake additional ETH (atomic group)
            if eth_amount > 0:
                orders.append(Order(
                    venue=self.staking_protocol,
                    operation=OrderOperation.STAKE,
                    token_in='ETH',
                    token_out=self.lst_type,
                    amount=eth_amount,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=2,
                    strategy_intent='entry_partial',
                    strategy_id='eth_leveraged'
                ))
            
            # 3. Increase hedge position if configured (atomic group)
            if hedge_amount > 0:
                orders.append(Order(
                    venue='bybit',
                    operation=OrderOperation.PERP_TRADE,
                    pair='ETHUSDT',
                    side='SHORT',
                    amount=hedge_amount,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=3,
                    strategy_intent='entry_partial',
                    strategy_id='eth_leveraged'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating entry partial orders: {e}")
            return []
    
    def _create_exit_full_orders(self, equity: float) -> List[Order]:
        """
        Create exit full orders for ETH leveraged strategy.
        
        Args:
            equity: Total equity to exit
            
        Returns:
            List of Order objects for full exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            lst_balance = current_position.get(f'{self.lst_type.lower()}_balance', 0.0)
            hedge_balance = current_position.get('eth_perpetual_short', 0.0)
            
            orders = []
            atomic_group_id = f"eth_leveraged_exit_{int(equity)}"
            
            # 1. Close hedge position (atomic group)
            if hedge_balance < 0:
                orders.append(Order(
                    venue='bybit',
                    operation=OrderOperation.PERP_TRADE,
                    pair='ETHUSDT',
                    side='LONG',  # Close short position
                    amount=abs(hedge_balance),
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=1,
                    strategy_intent='exit_full',
                    strategy_id='eth_leveraged'
                ))
            
            # 2. Unstake LST to get ETH (atomic group)
            if lst_balance > 0:
                orders.append(Order(
                    venue=self.staking_protocol,
                    operation=OrderOperation.UNSTAKE,
                    token_in=self.lst_type,
                    token_out='ETH',
                    amount=lst_balance,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=2,
                    strategy_intent='exit_full',
                    strategy_id='eth_leveraged'
                ))
            
            # 3. Sell ETH (atomic group)
            if lst_balance > 0:
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='SELL',
                    amount=lst_balance,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=3,
                    strategy_intent='exit_full',
                    strategy_id='eth_leveraged'
                ))
            
            # 4. Convert all to share class currency (sequential)
            orders.append(Order(
                venue='wallet',
                operation=OrderOperation.TRANSFER,
                source_venue='wallet',
                target_venue='wallet',
                token=self.share_class,
                amount=equity,
                execution_mode='sequential',
                strategy_intent='exit_full',
                strategy_id='eth_leveraged'
            ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating exit full orders: {e}")
            return []
    
    def _create_exit_partial_orders(self, equity_delta: float) -> List[Order]:
        """
        Create exit partial orders for ETH leveraged strategy.
        
        Args:
            equity_delta: Equity to remove from position
            
        Returns:
            List of Order objects for partial exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            lst_balance = current_position.get(f'{self.lst_type.lower()}_balance', 0.0)
            hedge_balance = current_position.get('eth_perpetual_short', 0.0)
            
            # Calculate proportional reduction
            total_position = lst_balance + abs(hedge_balance)
            if total_position > 0:
                reduction_ratio = min(equity_delta / (total_position * self._get_asset_price()), 1.0)
            else:
                reduction_ratio = 0.0
            
            lst_reduction = lst_balance * reduction_ratio
            hedge_reduction = abs(hedge_balance) * reduction_ratio
            
            orders = []
            atomic_group_id = f"eth_leveraged_partial_exit_{int(equity_delta)}"
            
            # 1. Reduce hedge position (atomic group)
            if hedge_reduction > 0:
                orders.append(Order(
                    venue='bybit',
                    operation=OrderOperation.PERP_TRADE,
                    pair='ETHUSDT',
                    side='LONG',  # Reduce short position
                    amount=hedge_reduction,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=1,
                    strategy_intent='exit_partial',
                    strategy_id='eth_leveraged'
                ))
            
            # 2. Unstake proportional LST (atomic group)
            if lst_reduction > 0:
                orders.append(Order(
                    venue=self.staking_protocol,
                    operation=OrderOperation.UNSTAKE,
                    token_in=self.lst_type,
                    token_out='ETH',
                    amount=lst_reduction,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=2,
                    strategy_intent='exit_partial',
                    strategy_id='eth_leveraged'
                ))
            
            # 3. Sell proportional ETH (atomic group)
            if lst_reduction > 0:
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='SELL',
                    amount=lst_reduction,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=3,
                    strategy_intent='exit_partial',
                    strategy_id='eth_leveraged'
                ))
            
            # 4. Convert to share class currency (sequential)
            orders.append(Order(
                venue='wallet',
                operation=OrderOperation.TRANSFER,
                source_venue='wallet',
                target_venue='wallet',
                token=self.share_class,
                amount=equity_delta,
                execution_mode='sequential',
                strategy_intent='exit_partial',
                strategy_id='eth_leveraged'
            ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating exit partial orders: {e}")
            return []
    
    def _create_dust_sell_orders(self, dust_tokens: Dict[str, float]) -> List[Order]:
        """
        Create dust sell orders for ETH leveraged strategy.
        
        Args:
            dust_tokens: Dictionary of dust tokens and amounts
            
        Returns:
            List of Order objects for dust selling
        """
        try:
            orders = []
            
            for token, amount in dust_tokens.items():
                if amount > 0 and token != self.share_class:
                    # Convert to share class currency
                    if token == 'ETH':
                        # Sell ETH for share class
                        orders.append(Order(
                            venue='binance',
                            operation=OrderOperation.SPOT_TRADE,
                            pair='ETH/USDT',
                            side='SELL',
                            amount=amount,
                            execution_mode='sequential',
                            strategy_intent='sell_dust',
                            strategy_id='eth_leveraged'
                        ))
                    
                    elif token == self.lst_type:
                        # Unstake LST first, then sell ETH (atomic group)
                        atomic_group_id = f"dust_unstake_{token}_{int(amount)}"
                        orders.append(Order(
                            venue=self.staking_protocol,
                            operation=OrderOperation.UNSTAKE,
                            token_in=token,
                            token_out='ETH',
                            amount=amount,
                            execution_mode='atomic',
                            atomic_group_id=atomic_group_id,
                            sequence_in_group=1,
                            strategy_intent='sell_dust',
                            strategy_id='eth_leveraged'
                        ))
                        orders.append(Order(
                            venue='binance',
                            operation=OrderOperation.SPOT_TRADE,
                            pair='ETH/USDT',
                            side='SELL',
                            amount=amount,
                            execution_mode='atomic',
                            atomic_group_id=atomic_group_id,
                            sequence_in_group=2,
                            strategy_intent='sell_dust',
                            strategy_id='eth_leveraged'
                        ))
                    
                    elif token in ['BTC', 'USDT']:
                        # Direct conversion
                        orders.append(Order(
                            venue='wallet',
                            operation=OrderOperation.TRANSFER,
                            source_venue='wallet',
                            target_venue='wallet',
                            token=token,
                            amount=amount,
                            execution_mode='sequential',
                            strategy_intent='sell_dust',
                            strategy_id='eth_leveraged'
                        ))
                    
                    else:
                        # Other tokens - sell for share class
                        orders.append(Order(
                            venue='binance',
                            operation=OrderOperation.SPOT_TRADE,
                            pair=f'{token}/USDT',
                            side='SELL',
                            amount=amount,
                            execution_mode='sequential',
                            strategy_intent='sell_dust',
                            strategy_id='eth_leveraged'
                        ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating dust sell orders: {e}")
            return []
    
    # Public action methods for backward compatibility
    def entry_full(self, equity: float) -> StrategyAction:
        """Enter full ETH leveraged position - wrapper for Order-based implementation."""
        try:
            orders = self._create_entry_full_orders(equity)
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
                    'atomic_group_id': order.atomic_group_id,
                    'sequence_in_group': order.sequence_in_group
                })
            
            return StrategyAction(
                action_type='entry_full',
                target_amount=equity,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'eth_leveraged',
                    'eth_allocation': self.eth_allocation,
                    'leverage_multiplier': self.leverage_multiplier,
                    'lst_type': self.lst_type,
                    'hedge_allocation': self.hedge_allocation,
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
        """Enter partial ETH leveraged position - wrapper for Order-based implementation."""
        try:
            orders = self._create_entry_partial_orders(equity_delta)
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
                    'atomic_group_id': order.atomic_group_id,
                    'sequence_in_group': order.sequence_in_group
                })
            
            return StrategyAction(
                action_type='entry_partial',
                target_amount=equity_delta,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'eth_leveraged',
                    'eth_delta': equity_delta,
                    'leverage_multiplier': self.leverage_multiplier,
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
        """Exit full ETH leveraged position - wrapper for Order-based implementation."""
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
                    'execution_mode': order.execution_mode,
                    'atomic_group_id': order.atomic_group_id,
                    'sequence_in_group': order.sequence_in_group
                })
            
            return StrategyAction(
                action_type='exit_full',
                target_amount=equity,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'eth_leveraged',
                    'lst_type': self.lst_type,
                    'leverage_multiplier': self.leverage_multiplier,
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
        """Exit partial ETH leveraged position - wrapper for Order-based implementation."""
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
                    'execution_mode': order.execution_mode,
                    'atomic_group_id': order.atomic_group_id,
                    'sequence_in_group': order.sequence_in_group
                })
            
            return StrategyAction(
                action_type='exit_partial',
                target_amount=equity_delta,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'eth_leveraged',
                    'equity_delta': equity_delta,
                    'lst_type': self.lst_type,
                    'leverage_multiplier': self.leverage_multiplier,
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
    
    def sell_dust(self, dust_tokens: Dict[str, float]) -> StrategyAction:
        """Sell dust tokens - wrapper for Order-based implementation."""
        try:
            orders = self._create_dust_sell_orders(dust_tokens)
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
                    'atomic_group_id': order.atomic_group_id,
                    'sequence_in_group': order.sequence_in_group
                })
            
            return StrategyAction(
                action_type='sell_dust',
                target_amount=sum(dust_tokens.values()),
                target_currency=self.share_class,
                instructions=instructions,
                atomic=False,
                metadata={
                    'strategy': 'eth_leveraged',
                    'dust_tokens': dust_tokens,
                    'lst_type': self.lst_type,
                    'order_system': 'unified_order_trade'
                }
            )
        except Exception as e:
            logger.error(f"Error in sell_dust: {e}")
            return StrategyAction(
                action_type='sell_dust',
                target_amount=0.0,
                target_currency=self.share_class,
                instructions=[],
                atomic=False,
                metadata={'error': str(e)}
            )
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get ETH leveraged strategy information and status.
        
        Returns:
            Dictionary with strategy information
        """
        try:
            base_info = super().get_strategy_info()
            
            # Add ETH leveraged-specific information
            base_info.update({
                'strategy_type': 'eth_leveraged',
                'eth_allocation': self.eth_allocation,
                'leverage_multiplier': self.leverage_multiplier,
                'lst_type': self.lst_type,
                'staking_protocol': self.staking_protocol,
                'hedge_allocation': self.hedge_allocation,
                'description': 'ETH leveraged staking with LST tokens and optional hedging using Order/Trade system',
                'order_system': 'unified_order_trade'
            })
            
            return base_info
            
        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                'strategy_type': 'eth_leveraged',
                'mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'error': str(e)
            }
