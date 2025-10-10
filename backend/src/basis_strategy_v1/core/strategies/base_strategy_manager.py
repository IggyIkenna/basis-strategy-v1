"""
Base Strategy Manager Architecture

Provides the base class and standardized interface for all strategy implementations.
Uses inheritance-based strategy modes with standardized wrapper actions.

Reference: docs/MODES.md - Standardized Strategy Manager Architecture
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
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
    metadata: Dict[str, Any] = {}

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
        # Validate required configuration at startup (fail-fast)
        required_keys = ['share_class', 'asset', 'mode']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        self.config = config
        self.risk_monitor = risk_monitor
        self.position_monitor = position_monitor
        self.event_engine = event_engine
        self.share_class = config['share_class']
        self.asset = config['asset']
        self.mode = config['mode']
        
        # Reserve management (optional with fail-fast)
        if 'reserve_ratio' in config:
            self.reserve_ratio = config['reserve_ratio']
        else:
            self.reserve_ratio = 0.05  # 5% default only if not specified
            
        if 'dust_delta' in config:
            self.dust_delta = config['dust_delta']
        else:
            self.dust_delta = 0.002  # 0.2% default only if not specified
        
        logger.info(f"BaseStrategyManager initialized for {self.mode} mode, {self.share_class} share class")
    
    @abstractmethod
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position based on current equity.
        
        Args:
            current_equity: Current equity in share class currency
            
        Returns:
            Dictionary of target positions by token/venue
        """
        pass
    
    @abstractmethod
    def entry_full(self, equity: float) -> StrategyAction:
        """
        Enter full position (initial setup or large deposits).
        
        Args:
            equity: Available equity in share class currency
            
        Returns:
            StrategyAction with instructions for full entry
        """
        pass
    
    @abstractmethod
    def entry_partial(self, equity_delta: float) -> StrategyAction:
        """
        Scale up position (small deposits or PnL gains).
        
        Args:
            equity_delta: Additional equity to deploy
            
        Returns:
            StrategyAction with instructions for partial entry
        """
        pass
    
    @abstractmethod
    def exit_full(self, equity: float) -> StrategyAction:
        """
        Exit entire position (withdrawals or risk override).
        
        Args:
            equity: Total equity to exit
            
        Returns:
            StrategyAction with instructions for full exit
        """
        pass
    
    @abstractmethod
    def exit_partial(self, equity_delta: float) -> StrategyAction:
        """
        Scale down position (small withdrawals or risk reduction).
        
        Args:
            equity_delta: Equity to remove from position
            
        Returns:
            StrategyAction with instructions for partial exit
        """
        pass
    
    @abstractmethod
    def sell_dust(self, dust_tokens: Dict[str, float]) -> StrategyAction:
        """
        Convert non-share-class tokens to share class currency.
        
        Args:
            dust_tokens: Dictionary of dust tokens and amounts
            
        Returns:
            StrategyAction with instructions for dust selling
        """
        pass
    
    def get_equity(self) -> float:
        """
        Get current equity in share class currency.
        
        Returns:
            Current equity (assets net of debt, excluding futures positions)
            Only includes tokens on actual wallets, not locked in smart contracts
        """
        try:
            # Get current position from position monitor
            current_position = self.position_monitor.get_current_position()
            
            # Calculate equity in share class currency
            equity = 0.0
            
            # Add share class currency balance
            share_class_balance = current_position.get(f'{self.share_class.lower()}_balance', 0.0)
            equity += share_class_balance
            
            # Add asset balance (converted to share class currency)
            asset_balance = current_position.get(f'{self.asset.lower()}_balance', 0.0)
            if asset_balance > 0:
                # Get current asset price in share class currency
                asset_price = self._get_asset_price()
                equity += asset_balance * asset_price
            
            # Add LST balances (converted to share class currency)
            lst_balances = current_position.get('lst_balances', {})
            for lst_token, balance in lst_balances.items():
                if balance > 0:
                    lst_price = self._get_lst_price(lst_token)
                    equity += balance * lst_price
            
            # Subtract debt (if any)
            debt_balance = current_position.get('debt_balance', 0.0)
            equity -= debt_balance
            
            return equity
            
        except Exception as e:
            logger.error(f"Error calculating equity: {e}")
            return 0.0
    
    def _get_asset_price(self) -> float:
        """Get current asset price in share class currency."""
        try:
            # This would typically get price from data provider
            # For now, return a placeholder
            if self.asset == 'ETH' and self.share_class == 'USDT':
                return 3000.0  # Placeholder ETH price
            elif self.asset == 'BTC' and self.share_class == 'USDT':
                return 60000.0  # Placeholder BTC price
            else:
                return 1.0  # Default
        except Exception as e:
            logger.error(f"Error getting asset price: {e}")
            return 1.0
    
    def _get_lst_price(self, lst_token: str) -> float:
        """Get current LST price in share class currency."""
        try:
            # This would typically get price from data provider
            # For now, return a placeholder
            if lst_token == 'weETH' and self.share_class == 'USDT':
                return 3000.0  # Placeholder weETH price
            elif lst_token == 'wstETH' and self.share_class == 'USDT':
                return 3000.0  # Placeholder wstETH price
            else:
                return 1.0  # Default
        except Exception as e:
            logger.error(f"Error getting LST price: {e}")
            return 1.0
    
    def should_sell_dust(self, dust_tokens: Dict[str, float]) -> bool:
        """
        Check if dust tokens exceed threshold.
        
        Args:
            dust_tokens: Dictionary of dust tokens and amounts
            
        Returns:
            True if dust should be sold, False otherwise
        """
        try:
            dust_value = 0.0
            for token, amount in dust_tokens.items():
                if amount > 0:
                    if token == self.share_class:
                        dust_value += amount
                    elif token == self.asset:
                        dust_value += amount * self._get_asset_price()
                    else:
                        # Assume LST token
                        dust_value += amount * self._get_lst_price(token)
            
            equity = self.get_equity()
            threshold = equity * self.dust_delta
            
            return dust_value > threshold
            
        except Exception as e:
            logger.error(f"Error checking dust threshold: {e}")
            return False
    
    def check_reserves(self) -> Dict[str, Any]:
        """
        Check if reserves are low and need replenishment.
        
        Returns:
            Dictionary with reserve status and recommendations
        """
        try:
            current_position = self.position_monitor.get_current_position()
            share_class_balance = current_position.get(f'{self.share_class.lower()}_balance', 0.0)
            equity = self.get_equity()
            
            reserve_ratio_actual = share_class_balance / equity if equity > 0 else 0.0
            reserve_low = reserve_ratio_actual < self.reserve_ratio
            
            return {
                'reserve_ratio_actual': reserve_ratio_actual,
                'reserve_ratio_target': self.reserve_ratio,
                'reserve_low': reserve_low,
                'share_class_balance': share_class_balance,
                'equity': equity,
                'recommendation': 'replenish_reserves' if reserve_low else 'maintain_reserves'
            }
            
        except Exception as e:
            logger.error(f"Error checking reserves: {e}")
            return {
                'reserve_ratio_actual': 0.0,
                'reserve_ratio_target': self.reserve_ratio,
                'reserve_low': True,
                'share_class_balance': 0.0,
                'equity': 0.0,
                'recommendation': 'error'
            }
    
    def trigger_tight_loop(self):
        """
        Trigger tight loop component chain after position updates.
        
        Position updates trigger sequential component chain:
        position_monitor → exposure_monitor → risk_monitor → pnl_monitor
        """
        try:
            if hasattr(self.event_engine, 'trigger_tight_loop'):
                self.event_engine.trigger_tight_loop()
            else:
                logger.warning("Event engine does not have trigger_tight_loop method")
        except Exception as e:
            logger.error(f"Error triggering tight loop: {e}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get strategy information and status.
        
        Returns:
            Dictionary with strategy information
        """
        try:
            equity = self.get_equity()
            reserves = self.check_reserves()
            
            return {
                'mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': equity,
                'reserves': reserves,
                'config': {
                    'reserve_ratio': self.reserve_ratio,
                    'dust_delta': self.dust_delta
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                'mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'reserves': {'reserve_low': True},
                'config': {
                    'reserve_ratio': self.reserve_ratio,
                    'dust_delta': self.dust_delta
                }
            }

