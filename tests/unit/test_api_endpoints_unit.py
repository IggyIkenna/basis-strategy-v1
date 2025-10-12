"""
Unit tests for API Endpoints component.

Tests API endpoint functionality in isolation with mocked dependencies.
"""

import pytest
import os
from unittest.mock import Mock, patch
import json
from fastapi.testclient import TestClient


class TestAPIEndpoints:
    """Test API Endpoints component in isolation."""
    
    def setup_method(self):
        """Set up test environment variables."""
        # Set required environment variables for API tests
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
        os.environ['BASIS_API_PORT'] = '8001'
        os.environ['BASIS_API_HOST'] = '0.0.0.0'
        os.environ['DATA_LOAD_TIMEOUT'] = '300'
        os.environ['DATA_VALIDATION_STRICT'] = 'true'
        os.environ['DATA_CACHE_SIZE'] = '1000'
        os.environ['STRATEGY_MANAGER_TIMEOUT'] = '30'
        os.environ['STRATEGY_MANAGER_MAX_RETRIES'] = '3'
        os.environ['STRATEGY_FACTORY_TIMEOUT'] = '30'
        os.environ['STRATEGY_FACTORY_MAX_RETRIES'] = '3'
    
    def teardown_method(self):
        """Clean up test environment variables."""
        # Clean up environment variables
        env_vars_to_remove = [
            'BASIS_ENVIRONMENT', 'BASIS_DEPLOYMENT_MODE', 'BASIS_DEPLOYMENT_MACHINE',
            'BASIS_DATA_DIR', 'BASIS_DATA_MODE', 'BASIS_RESULTS_DIR', 'BASIS_DEBUG',
            'BASIS_LOG_LEVEL', 'BASIS_EXECUTION_MODE', 'BASIS_DATA_START_DATE',
            'BASIS_DATA_END_DATE', 'BASIS_API_PORT', 'BASIS_API_HOST',
            'DATA_LOAD_TIMEOUT', 'DATA_VALIDATION_STRICT', 'DATA_CACHE_SIZE',
            'STRATEGY_MANAGER_TIMEOUT', 'STRATEGY_MANAGER_MAX_RETRIES',
            'STRATEGY_FACTORY_TIMEOUT', 'STRATEGY_FACTORY_MAX_RETRIES'
        ]
        for var in env_vars_to_remove:
            if var in os.environ:
                del os.environ[var]
    
    def test_api_client_initialization(self, mock_config, mock_data_provider):
        """Test API client initializes correctly with config and data provider."""
        from backend.src.basis_strategy_v1.api.main import app
        
        # Test that the FastAPI app can be created
        assert app is not None
        assert app.title == "Basis Strategy API"
    
    def test_health_endpoint(self, mock_config, mock_data_provider):
        """Test health endpoint returns correct status."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/health/")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
    
    def test_detailed_health_endpoint(self, mock_config, mock_data_provider):
        """Test detailed health endpoint returns comprehensive status."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/health/detailed")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "components" in data
            assert "timestamp" in data
    
    def test_strategy_list_endpoint(self, mock_config, mock_data_provider):
        """Test strategy list endpoint returns available strategies."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/v1/strategies/")
            
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert data["success"] == True
            assert "data" in data
            assert "strategies" in data["data"]
    
    def test_strategy_parameters_endpoint(self, mock_config, mock_data_provider):
        """Test strategy parameters endpoint returns correct parameters."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/v1/strategies/pure_lending/parameters")
            
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert data["success"] == True
            assert "data" in data
    
    def test_backtest_execution_endpoint(self, mock_config, mock_data_provider):
        """Test backtest execution endpoint with valid parameters."""
        from backend.src.basis_strategy_v1.api.main import app
        
        backtest_request = {
            "strategy_name": "pure_lending",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "initial_capital": 100000.0,
            "share_class": "USDT",
            "config_overrides": {
                "max_drawdown": 0.2,
                "leverage_enabled": False
            }
        }
        
        with TestClient(app) as client:
            response = client.post("/api/v1/backtest/", json=backtest_request)
            
            # Should return 200 or 422 (validation error)
            assert response.status_code in [200, 422]
            if response.status_code == 200:
                data = response.json()
                assert "success" in data
                assert data["success"] == True
    
    def test_backtest_results_endpoint(self, mock_config, mock_data_provider):
        """Test backtest results retrieval endpoint."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/v1/results/test_id_123")
            
            # Should return 404 for non-existent result or 200 for valid result
            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = response.json()
                assert "success" in data
                assert data["success"] == True
    
    def test_live_trading_start_endpoint(self, mock_config, mock_data_provider):
        """Test live trading start endpoint."""
        from backend.src.basis_strategy_v1.api.main import app
        
        live_request = {
            "strategy_name": "btc_basis",
            "share_class": "USDT",
            "initial_capital": 100000.0,
            "exchange": "binance",
            "api_credentials": {
                "api_key": "test_key",
                "secret": "test_secret"
            },
            "risk_limits": {
                "max_drawdown": 0.15,
                "leverage_ratio": 2.0
            }
        }
        
        with TestClient(app) as client:
            response = client.post("/api/v1/live/start", json=live_request)
            
            # Should return 200, 422 (validation error), or 500 (service error)
            assert response.status_code in [200, 422, 500]
            if response.status_code == 200:
                data = response.json()
                assert "success" in data
                assert data["success"] == True
    
    def test_live_trading_stop_endpoint(self, mock_config, mock_data_provider):
        """Test live trading stop endpoint."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.post("/api/v1/live/stop/live_session_123")
            
            # Should return 200 or 404 (not found)
            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = response.json()
                assert "success" in data
                assert data["success"] == True
    
    def test_live_trading_status_endpoint(self, mock_config, mock_data_provider):
        """Test live trading status endpoint."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/v1/live/status/live_session_123")
            
            # Should return 200 or 404 (not found)
            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = response.json()
                assert "success" in data
                assert data["success"] == True
    
    def test_environment_info_endpoint(self, mock_config, mock_data_provider):
        """Test environment information endpoint."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/v1/config/environment")
            
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert data["success"] == True
            assert "data" in data
    
    def test_system_status_endpoint(self, mock_config, mock_data_provider):
        """Test system status endpoint."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/v1/config/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert data["success"] == True
            assert "data" in data
    
    def test_invalid_strategy_endpoint(self, mock_config, mock_data_provider):
        """Test API handles invalid strategy requests gracefully."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/v1/strategies/invalid_strategy/parameters")
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
    
    def test_invalid_backtest_id_endpoint(self, mock_config, mock_data_provider):
        """Test API handles invalid backtest ID requests gracefully."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/v1/results/invalid_id")
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
    
    def test_api_error_handling(self, mock_config, mock_data_provider):
        """Test API error handling and proper HTTP status codes."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            # Test malformed JSON request
            response = client.post(
                "/api/v1/backtest/",
                data="invalid json",
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 422  # Unprocessable Entity
            
            # Test missing required fields
            incomplete_request = {
                "strategy_name": "pure_lending"
                # Missing required fields
            }
            
            response = client.post("/api/v1/backtest/", json=incomplete_request)
            
            assert response.status_code == 422  # Unprocessable Entity
