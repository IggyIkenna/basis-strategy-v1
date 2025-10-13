"""
BTC Basis Strategy Implementation

Implements BTC basis trading strategy with funding rate arbitrage.
Inherits from BaseStrategyManager and implements the 5 standard actions.

Reference: docs/MODES.md - BTC Basis Strategy Mode
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any
import logging

from .base_strategy_manager import BaseStrategyManager, StrategyAction

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

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
    
    def entry_full(self, equity: float) -> StrategyAction:
        """
        Enter full BTC basis position.
        
        Args:
            equity: Available equity in share class currency
            
        Returns:
            StrategyAction with instructions for full entry
        """
        try:
            # Calculate target position
            target_position = self.calculate_target_position(equity)
            
            # Create instructions for full entry
            instructions = []
            
            # 1. Buy BTC spot
            btc_amount = target_position['btc_balance']
            if btc_amount > 0:
                instructions.append({
                    'action': 'buy',
                    'asset': 'BTC',
                    'amount': btc_amount,
                    'venue': 'binance',  # Primary venue for BTC
                    'order_type': 'market'
                })
            
            # 2. Open short perpetual position
            short_amount = target_position['btc_perpetual_short']
            if short_amount < 0:
                instructions.append({
                    'action': 'sell',
                    'asset': 'BTC-PERP',
                    'amount': abs(short_amount),
                    'venue': 'bybit',  # Primary venue for perpetuals
                    'order_type': 'market',
                    'position_type': 'short'
                })
            
            # 3. Maintain reserves
            reserve_amount = target_position[f'{self.share_class.lower()}_balance']
            if reserve_amount > 0:
                instructions.append({
                    'action': 'reserve',
                    'asset': self.share_class,
                    'amount': reserve_amount,
                    'venue': 'wallet',
                    'order_type': 'hold'
                })
            
            return StrategyAction(
                action_type='entry_full',
                target_amount=equity,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,  # All or nothing for basis strategy
                metadata={
                    'strategy': 'btc_basis',
                    'btc_allocation': self.btc_allocation,
                    'funding_threshold': self.funding_threshold
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
        """
        Scale up BTC basis position.
        
        Args:
            equity_delta: Additional equity to deploy
            
        Returns:
            StrategyAction with instructions for partial entry
        """
        try:
            # Calculate proportional allocation
            btc_delta = equity_delta * self.btc_allocation
            
            # Get current BTC price
            btc_price = self._get_asset_price()
            btc_amount = btc_delta / btc_price if btc_price > 0 else 0
            
            instructions = []
            
            # 1. Buy additional BTC spot
            if btc_amount > 0:
                instructions.append({
                    'action': 'buy',
                    'asset': 'BTC',
                    'amount': btc_amount,
                    'venue': 'binance',
                    'order_type': 'market'
                })
            
            # 2. Increase short perpetual position
            if btc_amount > 0:
                instructions.append({
                    'action': 'sell',
                    'asset': 'BTC-PERP',
                    'amount': btc_amount,
                    'venue': 'bybit',
                    'order_type': 'market',
                    'position_type': 'short'
                })
            
            # 3. Add to reserves
            if reserve_delta > 0:
                instructions.append({
                    'action': 'reserve',
                    'asset': self.share_class,
                    'amount': reserve_delta,
                    'venue': 'wallet',
                    'order_type': 'hold'
                })
            
            return StrategyAction(
                action_type='entry_partial',
                target_amount=equity_delta,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'btc_basis',
                    'btc_delta': btc_delta,
                    'reserve_delta': reserve_delta
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
        """
        Exit entire BTC basis position.
        
        Args:
            equity: Total equity to exit
            
        Returns:
            StrategyAction with instructions for full exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            btc_balance = current_position.get('btc_balance', 0.0)
            btc_short = current_position.get('btc_perpetual_short', 0.0)
            
            instructions = []
            
            # 1. Close short perpetual position
            if btc_short < 0:
                instructions.append({
                    'action': 'buy',
                    'asset': 'BTC-PERP',
                    'amount': abs(btc_short),
                    'venue': 'bybit',
                    'order_type': 'market',
                    'position_type': 'close_short'
                })
            
            # 2. Sell BTC spot
            if btc_balance > 0:
                instructions.append({
                    'action': 'sell',
                    'asset': 'BTC',
                    'amount': btc_balance,
                    'venue': 'binance',
                    'order_type': 'market'
                })
            
            # 3. Convert all to share class currency
            instructions.append({
                'action': 'convert',
                'asset': self.share_class,
                'amount': equity,
                'venue': 'wallet',
                'order_type': 'market'
            })
            
            return StrategyAction(
                action_type='exit_full',
                target_amount=equity,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'btc_basis',
                    'btc_balance': btc_balance,
                    'btc_short': btc_short
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
        """
        Scale down BTC basis position.
        
        Args:
            equity_delta: Equity to remove from position
            
        Returns:
            StrategyAction with instructions for partial exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            btc_balance = current_position.get('btc_balance', 0.0)
            btc_short = current_position.get('btc_perpetual_short', 0.0)
            
            # Calculate proportional reduction
            total_btc = btc_balance + abs(btc_short)
            if total_btc > 0:
                reduction_ratio = min(equity_delta / (total_btc * self._get_asset_price()), 1.0)
            else:
                reduction_ratio = 0.0
            
            btc_reduction = btc_balance * reduction_ratio
            short_reduction = abs(btc_short) * reduction_ratio
            
            instructions = []
            
            # 1. Reduce short perpetual position
            if short_reduction > 0:
                instructions.append({
                    'action': 'buy',
                    'asset': 'BTC-PERP',
                    'amount': short_reduction,
                    'venue': 'bybit',
                    'order_type': 'market',
                    'position_type': 'reduce_short'
                })
            
            # 2. Sell proportional BTC spot
            if btc_reduction > 0:
                instructions.append({
                    'action': 'sell',
                    'asset': 'BTC',
                    'amount': btc_reduction,
                    'venue': 'binance',
                    'order_type': 'market'
                })
            
            # 3. Convert to share class currency
            instructions.append({
                'action': 'convert',
                'asset': self.share_class,
                'amount': equity_delta,
                'venue': 'wallet',
                'order_type': 'market'
            })
            
            return StrategyAction(
                action_type='exit_partial',
                target_amount=equity_delta,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'btc_basis',
                    'btc_reduction': btc_reduction,
                    'short_reduction': short_reduction,
                    'reduction_ratio': reduction_ratio
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
        """
        Convert non-share-class tokens to share class currency.
        
        Args:
            dust_tokens: Dictionary of dust tokens and amounts
            
        Returns:
            StrategyAction with instructions for dust selling
        """
        try:
            instructions = []
            total_converted = 0.0
            
            for token, amount in dust_tokens.items():
                if amount > 0 and token != self.share_class:
                    # Convert to share class currency
                    if token == 'BTC':
                        # Sell BTC for share class
                        instructions.append({
                            'action': 'sell',
                            'asset': token,
                            'amount': amount,
                            'venue': 'binance',
                            'order_type': 'market',
                            'target_currency': self.share_class
                        })
                        total_converted += amount * self._get_asset_price()
                    
                    elif token in ['ETH', 'USDT']:
                        # Direct conversion
                        instructions.append({
                            'action': 'convert',
                            'asset': token,
                            'amount': amount,
                            'venue': 'wallet',
                            'order_type': 'market',
                            'target_currency': self.share_class
                        })
                        total_converted += amount
                    
                    else:
                        # Other tokens - sell for share class
                        instructions.append({
                            'action': 'sell',
                            'asset': token,
                            'amount': amount,
                            'venue': 'binance',
                            'order_type': 'market',
                            'target_currency': self.share_class
                        })
                        # Estimate value (would use actual price in real implementation)
                        total_converted += amount * 0.1  # Placeholder
            
            return StrategyAction(
                action_type='sell_dust',
                target_amount=total_converted,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=False,  # Can execute individually
                metadata={
                    'strategy': 'btc_basis',
                    'dust_tokens': dust_tokens,
                    'total_converted': total_converted
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
        Get BTC basis strategy information and status.
        
        Returns:
            Dictionary with strategy information
        """
        try:
            base_info = super().get_strategy_info()
            
            # Add BTC-specific information
            base_info.update({
                'strategy_type': 'btc_basis',
                'btc_allocation': self.btc_allocation,
                'funding_threshold': self.funding_threshold,
                'max_leverage': self.max_leverage,
                'description': 'BTC funding rate arbitrage with spot/perpetual basis trading'
            })
            
            return base_info
            
        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                'strategy_type': 'btc_basis',
                'mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'error': str(e)
            }
