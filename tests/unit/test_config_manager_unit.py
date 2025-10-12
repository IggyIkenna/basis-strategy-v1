"""
Unit tests for ConfigManager - Environment switching and fail-fast validation
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import sys

# Add the backend src to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend" / "src"))

from basis_strategy_v1.infrastructure.config.config_manager import ConfigManager, get_config_manager


class TestConfigManagerEnvironmentSwitching:
    """Test environment file switching functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear any existing instance
        ConfigManager._instance = None
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create test environment files
        self._create_test_env_files()
        
        # Create test configuration directories
        self._create_test_config_directories()
    
    def teardown_method(self):
        """Clean up test environment."""
        # Clear environment variables
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_') or key in ['HEALTH_CHECK_INTERVAL', 'HEALTH_CHECK_ENDPOINT']:
                del os.environ[key]
        
        # Clear singleton instance
        ConfigManager._instance = None
    
    def _create_test_env_files(self):
        """Create test environment files."""
        # Create env.unified
        unified_content = """# Base environment variables
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
"""
        (self.temp_path / "env.unified").write_text(unified_content)
        
        # Create env.dev
        dev_content = """# Development environment
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
BASIS_API_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
"""
        (self.temp_path / "env.dev").write_text(dev_content)
        
        # Create env.staging
        staging_content = """# Staging environment
BASIS_ENVIRONMENT=staging
BASIS_DEPLOYMENT_MODE=staging
BASIS_DEPLOYMENT_MACHINE=staging_server
BASIS_DATA_DIR=/staging/data
BASIS_DATA_MODE=csv
BASIS_RESULTS_DIR=/staging/results
BASIS_DEBUG=false
BASIS_LOG_LEVEL=INFO
BASIS_EXECUTION_MODE=backtest
BASIS_DATA_START_DATE=2024-01-01
BASIS_DATA_END_DATE=2024-12-31
HEALTH_CHECK_INTERVAL=30s
HEALTH_CHECK_ENDPOINT=/health
BASIS_API_PORT=8001
BASIS_API_HOST=0.0.0.0
BASIS_API_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
"""
        (self.temp_path / "env.staging").write_text(staging_content)
        
        # Create env.prod
        prod_content = """# Production environment
BASIS_ENVIRONMENT=prod
BASIS_DEPLOYMENT_MODE=prod
BASIS_DEPLOYMENT_MACHINE=prod_server
BASIS_DATA_DIR=/prod/data
BASIS_DATA_MODE=db
BASIS_RESULTS_DIR=/prod/results
BASIS_DEBUG=false
BASIS_LOG_LEVEL=WARNING
BASIS_EXECUTION_MODE=live
BASIS_DATA_START_DATE=2024-01-01
BASIS_DATA_END_DATE=2024-12-31
HEALTH_CHECK_INTERVAL=30s
HEALTH_CHECK_ENDPOINT=/health
BASIS_API_PORT=8001
BASIS_API_HOST=0.0.0.0
BASIS_API_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
"""
        (self.temp_path / "env.prod").write_text(prod_content)
    
    def _create_test_config_directories(self):
        """Create test configuration directories."""
        # Create configs directory structure
        (self.temp_path / "configs" / "modes").mkdir(parents=True)
        (self.temp_path / "configs" / "venues").mkdir(parents=True)
        (self.temp_path / "configs" / "share_classes").mkdir(parents=True)
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_environment_switching_dev(self, mock_path):
        """Test dev environment loading."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Set environment variable
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        
        # Create config manager
        config_manager = ConfigManager()
        
        # Verify environment is loaded correctly
        assert config_manager.get_environment() == 'dev'
        assert config_manager.get_execution_mode() == 'backtest'
        assert config_manager.config_cache['env']['BASIS_DEBUG'] == 'true'
        assert config_manager.config_cache['env']['BASIS_LOG_LEVEL'] == 'DEBUG'
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_environment_switching_staging(self, mock_path):
        """Test staging environment loading."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Set environment variable
        os.environ['BASIS_ENVIRONMENT'] = 'staging'
        
        # Create config manager
        config_manager = ConfigManager()
        
        # Verify environment is loaded correctly
        assert config_manager.get_environment() == 'staging'
        assert config_manager.get_execution_mode() == 'backtest'
        assert config_manager.config_cache['env']['BASIS_DEBUG'] == 'false'
        assert config_manager.config_cache['env']['BASIS_LOG_LEVEL'] == 'INFO'
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_environment_switching_prod(self, mock_path):
        """Test prod environment loading."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Set environment variable
        os.environ['BASIS_ENVIRONMENT'] = 'prod'
        
        # Create config manager
        config_manager = ConfigManager()
        
        # Verify environment is loaded correctly
        assert config_manager.get_environment() == 'prod'
        assert config_manager.get_execution_mode() == 'live'
        assert config_manager.config_cache['env']['BASIS_DEBUG'] == 'false'
        assert config_manager.config_cache['env']['BASIS_LOG_LEVEL'] == 'WARNING'
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_missing_environment_variable_fails(self, mock_path):
        """Test that missing BASIS_ENVIRONMENT fails fast."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Don't set BASIS_ENVIRONMENT
        if 'BASIS_ENVIRONMENT' in os.environ:
            del os.environ['BASIS_ENVIRONMENT']
        
        # Should fail fast
        with pytest.raises(ValueError, match="REQUIRED environment variable not set: BASIS_ENVIRONMENT"):
            ConfigManager()
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_missing_environment_file_fails(self, mock_path):
        """Test that missing environment file fails fast."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Set environment variable
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        
        # Remove the dev environment file
        (self.temp_path / "env.dev").unlink()
        
        # Should fail fast
        with pytest.raises(FileNotFoundError, match="Environment file not found"):
            ConfigManager()
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_invalid_environment_value_fails(self, mock_path):
        """Test that invalid environment value fails fast."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Set invalid environment variable
        os.environ['BASIS_ENVIRONMENT'] = 'invalid'
        
        # Should fail fast
        with pytest.raises(ValueError, match="Unknown environment: invalid"):
            ConfigManager()
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_missing_required_variable_fails(self, mock_path):
        """Test that missing required variable fails fast."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Clear all environment variables first
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_') or key in ['HEALTH_CHECK_INTERVAL', 'HEALTH_CHECK_ENDPOINT']:
                del os.environ[key]
        
        # Set only BASIS_ENVIRONMENT, don't load environment files
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        
        # Mock the environment file loading to not load any files
        with patch.object(ConfigManager, '_load_env_file'):
            # Should fail fast because required variables are missing
            with pytest.raises(ValueError, match="REQUIRED environment variable not set"):
                ConfigManager()
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_invalid_boolean_value_fails(self, mock_path):
        """Test that invalid boolean value fails fast."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Clear all environment variables first
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_') or key in ['HEALTH_CHECK_INTERVAL', 'HEALTH_CHECK_ENDPOINT']:
                del os.environ[key]
        
        # Set all required environment variables with valid values
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        os.environ['BASIS_DEPLOYMENT_MODE'] = 'local'
        os.environ['BASIS_DEPLOYMENT_MACHINE'] = 'local_mac'
        os.environ['BASIS_DATA_DIR'] = '/test/data'
        os.environ['BASIS_DATA_MODE'] = 'csv'
        os.environ['BASIS_RESULTS_DIR'] = '/test/results'
        os.environ['BASIS_LOG_LEVEL'] = 'DEBUG'
        os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
        os.environ['BASIS_DATA_START_DATE'] = '2024-01-01'
        os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
        os.environ['HEALTH_CHECK_INTERVAL'] = '30s'
        os.environ['HEALTH_CHECK_ENDPOINT'] = '/health'
        
        # Set invalid boolean value
        os.environ['BASIS_DEBUG'] = 'invalid'
        
        # Mock the environment file loading to not load any files
        with patch.object(ConfigManager, '_load_env_file'):
            # Should fail fast
            with pytest.raises(ValueError, match="Invalid boolean value for BASIS_DEBUG"):
                ConfigManager()
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_invalid_integer_value_fails(self, mock_path):
        """Test that invalid integer value fails fast."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Clear all environment variables first
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_') or key in ['HEALTH_CHECK_INTERVAL', 'HEALTH_CHECK_ENDPOINT']:
                del os.environ[key]
        
        # Set all required environment variables with valid values
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        os.environ['BASIS_DEPLOYMENT_MODE'] = 'local'
        os.environ['BASIS_DEPLOYMENT_MACHINE'] = 'local_mac'
        os.environ['BASIS_DATA_DIR'] = '/test/data'
        os.environ['BASIS_DATA_MODE'] = 'csv'
        os.environ['BASIS_RESULTS_DIR'] = '/test/results'
        os.environ['BASIS_DEBUG'] = 'true'
        os.environ['BASIS_LOG_LEVEL'] = 'DEBUG'
        os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
        os.environ['BASIS_DATA_START_DATE'] = '2024-01-01'
        os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
        os.environ['HEALTH_CHECK_INTERVAL'] = '30s'
        os.environ['HEALTH_CHECK_ENDPOINT'] = '/health'
        
        # Set invalid integer value
        os.environ['BASIS_API_PORT'] = 'invalid'
        
        # Mock the environment file loading to not load any files
        with patch.object(ConfigManager, '_load_env_file'):
            # Should fail fast
            with pytest.raises(ValueError, match="Invalid integer value for BASIS_API_PORT"):
                ConfigManager()
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_invalid_date_format_fails(self, mock_path):
        """Test that invalid date format fails fast."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Clear all environment variables first
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_') or key in ['HEALTH_CHECK_INTERVAL', 'HEALTH_CHECK_ENDPOINT']:
                del os.environ[key]
        
        # Set all required environment variables with valid values
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        os.environ['BASIS_DEPLOYMENT_MODE'] = 'local'
        os.environ['BASIS_DEPLOYMENT_MACHINE'] = 'local_mac'
        os.environ['BASIS_DATA_DIR'] = '/test/data'
        os.environ['BASIS_DATA_MODE'] = 'csv'
        os.environ['BASIS_RESULTS_DIR'] = '/test/results'
        os.environ['BASIS_DEBUG'] = 'true'
        os.environ['BASIS_LOG_LEVEL'] = 'DEBUG'
        os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
        os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
        os.environ['HEALTH_CHECK_INTERVAL'] = '30s'
        os.environ['HEALTH_CHECK_ENDPOINT'] = '/health'
        
        # Set invalid date value
        os.environ['BASIS_DATA_START_DATE'] = 'invalid-date'
        
        # Mock the environment file loading to not load any files
        with patch.object(ConfigManager, '_load_env_file'):
            # Should fail fast
            with pytest.raises(ValueError, match="Invalid date format for BASIS_DATA_START_DATE"):
                ConfigManager()
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_invalid_duration_format_fails(self, mock_path):
        """Test that invalid duration format fails fast."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Clear all environment variables first
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_') or key in ['HEALTH_CHECK_INTERVAL', 'HEALTH_CHECK_ENDPOINT']:
                del os.environ[key]
        
        # Set all required environment variables with valid values
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        os.environ['BASIS_DEPLOYMENT_MODE'] = 'local'
        os.environ['BASIS_DEPLOYMENT_MACHINE'] = 'local_mac'
        os.environ['BASIS_DATA_DIR'] = '/test/data'
        os.environ['BASIS_DATA_MODE'] = 'csv'
        os.environ['BASIS_RESULTS_DIR'] = '/test/results'
        os.environ['BASIS_DEBUG'] = 'true'
        os.environ['BASIS_LOG_LEVEL'] = 'DEBUG'
        os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
        os.environ['BASIS_DATA_START_DATE'] = '2024-01-01'
        os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
        os.environ['HEALTH_CHECK_ENDPOINT'] = '/health'
        
        # Set invalid duration value
        os.environ['HEALTH_CHECK_INTERVAL'] = 'invalid'
        
        # Mock the environment file loading to not load any files
        with patch.object(ConfigManager, '_load_env_file'):
            # Should fail fast
            with pytest.raises(ValueError, match="Invalid duration format for HEALTH_CHECK_INTERVAL"):
                ConfigManager()
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_environment_file_permission_error_fails(self, mock_path):
        """Test that unreadable environment file fails fast."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Set environment variable
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        
        # Make the file unreadable
        env_file = self.temp_path / "env.dev"
        env_file.chmod(0o000)
        
        try:
            # Should fail fast
            with pytest.raises(PermissionError, match="Environment file not readable"):
                ConfigManager()
        finally:
            # Restore permissions for cleanup
            env_file.chmod(0o644)
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_singleton_pattern(self, mock_path):
        """Test that ConfigManager follows singleton pattern."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Clear any existing instance
        ConfigManager._instance = None
        
        # Clear all environment variables first
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_') or key in ['HEALTH_CHECK_INTERVAL', 'HEALTH_CHECK_ENDPOINT']:
                del os.environ[key]
        
        # Set required environment variables
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        os.environ['BASIS_DEPLOYMENT_MODE'] = 'local'
        os.environ['BASIS_DEPLOYMENT_MACHINE'] = 'local_mac'
        os.environ['BASIS_DATA_DIR'] = '/test/data'
        os.environ['BASIS_DATA_MODE'] = 'csv'
        os.environ['BASIS_RESULTS_DIR'] = '/test/results'
        os.environ['BASIS_DEBUG'] = 'true'
        os.environ['BASIS_LOG_LEVEL'] = 'DEBUG'
        os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
        os.environ['BASIS_DATA_START_DATE'] = '2024-01-01'
        os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
        os.environ['HEALTH_CHECK_INTERVAL'] = '30s'
        os.environ['HEALTH_CHECK_ENDPOINT'] = '/health'
        os.environ['BASIS_API_PORT'] = '8001'
        os.environ['BASIS_API_HOST'] = '0.0.0.0'
        os.environ['BASIS_API_CORS_ORIGINS'] = 'http://localhost:3000,http://localhost:5173'
        
        # Create first instance
        instance1 = ConfigManager()
        
        # Create second instance
        instance2 = ConfigManager()
        
        # Should be the same instance
        assert instance1 is instance2
    
    @patch('basis_strategy_v1.infrastructure.config.config_manager.Path')
    def test_get_config_manager_function(self, mock_path):
        """Test the get_config_manager function."""
        # Mock the base directory to point to our temp directory
        mock_path.return_value.parent.parent.parent.parent.parent.parent = self.temp_path
        
        # Clear any existing instance
        ConfigManager._instance = None
        
        # Clear all environment variables first
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_') or key in ['HEALTH_CHECK_INTERVAL', 'HEALTH_CHECK_ENDPOINT']:
                del os.environ[key]
        
        # Set required environment variables
        os.environ['BASIS_ENVIRONMENT'] = 'dev'
        os.environ['BASIS_DEPLOYMENT_MODE'] = 'local'
        os.environ['BASIS_DEPLOYMENT_MACHINE'] = 'local_mac'
        os.environ['BASIS_DATA_DIR'] = '/test/data'
        os.environ['BASIS_DATA_MODE'] = 'csv'
        os.environ['BASIS_RESULTS_DIR'] = '/test/results'
        os.environ['BASIS_DEBUG'] = 'true'
        os.environ['BASIS_LOG_LEVEL'] = 'DEBUG'
        os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
        os.environ['BASIS_DATA_START_DATE'] = '2024-01-01'
        os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
        os.environ['HEALTH_CHECK_INTERVAL'] = '30s'
        os.environ['HEALTH_CHECK_ENDPOINT'] = '/health'
        os.environ['BASIS_API_PORT'] = '8001'
        os.environ['BASIS_API_HOST'] = '0.0.0.0'
        os.environ['BASIS_API_CORS_ORIGINS'] = 'http://localhost:3000,http://localhost:5173'
        
        # Get config manager
        config_manager = get_config_manager()
        
        # Should be a ConfigManager instance
        assert isinstance(config_manager, ConfigManager)
        
        # Should be singleton
        config_manager2 = get_config_manager()
        assert config_manager is config_manager2


if __name__ == "__main__":
    pytest.main([__file__])
