"""
USDT Market Neutral Strategy Implementation

Implements USDT market neutral strategy with leverage.
Uses unified Order/Trade system for execution.

Reference: docs/MODES.md - USDT Market Neutral Strategy Mode
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any
import logging
import pandas as pd

from .base_strategy_manager import BaseStrategyManager
from ...core.models.order import Order, OrderOperation
from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)


class USDTMarketNeutralStrategy(BaseStrategyManager):
    """
    USDT Market Neutral Strategy - Market neutral with leverage.
    
    Strategy Overview:
    - Lend USDT on AAVE/Morpho with leverage
    - Stake ETH via liquid staking
    - Use leverage to increase exposure
    - Target APY: 15-30%
    """
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, event_engine):
        """
        Initialize USDT market neutral strategy.
        
        Args:
            config: Strategy configuration
            risk_monitor: Risk monitor instance
            position_monitor: Position monitor instance
            event_engine: Event engine instance
        """
        super().__init__(config, risk_monitor, position_monitor, event_engine)
        
        # Validate required configuration at startup (fail-fast)
        required_keys = ['usdt_allocation', 'eth_allocation', 'leverage_multiplier', 'lst_type', 'lending_protocol', 'staking_protocol']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        # USDT market neutral-specific configuration (fail-fast access)
        self.usdt_allocation = config['usdt_allocation']  # 70% to USDT lending
        self.eth_allocation = config['eth_allocation']  # 20% to ETH staking
        self.leverage_multiplier = config['leverage_multiplier']  # 2x leverage
        self.lst_type = config['lst_type']  # Default LST type
        self.lending_protocol = config['lending_protocol']  # Default lending protocol
        self.staking_protocol = config['staking_protocol']  # Default staking protocol
        
        logger.info(f"USDTMarketNeutralStrategy initialized with {self.usdt_allocation*100}% USDT lending, {self.eth_allocation*100}% ETH staking, {self.leverage_multiplier}x leverage")
    
    def make_strategy_decision(self, timestamp: pd.Timestamp, trigger_source: str, market_data: Dict, exposure_data: Dict, risk_assessment: Dict) -> List[Order]:
        """
        Make USDT market neutral strategy decision based on market conditions.
        
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
                message=f"Making USDT market neutral strategy decision triggered by {trigger_source}",
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
                current_positions.get('aUSDT_balance', 0.0) > 0 or
                current_positions.get(f'{self.lst_type.lower()}_balance', 0.0) > 0
                for _ in [1]
            )
            
            # USDT Market Neutral Strategy Decision Logic
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
            logger.error(f"Error in USDT market neutral strategy decision: {e}")
            return []
    
    def _get_asset_price(self) -> float:
        """Get current ETH price for testing."""
        # In real implementation, this would get actual price from market data
        return 3000.0  # Mock ETH price
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position for USDT market neutral strategy.
        
        Args:
            current_equity: Current equity in share class currency
            
        Returns:
            Dictionary of target positions by token/venue
        """
        try:
            # Calculate target allocations with leverage
            leveraged_equity = current_equity * self.leverage_multiplier
            usdt_target = leveraged_equity * self.usdt_allocation
            eth_target = leveraged_equity * self.eth_allocation
            
            # Get current ETH price
            eth_price = self._get_asset_price()
            eth_amount = eth_target / eth_price if eth_price > 0 else 0
            
            return {
                'usdt_balance': 0.0,  # No raw USDT, all lent
                'aUSDT_balance': usdt_target,  # Leveraged lent USDT
                'eth_balance': 0.0,  # No raw ETH, all staked
                f'{self.lst_type.lower()}_balance': eth_amount,  # Staked ETH
                f'{self.share_class.lower()}_balance': current_equity,
                'total_equity': current_equity,
                'leveraged_equity': leveraged_equity
            }
            
        except Exception as e:
            logger.error(f"Error calculating target position: {e}")
            return {
                'usdt_balance': 0.0,
                'aUSDT_balance': 0.0,
                'eth_balance': 0.0,
                f'{self.lst_type.lower()}_balance': 0.0,
                f'{self.share_class.lower()}_balance': current_equity,
                'total_equity': current_equity,
                'leveraged_equity': current_equity
            }
    
    def _create_entry_full_orders(self, equity: float) -> List[Order]:
        """
        Create entry full orders for USDT market neutral strategy.
        
        Args:
            equity: Available equity in share class currency
            
        Returns:
            List of Order objects for full entry
        """
        try:
            # Calculate target position
            target_position = self.calculate_target_position(equity)
            
            orders = []
            atomic_group_id = f"usdt_market_neutral_entry_{int(equity)}"
            
            # 1. Lend USDT with leverage (atomic group)
            usdt_amount = target_position['aUSDT_balance']
            if usdt_amount > 0:
                orders.append(Order(
                    venue=self.lending_protocol,
                    operation=OrderOperation.SUPPLY,
                    token_in='USDT',
                    token_out='aUSDT',
                    amount=usdt_amount,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=1,
                    strategy_intent='entry_full',
                    strategy_id='usdt_market_neutral',
                    metadata={'leverage': self.leverage_multiplier}
                ))
            
            # 2. Buy ETH for staking (atomic group)
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
                    sequence_in_group=2,
                    strategy_intent='entry_full',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 3. Stake ETH (atomic group)
            if eth_amount > 0:
                orders.append(Order(
                    venue=self.staking_protocol,
                    operation=OrderOperation.STAKE,
                    token_in='ETH',
                    token_out=self.lst_type,
                    amount=eth_amount,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=3,
                    strategy_intent='entry_full',
                    strategy_id='usdt_market_neutral'
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
                    strategy_id='usdt_market_neutral'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating entry full orders: {e}")
            return []
    
    def _create_entry_partial_orders(self, equity_delta: float) -> List[Order]:
        """
        Create entry partial orders for USDT market neutral strategy.
        
        Args:
            equity_delta: Additional equity to deploy
            
        Returns:
            List of Order objects for partial entry
        """
        try:
            # Calculate proportional allocation with leverage
            leveraged_delta = equity_delta * self.leverage_multiplier
            usdt_delta = leveraged_delta * self.usdt_allocation
            eth_delta = leveraged_delta * self.eth_allocation
            
            # Get current ETH price
            eth_price = self._get_asset_price()
            eth_amount = eth_delta / eth_price if eth_price > 0 else 0
            
            orders = []
            atomic_group_id = f"usdt_market_neutral_partial_{int(equity_delta)}"
            
            # 1. Lend additional USDT with leverage (atomic group)
            if usdt_delta > 0:
                orders.append(Order(
                    venue=self.lending_protocol,
                    operation=OrderOperation.SUPPLY,
                    token_in='USDT',
                    token_out='aUSDT',
                    amount=usdt_delta,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=1,
                    strategy_intent='entry_partial',
                    strategy_id='usdt_market_neutral',
                    metadata={'leverage': self.leverage_multiplier}
                ))
            
            # 2. Buy additional ETH (atomic group)
            if eth_amount > 0:
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='BUY',
                    amount=eth_amount,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=2,
                    strategy_intent='entry_partial',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 3. Stake additional ETH (atomic group)
            if eth_amount > 0:
                orders.append(Order(
                    venue=self.staking_protocol,
                    operation=OrderOperation.STAKE,
                    token_in='ETH',
                    token_out=self.lst_type,
                    amount=eth_amount,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=3,
                    strategy_intent='entry_partial',
                    strategy_id='usdt_market_neutral'
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating entry partial orders: {e}")
            return []
    
    def _create_exit_full_orders(self, equity: float) -> List[Order]:
        """
        Create exit full orders for USDT market neutral strategy.
        
        Args:
            equity: Total equity to exit
            
        Returns:
            List of Order objects for full exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            ausdt_balance = current_position.get('aUSDT_balance', 0.0)
            lst_balance = current_position.get(f'{self.lst_type.lower()}_balance', 0.0)
            
            orders = []
            atomic_group_id = f"usdt_market_neutral_exit_{int(equity)}"
            
            # 1. Unstake LST to get ETH (atomic group)
            if lst_balance > 0:
                orders.append(Order(
                    venue=self.staking_protocol,
                    operation=OrderOperation.UNSTAKE,
                    token_in=self.lst_type,
                    token_out='ETH',
                    amount=lst_balance,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=1,
                    strategy_intent='exit_full',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 2. Sell ETH (atomic group)
            if lst_balance > 0:
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='SELL',
                    amount=lst_balance,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=2,
                    strategy_intent='exit_full',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 3. Withdraw lent USDT (atomic group)
            if ausdt_balance > 0:
                orders.append(Order(
                    venue=self.lending_protocol,
                    operation=OrderOperation.WITHDRAW,
                    token_in='aUSDT',
                    token_out='USDT',
                    amount=ausdt_balance,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=3,
                    strategy_intent='exit_full',
                    strategy_id='usdt_market_neutral'
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
                strategy_id='usdt_market_neutral'
            ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating exit full orders: {e}")
            return []
    
    def _create_exit_partial_orders(self, equity_delta: float) -> List[Order]:
        """
        Create exit partial orders for USDT market neutral strategy.
        
        Args:
            equity_delta: Equity to remove from position
            
        Returns:
            List of Order objects for partial exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            ausdt_balance = current_position.get('aUSDT_balance', 0.0)
            lst_balance = current_position.get(f'{self.lst_type.lower()}_balance', 0.0)
            
            # Calculate proportional reduction
            total_position_value = ausdt_balance + (lst_balance * self._get_asset_price())
            if total_position_value > 0:
                reduction_ratio = min(equity_delta / total_position_value, 1.0)
            else:
                reduction_ratio = 0.0
            
            ausdt_reduction = ausdt_balance * reduction_ratio
            lst_reduction = lst_balance * reduction_ratio
            
            orders = []
            atomic_group_id = f"usdt_market_neutral_partial_exit_{int(equity_delta)}"
            
            # 1. Unstake proportional LST (atomic group)
            if lst_reduction > 0:
                orders.append(Order(
                    venue=self.staking_protocol,
                    operation=OrderOperation.UNSTAKE,
                    token_in=self.lst_type,
                    token_out='ETH',
                    amount=lst_reduction,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=1,
                    strategy_intent='exit_partial',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 2. Sell proportional ETH (atomic group)
            if lst_reduction > 0:
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='SELL',
                    amount=lst_reduction,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=2,
                    strategy_intent='exit_partial',
                    strategy_id='usdt_market_neutral'
                ))
            
            # 3. Withdraw proportional lent USDT (atomic group)
            if ausdt_reduction > 0:
                orders.append(Order(
                    venue=self.lending_protocol,
                    operation=OrderOperation.WITHDRAW,
                    token_in='aUSDT',
                    token_out='USDT',
                    amount=ausdt_reduction,
                    execution_mode='atomic',
                    atomic_group_id=atomic_group_id,
                    sequence_in_group=3,
                    strategy_intent='exit_partial',
                    strategy_id='usdt_market_neutral'
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
                strategy_id='usdt_market_neutral'
            ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating exit partial orders: {e}")
            return []
    
    def _create_dust_sell_orders(self, dust_tokens: Dict[str, float]) -> List[Order]:
        """
        Create dust sell orders for USDT market neutral strategy.
        
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
                    if token == 'USDT':
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
                            strategy_id='usdt_market_neutral'
                        ))
                    
                    elif token == 'ETH':
                        # Sell ETH for share class
                        orders.append(Order(
                            venue='binance',
                            operation=OrderOperation.SPOT_TRADE,
                            pair='ETH/USDT',
                            side='SELL',
                            amount=amount,
                            execution_mode='sequential',
                            strategy_intent='sell_dust',
                            strategy_id='usdt_market_neutral'
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
                            strategy_id='usdt_market_neutral'
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
                            strategy_id='usdt_market_neutral'
                        ))
                    
                    elif token == 'aUSDT':
                        # Withdraw from lending protocol first, then convert (atomic group)
                        atomic_group_id = f"dust_withdraw_{token}_{int(amount)}"
                        orders.append(Order(
                            venue=self.lending_protocol,
                            operation=OrderOperation.WITHDRAW,
                            token_in=token,
                            token_out='USDT',
                            amount=amount,
                            execution_mode='atomic',
                            atomic_group_id=atomic_group_id,
                            sequence_in_group=1,
                            strategy_intent='sell_dust',
                            strategy_id='usdt_market_neutral'
                        ))
                        orders.append(Order(
                            venue='wallet',
                            operation=OrderOperation.TRANSFER,
                            source_venue='wallet',
                            target_venue='wallet',
                            token='USDT',
                            amount=amount,
                            execution_mode='atomic',
                            atomic_group_id=atomic_group_id,
                            sequence_in_group=2,
                            strategy_intent='sell_dust',
                            strategy_id='usdt_market_neutral'
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
                            strategy_id='usdt_market_neutral'
                        ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error creating dust sell orders: {e}")
            return []
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get USDT market neutral strategy information and status.
        
        Returns:
            Dictionary with strategy information
        """
        try:
            base_info = super().get_strategy_info()
            
            # Add USDT market neutral-specific information
            base_info.update({
                'strategy_type': 'usdt_market_neutral',
                'usdt_allocation': self.usdt_allocation,
                'eth_allocation': self.eth_allocation,
                'leverage_multiplier': self.leverage_multiplier,
                'lst_type': self.lst_type,
                'lending_protocol': self.lending_protocol,
                'staking_protocol': self.staking_protocol,
                'description': 'USDT market neutral strategy with leverage, lending and staking using Order/Trade system',
                'order_system': 'unified_order_trade'
            })
            
            return base_info
            
        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                'strategy_type': 'usdt_market_neutral',
                'mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'error': str(e)
            }
