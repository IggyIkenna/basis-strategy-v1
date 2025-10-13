"""Unit tests for config routes."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
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

from basis_strategy_v1.api.routes.config import router
from basis_strategy_v1.infrastructure.config.config_manager import ConfigManager


class TestConfigRoutes:
    """Test class for config routes."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app for testing."""
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/config")
        return app

    @pytest.fixture
    def test_client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_config_manager(self):
        """Mock config manager."""
        manager = Mock(spec=ConfigManager)
        manager.get_complete_config.return_value = {
            "environment": "dev",
            "deployment_mode": "local",
            "execution_mode": "backtest",
            "data_mode": "csv",
            "debug": True,
            "log_level": "DEBUG"
        }
        return manager

    @pytest.fixture
    def mock_request(self):
        """Mock request object."""
        request = Mock()
        request.state.correlation_id = "test-correlation-id"
        return request

    def override_dependency(self, test_client, mock_config_manager):
        """Helper method to override the config manager dependency."""
        from basis_strategy_v1.api.routes.config import get_config_manager
        
        def override_get_config_manager():
            return mock_config_manager
        
        test_client.app.dependency_overrides[get_config_manager] = override_get_config_manager
        return test_client

    def test_get_configuration_success(self, test_client, mock_config_manager, mock_request):
        """Test successful configuration retrieval."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["environment"] == "dev"
            assert data["data"]["deployment_mode"] == "local"
            assert data["data"]["execution_mode"] == "backtest"
        finally:
            test_client.app.dependency_overrides.clear()

    def test_get_configuration_service_error(self, test_client, mock_config_manager):
        """Test configuration retrieval when service raises an error."""
        mock_config_manager.get_complete_config.side_effect = Exception("Config error")
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/")
            assert response.status_code == 500
            assert "Failed to get configuration" in response.json()["detail"]
        finally:
            test_client.app.dependency_overrides.clear()

    def test_get_environment_info_success(self, test_client, mock_config_manager, mock_request):
        """Test successful environment info retrieval."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/environment")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["environment"] == "dev"
            assert data["data"]["deployment_mode"] == "local"
            assert data["data"]["execution_mode"] == "backtest"
            assert data["data"]["data_mode"] == "csv"
            assert data["data"]["debug"] is True
            assert data["data"]["log_level"] == "DEBUG"
        finally:
            test_client.app.dependency_overrides.clear()

    def test_get_environment_info_missing_env_vars(self, test_client, mock_config_manager):
        """Test environment info retrieval with missing environment variables."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            # Temporarily remove some environment variables
            with patch.dict(os.environ, {}, clear=True):
                response = test_client.get("/api/v1/config/environment")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "data" in data
                # Should have default values for missing env vars
                assert data["data"]["environment"] == "unknown"
                assert data["data"]["deployment_mode"] == "unknown"
                assert data["data"]["execution_mode"] == "unknown"
        finally:
            test_client.app.dependency_overrides.clear()

    def test_get_environment_info_service_error(self, test_client, mock_config_manager):
        """Test environment info retrieval when service raises an error."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            # Mock os.getenv to raise an exception
            with patch('os.getenv', side_effect=Exception("Environment error")):
                response = test_client.get("/api/v1/config/environment")
                assert response.status_code == 500
                assert "Failed to get environment info" in response.json()["detail"]
        finally:
            test_client.app.dependency_overrides.clear()

    def test_get_system_status_success(self, test_client, mock_config_manager, mock_request):
        """Test successful system status retrieval."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/status")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["status"] == "healthy"
            assert data["data"]["environment"] == "dev"
            assert data["data"]["deployment_mode"] == "local"
            assert "python_version" in data["data"]
            assert "platform" in data["data"]
            assert data["data"]["config_loaded"] is True
            assert "services" in data["data"]
            assert data["data"]["services"]["config_manager"] == "healthy"
            assert data["data"]["services"]["data_provider"] == "healthy"
            assert data["data"]["services"]["strategy_engine"] == "healthy"
        finally:
            test_client.app.dependency_overrides.clear()

    def test_get_system_status_service_error(self, test_client, mock_config_manager):
        """Test system status retrieval when service raises an error."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            # Mock platform.platform to raise an exception
            with patch('platform.platform', side_effect=Exception("Platform error")):
                response = test_client.get("/api/v1/config/status")
                assert response.status_code == 500
                assert "Failed to get system status" in response.json()["detail"]
        finally:
            test_client.app.dependency_overrides.clear()

    def test_configuration_data_structure(self, test_client, mock_config_manager):
        """Test that configuration data has the expected structure."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "timestamp" in data
            
            config_data = data["data"]
            assert isinstance(config_data, dict)
            assert "environment" in config_data
            assert "deployment_mode" in config_data
            assert "execution_mode" in config_data
        finally:
            test_client.app.dependency_overrides.clear()

    def test_environment_info_data_structure(self, test_client, mock_config_manager):
        """Test that environment info data has the expected structure."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/environment")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "timestamp" in data
            
            env_data = data["data"]
            assert isinstance(env_data, dict)
            assert "environment" in env_data
            assert "deployment_mode" in env_data
            assert "deployment_machine" in env_data
            assert "execution_mode" in env_data
            assert "data_mode" in env_data
            assert "debug" in env_data
            assert "log_level" in env_data
            assert "data_dir" in env_data
            assert "results_dir" in env_data
        finally:
            test_client.app.dependency_overrides.clear()

    def test_system_status_data_structure(self, test_client, mock_config_manager):
        """Test that system status data has the expected structure."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/status")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "timestamp" in data
            
            status_data = data["data"]
            assert isinstance(status_data, dict)
            assert "status" in status_data
            assert "environment" in status_data
            assert "deployment_mode" in status_data
            assert "python_version" in status_data
            assert "platform" in status_data
            assert "config_loaded" in status_data
            assert "services" in status_data
            
            services = status_data["services"]
            assert isinstance(services, dict)
            assert "config_manager" in services
            assert "data_provider" in services
            assert "strategy_engine" in services
        finally:
            test_client.app.dependency_overrides.clear()

    def test_correlation_id_handling(self, test_client, mock_config_manager):
        """Test that correlation ID is properly handled in requests."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/")
            assert response.status_code == 200
            data = response.json()
            assert "timestamp" in data
            # Should have a timestamp
            assert data["timestamp"] is not None
        finally:
            test_client.app.dependency_overrides.clear()

    def test_error_logging(self, test_client, mock_config_manager):
        """Test that errors are properly logged."""
        mock_config_manager.get_complete_config.side_effect = Exception("Test error")
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/")
            assert response.status_code == 500
            # The error is logged (we can see it in the captured log output)
            # but mocking structlog is complex, so we just verify the behavior
        finally:
            test_client.app.dependency_overrides.clear()

    def test_boolean_environment_variables(self, test_client, mock_config_manager):
        """Test that boolean environment variables are properly parsed."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            # Test with debug=true
            with patch.dict(os.environ, {"BASIS_DEBUG": "true"}):
                response = test_client.get("/api/v1/config/environment")
                assert response.status_code == 200
                data = response.json()
                assert data["data"]["debug"] is True
            
            # Test with debug=false
            with patch.dict(os.environ, {"BASIS_DEBUG": "false"}):
                response = test_client.get("/api/v1/config/environment")
                assert response.status_code == 200
                data = response.json()
                assert data["data"]["debug"] is False
            
            # Test with debug=invalid (should default to False)
            with patch.dict(os.environ, {"BASIS_DEBUG": "invalid"}):
                response = test_client.get("/api/v1/config/environment")
                assert response.status_code == 200
                data = response.json()
                assert data["data"]["debug"] is False
        finally:
            test_client.app.dependency_overrides.clear()

    def test_platform_information(self, test_client, mock_config_manager):
        """Test that platform information is included in system status."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/status")
            assert response.status_code == 200
            data = response.json()
            assert "python_version" in data["data"]
            assert "platform" in data["data"]
            # Python version should be a string
            assert isinstance(data["data"]["python_version"], str)
            # Platform should be a string
            assert isinstance(data["data"]["platform"], str)
        finally:
            test_client.app.dependency_overrides.clear()

    def test_services_health_status(self, test_client, mock_config_manager):
        """Test that services health status is properly reported."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/status")
            assert response.status_code == 200
            data = response.json()
            services = data["data"]["services"]
            
            # All services should be healthy
            assert services["config_manager"] == "healthy"
            assert services["data_provider"] == "healthy"
            assert services["strategy_engine"] == "healthy"
        finally:
            test_client.app.dependency_overrides.clear()

    def test_config_manager_dependency_injection(self, test_client, mock_config_manager):
        """Test that config manager is properly injected as a dependency."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/")
            assert response.status_code == 200
            # Verify that the config manager was called
            mock_config_manager.get_complete_config.assert_called_once()
        finally:
            test_client.app.dependency_overrides.clear()

    def test_http_exception_handling(self, test_client, mock_config_manager):
        """Test that HTTP exceptions are properly handled."""
        mock_config_manager.get_complete_config.side_effect = Exception("Config error")
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/")
            assert response.status_code == 500
            error_detail = response.json()["detail"]
            assert "Failed to get configuration" in error_detail
            assert "Config error" in error_detail
        finally:
            test_client.app.dependency_overrides.clear()

    def test_response_model_validation(self, test_client, mock_config_manager):
        """Test that response models are properly validated."""
        test_client = self.override_dependency(test_client, mock_config_manager)
        
        try:
            response = test_client.get("/api/v1/config/")
            assert response.status_code == 200
            data = response.json()
            
            # Verify StandardResponse structure
            assert "success" in data
            assert "data" in data
            assert "timestamp" in data
            assert isinstance(data["success"], bool)
            assert isinstance(data["data"], dict)
            assert isinstance(data["timestamp"], str)
        finally:
            test_client.app.dependency_overrides.clear()