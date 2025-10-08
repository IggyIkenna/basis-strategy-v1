#!/usr/bin/env python3
"""Script to complete the USDT analyzer implementation"""

import re

# Read the current USDT file
with open('scripts/analyzers/analyze_leveraged_restaking_USDT.py', 'r') as f:
    lines = f.readlines()

# Find the TODO section (around line 532-541)
stub_start = None
stub_end = None
for i, line in enumerate(lines):
    if '# TODO: Implement leverage loop for long side' in line:
        stub_start = i
    if 'return {}' in line and stub_start and i > stub_start:
        stub_end = i + 1
        break

print(f"Found stub from line {stub_start} to {stub_end}")

# Read the completion code
completion_code = '''
        # Execute leverage loop for long side
        long_position = self._execute_leverage_loop_usd(t0, long_capital_usd, eth_price_spot)
        
        self.logger.info("")
        self.logger.info("STEP 2: Open perp shorts to hedge long exposure")
        self.logger.info("-" * 50)
        
        # CRITICAL: Size hedge to ACTUAL long exposure, not initial allocation!
        actual_long_eth = long_position['long_eth_exposure']
        actual_hedge_usd = actual_long_eth * eth_price_spot
        
        short_positions = self._open_perp_shorts(t0, actual_hedge_usd, eth_price_spot)
        
        # Verify market neutrality
        net_delta_eth = actual_long_eth - short_positions['total_eth_short']
        delta_pct = (net_delta_eth / actual_long_eth) * 100 if actual_long_eth > 0 else 0
        
        self.logger.info("")
        self.logger.info("⚖️  MARKET NEUTRALITY CHECK:")
        self.logger.info(f"   Long ETH Exposure:  {actual_long_eth:.4f} ETH")
        self.logger.info(f"   Short ETH Position: {short_positions['total_eth_short']:.4f} ETH")
        self.logger.info(f"   Net Delta:          {net_delta_eth:+.4f} ETH ({delta_pct:+.2f}%)")
        if abs(delta_pct) < 5:
            self.logger.info("   ✅ Market neutral (delta < 5%)")
        else:
            self.logger.warning(f"   ⚠️  Delta > 5%! Hedge sizing may need adjustment")
        
        self.logger.info("")
        self.logger.info("STEP 3: Track positions hourly with P&L")
        self.logger.info("-" * 50)
        
        # Store initial position for reference
        initial_long_position = long_position.copy()
        initial_net_position_usd = initial_long_position['net_position_usd']
        
        # Track position through time
        hourly_pnl = []
        
        # Track cumulative P&L components
        cumulative_supply_pnl_usd = 0.0
        cumulative_seasonal_pnl_usd = 0.0
        cumulative_borrow_cost_usd = 0.0
        cumulative_price_change_pnl_usd = 0.0
        cumulative_funding_cost_usd = 0.0
        cumulative_net_pnl_usd = 0.0
        
        # Current position state (updated hourly)
        weeth_collateral = long_position['weeth_collateral']
        weth_debt = long_position['weth_debt']
        weeth_price = long_position['weeth_price']
        
        for i, timestamp in enumerate(timestamps[1:], start=1):
            if i % 1000 == 0:
                self.logger.info(f"Processing hour {i}/{len(timestamps)}: {timestamp}")
            
            # Get current prices/rates
            eth_price = self._get_spot_price(timestamp)
            rates = self._get_rates_at_timestamp(timestamp)
            staking_yields = self._get_staking_yield_at_timestamp(timestamp)
            
            # Store old values for P&L calculation
            old_weeth_price = weeth_price
            old_weeth_collateral = weeth_collateral
            old_weth_debt = weth_debt
            
            # Calculate collateral and debt values in WETH
            old_collateral_value_weth = old_weeth_collateral * old_weeth_price
            old_debt_value_weth = old_weth_debt
            
            # Calculate LONG side P&L (in WETH, then convert to USD)
            # 1. AAVE supply yield
            supply_pnl_weth = old_collateral_value_weth * (rates['weeth_supply_growth_factor'] - 1)
            
            # 2. Seasonal rewards ONLY (base is in oracle price)
            seasonal_pnl_weth = old_collateral_value_weth * staking_yields['seasonal_yield_hourly']
            
            # 3. Borrow cost
            borrow_cost_weth = old_debt_value_weth * (rates['weth_borrow_growth_factor'] - 1)
            
            # 4. Update collateral with growth
            weeth_collateral *= rates['weeth_supply_growth_factor']
            weeth_collateral *= (1 + staking_yields['seasonal_yield_hourly'])
            
            # 5. Update debt
            weth_debt *= rates['weth_borrow_growth_factor']
            
            # 6. Update weETH price
            weeth_price = rates['weeth_price']
            
            # 7. Calculate price appreciation P&L
            new_weeth_units_after_yields = old_weeth_collateral * rates['weeth_supply_growth_factor'] * (1 + staking_yields['seasonal_yield_hourly'])
            price_change_pnl_weth = new_weeth_units_after_yields * (weeth_price - old_weeth_price)
            
            # Convert to USD
            supply_pnl_usd = supply_pnl_weth * eth_price
            seasonal_pnl_usd = seasonal_pnl_weth * eth_price
            borrow_cost_usd = borrow_cost_weth * eth_price
            price_change_pnl_usd = price_change_pnl_weth * eth_price
            
            long_pnl_usd = supply_pnl_usd + seasonal_pnl_usd + price_change_pnl_usd - borrow_cost_usd
            
            # Calculate SHORT side costs
            funding_costs = self._calculate_funding_costs(timestamp, short_positions)
            
            # NET P&L (market-neutral)
            net_pnl_usd = long_pnl_usd - funding_costs['total_funding_cost_usd']
            
            # Update cumulatives
            cumulative_supply_pnl_usd += supply_pnl_usd
            cumulative_seasonal_pnl_usd += seasonal_pnl_usd
            cumulative_borrow_cost_usd += borrow_cost_usd
            cumulative_price_change_pnl_usd += price_change_pnl_usd
            cumulative_funding_cost_usd += funding_costs['total_funding_cost_usd']
            cumulative_net_pnl_usd += net_pnl_usd
            
            # Calculate current health factor
            collateral_value_weth = weeth_collateral * weeth_price
            debt_value_weth = weth_debt
            health_factor = (self.config.liquidation_threshold * collateral_value_weth) / debt_value_weth if debt_value_weth > 0 else float('inf')
            
            # Track current exposures
            long_eth_exposure = collateral_value_weth - debt_value_weth
            short_eth_exposure = short_positions['total_eth_short']
            net_delta_eth_current = long_eth_exposure - short_eth_exposure
            delta_pct_current = (net_delta_eth_current / long_eth_exposure) * 100 if long_eth_exposure > 0 else 0
            
            # Record hourly data
            hourly_pnl.append({
                'timestamp': timestamp,
                'eth_price': eth_price,
                # Long side P&L
                'supply_pnl_usd': supply_pnl_usd,
                'seasonal_pnl_usd': seasonal_pnl_usd,
                'borrow_cost_usd': borrow_cost_usd,
                'price_change_pnl_usd': price_change_pnl_usd,
                'long_pnl_usd': long_pnl_usd,
                # Short side costs
                'funding_cost_usd': funding_costs['total_funding_cost_usd'],
                'binance_funding_cost_usd': funding_costs['binance_cost'],
                'bybit_funding_cost_usd': funding_costs['bybit_cost'],
                'binance_funding_rate': funding_costs['binance_rate'],
                'bybit_funding_rate': funding_costs['bybit_rate'],
                # Net P&L
                'net_pnl_usd': net_pnl_usd,
                # Cumulatives
                'cumulative_supply_pnl_usd': cumulative_supply_pnl_usd,
                'cumulative_seasonal_pnl_usd': cumulative_seasonal_pnl_usd,
                'cumulative_borrow_cost_usd': cumulative_borrow_cost_usd,
                'cumulative_price_change_pnl_usd': cumulative_price_change_pnl_usd,
                'cumulative_funding_cost_usd': cumulative_funding_cost_usd,
                'cumulative_net_pnl_usd': cumulative_net_pnl_usd,
                # Positions
                'weeth_collateral': weeth_collateral,
                'weth_debt': weth_debt,
                'collateral_value_weth': collateral_value_weth,
                'debt_value_weth': debt_value_weth,
                'health_factor': health_factor,
                'weeth_price': weeth_price,
                # Market neutrality
                'long_eth_exposure': long_eth_exposure,
                'short_eth_exposure': short_eth_exposure,
                'net_delta_eth': net_delta_eth_current,
                'delta_pct': delta_pct_current,
                # Rates
                'weeth_supply_apy': rates['weeth_supply_apy'],
                'weth_borrow_apy': rates['weth_borrow_apy'],
                'seasonal_yield_hourly': staking_yields['seasonal_yield_hourly'],
                'base_yield_hourly': staking_yields['base_yield_hourly']
            })
        
        # Calculate final metrics
        final_position_value_weth = (weeth_collateral * weeth_price) - weth_debt
        final_position_value_usd = final_position_weth * self._get_spot_price(timestamps[-1])
        
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
                'eigen_only': self.config.eigen_only
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
                'initial_net_position_usd': initial_net_position_usd,
                'final_position_value_usd': final_position_value_usd,
                'cumulative_supply_pnl_usd': cumulative_supply_pnl_usd,
                'cumulative_seasonal_pnl_usd': cumulative_seasonal_pnl_usd,
                'cumulative_borrow_cost_usd': cumulative_borrow_cost_usd,
                'cumulative_price_change_pnl_usd': cumulative_price_change_pnl_usd,
                'cumulative_funding_cost_usd': cumulative_funding_cost_usd,
                'cumulative_net_pnl_usd': cumulative_net_pnl_usd,
                'total_gas_costs_usd': initial_long_position['total_gas_costs_usd'],
                'apr_pct': apr_pct,
                'apy_pct': apy_pct,
                'sharpe_ratio': sharpe_ratio,
                'annualized_volatility': annualized_volatility * 100,
                'max_drawdown_pct': max_drawdown_pct,
                'avg_delta_pct': pnl_df['delta_pct'].mean(),
                'max_abs_delta_pct': pnl_df['delta_pct'].abs().max()
            },
            'hourly_pnl': hourly_pnl,
            'event_log': self.event_log
        }
        
        self.logger.info("=" * 80)
        self.logger.info("📊 ANALYSIS RESULTS:")
        self.logger.info("=" * 80)
        self.logger.info(f"⏱️  Total hours analyzed: {len(hourly_pnl):,}")
        self.logger.info(f"💰 Initial USDT: ${self.config.initial_usdt:,.2f}")
        self.logger.info(f"💰 Initial Net Position: ${initial_net_position_usd:,.2f}")
        self.logger.info(f"💰 Final Position Value: ${final_position_value_usd:,.2f}")
        self.logger.info("")
        self.logger.info("📊 P&L COMPONENT BREAKDOWN:")
        self.logger.info(f"   ✅ AAVE Supply Yield:      ${cumulative_supply_pnl_usd:,.2f}")
        self.logger.info(f"   ✅ Seasonal Rewards:       ${cumulative_seasonal_pnl_usd:,.2f}")
        self.logger.info(f"   📈 Price Appreciation:     ${cumulative_price_change_pnl_usd:,.2f} (incl. base staking)")
        self.logger.info(f"   ❌ AAVE Borrow Cost:       -${cumulative_borrow_cost_usd:,.2f}")
        self.logger.info(f"   ❌ Funding Costs:          -${cumulative_funding_cost_usd:,.2f}")
        self.logger.info(f"   💰 Net P&L:                ${cumulative_net_pnl_usd:,.2f}")
        self.logger.info("")
        self.logger.info(f"⛽ Total Gas Costs: ${initial_long_position['total_gas_costs_usd']:,.2f}")
        self.logger.info("")
        self.logger.info("📈 PERFORMANCE METRICS:")
        self.logger.info(f"   APR:                  {apr_pct:.2f}%")
        self.logger.info(f"   APY (compounded):     {apy_pct:.2f}%")
        self.logger.info(f"   Sharpe Ratio:         {sharpe_ratio:.3f}")
        self.logger.info(f"   Annualized Vol:       {annualized_volatility * 100:.2f}%")
        self.logger.info(f"   Max Drawdown:         {max_drawdown_pct:.2f}%")
        self.logger.info("")
        self.logger.info("⚖️  MARKET NEUTRALITY:")
        self.logger.info(f"   Avg Delta:            {self.results['summary']['avg_delta_pct']:+.2f}%")
        self.logger.info(f"   Max Abs Delta:        {self.results['summary']['max_abs_delta_pct']:.2f}%")
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
        if self.config.eigen_only:
            config_label += "_eigen_only"
        
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
        
        # Save event log
        if self.event_log:
            event_df = pd.DataFrame(self.event_log)
            event_file = output_path / f"leveraged_restaking_USDT_event_log_{config_label}_{timestamp_str}.csv"
            event_df.to_csv(event_file, index=False)
            self.logger.info(f"  📋 Event Log: {event_file} ({len(self.event_log):,} events)")
        
        self.logger.info(f"💾 Results saved to {output_path}")
        self.logger.info(f"  📄 Summary: {summary_file}")
        self.logger.info(f"  📊 Hourly P&L: {pnl_file}")
    
    def create_plots(self, output_dir: str = "data/analysis") -> None:
        """Create visualization plots."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
        config_label = f"usdt_{int(self.config.initial_usdt/1000)}k"
        if self.config.eigen_only:
            config_label += "_eigen_only"
        
        pnl_df = pd.DataFrame(self.results['hourly_pnl'])
        
        # Set up plotting
        plt.style.use('seaborn-v0_8')
        fig = plt.figure(figsize=(28, 14))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        rewards_label = "EIGEN Only" if self.config.eigen_only else "All Rewards"
        fig.suptitle(f'USDT Market-Neutral Leveraged Restaking | {rewards_label}', fontsize=16, fontweight='bold')
        
        # Create subplots
        ax1 = fig.add_subplot(gs[0, 0])  # Cumulative Net P&L
        ax2 = fig.add_subplot(gs[0, 1])  # P&L Components
        ax3 = fig.add_subplot(gs[0, 2])  # Market Neutrality
        ax4 = fig.add_subplot(gs[1, 0])  # Health Factor
        ax5 = fig.add_subplot(gs[1, 1])  # ETH Price
        ax6 = fig.add_subplot(gs[1, 2])  # Long vs Short Exposure
        ax7 = fig.add_subplot(gs[2, :])  # Drawdown (full width)
        
        # Plot 1: Cumulative Net P&L
        ax1.plot(pnl_df['timestamp'], pnl_df['cumulative_net_pnl_usd'], linewidth=2, color='green')
        ax1.set_title('Cumulative Net P&L (USD)')
        ax1.set_ylabel('Cumulative P&L ($)')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        ax1.axhline(y=0, color='black', linestyle='--', alpha=0.3)
        
        # Plot 2: P&L Components
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_supply_pnl_usd'], label='AAVE Supply', linewidth=1.5, alpha=0.8)
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_seasonal_pnl_usd'], label='Seasonal Rewards', linewidth=1.5, alpha=0.8)
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_price_change_pnl_usd'], label='Price Appreciation', linewidth=1.5, alpha=0.8)
        ax2.plot(pnl_df['timestamp'], -pnl_df['cumulative_borrow_cost_usd'], label='Borrow Cost (neg)', linewidth=1.5, alpha=0.8)
        ax2.plot(pnl_df['timestamp'], -pnl_df['cumulative_funding_cost_usd'], label='Funding Cost (neg)', linewidth=1.5, alpha=0.8, color='red')
        ax2.plot(pnl_df['timestamp'], pnl_df['cumulative_net_pnl_usd'], label='Net P&L', linewidth=2, color='black')
        ax2.set_title('Cumulative P&L Components (USD)')
        ax2.set_ylabel('Cumulative USD')
        ax2.legend(loc='best', fontsize=7)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)
        
        # Plot 3: Market Neutrality (Delta %)
        ax3.plot(pnl_df['timestamp'], pnl_df['delta_pct'], linewidth=1, color='blue', alpha=0.6)
        ax3.axhline(y=0, color='green', linestyle='-', alpha=0.5, linewidth=2, label='Perfect Neutral')
        ax3.axhline(y=5, color='orange', linestyle='--', alpha=0.5, label='+5%')
        ax3.axhline(y=-5, color='orange', linestyle='--', alpha=0.5, label='-5%')
        ax3.set_title('Market Neutrality (Delta %)')
        ax3.set_ylabel('Delta (%)')
        ax3.legend(loc='best', fontsize=8)
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(axis='x', rotation=45)
        
        # Plot 4: Health Factor
        ax4.plot(pnl_df['timestamp'], pnl_df['health_factor'], linewidth=2, color='blue')
        ax4.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Liquidation (HF=1.0)')
        ax4.axhline(y=1.015, color='orange', linestyle='--', alpha=0.5, label='Warning (HF=1.015)')
        ax4.set_title('Health Factor (Long Side)')
        ax4.set_ylabel('Health Factor')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.tick_params(axis='x', rotation=45)
        ax4.set_ylim(bottom=0.95)
        
        # Plot 5: ETH Price Evolution
        ax5.plot(pnl_df['timestamp'], pnl_df['eth_price'], linewidth=2, color='purple')
        ax5.set_title('ETH/USD Price (Market-Neutral to This!)')
        ax5.set_ylabel('ETH Price ($)')
        ax5.grid(True, alpha=0.3)
        ax5.tick_params(axis='x', rotation=45)
        
        # Plot 6: Long vs Short Exposure
        ax6.plot(pnl_df['timestamp'], pnl_df['long_eth_exposure'], label='Long ETH', linewidth=2, color='green', alpha=0.8)
        ax6.plot(pnl_df['timestamp'], pnl_df['short_eth_exposure'], label='Short ETH', linewidth=2, color='red', alpha=0.8)
        ax6.fill_between(pnl_df['timestamp'], pnl_df['long_eth_exposure'], pnl_df['short_eth_exposure'], 
                         alpha=0.2, color='gray', label='Net Delta')
        ax6.set_title('Long vs Short Exposure (ETH)')
        ax6.set_ylabel('ETH Exposure')
        ax6.legend(loc='best')
        ax6.grid(True, alpha=0.3)
        ax6.tick_params(axis='x', rotation=45)
        
        # Plot 7: Drawdown
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
'''

# Replace stub with completion code
new_lines = lines[:stub_start] + [completion_code] + lines[stub_end:]

# Write the completed file
with open('scripts/analyzers/analyze_leveraged_restaking_USDT.py', 'w') as f:
    f.writelines(new_lines)

print(f"✅ Completed! New file has {len(new_lines)} lines")
print("Run the analyzer to test it!")
