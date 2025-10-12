# Task 32: Event Logger Unit Tests

## Overview
Implement comprehensive unit tests for the Event Logger component to ensure proper event logging functionality with mocked dependencies.

## Reference
- **Component**: `backend/src/basis_strategy_v1/infrastructure/logging/event_logger.py`
- **Specification**: `docs/specs/17_HEALTH_ERROR_SYSTEMS.md` (Event Logging section)
- **Architecture**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6.2

## Implementation Requirements

### 1. Event Logger Component Testing
- **File**: `tests/unit/test_event_logger_unit.py`
- **Scope**: Event logging functionality in isolation
- **Dependencies**: Mocked config and data provider

### 2. Test Coverage Requirements
- **Initialization**: Event logger initializes correctly with config and data provider
- **Strategy Events**: Logging strategy events with proper formatting
- **Error Events**: Logging error events with stack traces
- **Performance Metrics**: Logging performance metrics with timing data
- **Audit Trail**: Logging audit trail events for compliance
- **Health Status**: Logging health status events

### 3. Mock Strategy
- Use pytest fixtures with mocked config and data provider
- Test component in isolation without external dependencies
- Validate event formatting and structure

## Quality Gate
**Quality Gate Script**: `tests/unit/test_event_logger_unit.py`
**Validation**: Event logging functionality, formatting, error handling, unit tests
**Status**: ✅ IMPLEMENTED

## Success Criteria
- [ ] Event logger initializes correctly with mocked dependencies
- [ ] Strategy events are logged with proper formatting
- [ ] Error events include stack traces and context
- [ ] Performance metrics are logged with timing data
- [ ] Audit trail events are logged for compliance
- [ ] Health status events are logged correctly
- [ ] All unit tests pass with 80%+ coverage
- [ ] Component works in isolation with mocked dependencies

## Implementation Notes
- Event logger should handle different log levels (INFO, ERROR, WARNING)
- Events should include timestamps and proper formatting
- Error events should capture full stack traces
- Performance metrics should include timing and memory usage
- Audit trail should include user actions and configuration changes
- Health status should include component status and metrics

## Dependencies
- Event Logger component implementation
- Pytest testing framework
- Mock objects for dependencies
- Logging configuration

## Related Tasks
- Task 17: Health & Error Systems (Event Logger implementation)
- Task 34: Health System Unit Tests (Health status logging)
- Task 35: API Endpoints Unit Tests (API event logging)
