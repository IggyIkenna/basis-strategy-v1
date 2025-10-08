"""
Position Monitor Component

Tracks raw ERC-20/token balances and derivative positions with NO conversions.
This component knows about balances in NATIVE token units only.

Key Principle: This component tracks balances in native units:
- aWeETH is just a number (doesn't know it represents underlying weETH)
- ETH is just a number (doesn't know its USD value)  
- Perp position is just a size (doesn't know its USD exposure)

Conversions happen in Exposure Monitor!

AAVE Index Mechanics:
- aWeETH balance is CONSTANT after supply (never changes)
- Underlying weETH claimable grows via weETH_claimable = aWeETH * LiquidityIndex
- Index at supply time determines how much aWeETH you receive: aWeETH = weETH_supplied / LiquidityIndex_at_supply
"""

from typing import Dict, List, Optional, Any
import redis
import json
import logging
import asyncio
from datetime import datetime
import pandas as pd
from dataclasses import dataclass, field
from pathlib import Path

from ....core.error_codes.error_code_registry import get_error_info, ErrorCodeInfo

logger = logging.getLogger(__name__)

# Create dedicated position monitor logger
position_logger = logging.getLogger('position_monitor')
position_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent.parent.parent.parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Create file handler for position monitor logs
position_handler = logging.FileHandler(logs_dir / 'position_monitor.log')
position_handler.setLevel(logging.INFO)

# Create formatter
position_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
position_handler.setFormatter(position_formatter)

# Add handler to logger if not already added
if not position_logger.handlers:
    position_logger.addHandler(position_handler)
    position_logger.propagate = False


class PositionMonitorError(Exception):
    """Custom exception for position monitor errors with error codes."""
    
    def __init__(self, error_code: str, message: str = None, **kwargs):
        self.error_code = error_code
        error_info = get_error_info(error_code)
        
        if error_info:
            self.component = error_info.component
            self.severity = error_info.severity
            self.description = error_info.description
            self.resolution = error_info.resolution
            
            # Use provided message or default from error code
            self.message = message or error_info.message
        else:
            # Fallback if error code not found
            self.component = "POS"
            self.severity = "HIGH"
            self.message = message or f"Unknown error: {error_code}"
        
        # Add any additional context
        self.context = kwargs
        
        # Create the full error message
        full_message = f"{error_code}: {self.message}"
        if self.context:
            context_str = ", ".join([f"{k}={v}" for k, v in self.context.items()])
            full_message += f" ({context_str})"
        
        super().__init__(full_message)


@dataclass
class PositionData:
    """Data structure for derivative positions."""
    size: float
    entry_price: float
    entry_timestamp: str
    notional_usd: float


class TokenBalanceMonitor:
    """Track raw token balances (internal to PositionMonitor)."""
    
    def __init__(self):
        # On-chain wallet (single Ethereum address)
        self.wallet = {
            'ETH': 0.0,                    # Native ETH for gas
            'USDT': 0.0,                   # USDT ERC-20
            'BTC': 0.0,                    # BTC ERC-20 (wrapped BTC)
            'weETH': 0.0,                  # Free weETH (not in AAVE)
            'wstETH': 0.0,                 # Free wstETH
            'aWeETH': 0.0,                 # AAVE aToken (CONSTANT - grows via index)
            'awstETH': 0.0,                # AAVE aToken for wstETH
            'aUSDT': 0.0,                  # AAVE aToken for USDT
            'aBTC': 0.0,                   # AAVE aToken for BTC
            'variableDebtWETH': 0.0,       # AAVE debt token (CONSTANT - grows via index)
            'variableDebtUSDT': 0.0,       # AAVE debt token for USDT
            'variableDebtBTC': 0.0,        # AAVE debt token for BTC
            'KING': 0.0,                   # KING rewards (seasonal - to be unwrapped into EIGEN and ETHFI)
            'EIGEN': 0.0,                  # EIGEN rewards (seasonal - from KING unwrapping)
            'ETHFI': 0.0                   # ETHFI rewards (seasonal - from KING unwrapping)
        }
        
        # CEX accounts (separate per exchange) - initialize with zero balances
        self.cex_accounts = {
            'binance': {
                'USDT': 0.0,
                'ETH': 0.0,
                'BTC': 0.0
            },
            'bybit': {
                'USDT': 0.0,
                'ETH': 0.0,
                'BTC': 0.0
            },
            'okx': {
                'USDT': 0.0,
                'ETH': 0.0,
                'BTC': 0.0
            }
        }


class DerivativeBalanceMonitor:
    """Track perpetual positions (internal to PositionMonitor)."""
    
    def __init__(self):
        self.perp_positions = {
            'binance': {},  # Dict[instrument, PositionData]
            'bybit': {},
            'okx': {}
        }


class PositionMonitor:
    """
    Wrapper ensuring Token + Derivative monitors update synchronously.
    
    PUBLIC INTERFACE for all other components.
    """
    
    def __init__(self, 
                 config: Dict[str, Any], 
                 execution_mode: str, 
                 initial_capital: float, 
                 share_class: str,
                 data_provider=None,
                 debug_mode: bool = False):
        """
        Initialize position monitor with capital from API request.
        
        Phase 3: NO DEFAULTS - all parameters must be provided from API request.
        
        Args:
            config: Strategy configuration from validated config manager
            execution_mode: 'backtest' or 'live' (from startup config)
            initial_capital: Initial capital amount from API request (NO DEFAULT)
            share_class: Share class from API request ('USDT' or 'ETH') (NO DEFAULT)
            data_provider: Data provider instance for price lookups
        """
        self.config = config
        self.execution_mode = execution_mode
        self.initial_capital = initial_capital
        self.share_class = share_class
        self.data_provider = data_provider
        self.debug_mode = debug_mode
        
        # Validate required parameters (FAIL FAST)
        if not initial_capital or initial_capital <= 0:
            raise ValueError(f"Invalid initial_capital: {initial_capital}. Must be > 0.")
        
        if share_class not in ['USDT', 'ETH']:
            raise ValueError(f"Invalid share_class: {share_class}. Must be 'USDT' or 'ETH'.")
        
        # Internal monitors
        self._token_monitor = TokenBalanceMonitor()
        self._derivative_monitor = DerivativeBalanceMonitor()
        
        # Initialize capital based on share class (NO DEFAULTS)
        self._initialize_capital()
        
        # Redis for inter-component communication
        self.redis = None
        if execution_mode == 'live':
            try:
                import os
                redis_url = os.getenv('BASIS_REDIS_URL')
                if not redis_url:
                    raise ValueError("BASIS_REDIS_URL environment variable required for live mode")
                
                self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis.ping()
                logger.info("Redis connection established for Position Monitor")
            except Exception as e:
                logger.error(f"Redis connection failed for live mode: {e}")
                raise ValueError(f"Redis required for live mode but connection failed: {e}")
        
        logger.info(f"Position Monitor initialized: {execution_mode} mode, {share_class} share class, {initial_capital} initial capital")
    
    def _initialize_capital(self):
        """Initialize capital based on share class and initial capital from API request."""
        logger.info(f"Position Monitor: _initialize_capital called with share_class={self.share_class}, initial_capital={self.initial_capital}")
        
        
        if self.share_class == 'USDT':
            self._token_monitor.wallet['USDT'] = float(self.initial_capital)
            logger.info(f"Position Monitor: Initialized USDT capital: {self.initial_capital}")
            logger.info(f"Position Monitor: Wallet after initialization: {self._token_monitor.wallet}")
        elif self.share_class == 'ETH':
            self._token_monitor.wallet['ETH'] = float(self.initial_capital)
            logger.info(f"Position Monitor: Initialized ETH capital: {self.initial_capital}")
            logger.info(f"Position Monitor: Wallet after initialization: {self._token_monitor.wallet}")
        else:
            raise ValueError(f"Invalid share class: {self.share_class}")
        
        logger.info(f"Position Monitor: Capital initialized: {self.share_class} = {self.initial_capital}")
    
    async def update(self, changes: Dict) -> Dict:
        """
        Update balances (SYNCHRONOUS - blocks until complete).
        
        Args:
            changes: {
                'timestamp': pd.Timestamp,
                'trigger': str,
                'token_changes': [
                    {'venue': 'WALLET', 'token': 'ETH', 'delta': -0.0035, 'reason': 'GAS_FEE'},
                    {'venue': 'WALLET', 'token': 'aWeETH', 'delta': +95.24, 'reason': 'AAVE_SUPPLY'}
                ],
                'derivative_changes': [
                    {'venue': 'binance', 'instrument': 'ETHUSDT-PERP', 'action': 'OPEN', 'data': {...}}
                ]
            }
        
        Returns:
            Updated snapshot
        """
        try:
            # Update token balances
            for change in changes.get('token_changes', []):
                self._apply_token_change(change)
            
            
            # Update derivative positions
            for change in changes.get('derivative_changes', []):
                self._apply_derivative_change(change)
            
            
            # Get snapshot
            snapshot = self.get_snapshot()
            
            # Add metadata
            snapshot['timestamp'] = changes.get('timestamp', pd.Timestamp.now(tz='UTC'))
            snapshot['last_updated'] = datetime.utcnow().isoformat() + 'Z'
            
            # Publish to Redis (for other components)
            if self.redis:
                await self._publish_update(snapshot, changes)
            
            logger.debug(f"Position Monitor updated: {changes.get('trigger', 'UNKNOWN')}")
            
            # Debug: Log position snapshot after update
            if self.debug_mode:
                timestamp = changes.get('timestamp', pd.Timestamp.now(tz='UTC'))
                trigger = changes.get('trigger', 'UNKNOWN')
                self.log_position_snapshot(timestamp, f"UPDATE_{trigger}")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error updating Position Monitor: {e}")
            raise
    
    def get_snapshot(self) -> Dict:
        """Get current position snapshot (read-only)."""
        try:
            logger.info(f"Position Monitor: get_snapshot called")
            logger.info(f"Position Monitor: Current wallet state: {self._token_monitor.wallet}")
            
            # Convert PositionData objects to dictionaries for serialization
            perp_positions = {}
            for venue, positions in self._derivative_monitor.perp_positions.items():
                perp_positions[venue] = {}
                if positions:  # Only include instruments that have positions
                    for instrument, position_data in positions.items():
                        perp_positions[venue][instrument] = {
                            'size': position_data.size,
                            'entry_price': position_data.entry_price,
                            'entry_timestamp': position_data.entry_timestamp,
                            'notional_usd': position_data.notional_usd
                        }
            
            snapshot = {
                'wallet': self._token_monitor.wallet.copy(),
                'cex_accounts': {k: v.copy() for k, v in self._token_monitor.cex_accounts.items()},
                'perp_positions': perp_positions,
                'last_updated': pd.Timestamp.now(tz='UTC')
            }
            
            logger.info(f"Position Monitor: get_snapshot returning {len(snapshot)} keys")
            logger.info(f"Position Monitor: Wallet in snapshot: {snapshot['wallet']}")
            return snapshot
            
        except Exception as e:
            logger.error(f"Position Monitor: get_snapshot failed: {e}")
            raise
    
    def _apply_token_change(self, change: Dict):
        """Apply single token balance change."""
        venue = change['venue']
        token = change['token']
        delta = change['delta']
        
        if venue == 'WALLET':
            if token not in self._token_monitor.wallet:
                logger.warning(f"Unknown wallet token: {token}")
                return
            
            old_balance = self._token_monitor.wallet[token]
            new_balance = old_balance + delta
            self._token_monitor.wallet[token] = new_balance
            
            logger.debug(f"Wallet {token}: {old_balance} -> {new_balance} (delta: {delta})")
            
        elif venue.lower() in ['binance', 'bybit', 'okx']:
            exchange = venue.lower()
            if exchange not in self._token_monitor.cex_accounts:
                logger.warning(f"Unknown CEX: {exchange}")
                return
            
            # Initialize token balance if it doesn't exist
            if token not in self._token_monitor.cex_accounts[exchange]:
                self._token_monitor.cex_accounts[exchange][token] = 0.0
            
            old_balance = self._token_monitor.cex_accounts[exchange][token]
            new_balance = old_balance + delta
            self._token_monitor.cex_accounts[exchange][token] = new_balance
            
            logger.debug(f"{exchange} {token}: {old_balance} -> {new_balance} (delta: {delta})")
        
        else:
            logger.warning(f"Unknown venue: {venue}")
    
    def _apply_derivative_change(self, change: Dict):
        """Apply single derivative position change."""
        venue = change['venue'].lower()
        instrument = change['instrument']
        action = change['action']
        data = change['data']
        
        if venue not in self._derivative_monitor.perp_positions:
            logger.warning(f"Unknown derivative venue: {venue}")
            return
        
        if action == 'OPEN':
            # Create new position
            position_data = PositionData(
                size=data['size'],
                entry_price=data['entry_price'],
                entry_timestamp=data.get('entry_timestamp', datetime.utcnow().isoformat()),
                notional_usd=data['notional_usd']
            )
            self._derivative_monitor.perp_positions[venue][instrument] = position_data
            logger.debug(f"Opened {venue} {instrument}: size={data['size']}, price={data['entry_price']}")
            
        elif action == 'CLOSE':
            # Remove position
            if instrument in self._derivative_monitor.perp_positions[venue]:
                del self._derivative_monitor.perp_positions[venue][instrument]
                logger.debug(f"Closed {venue} {instrument}")
            else:
                logger.warning(f"Position {venue} {instrument} not found for closing")
                
        elif action == 'ADJUST':
            # Modify existing position
            if instrument in self._derivative_monitor.perp_positions[venue]:
                position = self._derivative_monitor.perp_positions[venue][instrument]
                position.size = data['size']
                position.notional_usd = data['notional_usd']
                logger.debug(f"Adjusted {venue} {instrument}: new_size={data['size']}")
            else:
                logger.warning(f"Position {venue} {instrument} not found for adjustment")
        
        else:
            logger.warning(f"Unknown derivative action: {action}")
    
    async def _publish_update(self, snapshot: Dict, changes: Dict):
        """Publish update to Redis."""
        try:
            # Store snapshot
            await asyncio.get_event_loop().run_in_executor(
                None, 
                self.redis.set, 
                'position:snapshot', 
                json.dumps(snapshot, default=str)
            )
            
            # Publish update event
            update_event = {
                'timestamp': changes.get('timestamp', pd.Timestamp.now(tz='UTC')),
                'trigger': changes.get('trigger', 'UNKNOWN'),
                'changes_count': len(changes.get('token_changes', [])) + len(changes.get('derivative_changes', []))
            }
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.redis.publish,
                'position:updated',
                json.dumps(update_event, default=str)
            )
            
        except Exception as e:
            raise PositionMonitorError(
                'POS-005',
                message=f"Redis publish failed: {e}",
                error=str(e)
            )
    
    async def reconcile_with_live(self, live_balances: Optional[Dict] = None) -> Dict:
        """
        Reconcile tracked balances with live queries (live mode only).
        
        Queries:
        - Web3: Actual wallet balances
        - CEX APIs: Actual account balances
        - CEX APIs: Actual perp positions
        
        Compares with tracked, logs discrepancies.
        """
        if self.execution_mode != 'live':
            logger.info("Reconciliation skipped in backtest mode")
            return {}
        
        try:
            # Query real balances
            real_wallet = await self._query_web3_wallet()
            real_cex = await self._query_cex_balances()
            real_perps = await self._query_perp_positions()
            
            # Compare
            discrepancies = self._find_discrepancies(
                tracked={
                    'wallet': self._token_monitor.wallet,
                    'cex_accounts': self._token_monitor.cex_accounts,
                    'perp_positions': self._derivative_monitor.perp_positions
                },
                real={
                    'wallet': real_wallet,
                    'cex_accounts': real_cex,
                    'perp_positions': real_perps
                }
            )
            
            if discrepancies:
                raise PositionMonitorError(
                    'POS-001',
                    message="Balance drift detected during reconciliation",
                    discrepancies=discrepancies,
                    discrepancy_count=len(discrepancies)
                )
            else:
                logger.info("✅ Balance reconciliation successful - no discrepancies")
            
            return discrepancies
            
        except PositionMonitorError:
            # Re-raise our custom errors as-is
            raise
        except Exception as e:
            raise PositionMonitorError(
                'POS-001',
                message=f"Error during reconciliation: {e}",
                error=str(e)
            )
    
    async def _query_web3_wallet(self) -> Dict:
        """Live mode: Query actual wallet balances."""
        # TODO: Implement Web3 queries for live mode
        # This would query actual blockchain state
        logger.info("Web3 wallet query not implemented yet")
        return {}
    
    async def _query_cex_balances(self) -> Dict:
        """Live mode: Query actual CEX balances."""
        # TODO: Implement CEX API queries for live mode
        # This would query actual exchange balances
        logger.info("CEX balance query not implemented yet")
        return {}
    
    async def _query_perp_positions(self) -> Dict:
        """Live mode: Query actual perp positions."""
        # TODO: Implement CEX API queries for live mode
        # This would query actual exchange positions
        logger.info("Perp position query not implemented yet")
        return {}
    
    def _find_discrepancies(self, tracked: Dict, real: Dict) -> Dict:
        """Find discrepancies between tracked and real balances."""
        discrepancies = {}
        
        # Compare wallet balances
        for token, tracked_balance in tracked['wallet'].items():
            real_balance = real['wallet'].get(token, 0.0)
            diff = abs(tracked_balance - real_balance)
            if diff > 0.01:  # Threshold for discrepancy
                discrepancies[f'wallet_{token}'] = {
                    'tracked': tracked_balance,
                    'real': real_balance,
                    'difference': diff
                }
        
        # Compare CEX balances
        for exchange, tokens in tracked['cex_accounts'].items():
            for token, tracked_balance in tokens.items():
                real_balance = real['cex_accounts'].get(exchange, {}).get(token, 0.0)
                diff = abs(tracked_balance - real_balance)
                if diff > 0.01:
                    discrepancies[f'cex_{exchange}_{token}'] = {
                        'tracked': tracked_balance,
                        'real': real_balance,
                        'difference': diff
                    }
        
        return discrepancies
    
    async def _alert_discrepancies(self, discrepancies: Dict):
        """Alert monitoring system about discrepancies."""
        # TODO: Implement alerting system
        logger.error(f"Balance discrepancies detected: {len(discrepancies)} items")
        for key, data in discrepancies.items():
            logger.error(f"  {key}: tracked={data['tracked']}, real={data['real']}, diff={data['difference']}")
    
    def log_position_snapshot(self, timestamp: pd.Timestamp, trigger: str = "TIMESTEP"):
        """Log position snapshot to dedicated position monitor log file."""
        try:
            snapshot = self.get_snapshot()
            
            # Format the log message
            log_message = f"TIMESTEP: {timestamp.isoformat()} | TRIGGER: {trigger}\n"
            
            # Wallet balances
            wallet = snapshot.get('wallet', {})
            non_zero_wallet = {k: v for k, v in wallet.items() if v != 0}
            if non_zero_wallet:
                log_message += "WALLET: " + json.dumps(non_zero_wallet, indent=2) + "\n"
            else:
                log_message += "WALLET: No non-zero balances\n"
            
            # CEX accounts
            cex_accounts = snapshot.get('cex_accounts', {})
            non_zero_cex = {}
            for exchange, tokens in cex_accounts.items():
                non_zero_tokens = {k: v for k, v in tokens.items() if v != 0}
                if non_zero_tokens:
                    non_zero_cex[exchange] = non_zero_tokens
            
            if non_zero_cex:
                log_message += "CEX: " + json.dumps(non_zero_cex, indent=2) + "\n"
            else:
                log_message += "CEX: No non-zero balances\n"
            
            # Perpetual positions
            perp_positions = snapshot.get('perp_positions', {})
            non_zero_perps = {}
            for exchange, positions in perp_positions.items():
                if positions:  # Only include exchanges with positions
                    non_zero_perps[exchange] = positions
            
            if non_zero_perps:
                log_message += "PERPS: " + json.dumps(non_zero_perps, indent=2) + "\n"
            else:
                log_message += "PERPS: No positions\n"
            
            log_message += "-" * 80 + "\n"
            
            # Log to dedicated position monitor log file
            position_logger.info(log_message)
            
        except Exception as e:
            position_logger.error(f"Failed to log position snapshot: {e}")

