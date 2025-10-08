"""
AaveScan Pro API client for AAVE lending protocol data.

⚠️  IMPLEMENTATION PENDING: Waiting for AaveScan Pro API key
🔄 Status: PLACEHOLDER - Ready for API key integration

Will handle:
- Historical lending/borrowing rates (hourly granularity)
- Reserve data (total supply/borrows for market impact modeling)  
- Risk parameters (LTV, liquidation thresholds, caps)
- Oracle pricing data
- Multi-chain support (Ethereum, Arbitrum, Optimism, Base)

🔑 API KEY SETUP REQUIRED:
This client requires an AaveScan Pro API key for full functionality.

1. Get an AaveScan Pro API key from: https://aavescan.com/pricing
2. Add it to backend/env.unified:
   BASIS_DOWNLOADERS__AAVESCAN_API_KEY=your_api_key_here

3. Load environment variables before running:
   source scripts/load_env.sh
   python scripts/downloaders/clients/aavescan_client.py

⚠️  WITHOUT API KEY: Runs in placeholder mode with sample data
✅  WITH API KEY: Full AAVE v3 historical data access
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

# Handle both standalone and module imports
try:
    from ..base_downloader import BaseDownloader
except ImportError:
    # Standalone execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from base_downloader import BaseDownloader


class AaveScanProClient(BaseDownloader):
    """
    AaveScan Pro API client - PENDING API KEY IMPLEMENTATION
    
    🔄 PLACEHOLDER STATUS:
    - Structure ready for API key integration
    - Endpoints defined based on documentation
    - Schema designed for backtest compatibility
    - Waiting for AaveScan Pro Advanced Plan API key
    
    Features (when API key available):
    - Historical AAVE v3 rates (supply/borrow APR)
    - Reserve sizes for market impact calculation
    - Risk parameter history (LTV/LT changes with timestamps)
    - CSV bulk export for historical backfill
    - Multi-chain support
    """
    
    def __init__(self, output_dir: str = "data/lending"):
        super().__init__("aavescan_pro", output_dir, rate_limit_per_minute=1000)  # 1M calls/month
        
        # ⚠️ API KEY REQUIRED
        self.api_key = self.config['api_keys']['aavescan']
        if not self.api_key or self.api_key == "PENDING":
            self.logger.warning("🔄 AaveScan Pro API key not available - using placeholder mode")
            self.placeholder_mode = True
        else:
            self.placeholder_mode = False
            self.logger.info(f"✅ AaveScan Pro API key configured")
        
        # API configuration (based on actual API testing)
        self.base_url = "https://api.aavescan.com/v2"
        # Note: AaveScan Pro uses apiKey parameter, not Authorization header
        
        # AAVE markets - ETHEREUM ONLY (as requested)
        self.aave_markets = {
            'ethereum': 'aave-v3-ethereum'  # Only Ethereum mainnet
        }
        
        # Asset symbols we're interested in (addresses discovered dynamically per chain)
        self.target_assets = ['WETH', 'wstETH', 'weETH', 'USDT']  # Removed DAI/USDC - not used in strategy
        
        # Chain-specific asset addresses (discovered from API)
        self.chain_assets = {}
        
        if self.placeholder_mode:
            self.logger.warning("=" * 60)
            self.logger.warning("⚠️  AAVESCAN PRO CLIENT IN PLACEHOLDER MODE")
            self.logger.warning("🔑 Waiting for AaveScan Pro Advanced Plan API key")
            self.logger.warning("📋 Plan includes:")
            self.logger.warning("   • Full API for Aave/Ecosystem markets")
            self.logger.warning("   • 1M API calls per month")
            self.logger.warning("   • Market rates and oracle pricing")
            self.logger.warning("   • Priority support and onboarding")
            self.logger.warning("=" * 60)
        else:
            self.logger.info(f"AaveScan Pro client initialized for {len(self.aave_markets)} markets")
    
    async def get_reserves_latest(self, market: Optional[str] = None) -> Optional[Dict]:
        """
        Get latest reserve data for all assets.
        
        Args:
            market: Specific market (e.g., 'aave-v3-ethereum') or None for all
            
        Returns:
            Latest reserves data or None if failed/placeholder
        """
        if self.placeholder_mode:
            self.logger.warning("🔄 get_reserves_latest called in placeholder mode")
            return self._generate_placeholder_reserves_data()
        
        url = f"{self.base_url}/reserves/latest"
        params = {'apiKey': self.api_key}
        if market:
            params['market'] = market
        
        return await self.make_request(url, params=params)
    
    async def get_reserves_historical(self, market: str, symbol: str, 
                                    start_date: str, end_date: str) -> Optional[Dict]:
        """
        Get historical reserve data for a specific asset.
        
        Args:
            market: AAVE market (e.g., 'aave-v3-ethereum')
            symbol: Asset symbol (e.g., 'weth')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Historical data or None if failed/placeholder
        """
        if self.placeholder_mode:
            self.logger.warning(f"🔄 get_reserves_historical called for {symbol} in placeholder mode")
            return self._generate_placeholder_historical_data(symbol, start_date, end_date)
        
        url = f"{self.base_url}/reserves/historical"
        params = {
            'market': market,
            'symbol': symbol.lower(),
            'apiKey': self.api_key,
            'start': start_date,
            'end': end_date
        }
        
        return await self.make_request(url, params=params)
    
    async def discover_chain_assets(self, market_slug: str) -> Dict[str, str]:
        """
        Discover available assets and their addresses for a specific chain.
        
        Args:
            market_slug: Market identifier (e.g., 'aave-v3-arbitrum')
            
        Returns:
            Dictionary mapping asset symbols to addresses for this chain
        """
        if self.placeholder_mode:
            return {}
        
        # Get latest reserves to discover assets
        latest_data = await self.get_reserves_latest()
        
        if not latest_data:
            return {}
        
        chain_assets = {}
        
        # Find the market data for this chain
        for market_data in latest_data:
            if market_data.get('marketSlug') == market_slug:
                reserves = market_data.get('reserveData', [])
                
                for reserve in reserves:
                    if 'asset' in reserve:
                        symbol = reserve['asset'].get('symbol', '')
                        address = reserve['asset'].get('address', '')
                        
                        # Only include assets we're interested in
                        if symbol in self.target_assets:
                            chain_assets[symbol] = address
                
                break
        
        self.logger.info(f"Discovered {len(chain_assets)} assets for {market_slug}: {list(chain_assets.keys())}")
        return chain_assets
    
    async def get_csv_export(self, market: str, symbol: str, reserve_address: str) -> Optional[bytes]:
        """
        Download bulk CSV export for historical data.
        
        Args:
            market: AAVE market (e.g., 'aave-v3-ethereum')
            symbol: Asset symbol (e.g., 'WETH')
            reserve_address: Reserve contract address
            
        Returns:
            CSV data bytes or None if failed/placeholder
        """
        if self.placeholder_mode:
            self.logger.warning(f"🔄 get_csv_export called for {symbol} in placeholder mode")
            return self._generate_placeholder_csv(symbol)
        
        url = f"{self.base_url}/csv"
        params = {
            'market': market,
            'reserveAddress': reserve_address,  # Use reserveAddress instead of symbol
            'apiKey': self.api_key
        }
        
        # Special handling for CSV download
        await self.rate_limiter.wait_if_needed()
        
        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            if response.status_code == 200:
                return response.content
            else:
                self.logger.warning(f"Unexpected status code {response.status_code} for CSV export")
                return None
                
        except Exception as e:
            self.logger.error(f"CSV export failed for {symbol}: {e}")
            return None
    
    def _generate_placeholder_reserves_data(self) -> Dict:
        """Generate placeholder data for testing (when API key not available)."""
        return {
            "placeholder": True,
            "message": "Waiting for AaveScan Pro API key",
            "reserves": {
                "WETH": {
                    "supply_apr": 0.0234,
                    "borrow_apr": 0.0456,
                    "ltv": 0.805,
                    "liquidation_threshold": 0.83,
                    "utilization_rate": 0.67,
                    "total_supply": 150000.0,
                    "total_borrows": 100500.0,
                    # Supply/demand dynamics for interest rate modeling
                    "available_liquidity": 49500.0,  # total_supply - total_borrows
                    "optimal_utilization_rate": 0.80,  # AAVE's target utilization
                    "base_variable_borrow_rate": 0.0,
                    "variable_rate_slope1": 0.038,
                    "variable_rate_slope2": 0.80,
                    "reserve_factor": 0.15
                },
                "wstETH": {
                    "supply_apr": 0.0198,
                    "borrow_apr": 0.0421,
                    "ltv": 0.785,
                    "liquidation_threshold": 0.81,
                    "utilization_rate": 0.72,
                    "total_supply": 80000.0,
                    "total_borrows": 57600.0,
                    # Supply/demand dynamics for interest rate modeling
                    "available_liquidity": 22400.0,
                    "optimal_utilization_rate": 0.75,
                    "base_variable_borrow_rate": 0.0,
                    "variable_rate_slope1": 0.045,
                    "variable_rate_slope2": 1.00,
                    "reserve_factor": 0.15
                }
            }
        }
    
    def _generate_placeholder_historical_data(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """Generate placeholder historical data for testing."""
        return {
            "placeholder": True,
            "message": f"Placeholder historical data for {symbol}",
            "symbol": symbol,
            "date_range": f"{start_date} to {end_date}",
            "data_points": 100  # Would be actual historical records
        }
    
    def _generate_placeholder_csv(self, symbol: str) -> bytes:
        """Generate placeholder CSV data for testing."""
        csv_content = f"""timestamp,market,symbol,supply_apr,borrow_apr,utilization_rate,total_supply,total_borrows,source
2024-01-01T00:00:00Z,aave-v3-ethereum,{symbol},0.0234,0.0456,0.67,150000.0,100500.0,aavescan_pro_placeholder
2024-01-01T01:00:00Z,aave-v3-ethereum,{symbol},0.0235,0.0457,0.68,150100.0,100600.0,aavescan_pro_placeholder
# PLACEHOLDER DATA - Waiting for AaveScan Pro API key
"""
        return csv_content.encode('utf-8')
    
    
    def calculate_interest_rate_impact(self, current_reserves: Dict, 
                                     additional_supply: float = 0.0,
                                     additional_borrow: float = 0.0) -> Dict:
        """
        Calculate the impact of additional supply/borrow on interest rates.
        
        This implements AAVE's interest rate model to predict how large
        strategy positions would affect the pool's interest rates.
        
        Args:
            current_reserves: Current reserve data from API
            additional_supply: Additional supply amount (in tokens)
            additional_borrow: Additional borrow amount (in tokens)
            
        Returns:
            Dictionary with rate impact analysis
        """
        if self.placeholder_mode:
            self.logger.info("🔄 Interest rate impact calculation in placeholder mode")
        
        # Extract current state
        total_supply = current_reserves.get('total_supply', 0.0)
        total_borrows = current_reserves.get('total_borrows', 0.0)
        current_utilization = current_reserves.get('utilization_rate', 0.0)
        
        # AAVE interest rate model parameters
        optimal_utilization = current_reserves.get('optimal_utilization_rate', 0.80)
        base_rate = current_reserves.get('base_variable_borrow_rate', 0.0)
        slope1 = current_reserves.get('variable_rate_slope1', 0.04)
        slope2 = current_reserves.get('variable_rate_slope2', 1.0)
        reserve_factor = current_reserves.get('reserve_factor', 0.15)
        
        # Calculate new state after strategy impact
        new_total_supply = total_supply + additional_supply
        new_total_borrows = total_borrows + additional_borrow
        new_utilization = new_total_borrows / new_total_supply if new_total_supply > 0 else 0.0
        
        def calculate_borrow_rate(utilization_rate: float) -> float:
            """Calculate borrow rate using AAVE's kinked rate model."""
            if utilization_rate <= optimal_utilization:
                # Below optimal: linear increase
                return base_rate + (utilization_rate / optimal_utilization) * slope1
            else:
                # Above optimal: steep increase
                excess_utilization = utilization_rate - optimal_utilization
                max_excess = 1.0 - optimal_utilization
                return base_rate + slope1 + (excess_utilization / max_excess) * slope2
        
        def calculate_supply_rate(borrow_rate: float, utilization_rate: float) -> float:
            """Calculate supply rate from borrow rate."""
            return borrow_rate * utilization_rate * (1 - reserve_factor)
        
        # Current rates
        current_borrow_rate = calculate_borrow_rate(current_utilization)
        current_supply_rate = calculate_supply_rate(current_borrow_rate, current_utilization)
        
        # New rates after strategy impact
        new_borrow_rate = calculate_borrow_rate(new_utilization)
        new_supply_rate = calculate_supply_rate(new_borrow_rate, new_utilization)
        
        # Calculate impacts
        borrow_rate_impact = new_borrow_rate - current_borrow_rate
        supply_rate_impact = new_supply_rate - current_supply_rate
        utilization_impact = new_utilization - current_utilization
        
        return {
            'current_state': {
                'total_supply': total_supply,
                'total_borrows': total_borrows,
                'utilization_rate': current_utilization,
                'borrow_rate': current_borrow_rate,
                'supply_rate': current_supply_rate
            },
            'new_state': {
                'total_supply': new_total_supply,
                'total_borrows': new_total_borrows,
                'utilization_rate': new_utilization,
                'borrow_rate': new_borrow_rate,
                'supply_rate': new_supply_rate
            },
            'impacts': {
                'additional_supply': additional_supply,
                'additional_borrow': additional_borrow,
                'utilization_change': utilization_impact,
                'borrow_rate_change': borrow_rate_impact,
                'supply_rate_change': supply_rate_impact,
                'borrow_rate_change_bps': borrow_rate_impact * 10000,  # Basis points
                'supply_rate_change_bps': supply_rate_impact * 10000
            },
            'model_parameters': {
                'optimal_utilization': optimal_utilization,
                'base_rate': base_rate,
                'slope1': slope1,
                'slope2': slope2,
                'reserve_factor': reserve_factor
            }
        }
    
    async def download_aave_rates(self, market: str, symbol: str, 
                                start_date: str, end_date: str) -> Dict:
        """
        Download AAVE rates for a specific asset.
        
        Args:
            market: AAVE market identifier
            symbol: Asset symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Download result dictionary
        """
        if self.placeholder_mode:
            self.logger.warning(f"🔄 Placeholder download for {symbol} ({start_date} to {end_date})")
            
            # Create placeholder CSV file
            filename = f"aave_v3_{market}_{symbol}_rates_{start_date}_{end_date}_PLACEHOLDER.csv"
            csv_data = self._generate_placeholder_csv(symbol)
            
            filepath = self.output_dir / filename
            with open(filepath, 'wb') as f:
                f.write(csv_data)
            
            return {
                'success': True,
                'placeholder': True,
                'market': market,
                'symbol': symbol,
                'record_count': 2,  # Placeholder records
                'output_file': str(filepath),
                'date_range': f"{start_date} to {end_date}",
                'message': "Placeholder data created - waiting for AaveScan Pro API key"
            }
        
        self.logger.info(f"Downloading {symbol} AAVE rates from {start_date} to {end_date}")
        
        # Get reserve address for this symbol on this chain
        if market not in self.chain_assets:
            # Discover assets for this chain
            self.chain_assets[market] = await self.discover_chain_assets(market)
        
        chain_assets = self.chain_assets.get(market, {})
        reserve_address = chain_assets.get(symbol)
        
        if not reserve_address:
            self.logger.warning(f"Asset {symbol} not available on {market}")
            return {
                'success': False,
                'market': market,
                'symbol': symbol,
                'record_count': 0,
                'error': f'Asset {symbol} not available on {market}'
            }
        
        # Try CSV bulk export first (more efficient for historical data)
        csv_data = await self.get_csv_export(market, symbol, reserve_address)
        
        if csv_data:
            filename = f"aave_v3_{market}_{symbol}_rates_{start_date}_{end_date}.csv"
            filepath = self.output_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(csv_data)
            
            # Parse CSV to count records (simplified)
            record_count = csv_data.decode('utf-8').count('\n') - 1  # Subtract header
            
            return {
                'success': True,
                'market': market,
                'symbol': symbol,
                'record_count': record_count,
                'output_file': str(filepath),
                'date_range': f"{start_date} to {end_date}",
                'method': 'csv_export'
            }
        else:
            # Fall back to API historical endpoint
            historical_data = await self.get_reserves_historical(market, symbol, start_date, end_date)
            
            if historical_data:
                # Convert API data to CSV format (implementation would depend on actual API response)
                # This is a placeholder for the actual conversion logic
                filename = f"aave_v3_{market}_{symbol}_rates_{start_date}_{end_date}.csv"
                # ... conversion logic would go here ...
                
                return {
                    'success': True,
                    'market': market,
                    'symbol': symbol,
                    'record_count': 0,  # Would be actual count
                    'output_file': None,  # Would be actual file
                    'date_range': f"{start_date} to {end_date}",
                    'method': 'api_historical'
                }
            else:
                return {
                    'success': False,
                    'market': market,
                    'symbol': symbol,
                    'record_count': 0,
                    'error': 'Failed to get data from both CSV and API endpoints'
                }
    
    async def download_all_aave_data(self, start_date: Optional[str] = None, 
                                   end_date: Optional[str] = None) -> Dict:
        """
        Download AAVE data for all configured markets and assets.
        
        Args:
            start_date: Start date (YYYY-MM-DD), uses config default if None
            end_date: End date (YYYY-MM-DD), uses config default if None
            
        Returns:
            Combined download results
        """
        if start_date is None or end_date is None:
            config_start, config_end = self.get_date_range()
            start_date = start_date or config_start
            end_date = end_date or config_end
        
        if self.placeholder_mode:
            self.logger.warning("🔄 PLACEHOLDER MODE: Creating sample AAVE data structure")
        
        self.logger.info(f"Starting AAVE data download for {len(self.aave_markets)} markets")
        self.logger.info(f"Target assets: {', '.join(self.target_assets)}")
        self.logger.info(f"Date range: {start_date} to {end_date}")
        self.logger.info(f"Markets: {', '.join(self.aave_markets.keys())}")
        
        download_results = []
        
        # Note: Oracle prices are included in the 'price' column of each asset's CSV data
        # No separate oracle collection needed
        
        # Download data for each market and asset combination
        for market_name, market_id in self.aave_markets.items():
            for asset_symbol in self.target_assets:
                try:
                    # Set minimum floor dates for each asset
                    floor_dates = {
                        'wstETH': '2024-05-12',  # LST launch date
                        'weETH': '2024-05-12',   # LST launch date
                        'WETH': '2024-01-01',    # Earlier availability
                        'USDT': '2024-01-01'     # Earlier availability
                    }
                    
                    # Use the later of command line start_date or asset floor date
                    floor_date = floor_dates.get(asset_symbol, start_date)
                    asset_start_date = max(start_date, floor_date)
                    
                    if asset_start_date != start_date:
                        self.logger.info(f"Using floor date {asset_start_date} for {asset_symbol} (command line: {start_date})")
                    else:
                        self.logger.info(f"Using command line date {asset_start_date} for {asset_symbol}")
                    
                    result = await self.download_aave_rates(market_id, asset_symbol, asset_start_date, end_date)
                    
                    # Filter data to respect floor dates if API returned earlier data
                    if result['success'] and 'output_file' in result:
                        result = self._filter_data_by_floor_date(result, asset_start_date)
                    
                    download_results.append(result)
                    
                    if result['success']:
                        status = "🔄 PLACEHOLDER" if result.get('placeholder') else "✅"
                        self.logger.info(f"{status} {market_name}/{asset_symbol}: {result['record_count']} records (from {asset_start_date})")
                    else:
                        self.logger.error(f"❌ {market_name}/{asset_symbol}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    self.logger.error(f"❌ {market_name}/{asset_symbol}: Unexpected error - {e}")
                    download_results.append({
                        'success': False,
                        'market': market_id,
                        'symbol': asset_symbol,
                        'error': str(e),
                        'record_count': 0
                    })
        
        # Create summary report
        report = self.create_summary_report(download_results)
        
        if self.placeholder_mode:
            report['placeholder_mode'] = True
            report['api_key_status'] = 'PENDING - Waiting for AaveScan Pro API key'
        
        report_filename = f"aavescan_report_{start_date}_{end_date}"
        if self.placeholder_mode:
            report_filename += "_PLACEHOLDER"
        report_filename += ".json"
        
        report_file = self.save_report(report, report_filename)
        
        return report
    
    def _filter_data_by_floor_date(self, result: Dict, floor_date: str) -> Dict:
        """
        Filter downloaded data to respect floor dates if API returned earlier data.
        
        Args:
            result: Download result dictionary
            floor_date: Minimum date to keep (YYYY-MM-DD)
            
        Returns:
            Updated result dictionary with filtered data
        """
        try:
            import pandas as pd
            from datetime import datetime
            
            file_path = result['output_file']
            df = pd.read_csv(file_path)
            
            # Convert date columns
            if 'targetDate' in df.columns:
                df['date'] = pd.to_datetime(df['targetDate']).dt.date
            elif 'timestamp' in df.columns:
                df['date'] = pd.to_datetime(df['timestamp']).dt.date
            else:
                return result  # No date column to filter
            
            # Convert floor date
            floor_date_obj = datetime.strptime(floor_date, '%Y-%m-%d').date()
            
            # Filter data
            original_count = len(df)
            df_filtered = df[df['date'] >= floor_date_obj].copy()
            filtered_count = len(df_filtered)
            
            if filtered_count < original_count:
                # Save filtered data
                df_filtered.to_csv(file_path, index=False)
                
                # Update result
                result['record_count'] = filtered_count
                result['filtered'] = True
                result['original_count'] = original_count
                result['floor_date'] = floor_date
                
                self.logger.info(f"Filtered {original_count} → {filtered_count} records for floor date {floor_date}")
            
            return result
            
        except Exception as e:
            self.logger.warning(f"Failed to filter data by floor date: {e}")
            return result
    
    async def download_data(self, start_date: str, end_date: str) -> Dict:
        """
        Main download method (implements abstract base method).
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Download results
        """
        return await self.download_all_aave_data(start_date, end_date)
