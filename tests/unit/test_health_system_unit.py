"""
Unit tests for Health System component.

Tests health monitoring functionality in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta


class TestHealthSystem:
    """Test Health System component in isolation."""
    
    def test_health_system_initialization(self, mock_config, mock_data_provider):
        """Test health system initializes correctly with config and data provider."""
        from backend.src.basis_strategy_v1.infrastructure.health.health_system import HealthSystem
        
        health_system = HealthSystem(config=mock_config, data_provider=mock_data_provider)
        
        assert health_system.config == mock_config
        assert health_system.data_provider == mock_data_provider
        assert health_system.check_interval == mock_config.get('health_check_interval', 30)
    
    def test_register_component(self, mock_config, mock_data_provider):
        """Test registering components for health monitoring."""
        from backend.src.basis_strategy_v1.infrastructure.health.health_system import HealthSystem
        
        health_system = HealthSystem(config=mock_config, data_provider=mock_data_provider)
        
        mock_component = Mock()
        mock_component.name = "position_monitor"
        mock_component.health_check.return_value = {"status": "healthy", "uptime": 3600}
        
        health_system.register_component(mock_component)
        
        assert "position_monitor" in health_system.components
        assert health_system.components["position_monitor"] == mock_component
    
    def test_get_overall_health_status(self, mock_config, mock_data_provider):
        """Test getting overall system health status."""
        from backend.src.basis_strategy_v1.infrastructure.health.health_system import HealthSystem
        
        health_system = HealthSystem(config=mock_config, data_provider=mock_data_provider)
        
        # Register healthy components
        mock_component1 = Mock()
        mock_component1.name = "position_monitor"
        mock_component1.health_check.return_value = {"status": "healthy", "uptime": 3600}
        
        mock_component2 = Mock()
        mock_component2.name = "risk_monitor"
        mock_component2.health_check.return_value = {"status": "healthy", "uptime": 3600}
        
        health_system.register_component(mock_component1)
        health_system.register_component(mock_component2)
        
        overall_status = health_system.get_overall_health_status()
        
        assert overall_status["status"] == "healthy"
        assert overall_status["total_components"] == 2
        assert overall_status["healthy_components"] == 2
        assert overall_status["unhealthy_components"] == 0
    
    def test_get_detailed_health_status(self, mock_config, mock_data_provider):
        """Test getting detailed health status for all components."""
        from backend.src.basis_strategy_v1.infrastructure.health.health_system import HealthSystem
        
        health_system = HealthSystem(config=mock_config, data_provider=mock_data_provider)
        
        # Register components with different health statuses
        mock_component1 = Mock()
        mock_component1.name = "position_monitor"
        mock_component1.health_check.return_value = {
            "status": "healthy",
            "uptime": 3600,
            "memory_usage": 0.75,
            "last_check": datetime.now().isoformat()
        }
        
        mock_component2 = Mock()
        mock_component2.name = "risk_monitor"
        mock_component2.health_check.return_value = {
            "status": "degraded",
            "uptime": 1800,
            "memory_usage": 0.95,
            "last_check": datetime.now().isoformat(),
            "warning": "High memory usage"
        }
        
        health_system.register_component(mock_component1)
        health_system.register_component(mock_component2)
        
        detailed_status = health_system.get_detailed_health_status()
        
        assert "position_monitor" in detailed_status["components"]
        assert "risk_monitor" in detailed_status["components"]
        assert detailed_status["components"]["position_monitor"]["status"] == "healthy"
        assert detailed_status["components"]["risk_monitor"]["status"] == "degraded"
        assert detailed_status["components"]["risk_monitor"]["warning"] == "High memory usage"
    
    def test_health_check_failure_handling(self, mock_config, mock_data_provider):
        """Test handling of component health check failures."""
        from backend.src.basis_strategy_v1.infrastructure.health.health_system import HealthSystem
        
        health_system = HealthSystem(config=mock_config, data_provider=mock_data_provider)
        
        # Register component that raises exception during health check
        mock_component = Mock()
        mock_component.name = "failing_component"
        mock_component.health_check.side_effect = Exception("Health check failed")
        
        health_system.register_component(mock_component)
        
        overall_status = health_system.get_overall_health_status()
        
        assert overall_status["status"] == "unhealthy"
        assert overall_status["total_components"] == 1
        assert overall_status["healthy_components"] == 0
        assert overall_status["unhealthy_components"] == 1
    
    def test_health_metrics_collection(self, mock_config, mock_data_provider):
        """Test collecting health metrics from components."""
        from backend.src.basis_strategy_v1.infrastructure.health.health_system import HealthSystem
        
        health_system = HealthSystem(config=mock_config, data_provider=mock_data_provider)
        
        mock_component = Mock()
        mock_component.name = "metrics_component"
        mock_component.health_check.return_value = {
            "status": "healthy",
            "metrics": {
                "cpu_usage": 0.25,
                "memory_usage": 0.60,
                "disk_usage": 0.40,
                "network_latency_ms": 15.5
            }
        }
        
        health_system.register_component(mock_component)
        
        metrics = health_system.collect_health_metrics()
        
        assert "metrics_component" in metrics
        assert metrics["metrics_component"]["cpu_usage"] == 0.25
        assert metrics["metrics_component"]["memory_usage"] == 0.60
        assert metrics["metrics_component"]["disk_usage"] == 0.40
        assert metrics["metrics_component"]["network_latency_ms"] == 15.5
    
    def test_health_status_caching(self, mock_config, mock_data_provider):
        """Test health status caching to avoid excessive checks."""
        from backend.src.basis_strategy_v1.infrastructure.health.health_system import HealthSystem
        
        health_system = HealthSystem(config=mock_config, data_provider=mock_data_provider)
        health_system.cache_duration = timedelta(seconds=5)
        
        mock_component = Mock()
        mock_component.name = "cached_component"
        mock_component.health_check.return_value = {"status": "healthy"}
        
        health_system.register_component(mock_component)
        
        # First call should trigger health check
        status1 = health_system.get_overall_health_status()
        assert mock_component.health_check.call_count == 1
        
        # Second call within cache duration should use cached result
        status2 = health_system.get_overall_health_status()
        assert mock_component.health_check.call_count == 1  # No additional calls
        
        assert status1 == status2
    
    def test_health_alert_thresholds(self, mock_config, mock_data_provider):
        """Test health alert thresholds and notifications."""
        from backend.src.basis_strategy_v1.infrastructure.health.health_system import HealthSystem
        
        health_system = HealthSystem(config=mock_config, data_provider=mock_data_provider)
        health_system.alert_thresholds = {
            "memory_usage": 0.90,
            "cpu_usage": 0.80,
            "disk_usage": 0.85
        }
        
        mock_component = Mock()
        mock_component.name = "alert_component"
        mock_component.health_check.return_value = {
            "status": "healthy",
            "metrics": {
                "memory_usage": 0.95,  # Above threshold
                "cpu_usage": 0.75,     # Below threshold
                "disk_usage": 0.90     # Above threshold
            }
        }
        
        health_system.register_component(mock_component)
        
        with patch('backend.src.basis_strategy_v1.infrastructure.health.health_system.logger') as mock_logger:
            health_system.check_alert_thresholds()
            
            # Should log alerts for memory_usage and disk_usage
            assert mock_logger.warning.call_count == 2
            warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
            assert any("memory_usage" in call for call in warning_calls)
            assert any("disk_usage" in call for call in warning_calls)
