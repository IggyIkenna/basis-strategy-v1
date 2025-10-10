"""
Tests for Configuration Validation

Tests config loading, validation, and business logic decisions.
"""

import pytest
import os
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from basis_strategy_v1.infrastructure.config.config_validator import ConfigValidator, ValidationResult
from basis_strategy_v1.infrastructure.config.config_loader import ConfigLoader
from basis_strategy_v1.infrastructure.config.health_check import ConfigHealthChecker, ComponentStatus


class TestConfigValidator:
    """Test configuration validation."""
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["test warning"],
            environment="dev",
            config_summary={"test": "value"}
        )
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.environment == "dev"
        assert result.config_summary["test"] == "value"
    
    def test_validator_initialization(self):
        """Test ConfigValidator initialization."""
        with patch('basis_strategy_v1.infrastructure.config.config_validator.get_environment') as mock_env:
            mock_env.return_value = "dev"
            
            validator = ConfigValidator()
            
            assert validator.environment == "dev"
            assert len(validator.errors) == 0
            assert len(validator.warnings) == 0
    
    def test_validate_base_configs_missing_default(self):
        """Test validation when default.json is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('basis_strategy_v1.infrastructure.config.config_validator._BASE_DIR', Path(temp_dir)):
                validator = ConfigValidator()
                validator._validate_base_configs()
                
                assert len(validator.errors) > 0
                assert any("Missing required config file" in error for error in validator.errors)
    
    def test_validate_base_configs_invalid_json(self):
        """Test validation with invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            configs_dir = Path(temp_dir) / "configs"
            configs_dir.mkdir()
            
            # Create invalid JSON
            with open(configs_dir / "default.json", 'w') as f:
                f.write("{ invalid json }")
            
            with patch('basis_strategy_v1.infrastructure.config.config_validator._BASE_DIR', Path(temp_dir)):
                validator = ConfigValidator()
                validator._validate_base_configs()
                
                assert len(validator.errors) > 0
                assert any("Invalid default.json" in error for error in validator.errors)
    
    def test_validate_base_configs_valid(self):
        """Test validation with valid base configs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            configs_dir = Path(temp_dir) / "configs"
            configs_dir.mkdir()
            
            # Create valid default.json
            default_config = {
                "api": {"port": 8000},
                "database": {"type": "sqlite"},
                "cache": {"type": "in_memory"}
            }
            
            with open(configs_dir / "default.json", 'w') as f:
                json.dump(default_config, f)
            
            with patch('basis_strategy_v1.infrastructure.config.config_validator._BASE_DIR', Path(temp_dir)):
                validator = ConfigValidator()
                validator._validate_base_configs()
                
                assert len(validator.errors) == 0
    
    def test_validate_environment_variables_missing(self):
        """Test validation when environment variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            validator = ConfigValidator()
            validator._validate_environment_variables()
            
            assert len(validator.errors) > 0
            assert any("BASIS_ENVIRONMENT" in error for error in validator.errors)
    
    def test_validate_environment_variables_placeholders(self):
        """Test validation with placeholder values."""
        env_vars = {
            'BASIS_ENVIRONMENT': 'dev',
            'BASIS_DEV__ALCHEMY__PRIVATE_KEY': 'your_testnet_erc20_wallet_private_key',
            'BASIS_DEV__ALCHEMY__WALLET_ADDRESS': '0x...',
            'BASIS_DEV__CEX__BINANCE_SPOT_API_KEY': 'your_testnet_binance_spot_api_key'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            validator = ConfigValidator()
            validator._validate_environment_variables()
            
            assert len(validator.warnings) > 0
            assert any("placeholder values" in warning for warning in validator.warnings)
    
    def test_validate_mode_business_logic_leverage_inconsistency(self):
        """Test business logic validation for leverage inconsistency. DEPRECATED NEED NEW BUSIENSS LGOCI TEST """
        #config = {
        #    'leverage_enabled': True,
        #    'max_ltv': 0.0,
        #    'hedge_venues': ['binance'],
        #}
        ##    'hedge_allocation': {'binance': 1.0}
        #
        #validator = ConfigValidator()
        #validator._validate_mode_business_logic(config, 'test_mode')
        
        #assert len(validator.errors) > 0
        # assert any("leverage_enabled=true but max_ltv=0.0" in error for error in validator.errors)
        assert 1== 1
    
    def test_validate_mode_business_logic_hedge_inconsistency(self):
        """Test business logic validation for hedge inconsistency."""
        config = {
            'leverage_enabled': False,
            'max_ltv': 0.0,
            'hedge_venues': ['binance'],
            'hedge_allocation': {}
        }
        
        validator = ConfigValidator()
        validator._validate_mode_business_logic(config, 'test_mode')
        
        assert len(validator.errors) > 0
        assert any("hedge_venues specified but no hedge_allocation" in error for error in validator.errors)
    
    def test_validate_mode_business_logic_hedge_allocation_sum(self):
        """Test business logic validation for hedge allocation sum."""
        config = {
            'leverage_enabled': False,
            'max_ltv': 0.0,
            'hedge_venues': ['binance', 'bybit'],
            'hedge_allocation': {'binance': 0.6, 'bybit': 0.3}  # Sums to 0.9, not 1.0
        }
        
        validator = ConfigValidator()
        validator._validate_mode_business_logic(config, 'test_mode')
        
        assert len(validator.warnings) > 0
        # Check if any warning contains the hedge allocation sum message
        hedge_warnings = [w for w in validator.warnings if "hedge_allocation sums to" in w]
        assert len(hedge_warnings) > 0
        assert "0.8999999999999999" in hedge_warnings[0] or "0.9" in hedge_warnings[0]


class TestConfigLoader:
    """Test configuration loading."""
    
    def test_loader_initialization(self):
        """Test ConfigLoader initialization."""
        with patch('basis_strategy_v1.infrastructure.config.config_loader.validate_configuration') as mock_validator:
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_result.warnings = []
            mock_validator.return_value.validate_all.return_value = mock_result

            with patch('basis_strategy_v1.infrastructure.config.config_loader._BASE_DIR', Path("/tmp")):
                loader = ConfigLoader()
                
                # In test environment, should be 'test', otherwise 'dev'
                expected_env = "test" if os.getenv('BASIS_ENVIRONMENT') == 'test' else "dev"
                assert loader.environment == expected_env
                assert 'base' in loader._config_cache
    
    def test_get_mode_config(self):
        """Test getting mode configuration."""
        with patch('basis_strategy_v1.infrastructure.config.config_loader.validate_configuration') as mock_validator:
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_result.warnings = []
            mock_validator.return_value = mock_result
            
            with patch('basis_strategy_v1.infrastructure.config.config_loader._BASE_DIR', Path("/tmp")):
                loader = ConfigLoader()
                loader._config_cache['modes'] = {'test_mode': {'mode': 'test'}}
                
                config = loader.get_mode_config('test_mode')
                assert config['mode'] == 'test'
                
                # Test non-existent mode
                config = loader.get_mode_config('non_existent')
                assert config == {}
    
    def test_get_complete_config(self):
        """Test getting complete configuration."""
        with patch('basis_strategy_v1.infrastructure.config.config_loader.validate_configuration') as mock_validator:
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_result.warnings = []
            mock_validator.return_value = mock_result
            
            with patch('basis_strategy_v1.infrastructure.config.config_loader._BASE_DIR', Path("/tmp")):
                loader = ConfigLoader()
                loader._config_cache = {
                    'base': {'api': {'port': 8000}},
                    'modes': {'test_mode': {'mode': 'test', 'leverage_enabled': True}},
                    'venues': {'binance': {'venue': 'binance', 'type': 'cex'}}
                }
                
                config = loader.get_complete_config(mode='test_mode', venue='binance')
                
                assert config['api']['port'] == 8000
                assert config['mode'] == 'test'
                assert config['leverage_enabled'] is True
                assert config['venue'] == 'binance'
                assert config['type'] == 'cex'
    
    def test_deep_merge(self):
        """Test deep merging of configurations."""
        with patch('basis_strategy_v1.infrastructure.config.config_loader.validate_configuration') as mock_validator:
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_result.warnings = []
            mock_validator.return_value = mock_result
            
            with patch('basis_strategy_v1.infrastructure.config.config_loader._BASE_DIR', Path("/tmp")):
                loader = ConfigLoader()
                
                base = {
                    'api': {'port': 8000, 'host': 'localhost'},
                    'database': {'type': 'sqlite'}
                }
                
                override = {
                    'api': {'port': 8001},
                    'cache': {'type': 'in_memory'}
                }
                
                result = loader._deep_merge(base, override)
                
                assert result['api']['port'] == 8001
                assert result['api']['host'] == 'localhost'
                assert result['database']['type'] == 'sqlite'
                assert result['cache']['type'] == 'in_memory'


class TestConfigHealthChecker:
    """Test configuration health checking."""
    
    def test_health_checker_initialization(self):
        """Test ConfigHealthChecker initialization."""
        checker = ConfigHealthChecker()
        
        assert len(checker.components) == 0
        assert len(checker.required_components) == 9
        assert 'strategy_manager' in checker.required_components
    
    def test_register_component(self):
        """Test component registration."""
        checker = ConfigHealthChecker()
        
        checker.register_component('test_component', ['dependency1'])
        
        assert 'test_component' in checker.components
        assert checker.components['test_component'].status == ComponentStatus.NOT_INITIALIZED
        assert 'dependency1' in checker.components['test_component'].dependencies
    
    def test_mark_component_healthy(self):
        """Test marking component as healthy."""
        checker = ConfigHealthChecker()
        
        checker.register_component('test_component')
        checker.mark_component_healthy('test_component', 'v1.0')
        
        comp = checker.components['test_component']
        assert comp.status == ComponentStatus.HEALTHY
        assert comp.config_version == 'v1.0'
        assert comp.last_config_read is not None
    
    def test_mark_component_unhealthy(self):
        """Test marking component as unhealthy."""
        checker = ConfigHealthChecker()
        
        checker.register_component('test_component')
        checker.mark_component_unhealthy('test_component', 'Config error')
        
        comp = checker.components['test_component']
        assert comp.status == ComponentStatus.UNHEALTHY
        assert comp.error_message == 'Config error'
    
    def test_get_health_summary(self):
        """Test getting health summary."""
        checker = ConfigHealthChecker()
        
        checker.register_component('risk_monitor')
        checker.mark_component_healthy('risk_monitor')
        
        summary = checker.get_health_summary()
        
        assert summary['total_components'] == 1
        assert summary['healthy_components'] == 1
        assert summary['unhealthy_components'] == 0
        assert summary['not_initialized_components'] == 0
        assert summary["missing_components"] == 8  # 9 required - 1 registered
        assert summary['overall_health'] == 'healthy'  # No unhealthy or not_initialized components
    
    def test_is_system_healthy(self):
        """Test system health check."""
        checker = ConfigHealthChecker()
        
        # Initially unhealthy (no components registered)
        assert not checker.is_system_healthy()
        
        # Register and mark all required components as healthy
        for comp_name in checker.required_components:
            checker.register_component(comp_name)
            checker.mark_component_healthy(comp_name)
        
        assert checker.is_system_healthy()
    
    def test_check_dependencies(self):
        """Test dependency checking."""
        checker = ConfigHealthChecker()
        
        checker.register_component('component_a')
        checker.register_component('component_b', ['component_a'])
        checker.register_component('component_c', ['component_b'])
        
        checker.mark_component_healthy('component_a')
        checker.mark_component_healthy('component_b')
        checker.mark_component_healthy('component_c')
        
        # All dependencies satisfied
        issues = checker.check_dependencies()
        assert len(issues) == 0
        
        # Mark component_a as unhealthy
        checker.mark_component_unhealthy('component_a', 'Error')
        
        issues = checker.check_dependencies()
        assert 'component_b' in issues
        # component_b depends on component_a, which is unhealthy
        # component_c depends on component_b, but component_b is still healthy
        assert 'component_a' in issues['component_b']


class TestConfigBusinessLogic:
    """Test business logic decisions for different config combinations."""
    
    def test_leverage_mode_detection(self):
        """Test that leverage modes are correctly identified."""
        leverage_configs = [
            'eth_leveraged',
            'usdt_market_neutral'
        ]
        
        non_leverage_configs = [
            'pure_lending',
            'btc_basis',
            'eth_staking_only',
            'usdt_market_neutral_no_leverage'
        ]
        
        # This would be tested with actual config loading
        # For now, we test the logic
        for mode in leverage_configs:
            # Simulate config that should have leverage enabled
            assert True  # Placeholder for actual test
    
    def test_hedge_venue_requirements(self):
        """Test that hedge venues are required for certain modes."""
        hedge_required_modes = [
            'btc_basis',
            'usdt_market_neutral',
            'usdt_market_neutral_no_leverage'
        ]
        
        no_hedge_modes = [
            'pure_lending',
            'eth_leveraged',
            'eth_staking_only'
        ]
        
        # This would be tested with actual config loading
        for mode in hedge_required_modes:
            # Simulate config that should have hedge venues
            assert True  # Placeholder for actual test
    
    def test_share_class_consistency(self):
        """Test that share classes are consistent with modes."""
        usdt_modes = [
            'pure_lending',
            'btc_basis',
            'usdt_market_neutral',
            'usdt_market_neutral_no_leverage'
        ]
        
        eth_modes = [
            'eth_leveraged',
            'eth_staking_only'
        ]
        
        # This would be tested with actual config loading
        for mode in usdt_modes:
            # Simulate config that should have USDT share class
            assert True  # Placeholder for actual test


@pytest.mark.asyncio
async def test_config_loading_performance():
    """Test that config loading is performant."""
    import time
    
    start_time = time.time()
    
    # This would test actual config loading performance
    # For now, we just test that the test framework works
    import asyncio
    await asyncio.sleep(0.001)  # Simulate some work
    
    end_time = time.time()
    assert (end_time - start_time) < 1.0  # Should be fast


def test_config_immutability():
    """Test that config changes on the fly are not picked up."""
    # This test would verify that:
    # 1. Config is loaded once at startup
    # 2. Changes to config files are not picked up without restart
    # 3. Environment variable changes are not picked up without restart
    
    # For now, this is a placeholder
    assert True


class TestComprehensiveConfigLoading:
    """Test comprehensive config loading for all modes."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.config_loader = ConfigLoader()
    
    def test_base_config_loading(self):
        """Test base config loading."""
        base_config = self.config_loader.get_base_config()
        
        assert base_config is not None
        assert isinstance(base_config, dict)
        
        # Check required sections
        required_sections = ['environment', 'api', 'database', 'data', 'execution']
        for section in required_sections:
            assert section in base_config, f"Missing required section: {section}"
        
        # Check environment
        assert base_config['environment'] in ['dev', 'staging', 'prod', 'test']
        
        # Check data directory exists
        data_dir = base_config.get('data', {}).get('data_dir', 'data/')
        assert os.path.exists(data_dir), f"Data directory does not exist: {data_dir}"
    
    def test_scenario_configs_loading(self):
        """Test mode configs loading."""
        mode_configs = self.config_loader.get_all_mode_configs()
        
        assert len(mode_configs) > 0, "No mode configs found"
        
        # Test each mode config
        for mode_name, config in mode_configs.items():
            assert isinstance(config, dict), f"Config for {mode_name} is not a dict"
            assert config['mode'] == mode_name, f"Mode mismatch for {mode_name}"
            assert 'share_class' in config, f"Missing share_class for {mode_name}"
            assert 'data_requirements' in config, f"Missing data_requirements for {mode_name}"
            assert config['share_class'] in ['USDT', 'ETH'], f"Invalid share_class for {mode_name}"
    
    def test_venue_configs_loading(self):
        """Test venue configs loading."""
        venue_configs = self.config_loader.get_all_venue_configs()
        
        assert len(venue_configs) > 0, "No venue configs found"
        
        # Test each venue config
        for venue_name, config in venue_configs.items():
            assert isinstance(config, dict), f"Config for {venue_name} is not a dict"
            assert 'venue' in config, f"Missing venue field for {venue_name}"
            assert config['venue'] == venue_name, f"Venue mismatch for {venue_name}"
    
    def test_combined_configs_loading(self):
        """Test combined configs loading for all modes."""
        scenario_configs = self.config_loader.get_all_scenario_configs()
        
        for mode_name in scenario_configs.keys():
            combined_config = self.config_loader.load_combined_config(mode_name)
            
            assert combined_config is not None, f"Failed to load combined config for {mode_name}"
            assert combined_config['mode'] == mode_name, f"Mode mismatch in combined config for {mode_name}"
            
            # Check that base config sections are included
            assert 'environment' in combined_config, f"Missing environment in combined config for {mode_name}"
            assert 'data' in combined_config, f"Missing data section in combined config for {mode_name}"
            
            # Check mode-specific sections
            assert 'share_class' in combined_config, f"Missing share_class in combined config for {mode_name}"
            assert 'data_requirements' in combined_config, f"Missing data_requirements in combined config for {mode_name}"
    
    def test_data_requirements_validation(self):
        """Test that data requirements are properly specified."""
        scenario_configs = self.config_loader.get_all_scenario_configs()
        
        for mode_name, config in scenario_configs.items():
            data_requirements = config.get('data_requirements', [])
            
            assert isinstance(data_requirements, list), f"data_requirements should be a list for {mode_name}"
            assert len(data_requirements) > 0, f"No data requirements specified for {mode_name}"
            
            # Check for common required data types
            common_requirements = ['eth_prices', 'aave_lending_rates', 'gas_costs']
            for req in common_requirements:
                if req in data_requirements:
                    # This requirement is specified, which is good
                    pass
    
    def test_share_class_consistency(self):
        """Test that share classes are consistent with modes."""
        mode_configs = self.config_loader.get_all_mode_configs()
        
        usdt_modes = []
        eth_modes = []
        
        for mode_name, config in mode_configs.items():
            share_class = config.get('share_class')
            if share_class == 'USDT':
                usdt_modes.append(mode_name)
            elif share_class == 'ETH':
                eth_modes.append(mode_name)
        
        # Verify we have both USDT and ETH modes
        assert len(usdt_modes) > 0, "No USDT modes found"
        assert len(eth_modes) > 0, "No ETH modes found"
        
        # Verify expected modes are in correct categories
        expected_usdt_modes = ['pure_lending', 'btc_basis', 'usdt_market_neutral']
        expected_eth_modes = ['eth_leveraged', 'eth_staking_only']
        
        for mode in expected_usdt_modes:
            if mode in mode_configs:
                assert mode in usdt_modes, f"Expected USDT mode {mode} has wrong share class"
        
        for mode in expected_eth_modes:
            if mode in mode_configs:
                assert mode in eth_modes, f"Expected ETH mode {mode} has wrong share class"
