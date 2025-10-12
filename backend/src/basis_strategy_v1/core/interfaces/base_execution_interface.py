"""
Base Execution Interface

Abstract base class for all execution interfaces.
Defines the contract that all execution implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class BaseExecutionInterface(ABC):
    """
    Abstract base class for execution interfaces.
    
    Provides the contract that all execution implementations must follow,
    enabling seamless switching between backtest and live modes.
    """
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        """
        Initialize execution interface.
        
        Args:
            execution_mode: 'backtest' or 'live'
            config: Configuration dictionary
        """
        self.execution_mode = execution_mode
        self.config = config
        self.position_monitor = None
        self.event_logger = None
        self.data_provider = None
        
        logger.info(f"{self.__class__.__name__} initialized in {execution_mode} mode")
    
    def set_dependencies(self, position_monitor, event_logger, data_provider):
        """Set component dependencies."""
        self.position_monitor = position_monitor
        self.event_logger = event_logger
        self.data_provider = data_provider
    
    @abstractmethod
    async def execute_trade(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade instruction.
        
        Args:
            instruction: Trade instruction dictionary
            market_data: Current market data snapshot
            
        Returns:
            Execution result dictionary
        """
        pass
    
    @abstractmethod
    async def get_balance(self, asset: str, venue: Optional[str] = None) -> float:
        """
        Get current balance for an asset.
        
        Args:
            asset: Asset symbol (e.g., 'ETH', 'USDT')
            venue: Venue name (for CEX) or None (for on-chain)
            
        Returns:
            Current balance
        """
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str, venue: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current position for a trading pair.
        
        Args:
            symbol: Trading pair symbol (e.g., 'ETH/USDT', 'ETHUSDT-PERP')
            venue: Venue name (for CEX) or None (for on-chain)
            
        Returns:
            Position information dictionary
        """
        pass
    
    @abstractmethod
    async def cancel_all_orders(self, venue: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel all open orders.
        
        Args:
            venue: Venue name (for CEX) or None (for on-chain)
            
        Returns:
            Cancellation result dictionary
        """
        pass
    
    @abstractmethod
    async def execute_transfer(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a cross-venue transfer.
        
        Args:
            instruction: Transfer instruction dictionary
            market_data: Current market data snapshot
            
        Returns:
            Transfer execution result dictionary
        """
        pass
    
    async def _log_execution_event(self, event_type: str, details: Dict[str, Any]):
        """Log execution event."""
        if self.event_logger:
            await self.event_logger.log_event(
                event_type=event_type,
                details=details,
                timestamp=datetime.now(timezone.utc),
                venue=details.get('venue', 'system'),
                token=details.get('token', None)
            )
    
    def _update_position_monitor(self, changes: Dict[str, Any]):
        """Update position monitor with execution changes."""
        if self.position_monitor:
            # Format changes for position monitor
            formatted_changes = self._format_changes_for_position_monitor(changes)
            self.position_monitor.update_state(
                changes.get('timestamp', pd.Timestamp.now()),
                'execution_interface',
                **formatted_changes
            )
    
    def _format_changes_for_position_monitor(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Format execution changes for position monitor."""
        operation = changes.get('operation', 'UNKNOWN')
        
        if operation == 'AAVE_SUPPLY':
            # AAVE supply: USDT → aUSDT conversion
            token_in = changes.get('token_in', 'USDT')
            token_out = changes.get('token_out', 'aUSDT')
            amount_in = changes.get('amount_in', 0)
            amount_out = changes.get('amount_out', 0)
            gas_cost = changes.get('gas_cost', 0)
            
            return {
                'timestamp': pd.Timestamp.now(tz='UTC'),
                'trigger': 'AAVE_SUPPLY',
                'token_changes': [
                    {
                        'venue': 'WALLET',
                        'token': token_in,
                        'delta': -amount_in,  # Remove USDT
                        'reason': 'AAVE_SUPPLY_INPUT'
                    },
                    {
                        'venue': 'WALLET',
                        'token': token_out,
                        'delta': +amount_out,  # Add aUSDT
                        'reason': 'AAVE_SUPPLY_OUTPUT'
                    },
                    {
                        'venue': 'WALLET',
                        'token': 'ETH',
                        'delta': -gas_cost,  # Gas fee
                        'reason': 'GAS_FEE'
                    }
                ],
                'derivative_changes': []
            }
        else:
            # Generic operation
            token = changes.get('token', 'ETH')
            amount = changes.get('amount', 0)
            gas_cost = changes.get('gas_cost', 0)
            
            return {
                'timestamp': pd.Timestamp.now(tz='UTC'),
                'trigger': operation,
                'token_changes': [
                    {
                        'venue': 'WALLET',
                        'token': token,
                        'delta': amount,
                        'reason': operation
                    },
                    {
                        'venue': 'WALLET',
                        'token': 'ETH',
                        'delta': -gas_cost,
                        'reason': 'GAS_FEE'
                    }
                ],
                'derivative_changes': []
            }
    
    def _get_execution_cost(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """Get execution cost for instruction."""
        try:
            logger.debug(f"Base Interface: _get_execution_cost called with instruction type: {type(instruction)}")
            logger.debug(f"Base Interface: instruction keys: {list(instruction.keys()) if hasattr(instruction, 'keys') else 'Not a dict'}")
            
            if self.data_provider:
                pair = instruction.get('pair', '')
                amount = instruction.get('amount', 0)
                venue = instruction.get('venue', '')
                trade_type = instruction.get('trade_type', 'SPOT')
                eth_price = market_data.get('eth_usd_price', 0)
                notional = amount * eth_price
                
                logger.debug(f"Base Interface: Getting execution cost using canonical pattern for pair={pair}, notional={notional}, venue={venue}, trade_type={trade_type}")
                
                # Get data using canonical pattern
                data = self.data_provider.get_data(market_data.get('timestamp'))
                execution_costs = data['execution_data']['execution_costs']
                
                # Look for the specific execution cost
                cost_key = f"{pair}_{venue}_{trade_type}"
                if cost_key in execution_costs:
                    return execution_costs[cost_key]
                elif pair in execution_costs:
                    return execution_costs[pair]
                else:
                    return 0.0  # Default if not found
            return 0.0
            
        except Exception as e:
            logger.error(f"Base Interface: _get_execution_cost failed: {e}")
            logger.error(f"Base Interface: instruction: {instruction}")
            logger.error(f"Base Interface: market_data keys: {list(market_data.keys()) if hasattr(market_data, 'keys') else 'Not a dict'}")
            raise
    
    def _get_gas_cost(self, operation: str, market_data: Dict[str, Any]) -> float:
        """Get gas cost for operation using canonical pattern."""
        if self.data_provider:
            timestamp = market_data.get('timestamp')
            if timestamp is None:
                # Use current timestamp if not provided
                timestamp = pd.Timestamp.now(tz='UTC')
            
            # Get data using canonical pattern
            data = self.data_provider.get_data(timestamp)
            gas_costs = data['execution_data']['gas_costs']
            
            # Look for the specific operation gas cost
            if operation in gas_costs:
                return gas_costs[operation]
            else:
                return 0.0  # Default if not found
        return 0.001  # Default 0.001 ETH
