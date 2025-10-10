"""
Pure Lending Strategy Implementation

Implements the pure lending strategy using the base strategy manager architecture.
This strategy focuses on lending assets to earn yield without leverage or complex positions.

Reference: docs/MODES.md - Pure Lending Strategy
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any
import logging
from .base_strategy_manager import BaseStrategyManager, StrategyAction

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
        self.lending_venue = config.get('lending_venue', 'aave')
        self.target_apy = config.get('target_apy', 0.05)  # 5% default
        
        logger.info(f"PureLendingStrategy initialized for {self.lending_venue} venue")
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position for pure lending strategy.
        
        Args:
            current_equity: Current equity in share class currency
            
        Returns:
            Dictionary of target positions by token/venue
        """
        try:
            # Pure lending strategy: lend all available equity
            target_positions = {}
            
            if self.share_class == 'USDT':
                # Lend USDT to earn yield
                target_positions[f'{self.lending_venue}_usdt_supply'] = current_equity
            elif self.share_class == 'ETH':
                # Lend ETH to earn yield
                target_positions[f'{self.lending_venue}_eth_supply'] = current_equity
            
            return target_positions
            
        except Exception as e:
            logger.error(f"Error calculating target position: {e}")
            return {}
    
    def entry_full(self, equity: float) -> StrategyAction:
        """
        Enter full position for pure lending strategy.
        
        Args:
            equity: Available equity in share class currency
            
        Returns:
            StrategyAction with instructions for full entry
        """
        try:
            instructions = []
            
            if self.share_class == 'USDT':
                # Supply USDT to lending venue
                instructions.append({
                    'action': 'supply',
                    'venue': self.lending_venue,
                    'token': 'USDT',
                    'amount': equity,
                    'atomic': True
                })
            elif self.share_class == 'ETH':
                # Supply ETH to lending venue
                instructions.append({
                    'action': 'supply',
                    'venue': self.lending_venue,
                    'token': 'ETH',
                    'amount': equity,
                    'atomic': True
                })
            
            return StrategyAction(
                action_type='entry_full',
                target_amount=equity,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'pure_lending',
                    'venue': self.lending_venue,
                    'target_apy': self.target_apy
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
        Scale up position for pure lending strategy.
        
        Args:
            equity_delta: Additional equity to deploy
            
        Returns:
            StrategyAction with instructions for partial entry
        """
        try:
            instructions = []
            
            if self.share_class == 'USDT':
                # Supply additional USDT to lending venue
                instructions.append({
                    'action': 'supply',
                    'venue': self.lending_venue,
                    'token': 'USDT',
                    'amount': equity_delta,
                    'atomic': True
                })
            elif self.share_class == 'ETH':
                # Supply additional ETH to lending venue
                instructions.append({
                    'action': 'supply',
                    'venue': self.lending_venue,
                    'token': 'ETH',
                    'amount': equity_delta,
                    'atomic': True
                })
            
            return StrategyAction(
                action_type='entry_partial',
                target_amount=equity_delta,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'pure_lending',
                    'venue': self.lending_venue,
                    'target_apy': self.target_apy
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
        Exit entire position for pure lending strategy.
        
        Args:
            equity: Total equity to exit
            
        Returns:
            StrategyAction with instructions for full exit
        """
        try:
            instructions = []
            
            if self.share_class == 'USDT':
                # Withdraw all USDT from lending venue
                instructions.append({
                    'action': 'withdraw',
                    'venue': self.lending_venue,
                    'token': 'USDT',
                    'amount': equity,
                    'atomic': True
                })
            elif self.share_class == 'ETH':
                # Withdraw all ETH from lending venue
                instructions.append({
                    'action': 'withdraw',
                    'venue': self.lending_venue,
                    'token': 'ETH',
                    'amount': equity,
                    'atomic': True
                })
            
            return StrategyAction(
                action_type='exit_full',
                target_amount=equity,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'pure_lending',
                    'venue': self.lending_venue
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
        Scale down position for pure lending strategy.
        
        Args:
            equity_delta: Equity to remove from position
            
        Returns:
            StrategyAction with instructions for partial exit
        """
        try:
            instructions = []
            
            if self.share_class == 'USDT':
                # Withdraw partial USDT from lending venue
                instructions.append({
                    'action': 'withdraw',
                    'venue': self.lending_venue,
                    'token': 'USDT',
                    'amount': equity_delta,
                    'atomic': True
                })
            elif self.share_class == 'ETH':
                # Withdraw partial ETH from lending venue
                instructions.append({
                    'action': 'withdraw',
                    'venue': self.lending_venue,
                    'token': 'ETH',
                    'amount': equity_delta,
                    'atomic': True
                })
            
            return StrategyAction(
                action_type='exit_partial',
                target_amount=equity_delta,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'pure_lending',
                    'venue': self.lending_venue
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
        Convert non-share-class tokens to share class currency for pure lending strategy.
        
        Args:
            dust_tokens: Dictionary of dust tokens and amounts
            
        Returns:
            StrategyAction with instructions for dust selling
        """
        try:
            instructions = []
            total_dust_value = 0.0
            
            for token, amount in dust_tokens.items():
                if amount > 0 and token != self.share_class:
                    # Convert dust token to share class currency
                    instructions.append({
                        'action': 'swap',
                        'from_token': token,
                        'to_token': self.share_class,
                        'amount': amount,
                        'atomic': True
                    })
                    
                    # Calculate dust value for metadata
                    if token == self.asset:
                        total_dust_value += amount * self._get_asset_price()
                    else:
                        total_dust_value += amount * self._get_lst_price(token)
            
            return StrategyAction(
                action_type='sell_dust',
                target_amount=total_dust_value,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'pure_lending',
                    'dust_tokens': dust_tokens
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
