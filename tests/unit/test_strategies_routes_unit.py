"""
Unit tests for Strategies Routes API endpoints.

Tests strategies API endpoints in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from fastapi import FastAPI
from pathlib import Path
import yaml

# Import the routes module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend' / 'src'))

from basis_strategy_v1.api.routes.strategies import router
from basis_strategy_v1.api.models.responses import (
    StandardResponse,
    StrategyInfoResponse,
    StrategyListResponse
)


class TestStrategiesRoutes:
    """Test strategies API endpoints."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with strategies routes."""
        app = FastAPI()
        app.include_router(router, prefix="/strategies")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_strategy_config(self):
        """Mock strategy configuration."""
        return {
            "strategy": {
                "share_class": "USDT",
                "target_apy": 0.1,
                "lending_enabled": True,
                "staking_enabled": False,
                "staking_leverage_enabled": False,
                "basis_trade_enabled": False
            },
            "backtest": {
                "initial_capital": 10000,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        }

    @pytest.fixture
    def mock_mode_config(self):
        """Mock mode configuration."""
        return {
            "mode": "pure_lending_usdt",
            "description": "Pure lending strategy",
            "target_apy": 0.08,
            "max_drawdown": 0.15,
            "share_class": "USDT",
            "leverage_enabled": False,
            "lending_enabled": True,
            "staking_enabled": False,
            "basis_trade_enabled": False
        }

    def test_list_strategies_success(self, client, mock_strategy_config):
        """Test successful strategies listing."""
        with patch('basis_strategy_v1.api.routes.strategies.get_available_strategies', return_value=["pure_lending_usdt", "btc_basis"]):
            with patch('basis_strategy_v1.api.routes.strategies.load_merged_strategy_config') as mock_load:
                mock_load.return_value = mock_strategy_config
                response = client.get("/strategies/")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]["strategies"]) == 2
                assert data["data"]["total"] == 2
                assert data["data"]["strategies"][0]["name"] == "pure_lending_usdt"
                assert data["data"]["strategies"][0]["share_class"] == "USDT"

    def test_list_strategies_with_filters(self, client, mock_strategy_config):
        """Test strategies listing with filters."""
        with patch('basis_strategy_v1.api.routes.strategies.get_available_strategies', return_value=["pure_lending_usdt", "eth_basis"]):
            with patch('basis_strategy_v1.api.routes.strategies.load_merged_strategy_config') as mock_load:
                # First strategy matches filter, second doesn't
                mock_load.side_effect = [
                    mock_strategy_config,  # pure_lending_usdt - USDT
                    {**mock_strategy_config, "strategy": {**mock_strategy_config["strategy"], "share_class": "ETH"}}  # eth_basis - ETH
                ]
                response = client.get("/strategies/?share_class=USDT")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]["strategies"]) == 1
                assert data["data"]["strategies"][0]["share_class"] == "USDT"

    def test_list_strategies_no_strategies_found(self, client):
        """Test strategies listing when no strategies are found."""
        with patch('basis_strategy_v1.api.routes.strategies.get_available_strategies', return_value=[]):
            response = client.get("/strategies/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["strategies"]) == 0
            assert data["data"]["total"] == 0

    def test_list_strategies_config_load_error(self, client):
        """Test strategies listing when config loading fails."""
        with patch('basis_strategy_v1.api.routes.strategies.get_available_strategies', return_value=["pure_lending_usdt"]):
            with patch('basis_strategy_v1.api.routes.strategies.load_merged_strategy_config', return_value=None):
                response = client.get("/strategies/")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]["strategies"]) == 0

    # Removed: validate_strategy_config tests - endpoint removed as redundant
    # Config validation happens at startup via Pydantic models
    # Runtime parameters come from API calls, not config validation

    def test_get_strategy_parameters_success(self, client, mock_strategy_config):
        """Test successful strategy parameters retrieval."""
        with patch('basis_strategy_v1.api.routes.strategies.validate_strategy_name'):
            with patch('basis_strategy_v1.api.routes.strategies.load_merged_strategy_config', return_value=mock_strategy_config):
                response = client.get("/strategies/pure_lending_usdt/parameters")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "strategy" in data["data"]
                assert "backtest" in data["data"]
                assert data["data"]["strategy"]["share_class"]["default"] == "USDT"
                assert data["data"]["backtest"]["initial_capital"]["default"] == 10000

    def test_get_strategy_parameters_invalid_name(self, client):
        """Test strategy parameters retrieval with invalid strategy name."""
        with patch('basis_strategy_v1.api.routes.strategies.validate_strategy_name', side_effect=ValueError("Invalid strategy name")):
            response = client.get("/strategies/invalid_strategy/parameters")
            
            assert response.status_code == 404
            data = response.json()
            assert "Invalid strategy name" in data["detail"]

    def test_get_strategy_parameters_not_found(self, client):
        """Test strategy parameters retrieval for non-existent strategy."""
        with patch('basis_strategy_v1.api.routes.strategies.validate_strategy_name'):
            with patch('basis_strategy_v1.api.routes.strategies.load_merged_strategy_config', return_value=None):
                response = client.get("/strategies/nonexistent/parameters")
                
                assert response.status_code == 404
                data = response.json()
                assert "Strategy config not found" in data["detail"]

    def test_get_strategy_success(self, client, mock_strategy_config):
        """Test successful strategy details retrieval."""
        with patch('basis_strategy_v1.api.routes.strategies.validate_strategy_name'):
            with patch('basis_strategy_v1.api.routes.strategies.load_merged_strategy_config', return_value=mock_strategy_config):
                response = client.get("/strategies/pure_lending_usdt")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["name"] == "pure_lending_usdt"
                assert data["data"]["share_class"] == "USDT"
                assert data["data"]["risk_level"] == "low"
                assert "lending" in data["data"]["parameters"]["strategy_type"]

    def test_get_strategy_invalid_name(self, client):
        """Test strategy details retrieval with invalid strategy name."""
        with patch('basis_strategy_v1.api.routes.strategies.validate_strategy_name', side_effect=ValueError("Invalid strategy name")):
            response = client.get("/strategies/invalid_strategy")
            
            assert response.status_code == 404
            data = response.json()
            assert "Invalid strategy name" in data["detail"]

    def test_get_strategy_not_found(self, client):
        """Test strategy details retrieval for non-existent strategy."""
        with patch('basis_strategy_v1.api.routes.strategies.validate_strategy_name'):
            with patch('basis_strategy_v1.api.routes.strategies.load_merged_strategy_config', return_value=None):
                response = client.get("/strategies/nonexistent")
                
                assert response.status_code == 404
                data = response.json()
                assert "Strategy config file not found or invalid" in data["detail"]

    def test_get_merged_config_success(self, client, mock_strategy_config):
        """Test successful merged config retrieval."""
        with patch('basis_strategy_v1.api.routes.strategies.validate_strategy_name'):
            with patch('basis_strategy_v1.api.routes.strategies.load_merged_strategy_config', return_value=mock_strategy_config):
                response = client.get("/strategies/pure_lending_usdt/config/merged?start_date=2024-01-01&end_date=2024-12-31&initial_capital=20000&share_class=ETH")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["strategy_name"] == "pure_lending_usdt"
                assert "config_json" in data["data"]
                assert "config_yaml" in data["data"]
                assert data["data"]["config_json"]["backtest"]["initial_capital"] == 20000.0
                assert data["data"]["config_json"]["strategy"]["share_class"] == "ETH"

    def test_get_merged_config_invalid_name(self, client):
        """Test merged config retrieval with invalid strategy name."""
        with patch('basis_strategy_v1.api.routes.strategies.validate_strategy_name', side_effect=ValueError("Invalid strategy name")):
            response = client.get("/strategies/invalid_strategy/config/merged")
            
            assert response.status_code == 404
            data = response.json()
            assert "Invalid strategy name" in data["detail"]

    def test_get_mode_config_success(self, client, mock_mode_config):
        """Test successful mode configuration retrieval."""
        with patch('basis_strategy_v1.api.routes.strategies.Path') as mock_path:
            mock_config_file = Mock()
            mock_config_file.exists.return_value = True
            mock_config_file.open.return_value.__enter__.return_value.read.return_value = yaml.dump(mock_mode_config)
            mock_path.return_value = mock_config_file
            
            response = client.get("/strategies/modes/pure_lending_usdt")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["mode"] == "pure_lending_usdt"
            assert data["data"]["target_apy"] == 0.08
            assert data["data"]["max_drawdown"] == 0.15
            assert data["data"]["share_class"] == "USDT"
            assert data["data"]["risk_level"] == "medium"

    def test_get_mode_config_not_found(self, client):
        """Test mode configuration retrieval for non-existent mode."""
        with patch('basis_strategy_v1.api.routes.strategies.Path') as mock_path:
            mock_config_file = Mock()
            mock_config_file.exists.return_value = False
            mock_path.return_value = mock_config_file
            
            response = client.get("/strategies/modes/nonexistent_mode")
            
            assert response.status_code == 404
            data = response.json()
            assert "Mode config not found" in data["detail"]

    def test_list_modes_success(self, client, mock_mode_config):
        """Test successful modes listing."""
        with patch('basis_strategy_v1.api.routes.strategies.Path') as mock_path:
            mock_modes_dir = Mock()
            mock_modes_dir.exists.return_value = True
            mock_yaml_file = Mock()
            mock_yaml_file.stem = "pure_lending_usdt"
            mock_yaml_file.open.return_value.__enter__.return_value.read.return_value = yaml.dump(mock_mode_config)
            mock_modes_dir.glob.return_value = [mock_yaml_file]
            mock_path.return_value = mock_modes_dir
            
            response = client.get("/strategies/modes/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["modes"]) == 1
            assert data["data"]["total"] == 1
            assert data["data"]["modes"][0]["mode"] == "pure_lending_usdt"

    def test_list_modes_with_filter(self, client, mock_mode_config):
        """Test modes listing with share class filter."""
        with patch('basis_strategy_v1.api.routes.strategies.Path') as mock_path:
            mock_modes_dir = Mock()
            mock_modes_dir.exists.return_value = True
            mock_yaml_file = Mock()
            mock_yaml_file.stem = "pure_lending_usdt"
            mock_yaml_file.open.return_value.__enter__.return_value.read.return_value = yaml.dump(mock_mode_config)
            mock_modes_dir.glob.return_value = [mock_yaml_file]
            mock_path.return_value = mock_modes_dir
            
            response = client.get("/strategies/modes/?share_class=USDT")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["modes"]) == 1

    def test_list_modes_directory_not_found(self, client):
        """Test modes listing when modes directory doesn't exist."""
        with patch('basis_strategy_v1.api.routes.strategies.Path') as mock_path:
            mock_modes_dir = Mock()
            mock_modes_dir.exists.return_value = False
            mock_path.return_value = mock_modes_dir
            
            response = client.get("/strategies/modes/")
            
            assert response.status_code == 404
            data = response.json()
            assert "Modes directory not found" in data["detail"]

    def test_correlation_id_handling(self, client, mock_strategy_config):
        """Test that correlation IDs are properly handled."""
        with patch('basis_strategy_v1.api.routes.strategies.get_available_strategies', return_value=["pure_lending_usdt"]):
            with patch('basis_strategy_v1.api.routes.strategies.load_merged_strategy_config', return_value=mock_strategy_config):
                response = client.get("/strategies/")
                
                assert response.status_code == 200
                data = response.json()
                assert "correlation_id" in data
                assert data["correlation_id"] is not None

    def test_error_handling_with_logging(self, client):
        """Test that errors are properly logged and handled."""
        with patch('basis_strategy_v1.api.routes.strategies.get_available_strategies', side_effect=Exception("Test error")):
            with patch('basis_strategy_v1.api.routes.strategies.logger') as mock_logger:
                response = client.get("/strategies/")
                
                assert response.status_code == 500
                # Verify error was logged
                mock_logger.error.assert_called_once()
                call_args = mock_logger.error.call_args
                assert "Failed to list strategies" in call_args[0][0]

    def test_strategy_info_derivation(self, client):
        """Test strategy information derivation from config."""
        high_risk_config = {
            "strategy": {
                "share_class": "ETH",
                "staking_leverage_enabled": True,
                "basis_trade_enabled": True,
                "lending_enabled": False,
                "staking_enabled": True
            },
            "backtest": {
                "initial_capital": 50000
            }
        }
        
        with patch('basis_strategy_v1.api.routes.strategies.get_available_strategies', return_value=["eth_basis"]):
            with patch('basis_strategy_v1.api.routes.strategies.load_merged_strategy_config', return_value=high_risk_config):
                response = client.get("/strategies/")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                strategy_info = data["data"]["strategies"][0]
                assert strategy_info["risk_level"] == "high"
                assert strategy_info["share_class"] == "ETH"
                assert "leverage" in strategy_info["parameters"]["strategy_type"]
                assert "basis_trading" in strategy_info["parameters"]["strategy_type"]
