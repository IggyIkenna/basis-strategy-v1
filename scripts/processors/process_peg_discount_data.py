"""
Process LST Peg Discount/Premium Data

Processes LST peg discount/premium data for staking spread risk analysis:
- Uses AAVE oracle prices as benchmark fair value (replaces manual CSV files)
- Analyzes market rates vs AAVE oracle rates (protocol fair value)
- Determines optimal entry/exit routes (DEX vs direct staking)
- Incorporates gas costs and execution costs for realistic cost comparison
- Calculates staking spread risk for risk management

🔄 HOURLY DATA SUPPORT:
- Uses pre-interpolated hourly AAVE oracle data (from fetch_aave_data.py)
- All AAVE data (oracle, rates, reserves) is automatically interpolated to hourly
- No interpolation needed in this processor - uses ready hourly data

Input: 
- data/protocol_data/aave/oracle/*_ETH_oracle_*_hourly.csv (hourly interpolated)
- data/market_data/spot_prices/lst_eth_ratios/*.csv (market rates from DEX pools)
Output: data/protocol_data/staking/peg_analysis/*_peg_analysis_*.csv
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import logging
import numpy as np

class PegDiscountProcessor:
    """Process LST peg discount/premium data for staking analysis."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.oracle_dir = self.data_dir / "protocol_data" / "aave" / "oracle"
        self.market_dir = self.data_dir / "market_data" / "spot_prices" / "lst_eth_ratios"
        self.output_dir = self.data_dir / "protocol_data" / "staking" / "peg_analysis"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Cost lookup directories
        self.execution_costs_file = self.data_dir / "execution_costs" / "lookup_tables" / "execution_costs_lookup.json"
        
        # Trading size for cost simulation ($10k worth)
        self.simulation_size_usd = 10000
        
        # Gas units for operations (from analyze_gas_costs.py)
        self.gas_operations = {
            "STAKE_DEPOSIT": 150000,    # Direct protocol staking
            "TOKEN_SWAP": 180000,       # DEX swap to LST
        }
        
        # Set up logging
        self.logger = logging.getLogger("peg_processor")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info("LST Peg Discount Processor initialized")
        
        # Load cost data
        self._load_cost_data()
    
    def _load_cost_data(self):
        """Load execution costs data."""
        try:
            # Load execution costs lookup
            if self.execution_costs_file.exists():
                with open(self.execution_costs_file, 'r') as f:
                    self.execution_costs_lookup = json.load(f)
                
                # Count total records
                total_pairs = len(self.execution_costs_lookup)
                self.logger.info(f"✅ Loaded execution costs lookup table with {total_pairs} trading pairs")
            else:
                self.logger.warning(f"⚠️ Execution costs file not found: {self.execution_costs_file}")
                self.execution_costs_lookup = None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to load cost data: {e}")
            self.execution_costs_lookup = None
    
    def _get_execution_cost_usd(self, date: str, trading_pair: str, operation: str) -> float:
        """Get execution cost in USD for a specific date, trading pair, and operation."""
        if self.execution_costs_lookup is None:
            return 0.0
        
        try:
            # Parse date to get date string (YYYY-MM-DD)
            target_date = pd.to_datetime(date).strftime('%Y-%m-%d')
            
            # Get the trading pair data
            pair_data = self.execution_costs_lookup.get(trading_pair, {})
            if not pair_data:
                return 0.0
            
            # Get the size data (10k for $10,000 trades)
            size_key = f"{self.simulation_size_usd // 1000}k"
            size_data = pair_data.get(size_key, {})
            if not size_data:
                return 0.0
            
            # Get the cost for the specific date
            cost_usd = size_data.get(target_date, 0)
            return float(cost_usd)
            
        except Exception as e:
            self.logger.debug(f"Execution cost lookup failed for {date}, {trading_pair}: {e}")
            return 0.0
    
    def _get_execution_cost_bps(self, date: str, pair: str, size_bucket: str = "10k") -> float:
        """Get execution cost in basis points for a specific date and pair."""
        if self.execution_costs_lookup is None:
            return 0.0
        
        try:
            # Format pair for lookup (replace / with _)
            pair_key = pair.replace('/', '_')
            
            if pair_key not in self.execution_costs_lookup:
                return 0.0
            
            if size_bucket not in self.execution_costs_lookup[pair_key]:
                return 0.0
            
            # Get cost for the specific date
            date_costs = self.execution_costs_lookup[pair_key][size_bucket]
            if date in date_costs:
                return float(date_costs[date])
            else:
                # Return a default cost if date not found
                costs = list(date_costs.values())
                return float(costs[0]) if costs else 0.0
                
        except Exception as e:
            self.logger.debug(f"Execution cost lookup failed for {date}, {pair}: {e}")
            return 0.0
    
    def _calculate_total_costs(self, date: str, asset: str, premium_percent: float) -> Dict[str, float]:
        """
        Calculate total costs for both direct staking and DEX routes.
        
        Args:
            date: Date string (YYYY-MM-DD)
            asset: Asset name (e.g., 'wstETH', 'weETH')
            premium_percent: Market premium/discount percentage
            
        Returns:
            Dictionary with cost breakdown for both routes
        """
        costs = {
            'direct_gas_cost_usd': 0.0,
            'dex_gas_cost_usd': 0.0,
            'dex_execution_cost_bps': 0.0,
            'dex_execution_cost_usd': 0.0,
            'total_direct_cost_usd': 0.0,
            'total_dex_cost_usd': 0.0,
            'cost_difference_usd': 0.0,
            'optimal_route_by_cost': 'direct_staking'
        }
        
        try:
            # Execution costs for direct staking (using ETH_wstETH or ETH_weETH pair)
            direct_pair = f"ETH_{asset}"
            costs['direct_gas_cost_usd'] = self._get_execution_cost_usd(date, direct_pair, "STAKE_DEPOSIT")
            
            # Execution costs for DEX swap (using ETH_wstETH or ETH_weETH pair)
            costs['dex_gas_cost_usd'] = self._get_execution_cost_usd(date, direct_pair, "TOKEN_SWAP")
            
            # Execution costs for DEX (basis points)
            pair = f"ETH/{asset}"
            costs['dex_execution_cost_bps'] = self._get_execution_cost_bps(date, pair)
            
            # Convert execution cost to USD (basis points to dollar amount)
            costs['dex_execution_cost_usd'] = (costs['dex_execution_cost_bps'] / 10000) * self.simulation_size_usd
            
            # Total costs
            costs['total_direct_cost_usd'] = costs['direct_gas_cost_usd']
            costs['total_dex_cost_usd'] = costs['dex_gas_cost_usd'] + costs['dex_execution_cost_usd']
            
            # Cost difference (positive means DEX is more expensive)
            costs['cost_difference_usd'] = costs['total_dex_cost_usd'] - costs['total_direct_cost_usd']
            
            # Determine optimal route by cost alone
            costs['optimal_route_by_cost'] = 'direct_staking' if costs['cost_difference_usd'] > 0 else 'dex_swap'
            
        except Exception as e:
            self.logger.debug(f"Cost calculation failed for {date}, {asset}: {e}")
        
        return costs
    
    def _determine_optimal_route_with_costs(self, premium_percent: float, costs: Dict[str, float], asset: str = None) -> str:
        """
        Determine optimal route considering both peg premium and transaction costs.
        
        Args:
            premium_percent: Market premium/discount percentage
            costs: Cost breakdown from _calculate_total_costs
            asset: Asset name for protocol-specific routing
            
        Returns:
            Optimal route string
        """
        # Calculate the value of the premium/discount in USD terms
        # Note: premium_percent is in percentage form (e.g., -0.36 = -36 bps)
        premium_value_usd = (premium_percent / 100) * self.simulation_size_usd
        
        # If market is at discount, we save money buying on DEX
        # But we need to account for the additional costs
        if premium_percent < 0:  # Market discount
            # Savings from buying at discount
            discount_savings_usd = abs(premium_value_usd)
            
            # Net benefit = savings from discount - additional DEX costs
            net_dex_benefit = discount_savings_usd - costs['cost_difference_usd']
            
            if net_dex_benefit > 0:
                return "dex_swap"  # DEX is better even after costs
        
        # Default to direct staking (premium market or costs too high for DEX)
        if asset == 'weETH':
            return "direct_etherfi"
        else:
            return "direct_lido"
    
    
    def _classify_peg_status(self, premium_percent: float) -> str:
        """Classify peg status based on premium/discount."""
        if premium_percent > 0.5:
            return "premium"
        elif premium_percent < -0.5:
            return "discount"
        else:
            return "at_peg"
    
    def _determine_optimal_route(self, premium_percent: float, asset: str = None) -> str:
        """Determine optimal entry/exit route based on peg premium."""
        # If market is at discount (negative premium), DEX is cheaper
        # If market is at premium or peg, direct protocol is better
        if premium_percent < -0.1:  # More than 0.1% discount
            return "dex_swap"
        else:
            # Use appropriate direct route based on asset
            if asset == 'weETH':
                return "direct_etherfi"
            else:
                return "direct_lido"
    
    def _load_aave_oracle_data(self, asset: str) -> pd.DataFrame:
        """Load AAVE oracle data for an asset (fair value benchmark) - uses hourly data from oracle processor."""
        # Try to load hourly interpolated data with _hourly suffix first
        oracle_file_hourly = self.oracle_dir / f"{asset}_ETH_oracle_2024-01-01_2025-09-18_hourly.csv"
        # Then try the standard oracle file (which is now hourly from the oracle processor)
        oracle_file_standard = self.oracle_dir / f"{asset}_ETH_oracle_2024-01-01_2025-09-18.csv"
        
        if oracle_file_hourly.exists():
            # Use pre-interpolated hourly data with _hourly suffix
            self.logger.info(f"📄 Loading hourly AAVE oracle data: {oracle_file_hourly.name}")
            df = pd.read_csv(oracle_file_hourly, comment='#')
        elif oracle_file_standard.exists():
            # Use standard oracle file (which is now hourly from oracle processor)
            self.logger.info(f"📄 Loading AAVE oracle data: {oracle_file_standard.name}")
            df = pd.read_csv(oracle_file_standard, comment='#')
        else:
            raise FileNotFoundError(f"AAVE oracle data not found: {oracle_file_standard}")
        
        # Convert timestamp to datetime and create date column
        # Handle both Unix timestamps and datetime strings
        if df['timestamp'].dtype == 'object':
            # Try to parse as datetime string first
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except:
                # Fallback to Unix timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        else:
            # Assume it's a Unix timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Ensure timezone consistency - convert to UTC if timezone-aware, or assume UTC if naive
        if df['timestamp'].dt.tz is not None:
            df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
        else:
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        
        df['date'] = df['timestamp'].dt.strftime('%Y-%m-%d')
        
        # Rename oracle price column for clarity
        df = df.rename(columns={'oracle_price_eth': 'protocol_rate'})
        
        # Check if this is hourly data by looking at the time intervals
        if len(df) > 1:
            time_diff = df['timestamp'].iloc[1] - df['timestamp'].iloc[0]
            if time_diff.total_seconds() == 3600:  # 1 hour
                self.logger.info(f"📊 Loaded {len(df):,} hourly oracle records")
            else:
                self.logger.info(f"📊 Loaded {len(df):,} oracle records (daily data)")
        else:
            self.logger.info(f"📊 Loaded {len(df):,} oracle records")
        
        return df
    
    def _load_market_data(self, asset: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Load market data from the appropriate DEX pool for each asset.
        
        Args:
            asset: Asset symbol (wstETH uses Uniswap, weETH uses Curve)
            start_date: Optional start date for coverage validation (YYYY-MM-DD)
            end_date: Optional end date for coverage validation (YYYY-MM-DD)
            
        Returns:
            Market data DataFrame from the appropriate DEX
            
        Raises:
            ValueError: If required date coverage is not available
        """
        # Each asset has its specific DEX pool
        if asset == 'wstETH':
            # wstETH uses Uniswap V3
            market_files = list(self.market_dir.glob(f"uniswapv3_{asset}WETH_*.csv"))
            dex_name = 'uniswap'
        elif asset == 'weETH':
            # weETH uses Curve
            market_files = list(self.market_dir.glob(f"curve_{asset}WETH_*.csv"))
            dex_name = 'curve'
        else:
            raise ValueError(f"Unknown asset: {asset}")
        
        if not market_files:
            raise FileNotFoundError(f"No {dex_name} market data found for {asset} in {self.market_dir}")
        
        market_file = market_files[0]
        self.logger.info(f"📄 Loading {dex_name} data for {asset}: {market_file.name}")
        
        df = pd.read_csv(market_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Ensure timezone consistency - localize to UTC
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        
        df['date'] = df['timestamp'].dt.strftime('%Y-%m-%d')
        df['dex'] = dex_name
        df = df[['timestamp', 'date', 'close', 'dex']].rename(columns={'close': 'market_rate'})
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Apply 24-hour rolling median to smooth market prices
        df['market_rate_median_24h'] = df['market_rate'].rolling(window=24, min_periods=24).median()
        # Use the median price as the market rate (will have NaN for first 24 points)
        df['market_rate'] = df['market_rate_median_24h']
        
        # Validate date coverage if requested
        if start_date and end_date:
            self._validate_market_data_coverage(df, asset, start_date, end_date)
        
        # Count valid records (excluding first 24 NaN values)
        valid_records = len(df.dropna(subset=['market_rate']))
        self.logger.info(f"📊 Loaded {asset} market data: {len(df):,} total records, {valid_records:,} valid (24h median) from {dex_name}")
        
        return df
    
    def _validate_market_data_coverage(self, df: pd.DataFrame, asset: str, start_date: str, end_date: str):
        """
        Validate that the market data covers the required date range.
        
        Args:
            df: DataFrame with timestamp column
            asset: Asset symbol for error messages
            start_date: Required start date (YYYY-MM-DD)
            end_date: Required end date (YYYY-MM-DD)
            
        Raises:
            ValueError: If data coverage is insufficient
        """
        if len(df) == 0:
            raise ValueError(f"No market data available for {asset}")
        
        # Get actual date range from data
        actual_start = df['timestamp'].min()
        actual_end = df['timestamp'].max()
        
        # Convert requested dates to datetime
        req_start = pd.to_datetime(start_date)
        req_end = pd.to_datetime(end_date)
        
        # Check coverage
        if actual_start > req_start:
            raise ValueError(f"Market data coverage gap for {asset}: missing data from {req_start.date()} to {actual_start.date()}")
        
        if actual_end < req_end:
            raise ValueError(f"Market data coverage gap for {asset}: missing data from {actual_end.date()} to {req_end.date()}")
        
        self.logger.info(f"✅ {asset} market data coverage validated: {actual_start.date()} to {actual_end.date()}")
    
    def _process_peg_data_generic(self, asset: str) -> Dict:
        """Generic function to process peg discount/premium data for any LST using AAVE oracle."""
        self.logger.info(f"🔄 Processing {asset} peg discount/premium data using AAVE oracle...")
        
        try:
            # Load AAVE oracle data (fair value benchmark)
            oracle_df = self._load_aave_oracle_data(asset)
            
            # Load market data from DEX pools
            market_df = self._load_market_data(asset)
            
            # Merge oracle and market data on timestamp
            df = oracle_df.merge(market_df, on='timestamp', how='inner', suffixes=('_oracle', '_market'))
            
            # Remove rows where market_rate is NaN (first 24 hours of 24h median)
            df = df.dropna(subset=['market_rate'])
            
            # Calculate peg premium/discount
            df['peg_premium_percent'] = ((df['market_rate'] - df['protocol_rate']) / df['protocol_rate']) * 100
            
            # Add analysis columns
            df['asset'] = asset
            df['base_asset'] = 'ETH'
            df['source'] = 'aave_oracle_derived'
            df['processed_date'] = datetime.now().isoformat()
            
            # Sort by timestamp
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Calculate costs for each row
            self.logger.info("🔄 Calculating transaction costs for optimal route determination...")
            cost_columns = [
                'direct_gas_cost_usd', 'dex_gas_cost_usd', 'dex_execution_cost_bps', 
                'dex_execution_cost_usd', 'total_direct_cost_usd', 'total_dex_cost_usd',
                'cost_difference_usd', 'optimal_route_by_cost', 'net_dex_benefit_usd'
            ]
            
            for col in cost_columns:
                df[col] = 0.0
            
            # Determine protocol-specific route
            if asset == 'weETH':
                default_route = 'direct_etherfi'
            else:
                default_route = 'direct_lido'
            
            df['optimal_route_with_costs'] = default_route
            
            for idx, row in df.iterrows():
                if pd.notna(row.get('date_oracle')) and pd.notna(row.get('peg_premium_percent')):
                    costs = self._calculate_total_costs(row['date_oracle'], asset, row['peg_premium_percent'])
                    
                    # Update cost columns
                    for cost_key, cost_value in costs.items():
                        if cost_key in df.columns:
                            df.at[idx, cost_key] = cost_value
                    
                    # Calculate net DEX benefit
                    # Note: peg_premium_percent is in percentage form (e.g., -0.36 = -36 bps)
                    premium_value_usd = (row['peg_premium_percent'] / 100) * self.simulation_size_usd
                    if row['peg_premium_percent'] < 0:  # Discount
                        discount_savings_usd = abs(premium_value_usd)
                        net_benefit = discount_savings_usd - costs['cost_difference_usd']
                        df.at[idx, 'net_dex_benefit_usd'] = net_benefit
                    
                    # Determine optimal route with costs
                    df.at[idx, 'optimal_route_with_costs'] = self._determine_optimal_route_with_costs(
                        row['peg_premium_percent'], costs, asset
                    )
            
            # Classify peg status (keep for analysis)
            df['peg_status'] = df['peg_premium_percent'].apply(self._classify_peg_status)
            
            # Calculate summary statistics
            avg_premium = df['peg_premium_percent'].mean()
            std_premium = df['peg_premium_percent'].std()
            min_premium = df['peg_premium_percent'].min()
            max_premium = df['peg_premium_percent'].max()
            
            # Count route recommendations (cost-aware only)
            direct_count_with_costs = len(df[df['optimal_route_with_costs'] == default_route])
            dex_count_with_costs = len(df[df['optimal_route_with_costs'] == 'dex_swap'])
            
            # Cost analysis
            avg_direct_cost = df['total_direct_cost_usd'].mean()
            avg_dex_cost = df['total_dex_cost_usd'].mean()
            avg_cost_diff = df['cost_difference_usd'].mean()
            
            # Count profitable DEX opportunities
            profitable_dex = len(df[df['net_dex_benefit_usd'] > 0])
            
            self.logger.info(f"📊 {asset} Peg Analysis Results:")
            self.logger.info(f"   Average premium: {avg_premium:.2f}%")
            self.logger.info(f"   Premium std dev: {std_premium:.2f}%")
            self.logger.info(f"   Premium range: {min_premium:.2f}% to {max_premium:.2f}%")
            self.logger.info(f"   Optimal routes (cost-aware): {direct_count_with_costs} direct, {dex_count_with_costs} DEX")
            self.logger.info(f"   Average costs: Direct ${avg_direct_cost:.2f}, DEX ${avg_dex_cost:.2f}")
            self.logger.info(f"   Profitable DEX opportunities: {profitable_dex}/{len(df)} ({profitable_dex/len(df)*100:.1f}%)")
            
            # Save processed data
            output_file = self.output_dir / f"{asset}_peg_analysis_2024-01-01_2025-09-18.csv"
            df.to_csv(output_file, index=False)
            
            # Create summary
            protocol_key = 'direct_etherfi' if asset == 'weETH' else 'direct_lido'
            
            summary = {
                'processing_completed': datetime.now().isoformat(),
                'data_sources': {
                    'fair_value_source': 'aave_oracle_derived_hourly',
                    'market_data_source': 'dex_pools_24h_median',
                    'oracle_file': f"{asset}_ETH_oracle_2024-01-01_2025-09-18_hourly.csv",
                    'market_files': list(market_df['dex'].unique()),
                    'market_methodology': '24_hour_rolling_median',
                    'aave_interpolation': 'pre_interpolated_by_fetch_aave_data'
                },
                'output_file': output_file.name,
                'records_processed': len(df),
                'asset': asset,
                'base_asset': 'ETH',
                'peg_statistics': {
                    'average_premium_percent': avg_premium,
                    'std_dev_premium_percent': std_premium,
                    'min_premium_percent': min_premium,
                    'max_premium_percent': max_premium
                },
                'route_analysis': {
                    f'{protocol_key}_optimal': direct_count_with_costs,
                    'dex_swap_optimal': dex_count_with_costs,
                    f'{protocol_key}_percentage': (direct_count_with_costs / len(df)) * 100,
                    'dex_swap_percentage': (dex_count_with_costs / len(df)) * 100
                },
                'cost_analysis': {
                    'simulation_size_usd': self.simulation_size_usd,
                    'average_direct_cost_usd': avg_direct_cost,
                    'average_dex_cost_usd': avg_dex_cost,
                    'average_cost_difference_usd': avg_cost_diff,
                    'profitable_dex_opportunities': profitable_dex,
                    'profitable_dex_percentage': (profitable_dex / len(df)) * 100,
                    f'{protocol_key}_optimal_with_costs': direct_count_with_costs,
                    'dex_swap_optimal_with_costs': dex_count_with_costs
                },
                'usage': {
                    'purpose': 'staking_spread_risk_analysis',
                    'integration': 'backtest_entry_exit_route_optimization',
                    'methodology': 'aave_oracle_as_fair_value_benchmark'
                }
            }
            
            # Save summary
            summary_file = self.output_dir / f"{asset}_peg_analysis_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.logger.info(f"💾 Output: {output_file}")
            self.logger.info(f"💾 Summary: {summary_file}")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ {asset} processing failed: {e}")
            raise
    
    def process_wsteth_peg_data(self) -> Dict:
        """Process wstETH peg discount/premium data using AAVE oracle."""
        return self._process_peg_data_generic('wstETH')

    def process_weeth_peg_data(self) -> Dict:
        """Process weETH peg discount/premium data using AAVE oracle."""
        return self._process_peg_data_generic('weETH')
    
    
    def process_all_peg_data(self) -> Dict:
        """Process all available peg discount data."""
        self.logger.info("🚀 Processing all LST peg discount data...")
        
        results = {}
        
        # Process wstETH
        try:
            wsteth_result = self.process_wsteth_peg_data()
            results['wstETH'] = wsteth_result
            self.logger.info(f"✅ wstETH: {wsteth_result['records_processed']:,} records")
        except Exception as e:
            self.logger.error(f"❌ wstETH processing failed: {e}")
            results['wstETH'] = {'error': str(e)}
        
        # Process weETH
        try:
            weeth_result = self.process_weeth_peg_data()
            results['weETH'] = weeth_result
            self.logger.info(f"✅ weETH: {weeth_result['records_processed']:,} records")
        except Exception as e:
            self.logger.error(f"❌ weETH processing failed: {e}")
            results['weETH'] = {'error': str(e)}
        
        
        # Final summary
        successful = sum(1 for r in results.values() if 'error' not in r)
        
        self.logger.info("=" * 70)
        self.logger.info("🎯 PEG DISCOUNT PROCESSING COMPLETE!")
        self.logger.info("=" * 70)
        self.logger.info(f"✅ Assets processed: {successful}/{len(results)}")
        
        for asset, result in results.items():
            if 'error' not in result:
                avg_premium = result['peg_statistics']['average_premium_percent']
                cost_analysis = result.get('cost_analysis', {})
                profitable_dex_pct = cost_analysis.get('profitable_dex_percentage', 0)
                
                protocol = "lido" if asset == "wstETH" else "etherfi"
                direct_pct = result['route_analysis'][f'direct_{protocol}_percentage']
                dex_pct = result['route_analysis']['dex_swap_percentage']
                
                self.logger.info(f"📊 {asset}: {avg_premium:.2f}% avg premium")
                self.logger.info(f"   🛣️  Optimal routes: {direct_pct:.1f}% direct, {dex_pct:.1f}% DEX")
                self.logger.info(f"   💰 Profitable DEX opportunities: {profitable_dex_pct:.1f}% (${self.simulation_size_usd:,} size)")
        
        self.logger.info(f"💾 Output directory: {self.output_dir}")
        self.logger.info("=" * 70)
        
        return results

def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process LST peg discount/premium data")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    
    args = parser.parse_args()
    
    try:
        processor = PegDiscountProcessor(args.data_dir)
        
        print("🎯 Processing LST peg discount/premium data using AAVE oracle...")
        print("📊 Analyzing optimal entry/exit routes (DEX vs direct staking)")
        print("🔄 Using AAVE oracle prices as fair value benchmark")
        
        results = processor.process_all_peg_data()
        
        successful = sum(1 for r in results.values() if 'error' not in r)
        
        if successful > 0:
            print(f"\\n🎉 SUCCESS! Processed {successful} LST peg datasets")
            print("📈 Data ready for staking spread risk analysis")
        else:
            print(f"\\n❌ FAILED! No peg data was processed successfully")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\\n💥 ERROR: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
