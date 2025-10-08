#!/usr/bin/env python3
"""
Leveraged Restaking Strategy Analyzer - CORRECTED VERSION

Analyzes a leveraged restaking strategy using weETH:
1. At t=0: Execute leverage loop (stake ETH → weETH → supply → borrow → repeat) until <10 ETH remaining
2. Track single leveraged position through time with hourly P&L updates
3. Use time-varying rates from AAVE and staking data

Key Features:
- Leverage loop executed ONCE at t=0 (not spread over time)
- Dynamic rate lookup every hour (no caching)
- Proper position balance updates with growth factors
- Correct health factor formula with liquidation threshold
- Hourly staking yield accrual from oracle data

Data Sources:
- weETH rates: data/protocol_data/aave/rates/aave_v3_aave-v3-ethereum_weETH_rates_2024-05-12_2025-09-18_hourly.csv
- WETH rates: data/protocol_data/aave/rates/aave_v3_aave-v3-ethereum_WETH_rates_2024-01-01_2025-09-18_hourly.csv
- Staking yields: data/protocol_data/staking/base_yields/weeth_oracle_yields_2024-01-01_2025-09-18.csv
- Seasonal rewards: data/protocol_data/staking/restaking_final/etherfi_seasonal_rewards_2024-01-01_2025-09-18.csv
- Gas costs: data/blockchain_data/gas_prices/ethereum_gas_prices_enhanced_2024-01-01_2025-09-26.csv
- Oracle prices: data/protocol_data/aave/oracle/weETH_ETH_oracle_2024-01-01_2025-09-18.csv
- Risk parameters: data/protocol_data/aave/risk_params/aave_v3_risk_parameters.json
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass


@dataclass
class StrategyConfig:
    """Configuration for the leveraged restaking strategy."""
    initial_eth: float = 100.0
    min_position_eth: float = 10.0  # Stop leverage loop when remaining < 10 ETH
    max_ltv: float = 0.93  # AAVE maximum LTV cap
    liquidation_threshold: float = 0.95  # weETH liquidation threshold (eMode)
    gas_cost_multiplier: float = 1.2  # Safety margin for gas costs
    max_leverage_iterations: Optional[int] = None  # Cap on leverage loops (None = unlimited, 0 = no leverage)
    eigen_only: bool = False  # If True, only include EIGEN rewards (exclude ETHFI)
    fixed_balance_pnl: bool = False  # If True, calculate P&L on fixed initial balance (constant notional)


class LeveragedRestakingAnalyzer:
    """Analyzes leveraged restaking strategy performance."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.config = StrategyConfig()
        
        # Set up logging
        self.logger = logging.getLogger("leveraged_restaking_analyzer")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Load risk parameters
        self.risk_params = self._load_risk_parameters()
        
        # Data storage
        self.data = {}
        self.results = {}
        self.event_log = []  # Track all events
        
        self.logger.info("Leveraged Restaking Analyzer initialized (CORRECTED VERSION)")
    
    def _log_event(self, timestamp: pd.Timestamp, event_type: str, venue: str, 
                   token: str = None, amount: float = None, **event_data) -> None:
        """Log an event with full details for audit trail."""
        event = {
            'timestamp': timestamp,
            'event_type': event_type,
            'venue': venue,
            'token': token,
            'amount': amount,
            **event_data
        }
        self.event_log.append(event)
    
    def _load_risk_parameters(self) -> Dict:
        """Load AAVE risk parameters."""
        risk_file = self.data_dir / "protocol_data" / "aave" / "risk_params" / "aave_v3_risk_parameters.json"
        
        with open(risk_file, 'r') as f:
            params = json.load(f)
        
        # Extract weETH parameters (eMode for weETH-WETH pair)
        emode_params = params['emode']
        weeth_params = {
            'liquidation_threshold': emode_params['liquidation_thresholds']['weETH_WETH'],
            'max_ltv': emode_params['max_ltv_limits']['weETH_WETH'],
            'liquidation_bonus': emode_params['liquidation_bonus']['weETH_WETH']
        }
        
        self.logger.info(f"Loaded weETH risk parameters: {weeth_params}")
        return weeth_params
    
    def _load_data(self) -> None:
        """Load all required data files."""
        self.logger.info("Loading data files...")
        
        # Load weETH rates
        weeth_rates_file = self.data_dir / "protocol_data" / "aave" / "rates" / "aave_v3_aave-v3-ethereum_weETH_rates_2024-05-12_2025-09-18_hourly.csv"
        self.data['weeth_rates'] = pd.read_csv(weeth_rates_file)
        self.data['weeth_rates']['timestamp'] = pd.to_datetime(self.data['weeth_rates']['timestamp'])
        self.data['weeth_rates'] = self.data['weeth_rates'].set_index('timestamp').sort_index()
        
        # Load WETH rates
        weth_rates_file = self.data_dir / "protocol_data" / "aave" / "rates" / "aave_v3_aave-v3-ethereum_WETH_rates_2024-01-01_2025-09-18_hourly.csv"
        self.data['weth_rates'] = pd.read_csv(weth_rates_file)
        self.data['weth_rates']['timestamp'] = pd.to_datetime(self.data['weth_rates']['timestamp'])
        self.data['weth_rates'] = self.data['weth_rates'].set_index('timestamp').sort_index()
        
        # Load staking yields (daily data at 00:00 UTC)
        staking_file = self.data_dir / "protocol_data" / "staking" / "base_yields" / "weeth_oracle_yields_2024-01-01_2025-09-18.csv"
        self.data['staking_yields'] = pd.read_csv(staking_file)
        self.data['staking_yields']['timestamp'] = pd.to_datetime(self.data['staking_yields']['timestamp'].str.replace('Z', ''))
        self.data['staking_yields']['date'] = pd.to_datetime(self.data['staking_yields']['date'])
        
        # Load seasonal rewards
        seasonal_file = self.data_dir / "protocol_data" / "staking" / "restaking_final" / "etherfi_seasonal_rewards_2024-01-01_2025-09-18.csv"
        self.data['seasonal_rewards'] = pd.read_csv(seasonal_file)
        self.data['seasonal_rewards']['payout_date'] = pd.to_datetime(self.data['seasonal_rewards']['payout_date'])
        self.data['seasonal_rewards']['period_start'] = pd.to_datetime(self.data['seasonal_rewards']['period_start'])
        self.data['seasonal_rewards']['period_end'] = pd.to_datetime(self.data['seasonal_rewards']['period_end'])
        
        # Load gas costs
        gas_file = self.data_dir / "blockchain_data" / "gas_prices" / "ethereum_gas_prices_enhanced_2024-01-01_2025-09-26.csv"
        self.data['gas_costs'] = pd.read_csv(gas_file)
        self.data['gas_costs']['timestamp'] = pd.to_datetime(self.data['gas_costs']['timestamp'])
        self.data['gas_costs'] = self.data['gas_costs'].set_index('timestamp').sort_index()
        
        # Load oracle prices
        oracle_file = self.data_dir / "protocol_data" / "aave" / "oracle" / "weETH_ETH_oracle_2024-01-01_2025-09-18.csv"
        self.data['oracle_prices'] = pd.read_csv(oracle_file, comment='#')
        self.data['oracle_prices']['timestamp'] = pd.to_datetime(self.data['oracle_prices']['timestamp'])
        self.data['oracle_prices'] = self.data['oracle_prices'].set_index('timestamp').sort_index()
        
        # Load Ethena benchmark (optional - for comparison)
        ethena_file = self.data_dir / "protocol_data" / "staking" / "benchmark_yields" / "ethena_susde_apr_benchmark_hourly_2024-02-16_2025-09-18.csv"
        if ethena_file.exists():
            self.data['ethena_benchmark'] = pd.read_csv(ethena_file)
            self.data['ethena_benchmark']['timestamp'] = pd.to_datetime(self.data['ethena_benchmark']['timestamp']).dt.tz_localize('UTC')
            self.data['ethena_benchmark'] = self.data['ethena_benchmark'].set_index('timestamp').sort_index()
            self.logger.info(f"  Ethena benchmark: {len(self.data['ethena_benchmark'])} records")
        else:
            self.data['ethena_benchmark'] = None
            self.logger.info("  Ethena benchmark: Not available (skipping comparison)")
        
        self.logger.info("Data loading completed")
        self.logger.info(f"  weETH rates: {len(self.data['weeth_rates'])} records")
        self.logger.info(f"  WETH rates: {len(self.data['weth_rates'])} records")
        self.logger.info(f"  Staking yields: {len(self.data['staking_yields'])} records")
        self.logger.info(f"  Seasonal rewards: {len(self.data['seasonal_rewards'])} periods")
    
    def _get_gas_cost(self, timestamp: pd.Timestamp, transaction_type: str) -> float:
        """Get gas cost in ETH for a specific transaction type at a given timestamp."""
        # Find closest timestamp in gas data
        gas_data = self.data['gas_costs']
        
        # Use asof for efficient lookup of closest past timestamp
        closest_ts = gas_data.index.asof(timestamp)
        
        if pd.isna(closest_ts):
            # Fallback to first available
            closest_ts = gas_data.index[0]
        
        gas_cost_eth = gas_data.loc[closest_ts, f'{transaction_type}_eth']
        
        # Apply safety multiplier
        return gas_cost_eth * self.config.gas_cost_multiplier
    
    def _get_rates_at_timestamp(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get all relevant rates at a specific timestamp (FRESH LOOKUP - NO CACHING)."""
        rates = {}
        
        # weETH supply rate growth factor (hourly)
        weeth_data = self.data['weeth_rates']
        weeth_ts = weeth_data.index.asof(timestamp)
        if pd.isna(weeth_ts):
            weeth_ts = weeth_data.index[0]
        
        rates['weeth_supply_growth_factor'] = weeth_data.loc[weeth_ts, 'liquidity_growth_factor']
        rates['weeth_supply_apy'] = weeth_data.loc[weeth_ts, 'liquidity_apy_hourly']
        
        # WETH borrow rate growth factor (hourly)
        weth_data = self.data['weth_rates']
        weth_ts = weth_data.index.asof(timestamp)
        if pd.isna(weth_ts):
            weth_ts = weth_data.index[0]
        
        rates['weth_borrow_growth_factor'] = weth_data.loc[weth_ts, 'borrow_growth_factor']
        rates['weth_borrow_apy'] = weth_data.loc[weth_ts, 'borrow_apy_hourly']
        
        # weETH oracle price
        oracle_data = self.data['oracle_prices']
        oracle_ts = oracle_data.index.asof(timestamp)
        if pd.isna(oracle_ts):
            oracle_ts = oracle_data.index[0]
        
        rates['weeth_price'] = oracle_data.loc[oracle_ts, 'oracle_price_eth']
        
        return rates
    
    def _get_ethena_apr_at_timestamp(self, timestamp: pd.Timestamp) -> float:
        """Get Ethena benchmark APR at a specific timestamp."""
        if self.data['ethena_benchmark'] is None:
            return 0.0
        
        ethena_data = self.data['ethena_benchmark']
        ethena_ts = ethena_data.index.asof(timestamp)
        
        if pd.isna(ethena_ts):
            return 0.0
        
        # Return APR as decimal (e.g., 0.1178 for 11.78%)
        return ethena_data.loc[ethena_ts, 'apr_decimal']
    
    def _get_staking_yield_at_timestamp(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get staking yield (base + seasonal) at a specific timestamp using actual CSV data."""
        
        # Get base staking yield from oracle data (daily at 00:00 UTC)
        # Find the most recent daily record
        timestamp_date = timestamp.date()
        staking_data = self.data['staking_yields']
        
        # Find matching date or most recent past date
        matching_dates = staking_data[staking_data['date'] <= pd.Timestamp(timestamp_date)]
        if len(matching_dates) == 0:
            # Use first available date
            daily_yield = staking_data.iloc[0]['daily_yield']
            base_yield_annual = staking_data.iloc[0]['base_staking_apr']
        else:
            # Use most recent
            latest_record = matching_dates.iloc[-1]
            daily_yield = latest_record['daily_yield']
            base_yield_annual = latest_record['base_staking_apr']
        
        # Convert daily yield to hourly for continuous accrual
        # hourly_yield = (1 + daily_yield)^(1/24) - 1
        base_yield_hourly = (1 + daily_yield) ** (1 / 24) - 1
        
        # Seasonal rewards (daily, so we need to find the period this timestamp falls into)
        seasonal_data = self.data['seasonal_rewards']
        
        # Filter by reward type if eigen_only mode is enabled
        if self.config.eigen_only:
            # Only include EIGEN rewards (exclude ETHFI)
            seasonal_data = seasonal_data[seasonal_data['reward_type'].str.contains('EIGEN', case=False, na=False)]
        
        # Find the period this timestamp falls into
        seasonal_yield_daily = 0.0
        for _, row in seasonal_data.iterrows():
            # Ensure timezone-aware comparison
            period_start = row['period_start']
            period_end = row['period_end']
            
            # Convert to timezone-aware if needed
            if period_start.tzinfo is None:
                period_start = period_start.tz_localize('UTC')
            if period_end.tzinfo is None:
                period_end = period_end.tz_localize('UTC')
            
            if period_start <= timestamp <= period_end:
                seasonal_yield_daily = row['daily_yield_final']
                break
        
        # Convert daily seasonal yield to hourly: (1 + daily)^(1/24) - 1
        seasonal_yield_hourly = (1 + seasonal_yield_daily) ** (1 / 24) - 1 if seasonal_yield_daily > 0 else 0.0
        
        # Total staking yield (base + seasonal)
        total_staking_yield_hourly = base_yield_hourly + seasonal_yield_hourly
        
        return {
            'base_yield_hourly': base_yield_hourly,
            'seasonal_yield_hourly': seasonal_yield_hourly,
            'total_staking_yield_hourly': total_staking_yield_hourly,
            'base_yield_annual': base_yield_annual,
            'seasonal_yield_daily': seasonal_yield_daily
        }
    
    def _execute_leverage_loop_at_t0(self, timestamp: pd.Timestamp) -> Dict:
        """
        Execute the complete leverage loop at t=0.
        
        Start with initial_eth, then loop:
        1. Stake ETH → weETH
        2. Supply weETH to AAVE
        3. Borrow WETH at max LTV
        4. Repeat until remaining ETH < min_position_eth
        
        Returns initial position state and total gas costs.
        """
        self.logger.info(f"🔄 Executing leverage loop at t=0 (timestamp: {timestamp})...")
        
        # Get rates at t=0
        rates = self._get_rates_at_timestamp(timestamp)
        weeth_price = rates['weeth_price']
        
        # Initialize
        available_eth = self.config.initial_eth
        total_weeth_collateral = 0.0
        total_weth_debt = 0.0
        total_gas_costs = 0.0
        iteration_count = 0
        
        # Track positions at each venue
        venue_positions = {
            'etherfi': {'eth_staked': 0.0, 'weeth_received': 0.0},
            'aave': {'weeth_collateral': 0.0, 'weth_debt': 0.0}
        }
        
        # Special case: if max_leverage_iterations=0, stake once and don't loop
        if self.config.max_leverage_iterations == 0:
            max_iterations = 1
        else:
            max_iterations = self.config.max_leverage_iterations
        
        while available_eth >= self.config.min_position_eth:
            iteration_count += 1
            
            # Check if we've hit max leverage iterations
            if max_iterations is not None and iteration_count > max_iterations:
                self.logger.info(f"  Stopped: Max leverage iterations ({max_iterations}) reached")
                break
            
            # Check if this will be the last iteration (next loop would be < min)
            is_last_iteration = False
            if self.config.max_leverage_iterations != 0:
                # Calculate what the next borrow would be
                rates = self._get_rates_at_timestamp(timestamp)
                weeth_price_check = rates['weeth_price']
                potential_weeth = (available_eth - self._get_gas_cost(timestamp, 'CREATE_LST')) / weeth_price_check
                potential_borrow = potential_weeth * weeth_price_check * self.config.max_ltv
                
                # If next iteration would be below minimum, this is the last iteration
                if potential_borrow < self.config.min_position_eth:
                    is_last_iteration = True
                    self.logger.info(f"  Iteration {iteration_count}: FINAL iteration (next would be < {self.config.min_position_eth} ETH)")
            
            # Step 1: Stake ETH → weETH (pay gas)
            stake_gas = self._get_gas_cost(timestamp, 'CREATE_LST')
            self._log_event(timestamp, 'GAS_FEE_PAID', 'ETHEREUM', 'ETH', stake_gas,
                          fee_type='create_lst', related_transaction=f'stake_iteration_{iteration_count}')
            
            eth_after_gas = available_eth - stake_gas
            
            if eth_after_gas <= 0:
                break
            
            # Convert ETH to weETH using oracle price
            weeth_received = eth_after_gas / weeth_price
            
            # Log staking event
            self._log_event(timestamp, 'STAKE_DEPOSIT', 'ETHERFI', 'ETH', eth_after_gas,
                          input_token='ETH', output_token='weETH', amount_out=weeth_received,
                          oracle_price=weeth_price, iteration=iteration_count)
            
            # Update venue positions
            venue_positions['etherfi']['eth_staked'] += eth_after_gas
            venue_positions['etherfi']['weeth_received'] += weeth_received
            
            # Step 2: Supply weETH to AAVE (pay gas)
            supply_gas = self._get_gas_cost(timestamp, 'COLLATERAL_SUPPLIED')
            self._log_event(timestamp, 'GAS_FEE_PAID', 'ETHEREUM', 'ETH', supply_gas,
                          fee_type='collateral_supplied', related_transaction=f'supply_iteration_{iteration_count}')
            
            total_weeth_collateral += weeth_received
            
            # Log collateral supply event
            self._log_event(timestamp, 'COLLATERAL_SUPPLIED', 'AAVE', 'weETH', weeth_received,
                          collateral_type='supply_for_borrowing', enables_borrowing=True,
                          iteration=iteration_count)
            
            # Update venue positions
            venue_positions['aave']['weeth_collateral'] += weeth_received
            
            # Step 3: Borrow WETH at max LTV (pay gas) - ONLY if not last iteration and not max_leverage_iterations=0
            if self.config.max_leverage_iterations != 0 and not is_last_iteration:
                borrow_gas = self._get_gas_cost(timestamp, 'LOAN_CREATED')
                self._log_event(timestamp, 'GAS_FEE_PAID', 'ETHEREUM', 'ETH', borrow_gas,
                              fee_type='loan_created', related_transaction=f'borrow_iteration_{iteration_count}')
                
                max_borrow = weeth_received * weeth_price * self.config.max_ltv
                total_weth_debt += max_borrow
                
                # Log borrow event
                self._log_event(timestamp, 'LOAN_CREATED', 'AAVE', 'WETH', max_borrow,
                              debt_type='variable_rate', ltv=self.config.max_ltv,
                              collateral_token='weETH', collateral_amount=weeth_received,
                              iteration=iteration_count)
                
                # Update venue positions
                venue_positions['aave']['weth_debt'] += max_borrow
                
                total_gas_costs += borrow_gas
            else:
                # No borrowing in zero-leverage mode OR on last iteration
                max_borrow = 0.0
                if is_last_iteration:
                    self.logger.info(f"  Final iteration: Staked and supplied but DID NOT borrow (keeps position balanced)")
            
            # Track gas costs (stake + supply, optionally + borrow)
            total_gas_costs += (stake_gas + supply_gas)
            
            # Update available ETH for next iteration
            available_eth = max_borrow
            
            if iteration_count % 10 == 0:
                self.logger.info(f"  Iteration {iteration_count}: {total_weeth_collateral:.2f} weETH collateral, {total_weth_debt:.2f} WETH debt")
        
        # Calculate final metrics
        collateral_value_eth = total_weeth_collateral * weeth_price
        net_position_eth = collateral_value_eth - total_weth_debt
        
        # Correct health factor formula: HF = (LT * collateral) / debt
        health_factor = (self.config.liquidation_threshold * collateral_value_eth) / total_weth_debt if total_weth_debt > 0 else float('inf')
        
        # Calculate leverage multiplier
        leverage_multiplier = collateral_value_eth / self.config.initial_eth
        
        self.logger.info(f"✅ Leverage loop completed:")
        self.logger.info(f"   Iterations: {iteration_count}")
        self.logger.info(f"   Initial ETH: {self.config.initial_eth:.2f}")
        self.logger.info(f"   weETH Collateral: {total_weeth_collateral:.4f} ({collateral_value_eth:.2f} ETH)")
        self.logger.info(f"   WETH Debt: {total_weth_debt:.2f}")
        self.logger.info(f"   Net Position: {net_position_eth:.2f} ETH")
        self.logger.info(f"   Leverage: {leverage_multiplier:.2f}x")
        self.logger.info(f"   Health Factor: {health_factor:.3f}")
        self.logger.info(f"   Total Gas Costs: {total_gas_costs:.6f} ETH")
        
        return {
            'timestamp': timestamp,
            'iteration_count': iteration_count,
            'weeth_collateral': total_weeth_collateral,
            'weth_debt': total_weth_debt,
            'collateral_value_eth': collateral_value_eth,
            'debt_value_eth': total_weth_debt,
            'net_position_eth': net_position_eth,
            'health_factor': health_factor,
            'leverage_multiplier': leverage_multiplier,
            'total_gas_costs': total_gas_costs,
            'weeth_price': weeth_price,
            'venue_positions': venue_positions
        }
    
    def _update_position_balances(self, position: Dict, timestamp: pd.Timestamp, 
                                   fixed_balance_ref: Optional[Dict] = None) -> Tuple[Dict, Dict]:
        """
        Update position balances based on hourly growth factors.
        
        This updates the actual collateral and debt balances with:
        - AAVE supply growth factor
        - Staking yield accrual
        - AAVE borrow growth factor
        
        Args:
            position: Current position state
            timestamp: Current timestamp
            fixed_balance_ref: If provided, calculate P&L on this fixed balance (constant notional mode)
        
        Returns: (updated_position, pnl_dict)
        """
        # Get current rates (FRESH LOOKUP)
        rates = self._get_rates_at_timestamp(timestamp)
        staking_yields = self._get_staking_yield_at_timestamp(timestamp)
        
        # Store OLD balances for P&L calculation
        old_collateral_value = position['collateral_value_eth']
        old_debt_value = position['debt_value_eth']
        old_net_position = position['net_position_eth']
        old_weeth_units = position['weeth_collateral']
        old_weeth_price = position['weeth_price']
        
        # Determine which balance to use for P&L calculation
        if self.config.fixed_balance_pnl and fixed_balance_ref is not None:
            # Use FIXED initial balance for P&L (constant notional)
            pnl_collateral_value = fixed_balance_ref['collateral_value_eth']
            pnl_debt_value = fixed_balance_ref['debt_value_eth']
            pnl_weeth_units = fixed_balance_ref['weeth_collateral']
        else:
            # Use actual OLD balance for P&L (compounding)
            pnl_collateral_value = old_collateral_value
            pnl_debt_value = old_debt_value
            pnl_weeth_units = old_weeth_units
        
        # Calculate P&L BEFORE updating balances (using chosen balance)
        # 1. AAVE supply yield (on weETH collateral)
        supply_pnl_eth = pnl_collateral_value * (rates['weeth_supply_growth_factor'] - 1)
        
        # 2. Seasonal rewards ONLY (EIGEN + ETHFI - base staking is in oracle price!)
        seasonal_pnl_eth = pnl_collateral_value * staking_yields['seasonal_yield_hourly']
        
        # 3. Borrow cost
        borrow_cost_eth = pnl_debt_value * (rates['weth_borrow_growth_factor'] - 1)
        
        # 4. Oracle price appreciation (weETH/ETH) - INCLUDES base staking implicitly!
        # After AAVE supply growth and seasonal rewards, calculate price impact
        new_weeth_units_from_yields = pnl_weeth_units * rates['weeth_supply_growth_factor'] * (1 + staking_yields['seasonal_yield_hourly'])
        price_change_pnl_eth = new_weeth_units_from_yields * (rates['weeth_price'] - old_weeth_price)
        
        # Total P&L: supply + seasonal + price appreciation - borrow
        # NOTE: Base staking yield is NOT added separately (it's in price appreciation!)
        net_pnl_eth = supply_pnl_eth + seasonal_pnl_eth + price_change_pnl_eth - borrow_cost_eth
        
        # Now update balances
        # Update collateral with AAVE supply growth
        position['weeth_collateral'] *= rates['weeth_supply_growth_factor']
        
        # Update collateral with SEASONAL rewards only (base staking is in oracle price!)
        position['weeth_collateral'] *= (1 + staking_yields['seasonal_yield_hourly'])
        
        # Update debt with borrow growth
        position['weth_debt'] *= rates['weth_borrow_growth_factor']
        
        # Update derived values
        position['collateral_value_eth'] = position['weeth_collateral'] * rates['weeth_price']
        position['debt_value_eth'] = position['weth_debt']
        position['net_position_eth'] = position['collateral_value_eth'] - position['debt_value_eth']
        
        # Verify P&L matches change in net position
        actual_change = position['net_position_eth'] - old_net_position
        
        # Correct health factor: HF = (LT * collateral) / debt
        position['health_factor'] = (self.config.liquidation_threshold * position['collateral_value_eth']) / position['debt_value_eth'] if position['debt_value_eth'] > 0 else float('inf')
        
        position['weeth_price'] = rates['weeth_price']
        position['timestamp'] = timestamp
        
        # Store rates used for this update
        position['rates'] = {
            'weeth_supply_growth_factor': rates['weeth_supply_growth_factor'],
            'weth_borrow_growth_factor': rates['weth_borrow_growth_factor'],
            'weeth_supply_apy': rates['weeth_supply_apy'],
            'weth_borrow_apy': rates['weth_borrow_apy'],
            'staking_yields': staking_yields
        }
        
        # Create P&L dictionary
        pnl_dict = {
            'supply_pnl_eth': supply_pnl_eth,
            'seasonal_pnl_eth': seasonal_pnl_eth,  # Only seasonal rewards (not base staking!)
            'borrow_cost_eth': borrow_cost_eth,
            'price_change_pnl_eth': price_change_pnl_eth,  # Includes base staking implicitly
            'net_pnl_eth': net_pnl_eth,
            'actual_position_change_eth': actual_change,
            'pnl_verification_error_eth': actual_change - net_pnl_eth  # Should be ~0
        }
        
        return position, pnl_dict
    
    def _create_pnl_record(self, pnl_dict: Dict, position: Dict, timestamp: pd.Timestamp, 
                           cumulative_supply_pnl: float, cumulative_seasonal_pnl: float, 
                           cumulative_borrow_cost: float, cumulative_price_change_pnl: float,
                           cumulative_net_pnl: float, ethena_apr: float, 
                           cumulative_ethena_pnl: float, initial_net_position: float) -> Dict:
        """
        Create a complete P&L record with both ETH amounts and annualized bps.
        
        NOTE: Base staking yield is NOT tracked separately - it's embedded in weETH price appreciation!
        """
        rates = position['rates']
        staking_yields = rates['staking_yields']
        
        # Convert to annualized bps for display
        supply_yield_bps = (rates['weeth_supply_growth_factor'] - 1) * 10000 * 365 * 24
        seasonal_yield_bps = staking_yields['seasonal_yield_hourly'] * 10000 * 365 * 24
        borrow_cost_bps = (rates['weth_borrow_growth_factor'] - 1) * 10000 * 365 * 24
        
        # Calculate net yield bps based on actual net position
        net_yield_bps = (pnl_dict['net_pnl_eth'] / position['net_position_eth']) * 10000 * 365 * 24 if position['net_position_eth'] > 0 else 0
        
        # For reference: base staking is in oracle price, so we track it separately for display only
        base_staking_yield_bps = staking_yields['base_yield_hourly'] * 10000 * 365 * 24
        
        # Calculate Ethena benchmark hourly P&L (on same initial notional)
        ethena_hourly_pnl = initial_net_position * (ethena_apr / (365 * 24))
        
        return {
            'timestamp': timestamp,
            # P&L in ETH (hourly incremental)
            'supply_pnl_eth': pnl_dict['supply_pnl_eth'],
            'seasonal_pnl_eth': pnl_dict['seasonal_pnl_eth'],  # EIGEN + ETHFI only
            'borrow_cost_eth': pnl_dict['borrow_cost_eth'],
            'price_change_pnl_eth': pnl_dict['price_change_pnl_eth'],  # Includes base staking!
            'net_pnl_eth': pnl_dict['net_pnl_eth'],
            # Cumulative P&L in ETH (running totals)
            'cumulative_supply_pnl_eth': cumulative_supply_pnl,
            'cumulative_seasonal_pnl_eth': cumulative_seasonal_pnl,
            'cumulative_borrow_cost_eth': cumulative_borrow_cost,
            'cumulative_price_change_pnl_eth': cumulative_price_change_pnl,
            'cumulative_net_pnl_eth': cumulative_net_pnl,
            # Ethena benchmark (for comparison)
            'ethena_apr_percent': ethena_apr * 100,
            'ethena_hourly_pnl_eth': ethena_hourly_pnl,
            'cumulative_ethena_pnl_eth': cumulative_ethena_pnl,
            # Annualized yields in bps
            'supply_yield_bps': supply_yield_bps,
            'seasonal_yield_bps': seasonal_yield_bps,
            'borrow_cost_bps': borrow_cost_bps,
            'net_yield_bps': net_yield_bps,
            'base_staking_yield_bps': base_staking_yield_bps,  # For reference only
            # Position values
            'collateral_value_eth': position['collateral_value_eth'],
            'debt_value_eth': position['debt_value_eth'],
            'net_position_eth': position['net_position_eth'],
            'health_factor': position['health_factor'],
            'weeth_price': position['weeth_price'],
            # Verification
            'actual_position_change_eth': pnl_dict['actual_position_change_eth'],
            'pnl_verification_error_eth': pnl_dict['pnl_verification_error_eth']
        }
    
    def run_analysis(self, start_date: str = "2024-05-12", end_date: str = "2025-09-18") -> Dict:
        """Run the complete leveraged restaking analysis."""
        self.logger.info("=" * 80)
        self.logger.info("🚀 LEVERAGED RESTAKING ANALYSIS (CORRECTED VERSION)")
        self.logger.info("=" * 80)
        self.logger.info(f"📅 Date range: {start_date} to {end_date}")
        self.logger.info(f"💰 Initial ETH: {self.config.initial_eth}")
        self.logger.info(f"🎯 Max LTV: {self.config.max_ltv}")
        self.logger.info(f"⚠️  Liquidation Threshold: {self.config.liquidation_threshold}")
        self.logger.info("=" * 80)
        
        # Load data
        self._load_data()
        
        # Create timestamp range (hourly) - timezone-aware to match data
        start_ts = pd.to_datetime(start_date).tz_localize('UTC')
        end_ts = pd.to_datetime(end_date).tz_localize('UTC')
        timestamps = pd.date_range(start=start_ts, end=end_ts, freq='H')
        
        self.logger.info(f"📊 Total time periods: {len(timestamps)} hours")
        self.logger.info("")
        
        # STEP 1: Execute leverage loop at t=0
        self.logger.info("STEP 1: Execute leverage loop at t=0")
        self.logger.info("-" * 50)
        position = self._execute_leverage_loop_at_t0(timestamps[0])
        
        # Store initial position for reference
        initial_position = position.copy()
        initial_net_position = initial_position['net_position_eth']
        
        self.logger.info("")
        self.logger.info("STEP 2: Track position through time with hourly P&L")
        self.logger.info("-" * 50)
        
        # STEP 2: Track position through time
        hourly_pnl = []
        
        # Track cumulative P&L components
        cumulative_supply_pnl = 0.0
        cumulative_seasonal_pnl = 0.0  # Only seasonal (base is in price!)
        cumulative_borrow_cost = 0.0
        cumulative_price_change_pnl = 0.0
        cumulative_net_pnl = 0.0
        cumulative_ethena_pnl = 0.0
        
        # For fixed balance mode, use initial position as reference
        fixed_balance_ref = initial_position.copy() if self.config.fixed_balance_pnl else None
        
        if self.config.fixed_balance_pnl:
            self.logger.info(f"📊 Fixed Balance P&L Mode: Calculating returns on constant {initial_position['net_position_eth']:.2f} ETH notional")
        
        for i, timestamp in enumerate(timestamps[1:], start=1):  # Skip t=0 (already done)
            if i % 1000 == 0:
                self.logger.info(f"Processing hour {i}/{len(timestamps)}: {timestamp}")
            
            # Update position balances and get P&L
            # In fixed mode: P&L on fixed balance, but position still grows
            position, pnl_dict = self._update_position_balances(position, timestamp, fixed_balance_ref)
            
            # Get Ethena benchmark APR for this hour
            ethena_apr = self._get_ethena_apr_at_timestamp(timestamp)
            
            # Calculate Ethena hourly P&L (on initial notional for fair comparison)
            ethena_hourly_pnl = initial_net_position * (ethena_apr / (365 * 24))
            
            # Update cumulative P&L components
            cumulative_supply_pnl += pnl_dict['supply_pnl_eth']
            cumulative_seasonal_pnl += pnl_dict['seasonal_pnl_eth']
            cumulative_borrow_cost += pnl_dict['borrow_cost_eth']
            cumulative_price_change_pnl += pnl_dict['price_change_pnl_eth']
            cumulative_net_pnl += pnl_dict['net_pnl_eth']
            cumulative_ethena_pnl += ethena_hourly_pnl
            
            # Create complete P&L record
            pnl_record = self._create_pnl_record(
                pnl_dict, position, timestamp,
                cumulative_supply_pnl, cumulative_seasonal_pnl,
                cumulative_borrow_cost, cumulative_price_change_pnl, cumulative_net_pnl,
                ethena_apr, cumulative_ethena_pnl, initial_net_position
            )
            
            hourly_pnl.append(pnl_record)
        
        # Calculate final metrics
        final_position_value_eth = position['net_position_eth']
        
        # Net profit = final position - initial position (after gas)
        actual_net_profit_eth = final_position_value_eth - initial_net_position
        
        # This should match cumulative_net_pnl
        total_return_pct = (actual_net_profit_eth / self.config.initial_eth) * 100
        
        # Calculate annualized return based on actual time period
        time_delta = end_ts - start_ts
        years_analyzed = time_delta.total_seconds() / (365.25 * 24 * 3600)
        days_analyzed = time_delta.total_seconds() / (24 * 3600)
        
        if years_analyzed > 0:
            annualized_return_pct = ((final_position_value_eth / self.config.initial_eth) ** (1 / years_analyzed) - 1) * 100
        else:
            annualized_return_pct = 0
        
        # Calculate additional performance metrics
        pnl_df = pd.DataFrame(hourly_pnl)
        
        # 1. Calculate daily returns for Sharpe ratio and uncompounded return
        pnl_df['date'] = pd.to_datetime(pnl_df['timestamp']).dt.date
        daily_pnl = pnl_df.groupby('date').agg({
            'net_pnl_eth': 'sum',
            'net_position_eth': 'last'
        }).reset_index()
        
        # Daily return = daily P&L / starting position for that day
        daily_pnl['daily_return'] = daily_pnl['net_pnl_eth'] / daily_pnl['net_position_eth'].shift(1)
        daily_pnl = daily_pnl.dropna()
        
        # Uncompounded daily return annualized (simple average)
        avg_daily_return = daily_pnl['daily_return'].mean()
        uncompounded_annual_return_pct = avg_daily_return * 365 * 100
        
        # Sharpe ratio (annualized return / annualized daily volatility)
        daily_return_std = daily_pnl['daily_return'].std()
        annualized_volatility = daily_return_std * np.sqrt(365)
        sharpe_ratio = (annualized_return_pct / 100) / annualized_volatility if annualized_volatility > 0 else 0
        
        # 2. Max drawdown - calculate on cumulative_net_pnl_eth column
        pnl_df['cumulative_value_eth'] = initial_net_position + pnl_df['cumulative_net_pnl_eth']
        pnl_df['peak_value_eth'] = pnl_df['cumulative_value_eth'].cummax()
        pnl_df['drawdown_eth'] = pnl_df['cumulative_value_eth'] - pnl_df['peak_value_eth']
        pnl_df['drawdown_pct'] = (pnl_df['drawdown_eth'] / pnl_df['peak_value_eth']) * 100
        max_drawdown_pct = pnl_df['drawdown_pct'].min()
        
        # Update hourly_pnl records with calculated drawdown
        for i in range(len(hourly_pnl)):
            hourly_pnl[i]['drawdown_pct'] = pnl_df.iloc[i]['drawdown_pct']
            hourly_pnl[i]['cumulative_value_eth'] = pnl_df.iloc[i]['cumulative_value_eth']
            hourly_pnl[i]['peak_value_eth'] = pnl_df.iloc[i]['peak_value_eth']
        
        # 3. P&L over notional (total ETH traded)
        # Total notional = sum of all position creation amounts (from leverage loop)
        # For recursive leverage: total_traded = initial_eth * (1 + ltv + ltv^2 + ... + ltv^n)
        # = initial_eth * (1 - ltv^(n+1)) / (1 - ltv)
        leverage_iterations = initial_position['iteration_count']
        ltv = self.config.max_ltv
        total_notional_traded = self.config.initial_eth * sum([ltv**i for i in range(leverage_iterations)])
        pnl_over_notional_bps = (cumulative_net_pnl / total_notional_traded) * 10000 if total_notional_traded > 0 else 0
        
        # Compile results
        self.results = {
            'config': {
                'initial_eth': self.config.initial_eth,
                'min_position_eth': self.config.min_position_eth,
                'max_ltv': self.config.max_ltv,
                'liquidation_threshold': self.config.liquidation_threshold,
                'max_leverage_iterations': self.config.max_leverage_iterations,
                'eigen_only': self.config.eigen_only,
                'fixed_balance_pnl': self.config.fixed_balance_pnl
            },
            'initial_position': {
                'iteration_count': initial_position['iteration_count'],
                'weeth_collateral': initial_position['weeth_collateral'],
                'weth_debt': initial_position['weth_debt'],
                'leverage_multiplier': initial_position['leverage_multiplier'],
                'health_factor': initial_position['health_factor'],
                'total_gas_costs': initial_position['total_gas_costs'],
                'venue_positions': initial_position['venue_positions']
            },
            'final_position': {
                'weeth_collateral': position['weeth_collateral'],
                'weth_debt': position['weth_debt'],
                'collateral_value_eth': position['collateral_value_eth'],
                'debt_value_eth': position['debt_value_eth'],
                'net_position_eth': position['net_position_eth'],
                'health_factor': position['health_factor']
            },
            'summary': {
                'total_hours': len(hourly_pnl),
                'days_analyzed': days_analyzed,
                'initial_eth': self.config.initial_eth,
                'initial_net_position_eth': initial_net_position,
                'final_position_value_eth': final_position_value_eth,
                'actual_net_profit_eth': actual_net_profit_eth,
                'cumulative_supply_pnl_eth': cumulative_supply_pnl,
                'cumulative_seasonal_pnl_eth': cumulative_seasonal_pnl,
                'cumulative_borrow_cost_eth': cumulative_borrow_cost,
                'cumulative_price_change_pnl_eth': cumulative_price_change_pnl,
                'cumulative_net_pnl_eth': cumulative_net_pnl,
                'note': 'price_change_pnl includes base staking yield implicitly via oracle price',
                'pnl_verification_match': abs(actual_net_profit_eth - cumulative_net_pnl) < 0.01,
                'total_gas_costs_eth': initial_position['total_gas_costs'],
                'total_return_pct': total_return_pct,
                'annualized_return_pct': annualized_return_pct,
                'uncompounded_annual_return_pct': uncompounded_annual_return_pct,
                'sharpe_ratio': sharpe_ratio,
                'annualized_volatility': annualized_volatility * 100,
                'max_drawdown_pct': max_drawdown_pct,
                'total_notional_traded_eth': total_notional_traded,
                'pnl_over_notional_bps': pnl_over_notional_bps,
                'years_analyzed': years_analyzed,
                'ethena_benchmark': {
                    'cumulative_pnl_eth': cumulative_ethena_pnl,
                    'available': self.data['ethena_benchmark'] is not None,
                    'outperformance_eth': cumulative_net_pnl - cumulative_ethena_pnl if self.data['ethena_benchmark'] is not None else None
                }
            },
            'hourly_pnl': hourly_pnl,
            'event_log': self.event_log
        }
        
        self.logger.info("=" * 80)
        self.logger.info("📊 ANALYSIS RESULTS (CORRECTED P&L):")
        self.logger.info("=" * 80)
        self.logger.info(f"⏱️  Total hours analyzed: {len(hourly_pnl):,}")
        self.logger.info(f"💰 Initial ETH: {self.config.initial_eth:.2f}")
        self.logger.info(f"💰 Initial Net Position (after gas): {initial_net_position:.2f} ETH")
        self.logger.info(f"💰 Final Position Value: {final_position_value_eth:.2f} ETH")
        self.logger.info(f"📈 Actual Net Profit: {actual_net_profit_eth:.2f} ETH")
        self.logger.info("")
        self.logger.info("📊 P&L COMPONENT BREAKDOWN:")
        self.logger.info(f"   ✅ AAVE Supply Yield:        +{cumulative_supply_pnl:.4f} ETH")
        self.logger.info(f"   ✅ Seasonal Rewards:         +{cumulative_seasonal_pnl:.4f} ETH (EIGEN ± ETHFI)")
        self.logger.info(f"   📈 Price Appreciation:       +{cumulative_price_change_pnl:.4f} ETH (weETH/ETH - includes base staking)")
        self.logger.info(f"   ❌ AAVE Borrow Cost:         -{cumulative_borrow_cost:.4f} ETH")
        self.logger.info(f"   💰 Net P&L:                  {cumulative_net_pnl:.4f} ETH")
        
        if self.config.fixed_balance_pnl:
            compounding_effect = actual_net_profit_eth - cumulative_net_pnl
            self.logger.info(f"   📊 Actual Position Change:   {actual_net_profit_eth:.4f} ETH (with compounding)")
            self.logger.info(f"   🔄 Compounding Effect:       {compounding_effect:.4f} ETH ({compounding_effect/actual_net_profit_eth*100:.1f}%)")
            self.logger.info(f"   ℹ️  Fixed Balance Mode: P&L calculated on constant {initial_net_position:.2f} ETH notional")
        else:
            self.logger.info(f"   ✔️  Verification:             {'PASS ✓' if abs(actual_net_profit_eth - cumulative_net_pnl) < 0.01 else 'FAIL ✗'}")
        
        self.logger.info(f"   ℹ️  Note: Base staking yield (~2.8% APR) is embedded in price appreciation")
        self.logger.info("")
        self.logger.info(f"⛽ Total Gas Costs: {initial_position['total_gas_costs']:.6f} ETH")
        self.logger.info("")
        self.logger.info("📈 PERFORMANCE METRICS:")
        self.logger.info(f"   Total Return:                    {total_return_pct:.2f}%")
        self.logger.info(f"   APY (compounded):                {annualized_return_pct:.2f}%")
        self.logger.info(f"   APR (simple, avg daily × 365):   {uncompounded_annual_return_pct:.2f}%")
        self.logger.info(f"   Sharpe Ratio:                    {sharpe_ratio:.3f}")
        self.logger.info(f"   Annualized Volatility:           {annualized_volatility * 100:.2f}%")
        self.logger.info(f"   Max Drawdown:                    {max_drawdown_pct:.2f}%")
        self.logger.info(f"   P&L / Notional:                  {pnl_over_notional_bps:.1f} bps")
        self.logger.info(f"   Total Notional Traded:           {total_notional_traded:.2f} ETH")
        self.logger.info("")
        
        # Ethena benchmark comparison (if available)
        if self.data['ethena_benchmark'] is not None:
            ethena_outperformance = cumulative_net_pnl - cumulative_ethena_pnl
            ethena_outperformance_pct = (ethena_outperformance / cumulative_ethena_pnl) * 100 if cumulative_ethena_pnl > 0 else 0
            
            self.logger.info("📊 ETHENA BENCHMARK COMPARISON:")
            self.logger.info(f"   Ethena Cumulative P&L:   {cumulative_ethena_pnl:.4f} ETH (on same {initial_net_position:.2f} ETH notional)")
            self.logger.info(f"   Our Cumulative P&L:      {cumulative_net_pnl:.4f} ETH")
            self.logger.info(f"   Outperformance:          {ethena_outperformance:+.4f} ETH ({ethena_outperformance_pct:+.1f}%)")
            self.logger.info("")
        
        self.logger.info(f"🏥 Final Health Factor: {position['health_factor']:.3f}")
        self.logger.info("")
        self.logger.info("📍 VENUE POSITIONS (at t=0):")
        venue_pos = initial_position.get('venue_positions', {})
        if venue_pos:
            self.logger.info(f"   🌐 EtherFi:")
            self.logger.info(f"      ETH Staked:     {venue_pos.get('etherfi', {}).get('eth_staked', 0):.4f} ETH")
            self.logger.info(f"      weETH Received: {venue_pos.get('etherfi', {}).get('weeth_received', 0):.4f} weETH")
            self.logger.info(f"   🏦 AAVE:")
            self.logger.info(f"      weETH Collateral: {venue_pos.get('aave', {}).get('weeth_collateral', 0):.4f} weETH")
            self.logger.info(f"      WETH Debt:        {venue_pos.get('aave', {}).get('weth_debt', 0):.4f} WETH")
        self.logger.info("")
        self.logger.info(f"📋 Event Log: {len(self.event_log):,} events (stake, supply, borrow, fees)")
        self.logger.info("=" * 80)
        
        return self.results
    
    def save_results(self, output_dir: str = "data/analysis") -> None:
        """Save analysis results to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
        
        # Create descriptive label based on config
        config_label = self._get_config_label()
        
        # Save summary
        summary_file = output_path / f"leveraged_restaking_ETH_summary_{config_label}_{timestamp_str}.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'config': self.results['config'],
                'initial_position': self.results['initial_position'],
                'final_position': self.results['final_position'],
                'summary': self.results['summary']
            }, f, indent=2, default=str)
        
        # Save hourly P&L data
        pnl_df = pd.DataFrame(self.results['hourly_pnl'])
        pnl_file = output_path / f"leveraged_restaking_ETH_hourly_pnl_{config_label}_{timestamp_str}.csv"
        pnl_df.to_csv(pnl_file, index=False)
        
        # Save event log
        if self.event_log:
            event_df = pd.DataFrame(self.event_log)
            event_file = output_path / f"leveraged_restaking_ETH_event_log_{config_label}_{timestamp_str}.csv"
            event_df.to_csv(event_file, index=False)
            self.logger.info(f"  📋 Event Log: {event_file} ({len(self.event_log):,} events)")
        
        self.logger.info(f"💾 Results saved to {output_path}")
        self.logger.info(f"  📄 Summary: {summary_file}")
        self.logger.info(f"  📊 Hourly P&L: {pnl_file}")
    
    def _get_leverage_label(self) -> str:
        """Get descriptive label for leverage configuration."""
        if self.config.max_leverage_iterations == 0:
            return "no_leverage"
        elif self.config.max_leverage_iterations == 1:
            return "stake_only"
        elif self.config.max_leverage_iterations is not None:
            return f"lev_{self.config.max_leverage_iterations}x"
        else:
            return "full_leverage"
    
    def _get_config_label(self) -> str:
        """Get complete configuration label for filenames."""
        leverage_label = self._get_leverage_label()
        rewards_label = "eigen_only" if self.config.eigen_only else "all_rewards"
        balance_label = "fixed_bal" if self.config.fixed_balance_pnl else "compound"
        
        return f"{leverage_label}_{rewards_label}_{balance_label}"
    
    def create_plots(self, output_dir: str = "data/analysis") -> None:
        """Create visualization plots."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
        
        # Create descriptive label based on config
        config_label = self._get_config_label()
        
        # Convert to DataFrame
        pnl_df = pd.DataFrame(self.results['hourly_pnl'])
        
        # Create title based on configuration
        leverage_label = self._get_leverage_label()
        rewards_label = "EIGEN Only" if self.config.eigen_only else "All Rewards"
        balance_label = "Fixed Balance" if self.config.fixed_balance_pnl else "Compounding"
        title = f'ETH Leveraged Restaking: {leverage_label.replace("_", " ").title()} | {rewards_label} | {balance_label}'
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        fig = plt.figure(figsize=(28, 14))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        # Create subplots with custom layout
        ax1 = fig.add_subplot(gs[0, 0])  # P&L vs Ethena
        ax2 = fig.add_subplot(gs[0, 1])  # P&L Components
        ax3 = fig.add_subplot(gs[0, 2])  # Yield Components
        ax4 = fig.add_subplot(gs[1, 0])  # Health Factor
        ax5 = fig.add_subplot(gs[1, 1])  # Position Values
        ax6 = fig.add_subplot(gs[1, 2])  # Drawdown
        ax7 = fig.add_subplot(gs[2, :])  # Venue Breakdown (full width)
        
        axes = [[ax1, ax2, ax3], [ax4, ax5, ax6], [ax7]]
        
        # Plot 1: Cumulative Net P&L with Ethena Benchmark
        ax1.plot(pnl_df['timestamp'], pnl_df['cumulative_net_pnl_eth'], 
                linewidth=2, color='green', label='Leveraged Restaking (weETH)')
        
        # Add Ethena benchmark if available
        if 'cumulative_ethena_pnl_eth' in pnl_df.columns and pnl_df['cumulative_ethena_pnl_eth'].max() > 0:
            ax1.plot(pnl_df['timestamp'], pnl_df['cumulative_ethena_pnl_eth'], 
                    linewidth=2, color='purple', linestyle='--', label='Ethena Benchmark (sUSDE)', alpha=0.8)
            ax1.legend(loc='best')
        
        ax1.set_title('Cumulative Net P&L vs Ethena Benchmark (ETH)')
        ax1.set_ylabel('Cumulative P&L (ETH)')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # Plot 2: P&L Components (Cumulative ETH)
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_supply_pnl_eth'], label='AAVE Supply Yield', linewidth=1.5, alpha=0.8)
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_seasonal_pnl_eth'], label='Seasonal Rewards (EIGEN+ETHFI)', linewidth=1.5, alpha=0.8)
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_price_change_pnl_eth'], label='Price Appreciation (incl. base staking)', linewidth=1.5, alpha=0.8)
        ax2.plot(pnl_df['timestamp'], -pnl_df['cumulative_borrow_cost_eth'], label='Borrow Cost (negative)', linewidth=1.5, alpha=0.8)
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_net_pnl_eth'], label='Net P&L', linewidth=2, color='black')
        ax2.set_title('Cumulative P&L Components (ETH)')
        ax2.set_ylabel('Cumulative ETH')
        ax2.legend(loc='best', fontsize=7)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)
        
        # Plot 3: Yield Components (Annualized bps) with smoothing
        # Add 168-hour (weekly) rolling average for net yield to show trend
        pnl_df['net_yield_bps_smooth'] = pnl_df['net_yield_bps'].rolling(window=168, min_periods=1).mean()
        
        ax3.plot(pnl_df['timestamp'], pnl_df['supply_yield_bps'], label='AAVE Supply', alpha=0.7, linewidth=1)
        ax3.plot(pnl_df['timestamp'], pnl_df['seasonal_yield_bps'], label='Seasonal Rewards', alpha=0.7, linewidth=1.5)
        ax3.plot(pnl_df['timestamp'], pnl_df['base_staking_yield_bps'], label='Base Staking (ref only)', alpha=0.3, linewidth=0.5, linestyle=':')
        ax3.plot(pnl_df['timestamp'], -pnl_df['borrow_cost_bps'], label='Borrow Cost', alpha=0.7, linewidth=1)
        # Show both raw and smoothed net yield
        ax3.plot(pnl_df['timestamp'], pnl_df['net_yield_bps'], label='Net Yield (hourly)', linewidth=0.5, color='red', alpha=0.2)
        ax3.plot(pnl_df['timestamp'], pnl_df['net_yield_bps_smooth'], label='Net Yield (weekly avg)', linewidth=2.5, color='darkred')
        ax3.set_title('Hourly Yield Components (Annualized bps)')
        ax3.set_ylabel('Yield (bps)')
        ax3.legend(loc='best', fontsize=6)
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(axis='x', rotation=45)
        
        # Plot 4: Health Factor
        ax4.plot(pnl_df['timestamp'], pnl_df['health_factor'], label='Health Factor', linewidth=2, color='blue')
        ax4.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Liquidation (HF=1.0)')
        ax4.axhline(y=1.015, color='orange', linestyle='--', alpha=0.5, label='Warning (HF=1.015)')
        ax4.set_title('Health Factor (Correct Formula: LT * Collateral / Debt)')
        ax4.set_ylabel('Health Factor')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.tick_params(axis='x', rotation=45)
        ax4.set_ylim(bottom=0.95)
        
        # Plot 5: AAVE Positions Over Time (Native Units)
        # Calculate weETH and WETH balances over time from collateral/debt values
        initial_weeth_collateral = self.results['initial_position']['weeth_collateral']
        initial_weth_debt = self.results['initial_position']['weth_debt']
        
        # Derive native unit balances from ETH values
        pnl_df['weeth_collateral_units'] = pnl_df['collateral_value_eth'] / pnl_df['weeth_price']
        pnl_df['weth_debt_units'] = pnl_df['debt_value_eth']  # Already in WETH
        
        ax5.plot(pnl_df['timestamp'], pnl_df['weeth_collateral_units'], 
                label='AAVE weETH Collateral', linewidth=2, color='#2196F3')
        ax5.plot(pnl_df['timestamp'], pnl_df['weth_debt_units'], 
                label='AAVE WETH Debt', linewidth=2, color='#F44336')
        ax5.axhline(y=initial_weeth_collateral, color='#2196F3', linestyle='--', alpha=0.3, label=f'Initial weETH: {initial_weeth_collateral:.0f}')
        ax5.axhline(y=initial_weth_debt, color='#F44336', linestyle='--', alpha=0.3, label=f'Initial WETH: {initial_weth_debt:.0f}')
        
        ax5.set_title('AAVE Position Evolution (Native Units)')
        ax5.set_ylabel('Position Size (weETH / WETH)')
        ax5.legend(loc='best', fontsize=9)
        ax5.grid(True, alpha=0.3)
        ax5.tick_params(axis='x', rotation=45)
        
        # Plot 6: Drawdown
        ax6.fill_between(pnl_df['timestamp'], 0, pnl_df['drawdown_pct'], 
                        alpha=0.3, color='red', label='Drawdown')
        ax6.plot(pnl_df['timestamp'], pnl_df['drawdown_pct'], linewidth=1.5, color='darkred')
        max_dd = pnl_df['drawdown_pct'].min()
        ax6.axhline(y=max_dd, color='red', linestyle='--', alpha=0.7, 
                   label=f'Max DD: {max_dd:.2f}%')
        ax6.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax6.set_title('Drawdown from Peak (%)')
        ax6.set_ylabel('Drawdown (%)')
        ax6.legend(loc='lower left')
        ax6.grid(True, alpha=0.3)
        ax6.tick_params(axis='x', rotation=45)
        ax6.set_ylim(top=1)  # Start just above 0
        
        # Plot 7: Venue Position Breakdown with Correct Units
        venue_data = self.results['initial_position'].get('venue_positions', {})
        if venue_data:
            etherfi_eth_staked = venue_data.get('etherfi', {}).get('eth_staked', 0)
            etherfi_weeth_received = venue_data.get('etherfi', {}).get('weeth_received', 0)
            aave_collateral_weeth = venue_data.get('aave', {}).get('weeth_collateral', 0)
            aave_debt_weth = venue_data.get('aave', {}).get('weth_debt', 0)
            weeth_price = pnl_df.iloc[0]['weeth_price']
            
            # Create bar chart with CORRECT units
            categories = ['EtherFi\nETH Staked', 'EtherFi\nweETH Received', 'AAVE\nweETH Collateral', 'AAVE\nWETH Debt']
            values = [etherfi_eth_staked, etherfi_weeth_received, aave_collateral_weeth, aave_debt_weth]
            colors = ['#4CAF50', '#81C784', '#2196F3', '#F44336']
            unit_labels = ['ETH', 'weETH', 'weETH', 'WETH']
            
            bars = ax7.bar(categories, values, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
            
            # Add value labels on bars with correct units
            for bar, val, unit in zip(bars, values, unit_labels):
                height = bar.get_height()
                ax7.text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.2f} {unit}',
                        ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            # Add conversion annotation
            annotation_text = (
                f'weETH/ETH Oracle: {weeth_price:.4f}\n'
                f'Leverage: {self.results["initial_position"]["leverage_multiplier"]:.2f}x\n'
                f'Iterations: {self.results["initial_position"]["iteration_count"]}\n\n'
                f'Real Exposure: Long {self.config.initial_eth:.0f} ETH'
            )
            ax7.text(0.98, 0.98, annotation_text,
                    transform=ax7.transAxes, fontsize=11, verticalalignment='top',
                    horizontalalignment='right', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
            
            ax7.set_title('Venue Positions at t=0 (Correct Units: weETH ≠ ETH)', fontsize=13, fontweight='bold')
            ax7.set_ylabel('Position Size (Native Units)', fontsize=11)
            ax7.grid(True, alpha=0.3, axis='y')
            ax7.set_axisbelow(True)
        
        plt.tight_layout()
        
        # Save plot
        plot_file = output_path / f"leveraged_restaking_ETH_analysis_{config_label}_{timestamp_str}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"📊 Plots saved to {plot_file}")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze ETH-based leveraged restaking strategy (CORRECTED)")
    parser.add_argument("--start-date", type=str, default="2024-05-12", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2025-09-18", help="End date (YYYY-MM-DD)")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--output-dir", type=str, default="data/analysis", help="Output directory")
    parser.add_argument("--initial-eth", type=float, default=100.0, help="Initial ETH amount")
    parser.add_argument("--min-position-eth", type=float, default=10.0, help="Minimum position ETH to continue leverage loop")
    parser.add_argument("--max-leverage-iterations", type=int, default=None, help="Max leverage iterations (0=no leverage/borrow, None=unlimited)")
    parser.add_argument("--eigen-only", action="store_true", help="Only include EIGEN rewards (exclude ETHFI)")
    parser.add_argument("--fixed-balance-pnl", action="store_true", help="Calculate P&L on fixed initial balance (constant notional, no compounding)")
    parser.add_argument("--no-plots", action="store_true", help="Skip creating plots")
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = LeveragedRestakingAnalyzer(args.data_dir)
        
        # Update config
        analyzer.config.initial_eth = args.initial_eth
        analyzer.config.min_position_eth = args.min_position_eth
        analyzer.config.max_leverage_iterations = args.max_leverage_iterations
        analyzer.config.eigen_only = args.eigen_only
        analyzer.config.fixed_balance_pnl = args.fixed_balance_pnl
        
        # Determine mode description
        if args.max_leverage_iterations == 0:
            mode = "NO LEVERAGE (Stake only, no borrowing)"
        elif args.max_leverage_iterations is not None:
            mode = f"LIMITED LEVERAGE (Max {args.max_leverage_iterations} iterations)"
        else:
            mode = "FULL LEVERAGE (Until <10 ETH remaining)"
        
        rewards_mode = "EIGEN ONLY" if args.eigen_only else "EIGEN + ETHFI"
        pnl_mode = "FIXED BALANCE (Constant Notional)" if args.fixed_balance_pnl else "COMPOUNDING"
        
        print("🎯 ETH-Based Leveraged Restaking Strategy Analysis")
        print(f"📅 Date range: {args.start_date} to {args.end_date}")
        print(f"💰 Initial ETH: {args.initial_eth}")
        print(f"🔧 Leverage: {mode}")
        print(f"🎁 Rewards: {rewards_mode}")
        print(f"📊 P&L Mode: {pnl_mode}")
        print()
        
        # Run analysis
        results = analyzer.run_analysis(args.start_date, args.end_date)
        
        # Save results
        analyzer.save_results(args.output_dir)
        
        # Create plots
        if not args.no_plots:
            analyzer.create_plots(args.output_dir)
        
        print(f"\n🎉 Analysis completed successfully!")
        print(f"📁 Results saved to: {args.output_dir}")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())