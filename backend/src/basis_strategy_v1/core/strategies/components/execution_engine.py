"""
Mode-Agnostic Execution Engine

Provides mode-agnostic execution engine that works for both backtest and live modes.
Manages execution across all venues and provides generic execution logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/17_EXECUTION_ENGINE.md - Mode-agnostic execution management
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class ExecutionEngine:
    """Mode-agnostic execution engine that works for both backtest and live modes"""
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize execution engine.
        
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
        self.active_executions = {}
        
        logger.info("ExecutionEngine initialized (mode-agnostic)")
    
    def execute_strategy_action(self, action: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Execute strategy action regardless of mode (backtest or live).
        
        Args:
            action: Strategy action to execute
            timestamp: Current timestamp
            
        Returns:
            Dictionary with execution result
        """
        try:
            # Validate action
            validation_result = self._validate_action(action)
            if not validation_result['valid']:
                return {
                    'status': 'failed',
                    'error': validation_result['error'],
                    'timestamp': timestamp
                }
            
            # Execute action based on type
            action_type = action.get('action_type')
            
            if action_type == 'entry_full':
                execution_result = self._execute_entry_full(action, timestamp)
            elif action_type == 'entry_partial':
                execution_result = self._execute_entry_partial(action, timestamp)
            elif action_type == 'exit_full':
                execution_result = self._execute_exit_full(action, timestamp)
            elif action_type == 'exit_partial':
                execution_result = self._execute_exit_partial(action, timestamp)
            elif action_type == 'sell_dust':
                execution_result = self._execute_sell_dust(action, timestamp)
            else:
                return {
                    'status': 'failed',
                    'error': f"Unsupported action type: {action_type}",
                    'timestamp': timestamp
                }
            
            # Add to execution history
            self.execution_history.append({
                'action': action,
                'result': execution_result,
                'timestamp': timestamp
            })
            
            return {
                'status': 'success' if execution_result['success'] else 'failed',
                'action_type': action_type,
                'result': execution_result,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error executing strategy action: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def execute_instructions(self, instructions: List[Dict[str, Any]], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Execute list of instructions regardless of mode (backtest or live).
        
        Args:
            instructions: List of instructions to execute
            timestamp: Current timestamp
            
        Returns:
            Dictionary with execution result
        """
        try:
            # Validate instructions
            validation_result = self._validate_instructions(instructions)
            if not validation_result['valid']:
                return {
                    'status': 'failed',
                    'error': validation_result['error'],
                    'timestamp': timestamp
                }
            
            # Execute instructions
            execution_result = self._execute_instructions_internal(instructions, timestamp)
            
            # Add to execution history
            self.execution_history.append({
                'instructions': instructions,
                'result': execution_result,
                'timestamp': timestamp
            })
            
            return {
                'status': 'success' if execution_result['success'] else 'failed',
                'instruction_count': len(instructions),
                'result': execution_result,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error executing instructions: {e}")
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
                'active_executions': self.active_executions,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting execution history: {e}")
            return {
                'execution_history': [],
                'active_executions': {},
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def _validate_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Validate action before execution."""
        try:
            # Check required fields
            required_fields = ['action_type', 'target_amount', 'target_currency', 'instructions']
            for field in required_fields:
                if field not in action:
                    return {
                        'valid': False,
                        'error': f"Missing required field: {field}"
                    }
            
            # Check action type
            valid_types = ['entry_full', 'entry_partial', 'exit_full', 'exit_partial', 'sell_dust']
            if action['action_type'] not in valid_types:
                return {
                    'valid': False,
                    'error': f"Invalid action type: {action['action_type']}"
                }
            
            # Check target amount
            if action['target_amount'] <= 0:
                return {
                    'valid': False,
                    'error': f"Invalid target amount: {action['target_amount']}"
                }
            
            # Check instructions
            if not isinstance(action['instructions'], list) or not action['instructions']:
                return {
                    'valid': False,
                    'error': "Instructions must be a non-empty list"
                }
            
            return {'valid': True}
        except Exception as e:
            logger.error(f"Error validating action: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _validate_instructions(self, instructions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate instructions before execution."""
        try:
            if not instructions:
                return {
                    'valid': False,
                    'error': "No instructions provided"
                }
            
            # Validate each instruction
            for i, instruction in enumerate(instructions):
                validation_result = self._validate_instruction(instruction)
                if not validation_result['valid']:
                    return {
                        'valid': False,
                        'error': f"Invalid instruction {i}: {validation_result['error']}"
                    }
            
            return {'valid': True}
        except Exception as e:
            logger.error(f"Error validating instructions: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _validate_instruction(self, instruction: Dict[str, Any]) -> Dict[str, Any]:
        """Validate individual instruction."""
        try:
            # Check required fields
            required_fields = ['type', 'venue', 'asset', 'amount']
            for field in required_fields:
                if field not in instruction:
                    return {
                        'valid': False,
                        'error': f"Missing required field: {field}"
                    }
            
            # Check instruction type
            valid_types = ['cex_trade', 'onchain_supply', 'onchain_withdraw', 
                          'onchain_borrow', 'onchain_repay', 'onchain_stake', 'onchain_unstake']
            if instruction['type'] not in valid_types:
                return {
                    'valid': False,
                    'error': f"Invalid instruction type: {instruction['type']}"
                }
            
            # Check amount
            if instruction['amount'] <= 0:
                return {
                    'valid': False,
                    'error': f"Invalid amount: {instruction['amount']}"
                }
            
            return {'valid': True}
        except Exception as e:
            logger.error(f"Error validating instruction: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _execute_entry_full(self, action: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute entry full action."""
        try:
            logger.info(f"Executing entry full action: {action['target_amount']} {action['target_currency']}")
            
            # Execute instructions
            instructions = action['instructions']
            execution_result = self._execute_instructions_internal(instructions, timestamp)
            
            return {
                'success': execution_result['success'],
                'action_type': 'entry_full',
                'target_amount': action['target_amount'],
                'target_currency': action['target_currency'],
                'instruction_count': len(instructions),
                'execution_result': execution_result,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error executing entry full action: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_entry_partial(self, action: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute entry partial action."""
        try:
            logger.info(f"Executing entry partial action: {action['target_amount']} {action['target_currency']}")
            
            # Execute instructions
            instructions = action['instructions']
            execution_result = self._execute_instructions_internal(instructions, timestamp)
            
            return {
                'success': execution_result['success'],
                'action_type': 'entry_partial',
                'target_amount': action['target_amount'],
                'target_currency': action['target_currency'],
                'instruction_count': len(instructions),
                'execution_result': execution_result,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error executing entry partial action: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_exit_full(self, action: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute exit full action."""
        try:
            logger.info(f"Executing exit full action: {action['target_amount']} {action['target_currency']}")
            
            # Execute instructions
            instructions = action['instructions']
            execution_result = self._execute_instructions_internal(instructions, timestamp)
            
            return {
                'success': execution_result['success'],
                'action_type': 'exit_full',
                'target_amount': action['target_amount'],
                'target_currency': action['target_currency'],
                'instruction_count': len(instructions),
                'execution_result': execution_result,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error executing exit full action: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_exit_partial(self, action: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute exit partial action."""
        try:
            logger.info(f"Executing exit partial action: {action['target_amount']} {action['target_currency']}")
            
            # Execute instructions
            instructions = action['instructions']
            execution_result = self._execute_instructions_internal(instructions, timestamp)
            
            return {
                'success': execution_result['success'],
                'action_type': 'exit_partial',
                'target_amount': action['target_amount'],
                'target_currency': action['target_currency'],
                'instruction_count': len(instructions),
                'execution_result': execution_result,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error executing exit partial action: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_sell_dust(self, action: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute sell dust action."""
        try:
            logger.info(f"Executing sell dust action: {action['target_amount']} {action['target_currency']}")
            
            # Execute instructions
            instructions = action['instructions']
            execution_result = self._execute_instructions_internal(instructions, timestamp)
            
            return {
                'success': execution_result['success'],
                'action_type': 'sell_dust',
                'target_amount': action['target_amount'],
                'target_currency': action['target_currency'],
                'instruction_count': len(instructions),
                'execution_result': execution_result,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error executing sell dust action: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_instructions_internal(self, instructions: List[Dict[str, Any]], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Internal method to execute instructions."""
        try:
            execution_results = []
            success_count = 0
            
            for i, instruction in enumerate(instructions):
                try:
                    # Execute individual instruction
                    instruction_result = self._execute_instruction(instruction, timestamp)
                    execution_results.append(instruction_result)
                    
                    if instruction_result['success']:
                        success_count += 1
                        
                except Exception as e:
                    logger.error(f"Error executing instruction {i}: {e}")
                    execution_results.append({
                        'success': False,
                        'error': str(e),
                        'instruction_index': i
                    })
            
            # Calculate overall success
            overall_success = success_count == len(instructions)
            
            return {
                'success': overall_success,
                'total_instructions': len(instructions),
                'successful_instructions': success_count,
                'failed_instructions': len(instructions) - success_count,
                'execution_results': execution_results,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error in internal instruction execution: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_instruction(self, instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute individual instruction."""
        try:
            instruction_type = instruction['type']
            
            if instruction_type == 'cex_trade':
                return self._execute_cex_trade_instruction(instruction, timestamp)
            elif instruction_type == 'onchain_supply':
                return self._execute_onchain_supply_instruction(instruction, timestamp)
            elif instruction_type == 'onchain_withdraw':
                return self._execute_onchain_withdraw_instruction(instruction, timestamp)
            elif instruction_type == 'onchain_borrow':
                return self._execute_onchain_borrow_instruction(instruction, timestamp)
            elif instruction_type == 'onchain_repay':
                return self._execute_onchain_repay_instruction(instruction, timestamp)
            elif instruction_type == 'onchain_stake':
                return self._execute_onchain_stake_instruction(instruction, timestamp)
            elif instruction_type == 'onchain_unstake':
                return self._execute_onchain_unstake_instruction(instruction, timestamp)
            else:
                return {
                    'success': False,
                    'error': f"Unsupported instruction type: {instruction_type}",
                    'timestamp': timestamp
                }
                
        except Exception as e:
            logger.error(f"Error executing instruction: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_cex_trade_instruction(self, instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute CEX trade instruction."""
        try:
            venue = instruction['venue']
            asset = instruction['asset']
            amount = instruction['amount']
            
            logger.info(f"Executing CEX trade: {amount} {asset} on {venue}")
            
            # Placeholder for actual CEX trade execution
            # In real implementation, this would call the appropriate CEX API
            
            return {
                'success': True,
                'instruction_type': 'cex_trade',
                'venue': venue,
                'asset': asset,
                'amount': amount,
                'execution_id': f"cex_trade_{venue}_{timestamp.timestamp()}",
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error executing CEX trade instruction: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_onchain_supply_instruction(self, instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute onchain supply instruction."""
        try:
            venue = instruction['venue']
            asset = instruction['asset']
            amount = instruction['amount']
            
            logger.info(f"Executing onchain supply: {amount} {asset} to {venue}")
            
            # Placeholder for actual onchain supply execution
            # In real implementation, this would call the appropriate smart contract
            
            return {
                'success': True,
                'instruction_type': 'onchain_supply',
                'venue': venue,
                'asset': asset,
                'amount': amount,
                'execution_id': f"supply_{venue}_{timestamp.timestamp()}",
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error executing onchain supply instruction: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_onchain_withdraw_instruction(self, instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute onchain withdraw instruction."""
        try:
            venue = instruction['venue']
            asset = instruction['asset']
            amount = instruction['amount']
            
            logger.info(f"Executing onchain withdraw: {amount} {asset} from {venue}")
            
            # Placeholder for actual onchain withdraw execution
            # In real implementation, this would call the appropriate smart contract
            
            return {
                'success': True,
                'instruction_type': 'onchain_withdraw',
                'venue': venue,
                'asset': asset,
                'amount': amount,
                'execution_id': f"withdraw_{venue}_{timestamp.timestamp()}",
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error executing onchain withdraw instruction: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_onchain_borrow_instruction(self, instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute onchain borrow instruction."""
        try:
            venue = instruction['venue']
            asset = instruction['asset']
            amount = instruction['amount']
            
            logger.info(f"Executing onchain borrow: {amount} {asset} from {venue}")
            
            # Placeholder for actual onchain borrow execution
            # In real implementation, this would call the appropriate smart contract
            
            return {
                'success': True,
                'instruction_type': 'onchain_borrow',
                'venue': venue,
                'asset': asset,
                'amount': amount,
                'execution_id': f"borrow_{venue}_{timestamp.timestamp()}",
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error executing onchain borrow instruction: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_onchain_repay_instruction(self, instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute onchain repay instruction."""
        try:
            venue = instruction['venue']
            asset = instruction['asset']
            amount = instruction['amount']
            
            logger.info(f"Executing onchain repay: {amount} {asset} to {venue}")
            
            # Placeholder for actual onchain repay execution
            # In real implementation, this would call the appropriate smart contract
            
            return {
                'success': True,
                'instruction_type': 'onchain_repay',
                'venue': venue,
                'asset': asset,
                'amount': amount,
                'execution_id': f"repay_{venue}_{timestamp.timestamp()}",
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error executing onchain repay instruction: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_onchain_stake_instruction(self, instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute onchain stake instruction."""
        try:
            venue = instruction['venue']
            asset = instruction['asset']
            amount = instruction['amount']
            
            logger.info(f"Executing onchain stake: {amount} {asset} to {venue}")
            
            # Placeholder for actual onchain stake execution
            # In real implementation, this would call the appropriate smart contract
            
            return {
                'success': True,
                'instruction_type': 'onchain_stake',
                'venue': venue,
                'asset': asset,
                'amount': amount,
                'execution_id': f"stake_{venue}_{timestamp.timestamp()}",
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error executing onchain stake instruction: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _execute_onchain_unstake_instruction(self, instruction: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute onchain unstake instruction."""
        try:
            venue = instruction['venue']
            asset = instruction['asset']
            amount = instruction['amount']
            
            logger.info(f"Executing onchain unstake: {amount} {asset} from {venue}")
            
            # Placeholder for actual onchain unstake execution
            # In real implementation, this would call the appropriate smart contract
            
            return {
                'success': True,
                'instruction_type': 'onchain_unstake',
                'venue': venue,
                'asset': asset,
                'amount': amount,
                'execution_id': f"unstake_{venue}_{timestamp.timestamp()}",
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error executing onchain unstake instruction: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
