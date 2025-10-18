"""
P&L Calculator Component

Mode-agnostic P&L calculator using config-driven attribution types.
Calculates balance-based and attribution P&L with reconciliation in share class currency.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Mode-Agnostic Architecture
Reference: docs/specs/04_pnl_monitor.md - Complete specification
"""

from typing import Dict, List, Optional, Any
import json
import logging
import asyncio
import os
import uuid
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from pathlib import Path

from ...infrastructure.logging.structured_logger import StructuredLogger
from ...infrastructure.logging.domain_event_logger import DomainEventLogger
from ...core.models.domain_events import PnLCalculation
from ...core.errors.error_codes import ERROR_REGISTRY

logger = logging.getLogger(__name__)

# Error codes for P&L Calculator
ERROR_CODES = {
    'PNL-001': 'Reconciliation failed (tolerance exceeded)',
    'PNL-002': 'Attribution calculation error',
    'PNL-003': 'Balance-based P&L calculation failed',
    'PNL-004': 'Previous exposure data missing for attribution'
}


class PnLCalculatorError(Exception):
    """Custom exception for P&L calculator errors with error codes."""
    
    def __init__(self, error_code: str, message: str = None, **kwargs):
        self.error_code = error_code
        # error_info = get_error_info(error_code)  # Removed - using new error system
        
        # Simplified error handling
        self.component = "PnLCalculator"
        self.severity = "ERROR"
        self.message = message or f"P&L Calculator error: {error_code}"
        
        # Add any additional context
        self.context = kwargs
        
        # Create the full error message
        full_message = f"{error_code}: {self.message}"
        if self.context:
            context_str = ", ".join([f"{k}={v}" for k, v in self.context.items()])
            full_message += f" ({context_str})"
        
        super().__init__(full_message)
    
    def _log_structured_error(self, context: Dict[str, Any] = None):
        """Log structured error with error code and context."""
        # error_info = get_error_info(self.error_code)  # Removed - using new error system
        
        log_data = {
            'error_code': self.error_code,
            'error_message': self.message,
            'component': self.component,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': self.severity.value if hasattr(self.severity, 'value') else str(self.severity)
        }
        
        if context:
            log_data['context'] = context
        
        if self.context:
            log_data['error_context'] = self.context
        
        # Log via standard logger (structured logger not available in exception class)
        if hasattr(self.severity, 'value'):
            if self.severity.value in ['CRITICAL', 'HIGH']:
                logger.error(f"{self.error_code}: {self.message}", extra=log_data)
            elif self.severity.value == 'MEDIUM':
                logger.warning(f"{self.error_code}: {self.message}", extra=log_data)
            else:
                logger.info(f"{self.error_code}: {self.message}", extra=log_data)
        else:
            logger.error(f"{self.error_code}: {self.message}", extra=log_data)


class PnLCalculator:
    """Calculate P&L using balance-based and attribution methods."""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 config: Dict[str, Any],
                 share_class: str, 
                 initial_capital: float,
                 data_provider=None,
                 utility_manager=None,
                 exposure_monitor=None,
                 correlation_id: str = None,
                 pid: int = None,
                 log_dir: Path = None):
        """
        Initialize P&L calculator with injected config and parameters.
        
        Phase 3: Uses validated config for calculation parameters.
        
        Args:
            config: Strategy configuration from validated config manager
            share_class: Share class ('ETH' or 'USDT')
            initial_capital: Initial capital from API request
            data_provider: Data provider for market data
            utility_manager: Utility manager for conversions
            exposure_monitor: Exposure monitor reference for getting current exposure
        """
        self.config = config
        self.share_class = share_class
        self.initial_capital = initial_capital
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        self.exposure_monitor = exposure_monitor
        self.health_status = "healthy"
        
        # Get position subscriptions from config
        position_config = config.get('component_config', {}).get('position_monitor', {})
        self.position_subscriptions = position_config.get('position_subscriptions', [])
        
        logger.info(f"PnLMonitor subscribed to {len(self.position_subscriptions)} positions")
        self.error_count = 0
        
        # Initialize logging infrastructure
        self.correlation_id = correlation_id or str(uuid.uuid4().hex)
        self.pid = pid or os.getpid()
        self.log_dir = log_dir
        
        # Initialize structured logger
        self.logger = StructuredLogger(
            component_name="PnLCalculator",
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
            engine=None
        )
        
        # Initialize domain event logger
        self.domain_event_logger = DomainEventLogger(self.log_dir) if self.log_dir else None
        
        # Load component-specific configuration - direct access without intermediate variable
        pnl_monitor_config = config['component_config']['pnl_monitor']
        self.attribution_types = pnl_monitor_config['attribution_types']
        self.reporting_currency = pnl_monitor_config['reporting_currency']
        self.reconciliation_tolerance = pnl_monitor_config['reconciliation_tolerance']
        
        # Track cumulative attribution components
        self.cumulative = {
            'supply_pnl': 0.0,
            'staking_yield_oracle': 0.0,    # Oracle price drift (weETH/ETH appreciation)
            'staking_yield_rewards': 0.0,   # Seasonal rewards (EIGEN + ETHFI)
            'borrow_cost': 0.0,
            'funding_pnl': 0.0,
            'basis_spread_pnl': 0.0,        # Basis spread P&L (spot long + perp short)
            'net_delta_pnl': 0.0,           # Net delta P&L (market neutrality)
            'delta_pnl': 0.0,
            'transaction_costs': 0.0
        }
        
        # Initial value (set at t=0) - use initial_capital as default
        self.initial_total_value = initial_capital
        
        # Initialize P&L tracking
        self._initialize_pnl_tracking()
        
        # Add caching state for read-only access
        self.latest_pnl_result: Optional[Dict] = None
        self.pnl_history: List[Dict] = []
        self.calculation_timestamps: List[pd.Timestamp] = []
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            'status': self.health_status,
            'error_count': self.error_count,
            'share_class': self.share_class,
            'initial_capital': self.initial_capital,
            'attribution_types_count': len(self.attribution_types),
            'component': self.__class__.__name__
        }
    
    def _log_pnl_calculation(self, pnl_data: Dict[str, Any]) -> None:
        """Log P&L calculation as domain event."""
        if not self.log_dir or not self.domain_event_logger:
            return
        
        timestamp = datetime.now().isoformat()
        real_utc = datetime.now(timezone.utc).isoformat()
        
        calculation = PnLCalculation(
            timestamp=timestamp,
            real_utc_time=real_utc,
            correlation_id=self.correlation_id,
            pid=self.pid,
            realized_pnl=pnl_data.get('realized_pnl', 0.0),
            unrealized_pnl=pnl_data.get('unrealized_pnl', 0.0),
            total_pnl=pnl_data.get('total_pnl', 0.0),
            fees_paid=pnl_data.get('fees_paid', 0.0),
            funding_received=pnl_data.get('funding_received', 0.0),
            pnl_by_venue=pnl_data.get('pnl_by_venue', {}),
            pnl_by_asset=pnl_data.get('pnl_by_asset', {}),
            metadata={}
        )
        
        self.domain_event_logger.log_pnl_calculation(calculation)
    
    def _initialize_pnl_tracking(self):
        """Initialize P&L tracking variables."""
        # Previous exposure for delta calculations
        self.previous_exposure = None
        
        
        
        # Get currency symbol based on share class
        currency_symbol = "ETH" if self.share_class == "ETH" else "USDT" if self.share_class == "USDT" else "BTC" if self.share_class == "BTC" else "$"
        
        logger.info(f"P&L Calculator initialized for {self.share_class} share class with {self.initial_capital:,.2f} {currency_symbol} initial capital")
        self.logger.info(
            f"P&L Calculator initialized: share_class={self.share_class}, initial_capital={self.initial_capital:,.2f} {currency_symbol}",
            event_type="pnl_monitor_initialized",
            share_class=self.share_class,
            initial_capital=self.initial_capital
        )
    
    def _calculate_pnl(
        self,
        current_exposure: Dict,
        previous_exposure: Optional[Dict] = None,
        timestamp: pd.Timestamp = None,
        period_start: pd.Timestamp = None
    ) -> Dict:
        """
        Explicitly calculate P&L and store results.
        
        This method performs full P&L calculation and updates internal state.
        For read-only access to cached results, use get_latest_pnl().
        
        Triggered by: Risk Monitor updates (sequential chain)
        """
        try:
            if timestamp is None:
                timestamp = pd.Timestamp.now(tz='UTC')
            
            self.logger.info(f"P&L Calculator: Starting P&L calculation for timestamp {timestamp}")
            if period_start is None:
                period_start = timestamp
            
            # Set initial value if first calculation
            if self.initial_total_value is None:
                # Use initial capital as baseline, not first exposure value
                # The first exposure value already includes liquidity index growth
                self.initial_total_value = self.initial_capital
                logger.info(f"Initial portfolio value set to ${self.initial_total_value:,.2f} (initial capital)")
                self.logger.info(f"P&L Calculator: Initial portfolio value set to ${self.initial_total_value:,.2f} (initial capital)")
                self.logger.info(f"P&L Calculator: First exposure total_value_usd: ${current_exposure['total_value_usd']:,.2f}")
            else:
                self.logger.info(f"P&L Calculator: Using existing initial_total_value: ${self.initial_total_value:,.2f}")
            
            # Use utility_manager for config-driven operations if available
            if self.utility_manager:
                # Get share class from config via utility_manager
                share_class = self.utility_manager.get_share_class_from_mode(self.config.get('mode', 'default'))
                self.logger.info(f"P&L Calculator: Using share class {share_class} from config")
            
            # 1. Balance-Based P&L (source of truth)
            self.logger.info(f"P&L Calculator: About to calculate balance-based P&L")
            self.logger.info(f"P&L Calculator: Current exposure keys: {list(current_exposure.keys())}")
            balance_pnl_data = self._calculate_balance_based_pnl(
                current_exposure,
                period_start,
                current_time=timestamp
            )
            self.logger.info(f"P&L Calculator: Balance-based P&L calculated successfully")
            
            # 2. Attribution P&L (breakdown)
            attribution_pnl_data = self._calculate_attribution_pnl(
                current_exposure,
                previous_exposure or self.previous_exposure,
                timestamp
            )
            
            # 3. Reconciliation
            reconciliation = self._reconcile_pnl(
                balance_pnl_data,
                attribution_pnl_data,
                period_start,
                current_time=timestamp
            )
            
            # Combine results
            pnl_data = {
                'timestamp': timestamp,
                'share_class': self.share_class,
                'balance_based': balance_pnl_data,
                'attribution': attribution_pnl_data,
                'reconciliation': reconciliation
            }
            
            # Store previous exposure for next calculation
            self.previous_exposure = current_exposure.copy()
            
            # Store results in cache for read-only access
            self.latest_pnl_result = pnl_data
            self.pnl_history.append(pnl_data)
            self.calculation_timestamps.append(timestamp)
            
            # Log P&L calculation
            self._log_pnl_calculation(pnl_data)
            
            logger.debug(f"P&L calculated: balance=${balance_pnl_data['pnl_cumulative']:,.2f}, attribution=${attribution_pnl_data['pnl_cumulative']:,.2f}")
            return pnl_data
            
        except PnLCalculatorError:
            # Re-raise our custom errors as-is
            raise
        except Exception as e:
            raise PnLCalculatorError(
                'PNL-003',
                message=f"Balance-based P&L calculation failed: {e}",
                error=str(e),
                timestamp=timestamp.isoformat() if timestamp else None
            )
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> None:
        """
        Update component state (called by EventDrivenStrategyEngine).
        
        Args:
            timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
            trigger_source: 'full_loop' | 'tight_loop' | 'manual'
            **kwargs: Additional parameters (not used, gets exposure from exposure_monitor)
        """
        # Get current exposure from exposure_monitor reference
        if self.exposure_monitor:
            current_exposure = self.exposure_monitor.get_current_exposure()
            previous_exposure = self.previous_exposure
            
            if current_exposure:
                # Perform P&L calculation using private method
                pnl_result = self._calculate_pnl(
                    current_exposure=current_exposure,
                    previous_exposure=previous_exposure,
                    timestamp=timestamp
                )
                
                # Log P&L calculation
                self.logger.info(
                    f"P&L calculation completed: trigger_source={trigger_source}, "
                    f"balance_pnl={pnl_result.get('balance_based', {}).get('pnl_cumulative', 0.0):.2f}, "
                    f"attribution_pnl={pnl_result.get('attribution', {}).get('pnl_cumulative', 0.0):.2f}"
                )
        else:
            self.logger.warning("No exposure_monitor reference available for P&L calculation")
    
    def _calculate_balance_based_pnl(
        self,
        current_exposure: Dict,
        period_start: pd.Timestamp,
        current_time: pd.Timestamp
    ) -> Dict:
        """Calculate P&L from portfolio value change in share class currency."""
        try:
            self.logger.info(f"P&L Calculator: _calculate_balance_based_pnl called with current_exposure type: {type(current_exposure)}")
            self.logger.info(f"P&L Calculator: current_exposure keys: {list(current_exposure.keys()) if isinstance(current_exposure, dict) else 'Not a dict'}")
            
            # Use share class value for P&L calculation
            if 'share_class_value' not in current_exposure:
                raise PnLCalculatorError(
                    'PNL-003',
                    message="Missing share_class_value in current exposure",
                    exposure_keys=list(current_exposure.keys())
                )
            
            current_value = current_exposure['share_class_value']
            
            # Calculate P&L as the change in share class value since initial snapshot
            # This is mode-agnostic - it measures the change in total portfolio value in share class currency
            pnl_cumulative = current_value - self.initial_total_value
            self.logger.info(f"P&L Calculator: Balance-based P&L - current_value: ${current_value:,.2f}, initial_total_value: ${self.initial_total_value:,.2f}, pnl_cumulative: ${pnl_cumulative:,.2f}")
            
            # Calculate hourly P&L if we have previous exposure
            if self.previous_exposure:
                if 'share_class_value' not in self.previous_exposure:
                    raise PnLCalculatorError(
                        'PNL-004',
                        message="Previous exposure missing share_class_value",
                        previous_keys=list(self.previous_exposure.keys())
                    )
                previous_value = self.previous_exposure['share_class_value']
                pnl_hourly = current_value - previous_value
            else:
                pnl_hourly = 0.0
            
            return {
                'total_value_current': current_value,
                'total_value_initial': self.initial_total_value,
                'pnl_hourly': pnl_hourly,
                'pnl_cumulative': pnl_cumulative,
                'pnl_pct': (pnl_cumulative / self.initial_capital) * 100
            }
            
        except PnLCalculatorError:
            raise
        except Exception as e:
            raise PnLCalculatorError(
                'PNL-003',
                message=f"Balance-based P&L calculation failed: {e}",
                error=str(e),
                current_value=current_exposure.get('total_value_usd'),
                initial_value=self.initial_total_value
            )
    
    def _calculate_attribution_pnl(
        self,
        current_exposure: Dict,
        previous_exposure: Optional[Dict],
        timestamp: pd.Timestamp
    ) -> Dict:
        """Calculate P&L from component breakdown."""
        if previous_exposure is None:
            # First hour, no P&L yet
            return self._zero_attribution()
        
        # Ensure previous_exposure is a dictionary, not a Timestamp
        if not isinstance(previous_exposure, dict):
            self.logger.warning(f"Previous exposure is not a dict: {type(previous_exposure)}, returning zero attribution")
            return self._zero_attribution()
        
        # Config-driven attribution calculation
        # All strategies use the same attribution logic based on config-driven attribution types
        return self._calculate_config_driven_attribution(current_exposure, previous_exposure, timestamp)
    
    
    def _calculate_config_driven_attribution(
        self,
        current_exposure: Dict,
        previous_exposure: Dict,
        timestamp: pd.Timestamp
    ) -> Dict:
        """Calculate P&L attribution using config-driven attribution types."""
        attribution_pnl = {}
        
        # Calculate each enabled attribution type from config
        for attr_type in self.attribution_types:
            try:
                if attr_type == 'supply_yield':
                    attribution_pnl[attr_type] = self._calc_supply_yield(current_exposure, previous_exposure)
                elif attr_type == 'borrow_costs':
                    attribution_pnl[attr_type] = self._calc_borrow_costs(current_exposure, previous_exposure)
                elif attr_type == 'staking_yield_oracle':
                    attribution_pnl[attr_type] = self._calc_staking_yield_oracle(current_exposure, previous_exposure)
                elif attr_type == 'staking_yield_rewards':
                    attribution_pnl[attr_type] = self._calc_staking_yield_rewards(current_exposure, previous_exposure)
                elif attr_type == 'funding_pnl':
                    attribution_pnl[attr_type] = self._calc_funding_pnl(current_exposure, timestamp)
                elif attr_type == 'delta_pnl':
                    attribution_pnl[attr_type] = self._calc_delta_pnl(current_exposure, previous_exposure)
                elif attr_type == 'basis_pnl':
                    attribution_pnl[attr_type] = self._calc_basis_pnl(current_exposure, previous_exposure)
                elif attr_type == 'dust_pnl':
                    attribution_pnl[attr_type] = self._calc_dust_pnl(current_exposure, previous_exposure)
                elif attr_type == 'transaction_costs':
                    attribution_pnl[attr_type] = self._calc_transaction_costs(current_exposure, previous_exposure)
                else:
                    self.logger.warning(f"Unknown attribution type: {attr_type}")
                    attribution_pnl[attr_type] = 0.0
            
            except Exception as e:
                self.logger.error(f"Error calculating {attr_type}: {e}")
                attribution_pnl[attr_type] = 0.0  # Gracefully handle errors
        
        # Update cumulative tracking
        for attr_type, value in attribution_pnl.items():
            if attr_type in self.cumulative:
                self.cumulative[attr_type] += value
        
        # Add cumulative totals
        attribution_pnl['pnl_cumulative'] = sum(self.cumulative.values())
        
        return attribution_pnl
    
    def _zero_attribution(self) -> Dict:
        """Return zero attribution for first calculation."""
        return {
            'supply_pnl': 0.0,
            'staking_pnl': 0.0,
            'price_change_pnl': 0.0,
            'borrow_cost': 0.0,
            'funding_pnl': 0.0,
            'delta_pnl': 0.0,
            'transaction_costs': 0.0,
            'pnl_hourly': 0.0,
            'cumulative_supply_pnl': 0.0,
            'cumulative_staking_pnl': 0.0,
            'cumulative_price_change_pnl': 0.0,
            'cumulative_borrow_cost': 0.0,
            'cumulative_funding_pnl': 0.0,
            'cumulative_delta_pnl': 0.0,
            'cumulative_transaction_costs': 0.0,
            'pnl_cumulative': 0.0
        }
    
    def _calc_supply_yield(self, current: Dict, previous: Dict) -> float:
        """Calculate AAVE supply yield from index growth."""
        if previous is None:
            return 0.0
            
        supply_pnl = 0.0
        
        # Ensure both parameters are dictionaries
        if not isinstance(current, dict) or not isinstance(previous, dict):
            self.logger.warning(f"Supply yield calculation: current type: {type(current)}, previous type: {type(previous)}")
            return 0.0
        
        # Calculate aWeETH supply P&L (for ETH-based strategies)
        current_aweeth = current.get('exposures', {}).get('aWeETH', {})
        previous_aweeth = previous.get('exposures', {}).get('aWeETH', {})
        
        if current_aweeth and previous_aweeth:
            # Supply P&L = (current_underlying - previous_underlying) × oracle_price × eth_price
            current_underlying = current_aweeth.get('underlying_native', 0)
            previous_underlying = previous_aweeth.get('underlying_native', 0)
            
            if previous_underlying > 0:
                # Use utility manager for price conversions
                if self.utility_manager:
                    oracle_price = self.utility_manager.get_oracle_price('weETH', current_aweeth.get('timestamp'))
                    eth_price = self.utility_manager.get_market_price('ETH', current_aweeth.get('timestamp'))
                else:
                    # Fallback values when utility manager is not available
                    oracle_price = 1.0
                    eth_price = 3000.0
                
                underlying_change = current_underlying - previous_underlying
                aweeth_pnl = underlying_change * oracle_price * eth_price
                supply_pnl += aweeth_pnl
        
        # Calculate aUSDT supply P&L (for pure lending strategies)
        current_ausdt = current.get('exposures', {}).get('aUSDT', {})
        previous_ausdt = previous.get('exposures', {}).get('aUSDT', {})
        
        if current_ausdt and previous_ausdt:
            # Supply P&L = (current_underlying - previous_underlying) × 1.0 (USDT is 1:1 with USD)
            current_underlying = current_ausdt.get('underlying_balance', current_ausdt.get('underlying_native', 0))
            previous_underlying = previous_ausdt.get('underlying_balance', previous_ausdt.get('underlying_native', 0))
            
            if previous_underlying > 0:
                underlying_change = current_underlying - previous_underlying
                ausdt_pnl = underlying_change * 1.0  # USDT is 1:1 with USD
                supply_pnl += ausdt_pnl
        
        return supply_pnl
    
    def _calc_staking_yield_oracle(self, current: Dict, previous: Dict) -> float:
        """Calculate staking yield from oracle price changes."""
        if previous is None:
            return 0.0
            
        # Ensure both parameters are dictionaries
        if not isinstance(current, dict) or not isinstance(previous, dict):
            self.logger.warning(f"Staking yield oracle calculation: current type: {type(current)}, previous type: {type(previous)}")
            return 0.0
        
        # This captures the weETH/ETH oracle price appreciation
        # (base staking yield, not seasonal rewards)
        
        current_aweeth = current.get('exposures', {}).get('aWeETH', {})
        previous_aweeth = previous.get('exposures', {}).get('aWeETH', {})
        
        if not current_aweeth or not previous_aweeth:
            return 0.0
        
        # Use utility manager for oracle prices
        if self.utility_manager:
            current_oracle = self.utility_manager.get_oracle_price('weETH', current_aweeth.get('timestamp'))
            previous_oracle = self.utility_manager.get_oracle_price('weETH', previous_aweeth.get('timestamp'))
            eth_price = self.utility_manager.get_market_price('ETH', current_aweeth.get('timestamp'))
        else:
            current_oracle = current_aweeth.get('oracle_price', 1.0)
            previous_oracle = previous_aweeth.get('oracle_price', 1.0)
            eth_price = current_aweeth.get('eth_usd_price', 3000.0)
        
        if previous_oracle == 0:
            return 0.0
        
        # Staking P&L = underlying_weETH × oracle_change × eth_price
        underlying_weeth = current_aweeth.get('underlying_native', 0)
        oracle_change = current_oracle - previous_oracle
        
        staking_pnl = underlying_weeth * oracle_change * eth_price
        
        return staking_pnl
    
    def _calc_price_change_pnl(self, current: Dict, previous: Dict) -> float:
        """Calculate P&L from ETH price changes on net exposure."""
        # Ensure both parameters are dictionaries
        if not isinstance(current, dict) or not isinstance(previous, dict):
            self.logger.warning(f"Price change PnL calculation: current type: {type(current)}, previous type: {type(previous)}")
            return 0.0
        # This captures the effect of ETH price changes on the net delta
        current_eth_price = current['exposures'].get('aWeETH', {}).get('eth_usd_price', 3000.0)
        previous_eth_price = previous['exposures'].get('aWeETH', {}).get('eth_usd_price', 3000.0)
        
        if previous_eth_price == 0:
            return 0.0
        
        # Use previous net delta (before price change)
        net_delta_eth = previous.get('net_delta_eth', 0)
        
        # Use utility manager for price conversion
        if self.utility_manager:
            price_change = self.utility_manager.convert_price(previous_eth_price, current_eth_price, 1.0)
        else:
            price_change = current_eth_price - previous_eth_price
        
        price_change_pnl = net_delta_eth * price_change
        
        return price_change_pnl
    
    def _calc_borrow_costs(self, current: Dict, previous: Dict) -> float:
        """Calculate AAVE borrow costs from debt index growth."""
        if previous is None:
            return 0.0
            
        # Ensure both parameters are dictionaries
        if not isinstance(current, dict) or not isinstance(previous, dict):
            self.logger.warning(f"Borrow cost calculation: current type: {type(current)}, previous type: {type(previous)}")
            return 0.0
        
        # Get debt exposure
        current_debt = current.get('exposures', {}).get('variableDebtWETH', {})
        previous_debt = previous.get('exposures', {}).get('variableDebtWETH', {})
        
        if not current_debt or not previous_debt:
            return 0.0
        
        # Borrow cost = (current_underlying - previous_underlying) × eth_price
        current_underlying = current_debt.get('underlying_native', 0)
        previous_underlying = previous_debt.get('underlying_native', 0)
        
        if previous_underlying == 0:
            return 0.0
        
        # Use utility manager for price conversions
        if self.utility_manager:
            eth_price = self.utility_manager.get_market_price('ETH', current_debt.get('timestamp'))
        else:
            eth_price = current_debt.get('eth_usd_price', 3000.0)
            
        underlying_change = current_underlying - previous_underlying
        
        # Borrow cost is negative (cost)
        borrow_cost = -underlying_change * eth_price
        
        return borrow_cost
    
    def _calc_funding_pnl(self, current: Dict, timestamp: pd.Timestamp) -> float:
        """Calculate perp funding P&L (only at funding times: 0/8/16 UTC)."""
        # Funding happens every 8 hours at 0, 8, 16 UTC
        hour = timestamp.hour
        if hour not in [0, 8, 16]:
            return 0.0
        
        # Sum funding P&L from all perp positions
        total_funding_pnl = 0.0
        
        for token, exp in current['exposures'].items():
            if 'PERP' in token and 'unrealized_pnl' in exp:
                # This is a simplified calculation
                # In reality, you'd track funding payments separately
                # For now, we'll use a placeholder
                position_size = abs(exp.get('size', 0))
                if position_size > 0:
                    # Estimate funding rate (this would come from market data)
                    # Get funding rate from data provider via utility manager
                    if self.utility_manager:
                        funding_rate = self.utility_manager.get_funding_rate('binance', token, timestamp)
                    else:
                        funding_rate = 0.0001  # Fallback if no utility manager
                    funding_pnl = position_size * funding_rate * exp.get('mark_price', 3000)
                    total_funding_pnl += funding_pnl
        
        return total_funding_pnl
    
    def _calc_funding_pnl(self, current: Dict, timestamp: pd.Timestamp) -> float:
        """Calculate funding P&L using ACTUAL funding rates (NO FALLBACKS) for any asset."""
        # Funding happens every 8 hours at 0, 8, 16 UTC
        hour = timestamp.hour
        if hour not in [0, 8, 16]:
            return 0.0
        
        total_funding_pnl = 0.0
        
        # Get BTC perp positions
        btc_exposure = current.get('exposures', {}).get('BTC', {})
        perp_positions = btc_exposure.get('cex_perps', {})
        
        for venue, position in perp_positions.items():
            if position and position.get('size', 0) != 0:
                # Get actual funding rate for this venue from data provider
                funding_rate = self._get_btc_funding_rate(venue, timestamp)
                
                # Calculate funding payment (positive = receive, negative = pay)
                position_size_usd = abs(position.get('size', 0)) * position.get('mark_price', 50000)
                funding_payment = position_size_usd * funding_rate
                
                # Short positions receive funding when rate is positive
                if position.get('size', 0) < 0:  # Short position
                    total_funding_pnl += funding_payment
                else:  # Long position
                    total_funding_pnl -= funding_payment
        
        return total_funding_pnl
    
    def _get_btc_funding_rate(self, venue: str, timestamp: pd.Timestamp) -> float:
        """Get BTC funding rate for a specific venue using UtilityManager."""
        if not self.utility_manager:
            raise PnLCalculatorError(
                'PNL-BTC-001', 
                f"No utility manager available for funding rate lookup for {venue}"
            )
        
        try:
            # Use UtilityManager for centralized funding rate access
            return self.utility_manager.get_funding_rate(venue, 'BTCUSDT', timestamp)
        except Exception as e:
            raise PnLCalculatorError(
                'PNL-BTC-001',
                f"Failed to get funding rate for {venue}: {e}"
            )
    
    def _calc_basis_spread_pnl(self, current: Dict, previous: Dict) -> float:
        """Calculate basis spread P&L (futures-spot price difference changes) for any asset."""
        if not previous:
            return 0.0
        
        # Get current and previous basis spreads
        current_basis = self._get_btc_basis_spread(current)
        previous_basis = self._get_btc_basis_spread(previous)
        
        # Calculate basis spread change
        basis_change = current_basis - previous_basis
        
        # Get hedged exposure (min of spot and perp positions)
        hedged_exposure = self._get_btc_hedged_exposure(current)
        
        # Basis spread P&L = hedged_exposure * basis_change
        basis_spread_pnl = hedged_exposure * basis_change
        
        return basis_spread_pnl
    
    def _get_btc_basis_spread(self, exposure: Dict) -> float:
        """Get BTC basis spread (futures - spot) per venue, then aggregate."""
        # Get spot price
        spot_price = exposure.get('market_data', {}).get('btc_usd_price', 50000)
        
        # Get weighted average futures price across all venues
        btc_exposure = exposure.get('exposures', {}).get('BTC', {})
        perp_positions = btc_exposure.get('cex_perps', {})
        
        total_futures_value = 0.0
        total_size = 0.0
        
        for venue, position in perp_positions.items():
            if position and position.get('size', 0) != 0:
                futures_price = position.get('mark_price', spot_price)
                size = abs(position.get('size', 0))
                total_futures_value += futures_price * size
                total_size += size
        
        if total_size == 0:
            return 0.0
        
        avg_futures_price = total_futures_value / total_size
        return avg_futures_price - spot_price
    
    def _get_btc_hedged_exposure(self, exposure: Dict) -> float:
        """Get hedged exposure (min of spot and perp positions)."""
        btc_exposure = exposure.get('exposures', {}).get('BTC', {})
        
        # Sum spot positions
        cex_spot = btc_exposure.get('cex_spot', {})
        total_spot = sum(cex_spot.values())
        
        # Sum perp positions (absolute values)
        cex_perps = btc_exposure.get('cex_perps', {})
        total_perp = sum(abs(position.get('size', 0)) for position in cex_perps.values() if position)
        
        # Hedged exposure is the minimum of spot and perp
        return min(total_spot, total_perp)
    
    def _calc_net_delta_pnl(self, current: Dict, previous: Dict) -> float:
        """Calculate net delta P&L (should be ~0 for perfect market neutrality) for any asset."""
        if not previous:
            return 0.0
        
        # Get current and previous net deltas
        current_net_delta = current.get('net_delta_primary_asset', 0)
        previous_net_delta = previous.get('net_delta_primary_asset', 0)
        
        # Get BTC price change using utility manager
        if self.utility_manager:
            current_price = self.utility_manager.get_market_price('BTC', current.get('timestamp'))
            previous_price = self.utility_manager.get_market_price('BTC', previous.get('timestamp'))
            price_change = self.utility_manager.convert_price(previous_price, current_price, 1.0)
        else:
            current_price = current.get('market_data', {}).get('btc_usd_price', 50000)
            previous_price = previous.get('market_data', {}).get('btc_usd_price', 50000)
            price_change = current_price - previous_price
        
        # Net delta P&L = net_delta * price_change
        # For perfect market neutrality, net_delta should be 0
        net_delta_pnl = current_net_delta * price_change
        
        return net_delta_pnl
    
    def _calc_delta_pnl(self, current: Dict, previous: Dict) -> float:
        """Calculate P&L from delta drift."""
        if previous is None:
            return 0.0
            
        # Ensure both parameters are dictionaries
        if not isinstance(current, dict) or not isinstance(previous, dict):
            self.logger.warning(f"Delta PnL calculation: current type: {type(current)}, previous type: {type(previous)}")
            return 0.0
        
        # Delta P&L = (current_delta - previous_delta) × price_change
        current_delta = current.get('net_delta_eth', 0)
        previous_delta = previous.get('net_delta_eth', 0)
        
        # Use utility manager for price conversions
        if self.utility_manager:
            current_eth_price = self.utility_manager.get_market_price('ETH', current.get('timestamp'))
            previous_eth_price = self.utility_manager.get_market_price('ETH', previous.get('timestamp'))
        else:
            current_eth_price = current.get('exposures', {}).get('aWeETH', {}).get('eth_usd_price', 3000.0)
            previous_eth_price = previous.get('exposures', {}).get('aWeETH', {}).get('eth_usd_price', 3000.0)
        
        if previous_eth_price == 0:
            return 0.0
        
        delta_change = current_delta - previous_delta
        
        # Use utility manager for price conversion
        if self.utility_manager:
            price_change = self.utility_manager.convert_price(previous_eth_price, current_eth_price, 1.0)
        else:
            price_change = current_eth_price - previous_eth_price
        
        # Use average delta for the period
        avg_delta = (current_delta + previous_delta) / 2
        delta_pnl = avg_delta * price_change
        
        return delta_pnl
    
    def _reconcile_pnl(
        self,
        balance_pnl_data: Dict,
        attribution_pnl_data: Dict,
        period_start: pd.Timestamp,
        current_time: pd.Timestamp
    ) -> Dict:
        """Reconcile balance-based vs attribution P&L."""
        balance_pnl = balance_pnl_data['pnl_cumulative']
        attribution_pnl = attribution_pnl_data['pnl_cumulative']
        
        difference = balance_pnl - attribution_pnl
        unexplained_pnl = difference
        
        # Calculate tolerance (2% annualized)
        period_months = (current_time - period_start).total_seconds() / (30 * 24 * 3600)  # Approximate months
        tolerance = self.initial_capital * 0.02 * (period_months / 12)
        
        passed = abs(difference) <= tolerance
        diff_pct_of_capital = (difference / self.initial_capital) * 100
        
        return {
            'balance_pnl': balance_pnl,
            'attribution_pnl': attribution_pnl,
            'difference': difference,
            'unexplained_pnl': unexplained_pnl,
            'tolerance': tolerance,
            'passed': passed,
            'diff_pct_of_capital': diff_pct_of_capital,
            
            # Potential sources of unexplained P&L
            'potential_sources': {
                'spread_basis_pnl': 'Spot-perp spread changes not explicitly tracked',
                'seasonal_rewards_unsold': 'EIGEN/ETHFI tokens received but not sold to USD',
                'funding_notional_drift': 'Funding on entry notional vs current exposure',
                'yield_calc_approximations': 'Hourly accrual vs actual discrete payments'
            }
        }
    
    
    def _get_pnl_summary(self, pnl_data: Dict) -> str:
        """Get a human-readable P&L summary."""
        balance = pnl_data['balance_based']
        attribution = pnl_data['attribution']
        recon = pnl_data['reconciliation']
        
        summary = f"P&L Summary ({pnl_data['share_class']} share class):\n"
        summary += f"Balance-based: ${balance['pnl_cumulative']:,.2f} ({balance['pnl_pct']:.2f}%)\n"
        summary += f"Attribution: ${attribution['pnl_cumulative']:,.2f}\n"
        summary += f"Reconciliation: {'✅ PASSED' if recon['passed'] else '⚠️ FAILED'}\n"
        summary += f"Difference: ${recon['difference']:,.2f} ({recon['diff_pct_of_capital']:.3f}%)\n"
        
        if not recon['passed']:
            summary += f"Tolerance: ${recon['tolerance']:,.2f}\n"
        
        return summary
    
    def _calc_transaction_costs(self, current: Dict, previous: Dict) -> float:
        """Calculate transaction costs from trading activity."""
        # For BTC basis, transaction costs come from:
        # 1. Spot trading fees (typically 0.1% per trade)
        # 2. Perp trading fees (typically 0.1% per trade)
        # 3. Transfer fees (minimal for most CEX)
        
        # For now, return a simple estimate based on position changes
        # In a full implementation, this would track actual trade execution costs
        
        transaction_costs = 0.0
        
        # Check for position changes that would indicate trading activity
        if previous:
            # Compare spot positions
            current_spot = current.get('exposures', {}).get('BTC', {}).get('cex_spot', {})
            previous_spot = previous.get('exposures', {}).get('BTC', {}).get('cex_spot', {})
            
            for venue in current_spot:
                current_size = current_spot[venue].get('size', 0) if current_spot[venue] else 0
                previous_size = previous_spot.get(venue, {}).get('size', 0) if previous_spot.get(venue) else 0
                
                if abs(current_size - previous_size) > 0.001:  # Position changed
                    # Estimate 0.1% fee on the traded amount
                    traded_amount = abs(current_size - previous_size)
                    current_price = current_spot[venue].get('price', 50000) if current_spot[venue] else 50000
                    transaction_costs += traded_amount * current_price * 0.001
            
            # Compare perp positions
            current_perp = current.get('exposures', {}).get('BTC', {}).get('cex_perps', {})
            previous_perp = previous.get('exposures', {}).get('BTC', {}).get('cex_perps', {})
            
            for venue in current_perp:
                current_size = current_perp[venue].get('size', 0) if current_perp[venue] else 0
                previous_size = previous_perp.get(venue, {}).get('size', 0) if previous_perp.get(venue) else 0
                
                if abs(current_size - previous_size) > 0.001:  # Position changed
                    # Estimate 0.1% fee on the traded amount
                    traded_amount = abs(current_size - previous_size)
                    current_price = current_perp[venue].get('mark_price', 50000) if current_perp[venue] else 50000
                    transaction_costs += traded_amount * current_price * 0.001
        
        return transaction_costs
    
    def _calc_staking_yield_rewards(self, current: Dict, previous: Dict) -> float:
        """
        Calculate staking yield from LST token value changes using AAVE oracle pricing.
        
        Staking yield = change in underlying token value (LST converted at AAVE oracle pricing)
        
        Args:
            current: Current exposure data
            previous: Previous exposure data
            
        Returns:
            Staking yield P&L in USD
        """
        if previous is None:
            return 0.0
            
        try:
            staking_yield = 0.0
            
            # Get current and previous exposures
            current_exposures = current.get('exposures', {})
            previous_exposures = previous.get('exposures', {})
            
            # Check each asset for LST positions
            for asset in current_exposures.keys():
                current_asset_exposure = current_exposures.get(asset, {})
                previous_asset_exposure = previous_exposures.get(asset, {})
                
                # Check for LST positions (stETH, eETH, wstETH, weETH)
                lst_tokens = ['stETH', 'eETH', 'wstETH', 'weETH']
                for lst_token in lst_tokens:
                    if lst_token in asset:
                        current_lst_amount = current_asset_exposure.get('amount', 0)
                        previous_lst_amount = previous_asset_exposure.get('amount', 0)
                        
                        if current_lst_amount > 0 or previous_lst_amount > 0:
                            # Get AAVE oracle prices for LST tokens
                            current_lst_price = self._get_aave_oracle_price(lst_token, current.get('timestamp'))
                            previous_lst_price = self._get_aave_oracle_price(lst_token, previous.get('timestamp'))
                            
                            if current_lst_price > 0 and previous_lst_price > 0:
                                # Calculate yield from price change
                                current_value = current_lst_amount * current_lst_price
                                previous_value = previous_lst_amount * previous_lst_price
                                
                                # Staking yield = change in token value
                                asset_yield = current_value - previous_value
                                staking_yield += asset_yield
                                
                                # Calculate price change using utility manager
                                if self.utility_manager:
                                    price_change = self.utility_manager.convert_price(previous_lst_price, current_lst_price, 1.0)
                                else:
                                    price_change = current_lst_price - previous_lst_price
                                
                                logger.debug(f"Staking yield for {lst_token}: amount_change={current_lst_amount - previous_lst_amount}, price_change={price_change:.6f}, yield={asset_yield:.2f}")
            
            return staking_yield
            
        except Exception as e:
            logger.error(f"Error calculating staking yield: {e}")
            return 0.0
    
    def _get_aave_oracle_price(self, token: str, timestamp: pd.Timestamp) -> float:
        """
        Get AAVE oracle price for LST token using UtilityManager.
        
        Args:
            token: LST token symbol (e.g., 'wstETH', 'weETH')
            timestamp: Timestamp for price lookup
            
        Returns:
            Price in USD from AAVE oracle
        """
        if not self.utility_manager:
            logger.warning(f"No utility manager available for oracle price lookup for {token}")
            return 0.0
        
        try:
            # Use UtilityManager for centralized oracle price access
            return self.utility_manager.get_oracle_price(token, timestamp)
        except Exception as e:
            logger.error(f"Error getting AAVE oracle price for {token}: {e}")
            return 0.0
    
    def _calc_basis_pnl(self, current: Dict, previous: Dict) -> float:
        """
        Calculate basis P&L from spot-perp spread changes.
        
        Basis P&L = min(long_amount, short_amount) * spread_price_change
        
        Args:
            current: Current exposure data
            previous: Previous exposure data
            
        Returns:
            Basis P&L in USD
        """
        if previous is None:
            return 0.0
            
        try:
            basis_pnl = 0.0
            
            # Get current and previous exposures
            current_exposures = current.get('exposures', {})
            previous_exposures = previous.get('exposures', {})
            
            # Check each asset for basis trading positions
            for asset in current_exposures.keys():
                current_asset_exposure = current_exposures.get(asset, {})
                previous_asset_exposure = previous_exposures.get(asset, {})
                
                # Check for spot long and perp short positions
                current_spot_long = current_asset_exposure.get('spot_long', {}).get('amount', 0)
                current_perp_short = current_asset_exposure.get('perp_short', {}).get('amount', 0)
                previous_spot_long = previous_asset_exposure.get('spot_long', {}).get('amount', 0)
                previous_perp_short = previous_asset_exposure.get('perp_short', {}).get('amount', 0)
                
                # Only calculate if we have both spot long and perp short positions
                if current_spot_long > 0 and current_perp_short > 0:
                    # Calculate the minimum of long and short positions
                    min_position = min(current_spot_long, current_perp_short)
                    
                    # Get current and previous spread prices
                    current_spot_price = current_asset_exposure.get('spot_long', {}).get('price', 0)
                    current_perp_price = current_asset_exposure.get('perp_short', {}).get('price', 0)
                    previous_spot_price = previous_asset_exposure.get('spot_long', {}).get('price', 0)
                    previous_perp_price = previous_asset_exposure.get('perp_short', {}).get('price', 0)
                    
                    if current_spot_price > 0 and current_perp_price > 0 and previous_spot_price > 0 and previous_perp_price > 0:
                        # Calculate spread change
                        current_spread = current_spot_price - current_perp_price
                        previous_spread = previous_spot_price - previous_perp_price
                        spread_change = current_spread - previous_spread
                        
                        # Basis P&L = min(long, short) * spread_change
                        asset_basis_pnl = min_position * spread_change
                        basis_pnl += asset_basis_pnl
                        
                        logger.debug(f"Basis P&L for {asset}: min_pos={min_position}, spread_change={spread_change:.6f}, pnl={asset_basis_pnl:.2f}")
            
            return basis_pnl
            
        except Exception as e:
            logger.error(f"Error calculating basis P&L: {e}")
            return 0.0
    
    def _calc_dust_pnl(self, current: Dict, previous: Dict) -> float:
        """
        Calculate dust token price movements using protocol token prices.
        
        Dust P&L = change in dust token values from data/market_data/spot_prices/protocol_tokens/
        
        Args:
            current: Current exposure data
            previous: Previous exposure data
            
        Returns:
            Dust P&L in USD
        """
        if previous is None:
            return 0.0
            
        try:
            dust_pnl = 0.0
            
            # Get current and previous exposures
            current_exposures = current.get('exposures', {})
            previous_exposures = previous.get('exposures', {})
            
            # Define dust tokens (EIGEN, ETHFI, KING)
            dust_tokens = ['EIGEN', 'ETHFI', 'KING']
            
            # Check each asset for dust token positions
            for asset in current_exposures.keys():
                current_asset_exposure = current_exposures.get(asset, {})
                previous_asset_exposure = previous_exposures.get(asset, {})
                
                # Check if this is a dust token
                for dust_token in dust_tokens:
                    if dust_token in asset:
                        current_dust_amount = current_asset_exposure.get('amount', 0)
                        previous_dust_amount = previous_asset_exposure.get('amount', 0)
                        
                        if current_dust_amount > 0 or previous_dust_amount > 0:
                            # Get protocol token prices
                            current_dust_price = self._get_protocol_token_price(dust_token, current.get('timestamp'))
                            previous_dust_price = self._get_protocol_token_price(dust_token, previous.get('timestamp'))
                            
                            if current_dust_price > 0 and previous_dust_price > 0:
                                # Calculate P&L from price change
                                current_value = current_dust_amount * current_dust_price
                                previous_value = previous_dust_amount * previous_dust_price
                                
                                # Dust P&L = change in token value
                                asset_dust_pnl = current_value - previous_value
                                dust_pnl += asset_dust_pnl
                                
                                # Calculate price change using utility manager
                                if self.utility_manager:
                                    price_change = self.utility_manager.convert_price(previous_dust_price, current_dust_price, 1.0)
                                else:
                                    price_change = current_dust_price - previous_dust_price
                                
                                logger.debug(f"Dust P&L for {dust_token}: amount_change={current_dust_amount - previous_dust_amount}, price_change={price_change:.6f}, pnl={asset_dust_pnl:.2f}")
            
            return dust_pnl
            
        except Exception as e:
            logger.error(f"Error calculating dust P&L: {e}")
            return 0.0
    
    def _get_protocol_token_price(self, token: str, timestamp: pd.Timestamp) -> float:
        """
        Get protocol token price from data/market_data/spot_prices/protocol_tokens/.
        
        Args:
            token: Protocol token symbol (e.g., 'EIGEN', 'ETHFI', 'KING')
            timestamp: Timestamp for price lookup
            
        Returns:
            Price in USD from protocol token data
        """
        try:
            # Get data from data provider
            data = self.data_provider.get_data(timestamp)
            protocol_prices = data.get('market_data', {}).get('protocol_token_prices', {})
            
            # Map token names to price keys
            token_mapping = {
                'EIGEN': 'eigen',
                'ETHFI': 'ethfi',
                'KING': 'king'
            }
            
            price_key = token_mapping.get(token, token.lower())
            price = protocol_prices.get(price_key, 0.0)
            
            if price == 0.0:
                logger.warning(f"Protocol token price not found for {token} (key: {price_key})")
            
            return price
            
        except Exception as e:
            logger.error(f"Error getting protocol token price for {token}: {e}")
            return 0.0
    
    # Read-only methods for cached access
    
    def get_latest_pnl(self) -> Optional[Dict]:
        """Get the most recent P&L result without calculation."""
        return self.latest_pnl_result
    
    def get_pnl_history(self, limit: int = 100) -> List[Dict]:
        """Get P&L history without calculation."""
        return self.pnl_history[-limit:] if self.pnl_history else []
    
    def get_cumulative_attribution(self) -> Dict[str, float]:
        """Get cumulative attribution values without calculation."""
        return self.cumulative.copy()
    
    def get_pnl_summary(self) -> str:
        """Get formatted summary of latest P&L without calculation."""
        if not self.latest_pnl_result:
            return "No P&L data available"
        
        pnl = self.latest_pnl_result
        balance = pnl.get('balance_based', {})
        return f"Total P&L: ${balance.get('pnl_cumulative', 0):,.2f} | Return: {balance.get('pnl_pct', 0):.2f}%"
    

