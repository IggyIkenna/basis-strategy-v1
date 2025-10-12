"""
Pure Lending Strategy Implementation

This module implements the pure lending strategy using the base strategy manager
architecture with standardized 5-action interface.

Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
Reference: docs/MODES.md - Pure Lending Strategy
"""

from typing import Dict, List, Any
from .base_strategy_manager import BaseStrategyManager, StrategyAction
import logging

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
        venues_config = config.get('venues', {})
        self.lending_venues = [venue for venue, settings in venues_config.items() if settings.get('enabled', False)]
        
        # Pure lending doesn't use LTV (no borrowing/leverage)
        # LTV values are not applicable for pure lending strategies
        
        logger.info(f"PureLendingStrategy initialized for {self.share_class} {self.asset}")
    
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
    
    def entry_full(self, equity: float) -> StrategyAction:
        """Enter full position (initial setup or large deposits)"""
        try:
            target_position = self.calculate_target_position(equity)
            
            instructions = []
            for venue in self.lending_venues:
                instructions.append({
                    'venue': venue,
                    'action': 'supply',
                    'amount': target_position['supply'] / len(self.lending_venues),
                    'currency': self.asset
                })
                instructions.append({
                    'venue': venue,
                    'action': 'borrow',
                    'amount': target_position['borrow'] / len(self.lending_venues),
                    'currency': self.asset
                })
            
            return StrategyAction(
                action_type='entry_full',
                target_amount=target_position['supply'],
                target_currency=self.asset,
                instructions=instructions,
                atomic=True
            )
        except Exception as e:
            logger.error(f"Failed to create entry_full action: {e}")
            return StrategyAction(
                action_type='entry_full',
                target_amount=0.0,
                target_currency=self.asset,
                instructions=[],
                atomic=True
            )
    
    def entry_partial(self, equity_delta: float) -> StrategyAction:
        """Scale up position (small deposits or PnL gains)"""
        try:
            # Scale up proportionally
            target_position = self.calculate_target_position(equity_delta)
            
            instructions = []
            for venue in self.lending_venues:
                instructions.append({
                    'venue': venue,
                    'action': 'supply',
                    'amount': target_position['supply'] / len(self.lending_venues),
                    'currency': self.asset
                })
                instructions.append({
                    'venue': venue,
                    'action': 'borrow',
                    'amount': target_position['borrow'] / len(self.lending_venues),
                    'currency': self.asset
                })
            
            return StrategyAction(
                action_type='entry_partial',
                target_amount=target_position['supply'],
                target_currency=self.asset,
                instructions=instructions,
                atomic=True
            )
        except Exception as e:
            logger.error(f"Failed to create entry_partial action: {e}")
            return StrategyAction(
                action_type='entry_partial',
                target_amount=0.0,
                target_currency=self.asset,
                instructions=[],
                atomic=True
            )
    
    def exit_full(self, equity: float) -> StrategyAction:
        """Exit entire position (withdrawals or risk override)"""
        try:
            # Get current position to determine exit amounts
            position_snapshot = self.position_monitor.get_position_snapshot()
            current_supply = position_snapshot.get('total_supply', 0.0)
            current_borrow = position_snapshot.get('total_borrow', 0.0)
            
            instructions = []
            for venue in self.lending_venues:
                instructions.append({
                    'venue': venue,
                    'action': 'repay',
                    'amount': current_borrow / len(self.lending_venues),
                    'currency': self.asset
                })
                instructions.append({
                    'venue': venue,
                    'action': 'withdraw',
                    'amount': current_supply / len(self.lending_venues),
                    'currency': self.asset
                })
            
            return StrategyAction(
                action_type='exit_full',
                target_amount=current_supply,
                target_currency=self.asset,
                instructions=instructions,
                atomic=True
            )
        except Exception as e:
            logger.error(f"Failed to create exit_full action: {e}")
            return StrategyAction(
                action_type='exit_full',
                target_amount=0.0,
                target_currency=self.asset,
                instructions=[],
                atomic=True
            )
    
    def exit_partial(self, equity_delta: float) -> StrategyAction:
        """Scale down position (small withdrawals or risk reduction)"""
        try:
            # Scale down proportionally
            target_position = self.calculate_target_position(equity_delta)
            
            instructions = []
            for venue in self.lending_venues:
                instructions.append({
                    'venue': venue,
                    'action': 'repay',
                    'amount': target_position['borrow'] / len(self.lending_venues),
                    'currency': self.asset
                })
                instructions.append({
                    'venue': venue,
                    'action': 'withdraw',
                    'amount': target_position['supply'] / len(self.lending_venues),
                    'currency': self.asset
                })
            
            return StrategyAction(
                action_type='exit_partial',
                target_amount=target_position['supply'],
                target_currency=self.asset,
                instructions=instructions,
                atomic=True
            )
        except Exception as e:
            logger.error(f"Failed to create exit_partial action: {e}")
            return StrategyAction(
                action_type='exit_partial',
                target_amount=0.0,
                target_currency=self.asset,
                instructions=[],
                atomic=True
            )
    
    def sell_dust(self, dust_tokens: Dict[str, float]) -> StrategyAction:
        """Convert non-share-class tokens to share class currency"""
        try:
            instructions = []
            for token, amount in dust_tokens.items():
                if token != self.asset and amount > 0:
                    instructions.append({
                        'venue': 'spot_exchange',
                        'action': 'sell',
                        'amount': amount,
                        'currency': token,
                        'target_currency': self.asset
                    })
            
            return StrategyAction(
                action_type='sell_dust',
                target_amount=sum(dust_tokens.values()),
                target_currency=self.asset,
                instructions=instructions,
                atomic=False
            )
        except Exception as e:
            logger.error(f"Failed to create sell_dust action: {e}")
            return StrategyAction(
                action_type='sell_dust',
                target_amount=0.0,
                target_currency=self.asset,
                instructions=[],
                atomic=False
            )