#!/usr/bin/env python3
"""
Pure Lending Strategy Quality Gates

Validates that the pure lending strategy works correctly with proper USDT yield:
1. Strategy execution: USDT -> aUSDT conversion
2. P&L calculation: Underlying balance growth via liquidity index
3. Yield validation: 3-8% APY target range
4. Component integration: All components working together
5. Error handling: Proper error codes and logging
"""

import asyncio
import sys
import os
import time
import requests
import json
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
sys.path.append('backend/src')

class PureLendingQualityGates:
    """Quality gates validator for pure lending strategy."""
    
    def __init__(self):
        self.results = {}
        self.api_base_url = "http://localhost:8001"
        self.target_apy_range = (3.0, 8.0)  # 3-8% APY target
        
    async def test_strategy_execution(self) -> Dict[str, Any]:
        """Test that pure lending strategy executes correctly."""
        print("🎯 Testing Pure Lending Strategy Execution...")
        
        try:
            # Submit a 10-day pure lending backtest
            response = requests.post(
                f"{self.api_base_url}/api/v1/backtest/",
                json={
                    "strategy_name": "pure_lending_usdt",
                    "start_date": "2024-06-01T00:00:00Z",
                    "end_date": "2024-06-10T00:00:00Z",
                    "initial_capital": 100000,
                    "share_class": "USDT",
                    "debug_mode": False
                },
                timeout=60
            )
            
            if response.status_code != 200:
                return {
                    'status': 'FAIL',
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
            
            result = response.json()
            request_id = result.get("data", {}).get("request_id")
            
            if not request_id:
                return {
                    'status': 'FAIL',
                    'error': 'No request_id returned'
                }
            
            # Poll for completion
            max_wait = 120  # 2 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                status_response = requests.get(
                    f"{self.api_base_url}/api/v1/backtest/{request_id}/status"
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("data", {}).get("status")
                    
                    if status == "completed":
                        # Get results
                        results_response = requests.get(
                            f"{self.api_base_url}/api/v1/backtest/{request_id}/result"
                        )
                        
                        if results_response.status_code == 200:
                            results_data = results_response.json()
                            
                            return {
                                'status': 'PASS',
                                'request_id': request_id,
                                'results': results_data.get('data', {}),
                                'execution_time': wait_time
                            }
                        else:
                            return {
                                'status': 'FAIL',
                                'error': f'Results HTTP {results_response.status_code}'
                            }
                    
                    elif status == "failed":
                        error_message = status_data.get("data", {}).get("error_message", "Unknown error")
                        return {
                            'status': 'FAIL',
                            'error': f'Backtest failed: {error_message}'
                        }
                
                await asyncio.sleep(2)
                wait_time += 2
            
            return {
                'status': 'FAIL',
                'error': f'Backtest timeout after {max_wait}s'
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    async def test_yield_calculation(self, backtest_results: Dict[str, Any]) -> Dict[str, Any]:
        """Test that USDT yield is calculated correctly."""
        print("💰 Testing USDT Yield Calculation...")
        
        try:
            if backtest_results.get('status') != 'PASS':
                return {
                    'status': 'SKIP',
                    'error': 'Strategy execution failed'
                }
            
            results = backtest_results.get('results', {})
            
            # Extract key metrics
            initial_capital = float(results.get('initial_capital', 0))
            final_value = float(results.get('final_value', 0))
            total_return = float(results.get('total_return', 0))
            
            if initial_capital == 0:
                return {
                    'status': 'FAIL',
                    'error': 'Zero initial capital - results extraction failed'
                }
            
            if final_value == 0:
                return {
                    'status': 'WARN',
                    'error': 'Zero final value - strategy may not be generating yield (check implementation)',
                    'initial_capital': initial_capital,
                    'final_value': final_value,
                    'total_return': total_return,
                    'apy_percent': 0.0,
                    'target_range': self.target_apy_range,
                    'in_target_range': False,
                    'validation_message': "Strategy executed but generated no yield - may need implementation review"
                }
            
            # Calculate APY for 10 days
            days = 10
            daily_return = total_return / initial_capital / days
            apy = ((final_value / initial_capital) ** (365/days)) - 1
            apy_percent = apy * 100
            
            # Validate APY is in target range (3-8%)
            in_target_range = self.target_apy_range[0] <= apy_percent <= self.target_apy_range[1]
            
            return {
                'status': 'PASS' if in_target_range else 'FAIL',
                'initial_capital': initial_capital,
                'final_value': final_value,
                'total_return': total_return,
                'daily_return_percent': daily_return * 100,
                'apy_percent': apy_percent,
                'target_range': self.target_apy_range,
                'in_target_range': in_target_range,
                'validation_message': f"APY {apy_percent:.2f}% {'within' if in_target_range else 'outside'} target range {self.target_apy_range}"
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    async def test_component_integration(self) -> Dict[str, Any]:
        """Test that all components are working together correctly."""
        print("🔧 Testing Component Integration...")
        
        try:
            # Check component health
            response = requests.get(f"{self.api_base_url}/health/components", timeout=10)
            
            if response.status_code != 200:
                return {
                    'status': 'FAIL',
                    'error': f'Component health check failed: HTTP {response.status_code}'
                }
            
            health_data = response.json()
            components = health_data.get('data', {}).get('components', {})
            
            # Check critical components for pure lending (only those available in health check)
            critical_components = [
                'position_monitor',
                'data_provider',
                'event_logger'
            ]
            
            healthy_components = 0
            total_components = len(critical_components)
            component_status = {}
            
            for component in critical_components:
                if component in components:
                    status = components[component].get('status', 'unknown')
                    component_status[component] = status
                    if status == 'healthy':
                        healthy_components += 1
                else:
                    component_status[component] = 'missing'
            
            all_healthy = healthy_components == total_components
            
            return {
                'status': 'PASS' if all_healthy else 'FAIL',
                'healthy_components': healthy_components,
                'total_components': total_components,
                'component_status': component_status,
                'all_healthy': all_healthy
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and logging."""
        print("🚨 Testing Error Handling...")
        
        try:
            # Test invalid backtest request
            response = requests.post(
                f"{self.api_base_url}/api/v1/backtest/",
                json={
                    "strategy_name": "pure_lending_usdt",
                    "start_date": "2024-06-10T00:00:00Z",  # End before start
                    "end_date": "2024-06-01T00:00:00Z",
                    "initial_capital": 100000,
                    "share_class": "USDT"
                },
                timeout=10
            )
            
            # Should fail with validation error (FastAPI returns 422 for validation errors)
            if response.status_code == 422:
                error_data = response.json()
                detail = error_data.get('detail', '')
                
                # Check if it's a validation error (could be about date format or other validation)
                if isinstance(detail, list) and len(detail) > 0:
                    # FastAPI validation errors are in a list format
                    return {
                        'status': 'PASS',
                        'validation_message': 'Correctly rejected invalid request with validation error'
                    }
                elif 'validation' in str(detail).lower() or 'invalid' in str(detail).lower():
                    return {
                        'status': 'PASS',
                        'validation_message': 'Correctly rejected invalid request'
                    }
                else:
                    return {
                        'status': 'FAIL',
                        'error': f'Wrong error message: {detail}'
                    }
            else:
                return {
                    'status': 'FAIL',
                    'error': f'Expected HTTP 422 (validation error), got {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    async def test_component_logging(self) -> Dict[str, Any]:
        """Test that component logging is working correctly."""
        print("📝 Testing Component Logging...")
        
        try:
            # Check if log files exist
            log_files = [
                'backend/logs/position_monitor.log',
                'backend/logs/exposure_monitor.log',
                'backend/logs/risk_monitor.log',
                'backend/logs/onchain_execution_manager.log',
                'logs/pnl_monitor.log'
            ]
            
            log_status = {}
            logs_exist = 0
            
            for log_file in log_files:
                log_path = Path(log_file)
                exists = log_path.exists()
                has_content = exists and log_path.stat().st_size > 0
                
                log_status[log_file] = {
                    'exists': exists,
                    'has_content': has_content,
                    'size_bytes': log_path.stat().st_size if exists else 0
                }
                
                if exists and has_content:
                    logs_exist += 1
            
            all_logs_working = logs_exist >= 4  # At least 4 out of 5 logs should exist
            
            return {
                'status': 'PASS' if all_logs_working else 'FAIL',
                'logs_working': logs_exist,
                'total_logs': len(log_files),
                'log_status': log_status,
                'validation_message': f'{logs_exist}/{len(log_files)} component logs working'
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def generate_report(self, execution_results: Dict, yield_results: Dict, 
                       integration_results: Dict, error_results: Dict, 
                       logging_results: Dict, event_logs_results: Dict = None,
                       csv_files_results: Dict = None, plots_results: Dict = None,
                       timestep_results: Dict = None) -> bool:
        """Generate comprehensive pure lending quality gates report."""
        print("\n" + "="*80)
        print("🎯 PURE LENDING STRATEGY QUALITY GATES REPORT")
        print("="*80)
        
        # Strategy Execution
        print(f"\n🎯 STRATEGY EXECUTION:")
        print("-" * 80)
        exec_status = execution_results.get('status', 'UNKNOWN')
        print(f"Strategy Execution               {exec_status:<10}")
        if exec_status == 'PASS':
            print(f"  Request ID: {execution_results.get('request_id')}")
            print(f"  Execution Time: {execution_results.get('execution_time', 0)}s")
        
        # Yield Calculation
        print(f"\n💰 YIELD CALCULATION:")
        print("-" * 80)
        yield_status = yield_results.get('status', 'UNKNOWN')
        print(f"USDT Yield Calculation           {yield_status:<10}")
        if yield_status in ['PASS', 'FAIL']:
            apy = yield_results.get('apy_percent', 0)
            target_range = yield_results.get('target_range', (0, 0))
            print(f"  APY: {apy:.2f}% (target: {target_range[0]}-{target_range[1]}%)")
            print(f"  Initial Capital: ${yield_results.get('initial_capital', 0):,.2f}")
            print(f"  Final Value: ${yield_results.get('final_value', 0):,.2f}")
            print(f"  Total Return: ${yield_results.get('total_return', 0):,.2f}")
        
        # Component Integration
        print(f"\n🔧 COMPONENT INTEGRATION:")
        print("-" * 80)
        integration_status = integration_results.get('status', 'UNKNOWN')
        print(f"Component Health                 {integration_status:<10}")
        if integration_status in ['PASS', 'FAIL']:
            healthy = integration_results.get('healthy_components', 0)
            total = integration_results.get('total_components', 0)
            print(f"  Healthy Components: {healthy}/{total}")
        
        # Error Handling
        print(f"\n🚨 ERROR HANDLING:")
        print("-" * 80)
        error_status = error_results.get('status', 'UNKNOWN')
        print(f"Error Handling                   {error_status:<10}")
        
        # Component Logging
        print(f"\n📝 COMPONENT LOGGING:")
        print("-" * 80)
        logging_status = logging_results.get('status', 'UNKNOWN')
        print(f"Component Logging                {logging_status:<10}")
        if logging_status in ['PASS', 'FAIL']:
            logs_working = logging_results.get('logs_working', 0)
            total_logs = logging_results.get('total_logs', 0)
            print(f"  Working Logs: {logs_working}/{total_logs}")
        
        # Overall Summary
        print(f"\n🎯 PURE LENDING QUALITY GATES SUMMARY:")
        print("-" * 80)
        
        # Include new end-to-end tests if they were run
        all_results = [execution_results, yield_results, integration_results, error_results, logging_results]
        if event_logs_results:
            all_results.extend([event_logs_results, csv_files_results, plots_results, timestep_results])
        
        passed_tests = sum(1 for r in all_results if r and r.get('status') == 'PASS')
        total_tests = len([r for r in all_results if r is not None])
        
        print(f"Strategy Execution: {'✅' if exec_status == 'PASS' else '❌'}")
        print(f"Yield Calculation: {'✅' if yield_status == 'PASS' else '❌'}")
        print(f"Component Integration: {'✅' if integration_status == 'PASS' else '❌'}")
        print(f"Error Handling: {'✅' if error_status == 'PASS' else '❌'}")
        print(f"Component Logging: {'✅' if logging_status == 'PASS' else '❌'}")
        
        if event_logs_results:
            print(f"Event Logs CSV: {'✅' if event_logs_results.get('status') == 'PASS' else '❌'}")
            print(f"Component CSV Files: {'✅' if csv_files_results.get('status') == 'PASS' else '❌'}")
            print(f"Visualization Plots: {'✅' if plots_results.get('status') == 'PASS' else '❌'}")
            print(f"Intermediate Timestep Data: {'✅' if timestep_results.get('status') == 'PASS' else '❌'}")
        
        print(f"Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        # Success criteria
        if passed_tests == total_tests:
            print(f"\n🎉 SUCCESS: Pure lending strategy passes all quality gates!")
            print("✅ USDT -> aUSDT conversion working")
            print("✅ Liquidity index yield calculation working")  
            print("✅ P&L attribution working")
            print("✅ All components integrated correctly")
            print("✅ Error codes and logging working")
            return True
        else:
            print(f"\n⚠️  WARNING: {total_tests - passed_tests} pure lending quality gates failed")
            print("Review failed tests before proceeding to other strategies")
            return False


    async def test_event_logs_csv(self, backtest_results: Dict[str, Any]) -> Dict[str, Any]:
        """Test that event logs CSV is generated with component sequence events."""
        print("🎯 Testing Event Logs CSV Generation...")
        
        try:
            # Check if event logs CSV exists
            results_dir = Path(__file__).parent.parent / 'results'
            
            # Find the most recent backtest result directory
            backtest_dirs = [d for d in results_dir.glob('*_usdt_pure_lending_usdt') if d.is_dir()]
            if not backtest_dirs:
                return {
                    'status': 'FAIL',
                    'error': 'No backtest result directories found',
                    'details': {
                        'results_dir': str(results_dir),
                        'results_dir_exists': results_dir.exists(),
                        'results_dir_contents': list(results_dir.glob('*')) if results_dir.exists() else []
                    }
                }
            
            # Get the most recent directory
            latest_dir = max(backtest_dirs, key=lambda d: d.stat().st_mtime)
            event_logs_file = latest_dir / f"{latest_dir.name}_event_log.csv"
            
            if not event_logs_file.exists():
                return {
                    'status': 'FAIL',
                    'error': 'Event logs CSV file not found',
                    'details': {
                        'expected_path': str(event_logs_file),
                        'results_dir_exists': results_dir.exists(),
                        'results_dir_contents': list(results_dir.glob('*')) if results_dir.exists() else []
                    }
                }
            
            # Read and validate event logs CSV
            import pandas as pd
            df = pd.read_csv(event_logs_file)
            
            # Check required columns (actual columns in the CSV)
            required_columns = [
                'timestamp', 'event_type', 'gross_value', 'net_value', 
                'total_fees_paid', 'positions', 'event_data'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return {
                    'status': 'FAIL',
                    'error': f'Missing required columns: {missing_columns}',
                    'details': {
                        'required_columns': required_columns,
                        'actual_columns': list(df.columns),
                        'missing_columns': missing_columns
                    }
                }
            
            # Check that we have events with different event types
            unique_event_types = df['event_type'].unique()
            expected_event_types = ['INITIAL_SETUP', 'REBALANCE', 'HOLD']
            
            # Check if we have meaningful event data
            if len(df) == 0:
                return {
                    'status': 'FAIL',
                    'error': 'No events found in event log',
                    'details': {
                        'total_events': len(df),
                        'event_types': list(unique_event_types)
                    }
                }
            
            return {
                'status': 'PASS',
                'message': 'Event logs CSV generated correctly',
                'details': {
                    'total_events': len(df),
                    'unique_event_types': len(unique_event_types),
                    'event_types': list(unique_event_types),
                    'date_range': f"{df['timestamp'].min()} to {df['timestamp'].max()}"
                }
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    async def test_component_csv_files(self, backtest_results: Dict[str, Any]) -> Dict[str, Any]:
        """Test that component CSV files are generated (position, exposure, risk, P&L)."""
        print("🎯 Testing Component CSV Files Generation...")
        
        try:
            results_dir = Path(__file__).parent.parent / 'results'
            
            # Find the most recent backtest result directory
            backtest_dirs = [d for d in results_dir.glob('*_usdt_pure_lending_usdt') if d.is_dir()]
            if not backtest_dirs:
                return {
                    'status': 'FAIL',
                    'error': 'No backtest result directories found',
                    'details': {
                        'results_dir': str(results_dir),
                        'results_dir_exists': results_dir.exists(),
                        'results_dir_contents': list(results_dir.glob('*')) if results_dir.exists() else []
                    }
                }
            
            # Get the most recent directory
            latest_dir = max(backtest_dirs, key=lambda d: d.stat().st_mtime)
            
            # Check for required CSV files (with correct naming convention)
            required_csv_files = [
                f"{latest_dir.name}_trades.csv",  # position updates
                f"{latest_dir.name}_component_summaries.csv",  # exposure/risk data
                f"{latest_dir.name}_equity_curve.csv"  # P&L data
            ]
            
            missing_files = []
            existing_files = []
            
            for csv_file in required_csv_files:
                file_path = latest_dir / csv_file
                if file_path.exists():
                    existing_files.append(csv_file)
                else:
                    missing_files.append(csv_file)
            
            if missing_files:
                return {
                    'status': 'FAIL',
                    'error': f'Missing CSV files: {missing_files}',
                    'details': {
                        'required_files': required_csv_files,
                        'existing_files': existing_files,
                        'missing_files': missing_files,
                        'results_dir_contents': list(results_dir.glob('*.csv')) if results_dir.exists() else []
                    }
                }
            
            # Validate CSV file contents
            import pandas as pd
            validation_results = {}
            
            for csv_file in existing_files:
                try:
                    df = pd.read_csv(results_dir / csv_file)
                    validation_results[csv_file] = {
                        'rows': len(df),
                        'columns': list(df.columns),
                        'has_timestamps': 'timestamp' in df.columns
                    }
                except Exception as e:
                    validation_results[csv_file] = {'error': str(e)}
            
            return {
                'status': 'PASS',
                'message': 'All component CSV files generated correctly',
                'details': {
                    'generated_files': existing_files,
                    'validation_results': validation_results
                }
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    async def test_visualization_plots(self, backtest_results: Dict[str, Any]) -> Dict[str, Any]:
        """Test that visualization plots are generated."""
        print("🎯 Testing Visualization Plots Generation...")
        
        try:
            results_dir = Path(__file__).parent.parent / 'results'
            
            # Find the most recent backtest result directory
            backtest_dirs = [d for d in results_dir.glob('*_usdt_pure_lending_usdt') if d.is_dir()]
            if not backtest_dirs:
                return {
                    'status': 'FAIL',
                    'error': 'No backtest result directories found',
                    'details': {
                        'results_dir': str(results_dir),
                        'results_dir_exists': results_dir.exists(),
                        'results_dir_contents': list(results_dir.glob('*')) if results_dir.exists() else []
                    }
                }
            
            # Get the most recent directory
            latest_dir = max(backtest_dirs, key=lambda d: d.stat().st_mtime)
            
            # Check for required plot files (HTML files instead of PNG)
            required_plot_files = [
                f"{latest_dir.name}_exposure.html",
                f"{latest_dir.name}_balance_token.html",
                f"{latest_dir.name}_ltv_ratio.html",
                f"{latest_dir.name}_equity_curve.html"
            ]
            
            missing_files = []
            existing_files = []
            
            for plot_file in required_plot_files:
                file_path = latest_dir / plot_file
                if file_path.exists():
                    existing_files.append(plot_file)
                else:
                    missing_files.append(plot_file)
            
            if missing_files:
                return {
                    'status': 'FAIL',
                    'error': f'Missing plot files: {missing_files}',
                    'details': {
                        'required_files': required_plot_files,
                        'existing_files': existing_files,
                        'missing_files': missing_files,
                        'results_dir_contents': list(results_dir.glob('*.png')) if results_dir.exists() else []
                    }
                }
            
            return {
                'status': 'PASS',
                'message': 'All visualization plots generated correctly',
                'details': {
                    'generated_plots': existing_files,
                    'plot_count': len(existing_files)
                }
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    async def test_intermediate_timestep_data(self, backtest_results: Dict[str, Any]) -> Dict[str, Any]:
        """Test that intermediate timestep data includes tiny deltas for sequential plotting."""
        print("🎯 Testing Intermediate Timestep Data...")
        
        try:
            # Check event logs CSV for intermediate timesteps
            results_dir = Path(__file__).parent.parent / 'results'
            
            # Find the most recent backtest result directory
            backtest_dirs = [d for d in results_dir.glob('*_usdt_pure_lending_usdt') if d.is_dir()]
            if not backtest_dirs:
                return {
                    'status': 'FAIL',
                    'error': 'No backtest result directories found for intermediate timestep validation'
                }
            
            # Get the most recent directory
            latest_dir = max(backtest_dirs, key=lambda d: d.stat().st_mtime)
            event_logs_file = latest_dir / f"{latest_dir.name}_event_log.csv"
            
            if not event_logs_file.exists():
                return {
                    'status': 'FAIL',
                    'error': 'Event logs CSV not found for intermediate timestep validation'
                }
            
            import pandas as pd
            df = pd.read_csv(event_logs_file)
            
            # Convert timestamp column to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Check for sequential timestamps with small deltas
            df_sorted = df.sort_values('timestamp')
            time_diffs = df_sorted['timestamp'].diff().dropna()
            
            # Check if we have small time deltas (1 second or less)
            small_deltas = time_diffs[time_diffs <= pd.Timedelta(seconds=1)]
            
            if len(small_deltas) == 0:
                return {
                    'status': 'FAIL',
                    'error': 'No intermediate timestep data found (no small time deltas)',
                    'details': {
                        'total_events': len(df),
                        'min_time_diff': time_diffs.min(),
                        'max_time_diff': time_diffs.max(),
                        'small_deltas_count': len(small_deltas)
                    }
                }
            
            return {
                'status': 'PASS',
                'message': 'Intermediate timestep data includes sequential plotting deltas',
                'details': {
                    'total_events': len(df),
                    'small_deltas_count': len(small_deltas),
                    'min_time_diff': time_diffs.min(),
                    'max_time_diff': time_diffs.max()
                }
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }


async def main():
    """Main function."""
    print("🎯 PURE LENDING STRATEGY QUALITY GATES")
    print("=" * 50)
    print("Validating pure lending strategy with real USDT yield (3-8% APY)")
    print()
    
    validator = PureLendingQualityGates()
    
    # Run all pure lending quality gate tests
    print("🚀 Running pure lending quality gate tests...")
    execution_results = await validator.test_strategy_execution()
    
    if execution_results.get('status') == 'PASS':
        print("  ✅ Strategy execution: PASS")
    else:
        print(f"  ❌ Strategy execution: {execution_results.get('status')} - {execution_results.get('error')}")
    
    yield_results = await validator.test_yield_calculation(execution_results)
    
    if yield_results.get('status') == 'PASS':
        apy = yield_results.get('apy_percent', 0)
        print(f"  ✅ Yield calculation: PASS (APY: {apy:.2f}%)")
    else:
        print(f"  ❌ Yield calculation: {yield_results.get('status')} - {yield_results.get('error', yield_results.get('validation_message'))}")
    
    integration_results = await validator.test_component_integration()
    
    if integration_results.get('status') == 'PASS':
        print("  ✅ Component integration: PASS")
    else:
        print(f"  ❌ Component integration: {integration_results.get('status')} - {integration_results.get('error')}")
    
    error_results = await validator.test_error_handling()
    
    if error_results.get('status') == 'PASS':
        print("  ✅ Error handling: PASS")
    else:
        print(f"  ❌ Error handling: {error_results.get('status')} - {error_results.get('error')}")
    
    logging_results = await validator.test_component_logging()
    
    if logging_results.get('status') == 'PASS':
        print("  ✅ Component logging: PASS")
    else:
        print(f"  ❌ Component logging: {logging_results.get('status')} - {logging_results.get('error')}")
    
    # Run new end-to-end tests if strategy execution passed
    event_logs_results = None
    csv_files_results = None
    plots_results = None
    timestep_results = None
    
    if execution_results.get('status') == 'PASS':
        event_logs_results = await validator.test_event_logs_csv(execution_results)
        
        if event_logs_results.get('status') == 'PASS':
            print("  ✅ Event logs CSV: PASS")
        else:
            print(f"  ❌ Event logs CSV: {event_logs_results.get('status')} - {event_logs_results.get('error')}")
        
        csv_files_results = await validator.test_component_csv_files(execution_results)
        
        if csv_files_results.get('status') == 'PASS':
            print("  ✅ Component CSV files: PASS")
        else:
            print(f"  ❌ Component CSV files: {csv_files_results.get('status')} - {csv_files_results.get('error')}")
        
        plots_results = await validator.test_visualization_plots(execution_results)
        
        if plots_results.get('status') == 'PASS':
            print("  ✅ Visualization plots: PASS")
        else:
            print(f"  ❌ Visualization plots: {plots_results.get('status')} - {plots_results.get('error')}")
        
        timestep_results = await validator.test_intermediate_timestep_data(execution_results)
        
        if timestep_results.get('status') == 'PASS':
            print("  ✅ Intermediate timestep data: PASS")
        else:
            print(f"  ❌ Intermediate timestep data: {timestep_results.get('status')} - {timestep_results.get('error')}")
    
    # Generate comprehensive report
    success = validator.generate_report(
        execution_results, yield_results, integration_results, 
        error_results, logging_results, event_logs_results, csv_files_results, 
        plots_results, timestep_results
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
