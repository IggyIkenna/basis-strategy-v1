"""
Venue Interface Manager

Manages venue interfaces and routes instructions to appropriate venues.
Implements instruction routing logic for 3 instruction types:
- wallet_transfer: Routes to transfer venue interface
- smart_contract_action: Routes to onchain venue interface  
- cex_trade: Routes to CEX venue interface

Reference: docs/specs/07_VENUE_INTERFACE_MANAGER.md
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - ADR-001 (Tight Loop Architecture)
"""

import logging
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..interfaces.venue_interface_factory import VenueInterfaceFactory
from ..interfaces.base_execution_interface import BaseExecutionInterface

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType
from ...core.errors.component_error import ComponentError

logger = logging.getLogger(__name__)

# Error codes for Venue Interface Manager
ERROR_CODES = {
    'VIM-001': 'Venue routing failed',
    'VIM-002': 'Unsupported instruction type',
    'VIM-003': 'Venue interface not available',
    'VIM-004': 'Credential validation failed',
    'VIM-005': 'Venue interface initialization failed',
    'VIM-006': 'Atomic chaining failed',
    'VIM-007': 'Venue instruction execution failed',
    'VIM-008': 'Position update failed',
    'VIM-009': 'Reconciliation failed',
    'VIM-010': 'Error handling failed',
    'VIM-011': 'Venue interface dependency injection failed',
    'VIM-012': 'Instruction validation failed',
    'VIM-013': 'Venue routing failed'
}


class VenueInterfaceManager(StandardizedLoggingMixin):
    """
    Manages venue interfaces and routes instructions to appropriate venues.
    
    Implements the tight loop architecture pattern:
    1. Route instruction to appropriate venue interface
    2. Execute instruction through venue interface
    3. Update position monitor
    4. Verify reconciliation
    5. Return execution result
    """
    
    def __init__(self, config: Dict[str, Any], data_provider, execution_mode: str):
        """
        Initialize venue interface manager.
        
        Args:
            config: Configuration dictionary (reference, never modified)
            data_provider: Data provider instance (reference)
            execution_mode: 'backtest' or 'live' (from BASIS_EXECUTION_MODE)
        """
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Health integration
        self.health_status = {
            'status': 'healthy',
            'last_check': datetime.now(),
            'error_count': 0,
            'success_count': 0
        }
        
        # Initialize venue credentials
        self._initialize_venue_credentials()
        
        # Initialize venue interfaces with credentials
        self.venue_interfaces = self._initialize_venue_interfaces()
        
        # Initialize component-specific state
        self.current_instruction = None
        self.routing_history = []
        self.instructions_routed = 0
        self.instructions_failed = 0
        self.instructions_succeeded = 0
        
        logger.info(f"VenueInterfaceManager initialized in {execution_mode} mode")
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.health_status['error_count'] += 1
        error_code = f"VIM_ERROR_{self.health_status['error_count']:04d}"
        
        logger.error(f"Venue Interface Manager error {error_code}: {str(error)}", extra={
            'error_code': error_code,
            'context': context,
            'execution_mode': self.execution_mode,
            'component': self.__class__.__name__
        })
        
        # Update health status based on error count
        if self.health_status['error_count'] > 10:
            self.health_status['status'] = "unhealthy"
        elif self.health_status['error_count'] > 5:
            self.health_status['status'] = "degraded"
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            'status': self.health_status['status'],
            'error_count': self.health_status['error_count'],
            'success_count': self.health_status['success_count'],
            'execution_mode': self.execution_mode,
            'instructions_routed': self.instructions_routed,
            'instructions_succeeded': self.instructions_succeeded,
            'component': self.__class__.__name__
        }
    
    def _process_config_driven_operations(self, operations: List[Dict]) -> List[Dict]:
        """Process operations based on configuration settings."""
        processed_operations = []
        for operation in operations:
            if self._validate_operation(operation):
                processed_operations.append(operation)
            else:
                self._handle_error(ValueError(f"Invalid operation: {operation}"), "config_driven_validation")
        return processed_operations
    
    def _validate_operation(self, operation: Dict) -> bool:
        """Validate operation against configuration."""
        required_fields = ['action', 'venue', 'instruction']
        return all(field in operation for field in required_fields)
    
    def _initialize_venue_credentials(self):
        """Initialize venue credentials based on environment."""
        self.venue_credentials = {}
        
        # Get environment from config or environment variable
        environment = self.config.get('environment', 'dev')
        
        # Initialize credentials for each venue type
        self.venue_credentials['cex'] = self._get_cex_credentials(environment)
        self.venue_credentials['onchain'] = self._get_onchain_credentials(environment)
        self.venue_credentials['transfer'] = self._get_transfer_credentials(environment)
        
        logger.info(f"Initialized venue credentials for environment: {environment}")
    
    def _get_cex_credentials(self, environment: str) -> Dict[str, Any]:
        """Get CEX credentials for the given environment."""
        credentials = {}
        
        # Get CEX venues from config
        cex_venues = self.config.get('component_config', {}).get('execution_interfaces', {}).get('cex_venues', [])
        
        for venue in cex_venues:
            venue_config = self.config.get('venue_config', {}).get(venue, {})
            credentials[venue] = {
                'api_key': venue_config.get(f'{environment}_api_key'),
                'secret_key': venue_config.get(f'{environment}_secret_key'),
                'testnet': venue_config.get('testnet', False)
            }
        
        return credentials
    
    def _get_onchain_credentials(self, environment: str) -> Dict[str, Any]:
        """Get OnChain credentials for the given environment."""
        credentials = {}
        
        # Get OnChain protocols from config
        onchain_protocols = self.config.get('component_config', {}).get('execution_interfaces', {}).get('onchain_protocols', [])
        
        for protocol in onchain_protocols:
            protocol_config = self.config.get('venue_config', {}).get(protocol, {})
            credentials[protocol] = {
                'rpc_url': protocol_config.get(f'{environment}_rpc_url'),
                'private_key': protocol_config.get(f'{environment}_private_key'),
                'contract_address': protocol_config.get('contract_address')
            }
        
        return credentials
    
    def _get_transfer_credentials(self, environment: str) -> Dict[str, Any]:
        """Get transfer credentials for the given environment."""
        credentials = {}
        
        # Get transfer types from config
        transfer_types = self.config.get('component_config', {}).get('execution_interfaces', {}).get('transfer_types', [])
        
        for transfer_type in transfer_types:
            transfer_config = self.config.get('venue_config', {}).get(transfer_type, {})
            credentials[transfer_type] = {
                'wallet_address': transfer_config.get(f'{environment}_wallet_address'),
                'private_key': transfer_config.get(f'{environment}_private_key')
            }
        
        return credentials
    
    def _initialize_venue_interfaces(self) -> Dict[str, BaseExecutionInterface]:
        """Initialize venue interfaces with credentials."""
        interfaces = {}
        
        try:
            # Create CEX venue interfaces
            for venue, credentials in self.venue_credentials['cex'].items():
                if credentials.get('api_key') and credentials.get('secret_key'):
                    interfaces[f'cex_{venue}'] = VenueInterfaceFactory.create_venue_interface(
                        'cex', self.execution_mode, self.config, self.data_provider
                    )
                    logger.info(f"Created CEX venue interface for {venue}")
        
        except Exception as e:
            logger.error(f"Failed to create CEX venue interfaces: {e}")
        
        try:
            # Create OnChain venue interfaces
            for protocol, credentials in self.venue_credentials['onchain'].items():
                if credentials.get('rpc_url') and credentials.get('private_key'):
                    interfaces[f'onchain_{protocol}'] = VenueInterfaceFactory.create_venue_interface(
                        'onchain', self.execution_mode, self.config, self.data_provider
                    )
                    logger.info(f"Created OnChain venue interface for {protocol}")
        
        except Exception as e:
            logger.error(f"Failed to create OnChain venue interfaces: {e}")
        
        try:
            # Create transfer venue interfaces
            for transfer_type, credentials in self.venue_credentials['transfer'].items():
                if credentials.get('wallet_address') and credentials.get('private_key'):
                    interfaces[f'transfer_{transfer_type}'] = VenueInterfaceFactory.create_venue_interface(
                        'transfer', self.execution_mode, self.config, self.data_provider
                    )
                    logger.info(f"Created transfer venue interface for {transfer_type}")
        
        except Exception as e:
            logger.error(f"Failed to create transfer venue interfaces: {e}")
        
        return interfaces
    
    def route_to_venue(self, timestamp: pd.Timestamp, instruction_block: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route instruction to appropriate venue interface.
        
        Args:
            timestamp: Current timestamp
            instruction_block: Instruction block containing instruction details
            
        Returns:
            Execution result dictionary
        """
        # Config-driven behavior
        routing_config = self.config.get('venue_interface_manager', {}).get('routing', {})
        enable_logging = routing_config.get('enable_logging', True)
        timeout_seconds = routing_config.get('timeout_seconds', 30)
        try:
            # Parse instruction type
            instruction_type = instruction_block.get('type')
            if not instruction_type:
                raise ValueError("Instruction type not specified")
            
            # Route to appropriate interface
            if instruction_type == 'wallet_transfer':
                return self._route_to_transfer(timestamp, instruction_block)
            elif instruction_type == 'smart_contract_action':
                return self._route_to_onchain(timestamp, instruction_block)
            elif instruction_type == 'cex_trade':
                return self._route_to_cex(timestamp, instruction_block)
            else:
                raise ValueError(f"Unknown instruction type: {instruction_type}")
        
        except Exception as e:
            self.instructions_failed += 1
            logger.error(f"Venue routing failed: {e}")
            raise
    
    def _route_to_transfer(self, timestamp: pd.Timestamp, instruction_block: Dict[str, Any]) -> Dict[str, Any]:
        """Route wallet transfer instruction to transfer interface."""
        try:
            # Get transfer type from instruction
            transfer_type = instruction_block.get('transfer_type', 'default')
            interface_key = f'transfer_{transfer_type}'
            
            # Get transfer interface
            transfer_interface = self.venue_interfaces.get(interface_key)
            if not transfer_interface:
                raise ValueError(f"Transfer interface not available for type: {transfer_type}")
            
            # Execute transfer
            result = transfer_interface.execute_transfer(instruction_block, {})
            
            # Update routing history
            self.routing_history.append({
                'timestamp': timestamp,
                'instruction_type': 'wallet_transfer',
                'transfer_type': transfer_type,
                'result': result
            })
            
            self.instructions_routed += 1
            self.instructions_succeeded += 1
            
            return result
        
        except Exception as e:
            self.instructions_failed += 1
            logger.error(f"Transfer routing failed: {e}")
            raise
    
    def _route_to_onchain(self, timestamp: pd.Timestamp, instruction_block: Dict[str, Any]) -> Dict[str, Any]:
        """Route smart contract action instruction to onchain interface."""
        try:
            # Get protocol from instruction
            protocol = instruction_block.get('protocol', 'default')
            interface_key = f'onchain_{protocol}'
            
            # Get onchain interface
            onchain_interface = self.venue_interfaces.get(interface_key)
            if not onchain_interface:
                raise ValueError(f"OnChain interface not available for protocol: {protocol}")
            
            # Execute smart contract action
            result = onchain_interface.execute_smart_contract_action(instruction_block, {})
            
            # Update routing history
            self.routing_history.append({
                'timestamp': timestamp,
                'instruction_type': 'smart_contract_action',
                'protocol': protocol,
                'result': result
            })
            
            self.instructions_routed += 1
            self.instructions_succeeded += 1
            
            return result
        
        except Exception as e:
            self.instructions_failed += 1
            logger.error(f"OnChain routing failed: {e}")
            raise
    
    def _route_to_cex(self, timestamp: pd.Timestamp, instruction_block: Dict[str, Any]) -> Dict[str, Any]:
        """Route CEX trade instruction to CEX interface."""
        try:
            # Get venue from instruction
            venue = instruction_block.get('venue', 'default')
            interface_key = f'cex_{venue}'
            
            # Get CEX interface
            cex_interface = self.venue_interfaces.get(interface_key)
            if not cex_interface:
                raise ValueError(f"CEX interface not available for venue: {venue}")
            
            # Execute trade
            result = cex_interface.execute_trade(instruction_block, {})
            
            # Update routing history
            self.routing_history.append({
                'timestamp': timestamp,
                'instruction_type': 'cex_trade',
                'venue': venue,
                'result': result
            })
            
            self.instructions_routed += 1
            self.instructions_succeeded += 1
            
            return result
        
        except Exception as e:
            self.instructions_failed += 1
            logger.error(f"CEX routing failed: {e}")
            raise
    
    def _get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        return {
            'instructions_routed': self.instructions_routed,
            'instructions_succeeded': self.instructions_succeeded,
            'instructions_failed': self.instructions_failed,
            'success_rate': self.instructions_succeeded / max(self.instructions_routed, 1),
            'available_interfaces': list(self.venue_interfaces.keys()),
            'routing_history_count': len(self.routing_history)
        }
    
    def _set_dependencies(self, position_monitor, event_logger, data_provider):
        """Set dependencies for all venue interfaces."""
        for interface in self.venue_interfaces.values():
            if hasattr(interface, 'set_dependencies'):
                interface.set_dependencies(position_monitor, event_logger, data_provider)
        
        logger.info("Set dependencies for all venue interfaces")
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, instruction_block: Optional[Dict] = None) -> Dict:
        """
        Main entry point for instruction routing.
        
        Args:
            timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
            trigger_source: 'venue_manager' | 'manual' | 'retry'
            instruction_block: Dict (optional) - instruction block from Venue Manager
            
        Returns:
            Dict: Execution deltas (net position changes)
        """
        try:
            logger.info(f"Venue Interface Manager: Updating state from {trigger_source}")
            
            if instruction_block:
                return self.route_to_venue(timestamp, instruction_block)
            else:
                return {'success': True, 'message': 'No instruction block to process'}
                
        except Exception as e:
            logger.error(f"Venue Interface Manager: Error in update_state: {e}")
            return {
                'success': False,
                'error': str(e),
                'trigger_source': trigger_source
            }


# Legacy compatibility class for backward transition
# This will be removed in a future version
class ExecutionInterfaceManager(StandardizedLoggingMixin):
    """
    Legacy ExecutionInterfaceManager - DEPRECATED
    
    Use VenueInterfaceManager instead.
    This class is provided for backward compatibility only.
    """
    
    def __init__(self, config: Dict[str, Any], data_provider, execution_mode: str):
        """Legacy constructor - use VenueInterfaceManager instead."""
        self._venue_manager = VenueInterfaceManager(config, data_provider, execution_mode)
        # Map legacy attributes
        self.execution_interfaces = self._venue_manager.venue_interfaces
        self.current_instruction = self._venue_manager.current_instruction
        self.routing_history = self._venue_manager.routing_history
        self.instructions_routed = self._venue_manager.instructions_routed
        self.instructions_failed = self._venue_manager.instructions_failed
        self.instructions_succeeded = self._venue_manager.instructions_succeeded
    
    def _route_instruction(self, timestamp: pd.Timestamp, instruction_block: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method - use VenueInterfaceManager.route_to_venue() instead."""
        return self._venue_manager.route_to_venue(timestamp, instruction_block)
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Legacy method - use VenueInterfaceManager.get_routing_stats() instead."""
        return self._venue_manager.get_routing_stats()
    
    def set_dependencies(self, position_monitor, event_logger, data_provider):
        """Legacy method - use VenueInterfaceManager.set_dependencies() instead."""
        return self._venue_manager.set_dependencies(position_monitor, event_logger, data_provider)
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, instruction_block: Optional[Dict] = None) -> Dict:
        """Legacy method - use VenueInterfaceManager.update_state() instead."""
        return self._venue_manager.update_state(timestamp, trigger_source, instruction_block)
    
    def _route_to_cex(self, instruction: Dict) -> Dict:
        """Route CEX trade instruction to appropriate CEX interface."""
        try:
            venue = instruction['venue']
            interface = self.cex_venue_interfaces.get(venue)
            
            if not interface:
                raise ValueError(f"CEX interface not found for venue: {venue}")
            
            if self.execution_mode == 'backtest':
                return interface.execute_backtest_trade(instruction)
            else:
                return interface.execute_live_trade(instruction)
                
        except Exception as e:
            logger.error(f"Failed to route CEX instruction: {e}")
            return {'success': False, 'error': str(e)}
    
    def _route_to_onchain(self, instruction: Dict) -> Dict:
        """Route smart contract action to appropriate OnChain interface."""
        try:
            protocol = instruction['protocol']
            interface = self.onchain_venue_interfaces.get(protocol)
            
            if not interface:
                raise ValueError(f"OnChain interface not found for protocol: {protocol}")
            
            if self.execution_mode == 'backtest':
                return interface.execute_backtest_action(instruction)
            else:
                return interface.execute_live_action(instruction)
                
        except Exception as e:
            logger.error(f"Failed to route OnChain instruction: {e}")
            return {'success': False, 'error': str(e)}
    
    def _route_to_transfer(self, instruction: Dict) -> Dict:
        """Route wallet transfer to appropriate interface."""
        try:
            from_venue = instruction['from_venue']
            to_venue = instruction['to_venue']
            
            # Determine which interface to use based on venues
            if from_venue in self.cex_venue_interfaces and to_venue in self.cex_venue_interfaces:
                # CEX to CEX transfer
                interface = self.cex_venue_interfaces[from_venue]
                return interface.execute_transfer(instruction)
            elif from_venue in self.onchain_venue_interfaces and to_venue in self.onchain_venue_interfaces:
                # OnChain to OnChain transfer
                interface = self.onchain_venue_interfaces[from_venue]
                return interface.execute_transfer(instruction)
            else:
                # Cross-venue transfer - use bridge interface
                bridge_interface = self.bridge_venue_interfaces.get('cross_venue')
                if bridge_interface:
                    return bridge_interface.execute_transfer(instruction)
                else:
                    raise ValueError(f"No bridge interface available for cross-venue transfer: {from_venue} -> {to_venue}")
                    
        except Exception as e:
            logger.error(f"Failed to route transfer instruction: {e}")
            self._handle_error('VIM-013', f"Failed to route transfer instruction: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_component_health(self) -> Dict[str, Any]:
        """
        Check component health status.
        
        Returns:
            Health status dictionary
        """
        try:
            current_time = datetime.now()
            
            # Check if component is responsive
            if (current_time - self.health_status['last_check']).seconds > 300:  # 5 minutes
                self.health_status['status'] = 'unhealthy'
                self.health_status['error'] = 'Component not responding'
            
            # Check error rate
            total_operations = self.health_status['error_count'] + self.health_status['success_count']
            if total_operations > 0:
                error_rate = self.health_status['error_count'] / total_operations
                if error_rate > 0.1:  # 10% error rate threshold
                    self.health_status['status'] = 'degraded'
                    self.health_status['error_rate'] = error_rate
            
            self.health_status['last_check'] = current_time
            
            return {
                'component': 'venue_interface_manager',
                'status': self.health_status['status'],
                'last_check': self.health_status['last_check'].isoformat(),
                'error_count': self.health_status['error_count'],
                'success_count': self.health_status['success_count'],
                'total_operations': total_operations
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'component': 'venue_interface_manager',
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _handle_error(self, error_code: str, error_message: str, details: Optional[Dict] = None):
        """
        Handle errors with structured error handling.
        
        Args:
            error_code: Error code from ERROR_CODES
            error_message: Error message
            details: Additional error details
        """
        try:
            # Update health status
            self.health_status['error_count'] += 1
            
            # Create structured error
            error = ComponentError(
                component='venue_interface_manager',
                error_code=error_code,
                message=error_message,
                details=details or {}
            )
            
            # Log structured error
            self.structured_logger.error(
                f"Venue Interface Manager Error: {error_code}",
                error_code=error_code,
                error_message=error_message,
                details=details,
                component='venue_interface_manager'
            )
            
            # Update health status if too many errors
            if self.health_status['error_count'] > 10:
                self.health_status['status'] = 'unhealthy'
            
        except Exception as e:
            logger.error(f"Failed to handle error: {e}")
    
    def _log_success(self, operation: str, details: Optional[Dict] = None):
        """
        Log successful operations.
        
        Args:
            operation: Operation name
            details: Operation details
        """
        try:
            # Update health status
            self.health_status['success_count'] += 1
            
            # Log success
            self.structured_logger.info(
                f"Venue Interface Manager Success: {operation}",
                operation=operation,
                details=details,
                component='venue_interface_manager'
            )
            
        except Exception as e:
            logger.error(f"Failed to log success: {e}")
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Get data using canonical data access pattern.
        
        Args:
            timestamp: Current timestamp
            
        Returns:
            Data dictionary
        """
        try:
            if self.data_provider:
                return self.data_provider.get_data(timestamp)
            else:
                return {}
        except Exception as e:
            self._handle_error('VIM-001', f"Failed to get data: {e}")
            return {}
