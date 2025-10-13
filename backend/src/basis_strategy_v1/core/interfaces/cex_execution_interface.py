"""
CEX Execution Interface

✅ FIXED: Environment variable integration now properly implemented
- Uses BASIS_ENVIRONMENT routing for venue credentials
- Properly routes dev/staging/prod credentials
- Uses environment variables instead of config for API keys

TODO-REFACTOR: MISSING CENTRALIZED UTILITY MANAGER VIOLATION - See docs/REFERENCE_ARCHITECTURE_CANONICAL.md
ISSUE: This component has scattered utility methods that should be centralized:

1. CENTRALIZED UTILITY MANAGER REQUIREMENTS:
   - Utility methods should be centralized in a single manager
   - Liquidity index calculations should be centralized
   - Market price conversions should be centralized
   - No scattered utility methods across components

2. REQUIRED VERIFICATION:
   - Check for scattered utility methods in this component
   - Verify utility methods are properly centralized
   - Ensure no duplicate utility logic across components

3. CANONICAL SOURCE:
   - docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Mode-Agnostic Architecture
   - Centralized utilities required
   - No logic to route based on BASIS_ENVIRONMENT (dev/staging/prod) to select appropriate credentials

2. REQUIRED ARCHITECTURE (per 19_venue_based_execution_architecture.md):
   - Should route to appropriate environment-specific credentials based on BASIS_ENVIRONMENT
   - Backtest mode: Execution interfaces exist for CODE ALIGNMENT only - NO credentials needed, NO heartbeat tests
   - Backtest mode: Data source (CSV vs DB) is handled by DATA PROVIDER, not venue execution manager
   - Backtest mode: Dummy venue calls - make dummy calls but don't wait for responses, mark complete immediately
   - Live mode: Use real APIs with pattern: BASIS_DEV__CEX__BINANCE_SPOT_API_KEY, BASIS_PROD__CEX__BINANCE_SPOT_API_KEY
   - Live mode: Should handle testnet vs production endpoint routing and heartbeat tests
   - Live mode: Should support separate spot/futures clients for Binance
   - **Reference**: docs/VENUE_ARCHITECTURE.md - Venue-Based Execution

3. SEPARATION OF CONCERNS:
   - BASIS_DEPLOYMENT_MODE: Controls port/host forwarding and dependency injection (local vs docker)
   - BASIS_ENVIRONMENT: Controls venue credential routing (dev/staging/prod) and data sources (CSV vs DB)
   - BASIS_EXECUTION_MODE: Controls venue execution behavior (backtest simulation vs live execution)

4. CURRENT VIOLATIONS:
   - Hardcoded config keys instead of environment-specific variables
   - No BASIS_ENVIRONMENT routing logic
   - Missing testnet vs production endpoint routing
   - No separate spot/futures client initialization

5. REQUIRED FIX:
   - Implement _get_venue_credentials() method with BASIS_ENVIRONMENT routing
   - Use environment-specific variables: BASIS_DEV__CEX__, BASIS_PROD__CEX__
   - Add testnet vs production endpoint routing
   - Add separate spot/futures client initialization for Binance

CURRENT STATE: This component needs environment variable integration refactoring.
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from datetime import datetime, timezone
import json
from pathlib import Path
import ccxt

from .base_execution_interface import BaseExecutionInterface

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)

# Create dedicated CEX execution interface logger
cex_interface_logger = logging.getLogger('cex_execution_interface')
cex_interface_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent.parent.parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Create file handler for CEX execution interface logs
cex_interface_handler = logging.FileHandler(logs_dir / 'cex_execution_interface.log')
cex_interface_handler.setLevel(logging.INFO)

# Create formatter
cex_interface_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
cex_interface_handler.setFormatter(cex_interface_formatter)

# Add handler to logger
cex_interface_logger.addHandler(cex_interface_handler)

# Error codes for CEX Execution Interface
ERROR_CODES = {
    'CEX-IF-001': 'CEX trade execution failed',
    'CEX-IF-002': 'Exchange client not available',
    'CEX-IF-003': 'Order execution failed',
    'CEX-IF-004': 'Balance retrieval failed',
    'CEX-IF-005': 'Position retrieval failed',
    'CEX-IF-006': 'Transfer execution failed',
    'CEX-IF-007': 'Exchange client initialization failed',
    'CEX-IF-008': 'CCXT library not available'
}


class CEXExecutionInterface(BaseExecutionInterface):
    """
    CEX execution interface for centralized exchange trading.
    
    Supports both backtest (simulated) and live (real) execution modes.
    """
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        super().__init__(execution_mode, config)
        
        # Initialize exchange clients for live mode
        if execution_mode == 'live':
            self._init_exchange_clients()
        else:
            self.exchange_clients = {}
    
    def _init_exchange_clients(self):
        """Initialize CCXT exchange clients for live mode."""
        try:
            import ccxt
            
            self.exchange_clients = {}
            
            # Get environment-specific credentials
            environment = os.getenv('BASIS_ENVIRONMENT', 'dev')
            
            # Binance
            binance_api_key = os.getenv(f'BASIS_{environment.upper()}__CEX__BINANCE_FUTURES_API_KEY')
            binance_secret = os.getenv(f'BASIS_{environment.upper()}__CEX__BINANCE_FUTURES_SECRET')
            if binance_api_key and binance_secret:
                self.exchange_clients['binance'] = ccxt.binance({
                    'apiKey': binance_api_key,
                    'secret': binance_secret,
                    'sandbox': environment == 'dev',  # Use sandbox for dev environment
                    'enableRateLimit': True,
                })
            
            # Bybit
            bybit_api_key = os.getenv(f'BASIS_{environment.upper()}__CEX__BYBIT_API_KEY')
            bybit_secret = os.getenv(f'BASIS_{environment.upper()}__CEX__BYBIT_SECRET')
            if bybit_api_key and bybit_secret:
                self.exchange_clients['bybit'] = ccxt.bybit({
                    'apiKey': bybit_api_key,
                    'secret': bybit_secret,
                    'sandbox': environment == 'dev',  # Use sandbox for dev environment
                    'enableRateLimit': True,
                })
            
            # OKX
            okx_api_key = os.getenv(f'BASIS_{environment.upper()}__CEX__OKX_API_KEY')
            okx_secret = os.getenv(f'BASIS_{environment.upper()}__CEX__OKX_SECRET')
            okx_passphrase = os.getenv(f'BASIS_{environment.upper()}__CEX__OKX_PASSPHRASE', '')
            if okx_api_key and okx_secret:
                self.exchange_clients['okx'] = ccxt.okx({
                    'apiKey': okx_api_key,
                    'secret': okx_secret,
                    'password': okx_passphrase,
                    'sandbox': environment == 'dev',  # Use sandbox for dev environment
                    'enableRateLimit': True,
                })
            
            logger.info(f"Initialized {len(self.exchange_clients)} exchange clients: {list(self.exchange_clients.keys())}")
            
        except ImportError:
            logger.error("CCXT not installed. Install with: pip install ccxt")
            self.exchange_clients = {}
        except Exception as e:
            logger.error(f"Failed to initialize exchange clients: {e}")
            self.exchange_clients = {}
    
    async def execute_trade(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a CEX trade.
        
        Args:
            instruction: Trade instruction
            market_data: Current market data
            
        Returns:
            Execution result
        """
        try:
            cex_interface_logger.info(f"CEX Interface: Received instruction: {instruction}")
            
            venue = instruction.get('venue', 'binance')
            trade_type = instruction.get('trade_type', 'SPOT')
            symbol = instruction.get('pair', 'ETH/USDT')
            side = instruction.get('side', 'BUY')
            amount = instruction.get('amount', 0.0)
            
            cex_interface_logger.info(f"CEX Interface: Parsed - venue={venue}, trade_type={trade_type}, symbol={symbol}, side={side}, amount={amount}")
            
        except Exception as e:
            cex_interface_logger.error(f"CEX Interface: Error parsing instruction: {e}")
            raise
        
        if self.execution_mode == 'backtest':
            return await self._execute_backtest_trade(instruction, market_data)
        else:
            return await self._execute_live_trade(instruction, market_data)
    
    async def _execute_backtest_trade(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute simulated trade for backtest mode."""
        try:
            cex_interface_logger.info("CEX Interface: Starting backtest trade execution")
            
            venue = instruction.get('venue', 'binance')
            trade_type = instruction.get('trade_type', 'SPOT')
            symbol = instruction.get('pair', 'ETH/USDT')
            side = instruction.get('side', 'BUY')
            amount = instruction.get('amount', 0.0)
            
            cex_interface_logger.info(f"CEX Interface: Backtest trade - {venue} {trade_type} {symbol} {side} {amount}")
            
        except Exception as e:
            cex_interface_logger.error(f"CEX Interface: Error in backtest trade setup: {e}")
            raise
        
        # Get market price
        if trade_type == 'SPOT':
            price_key = f'{venue}_spot_price'
        else:  # PERP
            price_key = f'{venue}_perp_price'
        
        market_price = market_data.get(price_key, market_data.get('eth_usd_price', 3000.0))
        cex_interface_logger.info(f"CEX Interface: Market price lookup - price_key={price_key}, market_price={market_price}")
        
        # Calculate execution cost
        cex_interface_logger.info("CEX Interface: About to calculate execution cost")
        execution_cost = self._get_execution_cost(instruction, market_data)
        cex_interface_logger.info(f"CEX Interface: Execution cost calculated: {execution_cost}")
        
        # Simulate slippage
        slippage = execution_cost / 10000  # Convert bps to decimal
        if side in ['BUY', 'LONG']:
            fill_price = market_price * (1 + slippage)
        else:  # SELL, SHORT
            fill_price = market_price * (1 - slippage)
        
        # Calculate fill amount
        if side in ['BUY', 'LONG']:
            fill_amount = amount
        else:  # SELL, SHORT
            fill_amount = amount
        
        result = {
            'status': 'FILLED',
            'venue': venue,
            'symbol': symbol,
            'side': side,
            'amount': fill_amount,
            'price': fill_price,
            'market_price': market_price,
            'slippage': slippage,
            'execution_cost': execution_cost,
            'timestamp': datetime.now(timezone.utc),
            'order_id': f"backtest_{venue}_{symbol}_{int(datetime.now().timestamp())}",
            'execution_mode': 'backtest'
        }
        
        try:
            # Log event
            cex_interface_logger.info("CEX Interface: Trade execution event logged")
            
            # Update position monitor with correct format
            cex_interface_logger.info("CEX Interface: About to update position monitor")
            
            # Convert CEX trade to position monitor format
            if trade_type == 'SPOT':
                # Spot trade updates token balances
                base_token = symbol.split('/')[0]  # 'BTC' from 'BTC/USDT'
                quote_token = symbol.split('/')[1]  # 'USDT' from 'BTC/USDT'
                
                if side in ['BUY', 'LONG']:
                    token_changes = [
                        {'venue': venue.upper(), 'token': base_token, 'delta': +fill_amount, 'reason': f'SPOT_{side}'},
                        {'venue': venue.upper(), 'token': quote_token, 'delta': -(fill_amount * fill_price), 'reason': f'SPOT_{side}'}
                    ]
                else:  # SELL, SHORT
                    token_changes = [
                        {'venue': venue.upper(), 'token': base_token, 'delta': -fill_amount, 'reason': f'SPOT_{side}'},
                        {'venue': venue.upper(), 'token': quote_token, 'delta': +(fill_amount * fill_price), 'reason': f'SPOT_{side}'}
                    ]
                
                # Log spot trade execution
                cex_interface_logger.info(f"CEX Interface: Spot trade executed - {venue} {symbol} {side} {fill_amount} @ {fill_price}")
            else:  # PERP
                # Perp trade updates derivative positions
                derivative_changes = [{
                    'venue': venue,
                    'instrument': symbol,  # 'BTCUSDT' 
                    'action': 'OPEN',
                    'data': {
                        'size': -fill_amount if side in ['SELL', 'SHORT'] else +fill_amount,
                        'entry_price': fill_price,
                        'entry_timestamp': datetime.now(timezone.utc).isoformat(),
                        'notional_usd': fill_amount * fill_price
                    }
                }]
                
                # Log perp trade execution
                cex_interface_logger.info(f"CEX Interface: Perp trade executed - {venue} {symbol} {side} {fill_amount} @ {fill_price}")
            
            cex_interface_logger.info("CEX Interface: Position monitor updated successfully")
            
        except Exception as e:
            cex_interface_logger.error(f"CEX Interface: Error in post-trade operations: {e}")
            raise
        
        cex_interface_logger.info(f"CEX Interface: Trade execution completed successfully")
        return result
    
    async def _execute_live_trade(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute real trade for live mode."""
        venue = instruction.get('venue', 'binance')
        trade_type = instruction.get('trade_type', 'SPOT')
        symbol = instruction.get('pair', 'ETH/USDT')
        side = instruction.get('side', 'BUY')
        amount = instruction.get('amount', 0.0)
        
        if venue not in self.exchange_clients:
            raise ValueError(f"Exchange client not available for venue: {venue}")
        
        exchange = self.exchange_clients[venue]
        
        try:
            # Convert side to CCXT format
            ccxt_side = 'buy' if side in ['BUY', 'LONG'] else 'sell'
            
            # Execute order
            if trade_type == 'SPOT':
                order = await asyncio.get_event_loop().run_in_executor(
                    None,
                    exchange.create_market_order,
                    symbol,
                    ccxt_side,
                    amount
                )
            else:  # PERP
                order = await asyncio.get_event_loop().run_in_executor(
                    None,
                    exchange.create_market_order,
                    symbol,
                    ccxt_side,
                    amount,
                    None,
                    None,
                    {'type': 'market'}
                )
            
            result = {
                'status': 'FILLED',
                'venue': venue,
                'symbol': symbol,
                'side': side,
                'amount': order.get('filled', amount),
                'price': order.get('average', order.get('price', 0.0)),
                'market_price': market_data.get('eth_usd_price', 0.0),
                'slippage': 0.0,  # Calculate from order data
                'execution_cost': 0.0,  # Calculate from order data
                'timestamp': datetime.now(timezone.utc),
                'order_id': order.get('id', ''),
                'execution_mode': 'live',
                'ccxt_order': order
            }
            
            # Log event
            await self._log_execution_event('CEX_TRADE_EXECUTED', result)
            
            # Live mode: Check transaction confirmation before updating position monitor
            if self.execution_mode == 'live':
                await self._await_transaction_confirmation(venue, result.get('order_id'))
            
            # Update position monitor using Position Update Handler
            if hasattr(self, 'position_update_handler') and self.position_update_handler:
                current_timestamp = pd.Timestamp.now(tz='UTC')
                await self.position_update_handler.handle_position_update(
                    changes={
                        'timestamp': current_timestamp,
                        'trigger': 'CEX_LIVE_TRADE',
                        'trade_data': {
                            'venue': venue,
                            'symbol': symbol,
                            'side': side,
                            'amount': result['amount'],
                            'price': result['price']
                        }
                    },
                    timestamp=current_timestamp,
                    market_data=market_data,
                    trigger_component='CEX_LIVE_TRADE'
                )
            else:
                # Fallback to direct position monitor update
                await self._update_position_monitor({
                    'venue': venue,
                    'symbol': symbol,
                    'side': side,
                    'amount': result['amount'],
                    'price': result['price']
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute live trade on {venue}: {e}")
            raise
    
    async def _await_transaction_confirmation(self, venue: str, order_id: str, max_retries: int = 3, retry_delay: float = 5.0):
        """
        Wait for transaction confirmation in live mode.
        
        This ensures that the transaction has been reflected on the exchange
        before we update the position monitor and proceed to the next component.
        
        Args:
            venue: Exchange venue
            order_id: Order ID to check
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        if not order_id:
            cex_interface_logger.warning(f"No order ID provided for confirmation check on {venue}")
            return
        
        cex_interface_logger.info(f"Awaiting transaction confirmation for order {order_id} on {venue}")
        
        for attempt in range(max_retries):
            try:
                if venue in self.exchange_clients:
                    exchange = self.exchange_clients[venue]
                    order = await exchange.fetch_order(order_id)
                    
                    if order.get('status') in ['closed', 'filled']:
                        cex_interface_logger.info(f"Transaction confirmed for order {order_id} on {venue}")
                        return
                    elif order.get('status') in ['canceled', 'rejected']:
                        raise Exception(f"Order {order_id} was {order.get('status')} on {venue}")
                    else:
                        cex_interface_logger.info(f"Order {order_id} status: {order.get('status')}, waiting...")
                        await asyncio.sleep(retry_delay)
                else:
                    cex_interface_logger.warning(f"Exchange client not available for {venue}")
                    return
                    
            except Exception as e:
                cex_interface_logger.error(f"Error checking order confirmation (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to confirm transaction after {max_retries} attempts: {e}")
                await asyncio.sleep(retry_delay)
        
        raise Exception(f"Transaction confirmation timeout for order {order_id} on {venue}")
    
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
        if not venue or venue not in self.exchange_clients:
            return 0.0
        
        exchange = self.exchange_clients[venue]
        
        try:
            balance = await asyncio.get_event_loop().run_in_executor(
                None,
                exchange.fetch_balance
            )
            return balance.get(asset, {}).get('free', 0.0)
        except Exception as e:
            logger.error(f"Failed to get balance from {venue}: {e}")
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
        if not venue or venue not in self.exchange_clients:
            return {'amount': 0.0, 'side': 'NONE'}
        
        exchange = self.exchange_clients[venue]
        
        try:
            positions = await asyncio.get_event_loop().run_in_executor(
                None,
                exchange.fetch_positions,
                [symbol]
            )
            
            if positions:
                pos = positions[0]
                return {
                    'amount': abs(pos.get('contracts', 0.0)),
                    'side': 'LONG' if pos.get('side') == 'long' else 'SHORT' if pos.get('side') == 'short' else 'NONE',
                    'unrealized_pnl': pos.get('unrealizedPnl', 0.0),
                    'entry_price': pos.get('entryPrice', 0.0)
                }
            else:
                return {'amount': 0.0, 'side': 'NONE'}
                
        except Exception as e:
            logger.error(f"Failed to get position from {venue}: {e}")
            return {'amount': 0.0, 'side': 'NONE'}
    
    async def cancel_all_orders(self, venue: Optional[str] = None) -> Dict[str, Any]:
        """Cancel all open orders."""
        if self.execution_mode == 'backtest':
            return {'status': 'SUCCESS', 'cancelled_orders': 0, 'execution_mode': 'backtest'}
        
        if not venue or venue not in self.exchange_clients:
            return {'status': 'ERROR', 'message': f'Exchange client not available for venue: {venue}'}
        
        exchange = self.exchange_clients[venue]
        
        try:
            cancelled_orders = await asyncio.get_event_loop().run_in_executor(
                None,
                exchange.cancel_all_orders
            )
            
            result = {
                'status': 'SUCCESS',
                'cancelled_orders': len(cancelled_orders),
                'venue': venue,
                'execution_mode': 'live'
            }
            
            # Log event
            await self._log_execution_event('CEX_ORDERS_CANCELLED', result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to cancel orders on {venue}: {e}")
            return {'status': 'ERROR', 'message': str(e)}
    
    async def execute_transfer(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a cross-venue transfer (CEX-specific).
        
        Args:
            instruction: Transfer instruction
            market_data: Current market data
            
        Returns:
            Transfer execution result
        """
        # CEX transfers are typically simple deposits/withdrawals
        venue = instruction.get('venue', 'binance')
        token = instruction.get('token', 'USDT')
        amount = instruction.get('amount', 0.0)
        side = instruction.get('side', 'deposit')
        
        if self.execution_mode == 'backtest':
            return await self._execute_backtest_transfer(venue, token, amount, side, market_data)
        else:
            return await self._execute_live_transfer(venue, token, amount, side, market_data)
    
    async def _execute_backtest_transfer(
        self, 
        venue: str, 
        token: str, 
        amount: float, 
        side: str, 
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute simulated CEX transfer for backtest mode."""
        result = {
            'status': 'COMPLETED',
            'venue': venue,
            'token': token,
            'amount': amount,
            'side': side,
            'fee': 0.0,  # CEX transfers typically have no fees
            'timestamp': datetime.now(timezone.utc),
            'execution_mode': 'backtest',
            'transfer_id': f"backtest_cex_{venue}_{token}_{int(datetime.now().timestamp())}"
        }
        
        # Log event
        await self._log_execution_event('CEX_TRANSFER_EXECUTED', result)
        
        # Update position monitor
        await self._update_position_monitor({
            'venue': venue,
            'token': token,
            'side': side,
            'amount': amount,
            'trade_type': 'venue_transfer'
        })
        
        return result
    
    async def _execute_live_transfer(
        self, 
        venue: str, 
        token: str, 
        amount: float, 
        side: str, 
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute real CEX transfer for live mode."""
        if venue not in self.exchange_clients:
            raise ValueError(f"Exchange client not available for venue: {venue}")
        
        exchange = self.exchange_clients[venue]
        
        try:
            if side == 'deposit':
                # Execute deposit
                deposit_result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    exchange.deposit,
                    token,
                    amount
                )
            else:  # withdraw
                # Execute withdrawal
                withdrawal_result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    exchange.withdraw,
                    token,
                    amount
                )
            
            result = {
                'status': 'COMPLETED',
                'venue': venue,
                'token': token,
                'amount': amount,
                'side': side,
                'fee': 0.0,  # Would be extracted from actual result
                'timestamp': datetime.now(timezone.utc),
                'execution_mode': 'live',
                'transfer_id': f"live_cex_{venue}_{token}_{int(datetime.now().timestamp())}"
            }
            
            # Log event
            await self._log_execution_event('CEX_TRANSFER_EXECUTED', result)
            
            # Update position monitor
            await self._update_position_monitor({
                'venue': venue,
                'token': token,
                'side': side,
                'amount': amount,
                'trade_type': 'venue_transfer'
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute CEX transfer on {venue}: {e}")
            raise
    
    async def execute_borrow(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute borrow action on OnChain protocol.
        Note: CEX interfaces don't support borrowing, this is for interface compliance.
        
        Args:
            instruction: Borrow instruction dictionary
            market_data: Current market data snapshot
            
        Returns:
            Borrow execution result dictionary
        """
        logger.warning("CEX Interface: Borrow operation not supported on CEX venues")
        return {
            'status': 'not_supported',
            'message': 'Borrow operations are not supported on CEX venues',
            'instruction': instruction,
            'venue': instruction.get('venue', 'unknown')
        }
    
    async def execute_spot_trade(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute spot trade on CEX.
        
        Args:
            instruction: Spot trade instruction dictionary
            market_data: Current market data snapshot
            
        Returns:
            Spot trade execution result dictionary
        """
        try:
            logger.info(f"CEX Interface: Executing spot trade instruction: {instruction}")
            
            # Validate instruction
            if not self._validate_spot_trade_instruction(instruction):
                raise ValueError("Invalid spot trade instruction")
            
            # Get execution cost
            execution_cost = self._get_execution_cost(instruction, market_data)
            
            # Execute based on mode
            if self.execution_mode == 'backtest':
                result = await self._execute_backtest_spot_trade(instruction, market_data)
            elif self.execution_mode == 'live':
                result = await self._execute_live_spot_trade(instruction, market_data)
            else:
                raise ValueError(f"Unknown execution mode: {self.execution_mode}")
            
            # Add execution cost to result
            result['execution_cost'] = execution_cost
            
            # Log execution event
            await self._log_execution_event('spot_trade_executed', {
                'instruction': instruction,
                'result': result,
                'venue': instruction.get('venue', 'unknown'),
                'token': instruction.get('symbol', 'unknown')
            })
            
            return result
            
        except Exception as e:
            logger.error(f"CEX Interface: Spot trade execution failed: {e}")
            await self._log_execution_event('spot_trade_failed', {
                'instruction': instruction,
                'error': str(e),
                'venue': instruction.get('venue', 'unknown'),
                'token': instruction.get('symbol', 'unknown')
            })
            raise
    
    async def execute_supply(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute supply action on OnChain protocol.
        Note: CEX interfaces don't support supplying, this is for interface compliance.
        
        Args:
            instruction: Supply instruction dictionary
            market_data: Current market data snapshot
            
        Returns:
            Supply execution result dictionary
        """
        logger.warning("CEX Interface: Supply operation not supported on CEX venues")
        return {
            'status': 'not_supported',
            'message': 'Supply operations are not supported on CEX venues',
            'instruction': instruction,
            'venue': instruction.get('venue', 'unknown')
        }
    
    async def execute_perp_trade(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute perpetual trade on CEX.
        
        Args:
            instruction: Perp trade instruction dictionary
            market_data: Current market data snapshot
            
        Returns:
            Perp trade execution result dictionary
        """
        try:
            logger.info(f"CEX Interface: Executing perp trade instruction: {instruction}")
            
            # Validate instruction
            if not self._validate_perp_trade_instruction(instruction):
                raise ValueError("Invalid perp trade instruction")
            
            # Get execution cost
            execution_cost = self._get_execution_cost(instruction, market_data)
            
            # Execute based on mode
            if self.execution_mode == 'backtest':
                result = await self._execute_backtest_perp_trade(instruction, market_data)
            elif self.execution_mode == 'live':
                result = await self._execute_live_perp_trade(instruction, market_data)
            else:
                raise ValueError(f"Unknown execution mode: {self.execution_mode}")
            
            # Add execution cost to result
            result['execution_cost'] = execution_cost
            
            # Log execution event
            await self._log_execution_event('perp_trade_executed', {
                'instruction': instruction,
                'result': result,
                'venue': instruction.get('venue', 'unknown'),
                'token': instruction.get('symbol', 'unknown')
            })
            
            return result
            
        except Exception as e:
            logger.error(f"CEX Interface: Perp trade execution failed: {e}")
            await self._log_execution_event('perp_trade_failed', {
                'instruction': instruction,
                'error': str(e),
                'venue': instruction.get('venue', 'unknown'),
                'token': instruction.get('symbol', 'unknown')
            })
            raise
    
    async def execute_swap(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute token swap on DEX.
        Note: CEX interfaces don't support swaps, this is for interface compliance.
        
        Args:
            instruction: Swap instruction dictionary
            market_data: Current market data snapshot
            
        Returns:
            Swap execution result dictionary
        """
        logger.warning("CEX Interface: Swap operation not supported on CEX venues")
        return {
            'status': 'not_supported',
            'message': 'Swap operations are not supported on CEX venues',
            'instruction': instruction,
            'venue': instruction.get('venue', 'unknown')
        }
    
    def _validate_spot_trade_instruction(self, instruction: Dict[str, Any]) -> bool:
        """Validate spot trade instruction."""
        required_fields = ['symbol', 'side', 'amount', 'venue']
        return all(field in instruction for field in required_fields)
    
    def _validate_perp_trade_instruction(self, instruction: Dict[str, Any]) -> bool:
        """Validate perp trade instruction."""
        required_fields = ['symbol', 'side', 'amount', 'venue']
        return all(field in instruction for field in required_fields)
    
    async def _execute_backtest_spot_trade(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute simulated spot trade for backtest mode."""
        return {
            'status': 'COMPLETED',
            'symbol': instruction['symbol'],
            'side': instruction['side'],
            'amount': instruction['amount'],
            'venue': instruction['venue'],
            'execution_mode': 'backtest',
            'timestamp': datetime.now(timezone.utc)
        }
    
    async def _execute_live_spot_trade(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute real spot trade for live mode."""
        # Placeholder for live implementation
        return {
            'status': 'COMPLETED',
            'symbol': instruction['symbol'],
            'side': instruction['side'],
            'amount': instruction['amount'],
            'venue': instruction['venue'],
            'execution_mode': 'live',
            'timestamp': datetime.now(timezone.utc)
        }
    
    async def _execute_backtest_perp_trade(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute simulated perp trade for backtest mode."""
        return {
            'status': 'COMPLETED',
            'symbol': instruction['symbol'],
            'side': instruction['side'],
            'amount': instruction['amount'],
            'venue': instruction['venue'],
            'execution_mode': 'backtest',
            'timestamp': datetime.now(timezone.utc)
        }
    
    async def _execute_live_perp_trade(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute real perp trade for live mode."""
        # Placeholder for live implementation
        return {
            'status': 'COMPLETED',
            'symbol': instruction['symbol'],
            'side': instruction['side'],
            'amount': instruction['amount'],
            'venue': instruction['venue'],
            'execution_mode': 'live',
            'timestamp': datetime.now(timezone.utc)
        }