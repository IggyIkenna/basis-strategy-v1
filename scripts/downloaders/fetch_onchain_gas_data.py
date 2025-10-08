"""
On-Chain Gas Data Downloader - Gas prices only.

Downloads:
- Gas price data (Alchemy): Hourly gas price averages for transaction cost modeling
- Uses Alchemy JSON-RPC for accurate historical gas prices (base fee + priority fee percentiles)
- Multi-chain support: Ethereum
- Follows same pattern as other downloaders with load_env.sh

Note: LST exchange rates are now handled by fetch_pool_data.py via CoinGecko
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add the backend source to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "backend" / "src"))

# Handle both standalone and module imports
try:
    from .clients.alchemy_client_fast import FastAlchemyClient
    from .base_downloader import BaseDownloader
except ImportError:
    # Standalone execution
    sys.path.append(str(Path(__file__).parent))
    from clients.alchemy_client_fast import FastAlchemyClient
    from base_downloader import BaseDownloader


class OnChainGasDataDownloader(BaseDownloader):
    """
    On-chain gas data downloader for gas prices only.
    
    Features:
    - Accurate gas price data via Alchemy JSON-RPC (eth_feeHistory)
    - Base fee + priority fee percentiles for accurate gas pricing
    - Multi-chain support
    - Transaction cost modeling data
    - Uses environment variables for API configuration
    
    Note: LST rates removed - handled by fetch_pool_data.py
    """
    
    def __init__(self, output_dir: str = "data/blockchain_data"):
        super().__init__("onchain_gas_data", output_dir)
        
        # Initialize gas data output directory
        self.gas_output_dir = f"{output_dir}/gas_prices"
        Path(self.gas_output_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize Fast Alchemy client for accurate gas data
        try:
            self.alchemy_client = FastAlchemyClient(self.gas_output_dir)
            self.logger.info("✅ Fast Alchemy client initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Fast Alchemy client: {e}")
            self.alchemy_client = None
            raise RuntimeError("Alchemy client required for gas data")
    
    async def download_gas_data(self, start_date: str, end_date: str) -> Optional[Dict]:
        """
        Download gas price data via Alchemy JSON-RPC.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Gas data download results or None if failed
        """
        if not self.alchemy_client:
            self.logger.error("❌ Alchemy client not available")
            return None
        
        self.logger.info("🔄 Starting gas price data download (Alchemy JSON-RPC)")
        
        try:
            result = await self.alchemy_client.download_all_gas_data(start_date, end_date)
            
            successful = result.get('successful_downloads', 0)
            total = result.get('total_downloads', 0)
            records = result.get('total_records', 0)
            
            self.logger.info(f"✅ Gas data complete (Alchemy): {successful}/{total} chains, {records} total records")
            self.logger.info(f"✅ Using accurate historical gas data with base fee + priority fee percentiles")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Alchemy gas data download failed: {e}")
            return None
    
    # LST rates functionality removed - now handled by fetch_pool_data.py orchestrator
    
    async def calculate_gas_costs_usd(self, gas_data_file: str, eth_price_data: Dict) -> List[Dict]:
        """
        Calculate gas costs in USD using ETH price data.
        
        Args:
            gas_data_file: Path to gas price CSV file
            eth_price_data: ETH price data from CoinGecko
            
        Returns:
            List of gas cost records with USD values
        """
        import pandas as pd
        
        try:
            # Load gas data
            gas_df = pd.read_csv(gas_data_file)
            gas_df['timestamp'] = pd.to_datetime(gas_df['timestamp'])
            
            # Common gas usage estimates (in gas units)
            gas_operations = {
                'stake_eth_to_eeth': 21000,      # Placeholder - needs validation
                'deposit_to_aave': 150000,       # Placeholder - needs validation  
                'borrow_from_aave': 200000,      # Placeholder - needs validation
                'repay_aave_loan': 180000,       # Placeholder - needs validation
                'withdraw_from_aave': 160000     # Placeholder - needs validation
            }
            
            # Calculate USD costs for each operation
            enriched_records = []
            
            for _, row in gas_df.iterrows():
                base_record = row.to_dict()
                
                # Get ETH price for this timestamp (simplified lookup)
                eth_price_usd = 3300.0  # Placeholder - would need actual price lookup
                
                # Calculate gas costs for each operation
                for operation, gas_units in gas_operations.items():
                    gas_cost_eth = (row['gas_price_gwei'] * 1e-9) * gas_units
                    gas_cost_usd = gas_cost_eth * eth_price_usd
                    
                    base_record[f'{operation}_gas_cost_usd'] = round(gas_cost_usd, 4)
                
                enriched_records.append(base_record)
            
            return enriched_records
            
        except Exception as e:
            self.logger.error(f"Failed to calculate gas costs USD: {e}")
            return []
    
    async def download_data(self, start_date: str, end_date: str) -> Dict:
        """
        Download gas price data only.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Gas download results
        """
        self.logger.info("🚀 Starting gas price data download")
        self.logger.info(f"📅 Date range: {start_date} to {end_date}")
        
        # Download gas data only
        gas_result = await self.download_gas_data(start_date, end_date)
        
        # Handle exceptions
        if isinstance(gas_result, Exception):
            self.logger.error(f"Gas download exception: {gas_result}")
            gas_result = None
        
        # Create report
        if gas_result:
            gas_downloads = gas_result.get('downloads', [])
            total_records = gas_result.get('total_records', 0)
            successful_downloads = gas_result.get('successful_downloads', 0)
            
            combined_report = {
                'timestamp': datetime.now().isoformat(),
                'downloader': 'onchain_gas_data',
                'date_range': f"{start_date} to {end_date}",
                'total_downloads': len(gas_downloads),
                'successful_downloads': successful_downloads,
                'failed_downloads': len(gas_downloads) - successful_downloads,
                'total_records': total_records,
                'gas_result': gas_result,
                'downloads': gas_downloads,
                'data_source': 'alchemy'
            }
        else:
            combined_report = {
                'timestamp': datetime.now().isoformat(),
                'downloader': 'onchain_gas_data',
                'date_range': f"{start_date} to {end_date}",
                'total_downloads': 0,
                'successful_downloads': 0,
                'failed_downloads': 0,
                'total_records': 0,
                'gas_result': None,
                'downloads': [],
                'data_source': 'alchemy'
            }
        
        # Save report
        report_file = self.save_report(
            combined_report, 
            f"onchain_gas_data_report_{start_date}_{end_date}.json"
        )
        
        # Log summary
        self.logger.info("=" * 70)
        self.logger.info("🎯 ON-CHAIN GAS DATA DOWNLOAD COMPLETE!")
        self.logger.info("=" * 70)
        self.logger.info(f"✅ Total downloads: {combined_report['total_downloads']}")
        self.logger.info(f"✅ Successful: {combined_report['successful_downloads']}")
        self.logger.info(f"❌ Failed: {combined_report['failed_downloads']}")
        self.logger.info(f"📊 Total records: {combined_report['total_records']:,}")
        
        if gas_result:
            gas_records = gas_result.get('total_records', 0)
            self.logger.info(f"   ⛽ Gas data (Alchemy): {gas_records:,} records")
        
        self.logger.info(f"💾 Report saved: {report_file}")
        self.logger.info("=" * 70)
        
        return combined_report


async def main():
    """
    Main execution function for standalone script usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Download on-chain gas price data")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default="data/blockchain_data", help="Output directory")
    parser.add_argument("--quick-test", action="store_true", help="Run with last 3 days for testing")
    
    args = parser.parse_args()
    
    try:
        # Initialize downloader
        downloader = OnChainGasDataDownloader(args.output_dir)
        
        # Use provided dates, current date defaults, or quick test
        from datetime import datetime, timedelta
        if args.quick_test:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
            print(f"🚀 Quick test mode: {start_date} to {end_date}")
        elif args.start_date and args.end_date:
            start_date, end_date = args.start_date, args.end_date
        elif args.start_date:
            # Only start date provided, use current date as end date
            start_date = args.start_date
            end_date = datetime.now().strftime('%Y-%m-%d')
            print(f"Using provided start date with current end date: {start_date} to {end_date}")
        else:
            # No dates provided, use last 30 days
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            print(f"Using default date range (last 30 days): {start_date} to {end_date}")
        
        print(f"Using Alchemy JSON-RPC for accurate historical gas data")
        
        # Run download
        result = await downloader.download_data(start_date, end_date)
        
        # Print summary
        if result['successful_downloads'] > 0:
            print(f"\n🎉 SUCCESS! Downloaded {result['total_records']:,} gas price records")
            print(f"📊 Data source: Alchemy (accurate)")
            print(f"📁 Output directory: {args.output_dir}/gas_prices/")
        else:
            print(f"\n❌ FAILED! No gas price data was downloaded successfully")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
