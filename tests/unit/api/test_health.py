"""
Test Health API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
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
    
    def test_basic_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "timestamp" in data
        assert "components" in data
        assert "metrics" in data
        
        # Verify status
        assert data["status"] == "healthy"
        
        # Verify components
        assert "service" in data["components"]
        assert "api" in data["components"]
        assert "system" in data["components"]
        
        # Verify metrics
        assert "cpu_percent" in data["metrics"]
        assert "memory_percent" in data["metrics"]
        assert "memory_available_gb" in data["metrics"]
    
    def test_detailed_health_check(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "timestamp" in data
        assert "components" in data
        assert "metrics" in data
        
        # Verify status
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_health_check_with_mock_metrics(self, mock_memory, mock_cpu, client):
        """Test health check with mocked system metrics."""
        # Mock system metrics
        mock_cpu.return_value = 25.5
        mock_memory.return_value = Mock(
            percent=60.0,
            available=8 * 1024**3  # 8GB
        )
        
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify mocked metrics
        assert data["metrics"]["cpu_percent"] == 25.5
        assert data["metrics"]["memory_percent"] == 60.0
        assert data["metrics"]["memory_available_gb"] == 8.0
    
    def test_health_check_error_handling(self, client):
        """Test health check error handling."""
        with patch('psutil.cpu_percent', side_effect=Exception("System error")):
            response = client.get("/health/")
            
            # Should still return 200 with basic health info
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])