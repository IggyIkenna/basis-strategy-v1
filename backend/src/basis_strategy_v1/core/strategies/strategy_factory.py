"""
Strategy Factory

Factory for creating strategy instances based on mode.
Provides centralized strategy creation and management.

Reference: docs/MODES.md - Standardized Strategy Manager Architecture
"""

from typing import Dict, Any
import logging

# Import strategy implementations
from .pure_lending_strategy import PureLendingStrategy

logger = logging.getLogger(__name__)

class StrategyFactory:
    """Factory for creating strategy instances based on mode"""
    
    # Strategy mapping - populated with implemented strategies
    STRATEGY_MAP = {
        'pure_lending': PureLendingStrategy,
        # 'btc_basis': BTCBasisStrategy,
        # 'eth_basis': ETHBasisStrategy,
        # 'eth_staking_only': ETHStakingOnlyStrategy,
        # 'eth_leveraged': ETHLeveragedStrategy,
        # 'usdt_market_neutral_no_leverage': USDTMarketNeutralNoLeverageStrategy,
        # 'usdt_market_neutral': USDTMarketNeutralStrategy,
    }
    
    @classmethod
    def create_strategy(cls, mode: str, config: Dict[str, Any], risk_monitor, position_monitor, event_engine):
        """
        Create strategy instance based on mode.
        
        Args:
            mode: Strategy mode (e.g., 'pure_lending', 'btc_basis')
            config: Strategy configuration
            risk_monitor: Risk monitor instance
            position_monitor: Position monitor instance
            event_engine: Event engine instance
            
        Returns:
            Strategy instance
            
        Raises:
            ValueError: If strategy mode is not supported
        """
        strategy_class = cls.STRATEGY_MAP.get(mode)
        if not strategy_class:
            available_modes = list(cls.STRATEGY_MAP.keys())
            raise ValueError(f"Unknown strategy mode: {mode}. Available modes: {available_modes}")
        
        try:
            strategy = strategy_class(config, risk_monitor, position_monitor, event_engine)
            logger.info(f"Created {mode} strategy instance")
            return strategy
        except Exception as e:
            logger.error(f"Failed to create {mode} strategy: {e}")
            raise
    
    @classmethod
    def get_available_modes(cls) -> list:
        """
        Get list of available strategy modes.
        
        Returns:
            List of available strategy mode names
        """
        return list(cls.STRATEGY_MAP.keys())
    
    @classmethod
    def is_mode_supported(cls, mode: str) -> bool:
        """
        Check if a strategy mode is supported.
        
        Args:
            mode: Strategy mode to check
            
        Returns:
            True if mode is supported, False otherwise
        """
        return mode in cls.STRATEGY_MAP
    
    @classmethod
    def register_strategy(cls, mode: str, strategy_class):
        """
        Register a new strategy class.
        
        Args:
            mode: Strategy mode name
            strategy_class: Strategy class to register
        """
        cls.STRATEGY_MAP[mode] = strategy_class
        logger.info(f"Registered strategy mode: {mode}")
    
    @classmethod
    def unregister_strategy(cls, mode: str):
        """
        Unregister a strategy class.
        
        Args:
            mode: Strategy mode name to unregister
        """
        if mode in cls.STRATEGY_MAP:
            del cls.STRATEGY_MAP[mode]
            logger.info(f"Unregistered strategy mode: {mode}")
        else:
            logger.warning(f"Strategy mode {mode} not found for unregistration")
