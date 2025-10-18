"""
Strategy Factory

Factory for creating strategy instances based on mode with proper dependency injection
and tight loop architecture integration.

Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-007 (11 Component Architecture)
Reference: docs/STRATEGY_MODES.md - Standardized Strategy Manager Architecture
"""

from typing import Dict, Any, Optional
import logging

from .base_strategy_manager import BaseStrategyManager
from .pure_lending_usdt_strategy import PureLendingUSDTStrategy
from .pure_lending_eth_strategy import PureLendingETHStrategy
from .btc_basis_strategy import BTCBasisStrategy
from .eth_basis_strategy import ETHBasisStrategy
from .eth_staking_only_strategy import ETHStakingOnlyStrategy
from .eth_leveraged_strategy import ETHLeveragedStrategy
from .usdt_eth_staking_hedged_simple_strategy import USDTETHStakingHedgedSimpleStrategy
from .usdt_eth_staking_hedged_leveraged_strategy import USDTETHStakingHedgedLeveragedStrategy
from .ml_btc_directional_usdt_margin_strategy import MLBTCDirectionalUSDTMarginStrategy
from .ml_btc_directional_btc_margin_strategy import MLBTCDirectionalBTCMarginStrategy
import logging

logger = logging.getLogger(__name__)


class StrategyFactory:
    """Factory for creating strategy instances based on mode."""
    
    # Strategy class mapping - all 10 strategy modes
    STRATEGY_MAP = {
        'pure_lending_usdt': PureLendingUSDTStrategy,
        'pure_lending_eth': PureLendingETHStrategy,
        'btc_basis': BTCBasisStrategy,
        'eth_basis': ETHBasisStrategy,
        'eth_staking_only': ETHStakingOnlyStrategy,
        'eth_leveraged': ETHLeveragedStrategy,
        'usdt_eth_staking_hedged_simple': USDTETHStakingHedgedSimpleStrategy,
        'usdt_eth_staking_hedged_leveraged': USDTETHStakingHedgedLeveragedStrategy,
        'ml_btc_directional_usdt_margin': MLBTCDirectionalUSDTMarginStrategy,
        'ml_btc_directional_btc_margin': MLBTCDirectionalBTCMarginStrategy,
    }
    
    @classmethod
    def create_strategy(
        cls, 
        mode: str, 
        config: Dict[str, Any], 
        data_provider,
        exposure_monitor,
        position_monitor,
        risk_monitor,
        utility_manager=None,
        correlation_id: str = None,
        pid: int = None,
        log_dir = None
    ) -> BaseStrategyManager:
        """
        Create strategy instance based on mode.
        
        Args:
            mode: Strategy mode (e.g., 'pure_lending_usdt', 'btc_basis')
            config: Strategy configuration
            data_provider: Data provider instance for market data
            exposure_monitor: Exposure monitor instance for exposure data
            position_monitor: Position monitor instance for position data
            risk_monitor: Risk monitor instance for risk assessment
            utility_manager: Centralized utility manager for conversion rates
            correlation_id: Unique correlation ID for this run
            pid: Process ID
            log_dir: Log directory path
            
        Returns:
            Strategy manager instance
            
        Raises:
            ValueError: If strategy mode is not supported
        """
        try:
            # Check if strategy mode is supported
            if mode not in cls.STRATEGY_MAP:
                raise ValueError(f"Unknown strategy mode: {mode}")
            
            # Get strategy class
            strategy_class = cls.STRATEGY_MAP[mode]
            if strategy_class is None:
                raise ValueError(f"Strategy mode '{mode}' is not yet implemented")
            
            # Create strategy instance with all required dependencies
            strategy = strategy_class(
                config=config,
                data_provider=data_provider,
                exposure_monitor=exposure_monitor,
                position_monitor=position_monitor,
                risk_monitor=risk_monitor,
                utility_manager=utility_manager,
                correlation_id=correlation_id,
                pid=pid,
                log_dir=log_dir
            )
            
            logger.info(f"Strategy created successfully: {mode} -> {strategy_class.__name__}")
            
            return strategy
            
        except Exception as e:
            logger.error(f"Failed to create strategy {mode}: {e}")
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
        
        logger.info(f"Strategy registered: {mode} -> {strategy_class.__name__}")


def create_strategy(
    mode: str,
    config: Dict[str, Any],
    data_provider,
    exposure_monitor,
    position_monitor,
    risk_monitor,
    utility_manager=None,
    correlation_id: str = None,
    pid: int = None,
    log_dir = None
) -> BaseStrategyManager:
    """
    Convenience function to create strategy instance.
    
    Args:
        mode: Strategy mode
        config: Strategy configuration
        data_provider: Data provider instance for market data
        exposure_monitor: Exposure monitor instance for exposure data
        position_monitor: Position monitor instance for position data
        risk_monitor: Risk monitor instance for risk assessment
        utility_manager: Centralized utility manager for conversion rates
        correlation_id: Unique correlation ID for this run
        pid: Process ID
        log_dir: Log directory path
        
    Returns:
        Strategy manager instance
    """
    return StrategyFactory.create_strategy(
        mode=mode,
        config=config,
        data_provider=data_provider,
        exposure_monitor=exposure_monitor,
        position_monitor=position_monitor,
        risk_monitor=risk_monitor,
        utility_manager=utility_manager,
        correlation_id=correlation_id,
        pid=pid,
        log_dir=log_dir
    )