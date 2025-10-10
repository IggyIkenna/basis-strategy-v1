<!-- 357eedf3-5d3c-4164-8b22-fa3c9b9b761e 69f6a5b1-21b5-420a-bd44-3f89bd54f3f6 -->
# Frontend & Backend Complete Implementation Plan

## Overview

Implement remaining frontend components (live trading UI, capital management), backend API endpoints (auth, capital management), integrate authentication into App.tsx, add comprehensive testing, and establish environment variable management for API mode switching.

## Phase 1: Backend API Endpoints (4-6 hours)

### 1.1 Authentication Routes

**File:** `backend/src/basis_strategy_v1/api/routes/auth.py` (NEW)

Create authentication endpoints:

- `POST /api/v1/auth/login` - JWT token generation
- `POST /api/v1/auth/logout` - Token invalidation
- `GET /api/v1/auth/me` - Current user info
```python
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt
from datetime import datetime, timedelta

router = APIRouter()
security = HTTPBearer()

USERS = {"admin": "admin123"}  # Simple in-memory store
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
```


### 1.2 Capital Management Routes

**File:** `backend/src/basis_strategy_v1/api/routes/capital.py` (NEW)

Create capital management endpoints:

- `POST /api/v1/capital/deposit` - Queue deposit request
- `POST /api/v1/capital/withdraw` - Queue withdrawal request
```python
@router.post("/deposit")
async def deposit_capital(request: DepositRequest):
    # Queue deposit for next timestep processing
    # Trigger rebalancing
    return {"message": "Deposit queued", "amount": request.amount}
```


### 1.3 Register Routes

**File:** `backend/src/basis_strategy_v1/api/main.py`

Add to main.py:

```python
from .routes import auth, capital

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(capital.router, prefix="/api/v1/capital", tags=["capital"])
```

## Phase 2: Live Trading UI Components (6-8 hours)

### 2.1 LiveTradingPanel Component

**File:** `frontend/src/components/live/LiveTradingPanel.tsx` (NEW)

Features:

- Start/stop controls with confirmation dialogs
- Real-time status display (60-second polling)
- Emergency stop button
- Manual rebalance trigger
- Component health display

### 2.2 CapitalManagement Component

**File:** `frontend/src/components/live/CapitalManagement.tsx` (NEW)

Features:

- Deposit/withdraw forms with validation
- Amount validation (min/max)
- Confirmation dialogs
- Success/error messaging

### 2.3 StatusMonitor Component

**File:** `frontend/src/components/live/StatusMonitor.tsx` (NEW)

Features:

- Component health status display
- System metrics (CPU, memory)
- Risk metrics (LTV, margin ratio)
- Real-time updates via polling

### 2.4 LivePerformanceDashboard Component

**File:** `frontend/src/components/live/LivePerformanceDashboard.tsx` (NEW)

Features:

- Live performance metrics
- Current P&L display
- Trade statistics
- Performance charts (using existing ChartsGrid)

## Phase 3: App Integration with React Router (3-4 hours)

### 3.1 Install React Router

**Command:** `cd frontend && npm install react-router-dom`

Add React Router to dependencies for proper URL-based navigation.

### 3.2 Update App.tsx with Routing

**File:** `frontend/src/App.tsx`

Implement proper routing with real URLs:

```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { LoginPage } from './components/auth/LoginPage';
import { Layout } from './components/layout/Layout';
import { WizardContainer } from './components/wizard/WizardContainer';
import { ResultsPage } from './components/results/ResultsPage';
import { LiveTradingDashboard } from './components/live/LiveTradingDashboard';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="/wizard" replace />} />
            <Route path="wizard" element={<WizardContainer />} />
            <Route path="results/:backtestId" element={<ResultsPage />} />
            <Route path="live" element={<LiveTradingDashboard />} />
          </Route>
          <Route path="*" element={<Navigate to="/wizard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
```

**Routes:**

- `/login` - Login page (public)
- `/wizard` - Backtest configuration wizard (protected)
- `/results/:backtestId` - Results page with backtest ID (protected)
- `/live` - Live trading dashboard (protected)
- `/` - Redirects to `/wizard`
- `*` - Catch-all redirects to `/wizard`

### 3.3 Create Layout Component

**File:** `frontend/src/components/layout/Layout.tsx` (NEW)

Layout wrapper with header and navigation:

```typescript
import { Outlet } from 'react-router-dom';
import { Header } from './Header';

export const Layout = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main>
        <Outlet />
      </main>
    </div>
  );
};
```

### 3.4 Create Navigation Header

**File:** `frontend/src/components/layout/Header.tsx` (NEW)

Features:

- Navigation links with active state highlighting
- User info display
- Logout button
- Responsive mobile menu
```typescript
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { LogoutButton } from '../auth/LogoutButton';

export const Header = () => {
  const location = useLocation();
  const { user } = useAuth();
  
  const navLinks = [
    { path: '/wizard', label: 'New Backtest' },
    { path: '/live', label: 'Live Trading' },
  ];
  
  return (
    <header className="bg-white shadow">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold">Basis Strategy</h1>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navLinks.map(link => (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    location.pathname === link.path
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center">
            <span className="text-sm text-gray-500 mr-4">
              {user?.username}
            </span>
            <LogoutButton variant="button" />
          </div>
        </div>
      </nav>
    </header>
  );
};
```


### 3.5 Update WizardContainer

**File:** `frontend/src/components/wizard/WizardContainer.tsx`

Update to use React Router navigation:

```typescript
import { useNavigate } from 'react-router-dom';

const navigate = useNavigate();

const handleComplete = async (config: WizardConfig) => {
  const response = await apiClient.runBacktest(config);
  navigate(`/results/${response.request_id}`);
};
```

### 3.6 Update ResultsPage

**File:** `frontend/src/components/results/ResultsPage.tsx`

Update to use URL parameter for backtest ID:

```typescript
import { useParams, useNavigate } from 'react-router-dom';

const { backtestId } = useParams<{ backtestId: string }>();
const navigate = useNavigate();

const handleBack = () => {
  navigate('/wizard');
};
```

### 3.7 Create LiveTradingDashboard

**File:** `frontend/src/components/live/LiveTradingDashboard.tsx` (NEW)

Main live trading dashboard page:

```typescript
import { LiveTradingPanel } from './LiveTradingPanel';
import { CapitalManagement } from './CapitalManagement';
import { StatusMonitor } from './StatusMonitor';
import { LivePerformanceDashboard } from './LivePerformanceDashboard';

export const LiveTradingDashboard = () => {
  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="space-y-6">
        <LiveTradingPanel />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CapitalManagement />
          <StatusMonitor />
        </div>
        <LivePerformanceDashboard />
      </div>
    </div>
  );
};
```

### 3.8 Update ProtectedRoute

**File:** `frontend/src/components/auth/ProtectedRoute.tsx`

Update to use React Router navigation:

```typescript
import { Navigate, useLocation } from 'react-router-dom';

export const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();
  
  if (loading) return <LoadingSpinner />;
  
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return <>{children}</>;
};
```

### 3.9 Update LoginPage

**File:** `frontend/src/components/auth/LoginPage.tsx`

Update to navigate after successful login:

```typescript
import { useNavigate, useLocation } from 'react-router-dom';

const navigate = useNavigate();
const location = useLocation();

const handleLoginSuccess = () => {
  const from = location.state?.from?.pathname || '/wizard';
  navigate(from, { replace: true });
};
```

## Phase 4: Environment Variable Management (2-3 hours)

### 4.1 Add API Mode Environment Variable

**Root files:**

- `.env.dev` - Add `VITE_API_MODE=mock`
- `.env.docker` - Add `VITE_API_MODE=mock`
- `.env.production` - Add `VITE_API_MODE=real`
- `env.unified` - Document the variable

**Docker files:**

- `docker/.env.dev` - Add `VITE_API_MODE=mock`
- `docker/.env.staging` - Add `VITE_API_MODE=mock`
- `docker/.env.production` - Add `VITE_API_MODE=real`

### 4.2 Update API Client

**File:** `frontend/src/services/api.ts`

Update export logic:

```typescript
export const apiClient = import.meta.env.VITE_API_MODE === 'mock'
  ? new MockApiClient()
  : new ApiClient();
```

### 4.3 Update Documentation Files

**File:** `docs/specs/12_FRONTEND_SPEC.md`

- Add environment variables section
- Document VITE_API_MODE usage
- Update deployment configuration section

**File:** `docs/specs/CONFIGURATION.md`

- Add frontend environment variables section
- Document API mode switching

**File:** `docs/ENVIRONMENT_VARIABLES.md`

- Add VITE_API_MODE to frontend section
- Explain mock vs real API modes

**File:** `docs/DEPLOYMENT_GUIDE.md`

- Add frontend deployment section
- Document environment variable injection
- Update build process for all environments

**File:** `docs/GETTING_STARTED.md`

- Add frontend setup section
- Document API mode for development

**File:** `docs/README.md`

- Update with frontend environment variables

**File:** `docs/USER_GUIDE.md`

- Add section on development vs production API modes

**File:** `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`

- Add frontend environment variable architecture section

**File:** `docs/ARCHITECTURAL_DECISION_RECORDS.md`

- Add ADR for API mode switching strategy

**File:** `docs/WORKFLOW_GUIDE.md`

- Update frontend workflows with environment variable usage

### 4.4 Update Config Validator

**File:** `backend/src/basis_strategy_v1/infrastructure/config/config_validator.py`

Add to `frontend_deployment_vars`:

```python
frontend_deployment_vars = [
    "VITE_API_BASE_URL",
    "VITE_APP_ENVIRONMENT",
    "VITE_APP_VERSION",
    "VITE_API_MODE",  # NEW
]
```

## Phase 5: Testing (4-6 hours)

### 5.1 Backend API Tests

**File:** `tests/unit/api/test_auth.py` (NEW)

Test authentication endpoints:

- Login with valid credentials
- Login with invalid credentials
- Logout functionality
- Get current user with valid token
- Get current user with invalid token

**File:** `tests/unit/api/test_capital.py` (NEW)

Test capital management endpoints:

- Deposit request validation
- Withdraw request validation
- Amount validation
- Response format

### 5.2 Frontend Component Tests

**File:** `tests/frontend/components/live/LiveTradingPanel.test.tsx` (NEW)

Test live trading panel:

- Start/stop button rendering
- Confirmation dialog display
- Status updates
- Error handling

**File:** `tests/frontend/components/live/CapitalManagement.test.tsx` (NEW)

Test capital management:

- Form validation
- Amount validation
- Confirmation dialogs
- API integration with mock

**File:** `tests/frontend/components/auth/LoginPage.test.tsx` (NEW)

Test login page:

- Form validation
- Submission handling
- Error display
- Success redirect

### 5.3 Integration Tests

**File:** `tests/integration/test_auth_flow.py` (NEW)

Test complete authentication flow:

- Login → Get user info → Logout
- Invalid credentials handling
- Token expiration handling

**File:** `tests/integration/test_capital_management.py` (NEW)

Test complete capital management flow:

- Deposit → Verify balance → Withdraw
- Validation errors
- Insufficient balance handling

## Phase 6: Frontend Dependencies Installation

### 6.1 Install Missing Dependencies

**File:** `frontend/package.json`

Run: `cd frontend && npm install`

Verify dependencies are installed:

- `@tanstack/react-virtual`
- `date-fns`
- `jwt-decode`

## Success Criteria

- [ ] All backend API endpoints implemented and tested
- [ ] All live trading UI components complete
- [ ] Authentication integrated into App.tsx
- [ ] Environment variables documented in all 10 docs files
- [ ] Config validator updated with VITE_API_MODE
- [ ] Unit tests passing (target 80% coverage)
- [ ] Integration tests passing
- [ ] Mock API works in development
- [ ] Real API ready for production
- [ ] Frontend builds successfully
- [ ] All linter errors resolved

## Estimated Total Time: 18-26 hours

## Notes

- Mock API client allows full frontend development without backend
- Environment variable approach provides clean separation
- All documentation updated for consistency
- Tests ensure quality and catch regressions
- Simple state-based routing keeps implementation straightforward

### To-dos

- [ ] Implement authentication routes (login, logout, me)
- [ ] Implement capital management routes (deposit, withdraw)
- [ ] Register new routes in main.py
- [ ] Create LiveTradingPanel component
- [ ] Create CapitalManagement component
- [ ] Create StatusMonitor component
- [ ] Create LivePerformanceDashboard component
- [ ] Update App.tsx with authentication and navigation
- [ ] Create Header component with logout
- [ ] Add VITE_API_MODE to root env files
- [ ] Add VITE_API_MODE to docker env files
- [ ] Update API client to use VITE_API_MODE
- [ ] Update docs/specs/12_FRONTEND_SPEC.md with env vars
- [ ] Update docs/specs/CONFIGURATION.md with frontend env vars
- [ ] Update docs/ENVIRONMENT_VARIABLES.md with VITE_API_MODE
- [ ] Update docs/DEPLOYMENT_GUIDE.md with frontend deployment
- [ ] Update docs/GETTING_STARTED.md with frontend setup
- [ ] Update docs/README.md with frontend env vars
- [ ] Update docs/USER_GUIDE.md with API mode info
- [ ] Update docs/REFERENCE_ARCHITECTURE_CANONICAL.md with frontend env vars
- [ ] Update docs/ARCHITECTURAL_DECISION_RECORDS.md with API mode ADR
- [ ] Update docs/WORKFLOW_GUIDE.md with env var usage
- [ ] Add VITE_API_MODE to frontend_deployment_vars in config_validator.py
- [ ] Write unit tests for auth and capital management endpoints
- [ ] Write unit tests for new frontend components
- [ ] Write integration tests for auth and capital flows
- [ ] Install frontend dependencies (npm install)