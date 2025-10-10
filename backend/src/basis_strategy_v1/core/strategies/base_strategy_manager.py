"""
Base Strategy Manager

Abstract base class for all strategy managers with standardized interface
and inheritance-based architecture.

Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-007 (11 Component Architecture)
Reference: docs/MODES.md - Standardized Strategy Manager Architecture
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from ...infrastructure.logging.structured_logger import get_strategy_manager_logger


class StrategyAction(BaseModel):
    """Standardized strategy action wrapper"""
    action_type: str  # entry_full, entry_partial, exit_full, exit_partial, sell_dust
    target_amount: float
    target_currency: str
    instructions: List[Dict[str, Any]]
    atomic: bool = False
    metadata: Optional[Dict[str, Any]] = None


class BaseStrategyManager(ABC):
    """Base strategy manager with standardized interface"""
    
    def __init__(
        self,
        config: Dict[str, Any],
        risk_monitor,
        position_monitor,
        event_engine,
        utility_manager=None
    ):
        self.config = config
        self.risk_monitor = risk_monitor
        self.position_monitor = position_monitor
        self.event_engine = event_engine
        self.utility_manager = utility_manager
        
        # Strategy configuration
        self.share_class = config.get('share_class')
        self.asset = config.get('asset')
        self.mode = config.get('mode')
        self.reserve_ratio = config.get('reserve_ratio', 0.1)
        self.dust_delta = config.get('dust_delta', 0.002)
        
        # Logging
        self.logger = get_strategy_manager_logger()
        
        self.logger.info(
            f"Strategy manager initialized: {self.mode}",
            event_type='initialization',
            strategy_mode=self.mode,
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
            Dictionary with target positions for each asset
        """
        pass
    
    @abstractmethod
    def entry_full(self, equity: float) -> StrategyAction:
        """
        Enter full position (initial setup or large deposits).
        
        Args:
            equity: Available equity to deploy
            
        Returns:
            StrategyAction with entry instructions
        """
        pass
    
    @abstractmethod
    def entry_partial(self, equity_delta: float) -> StrategyAction:
        """
        Scale up position (small deposits or PnL gains).
        
        Args:
            equity_delta: Additional equity to deploy
            
        Returns:
            StrategyAction with partial entry instructions
        """
        pass
    
    @abstractmethod
    def exit_full(self, equity: float) -> StrategyAction:
        """
        Exit entire position (withdrawals or risk override).
        
        Args:
            equity: Current equity to exit
            
        Returns:
            StrategyAction with full exit instructions
        """
        pass
    
    @abstractmethod
    def exit_partial(self, equity_delta: float) -> StrategyAction:
        """
        Scale down position (small withdrawals or risk reduction).
        
        Args:
            equity_delta: Equity to reduce from position
            
        Returns:
            StrategyAction with partial exit instructions
        """
        pass
    
    @abstractmethod
    def sell_dust(self, dust_tokens: Dict[str, float]) -> StrategyAction:
        """
        Convert non-share-class tokens to share class currency.
        
        Args:
            dust_tokens: Dictionary of dust tokens and amounts
            
        Returns:
            StrategyAction with dust selling instructions
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
            positions = self.position_monitor.get_all_positions()
            
            # Calculate equity in share class currency
            equity = 0.0
            for asset, position in positions.items():
                if asset == self.share_class:
                    equity += position.get('balance', 0.0)
                else:
                    # Convert other assets to share class currency
                    asset_value = self.get_token_value(asset, position.get('balance', 0.0))
                    equity += asset_value
            
            # Subtract any debt (if applicable)
            debt = self.position_monitor.get_total_debt()
            equity -= debt
            
            self.logger.debug(
                f"Equity calculated: {equity} {self.share_class}",
                event_type='equity_calculation',
                equity=equity,
                share_class=self.share_class
            )
            
            return equity
            
        except Exception as e:
            self.logger.error(
                f"Failed to calculate equity: {e}",
                event_type='equity_calculation_error',
                error=str(e)
            )
            return 0.0
    
    def get_token_value(self, token: str, amount: float) -> float:
        """
        Get value of token in share class currency.
        
        Args:
            token: Token symbol
            amount: Token amount
            
        Returns:
            Value in share class currency
        """
        if self.utility_manager:
            return self.utility_manager.get_token_value(token, amount, self.share_class)
        else:
            # Fallback to simple 1:1 conversion (for testing)
            return amount
    
    def should_sell_dust(self, dust_tokens: Dict[str, float]) -> bool:
        """
        Check if dust tokens exceed threshold.
        
        Args:
            dust_tokens: Dictionary of dust tokens and amounts
            
        Returns:
            True if dust should be sold
        """
        if not dust_tokens:
            return False
        
        dust_value = sum(
            self.get_token_value(token, amount) 
            for token, amount in dust_tokens.items()
        )
        equity = self.get_equity()
        threshold = equity * self.dust_delta
        
        should_sell = dust_value > threshold
        
        if should_sell:
            self.logger.info(
                f"Dust threshold exceeded: {dust_value} > {threshold}",
                event_type='dust_threshold_exceeded',
                dust_value=dust_value,
                threshold=threshold,
                dust_tokens=dust_tokens
            )
        
        return should_sell
    
    def trigger_tight_loop(self):
        """
        Trigger tight loop component chain after position updates.
        
        Position updates trigger sequential component chain:
        position_monitor → exposure_monitor → risk_monitor → pnl_monitor
        """
        try:
            if self.event_engine:
                self.event_engine.trigger_tight_loop()
                self.logger.debug("Tight loop triggered", event_type='tight_loop_triggered')
            else:
                self.logger.warning("No event engine available for tight loop", event_type='tight_loop_error')
        except Exception as e:
            self.logger.error(
                f"Failed to trigger tight loop: {e}",
                event_type='tight_loop_error',
                error=str(e)
            )
    
    def check_reserve_ratio(self) -> bool:
        """
        Check if reserves are below threshold.
        
        Returns:
            True if reserves are low
        """
        try:
            equity = self.get_equity()
            reserve_amount = equity * self.reserve_ratio
            current_reserves = self.position_monitor.get_reserve_balance(self.share_class)
            
            is_low = current_reserves < reserve_amount
            
            if is_low:
                self.logger.warning(
                    f"Reserves low: {current_reserves} < {reserve_amount}",
                    event_type='reserves_low',
                    current_reserves=current_reserves,
                    required_reserves=reserve_amount,
                    reserve_ratio=self.reserve_ratio
                )
            
            return is_low
            
        except Exception as e:
            self.logger.error(
                f"Failed to check reserve ratio: {e}",
                event_type='reserve_check_error',
                error=str(e)
            )
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get strategy manager health status."""
        try:
            equity = self.get_equity()
            reserves_low = self.check_reserve_ratio()
            
            return {
                'status': 'healthy',
                'strategy_mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': equity,
                'reserves_low': reserves_low,
                'reserve_ratio': self.reserve_ratio,
                'dust_delta': self.dust_delta,
                'interfaces_connected': {
                    'risk_monitor': self.risk_monitor is not None,
                    'position_monitor': self.position_monitor is not None,
                    'event_engine': self.event_engine is not None,
                    'utility_manager': self.utility_manager is not None
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'strategy_mode': self.mode
            }
    
    def log_strategy_event(
        self,
        event_type: str,
        message: str,
        level: str = 'INFO',
        **kwargs
    ):
        """Log strategy-specific event."""
        self.logger.log_strategy_event(
            strategy_name=self.mode,
            event_type=event_type,
            message=message,
            level=level,
            **kwargs
        )