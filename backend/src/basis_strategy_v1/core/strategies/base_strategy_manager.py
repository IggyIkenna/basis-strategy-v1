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
import logging
import os
import pandas as pd

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType
from ...core.models.order import Order

logger = logging.getLogger(__name__)

# Temporary placeholder for backward compatibility with other strategies
# TODO: Remove after all strategies are refactored to use Order model
class StrategyAction:
    """Temporary placeholder - will be removed after full refactor."""
    def __init__(self, action_type: str, target_amount: float, target_currency: str, instructions: List[Dict], atomic: bool = False):
        self.action_type = action_type
        self.target_amount = target_amount
        self.target_currency = target_currency
        self.instructions = instructions
        self.atomic = atomic

class BaseStrategyManager(ABC, StandardizedLoggingMixin):
    """Base strategy manager with standardized interface"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BaseStrategyManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, event_engine):
        """
        Initialize base strategy manager.
        
        Args:
            config: Strategy configuration
            risk_monitor: Risk monitor instance
            position_monitor: Position monitor instance
            event_engine: Event engine instance
        """
        super().__init__()
        self.config = config
        self.risk_monitor = risk_monitor
        self.position_monitor = position_monitor
        self.event_engine = event_engine
        self.share_class = config['share_class']
        self.asset = config['asset']
        
        # Log component initialization
        self.log_component_event(
            event_type=EventType.COMPONENT_INITIALIZATION,
            message=f"BaseStrategyManager initialized for {self.share_class} {self.asset}",
            data={
                'share_class': self.share_class,
                'asset': self.asset,
                'execution_mode': os.getenv('BASIS_EXECUTION_MODE', 'backtest'),
                'strategy_type': self.__class__.__name__
            },
            level=LogLevel.INFO
        )
        
        logger.info(f"BaseStrategyManager initialized for {self.share_class} {self.asset}")
    
    @abstractmethod
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """Calculate target position based on current equity"""
        pass
    
    @abstractmethod
    def make_strategy_decision(
        self,
        timestamp: pd.Timestamp,
        trigger_source: str,
        market_data: Dict,
        exposure_data: Dict,
        risk_assessment: Dict
    ) -> List[Order]:
        """
        Make strategy decision and return list of orders.
        
        This is the main method that strategies implement to specify what orders
        they want executed. No intermediate abstractions - strategies directly
        specify orders.
        
        Args:
            timestamp: Current timestamp
            trigger_source: Source of the decision trigger ('risk_monitor', 'exposure_monitor', 'scheduled', etc.)
            market_data: Current market data from data provider
            exposure_data: Current exposure data from exposure monitor
            risk_assessment: Current risk assessment from risk monitor
            
        Returns:
            List[Order]: List of orders to execute
        """
        pass
    
    def get_equity(self) -> float:
        """Get current equity in share class currency"""
        # Assets net of debt, excluding futures positions
        # Only include tokens on actual wallets, not locked in smart contracts
        try:
            position_snapshot = self.position_monitor.get_position_snapshot()
            return position_snapshot.get('total_equity', 0.0)
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'method': 'get_equity',
                    'share_class': self.share_class,
                    'asset': self.asset
                }
            )
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
            self.log_error(
                error=e,
                context={
                    'method': 'should_sell_dust',
                    'dust_tokens': dust_tokens,
                    'share_class': self.share_class
                }
            )
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
            self.log_error(
                error=e,
                context={
                    'method': 'get_token_value',
                    'token': token,
                    'amount': amount
                }
            )
            logger.error(f"Failed to get token value for {token}: {e}")
            return 0.0
    
    def trigger_tight_loop(self):
        """
        Trigger tight loop execution reconciliation pattern.
        
        The tight loop ensures that each execution instruction is followed by
        position reconciliation before proceeding to the next instruction.
        
        Tight Loop = execution → position_monitor → reconciliation → next instruction
        """
        try:
            self.event_engine.trigger_tight_loop()
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'method': 'trigger_tight_loop',
                    'share_class': self.share_class,
                    'asset': self.asset
                }
            )
            logger.error(f"Failed to trigger tight loop: {e}")
    
    def get_current_equity(self, exposure_data: Dict) -> float:
        """Get current equity from exposure data."""
        return exposure_data.get('total_exposure', 0.0)
    
    def should_enter_position(self, exposure_data: Dict, risk_assessment: Dict) -> bool:
        """Check if strategy should enter a position."""
        current_equity = self.get_current_equity(exposure_data)
        return current_equity > 0
    
    def should_exit_position(self, exposure_data: Dict, risk_assessment: Dict) -> bool:
        """Check if strategy should exit position."""
        # Check for risk overrides
        if risk_assessment.get('risk_override', False):
            return True
        
        # Check for withdrawal triggers
        if exposure_data.get('withdrawal_requested', False):
            return True
        
        return False
    
    def get_dust_tokens(self, exposure_data: Dict) -> Dict[str, float]:
        """Get dust tokens that should be converted."""
        return exposure_data.get('dust_tokens', {})
    
    def should_sell_dust(self, exposure_data: Dict) -> bool:
        """Check if dust tokens exceed threshold."""
        dust_tokens = self.get_dust_tokens(exposure_data)
        if not dust_tokens:
            return False
        
        try:
            dust_value = sum(self.get_token_value(token, amount) for token, amount in dust_tokens.items())
            equity = self.get_current_equity(exposure_data)
            dust_threshold = self.config.get('dust_delta', 0.002)
            return dust_value > (equity * dust_threshold)
        except Exception as e:
            self.log_error(
                error=e,
                context={
                    'method': 'should_sell_dust',
                    'dust_tokens': dust_tokens,
                    'share_class': self.share_class
                }
            )
            logger.error(f"Failed to check dust threshold: {e}")
            return False