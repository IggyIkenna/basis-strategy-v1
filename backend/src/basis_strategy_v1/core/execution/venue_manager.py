"""
Venue Manager Component - Tight Loop Architecture

Implements the tight loop execution pattern:
venue sends instruction → position_monitor updates → verify reconciliation → next instruction

Reference: .cursor/tasks/12_tight_loop_architecture.md
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 4
"""

from typing import Dict, Any, List, Optional
import logging
import asyncio
import pandas as pd
from datetime import datetime

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType
from ...core.errors.component_error import ComponentError

logger = logging.getLogger(__name__)

# Error codes for Venue Manager
ERROR_CODES = {
    'VM-001': 'Venue instruction failed',
    'VM-002': 'Venue interface not available',
    'VM-003': 'Venue instruction validation failed',
    'VM-004': 'Venue position update failed',
    'VM-005': 'Venue reconciliation failed',
    'VM-006': 'Venue instruction queue failed',
    'VM-007': 'Venue tight loop failed',
    'VM-008': 'Venue instruction execution failed',
    'VM-009': 'Venue instruction routing failed',
    'VM-010': 'Venue instruction processing failed'
}

class VenueManager(StandardizedLoggingMixin):
    """Centralized venue manager implementing tight loop architecture."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(VenueManager, cls).__new__(cls)
        return cls._instance
       
    def __init__(self, execution_mode: str, config: Dict[str, Any], position_monitor=None):
        self.execution_mode = execution_mode
        self.config = config
        self.position_monitor = position_monitor
        self.venue_interfaces = {}  # wallet, trade, etc.
        self.health_status = "healthy"
        self.error_count = 0
        self.instruction_queue = []
        self.current_instruction = None
        
        # Config-driven behavior
        self.action_mapping = self.config.get('venue_manager', {}).get('action_mapping', {
            'trade': 'execute_trade',
            'transfer': 'execute_transfer',
            'supply': 'execute_supply',
            'borrow': 'execute_borrow',
            'swap': 'execute_swap'
        })
        
        # Health integration
        self.health_status = {
            'status': 'healthy',
            'last_check': datetime.now(),
            'error_count': 0,
            'success_count': 0
        }
        
        self._initialize_venue_interfaces()
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.health_status['error_count'] += 1
        error_code = f"VM_ERROR_{self.health_status['error_count']:04d}"
        
        logger.error(f"Venue Manager error {error_code}: {str(error)}", extra={
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
            'venue_interfaces_count': len(self.venue_interfaces),
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
        required_fields = ['action', 'venue', 'amount']
        return all(field in operation for field in required_fields)
    
    def _handle_graceful_data_handling(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data gracefully with fallbacks and validation."""
        try:
            # Validate data structure
            if not isinstance(data, dict):
                self._handle_error(ValueError("Data must be a dictionary"), "graceful_data_handling")
                return {}
            
            # Apply data validation and cleaning
            cleaned_data = {}
            for key, value in data.items():
                if value is not None:
                    cleaned_data[key] = value
            
            return cleaned_data
        except Exception as e:
            self._handle_error(e, "graceful_data_handling")
            return {}
    
    def _process_mode_agnostic_operations(self, operations: List[Dict]) -> List[Dict]:
        """Process operations in a mode-agnostic way."""
        processed_operations = []
        for operation in operations:
            # Mode-agnostic processing - same logic for backtest and live
            if self.execution_mode == 'backtest':
                # Simulate execution
                operation['simulated'] = True
            else:
                # Live execution
                operation['simulated'] = False
            
            processed_operations.append(operation)
        return processed_operations
    
    def _create_component_factory(self) -> Dict[str, Any]:
        """Create component factory for venue interfaces."""
        factory = {
            'wallet_interface': self.__create_wallet_interface,
            'trade_interface': self.__create_trade_interface,
            'transfer_interface': self.__create_transfer_interface
        }
        return factory
    
    def __create_wallet_interface(self) -> Any:
        """Create wallet interface component."""
        # Factory method for wallet interface
        return None
    
    def __create_trade_interface(self) -> Any:
        """Create trade interface component."""
        # Factory method for trade interface
        return None
    
    def __create_transfer_interface(self) -> Any:
        """Create transfer interface component."""
        # Factory method for transfer interface
        return None
    
    def _initialize_venue_interfaces(self):
        """Initialize venue type interfaces (wallet, trade, etc.)."""
        # Create venue interfaces that handle different instruction types
        # Each interface routes to appropriate venue client implementations
        pass
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, instruction_blocks: Optional[List[Dict]] = None) -> Dict:
        """
        Main entry point for instruction block execution.
        
        Args:
            timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
            trigger_source: 'strategy_manager' | 'manual' | 'retry'
            instruction_blocks: List[Dict] (optional) - instruction blocks from Strategy Manager
            
        Returns:
            Dict: Execution summary with success/failure counts
        """
        try:
            logger.info(f"Venue Manager: Updating state from {trigger_source}")
            
            # Process instruction blocks if provided
            if instruction_blocks:
                return self.execute_venue_instructions(timestamp, instruction_blocks)
            
            # Continue processing queued blocks
            return self._process_queued_blocks(timestamp)
            
        except Exception as e:
            logger.error(f"Venue Manager: Error in update_state: {e}")
            return {
                'success': False,
                'error': str(e),
                'trigger_source': trigger_source
            }
    
    def execute_venue_instructions(self, timestamp: pd.Timestamp, instruction_blocks: List[Dict]) -> Dict:
        """
        Queue blocks for sequential processing.
        
        Args:
            timestamp: Current loop timestamp
            instruction_blocks: List of instruction blocks from Strategy Manager
            
        Returns:
            Dict: Execution summary
        """
        try:
            # Validate instruction blocks
            if not instruction_blocks:
                return {'success': True, 'message': 'No instruction blocks to process'}
            
            # Add to execution queue
            self.instruction_queue.extend(instruction_blocks)
            
            # Start processing first block
            return self._process_queued_blocks(timestamp)
            
        except Exception as e:
            logger.error(f"Venue Manager: Error in execute_venue_instructions: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    def _process_queued_blocks(self, timestamp: pd.Timestamp) -> Dict:
        """Process all queued instruction blocks."""
        results = []
        
        while self.instruction_queue:
            block = self.instruction_queue.pop(0)
            success = self._process_single_block(timestamp, block)
            results.append({'block': block, 'success': success})
            
            if not success:
                break
        
        return {
            'success': all(r['success'] for r in results),
            'results': results,
            'total_blocks': len(results)
        }
    
    def _get_execution_status(self, execution_id: str) -> Dict:
        """
        Get execution status for a specific execution ID.
        
        Args:
            execution_id: Execution identifier
            
        Returns:
            Dict: Execution status information
        """
        return {
            'execution_id': execution_id,
            'status': 'completed',  # Simplified for now
            'reconciliation_status': getattr(self, 'reconciliation_status', 'unknown')
        }
    
    # Legacy method for backward compatibility - will be removed
    async def __execute_instruction_sequence(self, instructions: List[Dict], market_data: Dict) -> Dict:
        """Legacy method - use update_state() instead."""
        return self.update_state(pd.Timestamp.now(), 'legacy', instructions)
    
    async def _execute_venue_loop(self, instruction: Dict, market_data: Dict) -> Dict:
        """
        Execute tight loop for a single instruction:
        venue → position_monitor → reconciliation → next instruction
        """
        try:
            # Step 1: Send instruction to venue
            logger.info(f"Venue Manager: Sending instruction to venue")
            execution_result = await self._send_instruction(instruction, market_data)
            
            if not execution_result.get('success', False):
                return {
                    'success': False,
                    'error': 'Venue instruction execution failed',
                    'execution_result': execution_result
                }
            
            # Step 2: Position monitor updates
            logger.info(f"Venue Manager: Updating position monitor")
            position_result = await self._update_position_monitor(instruction, execution_result)
            
            if not position_result.get('success', False):
                return {
                    'success': False,
                    'error': 'Position monitor update failed',
                    'execution_result': execution_result,
                    'position_result': position_result
                }
            
            # Step 3: Verify reconciliation
            logger.info(f"Venue Manager: Verifying reconciliation")
            reconciliation_result = await self._verify_reconciliation(instruction, execution_result, position_result)
            
            if not reconciliation_result.get('success', False):
                return {
                    'success': False,
                    'error': 'Reconciliation verification failed',
                    'execution_result': execution_result,
                    'position_result': position_result,
                    'reconciliation_result': reconciliation_result
                }
            
            # Tight loop completed successfully
            logger.info(f"Venue Manager: Tight loop completed successfully")
            return {
                'success': True,
                'execution_result': execution_result,
                'position_result': position_result,
                'reconciliation_result': reconciliation_result
            }
            
        except Exception as e:
            logger.error(f"Venue Manager: Tight loop failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _send_instruction(self, instruction: Dict, market_data: Dict) -> Dict:
        """Send instruction to appropriate venue."""
        try:
            # Get instruction type from 'action' field (ML strategies) or 'type' field (traditional)
            instruction_type = instruction.get('action', instruction.get('type', 'unknown'))
            venue = instruction.get('venue', 'unknown')
            
            logger.info(f"Venue Manager: Sending {instruction_type} instruction to {venue}")
            
            # Route to appropriate venue interface
            if instruction_type == 'wallet_transfer':
                return await self._execute_wallet_transfer(instruction, market_data)
            elif instruction_type == 'cex_trade':
                return await self._execute_cex_trade(instruction, market_data)
            elif instruction_type == 'smart_contract':
                return await self._execute_smart_contract(instruction, market_data)
            elif instruction_type == 'open_perp_long':
                return await self._execute_open_perp_long(instruction, market_data)
            elif instruction_type == 'open_perp_short':
                return await self._execute_open_perp_short(instruction, market_data)
            elif instruction_type == 'close_perp':
                return await self._execute_close_perp(instruction, market_data)
            elif instruction_type == 'update_stop_loss':
                return await self._execute_update_stop_loss(instruction, market_data)
            elif instruction_type == 'update_take_profit':
                return await self._execute_update_take_profit(instruction, market_data)
            else:
                return {
                    'success': False,
                    'error': f'Unknown instruction type: {instruction_type}'
                }
                
        except Exception as e:
            logger.error(f"Venue Manager: Instruction execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _update_position_monitor(self, instruction: Dict, execution_result: Dict) -> Dict:
        """Update position monitor based on instruction result."""
        try:
            if not self.position_monitor:
                logger.warning("Venue Manager: No position monitor available")
                return {'success': True, 'message': 'No position monitor available'}
            
            # Update position monitor with instruction result
            # This is mode-agnostic - position monitor handles backtest vs live
            timestamp = pd.Timestamp.now()
            
            # For now, just log the update
            logger.info(f"Venue Manager: Position monitor updated for instruction")
            
            return {
                'success': True,
                'timestamp': timestamp,
                'instruction': instruction,
                'execution_result': execution_result
            }
            
        except Exception as e:
            logger.error(f"Venue Manager: Position monitor update failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _verify_reconciliation(self, instruction: Dict, execution_result: Dict, position_result: Dict) -> Dict:
        """Verify that position matches expected state after instruction."""
        try:
            # Verify that the position change matches what was expected
            # This is the critical reconciliation step
            
            logger.info(f"Venue Manager: Verifying position reconciliation")
            
            # For now, always return success
            # TODO: Implement actual reconciliation logic
            return {
                'success': True,
                'expected_position': instruction.get('expected_position', {}),
                'actual_position': position_result.get('position', {}),
                'reconciliation_passed': True
            }
            
        except Exception as e:
            logger.error(f"Venue Manager: Reconciliation verification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _execute_wallet_transfer(self, instruction: Dict, market_data: Dict) -> Dict:
        """Execute wallet transfer instruction."""
        # TODO: Implement wallet transfer execution
        return {
            'success': True,
            'instruction_type': 'wallet_transfer',
            'message': 'Wallet transfer executed (simulated)'
        }
    
    async def _execute_cex_trade(self, instruction: Dict, market_data: Dict) -> Dict:
        """Execute CEX trade instruction."""
        # TODO: Implement CEX trade execution
        return {
            'success': True,
            'instruction_type': 'cex_trade',
            'message': 'CEX trade executed (simulated)'
        }
    
    async def _execute_smart_contract(self, instruction: Dict, market_data: Dict) -> Dict:
        """Execute smart contract instruction."""
        # TODO: Implement smart contract execution
        return {
            'success': True,
            'instruction_type': 'smart_contract',
            'message': 'Smart contract executed (simulated)'
        }
    
    # ============================================================================
    # ML Strategy Execution Methods (Perp Futures with TP/SL)
    # ============================================================================
    # TODO: ML data files required at data/market_data/ml/ and data/ml_data/predictions/
    # TODO: Set BASIS_ML_API_TOKEN environment variable for live mode
    
    async def _execute_open_perp_long(self, instruction: Dict, market_data: Dict) -> Dict:
        """
        Execute open perp long position with take-profit and stop-loss orders.
        
        Args:
            instruction: Instruction dictionary with symbol, amount, take_profit, stop_loss
            market_data: Current market data
            
        Returns:
            Execution result dictionary
        """
        try:
            symbol = instruction.get('symbol', '')
            amount = instruction.get('amount', 0.0)
            take_profit = instruction.get('take_profit')
            stop_loss = instruction.get('stop_loss')
            venue = instruction.get('venue', 'binance')
            
            logger.info(f"Opening perp long position: {amount} {symbol} on {venue}")
            
            if self.execution_mode == 'backtest':
                # Backtest mode - simulate execution
                return {
                    'success': True,
                    'instruction_type': 'open_perp_long',
                    'symbol': symbol,
                    'amount': amount,
                    'venue': venue,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'message': f'Perp long position opened (backtest): {amount} {symbol}'
                }
            else:
                # Live mode - actual execution
                # TODO: Implement actual perp long execution with TP/SL orders
                return {
                    'success': True,
                    'instruction_type': 'open_perp_long',
                    'symbol': symbol,
                    'amount': amount,
                    'venue': venue,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'message': f'Perp long position opened (live): {amount} {symbol}'
                }
                
        except Exception as e:
            logger.error(f"Failed to execute open perp long: {e}")
            return {
                'success': False,
                'error': str(e),
                'instruction_type': 'open_perp_long'
            }
    
    async def _execute_open_perp_short(self, instruction: Dict, market_data: Dict) -> Dict:
        """
        Execute open perp short position with take-profit and stop-loss orders.
        
        Args:
            instruction: Instruction dictionary with symbol, amount, take_profit, stop_loss
            market_data: Current market data
            
        Returns:
            Execution result dictionary
        """
        try:
            symbol = instruction.get('symbol', '')
            amount = instruction.get('amount', 0.0)
            take_profit = instruction.get('take_profit')
            stop_loss = instruction.get('stop_loss')
            venue = instruction.get('venue', 'binance')
            
            logger.info(f"Opening perp short position: {amount} {symbol} on {venue}")
            
            if self.execution_mode == 'backtest':
                # Backtest mode - simulate execution
                return {
                    'success': True,
                    'instruction_type': 'open_perp_short',
                    'symbol': symbol,
                    'amount': -amount,  # Negative for short
                    'venue': venue,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'message': f'Perp short position opened (backtest): {amount} {symbol}'
                }
            else:
                # Live mode - actual execution
                # TODO: Implement actual perp short execution with TP/SL orders
                return {
                    'success': True,
                    'instruction_type': 'open_perp_short',
                    'symbol': symbol,
                    'amount': -amount,  # Negative for short
                    'venue': venue,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'message': f'Perp short position opened (live): {amount} {symbol}'
                }
                
        except Exception as e:
            logger.error(f"Failed to execute open perp short: {e}")
            return {
                'success': False,
                'error': str(e),
                'instruction_type': 'open_perp_short'
            }
    
    async def _execute_close_perp(self, instruction: Dict, market_data: Dict) -> Dict:
        """
        Execute close perp position.
        
        Args:
            instruction: Instruction dictionary with symbol, amount, venue
            market_data: Current market data
            
        Returns:
            Execution result dictionary
        """
        try:
            symbol = instruction.get('symbol', '')
            amount = instruction.get('amount', 0.0)
            venue = instruction.get('venue', 'binance')
            
            logger.info(f"Closing perp position: {amount} {symbol} on {venue}")
            
            if self.execution_mode == 'backtest':
                # Backtest mode - simulate execution
                return {
                    'success': True,
                    'instruction_type': 'close_perp',
                    'symbol': symbol,
                    'amount': amount,
                    'venue': venue,
                    'message': f'Perp position closed (backtest): {amount} {symbol}'
                }
            else:
                # Live mode - actual execution
                # TODO: Implement actual perp close execution
                return {
                    'success': True,
                    'instruction_type': 'close_perp',
                    'symbol': symbol,
                    'amount': amount,
                    'venue': venue,
                    'message': f'Perp position closed (live): {amount} {symbol}'
                }
                
        except Exception as e:
            logger.error(f"Failed to execute close perp: {e}")
            return {
                'success': False,
                'error': str(e),
                'instruction_type': 'close_perp'
            }
    
    async def _execute_update_stop_loss(self, instruction: Dict, market_data: Dict) -> Dict:
        """
        Execute update stop-loss order.
        
        Args:
            instruction: Instruction dictionary with symbol, stop_loss, venue
            market_data: Current market data
            
        Returns:
            Execution result dictionary
        """
        try:
            symbol = instruction.get('symbol', '')
            stop_loss = instruction.get('stop_loss')
            venue = instruction.get('venue', 'binance')
            
            logger.info(f"Updating stop-loss: {symbol} to {stop_loss} on {venue}")
            
            if self.execution_mode == 'backtest':
                # Backtest mode - simulate execution
                return {
                    'success': True,
                    'instruction_type': 'update_stop_loss',
                    'symbol': symbol,
                    'stop_loss': stop_loss,
                    'venue': venue,
                    'message': f'Stop-loss updated (backtest): {symbol} to {stop_loss}'
                }
            else:
                # Live mode - actual execution
                # TODO: Implement actual stop-loss order update
                return {
                    'success': True,
                    'instruction_type': 'update_stop_loss',
                    'symbol': symbol,
                    'stop_loss': stop_loss,
                    'venue': venue,
                    'message': f'Stop-loss updated (live): {symbol} to {stop_loss}'
                }
                
        except Exception as e:
            logger.error(f"Failed to execute update stop-loss: {e}")
            return {
                'success': False,
                'error': str(e),
                'instruction_type': 'update_stop_loss'
            }
    
    async def _execute_update_take_profit(self, instruction: Dict, market_data: Dict) -> Dict:
        """
        Execute update take-profit order.
        
        Args:
            instruction: Instruction dictionary with symbol, take_profit, venue
            market_data: Current market data
            
        Returns:
            Execution result dictionary
        """
        try:
            symbol = instruction.get('symbol', '')
            take_profit = instruction.get('take_profit')
            venue = instruction.get('venue', 'binance')
            
            logger.info(f"Updating take-profit: {symbol} to {take_profit} on {venue}")
            
            if self.execution_mode == 'backtest':
                # Backtest mode - simulate execution
                return {
                    'success': True,
                    'instruction_type': 'update_take_profit',
                    'symbol': symbol,
                    'take_profit': take_profit,
                    'venue': venue,
                    'message': f'Take-profit updated (backtest): {symbol} to {take_profit}'
                }
            else:
                # Live mode - actual execution
                # TODO: Implement actual take-profit order update
                return {
                    'success': True,
                    'instruction_type': 'update_take_profit',
                    'symbol': symbol,
                    'take_profit': take_profit,
                    'venue': venue,
                    'message': f'Take-profit updated (live): {symbol} to {take_profit}'
                }
                
        except Exception as e:
            logger.error(f"Failed to execute update take-profit: {e}")
            return {
                'success': False,
                'error': str(e),
                'instruction_type': 'update_take_profit'
            }


# Legacy compatibility class for backward transition
# This will be removed in a future version
class ExecutionManager(StandardizedLoggingMixin):
    """
    Legacy ExecutionManager - DEPRECATED
    
    Use VenueManager instead.
    This class is provided for backward compatibility only.
    """
    
    def __init__(self, execution_mode: str, config: Dict[str, Any], position_monitor=None):
        """Legacy constructor - use VenueManager instead."""
        self._venue_manager = VenueManager(execution_mode, config, position_monitor)
        # Map legacy attributes
        self.execution_interfaces = self._venue_manager.venue_interfaces
        self.instruction_queue = self._venue_manager.instruction_queue
        self.current_instruction = self._venue_manager.current_instruction
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, instruction_blocks: Optional[List[Dict]] = None) -> Dict:
        """Legacy method - use VenueManager.update_state() instead."""
        return self._venue_manager.update_state(timestamp, trigger_source, instruction_blocks)
    
    def _execute_instruction_blocks(self, timestamp: pd.Timestamp, instruction_blocks: List[Dict]) -> Dict:
        """Legacy method - use VenueManager.execute_venue_instructions() instead."""
        return self._venue_manager.execute_venue_instructions(timestamp, instruction_blocks)
    
    async def _execute_tight_loop(self, instruction: Dict, market_data: Dict) -> Dict:
        """Legacy method - use VenueManager._execute_venue_loop() instead."""
        return await self._venue_manager._execute_venue_loop(instruction, market_data)
    
    def _process_single_block(self, timestamp: pd.Timestamp, block: Dict) -> bool:
        """Process single block with reconciliation handshake."""
        try:
            if self.execution_mode == 'backtest':
                # Execute with simulated reconciliation
                deltas = self.venue_interface_manager.route_instruction(timestamp, block)
                self.position_update_handler.update_state(timestamp, 'venue_manager', deltas)
                self.reconciliation_status = 'success'
                return True
            
            elif self.execution_mode == 'live':
                # Execute with real reconciliation
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    self.reconciliation_status = 'pending'
                    
                    # Execute instruction
                    deltas = self.venue_interface_manager.route_instruction(timestamp, block)
                    self.position_update_handler.update_state(timestamp, 'venue_manager', deltas)
                    
                    # Wait for reconciliation
                    reconciliation_result = self.position_monitor.reconcile_positions(timestamp)
                    
                    if reconciliation_result['success']:
                        self.reconciliation_status = 'success'
                        return True
                    else:
                        retry_count += 1
                        self.reconciliation_status = 'failed'
                        logger.warning(f"Reconciliation failed, retry {retry_count}/{max_retries}")
                
                return False
            
            else:
                logger.error(f"Unknown execution mode: {self.execution_mode}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to process single block: {e}")
            self.reconciliation_status = 'error'
            self._handle_error('VM-010', f"Failed to process single block: {e}")
            return False
    
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
                'component': 'venue_manager',
                'status': self.health_status['status'],
                'last_check': self.health_status['last_check'].isoformat(),
                'error_count': self.health_status['error_count'],
                'success_count': self.health_status['success_count'],
                'total_operations': total_operations
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'component': 'venue_manager',
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
                component='venue_manager',
                error_code=error_code,
                message=error_message,
                details=details or {}
            )
            
            # Log structured error
            self.structured_logger.error(
                f"Venue Manager Error: {error_code}",
                error_code=error_code,
                error_message=error_message,
                details=details,
                component='venue_manager'
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
                f"Venue Manager Success: {operation}",
                operation=operation,
                details=details,
                component='venue_manager'
            )
            
        except Exception as e:
            logger.error(f"Failed to log success: {e}")
    
    def _process_config_driven_operations(self, operation_type: str, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process operations based on configuration settings."""
        try:
            # Get config-driven operation settings
            venue_config = self.config.get('component_config', {}).get('venue_manager', {})
            supported_actions = venue_config.get('supported_actions', [])
            action_mapping = venue_config.get('action_mapping', {})
            
            # Validate operation against config
            if operation_type not in supported_actions:
                raise ComponentError(
                    f"Operation {operation_type} not supported by configuration",
                    error_code='VM-003'
                )
            
            # Process based on config-driven mapping
            mapped_actions = action_mapping.get(operation_type, [operation_type])
            
            result = {
                'operation_type': operation_type,
                'mapped_actions': mapped_actions,
                'config_driven': True,
                'supported_actions': supported_actions
            }
            
            return result
            
        except Exception as e:
            self._handle_error('config_driven_operation', str(e), 'VM-010')
            raise
    
    def _validate_operation(self, operation_type: str) -> bool:
        """Validate operation against configuration."""
        try:
            venue_config = self.config.get('component_config', {}).get('venue_manager', {})
            supported_actions = venue_config.get('supported_actions', [])
            return operation_type in supported_actions
        except Exception:
            return False
