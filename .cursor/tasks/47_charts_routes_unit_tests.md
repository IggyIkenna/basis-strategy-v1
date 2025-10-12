# Task 47: Charts Routes Unit Tests

## Overview
Implement comprehensive unit tests for the Charts Routes API endpoints to ensure proper chart generation functionality with mocked dependencies.

## Reference
- **Component**: `backend/src/basis_strategy_v1/api/routes/charts.py`
- **Specification**: `docs/specs/12_FRONTEND_SPEC.md` (Chart Generation section)
- **Architecture**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6.2

## Implementation Requirements

### 1. Charts Routes Component Testing
- **File**: `tests/unit/test_charts_routes_unit.py`
- **Scope**: Chart generation API endpoints in isolation
- **Dependencies**: Mocked chart service and dependencies

### 2. Test Coverage Requirements
- **Performance Charts**: GET /charts/performance with P&L visualization
- **Allocation Charts**: GET /charts/allocation with position breakdown
- **Risk Charts**: GET /charts/risk with risk metrics visualization
- **Historical Charts**: GET /charts/historical with time series data
- **Custom Charts**: POST /charts/custom with custom chart generation
- **Chart Export**: GET /charts/{id}/export with chart export functionality

### 3. Mock Strategy
- Use pytest fixtures with mocked chart service
- Test API endpoints in isolation without external dependencies
- Validate request/response formats and chart data structure

## Quality Gate
**Quality Gate Script**: `tests/unit/test_charts_routes_unit.py`
**Validation**: Chart endpoints, data visualization, export functionality
**Status**: 🟡 PENDING

## Success Criteria
- [ ] Charts routes initialize correctly with mocked dependencies
- [ ] Performance charts generate P&L visualizations correctly
- [ ] Allocation charts display position breakdowns properly
- [ ] Risk charts visualize risk metrics accurately
- [ ] Historical charts render time series data correctly
- [ ] Custom charts generate user-defined visualizations
- [ ] Chart export provides downloadable chart files

## Estimated Time
4-6 hours
