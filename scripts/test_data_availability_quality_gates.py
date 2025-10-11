#!/usr/bin/env python3
"""
Data Availability Quality Gates

Comprehensive pre-check quality gate for all data files to validate data completeness,
alignment, and availability for all strategy modes before proceeding with implementation.

Reference: .cursor/tasks/03_data_loading_quality_gate.md
Reference: docs/specs/09_DATA_PROVIDER.md
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'backend' / 'src'))

from basis_strategy_v1.infrastructure.data.data_validator import DataValidator, DataProviderError

logger = logging.getLogger(__name__)


class DataAvailabilityChecker:
    """Comprehensive data availability checker for all strategy modes"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.market_data_dir = self.data_dir / "market_data"
        self.protocol_data_dir = self.data_dir / "protocol_data"
        self.blockchain_data_dir = self.data_dir / "blockchain_data"
        self.execution_costs_dir = self.data_dir / "execution_costs"
        self.manual_sources_dir = self.data_dir / "manual_sources"
        
        # Initialize data validator
        self.validator = DataValidator(str(data_dir))
        
        # Strategy data requirements mapping
        self.strategy_data_requirements = {
            'pure_lending': {
                'protocols': ['aave_v3'],
                'assets': ['USDT'],
                'timeframes': ['1h'],
                'required_fields': ['apy', 'total_supply', 'liquidity_index']
            },
            'btc_basis': {
                'venues': ['binance', 'bybit', 'okx'],
                'assets': ['BTC'],
                'timeframes': ['1h'],
                'required_fields': ['funding_rate', 'spot_price', 'futures_price']
            },
            'eth_basis': {
                'venues': ['binance', 'bybit', 'okx'],
                'assets': ['ETH'],
                'timeframes': ['1h'],
                'required_fields': ['funding_rate', 'spot_price', 'futures_price']
            },
            'eth_leveraged': {
                'venues': [],
                'protocols': ['aave_v3', 'etherfi'],
                'assets': ['ETH', 'weETH', 'WETH'],
                'timeframes': ['1h'],
                'required_fields': ['apy', 'oracle_price', 'staking_yield', 'liquidity_index']
            },
            'eth_staking_only': {
                'venues': [],
                'protocols': ['etherfi'],
                'assets': ['ETH', 'weETH'],
                'timeframes': ['1h'],
                'required_fields': ['oracle_price', 'staking_yield']
            },
            'usdt_market_neutral_no_leverage': {
                'venues': ['binance', 'bybit', 'okx'],
                'protocols': ['etherfi'],
                'assets': ['ETH', 'weETH'],
                'timeframes': ['1h'],
                'required_fields': ['funding_rate', 'spot_price', 'futures_price', 'oracle_price', 'staking_yield']
            },
            'usdt_market_neutral': {
                'venues': ['binance', 'bybit', 'okx'],
                'protocols': ['aave_v3', 'etherfi'],
                'assets': ['ETH', 'weETH', 'WETH'],
                'timeframes': ['1h'],
                'required_fields': ['funding_rate', 'spot_price', 'futures_price', 'apy', 'oracle_price', 'staking_yield', 'liquidity_index']
            }
        }
    
    def check_all_data_availability(self) -> Dict[str, Any]:
        """
        Check all data availability for all strategy modes.
        
        Returns:
            Comprehensive data availability report
        """
        logger.info("🔍 Starting comprehensive data availability check...")
        
        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'data_directory': str(self.data_dir),
            'strategy_modes': {},
            'overall_status': 'unknown',
            'summary': {
                'total_modes': len(self.strategy_data_requirements),
                'modes_with_complete_data': 0,
                'modes_with_missing_data': 0,
                'total_files_checked': 0,
                'total_files_missing': 0
            }
        }
        
        # Check each strategy mode
        for mode, requirements in self.strategy_data_requirements.items():
            logger.info(f"📊 Checking data availability for mode: {mode}")
            mode_report = self._check_strategy_mode_data(mode, requirements)
            report['strategy_modes'][mode] = mode_report
            
            if mode_report['status'] == 'complete':
                report['summary']['modes_with_complete_data'] += 1
            else:
                report['summary']['modes_with_missing_data'] += 1
            
            report['summary']['total_files_checked'] += mode_report['files_checked']
            report['summary']['total_files_missing'] += mode_report['files_missing']
        
        # Determine overall status
        if report['summary']['modes_with_missing_data'] == 0:
            report['overall_status'] = 'complete'
        elif report['summary']['modes_with_complete_data'] == 0:
            report['overall_status'] = 'incomplete'
        else:
            report['overall_status'] = 'partial'
        
        logger.info(f"✅ Data availability check complete: {report['overall_status']}")
        logger.info(f"📈 Summary: {report['summary']['modes_with_complete_data']}/{report['summary']['total_modes']} modes complete")
        
        return report
    
    def _check_strategy_mode_data(self, mode: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check data availability for a specific strategy mode.
        
        Args:
            mode: Strategy mode name
            requirements: Data requirements for the mode
            
        Returns:
            Mode-specific data availability report
        """
        mode_report = {
            'mode': mode,
            'status': 'unknown',
            'files_checked': 0,
            'files_missing': 0,
            'missing_files': [],
            'available_files': [],
            'data_quality_issues': [],
            'requirements': requirements
        }
        
        try:
            # Check market data
            market_files = self._check_market_data(mode, requirements)
            mode_report['files_checked'] += len(market_files['checked'])
            mode_report['files_missing'] += len(market_files['missing'])
            mode_report['missing_files'].extend(market_files['missing'])
            mode_report['available_files'].extend(market_files['available'])
            
            # Check protocol data
            protocol_files = self._check_protocol_data(mode, requirements)
            mode_report['files_checked'] += len(protocol_files['checked'])
            mode_report['files_missing'] += len(protocol_files['missing'])
            mode_report['missing_files'].extend(protocol_files['missing'])
            mode_report['available_files'].extend(protocol_files['available'])
            
            # Check blockchain data
            blockchain_files = self._check_blockchain_data()
            mode_report['files_checked'] += len(blockchain_files['checked'])
            mode_report['files_missing'] += len(blockchain_files['missing'])
            mode_report['missing_files'].extend(blockchain_files['missing'])
            mode_report['available_files'].extend(blockchain_files['available'])
            
            # Check execution costs
            execution_files = self._check_execution_costs()
            mode_report['files_checked'] += len(execution_files['checked'])
            mode_report['files_missing'] += len(execution_files['missing'])
            mode_report['missing_files'].extend(execution_files['missing'])
            mode_report['available_files'].extend(execution_files['available'])
            
            # Validate data quality for available files
            quality_issues = self._validate_data_quality(mode_report['available_files'])
            mode_report['data_quality_issues'] = quality_issues
            
            # Determine status
            if mode_report['files_missing'] == 0 and len(quality_issues) == 0:
                mode_report['status'] = 'complete'
            elif mode_report['files_missing'] > 0:
                mode_report['status'] = 'missing_files'
            else:
                mode_report['status'] = 'quality_issues'
                
        except Exception as e:
            logger.error(f"❌ Error checking data for mode {mode}: {e}")
            mode_report['status'] = 'error'
            mode_report['error'] = str(e)
        
        return mode_report
    
    def _check_market_data(self, mode: str, requirements: Dict[str, Any]) -> Dict[str, List[str]]:
        """Check market data availability for strategy mode."""
        checked_files = []
        missing_files = []
        available_files = []
        
        # Check spot prices
        for asset in requirements.get('assets', []):
            if asset in ['ETH', 'BTC']:
                spot_file = self.market_data_dir / f"spot_prices/{asset.lower()}_usd/binance_{asset}USDT_1h_2020-01-01_2025-09-26.csv"
                checked_files.append(str(spot_file))
                
                if spot_file.exists():
                    available_files.append(str(spot_file))
                else:
                    missing_files.append(str(spot_file))
        
        # Check futures data
        for venue in requirements.get('venues', []):
            for asset in requirements.get('assets', []):
                if asset in ['ETH', 'BTC']:
                    futures_file = self.market_data_dir / f"derivatives/futures_ohlcv/{venue}_{asset}USDT_perp_1h_2024-01-01_2025-09-30.csv"
                    checked_files.append(str(futures_file))
                    
                    if futures_file.exists():
                        available_files.append(str(futures_file))
                    else:
                        missing_files.append(str(futures_file))
        
        # Check funding rates
        for venue in requirements.get('venues', []):
            for asset in requirements.get('assets', []):
                if asset in ['ETH', 'BTC']:
                    funding_file = self.market_data_dir / f"derivatives/funding_rates/{venue}_{asset}USDT_funding_rates_2024-01-01_2025-09-30.csv"
                    checked_files.append(str(funding_file))
                    
                    if funding_file.exists():
                        available_files.append(str(funding_file))
                    else:
                        missing_files.append(str(funding_file))
        
        return {
            'checked': checked_files,
            'missing': missing_files,
            'available': available_files
        }
    
    def _check_protocol_data(self, mode: str, requirements: Dict[str, Any]) -> Dict[str, List[str]]:
        """Check protocol data availability for strategy mode."""
        checked_files = []
        missing_files = []
        available_files = []
        
        # Check AAVE data
        if 'aave_v3' in requirements.get('protocols', []):
            for asset in ['USDT', 'WETH', 'weETH']:
                if asset in requirements.get('assets', []) or asset == 'USDT':
                    aave_file = self.protocol_data_dir / f"aave/rates/aave_v3_aave-v3-ethereum_{asset}_rates_2024-01-01_2025-09-18_hourly.csv"
                    checked_files.append(str(aave_file))
                    
                    if aave_file.exists():
                        available_files.append(str(aave_file))
                    else:
                        missing_files.append(str(aave_file))
            
            # Check AAVE risk parameters
            risk_file = self.protocol_data_dir / "aave/risk_params/aave_v3_risk_parameters.json"
            checked_files.append(str(risk_file))
            
            if risk_file.exists():
                available_files.append(str(risk_file))
            else:
                missing_files.append(str(risk_file))
            
            # Check oracle prices
            for asset in ['weETH', 'wstETH']:
                if asset in requirements.get('assets', []):
                    oracle_file = self.protocol_data_dir / f"aave/oracle/{asset}_ETH_oracle_2024-01-01_2025-09-18.csv"
                    checked_files.append(str(oracle_file))
                    
                    if oracle_file.exists():
                        available_files.append(str(oracle_file))
                    else:
                        missing_files.append(str(oracle_file))
        
        # Check staking data
        if 'etherfi' in requirements.get('protocols', []):
            staking_file = self.protocol_data_dir / "staking/base_staking_yields_2024-01-01_2025-09-18_hourly.csv"
            checked_files.append(str(staking_file))
            
            if staking_file.exists():
                available_files.append(str(staking_file))
            else:
                missing_files.append(str(staking_file))
            
            # Check seasonal rewards
            rewards_file = self.protocol_data_dir / "staking/restaking_final/etherfi_seasonal_rewards_2024-01-01_2025-09-18.csv"
            checked_files.append(str(rewards_file))
            
            if rewards_file.exists():
                available_files.append(str(rewards_file))
            else:
                missing_files.append(str(rewards_file))
        
        return {
            'checked': checked_files,
            'missing': missing_files,
            'available': available_files
        }
    
    def _check_blockchain_data(self) -> Dict[str, List[str]]:
        """Check blockchain data availability."""
        checked_files = []
        missing_files = []
        available_files = []
        
        # Check gas costs
        gas_files = [
            self.blockchain_data_dir / "gas_prices/ethereum_gas_prices_enhanced_2024-01-01_2025-09-26.csv",
            self.blockchain_data_dir / "gas_prices/ethereum_gas_prices_2024-01-01_2025-09-26.csv"
        ]
        
        for gas_file in gas_files:
            checked_files.append(str(gas_file))
            if gas_file.exists():
                available_files.append(str(gas_file))
                break  # Only need one gas file
        else:
            missing_files.append(str(gas_files[0]))  # Report first one as missing
        
        return {
            'checked': checked_files,
            'missing': missing_files,
            'available': available_files
        }
    
    def _check_execution_costs(self) -> Dict[str, List[str]]:
        """Check execution costs data availability."""
        checked_files = []
        missing_files = []
        available_files = []
        
        # Check execution costs
        exec_file = self.execution_costs_dir / "execution_cost_simulation_results.csv"
        checked_files.append(str(exec_file))
        
        if exec_file.exists():
            available_files.append(str(exec_file))
        else:
            missing_files.append(str(exec_file))
        
        # Check lookup table
        lookup_file = self.execution_costs_dir / "lookup_tables/execution_costs_lookup.json"
        checked_files.append(str(lookup_file))
        
        if lookup_file.exists():
            available_files.append(str(lookup_file))
        else:
            missing_files.append(str(lookup_file))
        
        return {
            'checked': checked_files,
            'missing': missing_files,
            'available': available_files
        }
    
    def _validate_data_quality(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Validate data quality for available files."""
        quality_issues = []
        
        for file_path in file_paths:
            try:
                # Skip non-CSV files
                if not file_path.endswith('.csv'):
                    continue
                
                # Validate file
                self.validator.validate_data_file(Path(file_path))
                
            except DataProviderError as e:
                quality_issues.append({
                    'file': file_path,
                    'error_code': e.error_code,
                    'message': e.message,
                    'context': e.context
                })
            except Exception as e:
                quality_issues.append({
                    'file': file_path,
                    'error_code': 'UNKNOWN',
                    'message': str(e)
                })
        
        return quality_issues


def test_data_availability():
    """Test data availability for all strategy modes."""
    logger.info("🚀 Starting data availability quality gate test...")
    
    try:
        # Initialize checker
        checker = DataAvailabilityChecker()
        
        # Run comprehensive check
        report = checker.check_all_data_availability()
        
        # Print summary
        print("\n" + "="*80)
        print("DATA AVAILABILITY QUALITY GATE RESULTS")
        print("="*80)
        print(f"Overall Status: {report['overall_status'].upper()}")
        print(f"Data Directory: {report['data_directory']}")
        print(f"Timestamp: {report['timestamp']}")
        print()
        
        print("STRATEGY MODE SUMMARY:")
        print("-" * 40)
        for mode, mode_report in report['strategy_modes'].items():
            status_emoji = "✅" if mode_report['status'] == 'complete' else "❌"
            print(f"{status_emoji} {mode}: {mode_report['status']}")
            if mode_report['files_missing'] > 0:
                print(f"   Missing files: {mode_report['files_missing']}")
            if mode_report['data_quality_issues']:
                print(f"   Quality issues: {len(mode_report['data_quality_issues'])}")
        
        print()
        print("OVERALL SUMMARY:")
        print("-" * 40)
        summary = report['summary']
        print(f"Total modes: {summary['total_modes']}")
        print(f"Complete modes: {summary['modes_with_complete_data']}")
        print(f"Incomplete modes: {summary['modes_with_missing_data']}")
        print(f"Total files checked: {summary['total_files_checked']}")
        print(f"Total files missing: {summary['total_files_missing']}")
        
        # Check if test passed
        if report['overall_status'] == 'complete':
            print("\n🎉 DATA AVAILABILITY QUALITY GATE: PASSED")
            return True
        else:
            print("\n❌ DATA AVAILABILITY QUALITY GATE: FAILED")
            return False
            
    except Exception as e:
        logger.error(f"❌ Data availability test failed: {e}")
        print(f"\n❌ DATA AVAILABILITY QUALITY GATE: ERROR - {e}")
        return False


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    success = test_data_availability()
    sys.exit(0 if success else 1)