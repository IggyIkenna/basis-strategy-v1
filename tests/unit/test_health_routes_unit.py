"""Unit tests for health routes."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime
import os

# Set up environment variables before importing the app
os.environ["BASIS_DATA_START_DATE"] = "2024-01-01"
os.environ["BASIS_DATA_END_DATE"] = "2024-01-31"
os.environ["BASIS_EXECUTION_MODE"] = "backtest"
os.environ["BASIS_ENVIRONMENT"] = "test"
os.environ["BASIS_DEPLOYMENT_MODE"] = "local"
os.environ["BASIS_DATA_DIR"] = "./data"
os.environ["BASIS_RESULTS_DIR"] = "./results"
os.environ["BASIS_DEBUG"] = "true"
os.environ["BASIS_LOG_LEVEL"] = "DEBUG"
os.environ["BASIS_DATA_MODE"] = "csv"
os.environ["BASIS_API_PORT"] = "8001"
os.environ["BASIS_API_HOST"] = "0.0.0.0"
os.environ["DATA_LOAD_TIMEOUT"] = "300"
os.environ["DATA_VALIDATION_STRICT"] = "true"
os.environ["DATA_CACHE_SIZE"] = "1000"
os.environ["STRATEGY_MANAGER_TIMEOUT"] = "30"
os.environ["STRATEGY_MANAGER_MAX_RETRIES"] = "3"
os.environ["STRATEGY_FACTORY_TIMEOUT"] = "30"
os.environ["STRATEGY_FACTORY_MAX_RETRIES"] = "3"

from basis_strategy_v1.api.routes.health import router
from basis_strategy_v1.infrastructure.health.health_checker import HealthChecker


class TestHealthRoutes:
    """Test class for health routes."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app for testing."""
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/health")
        return app

    @pytest.fixture
    def test_client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_health_checker(self):
        """Mock health checker."""
        checker = Mock(spec=HealthChecker)
        checker.check_health.return_value = {
            "status": "healthy",
            "timestamp": "2024-01-01T12:00:00Z",
            "service": "basis-strategy-v1",
            "execution_mode": "backtest",
            "uptime_seconds": 3600.0,
            "system": {
                "cpu_percent": 25.5,
                "memory_percent": 45.8,
                "memory_available_gb": 8.5
            },
            "components": {
                "config_manager": {
                    "status": "healthy",
                    "error_code": None,
                    "readiness_checks": {
                        "config_loaded": True,
                        "validation_passed": True
                    }
                },
                "data_provider": {
                    "status": "healthy",
                    "error_code": None,
                    "readiness_checks": {
                        "data_available": True,
                        "connection_ok": True
                    }
                }
            },
            "summary": {
                "total_components": 2,
                "healthy_components": 2,
                "unhealthy_components": 0
            }
        }
        checker.check_detailed_health.return_value = {
            "status": "healthy",
            "timestamp": "2024-01-01T12:00:00Z",
            "service": "basis-strategy-v1",
            "execution_mode": "backtest",
            "uptime_seconds": 3600.0,
            "system": {
                "cpu_percent": 25.5,
                "memory_percent": 45.8,
                "memory_available_gb": 8.5
            },
            "components": {
                "config_manager": {
                    "status": "healthy",
                    "error_code": None,
                    "readiness_checks": {
                        "config_loaded": True,
                        "validation_passed": True
                    }
                },
                "data_provider": {
                    "status": "healthy",
                    "error_code": None,
                    "readiness_checks": {
                        "data_available": True,
                        "connection_ok": True
                    }
                }
            },
            "summary": {
                "total_components": 2,
                "healthy_components": 2,
                "unhealthy_components": 0
            }
        }
        return checker

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_basic_health_success(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test successful basic health check."""
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "basis-strategy-v1"
        assert data["execution_mode"] == "backtest"
        assert data["uptime_seconds"] == 3600.0
        assert "timestamp" in data
        assert "components" in data
        assert "summary" in data

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_basic_health_checker_error(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test basic health check when health checker raises an exception."""
        mock_health_checker.check_health.side_effect = Exception("Health check failed")
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_detailed_health_success(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test successful detailed health check."""
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "basis-strategy-v1"
        assert data["execution_mode"] == "backtest"
        assert data["uptime_seconds"] == 3600.0
        assert "timestamp" in data
        assert "components" in data
        assert "summary" in data
        assert "system" in data

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_detailed_health_checker_error(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test detailed health check when health checker raises an exception."""
        mock_health_checker.check_detailed_health.side_effect = Exception("Detailed health check failed")
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_component_health_success(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test successful component health check."""
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/components")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "basis-strategy-v1"
        assert data["execution_mode"] == "backtest"
        assert data["uptime_seconds"] == 3600.0
        assert "timestamp" in data
        assert "components" in data
        assert "summary" in data

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_component_health_checker_error(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test component health check when health checker raises an exception."""
        mock_health_checker.check_detailed_health.side_effect = Exception("Component health check failed")
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/components")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_health_response_structure(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test that health response has the expected structure."""
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        
        # Verify HealthResponse structure
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "execution_mode" in data
        assert "uptime_seconds" in data
        assert "components" in data
        assert "summary" in data
        
        # Verify data types
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["service"], str)
        assert isinstance(data["execution_mode"], str)
        assert isinstance(data["uptime_seconds"], float)
        assert isinstance(data["components"], dict)
        assert isinstance(data["summary"], dict)

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_components_conversion(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test that components are properly structured."""
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        
        components = data["components"]
        assert isinstance(components, dict)
        assert "config_manager" in components
        assert "data_provider" in components
        
        # Verify component structure
        config_manager = components["config_manager"]
        assert config_manager["status"] == "healthy"
        assert "readiness_checks" in config_manager

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_timestamp_parsing(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test that timestamp is properly parsed and returned."""
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        
        # Verify timestamp is a valid ISO format string
        timestamp = data["timestamp"]
        assert isinstance(timestamp, str)
        # Should be able to parse it back to datetime
        parsed_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed_timestamp, datetime)

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_system_metrics(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test that system metrics are included in detailed health."""
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        
        assert "system" in data
        system = data["system"]
        assert isinstance(system, dict)
        assert "cpu_percent" in system
        assert "memory_percent" in system
        assert "memory_available_gb" in system

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_health_checker_dependency_injection(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test that health checker dependency is properly injected."""
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        
        # Verify that the mock was called
        mock_health_checker.check_health.assert_called_once()

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_correlation_id_handling(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test that correlation ID is handled properly in error responses."""
        mock_health_checker.check_health.side_effect = Exception("Test error")
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        
        # Should still return a valid response even with error
        assert "status" in data
        assert "timestamp" in data

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_error_logging(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test that errors are properly logged."""
        mock_health_checker.check_health.side_effect = Exception("Test error")
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        
        # Should return unhealthy status
        assert data["status"] == "unhealthy"

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_health_status_values(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test that health status values are valid."""
        mock_get_health_checker.return_value = mock_health_checker
        
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        
        # Status should be one of the valid values
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_service_name_consistency(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test that service name is consistent across all endpoints."""
        mock_get_health_checker.return_value = mock_health_checker
        
        # Test all endpoints
        endpoints = ["/", "/detailed", "/components"]
        for endpoint in endpoints:
            response = test_client.get(f"/api/v1/health{endpoint}")
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "basis-strategy-v1"

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_execution_mode_consistency(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test that execution mode is consistent across all endpoints."""
        mock_get_health_checker.return_value = mock_health_checker
        
        # Test all endpoints
        endpoints = ["/", "/detailed", "/components"]
        for endpoint in endpoints:
            response = test_client.get(f"/api/v1/health{endpoint}")
            assert response.status_code == 200
            data = response.json()
            assert data["execution_mode"] == "backtest"

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_uptime_seconds_consistency(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test that uptime seconds is consistent across all endpoints."""
        mock_get_health_checker.return_value = mock_health_checker
        
        # Test all endpoints
        endpoints = ["/", "/detailed", "/components"]
        for endpoint in endpoints:
            response = test_client.get(f"/api/v1/health{endpoint}")
            assert response.status_code == 200
            data = response.json()
            assert data["uptime_seconds"] == 3600.0

    @patch('basis_strategy_v1.api.routes.health.get_health_checker')
    def test_summary_consistency(self, mock_get_health_checker, app, test_client, mock_health_checker):
        """Test that summary is consistent across all endpoints."""
        mock_get_health_checker.return_value = mock_health_checker
        
        # Test all endpoints
        endpoints = ["/", "/detailed", "/components"]
        for endpoint in endpoints:
            response = test_client.get(f"/api/v1/health{endpoint}")
            assert response.status_code == 200
            data = response.json()
            expected_summary = {
                "total_components": 2,
                "healthy_components": 2,
                "unhealthy_components": 0
            }
            assert data["summary"] == expected_summary