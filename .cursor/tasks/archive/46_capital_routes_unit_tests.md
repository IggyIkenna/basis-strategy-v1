# Task 46: Capital Routes Unit Tests

## Overview
Implement comprehensive unit tests for the Capital Routes API endpoints to ensure proper capital management functionality with mocked dependencies.

## Reference
- **Component**: `backend/src/basis_strategy_v1/api/routes/capital.py`
- **Specification**: `docs/specs/12_FRONTEND_SPEC.md` (Capital Management section)
- **Architecture**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6.2

## Implementation Requirements

### 1. Capital Routes Component Testing
- **File**: `tests/unit/test_capital_routes_unit.py`
- **Scope**: Capital management API endpoints in isolation
- **Dependencies**: Mocked capital service and dependencies

### 2. Test Coverage Requirements
- **Capital Allocation**: GET /capital/allocation with current allocations
- **Capital Rebalancing**: POST /capital/rebalance with rebalancing logic
- **Capital Withdrawal**: POST /capital/withdraw with withdrawal processing
- **Capital Deposit**: POST /capital/deposit with deposit processing
- **Capital History**: GET /capital/history with transaction history
- **Capital Limits**: GET /capital/limits with risk limits validation

### 3. Mock Strategy
- Use pytest fixtures with mocked capital service
- Test API endpoints in isolation without external dependencies
- Validate request/response formats and status codes

## Quality Gate
**Quality Gate Script**: `tests/unit/test_capital_routes_unit.py`
**Validation**: Capital endpoints, allocation logic, transaction processing
**Status**: 🟡 PENDING

## Success Criteria
- [ ] Capital routes initialize correctly with mocked dependencies
- [ ] Capital allocation returns current position data
- [ ] Capital rebalancing triggers proper rebalancing logic
- [ ] Capital withdrawal processes requests with validation
- [ ] Capital deposit processes requests with validation
- [ ] Capital history returns transaction records with pagination
- [ ] Capital limits enforce risk management rules

## Estimated Time
4-6 hours
