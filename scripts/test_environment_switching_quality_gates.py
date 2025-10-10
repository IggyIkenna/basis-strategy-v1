#!/usr/bin/env python3
"""
Environment File Switching Quality Gates

Tests environment file switching functionality with fail-fast validation.
Validates BASIS_ENVIRONMENT variable controls, environment-specific file loading,
and proper error handling for missing files/variables.

Reference: .cursor/tasks/01_environment_file_switching.md
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from basis_strategy_v1.infrastructure.config.environment_loader import (
    EnvironmentLoader, 
    EnvironmentLoaderError,
    load_environment,
    get_environment_info
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnvironmentSwitchingQualityGates:
    """Quality gates for environment file switching functionality."""
    
    def __init__(self):
        self.results = {
            'overall_status': 'PENDING',
            'gates_passed': 0,
            'gates_failed': 0,
            'gate_results': {},
            'summary': {},
            'timestamp': None
        }
        self.temp_dir = None
        self.original_cwd = None
    
    def run_all_quality_gates(self) -> Dict[str, Any]:
        """Run all quality gates and return comprehensive results."""
        logger.info("🚀 Starting Environment Switching Quality Gates")
        logger.info("=" * 80)
        
        try:
            # Setup test environment
            self._setup_test_environment()
            
            # Run quality gates
            quality_gates = [
                ('QG1', 'Environment File Loading', self._test_environment_file_loading),
                ('QG2', 'Environment Variable Validation', self._test_environment_variable_validation),
                ('QG3', 'Override Functionality', self._test_override_functionality),
                ('QG4', 'Fail-Fast on Missing Files', self._test_fail_fast_missing_files),
                ('QG5', 'Fail-Fast on Missing Variables', self._test_fail_fast_missing_variables),
                ('QG6', 'Environment Switching', self._test_environment_switching),
                ('QG7', 'Integration Test', self._test_integration)
            ]
            
            for gate_id, gate_name, gate_test in quality_gates:
                logger.info(f"🔄 Running {gate_id}: {gate_name}")
                try:
                    result = gate_test()
                    self.results['gate_results'][gate_id] = {
                        'name': gate_name,
                        'status': 'PASS' if result else 'FAIL',
                        'details': result if isinstance(result, dict) else {}
                    }
                    if result:
                        self.results['gates_passed'] += 1
                        logger.info(f"✅ {gate_id}: {gate_name} - PASSED")
                    else:
                        self.results['gates_failed'] += 1
                        logger.error(f"❌ {gate_id}: {gate_name} - FAILED")
                except Exception as e:
                    self.results['gate_results'][gate_id] = {
                        'name': gate_name,
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    self.results['gates_failed'] += 1
                    logger.error(f"💥 {gate_id}: {gate_name} - ERROR: {e}")
            
            # Determine overall status
            total_gates = self.results['gates_passed'] + self.results['gates_failed']
            if self.results['gates_failed'] == 0:
                self.results['overall_status'] = 'PASS'
            else:
                self.results['overall_status'] = 'FAIL'
            
            self.results['summary'] = {
                'total_gates': total_gates,
                'passed': self.results['gates_passed'],
                'failed': self.results['gates_failed'],
                'pass_rate': (self.results['gates_passed'] / total_gates * 100) if total_gates > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"💥 Quality gates setup failed: {e}")
            self.results['overall_status'] = 'ERROR'
            self.results['error'] = str(e)
        
        finally:
            self._cleanup_test_environment()
        
        return self.results
    
    def _setup_test_environment(self):
        """Setup temporary test environment with test files."""
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp(prefix="env_test_")
        os.chdir(self.temp_dir)
        
        # Create test env.unified
        self._create_test_unified_file()
        
        # Create test environment files
        self._create_test_environment_files()
        
        logger.info(f"📁 Test environment setup: {self.temp_dir}")
    
    def _create_test_unified_file(self):
        """Create test env.unified file."""
        unified_content = """# Test Unified Environment Configuration
BASIS_ENVIRONMENT=
BASIS_DEPLOYMENT_MODE=
BASIS_DEPLOYMENT_MACHINE=
BASIS_DATA_DIR=
BASIS_DATA_MODE=
BASIS_RESULTS_DIR=
BASIS_DEBUG=
BASIS_LOG_LEVEL=
BASIS_EXECUTION_MODE=
BASIS_DATA_START_DATE=
BASIS_DATA_END_DATE=
HEALTH_CHECK_INTERVAL=
HEALTH_CHECK_ENDPOINT=
BASIS_API_PORT=
BASIS_API_HOST=
BASIS_API_CORS_ORIGINS=
APP_DOMAIN=
ACME_EMAIL=
HTTP_PORT=
HTTPS_PORT=
"""
        with open("env.unified", "w") as f:
            f.write(unified_content)
    
    def _create_test_environment_files(self):
        """Create test environment-specific files."""
        # Dev environment
        dev_content = """# Development Environment
BASIS_ENVIRONMENT=dev
BASIS_DEPLOYMENT_MODE=local
BASIS_DEPLOYMENT_MACHINE=local_mac
BASIS_DATA_DIR=/test/data
BASIS_DATA_MODE=csv
BASIS_RESULTS_DIR=/test/results
BASIS_DEBUG=true
BASIS_LOG_LEVEL=DEBUG
BASIS_EXECUTION_MODE=backtest
BASIS_DATA_START_DATE=2024-01-01
BASIS_DATA_END_DATE=2024-12-31
HEALTH_CHECK_INTERVAL=30s
HEALTH_CHECK_ENDPOINT=/health
BASIS_API_PORT=8001
BASIS_API_HOST=0.0.0.0
BASIS_API_CORS_ORIGINS=http://localhost:3000
APP_DOMAIN=localhost
ACME_EMAIL=dev@test.com
HTTP_PORT=80
HTTPS_PORT=443
"""
        with open("env.dev", "w") as f:
            f.write(dev_content)
        
        # Staging environment
        staging_content = """# Staging Environment
BASIS_ENVIRONMENT=staging
BASIS_DEPLOYMENT_MODE=docker
BASIS_DEPLOYMENT_MACHINE=gcloud_linux_vm
BASIS_DATA_DIR=/app/data
BASIS_DATA_MODE=csv
BASIS_RESULTS_DIR=/app/results
BASIS_DEBUG=false
BASIS_LOG_LEVEL=INFO
BASIS_EXECUTION_MODE=backtest
BASIS_DATA_START_DATE=2024-01-01
BASIS_DATA_END_DATE=2024-12-31
HEALTH_CHECK_INTERVAL=30s
HEALTH_CHECK_ENDPOINT=/health
BASIS_API_PORT=8001
BASIS_API_HOST=0.0.0.0
BASIS_API_CORS_ORIGINS=https://staging.test.com
APP_DOMAIN=staging.test.com
ACME_EMAIL=staging@test.com
HTTP_PORT=80
HTTPS_PORT=443
"""
        with open("env.staging", "w") as f:
            f.write(staging_content)
        
        # Production environment
        prod_content = """# Production Environment
BASIS_ENVIRONMENT=prod
BASIS_DEPLOYMENT_MODE=docker
BASIS_DEPLOYMENT_MACHINE=gcloud_linux_vm
BASIS_DATA_DIR=/app/data
BASIS_DATA_MODE=csv
BASIS_RESULTS_DIR=/app/results
BASIS_DEBUG=false
BASIS_LOG_LEVEL=WARNING
BASIS_EXECUTION_MODE=live
BASIS_DATA_START_DATE=2024-01-01
BASIS_DATA_END_DATE=2024-12-31
HEALTH_CHECK_INTERVAL=30s
HEALTH_CHECK_ENDPOINT=/health
BASIS_API_PORT=8001
BASIS_API_HOST=0.0.0.0
BASIS_API_CORS_ORIGINS=https://test.com
APP_DOMAIN=test.com
ACME_EMAIL=admin@test.com
HTTP_PORT=80
HTTPS_PORT=443
"""
        with open("env.prod", "w") as f:
            f.write(prod_content)
    
    def _cleanup_test_environment(self):
        """Cleanup test environment."""
        if self.original_cwd:
            os.chdir(self.original_cwd)
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _test_environment_file_loading(self) -> bool:
        """Test that environment files load correctly."""
        try:
            # Test dev environment
            loader = EnvironmentLoader('dev', Path.cwd())
            env_vars = loader.load_environment()
            
            # Verify key variables are loaded
            assert env_vars['BASIS_ENVIRONMENT'] == 'dev'
            assert env_vars['BASIS_DEPLOYMENT_MODE'] == 'local'
            assert env_vars['BASIS_DEBUG'] == 'true'
            
            # Test staging environment
            loader = EnvironmentLoader('staging', Path.cwd())
            env_vars = loader.load_environment()
            
            assert env_vars['BASIS_ENVIRONMENT'] == 'staging'
            assert env_vars['BASIS_DEPLOYMENT_MODE'] == 'docker'
            assert env_vars['BASIS_DEBUG'] == 'false'
            
            # Test production environment
            loader = EnvironmentLoader('prod', Path.cwd())
            env_vars = loader.load_environment()
            
            assert env_vars['BASIS_ENVIRONMENT'] == 'prod'
            assert env_vars['BASIS_DEPLOYMENT_MODE'] == 'docker'
            assert env_vars['BASIS_EXECUTION_MODE'] == 'live'
            
            return True
            
        except Exception as e:
            logger.error(f"Environment file loading test failed: {e}")
            return False
    
    def _test_environment_variable_validation(self) -> bool:
        """Test that environment variables are properly validated."""
        try:
            # Test with valid environment
            loader = EnvironmentLoader('dev', Path.cwd())
            env_vars = loader.load_environment()
            
            # Verify all required variables are present and non-empty
            required_vars = [
                'BASIS_ENVIRONMENT', 'BASIS_DEPLOYMENT_MODE', 'BASIS_DATA_DIR',
                'BASIS_DEBUG', 'BASIS_LOG_LEVEL', 'BASIS_API_PORT'
            ]
            
            for var in required_vars:
                assert var in env_vars, f"Required variable {var} not found"
                assert env_vars[var].strip(), f"Required variable {var} is empty"
            
            return True
            
        except Exception as e:
            logger.error(f"Environment variable validation test failed: {e}")
            return False
    
    def _test_override_functionality(self) -> bool:
        """Test that environment-specific overrides work correctly."""
        try:
            # Create a test unified file with different values
            with open("env.unified", "w") as f:
                f.write("""BASIS_ENVIRONMENT=unified_default
BASIS_DEPLOYMENT_MODE=unified_mode
BASIS_DEBUG=false
BASIS_LOG_LEVEL=INFO
BASIS_API_PORT=9000
""")
            
            # Create dev override
            with open("env.dev", "w") as f:
                f.write("""BASIS_ENVIRONMENT=dev
BASIS_DEBUG=true
BASIS_LOG_LEVEL=DEBUG
""")
            
            # Test that dev overrides unified
            loader = EnvironmentLoader('dev', Path.cwd())
            env_vars = loader.load_environment()
            
            assert env_vars['BASIS_ENVIRONMENT'] == 'dev'  # Overridden
            assert env_vars['BASIS_DEPLOYMENT_MODE'] == 'unified_mode'  # From unified
            assert env_vars['BASIS_DEBUG'] == 'true'  # Overridden
            assert env_vars['BASIS_LOG_LEVEL'] == 'DEBUG'  # Overridden
            assert env_vars['BASIS_API_PORT'] == '9000'  # From unified
            
            return True
            
        except Exception as e:
            logger.error(f"Override functionality test failed: {e}")
            return False
    
    def _test_fail_fast_missing_files(self) -> bool:
        """Test that missing environment files cause immediate failure."""
        try:
            # Remove dev environment file
            os.remove("env.dev")
            
            # Test that loading fails
            loader = EnvironmentLoader('dev', Path.cwd())
            try:
                loader.load_environment()
                return False  # Should have failed
            except EnvironmentLoaderError as e:
                assert "not found" in str(e).lower()
                return True
            
        except Exception as e:
            logger.error(f"Fail-fast missing files test failed: {e}")
            return False
    
    def _test_fail_fast_missing_variables(self) -> bool:
        """Test that missing required variables cause immediate failure."""
        try:
            # Create incomplete dev environment file with only 2 variables
            with open("env.dev", "w") as f:
                f.write("""BASIS_ENVIRONMENT=dev
BASIS_DEPLOYMENT_MODE=local
# Missing all other required variables
""")
            
            # Create incomplete unified file with only 2 variables
            with open("env.unified", "w") as f:
                f.write("""BASIS_ENVIRONMENT=
BASIS_DEPLOYMENT_MODE=
# Missing all other required variables
""")
            
            # Clear system environment variables that might interfere
            import os
            original_env = {}
            for key in list(os.environ.keys()):
                if key.startswith('BASIS_') or key in ['APP_DOMAIN', 'ACME_EMAIL', 'HTTP_PORT', 'HTTPS_PORT']:
                    original_env[key] = os.environ[key]
                    del os.environ[key]
            
            try:
                # Test that loading fails
                loader = EnvironmentLoader('dev', Path.cwd())
                try:
                    loader.load_environment()
                    return False  # Should have failed
                except EnvironmentLoaderError as e:
                    error_msg = str(e).lower()
                    # Check for missing or empty variable indicators
                    if "missing" in error_msg or "empty" in error_msg or "required" in error_msg:
                        return True
                    else:
                        logger.error(f"Unexpected error message: {e}")
                        return False
            finally:
                # Restore original environment
                for key, value in original_env.items():
                    os.environ[key] = value
            
        except Exception as e:
            logger.error(f"Fail-fast missing variables test failed: {e}")
            return False
    
    def _test_environment_switching(self) -> bool:
        """Test that BASIS_ENVIRONMENT variable controls environment switching."""
        try:
            # Test default environment (should be dev)
            os.environ.pop('BASIS_ENVIRONMENT', None)
            loader = EnvironmentLoader()
            assert loader.environment == 'dev'
            
            # Test explicit environment setting
            loader = EnvironmentLoader('staging')
            assert loader.environment == 'staging'
            
            # Test environment variable setting
            os.environ['BASIS_ENVIRONMENT'] = 'prod'
            loader = EnvironmentLoader()
            assert loader.environment == 'prod'
            
            return True
            
        except Exception as e:
            logger.error(f"Environment switching test failed: {e}")
            return False
    
    def _test_integration(self) -> bool:
        """Test integration with global loader functions."""
        try:
            # Test global load_environment function
            env_vars = load_environment('dev')
            assert env_vars['BASIS_ENVIRONMENT'] == 'dev'
            
            # Test get_environment_info function
            info = get_environment_info()
            assert info['environment'] == 'dev'
            assert 'env_file' in info
            assert 'unified_file' in info
            
            return True
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            return False


def main():
    """Main function to run quality gates."""
    quality_gates = EnvironmentSwitchingQualityGates()
    results = quality_gates.run_all_quality_gates()
    
    # Print results
    print("\n" + "=" * 80)
    print("🚦 ENVIRONMENT SWITCHING QUALITY GATES RESULTS")
    print("=" * 80)
    
    print(f"Overall Status: {results['overall_status']}")
    print(f"Gates Passed: {results['gates_passed']}")
    print(f"Gates Failed: {results['gates_failed']}")
    
    if 'summary' in results:
        summary = results['summary']
        print(f"Pass Rate: {summary['pass_rate']:.1f}%")
    
    print("\nGate Results:")
    for gate_id, gate_result in results['gate_results'].items():
        status = gate_result['status']
        name = gate_result['name']
        print(f"  {gate_id}: {name} - {status}")
        if 'error' in gate_result:
            print(f"    Error: {gate_result['error']}")
    
    if results['overall_status'] == 'PASS':
        print("\n🎉 All environment switching quality gates passed!")
        return 0
    else:
        print(f"\n❌ {results['gates_failed']} environment switching quality gates failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())