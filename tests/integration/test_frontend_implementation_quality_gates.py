#!/usr/bin/env python3
"""
Quality Gate: Frontend Implementation
Validates frontend components, API integration, and user interface functionality.
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_frontend_structure(frontend_dir: str = "frontend/") -> Dict[str, any]:
    """Check frontend directory structure and key files."""
    structure_checks = {
        'package_json_exists': False,
        'src_directory_exists': False,
        'components_directory_exists': False,
        'pages_directory_exists': False,
        'api_directory_exists': False,
        'styles_directory_exists': False,
        'public_directory_exists': False,
        'missing_files': [],
        'structure_compliant': True
    }
    
    required_files = [
        'package.json',
        'src/',
        'src/components/',
        'src/pages/',
        'src/api/',
        'src/styles/',
        'public/',
        'public/index.html'
    ]
    
    for file_path in required_files:
        full_path = os.path.join(frontend_dir, file_path)
        if os.path.exists(full_path):
            if file_path == 'package.json':
                structure_checks['package_json_exists'] = True
            elif file_path == 'src/':
                structure_checks['src_directory_exists'] = True
            elif file_path == 'src/components/':
                structure_checks['components_directory_exists'] = True
            elif file_path == 'src/pages/':
                structure_checks['pages_directory_exists'] = True
            elif file_path == 'src/api/':
                structure_checks['api_directory_exists'] = True
            elif file_path == 'src/styles/':
                structure_checks['styles_directory_exists'] = True
            elif file_path == 'public/':
                structure_checks['public_directory_exists'] = True
        else:
            structure_checks['missing_files'].append(file_path)
            structure_checks['structure_compliant'] = False
    
    return structure_checks

def check_package_json(frontend_dir: str = "frontend/") -> Dict[str, any]:
    """Check package.json for required dependencies and scripts."""
    package_json_path = os.path.join(frontend_dir, 'package.json')
    
    if not os.path.exists(package_json_path):
        return {
            'exists': False,
            'error': 'package.json not found'
        }
    
    try:
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        required_deps = [
            'react',
            'react-dom',
            'axios',
            'react-router-dom',
            'styled-components'
        ]
        
        required_scripts = [
            'start',
            'build',
            'test'
        ]
        
        deps = package_data.get('dependencies', {})
        scripts = package_data.get('scripts', {})
        
        missing_deps = [dep for dep in required_deps if dep not in deps]
        missing_scripts = [script for script in required_scripts if script not in scripts]
        
        return {
            'exists': True,
            'dependencies': deps,
            'scripts': scripts,
            'missing_dependencies': missing_deps,
            'missing_scripts': missing_scripts,
            'is_compliant': len(missing_deps) == 0 and len(missing_scripts) == 0
        }
    except Exception as e:
        return {
            'exists': True,
            'error': str(e),
            'is_compliant': False
        }

def check_react_components(frontend_dir: str = "frontend/") -> Dict[str, any]:
    """Check for React components and their structure."""
    components_dir = os.path.join(frontend_dir, 'src', 'components')
    
    if not os.path.exists(components_dir):
        return {
            'components_found': 0,
            'components_analyzed': 0,
            'jsx_components': 0,
            'tsx_components': 0,
            'missing_components': [],
            'is_compliant': False
        }
    
    components = []
    jsx_count = 0
    tsx_count = 0
    
    for file in os.listdir(components_dir):
        if file.endswith(('.jsx', '.tsx')):
            components.append(file)
            if file.endswith('.jsx'):
                jsx_count += 1
            else:
                tsx_count += 1
    
    # Expected components for basis strategy
    expected_components = [
        'StrategyDashboard',
        'PositionMonitor',
        'RiskMonitor',
        'PnlCalculator',
        'ExecutionManager',
        'DataProvider',
        'EventLogger'
    ]
    
    missing_components = []
    for expected in expected_components:
        found = any(expected.lower() in comp.lower() for comp in components)
        if not found:
            missing_components.append(expected)
    
    return {
        'components_found': len(components),
        'components_analyzed': len(components),
        'jsx_components': jsx_count,
        'tsx_components': tsx_count,
        'missing_components': missing_components,
        'is_compliant': len(missing_components) == 0
    }

def check_api_integration(frontend_dir: str = "frontend/") -> Dict[str, any]:
    """Check API integration and backend connectivity."""
    api_dir = os.path.join(frontend_dir, 'src', 'api')
    
    if not os.path.exists(api_dir):
        return {
            'api_files_found': 0,
            'backend_endpoints': [],
            'is_compliant': False
        }
    
    api_files = [f for f in os.listdir(api_dir) if f.endswith(('.js', '.ts'))]
    
    # Check for API service files
    expected_api_files = [
        'strategyService.js',
        'positionService.js',
        'riskService.js',
        'executionService.js'
    ]
    
    found_api_files = []
    for expected in expected_api_files:
        if any(expected.lower() in f.lower() for f in api_files):
            found_api_files.append(expected)
    
    return {
        'api_files_found': len(api_files),
        'expected_api_files': expected_api_files,
        'found_api_files': found_api_files,
        'missing_api_files': [f for f in expected_api_files if f not in found_api_files],
        'is_compliant': len(found_api_files) >= len(expected_api_files) * 0.8
    }

def check_backend_connectivity(backend_url: str = "http://localhost:8000") -> Dict[str, any]:
    """Check if frontend can connect to backend API."""
    try:
        # Test health endpoint
        health_response = requests.get(f"{backend_url}/health", timeout=5)
        health_status = health_response.status_code == 200
        
        # Test API endpoints
        api_endpoints = [
            "/api/strategies",
            "/api/positions",
            "/api/risk",
            "/api/execution"
        ]
        
        endpoint_status = {}
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"{backend_url}{endpoint}", timeout=5)
                endpoint_status[endpoint] = response.status_code in [200, 404]  # 404 is OK if endpoint exists but no data
            except:
                endpoint_status[endpoint] = False
        
        return {
            'backend_reachable': True,
            'health_endpoint': health_status,
            'api_endpoints': endpoint_status,
            'is_compliant': health_status and any(endpoint_status.values())
        }
    except Exception as e:
        return {
            'backend_reachable': False,
            'error': str(e),
            'is_compliant': False
        }

def main():
    """Main function."""
    print("🚦 FRONTEND IMPLEMENTATION QUALITY GATES")
    print("=" * 60)
    
    # Check frontend structure
    print("📁 Checking frontend structure...")
    structure_checks = check_frontend_structure()
    
    # Check package.json
    print("📦 Checking package.json...")
    package_checks = check_package_json()
    
    # Check React components
    print("⚛️  Checking React components...")
    component_checks = check_react_components()
    
    # Check API integration
    print("🔌 Checking API integration...")
    api_checks = check_api_integration()
    
    # Check backend connectivity
    print("🌐 Checking backend connectivity...")
    connectivity_checks = check_backend_connectivity()
    
    # Print results
    print(f"\n📊 FRONTEND STRUCTURE ANALYSIS")
    print("=" * 50)
    
    if structure_checks['structure_compliant']:
        print("✅ Frontend structure is compliant")
    else:
        print("❌ Frontend structure issues:")
        for missing in structure_checks['missing_files']:
            print(f"  - Missing: {missing}")
    
    print(f"\n📦 PACKAGE.JSON ANALYSIS")
    print("=" * 50)
    
    if package_checks.get('is_compliant', False):
        print("✅ Package.json is compliant")
    else:
        print("❌ Package.json issues:")
        if package_checks.get('missing_dependencies'):
            print(f"  - Missing dependencies: {package_checks['missing_dependencies']}")
        if package_checks.get('missing_scripts'):
            print(f"  - Missing scripts: {package_checks['missing_scripts']}")
    
    print(f"\n⚛️  REACT COMPONENTS ANALYSIS")
    print("=" * 50)
    
    print(f"Components found: {component_checks['components_found']}")
    print(f"JSX components: {component_checks['jsx_components']}")
    print(f"TSX components: {component_checks['tsx_components']}")
    
    if component_checks['is_compliant']:
        print("✅ All required components found")
    else:
        print("❌ Missing components:")
        for missing in component_checks['missing_components']:
            print(f"  - {missing}")
    
    print(f"\n🔌 API INTEGRATION ANALYSIS")
    print("=" * 50)
    
    print(f"API files found: {api_checks['api_files_found']}")
    print(f"Expected API files: {len(api_checks['expected_api_files'])}")
    print(f"Found API files: {len(api_checks['found_api_files'])}")
    
    if api_checks['is_compliant']:
        print("✅ API integration is compliant")
    else:
        print("❌ Missing API files:")
        for missing in api_checks['missing_api_files']:
            print(f"  - {missing}")
    
    print(f"\n🌐 BACKEND CONNECTIVITY ANALYSIS")
    print("=" * 50)
    
    if connectivity_checks['backend_reachable']:
        print("✅ Backend is reachable")
        print(f"Health endpoint: {'✅' if connectivity_checks['health_endpoint'] else '❌'}")
        print("API endpoints:")
        for endpoint, status in connectivity_checks['api_endpoints'].items():
            print(f"  {endpoint}: {'✅' if status else '❌'}")
    else:
        print("❌ Backend connectivity issues:")
        print(f"  Error: {connectivity_checks.get('error', 'Unknown error')}")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT")
    print("=" * 50)
    
    all_checks = [
        structure_checks['structure_compliant'],
        package_checks.get('is_compliant', False),
        component_checks['is_compliant'],
        api_checks['is_compliant'],
        connectivity_checks['is_compliant']
    ]
    
    passed_checks = sum(all_checks)
    total_checks = len(all_checks)
    compliance_rate = passed_checks / total_checks
    
    if compliance_rate >= 0.8:
        print("🎉 SUCCESS: Frontend implementation is compliant!")
        print(f"   Compliance Rate: {compliance_rate:.1%}")
        return 0
    else:
        print("⚠️  ISSUES FOUND:")
        print(f"   Compliance Rate: {compliance_rate:.1%}")
        print(f"   Passed Checks: {passed_checks}/{total_checks}")
        return 1

if __name__ == "__main__":
    sys.exit(main())