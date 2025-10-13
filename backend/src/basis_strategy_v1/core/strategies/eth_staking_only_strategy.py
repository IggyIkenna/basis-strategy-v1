"""
ETH Staking Only Strategy Implementation

Implements ETH staking strategy with liquid staking tokens (LSTs).
Inherits from BaseStrategyManager and implements the 5 standard actions.

Reference: docs/MODES.md - ETH Staking Only Strategy Mode
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any
import logging

from .base_strategy_manager import BaseStrategyManager, StrategyAction

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)


class ETHStakingOnlyStrategy(BaseStrategyManager):
    """
    ETH Staking Only Strategy - Liquid staking with LSTs.
    
    Strategy Overview:
    - Stake ETH via liquid staking protocols
    - Hold LST tokens (wstETH, weETH, etc.)
    - Earn staking rewards
    - Target APY: 8-15%
    """
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, event_engine):
        """
        Initialize ETH staking only strategy.
        
        Args:
            config: Strategy configuration
            risk_monitor: Risk monitor instance
            position_monitor: Position monitor instance
            event_engine: Event engine instance
        """
        super().__init__(config, risk_monitor, position_monitor, event_engine)
        
        # Validate required configuration at startup (fail-fast)
        required_keys = ['eth_allocation', 'lst_type', 'staking_protocol']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        # ETH staking-specific configuration (fail-fast access)
        self.eth_allocation = config['eth_allocation']  # 90% to ETH staking
        self.lst_type = config['lst_type']  # Default LST type
        self.staking_protocol = config['staking_protocol']  # Default protocol
        
        logger.info(f"ETHStakingOnlyStrategy initialized with {self.eth_allocation*100}% ETH allocation, {self.lst_type}")
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position for ETH staking strategy.
        
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
                'eth_balance': 0.0,  # No raw ETH, all staked
                f'{self.lst_type.lower()}_balance': eth_amount,  # All ETH converted to LST
                f'{self.share_class.lower()}_balance': current_equity,
                'total_equity': current_equity
            }
            
        except Exception as e:
            logger.error(f"Error calculating target position: {e}")
            return {
                'eth_balance': 0.0,
                f'{self.lst_type.lower()}_balance': 0.0,
                f'{self.share_class.lower()}_balance': 0.0,  # No reserve balance needed
                'total_equity': current_equity
            }
    
    def entry_full(self, equity: float) -> StrategyAction:
        """
        Enter full ETH staking position.
        
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
            
            # 1. Buy ETH
            eth_amount = target_position[f'{self.lst_type.lower()}_balance']
            if eth_amount > 0:
                instructions.append({
                    'action': 'buy',
                    'asset': 'ETH',
                    'amount': eth_amount,
                    'venue': 'binance',
                    'order_type': 'market'
                })
            
            # 2. Stake ETH to get LST
            if eth_amount > 0:
                instructions.append({
                    'action': 'stake',
                    'asset': 'ETH',
                    'amount': eth_amount,
                    'venue': self.staking_protocol,
                    'order_type': 'stake',
                    'target_token': self.lst_type
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
                atomic=True,  # All or nothing for staking
                metadata={
                    'strategy': 'eth_staking_only',
                    'eth_allocation': self.eth_allocation,
                    'lst_type': self.lst_type,
                    'staking_protocol': self.staking_protocol
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
        Scale up ETH staking position.
        
        Args:
            equity_delta: Additional equity to deploy
            
        Returns:
            StrategyAction with instructions for partial entry
        """
        try:
            # Calculate proportional allocation
            eth_delta = equity_delta * self.eth_allocation
            
            # Get current ETH price
            eth_price = self._get_asset_price()
            eth_amount = eth_delta / eth_price if eth_price > 0 else 0
            
            instructions = []
            
            # 1. Buy additional ETH
            if eth_amount > 0:
                instructions.append({
                    'action': 'buy',
                    'asset': 'ETH',
                    'amount': eth_amount,
                    'venue': 'binance',
                    'order_type': 'market'
                })
            
            # 2. Stake additional ETH
            if eth_amount > 0:
                instructions.append({
                    'action': 'stake',
                    'asset': 'ETH',
                    'amount': eth_amount,
                    'venue': self.staking_protocol,
                    'order_type': 'stake',
                    'target_token': self.lst_type
                })
            
            # No reserve allocation needed - all equity goes to active positions
            
            return StrategyAction(
                action_type='entry_partial',
                target_amount=equity_delta,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'eth_staking_only',
                    'eth_delta': eth_delta,
                    'lst_type': self.lst_type
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
        Exit entire ETH staking position.
        
        Args:
            equity: Total equity to exit
            
        Returns:
            StrategyAction with instructions for full exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            lst_balance = current_position.get(f'{self.lst_type.lower()}_balance', 0.0)
            
            instructions = []
            
            # 1. Unstake LST to get ETH
            if lst_balance > 0:
                instructions.append({
                    'action': 'unstake',
                    'asset': self.lst_type,
                    'amount': lst_balance,
                    'venue': self.staking_protocol,
                    'order_type': 'unstake',
                    'target_token': 'ETH'
                })
            
            # 2. Sell ETH
            if lst_balance > 0:
                instructions.append({
                    'action': 'sell',
                    'asset': 'ETH',
                    'amount': lst_balance,
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
                    'strategy': 'eth_staking_only',
                    'lst_balance': lst_balance,
                    'lst_type': self.lst_type
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
        Scale down ETH staking position.
        
        Args:
            equity_delta: Equity to remove from position
            
        Returns:
            StrategyAction with instructions for partial exit
        """
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            lst_balance = current_position.get(f'{self.lst_type.lower()}_balance', 0.0)
            
            # Calculate proportional reduction
            if lst_balance > 0:
                reduction_ratio = min(equity_delta / (lst_balance * self._get_lst_price(self.lst_type)), 1.0)
            else:
                reduction_ratio = 0.0
            
            lst_reduction = lst_balance * reduction_ratio
            
            instructions = []
            
            # 1. Unstake proportional LST
            if lst_reduction > 0:
                instructions.append({
                    'action': 'unstake',
                    'asset': self.lst_type,
                    'amount': lst_reduction,
                    'venue': self.staking_protocol,
                    'order_type': 'unstake',
                    'target_token': 'ETH'
                })
            
            # 2. Sell proportional ETH
            if lst_reduction > 0:
                instructions.append({
                    'action': 'sell',
                    'asset': 'ETH',
                    'amount': lst_reduction,
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
                    'strategy': 'eth_staking_only',
                    'lst_reduction': lst_reduction,
                    'reduction_ratio': reduction_ratio,
                    'lst_type': self.lst_type
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
                    if token == 'ETH':
                        # Sell ETH for share class
                        instructions.append({
                            'action': 'sell',
                            'asset': token,
                            'amount': amount,
                            'venue': 'binance',
                            'order_type': 'market',
                            'target_currency': self.share_class
                        })
                        total_converted += amount * self._get_asset_price()
                    
                    elif token == self.lst_type:
                        # Unstake LST first, then sell ETH
                        instructions.append({
                            'action': 'unstake',
                            'asset': token,
                            'amount': amount,
                            'venue': self.staking_protocol,
                            'order_type': 'unstake',
                            'target_token': 'ETH'
                        })
                        instructions.append({
                            'action': 'sell',
                            'asset': 'ETH',
                            'amount': amount,
                            'venue': 'binance',
                            'order_type': 'market',
                            'target_currency': self.share_class
                        })
                        total_converted += amount * self._get_lst_price(token)
                    
                    elif token in ['BTC', 'USDT']:
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
                    'strategy': 'eth_staking_only',
                    'dust_tokens': dust_tokens,
                    'total_converted': total_converted,
                    'lst_type': self.lst_type
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
        Get ETH staking only strategy information and status.
        
        Returns:
            Dictionary with strategy information
        """
        try:
            base_info = super().get_strategy_info()
            
            # Add ETH staking-specific information
            base_info.update({
                'strategy_type': 'eth_staking_only',
                'eth_allocation': self.eth_allocation,
                'lst_type': self.lst_type,
                'staking_protocol': self.staking_protocol,
                'description': 'ETH liquid staking with LST tokens for staking rewards'
            })
            
            return base_info
            
        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                'strategy_type': 'eth_staking_only',
                'mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'error': str(e)
            }
