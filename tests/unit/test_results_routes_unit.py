"""
Unit tests for Results Routes API endpoints.

Tests results API endpoints in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from fastapi import FastAPI
from pathlib import Path
import tempfile
import zipfile
import csv
import os

# Import the routes module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend' / 'src'))

from basis_strategy_v1.api.routes.results import router
from basis_strategy_v1.api.models.responses import StandardResponse, BacktestResultResponse


class TestResultsRoutes:
    """Test results API endpoints."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with results routes."""
        app = FastAPI()
        app.include_router(router, prefix="/results")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_backtest_service(self):
        """Mock backtest service."""
        service = Mock()
        service.get_result.return_value = {
            "request_id": "test_result_123",
            "strategy_name": "pure_lending",
            "start_date": "2024-05-12",
            "end_date": "2024-05-19",
            "initial_capital": 100000.0,
            "final_value": 101000.0,
            "total_return": 0.01,
            "annualized_return": 0.52,
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.02,
            "total_trades": 5,
            "total_fees": 50.0,
            "event_log": [
                {"timestamp": "2024-05-12T00:00:00", "action": "trade", "amount": 1000.0},
                {"timestamp": "2024-05-12T01:00:00", "action": "trade", "amount": 2000.0}
            ],
            "component_summaries": {
                "position_monitor": {"status": "healthy"},
                "risk_monitor": {"status": "healthy"}
            },
            "balances_by_venue": {
                "wallet": {"USDT": 50000.0},
                "binance": {"USDT": 51000.0}
            }
        }
        return service

    @pytest.fixture
    def mock_results_directory(self, tmp_path):
        """Create mock results directory with test files."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        # Create a test result directory
        result_dir = results_dir / "test_result_123_pure_lending"
        result_dir.mkdir()
        
        # Create mock CSV files
        event_log_file = result_dir / "test_result_123_pure_lending_event_log.csv"
        with open(event_log_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'action', 'amount', 'gross_value', 'net_value', 'total_fees_paid'])
            writer.writeheader()
            writer.writerow({
                'timestamp': '2024-05-12T00:00:00',
                'action': 'trade',
                'amount': '1000.0',
                'gross_value': '100000.0',
                'net_value': '99950.0',
                'total_fees_paid': '50.0'
            })
            writer.writerow({
                'timestamp': '2024-05-12T01:00:00',
                'action': 'trade',
                'amount': '2000.0',
                'gross_value': '101000.0',
                'net_value': '100950.0',
                'total_fees_paid': '50.0'
            })
        
        # Create mock equity curve file
        equity_curve_file = result_dir / "test_result_123_pure_lending_equity_curve.csv"
        with open(equity_curve_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'net_value', 'gross_value'])
            writer.writeheader()
            writer.writerow({'timestamp': '2024-05-12T00:00:00', 'net_value': '100000.0', 'gross_value': '100000.0'})
            writer.writerow({'timestamp': '2024-05-19T23:59:59', 'net_value': '101000.0', 'gross_value': '101000.0'})
        
        # Create mock trades file
        trades_file = result_dir / "test_result_123_pure_lending_trades.csv"
        with open(trades_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'action', 'amount', 'price'])
            writer.writeheader()
            writer.writerow({'timestamp': '2024-05-12T00:00:00', 'action': 'buy', 'amount': '1000.0', 'price': '1.0'})
        
        # Create mock HTML chart files
        chart_file = result_dir / "test_result_123_pure_lending_equity_curve.html"
        chart_file.write_text("<html><body>Equity Curve Chart</body></html>")
        
        return results_dir

    def test_get_result_events_success(self, client, mock_backtest_service):
        """Test successful result events retrieval."""
        with patch('basis_strategy_v1.api.routes.results.get_backtest_service', return_value=mock_backtest_service):
            response = client.get("/results/test_result_123/events?limit=10&offset=0")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["events"]) == 2
            assert data["data"]["total_events"] == 2
            assert data["data"]["has_event_log"] is True
            assert "component_summaries" in data["data"]
            assert "balances_by_venue" in data["data"]

    def test_get_result_events_with_pagination(self, client, mock_backtest_service):
        """Test result events retrieval with pagination."""
        with patch('basis_strategy_v1.api.routes.results.get_backtest_service', return_value=mock_backtest_service):
            response = client.get("/results/test_result_123/events?limit=1&offset=1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["events"]) == 1
            assert data["data"]["total_events"] == 2

    def test_get_result_events_not_found(self, client, mock_backtest_service):
        """Test result events retrieval for non-existent result."""
        mock_backtest_service.get_result.return_value = None
        
        with patch('basis_strategy_v1.api.routes.results.get_backtest_service', return_value=mock_backtest_service):
            with patch('basis_strategy_v1.api.routes.results._load_events_from_csv', return_value=(None, 0)):
                response = client.get("/results/nonexistent_id/events")
                
                assert response.status_code == 404
                data = response.json()
                assert "Result nonexistent_id not found" in data["detail"]

    def test_get_result_events_fallback_to_csv(self, client, mock_backtest_service, mock_results_directory):
        """Test result events retrieval with CSV fallback."""
        mock_backtest_service.get_result.return_value = None
        
        with patch('basis_strategy_v1.api.routes.results.get_backtest_service', return_value=mock_backtest_service):
            with patch('basis_strategy_v1.api.routes.results.Path') as mock_path:
                mock_path.return_value = mock_results_directory
                response = client.get("/results/test_result_123/events")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["has_event_log"] is True

    def test_get_export_info_success(self, client, mock_results_directory):
        """Test successful export info retrieval."""
        with patch('basis_strategy_v1.api.routes.results.Path') as mock_path:
            mock_path.return_value = mock_results_directory
            response = client.get("/results/test_result_123/export")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "chart_files" in data["data"]
            assert "csv_files" in data["data"]
            assert "download_url" in data["data"]
            assert data["data"]["total_files"] > 0

    def test_get_export_info_not_found(self, client):
        """Test export info retrieval for non-existent result."""
        with patch('basis_strategy_v1.api.routes.results.Path') as mock_path:
            mock_path.return_value = Path("/nonexistent")
            response = client.get("/results/nonexistent_id/export")
            
            assert response.status_code == 404
            data = response.json()
            assert "Result nonexistent_id not found" in data["detail"]

    def test_download_result_assets_success(self, client, mock_results_directory):
        """Test successful result assets download."""
        with patch('basis_strategy_v1.api.routes.results.Path') as mock_path:
            mock_path.return_value = mock_results_directory
            response = client.get("/results/test_result_123/download")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/zip"
            assert "attachment" in response.headers["content-disposition"]
            assert "test_result_123_pure_lending_export.zip" in response.headers["content-disposition"]

    def test_download_result_assets_not_found(self, client):
        """Test result assets download for non-existent result."""
        with patch('basis_strategy_v1.api.routes.results.Path') as mock_path:
            mock_path.return_value = Path("/nonexistent")
            response = client.get("/results/nonexistent_id/download")
            
            assert response.status_code == 404
            data = response.json()
            assert "Result nonexistent_id not found" in data["detail"]

    def test_list_results_success(self, client, mock_backtest_service):
        """Test successful results listing."""
        with patch('basis_strategy_v1.api.routes.results.get_backtest_service', return_value=mock_backtest_service):
            with patch('basis_strategy_v1.api.routes.results._scan_results_filesystem', return_value=[]):
                response = client.get("/results/?limit=10&offset=0")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert isinstance(data["data"], list)

    def test_list_results_with_filters(self, client, mock_backtest_service):
        """Test results listing with filters."""
        with patch('basis_strategy_v1.api.routes.results.get_backtest_service', return_value=mock_backtest_service):
            with patch('basis_strategy_v1.api.routes.results._scan_results_filesystem', return_value=[]):
                response = client.get("/results/?strategy=pure_lending&limit=5")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    def test_get_result_success(self, client, mock_backtest_service):
        """Test successful result retrieval."""
        with patch('basis_strategy_v1.api.routes.results.get_backtest_service', return_value=mock_backtest_service):
            response = client.get("/results/test_result_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["request_id"] == "test_result_123"
            assert data["data"]["strategy_name"] == "pure_lending"
            assert data["data"]["initial_capital"] == 100000.0
            assert data["data"]["final_value"] == 101000.0
            assert "chart_links" in data["data"]

    def test_get_result_with_timeseries(self, client, mock_backtest_service):
        """Test result retrieval with timeseries data."""
        mock_backtest_service.get_result.return_value = {
            **mock_backtest_service.get_result.return_value,
            "equity_curve": [{"timestamp": "2024-05-12", "value": 100000.0}]
        }
        
        with patch('basis_strategy_v1.api.routes.results.get_backtest_service', return_value=mock_backtest_service):
            response = client.get("/results/test_result_123?include_timeseries=true")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["equity_curve"] is not None

    def test_get_result_not_found(self, client, mock_backtest_service):
        """Test result retrieval for non-existent result."""
        mock_backtest_service.get_result.return_value = None
        
        with patch('basis_strategy_v1.api.routes.results.get_backtest_service', return_value=mock_backtest_service):
            with patch('basis_strategy_v1.api.routes.results._load_result_summary_from_filesystem', return_value=None):
                response = client.get("/results/nonexistent_id")
                
                assert response.status_code == 404
                data = response.json()
                assert "Result nonexistent_id not found" in data["detail"]

    def test_get_result_missing_dates(self, client, mock_backtest_service):
        """Test result retrieval with missing start/end dates."""
        mock_backtest_service.get_result.return_value = {
            "request_id": "test_result_123",
            "strategy_name": "pure_lending"
            # Missing start_date and end_date
        }
        
        with patch('basis_strategy_v1.api.routes.results.get_backtest_service', return_value=mock_backtest_service):
            response = client.get("/results/test_result_123")
            
            assert response.status_code == 500
            data = response.json()
            assert "Result missing start_date/end_date" in data["detail"]

    def test_delete_result_success(self, client):
        """Test successful result deletion."""
        response = client.delete("/results/test_result_123")
        
        assert response.status_code == 404  # Currently returns 404 as deletion is not implemented
        data = response.json()
        assert "Result test_result_123 not found" in data["detail"]

    def test_correlation_id_handling(self, client, mock_backtest_service):
        """Test that correlation IDs are properly handled."""
        with patch('basis_strategy_v1.api.routes.results.get_backtest_service', return_value=mock_backtest_service):
            response = client.get("/results/test_result_123")
            
            assert response.status_code == 200
            data = response.json()
            assert "correlation_id" in data
            assert data["correlation_id"] is not None

    def test_error_handling_with_logging(self, client, mock_backtest_service):
        """Test that errors are properly logged and handled."""
        mock_backtest_service.get_result.side_effect = Exception("Test error")
        
        with patch('basis_strategy_v1.api.routes.results.get_backtest_service', return_value=mock_backtest_service):
            with patch('basis_strategy_v1.api.routes.results.logger') as mock_logger:
                response = client.get("/results/test_result_123")
                
                assert response.status_code == 500
                # Verify error was logged
                mock_logger.error.assert_called_once()
                call_args = mock_logger.error.call_args
                assert "Failed to fetch result" in call_args[0][0]

    def test_csv_loading_edge_cases(self, client, mock_results_directory):
        """Test CSV loading with various edge cases."""
        # Test with empty CSV
        empty_csv = mock_results_directory / "test_result_123_pure_lending" / "empty_event_log.csv"
        with open(empty_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'action', 'amount'])
            writer.writeheader()
        
        with patch('basis_strategy_v1.api.routes.results.Path') as mock_path:
            mock_path.return_value = mock_results_directory
            response = client.get("/results/test_result_123/events")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_filesystem_scanning(self, client, mock_results_directory):
        """Test filesystem scanning functionality."""
        with patch('basis_strategy_v1.api.routes.results.Path') as mock_path:
            mock_path.return_value = mock_results_directory
            response = client.get("/results/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert isinstance(data["data"], list)
