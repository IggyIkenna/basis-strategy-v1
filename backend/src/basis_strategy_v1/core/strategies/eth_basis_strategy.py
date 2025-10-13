"""
ETH Basis Strategy Implementation

Implements ETH basis trading strategy with funding rate arbitrage.
Inherits from BaseStrategyManager and implements the 5 standard actions.

Reference: docs/MODES.md - ETH Basis Strategy Mode
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any
import logging
import pandas as pd

from .base_strategy_manager import BaseStrategyManager
from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType
from ...core.models.order import Order, OrderOperation

logger = logging.getLogger(__name__)


class ETHBasisStrategy(BaseStrategyManager):
    """
    ETH Basis Strategy - Funding rate arbitrage with ETH perpetuals.
    
    Strategy Overview:
    - Long ETH spot position
    - Short ETH perpetual position
    - Capture funding rate differential
    - Target APY: 15-25%
    """
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, event_engine):
        """
        Initialize ETH basis strategy.
        
        Args:
            config: Strategy configuration
            risk_monitor: Risk monitor instance
            position_monitor: Position monitor instance
            event_engine: Event engine instance
        """
        super().__init__(config, risk_monitor, position_monitor, event_engine)
        
        # Validate required configuration at startup (fail-fast)
        required_keys = ['eth_allocation', 'funding_threshold', 'max_leverage']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        # ETH-specific configuration (fail-fast access)
        self.eth_allocation = config['eth_allocation']  # 80% to ETH
        self.funding_threshold = config['funding_threshold']  # 1% funding rate threshold
        self.max_leverage = config['max_leverage']  # No leverage for basis trading
        
        logger.info(f"ETHBasisStrategy initialized with {self.eth_allocation*100}% ETH allocation")
    
    def _get_asset_price(self) -> float:
        """Get current ETH price. In real implementation, this would fetch from data provider."""
        # For testing purposes, return a default ETH price
        # In production, this would fetch from market data
        return 3000.0
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position for ETH basis strategy.
        
        Args:
            current_equity: Current equity in share class currency
            
        Returns:
            Dictionary of target positions by token/venue
        """
        try:
            # Calculate target allocations
            eth_target = current_equity * self.eth_allocation
            
            # Get current ETH price
            eth_price = self._get_asset_price()
            eth_amount = eth_target / eth_price if eth_price > 0 else 0
            
            return {
                'eth_balance': eth_amount,
                'eth_perpetual_short': -eth_amount,  # Short position
                'total_equity': current_equity
            }
            
        except Exception as e:
            logger.error(f"Error calculating target position: {e}")
            return {
                'eth_balance': 0.0,
                'eth_perpetual_short': 0.0,
                'total_equity': current_equity
            }
    
    def make_strategy_decision(
        self,
        timestamp: pd.Timestamp,
        trigger_source: str,
        market_data: Dict,
        exposure_data: Dict,
        risk_assessment: Dict
    ) -> List[Order]:
        """
        Make ETH basis strategy decision based on market conditions and risk assessment.
        
        ETH Basis Strategy Logic:
        - Analyze funding rates and basis spreads
        - Check risk metrics for liquidation risk
        - Decide on entry/exit based on profitability and risk
        - Generate appropriate orders for ETH spot + perp positions
        """
        try:
            # Log strategy decision start
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message=f"Making ETH basis strategy decision triggered by {trigger_source}",
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
            
            # ETH-specific market analysis
            eth_spot_price = market_data.get('prices', {}).get('ETH', 0.0)
            eth_funding_rate = market_data.get('rates', {}).get('eth_funding', 0.0)
            
            # Risk assessment
            liquidation_risk = risk_assessment.get('liquidation_risk', 0.0)
            margin_ratio = risk_assessment.get('cex_margin_ratio', 1.0)
            
            # ETH Basis Strategy Decision Logic
            # Check if we have existing ETH positions
            has_eth_position = (current_positions.get('eth_balance', 0) > 0 or 
                              current_positions.get('eth_perpetual_short', 0) != 0)
            
            if current_equity == 0 or not has_eth_position:
                # No position or no ETH position - check if we should enter
                if self._should_enter_basis_position(eth_funding_rate, eth_spot_price):
                    return self._create_entry_orders(current_equity)
                else:
                    return self._create_dust_sell_orders(exposure_data)  # Wait for better opportunity
                    
            elif liquidation_risk > 0.8 or margin_ratio < 0.2:
                # High risk - exit position
                return self._create_exit_orders(current_equity)
                
            elif liquidation_risk > 0.6 or margin_ratio < 0.3:
                # Medium risk - partial exit
                return self._create_exit_orders(current_equity * 0.5)
                
            elif self._should_rebalance_position(eth_funding_rate, current_positions):
                # Rebalance position based on funding rate changes
                return self._create_rebalance_orders(current_equity * 0.2)
                
            else:
                # Maintain current position
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
            logger.error(f"Error in ETH basis strategy decision: {e}")
            # Return safe default action
            return self._create_dust_sell_orders(exposure_data)
    
    def _should_enter_basis_position(self, funding_rate: float, spot_price: float) -> bool:
        """Determine if we should enter an ETH basis position."""
        # ETH basis strategy logic: enter when funding rate is favorable
        return abs(funding_rate) > self.funding_threshold and spot_price > 0
    
    def _should_rebalance_position(self, funding_rate: float, current_positions: Dict) -> bool:
        """Determine if we should rebalance the ETH basis position."""
        # Simple rebalancing logic based on funding rate changes
        # In production, this would be more sophisticated
        return abs(funding_rate) > self.funding_threshold * 1.5
    
    def _create_entry_orders(self, equity: float) -> List[Order]:
        """
        Create orders for full ETH basis position entry.
        
        Args:
            equity: Available equity in share class currency
            
        Returns:
            List[Order] for ETH spot buy + ETH perp short (sequential)
        """
        try:
            # Log order creation
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message=f"Creating entry orders with equity={equity}",
                data={
                    'action': 'create_entry_orders',
                    'equity': equity,
                    'strategy_type': self.__class__.__name__
                },
                level=LogLevel.INFO
            )
            
            # Calculate target position
            target_position = self.calculate_target_position(equity)
            orders = []
            
            # 1. Buy ETH spot
            eth_amount = target_position.get('eth_balance', 0.0)
            if eth_amount > 0:
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='BUY',
                    amount=eth_amount,
                    order_type='market',
                    execution_mode='sequential',
                    strategy_intent='eth_basis_entry',
                    strategy_id='eth_basis',
                    metadata={
                        'eth_allocation': self.eth_allocation,
                        'funding_threshold': self.funding_threshold
                    }
                ))
            
            # 2. Open short perpetual position
            short_amount = abs(target_position.get('eth_perpetual_short', 0.0))
            if short_amount > 0:
                orders.append(Order(
                    venue='bybit',
                    operation=OrderOperation.PERP_TRADE,
                    pair='ETHUSDT',
                    side='SHORT',
                    amount=short_amount,
                    order_type='market',
                    execution_mode='sequential',
                    strategy_intent='eth_basis_entry',
                    strategy_id='eth_basis',
                metadata={
                    'eth_allocation': self.eth_allocation,
                    'funding_threshold': self.funding_threshold
                }
                ))
            
            return orders
            
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'method': '_create_entry_orders',
                    'equity': equity
                }
            )
            logger.error(f"Error creating entry orders: {e}")
            return []
    
    def _create_rebalance_orders(self, equity_delta: float) -> List[Order]:
        """
        Create orders for rebalancing ETH basis position.
        
        Args:
            equity_delta: Additional equity to deploy
            
        Returns:
            List[Order] for proportional ETH spot buy + perp short increase
        """
        try:
            # Log order creation
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message=f"Creating rebalance orders with equity_delta={equity_delta}",
                data={
                    'action': 'create_rebalance_orders',
                    'equity_delta': equity_delta,
                    'strategy_type': self.__class__.__name__
                },
                level=LogLevel.INFO
            )
            
            # Calculate proportional allocation
            eth_delta = equity_delta * self.eth_allocation
            eth_price = self._get_asset_price()
            eth_amount = eth_delta / eth_price if eth_price > 0 else 0
            
            orders = []
            
            # 1. Buy additional ETH spot
            if eth_amount > 0:
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='BUY',
                    amount=eth_amount,
                    order_type='market',
                    execution_mode='sequential',
                    strategy_intent='eth_basis_rebalance',
                    strategy_id='eth_basis',
                    metadata={
                        'eth_delta': eth_delta,
                        'rebalance': True
                    }
                ))
            
            # 2. Increase short perpetual position
            if eth_amount > 0:
                orders.append(Order(
                    venue='bybit',
                    operation=OrderOperation.PERP_TRADE,
                    pair='ETHUSDT',
                    side='SHORT',
                    amount=eth_amount,
                    order_type='market',
                    execution_mode='sequential',
                    strategy_intent='eth_basis_rebalance',
                    strategy_id='eth_basis',
                    metadata={
                        'eth_delta': eth_delta,
                        'rebalance': True
                    }
                ))
            
            return orders
            
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'method': '_create_rebalance_orders',
                    'equity_delta': equity_delta
                }
            )
            logger.error(f"Error creating rebalance orders: {e}")
            return []
    
    def _create_exit_orders(self, equity: float) -> List[Order]:
        """
        Create orders for exiting ETH basis position.
        
        Args:
            equity: Total equity to exit (used to calculate scaling factor)
            
        Returns:
            List[Order] for closing ETH perp short + selling ETH spot
        """
        try:
            # Log order creation
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message=f"Creating exit orders with equity={equity}",
                data={
                    'action': 'create_exit_orders',
                    'equity': equity,
                    'strategy_type': self.__class__.__name__
                },
                level=LogLevel.INFO
            )
            
            # Get current position
            current_position = self.position_monitor.get_current_position()
            eth_balance = current_position.get('eth_balance', 0.0)
            eth_short = current_position.get('eth_perpetual_short', 0.0)
            
            # Calculate scaling factor based on equity vs total position value
            total_position_value = (eth_balance + abs(eth_short)) * self._get_asset_price()
            if total_position_value > 0:
                scaling_factor = min(equity / total_position_value, 1.0)
            else:
                scaling_factor = 1.0
            
            orders = []
            
            # 1. Close short perpetual position
            if eth_short < 0:
                scaled_short_amount = abs(eth_short) * scaling_factor
                orders.append(Order(
                    venue='bybit',
                    operation=OrderOperation.PERP_TRADE,
                    pair='ETHUSDT',
                    side='BUY',  # Close short position
                    amount=scaled_short_amount,
                    order_type='market',
                    execution_mode='sequential',
                    strategy_intent='eth_basis_exit',
                    strategy_id='eth_basis',
                    metadata={
                        'eth_balance': eth_balance,
                        'eth_short': eth_short,
                        'scaling_factor': scaling_factor,
                        'close_position': True
                    }
                ))
            
            # 2. Sell ETH spot
            if eth_balance > 0:
                scaled_eth_amount = eth_balance * scaling_factor
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='ETH/USDT',
                    side='SELL',
                    amount=scaled_eth_amount,
                    order_type='market',
                    execution_mode='sequential',
                    strategy_intent='eth_basis_exit',
                    strategy_id='eth_basis',
                    metadata={
                        'eth_balance': eth_balance,
                        'eth_short': eth_short,
                        'scaling_factor': scaling_factor,
                        'close_position': True
                    }
                ))
            
            return orders
            
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'method': '_create_exit_orders',
                    'equity': equity
                }
            )
            logger.error(f"Error creating exit orders: {e}")
            return []
    
    def _create_dust_sell_orders(self, exposure_data: Dict) -> List[Order]:
        """
        Create orders for selling dust tokens.
        
        Args:
            exposure_data: Current exposure data
            
        Returns:
            List[Order] for selling dust tokens
        """
        try:
            # Log order creation
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message="Creating dust sell orders",
                data={
                    'action': 'create_dust_sell_orders',
                    'strategy_type': self.__class__.__name__
                },
                level=LogLevel.INFO
            )
            
            # Get current positions
            current_positions = exposure_data.get('positions', {})
            orders = []
            
            # Check for dust tokens that need to be sold
            for token, amount in current_positions.items():
                if amount > 0 and token not in [self.share_class.lower(), 'eth_perpetual_short']:
                    # This is a dust token that should be sold
                    if token == 'eth_balance':
                        # Sell ETH for share class
                        orders.append(Order(
                            venue='binance',
                            operation=OrderOperation.SPOT_TRADE,
                            pair='ETH/USDT',
                            side='SELL',
                            amount=amount,
                            order_type='market',
                            execution_mode='sequential',
                            strategy_intent='eth_basis_dust_sell',
                            strategy_id='eth_basis',
                            metadata={
                                'dust_token': token,
                                'dust_amount': amount
                            }
                        ))
                    elif token in ['btc_balance']:
                        # BTC dust - sell for share class
                        orders.append(Order(
                            venue='binance',
                            operation=OrderOperation.SPOT_TRADE,
                            pair='BTC/USDT',
                            side='SELL',
                            amount=amount,
                            order_type='market',
                            execution_mode='sequential',
                            strategy_intent='eth_basis_dust_sell',
                            strategy_id='eth_basis',
                            metadata={
                                'dust_token': token,
                                'dust_amount': amount
                            }
                        ))
                    elif token == 'usdt_balance':
                        # USDT is already the share class, no action needed
                        continue
                    else:
                        # Other dust tokens - sell for share class
                        orders.append(Order(
                            venue='binance',
                            operation=OrderOperation.SPOT_TRADE,
                            pair=f'{token.upper()}/USDT',
                            side='SELL',
                            amount=amount,
                            order_type='market',
                            execution_mode='sequential',
                            strategy_intent='eth_basis_dust_sell',
                            strategy_id='eth_basis',
                            metadata={
                                'dust_token': token,
                                'dust_amount': amount
                            }
                        ))
            
            return orders
            
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'method': '_create_dust_sell_orders',
                    'exposure_data': exposure_data
                }
            )
            logger.error(f"Error creating dust sell orders: {e}")
            return []
    
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get ETH basis strategy information and status.
        
        Returns:
            Dictionary with strategy information
        """
        try:
            # Add ETH-specific information
            return {
                'strategy_type': 'eth_basis',
                'share_class': self.share_class,
                'asset': self.asset,
                'eth_allocation': self.eth_allocation,
                'funding_threshold': self.funding_threshold,
                'max_leverage': self.max_leverage,
                'description': 'ETH funding rate arbitrage with spot/perpetual basis trading'
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                'strategy_type': 'eth_basis',
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'error': str(e)
            }
