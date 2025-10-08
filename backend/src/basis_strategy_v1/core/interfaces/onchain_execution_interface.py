"""
OnChain Execution Interface

Provides on-chain execution capabilities for both backtest and live modes.
Implements the BaseExecutionInterface contract.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from datetime import datetime, timezone
import json
from pathlib import Path

from .base_execution_interface import BaseExecutionInterface

logger = logging.getLogger(__name__)

# Create dedicated OnChain execution interface logger
onchain_interface_logger = logging.getLogger('onchain_execution_interface')
onchain_interface_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent.parent.parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Create file handler for OnChain execution interface logs
onchain_interface_handler = logging.FileHandler(logs_dir / 'onchain_execution_interface.log')
onchain_interface_handler.setLevel(logging.INFO)

# Create formatter
onchain_interface_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
onchain_interface_handler.setFormatter(onchain_interface_formatter)

# Add handler to logger
onchain_interface_logger.addHandler(onchain_interface_handler)

# Error codes for OnChain Execution Interface
ERROR_CODES = {
    'ONCHAIN-IF-001': 'On-chain operation execution failed',
    'ONCHAIN-IF-002': 'Web3 client not available',
    'ONCHAIN-IF-003': 'Transaction building failed',
    'ONCHAIN-IF-004': 'Transaction signing failed',
    'ONCHAIN-IF-005': 'Transaction sending failed',
    'ONCHAIN-IF-006': 'Gas cost calculation failed',
    'ONCHAIN-IF-007': 'Contract interaction failed',
    'ONCHAIN-IF-008': 'Web3 library not available'
}


class OnChainExecutionInterface(BaseExecutionInterface):
    """
    On-chain execution interface for blockchain operations.
    
    Supports both backtest (simulated) and live (real) execution modes.
    """
    
    def __init__(self, execution_mode: str, config: Dict[str, Any], data_provider=None):
        super().__init__(execution_mode, config)
        
        # Store data provider for liquidity index queries
        self.data_provider = data_provider
        
        # Initialize Web3 clients for live mode
        if execution_mode == 'live':
            self._init_web3_clients()
        else:
            self.web3_clients = {}
            self.contracts = {}
    
    def _init_web3_clients(self):
        """Initialize Web3 clients and contracts for live mode."""
        try:
            from web3 import Web3
            from web3.middleware import geth_poa_middleware
            
            self.web3_clients = {}
            self.contracts = {}
            
            # Ethereum mainnet
            if self.config.get('alchemy_api_key'):
                w3 = Web3(Web3.HTTPProvider(f"https://eth-mainnet.g.alchemy.com/v2/{self.config['alchemy_api_key']}"))
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                self.web3_clients['ethereum'] = w3
            
            # Initialize contracts
            self._init_contracts()
            
            logger.info(f"Initialized {len(self.web3_clients)} Web3 clients: {list(self.web3_clients.keys())}")
            
        except ImportError:
            logger.error("Web3.py not installed. Install with: pip install web3")
            self.web3_clients = {}
            self.contracts = {}
        except Exception as e:
            logger.error(f"Failed to initialize Web3 clients: {e}")
            self.web3_clients = {}
            self.contracts = {}
    
    def _init_contracts(self):
        """Initialize smart contract instances."""
        # This would load contract ABIs and addresses
        # For now, just placeholder
        self.contracts = {
            'aave_v3': None,
            'uniswap_v3': None,
            'lido': None,
            'etherfi': None
        }
    
    async def execute_trade(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an on-chain operation.
        
        Args:
            instruction: Operation instruction
            market_data: Current market data
            
        Returns:
            Execution result
        """
        operation = instruction.get('operation', 'TRANSFER')
        
        if self.execution_mode == 'backtest':
            return await self._execute_backtest_operation(instruction, market_data)
        else:
            return await self._execute_live_operation(instruction, market_data)
    
    async def _execute_backtest_operation(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute simulated operation for backtest mode."""
        operation = instruction.get('operation', 'TRANSFER')
        token_in = instruction.get('token_in', 'ETH')
        token_out = instruction.get('token_out', 'ETH')
        amount = instruction.get('amount', 0.0)
        
        # Calculate gas cost
        gas_cost = self._get_gas_cost(operation, market_data)
        
        # Handle specific operations
        if operation == 'AAVE_SUPPLY':
            # AAVE supply: USDT → aUSDT conversion
            # In backtest mode, we need to use the correct liquidity index for the conversion
            if token_out == 'aUSDT':
                # Get the correct liquidity index using centralized utility
                from ..utils.market_data_utils import get_market_data_utils
                market_utils = get_market_data_utils(self.data_provider)
                
                if market_data and 'timestamp' in market_data:
                    liquidity_index = market_utils.get_liquidity_index('USDT', market_data.get('timestamp'))
                else:
                    # Fallback: use a default liquidity index if market_data is not available
                    logger.warning("Market data not available for liquidity index lookup, using default value")
                    liquidity_index = 1.070100  # Default value for backtest period
                
                amount_out = amount / liquidity_index
                logger.info(f"Onchain Execution: AAVE_SUPPLY USDT->aUSDT: {amount} USDT / {liquidity_index:.6f} = {amount_out:.2f} aUSDT")
                onchain_interface_logger.info(f"Onchain Execution: AAVE_SUPPLY USDT->aUSDT: {amount} USDT / {liquidity_index:.6f} = {amount_out:.2f} aUSDT")
            else:
                # For other tokens, use 1:1 ratio (this should be updated for other tokens too)
                amount_out = amount
                logger.info(f"Onchain Execution: AAVE_SUPPLY {token_in}->{token_out}: {amount} -> {amount_out} (1:1 ratio)")
                onchain_interface_logger.info(f"Onchain Execution: AAVE_SUPPLY {token_in}->{token_out}: {amount} -> {amount_out} (1:1 ratio)")
            
            result = {
                'status': 'SUCCESS',
                'operation': operation,
                'token_in': token_in,
                'token_out': token_out,
                'amount_in': amount,
                'amount_out': amount_out,  # Correct conversion using liquidity index
                'gas_cost': gas_cost,
                'gas_used': 150000,  # AAVE supply gas limit
                'gas_price': market_data.get('gas_price_gwei', 20.0),
                'timestamp': datetime.now(timezone.utc),
                'tx_hash': f"backtest_{operation}_{token_in}_{int(datetime.now().timestamp())}",
                'execution_mode': 'backtest',
                'liquidity_index': liquidity_index if token_out == 'aUSDT' else 1.0
            }
            
            # Update position monitor with proper token conversion
            await self._update_position_monitor({
                'operation': operation,
                'token_in': token_in,
                'token_out': token_out,
                'amount_in': amount,
                'amount_out': amount_out,  # Use the correct amount_out
                'gas_cost': gas_cost
            })
        else:
            # Generic operation
            result = {
                'status': 'SUCCESS',
                'operation': operation,
                'token': token_in,
                'amount': amount,
                'gas_cost': gas_cost,
                'gas_used': 21000,  # Default gas limit
                'gas_price': market_data.get('gas_price_gwei', 20.0),
                'timestamp': datetime.now(timezone.utc),
                'tx_hash': f"backtest_{operation}_{token_in}_{int(datetime.now().timestamp())}",
                'execution_mode': 'backtest'
            }
            
            # Update position monitor
            await self._update_position_monitor({
                'operation': operation,
                'token': token_in,
                'amount': amount,
                'gas_cost': gas_cost
            })
        
        # Log event
        await self._log_execution_event('ONCHAIN_OPERATION_EXECUTED', result)
        
        return result
    
    async def _execute_live_operation(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute real operation for live mode."""
        operation = instruction.get('operation', 'TRANSFER')
        token = instruction.get('token', 'ETH')
        amount = instruction.get('amount', 0.0)
        
        if 'ethereum' not in self.web3_clients:
            raise ValueError("Ethereum Web3 client not available")
        
        w3 = self.web3_clients['ethereum']
        
        try:
            # Get gas price
            gas_price = w3.eth.gas_price
            
            # Build transaction based on operation
            tx = await self._build_transaction(instruction, market_data)
            
            # Sign and send transaction
            # Note: This would require wallet integration
            # For now, simulate the transaction
            
            result = {
                'status': 'SUCCESS',
                'operation': operation,
                'token': token,
                'amount': amount,
                'gas_cost': gas_price * tx.get('gas', 21000),
                'gas_used': tx.get('gas', 21000),
                'gas_price': gas_price,
                'timestamp': datetime.now(timezone.utc),
                'tx_hash': f"0x{'0' * 64}",  # Placeholder
                'execution_mode': 'live'
            }
            
            # Log event
            await self._log_execution_event('ONCHAIN_OPERATION_EXECUTED', result)
            
            # Update position monitor
            await self._update_position_monitor({
                'operation': operation,
                'token': token,
                'amount': amount,
                'gas_cost': result['gas_cost']
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute live operation: {e}")
            raise
    
    async def _build_transaction(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build transaction for live execution."""
        operation = instruction.get('operation', 'TRANSFER')
        
        # This would build the actual transaction based on operation type
        # For now, return a placeholder
        return {
            'to': '0x' + '0' * 40,  # Placeholder address
            'value': 0,
            'gas': 21000,
            'data': b''
        }
    
    async def get_balance(self, asset: str, venue: Optional[str] = None) -> float:
        """Get current balance for an asset."""
        if self.execution_mode == 'backtest':
            return await self._get_backtest_balance(asset, venue)
        else:
            return await self._get_live_balance(asset, venue)
    
    async def _get_backtest_balance(self, asset: str, venue: Optional[str] = None) -> float:
        """Get simulated balance for backtest mode."""
        if self.position_monitor:
            return self.position_monitor.get_balance(asset, venue)
        return 0.0
    
    async def _get_live_balance(self, asset: str, venue: Optional[str] = None) -> float:
        """Get real balance for live mode."""
        if 'ethereum' not in self.web3_clients:
            return 0.0
        
        w3 = self.web3_clients['ethereum']
        
        try:
            # This would get the actual balance from the blockchain
            # For now, return 0
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0
    
    async def get_position(self, symbol: str, venue: Optional[str] = None) -> Dict[str, Any]:
        """Get current position for a trading pair."""
        if self.execution_mode == 'backtest':
            return await self._get_backtest_position(symbol, venue)
        else:
            return await self._get_live_position(symbol, venue)
    
    async def _get_backtest_position(self, symbol: str, venue: Optional[str] = None) -> Dict[str, Any]:
        """Get simulated position for backtest mode."""
        if self.position_monitor:
            return self.position_monitor.get_position(symbol, venue)
        return {'amount': 0.0, 'side': 'NONE'}
    
    async def _get_live_position(self, symbol: str, venue: Optional[str] = None) -> Dict[str, Any]:
        """Get real position for live mode."""
        # This would query the actual on-chain position
        # For now, return empty position
        return {'amount': 0.0, 'side': 'NONE'}
    
    async def cancel_all_orders(self, venue: Optional[str] = None) -> Dict[str, Any]:
        """Cancel all open orders (not applicable for on-chain)."""
        return {
            'status': 'SUCCESS',
            'message': 'No orders to cancel for on-chain operations',
            'execution_mode': self.execution_mode
        }
    
    async def execute_transfer(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a cross-venue transfer (on-chain specific).
        
        Args:
            instruction: Transfer instruction
            market_data: Current market data
            
        Returns:
            Transfer execution result
        """
        operation = instruction.get('operation', 'TRANSFER')
        token = instruction.get('token', 'ETH')
        amount = instruction.get('amount', 0.0)
        venue = instruction.get('venue', 'AAVE')
        
        if self.execution_mode == 'backtest':
            return await self._execute_backtest_transfer(operation, token, amount, venue, market_data)
        else:
            return await self._execute_live_transfer(operation, token, amount, venue, market_data)
    
    async def _execute_backtest_transfer(
        self, 
        operation: str, 
        token: str, 
        amount: float, 
        venue: str, 
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute simulated on-chain transfer for backtest mode."""
        # Calculate gas cost
        gas_cost = self._get_gas_cost(operation, market_data)
        
        result = {
            'status': 'COMPLETED',
            'operation': operation,
            'token': token,
            'amount': amount,
            'venue': venue,
            'gas_cost': gas_cost,
            'gas_used': 21000,  # Default gas limit
            'gas_price': market_data.get('gas_price_gwei', 20.0),
            'timestamp': datetime.now(timezone.utc),
            'execution_mode': 'backtest',
            'transfer_id': f"backtest_onchain_{venue}_{token}_{int(datetime.now().timestamp())}"
        }
        
        # Log event
        await self._log_execution_event('ONCHAIN_TRANSFER_EXECUTED', result)
        
        # Update position monitor
        await self._update_position_monitor({
            'operation': operation,
            'token': token,
            'amount': amount,
            'venue': venue,
            'gas_cost': gas_cost
        })
        
        return result
    
    async def _execute_live_transfer(
        self, 
        operation: str, 
        token: str, 
        amount: float, 
        venue: str, 
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute real on-chain transfer for live mode."""
        if 'ethereum' not in self.web3_clients:
            raise ValueError("Ethereum Web3 client not available")
        
        w3 = self.web3_clients['ethereum']
        
        try:
            # Get gas price
            gas_price = w3.eth.gas_price
            
            # Build transaction based on operation
            tx = await self._build_transfer_transaction(operation, token, amount, venue, market_data)
            
            # Sign and send transaction
            # Note: This would require wallet integration
            # For now, simulate the transaction
            
            result = {
                'status': 'COMPLETED',
                'operation': operation,
                'token': token,
                'amount': amount,
                'venue': venue,
                'gas_cost': gas_price * tx.get('gas', 21000),
                'gas_used': tx.get('gas', 21000),
                'gas_price': gas_price,
                'timestamp': datetime.now(timezone.utc),
                'execution_mode': 'live',
                'transfer_id': f"live_onchain_{venue}_{token}_{int(datetime.now().timestamp())}",
                'tx_hash': f"0x{'0' * 64}"  # Placeholder
            }
            
            # Log event
            await self._log_execution_event('ONCHAIN_TRANSFER_EXECUTED', result)
            
            # Update position monitor
            await self._update_position_monitor({
                'operation': operation,
                'token': token,
                'amount': amount,
                'venue': venue,
                'gas_cost': result['gas_cost']
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute on-chain transfer: {e}")
            raise
    
    async def _build_transfer_transaction(
        self, 
        operation: str, 
        token: str, 
        amount: float, 
        venue: str, 
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build transaction for on-chain transfer."""
        # This would build the actual transaction based on operation type
        # For now, return a placeholder
        return {
            'to': '0x' + '0' * 40,  # Placeholder address
            'value': 0,
            'gas': 21000,
            'data': b''
        }
