"""
Unit tests for API Endpoints component.

Tests API endpoint functionality in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch
import json
from fastapi.testclient import TestClient


class TestAPIEndpoints:
    """Test API Endpoints component in isolation."""
    
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
            assert data["status"] == "healthy"
    
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
            response = client.get("/api/strategies/")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            # Should include all 7 strategy modes
            strategy_names = [strategy["name"] for strategy in data]
            assert "pure_lending" in strategy_names
            assert "btc_basis" in strategy_names
            assert "eth_basis" in strategy_names
            assert "eth_staking_only" in strategy_names
            assert "eth_leveraged_staking" in strategy_names
            assert "usdt_market_neutral" in strategy_names
            assert "usdt_market_neutral_no_leverage" in strategy_names
    
    def test_strategy_parameters_endpoint(self, mock_config, mock_data_provider):
        """Test strategy parameters endpoint returns correct parameters."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/strategies/pure_lending/parameters")
            
            assert response.status_code == 200
            data = response.json()
            assert "strategy_mode" in data
            assert data["strategy_mode"] == "pure_lending"
            assert "parameters" in data
            assert isinstance(data["parameters"], dict)
    
    def test_backtest_execution_endpoint(self, mock_config, mock_data_provider):
        """Test backtest execution endpoint with valid parameters."""
        from backend.src.basis_strategy_v1.api.main import app
        
        backtest_request = {
            "strategy_mode": "pure_lending",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "initial_capital": 100000.0,
            "parameters": {
                "max_drawdown": 0.2,
                "leverage_enabled": False
            }
        }
        
        with TestClient(app) as client:
            with patch('backend.src.basis_strategy_v1.api.backtest.execute_backtest') as mock_backtest:
                mock_backtest.return_value = {
                    "backtest_id": "test_id_123",
                    "status": "completed",
                    "total_return": 0.05,
                    "sharpe_ratio": 1.2
                }
                
                response = client.post("/api/backtest/execute", json=backtest_request)
                
                assert response.status_code == 200
                data = response.json()
                assert "backtest_id" in data
                assert data["backtest_id"] == "test_id_123"
                assert data["status"] == "completed"
    
    def test_backtest_results_endpoint(self, mock_config, mock_data_provider):
        """Test backtest results retrieval endpoint."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            with patch('backend.src.basis_strategy_v1.api.backtest.get_backtest_results') as mock_results:
                mock_results.return_value = {
                    "backtest_id": "test_id_123",
                    "strategy_mode": "pure_lending",
                    "total_return": 0.05,
                    "sharpe_ratio": 1.2,
                    "max_drawdown": 0.02,
                    "positions": []
                }
                
                response = client.get("/api/backtest/results/test_id_123")
                
                assert response.status_code == 200
                data = response.json()
                assert data["backtest_id"] == "test_id_123"
                assert data["strategy_mode"] == "pure_lending"
                assert data["total_return"] == 0.05
    
    def test_live_trading_start_endpoint(self, mock_config, mock_data_provider):
        """Test live trading start endpoint."""
        from backend.src.basis_strategy_v1.api.main import app
        
        live_request = {
            "strategy_mode": "btc_basis",
            "parameters": {
                "max_drawdown": 0.15,
                "leverage_enabled": True
            }
        }
        
        with TestClient(app) as client:
            with patch('backend.src.basis_strategy_v1.api.live.start_live_trading') as mock_live:
                mock_live.return_value = {
                    "session_id": "live_session_123",
                    "status": "started",
                    "strategy_mode": "btc_basis"
                }
                
                response = client.post("/api/live/start", json=live_request)
                
                assert response.status_code == 200
                data = response.json()
                assert "session_id" in data
                assert data["session_id"] == "live_session_123"
                assert data["status"] == "started"
    
    def test_live_trading_stop_endpoint(self, mock_config, mock_data_provider):
        """Test live trading stop endpoint."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            with patch('backend.src.basis_strategy_v1.api.live.stop_live_trading') as mock_stop:
                mock_stop.return_value = {
                    "session_id": "live_session_123",
                    "status": "stopped",
                    "final_pnl": 1250.50
                }
                
                response = client.post("/api/live/stop/live_session_123")
                
                assert response.status_code == 200
                data = response.json()
                assert data["session_id"] == "live_session_123"
                assert data["status"] == "stopped"
                assert data["final_pnl"] == 1250.50
    
    def test_live_trading_status_endpoint(self, mock_config, mock_data_provider):
        """Test live trading status endpoint."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            with patch('backend.src.basis_strategy_v1.api.live.get_live_trading_status') as mock_status:
                mock_status.return_value = {
                    "session_id": "live_session_123",
                    "status": "running",
                    "current_pnl": 1250.50,
                    "active_positions": 3,
                    "daily_trades": 15
                }
                
                response = client.get("/api/live/status/live_session_123")
                
                assert response.status_code == 200
                data = response.json()
                assert data["session_id"] == "live_session_123"
                assert data["status"] == "running"
                assert data["current_pnl"] == 1250.50
                assert data["active_positions"] == 3
    
    def test_environment_info_endpoint(self, mock_config, mock_data_provider):
        """Test environment information endpoint."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/environment")
            
            assert response.status_code == 200
            data = response.json()
            assert "environment" in data
            assert "version" in data
            assert "config_loaded" in data
    
    def test_system_status_endpoint(self, mock_config, mock_data_provider):
        """Test system status endpoint."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "system_status" in data
            assert "components" in data
            assert "timestamp" in data
    
    def test_invalid_strategy_endpoint(self, mock_config, mock_data_provider):
        """Test API handles invalid strategy requests gracefully."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/api/strategies/invalid_strategy/parameters")
            
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert "not found" in data["error"].lower()
    
    def test_invalid_backtest_id_endpoint(self, mock_config, mock_data_provider):
        """Test API handles invalid backtest ID requests gracefully."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            with patch('backend.src.basis_strategy_v1.api.backtest.get_backtest_results') as mock_results:
                mock_results.return_value = None
                
                response = client.get("/api/backtest/results/invalid_id")
                
                assert response.status_code == 404
                data = response.json()
                assert "error" in data
                assert "not found" in data["error"].lower()
    
    def test_api_error_handling(self, mock_config, mock_data_provider):
        """Test API error handling and proper HTTP status codes."""
        from backend.src.basis_strategy_v1.api.main import app
        
        with TestClient(app) as client:
            # Test malformed JSON request
            response = client.post(
                "/api/backtest/execute",
                data="invalid json",
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 422  # Unprocessable Entity
            
            # Test missing required fields
            incomplete_request = {
                "strategy_mode": "pure_lending"
                # Missing required fields
            }
            
            response = client.post("/api/backtest/execute", json=incomplete_request)
            
            assert response.status_code == 422  # Unprocessable Entity
