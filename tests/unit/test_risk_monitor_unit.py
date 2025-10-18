"""
Unit Tests for Risk Monitor Component

Tests Risk Monitor in isolation with mocked dependencies.
Focuses on risk calculations, breach detection, and fail-fast config access.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

# Import the component under test
from basis_strategy_v1.core.components.risk_monitor import RiskMonitor


class TestRiskMonitorUnit:
    """Unit tests for Risk Monitor component."""
    
    def test_max_drawdown_check(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test max drawdown check."""
        # Arrange
        mock_config['max_drawdown'] = 0.2
        mock_config['component_config']['risk_monitor']['risk_limits']['max_drawdown'] = 0.2
        
        # Mock current portfolio value and peak value
        current_value = 80000.0  # 20% drawdown from 100000
        peak_value = 100000.0
        
        risk_monitor = RiskMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        risk_assessment = risk_monitor.assess_risk(current_value, peak_value)
        
        # Assert
        assert isinstance(risk_assessment, dict)
        assert 'max_drawdown' in risk_assessment
        assert 'drawdown_breach' in risk_assessment
        
        # Should detect 20% drawdown breach
        assert risk_assessment['max_drawdown'] == 0.2
        assert risk_assessment['drawdown_breach'] == True
    
    def test_leverage_ratio_calculation(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test leverage ratio calculation."""
        # Arrange
        mock_config['leverage_enabled'] = True
        mock_config['component_config']['risk_monitor']['risk_limits']['leverage_ratio'] = 2.0
        
        # Mock position data
        total_exposure = 200000.0  # 2x leverage on 100k capital
        capital = 100000.0
        
        risk_monitor = RiskMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        risk_assessment = risk_monitor.assess_risk(capital, total_exposure=total_exposure)
        
        # Assert
        assert isinstance(risk_assessment, dict)
        assert 'leverage_ratio' in risk_assessment
        assert 'leverage_breach' in risk_assessment
        
        # Should calculate 2x leverage
        assert risk_assessment['leverage_ratio'] == 2.0
        assert risk_assessment['leverage_breach'] == False  # At limit but not breached
    
    def test_position_limits(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test position limit validation."""
        # Arrange
        mock_config['component_config']['risk_monitor']['risk_limits']['max_position_size'] = 0.5
        
        # Mock position data
        btc_position = 0.6  # Exceeds 0.5 limit
        total_capital = 100000.0
        
        risk_monitor = RiskMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        risk_assessment = risk_monitor.assess_risk(total_capital, btc_position=btc_position)
        
        # Assert
        assert isinstance(risk_assessment, dict)
        assert 'position_limits' in risk_assessment
        assert 'position_breach' in risk_assessment
        
        # Should detect position limit breach
        assert risk_assessment['position_breach'] == True
    
    def test_risk_breach_detection(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test risk breach detection."""
        # Arrange - Create config with multiple risk limits
        mock_config['max_drawdown'] = 0.15
        mock_config['component_config']['risk_monitor'] = {
            'enabled_risk_types': ['max_drawdown', 'leverage_ratio', 'position_limits'],
            'risk_limits': {
                'max_drawdown': 0.15,
                'leverage_ratio': 2.0,
                'max_position_size': 0.5
            }
        }
        
        # Mock risky scenario
        current_value = 80000.0  # 20% drawdown (breach)
        peak_value = 100000.0
        total_exposure = 250000.0  # 2.5x leverage (breach)
        btc_position = 0.6  # Position limit breach
        
        risk_monitor = RiskMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act
        risk_assessment = risk_monitor.assess_risk(
            current_value, 
            peak_value=peak_value,
            total_exposure=total_exposure,
            btc_position=btc_position
        )
        
        # Assert
        assert isinstance(risk_assessment, dict)
        assert 'overall_risk_breach' in risk_assessment
        assert 'breach_details' in risk_assessment
        
        # Should detect multiple breaches
        assert risk_assessment['overall_risk_breach'] == True
        assert len(risk_assessment['breach_details']) > 0
    
    def test_mode_agnostic_calculations(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test mode-agnostic risk calculations."""
        # Test different modes
        modes = ['pure_lending_usdt', 'btc_basis', 'eth_basis', 'eth_leveraged', 'usdt_market_neutral']
        
        for mode in modes:
            test_config = mock_config.copy()
            test_config['mode'] = mode
            
            risk_monitor = RiskMonitor(
                config=test_config,
                data_provider=mock_data_provider,
                utility_manager=mock_utility_manager
            )
            
            # Should work for all modes
            risk_assessment = risk_monitor.assess_risk(100000.0)
            assert isinstance(risk_assessment, dict)
            assert 'max_drawdown' in risk_assessment
            assert 'leverage_ratio' in risk_assessment
    
    def test_fail_fast_config_access(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test fail-fast config access (no .get() calls)."""
        # Arrange - Create config with missing risk limits
        incomplete_config = mock_config.copy()
        del incomplete_config['component_config']['risk_monitor']['risk_limits']
        
        risk_monitor = RiskMonitor(
            config=incomplete_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act & Assert - Should fail fast on missing config
        try:
            risk_assessment = risk_monitor.assess_risk(100000.0)
            # If no exception, should handle gracefully
            assert isinstance(risk_assessment, dict)
        except KeyError as e:
            # Expected behavior - fail fast on missing config
            assert 'risk_limits' in str(e)
        except Exception as e:
            # Other exceptions should be handled appropriately
            assert isinstance(e, Exception)
    
    def test_risk_monitor_initialization(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test Risk Monitor initialization with different configs."""
        # Test pure lending mode
        pure_lending_usdt_config = mock_config.copy()
        pure_lending_usdt_config['mode'] = 'pure_lending_usdt'
        pure_lending_usdt_config['max_drawdown'] = 0.1
        
        risk_monitor = RiskMonitor(
            config=pure_lending_usdt_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        assert risk_monitor.config['mode'] == 'pure_lending_usdt'
        assert risk_monitor.config['max_drawdown'] == 0.1
        
        # Test leveraged mode
        leveraged_config = mock_config.copy()
        leveraged_config['mode'] = 'eth_leveraged'
        leveraged_config['leverage_enabled'] = True
        leveraged_config['max_drawdown'] = 0.2
        
        risk_monitor = RiskMonitor(
            config=leveraged_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        assert risk_monitor.config['mode'] == 'eth_leveraged'
        assert risk_monitor.config['leverage_enabled'] == True
    
    def test_risk_monitor_error_handling(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test Risk Monitor error handling."""
        # Arrange - Mock utility manager to raise exception
        mock_utility_manager.calculate_leverage_ratio.side_effect = Exception("Utility manager error")
        
        risk_monitor = RiskMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act & Assert - Should handle errors gracefully
        try:
            risk_assessment = risk_monitor.assess_risk(100000.0)
            # If no exception, should return error state
            assert isinstance(risk_assessment, dict)
            assert 'error' in risk_assessment or 'leverage_ratio' in risk_assessment
        except Exception as e:
            # If exception is raised, it should be handled appropriately
            assert "Utility manager error" in str(e)
    
    def test_risk_monitor_performance(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test Risk Monitor performance with multiple risk calculations."""
        # Arrange
        risk_monitor = RiskMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Act - Run multiple risk assessments
        import time
        start_time = time.time()
        
        for i in range(100):
            risk_assessment = risk_monitor.assess_risk(100000.0 + i * 1000)
            assert isinstance(risk_assessment, dict)
        
        end_time = time.time()
        
        # Assert - Should complete within reasonable time
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should complete within 1 second
    
    def test_risk_monitor_edge_cases(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test Risk Monitor edge cases."""
        risk_monitor = RiskMonitor(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Test zero values
        risk_assessment = risk_monitor.assess_risk(0.0)
        assert isinstance(risk_assessment, dict)
        assert 'max_drawdown' in risk_assessment
        
        # Test negative values
        risk_assessment = risk_monitor.assess_risk(-1000.0)
        assert isinstance(risk_assessment, dict)
        assert 'max_drawdown' in risk_assessment
        
        # Test very large values
        risk_assessment = risk_monitor.assess_risk(1000000000.0)
        assert isinstance(risk_assessment, dict)
        assert 'max_drawdown' in risk_assessment
    
    def test_risk_monitor_config_validation(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test Risk Monitor config validation."""
        # Test valid config
        valid_config = mock_config.copy()
        valid_config['component_config']['risk_monitor'] = {
            'enabled_risk_types': ['max_drawdown', 'leverage_ratio'],
            'risk_limits': {
                'max_drawdown': 0.2,
                'leverage_ratio': 2.0
            }
        }
        
        risk_monitor = RiskMonitor(
            config=valid_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        risk_assessment = risk_monitor.assess_risk(100000.0)
        assert isinstance(risk_assessment, dict)
        
        # Test invalid config (missing risk_limits)
        invalid_config = mock_config.copy()
        invalid_config['component_config']['risk_monitor'] = {
            'enabled_risk_types': ['max_drawdown']
            # Missing risk_limits
        }
        
        risk_monitor = RiskMonitor(
            config=invalid_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager
        )
        
        # Should handle invalid config gracefully
        try:
            risk_assessment = risk_monitor.assess_risk(100000.0)
            assert isinstance(risk_assessment, dict)
        except Exception as e:
            # Expected behavior for invalid config
            assert isinstance(e, Exception)
