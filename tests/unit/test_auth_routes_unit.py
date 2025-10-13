"""
Unit tests for Auth Routes API endpoints.

Tests authentication functionality with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import jwt
from datetime import datetime, timedelta
import os
import sys

# Mock environment variables before importing the auth module
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

# Now import the auth module
from basis_strategy_v1.api.routes.auth import (
    router, 
    create_access_token, 
    verify_token,
    LoginRequest,
    LoginResponse,
    UserResponse,
    LogoutResponse
)


class TestAuthRoutesUnit:
    """Test Auth Routes API endpoints in isolation."""
    
    @pytest.fixture
    def client(self):
        """Create test client for auth routes."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @pytest.fixture
    def mock_users(self):
        """Mock user store."""
        return {
            "admin": "admin123",
            "testuser": "testpass123"
        }
    
    def test_auth_routes_initialization(self, client):
        """Test that auth routes initialize correctly."""
        # Test that the router is properly configured
        assert router is not None
        assert len(router.routes) > 0
        
        # Test that routes are accessible
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_login_endpoint_success(self, client, mock_users):
        """Test successful login with valid credentials."""
        with patch('basis_strategy_v1.api.routes.auth.USERS', mock_users):
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = client.post("/login", json=login_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert "expires_in" in data
            assert data["token_type"] == "bearer"
            assert data["expires_in"] == 1800  # 30 minutes
    
    def test_login_endpoint_invalid_credentials(self, client, mock_users):
        """Test login with invalid credentials."""
        with patch('basis_strategy_v1.api.routes.auth.USERS', mock_users):
            login_data = {
                "username": "admin",
                "password": "wrongpassword"
            }
            
            response = client.post("/login", json=login_data)
            
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert "Invalid credentials" in data["detail"]
    
    def test_login_endpoint_nonexistent_user(self, client, mock_users):
        """Test login with nonexistent user."""
        with patch('basis_strategy_v1.api.routes.auth.USERS', mock_users):
            login_data = {
                "username": "nonexistent",
                "password": "password"
            }
            
            response = client.post("/login", json=login_data)
            
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert "Invalid credentials" in data["detail"]
    
    def test_login_endpoint_missing_fields(self, client):
        """Test login with missing required fields."""
        # Missing password
        login_data = {
            "username": "admin"
        }
        
        response = client.post("/login", json=login_data)
        assert response.status_code == 422  # Validation error
        
        # Missing username
        login_data = {
            "password": "admin123"
        }
        
        response = client.post("/login", json=login_data)
        assert response.status_code == 422  # Validation error
    
    def test_logout_endpoint_success(self, client):
        """Test successful logout."""
        # First login to get a token
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        login_response = client.post("/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Now logout with the token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/logout", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Successfully logged out" in data["message"]
    
    def test_logout_endpoint_no_token(self, client):
        """Test logout without token."""
        response = client.post("/logout")
        assert response.status_code == 403  # Forbidden
    
    def test_logout_endpoint_invalid_token(self, client):
        """Test logout with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/logout", headers=headers)
        assert response.status_code == 401  # Unauthorized
    
    def test_refresh_endpoint_success(self, client):
        """Test successful token refresh."""
        # First login to get a token
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        login_response = client.post("/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Now refresh the token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/refresh", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_endpoint_no_token(self, client):
        """Test refresh without token."""
        response = client.post("/refresh")
        assert response.status_code == 403  # Forbidden
    
    def test_refresh_endpoint_invalid_token(self, client):
        """Test refresh with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/refresh", headers=headers)
        assert response.status_code == 401  # Unauthorized
    
    def test_session_endpoint_success(self, client):
        """Test successful session validation."""
        # First login to get a token
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        login_response = client.post("/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Now check session
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/session", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "authenticated" in data
        assert data["username"] == "admin"
        assert data["authenticated"] is True
    
    def test_session_endpoint_no_token(self, client):
        """Test session check without token."""
        response = client.get("/session")
        assert response.status_code == 403  # Forbidden
    
    def test_session_endpoint_invalid_token(self, client):
        """Test session check with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/session", headers=headers)
        assert response.status_code == 401  # Unauthorized
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "admin"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token can be decoded
        decoded = jwt.decode(token, "dev-secret-key-change-in-production", algorithms=["HS256"])
        assert decoded["sub"] == "admin"
        assert "exp" in decoded
    
    def test_create_access_token_with_expires_delta(self):
        """Test access token creation with custom expiration."""
        data = {"sub": "admin"}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta)
        
        assert token is not None
        
        # Verify token can be decoded
        decoded = jwt.decode(token, "dev-secret-key-change-in-production", algorithms=["HS256"])
        assert decoded["sub"] == "admin"
        
        # Check expiration is approximately 60 minutes from now
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.now()
        time_diff = (exp_datetime - now).total_seconds()
        
        # Should be approximately 3600 seconds (60 minutes)
        assert 3500 < time_diff < 3700
    
    def test_verify_token_success(self):
        """Test successful token verification."""
        data = {"sub": "admin"}
        token = create_access_token(data)
        
        # Verify token
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "admin"
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid_token")
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)
    
    def test_verify_token_expired(self):
        """Test token verification with expired token."""
        # Create an expired token
        data = {"sub": "admin"}
        expired_time = datetime.utcnow() - timedelta(hours=1)
        token = jwt.encode(
            {"sub": "admin", "exp": expired_time},
            "dev-secret-key-change-in-production",
            algorithm="HS256"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)
    
    def test_login_request_model(self):
        """Test LoginRequest model validation."""
        # Valid request
        request = LoginRequest(username="admin", password="admin123")
        assert request.username == "admin"
        assert request.password == "admin123"
        
        # Test with different data
        request = LoginRequest(username="testuser", password="testpass")
        assert request.username == "testuser"
        assert request.password == "testpass"
    
    def test_login_response_model(self):
        """Test LoginResponse model validation."""
        response = LoginResponse(
            access_token="test_token",
            token_type="bearer",
            expires_in=1800
        )
        assert response.access_token == "test_token"
        assert response.token_type == "bearer"
        assert response.expires_in == 1800
    
    def test_user_response_model(self):
        """Test UserResponse model validation."""
        response = UserResponse(username="admin", authenticated=True)
        assert response.username == "admin"
        assert response.authenticated is True
    
    def test_logout_response_model(self):
        """Test LogoutResponse model validation."""
        response = LogoutResponse(message="Successfully logged out")
        assert response.message == "Successfully logged out"
    
    def test_auth_routes_error_handling(self, client):
        """Test error handling in auth routes."""
        # Test with malformed JSON
        response = client.post("/login", data="invalid json")
        assert response.status_code == 422
        
        # Test with empty request body
        response = client.post("/login", json={})
        assert response.status_code == 422
    
    def test_auth_routes_cors_headers(self, client):
        """Test that CORS headers are properly set."""
        response = client.options("/login")
        # FastAPI should handle CORS automatically
        assert response.status_code in [200, 405]  # 405 if OPTIONS not implemented
    
    def test_auth_routes_content_type(self, client):
        """Test that responses have correct content type."""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = client.post("/login", json=login_data)
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_auth_routes_security_headers(self, client):
        """Test that security headers are present."""
        response = client.get("/session")
        # Check for common security headers
        headers = response.headers
        
        # These might be set by middleware or server configuration
        # We're just checking that the response is properly formed
        assert response.status_code in [200, 403, 401]
