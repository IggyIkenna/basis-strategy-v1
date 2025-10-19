#!/usr/bin/env python3
"""
Data Files Quality Gates - Consolidated

Validates that all required data files exist and are accessible.
Simple validation that doesn't depend on complex imports.

Consolidated from:
- test_data_files_quality_gates.py
- test_data_availability_quality_gates.py (file existence parts)
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Set, Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')


class DataFilesQualityGates:
    """Quality gates for data files validation."""
    
    def __init__(self):
        self.results = {
            'overall_status': 'PENDING',
            'data_directories': {},
            'required_files': {},
            'file_accessibility': {}
        }
        
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        
        # Required data directories
        self.required_directories = [
            'market_data',
            'protocol_data', 
            'blockchain_data',
            'execution_costs',
            'analysis',
            'manual_sources'
        ]
        
        # Critical data files that must exist
        self.critical_files = [
            'market_data/spot_prices/btc_usd/binance_BTCUSDT_1h_2024-01-01_2025-09-30.csv',
            'market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv',
            'market_data/derivatives/funding_rates/binance_BTCUSDT_funding_rates_2024-01-01_2025-09-30.csv',
            'ml_data/predictions/btc_predictions.csv',
            'ml_data/predictions/usdt_predictions.csv',
            'market_data/derivatives/futures_ohlcv/binance_BTCUSDT_perp_1h_2024-01-01_2025-09-30.csv',
            'execution_costs/execution_cost_simulation_results.csv',
            'market_data/spot_prices/protocol_tokens/binance_EIGENUSDT_1h_2024-10-05_2025-09-30.csv',
            'market_data/spot_prices/protocol_tokens/binance_ETHFIUSDT_1h_2024-06-01_2025-09-30.csv'
        ]
    
    def validate_data_directories(self) -> Dict[str, Any]:
        """Validate that all required data directories exist."""
        print("🔍 Validating data directories...")
        
        directory_results = {}
        missing_directories = []
        
        for directory in self.required_directories:
            dir_path = self.data_dir / directory
            exists = dir_path.exists()
            directory_results[directory] = {
                'exists': exists,
                'path': str(dir_path)
            }
            
            if not exists:
                missing_directories.append(directory)
                print(f"  ❌ Missing directory: {directory}")
            else:
                print(f"  ✅ Directory exists: {directory}")
        
        self.results['data_directories'] = directory_results
        
        if missing_directories:
            print(f"❌ Missing {len(missing_directories)} required directories")
            return {'status': 'FAILED', 'missing_directories': missing_directories}
        else:
            print("✅ All required directories exist")
            return {'status': 'PASSED', 'missing_directories': []}
    
    def validate_critical_files(self) -> Dict[str, Any]:
        """Validate that all critical data files exist."""
        print("🔍 Validating critical data files...")
        
        file_results = {}
        missing_files = []
        
        for file_path in self.critical_files:
            full_path = self.data_dir / file_path
            exists = full_path.exists()
            size = full_path.stat().st_size if exists else 0
            
            file_results[file_path] = {
                'exists': exists,
                'size_bytes': size,
                'size_mb': round(size / (1024 * 1024), 2) if exists else 0
            }
            
            if not exists:
                missing_files.append(file_path)
                print(f"  ❌ Missing file: {file_path}")
            else:
                print(f"  ✅ {file_path}: {file_results[file_path]['size_mb']} MB")
        
        self.results['required_files'] = file_results
        
        if missing_files:
            print(f"❌ Missing {len(missing_files)} critical files")
            return {'status': 'FAILED', 'missing_files': missing_files}
        else:
            print("✅ All critical files exist")
            return {'status': 'PASSED', 'missing_files': []}
    
    def validate_file_accessibility(self) -> Dict[str, Any]:
        """Validate that files are readable."""
        print("🔍 Validating file accessibility...")
        
        accessibility_results = {}
        inaccessible_files = []
        
        for file_path in self.critical_files:
            full_path = self.data_dir / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        # Try to read first line
                        f.readline()
                    accessible = True
                except Exception as e:
                    accessible = False
                    inaccessible_files.append(file_path)
                    print(f"  ❌ Cannot read {file_path}: {e}")
            else:
                accessible = False
                inaccessible_files.append(file_path)
                print(f"  ❌ File does not exist: {file_path}")
            
            accessibility_results[file_path] = {
                'accessible': accessible,
                'path': str(full_path)
            }
        
        self.results['file_accessibility'] = accessibility_results
        
        if inaccessible_files:
            print(f"❌ {len(inaccessible_files)} files are not accessible")
            return {'status': 'FAILED', 'inaccessible_files': inaccessible_files}
        else:
            print("✅ All files are accessible")
            return {'status': 'PASSED', 'inaccessible_files': []}
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all data file quality gate checks."""
        print("🚀 Starting data files quality gate test...")
        print("=" * 80)
        
        # Run all checks
        directory_check = self.validate_data_directories()
        file_check = self.validate_critical_files()
        accessibility_check = self.validate_file_accessibility()
        
        # Determine overall status
        all_passed = (
            directory_check['status'] == 'PASSED' and
            file_check['status'] == 'PASSED' and
            accessibility_check['status'] == 'PASSED'
        )
        
        self.results['overall_status'] = 'PASSED' if all_passed else 'FAILED'
        
        # Print summary
        print("=" * 80)
        print("📊 DATA FILES QUALITY GATE SUMMARY")
        print("=" * 80)
        print(f"📁 Data Directories: {directory_check['status']}")
        print(f"📄 Critical Files: {file_check['status']}")
        print(f"🔓 File Accessibility: {accessibility_check['status']}")
        print(f"📈 Overall Status: {self.results['overall_status']}")
        
        if not all_passed:
            print("\n❌ FAILURE: Data files quality gates failed!")
            return False
        else:
            print("\n✅ SUCCESS: All data files quality gates passed!")
            return True


def main():
    """Main entry point for data files quality gates."""
    checker = DataFilesQualityGates()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()