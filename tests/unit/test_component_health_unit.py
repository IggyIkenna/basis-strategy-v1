"""
Unit tests for Component Health.

Tests the component health system in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from basis_strategy_v1.core.health.component_health import (
    ComponentHealthChecker, 
    HealthStatus, 
    ComponentHealthReport
)


class TestHealthStatus:
    """Test HealthStatus enumeration."""
    
    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.NOT_READY.value == "not_ready"
        assert HealthStatus.UNKNOWN.value == "unknown"
        assert HealthStatus.NOT_CONFIGURED.value == "not_configured"


class TestComponentHealthReport:
    """Test ComponentHealthReport dataclass."""
    
    def test_initialization(self):
        """Test ComponentHealthReport initialization."""
        report = ComponentHealthReport(
            component_name='test_component',
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(timezone.utc)
        )
        
        assert report.component_name == 'test_component'
        assert report.status == HealthStatus.HEALTHY
        assert isinstance(report.timestamp, datetime)
        assert report.error_code is None
        assert report.error_message is None
        assert report.readiness_checks == {}
        assert report.metrics == {}
        assert report.dependencies == []
    
    def test_initialization_with_all_fields(self):
        """Test ComponentHealthReport initialization with all fields."""
        timestamp = datetime.now(timezone.utc)
        report = ComponentHealthReport(
            component_name='test_component',
            status=HealthStatus.UNHEALTHY,
            timestamp=timestamp,
            error_code='TEST-001',
            error_message='Test error',
            readiness_checks={'check1': True, 'check2': False},
            metrics={'cpu_usage': 0.5, 'memory_usage': 0.7},
            dependencies=['dep1', 'dep2']
        )
        
        assert report.component_name == 'test_component'
        assert report.status == HealthStatus.UNHEALTHY
        assert report.timestamp == timestamp
        assert report.error_code == 'TEST-001'
        assert report.error_message == 'Test error'
        assert report.readiness_checks == {'check1': True, 'check2': False}
        assert report.metrics == {'cpu_usage': 0.5, 'memory_usage': 0.7}
        assert report.dependencies == ['dep1', 'dep2']
    
    def test_to_dict(self):
        """Test ComponentHealthReport to_dict method."""
        timestamp = datetime.now(timezone.utc)
        report = ComponentHealthReport(
            component_name='test_component',
            status=HealthStatus.HEALTHY,
            timestamp=timestamp,
            metrics={'cpu_usage': 0.5}
        )
        
        report_dict = report.to_dict()
        
        assert report_dict['component_name'] == 'test_component'
        assert report_dict['status'] == 'healthy'
        assert report_dict['timestamp'] == timestamp.isoformat()
        assert report_dict['metrics'] == {'cpu_usage': 0.5}
    
    def test_is_healthy(self):
        """Test ComponentHealthReport is_healthy property."""
        healthy_report = ComponentHealthReport(
            component_name='test_component',
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(timezone.utc)
        )
        
        unhealthy_report = ComponentHealthReport(
            component_name='test_component',
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.now(timezone.utc)
        )
        
        assert healthy_report.is_healthy is True
        assert unhealthy_report.is_healthy is False
    
    def test_is_ready(self):
        """Test ComponentHealthReport is_ready property."""
        ready_report = ComponentHealthReport(
            component_name='test_component',
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(timezone.utc),
            readiness_checks={'check1': True, 'check2': True}
        )
        
        not_ready_report = ComponentHealthReport(
            component_name='test_component',
            status=HealthStatus.NOT_READY,
            timestamp=datetime.now(timezone.utc),
            readiness_checks={'check1': True, 'check2': False}
        )
        
        assert ready_report.is_ready is True
        assert not_ready_report.is_ready is False


class TestComponentHealthChecker:
    """Test ComponentHealthChecker component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for component health checker."""
        return {
            'health_check_interval': 30,
            'timeout': 10,
            'max_retries': 3
        }
    
    @pytest.fixture
    def mock_health_checker(self, mock_config):
        """Create component health checker with mocked dependencies."""
        checker = ComponentHealthChecker('test_component')
        return checker
    
    def test_initialization(self, mock_config):
        """Test ComponentHealthChecker initialization."""
        checker = ComponentHealthChecker('test_component')
        
        assert checker.component_name == 'test_component'
        assert checker.last_health_check is None
    
    def test_register_component(self, mock_health_checker):
        """Test component registration."""
        mock_component = Mock()
        mock_component.name = 'test_component'
        mock_component.health_check = Mock(return_value={'status': 'healthy'})
        
        mock_health_checker.register_component(mock_component)
        
        assert 'test_component' in mock_health_checker.registered_components
        assert mock_health_checker.registered_components['test_component'] == mock_component
    
    def test_unregister_component(self, mock_health_checker):
        """Test component unregistration."""
        mock_component = Mock()
        mock_component.name = 'test_component'
        
        mock_health_checker.register_component(mock_component)
        assert 'test_component' in mock_health_checker.registered_components
        
        mock_health_checker.unregister_component('test_component')
        assert 'test_component' not in mock_health_checker.registered_components
    
    def test_check_component_health_healthy(self, mock_health_checker):
        """Test health check for healthy component."""
        mock_component = Mock()
        mock_component.name = 'test_component'
        mock_component.health_check.return_value = {
            'status': 'healthy',
            'metrics': {'cpu_usage': 0.5}
        }
        
        mock_health_checker.register_component(mock_component)
        
        report = mock_health_checker.check_component_health('test_component')
        
        assert report.component_name == 'test_component'
        assert report.status == HealthStatus.HEALTHY
        assert report.metrics == {'cpu_usage': 0.5}
        assert report.is_healthy is True
    
    def test_check_component_health_unhealthy(self, mock_health_checker):
        """Test health check for unhealthy component."""
        mock_component = Mock()
        mock_component.name = 'test_component'
        mock_component.health_check.return_value = {
            'status': 'unhealthy',
            'error_code': 'TEST-001',
            'error_message': 'Test error'
        }
        
        mock_health_checker.register_component(mock_component)
        
        report = mock_health_checker.check_component_health('test_component')
        
        assert report.component_name == 'test_component'
        assert report.status == HealthStatus.UNHEALTHY
        assert report.error_code == 'TEST-001'
        assert report.error_message == 'Test error'
        assert report.is_healthy is False
    
    def test_check_component_health_not_ready(self, mock_health_checker):
        """Test health check for not ready component."""
        mock_component = Mock()
        mock_component.name = 'test_component'
        mock_component.health_check.return_value = {
            'status': 'not_ready',
            'readiness_checks': {'check1': True, 'check2': False}
        }
        
        mock_health_checker.register_component(mock_component)
        
        report = mock_health_checker.check_component_health('test_component')
        
        assert report.component_name == 'test_component'
        assert report.status == HealthStatus.NOT_READY
        assert report.readiness_checks == {'check1': True, 'check2': False}
        assert report.is_ready is False
    
    def test_check_component_health_component_not_found(self, mock_health_checker):
        """Test health check for non-existent component."""
        report = mock_health_checker.check_component_health('non_existent_component')
        
        assert report.component_name == 'non_existent_component'
        assert report.status == HealthStatus.UNKNOWN
        assert report.error_message == 'Component not found'
    
    def test_check_component_health_exception(self, mock_health_checker):
        """Test health check when component raises exception."""
        mock_component = Mock()
        mock_component.name = 'test_component'
        mock_component.health_check.side_effect = Exception("Health check failed")
        
        mock_health_checker.register_component(mock_component)
        
        report = mock_health_checker.check_component_health('test_component')
        
        assert report.component_name == 'test_component'
        assert report.status == HealthStatus.UNHEALTHY
        assert 'Health check failed' in report.error_message
    
    def test_check_all_components(self, mock_health_checker):
        """Test health check for all registered components."""
        # Register multiple components
        mock_component1 = Mock()
        mock_component1.name = 'component1'
        mock_component1.health_check.return_value = {'status': 'healthy'}
        
        mock_component2 = Mock()
        mock_component2.name = 'component2'
        mock_component2.health_check.return_value = {'status': 'unhealthy', 'error_code': 'TEST-002'}
        
        mock_health_checker.register_component(mock_component1)
        mock_health_checker.register_component(mock_component2)
        
        reports = mock_health_checker.check_all_components()
        
        assert len(reports) == 2
        assert any(r.component_name == 'component1' and r.status == HealthStatus.HEALTHY for r in reports)
        assert any(r.component_name == 'component2' and r.status == HealthStatus.UNHEALTHY for r in reports)
    
    def test_get_system_health_summary(self, mock_health_checker):
        """Test system health summary generation."""
        # Register components with different health statuses
        mock_component1 = Mock()
        mock_component1.name = 'component1'
        mock_component1.health_check.return_value = {'status': 'healthy'}
        
        mock_component2 = Mock()
        mock_component2.name = 'component2'
        mock_component2.health_check.return_value = {'status': 'unhealthy'}
        
        mock_health_checker.register_component(mock_component1)
        mock_health_checker.register_component(mock_component2)
        
        summary = mock_health_checker.get_system_health_summary()
        
        assert summary['total_components'] == 2
        assert summary['healthy_components'] == 1
        assert summary['unhealthy_components'] == 1
        assert summary['overall_status'] == 'degraded'
        assert len(summary['component_reports']) == 2
    
    def test_get_system_health_summary_all_healthy(self, mock_health_checker):
        """Test system health summary when all components are healthy."""
        # Register only healthy components
        mock_component1 = Mock()
        mock_component1.name = 'component1'
        mock_component1.health_check.return_value = {'status': 'healthy'}
        
        mock_component2 = Mock()
        mock_component2.name = 'component2'
        mock_component2.health_check.return_value = {'status': 'healthy'}
        
        mock_health_checker.register_component(mock_component1)
        mock_health_checker.register_component(mock_component2)
        
        summary = mock_health_checker.get_system_health_summary()
        
        assert summary['total_components'] == 2
        assert summary['healthy_components'] == 2
        assert summary['unhealthy_components'] == 0
        assert summary['overall_status'] == 'healthy'
    
    def test_get_system_health_summary_all_unhealthy(self, mock_health_checker):
        """Test system health summary when all components are unhealthy."""
        # Register only unhealthy components
        mock_component1 = Mock()
        mock_component1.name = 'component1'
        mock_component1.health_check.return_value = {'status': 'unhealthy'}
        
        mock_component2 = Mock()
        mock_component2.name = 'component2'
        mock_component2.health_check.return_value = {'status': 'unhealthy'}
        
        mock_health_checker.register_component(mock_component1)
        mock_health_checker.register_component(mock_component2)
        
        summary = mock_health_checker.get_system_health_summary()
        
        assert summary['total_components'] == 2
        assert summary['healthy_components'] == 0
        assert summary['unhealthy_components'] == 2
        assert summary['overall_status'] == 'unhealthy'
    
    def test_get_system_health_summary_no_components(self, mock_health_checker):
        """Test system health summary when no components are registered."""
        summary = mock_health_checker.get_system_health_summary()
        
        assert summary['total_components'] == 0
        assert summary['healthy_components'] == 0
        assert summary['unhealthy_components'] == 0
        assert summary['overall_status'] == 'unknown'
        assert len(summary['component_reports']) == 0
    
    def test_error_handling_invalid_component_name(self, mock_health_checker):
        """Test error handling with invalid component name."""
        # Should handle None or empty component names gracefully
        report = mock_health_checker.check_component_health(None)
        assert report.status == HealthStatus.UNKNOWN
        
        report = mock_health_checker.check_component_health('')
        assert report.status == HealthStatus.UNKNOWN
    
    def test_error_handling_duplicate_component_registration(self, mock_health_checker):
        """Test error handling with duplicate component registration."""
        mock_component1 = Mock()
        mock_component1.name = 'test_component'
        
        mock_component2 = Mock()
        mock_component2.name = 'test_component'
        
        # First registration should succeed
        mock_health_checker.register_component(mock_component1)
        assert 'test_component' in mock_health_checker.registered_components
        
        # Second registration should overwrite the first
        mock_health_checker.register_component(mock_component2)
        assert mock_health_checker.registered_components['test_component'] == mock_component2
    
    def test_edge_case_component_without_health_check(self, mock_health_checker):
        """Test edge case with component that doesn't have health_check method."""
        mock_component = Mock()
        mock_component.name = 'test_component'
        # Don't set health_check method
        
        mock_health_checker.register_component(mock_component)
        
        report = mock_health_checker.check_component_health('test_component')
        
        assert report.status == HealthStatus.UNHEALTHY
        assert 'health_check method not found' in report.error_message
    
    def test_edge_case_component_health_check_returns_none(self, mock_health_checker):
        """Test edge case when component health_check returns None."""
        mock_component = Mock()
        mock_component.name = 'test_component'
        mock_component.health_check.return_value = None
        
        mock_health_checker.register_component(mock_component)
        
        report = mock_health_checker.check_component_health('test_component')
        
        assert report.status == HealthStatus.UNKNOWN
        assert 'Invalid health check response' in report.error_message
    
    def test_edge_case_component_health_check_returns_invalid_status(self, mock_health_checker):
        """Test edge case when component health_check returns invalid status."""
        mock_component = Mock()
        mock_component.name = 'test_component'
        mock_component.health_check.return_value = {'status': 'invalid_status'}
        
        mock_health_checker.register_component(mock_component)
        
        report = mock_health_checker.check_component_health('test_component')
        
        assert report.status == HealthStatus.UNKNOWN
        assert 'Invalid health status' in report.error_message
