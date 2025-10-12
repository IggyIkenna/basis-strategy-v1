"""
Strategy Factory

Factory for creating strategy instances based on mode with proper dependency injection
and tight loop architecture integration.

Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-007 (11 Component Architecture)
Reference: docs/MODES.md - Standardized Strategy Manager Architecture
"""

from typing import Dict, Any, Optional
import logging

from .base_strategy_manager import BaseStrategyManager
from .pure_lending_strategy import PureLendingStrategy
from .btc_basis_strategy import BTCBasisStrategy
from .eth_basis_strategy import ETHBasisStrategy
from .eth_staking_only_strategy import ETHStakingOnlyStrategy
from .eth_leveraged_strategy import ETHLeveragedStrategy
from .usdt_market_neutral_no_leverage_strategy import USDTMarketNeutralNoLeverageStrategy
from .usdt_market_neutral_strategy import USDTMarketNeutralStrategy
from ...infrastructure.logging.structured_logger import get_strategy_manager_logger

logger = logging.getLogger(__name__)


class StrategyFactory:
    """Factory for creating strategy instances based on mode."""
    
    # Strategy class mapping - all strategies implemented
    STRATEGY_MAP = {
        'pure_lending': PureLendingStrategy,
        'btc_basis': BTCBasisStrategy,
        'eth_basis': ETHBasisStrategy,
        'eth_staking_only': ETHStakingOnlyStrategy,
        'eth_leveraged': ETHLeveragedStrategy,
        'usdt_market_neutral_no_leverage': USDTMarketNeutralNoLeverageStrategy,
        'usdt_market_neutral': USDTMarketNeutralStrategy,
        'ml_btc_directional': BaseStrategyManager,
        'ml_usdt_directional': BaseStrategyManager,
    }
    
    @classmethod
    def create_strategy(
        cls, 
        mode: str, 
        config: Dict[str, Any], 
        risk_monitor, 
        position_monitor, 
        event_engine,
        data_provider=None  # NEW: Optional data provider for ML strategies
    ) -> BaseStrategyManager:
        """
        Create strategy instance based on mode.
        
        Args:
            mode: Strategy mode (e.g., 'pure_lending', 'btc_basis')
            config: Strategy configuration
            risk_monitor: Risk monitor instance
            position_monitor: Position monitor instance
            event_engine: Event engine instance
            data_provider: Data provider instance (required for ML strategies)
            
        Returns:
            Strategy manager instance
            
        Raises:
            ValueError: If strategy mode is not supported
        """
        structured_logger = get_strategy_manager_logger()
        
        try:
            # Check if strategy mode is supported
            if mode not in cls.STRATEGY_MAP:
                raise ValueError(f"Unknown strategy mode: {mode}")
            
            # Get strategy class
            strategy_class = cls.STRATEGY_MAP[mode]
            if strategy_class is None:
                raise ValueError(f"Strategy mode '{mode}' is not yet implemented")
            
            # Create strategy instance
            if mode in ['ml_btc_directional', 'ml_usdt_directional']:
                # ML strategies require data provider
                if data_provider is None:
                    raise ValueError(f"Data provider required for ML strategy: {mode}")
                strategy = strategy_class(
                    config=config,
                    risk_monitor=risk_monitor,
                    position_monitor=position_monitor,
                    event_engine=event_engine,
                    data_provider=data_provider
                )
            else:
                # Traditional strategies don't need data provider
                strategy = strategy_class(
                    config=config,
                    risk_monitor=risk_monitor,
                    position_monitor=position_monitor,
                    event_engine=event_engine
                )
            
            structured_logger.info(
                f"Strategy created successfully: {mode}",
                event_type="strategy_creation",
                mode=mode,
                strategy_class=strategy_class.__name__
            )
            
            return strategy
            
        except Exception as e:
            structured_logger.error(
                f"Failed to create strategy: {e}",
                event_type="strategy_creation_error",
                mode=mode,
                error=str(e)
            )
            raise
    
    @classmethod
    def get_supported_modes(cls) -> list:
        """
        Get list of supported strategy modes.
        
        Returns:
            List of supported strategy modes
        """
        return [mode for mode, strategy_class in cls.STRATEGY_MAP.items() 
                if strategy_class is not None]
    
    @classmethod
    def is_mode_supported(cls, mode: str) -> bool:
        """
        Check if strategy mode is supported.
        
        Args:
            mode: Strategy mode to check
            
        Returns:
            True if mode is supported and implemented
        """
        return mode in cls.STRATEGY_MAP and cls.STRATEGY_MAP[mode] is not None
    
    @classmethod
    def register_strategy(cls, mode: str, strategy_class: type):
        """
        Register a new strategy class.
        
        Args:
            mode: Strategy mode name
            strategy_class: Strategy class to register
        """
        if not issubclass(strategy_class, BaseStrategyManager):
            raise ValueError(f"Strategy class must inherit from BaseStrategyManager")
        
        cls.STRATEGY_MAP[mode] = strategy_class
        
        structured_logger = get_strategy_manager_logger()
        structured_logger.info(
            f"Strategy registered: {mode}",
            event_type="strategy_registration",
            mode=mode,
            strategy_class=strategy_class.__name__
        )


def create_strategy(
    mode: str,
    config: Dict[str, Any],
    risk_monitor,
    position_monitor,
    event_engine,
    data_provider=None  # NEW: Optional data provider for ML strategies
) -> BaseStrategyManager:
    """
    Convenience function to create strategy instance.
    
    Args:
        mode: Strategy mode
        config: Strategy configuration
        risk_monitor: Risk monitor instance
        position_monitor: Position monitor instance
        event_engine: Event engine instance
        
    Returns:
        Strategy manager instance
    """
    return StrategyFactory.create_strategy(
        mode=mode,
        config=config,
        risk_monitor=risk_monitor,
        position_monitor=position_monitor,
        event_engine=event_engine,
        data_provider=data_provider
    )