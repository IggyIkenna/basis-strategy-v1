"""
Position Monitor - Clean Implementation

Responsibilities:
- Track positions in format: venue:position_type:symbol -> amount
- Apply execution deltas from trades/operations  
- Simulate position updates in backtest mode
- Query real positions in live mode
- Automatic settlements (m2m pnl, staking rewards)

NOT responsible for:
- USD conversions (use ExposureMonitor)
- Risk calculations (use RiskMonitor)
- Position categorization (use Analytics/Frontend)
- Aggregation/metrics (use ExposureMonitor)

Reference: POSITION_MONITOR_REFACTOR_DESIGN.md
"""

from typing import Dict, List, Any, Optional, Set, Union
import logging
import pandas as pd
import os
import uuid
from pathlib import Path
from datetime import datetime, timezone

from ...infrastructure.logging.structured_logger import StructuredLogger
from ...infrastructure.logging.domain_event_logger import DomainEventLogger
from ...core.models.domain_events import PositionSnapshot
from ...core.errors.error_codes import ERROR_REGISTRY

logger = logging.getLogger(__name__)


class PositionMonitor:
    """
    Strategy-agnostic position tracking.
    
    Tracks positions in canonical format: venue:position_type:symbol -> amount
    Position types: BaseToken, aToken, debtToken, Perp
    """
    
    def __init__(
        self, 
        config: Dict[str, Any], 
        data_provider,
        utility_manager,
        venue_interface_factory=None,
        execution_mode: str = 'backtest',
        initial_capital: float = 100000,
        share_class: str = 'USDT',
        correlation_id: str = None,
        pid: int = None,
        log_dir: Path = None
    ):
        """
        Initialize position monitor.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
            venue_interface_factory: Venue interface factory for position interfaces
            execution_mode: Execution mode ('backtest' or 'live')
            initial_capital: Initial capital for backtest mode
            share_class: Share class ('USDT' or 'ETH')
        
        Raises:
            ValueError: If position_subscriptions not provided in config
        """
        # Core dependencies
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        self.venue_interface_factory = venue_interface_factory
        
        # Read from config if not explicitly passed (check for default values)
        self.execution_mode = config.get('execution_mode', execution_mode)
        self.initial_capital = config.get('initial_capital', initial_capital)
        self.share_class = config.get('share_class', share_class)
        
        # Health tracking
        self.health_status = "healthy"
        self.error_count = 0
        
        # Initialize logging infrastructure
        self.correlation_id = correlation_id or str(uuid.uuid4().hex)
        self.pid = pid or os.getpid()
        self.log_dir = log_dir
        
        # Initialize structured logger
        self.logger = StructuredLogger(
            component_name="PositionMonitor",
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
            engine=None  # Will be set by event engine if available
        )
        
        # Initialize domain event logger
        self.domain_event_logger = DomainEventLogger(self.log_dir) if self.log_dir else None
        
        # Core position state (position_key -> amount)
        self.simulated_positions: Dict[str, float] = {}
        self.real_positions: Dict[str, float] = {}
        
        # Timestamp tracking for settlement deduplication
        self.last_timestamp: Optional[pd.Timestamp] = None
        self.applied_this_timestamp: Set[str] = set()
        
        # MANDATORY: Pre-initialize positions from config
        self._initialize_positions_from_config()
        
        # Initialize position interfaces for live mode venue queries
        self.position_interfaces: Dict[str, Any] = {}
        if self.venue_interface_factory:
            self._initialize_position_interfaces()
        
        logger.info(
            f"PositionMonitor initialized: {execution_mode} mode, "
            f"{share_class} share class, ${initial_capital:,.0f} capital, "
            f"{len(self.simulated_positions)} positions declared"
        )
    
    def _log_position_snapshot(self, trigger_source: str = None) -> None:
        """Log position snapshot as domain event."""
        if not self.log_dir or not self.domain_event_logger:
            return
        
        timestamp = datetime.now().isoformat()
        real_utc = datetime.now(timezone.utc).isoformat()
        
        # Calculate total value (use share class for simplicity)
        total_value = sum(abs(v) for v in self.simulated_positions.values())
        
        snapshot = PositionSnapshot(
            timestamp=timestamp,
            real_utc_time=real_utc,
            correlation_id=self.correlation_id,
            pid=self.pid,
            positions=self.simulated_positions.copy(),
            total_value_usd=total_value,
            position_type='simulated' if self.execution_mode == 'backtest' else 'real',
            trigger_source=trigger_source,
            metadata={}
        )
        
        self.domain_event_logger.log_position_snapshot(snapshot)
    
    def _initialize_positions_from_config(self) -> None:
        """
        Initialize positions from config (MANDATORY).
        All positions must be pre-declared.
        
        Raises:
            ValueError: If position_subscriptions not provided
        """
        from ...core.models.instruments import validate_instrument_key
        
        position_config = self.config.get('component_config', {}).get('position_monitor', {})
        position_subs = position_config.get('position_subscriptions', [])
        
        if not position_subs:
            raise ValueError(
                "position_subscriptions is required in component_config.position_monitor. "
                "All positions must be pre-declared in config. "
                "Add position_subscriptions list to your mode YAML config."
            )
        
        # NEW: Validate all instruments exist in registry
        for position_key in position_subs:
            validate_instrument_key(position_key)
        
        logger.info(f"Pre-initializing {len(position_subs)} validated positions")
        
        for position_key in position_subs:
            self.simulated_positions[position_key] = 0.0
            self.real_positions[position_key] = 0.0
        
        logger.info(f"Position universe: {list(self.simulated_positions.keys())}")
    
    def _initialize_position_interfaces(self) -> None:
        """Initialize position interfaces for venue queries (live mode)."""
        try:
            # Get enabled venues from config
            venues = self._get_enabled_venues()
            
            # Create position interfaces TODO: ensure aligns with venue interface factory implementation
            self.position_interfaces = self.venue_interface_factory.get_venue_position_interfaces(
                venues, self.execution_mode, self.config
            )
            
            logger.info(
                f"Position interfaces initialized for {len(venues)} venues: {venues}"
            )
        except Exception as e:
            self.logger.error(
                f"Failed to initialize position interfaces: {e}",
                error_code="POS-001",
                exc_info=e,
                operation="initialize_position_interfaces"
            )
            self.position_interfaces = {}
    
    def _get_enabled_venues(self) -> List[str]:
        """Get list of enabled venues from position subscriptions."""
        venues = set()
        
        # Extract venue names from position keys
        for position_key in self.simulated_positions.keys():
            # Format: venue:position_type:symbol
            venue = position_key.split(':')[0]
            venues.add(venue)
        
        return list(venues)
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def get_current_positions(self) -> Dict[str, float]:
        """
        Get current raw positions.
        
        Returns:
            Dict mapping position_key -> amount
            
        Example:
            {
                "binance:BaseToken:USDT": 50000.0,
                "aave:aToken:WETH": 10.5,
                "aave:debtToken:USDT": 30000.0,
                "binance:Perp:BTCUSDT": -1.5
            }
        """
        return self.real_positions.copy()
    
    def update_state(
        self, 
        timestamp: pd.Timestamp, 
        trigger_source: str,
        execution_deltas: Optional[Union[Dict, List[Dict]]] = None
    ) -> Dict[str, float]:
        """
        Update position state. Routes internally based on trigger_source and execution_mode.
        
        Args:
            timestamp: Current timestamp
            trigger_source: Either 'venue_manager' (tight loop) or 'position_refresh' (timestep start)
            execution_deltas: Optional execution deltas from orders
            
        Returns:
            Current real positions
        """
        try:
            # Reset tracking if new timestamp
            if self.last_timestamp != timestamp:
                self.applied_this_timestamp = set()
                self.last_timestamp = timestamp
                logger.debug(f"New timestamp {timestamp}, reset settlement tracking")
            
            # Route based on trigger_source
            if trigger_source == 'venue_manager':
                # Tight loop: apply trade deltas + query balances
                if execution_deltas:
                    self._apply_execution_deltas(timestamp, execution_deltas)
                self._query_venue_balances(timestamp)
            
            elif trigger_source == 'position_refresh':
                # Position refresh: query balances only
                self._query_venue_balances(timestamp)
            
            else:
                raise ValueError(
                    f"Invalid trigger_source: '{trigger_source}'. "
                    f"Must be 'venue_manager' or 'position_refresh'."
                )
            
            return self.real_positions.copy()
        
        except Exception as e:
            self.logger.error(
                f"Error updating position state: {e}",
                error_code="POS-002",
                exc_info=e,
                operation="update_position_state"
            )
            raise
    
    # ========================================================================
    # PRIVATE METHODS - Delta Application
    # ========================================================================
    
    def _apply_execution_deltas(
        self, 
        timestamp: pd.Timestamp, 
        execution_deltas: Union[Dict, List[Dict]]
    ) -> None:
        """
        Apply execution deltas from venue_manager (trades/transfers).
        Normalizes format and delegates to unified applier.
        
        Args:
            timestamp: Current timestamp
            execution_deltas: Single delta or list of deltas from venue_manager
        """
        # Normalize to list
        if isinstance(execution_deltas, dict):
            execution_deltas = [execution_deltas]
        
        # Ensure all deltas have required fields
        normalized_deltas = []
        for delta in execution_deltas:
            normalized_delta = {
                "position_key": delta['position_key'],
                "delta_amount": delta['delta_amount'],
                "source": delta.get('source', 'trade'),
                "price": delta.get('price'),
                "fee": delta.get('fee')
            }
            normalized_deltas.append(normalized_delta)
        
        # Apply via unified applier
        self._apply_position_deltas(timestamp, normalized_deltas)
    
    def _apply_position_deltas(
        self, 
        timestamp: pd.Timestamp, 
        deltas: List[Dict]
    ) -> None:
        """
        Unified delta applier - handles ALL position updates.
        
        Used by:
        - _apply_execution_deltas() for trade/transfer deltas from venue_manager
        - _query_venue_balances() for automatic settlement deltas in backtest
        
        Args:
            timestamp: Current timestamp
            deltas: List of delta dicts with format:
                {
                    "position_key": str,      # "venue:position_type:symbol"
                    "delta_amount": float,    # Change in position (+/-)
                    "source": str,            # "trade"|"transfer"|"funding"|"reward"|"initial"
                    "price": Optional[float], # Execution price if applicable
                    "fee": Optional[float]    # Transaction fee if applicable
                }
        """
        for delta in deltas:
            position_key = delta['position_key']
            delta_amount = delta['delta_amount']
            
            # VALIDATION: Position must be pre-declared in config
            if position_key not in self.simulated_positions:
                raise ValueError(
                    f"Position '{position_key}' not found in position_subscriptions. "
                    f"All positions must be pre-declared in config. "
                    f"Declared positions: {list(self.simulated_positions.keys())}"
                )
            
            # Apply delta
            current_amount = self.simulated_positions[position_key]
            new_amount = current_amount + delta_amount
            self.simulated_positions[position_key] = new_amount
            
            # Log to standard logger
            logger.debug(
                f"Applied delta: {position_key} {delta_amount:+.6f} "
                f"(source: {delta.get('source', 'unknown')}, "
                f"old: {current_amount:.6f}, new: {new_amount:.6f})"
            )
            
            # Log to structured logger with duration tracking
            import time
            start_time = time.time()
            duration_ms = (time.time() - start_time) * 1000
            self.logger.info(
                f"Position delta applied: {position_key}",
                position_key=position_key,
                delta_amount=delta_amount,
                source=delta.get('source', 'unknown'),
                old_amount=current_amount,
                new_amount=new_amount,
                price=delta.get('price'),
                fee=delta.get('fee'),
                timestamp=timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                duration_ms=duration_ms
            )
        
        # Log position snapshot after all deltas applied
        self._log_position_snapshot(trigger_source="position_deltas")
    
    # ========================================================================
    # PRIVATE METHODS - Balance Queries
    # ========================================================================
    
    def _query_venue_balances(self, timestamp: pd.Timestamp) -> None:
        """
        Query/simulate venue balances with automatic settlements.
        
        BACKTEST MODE:
        - Apply automatic settlements (initial capital, funding, rewards)
        - Copy simulated to real AFTER applying deltas
        
        LIVE MODE:
        - Query actual positions from venue interfaces
        """
        if self.execution_mode == 'backtest':
            # Collect automatic settlement deltas
            automatic_deltas = []
            
            # 1. Initial capital (once at start)
            if ('initial_capital' not in self.applied_this_timestamp and 
                not any(v != 0 for v in self.simulated_positions.values())):
                initial_capital_deltas = self._generate_initial_capital_deltas()
                automatic_deltas.extend(initial_capital_deltas)
                self.applied_this_timestamp.add('initial_capital')
                
                # Log initial capital application
                logger.info(f"Applied initial capital at {timestamp}")
                import time
                start_time = time.time()
                duration_ms = (time.time() - start_time) * 1000
                self.logger.info(
                    f"Initial capital applied: {self.initial_capital} {self.share_class}",
                    amount=self.initial_capital,
                    share_class=self.share_class,
                    position_key=initial_capital_deltas[0]['position_key'] if initial_capital_deltas else None,
                    timestamp=timestamp.isoformat(),
                    duration_ms=duration_ms
                )
            
            # 2. Funding settlement (every 8 hours at 0/8/16 UTC)
            if (self._should_apply_funding_settlement(timestamp) and 
                'funding_settlement' not in self.applied_this_timestamp):
                automatic_deltas.extend(self._generate_funding_settlement_deltas(timestamp))
                self.applied_this_timestamp.add('funding_settlement')
                logger.info(f"Applied funding settlement at {timestamp}")
            
            # 3. Margin PnL (if configured)
            if (self._should_apply_margin_pnl(timestamp) and 
                'margin_pnl' not in self.applied_this_timestamp):
                automatic_deltas.extend(self._generate_margin_pnl_deltas(timestamp))
                self.applied_this_timestamp.add('margin_pnl')
                logger.info(f"Applied margin PnL at {timestamp}")
            
            # 4. Seasonal rewards (daily if configured)
            if (self._should_apply_seasonal_rewards(timestamp) and 
                'seasonal_rewards' not in self.applied_this_timestamp):
                automatic_deltas.extend(self._generate_seasonal_rewards_deltas(timestamp))
                self.applied_this_timestamp.add('seasonal_rewards')
                logger.info(f"Applied seasonal rewards at {timestamp}")
            
            # Apply all automatic deltas (updates simulated_positions)
            if automatic_deltas:
                self._apply_position_deltas(timestamp, automatic_deltas)
            
            # CRITICAL: Copy simulated to real AFTER applying deltas
            self.real_positions = self.simulated_positions.copy()
        
        elif self.execution_mode == 'live':
            # Live: query actual positions from venue interfaces
            self.real_positions = self._query_real_venue_positions(timestamp)
    
    def _query_real_venue_positions(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """
        Query actual positions from venue interfaces (live mode only).
        
        Returns:
            Dict mapping position_key -> actual amount
        """
        queried_positions = {}
        
        # Query each venue interface
        for venue, interface in self.position_interfaces.items():
            if interface is None:
                continue
            
            try:
                venue_positions = interface.get_positions(timestamp)
                queried_positions.update(venue_positions)
            except Exception as e:
                self.logger.error(
                    f"Failed to query positions from {venue}: {e}",
                    error_code="POS-003",
                    exc_info=e,
                    operation="query_venue_positions",
                    venue=venue
                )
        
        # Start with all declared positions at 0
        result = {k: 0.0 for k in self.simulated_positions.keys()}
        
        # Update with queried values (only for declared positions)
        for position_key, amount in queried_positions.items():
            if position_key in result:
                result[position_key] = amount
            else:
                # Position found but not declared in config
                logger.warning(
                    f"Venue returned undeclared position '{position_key}' with amount {amount}. "
                    f"Ignoring (not in position_subscriptions)."
                )
        
        return result
    
    # ========================================================================
    # PRIVATE METHODS - Delta Generators (Backtest Only)
    # ========================================================================
    
    def _generate_initial_capital_deltas(self) -> List[Dict]:
        """
        Generate initial capital delta based on share_class.
        Called once at backtest start.
        """
        if self.share_class == 'USDT':
            position_key = "wallet:BaseToken:USDT"
        elif self.share_class == 'ETH':
            position_key = "wallet:BaseToken:ETH"
        else:
            raise ValueError(f"Unknown share_class: {self.share_class}")
        
        # Validate position is declared
        if position_key not in self.simulated_positions:
            raise ValueError(
                f"Initial capital position '{position_key}' not found in position_subscriptions. "
                f"Add '{position_key}' to position_subscriptions in your mode YAML config."
            )
        
        return [{
            "position_key": position_key,
            "delta_amount": self.initial_capital,
            "source": "initial_capital",
            "price": None,
            "fee": None
        }]
    
    def _generate_funding_settlement_deltas(self, timestamp: pd.Timestamp) -> List[Dict]:
        """
        Generate funding rate settlement deltas for all perp positions.
        Called every 8 hours at 0/8/16 UTC in backtest mode.
        
        Returns list of deltas that update USDT balance based on funding payments.
        """
        deltas = []
        
        # Get all perp positions
        perp_positions = {k: v for k, v in self.simulated_positions.items() if ':Perp:' in k}
        
        for position_key, position_size in perp_positions.items():
            if position_size == 0:
                continue
            
            # Calculate funding payment using utility_manager
            funding_payment = self.utility_manager.calculate_funding_payment(
                position_key=position_key,
                position_size=position_size,
                timestamp=timestamp
            )
            
            if funding_payment != 0:
                # Funding settles to USDT balance
                # TODO: Extract venue-specific USDT position from position_key
                usdt_position_key = self._get_usdt_position_for_venue(position_key)
                
                deltas.append({
                    "position_key": usdt_position_key,
                    "delta_amount": funding_payment,
                    "source": "funding_settlement",
                    "price": None,
                    "fee": None,
                    "metadata": {
                        "perp_position": position_key,
                        "position_size": position_size
                    }
                })
        
        return deltas
    
    def _generate_margin_pnl_deltas(self, timestamp: pd.Timestamp) -> List[Dict]:
        """
        Generate margin PnL settlement deltas for closed/reduced perp positions.
        
        Returns list of deltas that update USDT balance based on realized PnL.
        """
        deltas = []
        
        # Strategy-specific: Check if margin PnL settlement is configured
        settlement_config = self._get_settlement_config()
        if not settlement_config.get('margin_pnl_enabled', False):
            return deltas
        
        # TODO: Implement margin PnL tracking and settlement
        # For now, this is primarily for funding - actual trade PnL comes through execution_deltas
        
        return deltas
    
    def _generate_seasonal_rewards_deltas(self, timestamp: pd.Timestamp) -> List[Dict]:
        """
        Generate seasonal reward deltas for LST positions.
        Called daily/weekly/ad-hoc if configured by strategy.
        
        Returns list of deltas that update token balances based on staking rewards.
        """
        deltas = []
        
        # Strategy-specific: Check if seasonal rewards are configured
        settlement_config = self._get_settlement_config()
        if not settlement_config.get('seasonal_rewards_enabled', False):
            return deltas
        
        # Get all LST staking positions (stETH, eETH, etc.)
        staking_positions = {
            k: v for k, v in self.simulated_positions.items() 
            if any(token in k for token in ['stETH', 'eETH', 'wstETH', 'weETH'])
        }
        
        for position_key, position_size in staking_positions.items():
            if position_size == 0:
                continue
            
            # Calculate daily staking rewards using utility_manager
            daily_rewards = self.utility_manager.calculate_staking_rewards(
                position_key=position_key,
                position_size=position_size,
                timestamp=timestamp
            )
            
            if daily_rewards > 0:
                # Staking rewards compound into same token
                deltas.append({
                    "position_key": position_key,
                    "delta_amount": daily_rewards,
                    "source": "seasonal_rewards",
                    "price": None,
                    "fee": None,
                    "metadata": {
                        "reward_type": "staking_yield"
                    }
                })
        
        return deltas
    
    # ========================================================================
    # PRIVATE METHODS - Settlement Timing
    # ========================================================================
    
    def _should_apply_funding_settlement(self, timestamp: pd.Timestamp) -> bool:
        """Check if funding settlement should occur (every 8 hours at 0/8/16 UTC)."""
        settlement_config = self._get_settlement_config()
        if not settlement_config.get('funding_enabled', False):
            return False
        return timestamp.hour in [0, 8, 16] and timestamp.minute == 0
    
    def _should_apply_margin_pnl(self, timestamp: pd.Timestamp) -> bool:
        """Check if margin PnL settlement should occur (strategy-specific)."""
        settlement_config = self._get_settlement_config()
        return settlement_config.get('margin_pnl_enabled', False)
    
    def _should_apply_seasonal_rewards(self, timestamp: pd.Timestamp) -> bool:
        """
        Check if seasonal rewards should be applied.
        Weekly rewards (e.g., EigenLayer) are applied on Mondays at midnight UTC.
        """
        settlement_config = self._get_settlement_config()
        if not settlement_config.get('seasonal_rewards_enabled', False):
            return False
        
        frequency = settlement_config.get('seasonal_rewards_frequency', 'weekly')
        
        if frequency == 'weekly':
            # Apply on Mondays (weekday=0) at midnight UTC
            return timestamp.weekday() == 0 and timestamp.hour == 0 and timestamp.minute == 0
        else:
            raise ValueError(f"Unknown seasonal_rewards_frequency: {frequency}")
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _get_settlement_config(self) -> Dict:
        """Get settlement configuration from component_config."""
        return self.config.get('component_config', {}).get('position_monitor', {}).get('settlement', {})
    
    def _get_usdt_position_for_venue(self, perp_position_key: str) -> str:
        """
        Get venue-specific USDT position for funding settlements.
        
        Funding settlements go to the venue's USDT balance (PnL currency).
        USDT perps get PnL paid in USDT including:
        - PnL from trades
        - PnL from open positions (m2m)  
        - Funding rate PnL
        
        Example: "binance:Perp:BTCUSDT" -> "binance:BaseToken:USDT"
        """
        # Format: venue:position_type:symbol
        parts = perp_position_key.split(':')
        venue = parts[0]
        usdt_key = f"{venue}:BaseToken:USDT"
        
        # Validate it exists
        if usdt_key not in self.simulated_positions:
            raise ValueError(
                f"USDT position '{usdt_key}' not found for funding settlement. "
                f"Add '{usdt_key}' to position_subscriptions in your mode YAML config."
            )
        
        return usdt_key
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            'status': self.health_status,
            'error_count': self.error_count,
            'position_count': len(self.simulated_positions),
            'position_interfaces_count': len(self.position_interfaces),
            'component': self.__class__.__name__
        }
