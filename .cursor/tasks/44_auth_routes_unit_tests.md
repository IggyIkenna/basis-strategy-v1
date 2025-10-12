# Task 44: Auth Routes Unit Tests

## Overview
Implement comprehensive unit tests for the Auth Routes API endpoints to ensure proper authentication functionality with mocked dependencies.

## Reference
- **Component**: `backend/src/basis_strategy_v1/api/routes/auth.py`
- **Specification**: `docs/specs/12_FRONTEND_SPEC.md` (Authentication section)
- **Architecture**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6.2

## Implementation Requirements

### 1. Auth Routes Component Testing
- **File**: `tests/unit/test_auth_routes_unit.py`
- **Scope**: Authentication API endpoints in isolation
- **Dependencies**: Mocked auth service and dependencies

### 2. Test Coverage Requirements
- **Login Endpoint**: POST /auth/login with username/password validation
- **Logout Endpoint**: POST /auth/logout with token invalidation
- **Token Refresh**: POST /auth/refresh with JWT token handling
- **User Registration**: POST /auth/register with user creation
- **Password Reset**: POST /auth/reset-password with email validation
- **Session Management**: GET /auth/session with session validation

### 3. Mock Strategy
- Use pytest fixtures with mocked auth service
- Test API endpoints in isolation without external dependencies
- Validate request/response formats and status codes

## Quality Gate
**Quality Gate Script**: `tests/unit/test_auth_routes_unit.py`
**Validation**: Authentication endpoints, JWT handling, session management
**Status**: 🟡 PENDING

## Success Criteria
- [ ] Auth routes initialize correctly with mocked dependencies
- [ ] Login endpoint validates credentials and returns JWT tokens
- [ ] Logout endpoint invalidates tokens properly
- [ ] Token refresh handles expired tokens correctly
- [ ] User registration creates accounts with validation
- [ ] Password reset sends emails with proper validation
- [ ] Session management validates active sessions

## Estimated Time
4-6 hours
