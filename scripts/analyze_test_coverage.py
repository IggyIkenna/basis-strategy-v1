#!/usr/bin/env python3
"""
Test Coverage Analysis Script

Analyzes current test coverage and identifies gaps to reach 80% overall coverage.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any
import argparse


def run_coverage_analysis() -> Dict[str, Any]:
    """Run pytest with coverage analysis."""
    print("🔍 Running test coverage analysis...")
    
    try:
        # Run pytest with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "--cov=backend/src/basis_strategy_v1",
            "--cov-report=json",
            "--cov-report=term-missing",
            "scripts/unit_tests/",
            "-v"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode != 0:
            print(f"❌ Test execution failed: {result.stderr}")
            return {}
        
        # Parse coverage report
        coverage_file = Path(__file__).parent.parent / "coverage.json"
        if coverage_file.exists():
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            return coverage_data
        else:
            print("❌ Coverage report not found")
            return {}
            
    except Exception as e:
        print(f"❌ Coverage analysis failed: {e}")
        return {}


def analyze_component_coverage(coverage_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze coverage by component."""
    if not coverage_data:
        return {}
    
    files = coverage_data.get('files', {})
    component_coverage = {}
    
    # Define component mappings
    component_mappings = {
        'position_monitor': 'core/strategies/components/position_monitor.py',
        'exposure_monitor': 'core/strategies/components/exposure_monitor.py',
        'risk_monitor': 'core/rebalancing/risk_monitor.py',
        'pnl_calculator': 'core/math/pnl_calculator.py',
        'strategy_manager': 'core/strategies/components/strategy_manager.py',
        'data_provider': 'infrastructure/data/historical_data_provider.py',
        'event_logger': 'core/strategies/components/event_logger.py',
        'event_engine': 'core/event_engine/event_driven_strategy_engine.py',
        'execution_interfaces': 'core/interfaces/',
        'health_system': 'core/health/',
        'api_routes': 'api/routes/',
        'config_system': 'infrastructure/config/'
    }
    
    for component, pattern in component_mappings.items():
        component_files = []
        total_lines = 0
        covered_lines = 0
        
        for file_path, file_data in files.items():
            if pattern in file_path:
                component_files.append(file_path)
                total_lines += file_data.get('summary', {}).get('num_statements', 0)
                covered_lines += file_data.get('summary', {}).get('covered_lines', 0)
        
        if total_lines > 0:
            coverage_pct = (covered_lines / total_lines) * 100
            component_coverage[component] = {
                'files': component_files,
                'total_lines': total_lines,
                'covered_lines': covered_lines,
                'coverage_pct': coverage_pct,
                'missing_lines': total_lines - covered_lines
            }
    
    return component_coverage


def identify_coverage_gaps(component_coverage: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify coverage gaps and recommendations."""
    gaps = []
    
    # Target coverage percentages
    targets = {
        'position_monitor': 85,
        'exposure_monitor': 90,
        'risk_monitor': 90,
        'pnl_calculator': 85,
        'strategy_manager': 80,
        'data_provider': 85,
        'event_logger': 90,
        'event_engine': 80,
        'execution_interfaces': 75,
        'health_system': 80,
        'api_routes': 70,
        'config_system': 80
    }
    
    for component, data in component_coverage.items():
        target = targets.get(component, 80)
        current = data['coverage_pct']
        
        if current < target:
            gap = target - current
            gaps.append({
                'component': component,
                'current_coverage': current,
                'target_coverage': target,
                'gap': gap,
                'missing_lines': data['missing_lines'],
                'files': data['files'],
                'priority': 'HIGH' if gap > 20 else 'MEDIUM' if gap > 10 else 'LOW'
            })
    
    return sorted(gaps, key=lambda x: x['gap'], reverse=True)


def generate_coverage_report(coverage_data: Dict[str, Any], component_coverage: Dict[str, Any], gaps: List[Dict[str, Any]]):
    """Generate comprehensive coverage report."""
    print("\n" + "="*80)
    print("📊 TEST COVERAGE ANALYSIS REPORT")
    print("="*80)
    
    # Overall coverage
    overall = coverage_data.get('totals', {})
    overall_coverage = overall.get('percent_covered', 0)
    print(f"\n🎯 OVERALL COVERAGE: {overall_coverage:.1f}%")
    print(f"   Target: 80.0%")
    print(f"   Gap: {80.0 - overall_coverage:.1f}%")
    print(f"   Status: {'✅ PASS' if overall_coverage >= 80 else '❌ FAIL'}")
    
    # Component coverage
    print(f"\n📋 COMPONENT COVERAGE:")
    print("-" * 80)
    print(f"{'Component':<20} {'Coverage':<10} {'Target':<10} {'Status':<10} {'Files':<10}")
    print("-" * 80)
    
    targets = {
        'position_monitor': 85, 'exposure_monitor': 90, 'risk_monitor': 90,
        'pnl_calculator': 85, 'strategy_manager': 80, 'data_provider': 85,
        'event_logger': 90, 'event_engine': 80, 'execution_interfaces': 75,
        'health_system': 80, 'api_routes': 70, 'config_system': 80
    }
    
    for component, data in component_coverage.items():
        target = targets.get(component, 80)
        status = '✅ PASS' if data['coverage_pct'] >= target else '❌ FAIL'
        print(f"{component:<20} {data['coverage_pct']:>6.1f}%   {target:>6.0f}%   {status:<10} {len(data['files']):>6}")
    
    # Coverage gaps
    if gaps:
        print(f"\n🔍 COVERAGE GAPS (Priority Order):")
        print("-" * 80)
        print(f"{'Component':<20} {'Current':<10} {'Target':<10} {'Gap':<10} {'Priority':<10}")
        print("-" * 80)
        
        for gap in gaps:
            print(f"{gap['component']:<20} {gap['current_coverage']:>6.1f}%   {gap['target_coverage']:>6.0f}%   {gap['gap']:>6.1f}%   {gap['priority']:<10}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 80)
    
    if gaps:
        for gap in gaps[:5]:  # Top 5 gaps
            print(f"🎯 {gap['component']}: Add {gap['missing_lines']} lines of test coverage")
            print(f"   Files: {', '.join([os.path.basename(f) for f in gap['files']])}")
            print()
    else:
        print("🎉 All components meet coverage targets!")
    
    # Test file analysis
    print(f"\n📁 TEST FILE ANALYSIS:")
    print("-" * 80)
    
    test_dir = Path(__file__).parent / "unit_tests"
    test_files = list(test_dir.rglob("test_*.py"))
    unit_tests = [f for f in test_files if "unit" in str(f)]
    integration_tests = [f for f in test_files if "integration" in str(f)]
    e2e_tests = [f for f in test_files if "e2e" in str(f)]
    
    print(f"Unit Tests: {len(unit_tests)} files")
    print(f"Integration Tests: {len(integration_tests)} files")
    print(f"E2E Tests: {len(e2e_tests)} files")
    print(f"Total Test Files: {len(test_files)} files")
    
    # Missing test files
    print(f"\n❌ MISSING TEST FILES:")
    print("-" * 80)
    
    # Check for missing test files
    src_dir = Path(__file__).parent.parent / "backend" / "src" / "basis_strategy_v1"
    missing_tests = []
    
    for py_file in src_dir.rglob("*.py"):
        if "__init__.py" in str(py_file):
            continue
        
        # Check if test file exists
        rel_path = py_file.relative_to(src_dir)
        test_path = test_dir / f"test_{rel_path.name}"
        
        if not test_path.exists():
            missing_tests.append(str(rel_path))
    
    if missing_tests:
        for test in missing_tests[:10]:  # Show first 10
            print(f"   {test}")
        if len(missing_tests) > 10:
            print(f"   ... and {len(missing_tests) - 10} more")
    else:
        print("   All source files have corresponding test files!")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Analyze test coverage")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    print("🧪 TEST COVERAGE ANALYSIS")
    print("=" * 50)
    
    # Run coverage analysis
    coverage_data = run_coverage_analysis()
    if not coverage_data:
        print("❌ Failed to run coverage analysis")
        return 1
    
    # Analyze component coverage
    component_coverage = analyze_component_coverage(coverage_data)
    
    # Identify gaps
    gaps = identify_coverage_gaps(component_coverage)
    
    # Generate report
    generate_coverage_report(coverage_data, component_coverage, gaps)
    
    # Overall status
    overall_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
    if overall_coverage >= 80:
        print(f"\n🎉 SUCCESS: Overall coverage {overall_coverage:.1f}% meets 80% target!")
        return 0
    else:
        print(f"\n⚠️  WARNING: Overall coverage {overall_coverage:.1f}% below 80% target")
        return 1


if __name__ == "__main__":
    sys.exit(main())
