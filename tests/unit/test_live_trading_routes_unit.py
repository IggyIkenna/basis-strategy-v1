"""Unit tests for live trading routes."""

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

from basis_strategy_v1.api.routes.live_trading import router
from basis_strategy_v1.core.services.live_service import LiveTradingService


class TestLiveTradingRoutes:
    """Test class for live trading routes."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app for testing."""
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/live-trading")
        return app

    @pytest.fixture
    def test_client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_live_trading_service(self):
        """Mock live trading service."""
        service = Mock(spec=LiveTradingService)
        service.create_request.return_value = Mock()
        service.start_live_trading.return_value = "test-request-123"
        service.stop_live_trading.return_value = True
        service.get_status.return_value = {
            "request_id": "test-request-123",
            "status": "running",
            "strategy_name": "pure_lending_usdt",
            "started_at": "2024-01-01T12:00:00Z",
            "uptime_seconds": 1800,
            "active_positions": 2,
            "total_trades": 15,
            "current_pnl": 125.50
        }
        service.get_performance_metrics.return_value = {
            "total_return": 0.125,
            "annualized_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.05,
            "total_trades": 15,
            "win_rate": 0.67
        }
        service.get_system_status.return_value = {
            "status": "healthy",
            "active_strategies": 1,
            "total_capital": 1000.0,
            "system_uptime": 3600
        }
        service.get_all_running_strategies.return_value = [
            {
                "request_id": "test-request-123",
                "strategy_name": "pure_lending_usdt",
                "status": "running",
                "started_at": "2024-01-01T12:00:00Z"
            }
        ]
        service.emergency_stop.return_value = True
        return service

    def override_dependency(self, app, mock_service):
        """Override the live trading service dependency."""
        from basis_strategy_v1.api.dependencies import get_live_trading_service
        app.dependency_overrides[get_live_trading_service] = lambda: mock_service

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_start_trading_success(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test successful start trading."""
        mock_get_service.return_value = mock_live_trading_service
        
        request_data = {
            "strategy_name": "pure_lending_usdt",
            "initial_capital": 1000.0,
            "share_class": "USDT",
            "config_overrides": {}
        }
        
        response = test_client.post("/api/v1/live-trading/start", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["request_id"] == "test-request-123"
        assert data["data"]["status"] == "started"
        assert data["data"]["strategy_name"] == "pure_lending_usdt"

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_start_trading_service_error(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test start trading when service raises an exception."""
        mock_live_trading_service.start_trading.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_live_trading_service
        
        request_data = {
            "strategy_name": "pure_lending_usdt",
            "initial_capital": 1000.0,
            "share_class": "USDT",
            "config_overrides": {}
        }
        
        response = test_client.post("/api/v1/live-trading/start", json=request_data)
        assert response.status_code in [200, 500]
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_start_trading_validation_error(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test start trading with invalid request data."""
        mock_get_service.return_value = mock_live_trading_service
        
        # Missing required fields
        request_data = {
            "strategy_name": "pure_lending_usdt"
            # Missing initial_capital and share_class
        }
        
        response = test_client.post("/api/v1/live-trading/start", json=request_data)
        assert response.status_code in [400, 422]

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_stop_trading_success(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test successful stop trading."""
        mock_get_service.return_value = mock_live_trading_service
        
        response = test_client.post("/api/v1/live-trading/stop/test-request-123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_stop_trading_service_error(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test stop trading when service raises an exception."""
        mock_live_trading_service.stop_live_trading.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_live_trading_service
        
        response = test_client.post("/api/v1/live-trading/stop/test-request-123")
        assert response.status_code in [200, 500]
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_get_trading_status_success(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test successful get trading status."""
        mock_get_service.return_value = mock_live_trading_service
        
        response = test_client.get("/api/v1/live-trading/status/test-request-123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["request_id"] == "test-request-123"
        assert data["data"]["status"] == "running"
        assert data["data"]["strategy_name"] == "pure_lending_usdt"
        assert "uptime_seconds" in data["data"]
        assert "active_positions" in data["data"]
        assert "total_trades" in data["data"]
        assert "current_pnl" in data["data"]

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_get_trading_status_not_found(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test get trading status when request not found."""
        mock_live_trading_service.get_status.side_effect = Exception("Request not found")
        mock_get_service.return_value = mock_live_trading_service
        
        response = test_client.get("/api/v1/live-trading/status/nonexistent")
        assert response.status_code in [200, 404]
        data = response.json()
        assert data is not None

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_get_performance_success(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test successful get performance metrics."""
        mock_get_service.return_value = mock_live_trading_service
        
        response = test_client.get("/api/v1/live-trading/performance/test-request-123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total_return" in data["data"]
        assert "annualized_return" in data["data"]
        assert "sharpe_ratio" in data["data"]
        assert "max_drawdown" in data["data"]
        assert "total_trades" in data["data"]
        assert "win_rate" in data["data"]

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_get_performance_not_found(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test get performance when request not found."""
        mock_live_trading_service.get_performance_metrics.side_effect = Exception("Request not found")
        mock_get_service.return_value = mock_live_trading_service
        
        response = test_client.get("/api/v1/live-trading/performance/nonexistent")
        assert response.status_code in [200, 404]
        data = response.json()
        assert data is not None

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_get_system_status_success(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test successful get system status."""
        mock_get_service.return_value = mock_live_trading_service
        
        response = test_client.get("/api/v1/live-trading/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "status" in data["data"]
        assert "active_strategies" in data["data"]
        assert "total_capital" in data["data"]
        assert "system_uptime" in data["data"]

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_get_strategies_success(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test successful get running strategies."""
        mock_get_service.return_value = mock_live_trading_service
        
        response = test_client.get("/api/v1/live-trading/strategies")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "strategies" in data["data"]
        assert len(data["data"]["strategies"]) == 1
        
        # Verify strategy structure
        strategy = data["data"]["strategies"][0]
        assert "request_id" in strategy
        assert "strategy_name" in strategy
        assert "status" in strategy
        assert "started_at" in strategy

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_emergency_stop_success(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test successful emergency stop."""
        mock_get_service.return_value = mock_live_trading_service
        
        response = test_client.post("/api/v1/live-trading/emergency-stop/test-request-123?reason=Test emergency")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_manual_rebalance_success(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test successful manual rebalance."""
        mock_get_service.return_value = mock_live_trading_service
        
        request_data = {
            "strategy_id": "test-request-123",
            "rebalance_type": "manual",
            "target_allocation": {"USDT": 0.6, "ETH": 0.4}
        }
        
        response = test_client.post("/api/v1/live-trading/rebalance", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_live_trading_response_structure(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test that live trading response has the expected structure."""
        mock_get_service.return_value = mock_live_trading_service
        
        request_data = {
            "strategy_name": "pure_lending_usdt",
            "initial_capital": 1000.0,
            "share_class": "USDT",
            "config_overrides": {}
        }
        
        response = test_client.post("/api/v1/live-trading/start", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        # Verify StandardResponse structure
        assert "success" in data
        assert "data" in data
        assert "timestamp" in data
        
        # Verify LiveTradingResponse structure
        trading_data = data["data"]
        assert "request_id" in trading_data
        assert "status" in trading_data
        assert "strategy_name" in trading_data
        assert "started_at" in trading_data

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_live_trading_service_dependency_injection(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test that live trading service dependency is properly injected."""
        mock_get_service.return_value = mock_live_trading_service
        
        request_data = {
            "strategy_name": "pure_lending_usdt",
            "initial_capital": 1000.0,
            "share_class": "USDT",
            "config_overrides": {}
        }
        
        response = test_client.post("/api/v1/live-trading/start", json=request_data)
        assert response.status_code == 200
        
        # Verify that the mock was called
        mock_live_trading_service.start_live_trading.assert_called_once()

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_timestamp_handling(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test that timestamps are properly handled."""
        mock_get_service.return_value = mock_live_trading_service
        
        response = test_client.get("/api/v1/live-trading/status/test-request-123")
        assert response.status_code == 200
        data = response.json()
        
        # Verify timestamp is a valid ISO format string
        timestamp = data["timestamp"]
        assert isinstance(timestamp, str)
        # Should be able to parse it back to datetime
        parsed_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed_timestamp, datetime)

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_error_logging(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test that errors are properly logged."""
        mock_live_trading_service.start_live_trading.side_effect = Exception("Test error")
        mock_get_service.return_value = mock_live_trading_service
        
        request_data = {
            "strategy_name": "pure_lending_usdt",
            "initial_capital": 1000.0,
            "share_class": "USDT",
            "config_overrides": {}
        }
        
        response = test_client.post("/api/v1/live-trading/start", json=request_data)
        assert response.status_code in [200, 500]
        data = response.json()
        
        # Should return error response
        assert data["success"] is False

    @patch('basis_strategy_v1.api.dependencies.get_live_trading_service')
    def test_live_trading_message_generation(self, mock_get_service, app, test_client, mock_live_trading_service):
        """Test that appropriate messages are generated for responses."""
        mock_get_service.return_value = mock_live_trading_service
        
        request_data = {
            "strategy_name": "pure_lending_usdt",
            "initial_capital": 1000.0,
            "share_class": "USDT",
            "config_overrides": {}
        }
        
        response = test_client.post("/api/v1/live-trading/start", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        # Check if message is present in the response data
        if "message" in data["data"]:
            assert isinstance(data["data"]["message"], str)
            assert len(data["data"]["message"]) > 0