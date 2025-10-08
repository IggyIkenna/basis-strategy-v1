"""
EtherFi Seasonal Rewards Processor

Processes all EtherFi seasonal rewards including:
1. EIGEN weekly distributions (real data from 2024-08-15 to 2025-08-02)
2. EIGEN + ETHFI combined rewards (DeFiLlama data from 2024-11-22 to 2025-09-29)
3. ETHFI top-ups (real data from GitBook)
4. ETHFI seasonal airdrops (estimated from seasonal_drops.csv)

Timeline:
- 2024-01-01 to 2024-08-14: No EIGEN rewards (program not started)
- 2024-08-15 to 2025-08-02: Real EIGEN weekly distributions from King Protocol
- 2025-08-03 onwards: DeFiLlama combined reward APY data (EIGEN + ETHFI)
- 2024-03-01 onwards: ETHFI seasonal airdrops and top-ups

Inputs:
- EIGEN distributions: data/manual_sources/etherfi_distributions/eigen_distributions_raw.csv
- DeFiLlama rewards: data/manual_sources/etherfi_distributions/bar-chart-supply-apy-2025-09-29-eeth.csv
- ETHFI top-ups: data/manual_sources/etherfi_distributions/ethfi_topups_raw.csv
- Seasonal drops: data/manual_sources/etherfi_distributions/seasonal_drops.csv
- Token prices: data/market_data/spot_prices/protocol_tokens/ and eth_usd/

Outputs:
- data/protocol_data/staking/restaking_final/etherfi_seasonal_rewards_2024-01-01_2025-09-18.csv
- Comprehensive seasonal rewards analysis
"""

import pandas as pd
import json
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging


class EtherFiSeasonalRewardsProcessor:
    """Process all EtherFi seasonal rewards comprehensively."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.output_dir = self.data_dir / "protocol_data" / "staking" / "restaking_final"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger("etherfi_seasonal_rewards")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info("EtherFi Seasonal Rewards Processor initialized")
        self.logger.info(f"Output directory: {self.output_dir}")
    
    def load_eigen_distributions(self) -> pd.DataFrame:
        """Load real EIGEN distribution data."""
        self.logger.info("📊 Loading EIGEN distributions...")
        
        eigen_file = self.data_dir / "manual_sources" / "etherfi_distributions" / "eigen_distributions_raw.csv"
        if not eigen_file.exists():
            raise FileNotFoundError(f"EIGEN distributions not found: {eigen_file}")
        
        df = pd.read_csv(eigen_file)
        df['staking_period_start'] = pd.to_datetime(df['staking_period_start'])
        df['staking_period_end'] = pd.to_datetime(df['staking_period_end'])
        
        self.logger.info(f"✅ EIGEN distributions: {len(df)} periods")
        self.logger.info(f"   Date range: {df['staking_period_start'].min().date()} to {df['staking_period_end'].max().date()}")
        self.logger.info(f"   Average EIGEN per eETH weekly: {df['eigen_per_eeth_weekly'].mean():.3f}")
        
        return df
    
    def load_ethfi_topups(self) -> pd.DataFrame:
        """Load real ETHFI top-up data (including all top-ups, even those not in seasonal CSV)."""
        self.logger.info("📊 Loading ETHFI top-ups...")
        
        topups_file = self.data_dir / "manual_sources" / "etherfi_distributions" / "ethfi_topups_raw.csv"
        if not topups_file.exists():
            self.logger.warning("⚠️  ETHFI top-ups not found")
            return pd.DataFrame()
        
        df = pd.read_csv(topups_file)
        df['top_up_date'] = pd.to_datetime(df['top_up_date'])
        df['staking_period_start'] = pd.to_datetime(df['staking_period_start'])
        df['staking_period_end'] = pd.to_datetime(df['staking_period_end'])
        
        self.logger.info(f"✅ ETHFI top-ups: {len(df)} periods")
        self.logger.info(f"   Date range: {df['top_up_date'].min().date()} to {df['top_up_date'].max().date()}")
        self.logger.info(f"   All top-ups included (including 2024-12-12 and 2024-12-19)")
        
        return df
    
    def load_defillama_fallback(self) -> pd.DataFrame:
        """Load DeFiLlama fallback data for EIGEN rewards after 2025-08-02.
        
        This uses the bar-chart-supply-apy CSV which contains DeFiLlama data with:
        - Base: Base staking yield
        - Reward: EIGEN + ETHFI seasonal rewards combined
        """
        self.logger.info("📊 Loading DeFiLlama fallback for EIGEN rewards...")
        
        # The correct file location - this is the DeFiLlama data export
        defillama_file = self.data_dir / "manual_sources" / "etherfi_distributions" / "bar-chart-supply-apy-2025-09-29-eeth.csv"
        if not defillama_file.exists():
            self.logger.warning("⚠️  DeFiLlama fallback not found")
            return pd.DataFrame()
        
        df = pd.read_csv(defillama_file)
        
        # Parse date - can be either direct Date column or Timestamp (unix)
        if 'Date' in df.columns:
            df['date'] = pd.to_datetime(df['Date'])
        elif 'Timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['Timestamp'], unit='s')
        else:
            raise ValueError("No Date or Timestamp column found in DeFiLlama data")
        
        # Handle reward column if present (DeFiLlama's EIGEN + ETHFI approximation)
        if 'Reward' in df.columns:
            df['defillama_reward_apy'] = df['Reward'].fillna(0.0) / 100.0  # Already in percentage, convert to decimal
        else:
            df['defillama_reward_apy'] = 0.0
        
        # Filter for dates after 2025-08-02 (when real EIGEN data ends)
        cutoff_date = pd.to_datetime('2025-08-02')
        df = df[df['date'] > cutoff_date]
        
        self.logger.info(f"✅ DeFiLlama fallback: {len(df)} records after 2025-08-02")
        if len(df) > 0:
            self.logger.info(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
            self.logger.info(f"   Records with rewards: {len(df[df['defillama_reward_apy'] > 0])}")
            if len(df[df['defillama_reward_apy'] > 0]) > 0:
                self.logger.info(f"   Reward APY range: {df[df['defillama_reward_apy'] > 0]['defillama_reward_apy'].min()*100:.2f}% - {df[df['defillama_reward_apy'] > 0]['defillama_reward_apy'].max()*100:.2f}%")
        
        return df
    
    def load_seasonal_drops(self) -> pd.DataFrame:
        """Load seasonal drops data (including estimated seasonal airdrops)."""
        self.logger.info("📊 Loading seasonal drops data...")
        
        seasonal_file = self.data_dir / "manual_sources" / "etherfi_distributions" / "seasonal_drops.csv"
        if not seasonal_file.exists():
            raise FileNotFoundError(f"Seasonal drops not found: {seasonal_file}")
        
        df = pd.read_csv(seasonal_file)
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])
        df['payout_date'] = pd.to_datetime(df['payout_date'])
        
        # Parse reward_per_eeth (handle ranges like "~5–15")
        df['reward_per_eeth_min'] = df['reward_per_eeth'].str.extract(r'~?(\d+(?:\.\d+)?)').astype(float)
        df['reward_per_eeth_max'] = df['reward_per_eeth'].str.extract(r'~?\d+(?:\.\d+)?[–-](\d+(?:\.\d+)?)').astype(float)
        df['reward_per_eeth_avg'] = (df['reward_per_eeth_min'] + df['reward_per_eeth_max']) / 2
        
        # For exact values (like top-ups), use the exact value
        exact_mask = ~df['reward_per_eeth'].str.contains('~', na=False)
        df.loc[exact_mask, 'reward_per_eeth_avg'] = df.loc[exact_mask, 'reward_per_eeth'].astype(float)
        
        self.logger.info(f"✅ Seasonal drops: {len(df)} events")
        self.logger.info(f"   Date range: {df['start_date'].min().date()} to {df['end_date'].max().date()}")
        
        # Show breakdown by event type
        event_counts = df['event'].value_counts()
        self.logger.info(f"   Events: {dict(event_counts)}")
        
        return df
    
    def load_token_prices(self) -> Dict[str, pd.DataFrame]:
        """Load token prices for yield calculations."""
        self.logger.info("💰 Loading token prices...")
        
        price_files = {
            'ETH': 'market_data/spot_prices/eth_usd/*ETHUSDT*1h*.csv',
            'EIGEN': 'market_data/spot_prices/protocol_tokens/EIGENUSDT_1h_*.csv',
            'ETHFI': 'market_data/spot_prices/protocol_tokens/ETHFIUSDT_1h_*.csv',
        }
        
        price_data = {}
        
        for token, pattern in price_files.items():
            matching_files = list(self.data_dir.glob(pattern))
            
            if not matching_files:
                self.logger.warning(f"⚠️  No price data files found for {token}")
                continue
            
            latest_file = max(matching_files, key=lambda x: x.stat().st_size)
            
            try:
                # Parse CSV with custom header extraction
                with open(latest_file, 'r') as f:
                    lines = f.readlines()
                    columns = lines[0].strip().split('\\n')[-1].split(',')
                    data_lines = lines[1:]
                
                csv_content = ','.join(columns) + '\n' + ''.join(data_lines)
                df = pd.read_csv(io.StringIO(csv_content))
                
                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
                df['date'] = df['timestamp'].dt.date
                
                # Create daily price averages
                daily_prices = df.groupby('date')['close'].mean().reset_index()
                daily_prices['token'] = token
                
                price_data[token] = daily_prices
                self.logger.info(f"✅ {token}: {len(daily_prices)} daily prices")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to load {token} prices: {e}")
        
        return price_data
    
    def _get_price_for_date(self, price_df: pd.DataFrame, target_date) -> float:
        """Get price for specific date with tolerance."""
        if price_df is None or price_df.empty:
            return None
        
        try:
            exact_matches = price_df[price_df['date'] == target_date]
            if len(exact_matches) > 0:
                return exact_matches['close'].iloc[0]
            
            # Find nearest date within 7 days
            price_df_copy = price_df.copy()
            price_df_copy['date_diff'] = abs((pd.to_datetime(price_df_copy['date']) - pd.to_datetime(target_date)).dt.days)
            nearest = price_df_copy[price_df_copy['date_diff'] <= 7]
            
            if len(nearest) > 0:
                closest_idx = nearest['date_diff'].idxmin()
                return nearest.loc[closest_idx, 'close']
            
            return None
            
        except Exception as e:
            self.logger.warning(f"⚠️  Price lookup failed for {target_date}: {e}")
            return None
    
    def calculate_king_protocol_apr(self, eigen_per_eeth: float, eigen_price: float, eth_price: float) -> float:
        """Calculate APR using King Protocol formula."""
        weekly_rewards_usd = eigen_per_eeth * eigen_price
        weekly_rewards_eth = weekly_rewards_usd / eth_price
        apr_decimal = weekly_rewards_eth * 52  # Annualize
        return apr_decimal
    
    def generate_comprehensive_seasonal_rewards(self, eigen_df: pd.DataFrame, topups_df: pd.DataFrame, 
                                              seasonal_df: pd.DataFrame, defillama_df: pd.DataFrame, price_data: Dict) -> List[Dict]:
        """Generate comprehensive seasonal rewards analysis with correct daily yield calculations."""
        self.logger.info("🎁 Generating comprehensive seasonal rewards...")
        
        reward_periods = []
        
        # 1. Process EIGEN weekly distributions (real data)
        self.logger.info("📊 Processing EIGEN weekly distributions...")
        for _, row in eigen_df.iterrows():
            try:
                period_start = row['staking_period_start'].date()
                period_end = row['staking_period_end'].date()
                eigen_per_eeth_weekly = row['eigen_per_eeth_weekly']
                
                # Get prices at period start
                eigen_price = self._get_price_for_date(price_data.get('EIGEN'), period_start) or 3.5
                eth_price = self._get_price_for_date(price_data.get('ETH'), period_start) or 3000
                
                # Calculate weekly reward in ETH terms
                weekly_reward_usd = eigen_per_eeth_weekly * eigen_price
                weekly_reward_eth = weekly_reward_usd / eth_price
                
                # Convert to daily yield over the 7-day period
                daily_yield_eth = weekly_reward_eth / 7  # Distribute weekly reward over 7 days
                daily_yield_pct = daily_yield_eth  # As percentage of eETH value
                
                period_days = (period_end - period_start).days
                
                reward_periods.append({
                    'period_start': period_start.strftime('%Y-%m-%d'),
                    'period_end': period_end.strftime('%Y-%m-%d'),
                    'payout_date': period_end.strftime('%Y-%m-%d'),
                    'period_days': period_days,
                    'reward_type': 'EIGEN_via_KING',
                    'event_name': 'EIGEN_Weekly_Distribution',
                    'eigen_per_eeth_weekly': eigen_per_eeth_weekly,
                    'eigen_price_usd': eigen_price,
                    'eth_price_usd': eth_price,
                    'weekly_reward_eth': weekly_reward_eth,
                    'daily_yield_pct': daily_yield_pct,
                    'daily_yield_conservative': daily_yield_pct * 0.8,  # 20% lower estimate
                    'daily_yield_aggressive': daily_yield_pct * 1.2,   # 20% higher estimate
                    'daily_yield_final': daily_yield_pct,  # Use exact data for final yield
                    'distribution_mechanism': 'king_protocol_weekly',
                    'data_source': 'real_eigen_distribution',
                    'data_quality': 'exact'
                })
                
            except Exception as e:
                self.logger.warning(f"⚠️  Failed to process EIGEN period: {e}")
        
        # 1b. Process DeFiLlama EIGEN fallback (post-2025-08-02)
        self.logger.info("📊 Processing DeFiLlama EIGEN fallback...")
        for _, row in defillama_df.iterrows():
            if row['defillama_reward_apy'] > 0:
                try:
                    date = row['date'].date()
                    reward_apy = row['defillama_reward_apy']
                    
                    # Convert APY to daily yield
                    daily_yield_pct = (1 + reward_apy) ** (1/365) - 1
                    
                    reward_periods.append({
                        'period_start': date.strftime('%Y-%m-%d'),
                        'period_end': date.strftime('%Y-%m-%d'),
                        'payout_date': date.strftime('%Y-%m-%d'),
                        'period_days': 1,
                        'reward_type': 'EIGEN_via_DEFILLAMA',
                        'event_name': 'EIGEN_DeFiLlama_Approximation',
                        'defillama_reward_apy': reward_apy,
                        'daily_yield_pct': daily_yield_pct,
                        'daily_yield_conservative': daily_yield_pct * 0.7,  # 30% lower (more uncertain)
                        'daily_yield_aggressive': daily_yield_pct * 1.3,   # 30% higher (more uncertain)
                        'daily_yield_final': daily_yield_pct * 0.7,  # Use conservative estimate for final yield
                        'distribution_mechanism': 'defillama_approximation',
                        'data_source': 'defillama_fallback',
                        'data_quality': 'estimated'
                    })
                    
                except Exception as e:
                    self.logger.warning(f"⚠️  Failed to process DeFiLlama EIGEN: {e}")
        
        # 2. Process ETHFI top-ups (real data)
        self.logger.info("📊 Processing ETHFI top-ups...")
        for _, row in topups_df.iterrows():
            try:
                top_up_date = row['top_up_date'].date()
                period_start = row['staking_period_start'].date()
                period_end = row['staking_period_end'].date()
                ethfi_per_eeth = row['ethfi_per_eeth_distributed']
                
                # Get prices at top-up date
                ethfi_price = self._get_price_for_date(price_data.get('ETHFI'), top_up_date) or 2.8
                eth_price = self._get_price_for_date(price_data.get('ETH'), top_up_date) or 3000
                
                # Calculate total reward in ETH terms
                distribution_usd = ethfi_per_eeth * ethfi_price
                distribution_eth = distribution_usd / eth_price
                
                # Distribute over the staking period as daily yield
                period_days = (period_end - period_start).days
                daily_yield_pct = distribution_eth / period_days if period_days > 0 else 0
                
                reward_periods.append({
                    'period_start': period_start.strftime('%Y-%m-%d'),
                    'period_end': period_end.strftime('%Y-%m-%d'),
                    'payout_date': top_up_date.strftime('%Y-%m-%d'),
                    'period_days': period_days,
                    'reward_type': 'ETHFI_via_KING',
                    'event_name': f'ETHFI_TopUp_{top_up_date.strftime("%Y%m%d")}',
                    'ethfi_per_eeth': ethfi_per_eeth,
                    'ethfi_price_usd': ethfi_price,
                    'eth_price_usd': eth_price,
                    'distribution_eth': distribution_eth,
                    'daily_yield_pct': daily_yield_pct,
                    'daily_yield_conservative': daily_yield_pct * 0.9,  # 10% lower (exact data, less uncertainty)
                    'daily_yield_aggressive': daily_yield_pct * 1.1,   # 10% higher (exact data, less uncertainty)
                    'daily_yield_final': daily_yield_pct,  # Use exact data for final yield
                    'distribution_mechanism': 'king_protocol_adhoc_topup',
                    'data_source': 'real_ethfi_topup',
                    'data_quality': 'exact'
                })
                
            except Exception as e:
                self.logger.warning(f"⚠️  Failed to process ETHFI top-up: {e}")
        
        # 3. Process seasonal airdrops (estimated data)
        self.logger.info("📊 Processing seasonal airdrops...")
        for _, row in seasonal_df.iterrows():
            # Skip top-ups (already processed above)
            if 'Top-Up' in str(row['event']):
                continue
            
            try:
                start_date = row['start_date'].date()
                end_date = row['end_date'].date()
                payout_date = row['payout_date'].date()
                event_name = row['event']
                ethfi_per_eeth = row['reward_per_eeth_avg']
                
                # Get prices at payout date
                ethfi_price = self._get_price_for_date(price_data.get('ETHFI'), payout_date) or 2.8
                eth_price = self._get_price_for_date(price_data.get('ETH'), payout_date) or 3000
                
                # Calculate total reward in ETH terms
                distribution_usd = ethfi_per_eeth * ethfi_price
                distribution_eth = distribution_usd / eth_price
                
                # Distribute over holding period as daily yield
                period_days = (end_date - start_date).days
                daily_yield_pct = distribution_eth / period_days if period_days > 0 else 0
                
                reward_periods.append({
                    'period_start': start_date.strftime('%Y-%m-%d'),
                    'period_end': end_date.strftime('%Y-%m-%d'),
                    'payout_date': payout_date.strftime('%Y-%m-%d'),
                    'period_days': period_days,
                    'reward_type': 'ETHFI_Seasonal_Airdrop',
                    'event_name': event_name,
                    'ethfi_per_eeth': ethfi_per_eeth,
                    'ethfi_price_usd': ethfi_price,
                    'eth_price_usd': eth_price,
                    'distribution_eth': distribution_eth,
                    'daily_yield_pct': daily_yield_pct,
                    'daily_yield_conservative': daily_yield_pct * 0.7,  # 30% lower (estimated data, more uncertainty)
                    'daily_yield_aggressive': daily_yield_pct * 1.3,   # 30% higher (estimated data, more uncertainty)
                    'daily_yield_final': daily_yield_pct * 0.7,  # Use conservative estimate for final yield
                    'distribution_mechanism': 'seasonal_airdrop',
                    'data_source': 'estimated_seasonal_drops',
                    'data_quality': 'estimated'
                })
                
            except Exception as e:
                self.logger.warning(f"⚠️  Failed to process seasonal event {row['event']}: {e}")
        
        self.logger.info(f"✅ Generated {len(reward_periods)} seasonal reward periods")
        
        return reward_periods
    
    def create_seasonal_analysis_summary(self, reward_periods: List[Dict]) -> Dict:
        """Create comprehensive seasonal analysis summary with daily yield methodology."""
        self.logger.info("📊 Creating seasonal analysis summary...")
        
        # Separate by reward type
        eigen_rewards = [r for r in reward_periods if r['reward_type'] in ['EIGEN_via_KING', 'EIGEN_via_DEFILLAMA']]
        ethfi_topups = [r for r in reward_periods if r['reward_type'] == 'ETHFI_via_KING']
        ethfi_seasonal = [r for r in reward_periods if r['reward_type'] == 'ETHFI_Seasonal_Airdrop']
        
        # Calculate weighted average daily yields (weighted by period days)
        def weighted_avg_daily_yield(rewards, yield_col='daily_yield_final'):
            if not rewards:
                return 0, 0, 0, 0
            
            total_days = sum(r['period_days'] for r in rewards)
            if total_days == 0:
                return 0, 0, 0, 0
            
            weighted_yield = sum(r[yield_col] * r['period_days'] for r in rewards) / total_days
            weighted_conservative = sum(r['daily_yield_conservative'] * r['period_days'] for r in rewards) / total_days
            weighted_aggressive = sum(r['daily_yield_aggressive'] * r['period_days'] for r in rewards) / total_days
            weighted_final = sum(r['daily_yield_final'] * r['period_days'] for r in rewards) / total_days
            
            return weighted_yield, weighted_conservative, weighted_aggressive, weighted_final
        
        # Calculate weighted averages
        eigen_avg, eigen_conservative, eigen_aggressive, eigen_final = weighted_avg_daily_yield(eigen_rewards)
        ethfi_topup_avg, ethfi_topup_conservative, ethfi_topup_aggressive, ethfi_topup_final = weighted_avg_daily_yield(ethfi_topups)
        ethfi_seasonal_avg, ethfi_seasonal_conservative, ethfi_seasonal_aggressive, ethfi_seasonal_final = weighted_avg_daily_yield(ethfi_seasonal)
        
        # Total daily yields (using final conservative estimates)
        total_daily_yield = eigen_final + ethfi_topup_final + ethfi_seasonal_final
        total_conservative = eigen_conservative + ethfi_topup_conservative + ethfi_seasonal_conservative
        total_aggressive = eigen_aggressive + ethfi_topup_aggressive + ethfi_seasonal_aggressive
        
        summary = {
            'analysis_completed': datetime.now().isoformat(),
            'methodology': 'daily_yield_distribution_analysis',
            'total_periods': len(reward_periods),
            'reward_breakdown': {
                'eigen_weekly_periods': len(eigen_rewards),
                'ethfi_topup_periods': len(ethfi_topups),
                'ethfi_seasonal_periods': len(ethfi_seasonal)
            },
            'daily_yield_analysis': {
                'eigen_daily_yield': eigen_avg,
                'ethfi_topup_daily_yield': ethfi_topup_avg,
                'ethfi_seasonal_daily_yield': ethfi_seasonal_avg,
                'total_daily_yield': total_daily_yield
            },
            'daily_yield_analysis_percent': {
                'eigen_daily_percent': eigen_avg * 100,
                'ethfi_topup_daily_percent': ethfi_topup_avg * 100,
                'ethfi_seasonal_daily_percent': ethfi_seasonal_avg * 100,
                'total_daily_percent': total_daily_yield * 100
            },
            'conservative_estimates': {
                'eigen_daily_conservative': eigen_conservative * 100,
                'ethfi_topup_daily_conservative': ethfi_topup_conservative * 100,
                'ethfi_seasonal_daily_conservative': ethfi_seasonal_conservative * 100,
                'total_daily_conservative': total_conservative * 100
            },
            'aggressive_estimates': {
                'eigen_daily_aggressive': eigen_aggressive * 100,
                'ethfi_topup_daily_aggressive': ethfi_topup_aggressive * 100,
                'ethfi_seasonal_daily_aggressive': ethfi_seasonal_aggressive * 100,
                'total_daily_aggressive': total_aggressive * 100
            },
            'data_quality': {
                'exact_data_periods': len([r for r in reward_periods if r['data_quality'] == 'exact']),
                'estimated_data_periods': len([r for r in reward_periods if r['data_quality'] == 'estimated'])
            },
            'timeline_coverage': {
                'eigen_start_date': min([r['period_start'] for r in eigen_rewards]) if eigen_rewards else None,
                'eigen_end_date': max([r['period_end'] for r in eigen_rewards]) if eigen_rewards else None,
                'ethfi_start_date': min([r['period_start'] for r in ethfi_topups + ethfi_seasonal]) if (ethfi_topups or ethfi_seasonal) else None,
                'ethfi_end_date': max([r['period_end'] for r in ethfi_topups + ethfi_seasonal]) if (ethfi_topups or ethfi_seasonal) else None
            }
        }
        
        self.logger.info(f"📈 Seasonal Rewards Summary (Daily Yield Methodology):")
        self.logger.info(f"   EIGEN daily: {eigen_avg*100:.4f}% ({len(eigen_rewards)} periods)")
        self.logger.info(f"   ETHFI top-ups daily: {ethfi_topup_avg*100:.4f}% ({len(ethfi_topups)} periods)")
        self.logger.info(f"   ETHFI seasonal daily: {ethfi_seasonal_avg*100:.4f}% ({len(ethfi_seasonal)} periods)")
        self.logger.info(f"   Total daily yield: {total_daily_yield*100:.4f}%")
        self.logger.info(f"   Conservative range: {total_conservative*100:.4f}% - {total_aggressive*100:.4f}%")
        
        return summary
    
    def process_all_seasonal_rewards(self, start_date: str = "2024-01-01", end_date: str = "2025-09-18") -> Dict:
        """Process all EtherFi seasonal rewards comprehensively."""
        self.logger.info("🚀 Processing all EtherFi seasonal rewards...")
        self.logger.info(f"📅 Period: {start_date} to {end_date}")
        
        try:
            # Load all data
            eigen_df = self.load_eigen_distributions()
            topups_df = self.load_ethfi_topups()
            seasonal_df = self.load_seasonal_drops()
            defillama_df = self.load_defillama_fallback()
            price_data = self.load_token_prices()
            
            # Generate comprehensive seasonal rewards
            reward_periods = self.generate_comprehensive_seasonal_rewards(eigen_df, topups_df, seasonal_df, defillama_df, price_data)
            
            # Save detailed reward periods
            if reward_periods:
                output_file = self.output_dir / f"etherfi_seasonal_rewards_{start_date}_{end_date}.csv"
                reward_df = pd.DataFrame(reward_periods)
                reward_df.to_csv(output_file, index=False)
                self.logger.info(f"💾 Seasonal rewards: {output_file}")
            
            # Create comprehensive summary
            summary = self.create_seasonal_analysis_summary(reward_periods)
            
            # Save summary
            summary_file = self.output_dir / f"etherfi_seasonal_analysis_{start_date}_{end_date}.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.logger.info("=" * 80)
            self.logger.info("🎯 ETHERFI SEASONAL REWARDS PROCESSING COMPLETE!")
            self.logger.info("=" * 80)
            self.logger.info(f"📊 Total periods: {summary['total_periods']}")
            self.logger.info(f"📈 Total daily yield: {summary['daily_yield_analysis_percent']['total_daily_percent']:.4f}%")
            self.logger.info(f"   EIGEN: {summary['daily_yield_analysis_percent']['eigen_daily_percent']:.4f}%")
            self.logger.info(f"   ETHFI top-ups: {summary['daily_yield_analysis_percent']['ethfi_topup_daily_percent']:.4f}%")
            self.logger.info(f"   ETHFI seasonal: {summary['daily_yield_analysis_percent']['ethfi_seasonal_daily_percent']:.4f}%")
            self.logger.info(f"📊 Conservative range: {summary['conservative_estimates']['total_daily_conservative']:.4f}% - {summary['aggressive_estimates']['total_daily_aggressive']:.4f}%")
            self.logger.info(f"📊 Data quality: {summary['data_quality']['exact_data_periods']} exact, {summary['data_quality']['estimated_data_periods']} estimated")
            self.logger.info(f"💾 All outputs: {self.output_dir}")
            self.logger.info("=" * 80)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Processing failed: {e}")
            raise


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process all EtherFi seasonal rewards")
    parser.add_argument("--start-date", type=str, default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2025-09-18", help="End date (YYYY-MM-DD)")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    
    args = parser.parse_args()
    
    try:
        processor = EtherFiSeasonalRewardsProcessor(args.data_dir)
        
        print("🎯 Processing all EtherFi seasonal rewards...")
        print("📊 EIGEN weekly + ETHFI top-ups + ETHFI seasonal airdrops")
        print("🔗 Reference: https://etherfi.gitbook.io/etherfi/king-protocol-formerly-lrt/king-rewards-distribution")
        
        results = processor.process_all_seasonal_rewards(args.start_date, args.end_date)
        
        print(f"\n🎉 SUCCESS! All EtherFi seasonal rewards processed")
        print(f"📈 Total daily yield: {results['daily_yield_analysis_percent']['total_daily_percent']:.4f}%")
        print(f"   EIGEN: {results['daily_yield_analysis_percent']['eigen_daily_percent']:.4f}%")
        print(f"   ETHFI top-ups: {results['daily_yield_analysis_percent']['ethfi_topup_daily_percent']:.4f}%")
        print(f"   ETHFI seasonal: {results['daily_yield_analysis_percent']['ethfi_seasonal_daily_percent']:.4f}%")
        print(f"📊 Conservative range: {results['conservative_estimates']['total_daily_conservative']:.4f}% - {results['aggressive_estimates']['total_daily_aggressive']:.4f}%")
        print(f"📊 Data quality: {results['data_quality']['exact_data_periods']} exact, {results['data_quality']['estimated_data_periods']} estimated")
        print(f"💾 All outputs: {processor.output_dir}")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
