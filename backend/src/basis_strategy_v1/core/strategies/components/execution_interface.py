"""
Mode-Agnostic Execution Interface

Provides mode-agnostic execution interface that works for both backtest and live modes.
Manages execution across all venues and provides generic execution logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/10_EXECUTION_INTERFACE.md - Mode-agnostic execution management
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class ExecutionInterface:
    """Mode-agnostic execution interface that works for both backtest and live modes"""
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize execution interface.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        
        # Execution tracking
        self.execution_history = []
        self.active_orders = {}
        
        logger.info("ExecutionInterface initialized (mode-agnostic)")
    
    def execute_trade(self, trade_instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Execute trade regardless of mode (backtest or live).
        
        Args:
            trade_instruction: Trade instruction dictionary
            timestamp: Current timestamp
            
        Returns:
            Dictionary with execution result
        """
        try:
            # Validate trade instruction
            validation_result = self._validate_trade_instruction(trade_instruction)
            if not validation_result['valid']:
                return {
                    'status': 'failed',
                    'error': validation_result['error'],
                    'timestamp': timestamp
                }
            
            # Execute trade based on type
            trade_type = trade_instruction.get('type')
            
            if trade_type == 'cex_trade':
                return self._execute_cex_trade(trade_instruction, timestamp)
            elif trade_type == 'onchain_supply':
                return self._execute_onchain_supply(trade_instruction, timestamp)
            elif trade_type == 'onchain_withdraw':
                return self._execute_onchain_withdraw(trade_instruction, timestamp)
            elif trade_type == 'onchain_borrow':
                return self._execute_onchain_borrow(trade_instruction, timestamp)
            elif trade_type == 'onchain_repay':
                return self._execute_onchain_repay(trade_instruction, timestamp)
            elif trade_type == 'onchain_stake':
                return self._execute_onchain_stake(trade_instruction, timestamp)
            elif trade_type == 'onchain_unstake':
                return self._execute_onchain_unstake(trade_instruction, timestamp)
            else:
                return {
                    'status': 'failed',
                    'error': f"Unsupported trade type: {trade_type}",
                    'timestamp': timestamp
                }
                
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def execute_atomic_transaction(self, transaction_instructions: List[Dict[str, Any]], 
                                 timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Execute atomic transaction regardless of mode (backtest or live).
        
        Args:
            transaction_instructions: List of transaction instructions
            timestamp: Current timestamp
            
        Returns:
            Dictionary with execution result
        """
        try:
            # Validate transaction instructions
            validation_result = self._validate_transaction_instructions(transaction_instructions)
            if not validation_result['valid']:
                return {
                    'status': 'failed',
                    'error': validation_result['error'],
                    'timestamp': timestamp
                }
            
            # Execute atomic transaction
            execution_result = self._execute_atomic_transaction_internal(
                transaction_instructions, timestamp
            )
            
            # Add to execution history
            self.execution_history.append({
                'type': 'atomic_transaction',
                'instructions': transaction_instructions,
                'result': execution_result,
                'timestamp': timestamp
            })
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Error executing atomic transaction: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def execute_sequential_operations(self, operation_instructions: List[Dict[str, Any]], 
                                    timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Execute sequential operations regardless of mode (backtest or live).
        
        Args:
            operation_instructions: List of operation instructions
            timestamp: Current timestamp
            
        Returns:
            Dictionary with execution result
        """
        try:
            # Validate operation instructions
            validation_result = self._validate_operation_instructions(operation_instructions)
            if not validation_result['valid']:
                return {
                    'status': 'failed',
                    'error': validation_result['error'],
                    'timestamp': timestamp
                }
            
            # Execute sequential operations
            execution_result = self._execute_sequential_operations_internal(
                operation_instructions, timestamp
            )
            
            # Add to execution history
            self.execution_history.append({
                'type': 'sequential_operations',
                'instructions': operation_instructions,
                'result': execution_result,
                'timestamp': timestamp
            })
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Error executing sequential operations: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def get_execution_history(self) -> Dict[str, Any]:
        """Get execution history."""
        try:
            return {
                'execution_history': self.execution_history,
                'history_count': len(self.execution_history),
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting execution history: {e}")
            return {
                'execution_history': [],
                'history_count': 0,
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def get_active_orders(self) -> Dict[str, Any]:
        """Get active orders."""
        try:
            return {
                'active_orders': self.active_orders,
                'order_count': len(self.active_orders),
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting active orders: {e}")
            return {
                'active_orders': {},
                'order_count': 0,
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def _validate_trade_instruction(self, trade_instruction: Dict[str, Any]) -> Dict[str, Any]:
        """Validate trade instruction."""
        try:
            # Check required fields
            required_fields = ['type', 'venue', 'asset', 'amount']
            for field in required_fields:
                if field not in trade_instruction:
                    return {
                        'valid': False,
                        'error': f"Missing required field: {field}"
                    }
            
            # Check trade type
            valid_types = ['cex_trade', 'onchain_supply', 'onchain_withdraw', 
                          'onchain_borrow', 'onchain_repay', 'onchain_stake', 'onchain_unstake']
            if trade_instruction['type'] not in valid_types:
                return {
                    'valid': False,
                    'error': f"Invalid trade type: {trade_instruction['type']}"
                }
            
            # Check amount
            if trade_instruction['amount'] <= 0:
                return {
                    'valid': False,
                    'error': f"Invalid amount: {trade_instruction['amount']}"
                }
            
            return {'valid': True}
        except Exception as e:
            logger.error(f"Error validating trade instruction: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _validate_transaction_instructions(self, transaction_instructions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate transaction instructions."""
        try:
            if not transaction_instructions:
                return {
                    'valid': False,
                    'error': "No transaction instructions provided"
                }
            
            # Validate each instruction
            for i, instruction in enumerate(transaction_instructions):
                validation_result = self._validate_trade_instruction(instruction)
                if not validation_result['valid']:
                    return {
                        'valid': False,
                        'error': f"Invalid instruction {i}: {validation_result['error']}"
                    }
            
            return {'valid': True}
        except Exception as e:
            logger.error(f"Error validating transaction instructions: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _validate_operation_instructions(self, operation_instructions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate operation instructions."""
        try:
            if not operation_instructions:
                return {
                    'valid': False,
                    'error': "No operation instructions provided"
                }
            
            # Validate each instruction
            for i, instruction in enumerate(operation_instructions):
                validation_result = self._validate_trade_instruction(instruction)
                if not validation_result['valid']:
                    return {
                        'valid': False,
                        'error': f"Invalid instruction {i}: {validation_result['error']}"
                    }
            
            return {'valid': True}
        except Exception as e:
            logger.error(f"Error validating operation instructions: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _execute_cex_trade(self, trade_instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute CEX trade."""
        try:
            venue = trade_instruction['venue']
            asset_in = trade_instruction['asset']
            amount_in = trade_instruction['amount']
            asset_out = trade_instruction.get('asset_out', 'USDT')
            trade_type = trade_instruction.get('trade_type', 'market_sell')
            
            # Placeholder for actual CEX trade execution
            # In real implementation, this would call the appropriate CEX API
            logger.info(f"Executing CEX trade: {amount_in} {asset_in} -> {asset_out} on {venue}")
            
            # Simulate trade execution
            execution_result = {
                'status': 'success',
                'type': 'cex_trade',
                'venue': venue,
                'asset_in': asset_in,
                'amount_in': amount_in,
                'asset_out': asset_out,
                'amount_out': amount_in * 0.99,  # Simulate 1% slippage
                'trade_type': trade_type,
                'timestamp': timestamp,
                'execution_id': f"cex_{venue}_{timestamp.timestamp()}"
            }
            
            # Add to execution history
            self.execution_history.append({
                'type': 'cex_trade',
                'instruction': trade_instruction,
                'result': execution_result,
                'timestamp': timestamp
            })
            
            return execution_result
        except Exception as e:
            logger.error(f"Error executing CEX trade: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_onchain_supply(self, trade_instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute onchain supply."""
        try:
            venue = trade_instruction['venue']
            asset = trade_instruction['asset']
            amount = trade_instruction['amount']
            
            # Placeholder for actual onchain supply execution
            # In real implementation, this would call the appropriate smart contract
            logger.info(f"Executing onchain supply: {amount} {asset} to {venue}")
            
            # Simulate supply execution
            execution_result = {
                'status': 'success',
                'type': 'onchain_supply',
                'venue': venue,
                'asset': asset,
                'amount': amount,
                'timestamp': timestamp,
                'execution_id': f"supply_{venue}_{timestamp.timestamp()}"
            }
            
            # Add to execution history
            self.execution_history.append({
                'type': 'onchain_supply',
                'instruction': trade_instruction,
                'result': execution_result,
                'timestamp': timestamp
            })
            
            return execution_result
        except Exception as e:
            logger.error(f"Error executing onchain supply: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_onchain_withdraw(self, trade_instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute onchain withdraw."""
        try:
            venue = trade_instruction['venue']
            asset = trade_instruction['asset']
            amount = trade_instruction['amount']
            
            # Placeholder for actual onchain withdraw execution
            # In real implementation, this would call the appropriate smart contract
            logger.info(f"Executing onchain withdraw: {amount} {asset} from {venue}")
            
            # Simulate withdraw execution
            execution_result = {
                'status': 'success',
                'type': 'onchain_withdraw',
                'venue': venue,
                'asset': asset,
                'amount': amount,
                'timestamp': timestamp,
                'execution_id': f"withdraw_{venue}_{timestamp.timestamp()}"
            }
            
            # Add to execution history
            self.execution_history.append({
                'type': 'onchain_withdraw',
                'instruction': trade_instruction,
                'result': execution_result,
                'timestamp': timestamp
            })
            
            return execution_result
        except Exception as e:
            logger.error(f"Error executing onchain withdraw: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_onchain_borrow(self, trade_instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute onchain borrow."""
        try:
            venue = trade_instruction['venue']
            asset = trade_instruction['asset']
            amount = trade_instruction['amount']
            
            # Placeholder for actual onchain borrow execution
            # In real implementation, this would call the appropriate smart contract
            logger.info(f"Executing onchain borrow: {amount} {asset} from {venue}")
            
            # Simulate borrow execution
            execution_result = {
                'status': 'success',
                'type': 'onchain_borrow',
                'venue': venue,
                'asset': asset,
                'amount': amount,
                'timestamp': timestamp,
                'execution_id': f"borrow_{venue}_{timestamp.timestamp()}"
            }
            
            # Add to execution history
            self.execution_history.append({
                'type': 'onchain_borrow',
                'instruction': trade_instruction,
                'result': execution_result,
                'timestamp': timestamp
            })
            
            return execution_result
        except Exception as e:
            logger.error(f"Error executing onchain borrow: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_onchain_repay(self, trade_instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute onchain repay."""
        try:
            venue = trade_instruction['venue']
            asset = trade_instruction['asset']
            amount = trade_instruction['amount']
            
            # Placeholder for actual onchain repay execution
            # In real implementation, this would call the appropriate smart contract
            logger.info(f"Executing onchain repay: {amount} {asset} to {venue}")
            
            # Simulate repay execution
            execution_result = {
                'status': 'success',
                'type': 'onchain_repay',
                'venue': venue,
                'asset': asset,
                'amount': amount,
                'timestamp': timestamp,
                'execution_id': f"repay_{venue}_{timestamp.timestamp()}"
            }
            
            # Add to execution history
            self.execution_history.append({
                'type': 'onchain_repay',
                'instruction': trade_instruction,
                'result': execution_result,
                'timestamp': timestamp
            })
            
            return execution_result
        except Exception as e:
            logger.error(f"Error executing onchain repay: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_onchain_stake(self, trade_instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute onchain stake."""
        try:
            venue = trade_instruction['venue']
            asset = trade_instruction['asset']
            amount = trade_instruction['amount']
            
            # Placeholder for actual onchain stake execution
            # In real implementation, this would call the appropriate smart contract
            logger.info(f"Executing onchain stake: {amount} {asset} to {venue}")
            
            # Simulate stake execution
            execution_result = {
                'status': 'success',
                'type': 'onchain_stake',
                'venue': venue,
                'asset': asset,
                'amount': amount,
                'timestamp': timestamp,
                'execution_id': f"stake_{venue}_{timestamp.timestamp()}"
            }
            
            # Add to execution history
            self.execution_history.append({
                'type': 'onchain_stake',
                'instruction': trade_instruction,
                'result': execution_result,
                'timestamp': timestamp
            })
            
            return execution_result
        except Exception as e:
            logger.error(f"Error executing onchain stake: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_onchain_unstake(self, trade_instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute onchain unstake."""
        try:
            venue = trade_instruction['venue']
            asset = trade_instruction['asset']
            amount = trade_instruction['amount']
            
            # Placeholder for actual onchain unstake execution
            # In real implementation, this would call the appropriate smart contract
            logger.info(f"Executing onchain unstake: {amount} {asset} from {venue}")
            
            # Simulate unstake execution
            execution_result = {
                'status': 'success',
                'type': 'onchain_unstake',
                'venue': venue,
                'asset': asset,
                'amount': amount,
                'timestamp': timestamp,
                'execution_id': f"unstake_{venue}_{timestamp.timestamp()}"
            }
            
            # Add to execution history
            self.execution_history.append({
                'type': 'onchain_unstake',
                'instruction': trade_instruction,
                'result': execution_result,
                'timestamp': timestamp
            })
            
            return execution_result
        except Exception as e:
            logger.error(f"Error executing onchain unstake: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_atomic_transaction_internal(self, transaction_instructions: List[Dict[str, Any]], 
                                           timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Internal method to execute atomic transaction."""
        try:
            # Placeholder for actual atomic transaction execution
            # In real implementation, this would use a transaction builder
            logger.info(f"Executing atomic transaction with {len(transaction_instructions)} instructions")
            
            # Simulate atomic transaction execution
            execution_result = {
                'status': 'success',
                'type': 'atomic_transaction',
                'instruction_count': len(transaction_instructions),
                'timestamp': timestamp,
                'execution_id': f"atomic_{timestamp.timestamp()}"
            }
            
            return execution_result
        except Exception as e:
            logger.error(f"Error in internal atomic transaction execution: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_sequential_operations_internal(self, operation_instructions: List[Dict[str, Any]], 
                                              timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Internal method to execute sequential operations."""
        try:
            # Placeholder for actual sequential operations execution
            # In real implementation, this would execute operations one by one
            logger.info(f"Executing sequential operations with {len(operation_instructions)} instructions")
            
            # Simulate sequential operations execution
            execution_result = {
                'status': 'success',
                'type': 'sequential_operations',
                'instruction_count': len(operation_instructions),
                'timestamp': timestamp,
                'execution_id': f"sequential_{timestamp.timestamp()}"
            }
            
            return execution_result
        except Exception as e:
            logger.error(f"Error in internal sequential operations execution: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
