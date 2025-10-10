# Task 27: Authentication System Implementation

**Priority**: HIGH  
**Estimated Time**: 4-6 hours  
**Dependencies**: None  
**Day**: 6 (Frontend & Live Mode Completion)

## Overview
Implement basic username/password authentication system for the frontend with username "admin" and password-based authentication.

## Requirements

### Backend Authentication Endpoints
- **POST /api/v1/auth/login** - User authentication with username/password
- **POST /api/v1/auth/logout** - User logout and token invalidation
- **GET /api/v1/auth/me** - Get current user info (optional)

### Frontend Authentication Components
- **LoginPage.tsx** - Username/password login form
- **AuthContext.tsx** - Authentication state management with JWT
- **ProtectedRoute.tsx** - Route guard for authenticated users
- **LogoutButton.tsx** - Logout functionality

### Authentication Flow
1. User enters username/password on login page
2. Frontend sends credentials to backend
3. Backend validates credentials (username: "admin")
4. Backend returns JWT token on success
5. Frontend stores JWT in localStorage
6. Frontend uses JWT for subsequent API calls
7. Protected routes check authentication status

## Implementation Details

### Backend Implementation
```python
# backend/src/basis_strategy_v1/api/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta

router = APIRouter()
security = HTTPBearer()

# Simple in-memory user store (for MVP)
USERS = {
    "admin": "admin123"  # In production, use proper password hashing
}

SECRET_KEY = "your-secret-key"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    if request.username not in USERS or USERS[request.username] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode(
        {"sub": request.username, "exp": datetime.utcnow() + access_token_expires},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/logout")
async def logout():
    # In production, implement token blacklisting
    return {"message": "Successfully logged out"}

@router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Frontend Implementation

#### AuthContext.tsx
```typescript
// frontend/src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { jwtDecode } from 'jwt-decode';

interface User {
  username: string;
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decoded = jwtDecode(token) as any;
        if (decoded.exp * 1000 > Date.now()) {
          setUser({ username: decoded.sub });
        } else {
          localStorage.removeItem('token');
        }
      } catch (error) {
        localStorage.removeItem('token');
      }
    }
    setLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error('Invalid credentials');
    }

    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    setUser({ username });
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

#### LoginPage.tsx
```typescript
// frontend/src/components/auth/LoginPage.tsx
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError('Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to Basis Strategy
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Username"
              />
            </div>
            <div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password"
              />
            </div>
          </div>

          {error && (
            <div className="text-red-600 text-sm text-center">{error}</div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
```

## Success Criteria
- [ ] Backend authentication endpoints implemented and tested
- [ ] Frontend login page with username/password form
- [ ] JWT token storage and management in localStorage
- [ ] Protected routes redirect to login when not authenticated
- [ ] Logout functionality clears token and redirects to login
- [ ] Authentication state persists across page refreshes
- [ ] Error handling for invalid credentials
- [ ] Loading states during authentication

## Testing Requirements
- [ ] Unit tests for authentication endpoints
- [ ] Integration tests for login/logout flow
- [ ] Frontend component tests for LoginPage and AuthContext
- [ ] E2E tests for complete authentication flow

## Files to Create/Modify
- `backend/src/basis_strategy_v1/api/routes/auth.py` - New authentication routes
- `frontend/src/contexts/AuthContext.tsx` - New authentication context
- `frontend/src/components/auth/LoginPage.tsx` - New login page component
- `frontend/src/components/auth/ProtectedRoute.tsx` - New route guard component
- `frontend/src/components/auth/LogoutButton.tsx` - New logout button component
- `backend/src/basis_strategy_v1/api/main.py` - Add auth router to main app
- `frontend/src/App.tsx` - Add AuthProvider and routing logic

## Notes
- This is a basic authentication system for MVP
- In production, implement proper password hashing (bcrypt)
- Consider implementing token refresh mechanism
- Add rate limiting for login attempts
- Store JWT secret in environment variables

