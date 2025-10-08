"""
Execution Interface Factory

Factory for creating execution interfaces based on execution mode and type.
Follows the architectural decision of seamless switching between modes.
"""

import logging
from typing import Dict, Any, Optional
from .base_execution_interface import BaseExecutionInterface
from .cex_execution_interface import CEXExecutionInterface
from .onchain_execution_interface import OnChainExecutionInterface
from .transfer_execution_interface import TransferExecutionInterface

logger = logging.getLogger(__name__)

# Error codes for Execution Interface Factory
ERROR_CODES = {
    'FACTORY-001': 'Interface creation failed',
    'FACTORY-002': 'Unsupported interface type',
    'FACTORY-003': 'Interface initialization failed',
    'FACTORY-004': 'Dependency injection failed',
    'FACTORY-005': 'Interface configuration invalid',
    'FACTORY-006': 'Interface connection failed'
}


class ExecutionInterfaceFactory:
    """
    Factory for creating execution interfaces.
    
    Provides a centralized way to create and manage execution interfaces
    for both backtest and live modes.
    """
    
    @staticmethod
    def create_interface(
        interface_type: str,
        execution_mode: str,
        config: Dict[str, Any],
        data_provider=None
    ) -> BaseExecutionInterface:
        """
        Create an execution interface.
        
        Args:
            interface_type: Type of interface ('cex', 'onchain', or 'transfer')
            execution_mode: Execution mode ('backtest' or 'live')
            config: Configuration dictionary
            
        Returns:
            Execution interface instance
            
        Raises:
            ValueError: If interface_type is not supported
        """
        if interface_type == 'cex':
            return CEXExecutionInterface(execution_mode, config)
        elif interface_type == 'onchain':
            return OnChainExecutionInterface(execution_mode, config, data_provider)
        elif interface_type == 'transfer':
            return TransferExecutionInterface(execution_mode, config)
        else:
            raise ValueError(f"Unsupported interface type: {interface_type}")
    
    @staticmethod
    def create_all_interfaces(
        execution_mode: str,
        config: Dict[str, Any],
        data_provider=None
    ) -> Dict[str, BaseExecutionInterface]:
        """
        Create all execution interfaces for the given mode.
        
        Args:
            execution_mode: Execution mode ('backtest' or 'live')
            config: Configuration dictionary
            
        Returns:
            Dictionary of interface type to interface instance
        """
        interfaces = {}
        
        try:
            interfaces['cex'] = ExecutionInterfaceFactory.create_interface(
                'cex', execution_mode, config, data_provider
            )
            logger.info(f"Created CEX execution interface in {execution_mode} mode")
        except Exception as e:
            logger.error(f"Failed to create CEX execution interface: {e}")
            interfaces['cex'] = None
        
        try:
            interfaces['onchain'] = ExecutionInterfaceFactory.create_interface(
                'onchain', execution_mode, config, data_provider
            )
            logger.info(f"Created OnChain execution interface in {execution_mode} mode")
        except Exception as e:
            logger.error(f"Failed to create OnChain execution interface: {e}")
            interfaces['onchain'] = None
        
        try:
            interfaces['transfer'] = ExecutionInterfaceFactory.create_interface(
                'transfer', execution_mode, config, data_provider
            )
            logger.info(f"Created Transfer execution interface in {execution_mode} mode")
        except Exception as e:
            logger.error(f"Failed to create Transfer execution interface: {e}")
            interfaces['transfer'] = None
        
        return interfaces
    
    @staticmethod
    def set_interface_dependencies(
        interfaces: Dict[str, BaseExecutionInterface],
        position_monitor,
        event_logger,
        data_provider
    ):
        """
        Set dependencies for all interfaces.
        
        Args:
            interfaces: Dictionary of interfaces
            position_monitor: Position monitor instance
            event_logger: Event logger instance
            data_provider: Data provider instance
        """
        for interface_type, interface in interfaces.items():
            if interface:
                interface.set_dependencies(position_monitor, event_logger, data_provider)
                logger.info(f"Set dependencies for {interface_type} execution interface")
        
        # Connect transfer interface with CEX and OnChain interfaces for live mode
        if interfaces.get('transfer') and hasattr(interfaces['transfer'], 'set_execution_interfaces'):
            interfaces['transfer'].set_execution_interfaces(
                interfaces.get('cex'),
                interfaces.get('onchain')
            )
            logger.info("Connected transfer interface with CEX and OnChain interfaces")
