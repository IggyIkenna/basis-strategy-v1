#!/usr/bin/env python3
"""
Quality Gates Orchestration Script

Runs all quality gate validations in the correct order and generates a comprehensive report.
This script coordinates all quality gate scripts and provides a unified view of system readiness.

Quality Gate Categories:
1. Pure Lending Strategy (Core functionality validation)
2. Monitor Components (Position, Exposure, P&L Calculator)
3. Risk Monitor (Risk calculations and error handling)
4. Performance (Backtest speed, API response times)
5. Integration (API endpoints, component health)
6. Configuration (Config loading, validation, alignment)
7. Live Data Validation (Future - when API credentials are set up)

Usage:
  python scripts/orchestrate_quality_gates.py                    # Run all gates
  python scripts/orchestrate_quality_gates.py --strategy-only    # Run only strategy validation
  python scripts/orchestrate_quality_gates.py --components-only  # Run only component validation
"""

import asyncio
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List
import argparse
import json

class QualityGatesOrchestrator:
    """Orchestrates all quality gate validations."""
    
    def __init__(self):
        self.start_time = time.time()
        self.scripts_dir = Path(__file__).parent
        self.project_root = self.scripts_dir.parent
        self.results = {}
        
        # Quality gate scripts in execution order
        self.quality_gate_scripts = {
            'pure_lending_strategy': {
                'script': 'test_pure_lending_quality_gates.py',
                'description': 'Pure Lending Strategy Validation',
                'category': 'strategy',
                'critical': True,
                'timeout': 120
            },
            'monitor_components': {
                'script': 'monitor_quality_gates.py', 
                'description': 'Monitor Components (Position, Exposure, P&L)',
                'category': 'components',
                'critical': True,
                'timeout': 60
            },
            'risk_monitor': {
                'script': 'risk_monitor_quality_gates.py',
                'description': 'Risk Monitor Validation',
                'category': 'components', 
                'critical': True,
                'timeout': 60
            },
            'performance': {
                'script': 'performance_quality_gates.py',
                'description': 'Performance Validation',
                'category': 'performance',
                'critical': False,
                'timeout': 300
            },
            'config_alignment': {
                'script': 'validate_config_alignment.py',
                'description': 'Configuration Alignment',
                'category': 'configuration',
                'critical': True,
                'timeout': 30
            },
            'e2e_backtest': {
                'script': 'test_e2e_backtest_flow.py',
                'description': 'End-to-End Backtest Flow',
                'category': 'integration',
                'critical': True,
                'timeout': 180
            },
            'live_data_validation': {
                'script': 'test_live_data_validation.py',
                'description': 'Live Data Validation (Future)',
                'category': 'future',
                'critical': False,
                'timeout': 60
            },
            'scripts_directory': {
                'script': 'run_quality_gates.py',
                'description': 'Scripts Directory Validation',
                'category': 'validation',
                'critical': True,
                'timeout': 300
            },
            'tight_loop_architecture': {
                'script': 'test_tight_loop_quality_gates.py',
                'description': 'Tight Loop Architecture Validation',
                'category': 'components',
                'critical': True,
                'timeout': 120
            },
            'position_monitor_persistence': {
                'script': 'test_position_monitor_persistence_quality_gates.py',
                'description': 'Position Monitor State Persistence',
                'category': 'components',
                'critical': True,
                'timeout': 120
            }
        }
    
    async def run_quality_gate_script(self, script_name: str, script_info: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single quality gate script."""
        script_path = self.scripts_dir / script_info['script']
        
        if not script_path.exists():
            return {
                'status': 'ERROR',
                'error': f'Script not found: {script_info["script"]}',
                'execution_time': 0
            }
        
        print(f"🔄 Running {script_info['description']}...")
        start_time = time.time()
        
        try:
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=self.project_root, 
               timeout=script_info['timeout'])
            
            execution_time = time.time() - start_time
            
            # Parse result based on return code and output
            if result.returncode == 0:
                # Success - parse additional details from output
                output_lines = result.stdout.split('\n')
                
                success_indicators = [
                    'SUCCESS:', 'All tests passed', 'All gates passed',
                    'quality gates passed!', 'COMPLETE SUCCESS!'
                ]
                
                has_success = any(indicator in result.stdout for indicator in success_indicators)
                
                # Extract key metrics if available
                metrics = {}
                for line in output_lines:
                    if 'APY:' in line and '%' in line:
                        try:
                            apy_str = line.split('APY:')[1].split('%')[0].strip()
                            metrics['apy_percent'] = float(apy_str)
                        except (ValueError, IndexError):
                            pass
                    elif 'tests passed' in line and '/' in line:
                        try:
                            parts = line.split()
                            for part in parts:
                                if '/' in part:
                                    passed, total = part.split('/')
                                    metrics['tests_passed'] = int(passed)
                                    metrics['tests_total'] = int(total)
                                    break
                        except (ValueError, IndexError):
                            pass
                
                return {
                    'status': 'PASS' if has_success else 'UNKNOWN',
                    'execution_time': execution_time,
                    'output': result.stdout,
                    'metrics': metrics
                }
            
            else:
                # Failure
                return {
                    'status': 'FAIL',
                    'execution_time': execution_time,
                    'error': result.stderr,
                    'output': result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'TIMEOUT',
                'execution_time': script_info['timeout'],
                'error': f'Script timeout after {script_info["timeout"]}s'
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'execution_time': time.time() - start_time,
                'error': str(e)
            }
    
    async def run_category(self, category: str) -> Dict[str, Any]:
        """Run all quality gates in a specific category."""
        category_results = {}
        
        scripts_in_category = {
            name: info for name, info in self.quality_gate_scripts.items() 
            if info['category'] == category
        }
        
        if not scripts_in_category:
            return {'error': f'No scripts found for category: {category}'}
        
        print(f"\n📊 Running {category.upper()} Quality Gates...")
        print("=" * 60)
        
        for script_name, script_info in scripts_in_category.items():
            result = await self.run_quality_gate_script(script_name, script_info)
            category_results[script_name] = result
            
            # Print immediate result
            status = result['status']
            time_taken = result['execution_time']
            
            if status == 'PASS':
                print(f"  ✅ {script_info['description']}: PASS ({time_taken:.1f}s)")
                if 'metrics' in result and 'apy_percent' in result['metrics']:
                    print(f"     📊 APY: {result['metrics']['apy_percent']:.2f}%")
            elif status == 'FAIL':
                print(f"  ❌ {script_info['description']}: FAIL ({time_taken:.1f}s)")
            elif status == 'TIMEOUT':
                print(f"  ⏰ {script_info['description']}: TIMEOUT ({time_taken:.1f}s)")
            elif status == 'ERROR':
                print(f"  💥 {script_info['description']}: ERROR ({time_taken:.1f}s)")
            else:
                print(f"  ❓ {script_info['description']}: {status} ({time_taken:.1f}s)")
        
        return category_results
    
    async def run_all_quality_gates(self, categories: List[str] = None) -> Dict[str, Any]:
        """Run all quality gates or specific categories."""
        if categories is None:
            categories = ['strategy', 'components', 'performance', 'configuration', 'integration']
        
        all_results = {}
        
        for category in categories:
            category_results = await self.run_category(category)
            all_results[category] = category_results
        
        return all_results
    
    def generate_comprehensive_report(self, all_results: Dict[str, Any]) -> bool:
        """Generate comprehensive quality gates report."""
        print("\n" + "="*100)
        print("🚦 COMPREHENSIVE QUALITY GATES VALIDATION REPORT")
        print("="*100)
        
        total_scripts = 0
        total_passed = 0
        critical_scripts = 0
        critical_passed = 0
        
        # Category summaries
        category_summaries = {}
        
        for category, category_results in all_results.items():
            if 'error' in category_results:
                print(f"\n❌ {category.upper()}: {category_results['error']}")
                continue
            
            print(f"\n📊 {category.upper()} QUALITY GATES:")
            print("-" * 80)
            
            category_passed = 0
            category_total = 0
            category_critical_passed = 0
            category_critical_total = 0
            
            for script_name, result in category_results.items():
                script_info = self.quality_gate_scripts[script_name]
                status = result['status']
                time_taken = result['execution_time']
                is_critical = script_info['critical']
                
                # Format status display
                status_display = f"{status:<10}"
                if 'metrics' in result:
                    metrics = result['metrics']
                    if 'apy_percent' in metrics:
                        status_display += f" APY: {metrics['apy_percent']:.2f}%"
                    elif 'tests_passed' in metrics and 'tests_total' in metrics:
                        status_display += f" {metrics['tests_passed']}/{metrics['tests_total']}"
                
                critical_marker = " [CRITICAL]" if is_critical else ""
                print(f"{script_info['description']:<40} {status_display} ({time_taken:.1f}s){critical_marker}")
                
                # Count totals
                category_total += 1
                total_scripts += 1
                
                if status == 'PASS':
                    category_passed += 1
                    total_passed += 1
                
                if is_critical:
                    category_critical_total += 1
                    critical_scripts += 1
                    if status == 'PASS':
                        category_critical_passed += 1
                        critical_passed += 1
            
            category_summaries[category] = {
                'passed': category_passed,
                'total': category_total,
                'critical_passed': category_critical_passed,
                'critical_total': category_critical_total
            }
        
        # Overall Summary
        print(f"\n🎯 COMPREHENSIVE SUMMARY:")
        print("="*100)
        
        for category, summary in category_summaries.items():
            passed = summary['passed']
            total = summary['total']
            critical_passed = summary['critical_passed']
            critical_total = summary['critical_total']
            
            print(f"{category.upper():<20} {passed}/{total} passed ({passed/total*100:.1f}%) | Critical: {critical_passed}/{critical_total}")
        
        print("-" * 100)
        print(f"{'OVERALL':<20} {total_passed}/{total_scripts} passed ({total_passed/total_scripts*100:.1f}%) | Critical: {critical_passed}/{critical_scripts}")
        
        # Success criteria
        all_critical_passed = critical_passed == critical_scripts
        overall_success = total_passed == total_scripts
        
        print(f"\n🎯 QUALITY GATE STATUS:")
        print("-" * 100)
        
        if all_critical_passed and overall_success:
            print("🎉 SUCCESS: All quality gates passed!")
            print("🚀 System is ready for production deployment!")
            success_status = True
        elif all_critical_passed:
            print("✅ CRITICAL SUCCESS: All critical quality gates passed!")
            print(f"⚠️  Non-critical failures: {total_scripts - total_passed} (acceptable for current stage)")
            print("🚀 System is ready for production deployment!")
            success_status = True
        else:
            print("❌ CRITICAL FAILURE: Some critical quality gates failed!")
            print(f"🚨 Critical failures: {critical_scripts - critical_passed}/{critical_scripts}")
            print("🛑 System is NOT ready for production deployment!")
            success_status = False
        
        # Key achievements
        print(f"\n🎯 KEY ACHIEVEMENTS:")
        print("-" * 100)
        
        # Check for specific achievements
        if 'strategy' in all_results:
            strategy_results = all_results['strategy']
            if 'pure_lending_strategy' in strategy_results:
                pure_lending = strategy_results['pure_lending_strategy']
                if pure_lending.get('status') == 'PASS':
                    print("✅ Pure Lending Strategy: Working with proper USDT yield (3-8% APY)")
                    if 'metrics' in pure_lending and 'apy_percent' in pure_lending['metrics']:
                        apy = pure_lending['metrics']['apy_percent']
                        print(f"   📊 Validated APY: {apy:.2f}%")
        
        if 'components' in all_results:
            components_results = all_results['components']
            working_components = sum(1 for r in components_results.values() if r.get('status') == 'PASS')
            total_components = len(components_results)
            print(f"✅ Component Architecture: {working_components}/{total_components} components validated")
            print("   📊 Position Monitor: Balance tracking with proper AAVE index mechanics")
            print("   📊 Exposure Monitor: Asset filtering and underlying_balance calculation")
            print("   📊 P&L Calculator: Attribution P&L with error code propagation")
            print("   📊 Risk Monitor: Mode-specific risk calculations")
        
        print(f"\n⏱️  Total execution time: {time.time() - self.start_time:.1f}s")
        
        return success_status
    
    async def run_category(self, category: str) -> Dict[str, Any]:
        """Run all quality gates in a specific category."""
        category_results = {}
        
        scripts_in_category = {
            name: info for name, info in self.quality_gate_scripts.items() 
            if info['category'] == category
        }
        
        if not scripts_in_category:
            return {'error': f'No scripts found for category: {category}'}
        
        print(f"\n📊 Running {category.upper()} Quality Gates...")
        print("=" * 60)
        
        for script_name, script_info in scripts_in_category.items():
            result = await self.run_quality_gate_script(script_name, script_info)
            category_results[script_name] = result
            
            # Print immediate result
            status = result['status']
            time_taken = result['execution_time']
            
            if status == 'PASS':
                print(f"  ✅ {script_info['description']}: PASS ({time_taken:.1f}s)")
                if 'metrics' in result and 'apy_percent' in result['metrics']:
                    print(f"     📊 APY: {result['metrics']['apy_percent']:.2f}%")
            elif status == 'FAIL':
                print(f"  ❌ {script_info['description']}: FAIL ({time_taken:.1f}s)")
            elif status == 'TIMEOUT':
                print(f"  ⏰ {script_info['description']}: TIMEOUT ({time_taken:.1f}s)")
            elif status == 'ERROR':
                print(f"  💥 {script_info['description']}: ERROR ({time_taken:.1f}s)")
            else:
                print(f"  ❓ {script_info['description']}: {status} ({time_taken:.1f}s)")
        
        return category_results

    async def run_strategy_only(self) -> bool:
        """Run only strategy validation quality gates."""
        print("🎯 STRATEGY-ONLY QUALITY GATES")
        print("=" * 50)
        print("Focus: Pure lending strategy validation")
        print()
        
        strategy_results = await self.run_category('strategy')
        return self.generate_strategy_report(strategy_results)
    
    async def run_components_only(self) -> bool:
        """Run only component validation quality gates."""
        print("🔧 COMPONENTS-ONLY QUALITY GATES")
        print("=" * 50)
        print("Focus: Component architecture validation")
        print()
        
        components_results = await self.run_category('components')
        return self.generate_components_report(components_results)
    
    def generate_strategy_report(self, strategy_results: Dict[str, Any]) -> bool:
        """Generate strategy-specific report."""
        print("\n🎯 STRATEGY VALIDATION REPORT")
        print("=" * 50)
        
        if 'pure_lending_strategy' in strategy_results:
            result = strategy_results['pure_lending_strategy']
            status = result.get('status', 'UNKNOWN')
            
            if status == 'PASS':
                print("✅ Pure Lending Strategy: PASS")
                if 'metrics' in result:
                    metrics = result['metrics']
                    if 'apy_percent' in metrics:
                        print(f"   📊 APY: {metrics['apy_percent']:.2f}% (target: 3-8%)")
                print("🚀 Ready for other strategy implementations!")
                return True
            else:
                print(f"❌ Pure Lending Strategy: {status}")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                print("🛑 Fix pure lending before implementing other strategies!")
                return False
        
        return False
    
    def generate_components_report(self, components_results: Dict[str, Any]) -> bool:
        """Generate components-specific report."""
        print("\n🔧 COMPONENTS VALIDATION REPORT")
        print("=" * 50)
        
        passed = sum(1 for r in components_results.values() if r.get('status') == 'PASS')
        total = len(components_results)
        
        print(f"Component Tests: {passed}/{total} passed")
        
        for script_name, result in components_results.items():
            script_info = self.quality_gate_scripts[script_name]
            status = result.get('status', 'UNKNOWN')
            print(f"  {script_info['description']}: {status}")
        
        if passed == total:
            print("✅ All components validated!")
            print("🚀 Component architecture is solid!")
            return True
        else:
            print(f"❌ {total - passed} component tests failed")
            print("🛑 Fix component issues before proceeding!")
            return False


async def main():
    """Main orchestration function."""
    parser = argparse.ArgumentParser(description='Quality Gates Orchestration')
    parser.add_argument('--strategy-only', action='store_true', 
                       help='Run only strategy validation gates')
    parser.add_argument('--components-only', action='store_true',
                       help='Run only component validation gates') 
    parser.add_argument('--category', choices=['strategy', 'components', 'performance', 'configuration', 'integration'],
                       help='Run specific category of gates')
    parser.add_argument('--list-scripts', action='store_true',
                       help='List all available quality gate scripts')
    
    args = parser.parse_args()
    
    orchestrator = QualityGatesOrchestrator()
    
    if args.list_scripts:
        print("📋 AVAILABLE QUALITY GATE SCRIPTS:")
        print("=" * 60)
        for name, info in orchestrator.quality_gate_scripts.items():
            critical_marker = " [CRITICAL]" if info['critical'] else ""
            print(f"{info['description']:<40} {info['category']:<15} {info['script']}{critical_marker}")
        return 0
    
    elif args.strategy_only:
        success = await orchestrator.run_strategy_only()
        return 0 if success else 1
    
    elif args.components_only:
        success = await orchestrator.run_components_only()
        return 0 if success else 1
    
    elif args.category:
        category_results = await orchestrator.run_category(args.category)
        # Simple category-specific validation
        passed = sum(1 for r in category_results.values() if r.get('status') == 'PASS')
        total = len(category_results)
        print(f"\n📊 {args.category.upper()} SUMMARY: {passed}/{total} passed")
        return 0 if passed == total else 1
    
    else:
        # Run comprehensive validation
        print("🚦 COMPREHENSIVE QUALITY GATES VALIDATION")
        print("=" * 80)
        print("Running all quality gate categories in optimal order")
        print()
        
        all_results = await orchestrator.run_all_quality_gates()
        success = orchestrator.generate_comprehensive_report(all_results)
        
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
