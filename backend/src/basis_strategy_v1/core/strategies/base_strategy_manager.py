"""
Base Strategy Manager Architecture

This module provides the base class for all strategy managers, implementing
the standardized 5-action interface and inheritance-based architecture.

Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-007
Reference: docs/MODES.md - Standardized Strategy Manager Architecture
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class StrategyAction(BaseModel):
    """Standardized strategy action wrapper"""
    action_type: str  # entry_full, entry_partial, exit_full, exit_partial, sell_dust
    target_amount: float
    target_currency: str
    instructions: List[Dict[str, Any]]
    atomic: bool = False

class BaseStrategyManager(ABC):
    """Base strategy manager with standardized interface"""
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, event_engine):
        """
        Initialize base strategy manager.
        
        Args:
            config: Strategy configuration
            risk_monitor: Risk monitor instance
            position_monitor: Position monitor instance
            event_engine: Event engine instance
        """
        self.config = config
        self.risk_monitor = risk_monitor
        self.position_monitor = position_monitor
        self.event_engine = event_engine
        self.share_class = config['share_class']
        self.asset = config['asset']
        
        logger.info(f"BaseStrategyManager initialized for {self.share_class} {self.asset}")
    
    @abstractmethod
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """Calculate target position based on current equity"""
        pass
    
    @abstractmethod
    def entry_full(self, equity: float) -> StrategyAction:
        """Enter full position (initial setup or large deposits)"""
        pass
    
    @abstractmethod
    def entry_partial(self, equity_delta: float) -> StrategyAction:
        """Scale up position (small deposits or PnL gains)"""
        pass
    
    @abstractmethod
    def exit_full(self, equity: float) -> StrategyAction:
        """Exit entire position (withdrawals or risk override)"""
        pass
    
    @abstractmethod
    def exit_partial(self, equity_delta: float) -> StrategyAction:
        """Scale down position (small withdrawals or risk reduction)"""
        pass
    
    @abstractmethod
    def sell_dust(self, dust_tokens: Dict[str, float]) -> StrategyAction:
        """Convert non-share-class tokens to share class currency"""
        pass
    
    def get_equity(self) -> float:
        """Get current equity in share class currency"""
        # Assets net of debt, excluding futures positions
        # Only include tokens on actual wallets, not locked in smart contracts
        try:
            position_snapshot = self.position_monitor.get_position_snapshot()
            return position_snapshot.get('total_equity', 0.0)
        except Exception as e:
            logger.error(f"Failed to get equity: {e}")
            return 0.0
    
    def should_sell_dust(self, dust_tokens: Dict[str, float]) -> bool:
        """Check if dust tokens exceed threshold"""
        try:
            dust_value = sum(self.get_token_value(token, amount) for token, amount in dust_tokens.items())
            equity = self.get_equity()
            dust_threshold = self.config.get('dust_delta', 0.002)
            return dust_value > (equity * dust_threshold)
        except Exception as e:
            logger.error(f"Failed to check dust threshold: {e}")
            return False
    
    def get_token_value(self, token: str, amount: float) -> float:
        """Get USD value of token amount"""
        try:
            # This would typically use a price feed or data provider
            # For now, return a placeholder implementation
            price_feed = self.config.get('price_feeds', {})
            token_price = price_feed.get(token, 1.0)  # Default to 1.0 if no price
            return amount * token_price
        except Exception as e:
            logger.error(f"Failed to get token value for {token}: {e}")
            return 0.0
    
    def trigger_tight_loop(self):
        """Trigger tight loop component chain after position updates"""
        # Position updates trigger sequential component chain:
        # position_monitor → exposure_monitor → risk_monitor → pnl_monitor
        try:
            self.event_engine.trigger_tight_loop()
        except Exception as e:
            logger.error(f"Failed to trigger tight loop: {e}")
    
    def execute_decision(self, action: StrategyAction) -> Dict[str, Any]:
        """Execute a strategy decision action"""
        try:
            logger.info(f"Executing strategy action: {action.action_type}")
            
            # This would typically delegate to execution managers
            # For now, return a placeholder implementation
            return {
                'success': True,
                'action_type': action.action_type,
                'target_amount': action.target_amount,
                'target_currency': action.target_currency,
                'atomic': action.atomic
            }
        except Exception as e:
            logger.error(f"Failed to execute strategy decision: {e}")
            return {
                'success': False,
                'error': str(e),
                'action_type': action.action_type
            }