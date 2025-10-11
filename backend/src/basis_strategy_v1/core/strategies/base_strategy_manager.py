"""
Base Strategy Manager

Provides the abstract base class for all strategy implementations with standardized
wrapper actions and tight loop architecture integration.

Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-007 (11 Component Architecture)
Reference: docs/MODES.md - Standardized Strategy Manager Architecture
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import pandas as pd
import logging

from ...infrastructure.logging.structured_logger import get_strategy_manager_logger

logger = logging.getLogger(__name__)


class StrategyAction(BaseModel):
    """Standardized strategy action wrapper."""
    action_type: str  # entry_full, entry_partial, exit_full, exit_partial, sell_dust
    target_amount: float  # Must be positive
    target_currency: str
    instructions: List[Dict[str, Any]]
    atomic: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
    
    def __init__(self, **data):
        """Initialize with validation."""
        super().__init__(**data)
        
        # Validate target_amount is positive
        if self.target_amount < 0:
            raise ValueError(f"target_amount must be positive, got {self.target_amount}")
        
        # Validate action_type is valid
        valid_actions = ['entry_full', 'entry_partial', 'exit_full', 'exit_partial', 'sell_dust']
        if self.action_type not in valid_actions:
            raise ValueError(f"action_type must be one of {valid_actions}, got {self.action_type}")


class BaseStrategyManager(ABC):
    """Base strategy manager with standardized interface."""
    
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
        
        # Initialize structured logger
        self.structured_logger = get_strategy_manager_logger()
        
        # Extract strategy parameters
        self.share_class = config.get('share_class', 'USDT')
        self.asset = config.get('asset', 'USDT')
        self.mode = config.get('mode', 'unknown')
        
        # Reserve management
        self.reserve_ratio = config.get('reserve_ratio', 0.1)  # 10% default
        self.dust_threshold = config.get('dust_threshold', 0.002)  # 0.2% default
        
        self.structured_logger.info(
            "BaseStrategyManager initialized",
            event_type="component_initialization",
            component="strategy_manager",
            mode=self.mode,
            share_class=self.share_class,
            asset=self.asset
        )
    
    @abstractmethod
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position based on current equity.
        
        Args:
            current_equity: Current equity in share class currency
            
        Returns:
            Dictionary with target positions by token
        """
        pass
    
    @abstractmethod
    def entry_full(self, equity: float) -> StrategyAction:
        """
        Enter full position (initial setup or large deposits).
        
        Args:
            equity: Available equity to deploy
            
        Returns:
            Strategy action for full entry
        """
        pass
    
    @abstractmethod
    def entry_partial(self, equity_delta: float) -> StrategyAction:
        """
        Scale up position (small deposits or PnL gains).
        
        Args:
            equity_delta: Additional equity to deploy
            
        Returns:
            Strategy action for partial entry
        """
        pass
    
    @abstractmethod
    def exit_full(self, equity: float) -> StrategyAction:
        """
        Exit entire position (withdrawals or risk override).
        
        Args:
            equity: Current equity to exit
            
        Returns:
            Strategy action for full exit
        """
        pass
    
    @abstractmethod
    def exit_partial(self, equity_delta: float) -> StrategyAction:
        """
        Scale down position (small withdrawals or risk reduction).
        
        Args:
            equity_delta: Equity to reduce
            
        Returns:
            Strategy action for partial exit
        """
        pass
    
    @abstractmethod
    def sell_dust(self, dust_tokens: Dict[str, float]) -> StrategyAction:
        """
        Convert non-share-class tokens to share class currency.
        
        Args:
            dust_tokens: Dictionary of dust tokens and amounts
            
        Returns:
            Strategy action for dust selling
        """
        pass
    
    def get_equity(self) -> float:
        """
        Get current equity in share class currency.
        
        Returns:
            Current equity (assets net of debt, excluding futures positions)
        """
        try:
            # Get current positions from position monitor
            positions = self.position_monitor.get_current_positions()
            
            # Calculate equity as assets net of debt
            # Only include tokens on actual wallets, not locked in smart contracts
            equity = 0.0
            
            # Add wallet positions (actual tokens)
            if 'wallet' in positions:
                for token, position in positions['wallet'].items():
                    if position.get('amount', 0) > 0:
                        # Convert to share class currency
                        value = self._get_token_value(token, position['amount'])
                        equity += value
            
            # Add smart contract positions (aTokens, LST tokens)
            if 'smart_contract' in positions:
                for token, position in positions['smart_contract'].items():
                    if position.get('amount', 0) > 0:
                        # Convert to share class currency
                        value = self._get_token_value(token, position['amount'])
                        equity += value
            
            # Subtract debt positions
            if 'debt' in positions:
                for token, position in positions['debt'].items():
                    if position.get('amount', 0) > 0:
                        # Convert to share class currency
                        value = self._get_token_value(token, position['amount'])
                        equity -= value
            
            self.structured_logger.debug(
                f"Calculated equity: {equity:.2f} {self.share_class}",
                event_type="equity_calculation",
                equity=equity,
                share_class=self.share_class
            )
            
            return equity
            
        except Exception as e:
            self.structured_logger.error(
                f"Error calculating equity: {e}",
                event_type="equity_calculation_error",
                error=str(e)
            )
            return 0.0
    
    def _get_token_value(self, token: str, amount: float) -> float:
        """
        Get token value in share class currency.
        
        Args:
            token: Token symbol
            amount: Token amount
            
        Returns:
            Value in share class currency
        """
        try:
            # Use utility manager for price conversion
            if hasattr(self, 'utility_manager') and self.utility_manager:
                return self.utility_manager.get_token_value(token, amount, self.share_class)
            else:
                # Fallback to simple conversion (1:1 for same currency)
                if token == self.share_class:
                    return amount
                else:
                    # For now, return amount as fallback
                    # In production, this should use proper price feeds
                    return amount
        except Exception as e:
            self.structured_logger.warning(
                f"Error getting token value for {token}: {e}",
                event_type="token_value_error",
                token=token,
                amount=amount,
                error=str(e)
            )
            return amount
    
    def should_sell_dust(self, dust_tokens: Dict[str, float]) -> bool:
        """
        Check if dust tokens exceed threshold.
        
        Args:
            dust_tokens: Dictionary of dust tokens and amounts
            
        Returns:
            True if dust should be sold
        """
        try:
            dust_value = sum(
                self._get_token_value(token, amount) 
                for token, amount in dust_tokens.items()
            )
            equity = self.get_equity()
            threshold = equity * self.dust_threshold
            
            should_sell = dust_value > threshold
            
            self.structured_logger.debug(
                f"Dust check: {dust_value:.2f} > {threshold:.2f} = {should_sell}",
                event_type="dust_check",
                dust_value=dust_value,
                threshold=threshold,
                should_sell=should_sell
            )
            
            return should_sell
            
        except Exception as e:
            self.structured_logger.error(
                f"Error checking dust threshold: {e}",
                event_type="dust_check_error",
                error=str(e)
            )
            return False
    
    def check_reserves(self) -> Dict[str, Any]:
        """
        Check if reserves are sufficient.
        
        Returns:
            Dictionary with reserve status
        """
        try:
            equity = self.get_equity()
            required_reserve = equity * self.reserve_ratio
            current_reserve = self._get_current_reserve()
            
            reserve_status = {
                'equity': equity,
                'required_reserve': required_reserve,
                'current_reserve': current_reserve,
                'reserve_ratio': self.reserve_ratio,
                'sufficient': current_reserve >= required_reserve,
                'shortfall': max(0, required_reserve - current_reserve)
            }
            
            if not reserve_status['sufficient']:
                self.structured_logger.warning(
                    f"Reserves insufficient: {current_reserve:.2f} < {required_reserve:.2f}",
                    event_type="reserve_warning",
                    **reserve_status
                )
            
            return reserve_status
            
        except Exception as e:
            self.structured_logger.error(
                f"Error checking reserves: {e}",
                event_type="reserve_check_error",
                error=str(e)
            )
            return {
                'equity': 0.0,
                'required_reserve': 0.0,
                'current_reserve': 0.0,
                'reserve_ratio': self.reserve_ratio,
                'sufficient': False,
                'shortfall': 0.0
            }
    
    def _get_current_reserve(self) -> float:
        """
        Get current reserve amount in share class currency.
        
        Returns:
            Current reserve amount
        """
        try:
            # Get current positions
            positions = self.position_monitor.get_current_positions()
            
            # Calculate reserve as liquid tokens in share class currency
            reserve = 0.0
            
            # Add wallet positions in share class currency
            if 'wallet' in positions:
                for token, position in positions['wallet'].items():
                    if token == self.share_class and position.get('amount', 0) > 0:
                        reserve += position['amount']
            
            return reserve
            
        except Exception as e:
            self.structured_logger.error(
                f"Error getting current reserve: {e}",
                event_type="reserve_calculation_error",
                error=str(e)
            )
            return 0.0
    
    def trigger_tight_loop(self):
        """
        Trigger tight loop component chain after position updates.
        
        Position updates trigger sequential component chain:
        position_monitor → exposure_monitor → risk_monitor → pnl_monitor
        """
        try:
            self.structured_logger.debug(
                "Triggering tight loop after position update",
                event_type="tight_loop_trigger"
            )
            
            # Trigger tight loop through event engine
            if hasattr(self.event_engine, 'trigger_tight_loop'):
                self.event_engine.trigger_tight_loop()
            else:
                self.structured_logger.warning(
                    "Event engine does not support tight loop triggering",
                    event_type="tight_loop_warning"
                )
                
        except Exception as e:
            self.structured_logger.error(
                f"Error triggering tight loop: {e}",
                event_type="tight_loop_error",
                error=str(e)
            )
    
    def make_decision(self, timestamp: pd.Timestamp, market_data: Dict[str, Any]) -> Optional[StrategyAction]:
        """
        Make strategy decision based on current state.
        
        Args:
            timestamp: Current timestamp
            market_data: Current market data
            
        Returns:
            Strategy action or None if no action needed
        """
        try:
            # Get current equity
            equity = self.get_equity()
            
            # Check reserves first
            reserve_status = self.check_reserves()
            if not reserve_status['sufficient']:
                # Need to add reserves - this is a priority
                self.structured_logger.warning(
                    f"Reserves insufficient, need to add {reserve_status['shortfall']:.2f}",
                    event_type="reserve_insufficient",
                    **reserve_status
                )
                # For now, return None - in production, this would trigger reserve addition
                return None
            
            # Calculate target position
            target_position = self.calculate_target_position(equity)
            
            # Compare with current position to determine action
            current_position = self.position_monitor.get_current_positions()
            
            # For now, return None - specific strategy implementations will handle this
            return None
            
        except Exception as e:
            self.structured_logger.error(
                f"Error making strategy decision: {e}",
                event_type="strategy_decision_error",
                error=str(e),
                timestamp=timestamp.isoformat()
            )
            return None