"""
Pure Lending Strategy Implementation

This module implements the pure lending strategy using the base strategy manager
architecture with standardized 5-action interface.

Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
Reference: docs/MODES.md - Pure Lending Strategy
"""

from typing import Dict, List, Any
import logging
import pandas as pd

from .base_strategy_manager import BaseStrategyManager
from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType
from ...core.models.order import Order, OrderOperation

logger = logging.getLogger(__name__)

class PureLendingStrategy(BaseStrategyManager):
    """Pure lending strategy implementation"""
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, event_engine):
        """
        Initialize pure lending strategy.
        
        Args:
            config: Strategy configuration
            risk_monitor: Risk monitor instance
            position_monitor: Position monitor instance
            event_engine: Event engine instance
        """
        super().__init__(config, risk_monitor, position_monitor, event_engine)
        
        # Pure lending specific configuration
        self.lending_venues = config.get('lending_venues', ['aave', 'morpho'])
        
        # Pure lending doesn't use LTV (no borrowing/leverage)
        # LTV values are not applicable for pure lending strategies
        
        logger.info(f"PureLendingStrategy initialized for {self.share_class} {self.asset}")
    
    def make_strategy_decision(
        self,
        timestamp: pd.Timestamp,
        trigger_source: str,
        market_data: Dict,
        exposure_data: Dict,
        risk_assessment: Dict
    ) -> List[Order]:
        """
        Make pure lending strategy decision and return list of orders.
        
        Pure Lending Strategy Logic:
        - Simple lending strategy - just supply USDT to AAVE
        - No complex trading decisions
        - Focus on maintaining lending position and managing risk
        """
        try:
            # Log strategy decision start
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message=f"Making pure lending strategy decision triggered by {trigger_source}",
                data={
                    'trigger_source': trigger_source,
                    'strategy_type': self.__class__.__name__,
                    'timestamp': str(timestamp)
                },
                level=LogLevel.INFO
            )
            
            # Get current equity and positions
            current_equity = self.get_current_equity(exposure_data)
            current_positions = exposure_data.get('positions', {})
            
            # Pure lending strategy - much simpler logic
            # Just check if we have USDT to lend and if AAVE rates are favorable
            
            # Simple decision logic for pure lending
            if current_equity == 0:
                # No position - wait for deposits
                return self._create_dust_sell_orders(exposure_data)
                
            elif current_equity > 0 and not current_positions.get('aave_usdt_supply', 0):
                # Have equity but not lending - start lending
                return self._create_entry_full_orders(current_equity)
                
            else:
                # Already lending - maintain position
                return self._create_dust_sell_orders(exposure_data)
                
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'method': 'make_strategy_decision',
                    'trigger_source': trigger_source,
                    'strategy_type': self.__class__.__name__
                }
            )
            logger.error(f"Error in pure lending strategy decision: {e}")
            # Return safe default action
            return self._create_dust_sell_orders(exposure_data)
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """Calculate target position based on current equity"""
        try:
            # For pure lending, no borrowing - just supply the full equity
            target_supply = current_equity
            target_borrow = 0.0  # No borrowing in pure lending
            
            return {
                'supply': target_supply,
                'borrow': target_borrow,
                'equity': current_equity
            }
        except Exception as e:
            logger.error(f"Failed to calculate target position: {e}")
            return {'supply': 0.0, 'borrow': 0.0, 'equity': current_equity}
    
    def _create_entry_full_orders(self, equity: float) -> List[Order]:
        """Create orders for full position entry (initial setup or large deposits)"""
        try:
            # Log action start
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message=f"Creating entry_full orders with equity={equity}",
                data={
                    'action': 'entry_full',
                    'equity': equity,
                    'strategy_type': self.__class__.__name__
                },
                level=LogLevel.INFO
            )
            
            target_position = self.calculate_target_position(equity)
            orders = []
            
            # Create supply orders for each lending venue
            for venue in self.lending_venues:
                supply_amount = target_position['supply'] / len(self.lending_venues)
                if supply_amount > 0:
                    orders.append(Order(
                        venue=venue,
                        operation=OrderOperation.SUPPLY,
                        token_in=self.asset,
                        token_out=f'a{self.asset}',
                        amount=supply_amount,
                        execution_mode='sequential',
                        strategy_intent='entry_full'
                    ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to create entry_full orders: {e}")
            return []
    
    def _create_entry_partial_orders(self, equity_delta: float) -> List[Order]:
        """Create orders for partial position entry (small deposits or PnL gains)"""
        try:
            # Scale up proportionally
            target_position = self.calculate_target_position(equity_delta)
            orders = []
            
            for venue in self.lending_venues:
                supply_amount = target_position['supply'] / len(self.lending_venues)
                if supply_amount > 0:
                    orders.append(Order(
                        venue=venue,
                        operation=OrderOperation.SUPPLY,
                        token_in=self.asset,
                        token_out=f'a{self.asset}',
                        amount=supply_amount,
                        execution_mode='sequential',
                        strategy_intent='entry_partial'
                    ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to create entry_partial orders: {e}")
            return []
    
    def _create_exit_full_orders(self, equity: float) -> List[Order]:
        """Create orders for full position exit (withdrawals or risk override)"""
        try:
            # Get current position to determine exit amounts
            position_snapshot = self.position_monitor.get_position_snapshot()
            current_supply = position_snapshot.get('total_supply', 0.0)
            current_borrow = position_snapshot.get('total_borrow', 0.0)
            
            orders = []
            for venue in self.lending_venues:
                # Withdraw supply
                withdraw_amount = current_supply / len(self.lending_venues)
                if withdraw_amount > 0:
                    orders.append(Order(
                        venue=venue,
                        operation=OrderOperation.WITHDRAW,
                        token_in=f'a{self.asset}',
                        token_out=self.asset,
                        amount=withdraw_amount,
                        execution_mode='sequential',
                        strategy_intent='exit_full'
                    ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to create exit_full orders: {e}")
            return []
    
    def _create_exit_partial_orders(self, equity_delta: float) -> List[Order]:
        """Create orders for partial position exit (small withdrawals or risk reduction)"""
        try:
            # Scale down proportionally
            target_position = self.calculate_target_position(equity_delta)
            orders = []
            
            for venue in self.lending_venues:
                withdraw_amount = target_position['supply'] / len(self.lending_venues)
                if withdraw_amount > 0:
                    orders.append(Order(
                        venue=venue,
                        operation=OrderOperation.WITHDRAW,
                        token_in=f'a{self.asset}',
                        token_out=self.asset,
                        amount=withdraw_amount,
                        execution_mode='sequential',
                        strategy_intent='exit_partial'
                    ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to create exit_partial orders: {e}")
            return []
    
    def _create_dust_sell_orders(self, exposure_data: Dict) -> List[Order]:
        """Create orders to convert non-share-class tokens to share class currency"""
        try:
            dust_tokens = self.get_dust_tokens(exposure_data)
            orders = []
            
            for token, amount in dust_tokens.items():
                if token != self.asset and amount > 0:
                    # For dust selling, we'd typically use a DEX or CEX
                    # This is a simplified example - in practice you'd route to appropriate venue
                    orders.append(Order(
                        venue='uniswap',  # Example DEX venue
                        operation=OrderOperation.SWAP,
                        token_in=token,
                        token_out=self.asset,
                        amount=amount,
                        execution_mode='sequential',
                        strategy_intent='sell_dust'
                    ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to create dust sell orders: {e}")
            return []