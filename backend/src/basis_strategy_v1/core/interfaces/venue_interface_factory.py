"""
Venue Interface Factory

Factory for creating venue interfaces based on execution mode and type.
Follows the architectural decision of seamless switching between modes.
"""

import logging
from typing import Dict, Any, Optional, List
from .base_execution_interface import BaseExecutionInterface
from .cex_execution_interface import CEXExecutionInterface
from .dex_execution_interface import DEXExecutionInterface
from .onchain_execution_interface import OnChainExecutionInterface
from .transfer_execution_interface import TransferExecutionInterface
from .base_position_interface import BasePositionInterface
from .cex_position_interface import CEXPositionInterface
from .onchain_position_interface import OnChainPositionInterface
from .transfer_position_interface import TransferPositionInterface

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)

# Error codes for Venue Interface Factory
ERROR_CODES = {
    'VIF-001': 'Venue interface creation failed',
    'VIF-002': 'Unsupported venue interface type',
    'VIF-003': 'Venue interface initialization failed',
    'VIF-004': 'Venue dependency injection failed',
    'VIF-005': 'Venue interface configuration invalid',
    'VIF-006': 'Venue interface connection failed'
}


class VenueInterfaceFactory(StandardizedLoggingMixin):
    """
    Factory for creating venue interfaces.
    
    Provides a centralized way to create and manage venue interfaces
    for both backtest and live modes.
    """
    
    def __init__(self):
        """Initialize the factory with health monitoring."""
        self.health_status = "healthy"
        self.error_count = 0
        self.created_interfaces = []
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.error_count += 1
        error_code = f"VIF_ERROR_{self.error_count:04d}"
        
        logger.error(f"Venue Interface Factory error {error_code}: {str(error)}", extra={
            'error_code': error_code,
            'context': context,
            'component': self.__class__.__name__
        })
        
        # Update health status based on error count
        if self.error_count > 10:
            self.health_status = "unhealthy"
        elif self.error_count > 5:
            self.health_status = "degraded"
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            'status': self.health_status,
            'error_count': self.error_count,
            'created_interfaces_count': len(self.created_interfaces),
            'component': self.__class__.__name__
        }
    
    def _process_config_driven_creation(self, interface_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process interface creation based on configuration settings."""
        try:
            # Apply config-driven logic
            if config.get('enable_validation', True):
                # Validate interface type based on config
                if self._validate_interface_type(interface_type, config):
                    return config
                else:
                    logger.warning(f"Interface type validation failed: {interface_type}")
                    return None
            else:
                return config
                
        except Exception as e:
            self._handle_error(e, f"config_driven_interface_creation")
            return None
    
    def _validate_interface_type(self, interface_type: str, config: Dict[str, Any]) -> bool:
        """Validate interface type based on configuration."""
        # Basic validation logic
        allowed_types = config.get('allowed_interface_types', ['cex', 'dex', 'onchain', 'transfer'])
        return interface_type.lower() in allowed_types
    
    @staticmethod
    def create_venue_interface(
        interface_type: str,
        execution_mode: str,
        config: Dict[str, Any],
        data_provider=None
    ) -> BaseExecutionInterface:
        """
        Create a venue interface.
        
        Args:
            interface_type: Type of interface ('cex', 'onchain', or 'transfer')
            execution_mode: Execution mode ('backtest' or 'live')
            config: Configuration dictionary
            
        Returns:
            Venue interface instance
            
        Raises:
            ValueError: If interface_type is not supported
        """
        if interface_type == 'cex':
            return CEXExecutionInterface(execution_mode, config)
        elif interface_type == 'dex':
            return DEXExecutionInterface(execution_mode, config)
        elif interface_type == 'onchain':
            return OnChainExecutionInterface(execution_mode, config, data_provider)
        elif interface_type == 'transfer':
            return TransferExecutionInterface(execution_mode, config)
        else:
            raise ValueError(f"Unsupported interface type: {interface_type}")
    
    @staticmethod
    def create_all_venue_interfaces(
        execution_mode: str,
        config: Dict[str, Any],
        data_provider=None
    ) -> Dict[str, BaseExecutionInterface]:
        """
        Create all venue interfaces for the given mode.
        
        Args:
            execution_mode: Execution mode ('backtest' or 'live')
            config: Configuration dictionary
            
        Returns:
            Dictionary of interface type to interface instance
        """
        interfaces = {}
        
        try:
            interfaces['cex'] = VenueInterfaceFactory.create_venue_interface(
                'cex', execution_mode, config, data_provider
            )
            logger.info(f"Created CEX venue interface in {execution_mode} mode")
        except Exception as e:
            logger.error(f"Failed to create CEX venue interface: {e}")
            interfaces['cex'] = None
        
        try:
            interfaces['dex'] = VenueInterfaceFactory.create_venue_interface(
                'dex', execution_mode, config, data_provider
            )
            logger.info(f"Created DEX venue interface in {execution_mode} mode")
        except Exception as e:
            logger.error(f"Failed to create DEX venue interface: {e}")
            interfaces['dex'] = None
        
        try:
            interfaces['onchain'] = VenueInterfaceFactory.create_venue_interface(
                'onchain', execution_mode, config, data_provider
            )
            logger.info(f"Created OnChain venue interface in {execution_mode} mode")
        except Exception as e:
            logger.error(f"Failed to create OnChain venue interface: {e}")
            interfaces['onchain'] = None
        
        try:
            interfaces['transfer'] = VenueInterfaceFactory.create_venue_interface(
                'transfer', execution_mode, config, data_provider
            )
            logger.info(f"Created Transfer venue interface in {execution_mode} mode")
        except Exception as e:
            logger.error(f"Failed to create Transfer venue interface: {e}")
            interfaces['transfer'] = None
        
        return interfaces
    
    @staticmethod
    def set_venue_dependencies(
        interfaces: Dict[str, BaseExecutionInterface],
        position_monitor,
        event_logger,
        data_provider
    ):
        """
        Set dependencies for all venue interfaces.
        
        Args:
            interfaces: Dictionary of interfaces
            position_monitor: Position monitor instance
            event_logger: Event logger instance
            data_provider: Data provider instance
        """
        for interface_type, interface in interfaces.items():
            if interface:
                interface.set_dependencies(position_monitor, event_logger, data_provider)
                logger.info(f"Set dependencies for {interface_type} venue interface")
        
        # Connect transfer interface with CEX and OnChain interfaces for live mode
        if interfaces.get('transfer') and hasattr(interfaces['transfer'], 'set_execution_interfaces'):
            interfaces['transfer'].set_execution_interfaces(
                interfaces.get('cex'),
                interfaces.get('onchain')
            )
            logger.info("Connected transfer interface with CEX and OnChain interfaces")
    
    @staticmethod
    def create_venue_position_interface(venue: str, execution_mode: str, config: Dict[str, Any]) -> BasePositionInterface:
        """
        Create position monitoring interface for a specific venue.
        
        Args:
            venue: Venue name ('binance', 'bybit', 'okx', 'aave', 'morpho', 'lido', 'etherfi', 'wallet')
            execution_mode: Execution mode ('backtest' or 'live')
            config: Configuration dictionary
            
        Returns:
            Position interface instance
            
        Raises:
            ValueError: If venue is not supported
        """
        try:
            if venue in ['binance', 'bybit', 'okx']:
                return CEXPositionInterface(venue, execution_mode, config)
            elif venue in ['aave', 'morpho', 'lido', 'etherfi']:
                return OnChainPositionInterface(venue, execution_mode, config)
            elif venue == 'wallet':
                return TransferPositionInterface(venue, execution_mode, config)
            else:
                raise ValueError(f"Unsupported venue for position monitoring: {venue}")
        except Exception as e:
            logger.error(f"Failed to create position interface for {venue}: {e}")
            raise
    
    @staticmethod
    def get_venue_position_interfaces(venues: List[str], execution_mode: str, config: Dict[str, Any]) -> Dict[str, BasePositionInterface]:
        """
        Create position monitoring interfaces for multiple venues.
        
        Args:
            venues: List of venue names
            execution_mode: Execution mode ('backtest' or 'live')
            config: Configuration dictionary
            
        Returns:
            Dictionary of venue name to position interface instance
        """
        position_interfaces = {}
        
        for venue in venues:
            try:
                position_interfaces[venue] = VenueInterfaceFactory.create_venue_position_interface(
                    venue, execution_mode, config
                )
                logger.info(f"Created position interface for {venue} in {execution_mode} mode")
            except Exception as e:
                logger.error(f"Failed to create position interface for {venue}: {e}")
                position_interfaces[venue] = None
        
        return position_interfaces
    
    @staticmethod
    def update_state(timestamp, trigger_source: str, **kwargs) -> None:
        """
        Update state for all venue interfaces.
        
        Args:
            timestamp: Current timestamp
            trigger_source: Source of the update trigger
            **kwargs: Additional update parameters
        """
        # Factory doesn't maintain state, but can be used to update all interfaces
        # This method is provided for consistency with the update_state pattern
        logger.debug(f"VenueInterfaceFactory.update_state called at {timestamp} from {trigger_source}")


# Legacy compatibility methods for backward transition
# These will be removed in a future version
class ExecutionInterfaceFactory(StandardizedLoggingMixin):
    """
    Legacy ExecutionInterfaceFactory - DEPRECATED
    
    Use VenueInterfaceFactory instead.
    This class is provided for backward compatibility only.
    """
    
    @staticmethod
    def __create_interface(interface_type: str, execution_mode: str, config: Dict[str, Any], data_provider=None):
        """Legacy method - use VenueInterfaceFactory.create_venue_interface() instead."""
        return VenueInterfaceFactory.create_venue_interface(interface_type, execution_mode, config, data_provider)
    
    @staticmethod
    def __create_all_interfaces(execution_mode: str, config: Dict[str, Any], data_provider=None):
        """Legacy method - use VenueInterfaceFactory.create_all_venue_interfaces() instead."""
        return VenueInterfaceFactory.create_all_venue_interfaces(execution_mode, config, data_provider)
    
    @staticmethod
    def __set_interface_dependencies(interfaces, position_monitor, event_logger, data_provider):
        """Legacy method - use VenueInterfaceFactory.set_venue_dependencies() instead."""
        return VenueInterfaceFactory.set_venue_dependencies(interfaces, position_monitor, event_logger, data_provider)
    
    @staticmethod
    def __create_position_interface(venue: str, execution_mode: str, config: Dict[str, Any]):
        """Legacy method - use VenueInterfaceFactory.create_venue_position_interface() instead."""
        return VenueInterfaceFactory.create_venue_position_interface(venue, execution_mode, config)
    
    @staticmethod
    def __get_position_interfaces(venues: List[str], execution_mode: str, config: Dict[str, Any]):
        """Legacy method - use VenueInterfaceFactory.get_venue_position_interfaces() instead."""
        return VenueInterfaceFactory.get_venue_position_interfaces(venues, execution_mode, config)