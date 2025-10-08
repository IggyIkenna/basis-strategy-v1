"""
Transfer Execution Interface

Provides cross-venue transfer capabilities for both backtest and live modes.
Integrates with the CrossVenueTransferManager for sophisticated transfer logic.
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

# Create dedicated Transfer execution interface logger
transfer_interface_logger = logging.getLogger('transfer_execution_interface')
transfer_interface_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent.parent.parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Create file handler for Transfer execution interface logs
transfer_interface_handler = logging.FileHandler(logs_dir / 'transfer_execution_interface.log')
transfer_interface_handler.setLevel(logging.INFO)

# Create formatter
transfer_interface_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
transfer_interface_handler.setFormatter(transfer_interface_formatter)

# Add handler to logger
transfer_interface_logger.addHandler(transfer_interface_handler)

# Error codes for Transfer Execution Interface
ERROR_CODES = {
    'TRANSFER-IF-001': 'Transfer execution failed',
    'TRANSFER-IF-002': 'Transfer manager not initialized',
    'TRANSFER-IF-003': 'Transfer planning failed',
    'TRANSFER-IF-004': 'Transfer trade execution failed',
    'TRANSFER-IF-005': 'Transfer completion failed',
    'TRANSFER-IF-006': 'Transfer interface connection failed',
    'TRANSFER-IF-007': 'Transfer mapping failed'
}


class TransferExecutionInterface(BaseExecutionInterface):
    """
    Transfer execution interface for cross-venue operations.
    
    Supports both backtest (simulated) and live (real) transfer execution modes.
    Integrates with CrossVenueTransferManager for sophisticated transfer logic.
    """
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        super().__init__(execution_mode, config)
        
        # Initialize transfer manager
        self._init_transfer_manager()
    
    def _init_transfer_manager(self):
        """Initialize the cross-venue transfer manager."""
        try:
            from ..rebalancing.transfer_manager import CrossVenueTransferManager
            
            # Create a mock portfolio for the transfer manager
            # In a real implementation, this would come from the position monitor
            mock_portfolio = {
                'positions': {},
                'initial_capital': self.config.get('initial_capital', 100000)
            }
            
            self.transfer_manager = CrossVenueTransferManager(self.config, mock_portfolio)
            logger.info("Transfer manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize transfer manager: {e}")
            self.transfer_manager = None
    
    async def execute_trade(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade instruction (not applicable for transfers).
        
        Args:
            instruction: Trade instruction
            market_data: Current market data
            
        Returns:
            Execution result
        """
        raise NotImplementedError("TransferExecutionInterface does not support direct trades. Use execute_transfer() instead.")
    
    async def execute_transfer(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a cross-venue transfer.
        
        Args:
            instruction: Transfer instruction
            market_data: Current market data
            
        Returns:
            Transfer execution result
        """
        if not self.transfer_manager:
            raise ValueError("Transfer manager not initialized")
        
        source_venue = instruction.get('source_venue')
        target_venue = instruction.get('target_venue')
        amount_usd = instruction.get('amount_usd', 0.0)
        purpose = instruction.get('purpose', 'Transfer')
        
        if self.execution_mode == 'backtest':
            return await self._execute_backtest_transfer(source_venue, target_venue, amount_usd, market_data, purpose)
        else:
            return await self._execute_live_transfer(source_venue, target_venue, amount_usd, market_data, purpose)
    
    async def _execute_backtest_transfer(
        self, 
        source_venue: str, 
        target_venue: str, 
        amount_usd: float, 
        market_data: Dict[str, Any], 
        purpose: str
    ) -> Dict[str, Any]:
        """Execute simulated transfer for backtest mode."""
        try:
            # Use transfer manager to plan the transfer
            trades = await self.transfer_manager.execute_optimal_transfer(
                source_venue, target_venue, amount_usd, market_data, purpose
            )
            
            # Simulate execution of each trade
            executed_trades = []
            total_cost = 0.0
            
            for trade in trades:
                # Simulate trade execution
                execution_result = {
                    'trade_id': f"backtest_{trade.trade_type}_{int(datetime.now().timestamp())}",
                    'status': 'EXECUTED',
                    'venue': trade.venue,
                    'trade_type': trade.trade_type,
                    'token': trade.token,
                    'amount': float(trade.amount),
                    'side': trade.side,
                    'purpose': trade.purpose,
                    'fee': trade.expected_fee,
                    'timestamp': datetime.now(timezone.utc),
                    'execution_mode': 'backtest'
                }
                
                executed_trades.append(execution_result)
                total_cost += trade.expected_fee
                
                # Log event
                await self._log_execution_event('TRANSFER_TRADE_EXECUTED', execution_result)
                
                # Update position monitor
                await self._update_position_monitor({
                    'venue': trade.venue,
                    'token': trade.token,
                    'side': trade.side,
                    'amount': float(trade.amount),
                    'trade_type': trade.trade_type
                })
            
            result = {
                'status': 'COMPLETED',
                'source_venue': source_venue,
                'target_venue': target_venue,
                'amount_usd': amount_usd,
                'purpose': purpose,
                'total_cost': total_cost,
                'trades_executed': len(executed_trades),
                'executed_trades': executed_trades,
                'timestamp': datetime.now(timezone.utc),
                'execution_mode': 'backtest'
            }
            
            # Log transfer completion
            await self._log_execution_event('TRANSFER_COMPLETED', result)
            
            return result
            
        except Exception as e:
            logger.error(f"Backtest transfer execution failed: {e}")
            raise
    
    async def _execute_live_transfer(
        self, 
        source_venue: str, 
        target_venue: str, 
        amount_usd: float, 
        market_data: Dict[str, Any], 
        purpose: str
    ) -> Dict[str, Any]:
        """Execute real transfer for live mode."""
        try:
            # Use transfer manager to plan the transfer
            trades = await self.transfer_manager.execute_optimal_transfer(
                source_venue, target_venue, amount_usd, market_data, purpose
            )
            
            # Execute each trade sequentially (waiting for completion)
            executed_trades = []
            total_cost = 0.0
            
            for trade in trades:
                # Execute trade using appropriate execution interface
                execution_result = await self._execute_live_trade(trade, market_data)
                
                executed_trades.append(execution_result)
                total_cost += execution_result.get('fee', 0.0)
                
                # Log event
                await self._log_execution_event('TRANSFER_TRADE_EXECUTED', execution_result)
                
                # Update position monitor
                await self._update_position_monitor({
                    'venue': trade.venue,
                    'token': trade.token,
                    'side': trade.side,
                    'amount': float(trade.amount),
                    'trade_type': trade.trade_type
                })
                
                # Wait for completion before next step (live mode requirement)
                if execution_result.get('status') != 'COMPLETED':
                    raise Exception(f"Trade execution failed: {execution_result}")
            
            result = {
                'status': 'COMPLETED',
                'source_venue': source_venue,
                'target_venue': target_venue,
                'amount_usd': amount_usd,
                'purpose': purpose,
                'total_cost': total_cost,
                'trades_executed': len(executed_trades),
                'executed_trades': executed_trades,
                'timestamp': datetime.now(timezone.utc),
                'execution_mode': 'live'
            }
            
            # Log transfer completion
            await self._log_execution_event('TRANSFER_COMPLETED', result)
            
            return result
            
        except Exception as e:
            logger.error(f"Live transfer execution failed: {e}")
            raise
    
    async def _execute_live_trade(self, trade, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single trade in live mode using appropriate execution interface."""
        # This would delegate to the appropriate execution interface (CEX or OnChain)
        # based on the trade type and venue
        
        if trade.venue in ['BINANCE', 'BYBIT', 'OKX']:
            # Use CEX execution interface
            if hasattr(self, 'cex_interface') and self.cex_interface:
                return await self.cex_interface.execute_trade({
                    'venue': trade.venue.lower(),
                    'trade_type': self._map_trade_type_to_cex(trade.trade_type),
                    'pair': f"{trade.token}/USDT",
                    'side': self._map_side_to_cex(trade.side),
                    'amount': float(trade.amount)
                }, market_data)
            else:
                raise ValueError(f"CEX execution interface not available for venue: {trade.venue}")
        
        elif trade.venue in ['AAVE', 'ETHERFI', 'LIDO']:
            # Use OnChain execution interface
            if hasattr(self, 'onchain_interface') and self.onchain_interface:
                return await self.onchain_interface.execute_trade({
                    'operation': self._map_trade_type_to_onchain(trade.trade_type),
                    'token': trade.token,
                    'amount': float(trade.amount),
                    'venue': trade.venue
                }, market_data)
            else:
                raise ValueError(f"OnChain execution interface not available for venue: {trade.venue}")
        
        else:
            raise ValueError(f"Unknown venue: {trade.venue}")
    
    def _map_trade_type_to_cex(self, trade_type: str) -> str:
        """Map transfer manager trade types to CEX trade types."""
        mapping = {
            'venue_transfer': 'SPOT',
            'lending_withdrawal': 'SPOT',
            'lending_deposit': 'SPOT',
            'unstaking': 'SPOT'
        }
        return mapping.get(trade_type, 'SPOT')
    
    def _map_side_to_cex(self, side: str) -> str:
        """Map transfer manager sides to CEX sides."""
        mapping = {
            'withdraw': 'SELL',
            'deposit': 'BUY',
            'unstake': 'SELL'
        }
        return mapping.get(side, 'BUY')
    
    def _map_trade_type_to_onchain(self, trade_type: str) -> str:
        """Map transfer manager trade types to on-chain operations."""
        mapping = {
            'lending_withdrawal': 'AAVE_WITHDRAW',
            'lending_deposit': 'AAVE_SUPPLY',
            'unstaking': 'UNSTAKE',
            'venue_transfer': 'TRANSFER'
        }
        return mapping.get(trade_type, 'TRANSFER')
    
    def set_execution_interfaces(self, cex_interface, onchain_interface):
        """Set the CEX and OnChain execution interfaces for live mode."""
        self.cex_interface = cex_interface
        self.onchain_interface = onchain_interface
        logger.info("Transfer execution interface connected to CEX and OnChain interfaces")
    
    async def get_balance(self, asset: str, venue: Optional[str] = None) -> float:
        """Get current balance for an asset."""
        # This would delegate to the appropriate execution interface
        if venue in ['BINANCE', 'BYBIT', 'OKX']:
            if hasattr(self, 'cex_interface') and self.cex_interface:
                return await self.cex_interface.get_balance(asset, venue.lower())
        elif venue in ['AAVE', 'ETHERFI', 'LIDO']:
            if hasattr(self, 'onchain_interface') and self.onchain_interface:
                return await self.onchain_interface.get_balance(asset, venue)
        
        return 0.0
    
    async def get_position(self, symbol: str, venue: Optional[str] = None) -> Dict[str, Any]:
        """Get current position for a trading pair."""
        # This would delegate to the appropriate execution interface
        if venue in ['BINANCE', 'BYBIT', 'OKX']:
            if hasattr(self, 'cex_interface') and self.cex_interface:
                return await self.cex_interface.get_position(symbol, venue.lower())
        elif venue in ['AAVE', 'ETHERFI', 'LIDO']:
            if hasattr(self, 'onchain_interface') and self.onchain_interface:
                return await self.onchain_interface.get_position(symbol, venue)
        
        return {'amount': 0.0, 'side': 'NONE'}
    
    async def cancel_all_orders(self, venue: Optional[str] = None) -> Dict[str, Any]:
        """Cancel all open orders (not applicable for transfers)."""
        return {
            'status': 'SUCCESS',
            'message': 'No orders to cancel for transfer operations',
            'execution_mode': self.execution_mode
        }
