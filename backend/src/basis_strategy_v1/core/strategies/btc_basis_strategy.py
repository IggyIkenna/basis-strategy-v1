"""
BTC Basis Strategy Implementation

Implements BTC basis trading strategy with funding rate arbitrage.
Inherits from BaseStrategyManager and implements the 5 standard actions.

Reference: docs/MODES.md - BTC Basis Strategy Mode
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any
import logging
import pandas as pd

from .base_strategy_manager import BaseStrategyManager
from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType
from ...core.models.order import Order, OrderOperation

logger = logging.getLogger(__name__)


class BTCBasisStrategy(BaseStrategyManager):
    """
    BTC Basis Strategy - Funding rate arbitrage with BTC perpetuals.
    
    Strategy Overview:
    - Long BTC spot position
    - Short BTC perpetual position
    - Capture funding rate differential
    - Target APY: 15-25%
    """
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, event_engine):
        """
        Initialize BTC basis strategy.
        
        Args:
            config: Strategy configuration
            risk_monitor: Risk monitor instance
            position_monitor: Position monitor instance
            event_engine: Event engine instance
        """
        super().__init__(config, risk_monitor, position_monitor, event_engine)
        
        # Validate required configuration at startup (fail-fast)
        required_keys = ['btc_allocation', 'funding_threshold', 'max_leverage']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        # BTC-specific configuration (fail-fast access)
        self.btc_allocation = config['btc_allocation']  # 80% to BTC
        self.funding_threshold = config['funding_threshold']  # 1% funding rate threshold
        self.max_leverage = config['max_leverage']  # No leverage for basis trading
        
        logger.info(f"BTCBasisStrategy initialized with {self.btc_allocation*100}% BTC allocation")
    
    def _get_asset_price(self) -> float:
        """Get current BTC price. In real implementation, this would fetch from data provider."""
        # For testing purposes, return a default BTC price
        # In production, this would fetch from market data
        return 50000.0
    
    def make_strategy_decision(
        self,
        timestamp: pd.Timestamp,
        trigger_source: str,
        market_data: Dict,
        exposure_data: Dict,
        risk_assessment: Dict
    ) -> List[Order]:
        """
        Make BTC basis strategy decision based on market conditions and risk assessment.
        
        BTC Basis Strategy Logic:
        - Analyze funding rates and basis spreads
        - Check risk metrics for liquidation risk
        - Decide on entry/exit based on profitability and risk
        - Generate appropriate instructions for BTC spot + perp positions
        """
        try:
            # Log strategy decision start
            self.log_component_event(
                event_type=EventType.BUSINESS_EVENT,
                message=f"Making BTC basis strategy decision triggered by {trigger_source}",
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
            
            # BTC-specific market analysis
            btc_spot_price = market_data.get('prices', {}).get('BTC', 0.0)
            btc_funding_rate = market_data.get('rates', {}).get('btc_funding', 0.0)
            
            # Risk assessment
            liquidation_risk = risk_assessment.get('liquidation_risk', 0.0)
            margin_ratio = risk_assessment.get('cex_margin_ratio', 1.0)
            
            # BTC Basis Strategy Decision Logic
            # Check if we have existing BTC positions
            has_btc_position = (current_positions.get('btc_balance', 0) > 0 or 
                              current_positions.get('btc_perpetual_short', 0) != 0)
            
            if current_equity == 0 or not has_btc_position:
                # No position or no BTC position - check if we should enter
                if self._should_enter_basis_position(btc_funding_rate, btc_spot_price):
                    return self._create_entry_orders(current_equity)
                else:
                    return self._create_dust_sell_orders(exposure_data)  # Wait for better opportunity
                    
            elif liquidation_risk > 0.8 or margin_ratio < 0.2:
                # High risk - exit position
                return self._create_exit_orders(current_equity)
                
            elif liquidation_risk > 0.6 or margin_ratio < 0.3:
                # Medium risk - partial exit
                return self._create_exit_orders(current_equity * 0.5)
                
            elif self._should_rebalance_position(btc_funding_rate, current_positions):
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
            logger.error(f"Error in BTC basis strategy decision: {e}")
            # Return safe default action
            return self._create_dust_sell_orders(exposure_data)
    
    def _should_enter_basis_position(self, funding_rate: float, spot_price: float) -> bool:
        """Determine if we should enter a BTC basis position."""
        # BTC basis strategy logic: enter when funding rate is favorable
        return abs(funding_rate) > self.funding_threshold and spot_price > 0
    
    def _should_rebalance_position(self, funding_rate: float, current_positions: Dict) -> bool:
        """Determine if we should rebalance the BTC basis position."""
        # Rebalance if funding rate has changed significantly
        return abs(funding_rate) > self.funding_threshold * 1.5
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position for BTC basis strategy.
        
        Args:
            current_equity: Current equity in share class currency
            
        Returns:
            Dictionary of target positions by token/venue
        """
        try:
            # Calculate target allocations
            btc_target = current_equity * self.btc_allocation
            
            # Get current BTC price
            btc_price = self._get_asset_price()
            btc_amount = btc_target / btc_price if btc_price > 0 else 0
            
            return {
                'btc_balance': btc_amount,
                'btc_perpetual_short': -btc_amount,  # Short position
                f'{self.share_class.lower()}_balance': current_equity,
                'total_equity': current_equity
            }
            
        except Exception as e:
            logger.error(f"Error calculating target position: {e}")
            return {
                'btc_balance': 0.0,
                'btc_perpetual_short': 0.0,
                f'{self.share_class.lower()}_balance': current_equity ,
                'total_equity': current_equity
            }
    
    def _create_entry_orders(self, equity: float) -> List[Order]:
        """
        Create orders for full BTC basis position entry.
        
        Args:
            equity: Available equity in share class currency
            
        Returns:
            List[Order] for BTC spot buy + BTC perp short (sequential)
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
            
            # 1. Buy BTC spot
            btc_amount = target_position.get('btc_balance', 0.0)
            if btc_amount > 0:
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='BTC/USDT',
                    side='BUY',
                    amount=btc_amount,
                    order_type='market',
                    execution_mode='sequential',
                    strategy_intent='btc_basis_entry',
                    strategy_id='btc_basis',
                    metadata={
                        'btc_allocation': self.btc_allocation,
                        'funding_threshold': self.funding_threshold
                    }
                ))
            
            # 2. Open short perpetual position
            short_amount = abs(target_position.get('btc_perpetual_short', 0.0))
            if short_amount > 0:
                orders.append(Order(
                    venue='bybit',
                    operation=OrderOperation.PERP_TRADE,
                    pair='BTCUSDT',
                    side='SHORT',
                    amount=short_amount,
                    order_type='market',
                    execution_mode='sequential',
                    strategy_intent='btc_basis_entry',
                    strategy_id='btc_basis',
                    metadata={
                        'btc_allocation': self.btc_allocation,
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
    
    def _create_exit_orders(self, equity: float) -> List[Order]:
        """
        Create orders for BTC basis position exit.
        
        Args:
            equity: Equity to exit (full or partial)
            
        Returns:
            List[Order] for closing perp short + BTC spot sell (sequential)
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
            btc_balance = current_position.get('btc_balance', 0.0)
            btc_short = current_position.get('btc_perpetual_short', 0.0)
            
            orders = []
            
            # 1. Close short perpetual position
            if btc_short < 0:
                orders.append(Order(
                    venue='bybit',
                    operation=OrderOperation.PERP_TRADE,
                    pair='BTCUSDT',
                    side='LONG',  # Close short position
                    amount=abs(btc_short),
                    order_type='market',
                    execution_mode='sequential',
                    strategy_intent='btc_basis_exit',
                    strategy_id='btc_basis',
                    metadata={
                        'position_type': 'close_short',
                        'original_short': btc_short
                    }
                ))
            
            # 2. Sell BTC spot
            if btc_balance > 0:
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='BTC/USDT',
                    side='SELL',
                    amount=btc_balance,
                    order_type='market',
                    execution_mode='sequential',
                    strategy_intent='btc_basis_exit',
                    strategy_id='btc_basis',
                    metadata={
                        'btc_balance': btc_balance
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
    
    def _create_rebalance_orders(self, equity_delta: float) -> List[Order]:
        """
        Create orders for BTC basis position rebalancing.
        
        Args:
            equity_delta: Additional equity to deploy for rebalancing
            
        Returns:
            List[Order] for proportional BTC spot buy + perp short increase
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
            btc_delta = equity_delta * self.btc_allocation
            btc_price = self._get_asset_price()
            btc_amount = btc_delta / btc_price if btc_price > 0 else 0
            
            orders = []
            
            # 1. Buy additional BTC spot
            if btc_amount > 0:
                orders.append(Order(
                    venue='binance',
                    operation=OrderOperation.SPOT_TRADE,
                    pair='BTC/USDT',
                    side='BUY',
                    amount=btc_amount,
                    order_type='market',
                    execution_mode='sequential',
                    strategy_intent='btc_basis_rebalance',
                    strategy_id='btc_basis',
                    metadata={
                        'btc_delta': btc_delta,
                        'rebalance_type': 'increase'
                    }
                ))
            
            # 2. Increase short perpetual position
            if btc_amount > 0:
                orders.append(Order(
                    venue='bybit',
                    operation=OrderOperation.PERP_TRADE,
                    pair='BTCUSDT',
                    side='SHORT',
                    amount=btc_amount,
                    order_type='market',
                    execution_mode='sequential',
                    strategy_intent='btc_basis_rebalance',
                    strategy_id='btc_basis',
                    metadata={
                        'btc_delta': btc_delta,
                        'rebalance_type': 'increase'
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
    
    def _create_dust_sell_orders(self, exposure_data: Dict) -> List[Order]:
        """
        Create orders for selling dust tokens.
        
        Args:
            exposure_data: Current exposure data containing dust tokens
            
        Returns:
            List[Order] for converting dust tokens to share class currency
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
            
            # Get dust tokens from exposure data
            positions = exposure_data.get('positions', {})
            dust_tokens = {k: v for k, v in positions.items() 
                          if v > 0 and k != f'{self.share_class.lower()}_balance'}
            
            orders = []
            
            for token, amount in dust_tokens.items():
                if amount > 0 and token != self.share_class:
                    if token == 'btc_balance':
                        # Sell BTC for share class
                        orders.append(Order(
                            venue='binance',
                            operation=OrderOperation.SPOT_TRADE,
                            pair='BTC/USDT',
                            side='SELL',
                            amount=amount,
                            order_type='market',
                            execution_mode='sequential',
                            strategy_intent='dust_sell',
                            strategy_id='btc_basis',
                            metadata={
                                'dust_token': token,
                                'target_currency': self.share_class
                            }
                        ))
                    elif token in ['eth_balance', 'usdt_balance']:
                        # Direct transfer to wallet (already in correct currency)
                        orders.append(Order(
                            venue='wallet',
                            operation=OrderOperation.TRANSFER,
                            token=token.replace('_balance', '').upper(),
                            amount=amount,
                            source_venue='cex',
                            target_venue='wallet',
                            execution_mode='sequential',
                            strategy_intent='dust_sell',
                            strategy_id='btc_basis',
                            metadata={
                                'dust_token': token
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
        Get BTC basis strategy information and status.
        
        Returns:
            Dictionary with strategy information
        """
        try:
            return {
                'strategy_type': 'btc_basis',
                'share_class': self.share_class,
                'asset': self.asset,
                'btc_allocation': self.btc_allocation,
                'funding_threshold': self.funding_threshold,
                'max_leverage': self.max_leverage,
                'description': 'BTC funding rate arbitrage with spot/perpetual basis trading'
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                'strategy_type': 'btc_basis',
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'error': str(e)
            }
