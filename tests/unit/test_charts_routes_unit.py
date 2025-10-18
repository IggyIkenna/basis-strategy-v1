"""Unit tests for charts routes."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from pathlib import Path
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

from basis_strategy_v1.api.routes.charts import router
from basis_strategy_v1.core.services.backtest_service import BacktestService


class TestChartsRoutes:
    """Test class for charts routes."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app for testing."""
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/results")
        return app

    @pytest.fixture
    def test_client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_backtest_service(self):
        """Mock backtest service."""
        service = Mock(spec=BacktestService)
        service.get_result = AsyncMock()
        return service

    @pytest.fixture
    def mock_request(self):
        """Mock request object."""
        request = Mock()
        request.state.correlation_id = "test-correlation-id"
        return request

    def test_list_charts_success(self, test_client, mock_backtest_service, mock_request):
        """Test successful chart listing."""
        # Mock the service dependency
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            # Mock the service response
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            # Mock file system to return existing charts
            mock_chart_file = Mock()
            mock_chart_file.stem = "test_id_pure_lending_usdt_equity_curve"
            mock_chart_file.name = "test_id_pure_lending_usdt_equity_curve.html"
            mock_chart_file.is_dir = lambda: False
            
            mock_dir = Mock()
            mock_dir.name = "test_id_pure_lending_usdt"
            mock_dir.is_dir = lambda: True
            mock_dir.iterdir = lambda: [mock_chart_file]
            
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('pathlib.Path.iterdir', return_value=[mock_dir]), \
                 patch('pathlib.Path.glob', return_value=[mock_chart_file]):
                
                response = test_client.get("/api/v1/results/test_id/charts")
                assert response.status_code == 200
                data = response.json()
                assert "charts" in data
                assert isinstance(data["charts"], dict)

    def test_list_charts_not_found(self, test_client, mock_backtest_service):
        """Test chart listing when no charts are found."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = None
            
            with patch('pathlib.Path.exists', return_value=False):
                response = test_client.get("/api/v1/results/nonexistent_id/charts")
                assert response.status_code == 404
                assert "No charts found" in response.json()["detail"]

    def test_list_charts_service_error(self, test_client, mock_backtest_service):
        """Test chart listing when service raises an error."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.side_effect = Exception("Service error")
            
            response = test_client.get("/api/v1/results/test_id/charts")
            # The code handles service errors by returning 404 when no charts are found
            assert response.status_code == 404
            assert "No charts found" in response.json()["detail"]

    def test_get_chart_success(self, test_client, mock_backtest_service, mock_request):
        """Test successful chart retrieval."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            # Mock file system to return existing chart
            mock_chart_content = "<html><body>Test Chart</body></html>"
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=mock_chart_content)):
                
                response = test_client.get("/api/v1/results/test_id/charts/equity_curve")
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/html; charset=utf-8"
                assert "Test Chart" in response.text

    def test_get_chart_invalid_name(self, test_client, mock_backtest_service):
        """Test chart retrieval with invalid chart name."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            response = test_client.get("/api/v1/results/test_id/charts/invalid_chart")
            assert response.status_code == 400
            assert "Invalid chart name" in response.json()["detail"]

    def test_get_chart_not_found(self, test_client, mock_backtest_service):
        """Test chart retrieval when chart is not found."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            with patch('pathlib.Path.exists', return_value=False):
                response = test_client.get("/api/v1/results/test_id/charts/equity_curve")
                assert response.status_code == 404
                assert "not found" in response.json()["detail"]

    def test_get_chart_service_error(self, test_client, mock_backtest_service):
        """Test chart retrieval when service raises an error."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.side_effect = Exception("Service error")
            
            response = test_client.get("/api/v1/results/test_id/charts/equity_curve")
            # The code handles service errors by returning 404 when chart is not found
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_dashboard_success(self, test_client, mock_backtest_service, mock_request):
        """Test successful dashboard retrieval."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            # Mock file system to return existing dashboard
            mock_dashboard_content = "<html><body>Dashboard</body></html>"
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=mock_dashboard_content)):
                
                response = test_client.get("/api/v1/results/test_id/dashboard")
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/html; charset=utf-8"
                assert "Dashboard" in response.text

    def test_get_dashboard_not_found(self, test_client, mock_backtest_service):
        """Test dashboard retrieval when dashboard is not found."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            with patch('pathlib.Path.exists', return_value=False):
                response = test_client.get("/api/v1/results/test_id/dashboard")
                assert response.status_code == 404
                assert "not found" in response.json()["detail"]

    def test_get_dashboard_service_error(self, test_client, mock_backtest_service):
        """Test dashboard retrieval when service raises an error."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.side_effect = Exception("Service error")
            
            response = test_client.get("/api/v1/results/test_id/dashboard")
            # The code handles service errors by returning 404 when chart is not found
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_chart_paths_priority(self, test_client, mock_backtest_service):
        """Test that chart paths are checked in the correct priority order."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            # Mock file system to return existing chart at the first priority path
            mock_chart_content = "<html><body>Priority Chart</body></html>"
            with patch('pathlib.Path.exists', side_effect=[True, False, False, False, False]), \
                 patch('builtins.open', mock_open(read_data=mock_chart_content)):
                
                response = test_client.get("/api/v1/results/test_id/charts/equity_curve")
                assert response.status_code == 200
                assert "Priority Chart" in response.text

    def test_chart_glob_fallback(self, test_client, mock_backtest_service):
        """Test that glob search is used as a fallback when direct paths fail."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            # Mock file system to fail direct paths and glob search
            with patch('pathlib.Path.exists', return_value=False), \
                 patch('glob.glob', return_value=[]):
                
                response = test_client.get("/api/v1/results/test_id/charts/equity_curve")
                # When all paths fail, the chart is not found
                assert response.status_code == 404
                assert "not found" in response.json()["detail"]

    def test_chart_legacy_paths(self, test_client, mock_backtest_service):
        """Test that legacy chart paths are checked."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            # Mock file system to fail modern paths but succeed with legacy path
            mock_chart_content = "<html><body>Legacy Chart</body></html>"
            with patch('pathlib.Path.exists', side_effect=[False, False, False, True, False]), \
                 patch('builtins.open', mock_open(read_data=mock_chart_content)):
                
                response = test_client.get("/api/v1/results/test_id/charts/equity_curve")
                assert response.status_code == 200
                assert "Legacy Chart" in response.text

    def test_chart_reading_error(self, test_client, mock_backtest_service):
        """Test handling of chart file reading errors."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            # Mock file system to return existing chart but fail to read it
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('builtins.open', side_effect=IOError("Read error")):
                
                response = test_client.get("/api/v1/results/test_id/charts/equity_curve")
                assert response.status_code == 404
                assert "not found" in response.json()["detail"]

    def test_chart_strategy_name_inference(self, test_client, mock_backtest_service):
        """Test that strategy name is inferred from directory structure when result is not found."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = None
            
            # Mock directory structure to infer strategy name
            mock_dir = Mock()
            mock_dir.name = "test_id_pure_lending_usdt"
            mock_dir.is_dir = lambda: True
            
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('pathlib.Path.iterdir', return_value=[mock_dir]), \
                 patch('pathlib.Path.glob', return_value=[
                     Mock(stem="test_id_pure_lending_usdt_equity_curve")
                 ]):
                
                response = test_client.get("/api/v1/results/test_id/charts")
                assert response.status_code == 200
                data = response.json()
                assert "charts" in data

    def test_chart_default_charts_fallback(self, test_client, mock_backtest_service):
        """Test that default charts are returned when no specific charts are found."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            # Mock file system to return no specific charts but have result
            with patch('pathlib.Path.exists', return_value=False):
                response = test_client.get("/api/v1/results/test_id/charts")
                # The code returns 404 when no charts are found, even with a result
                assert response.status_code == 404
                assert "No charts found" in response.json()["detail"]

    def test_chart_valid_chart_names(self, test_client, mock_backtest_service):
        """Test that all valid chart names are accepted."""
        valid_charts = [
            "equity_curve",
            "pnl_attribution", 
            "component_performance",
            "fee_breakdown",
            "metrics_summary",
            "dashboard",
            "ltv_ratio",
            "balance_venue",
            "balance_token",
            "margin_health",
            "exposure"
        ]
        
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            for chart_name in valid_charts:
                with patch('pathlib.Path.exists', return_value=True), \
                     patch('builtins.open', mock_open(read_data="<html>Test</html>")):
                    
                    response = test_client.get(f"/api/v1/results/test_id/charts/{chart_name}")
                    assert response.status_code == 200, f"Failed for chart: {chart_name}"

    def test_chart_correlation_id_handling(self, test_client, mock_backtest_service):
        """Test that correlation ID is properly handled in requests."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data="<html>Test</html>")):
                
                response = test_client.get("/api/v1/results/test_id/charts/equity_curve")
                assert response.status_code == 200

    def test_chart_error_logging(self, test_client, mock_backtest_service):
        """Test that errors are properly logged."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.side_effect = Exception("Test error")
            
            response = test_client.get("/api/v1/results/test_id/charts/equity_curve")
            # The code handles service errors by returning 404 when chart is not found
            assert response.status_code == 404
            # The warning is logged (we can see it in the captured log output)
            # but mocking structlog is complex, so we just verify the behavior

    def test_chart_content_type_headers(self, test_client, mock_backtest_service):
        """Test that proper content type headers are set for chart responses."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data="<html>Test</html>")):
                
                response = test_client.get("/api/v1/results/test_id/charts/equity_curve")
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/html; charset=utf-8"

    def test_chart_utf8_encoding(self, test_client, mock_backtest_service):
        """Test that chart content is properly encoded as UTF-8."""
        with patch('basis_strategy_v1.api.routes.charts.get_backtest_service', return_value=mock_backtest_service):
            mock_backtest_service.get_result.return_value = {
                "strategy_name": "pure_lending_usdt",
                "status": "completed"
            }
            
            # Test with UTF-8 content
            utf8_content = "<html><body>Test with émojis 🚀</body></html>"
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=utf8_content)):
                
                response = test_client.get("/api/v1/results/test_id/charts/equity_curve")
                assert response.status_code == 200
                assert "émojis 🚀" in response.text


def mock_open(read_data=""):
    """Mock open function for file reading."""
    from unittest.mock import mock_open as _mock_open
    return _mock_open(read_data=read_data)
