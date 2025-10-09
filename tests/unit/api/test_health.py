"""
Test Unified Health API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add backend to path
sys.path.append('/workspace/backend/src')

from basis_strategy_v1.api.main import create_application


class TestHealthAPI:
    """Test health API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_application()
        return TestClient(app)
    
    @patch('basis_strategy_v1.core.health.unified_health_manager.check_basic_health')
    def test_basic_health_check(self, mock_basic_health, client):
        """Test basic health check endpoint."""
        # Mock the unified health manager response
        mock_basic_health.return_value = {
            "status": "healthy",
            "timestamp": "2025-01-06T12:00:00Z",
            "service": "basis-strategy-v1",
            "execution_mode": "backtest",
            "uptime_seconds": 3600,
            "system": {
                "cpu_percent": 15.2,
                "memory_percent": 45.8,
                "memory_available_gb": 8.5
            }
        }
        
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "execution_mode" in data
        assert "uptime_seconds" in data
        assert "system" in data
        
        # Verify status
        assert data["status"] == "healthy"
        assert data["service"] == "basis-strategy-v1"
        assert data["execution_mode"] == "backtest"
        
        # Verify system metrics
        assert "cpu_percent" in data["system"]
        assert "memory_percent" in data["system"]
        assert "memory_available_gb" in data["system"]
    
    @patch('basis_strategy_v1.core.health.unified_health_manager.check_detailed_health')
    def test_detailed_health_check(self, mock_detailed_health, client):
        """Test detailed health check endpoint."""
        # Mock the unified health manager response
        mock_detailed_health.return_value = {
            "status": "healthy",
            "timestamp": "2025-01-06T12:00:00Z",
            "execution_mode": "backtest",
            "components": {
                "position_monitor": {
                    "status": "healthy",
                    "timestamp": "2025-01-06T12:00:00Z",
                    "error_code": None,
                    "error_message": None,
                    "readiness_checks": {"initialized": True},
                    "metrics": {},
                    "dependencies": []
                }
            },
            "system": {
                "cpu_percent": 15.2,
                "memory_percent": 45.8,
                "memory_available_gb": 8.5,
                "disk_percent": 23.1,
                "uptime_seconds": 3600
            },
            "summary": {
                "total_components": 1,
                "healthy_components": 1,
                "unhealthy_components": 0,
                "not_ready_components": 0,
                "unknown_components": 0
            }
        }
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "execution_mode" in data
        assert "components" in data
        assert "system" in data
        assert "summary" in data
        
        # Verify status
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert data["service"] == "basis-strategy-v1"
        
        # Verify components
        assert "position_monitor" in data["components"]
        component = data["components"]["position_monitor"]
        assert component["status"] == "healthy"
        assert component["error_code"] is None
        
        # Verify summary
        assert data["summary"]["total_components"] == 1
        assert data["summary"]["healthy_components"] == 1
    
    @patch('basis_strategy_v1.core.health.unified_health_manager.check_basic_health')
    def test_health_check_with_mock_metrics(self, mock_basic_health, client):
        """Test health check with mocked system metrics."""
        # Mock the unified health manager response
        mock_basic_health.return_value = {
            "status": "healthy",
            "timestamp": "2025-01-06T12:00:00Z",
            "service": "basis-strategy-v1",
            "execution_mode": "backtest",
            "uptime_seconds": 3600,
            "system": {
                "cpu_percent": 25.5,
                "memory_percent": 60.0,
                "memory_available_gb": 8.0
            }
        }
        
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify mocked metrics
        assert data["system"]["cpu_percent"] == 25.5
        assert data["system"]["memory_percent"] == 60.0
        assert data["system"]["memory_available_gb"] == 8.0
    
    @patch('basis_strategy_v1.core.health.unified_health_manager.check_basic_health')
    def test_health_check_error_handling(self, mock_basic_health, client):
        """Test health check error handling."""
        # Mock the unified health manager to raise an exception
        mock_basic_health.side_effect = Exception("System error")
        
        response = client.get("/health/")
        
        # Should still return 200 with error status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data
    
    @patch('basis_strategy_v1.core.health.unified_health_manager.check_detailed_health')
    def test_mode_aware_health_check(self, mock_detailed_health, client):
        """Test mode-aware health checking (backtest vs live)."""
        # Mock backtest mode response
        mock_detailed_health.return_value = {
            "status": "healthy",
            "timestamp": "2025-01-06T12:00:00Z",
            "execution_mode": "backtest",
            "components": {
                "position_monitor": {"status": "healthy"},
                "data_provider": {"status": "healthy"},
                "risk_monitor": {"status": "healthy"}
            },
            "system": {"cpu_percent": 15.2},
            "summary": {"total_components": 3, "healthy_components": 3}
        }
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify mode-specific response
        assert data["execution_mode"] == "backtest"
        assert len(data["components"]) == 3  # Only backtest components
        assert "position_monitor" in data["components"]
        assert "data_provider" in data["components"]
        assert "risk_monitor" in data["components"]
        # Live-specific components should not be present
        assert "cex_execution_manager" not in data["components"]
        assert "onchain_execution_manager" not in data["components"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])