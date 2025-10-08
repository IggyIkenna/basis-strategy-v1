"""
Wallet Transfer Executor

Handles simple wallet-to-venue transfers that can't be bundled with smart contract operations.

Key Principles:
- Simple, direct position monitor updates
- No complex routing or optimization
- Sequential execution only (can't be atomic with smart contracts)
- Dedicated logging and error codes
"""

import logging
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

from ..instructions import WalletTransferInstruction, InstructionBlock

logger = logging.getLogger(__name__)

# Create dedicated wallet transfer executor logger
wallet_transfer_logger = logging.getLogger('wallet_transfer_executor')
wallet_transfer_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent.parent.parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Create file handler for wallet transfer executor logs
wallet_transfer_handler = logging.FileHandler(logs_dir / 'wallet_transfer_executor.log')
wallet_transfer_handler.setLevel(logging.INFO)

# Create formatter
wallet_transfer_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
wallet_transfer_handler.setFormatter(wallet_transfer_formatter)

# Add handler to logger
wallet_transfer_logger.addHandler(wallet_transfer_handler)

# Error codes for Wallet Transfer Executor
ERROR_CODES = {
    'WALLET-001': 'Wallet transfer execution failed',
    'WALLET-002': 'Insufficient balance for transfer',
    'WALLET-003': 'Invalid transfer venues',
    'WALLET-004': 'Position monitor update failed',
    'WALLET-005': 'Transfer validation failed',
    'WALLET-006': 'Event logging failed'
}


class WalletTransferExecutor:
    """
    Execute simple wallet-to-venue transfers.
    
    Handles transfers between:
    - wallet ↔ binance
    - wallet ↔ bybit  
    - wallet ↔ okx
    - binance ↔ bybit ↔ okx (CEX-to-CEX)
    """
    
    def __init__(self, position_monitor, event_logger, execution_mode: str = 'backtest'):
        self.position_monitor = position_monitor
        self.event_logger = event_logger
        self.execution_mode = execution_mode
        
        wallet_transfer_logger.info(f"WalletTransferExecutor initialized in {execution_mode} mode")
    
    async def execute_transfer_block(self, transfer_block: InstructionBlock, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Execute a block of wallet transfer instructions sequentially.
        
        Args:
            transfer_block: Block containing wallet transfer instructions
            timestamp: Execution timestamp
            
        Returns:
            Execution results for the block
        """
        try:
            wallet_transfer_logger.info(f"Executing wallet transfer block: {transfer_block.timestamp_group}")
            
            results = []
            for instruction in transfer_block.instructions:
                result = await self._execute_single_transfer(instruction, timestamp)
                results.append(result)
            
            wallet_transfer_logger.info(f"Wallet transfer block completed: {len(results)} transfers")
            
            return {
                'success': True,
                'block_type': transfer_block.block_type,
                'timestamp_group': transfer_block.timestamp_group,
                'transfers_executed': len(results),
                'results': results
            }
            
        except Exception as e:
            wallet_transfer_logger.error(f"Wallet transfer block failed: {e}")
            raise ValueError(f"WALLET-001: Wallet transfer block execution failed: {e}")
    
    async def _execute_single_transfer(self, instruction: WalletTransferInstruction, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Execute a single wallet transfer instruction.
        
        Args:
            instruction: Wallet transfer instruction
            timestamp: Execution timestamp
            
        Returns:
            Transfer execution result
        """
        try:
            wallet_transfer_logger.info(f"Executing transfer: {instruction.source_venue} → {instruction.target_venue} "
                                      f"{instruction.amount} {instruction.token} ({instruction.purpose})")
            
            # Validate transfer
            await self._validate_transfer(instruction)
            
            # Execute based on mode
            if self.execution_mode == 'backtest':
                result = await self._execute_backtest_transfer(instruction, timestamp)
            else:
                result = await self._execute_live_transfer(instruction, timestamp)
            
            # Update position monitor
            await self._update_position_monitor(instruction, timestamp)
            
            # Log event
            await self._log_transfer_event(instruction, result, timestamp)
            
            wallet_transfer_logger.info(f"Transfer completed: {instruction.source_venue} → {instruction.target_venue} "
                                      f"{instruction.amount} {instruction.token}")
            
            return result
            
        except Exception as e:
            wallet_transfer_logger.error(f"Single transfer failed: {e}")
            raise ValueError(f"WALLET-001: Transfer execution failed: {e}")
    
    async def _validate_transfer(self, instruction: WalletTransferInstruction):
        """Validate transfer instruction and balances."""
        try:
            # Check valid venues
            valid_venues = ['wallet', 'binance', 'bybit', 'okx']
            if instruction.source_venue not in valid_venues or instruction.target_venue not in valid_venues:
                raise ValueError(f"WALLET-003: Invalid venues: {instruction.source_venue} → {instruction.target_venue}")
            
            # Check sufficient balance
            if instruction.source_venue == 'wallet':
                current_snapshot = self.position_monitor.get_snapshot()
                current_wallet = current_snapshot.get('wallet', {})
                current_balance = current_wallet.get(instruction.token, 0)
                
                if current_balance < instruction.amount:
                    raise ValueError(f"WALLET-002: Insufficient {instruction.token} balance in wallet: "
                                   f"{current_balance} < {instruction.amount}")
            
        except Exception as e:
            wallet_transfer_logger.error(f"Transfer validation failed: {e}")
            raise ValueError(f"WALLET-005: Transfer validation failed: {e}")
    
    async def _execute_backtest_transfer(self, instruction: WalletTransferInstruction, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute simulated transfer for backtest mode."""
        return {
            'success': True,
            'source_venue': instruction.source_venue,
            'target_venue': instruction.target_venue,
            'token': instruction.token,
            'amount': instruction.amount,
            'execution_mode': 'backtest',
            'timestamp': timestamp,
            'transfer_id': f"backtest_{instruction.source_venue}_{instruction.target_venue}_{instruction.token}_{int(timestamp.timestamp())}"
        }
    
    async def _execute_live_transfer(self, instruction: WalletTransferInstruction, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Execute real transfer for live mode."""
        # TODO: Implement live wallet transfers
        # This would involve actual wallet operations and CEX deposits/withdrawals
        raise NotImplementedError("Live wallet transfer execution not yet implemented")
    
    async def _update_position_monitor(self, instruction: WalletTransferInstruction, timestamp: pd.Timestamp):
        """Update position monitor with transfer changes."""
        try:
            changes = {
                'timestamp': timestamp,
                'trigger': 'WALLET_TRANSFER',
                'token_changes': [
                    {
                        'venue': instruction.source_venue.upper(),
                        'token': instruction.token,
                        'delta': -instruction.amount,
                        'reason': f'TRANSFER_TO_{instruction.target_venue.upper()}'
                    },
                    {
                        'venue': instruction.target_venue.upper(),
                        'token': instruction.token,
                        'delta': +instruction.amount,
                        'reason': f'TRANSFER_FROM_{instruction.source_venue.upper()}'
                    }
                ]
            }
            
            # Use Position Update Handler for tight loop (position → exposure → risk → P&L)
            if hasattr(self, 'position_update_handler') and self.position_update_handler:
                # Ensure timestamp is pandas Timestamp
                if not isinstance(timestamp, pd.Timestamp):
                    timestamp = pd.Timestamp(timestamp)
                await self.position_update_handler.handle_position_update(
                    changes=changes,
                    timestamp=timestamp,
                    market_data={},  # Wallet transfers don't need market data
                    trigger_component='WALLET_TRANSFER'
                )
            else:
                # Fallback to direct position monitor update
                await self.position_monitor.update(changes)
            
        except Exception as e:
            wallet_transfer_logger.error(f"Position monitor update failed: {e}")
            raise ValueError(f"WALLET-004: Position monitor update failed: {e}")
    
    async def _log_transfer_event(self, instruction: WalletTransferInstruction, result: Dict[str, Any], timestamp: pd.Timestamp):
        """Log transfer event."""
        try:
            if self.event_logger:
                await self.event_logger.log_event(
                    timestamp=timestamp,
                    event_type='WALLET_TRANSFER',
                    venue=instruction.target_venue,
                    token=instruction.token,
                    data={
                        'source_venue': instruction.source_venue,
                        'target_venue': instruction.target_venue,
                        'amount': instruction.amount,
                        'purpose': instruction.purpose,
                        'transfer_id': result.get('transfer_id'),
                        'execution_mode': result.get('execution_mode')
                    }
                )
        except Exception as e:
            wallet_transfer_logger.error(f"Event logging failed: {e}")
            # Don't raise - logging failure shouldn't stop execution
