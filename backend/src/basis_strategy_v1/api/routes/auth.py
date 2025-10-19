"""
Authentication routes for JWT-based user authentication.
"""

import os
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..models import ApiResponse

router = APIRouter()
security = HTTPBearer()

# Simple in-memory user store for MVP
USERS: Dict[str, str] = {"admin": "admin123"}

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    username: str
    authenticated: bool


class LogoutResponse(BaseModel):
    message: str


def create_access_token(data: Dict[str, Any], expires_delta: timedelta = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=ApiResponse[LoginResponse])
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.

    - **username**: Username for authentication
    - **password**: Password for authentication

    Returns JWT access token on successful authentication.
    """
    # Verify credentials
    if request.username not in USERS or USERS[request.username] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )

    return ApiResponse(
        success=True,
        data=LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        ),
        message="Login successful",
    )


@router.post("/logout", response_model=ApiResponse[LogoutResponse])
async def logout(token_payload: Dict[str, Any] = Depends(verify_token)):
    """
    Logout user and invalidate token.

    Note: In a production system, you would maintain a blacklist of invalidated tokens.
    For MVP, we rely on token expiration.
    """
    return ApiResponse(
        success=True,
        data=LogoutResponse(message="Successfully logged out"),
        message="Logout successful",
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user(token_payload: Dict[str, Any] = Depends(verify_token)):
    """
    Get current authenticated user information.

    Returns user details for the authenticated user.
    """
    username = token_payload.get("sub")

    return ApiResponse(
        success=True,
        data=UserResponse(username=username, authenticated=True),
        message="User information retrieved successfully",
    )
