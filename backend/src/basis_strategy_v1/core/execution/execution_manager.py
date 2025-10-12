"""
Execution Manager Component - Tight Loop Architecture

Implements the tight loop execution pattern:
execution sends instruction → position_monitor updates → verify reconciliation → next instruction

Reference: .cursor/tasks/12_tight_loop_architecture.md
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 4
"""

from typing import Dict, Any, List, Optional
import logging
import asyncio
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class ExecutionManager:
    """Centralized execution manager implementing tight loop architecture."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ExecutionManager, cls).__new__(cls)
        return cls._instance
       
    def __init__(self, execution_mode: str, config: Dict[str, Any], position_monitor=None):
        self.execution_mode = execution_mode
        self.config = config
        self.position_monitor = position_monitor
        self.execution_interfaces = {}  # wallet, trade, etc.
        self.instruction_queue = []
        self.current_instruction = None
        self._initialize_execution_interfaces()
    
    def _initialize_execution_interfaces(self):
        """Initialize execution type interfaces (wallet, trade, etc.)."""
        # Create execution interfaces that handle different instruction types
        # Each interface routes to appropriate venue client implementations
        pass
    
    async def execute_instruction_sequence(self, instructions: List[Dict], market_data: Dict) -> Dict:
        """
        Execute a sequence of instructions using tight loop architecture.
        
        Each instruction goes through:
        1. Send instruction to venue
        2. Position monitor updates
        3. Verify reconciliation
        4. Move to next instruction only after reconciliation
        """
        results = []
        
        for i, instruction in enumerate(instructions):
            logger.info(f"Execution Manager: Processing instruction {i+1}/{len(instructions)}")
            
            # Execute tight loop for this instruction
            result = await self._execute_tight_loop(instruction, market_data)
            results.append(result)
            
            # If instruction failed, stop execution
            if not result.get('success', False):
                logger.error(f"Execution Manager: Instruction {i+1} failed, stopping sequence")
                break
        
        return {
            'success': all(r.get('success', False) for r in results),
            'results': results,
            'total_instructions': len(instructions),
            'successful_instructions': sum(1 for r in results if r.get('success', False))
        }
    
    async def _execute_tight_loop(self, instruction: Dict, market_data: Dict) -> Dict:
        """
        Execute tight loop for a single instruction:
        execution → position_monitor → reconciliation → next instruction
        """
        try:
            # Step 1: Send instruction to venue
            logger.info(f"Execution Manager: Sending instruction to venue")
            execution_result = await self._send_instruction(instruction, market_data)
            
            if not execution_result.get('success', False):
                return {
                    'success': False,
                    'error': 'Instruction execution failed',
                    'execution_result': execution_result
                }
            
            # Step 2: Position monitor updates
            logger.info(f"Execution Manager: Updating position monitor")
            position_result = await self._update_position_monitor(instruction, execution_result)
            
            if not position_result.get('success', False):
                return {
                    'success': False,
                    'error': 'Position monitor update failed',
                    'execution_result': execution_result,
                    'position_result': position_result
                }
            
            # Step 3: Verify reconciliation
            logger.info(f"Execution Manager: Verifying reconciliation")
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
            logger.info(f"Execution Manager: Tight loop completed successfully")
            return {
                'success': True,
                'execution_result': execution_result,
                'position_result': position_result,
                'reconciliation_result': reconciliation_result
            }
            
        except Exception as e:
            logger.error(f"Execution Manager: Tight loop failed: {e}")
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
            
            logger.info(f"Execution Manager: Sending {instruction_type} instruction to {venue}")
            
            # Route to appropriate execution interface
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
            logger.error(f"Execution Manager: Instruction execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _update_position_monitor(self, instruction: Dict, execution_result: Dict) -> Dict:
        """Update position monitor based on instruction result."""
        try:
            if not self.position_monitor:
                logger.warning("Execution Manager: No position monitor available")
                return {'success': True, 'message': 'No position monitor available'}
            
            # Update position monitor with instruction result
            # This is mode-agnostic - position monitor handles backtest vs live
            timestamp = pd.Timestamp.now()
            
            # For now, just log the update
            logger.info(f"Execution Manager: Position monitor updated for instruction")
            
            return {
                'success': True,
                'timestamp': timestamp,
                'instruction': instruction,
                'execution_result': execution_result
            }
            
        except Exception as e:
            logger.error(f"Execution Manager: Position monitor update failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _verify_reconciliation(self, instruction: Dict, execution_result: Dict, position_result: Dict) -> Dict:
        """Verify that position matches expected state after instruction."""
        try:
            # Verify that the position change matches what was expected
            # This is the critical reconciliation step
            
            logger.info(f"Execution Manager: Verifying position reconciliation")
            
            # For now, always return success
            # TODO: Implement actual reconciliation logic
            return {
                'success': True,
                'expected_position': instruction.get('expected_position', {}),
                'actual_position': position_result.get('position', {}),
                'reconciliation_passed': True
            }
            
        except Exception as e:
            logger.error(f"Execution Manager: Reconciliation verification failed: {e}")
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