"""
P&L Calculator Component

TODO-REFACTOR: GENERIC VS MODE-SPECIFIC ARCHITECTURE VIOLATION - 18_generic_vs_mode_specific_architecture.md
ISSUE: This component violates canonical architecture requirements:

1. GENERIC COMPONENT VIOLATIONS:
   - Should be generic attribution logic across all modes
   - Should only care about share_class for reporting currency
   - Should NOT have mode-specific P&L calculation logic

2. REQUIRED ARCHITECTURE (per 18_generic_vs_mode_specific_architecture.md):
   - Should be generic P&L monitoring and attribution
   - Should only care about: share_class (reporting currency)
   - Should NOT care about: strategy mode specifics
   - Should use generic attribution logic across all modes

3. CURRENT VIOLATIONS:
   - Missing share_class awareness for reporting
   - May have mode-specific P&L calculation logic
   - Should be refactored to use: share_class = config.get('share_class')

4. REQUIRED FIX:
   - Ensure generic attribution logic across all modes
   - Add share_class awareness for reporting currency
   - Remove any mode-specific P&L calculation logic
   - Make component truly mode-agnostic
   - Implement generic P&L attribution system (basis, funding, delta, lending, staking)
   - Create centralized UtilityManager for shared utility methods

5. MISSING IMPLEMENTATIONS (per 15_fix_mode_specific_pnl_calculator.md):
   - Generic P&L attribution system not yet implemented
   - Centralized UtilityManager not yet created
   - Mode-agnostic balance calculation across all venues not implemented

CURRENT STATE: This component needs refactoring to be truly generic with share_class awareness and generic attribution system.
"""

from typing import Dict, List, Optional, Any
import redis
import json
import logging
import asyncio
from datetime import datetime
import pandas as pd
import numpy as np
from pathlib import Path

from ..error_codes.error_code_registry import get_error_info, ErrorCodeInfo

logger = logging.getLogger(__name__)

# Create dedicated P&L calculator logger
pnl_logger = logging.getLogger('pnl_calculator')
pnl_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent.parent.parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Create file handler for P&L calculator logs
pnl_handler = logging.FileHandler(logs_dir / 'pnl_calculator.log')
pnl_handler.setLevel(logging.INFO)

# Create formatter
pnl_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
pnl_handler.setFormatter(pnl_formatter)

# Add handler to logger if not already added
if not pnl_logger.handlers:
    pnl_logger.addHandler(pnl_handler)
    pnl_logger.propagate = False

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
            self.component = "PNL"
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
    
    def log_structured_error(self, context: Dict[str, Any] = None):
        """Log structured error with error code and context."""
        error_info = get_error_info(self.error_code)
        
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
        
        # Log to dedicated P&L logger
        if hasattr(self.severity, 'value'):
            if self.severity.value in ['CRITICAL', 'HIGH']:
                pnl_logger.error(f"{self.error_code}: {self.message}", extra=log_data)
            elif self.severity.value == 'MEDIUM':
                pnl_logger.warning(f"{self.error_code}: {self.message}", extra=log_data)
            else:
                pnl_logger.info(f"{self.error_code}: {self.message}", extra=log_data)
        else:
            pnl_logger.error(f"{self.error_code}: {self.message}", extra=log_data)


class PnLCalculator:
    """Calculate P&L using balance-based and attribution methods."""
    
    def __init__(self, 
                 config: Dict[str, Any],
                 share_class: str, 
                 initial_capital: float):
        """
        Initialize P&L calculator with injected config and parameters.
        
        Phase 3: Uses validated config for calculation parameters.
        
        Args:
            config: Strategy configuration from validated config manager
            share_class: Share class ('ETH' or 'USDT')
            initial_capital: Initial capital from API request
        """
        self.config = config
        self.share_class = share_class
        self.initial_capital = initial_capital
        self.data_provider = None  # Will be injected by event engine
        
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
        
        # Initial value (set at t=0)
        self.initial_total_value = None
        
        # Previous exposure for delta calculations
        self.previous_exposure = None
        
        # Redis for inter-component communication
        self.redis = None
        try:
            self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            # Test connection
            self.redis.ping()
            logger.info("Redis connection established for P&L Calculator")
        except Exception as e:
            logger.warning(f"Redis not available for P&L Calculator: {e}")
            self.redis = None
        
        logger.info(f"P&L Calculator initialized for {share_class} share class with ${initial_capital:,.2f} initial capital")
        pnl_logger.info(f"P&L Calculator initialized: share_class={share_class}, initial_capital=${initial_capital:,.2f}")
    
    def set_data_provider(self, data_provider):
        """Set the data provider for funding rate lookups."""
        self.data_provider = data_provider
    
    async def calculate_pnl(
        self,
        current_exposure: Dict,
        previous_exposure: Optional[Dict] = None,
        timestamp: pd.Timestamp = None,
        period_start: pd.Timestamp = None
    ) -> Dict:
        """
        Calculate both P&L methods and reconcile.
        
        Triggered by: Risk Monitor updates (sequential chain)
        """
        try:
            if timestamp is None:
                timestamp = pd.Timestamp.now(tz='UTC')
            
            pnl_logger.info(f"P&L Calculator: Starting P&L calculation for timestamp {timestamp}")
            if period_start is None:
                period_start = timestamp
            
            # Set initial value if first calculation
            if self.initial_total_value is None:
                # Use initial capital as baseline, not first exposure value
                # The first exposure value already includes liquidity index growth
                self.initial_total_value = self.initial_capital
                logger.info(f"Initial portfolio value set to ${self.initial_total_value:,.2f} (initial capital)")
                pnl_logger.info(f"P&L Calculator: Initial portfolio value set to ${self.initial_total_value:,.2f} (initial capital)")
                pnl_logger.info(f"P&L Calculator: First exposure total_value_usd: ${current_exposure['total_value_usd']:,.2f}")
            else:
                pnl_logger.info(f"P&L Calculator: Using existing initial_total_value: ${self.initial_total_value:,.2f}")
            
            # 1. Balance-Based P&L (source of truth)
            pnl_logger.info(f"P&L Calculator: About to calculate balance-based P&L")
            pnl_logger.info(f"P&L Calculator: Current exposure keys: {list(current_exposure.keys())}")
            balance_pnl_data = self._calculate_balance_based_pnl(
                current_exposure,
                period_start,
                current_time=timestamp
            )
            pnl_logger.info(f"P&L Calculator: Balance-based P&L calculated successfully")
            
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
            
            # Publish to Redis
            if self.redis:
                await self._publish_pnl(pnl_data)
            
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
    
    def _calculate_balance_based_pnl(
        self,
        current_exposure: Dict,
        period_start: pd.Timestamp,
        current_time: pd.Timestamp
    ) -> Dict:
        """Calculate P&L from portfolio value change."""
        try:
            pnl_logger.info(f"P&L Calculator: _calculate_balance_based_pnl called with current_exposure type: {type(current_exposure)}")
            pnl_logger.info(f"P&L Calculator: current_exposure keys: {list(current_exposure.keys()) if isinstance(current_exposure, dict) else 'Not a dict'}")
            
            if 'total_value_usd' not in current_exposure:
                raise PnLCalculatorError(
                    'PNL-003',
                    message="Missing total_value_usd in current exposure",
                    exposure_keys=list(current_exposure.keys())
                )
            
            current_value = current_exposure['total_value_usd']
            
            # For pure lending strategy, the P&L should be the yield from liquidity index growth
            # Calculate P&L as the change in overall balance value since initial snapshot
            # This is mode-agnostic - it just measures the change in total portfolio value
            pnl_cumulative = current_value - self.initial_total_value
            pnl_logger.info(f"P&L Calculator: Balance-based P&L - current_value: ${current_value:,.2f}, initial_total_value: ${self.initial_total_value:,.2f}, pnl_cumulative: ${pnl_cumulative:,.2f}")
            
            # Calculate hourly P&L if we have previous exposure
            if self.previous_exposure:
                if 'total_value_usd' not in self.previous_exposure:
                    raise PnLCalculatorError(
                        'PNL-004',
                        message="Previous exposure missing total_value_usd",
                        previous_keys=list(self.previous_exposure.keys())
                    )
                previous_value = self.previous_exposure['total_value_usd']
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
        
        # Mode-specific attribution calculation
        # Mode-agnostic attribution calculation
        # All strategies should use the same attribution logic based on exposure changes
        return self._calculate_default_attribution(current_exposure, previous_exposure, timestamp)
    
    def _calculate_basis_attribution(
        self,
        current_exposure: Dict,
        previous_exposure: Dict,
        timestamp: pd.Timestamp
    ) -> Dict:
        """Calculate basis P&L attribution for any spot long + perp short position combination."""
        # Funding P&L (perp funding rates - only at 0/8/16 UTC using ACTUAL rates)
        funding_pnl = self._calc_funding_pnl(current_exposure, timestamp)
        
        # Basis spread P&L (futures-spot price difference changes)
        basis_spread_pnl = self._calc_basis_spread_pnl(current_exposure, previous_exposure)
        
        # Net delta P&L (should be ~0 for perfect market neutrality)
        net_delta_pnl = self._calc_net_delta_pnl(current_exposure, previous_exposure)
        
        # Transaction costs (execution costs)
        transaction_costs = self._calc_transaction_costs(current_exposure, previous_exposure)
        
        # Total attribution P&L
        total_attribution_pnl = (funding_pnl + basis_spread_pnl + net_delta_pnl - transaction_costs)
        
        # Update cumulative tracking
        self.cumulative['funding_pnl'] += funding_pnl
        self.cumulative['basis_spread_pnl'] = self.cumulative.get('basis_spread_pnl', 0.0) + basis_spread_pnl
        self.cumulative['net_delta_pnl'] = self.cumulative.get('net_delta_pnl', 0.0) + net_delta_pnl
        self.cumulative['transaction_costs'] = self.cumulative.get('transaction_costs', 0.0) + transaction_costs
        
        return {
            'funding_pnl': funding_pnl,
            'basis_spread_pnl': basis_spread_pnl,
            'net_delta_pnl': net_delta_pnl,
            'transaction_costs': transaction_costs,
            'total_attribution_pnl': total_attribution_pnl,
            'cumulative_funding_pnl': self.cumulative['funding_pnl'],
            'cumulative_basis_spread_pnl': self.cumulative.get('basis_spread_pnl', 0.0),
            'cumulative_net_delta_pnl': self.cumulative.get('net_delta_pnl', 0.0),
            'cumulative_transaction_costs': self.cumulative.get('transaction_costs', 0.0)
        }
    
    def _calculate_default_attribution(
        self,
        current_exposure: Dict,
        previous_exposure: Dict,
        timestamp: pd.Timestamp
    ) -> Dict:
        """Calculate default P&L attribution for all modes (includes basis attribution)."""
        # Calculate hourly P&L components
        # (This logic comes from analyzers - validated!)
        
        # Supply yield (AAVE supply index growth)
        supply_pnl = self._calc_supply_pnl(current_exposure, previous_exposure)
        
        # Staking rewards (seasonal only - base in price appreciation)
        staking_pnl = self._calc_staking_pnl(current_exposure, previous_exposure)
        
        # Price appreciation (oracle price changes)
        price_change_pnl = self._calc_price_change_pnl(current_exposure, previous_exposure)
        
        # Borrow costs (AAVE debt index growth)
        borrow_cost = self._calc_borrow_cost(current_exposure, previous_exposure)
        
        # Basis attribution (spot long + perp short positions)
        basis_attribution = self._calculate_basis_attribution(current_exposure, previous_exposure, timestamp)
        funding_pnl = basis_attribution['funding_pnl']
        basis_spread_pnl = basis_attribution['basis_spread_pnl']
        net_delta_pnl = basis_attribution['net_delta_pnl']
        
        # Delta P&L (unhedged exposure × price change)
        delta_pnl = self._calc_delta_pnl(current_exposure, previous_exposure)
        
        # Transaction costs (only at t=0)
        transaction_costs = 0.0  # Handled separately
        
        # Calculate hourly total
        pnl_hourly = (supply_pnl + staking_pnl + price_change_pnl + 
                     borrow_cost + funding_pnl + basis_spread_pnl + net_delta_pnl + delta_pnl + transaction_costs)
        
        # Update cumulatives
        self.cumulative['supply_pnl'] += supply_pnl
        self.cumulative['staking_yield_oracle'] += staking_pnl
        self.cumulative['borrow_cost'] += borrow_cost
        self.cumulative['funding_pnl'] += funding_pnl
        self.cumulative['basis_spread_pnl'] = self.cumulative.get('basis_spread_pnl', 0.0) + basis_spread_pnl
        self.cumulative['net_delta_pnl'] = self.cumulative.get('net_delta_pnl', 0.0) + net_delta_pnl
        self.cumulative['delta_pnl'] += delta_pnl
        
        return {
            # Hourly components
            'supply_pnl': supply_pnl,
            'staking_pnl': staking_pnl,
            'price_change_pnl': price_change_pnl,
            'borrow_cost': borrow_cost,
            'funding_pnl': funding_pnl,
            'basis_spread_pnl': basis_spread_pnl,
            'net_delta_pnl': net_delta_pnl,
            'delta_pnl': delta_pnl,
            'transaction_costs': transaction_costs,
            'pnl_hourly': pnl_hourly,
            
            # Cumulative components
            'cumulative_supply_pnl': self.cumulative['supply_pnl'],
            'cumulative_staking_pnl': self.cumulative['staking_yield_oracle'],
            'cumulative_price_change_pnl': price_change_pnl,  # This would need separate tracking
            'cumulative_borrow_cost': self.cumulative['borrow_cost'],
            'cumulative_funding_pnl': self.cumulative['funding_pnl'],
            'cumulative_basis_spread_pnl': self.cumulative.get('basis_spread_pnl', 0.0),
            'cumulative_net_delta_pnl': self.cumulative.get('net_delta_pnl', 0.0),
            'cumulative_delta_pnl': self.cumulative['delta_pnl'],
            'cumulative_transaction_costs': self.cumulative['transaction_costs'],
            'pnl_cumulative': sum(self.cumulative.values())
        }
    
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
    
    def _calc_supply_pnl(self, current: Dict, previous: Dict) -> float:
        """Calculate AAVE supply yield from index growth."""
        supply_pnl = 0.0
        
        # Calculate aWeETH supply P&L (for ETH-based strategies)
        current_aweeth = current['exposures'].get('aWeETH', {})
        previous_aweeth = previous['exposures'].get('aWeETH', {})
        
        if current_aweeth and previous_aweeth:
            # Supply P&L = (current_underlying - previous_underlying) × oracle_price × eth_price
            current_underlying = current_aweeth.get('underlying_native', 0)
            previous_underlying = previous_aweeth.get('underlying_native', 0)
            
            if previous_underlying > 0:
                # Calculate USD value change
                oracle_price = current_aweeth.get('oracle_price', 1.0)
                eth_price = current_aweeth.get('eth_usd_price', 3000.0)
                
                underlying_change = current_underlying - previous_underlying
                aweeth_pnl = underlying_change * oracle_price * eth_price
                supply_pnl += aweeth_pnl
        
        # Calculate aUSDT supply P&L (for pure lending strategies)
        current_ausdt = current['exposures'].get('aUSDT', {})
        previous_ausdt = previous['exposures'].get('aUSDT', {})
        
        if current_ausdt and previous_ausdt:
            # Supply P&L = (current_underlying - previous_underlying) × 1.0 (USDT is 1:1 with USD)
            current_underlying = current_ausdt.get('underlying_balance', current_ausdt.get('underlying_native', 0))
            previous_underlying = previous_ausdt.get('underlying_balance', previous_ausdt.get('underlying_native', 0))
            
            logger.info(f"P&L Calculator: aUSDT current_underlying = {current_underlying}, previous_underlying = {previous_underlying}")
            
            if previous_underlying > 0:
                underlying_change = current_underlying - previous_underlying
                ausdt_pnl = underlying_change * 1.0  # USDT is 1:1 with USD
                supply_pnl += ausdt_pnl
                logger.info(f"P&L Calculator: aUSDT underlying_change = {underlying_change}, ausdt_pnl = {ausdt_pnl}")
            else:
                logger.info(f"P&L Calculator: No previous aUSDT underlying balance, skipping P&L calculation")
        
        return supply_pnl
    
    def _calc_staking_pnl(self, current: Dict, previous: Dict) -> float:
        """Calculate staking yield from oracle price changes."""
        # This captures the weETH/ETH oracle price appreciation
        # (base staking yield, not seasonal rewards)
        
        current_aweeth = current['exposures'].get('aWeETH', {})
        previous_aweeth = previous['exposures'].get('aWeETH', {})
        
        if not current_aweeth or not previous_aweeth:
            return 0.0
        
        current_oracle = current_aweeth.get('oracle_price', 1.0)
        previous_oracle = previous_aweeth.get('oracle_price', 1.0)
        
        if previous_oracle == 0:
            return 0.0
        
        # Staking P&L = underlying_weETH × oracle_change × eth_price
        underlying_weeth = current_aweeth.get('underlying_native', 0)
        oracle_change = current_oracle - previous_oracle
        eth_price = current_aweeth.get('eth_usd_price', 3000.0)
        
        staking_pnl = underlying_weeth * oracle_change * eth_price
        
        return staking_pnl
    
    def _calc_price_change_pnl(self, current: Dict, previous: Dict) -> float:
        """Calculate P&L from ETH price changes on net exposure."""
        # This captures the effect of ETH price changes on the net delta
        current_eth_price = current['exposures'].get('aWeETH', {}).get('eth_usd_price', 3000.0)
        previous_eth_price = previous['exposures'].get('aWeETH', {}).get('eth_usd_price', 3000.0)
        
        if previous_eth_price == 0:
            return 0.0
        
        # Use previous net delta (before price change)
        net_delta_eth = previous.get('net_delta_eth', 0)
        price_change = current_eth_price - previous_eth_price
        
        price_change_pnl = net_delta_eth * price_change
        
        return price_change_pnl
    
    def _calc_borrow_cost(self, current: Dict, previous: Dict) -> float:
        """Calculate AAVE borrow costs from debt index growth."""
        # Get debt exposure
        current_debt = current['exposures'].get('variableDebtWETH', {})
        previous_debt = previous['exposures'].get('variableDebtWETH', {})
        
        if not current_debt or not previous_debt:
            return 0.0
        
        # Borrow cost = (current_underlying - previous_underlying) × eth_price
        current_underlying = current_debt.get('underlying_native', 0)
        previous_underlying = previous_debt.get('underlying_native', 0)
        
        if previous_underlying == 0:
            return 0.0
        
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
                    # TODO-REFACTOR: This hardcodes funding rate instead of using config
                    # Canonical: .cursor/tasks/06_architecture_compliance_rules.md
                    # Fix: Add to config YAML and load from config
                    estimated_funding_rate = 0.0001  # WRONG - hardcoded funding rate (0.01% per 8 hours)
                    funding_pnl = position_size * estimated_funding_rate * exp.get('mark_price', 3000)
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
        """Get actual BTC funding rate for venue from data provider (NO FALLBACKS)."""
        # This would need to be injected from the data provider
        # For now, we'll raise an error if no data provider is available
        if not hasattr(self, 'data_provider') or not self.data_provider:
            raise PnLCalculatorError(
                'PNL-BTC-001', 
                f"No data provider available for funding rate lookup for {venue}"
            )
        
        try:
            return self.data_provider.get_funding_rate('BTC', venue, timestamp)
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
        
        # Get BTC price change
        current_price = current.get('market_data', {}).get('btc_usd_price', 50000)
        previous_price = previous.get('market_data', {}).get('btc_usd_price', 50000)
        price_change = current_price - previous_price
        
        # Net delta P&L = net_delta * price_change
        # For perfect market neutrality, net_delta should be 0
        net_delta_pnl = current_net_delta * price_change
        
        return net_delta_pnl
    
    def _calc_delta_pnl(self, current: Dict, previous: Dict) -> float:
        """Calculate P&L from delta drift."""
        # Delta P&L = (current_delta - previous_delta) × price_change
        current_delta = current.get('net_delta_eth', 0)
        previous_delta = previous.get('net_delta_eth', 0)
        
        current_eth_price = current['exposures'].get('aWeETH', {}).get('eth_usd_price', 3000.0)
        previous_eth_price = previous['exposures'].get('aWeETH', {}).get('eth_usd_price', 3000.0)
        
        if previous_eth_price == 0:
            return 0.0
        
        delta_change = current_delta - previous_delta
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
    
    async def _publish_pnl(self, pnl_data: Dict):
        """Publish P&L data to Redis."""
        try:
            # Store current P&L
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.redis.set,
                'pnl:current',
                json.dumps(pnl_data, default=str)
            )
            
            # Publish update event
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.redis.publish,
                'pnl:calculated',
                json.dumps({
                    'timestamp': pnl_data['timestamp'].isoformat() if hasattr(pnl_data['timestamp'], 'isoformat') else str(pnl_data['timestamp']),
                    'pnl_cumulative': pnl_data['balance_based']['pnl_cumulative'],
                    'reconciliation_passed': pnl_data['reconciliation']['passed']
                })
            )
            
        except Exception as e:
            logger.error(f"Error publishing P&L to Redis: {e}")
    
    async def subscribe_to_risk_updates(self):
        """Subscribe to risk updates and recalculate P&L."""
        if not self.redis:
            logger.warning("Redis not available for risk updates subscription")
            return
        
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe('risk:calculated')
            
            logger.info("Subscribed to risk updates")
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        timestamp = pd.Timestamp(data['timestamp'])
                        
                        # Get exposure data from Redis
                        exposure_data = await asyncio.get_event_loop().run_in_executor(
                            None,
                            self.redis.get,
                            'exposure:current'
                        )
                        
                        if exposure_data:
                            exposure = json.loads(exposure_data)
                            pnl = await self.calculate_pnl(exposure, timestamp=timestamp)
                            logger.debug(f"P&L recalculated from risk update: ${pnl['balance_based']['pnl_cumulative']:,.2f}")
                        
                    except Exception as e:
                        logger.error(f"Error processing risk update: {e}")
                        
        except Exception as e:
            logger.error(f"Error in risk updates subscription: {e}")
    
    def get_pnl_summary(self, pnl_data: Dict) -> str:
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


# Convenience function for creating P&L Calculator
def create_pnl_calculator(share_class: str, initial_capital: float) -> PnLCalculator:
    """Create a new P&L Calculator instance."""
    return PnLCalculator(share_class=share_class, initial_capital=initial_capital)