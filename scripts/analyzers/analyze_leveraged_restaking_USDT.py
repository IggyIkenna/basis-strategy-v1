#!/usr/bin/env python3
"""
USDT-Based Market-Neutral Leveraged Restaking Strategy Analyzer

Analyzes a delta-neutral leveraged restaking strategy:
1. Start with USDT (e.g., $100k)
2. Split 50/50:
   - 50%: Buy WETH → stake to weETH → leverage loop (long exposure)
   - 50%: Short ETH perpetual on CEX (hedge)
3. Track both legs with funding rate costs and restaking yields

Key Features:
- Market-neutral (delta hedged with perp short)
- Leverage loop on long side (like ETH version)
- Funding rate costs on short side
- Net yield = restaking yields - borrow costs - funding costs

Data Sources:
- Spot prices: data/market_data/spot_prices/eth_usd/uniswapv3_WETHUSDT_1h_2024-01-01_2025-09-27.csv
- Futures prices: data/market_data/derivatives/futures_ohlcv/binance_ETHUSDT_perp_1h_2024-01-01_2025-09-26.csv
- Funding rates: data/market_data/derivatives/funding_rates/binance_ETHUSDT_perp_funding_2024-01-01_2025-09-26.csv
- (Plus all the weETH/WETH AAVE rates, staking yields, etc. from ETH version)
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
    """Configuration for the USDT market-neutral leveraged restaking strategy."""
    initial_usdt: float = 100000.0
    allocation_to_long_pct: float = 0.50  # 50% to long restaking, 50% to short hedge
    min_position_usd: float = 10000.0  # Stop leverage loop when remaining < $10k
    max_ltv: float = 0.93  # AAVE maximum LTV cap (fixed by protocol)
    liquidation_threshold: float = 0.95  # weETH liquidation threshold (eMode)
    gas_cost_multiplier: float = 1.2
    max_leverage_iterations: Optional[int] = None
    # eigen_only removed - no seasonal rewards
    fixed_balance_pnl: bool = False
    # Perp hedge allocation across exchanges
    binance_hedge_pct: float = 0.33  # 33.33% of hedge on Binance
    bybit_hedge_pct: float = 0.33    # 33.33% of hedge on Bybit
    okx_hedge_pct: float = 0.34      # 33.34% of hedge on OKX
    # Spot purchase venue
    spot_venue: str = 'BINANCE'  # 'BINANCE' (CEX_SPOT) or 'UNISWAP' (DEX)
    # CEX margin settings
    initial_margin_ratio: float = 0.15  # 15% initial margin for perps
    maintenance_margin_ratio: float = 0.10  # 10% maintenance margin (liquidation threshold)
    # Rebalancing settings
    rebalance_threshold_pct: float = 5.0  # Trigger rebalance when delta > 5%
    # Flash loan / Atomic mode settings
    use_flash_one_shot: bool = False  # If True, use atomic entry/exit instead of recursive loop
    flash_source: str = "BALANCER"  # "BALANCER", "MORPHO", or "AAVE"
    flash_fee_bps: float = 0.0  # 0 bps for Balancer/Morpho, ~5 bps for Aave
    entry_hf_min: float = 1.04  # Minimum health factor after entry
    unwind_hf_min: float = 1.04  # Minimum health factor after partial unwind
    max_stake_spread_move: float = 0.02215  # Max expected adverse weETH/ETH oracle move (2.215%)
    # Note: target_ltv = max_ltv * (1 - max_stake_spread_move)
    # Example: 0.93 * (1 - 0.02215) = 0.93 * 0.97785 = 0.909 ≈ 0.91
    swap_slippage_bps: float = 5.0  # Slippage tolerance for swaps
    dex_fee_bps_weeth_weth: float = 5  # Curve/Uni pool fee weETH/WETH
    dex_fee_bps_weth_usdt: float = 5  # Pool fee WETH/USDT
    balance_pnl_log_threshold_usd: float = 500.0  # Log balance-based P&L moves above this size


class USDTLeveragedRestakingAnalyzer:
    """Analyzes USDT-based market-neutral leveraged restaking strategy."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.config = StrategyConfig()
        
        # Set up logging
        self.logger = logging.getLogger("usdt_leveraged_restaking")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Data storage
        self.data = {}
        self.results = {}
        self.event_log = []
        
        self.logger.info("USDT Market-Neutral Leveraged Restaking Analyzer initialized")
    
    def _log_event(self, timestamp: pd.Timestamp, event_type: str, venue: str, 
                   token: str = None, amount: float = None, **event_data) -> None:
        """Log an event for audit trail."""
        event = {
            'timestamp': timestamp,
            'event_type': event_type,
            'venue': venue,
            'token': token,
            'amount': amount,
            **event_data
        }
        self.event_log.append(event)
    
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
        
        # Load staking yields (base yield only - no seasonal rewards)
        staking_file = self.data_dir / "protocol_data" / "staking" / "base_yields" / "weeth_oracle_yields_2024-01-01_2025-09-18.csv"
        self.data['staking_yields'] = pd.read_csv(staking_file)
        self.data['staking_yields']['timestamp'] = pd.to_datetime(self.data['staking_yields']['timestamp'].str.replace('Z', ''))
        self.data['staking_yields']['date'] = pd.to_datetime(self.data['staking_yields']['date'])
        
        # Load spot prices (for WETH/USDT conversions)
        spot_file = self.data_dir / "market_data" / "spot_prices" / "eth_usd" / "uniswapv3_WETHUSDT_1h_2024-01-01_2025-09-27.csv"
        self.data['spot_prices'] = pd.read_csv(spot_file)
        # Parse as Unix timestamps (seconds since epoch)
        self.data['spot_prices']['timestamp'] = pd.to_datetime(self.data['spot_prices']['timestamp'], unit='s', utc=True)
        self.data['spot_prices'] = self.data['spot_prices'].set_index('timestamp').sort_index()
        # Use open price for execution (start of hour) to match perp pricing
        self.data['spot_prices']['exec_price'] = self.data['spot_prices']['open']
        
        # Load Binance futures prices (for perp hedge)
        futures_file = self.data_dir / "market_data" / "derivatives" / "futures_ohlcv" / "binance_ETHUSDT_perp_1h_2024-01-01_2025-09-26.csv"
        self.data['futures_prices'] = pd.read_csv(futures_file)
        self.data['futures_prices']['timestamp'] = pd.to_datetime(self.data['futures_prices']['timestamp'], utc=True)
        # Handle duplicate timestamps by keeping the last occurrence
        self.data['futures_prices'] = self.data['futures_prices'].drop_duplicates(subset=['timestamp'], keep='last')
        self.data['futures_prices'] = self.data['futures_prices'].set_index('timestamp').sort_index()
        
        # Load Bybit futures prices (for perp hedge) - PHASE 1 FIX
        bybit_futures_file = self.data_dir / "market_data" / "derivatives" / "futures_ohlcv" / "bybit_ETHUSDT_perp_1h_2024-01-01_2025-09-26.csv"
        self.data['bybit_futures'] = pd.read_csv(bybit_futures_file)
        self.data['bybit_futures']['timestamp'] = pd.to_datetime(self.data['bybit_futures']['timestamp'], utc=True)
        # Handle duplicate timestamps by keeping the last occurrence
        self.data['bybit_futures'] = self.data['bybit_futures'].drop_duplicates(subset=['timestamp'], keep='last')
        self.data['bybit_futures'] = self.data['bybit_futures'].set_index('timestamp').sort_index()
        
        # Load OKX futures prices (if available) - use when available, fallback to Binance proxy
        okx_futures_file = self.data_dir / "market_data" / "derivatives" / "futures_ohlcv" / "okx_ETHUSDT_perp_1h_2024-08-01_2025-09-18.csv"
        if okx_futures_file.exists():
            self.data['okx_futures'] = pd.read_csv(okx_futures_file)
            self.data['okx_futures']['timestamp'] = pd.to_datetime(self.data['okx_futures']['timestamp'], utc=True)
            # Handle duplicate timestamps by keeping the last occurrence
            self.data['okx_futures'] = self.data['okx_futures'].drop_duplicates(subset=['timestamp'], keep='last')
            self.data['okx_futures'] = self.data['okx_futures'].set_index('timestamp').sort_index()
            self.logger.info(f"  OKX futures prices: {len(self.data['okx_futures'])} records")
        else:
            self.data['okx_futures'] = None
            self.logger.info("  OKX futures prices: Not available (file not found)")
        
        # Load Binance funding rates  
        funding_file = self.data_dir / "market_data" / "derivatives" / "funding_rates" / "binance_ETHUSDT_funding_rates_2024-01-01_2025-09-26.csv"
        self.data['funding_rates'] = pd.read_csv(funding_file)
        self.data['funding_rates']['timestamp'] = pd.to_datetime(self.data['funding_rates']['funding_timestamp'], format='ISO8601', utc=True)
        self.data['funding_rates'] = self.data['funding_rates'].set_index('timestamp').sort_index()
        
        # Load Bybit funding rates
        bybit_funding_file = self.data_dir / "market_data" / "derivatives" / "funding_rates" / "bybit_ETHUSDT_funding_rates_2024-01-01_2025-09-26.csv"
        self.data['bybit_funding'] = pd.read_csv(bybit_funding_file)
        self.data['bybit_funding']['timestamp'] = pd.to_datetime(self.data['bybit_funding']['funding_timestamp'], format='ISO8601', utc=True)
        self.data['bybit_funding'] = self.data['bybit_funding'].set_index('timestamp').sort_index()
        
        # Load OKX funding rates (if available)
        okx_funding_file = self.data_dir / "market_data" / "derivatives" / "funding_rates" / "okx_ETHUSDT_funding_rates_2024-01-01_2025-09-18.csv"
        if okx_funding_file.exists():
            self.data['okx_funding'] = pd.read_csv(okx_funding_file)
            self.data['okx_funding']['timestamp'] = pd.to_datetime(self.data['okx_funding']['funding_timestamp'], format='ISO8601', utc=True)
            self.data['okx_funding'] = self.data['okx_funding'].set_index('timestamp').sort_index()
            self.logger.info(f"  OKX funding rates: {len(self.data['okx_funding'])} records")
        else:
            self.data['okx_funding'] = None
            self.logger.info("  OKX funding rates: Not available (file not found)")
        
        # Load oracle prices
        oracle_file = self.data_dir / "protocol_data" / "aave" / "oracle" / "weETH_ETH_oracle_2024-01-01_2025-09-18.csv"
        self.data['oracle_prices'] = pd.read_csv(oracle_file, comment='#')
        self.data['oracle_prices']['timestamp'] = pd.to_datetime(self.data['oracle_prices']['timestamp'])
        self.data['oracle_prices'] = self.data['oracle_prices'].set_index('timestamp').sort_index()
        
        # Load gas costs
        gas_file = self.data_dir / "blockchain_data" / "gas_prices" / "ethereum_gas_prices_enhanced_2024-01-01_2025-09-26.csv"
        self.data['gas_costs'] = pd.read_csv(gas_file)
        self.data['gas_costs']['timestamp'] = pd.to_datetime(self.data['gas_costs']['timestamp'])
        self.data['gas_costs'] = self.data['gas_costs'].set_index('timestamp').sort_index()
        
        # Load execution costs
        exec_cost_file = self.data_dir / "execution_costs" / "execution_cost_simulation_results.csv"
        self.data['execution_costs'] = pd.read_csv(exec_cost_file)
        self.data['execution_costs']['timestamp'] = pd.to_datetime(self.data['execution_costs']['timestamp'], utc=True)
        self.data['execution_costs'] = self.data['execution_costs'].set_index('timestamp').sort_index()
        
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
        self.logger.info(f"  Spot prices: {len(self.data['spot_prices'])} records")
        self.logger.info(f"  Binance futures prices: {len(self.data['futures_prices'])} records")
        self.logger.info(f"  Bybit futures prices: {len(self.data['bybit_futures'])} records")
        self.logger.info(f"  Binance funding rates: {len(self.data['funding_rates'])} records")
        self.logger.info(f"  Bybit funding rates: {len(self.data['bybit_funding'])} records")
        self.logger.info(f"  weETH rates: {len(self.data['weeth_rates'])} records")
        self.logger.info(f"  WETH rates: {len(self.data['weth_rates'])} records")
        self.logger.info(f"  Staking yields: {len(self.data['staking_yields'])} records")
    
    def _get_spot_price(self, timestamp: pd.Timestamp) -> float:
        """Get ETH/USDT spot price at timestamp (hourly candle open)."""
        spot_data = self.data['spot_prices']
        spot_ts = spot_data.index.asof(timestamp)
        
        if pd.isna(spot_ts):
            spot_ts = spot_data.index[0]
        
        return spot_data.loc[spot_ts, 'exec_price']
    
    def _get_funding_rate(self, timestamp: pd.Timestamp) -> float:
        """Get perpetual funding rate at timestamp (8-hourly on Binance)."""
        funding_data = self.data['funding_rates']
        funding_ts = funding_data.index.asof(timestamp)
        
        if pd.isna(funding_ts):
            return 0.0
        
        return funding_data.loc[funding_ts, 'funding_rate']
    
    def _get_gas_cost_usd(self, timestamp: pd.Timestamp, transaction_type: str, eth_price: float) -> float:
        """Get gas cost in USD."""
        gas_data = self.data['gas_costs']
        closest_ts = gas_data.index.asof(timestamp)
        
        if pd.isna(closest_ts):
            closest_ts = gas_data.index[0]
        
        gas_cost_eth = gas_data.loc[closest_ts, f'{transaction_type}_eth']
        return gas_cost_eth * eth_price * self.config.gas_cost_multiplier
    
    def _get_bybit_funding_rate(self, timestamp: pd.Timestamp) -> float:
        """Get Bybit perpetual funding rate at timestamp."""
        funding_data = self.data['bybit_funding']
        funding_ts = funding_data.index.asof(timestamp)
        
        if pd.isna(funding_ts):
            return 0.0
        
        return funding_data.loc[funding_ts, 'funding_rate']
    
    def _get_okx_funding_rate(self, timestamp: pd.Timestamp) -> float:
        """Get OKX perpetual funding rate at timestamp."""
        if self.data['okx_funding'] is None:
            return 0.0
        
        funding_data = self.data['okx_funding']
        funding_ts = funding_data.index.asof(timestamp)
        
        if pd.isna(funding_ts):
            return 0.0
        
        return funding_data.loc[funding_ts, 'funding_rate']
    
    def _get_execution_cost(self, timestamp: pd.Timestamp, pair: str, size_usd: float, venue: str) -> float:
        """
        Get execution cost in basis points for a given trade.
        
        Args:
            timestamp: Trade timestamp
            pair: Trading pair (e.g., 'ETH/USDT', 'ETHUSDT-PERP')
            size_usd: Trade size in USD
            venue: 'BINANCE' (CEX_SPOT), 'UNISWAP' (DEX), 'BINANCE_PERP', 'BYBIT_PERP'
        
        Returns:
            Execution cost in basis points (e.g., 7.0 = 0.07%)
        """
        exec_data = self.data['execution_costs']
        
        # Map venue to venue_type in data
        venue_type_map = {
            'BINANCE': 'CEX_SPOT',
            'UNISWAP': 'DEX',
            'BINANCE_PERP': 'CEX_PERP',
            'BYBIT_PERP': 'CEX_PERP'
        }
        venue_type = venue_type_map.get(venue, 'CEX_SPOT')
        
        # Map pair for perps
        if venue in ['BINANCE_PERP', 'BYBIT_PERP']:
            pair = 'ETHUSDT-PERP'
        
        # Determine size bucket
        if size_usd < 50000:
            size_bucket = '10k'
        elif size_usd < 500000:
            size_bucket = '100k'
        else:
            size_bucket = '1m'
        
        # Filter data
        filtered = exec_data[
            (exec_data['pair'] == pair) & 
            (exec_data['size_bucket'] == size_bucket) &
            (exec_data['venue_type'] == venue_type)
        ]
        
        if len(filtered) == 0:
            self.logger.warning(f"No execution cost data for {pair}/{venue_type}/{size_bucket}, using default 7 bps")
            return 7.0
        
        # Get closest timestamp
        closest_ts = filtered.index.asof(timestamp)
        if pd.isna(closest_ts):
            closest_ts = filtered.index[0]
        
        return filtered.loc[closest_ts, 'execution_cost_bps']
    
    def _buy_eth_spot(self, timestamp: pd.Timestamp, usdt_amount: float, eth_price: float) -> Tuple[float, float, float]:
        """
        Buy ETH with USDT on spot market (CEX).
        
        Process:
        1. Pay gas to send USDT to CEX (VENUE_TRANSFER)
        2. Execute spot trade (pay execution cost)
        3. Pay gas to send ETH back to wallet (VENUE_TRANSFER)
        
        Returns: (eth_received, execution_cost_usd, total_gas_cost_usd)
        """
        venue = self.config.spot_venue
        
        # Step 1: Pay gas to send USDT to CEX
        usdt_transfer_gas = self._get_gas_cost_usd(timestamp, 'VENUE_TRANSFER', eth_price)
        self._log_event(timestamp, 'GAS_FEE_PAID', 'ETHEREUM', 'ETH', usdt_transfer_gas / eth_price,
                       fee_type='venue_transfer', related_transaction='usdt_to_cex',
                       fee_usd=usdt_transfer_gas, direction='USDT_to_CEX')
        
        # Step 2: Execute spot trade with execution cost
        exec_cost_bps = self._get_execution_cost(timestamp, 'ETH/USDT', usdt_amount, venue)
        exec_cost_usd = usdt_amount * (exec_cost_bps / 10000)
        
        net_usdt = usdt_amount - exec_cost_usd
        eth_received_at_cex = net_usdt / eth_price
        
        self._log_event(timestamp, 'SPOT_TRADE', venue, 'ETH', eth_received_at_cex,
                       side='BUY', usdt_spent=usdt_amount, usdt_net=net_usdt,
                       execution_cost_usd=exec_cost_usd, execution_cost_bps=exec_cost_bps,
                       eth_price=eth_price)
        
        # Step 3: Pay gas to send ETH back to wallet
        eth_transfer_gas = self._get_gas_cost_usd(timestamp, 'VENUE_TRANSFER', eth_price)
        self._log_event(timestamp, 'GAS_FEE_PAID', 'ETHEREUM', 'ETH', eth_transfer_gas / eth_price,
                       fee_type='venue_transfer', related_transaction='eth_from_cex',
                       fee_usd=eth_transfer_gas, direction='ETH_from_CEX')
        
        total_gas = usdt_transfer_gas + eth_transfer_gas
        
        self.logger.info(f"   💱 Spot ETH Purchase Flow:")
        self.logger.info(f"      1. Gas to send USDT → {venue}: ${usdt_transfer_gas:.2f}")
        self.logger.info(f"      2. Buy ETH on {venue}: {eth_received_at_cex:.4f} ETH @ ${eth_price:,.2f}")
        self.logger.info(f"         Execution Cost: ${exec_cost_usd:.2f} ({exec_cost_bps} bps)")
        self.logger.info(f"      3. Gas to send ETH → Wallet: ${eth_transfer_gas:.2f}")
        self.logger.info(f"      Total ETH in Wallet: {eth_received_at_cex:.4f} ETH")
        self.logger.info(f"      Total Gas (transfers): ${total_gas:.2f}")
        
        return eth_received_at_cex, exec_cost_usd, total_gas
    
    def _get_rates_at_timestamp(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get all relevant rates at a specific timestamp."""
        rates = {}
        
        # weETH supply rate growth factor (hourly)
        weeth_data = self.data['weeth_rates']
        weeth_ts = weeth_data.index.asof(timestamp)
        if pd.isna(weeth_ts):
            weeth_ts = weeth_data.index[0]
        
        rates['weeth_supply_growth_factor'] = weeth_data.loc[weeth_ts, 'liquidity_growth_factor']
        rates['weeth_supply_apy'] = weeth_data.loc[weeth_ts, 'liquidity_apy_hourly']
        
        # PHASE 2.5: Add AAVE indices for exact mechanics
        if 'liquidityIndex' in weeth_data.columns:
            rates['liquidityIndex'] = weeth_data.loc[weeth_ts, 'liquidityIndex']
        
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
    
    def _get_staking_yield_at_timestamp(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get base staking yield at a specific timestamp (no seasonal rewards)."""
        
        # Get base staking yield from oracle data
        timestamp_date = timestamp.date()
        staking_data = self.data['staking_yields']
        
        matching_dates = staking_data[staking_data['date'] <= pd.Timestamp(timestamp_date)]
        if len(matching_dates) == 0:
            daily_yield = staking_data.iloc[0]['daily_yield']
            base_yield_annual = staking_data.iloc[0]['base_staking_apr']
        else:
            latest_record = matching_dates.iloc[-1]
            daily_yield = latest_record['daily_yield']
            base_yield_annual = latest_record['base_staking_apr']
        
        # Convert daily yield to hourly
        base_yield_hourly = (1 + daily_yield) ** (1 / 24) - 1
        
        return {
            'base_yield_hourly': base_yield_hourly,
            'base_yield_annual': base_yield_annual,
            'daily_yield': daily_yield
        }
    
    def _get_ethena_apr_at_timestamp(self, timestamp: pd.Timestamp) -> float:
        """Get Ethena benchmark APR at a specific timestamp."""
        if self.data['ethena_benchmark'] is None:
            return 0.0
        
        ethena_data = self.data['ethena_benchmark']
        ethena_ts = ethena_data.index.asof(timestamp)
        
        if pd.isna(ethena_ts):
            ethena_ts = ethena_data.index[0]
        
        return ethena_data.loc[ethena_ts, 'apr_decimal']
    
    def _execute_leverage_loop_usd(self, timestamp: pd.Timestamp, long_capital_usd: float, eth_price: float) -> Dict:
        """Execute leverage loop starting with USD capital."""
        self.logger.info(f"🔄 Executing leverage loop at t=0 (timestamp: {timestamp})...")
        
        # Get rates at t=0
        rates = self._get_rates_at_timestamp(timestamp)
        weeth_price = rates['weeth_price']
        
        # Convert USD to WETH
        available_weth = long_capital_usd / eth_price
        
        # Initialize
        total_weeth_collateral = 0.0
        total_weth_debt = 0.0
        total_gas_costs_usd = 0.0
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
        
        while (available_weth * eth_price) >= self.config.min_position_usd:
            iteration_count += 1
            
            if max_iterations is not None and iteration_count > max_iterations:
                self.logger.info(f"  Stopped: Max leverage iterations ({max_iterations}) reached")
                break
            
            # Check if this will be the last iteration (next loop would be < min)
            is_last_iteration = False
            if self.config.max_leverage_iterations != 0:
                # Calculate what the next borrow would be
                stake_gas_check = self._get_gas_cost_usd(timestamp, 'CREATE_LST', eth_price)
                weth_after_gas_check = available_weth - (stake_gas_check / eth_price)
                potential_weeth = weth_after_gas_check / weeth_price
                potential_borrow_usd = potential_weeth * weeth_price * self.config.max_ltv * eth_price
                
                # If next iteration would be below minimum, this is the last iteration
                if potential_borrow_usd < self.config.min_position_usd:
                    is_last_iteration = True
                    self.logger.info(f"  Iteration {iteration_count}: FINAL iteration (next would be < ${self.config.min_position_usd:,.0f})")
            
            # Step 1: Stake WETH → weETH (pay gas)
            stake_gas_usd = self._get_gas_cost_usd(timestamp, 'CREATE_LST', eth_price)
            self._log_event(timestamp, 'GAS_FEE_PAID', 'ETHEREUM', 'ETH', stake_gas_usd / eth_price,
                          fee_type='create_lst', fee_usd=stake_gas_usd, iteration=iteration_count)
            
            weth_after_gas = available_weth - (stake_gas_usd / eth_price)
            
            if weth_after_gas <= 0:
                break
            
            # Convert WETH to weETH using oracle price
            weeth_received = weth_after_gas / weeth_price
            
            self._log_event(timestamp, 'STAKE_DEPOSIT', 'ETHERFI', 'ETH', weth_after_gas,
                          output_token='weETH', amount_out=weeth_received,
                          oracle_price=weeth_price, iteration=iteration_count)
            
            venue_positions['etherfi']['eth_staked'] += weth_after_gas
            venue_positions['etherfi']['weeth_received'] += weeth_received
            
            # Step 2: Supply weETH to AAVE (pay gas, receive aWeETH)
            supply_gas_usd = self._get_gas_cost_usd(timestamp, 'COLLATERAL_SUPPLIED', eth_price)
            self._log_event(timestamp, 'GAS_FEE_PAID', 'ETHEREUM', 'ETH', supply_gas_usd / eth_price,
                          fee_type='collateral_supplied', fee_usd=supply_gas_usd, iteration=iteration_count)
            
            # Supply weETH → receive aWeETH (1:1 initially)
            aweeth_received = weeth_received  # 1:1 on deposit
            total_weeth_collateral += weeth_received
            
            self._log_event(timestamp, 'COLLATERAL_SUPPLIED', 'AAVE', 'weETH', weeth_received,
                          collateral_type='supply_for_borrowing', 
                          atoken_received='aWeETH', atoken_amount=aweeth_received,
                          iteration=iteration_count)
            
            venue_positions['aave']['weeth_collateral'] += weeth_received
            venue_positions['aave']['aweeth_balance'] = venue_positions['aave'].get('aweeth_balance', 0.0) + aweeth_received
            
            # Step 3: Borrow WETH at max LTV (pay gas) - ONLY if not last iteration and not max_leverage_iterations=0
            if self.config.max_leverage_iterations != 0 and not is_last_iteration:
                borrow_gas_usd = self._get_gas_cost_usd(timestamp, 'LOAN_CREATED', eth_price)
                self._log_event(timestamp, 'GAS_FEE_PAID', 'ETHEREUM', 'ETH', borrow_gas_usd / eth_price,
                              fee_type='loan_created', fee_usd=borrow_gas_usd, iteration=iteration_count)
                
                max_borrow = weeth_received * weeth_price * self.config.max_ltv
                total_weth_debt += max_borrow
                
                self._log_event(timestamp, 'LOAN_CREATED', 'AAVE', 'WETH', max_borrow,
                              debt_type='variable_rate', ltv=self.config.max_ltv,
                              collateral_token='weETH', collateral_amount=weeth_received,
                              iteration=iteration_count)
                
                venue_positions['aave']['weth_debt'] += max_borrow
                
                total_gas_costs_usd += borrow_gas_usd
            else:
                # No borrowing in zero-leverage mode OR on last iteration
                max_borrow = 0.0
                if is_last_iteration:
                    self.logger.info(f"  Final iteration: Staked and supplied but DID NOT borrow (keeps position balanced)")
            
            total_gas_costs_usd += (stake_gas_usd + supply_gas_usd)
            
            # Update available WETH for next iteration
            available_weth = max_borrow
            
            if iteration_count % 10 == 0:
                self.logger.info(f"  Iteration {iteration_count}: {total_weeth_collateral:.2f} weETH collateral, {total_weth_debt:.2f} WETH debt")
        
        # Calculate final metrics
        collateral_value_weth = total_weeth_collateral * weeth_price
        net_position_weth = collateral_value_weth - total_weth_debt
        net_position_usd = net_position_weth * eth_price
        
        health_factor = (self.config.liquidation_threshold * collateral_value_weth) / total_weth_debt if total_weth_debt > 0 else float('inf')
        leverage_multiplier = collateral_value_weth / (long_capital_usd / eth_price)
        
        self.logger.info(f"✅ Leverage loop completed:")
        self.logger.info(f"   Iterations: {iteration_count}")
        self.logger.info(f"   Initial USD: ${long_capital_usd:,.2f}")
        self.logger.info(f"   weETH Collateral: {total_weeth_collateral:.4f} ({collateral_value_weth:.2f} WETH)")
        self.logger.info(f"   WETH Debt: {total_weth_debt:.2f}")
        self.logger.info(f"   Net Position: {net_position_weth:.2f} WETH (${net_position_usd:,.2f})")
        self.logger.info(f"   Long ETH Exposure: {net_position_weth:.2f} ETH")
        self.logger.info(f"   Leverage: {leverage_multiplier:.2f}x")
        self.logger.info(f"   Health Factor: {health_factor:.3f}")
        self.logger.info(f"   Total Gas Costs: ${total_gas_costs_usd:.2f}")
        
        return {
            'timestamp': timestamp,
            'iteration_count': iteration_count,
            'weeth_collateral': total_weeth_collateral,
            'weth_debt': total_weth_debt,
            'collateral_value_weth': collateral_value_weth,
            'net_position_weth': net_position_weth,
            'net_position_usd': net_position_usd,
            'long_eth_exposure': net_position_weth,
            'health_factor': health_factor,
            'leverage_multiplier': leverage_multiplier,
            'total_gas_costs_usd': total_gas_costs_usd,
            'weeth_price': weeth_price,
            'venue_positions': venue_positions
        }
    
    def _execute_leverage_one_shot_usd(self, timestamp: pd.Timestamp, equity_usd: float, eth_price: float) -> Dict:
        """
        Execute leverage in ONE atomic transaction using flash loans (Instadapp-style).
        
        Math:
        - Equity E = equity_usd
        - LTV λ = max_ltv - buffer (e.g., 0.91 instead of 0.93)
        - Flash amount F = (λ/(1-λ)) * E
        - Supply S = E + F
        - Borrow B = min(F, λ*S - δ) where δ is safety buffer
        
        Atomic transaction:
        1. Flash borrow WETH = F
        2. Unwrap WETH → ETH (if needed)
        3. Stake ETH → weETH at Ether.fi
        4. Supply weETH to AAVE (receive aWeETH)
        5. Borrow WETH = B from AAVE
        6. Repay flash with B
        
        Result: Leveraged position in single tx (much lower gas!)
        """
        self.logger.info(f"⚡ Executing ATOMIC leverage (flash loan) at t=0...")
        
        # Calculate leverage sizing with buffer
        # Key: Flash loan must equal what we borrow (to repay it!)
        # Target LTV accounts for max expected adverse weETH/ETH oracle movement
        # target_ltv = max_ltv * (1 - max_stake_spread_move)
        ltv_target = self.config.max_ltv * (1 - self.config.max_stake_spread_move)
        E = equity_usd
        λ = ltv_target
        
        # Flash loan sizing: F = (λ/(1-λ)) * E
        # This is what we need to flash AND what we'll borrow
        F_usd = (λ / (1 - λ)) * E
        S_usd = E + F_usd
        
        # Borrow amount MUST equal flash amount (to repay it!)
        B_usd = F_usd
        
        # Verify LTV is within target
        actual_ltv = B_usd / S_usd if S_usd > 0 else 0
        if actual_ltv > self.config.max_ltv:
            self.logger.warning(f"   ⚠️ LTV {actual_ltv:.4f} exceeds max {self.config.max_ltv}!")
        
        self.logger.info(f"   📐 Leverage Math:")
        self.logger.info(f"      Equity (E): ${E:,.2f}")
        self.logger.info(f"      Target LTV (λ): {λ:.4f} (max {self.config.max_ltv} × (1 - {self.config.max_stake_spread_move:.4f}))")
        self.logger.info(f"      Max Stake Spread Move: {self.config.max_stake_spread_move*100:.3f}% (oracle risk buffer)")
        self.logger.info(f"      Flash (F): ${F_usd:,.2f}")
        self.logger.info(f"      Supply (S): ${S_usd:,.2f}")
        self.logger.info(f"      Borrow (B): ${B_usd:,.2f}")
        self.logger.info(f"      ✅ B = F (can repay flash exactly!)")
        
        # Get rates at t=0
        rates = self._get_rates_at_timestamp(timestamp)
        weeth_price = rates['weeth_price']
        
        # Convert to WETH/weETH units
        F_weth = F_usd / eth_price
        S_weth = S_usd / eth_price
        B_weth = B_usd / eth_price
        
        # weETH units = WETH / oracle_price
        S_weeth = S_weth / weeth_price
        
        # Use actual temporal gas cost data for atomic entry
        gas_atomic_usd = self._get_gas_cost_usd(timestamp, 'ATOMIC_ENTRY', eth_price)
        
        # Get gas cost in ETH for logging
        gas_data = self.data['gas_costs']
        gas_ts = gas_data.index.asof(timestamp)
        if not pd.isna(gas_ts) and 'ATOMIC_ENTRY_eth' in gas_data.columns:
            gas_cost_eth = gas_data.loc[gas_ts, 'ATOMIC_ENTRY_eth'] * self.config.gas_cost_multiplier
            gas_units = 1250000  # Standard atomic entry gas units
        else:
            # Fallback if enhanced data not available
            gas_units = 1250000
            gas_price_gwei = gas_data.loc[gas_ts, 'gas_price_avg_gwei'] if not pd.isna(gas_ts) else 12.0
            gas_cost_eth = (gas_units * gas_price_gwei * 1e9) / 1e18 * self.config.gas_cost_multiplier
            gas_atomic_usd = gas_cost_eth * eth_price
        
        # Flash fee (0 for Balancer/Morpho, ~5 bps for Aave)
        flash_fee_usd = (self.config.flash_fee_bps / 10000) * F_usd
        
        # Calculate final metrics FIRST (before creating JSON)
        collateral_value_weth = S_weeth * weeth_price
        net_position_weth = collateral_value_weth - B_weth
        net_position_usd = net_position_weth * eth_price
        
        # Health Factor: HF = (LT * collateral) / debt
        health_factor = (self.config.liquidation_threshold * collateral_value_weth) / B_weth if B_weth > 0 else float('inf')
        leverage_multiplier = collateral_value_weth / (equity_usd / eth_price)
        actual_ltv = B_weth / collateral_value_weth if collateral_value_weth > 0 else 0
        
        # Create atomic transaction details as JSON for audit trail
        atomic_tx_details = {
            'operations': [
                {'step': 1, 'action': 'FLASH_BORROW', 'venue': self.config.flash_source, 
                 'amount': f'{F_weth:.6f} WETH', 'usd_value': f'${F_usd:,.2f}'},
                {'step': 2, 'action': 'STAKE', 'venue': 'ETHERFI',
                 'input': f'{S_weth:.6f} ETH', 'output': f'{S_weeth:.6f} weETH', 
                 'oracle_price': f'{weeth_price:.6f}'},
                {'step': 3, 'action': 'SUPPLY', 'venue': 'AAVE',
                 'input': f'{S_weeth:.6f} weETH', 'output': f'{S_weeth:.6f} aWeETH'},
                {'step': 4, 'action': 'BORROW', 'venue': 'AAVE',
                 'amount': f'{B_weth:.6f} WETH', 'ltv': f'{λ:.4f}'},
                {'step': 5, 'action': 'FLASH_REPAID', 'venue': self.config.flash_source,
                 'amount': f'{F_weth:.6f} WETH', 'fee': f'${flash_fee_usd:.2f}'},
                {'step': 6, 'action': 'GAS_PAID', 
                 'amount': f'{gas_cost_eth:.6f} ETH', 'usd': f'${gas_atomic_usd:.2f}'}
            ],
            'net_result': {
                'weeth_collateral': f'{S_weeth:.6f}',
                'weth_debt': f'{B_weth:.6f}',
                'net_position_weth': f'{(S_weeth * weeth_price) - B_weth:.6f}',
                'leverage': f'{leverage_multiplier:.2f}x',
                'health_factor': f'{health_factor:.3f}',
                'ltv': f'{actual_ltv:.4f}'
            },
            'verification': {
                'flash_equals_borrow': bool(F_weth == B_weth),
                'can_repay_flash': bool(B_weth >= F_weth)
            }
        }
        
        # Log atomic transaction as a single bundled event with details
        self._log_event(timestamp, 'ATOMIC_TRANSACTION', 'INSTADAPP', 'COMPOSITE', 1,
                       transaction_type='ATOMIC_ENTRY',
                       atomic_details=json.dumps(atomic_tx_details),
                       flash_amount_weth=F_weth,
                       collateral_weeth=S_weeth,
                       debt_weth=B_weth,
                       gas_paid_eth=gas_cost_eth,
                       flash_fee_usd=flash_fee_usd,
                       note='Single atomic transaction containing 6 operations')
        
        # Also log individual operations for filtering
        self._log_event(timestamp, 'FLASH_BORROW', self.config.flash_source, 'WETH', F_weth,
                       amount_usd=F_usd, fee_bps=self.config.flash_fee_bps, transaction_type='ATOMIC_ENTRY')
        
        self._log_event(timestamp, 'STAKE_DEPOSIT', 'ETHERFI', 'ETH', S_weth,
                       output_token='weETH', amount_out=S_weeth,
                       oracle_price=weeth_price, transaction_type='ATOMIC_ENTRY')
        
        self._log_event(timestamp, 'COLLATERAL_SUPPLIED', 'AAVE', 'weETH', S_weeth,
                       collateral_type='supply_for_borrowing',
                       atoken_received='aWeETH', atoken_amount=S_weeth,
                       transaction_type='ATOMIC_ENTRY')
        
        self._log_event(timestamp, 'LOAN_CREATED', 'AAVE', 'WETH', B_weth,
                       debt_type='variable_rate', ltv=λ,
                       collateral_token='weETH', collateral_amount=S_weeth,
                       transaction_type='ATOMIC_ENTRY')
        
        self._log_event(timestamp, 'FLASH_REPAID', self.config.flash_source, 'WETH', F_weth,
                       amount_usd=F_usd, fee_usd=flash_fee_usd, transaction_type='ATOMIC_ENTRY')
        
        self._log_event(timestamp, 'GAS_FEE_PAID', 'ETHEREUM', 'ETH', gas_cost_eth,
                       fee_type='atomic_entry', fee_usd=gas_atomic_usd,
                       gas_units=gas_units, transaction_type='ATOMIC_ENTRY')
        
        # Verify minimum HF
        if health_factor < self.config.entry_hf_min:
            self.logger.warning(f"   ⚠️ Health factor {health_factor:.3f} below minimum {self.config.entry_hf_min}!")
        
        self.logger.info(f"   ✅ Atomic leverage completed:")
        self.logger.info(f"      Mode: FLASH LOAN (single transaction)")
        self.logger.info(f"      Flash Source: {self.config.flash_source}")
        self.logger.info(f"      Initial USD: ${equity_usd:,.2f}")
        self.logger.info(f"      weETH Collateral: {S_weeth:.4f} ({collateral_value_weth:.2f} WETH)")
        self.logger.info(f"      WETH Debt: {B_weth:.2f}")
        self.logger.info(f"      Net Position: {net_position_weth:.2f} WETH (${net_position_usd:,.2f})")
        self.logger.info(f"      Target LTV: {λ:.4f} (vs max {self.config.max_ltv})")
        self.logger.info(f"      Actual LTV: {(B_weth/collateral_value_weth):.4f}")
        self.logger.info(f"      Leverage: {leverage_multiplier:.2f}x")
        self.logger.info(f"      Health Factor: {health_factor:.3f} (min: {self.config.entry_hf_min})")
        self.logger.info(f"      Flash Fee: ${flash_fee_usd:.2f} ({self.config.flash_fee_bps} bps)")
        self.logger.info(f"      Gas Cost: ${gas_atomic_usd:.2f} (vs ${192:.2f} for 23-loop)")
        
        # Track venue positions
        venue_positions = {
            'etherfi': {'eth_staked': S_weth, 'weeth_received': S_weeth},
            'aave': {'weeth_collateral': S_weeth, 'weth_debt': B_weth, 'aweeth_balance': S_weeth}
        }
        
        return {
            'timestamp': timestamp,
            'iteration_count': 1,  # Single atomic transaction
            'mode': 'ATOMIC_FLASH',
            'flash_amount_usd': F_usd,
            'flash_fee_usd': flash_fee_usd,
            'weeth_collateral': S_weeth,
            'weth_debt': B_weth,
            'collateral_value_weth': collateral_value_weth,
            'net_position_weth': net_position_weth,
            'net_position_usd': net_position_usd,
            'long_eth_exposure': net_position_weth,
            'health_factor': health_factor,
            'leverage_multiplier': leverage_multiplier,
            'total_gas_costs_usd': gas_atomic_usd,
            'weeth_price': weeth_price,
            'ltv_target': λ,
            'ltv_actual': B_weth / collateral_value_weth if collateral_value_weth > 0 else 0,
            'venue_positions': venue_positions
        }
    
    def _open_perp_shorts(self, timestamp: pd.Timestamp, hedge_size_usd: float, eth_price: float) -> Dict:
        """Open short ETH perpetuals to hedge long exposure."""
        self.logger.info(f"📉 Opening perp shorts to hedge ${hedge_size_usd:,.2f} long exposure...")
        
        # Split across exchanges
        binance_notional = hedge_size_usd * self.config.binance_hedge_pct
        bybit_notional = hedge_size_usd * self.config.bybit_hedge_pct
        okx_notional = hedge_size_usd * self.config.okx_hedge_pct
        
        # PHASE 1 FIX: Get separate entry prices from respective futures data
        binance_futures = self.data['futures_prices']
        binance_futures_ts = binance_futures.index.asof(timestamp)
        if pd.isna(binance_futures_ts):
            binance_futures_ts = binance_futures.index[0]
        binance_entry_price = binance_futures.loc[binance_futures_ts, 'open']
        binance_entry_close = binance_futures.loc[binance_futures_ts, 'close']
        
        bybit_futures = self.data['bybit_futures']
        bybit_futures_ts = bybit_futures.index.asof(timestamp)
        if pd.isna(bybit_futures_ts):
            bybit_futures_ts = bybit_futures.index[0]
        bybit_entry_price = bybit_futures.loc[bybit_futures_ts, 'open']
        bybit_entry_close = bybit_futures.loc[bybit_futures_ts, 'close']
        
        # OKX futures prices (if available) - use Binance as proxy if not available
        if 'okx_futures' in self.data and self.data['okx_futures'] is not None:
            okx_futures = self.data['okx_futures']
            okx_futures_ts = okx_futures.index.asof(timestamp)
            if pd.isna(okx_futures_ts):
                okx_futures_ts = okx_futures.index[0]
            okx_entry_price = okx_futures.loc[okx_futures_ts, 'open']
            okx_entry_close = okx_futures.loc[okx_futures_ts, 'close']
        else:
            # Use Binance prices as proxy for OKX
            okx_entry_price = binance_entry_price
            okx_entry_close = binance_entry_close
        
        # Get execution costs for perp trades
        binance_exec_cost_bps = self._get_execution_cost(timestamp, 'ETHUSDT-PERP', binance_notional, 'BINANCE_PERP')
        binance_exec_cost = binance_notional * (binance_exec_cost_bps / 10000)
        
        bybit_exec_cost_bps = self._get_execution_cost(timestamp, 'ETHUSDT-PERP', bybit_notional, 'BYBIT_PERP')
        bybit_exec_cost = bybit_notional * (bybit_exec_cost_bps / 10000)
        
        okx_exec_cost_bps = self._get_execution_cost(timestamp, 'ETHUSDT-PERP', okx_notional, 'OKX_PERP')
        okx_exec_cost = okx_notional * (okx_exec_cost_bps / 10000)
        
        total_exec_costs = binance_exec_cost + bybit_exec_cost + okx_exec_cost
        
        # Calculate position sizes using respective exchange prices
        binance_eth_short = binance_notional / binance_entry_price
        bybit_eth_short = bybit_notional / bybit_entry_price
        okx_eth_short = okx_notional / okx_entry_price
        
        # Log events with correct entry prices
        self._log_event(timestamp, 'TRADE_EXECUTED', 'BINANCE', 'ETH', binance_eth_short,
                       side='SHORT', notional_usd=binance_notional, instrument='ETHUSDT-PERP',
                       entry_price=binance_entry_price, entry_price_close=binance_entry_close, execution_cost_usd=binance_exec_cost,
                       execution_cost_bps=binance_exec_cost_bps)
        
        self._log_event(timestamp, 'TRADE_EXECUTED', 'BYBIT', 'ETH', bybit_eth_short,
                       side='SHORT', notional_usd=bybit_notional, instrument='ETHUSDT-PERP',
                       entry_price=bybit_entry_price, entry_price_close=bybit_entry_close, execution_cost_usd=bybit_exec_cost,
                       execution_cost_bps=bybit_exec_cost_bps)
        
        self._log_event(timestamp, 'TRADE_EXECUTED', 'OKX', 'ETH', okx_eth_short,
                       side='SHORT', notional_usd=okx_notional, instrument='ETHUSDT-PERP',
                       entry_price=okx_entry_price, entry_price_close=okx_entry_close, execution_cost_usd=okx_exec_cost,
                       execution_cost_bps=okx_exec_cost_bps)
        
        self.logger.info(f"   Binance: Short {binance_eth_short:.4f} ETH @ ${binance_entry_price:,.2f} (${binance_notional:,.2f})")
        self.logger.info(f"   Binance Exec Cost: ${binance_exec_cost:.2f} ({binance_exec_cost_bps} bps)")
        self.logger.info(f"   Bybit: Short {bybit_eth_short:.4f} ETH @ ${bybit_entry_price:,.2f} (${bybit_notional:,.2f})")
        self.logger.info(f"   Bybit Exec Cost: ${bybit_exec_cost:.2f} ({bybit_exec_cost_bps} bps)")
        self.logger.info(f"   OKX: Short {okx_eth_short:.4f} ETH @ ${okx_entry_price:,.2f} (${okx_notional:,.2f})")
        self.logger.info(f"   OKX Exec Cost: ${okx_exec_cost:.2f} ({okx_exec_cost_bps} bps)")
        self.logger.info(f"   Total Short: {binance_eth_short + bybit_eth_short + okx_eth_short:.4f} ETH")
        self.logger.info(f"   Total Exec Costs: ${total_exec_costs:.2f}")
        self.logger.info(f"   Price Differences: Binance vs Bybit = ${binance_entry_price - bybit_entry_price:+.2f}, Binance vs OKX = ${binance_entry_price - okx_entry_price:+.2f}")
        
        # Calculate required margin (initial margin ratio)
        binance_margin_required = binance_notional * self.config.initial_margin_ratio
        bybit_margin_required = bybit_notional * self.config.initial_margin_ratio
        okx_margin_required = okx_notional * self.config.initial_margin_ratio
        total_margin_required = binance_margin_required + bybit_margin_required + okx_margin_required
        
        # Initial margin locked (from  hedge capital, after execution costs)
        binance_margin_locked = binance_margin_required
        bybit_margin_locked = bybit_margin_required
        okx_margin_locked = okx_margin_required
        
        self.logger.info(f"   💰 Margin Locked:")
        self.logger.info(f"      Binance: ${binance_margin_locked:,.2f} ({self.config.initial_margin_ratio*100:.0f}% of ${binance_notional:,.0f})")
        self.logger.info(f"      Bybit: ${bybit_margin_locked:,.2f} ({self.config.initial_margin_ratio*100:.0f}% of ${bybit_notional:,.0f})")
        self.logger.info(f"      OKX: ${okx_margin_locked:,.2f} ({self.config.initial_margin_ratio*100:.0f}% of ${okx_notional:,.0f})")
        self.logger.info(f"      Total: ${total_margin_required:,.2f}")
        
        # Store short positions with ETH amounts and separate entry prices for M2M calculation
        short_position_data = {
            'binance': {
                'eth_short': binance_eth_short,
                'notional_usd': binance_notional,
                'entry_price': binance_entry_price,  # PHASE 1 FIX: Binance-specific price
                'margin_posted': binance_margin_locked,
                'exec_cost': binance_exec_cost,
                'entry_price_close': binance_entry_close
            },
            'bybit': {
                'eth_short': bybit_eth_short,
                'notional_usd': bybit_notional,
                'entry_price': bybit_entry_price,  # PHASE 1 FIX: Bybit-specific price
                'margin_posted': bybit_margin_locked,
                'exec_cost': bybit_exec_cost,
                'entry_price_close': bybit_entry_close
            },
            'okx': {
                'eth_short': okx_eth_short,
                'notional_usd': okx_notional,
                'entry_price': okx_entry_price,  # OKX-specific price
                'margin_posted': okx_margin_locked,
                'exec_cost': okx_exec_cost,
                'entry_price_close': okx_entry_close
            },
            'total_eth_short': binance_eth_short + bybit_eth_short + okx_eth_short,
            'total_notional_usd': hedge_size_usd,
            'total_margin_posted': total_margin_required,
            'total_exec_costs': total_exec_costs
            # REMOVED: Single 'entry_price' field (now stored per exchange)
        }
        
        return short_position_data
    
    def _calculate_funding_costs(self, timestamp: pd.Timestamp, short_positions: Dict) -> Dict:
        """
        Calculate funding P&L (paid every 8 hours at 00:00, 08:00, 16:00 UTC).
        
        IMPORTANT: Positive funding rate = longs pay shorts = shorts RECEIVE
                   Negative funding rate = shorts pay longs = shorts PAY
        
        So funding_pnl = notional * funding_rate (positive = gain for shorts)
        """
        hour = timestamp.hour
        if hour not in [0, 8, 16]:
            return {
                'total_funding_pnl_usd': 0.0,
                'binance_pnl': 0.0,
                'bybit_pnl': 0.0,
                'okx_pnl': 0.0,
                'binance_rate': 0.0,
                'bybit_rate': 0.0,
                'okx_rate': 0.0
            }
        
        # Get rates
        binance_fr = self._get_funding_rate(timestamp)
        bybit_fr = self._get_bybit_funding_rate(timestamp)
        okx_fr = self._get_okx_funding_rate(timestamp)
        
        # Calculate P&L (positive funding = shorts receive = positive P&L)
        binance_pnl = short_positions['binance']['notional_usd'] * binance_fr
        bybit_pnl = short_positions['bybit']['notional_usd'] * bybit_fr
        okx_pnl = short_positions['okx']['notional_usd'] * okx_fr
        
        # Log funding payments
        if binance_pnl != 0:
            pnl_type = 'RECEIVED' if binance_pnl > 0 else 'PAID'
            self._log_event(timestamp, 'FUNDING_PAYMENT', 'BINANCE', 'USDT', abs(binance_pnl),
                           funding_rate=binance_fr, pnl_type=pnl_type, pnl_usd=binance_pnl,
                           instrument='ETHUSDT-PERP')
        
        if bybit_pnl != 0:
            pnl_type = 'RECEIVED' if bybit_pnl > 0 else 'PAID'
            self._log_event(timestamp, 'FUNDING_PAYMENT', 'BYBIT', 'USDT', abs(bybit_pnl),
                           funding_rate=bybit_fr, pnl_type=pnl_type, pnl_usd=bybit_pnl,
                           instrument='ETHUSDT-PERP')
        
        if okx_pnl != 0:
            pnl_type = 'RECEIVED' if okx_pnl > 0 else 'PAID'
            self._log_event(timestamp, 'FUNDING_PAYMENT', 'OKX', 'USDT', abs(okx_pnl),
                           funding_rate=okx_fr, pnl_type=pnl_type, pnl_usd=okx_pnl,
                           instrument='ETHUSDT-PERP')
        
        return {
            'total_funding_pnl_usd': binance_pnl + bybit_pnl + okx_pnl,
            'binance_pnl': binance_pnl,
            'bybit_pnl': bybit_pnl,
            'okx_pnl': okx_pnl,
            'binance_rate': binance_fr,
            'bybit_rate': bybit_fr,
            'okx_rate': okx_fr
        }
    
    def run_analysis(self, start_date: str = "2024-05-12", end_date: str = "2025-09-18") -> Dict:
        """Run the USDT market-neutral leveraged restaking analysis."""
        self.logger.info("=" * 80)
        self.logger.info("🚀 USDT MARKET-NEUTRAL LEVERAGED RESTAKING ANALYSIS")
        self.logger.info("=" * 80)
        self.logger.info(f"📅 Date range: {start_date} to {end_date}")
        self.logger.info(f"💰 Initial USDT: ${self.config.initial_usdt:,.2f}")
        self.logger.info(f"📊 Allocation: {self.config.allocation_to_long_pct*100:.0f}% long restaking, {(1-self.config.allocation_to_long_pct)*100:.0f}% short hedge")
        self.logger.info("=" * 80)
        
        # Load data
        self._load_data()
        
        # Create timestamp range
        start_ts = pd.to_datetime(start_date).tz_localize('UTC')
        end_ts = pd.to_datetime(end_date).tz_localize('UTC')
        timestamps = pd.date_range(start=start_ts, end=end_ts, freq='H')
        
        self.logger.info(f"📊 Total time periods: {len(timestamps)} hours")
        self.logger.info("")
        
        # STEP 1: Initialize positions at t=0
        self.logger.info("STEP 1: Fund CEX accounts and execute spot + perp simultaneously")
        self.logger.info("-" * 50)
        
        t0 = timestamps[0]
        eth_price_spot = self._get_spot_price(t0)
        
        # Split capital
        long_capital_usd = self.config.initial_usdt * self.config.allocation_to_long_pct
        hedge_capital_usd = self.config.initial_usdt * (1 - self.config.allocation_to_long_pct)
        
        self.logger.info(f"  ETH Spot Price: ${eth_price_spot:,.2f}")
        self.logger.info(f"  Long Capital (for spot): ${long_capital_usd:,.2f}")
        self.logger.info(f"  Hedge Capital (for perps): ${hedge_capital_usd:,.2f}")
        self.logger.info("")
        
        # Calculate capital allocation to CEXs
        binance_total_usdt = long_capital_usd + (hedge_capital_usd * self.config.binance_hedge_pct)
        bybit_total_usdt = hedge_capital_usd * self.config.bybit_hedge_pct
        
        self.logger.info(f"  💸 Capital Allocation to CEXs:")
        self.logger.info(f"     Binance: ${binance_total_usdt:,.2f} (${long_capital_usd:,.2f} spot + ${hedge_capital_usd * self.config.binance_hedge_pct:,.2f} perp)")
        self.logger.info(f"     Bybit: ${bybit_total_usdt:,.2f} (perp only)")
        self.logger.info("")
        
        # Step 1a: Send USDT to Binance (gas paid)
        binance_transfer_gas = self._get_gas_cost_usd(t0, 'VENUE_TRANSFER', eth_price_spot)
        self._log_event(t0, 'GAS_FEE_PAID', 'ETHEREUM', 'ETH', binance_transfer_gas / eth_price_spot,
                       fee_type='venue_transfer', related_transaction='usdt_to_binance',
                       fee_usd=binance_transfer_gas, direction='USDT_to_BINANCE',
                       amount_usd=binance_total_usdt)
        
        # Step 1b: Send USDT to Bybit (gas paid)
        bybit_transfer_gas = self._get_gas_cost_usd(t0, 'VENUE_TRANSFER', eth_price_spot)
        self._log_event(t0, 'GAS_FEE_PAID', 'ETHEREUM', 'ETH', bybit_transfer_gas / eth_price_spot,
                       fee_type='venue_transfer', related_transaction='usdt_to_bybit',
                       fee_usd=bybit_transfer_gas, direction='USDT_to_BYBIT',
                       amount_usd=bybit_total_usdt)
        
        total_usdt_transfer_gas = binance_transfer_gas + bybit_transfer_gas
        
        self.logger.info(f"  ⛽ Gas to fund CEX accounts:")
        self.logger.info(f"     USDT → Binance: ${binance_transfer_gas:.2f}")
        self.logger.info(f"     USDT → Bybit: ${bybit_transfer_gas:.2f}")
        self.logger.info(f"     Total: ${total_usdt_transfer_gas:.2f}")
        self.logger.info("")
        
        # Step 2: Execute spot + perps SIMULTANEOUSLY on Binance
        self.logger.info(f"  🔄 Simultaneous Execution on Binance:")
        self.logger.info(f"     Buy ${long_capital_usd:,.2f} ETH spot")
        self.logger.info(f"     Short ${hedge_capital_usd * self.config.binance_hedge_pct:,.2f} perp")
        self.logger.info(f"     (Executed together - delta neutral from start!)")
        
        # Buy ETH spot (with execution costs, but NO additional transfer gas - already at Binance!)
        exec_cost_bps = self._get_execution_cost(t0, 'ETH/USDT', long_capital_usd, self.config.spot_venue)
        spot_exec_cost = long_capital_usd * (exec_cost_bps / 10000)
        net_usdt = long_capital_usd - spot_exec_cost
        eth_bought_at_binance = net_usdt / eth_price_spot
        
        self._log_event(t0, 'SPOT_TRADE', self.config.spot_venue, 'ETH', eth_bought_at_binance,
                       side='BUY', usdt_spent=long_capital_usd, usdt_net=net_usdt,
                       execution_cost_usd=spot_exec_cost, execution_cost_bps=exec_cost_bps,
                       eth_price=eth_price_spot)
        
        self.logger.info(f"     Spot execution cost: ${spot_exec_cost:.2f} ({exec_cost_bps} bps)")
        self.logger.info(f"     ETH received: {eth_bought_at_binance:.4f} ETH")
        
        # Step 3: Transfer ETH back to wallet
        # CEX deducts gas from the transfer amount (not paid separately)
        eth_return_transfer_gas = self._get_gas_cost_usd(t0, 'VENUE_TRANSFER', eth_price_spot)
        eth_transfer_fee_eth = eth_return_transfer_gas / eth_price_spot
        
        # Actual ETH received = ETH bought - gas fee deducted by CEX
        eth_received_in_wallet = eth_bought_at_binance - eth_transfer_fee_eth
        
        self._log_event(t0, 'GAS_FEE_PAID', 'ETHEREUM', 'ETH', eth_transfer_fee_eth,
                       fee_type='venue_transfer', related_transaction='eth_from_binance',
                       fee_usd=eth_return_transfer_gas, direction='ETH_from_BINANCE',
                       amount_eth=eth_bought_at_binance, eth_received=eth_received_in_wallet,
                       note='CEX deducts gas from transfer amount')
        
        self.logger.info(f"     Gas deducted by CEX: ${eth_return_transfer_gas:.2f}")
        self.logger.info(f"     ETH sent: {eth_bought_at_binance:.6f} ETH")
        self.logger.info(f"     ETH received in wallet: {eth_received_in_wallet:.6f} ETH")
        self.logger.info(f"     (CEX deducted {eth_transfer_fee_eth:.6f} ETH as network fee)")
        
        # Total gas for USDT transfers + ETH return
        spot_transfer_gas = total_usdt_transfer_gas + eth_return_transfer_gas
        
        self.logger.info("")
        leverage_mode = "ATOMIC FLASH LOAN" if self.config.use_flash_one_shot else "RECURSIVE LOOP (23 iterations)"
        self.logger.info(f"STEP 2: Execute leverage - {leverage_mode}")
        self.logger.info("-" * 50)
        
        # Execute leverage loop with the ETH we ACTUALLY received (after all deductions)
        # ETH in wallet = eth_bought - spot_exec_cost equivalent - CEX withdrawal fee
        actual_eth_in_wallet = eth_received_in_wallet
        long_capital_net = actual_eth_in_wallet * eth_price_spot
        
        if self.config.use_flash_one_shot:
            # Atomic flash loan entry (single transaction)
            long_position = self._execute_leverage_one_shot_usd(t0, long_capital_net, eth_price_spot)
        else:
            # Recursive loop entry (23 separate transactions)
            long_position = self._execute_leverage_loop_usd(t0, long_capital_net, eth_price_spot)
        
        self.logger.info("")
        self.logger.info("STEP 3: Open perp shorts (executed simultaneously with spot at t=0)")
        self.logger.info("-" * 50)
        
        # CRITICAL: Hedge the INITIAL ETH purchased, not the net position!
        # The initial ETH is the only net exposure - all borrows cancel out when re-staked
        initial_eth_purchased = long_capital_usd / eth_price_spot
        actual_hedge_usd = initial_eth_purchased * eth_price_spot
        
        self.logger.info(f"  Initial ETH purchased: {initial_eth_purchased:.4f} ETH")
        self.logger.info(f"  Net position after leverage: {long_position['long_eth_exposure']:.4f} ETH")
        self.logger.info(f"  Hedging initial purchase: {initial_eth_purchased:.4f} ETH (${actual_hedge_usd:,.2f})")
        self.logger.info("")
        self.logger.info(f"  ⏱️  Timing: Spot + Perp executed SIMULTANEOUSLY")
        self.logger.info(f"     → Avoids timing risk between long and short entries")
        self.logger.info(f"     → Execution costs (~10 bps) account for simultaneous fill")
        self.logger.info(f"     → Delta neutral from moment of entry! ✅")
        
        short_positions = self._open_perp_shorts(t0, actual_hedge_usd, eth_price_spot)
        
        # Verify market neutrality (should hedge initial purchase)
        net_delta_eth = initial_eth_purchased - short_positions['total_eth_short']
        delta_pct = (net_delta_eth / initial_eth_purchased) * 100 if initial_eth_purchased > 0 else 0
        
        self.logger.info("")
        self.logger.info("⚖️  MARKET NEUTRALITY CHECK:")
        self.logger.info(f"   Initial ETH (long): {initial_eth_purchased:.4f} ETH")
        self.logger.info(f"   Short ETH Position: {short_positions['total_eth_short']:.4f} ETH")
        self.logger.info(f"   Net Delta:          {net_delta_eth:+.4f} ETH ({delta_pct:+.2f}%)")
        if abs(delta_pct) < 1:
            self.logger.info("   ✅ Market neutral (delta < 1%)")
        else:
            self.logger.warning(f"   ⚠️  Delta > 1%! Hedge sizing may need adjustment")
        
        self.logger.info("")
        self.logger.info("STEP 4: Track positions hourly with P&L")
        self.logger.info("-" * 50)
        
        # Store initial position for reference
        initial_long_position = long_position.copy()
        
        # Track position through time
        hourly_pnl = []
        
        # Track cumulative P&L components
        cumulative_supply_pnl_usd = 0.0
        cumulative_borrow_cost_usd = 0.0
        cumulative_price_change_pnl_usd = 0.0
        cumulative_funding_cost_usd = 0.0
        cumulative_perp_mtm_pnl_usd = 0.0  # Total unrealized P&L on short perps
        cumulative_ethena_pnl_usd = 0.0  # Ethena benchmark P&L
        cumulative_binance_perp_mtm_usd = 0.0  # Binance-specific cumulative
        cumulative_bybit_perp_mtm_usd = 0.0  # Bybit-specific cumulative
        cumulative_okx_perp_mtm_usd = 0.0  # OKX-specific cumulative
        cumulative_transaction_costs_pnl_usd = 0.0  # Entry costs (gas + execution)
        cumulative_net_pnl_usd = 0.0
        
        # PHASE 2.5: Track AAVE positions using exact AAVE v3 mechanics
        # Scaled balances are CONSTANT (ERC-20 token balances)
        # Underlying values calculated using indices each hour
        
        # Get initial indices
        rates_t0 = self._get_rates_at_timestamp(t0)
        weth_rates_t0 = self.data['weth_rates']
        weth_ts = weth_rates_t0.index.asof(t0)
        if pd.isna(weth_ts):
            weth_ts = weth_rates_t0.index[0]
        
        # PHASE 2.5: Indices in our data are already normalized (~1.0, not 10^27!)
        initial_liquidity_index_weeth = rates_t0['liquidityIndex'] if 'liquidityIndex' in rates_t0 else 1.0
        initial_borrow_index_weth = weth_rates_t0.loc[weth_ts, 'variableBorrowIndex'] if 'variableBorrowIndex' in weth_rates_t0.columns else 1.0
        
        # Calculate CONSTANT scaled balances (AAVE ERC-20 token amounts)
        # Formula: scaledBalance = underlyingAmount / index (data already normalized!)
        initial_weeth = long_position['weeth_collateral']
        initial_weth_debt = long_position['weth_debt']
        
        aweeth_scaled_balance = initial_weeth / initial_liquidity_index_weeth
        weth_debt_scaled_balance = initial_weth_debt / initial_borrow_index_weth
        
        # These NEVER change (constant ERC-20 balances)
        # What changes: The indices (liquidityIndex, variableBorrowIndex)
        
        # Calculate initial underlying amounts (should equal long_position values)
        weeth_collateral = aweeth_scaled_balance * initial_liquidity_index_weeth
        weth_debt = weth_debt_scaled_balance * initial_borrow_index_weth
        weeth_price = long_position['weeth_price']
        
        # For display: aWeETH balance is the scaled balance (what wallet shows)
        aweeth_balance = aweeth_scaled_balance
        
        # Initialize old values for P&L calculation (first iteration will have zero P&L)
        # Use underlying values (without seasonal rewards) for consistent P&L tracking
        weeth_collateral_underlying = weeth_collateral  # Initially same as collateral
        weth_debt_underlying = weth_debt  # Initially same as debt
        old_weeth_collateral_underlying = weeth_collateral_underlying
        old_weth_debt_underlying = weth_debt_underlying
        old_weeth_price = weeth_price
        
        # Track ETH balance for gas fees
        # Starts at 0 (no pre-funding), goes negative as gas is paid
        # This creates an "ETH debt" we'd need to cover in practice
        
        # Calculate total gas paid in ETH from all operations
        gas_events_df = pd.DataFrame([e for e in self.event_log if e['event_type'] == 'GAS_FEE_PAID'])
        total_gas_eth = gas_events_df['amount'].sum() if len(gas_events_df) > 0 else 0.0
        
        # ETH balance starts at 0, gas makes it negative
        eth_balance_for_gas = -total_gas_eth  # Negative = we owe this ETH
        cumulative_gas_paid_eth = total_gas_eth
        
        # Track costs separately for rebalancing analysis
        # Gas costs (all on-chain operations)
        # Includes: USDT transfers to CEXs + leverage loop + ETH return transfer
        cumulative_gas_costs_usd = initial_long_position['total_gas_costs_usd'] + spot_transfer_gas
        
        # Execution costs (trading slippage/fees)
        cumulative_execution_costs_usd = spot_exec_cost + short_positions['total_exec_costs']
        
        # Total transaction costs (gas + execution)
        total_transaction_costs = cumulative_gas_costs_usd + cumulative_execution_costs_usd
        
        # Track previous values for delta P&L calculation
        prev_eth_price = eth_price_spot
        prev_net_delta_eth = 0.0  # Start at 0 delta
        cumulative_delta_pnl_usd = 0.0
        
        # PHASE 1.5 FIX: Track TOTAL CEX account balances (not just required margin)
        # Initial account balance = capital deposited - execution costs
        binance_account_balance = (hedge_capital_usd * self.config.binance_hedge_pct) - short_positions['binance']['exec_cost']
        bybit_account_balance = (hedge_capital_usd * self.config.bybit_hedge_pct) - short_positions['bybit']['exec_cost']
        okx_account_balance = (hedge_capital_usd * self.config.okx_hedge_pct) - short_positions['okx']['exec_cost']
        
        # For reference: required margin is only 15% of exposure
        binance_required_margin_initial = short_positions['binance']['notional_usd'] * self.config.initial_margin_ratio
        bybit_required_margin_initial = short_positions['bybit']['notional_usd'] * self.config.initial_margin_ratio
        
        # PHASE 2.5: Calculate TOTAL initial value (all venues) using UNDERLYING values
        # Total Value = CEX Balances + ETH Wallet Assets - AAVE Debt - ETH Gas Debt
        initial_cex_balance_usd = binance_account_balance + bybit_account_balance  # USDT in CEX
        
        # ETH Wallet Assets: aTokens valued using AAVE formula
        # Value = scaledBalance × liquidityIndex × oracle × ETH/USD
        # NOTE: Indices already normalized in our data (~1.0), no 1e27 division needed!
        initial_eth_wallet_assets_usd = (aweeth_scaled_balance * initial_liquidity_index_weeth * 
                                         weeth_price * eth_price_spot)
        
        # AAVE Debt: debt tokens valued using AAVE formula
        # Debt = scaledBalance × borrowIndex × ETH/USD
        initial_aave_debt_usd = (weth_debt_scaled_balance * initial_borrow_index_weth * 
                                 eth_price_spot)
        
        # ETH Gas Debt
        initial_eth_gas_debt_usd = -eth_balance_for_gas * eth_price_spot  # ETH owed for gas (positive value)
        
        initial_total_value_usd = (initial_cex_balance_usd + initial_eth_wallet_assets_usd - 
                                   initial_aave_debt_usd - initial_eth_gas_debt_usd)
        initial_total_value_pre_cost_usd = initial_total_value_usd + total_transaction_costs
        
        # For backwards compatibility and reporting
        initial_aave_net_usd = initial_long_position['net_position_usd']
        initial_net_position_usd = initial_aave_net_usd
        
        self.logger.info(f"   📊 Initial Cost Breakdown:")
        self.logger.info(f"      Gas (transfers): ${spot_transfer_gas:.2f}")
        self.logger.info(f"      Gas (leverage loop): ${initial_long_position['total_gas_costs_usd']:.2f}")
        self.logger.info(f"      Execution (spot): ${spot_exec_cost:.2f}")
        self.logger.info(f"      Execution (perps): ${short_positions['total_exec_costs']:.2f}")
        self.logger.info(f"      TOTAL: ${total_transaction_costs:.2f}")
        
        # Initialize balance sheet history for tracking P&L jumps
        initial_balance_component = {
            'timestamp': t0,
            'net_aave_position_usd': initial_net_position_usd,
            'net_aave_position_weth': initial_long_position['net_position_weth'],
            'weeth_collateral_value_weth': initial_long_position['collateral_value_weth'],
            'weeth_collateral_value_usd': initial_long_position['collateral_value_weth'] * eth_price_spot,
            'weth_debt_value_weth': initial_long_position['weth_debt'],
            'weth_debt_value_usd': initial_long_position['weth_debt'] * eth_price_spot,
            'weeth_price': initial_long_position['weeth_price'],
            'eth_price': eth_price_spot,
            'binance_balance_usd': binance_account_balance,
            'bybit_balance_usd': bybit_account_balance,
            'total_cex_balance_usd': initial_cex_balance_usd,
            'eth_gas_debt_eth': eth_balance_for_gas,
            'eth_gas_debt_usd': initial_eth_gas_debt_usd,
            'total_value_usd': initial_total_value_usd,
            'balance_pnl_usd': initial_total_value_usd - initial_total_value_pre_cost_usd
        }
        balance_sheet_history = [initial_balance_component]
        
        for i, timestamp in enumerate(timestamps[1:], start=1):
            if i % 1000 == 0:
                self.logger.info(f"Processing hour {i}/{len(timestamps)}: {timestamp}")
            
            # Get current prices/rates
            eth_price = self._get_spot_price(timestamp)
            rates = self._get_rates_at_timestamp(timestamp)
            staking_yields = self._get_staking_yield_at_timestamp(timestamp)
            
            # Get Ethena benchmark APR for this hour
            ethena_apr = self._get_ethena_apr_at_timestamp(timestamp)
            
            # PHASE 2.5: Get current AAVE indices for exact mechanics
            # NOTE: Indices in our data are already normalized (~1.0), not raw 10^27 values!
            current_liquidity_index_weeth = rates['liquidityIndex'] if 'liquidityIndex' in rates else 1.0
            
            # Get WETH variable borrow index
            weth_rates_data = self.data['weth_rates']
            weth_ts = weth_rates_data.index.asof(timestamp)
            if pd.isna(weth_ts):
                weth_ts = weth_rates_data.index[0]
            current_borrow_index_weth = weth_rates_data.loc[weth_ts, 'variableBorrowIndex'] if 'variableBorrowIndex' in weth_rates_data.columns else 1.0
            
            # PHASE 2.5: Calculate underlying amounts using AAVE indices
            # Scaled balances (aweeth_scaled_balance, weth_debt_scaled_balance) are CONSTANT
            # Underlying = scaledBalance × index (data already normalized, no 1e27 division!)
            weeth_collateral_underlying = aweeth_scaled_balance * current_liquidity_index_weeth
            weth_debt_underlying = weth_debt_scaled_balance * current_borrow_index_weth
            
            # Use actual hourly weETH price changes instead of interpolated daily yields
            # This eliminates the jumpiness caused by daily yield interpolation
            weeth_collateral = weeth_collateral_underlying  # No seasonal adjustment - price changes are captured in weeth_price
            weth_debt = weth_debt_underlying  # Debt doesn't get seasonal adjustments
            
            # Update weETH/ETH oracle price
            weeth_price = rates['weeth_price']
            
            # Calculate collateral and debt values in WETH
            old_collateral_value_weth = old_weeth_collateral_underlying * old_weeth_price
            old_debt_value_weth = old_weth_debt_underlying
            new_collateral_value_weth = weeth_collateral * weeth_price
            new_debt_value_weth = weth_debt
            
            # Calculate LONG side P&L (in WETH, then convert to USD)
            # 1. AAVE supply yield (from index growth)
            supply_pnl_weth = (weeth_collateral_underlying - old_weeth_collateral_underlying) * old_weeth_price
            
            # 2. No seasonal rewards - all yield captured in weETH price changes
            seasonal_pnl_weth = 0.0
            
            # 3. Borrow cost (from borrow index growth)
            borrow_cost_weth = weth_debt_underlying - old_weth_debt_underlying
            
            # 4. weETH/ETH oracle price appreciation (base staking)
            # This is the non-rebasing yield (oracle price grows)
            price_change_pnl_weth = weeth_collateral * (weeth_price - old_weeth_price)
            
            # Update aWeETH balance display (scaled balance is constant)
            aweeth_balance = aweeth_scaled_balance  # Never changes!
            
            # Convert to USD
            supply_pnl_usd = supply_pnl_weth * eth_price
            seasonal_pnl_usd = 0.0  # No seasonal rewards
            borrow_cost_usd = borrow_cost_weth * eth_price
            price_change_pnl_usd = price_change_pnl_weth * eth_price
            
            # Calculate Ethena benchmark hourly P&L (on same initial notional for fair comparison)
            ethena_hourly_pnl_usd = initial_total_value_usd * (ethena_apr / (365 * 24))
            
            # DETAILED LOGGING: Token balances and P&L contributions
            if timestamp.hour == 0:  # Log once per day at midnight
                self.logger.info(f"🔍 DETAILED TOKEN BALANCE ANALYSIS - {timestamp.strftime('%Y-%m-%d %H:%M')}")
                self.logger.info(f"   📊 AAVE TOKEN BALANCES:")
                self.logger.info(f"      aWeETH Scaled Balance: {aweeth_scaled_balance:.6f} (CONSTANT)")
                self.logger.info(f"      WETH Debt Scaled Balance: {weth_debt_scaled_balance:.6f} (CONSTANT)")
                self.logger.info(f"      weETH Collateral Underlying: {weeth_collateral_underlying:.6f}")
                self.logger.info(f"      WETH Debt Underlying: {weth_debt_underlying:.6f}")
                self.logger.info(f"      AAVE Liquidity Index: {rates.get('liquidityIndex', 'N/A')}")
                self.logger.info(f"      AAVE Borrow Index: {rates.get('variableBorrowIndex', 'N/A')}")
                self.logger.info(f"      Available rate keys: {list(rates.keys())}")
                self.logger.info(f"   🔍 INDEX COMPARISON:")
                self.logger.info(f"      Initial Liquidity Index: {initial_liquidity_index_weeth:.6f}")
                self.logger.info(f"      Current Liquidity Index: {current_liquidity_index_weeth:.6f}")
                self.logger.info(f"      Initial Borrow Index: {initial_borrow_index_weth:.6f}")
                self.logger.info(f"      Current Borrow Index: {current_borrow_index_weth:.6f}")
                self.logger.info(f"   💰 P&L CONTRIBUTIONS (USD):")
                self.logger.info(f"      Supply P&L: ${supply_pnl_usd:.6f}")
                self.logger.info(f"      Borrow Cost: ${borrow_cost_usd:.6f}")
                self.logger.info(f"      Price Change P&L: ${price_change_pnl_usd:.6f}")
                # No seasonal P&L logging
                self.logger.info(f"   📈 GROWTH FACTORS:")
                self.logger.info(f"      Supply Growth Factor: {rates['weeth_supply_growth_factor']:.10f}")
                self.logger.info(f"      Borrow Growth Factor: {rates['weth_borrow_growth_factor']:.10f}")
                self.logger.info(f"   🔢 CALCULATION BREAKDOWN:")
                self.logger.info(f"      Old weETH Collateral Underlying: {old_weeth_collateral_underlying:.6f}")
                self.logger.info(f"      New weETH Collateral Underlying: {weeth_collateral_underlying:.6f}")
                self.logger.info(f"      Collateral Difference: {weeth_collateral_underlying - old_weeth_collateral_underlying:.10f}")
                self.logger.info(f"      Old WETH Debt Underlying: {old_weth_debt_underlying:.6f}")
                self.logger.info(f"      New WETH Debt Underlying: {weth_debt_underlying:.6f}")
                self.logger.info(f"      Debt Difference: {weth_debt_underlying - old_weth_debt_underlying:.10f}")
                self.logger.info("")
            
            # No seasonal rewards in attribution P&L
            long_pnl_usd = supply_pnl_usd + price_change_pnl_usd - borrow_cost_usd
            
            # Calculate SHORT side P&L
            funding_pnl = self._calculate_funding_costs(timestamp, short_positions)
            
            # PHASE 1 FIX: Get current mark prices for each exchange
            binance_futures = self.data['futures_prices']
            binance_futures_ts = binance_futures.index.asof(timestamp)
            if pd.isna(binance_futures_ts):
                binance_futures_ts = binance_futures.index[0]
            binance_mark_price = binance_futures.loc[binance_futures_ts, 'open']
            binance_mark_close = binance_futures.loc[binance_futures_ts, 'close']
            
            bybit_futures = self.data['bybit_futures']
            bybit_futures_ts = bybit_futures.index.asof(timestamp)
            if pd.isna(bybit_futures_ts):
                bybit_futures_ts = bybit_futures.index[0]
            bybit_mark_price = bybit_futures.loc[bybit_futures_ts, 'open']
            bybit_mark_close = bybit_futures.loc[bybit_futures_ts, 'close']
            
            # OKX futures prices (if available) - use when available, fallback to Binance proxy
            if 'okx_futures' in self.data and self.data['okx_futures'] is not None:
                okx_futures = self.data['okx_futures']
                okx_futures_ts = okx_futures.index.asof(timestamp)
                if pd.isna(okx_futures_ts):
                    # No OKX data for this timestamp, use Binance as proxy
                    okx_mark_price = binance_mark_price
                    okx_mark_close = binance_mark_close
                else:
                    okx_mark_price = okx_futures.loc[okx_futures_ts, 'open']
                    okx_mark_close = okx_futures.loc[okx_futures_ts, 'close']
            else:
                # No OKX futures data available, use Binance as proxy
                okx_mark_price = binance_mark_price
                okx_mark_close = binance_mark_close
            
            # Calculate perp M2M separately per exchange
            # Short P&L = eth_short * (entry_price - current_mark_price)
            # Positive when price drops (shorts profit from price decrease)
            binance_perp_mtm_usd = short_positions['binance']['eth_short'] * (
                short_positions['binance']['entry_price'] - binance_mark_price
            )
            bybit_perp_mtm_usd = short_positions['bybit']['eth_short'] * (
                short_positions['bybit']['entry_price'] - bybit_mark_price
            )
            okx_perp_mtm_usd = short_positions['okx']['eth_short'] * (
                short_positions['okx']['entry_price'] - okx_mark_price
            )
            perp_mtm_total_usd = binance_perp_mtm_usd + bybit_perp_mtm_usd + okx_perp_mtm_usd
            
            # CRITICAL FIX: Calculate CHANGE in M2M per exchange (not split total!)
            binance_perp_mtm_hourly = binance_perp_mtm_usd - cumulative_binance_perp_mtm_usd
            bybit_perp_mtm_hourly = bybit_perp_mtm_usd - cumulative_bybit_perp_mtm_usd
            okx_perp_mtm_hourly = okx_perp_mtm_usd - cumulative_okx_perp_mtm_usd
            perp_mtm_pnl_hourly = binance_perp_mtm_hourly + bybit_perp_mtm_hourly + okx_perp_mtm_hourly
            
            # Record transaction costs as a one-time P&L hit at the first tracked hour
            transaction_costs_pnl_hourly = -total_transaction_costs if i == 1 else 0.0

            # Update cumulative trackers (perp M2M tracked separately for transparency)
            cumulative_supply_pnl_usd += supply_pnl_usd
            cumulative_borrow_cost_usd += borrow_cost_usd
            cumulative_price_change_pnl_usd += price_change_pnl_usd
            cumulative_funding_cost_usd += funding_pnl['total_funding_pnl_usd']
            cumulative_ethena_pnl_usd += ethena_hourly_pnl_usd
            cumulative_perp_mtm_pnl_usd = perp_mtm_total_usd  # Reference only (excluded from attribution)
            
            # PHASE 2.5: Calculate health factor using UNDERLYING values (what AAVE sees)
            # AAVE balance calculations
            aave_collateral_value_weth = weeth_collateral_underlying * weeth_price
            aave_debt_value_weth = weth_debt_underlying
            health_factor = (self.config.liquidation_threshold * aave_collateral_value_weth) / aave_debt_value_weth if aave_debt_value_weth > 0 else float('inf')
            
            # Calculate actual LTV (what AAVE calculates)
            actual_ltv = aave_debt_value_weth / aave_collateral_value_weth if aave_collateral_value_weth > 0 else 0
            
            # PHASE 2.5: Track balances in ETH equivalent using UNDERLYING values
            # Use underlying values for balance calculations
            weeth_balance_eth = weeth_collateral_underlying * weeth_price  # Redeemable weETH → ETH
            weth_debt_eth = weth_debt_underlying  # Owed WETH (WETH = ETH, 1:1)
            aave_net_eth = weeth_balance_eth - weth_debt_eth
            
            # EXACT ETH EQUIVALENT CALCULATION for delta tracking
            # Long exposure: NET AAVE position (collateral - debt) in ETH equivalent
            exact_long_eth = (weeth_collateral_underlying * weeth_price) - weth_debt_underlying
            # Short exposure: Perp shorts (fixed until rebalancing)
            exact_short_eth = short_positions['total_eth_short']
            # Net delta: Exact ETH equivalent difference
            exact_net_delta_eth = exact_long_eth - exact_short_eth
            
            # Track total collateral for display
            collateral_value_weth = aave_collateral_value_weth
            debt_value_weth = aave_debt_value_weth
            
            # CEX perp position in ETH terms (fixed amount)
            perp_short_eth = short_positions['total_eth_short']
            
            # Net delta in ETH terms (using exact ETH equivalent calculation)
            net_delta_eth_current = exact_net_delta_eth
            
            # Delta percentages (using exact values)
            delta_pct_vs_initial = (net_delta_eth_current / initial_eth_purchased) * 100
            delta_pct_vs_aave = (net_delta_eth_current / exact_long_eth) * 100 if exact_long_eth > 0 else 0
            
            # Calculate P&L from delta exposure (unhedged exposure × price change)
            # Using average delta between this hour and last hour
            avg_delta_eth = (net_delta_eth_current + prev_net_delta_eth) / 2
            eth_price_change = eth_price - prev_eth_price
            delta_pnl_hourly = avg_delta_eth * eth_price_change
            cumulative_delta_pnl_usd += delta_pnl_hourly

            # Total attribution P&L for this hour (no perp mark-to-market)
            net_pnl_usd = (
                supply_pnl_usd
                + price_change_pnl_usd
                - borrow_cost_usd
                + funding_pnl['total_funding_pnl_usd']
                + delta_pnl_hourly
                + transaction_costs_pnl_hourly
            )
            cumulative_transaction_costs_pnl_usd += transaction_costs_pnl_hourly
            cumulative_net_pnl_usd += net_pnl_usd

            # Update previous values for next iteration
            prev_eth_price = eth_price
            prev_net_delta_eth = net_delta_eth_current

            # CRITICAL FIX: Update CEX account balances with P&L
            # Each exchange gets its OWN M2M changes (not split of total!)
            binance_account_balance += funding_pnl['binance_pnl'] + binance_perp_mtm_hourly
            bybit_account_balance += funding_pnl['bybit_pnl'] + bybit_perp_mtm_hourly
            okx_account_balance += funding_pnl['okx_pnl'] + okx_perp_mtm_hourly
            total_account_balance = binance_account_balance + bybit_account_balance + okx_account_balance
            
            # Update cumulative M2M per exchange
            cumulative_binance_perp_mtm_usd = binance_perp_mtm_usd
            cumulative_bybit_perp_mtm_usd = bybit_perp_mtm_usd
            cumulative_okx_perp_mtm_usd = okx_perp_mtm_usd
            
            # PHASE 1.5 FIX: Calculate current exposure (changes as mark price changes!)
            binance_exposure_usdt = short_positions['binance']['eth_short'] * binance_mark_price
            bybit_exposure_usdt = short_positions['bybit']['eth_short'] * bybit_mark_price
            okx_exposure_usdt = short_positions['okx']['eth_short'] * okx_mark_price
            total_exposure_usdt = binance_exposure_usdt + bybit_exposure_usdt + okx_exposure_usdt
            
            # PHASE 1.5 FIX: Calculate margin ratios (balance / exposure)
            binance_margin_ratio = binance_account_balance / binance_exposure_usdt if binance_exposure_usdt > 0 else 1.0
            bybit_margin_ratio = bybit_account_balance / bybit_exposure_usdt if bybit_exposure_usdt > 0 else 1.0
            okx_margin_ratio = okx_account_balance / okx_exposure_usdt if okx_exposure_usdt > 0 else 1.0
            
            # Calculate required margins for reference
            binance_required_margin = binance_exposure_usdt * self.config.initial_margin_ratio
            bybit_required_margin = bybit_exposure_usdt * self.config.initial_margin_ratio
            okx_required_margin = okx_exposure_usdt * self.config.initial_margin_ratio
            
            # PHASE 1.5 FIX: Liquidation at 10% margin ratio, warning at 20%
            margin_warning_threshold = 0.20  # Warn when margin ratio < 20%
            binance_liquidation_risk = binance_margin_ratio < self.config.maintenance_margin_ratio
            bybit_liquidation_risk = bybit_margin_ratio < self.config.maintenance_margin_ratio
            okx_liquidation_risk = okx_margin_ratio < self.config.maintenance_margin_ratio
            binance_margin_warning = binance_margin_ratio < margin_warning_threshold
            bybit_margin_warning = bybit_margin_ratio < margin_warning_threshold
            okx_margin_warning = okx_margin_ratio < margin_warning_threshold
            
            # Log liquidation risk (margin ratio < 10%)
            if binance_liquidation_risk:
                self._log_event(timestamp, 'LIQUIDATION_RISK', 'BINANCE', 'USDT', binance_account_balance,
                               margin_ratio=binance_margin_ratio, exposure_usdt=binance_exposure_usdt,
                               required_margin=binance_required_margin, threshold=self.config.maintenance_margin_ratio)
            
            if bybit_liquidation_risk:
                self._log_event(timestamp, 'LIQUIDATION_RISK', 'BYBIT', 'USDT', bybit_account_balance,
                               margin_ratio=bybit_margin_ratio, exposure_usdt=bybit_exposure_usdt,
                               required_margin=bybit_required_margin, threshold=self.config.maintenance_margin_ratio)
            
            if okx_liquidation_risk:
                self._log_event(timestamp, 'LIQUIDATION_RISK', 'OKX', 'USDT', okx_account_balance,
                               margin_ratio=okx_margin_ratio, exposure_usdt=okx_exposure_usdt,
                               required_margin=okx_required_margin, threshold=self.config.maintenance_margin_ratio)
            
            # Log margin warnings (margin ratio < 20% - time to rebalance!)
            if binance_margin_warning and not binance_liquidation_risk:
                self._log_event(timestamp, 'MARGIN_WARNING', 'BINANCE', 'USDT', binance_account_balance,
                               margin_ratio=binance_margin_ratio, exposure_usdt=binance_exposure_usdt,
                               threshold=margin_warning_threshold, action='CONSIDER_ADDING_MARGIN')
            
            if bybit_margin_warning and not bybit_liquidation_risk:
                self._log_event(timestamp, 'MARGIN_WARNING', 'BYBIT', 'USDT', bybit_account_balance,
                               margin_ratio=bybit_margin_ratio, exposure_usdt=bybit_exposure_usdt,
                               threshold=margin_warning_threshold, action='CONSIDER_ADDING_MARGIN')
            
            if okx_margin_warning and not okx_liquidation_risk:
                self._log_event(timestamp, 'MARGIN_WARNING', 'OKX', 'USDT', okx_account_balance,
                               margin_ratio=okx_margin_ratio, exposure_usdt=okx_exposure_usdt,
                               threshold=margin_warning_threshold, action='CONSIDER_ADDING_MARGIN')
            
            # Detect rebalancing trigger (but don't action it yet)
            rebalance_triggered = abs(delta_pct_vs_initial) > self.config.rebalance_threshold_pct
            if rebalance_triggered:
                self._log_event(timestamp, 'REBALANCE_TRIGGER', 'STRATEGY', 'ETH', net_delta_eth_current,
                               delta_pct=delta_pct_vs_initial, threshold=self.config.rebalance_threshold_pct,
                               aave_net_eth=aave_net_eth, perp_short_eth=perp_short_eth,
                               action='FLAGGED_ONLY')
            
            # Legacy for compatibility
            long_eth_exposure = aave_net_eth
            short_eth_exposure = perp_short_eth
            
            # Exact ETH equivalent values for improved delta tracking
            exact_long_eth_exposure = exact_long_eth
            exact_short_eth_exposure = exact_short_eth
            
            # Update old values for next iteration's P&L calculation
            old_weeth_collateral_underlying = weeth_collateral_underlying
            old_weth_debt_underlying = weth_debt_underlying
            old_weeth_price = weeth_price
            
            # Balance-based totals for this hour
            net_aave_position_eth = aave_net_eth
            net_aave_position_usd = net_aave_position_eth * eth_price
            eth_gas_debt_usd = -eth_balance_for_gas * eth_price
            total_value_usd = net_aave_position_usd + total_account_balance - eth_gas_debt_usd
            balance_pnl_usd = total_value_usd - initial_total_value_pre_cost_usd

            balance_component = {
                'timestamp': timestamp,
                'net_aave_position_usd': net_aave_position_usd,
                'net_aave_position_weth': net_aave_position_eth,
                'weeth_collateral_value_weth': aave_collateral_value_weth,
                'weeth_collateral_value_usd': aave_collateral_value_weth * eth_price,
                'weth_debt_value_weth': aave_debt_value_weth,
                'weth_debt_value_usd': aave_debt_value_weth * eth_price,
                'weeth_price': weeth_price,
                'eth_price': eth_price,
                'binance_balance_usd': binance_account_balance,
                'bybit_balance_usd': bybit_account_balance,
                'total_cex_balance_usd': total_account_balance,
                'eth_gas_debt_eth': eth_balance_for_gas,
                'eth_gas_debt_usd': eth_gas_debt_usd,
                'total_value_usd': total_value_usd,
                'balance_pnl_usd': balance_pnl_usd
            }
            balance_sheet_history.append(balance_component)

            hour_balance_change = balance_pnl_usd - (balance_sheet_history[-2]['balance_pnl_usd'] if len(balance_sheet_history) > 1 else 0)
            if abs(hour_balance_change) >= self.config.balance_pnl_log_threshold_usd:
                self.logger.warning(
                    "BALANCE P&L SWING | %s | Δ$%.2f | NetAAVE $%.2f | CEX $%.2f | GasDebt $%.2f",
                    timestamp,
                    hour_balance_change,
                    net_aave_position_usd,
                    total_account_balance,
                    eth_gas_debt_usd
                )
            
            # Record hourly data
            hourly_pnl.append({
                'timestamp': timestamp,
                'eth_price': eth_price,
                # Balance-based tracking
                'balance_based_pnl_usd': balance_pnl_usd,
                'total_value_usd': total_value_usd,
                'net_aave_position_usd': net_aave_position_usd,
                'net_aave_position_weth': net_aave_position_eth,
                'total_cex_balance_usd': total_account_balance,
                'eth_gas_debt_usd': eth_gas_debt_usd,
                # Long side P&L
                'supply_pnl_usd': supply_pnl_usd,
                'seasonal_pnl_usd': 0.0,  # No seasonal rewards
                'borrow_cost_usd': borrow_cost_usd,
                'price_change_pnl_usd': price_change_pnl_usd,
                'long_pnl_usd': long_pnl_usd,
                # Short side P&L
                'funding_pnl_usd': funding_pnl['total_funding_pnl_usd'],
                'binance_funding_pnl_usd': funding_pnl['binance_pnl'],
                'bybit_funding_pnl_usd': funding_pnl['bybit_pnl'],
                'binance_funding_rate': funding_pnl['binance_rate'],
                'bybit_funding_rate': funding_pnl['bybit_rate'],
                'perp_mtm_pnl_hourly': perp_mtm_pnl_hourly,
                'perp_mtm_total_unrealized': perp_mtm_total_usd,
                'transaction_costs_pnl_hourly': transaction_costs_pnl_hourly,
                'cumulative_transaction_costs_pnl_usd': cumulative_transaction_costs_pnl_usd,
                # PHASE 1 FIX: Per-exchange mark prices and unrealized P&L
                'binance_perp_mark_price': binance_mark_price,
                'binance_perp_mark_close': binance_mark_close,
                'binance_perp_entry_price': short_positions['binance']['entry_price'],
                'binance_perp_entry_close': short_positions['binance']['entry_price_close'],
                'binance_perp_unrealized_pnl': binance_perp_mtm_usd,
                'bybit_perp_mark_price': bybit_mark_price,
                'bybit_perp_mark_close': bybit_mark_close,
                'bybit_perp_entry_price': short_positions['bybit']['entry_price'],
                'bybit_perp_entry_close': short_positions['bybit']['entry_price_close'],
                'bybit_perp_unrealized_pnl': bybit_perp_mtm_usd,
                'okx_perp_mark_price': okx_mark_price,
                'okx_perp_mark_close': okx_mark_close,
                'okx_perp_entry_price': short_positions['okx']['entry_price'],
                'okx_perp_entry_close': short_positions['okx']['entry_price_close'],
                'okx_perp_unrealized_pnl': okx_perp_mtm_usd,
                # Delta exposure P&L
                'delta_pnl_hourly': delta_pnl_hourly,
                'cumulative_delta_pnl_usd': cumulative_delta_pnl_usd,
                # Net P&L
                'net_pnl_usd': net_pnl_usd,
                # Cumulatives
                'cumulative_supply_pnl_usd': cumulative_supply_pnl_usd,
                'cumulative_seasonal_pnl_usd': 0.0,  # No seasonal rewards
                'cumulative_borrow_cost_usd': cumulative_borrow_cost_usd,
                'cumulative_price_change_pnl_usd': cumulative_price_change_pnl_usd,
                'cumulative_funding_cost_usd': cumulative_funding_cost_usd,
                'cumulative_perp_mtm_pnl_usd': cumulative_perp_mtm_pnl_usd,
                'cumulative_net_pnl_usd': cumulative_net_pnl_usd,
                # Ethena benchmark (for comparison)
                'ethena_apr_percent': ethena_apr * 100,
                'ethena_hourly_pnl_usd': ethena_hourly_pnl_usd,
                'cumulative_ethena_pnl_usd': cumulative_ethena_pnl_usd,
                # PHASE 2.5: AAVE positions (exact mechanics)
                'aweeth_scaled_balance': aweeth_scaled_balance,  # CONSTANT (ERC-20 balance)
                'weth_debt_scaled_balance': weth_debt_scaled_balance,  # CONSTANT (debt token balance)
                'weeth_collateral_underlying': weeth_collateral_underlying,  # From index only
                'weth_debt_underlying': weth_debt_underlying,  # From index only
                'weeth_collateral': weeth_collateral,  # Underlying collateral
                'aweeth_balance': aweeth_balance,  # Scaled balance (constant)
                'weth_debt': weth_debt,  # Underlying debt
                'aave_liquidity_index_weeth': current_liquidity_index_weeth,  # AAVE index
                'aave_borrow_index_weth': current_borrow_index_weth,  # AAVE borrow index
                'aave_collateral_value_weth': aave_collateral_value_weth,  # What AAVE sees
                'aave_debt_value_weth': aave_debt_value_weth,  # What AAVE sees
                'actual_ltv': actual_ltv,  # Current LTV (AAVE calculation)
                'collateral_value_weth': collateral_value_weth,  # For backwards compat
                'debt_value_weth': debt_value_weth,  # For backwards compat
                'health_factor': health_factor,
                'weeth_price': weeth_price,
                # Venue balances in ETH equivalent (for delta tracking)
                'aave_weeth_balance_eth': weeth_balance_eth,
                'aave_weth_debt_eth': weth_debt_eth,
                'aave_net_position_eth': aave_net_eth,
                'cex_perp_short_eth': perp_short_eth,
                # Market neutrality (legacy)
                'long_eth_exposure': long_eth_exposure,
                'short_eth_exposure': short_eth_exposure,
                'net_delta_eth': net_delta_eth_current,
                'delta_pct_vs_initial': delta_pct_vs_initial,
                'delta_pct_vs_aave': delta_pct_vs_aave,
                # Exact ETH equivalent values (improved delta tracking)
                'exact_long_eth_exposure': exact_long_eth_exposure,
                'exact_short_eth_exposure': exact_short_eth_exposure,
                'exact_net_delta_eth': exact_net_delta_eth,
                # ETH Wallet Token Balances (what wallet actually holds)
                'eth_wallet_aweeth_balance': aweeth_balance,  # AAVE claim token
                'eth_wallet_weeth_underlying': weeth_collateral,  # Underlying weETH
                'eth_wallet_weth_debt': weth_debt,  # AAVE debt
                'eth_wallet_net_eth': aave_net_eth,  # Net position in ETH
                # ETH Balance/Debt for Gas (tracks gas payments)
                'eth_wallet_eth_balance': eth_balance_for_gas,  # Usually negative (gas debt)
                'cumulative_gas_paid_eth': cumulative_gas_paid_eth,  # Total gas paid
                # PHASE 1.5 FIX: CEX account tracking (TOTAL balances, not just margin)
                'binance_account_balance_usdt': binance_account_balance,  # Total account balance
                'bybit_account_balance_usdt': bybit_account_balance,  # Total account balance
                'okx_account_balance_usdt': okx_account_balance,  # Total account balance
                'total_account_balance_usdt': total_account_balance,  # Sum of all three
                'binance_exposure_usdt': binance_exposure_usdt,  # Position value (changes with price)
                'bybit_exposure_usdt': bybit_exposure_usdt,  # Position value (changes with price)
                'okx_exposure_usdt': okx_exposure_usdt,  # Position value (changes with price)
                'total_exposure_usdt': total_exposure_usdt,  # Total short exposure
                'binance_required_margin_usdt': binance_required_margin,  # 15% of exposure (locked)
                'bybit_required_margin_usdt': bybit_required_margin,  # 15% of exposure (locked)
                'binance_margin_ratio': binance_margin_ratio,  # balance / exposure
                'bybit_margin_ratio': bybit_margin_ratio,  # balance / exposure
                'okx_margin_ratio': okx_margin_ratio,  # balance / exposure
                'binance_liquidation_risk': binance_liquidation_risk,  # margin_ratio < 10%
                'bybit_liquidation_risk': bybit_liquidation_risk,  # margin_ratio < 10%
                'okx_liquidation_risk': okx_liquidation_risk,  # margin_ratio < 10%
                'binance_margin_warning': binance_margin_warning,  # margin_ratio < 20%
                'bybit_margin_warning': bybit_margin_warning,  # margin_ratio < 20%
                'okx_margin_warning': okx_margin_warning,  # margin_ratio < 20%
                # CEX Position Sizes (ETH short amounts - constant)
                'binance_eth_short_position': short_positions['binance']['eth_short'],
                'bybit_eth_short_position': short_positions['bybit']['eth_short'],
                'okx_eth_short_position': short_positions['okx']['eth_short'],
                'total_eth_short_position': short_positions['total_eth_short'],
                # Rebalancing
                'rebalance_triggered': rebalance_triggered,
                # Rates
                'weeth_supply_apy': rates['weeth_supply_apy'],
                'weth_borrow_apy': rates['weth_borrow_apy'],
                'seasonal_yield_hourly': 0.0,  # No seasonal rewards
                'base_yield_hourly': staking_yields['base_yield_hourly']
            })
        
        # PHASE 2.5: Calculate final metrics (all venues) using UNDERLYING values
        final_eth_price = self._get_spot_price(timestamps[-1])
        
        # Get final indices
        final_rates = self._get_rates_at_timestamp(timestamps[-1])
        final_liquidity_index_weeth = final_rates['liquidityIndex'] if 'liquidityIndex' in final_rates else current_liquidity_index_weeth
        
        weth_rates_final = self.data['weth_rates']
        weth_ts_final = weth_rates_final.index.asof(timestamps[-1])
        if pd.isna(weth_ts_final):
            weth_ts_final = weth_rates_final.index[-1]
        final_borrow_index_weth = weth_rates_final.loc[weth_ts_final, 'variableBorrowIndex'] if 'variableBorrowIndex' in weth_rates_final.columns else current_borrow_index_weth
        
        # Total Value = CEX Balances + ETH Wallet Assets - AAVE Debt - ETH Gas Debt
        final_cex_balance_usd = total_account_balance  # USDT in CEX (includes all P&L)
        
        # ETH Wallet Assets: aTokens valued using exact AAVE formula
        # Value = scaledBalance × liquidityIndex × oracle × ETH/USD
        # NOTE: Indices already normalized in our data (~1.0), no 1e27 division!
        final_eth_wallet_assets_usd = (aweeth_scaled_balance * final_liquidity_index_weeth * 
                                       weeth_price * final_eth_price)
        
        # AAVE Debt: debt tokens valued using exact AAVE formula
        # Debt = scaledBalance × borrowIndex × ETH/USD
        final_aave_debt_usd = (weth_debt_scaled_balance * final_borrow_index_weth * 
                              final_eth_price)
        
        # ETH Gas Debt
        final_eth_gas_debt_usd = -eth_balance_for_gas * final_eth_price  # ETH owed for gas (positive value)
        
        final_total_value_usd = (final_cex_balance_usd + final_eth_wallet_assets_usd - 
                                 final_aave_debt_usd - final_eth_gas_debt_usd)
        
        # P&L from balance changes (transaction costs already reflected in balances)
        # Gas creates ETH debt (reduces value)
        # Execution costs reduce CEX balances (already accounted for)
        actual_total_pnl_usd = final_total_value_usd - initial_total_value_pre_cost_usd
        
        # P&L from attribution (sum of components)
        attribution_pnl_usd = cumulative_net_pnl_usd
        
        # Reconciliation difference (should be ~$0)
        pnl_reconciliation_diff = actual_total_pnl_usd - attribution_pnl_usd
        
        # Legacy values for compatibility
        final_aave_net_weth = (weeth_collateral * weeth_price) - weth_debt
        final_aave_net_usd = final_aave_net_weth * final_eth_price
        final_position_value_weth = final_aave_net_weth
        final_position_value_usd = final_aave_net_usd  # Only AAVE (for backwards compat)
        actual_net_profit_usd = cumulative_net_pnl_usd
        
        # Calculate annualized metrics
        time_delta = end_ts - start_ts
        years_analyzed = time_delta.total_seconds() / (365.25 * 24 * 3600)
        days_analyzed = time_delta.total_seconds() / (24 * 3600)
        
        # APR and APY
        if years_analyzed > 0:
            apr_pct = (actual_net_profit_usd / initial_net_position_usd) / years_analyzed * 100
            apy_pct = ((final_position_value_usd / initial_net_position_usd) ** (1 / years_analyzed) - 1) * 100
        else:
            apr_pct = 0
            apy_pct = 0
        
        # Additional metrics
        pnl_df = pd.DataFrame(hourly_pnl)
        
        # Daily Sharpe ratio
        pnl_df['date'] = pd.to_datetime(pnl_df['timestamp']).dt.date
        daily_pnl = pnl_df.groupby('date').agg({
            'net_pnl_usd': 'sum',
            'long_eth_exposure': 'last'
        }).reset_index()
        
        daily_pnl['daily_return'] = daily_pnl['net_pnl_usd'] / (daily_pnl['long_eth_exposure'].shift(1) * eth_price_spot)
        daily_pnl = daily_pnl.dropna()
        
        avg_daily_return = daily_pnl['daily_return'].mean()
        daily_return_std = daily_pnl['daily_return'].std()
        annualized_volatility = daily_return_std * np.sqrt(365)
        sharpe_ratio = (apr_pct / 100) / annualized_volatility if annualized_volatility > 0 else 0
        
        # Max drawdown
        pnl_df['cumulative_value_usd'] = initial_net_position_usd + pnl_df['cumulative_net_pnl_usd']
        pnl_df['peak_value_usd'] = pnl_df['cumulative_value_usd'].cummax()
        pnl_df['drawdown_usd'] = pnl_df['cumulative_value_usd'] - pnl_df['peak_value_usd']
        pnl_df['drawdown_pct'] = (pnl_df['drawdown_usd'] / pnl_df['peak_value_usd']) * 100
        max_drawdown_pct = pnl_df['drawdown_pct'].min()
        
        # Update hourly_pnl with drawdown
        for i in range(len(hourly_pnl)):
            hourly_pnl[i]['cumulative_value_usd'] = pnl_df.iloc[i]['cumulative_value_usd']
            hourly_pnl[i]['drawdown_pct'] = pnl_df.iloc[i]['drawdown_pct']
        
        # Compile results
        self.results = {
            'config': {
                'initial_usdt': self.config.initial_usdt,
                'allocation_to_long_pct': self.config.allocation_to_long_pct,
                'binance_hedge_pct': self.config.binance_hedge_pct,
                'bybit_hedge_pct': self.config.bybit_hedge_pct,
                'max_ltv': self.config.max_ltv,
                # eigen_only removed - no seasonal rewards
            },
            'initial_positions': {
                'long': initial_long_position,
                'short': short_positions,
                'net_delta_eth': net_delta_eth,
                'delta_pct': delta_pct
            },
            'summary': {
                'total_hours': len(hourly_pnl),
                'days_analyzed': days_analyzed,
                'years_analyzed': years_analyzed,
                'initial_usdt': self.config.initial_usdt,
                # PHASE 1.5: Balance Sheet Breakdown (Initial)
                'initial_cex_balance_usd': initial_cex_balance_usd,
                'initial_eth_wallet_assets_usd': initial_eth_wallet_assets_usd,
                'initial_aave_debt_usd': initial_aave_debt_usd,
                'initial_eth_gas_debt_usd': initial_eth_gas_debt_usd,
                'initial_total_value_usd': initial_total_value_usd,
                'initial_total_value_pre_cost_usd': initial_total_value_pre_cost_usd,
                # PHASE 1.5: Balance Sheet Breakdown (Final)
                'final_cex_balance_usd': final_cex_balance_usd,
                'final_eth_wallet_assets_usd': final_eth_wallet_assets_usd,
                'final_aave_debt_usd': final_aave_debt_usd,
                'final_eth_gas_debt_usd': final_eth_gas_debt_usd,
                'final_total_value_usd': final_total_value_usd,
                # PHASE 1.5: P&L Reconciliation
                'actual_total_pnl_usd': actual_total_pnl_usd,
                'attribution_pnl_usd': attribution_pnl_usd,
                'pnl_reconciliation_diff': pnl_reconciliation_diff,
                # Legacy (AAVE-only for backwards compat)
                'initial_aave_net_usd': initial_aave_net_usd,
                'final_aave_net_usd': final_aave_net_usd,
                'initial_net_position_usd': initial_net_position_usd,
                'final_position_value_usd': final_position_value_usd,
                'cumulative_supply_pnl_usd': cumulative_supply_pnl_usd,
                'cumulative_seasonal_pnl_usd': 0.0,  # No seasonal rewards
                'cumulative_borrow_cost_usd': cumulative_borrow_cost_usd,
                'cumulative_price_change_pnl_usd': cumulative_price_change_pnl_usd,
                'cumulative_funding_cost_usd': cumulative_funding_cost_usd,
                'cumulative_perp_mtm_pnl_usd': cumulative_perp_mtm_pnl_usd,
                'cumulative_delta_pnl_usd': cumulative_delta_pnl_usd,
                'cumulative_transaction_costs_pnl_usd': cumulative_transaction_costs_pnl_usd,
                'cumulative_net_pnl_usd': cumulative_net_pnl_usd,
                # Cost breakdown (for reference - already implicit in balances)
                'total_gas_costs_usd': cumulative_gas_costs_usd,
                'gas_transfer_costs_usd': spot_transfer_gas,
                'gas_leverage_loop_usd': initial_long_position['total_gas_costs_usd'],
                'total_execution_costs_usd': cumulative_execution_costs_usd,
                'spot_execution_cost_usd': spot_exec_cost,
                'perp_execution_costs_usd': short_positions['total_exec_costs'],
                'total_transaction_costs_usd': total_transaction_costs,
                'initial_eth_purchased': initial_eth_purchased,
                'total_margin_posted': short_positions['total_margin_posted'],
                'final_cex_account_balance': total_account_balance,
                'rebalance_triggers': pnl_df['rebalance_triggered'].sum(),
                'apr_pct': apr_pct,
                'apy_pct': apy_pct,
                'sharpe_ratio': sharpe_ratio,
                'annualized_volatility': annualized_volatility * 100,
                'max_drawdown_pct': max_drawdown_pct,
                'avg_delta_pct_vs_initial': pnl_df['delta_pct_vs_initial'].mean(),
                'max_abs_delta_pct_vs_initial': pnl_df['delta_pct_vs_initial'].abs().max(),
                'avg_delta_pct_vs_aave': pnl_df['delta_pct_vs_aave'].mean(),
                'max_abs_delta_pct_vs_aave': pnl_df['delta_pct_vs_aave'].abs().max()
            },
            'hourly_pnl': hourly_pnl,
            'event_log': self.event_log,
            'balance_sheet_history': balance_sheet_history
        }
        
        self.logger.info("=" * 80)
        self.logger.info("📊 ANALYSIS RESULTS:")
        self.logger.info("=" * 80)
        self.logger.info(f"⏱️  Total hours analyzed: {len(hourly_pnl):,}")
        self.logger.info(f"💰 Initial USDT: ${self.config.initial_usdt:,.2f}")
        self.logger.info("")
        self.logger.info("💼 INITIAL POSITION (All Venues - Balance Sheet View):")
        self.logger.info(f"   CEX Accounts (USDT):        +${initial_cex_balance_usd:,.2f}")
        self.logger.info(f"   ETH Wallet Assets (aWeETH): +${initial_eth_wallet_assets_usd:,.2f}")
        self.logger.info(f"   AAVE Debt (WETH):           -${initial_aave_debt_usd:,.2f}")
        self.logger.info(f"   ETH Gas Debt:               -${initial_eth_gas_debt_usd:,.2f}")
        self.logger.info(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.logger.info(f"   TOTAL VALUE (after costs):   ${initial_total_value_usd:,.2f}")
        self.logger.info(f"   Pre-cost baseline (P&L start): ${initial_total_value_pre_cost_usd:,.2f} (capital before costs)")
        self.logger.info("")
        self.logger.info("💼 FINAL POSITION (All Venues - Balance Sheet View):")
        self.logger.info(f"   CEX Accounts (USDT):        +${final_cex_balance_usd:,.2f}")
        self.logger.info(f"   ETH Wallet Assets (aWeETH): +${final_eth_wallet_assets_usd:,.2f}")
        self.logger.info(f"   AAVE Debt (WETH):           -${final_aave_debt_usd:,.2f}")
        self.logger.info(f"   ETH Gas Debt:               -${final_eth_gas_debt_usd:,.2f}")
        self.logger.info(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.logger.info(f"   TOTAL VALUE:                 ${final_total_value_usd:,.2f}")
        self.logger.info("")
        self.logger.info("💰 P&L FROM BALANCE CHANGES:")
        self.logger.info(f"   Initial baseline (pre-cost):  ${initial_total_value_pre_cost_usd:,.2f}")
        self.logger.info(f"   Final total value:            ${final_total_value_usd:,.2f}")
        self.logger.info(f"   Balance-based P&L:            ${actual_total_pnl_usd:,.2f}")
        self.logger.info("")
        self.logger.info("💰 P&L FROM ATTRIBUTION:")
        self.logger.info(f"   Sum of All Components:        ${attribution_pnl_usd:,.2f}")
        self.logger.info("")
        self.logger.info("🔍 RECONCILIATION CHECK:")
        self.logger.info(f"   Balance-based P&L:            ${actual_total_pnl_usd:,.2f}")
        self.logger.info(f"   Attribution-based P&L:        ${attribution_pnl_usd:,.2f}")
        self.logger.info(f"   Difference:                   ${pnl_reconciliation_diff:,.2f}")
        if abs(pnl_reconciliation_diff) < 10:
            self.logger.info(f"   ✅ RECONCILIATION PASSED (diff < $10)")
        else:
            self.logger.warning(f"   ⚠️ RECONCILIATION FAILED (diff > $10) - Check P&L components")
        self.logger.info("")
        self.logger.info("📊 P&L ATTRIBUTION BREAKDOWN:")
        self.logger.info(f"   ✅ AAVE Supply Yield:         +${cumulative_supply_pnl_usd:,.2f} (rebasing on collateral)")
        # No seasonal rewards in attribution P&L
        self.logger.info(f"   📈 weETH/ETH Oracle Return:  +${cumulative_price_change_pnl_usd:,.2f} (base staking gain)")
        self.logger.info(f"   ❌ AAVE Borrow Cost:         -${cumulative_borrow_cost_usd:,.2f} (variable debt growth)")
        funding_sign = "+" if cumulative_funding_cost_usd >= 0 else ""
        self.logger.info(f"   💵 Funding Rate P&L:         {funding_sign}${cumulative_funding_cost_usd:,.2f} (+ received / - paid)")
        delta_sign = "+" if cumulative_delta_pnl_usd >= 0 else ""
        self.logger.info(f"   ⚡ Net Delta P&L:            {delta_sign}${cumulative_delta_pnl_usd:,.2f} (unhedged ETH exposure)")
        txn_sign = "+" if cumulative_transaction_costs_pnl_usd >= 0 else ""
        self.logger.info(f"   🧾 Transaction Costs:        {txn_sign}${cumulative_transaction_costs_pnl_usd:,.2f} (gas + execution)")
        self.logger.info(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.logger.info(f"   💰 TOTAL ATTRIBUTION P&L:    ${cumulative_net_pnl_usd:,.2f}")
        self.logger.info("")
        perp_sign = "+" if cumulative_perp_mtm_pnl_usd >= 0 else ""
        self.logger.info("ℹ️  Reference (excluded from attribution sum):")
        self.logger.info(f"      • Perp Mark-to-Market:    {perp_sign}${cumulative_perp_mtm_pnl_usd:,.2f} (captured via CEX balances)")
        self.logger.info("")
        # Calculate total gas in ETH for display
        gas_events_df = pd.DataFrame([e for e in self.event_log if e['event_type'] == 'GAS_FEE_PAID'])
        total_gas_eth = gas_events_df['amount'].sum() if len(gas_events_df) > 0 else 0.0
        
        self.logger.info(f"💳 TRANSACTION COSTS (Detailed Breakdown):")
        self.logger.info(f"   ⛽ GAS COSTS: ${cumulative_gas_costs_usd:.2f} ({total_gas_eth:.6f} ETH)")
        self.logger.info(f"      ├─ CEX Funding Transfers:")
        self.logger.info(f"      │  ├─ USDT → Binance: ${binance_transfer_gas:.2f}")
        self.logger.info(f"      │  ├─ USDT → Bybit: ${bybit_transfer_gas:.2f}")
        self.logger.info(f"      │  └─ ETH ← Binance: ${eth_return_transfer_gas:.2f}")
        self.logger.info(f"      │  Subtotal: ${spot_transfer_gas:.2f}")
        self.logger.info(f"      ├─ Leverage Loop (23 iterations or atomic):")
        self.logger.info(f"      │  ├─ Stake (CREATE_LST × 23): ~${initial_long_position['total_gas_costs_usd'] * 0.22:.2f}")
        self.logger.info(f"      │  ├─ Supply (COLLATERAL × 23): ~${initial_long_position['total_gas_costs_usd'] * 0.36:.2f}")
        self.logger.info(f"      │  └─ Borrow (LOAN × 22): ~${initial_long_position['total_gas_costs_usd'] * 0.42:.2f}")
        self.logger.info(f"      └─ Subtotal Loop: ${initial_long_position['total_gas_costs_usd']:.2f}")
        self.logger.info(f"   💸 EXECUTION COSTS: ${cumulative_execution_costs_usd:.2f} (trading slippage/fees)")
        self.logger.info(f"      ├─ Spot Purchase (Binance): ${spot_exec_cost:.2f} ({exec_cost_bps} bps)")
        self.logger.info(f"      └─ Perp Opening (Binance+Bybit): ${short_positions['total_exec_costs']:.2f} (3 bps each)")
        self.logger.info(f"      ℹ️  Spot + Binance perp executed SIMULTANEOUSLY (delta neutral at entry)")
        self.logger.info(f"   💰 TOTAL COSTS: ${total_transaction_costs:.2f}")
        self.logger.info(f"   ℹ️  Gas paid from ETH wallet (creates ETH debt), Execution from USDT/margin")
        self.logger.info("")
        self.logger.info("💼 WALLET & ACCOUNT STRUCTURE:")
        self.logger.info(f"   📱 Single Ethereum Wallet: EtherFi + AAVE + Gas (all on-chain)")
        self.logger.info(f"   🏦 Separate CEX Accounts: Binance + Bybit + OKX (margin trading)")
        self.logger.info("")
        self.logger.info("💰 CEX ACCOUNT STATUS:")
        self.logger.info(f"   Initial Total Deposited: ${initial_cex_balance_usd:,.2f}")
        self.logger.info(f"     ├─ Binance: ${hedge_capital_usd * self.config.binance_hedge_pct - short_positions['binance']['exec_cost']:,.2f}")
        self.logger.info(f"     ├─ Bybit:   ${hedge_capital_usd * self.config.bybit_hedge_pct - short_positions['bybit']['exec_cost']:,.2f}")
        self.logger.info(f"     └─ OKX:     ${hedge_capital_usd * self.config.okx_hedge_pct - short_positions['okx']['exec_cost']:,.2f}")
        self.logger.info(f"   Final Account Balance: ${final_cex_balance_usd:,.2f}")
        self.logger.info(f"     ├─ Binance: {pnl_df['binance_account_balance_usdt'].iloc[-1]:,.2f}")
        self.logger.info(f"     ├─ Bybit:   {pnl_df['bybit_account_balance_usdt'].iloc[-1]:,.2f}")
        self.logger.info(f"     └─ OKX:     {pnl_df['okx_account_balance_usdt'].iloc[-1]:,.2f}")
        self.logger.info(f"   Change: ${final_cex_balance_usd - initial_cex_balance_usd:,.2f}")
        if final_cex_balance_usd < 0:
            self.logger.warning(f"   🚨 NEGATIVE BALANCE - Position would be liquidated by CEX!")
        
        # Show final margin ratios
        final_binance_ratio = pnl_df['binance_margin_ratio'].iloc[-1]
        final_bybit_ratio = pnl_df['bybit_margin_ratio'].iloc[-1]
        final_okx_ratio = pnl_df['okx_margin_ratio'].iloc[-1]
        self.logger.info("")
        self.logger.info(f"📊 FINAL MARGIN RATIOS:")
        self.logger.info(f"   Binance: {final_binance_ratio*100:.2f}% (liquidation < {self.config.maintenance_margin_ratio*100:.0f}%)")
        self.logger.info(f"   Bybit:   {final_bybit_ratio*100:.2f}% (liquidation < {self.config.maintenance_margin_ratio*100:.0f}%)")
        self.logger.info(f"   OKX:     {final_okx_ratio*100:.2f}% (liquidation < {self.config.maintenance_margin_ratio*100:.0f}%)")
        if final_binance_ratio < self.config.maintenance_margin_ratio or final_bybit_ratio < self.config.maintenance_margin_ratio or final_okx_ratio < self.config.maintenance_margin_ratio:
            self.logger.warning(f"   🚨 LIQUIDATED!")
        elif final_binance_ratio < 0.20 or final_bybit_ratio < 0.20:
            self.logger.warning(f"   ⚠️  Below 20% - urgent rebalancing needed!")
        self.logger.info("")
        self.logger.info("🔄 REBALANCING TRIGGERS:")
        self.logger.info(f"   Total Triggers: {self.results['summary']['rebalance_triggers']} times (delta > {self.config.rebalance_threshold_pct}%)")
        self.logger.info(f"   % of Time: {self.results['summary']['rebalance_triggers'] / len(hourly_pnl) * 100:.1f}%")
        self.logger.info("")
        self.logger.info("📈 PERFORMANCE METRICS:")
        self.logger.info(f"   APR:                  {apr_pct:.2f}%")
        self.logger.info(f"   APY (compounded):     {apy_pct:.2f}%")
        self.logger.info(f"   Sharpe Ratio:         {sharpe_ratio:.3f}")
        self.logger.info(f"   Annualized Vol:       {annualized_volatility * 100:.2f}%")
        self.logger.info(f"   Max Drawdown:         {max_drawdown_pct:.2f}%")
        self.logger.info("")
        self.logger.info("⚖️  MARKET NEUTRALITY:")
        self.logger.info(f"   Avg Delta (vs initial): {self.results['summary']['avg_delta_pct_vs_initial']:+.2f}%")
        self.logger.info(f"   Max Abs Delta:          {self.results['summary']['max_abs_delta_pct_vs_initial']:.2f}%")
        self.logger.info(f"   Avg Delta (vs AAVE):    {self.results['summary']['avg_delta_pct_vs_aave']:+.2f}%")
        self.logger.info("")
        self.logger.info(f"📋 Event Log: {len(self.event_log):,} events")
        self.logger.info("=" * 80)
        
        return self.results

    def save_results(self, output_dir: str = "data/analysis") -> None:
        """Save analysis results to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
        
        config_label = f"usdt_{int(self.config.initial_usdt/1000)}k"
        # No seasonal rewards config
        
        # Save summary
        summary_file = output_path / f"leveraged_restaking_USDT_summary_{config_label}_{timestamp_str}.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'config': self.results['config'],
                'initial_positions': self.results['initial_positions'],
                'summary': self.results['summary']
            }, f, indent=2, default=str)
        
        # Save hourly P&L
        pnl_df = pd.DataFrame(self.results['hourly_pnl'])
        pnl_file = output_path / f"leveraged_restaking_USDT_hourly_pnl_{config_label}_{timestamp_str}.csv"
        pnl_df.to_csv(pnl_file, index=False)
        
        # Save event log with balance snapshots
        if self.event_log:
            event_df = pd.DataFrame(self.event_log)
            
            # Add balance snapshot columns by matching to hourly data
            if len(pnl_df) > 0:
                event_df['event_timestamp'] = pd.to_datetime(event_df['timestamp'])
                
                # Balance columns to add (PHASE 1.5: Track total account balances + exposure)
                balance_cols = {
                    'eth_wallet_aweeth_balance': 'aWeETH',
                    'eth_wallet_weth_debt': 'WETH_debt', 
                    'eth_wallet_eth_balance': 'ETH_for_gas',
                    'binance_account_balance_usdt': 'Binance_account_USDT',
                    'binance_exposure_usdt': 'Binance_exposure_USDT',
                    'binance_eth_short_position': 'Binance_ETH_short',
                    'okx_account_balance_usdt': 'OKX_account_USDT',
                    'okx_exposure_usdt': 'OKX_exposure_USDT',
                    'okx_eth_short_position': 'OKX_ETH_short',
                    'binance_perp_mark_price': 'Binance_mark_price',
                    'binance_perp_mark_close': 'Binance_mark_close',
                    'binance_perp_entry_price': 'Binance_entry_price',
                    'binance_perp_entry_close': 'Binance_entry_close',
                    'binance_perp_unrealized_pnl': 'Binance_unrealized_PnL',
                    'binance_margin_ratio': 'Binance_margin_ratio',
                    'bybit_account_balance_usdt': 'Bybit_account_USDT',
                    'bybit_exposure_usdt': 'Bybit_exposure_USDT',
                    'bybit_eth_short_position': 'Bybit_ETH_short',
                    'bybit_perp_mark_price': 'Bybit_mark_price',
                    'bybit_perp_mark_close': 'Bybit_mark_close',
                    'bybit_perp_entry_price': 'Bybit_entry_price',
                    'bybit_perp_entry_close': 'Bybit_entry_close',
                    'bybit_perp_unrealized_pnl': 'Bybit_unrealized_PnL',
                    'bybit_margin_ratio': 'Bybit_margin_ratio',
                    'okx_perp_mark_price': 'OKX_mark_price',
                    'okx_perp_mark_close': 'OKX_mark_close',
                    'okx_perp_entry_price': 'OKX_entry_price',
                    'okx_perp_entry_close': 'OKX_entry_close',
                    'okx_perp_unrealized_pnl': 'OKX_unrealized_PnL',
                    'okx_margin_ratio': 'OKX_margin_ratio'
                }
                
                # For each event, find the balance state at/after that time
                for source_col, target_col in balance_cols.items():
                    if source_col in pnl_df.columns:
                        # Use first hour's balance for all t=0 events, then match hourly
                        first_hour = pd.to_datetime(pnl_df['timestamp'].iloc[0])
                        event_df[target_col] = event_df['event_timestamp'].apply(
                            lambda t: pnl_df[pnl_df['timestamp'] == t.strftime('%Y-%m-%d %H:%M:%S%z')][source_col].iloc[0]
                            if len(pnl_df[pnl_df['timestamp'] == t.strftime('%Y-%m-%d %H:%M:%S%z')]) > 0
                            else pnl_df[source_col].iloc[0]  # Use first hour for t=0 events
                        )
            
            event_file = output_path / f"leveraged_restaking_USDT_event_log_{config_label}_{timestamp_str}.csv"
            event_df.to_csv(event_file, index=False)
            self.logger.info(f"  📋 Event Log: {event_file} ({len(self.event_log):,} events)")
            if len(balance_cols) > 0 and len(pnl_df) > 0:
                self.logger.info(f"     ✅ Includes {len(balance_cols)} balance snapshot columns")
        
        self.logger.info(f"💾 Results saved to {output_path}")
        self.logger.info(f"  📄 Summary: {summary_file}")
        self.logger.info(f"  📊 Hourly P&L: {pnl_file}")
    
    def create_plots(self, output_dir: str = "data/analysis") -> None:
        """Create visualization plots."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
        config_label = f"usdt_{int(self.config.initial_usdt/1000)}k"
        # No seasonal rewards config
        
        pnl_df = pd.DataFrame(self.results['hourly_pnl'])
        
        # Calculate balance-based P&L FIRST (before any plotting)
        # Use NET AAVE position (collateral - debt) for proper balance-based P&L
        pnl_df['aweeth_collateral_usd'] = pnl_df['aweeth_balance'] * pnl_df['weeth_price'] * pnl_df['eth_price']
        pnl_df['weth_debt_usd'] = pnl_df['weth_debt_underlying'] * pnl_df['eth_price']
        pnl_df['net_aave_position_usd'] = pnl_df['aweeth_collateral_usd'] - pnl_df['weth_debt_usd']
        pnl_df['total_value_usd'] = pnl_df['net_aave_position_usd'] + pnl_df['total_account_balance_usdt']
        summary = self.results['summary']
        initial_total_value_pre_cost = summary.get('initial_total_value_pre_cost_usd', pnl_df['total_value_usd'].iloc[0])
        pnl_df['balance_based_pnl_usd'] = pnl_df['total_value_usd'] - initial_total_value_pre_cost
        
        # Set up plotting with ADDITIONAL panel for venue balances
        plt.style.use('seaborn-v0_8')
        fig = plt.figure(figsize=(28, 16))
        gs = fig.add_gridspec(4, 2, hspace=0.35, wspace=0.3)
        
        rewards_label = "Base Staking Only"  # No seasonal rewards
        fig.suptitle(f'USDT Market-Neutral Leveraged Restaking | {rewards_label}', fontsize=16, fontweight='bold')
        
        # Create subplots
        ax1 = fig.add_subplot(gs[0, 0])  # Cumulative Net P&L
        ax2 = fig.add_subplot(gs[0, 1])  # P&L Components
        ax3 = fig.add_subplot(gs[1, 0])  # Market Neutrality
        ax4 = fig.add_subplot(gs[1, 1])  # ETH Price
        ax5 = fig.add_subplot(gs[2, 0])  # Long vs Short Exposure
        ax6 = fig.add_subplot(gs[2, 1])  # Venue Balances (ETH equivalent)
        ax7 = fig.add_subplot(gs[3, :])  # Drawdown (full width)
        
        # Plot 1: Cumulative Net P&L (Balance-Based - Source of Truth)
        ax1.plot(pnl_df['timestamp'], pnl_df['balance_based_pnl_usd'], linewidth=2, color='green', label='Strategy P&L')
        
        # Add Ethena benchmark if available
        if 'cumulative_ethena_pnl_usd' in pnl_df.columns and pnl_df['cumulative_ethena_pnl_usd'].max() > 0:
            ax1.plot(pnl_df['timestamp'], pnl_df['cumulative_ethena_pnl_usd'], 
                    linewidth=2, color='purple', linestyle='--', label='Ethena Benchmark (sUSDE)', alpha=0.8)
        
        ax1.set_title('Cumulative Net P&L vs Ethena Benchmark (USD)')
        ax1.set_ylabel('Cumulative P&L ($)')
        ax1.legend(loc='best', fontsize=8)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        ax1.axhline(y=0, color='black', linestyle='--', alpha=0.3)
        
        # Plot 2: P&L Components (Attribution)
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_supply_pnl_usd'], label='Supply Yield (AAVE)', linewidth=1.8, alpha=0.9)
        # No seasonal rewards in attribution P&L
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_price_change_pnl_usd'], label='Oracle Return (weETH vs ETH)', linewidth=1.6, alpha=0.85)
        ax2.plot(pnl_df['timestamp'], -pnl_df['cumulative_borrow_cost_usd'], label='Borrow Cost (AAVE debt)', linewidth=1.6, alpha=0.85)
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_funding_cost_usd'], label='Funding Rate P&L', linewidth=1.6, alpha=0.9)
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_delta_pnl_usd'], label='Net Delta P&L', linewidth=2.0, alpha=0.9, color='purple')
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_transaction_costs_pnl_usd'], label='Transaction Costs', linewidth=1.8, linestyle='--', color='brown', alpha=0.8)
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_net_pnl_usd'], label='Attribution P&L', linewidth=2.5, color='black')
        ax2.set_title('Cumulative P&L Components (USD) - Attribution')
        ax2.set_ylabel('Cumulative USD')
        ax2.legend(loc='best', fontsize=7)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)
        
        # Plot 3: Market Neutrality (Delta %) with Rebalancing Triggers
        ax3.plot(pnl_df['timestamp'], pnl_df['delta_pct_vs_initial'], linewidth=1, color='blue', alpha=0.6, label='Delta %')
        
        # Highlight rebalancing trigger periods
        rebal_mask = pnl_df['rebalance_triggered'] == True
        if rebal_mask.sum() > 0:
            ax3.scatter(pnl_df.loc[rebal_mask, 'timestamp'], 
                       pnl_df.loc[rebal_mask, 'delta_pct_vs_initial'],
                       color='red', s=10, alpha=0.3, label=f'Rebal Trigger ({rebal_mask.sum()}x)', zorder=5)
        
        ax3.axhline(y=0, color='green', linestyle='-', alpha=0.5, linewidth=2, label='Perfect Neutral')
        ax3.axhline(y=5, color='orange', linestyle='--', alpha=0.5, label='+5% (trigger)', linewidth=1.5)
        ax3.axhline(y=-5, color='orange', linestyle='--', alpha=0.5, label='-5% (trigger)', linewidth=1.5)
        ax3.set_title(f'Market Neutrality & Rebalancing Triggers ({rebal_mask.sum()} triggers)')
        ax3.set_ylabel('Delta (%)')
        ax3.legend(loc='best', fontsize=7)
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(axis='x', rotation=45)
        
        # Plot 4: ETH Price Evolution (moved from Plot 5)
        ax4.plot(pnl_df['timestamp'], pnl_df['eth_price'], linewidth=2, color='purple')
        ax4.set_title('ETH/USD Price (Market-Neutral to This!)')
        ax4.set_ylabel('ETH Price ($)')
        ax4.grid(True, alpha=0.3)
        ax4.tick_params(axis='x', rotation=45)
        
        # Plot 5: Long vs Short Exposure (Exact ETH Equivalent)
        # Use the exact ETH equivalent values from the data
        exact_long_eth = pnl_df['exact_long_eth_exposure']
        exact_short_eth = pnl_df['exact_short_eth_exposure']
        exact_net_delta = pnl_df['exact_net_delta_eth']
        
        ax5.plot(pnl_df['timestamp'], exact_long_eth, label='Long ETH (exact equivalent)', linewidth=2, color='green', alpha=0.8)
        ax5.plot(pnl_df['timestamp'], exact_short_eth, label='Short ETH (perp shorts)', linewidth=2, color='red', alpha=0.8)
        ax5.fill_between(pnl_df['timestamp'], exact_long_eth, exact_short_eth, 
                         alpha=0.2, color='gray', label='Net Delta (exact)')
        
        # Add reference line for initial position
        initial_long = exact_long_eth.iloc[0]
        ax5.axhline(y=initial_long, color='green', linestyle=':', alpha=0.5, 
                   label=f'Initial Long ({initial_long:.1f} ETH)')
        
        ax5.set_title('Long vs Short Exposure (Exact ETH Equivalent)')
        ax5.set_ylabel('ETH Exposure')
        ax5.legend(loc='best', fontsize=8)
        ax5.grid(True, alpha=0.3)
        ax5.tick_params(axis='x', rotation=45)
        
        # Plot 6: All Venue Balances in ETH Equivalent (Single Axis)
        # Everything converted to ETH terms for consistency
        
        # AAVE position components
        ax6.plot(pnl_df['timestamp'], pnl_df['aave_weeth_balance_eth'], 
                label='AAVE weETH (converted to ETH)', linewidth=2, color='green', alpha=0.8)
        ax6.plot(pnl_df['timestamp'], pnl_df['aave_weth_debt_eth'], 
                label='AAVE WETH Debt', linewidth=2, color='red', alpha=0.8)
        ax6.plot(pnl_df['timestamp'], pnl_df['aave_net_position_eth'], 
                label='AAVE Net Position', linewidth=2.5, color='blue')
        
        # CEX short position (constant in ETH)
        ax6.plot(pnl_df['timestamp'], pnl_df['cex_perp_short_eth'], 
                label='CEX Perp Short (ETH, constant)', linewidth=2, color='orange', linestyle='--')
        
        # Net delta (AAVE net - perp short)
        ax6.plot(pnl_df['timestamp'], pnl_df['net_delta_eth'], 
                label='Net Delta (unhedged exposure)', linewidth=3, color='purple')
        
        # Reference lines
        ax6.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
        initial_eth = self.results['summary']['initial_eth_purchased']
        ax6.axhline(y=initial_eth, color='gray', linestyle=':', alpha=0.5, linewidth=1,
                   label=f'Initial ETH ({initial_eth:.1f})')
        
        # Styling
        ax6.set_title('All Venue Balances in ETH Equivalent - Shows Delta Drift!', 
                     fontsize=13, fontweight='bold')
        ax6.set_ylabel('ETH Equivalent', fontsize=11)
        ax6.set_xlabel('Date', fontsize=10)
        ax6.legend(loc='best', fontsize=8)
        ax6.grid(True, alpha=0.3)
        ax6.tick_params(axis='x', rotation=45)
        
        # Plot 8: Drawdown
        ax7.fill_between(pnl_df['timestamp'], 0, pnl_df['drawdown_pct'], 
                        alpha=0.3, color='red', label='Drawdown')
        ax7.plot(pnl_df['timestamp'], pnl_df['drawdown_pct'], linewidth=1.5, color='darkred')
        max_dd = pnl_df['drawdown_pct'].min()
        ax7.axhline(y=max_dd, color='red', linestyle='--', alpha=0.7, 
                   label=f'Max DD: {max_dd:.2f}%')
        ax7.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax7.set_title('Drawdown from Peak (%)')
        ax7.set_ylabel('Drawdown (%)')
        ax7.legend(loc='lower left')
        ax7.grid(True, alpha=0.3)
        ax7.tick_params(axis='x', rotation=45)
        ax7.set_ylim(top=1)
        
        plt.tight_layout()
        
        # Save plot
        plot_file = output_path / f"leveraged_restaking_USDT_analysis_{config_label}_{timestamp_str}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"📊 Plots saved to {plot_file}")
    
    def create_balance_sheet_plots(self, output_dir: str = "data/analysis") -> None:
        """Create detailed balance sheet visualization showing all wallet and CEX balances."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
        config_label = f"usdt_{int(self.config.initial_usdt/1000)}k"
        # No seasonal rewards config
        
        pnl_df = pd.DataFrame(self.results['hourly_pnl'])
        
        # Calculate balance-based P&L FIRST (before any plotting)
        # Use NET AAVE position (collateral - debt) for proper balance-based P&L
        pnl_df['aweeth_collateral_usd'] = pnl_df['aweeth_balance'] * pnl_df['weeth_price'] * pnl_df['eth_price']
        pnl_df['weth_debt_usd'] = pnl_df['weth_debt_underlying'] * pnl_df['eth_price']
        pnl_df['net_aave_position_usd'] = pnl_df['aweeth_collateral_usd'] - pnl_df['weth_debt_usd']
        pnl_df['total_value_usd'] = pnl_df['net_aave_position_usd'] + pnl_df['total_account_balance_usdt']
        summary = self.results['summary']
        initial_total_value_pre_cost = summary.get('initial_total_value_pre_cost_usd', pnl_df['total_value_usd'].iloc[0])
        pnl_df['balance_based_pnl_usd'] = pnl_df['total_value_usd'] - initial_total_value_pre_cost
        
        # Pre-calculate USDT values (using the corrected net AAVE position)
        pnl_df['eth_wallet_net_usd'] = pnl_df['net_aave_position_usd']  # Already calculated above
        pnl_df['total_equity_usd'] = pnl_df['net_aave_position_usd'] + pnl_df['total_account_balance_usdt']
        pnl_df['total_liabilities_usd'] = pnl_df['weth_debt_usd']
        
        # Balance-based P&L already calculated above
        
        # Sample for some plots (weekly)
        sample_interval = 168  # Weekly
        pnl_sample = pnl_df.iloc[::sample_interval].copy()
        
        # Set up plotting
        plt.style.use('seaborn-v0_8')
        fig = plt.figure(figsize=(24, 16))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        fig.suptitle('Complete Balance Sheet Evolution - All Wallets & Accounts', 
                     fontsize=16, fontweight='bold')
        
        # Create subplots
        ax1 = fig.add_subplot(gs[0, 0])  # ETH Wallet - Native Units
        ax2 = fig.add_subplot(gs[0, 1])  # ETH Wallet - USDT Equivalent
        ax3 = fig.add_subplot(gs[1, 0])  # CEX Margin (USDT)
        ax4 = fig.add_subplot(gs[1, 1])  # LTV & Health Factor (Balance Sheet Risk)
        ax5 = fig.add_subplot(gs[2, :])  # Complete Balance Sheet (USDT) - Full Width
        
        # Plot 1: Complete AAVE Token Hierarchy (6 Lines - Color Coordinated)
        # Show ERC-20 tokens, underlying claims, and ETH equivalent values
        
        # === ERC-20 TOKENS (Constant) ===
        # aWeETH: Constant ERC-20 balance (what wallet shows)
        ax1.plot(pnl_df['timestamp'], pnl_df['aweeth_scaled_balance'], 
                label='aWeETH (ERC-20 token, constant)', linewidth=3, color='darkgreen', alpha=0.9)
        
        # variableDebtWETH: Constant ERC-20 debt token (what wallet shows)
        ax1.plot(pnl_df['timestamp'], pnl_df['weth_debt_scaled_balance'], 
                label='variableDebtWETH (ERC-20 token, constant)', linewidth=3, color='darkred', alpha=0.9)
        
        # === UNDERLYING CLAIMS (Growing with Indices) ===
        # weETH: Underlying claim (what we can redeem, grows with liquidity index)
        ax1.plot(pnl_df['timestamp'], pnl_df['weeth_collateral_underlying'], 
                label='weETH (underlying claim, grows with index)', linewidth=2, color='lightgreen', alpha=0.8, linestyle='-')
        
        # WETH Debt: Underlying debt (what we owe, grows with borrow index)
        ax1.plot(pnl_df['timestamp'], pnl_df['weth_debt_underlying'], 
                label='WETH Debt (underlying debt, grows with index)', linewidth=2, color='red', alpha=0.8, linestyle='-')
        
        # === ETH EQUIVALENT VALUES (Growing with Oracle Price) ===
        # ETH equivalent collateral: weETH underlying × weETH/ETH oracle price
        ax1.plot(pnl_df['timestamp'], pnl_df['weeth_collateral_underlying'] * pnl_df['weeth_price'], 
                label='ETH Equivalent (collateral × oracle price)', linewidth=2, color='blue', alpha=0.8, linestyle='--')
        
        # ETH equivalent debt: WETH debt × 1 (WETH = ETH, 1:1)
        ax1.plot(pnl_df['timestamp'], pnl_df['weth_debt_underlying'], 
                label='ETH Equivalent (debt, WETH=ETH 1:1)', linewidth=2, color='orange', alpha=0.8, linestyle='--')
        
        ax1.set_title('Complete AAVE Token Hierarchy - ERC-20 → Underlying → ETH Equivalent', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Token Amount')
        ax1.legend(loc='best', fontsize=7)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # Add annotations showing the growth
        initial_aweeth = pnl_df['aweeth_scaled_balance'].iloc[0]
        final_weeth_underlying = pnl_df['weeth_collateral_underlying'].iloc[-1]
        initial_debt_scaled = pnl_df['weth_debt_scaled_balance'].iloc[0]
        final_debt_underlying = pnl_df['weth_debt_underlying'].iloc[-1]
        final_eth_collateral = (pnl_df['weeth_collateral_underlying'] * pnl_df['weeth_price']).iloc[-1]
        initial_eth_collateral = (pnl_df['weeth_collateral_underlying'] * pnl_df['weeth_price']).iloc[0]
        
        ax1.text(0.02, 0.98, 
                f'ERC-20 Tokens (constant):\\n'
                f'  aWeETH: {initial_aweeth:.2f}\\n'
                f'  Debt token: {initial_debt_scaled:.2f}\\n'
                f'Underlying Claims (index growth):\\n'
                f'  weETH: {final_weeth_underlying:.2f} (+{((final_weeth_underlying/initial_aweeth)-1)*100:.1f}%)\\n'
                f'  WETH debt: {final_debt_underlying:.2f} (+{((final_debt_underlying/initial_debt_scaled)-1)*100:.1f}%)\\n'
                f'ETH Equivalent (oracle growth):\\n'
                f'  Collateral: {final_eth_collateral:.2f} (+{((final_eth_collateral/initial_eth_collateral)-1)*100:.1f}%)',
                transform=ax1.transAxes, fontsize=7, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # Plot 2: ETH Wallet in USDT Equivalent
        ax2.fill_between(pnl_df['timestamp'], 0, pnl_df['aweeth_collateral_usd']/1000, 
                        alpha=0.3, color='green', label='Assets (aWeETH)')
        ax2.fill_between(pnl_df['timestamp'], 0, pnl_df['weth_debt_usd']/1000, 
                        alpha=0.3, color='red', label='Liabilities (WETH debt)')
        ax2.plot(pnl_df['timestamp'], pnl_df['eth_wallet_net_usd']/1000, 
                label='Net Equity', linewidth=3, color='blue')
        
        ax2.set_title('Ethereum Wallet - USDT Equivalent ($k)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Value ($k)')
        ax2.legend(loc='best', fontsize=9)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)
        
        # Plot 3: CEX Margin Balances (USDT) - Per Exchange Detail
        # Calculate maintenance margins first (10% of exposure, not total margin)
        binance_maint_margin = pnl_df['binance_exposure_usdt'].iloc[0] * self.config.maintenance_margin_ratio
        bybit_maint_margin = pnl_df['bybit_exposure_usdt'].iloc[0] * self.config.maintenance_margin_ratio
        okx_maint_margin = pnl_df['okx_exposure_usdt'].iloc[0] * self.config.maintenance_margin_ratio
        total_maint_margin = binance_maint_margin + bybit_maint_margin + okx_maint_margin
        
        ax3.plot(pnl_df['timestamp'], pnl_df['binance_account_balance_usdt']/1000, 
                label='Binance Account', linewidth=2, color='orange', alpha=0.9)
        ax3.plot(pnl_df['timestamp'], pnl_df['bybit_account_balance_usdt']/1000, 
                label='Bybit Account', linewidth=2, color='purple', alpha=0.9)
        ax3.plot(pnl_df['timestamp'], pnl_df['okx_account_balance_usdt']/1000, 
                label='OKX Account', linewidth=2, color='blue', alpha=0.9)
        ax3.plot(pnl_df['timestamp'], pnl_df['total_account_balance_usdt']/1000, 
                label='Total CEX Margin', linewidth=2.5, color='black')
        
        # Add per-exchange maintenance margin thresholds (liquidation risk lines)
        ax3.axhline(y=binance_maint_margin/1000, color='orange', linestyle='--', alpha=0.7, 
                   linewidth=2, label=f'Binance Liq. Risk (${binance_maint_margin/1000:.1f}k)')
        ax3.axhline(y=bybit_maint_margin/1000, color='purple', linestyle='--', alpha=0.7, 
                   linewidth=2, label=f'Bybit Liq. Risk (${bybit_maint_margin/1000:.1f}k)')
        ax3.axhline(y=okx_maint_margin/1000, color='blue', linestyle='--', alpha=0.7, 
                   linewidth=2, label=f'OKX Liq. Risk (${okx_maint_margin/1000:.1f}k)')
        ax3.axhline(y=total_maint_margin/1000, color='darkred', linestyle='-', alpha=0.8, 
                   linewidth=3, label=f'Total Liq. Risk (${total_maint_margin/1000:.1f}k)')
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1)
        
        # Highlight negative region
        ax3.fill_between(pnl_sample['timestamp'], 
                        pnl_sample['total_account_balance_usdt']/1000, 
                        0, 
                        where=(pnl_sample['total_account_balance_usdt'] < 0),
                        alpha=0.2, color='red', label='LIQUIDATED')
        
        ax3.set_title('CEX Margin Balances - USDT ($k)', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Margin Balance ($k)')
        ax3.legend(loc='best', fontsize=9)
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(axis='x', rotation=45)
        
        # Plot 4: LTV & Health Factor (Balance Sheet Risk Metrics)
        # Calculate ETH equivalent LTV using exact token mechanics
        eth_collateral = pnl_df['weeth_collateral_underlying'] * pnl_df['weeth_price']
        eth_debt = pnl_df['weth_debt_underlying']  # WETH = ETH (1:1)
        eth_ltv = eth_debt / eth_collateral
        
        # Plot LTV (left axis) - Better colors for readability
        ax4_twin = ax4.twinx()
        ax4.plot(pnl_df['timestamp'], eth_ltv, linewidth=3, color='darkred', alpha=0.9, label='LTV (ETH equivalent)')
        ax4_twin.plot(pnl_df['timestamp'], pnl_df['health_factor'], linewidth=3, color='darkblue', alpha=0.9, label='Health Factor')
        
        # LTV reference lines - Clear colors
        ax4.axhline(y=0.93, color='red', linestyle='--', alpha=0.7, linewidth=2, label='Max LTV (93%)')
        ax4.axhline(y=0.9094, color='orange', linestyle=':', alpha=0.8, linewidth=2, label='Target LTV (90.94%)')
        
        # Health Factor reference lines - Clear colors
        ax4_twin.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, linewidth=2, label='Liquidation (HF=1.0)')
        ax4_twin.axhline(y=1.015, color='orange', linestyle=':', alpha=0.8, linewidth=2, label='Warning (HF=1.015)')
        
        # Styling with better contrast
        ax4.set_title('LTV & Health Factor (Balance Sheet Risk)', fontsize=12, fontweight='bold')
        ax4.set_ylabel('LTV Ratio', color='darkred', fontweight='bold')
        ax4_twin.set_ylabel('Health Factor', color='darkblue', fontweight='bold')
        ax4.set_ylim(0.85, 0.95)
        ax4_twin.set_ylim(0.95, 1.1)
        
        # Color the y-axis labels to match the lines
        ax4.tick_params(axis='y', labelcolor='darkred')
        ax4_twin.tick_params(axis='y', labelcolor='darkblue')
        
        # Combined legend with better positioning
        lines1, labels1 = ax4.get_legend_handles_labels()
        lines2, labels2 = ax4_twin.get_legend_handles_labels()
        ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=7, framealpha=0.9)
        
        ax4.grid(True, alpha=0.3)
        ax4.tick_params(axis='x', rotation=45)
        
        # Plot 5: Complete Balance Sheet (Stacked Bar Chart Over Time)
        # Sample every week for readability
        sample_interval = 168  # Weekly
        pnl_sample = pnl_df.iloc[::sample_interval].copy()
        
        # Create stacked area chart
        ax5.fill_between(pnl_sample['timestamp'], 0, 
                        pnl_sample['aweeth_collateral_usd']/1000,
                        label='ETH Wallet Assets (aWeETH)', alpha=0.6, color='green')
        ax5.fill_between(pnl_sample['timestamp'], 0,
                        -pnl_sample['weth_debt_usd']/1000,
                        label='ETH Wallet Liabilities (WETH debt)', alpha=0.6, color='red')
        ax5.plot(pnl_sample['timestamp'], 
                pnl_sample['total_account_balance_usdt']/1000,
                label='CEX Margin (USDT)', linewidth=2.5, color='orange', marker='o', markersize=3)
        ax5.plot(pnl_sample['timestamp'], 
                pnl_sample['total_equity_usd']/1000,
                label='TOTAL EQUITY', linewidth=3.5, color='black', marker='s', markersize=4)
        
        # Add initial capital reference line
        initial_capital = self.config.initial_usdt
        ax5.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1.5)
        ax5.axhline(y=initial_capital/1000, color='gray', linestyle=':', alpha=0.6,
                   linewidth=2, label=f'Initial: ${initial_capital/1000:.0f}k')
        
        ax5.set_title('Complete Balance Sheet Evolution (Weekly Snapshots)', 
                     fontsize=13, fontweight='bold')
        ax5.set_ylabel('Value ($k)')
        ax5.set_xlabel('Date')
        ax5.legend(loc='best', fontsize=10)
        ax5.grid(True, alpha=0.3)
        ax5.tick_params(axis='x', rotation=45)
        
        # Add final values annotation
        final_annotation = (
            f'FINAL BALANCES:\n'
            f'━━━━━━━━━━━━━━━━━━━━━\n'
            f'ETH Wallet:\n'
            f'  aWeETH: {pnl_df["aweeth_balance"].iloc[-1]:.2f} tokens\n'
            f'  Value: ${pnl_df["aweeth_collateral_usd"].iloc[-1]/1000:.1f}k\n'
            f'  WETH Debt: ${pnl_df["weth_debt_usd"].iloc[-1]/1000:.1f}k\n'
            f'  Net: ${pnl_df["eth_wallet_net_usd"].iloc[-1]/1000:.1f}k\n'
            f'\n'
            f'CEX Accounts:\n'
            f'  Binance: ${pnl_df["binance_account_balance_usdt"].iloc[-1]/1000:.1f}k\n'
            f'  Bybit: ${pnl_df["bybit_account_balance_usdt"].iloc[-1]/1000:.1f}k\n'
            f'  OKX: ${pnl_df["okx_account_balance_usdt"].iloc[-1]/1000:.1f}k\n'
            f'  Total: ${pnl_df["total_account_balance_usdt"].iloc[-1]/1000:.1f}k\n'
            f'\n'
            f'TOTAL EQUITY: ${pnl_df["total_equity_usd"].iloc[-1]/1000:.1f}k'
        )
        ax5.text(0.98, 0.98, final_annotation,
                transform=ax5.transAxes, fontsize=10, verticalalignment='top',
                horizontalalignment='right', 
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95),
                family='monospace')
        
        plt.tight_layout()
        
        # Save balance sheet plot
        balance_plot_file = output_path / f"leveraged_restaking_USDT_balance_sheet_{config_label}_{timestamp_str}.png"
        plt.savefig(balance_plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"💰 Balance sheet plots saved to {balance_plot_file}")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze USDT market-neutral leveraged restaking")
    parser.add_argument("--start-date", type=str, default="2024-05-12", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2025-09-18", help="End date (YYYY-MM-DD)")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--output-dir", type=str, default="data/analysis", help="Output directory")
    parser.add_argument("--initial-usdt", type=float, default=100000.0, help="Initial USDT amount")
    parser.add_argument("--allocation-long-pct", type=float, default=0.50, help="% allocated to long restaking (default: 50%)")
    parser.add_argument("--max-leverage-iterations", type=int, default=None, help="Max leverage iterations")
    # --eigen-only removed - no seasonal rewards
    parser.add_argument("--fixed-balance-pnl", action="store_true", help="Fixed balance P&L mode")
    parser.add_argument("--spot-venue", type=str, default="BINANCE", choices=['BINANCE', 'UNISWAP'], help="Spot ETH purchase venue (default: BINANCE)")
    parser.add_argument("--use-flash", action="store_true", help="Use atomic flash loan entry (single tx) instead of recursive loop")
    parser.add_argument("--flash-source", type=str, default="BALANCER", choices=['BALANCER', 'MORPHO', 'AAVE'], help="Flash loan source (default: BALANCER = 0 bps)")
    parser.add_argument("--max-stake-spread-move", type=float, default=0.02215, help="Max expected adverse weETH/ETH oracle move (default: 0.02215 = 2.215%)")
    parser.add_argument("--no-plots", action="store_true", help="Skip plots")
    
    args = parser.parse_args()
    
    try:
        analyzer = USDTLeveragedRestakingAnalyzer(args.data_dir)
        analyzer.config.initial_usdt = args.initial_usdt
        analyzer.config.allocation_to_long_pct = args.allocation_long_pct
        analyzer.config.max_leverage_iterations = args.max_leverage_iterations
        # No seasonal rewards config
        analyzer.config.fixed_balance_pnl = args.fixed_balance_pnl
        analyzer.config.spot_venue = args.spot_venue
        analyzer.config.use_flash_one_shot = args.use_flash
        analyzer.config.flash_source = args.flash_source
        analyzer.config.max_stake_spread_move = args.max_stake_spread_move
        
        # Calculate target LTV from max_stake_spread_move
        # target_ltv = max_ltv * (1 - max_stake_spread_move)
        # max_ltv is always 0.93 (AAVE protocol limit)
        target_ltv = analyzer.config.max_ltv * (1 - analyzer.config.max_stake_spread_move)
        
        # Set flash fee based on source
        if args.flash_source in ['BALANCER', 'MORPHO']:
            analyzer.config.flash_fee_bps = 0.0
        elif args.flash_source == 'AAVE':
            analyzer.config.flash_fee_bps = 5.0
        
        leverage_mode_label = "⚡ ATOMIC FLASH LOAN" if args.use_flash else "🔄 RECURSIVE LOOP"
        
        print("🎯 USDT Market-Neutral Leveraged Restaking Analysis")
        print(f"📅 Date range: {args.start_date} to {args.end_date}")
        print(f"💰 Initial USDT: ${args.initial_usdt:,.2f}")
        print(f"📊 Long/Hedge Split: {args.allocation_long_pct*100:.0f}% / {(1-args.allocation_long_pct)*100:.0f}%")
        print(f"⚙️  Leverage Mode: {leverage_mode_label}")
        if args.use_flash:
            print(f"   Flash Source: {args.flash_source} ({analyzer.config.flash_fee_bps} bps fee)")
            print(f"   Max Stake Spread Move: {args.max_stake_spread_move*100:.3f}% (oracle risk buffer)")
            print(f"   Target LTV: {target_ltv:.4f} (= {analyzer.config.max_ltv} × (1 - {args.max_stake_spread_move:.5f}))")
        print()
        
        results = analyzer.run_analysis(args.start_date, args.end_date)
        
        # Save results
        analyzer.save_results(args.output_dir)
        
        # Create plots
        if not args.no_plots:
            analyzer.create_plots(args.output_dir)
            analyzer.create_balance_sheet_plots(args.output_dir)
        
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
