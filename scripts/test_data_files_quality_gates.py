#!/usr/bin/env python3
"""
Data Files Quality Gates

Validates that all required data files exist and are accessible.
Simple validation that doesn't depend on complex imports.

Reference: data/ directory structure
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
    
    def validate_data_directories(self) -> Dict[str, Any]:
        """Validate that all required data directories exist."""
        print("🔍 Validating data directories...")
        
        directory_results = {}
        missing_directories = []
        
        for dir_name in self.required_directories:
            dir_path = self.data_dir / dir_name
            
            if dir_path.exists() and dir_path.is_dir():
                # Count files in directory
                file_count = len(list(dir_path.glob('*')))
                directory_results[dir_name] = {
                    'status': 'PASS',
                    'path': str(dir_path),
                    'file_count': file_count
                }
                print(f"  ✅ {dir_name}: {file_count} files")
            else:
                directory_results[dir_name] = {
                    'status': 'FAIL',
                    'path': str(dir_path),
                    'error': 'Directory not found'
                }
                missing_directories.append(dir_name)
                print(f"  ❌ {dir_name}: Directory not found")
        
        result = {
            'total_directories': len(self.required_directories),
            'existing_directories': len(self.required_directories) - len(missing_directories),
            'missing_directories': missing_directories,
            'directory_results': directory_results,
            'status': 'PASS' if len(missing_directories) == 0 else 'FAIL'
        }
        
        print(f"  📊 Data Directories: {result['status']}")
        print(f"     Existing: {result['existing_directories']}/{result['total_directories']}")
        print(f"     Missing: {len(missing_directories)}")
        
        return result
    
    def validate_required_files(self) -> Dict[str, Any]:
        """Validate that critical data files exist."""
        print("🔍 Validating required data files...")
        
        # Critical files that should exist
        critical_files = [
            'data/market_data/spot_prices/btc_usd/binance_BTCUSDT_1h_2024-01-01_2025-09-30.csv',
            'data/market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv',
            'data/market_data/derivatives/funding_rates/binance_BTCUSDT_funding_rates_2024-01-01_2025-09-30.csv',
            'data/market_data/derivatives/futures_ohlcv/binance_BTCUSDT_perp_1h_2024-01-01_2025-09-30.csv',
            'data/protocol_data/aave/rates/aave_v3_aave-v3-ethereum_USDT_rates_2024-01-01_2025-09-18_hourly.csv'
        ]
        
        file_results = {}
        missing_files = []
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            
            if full_path.exists() and full_path.is_file():
                file_size = full_path.stat().st_size
                file_results[file_path] = {
                    'status': 'PASS',
                    'size_bytes': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2)
                }
                print(f"  ✅ {file_path}: {file_results[file_path]['size_mb']} MB")
            else:
                file_results[file_path] = {
                    'status': 'FAIL',
                    'error': 'File not found'
                }
                missing_files.append(file_path)
                print(f"  ❌ {file_path}: File not found")
        
        result = {
            'total_files': len(critical_files),
            'existing_files': len(critical_files) - len(missing_files),
            'missing_files': missing_files,
            'file_results': file_results,
            'status': 'PASS' if len(missing_files) == 0 else 'FAIL'
        }
        
        print(f"  📊 Required Files: {result['status']}")
        print(f"     Existing: {result['existing_files']}/{result['total_files']}")
        print(f"     Missing: {len(missing_files)}")
        
        return result
    
    def validate_file_accessibility(self) -> Dict[str, Any]:
        """Validate that data files are readable."""
        print("🔍 Validating file accessibility...")
        
        # Test reading a few key files
        test_files = [
            'data/market_data/spot_prices/btc_usd/binance_BTCUSDT_1h_2024-01-01_2025-09-30.csv',
            'data/market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv'
        ]
        
        accessibility_results = {}
        inaccessible_files = []
        
        for file_path in test_files:
            full_path = self.project_root / file_path
            
            try:
                if full_path.exists():
                    with open(full_path, 'r') as f:
                        # Read first few lines to test accessibility
                        lines = [f.readline() for _ in range(3)]
                        line_count = len([line for line in lines if line.strip()])
                    
                    accessibility_results[file_path] = {
                        'status': 'PASS',
                        'readable': True,
                        'sample_lines': line_count
                    }
                    print(f"  ✅ {file_path}: Readable ({line_count} sample lines)")
                else:
                    accessibility_results[file_path] = {
                        'status': 'SKIP',
                        'readable': False,
                        'error': 'File not found'
                    }
                    print(f"  ⚠️  {file_path}: File not found (skipped)")
            except Exception as e:
                accessibility_results[file_path] = {
                    'status': 'FAIL',
                    'readable': False,
                    'error': str(e)
                }
                inaccessible_files.append(file_path)
                print(f"  ❌ {file_path}: Not accessible - {e}")
        
        result = {
            'total_test_files': len(test_files),
            'accessible_files': len([r for r in accessibility_results.values() if r['status'] == 'PASS']),
            'inaccessible_files': inaccessible_files,
            'accessibility_results': accessibility_results,
            'status': 'PASS' if len(inaccessible_files) == 0 else 'FAIL'
        }
        
        print(f"  📊 File Accessibility: {result['status']}")
        print(f"     Accessible: {result['accessible_files']}/{result['total_test_files']}")
        print(f"     Inaccessible: {len(inaccessible_files)}")
        
        return result
    
    def run_validation(self) -> bool:
        """Run complete data files validation."""
        print("\n" + "="*80)
        print("🔍 DATA FILES QUALITY GATES")
        print("="*80)
        
        # Run all validations
        directories = self.validate_data_directories()
        required_files = self.validate_required_files()
        accessibility = self.validate_file_accessibility()
        
        # Store results
        self.results['data_directories'] = directories
        self.results['required_files'] = required_files
        self.results['file_accessibility'] = accessibility
        
        # Determine overall status
        all_passed = (
            directories['status'] == 'PASS' and
            required_files['status'] == 'PASS' and
            accessibility['status'] == 'PASS'
        )
        
        self.results['overall_status'] = 'PASS' if all_passed else 'FAIL'
        
        # Print summary
        print(f"\n📊 DATA FILES SUMMARY:")
        print(f"  Data Directories: {directories['status']} ({directories['existing_directories']}/{directories['total_directories']})")
        print(f"  Required Files: {required_files['status']} ({required_files['existing_files']}/{required_files['total_files']})")
        print(f"  File Accessibility: {accessibility['status']} ({accessibility['accessible_files']}/{accessibility['total_test_files']})")
        
        if all_passed:
            print(f"\n🎉 SUCCESS: All data files quality gates passed!")
            return True
        else:
            print(f"\n❌ FAILURE: Data files quality gates failed!")
            return False


def main():
    """Main function."""
    validator = DataFilesQualityGates()
    success = validator.run_validation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
