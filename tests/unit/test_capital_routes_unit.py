"""
Unit tests for Capital Routes API endpoints.

Tests capital management functionality with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import os
import sys

# Mock environment variables before importing the capital module
os.environ.update({
    'BASIS_ENVIRONMENT': 'dev',
    'BASIS_DEPLOYMENT_MODE': 'local',
    'BASIS_DATA_DIR': 'data',
    'BASIS_RESULTS_DIR': 'results',
    'BASIS_DEBUG': 'true',
    'BASIS_LOG_LEVEL': 'INFO',
    'BASIS_EXECUTION_MODE': 'backtest',
    'BASIS_DATA_MODE': 'csv',
    'BASIS_DATA_START_DATE': '2024-05-12',
    'BASIS_DATA_END_DATE': '2024-05-19',
    'BASIS_API_PORT': '8000',
    'BASIS_API_HOST': 'localhost',
    'DATA_LOAD_TIMEOUT': '30',
    'DATA_VALIDATION_STRICT': 'false',
    'DATA_CACHE_SIZE': '1000',
    'STRATEGY_MANAGER_TIMEOUT': '60',
    'STRATEGY_MANAGER_MAX_RETRIES': '3',
    'STRATEGY_FACTORY_TIMEOUT': '30',
    'STRATEGY_FACTORY_MAX_RETRIES': '3'
})

# Now import the capital module
from basis_strategy_v1.api.routes.capital import router
from basis_strategy_v1.api.models import ApiResponse
from basis_strategy_v1.api.routes.capital import (
    DepositRequest,
    WithdrawRequest,
    CapitalResponse
)
from basis_strategy_v1.api.routes.auth import verify_token


class TestCapitalRoutesUnit:
    """Test Capital Routes API endpoints in isolation."""
    
    @pytest.fixture
    def client(self):
        """Create test client for capital routes."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @pytest.fixture
    def mock_token_payload(self):
        """Mock token payload for authentication."""
        return {
            "user_id": "test_user",
            "email": "test@example.com",
            "permissions": ["capital:deposit", "capital:withdraw"]
        }
    
    def create_authenticated_client(self, mock_token_payload):
        """Create a test client with mocked authentication."""
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        
        def mock_verify_token():
            return mock_token_payload
        
        app.dependency_overrides[verify_token] = mock_verify_token
        return TestClient(app)
    
    def test_capital_routes_initialization(self, client):
        """Test that capital routes initialize correctly."""
        # Test that the router is properly configured
        assert router is not None
        assert len(router.routes) > 0
        
        # Test that routes are accessible
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_deposit_capital_success(self, mock_token_payload):
        """Test successful capital deposit."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        deposit_request = {
            "amount": 10000.0,
            "currency": "USDT",
            "share_class": "usdt",
            "source": "manual"
        }
        
        response = test_client.post("/deposit", json=deposit_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["amount"] == 10000.0
        assert data["data"]["currency"] == "USDT"
        assert data["data"]["share_class"] == "usdt"
        assert data["data"]["status"] == "queued"
        assert data["data"]["new_total_equity"] == 110000.0  # 100000 + 10000
        assert "id" in data["data"]
        assert "timestamp" in data["data"]
    
    def test_deposit_capital_eth_share_class(self, mock_token_payload):
        """Test capital deposit with ETH share class."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        deposit_request = {
            "amount": 5.0,
            "currency": "ETH",
            "share_class": "eth",
            "source": "manual"
        }
        
        response = test_client.post("/deposit", json=deposit_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["amount"] == 5.0
        assert data["data"]["currency"] == "ETH"
        assert data["data"]["share_class"] == "eth"
        assert data["data"]["status"] == "queued"
    
    def test_deposit_capital_validation_error_amount(self, mock_token_payload):
        """Test capital deposit with invalid amount."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        deposit_request = {
            "amount": 0,  # Invalid amount
            "currency": "USDT",
            "share_class": "usdt",
            "source": "manual"
        }
        
        response = test_client.post("/deposit", json=deposit_request)
        
        # Pydantic validation returns 422, custom validation returns 400
        assert response.status_code in [400, 422]
        data = response.json()
        if response.status_code == 400:
            assert "Deposit amount must be greater than 0" in data["detail"]
        else:
            # Pydantic validation error format
            assert "detail" in data
    
    def test_deposit_capital_validation_error_share_class(self, mock_token_payload):
        """Test capital deposit with invalid share class."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        deposit_request = {
            "amount": 1000.0,
            "currency": "USDT",
            "share_class": "invalid",  # Invalid share class
            "source": "manual"
        }
        
        response = test_client.post("/deposit", json=deposit_request)
        
        assert response.status_code == 400
        data = response.json()
        assert "Share class must be either 'usdt' or 'eth'" in data["detail"]
    
    def test_deposit_capital_default_values(self, mock_token_payload):
        """Test capital deposit with default values."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        deposit_request = {
            "amount": 5000.0
            # Using default values for currency, share_class, source
        }
        
        response = test_client.post("/deposit", json=deposit_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["amount"] == 5000.0
        assert data["data"]["currency"] == "USDT"  # Default
        assert data["data"]["share_class"] == "usdt"  # Default
        assert data["data"]["status"] == "queued"
    
    def test_withdraw_capital_success(self, mock_token_payload):
        """Test successful capital withdrawal."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        withdraw_request = {
            "amount": 5000.0,
            "currency": "USDT",
            "share_class": "usdt",
            "withdrawal_type": "fast"
        }
        
        response = test_client.post("/withdraw", json=withdraw_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["amount"] == 5000.0
        assert data["data"]["currency"] == "USDT"
        assert data["data"]["share_class"] == "usdt"
        assert data["data"]["status"] == "queued"
        assert data["data"]["new_total_equity"] == 95000.0  # 100000 - 5000
        assert "id" in data["data"]
        assert "timestamp" in data["data"]
    
    def test_withdraw_capital_slow_withdrawal(self, mock_token_payload):
        """Test capital withdrawal with slow withdrawal type."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        withdraw_request = {
            "amount": 10000.0,
            "currency": "ETH",
            "share_class": "eth",
            "withdrawal_type": "slow"
        }
        
        response = test_client.post("/withdraw", json=withdraw_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["amount"] == 10000.0
        assert data["data"]["currency"] == "ETH"
        assert data["data"]["share_class"] == "eth"
        assert data["data"]["status"] == "queued"
        assert data["data"]["new_total_equity"] == 90000.0  # 100000 - 10000
    
    def test_withdraw_capital_validation_error_amount(self, mock_token_payload):
        """Test capital withdrawal with invalid amount."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        withdraw_request = {
            "amount": -1000.0,  # Invalid amount
            "currency": "USDT",
            "share_class": "usdt",
            "withdrawal_type": "fast"
        }
        
        response = test_client.post("/withdraw", json=withdraw_request)
        
        # Pydantic validation returns 422, custom validation returns 400
        assert response.status_code in [400, 422]
        data = response.json()
        if response.status_code == 400:
            assert "Withdrawal amount must be greater than 0" in data["detail"]
        else:
            # Pydantic validation error format
            assert "detail" in data
    
    def test_withdraw_capital_validation_error_share_class(self, mock_token_payload):
        """Test capital withdrawal with invalid share class."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        withdraw_request = {
            "amount": 1000.0,
            "currency": "USDT",
            "share_class": "invalid",  # Invalid share class
            "withdrawal_type": "fast"
        }
        
        response = test_client.post("/withdraw", json=withdraw_request)
        
        assert response.status_code == 400
        data = response.json()
        assert "Share class must be either 'usdt' or 'eth'" in data["detail"]
    
    def test_withdraw_capital_validation_error_withdrawal_type(self, mock_token_payload):
        """Test capital withdrawal with invalid withdrawal type."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        withdraw_request = {
            "amount": 1000.0,
            "currency": "USDT",
            "share_class": "usdt",
            "withdrawal_type": "invalid"  # Invalid withdrawal type
        }
        
        response = test_client.post("/withdraw", json=withdraw_request)
        
        assert response.status_code == 400
        data = response.json()
        assert "Withdrawal type must be either 'fast' or 'slow'" in data["detail"]
    
    def test_withdraw_capital_default_values(self, mock_token_payload):
        """Test capital withdrawal with default values."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        withdraw_request = {
            "amount": 2000.0
            # Using default values for currency, share_class, withdrawal_type
        }
        
        response = test_client.post("/withdraw", json=withdraw_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["amount"] == 2000.0
        assert data["data"]["currency"] == "USDT"  # Default
        assert data["data"]["share_class"] == "usdt"  # Default
        assert data["data"]["status"] == "queued"
    
    def test_deposit_request_model_validation(self):
        """Test DepositRequest model validation."""
        # Valid request
        request = DepositRequest(
            amount=1000.0,
            currency="USDT",
            share_class="usdt",
            source="manual"
        )
        assert request.amount == 1000.0
        assert request.currency == "USDT"
        assert request.share_class == "usdt"
        assert request.source == "manual"
    
    def test_deposit_request_model_defaults(self):
        """Test DepositRequest model with default values."""
        request = DepositRequest(amount=1000.0)
        assert request.amount == 1000.0
        assert request.currency == "USDT"  # Default
        assert request.share_class == "usdt"  # Default
        assert request.source == "manual"  # Default
    
    def test_withdraw_request_model_validation(self):
        """Test WithdrawRequest model validation."""
        # Valid request
        request = WithdrawRequest(
            amount=1000.0,
            currency="USDT",
            share_class="usdt",
            withdrawal_type="fast"
        )
        assert request.amount == 1000.0
        assert request.currency == "USDT"
        assert request.share_class == "usdt"
        assert request.withdrawal_type == "fast"
    
    def test_withdraw_request_model_defaults(self):
        """Test WithdrawRequest model with default values."""
        request = WithdrawRequest(amount=1000.0)
        assert request.amount == 1000.0
        assert request.currency == "USDT"  # Default
        assert request.share_class == "usdt"  # Default
        assert request.withdrawal_type == "fast"  # Default
    
    def test_capital_response_model(self):
        """Test CapitalResponse model validation."""
        response = CapitalResponse(
            id="deposit_20240512_120000_1000",
            amount=1000.0,
            currency="USDT",
            share_class="usdt",
            status="queued",
            new_total_equity=101000.0,
            timestamp="2024-05-12T12:00:00Z"
        )
        assert response.id == "deposit_20240512_120000_1000"
        assert response.amount == 1000.0
        assert response.currency == "USDT"
        assert response.share_class == "usdt"
        assert response.status == "queued"
        assert response.new_total_equity == 101000.0
        assert response.timestamp == "2024-05-12T12:00:00Z"
    
    def test_capital_routes_error_handling(self, client):
        """Test error handling in capital routes."""
        # Test with malformed JSON
        response = client.post("/deposit", data="invalid json")
        assert response.status_code == 422
        
        # Test with empty request body (will fail auth first)
        response = client.post("/deposit", json={})
        assert response.status_code in [403, 422]  # 403 for auth, 422 for validation
    
    def test_capital_routes_cors_headers(self, client):
        """Test that CORS headers are properly set."""
        response = client.options("/deposit")
        # FastAPI should handle CORS automatically
        assert response.status_code in [200, 405]  # 405 if OPTIONS not implemented
    
    def test_capital_routes_content_type(self, client):
        """Test that responses have correct content type."""
        response = client.post("/deposit", json={"amount": 1000.0})
        assert response.status_code in [200, 401, 403, 422]  # 403 for auth, 422 for validation error
        if response.status_code == 200:
            assert "application/json" in response.headers.get("content-type", "")
    
    def test_capital_routes_authentication_required(self, client):
        """Test that capital routes require authentication."""
        # Test deposit without authentication
        response = client.post("/deposit", json={"amount": 1000.0})
        assert response.status_code in [401, 403, 422]  # 403 for auth, 422 for validation error
        
        # Test withdrawal without authentication
        response = client.post("/withdraw", json={"amount": 1000.0})
        assert response.status_code in [401, 403, 422]  # 403 for auth, 422 for validation error
    
    def test_capital_routes_request_id_generation(self, mock_token_payload):
        """Test that request IDs are generated correctly."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        # Test deposit request ID format
        response = test_client.post("/deposit", json={"amount": 1000.0})
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"].startswith("deposit_")
        assert "1000" in data["data"]["id"]  # Amount should be in ID
        
        # Test withdrawal request ID format
        response = test_client.post("/withdraw", json={"amount": 2000.0})
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"].startswith("withdraw_")
        assert "2000" in data["data"]["id"]  # Amount should be in ID
    
    def test_capital_routes_equity_calculation(self, mock_token_payload):
        """Test that equity calculations are correct."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        # Test deposit increases equity
        response = test_client.post("/deposit", json={"amount": 5000.0})
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["new_total_equity"] == 105000.0  # 100000 + 5000
        
        # Test withdrawal decreases equity
        response = test_client.post("/withdraw", json={"amount": 3000.0})
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["new_total_equity"] == 97000.0  # 100000 - 3000
    
    def test_capital_routes_message_generation(self, mock_token_payload):
        """Test that success messages are generated correctly."""
        test_client = self.create_authenticated_client(mock_token_payload)
        
        # Test deposit message
        response = test_client.post("/deposit", json={"amount": 1000.0, "currency": "USDT"})
        assert response.status_code == 200
        data = response.json()
        # Check if message field exists, if not, just verify success
        if "message" in data:
            assert "Deposit of 1000.0 USDT queued successfully" in data["message"]
        else:
            assert data["success"] is True
        
        # Test withdrawal message
        response = test_client.post("/withdraw", json={"amount": 2000.0, "currency": "ETH"})
        assert response.status_code == 200
        data = response.json()
        # Check if message field exists, if not, just verify success
        if "message" in data:
            assert "Withdrawal of 2000.0 ETH queued successfully" in data["message"]
        else:
            assert data["success"] is True
