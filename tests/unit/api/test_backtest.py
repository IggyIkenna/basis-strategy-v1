"""
Test Backtest API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append('/workspace/backend/src')

from basis_strategy_v1.api.main import create_application
from basis_strategy_v1.api.models.requests import BacktestRequest
from basis_strategy_v1.api.models.responses import BacktestResponse


class TestBacktestAPI:
    """Test backtest API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_application()
        return TestClient(app)
    
    @pytest.fixture
    def mock_backtest_request(self):
        """Create mock backtest request."""
        return BacktestRequest(
            strategy_name="pure_lending",
            share_class="USDT",
            initial_capital=100000,
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
    
    @pytest.fixture
    def mock_backtest_response(self):
        """Create mock backtest response."""
        return BacktestResponse(
            request_id="test-123",
            status="running",
            created_at=datetime.utcnow(),
            estimated_completion_time=datetime.utcnow()
        )
    
    @patch('basis_strategy_v1.api.routes.backtest.get_backtest_service')
    def test_run_backtest_success(self, mock_get_service, client, mock_backtest_request, mock_backtest_response):
        """Test successful backtest submission."""
        # Mock the backtest service
        mock_service = Mock()
        mock_service.create_request.return_value = {"test": "request"}
        mock_service.submit_backtest.return_value = mock_backtest_response
        mock_get_service.return_value = mock_service
        
        response = client.post("/backtest/", json=mock_backtest_request.dict())
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "success" in data
        assert "data" in data
        assert data["success"] is True
        
        # Verify backtest response data
        backtest_data = data["data"]
        assert "request_id" in backtest_data
        assert "status" in backtest_data
        assert "created_at" in backtest_data
    
    @patch('basis_strategy_v1.api.routes.backtest.get_backtest_service')
    def test_run_backtest_validation_error(self, mock_get_service, client):
        """Test backtest with validation error."""
        # Mock the backtest service to raise validation error
        mock_service = Mock()
        mock_service.create_request.side_effect = ValueError("Invalid strategy")
        mock_get_service.return_value = mock_service
        
        # Send invalid request
        invalid_request = {
            "strategy_name": "invalid_strategy",
            "share_class": "INVALID",
            "initial_capital": -1000,  # Invalid negative capital
            "start_date": "invalid-date",
            "end_date": "invalid-date"
        }
        
        response = client.post("/backtest/", json=invalid_request)
        
        # Should return 422 for validation error
        assert response.status_code == 422
    
    @patch('basis_strategy_v1.api.routes.backtest.get_backtest_service')
    def test_get_backtest_status(self, mock_get_service, client):
        """Test getting backtest status."""
        # Mock the backtest service
        mock_service = Mock()
        mock_service.get_status.return_value = {
            "request_id": "test-123",
            "status": "completed",
            "progress": 100,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        mock_get_service.return_value = mock_service
        
        response = client.get("/backtest/test-123/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "success" in data
        assert "data" in data
        assert data["success"] is True
        
        # Verify status data
        status_data = data["data"]
        assert "request_id" in status_data
        assert "status" in status_data
        assert "progress" in status_data
    
    @patch('basis_strategy_v1.api.routes.backtest.get_backtest_service')
    def test_get_backtest_status_not_found(self, mock_get_service, client):
        """Test getting status for non-existent backtest."""
        # Mock the backtest service to return None
        mock_service = Mock()
        mock_service.get_status.return_value = None
        mock_get_service.return_value = mock_service
        
        response = client.get("/backtest/non-existent/status")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    @patch('basis_strategy_v1.api.routes.backtest.get_backtest_service')
    def test_get_backtest_result(self, mock_get_service, client):
        """Test getting backtest result."""
        # Mock the backtest service
        mock_service = Mock()
        mock_service.get_result.return_value = {
            "request_id": "test-123",
            "status": "completed",
            "total_return": 0.05,
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.02,
            "results": {"test": "data"}
        }
        mock_get_service.return_value = mock_service
        
        response = client.get("/backtest/test-123/result")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "success" in data
        assert "data" in data
        assert data["success"] is True
        
        # Verify result data
        result_data = data["data"]
        assert "request_id" in result_data
        assert "status" in result_data
        assert "total_return" in result_data
    
    @patch('basis_strategy_v1.api.routes.backtest.get_backtest_service')
    def test_get_backtest_result_not_found(self, mock_get_service, client):
        """Test getting result for non-existent backtest."""
        # Mock the backtest service to return None
        mock_service = Mock()
        mock_service.get_result.return_value = None
        mock_get_service.return_value = mock_service
        
        response = client.get("/backtest/non-existent/result")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    @patch('basis_strategy_v1.api.routes.backtest.get_backtest_service')
    def test_list_backtests(self, mock_get_service, client):
        """Test listing backtests."""
        # Mock the backtest service
        mock_service = Mock()
        mock_service.list_backtests.return_value = [
            {
                "request_id": "test-1",
                "status": "completed",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "request_id": "test-2", 
                "status": "running",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        mock_get_service.return_value = mock_service
        
        response = client.get("/backtest/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "success" in data
        assert "data" in data
        assert data["success"] is True
        
        # Verify list data
        list_data = data["data"]
        assert isinstance(list_data, list)
        assert len(list_data) == 2
        assert "request_id" in list_data[0]
        assert "status" in list_data[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])