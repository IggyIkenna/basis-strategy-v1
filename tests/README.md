# Testing Overview 🧪

## 🎯 **Testing Strategy**

This directory contains all tests for the Basis Strategy platform, organized by type and component.

---

## 📁 **Directory Structure**

### **Unit Tests** (`tests/unit/`)
Fast, isolated tests for individual components:
- `components/` - Component unit tests
- `math/` - Mathematical calculation tests  
- `services/` - Service layer tests

### **Integration Tests** (`tests/integration/`)
Component coordination and interaction tests:
- Component integration tests
- API integration tests
- Database integration tests

### **End-to-End Tests** (`tests/e2e/`)
Full workflow and user journey tests:
- Frontend wizard flow tests
- Complete backtest workflow tests
- Deployment and production tests

### **Test Data & Fixtures** (`tests/fixtures/`)
- `test_data/` - Sample data files for testing
- `mock_responses/` - Mock API responses
- `sample_configs/` - Test configuration files

### **Test Utilities** (`tests/mocks/` & `tests/helpers/`)
- `mocks/` - Mock objects and test doubles
- `helpers/` - Test helper functions and utilities

---

## 🚀 **Running Tests**

### **Run All Tests**
```bash
pytest
```

### **Run by Category**
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/

# Specific component tests
pytest tests/unit/components/test_position_monitor.py
```

### **Frontend Testing with Docker**
For frontend testing with proper dependency management:

```bash
# Start frontend test environment (includes backend)
./deploy/test-frontend.sh

# Frontend available at: http://localhost:5173
# Backend available at: http://localhost:8001
```

**Docker Setup Files**:
- `deploy/Dockerfile.frontend-test` - Frontend testing environment
- `deploy/docker-compose.frontend-test.yml` - Complete test environment
- `deploy/test-frontend.sh` - Easy testing script

**Benefits**:
- ✅ Consistent dependency management
- ✅ Isolated testing environment
- ✅ No local Node.js/npm installation required
- ✅ Backend integration testing included

### **Run with Coverage**
```bash
pytest --cov=backend/src tests/
```

### **Run Specific Test**
```bash
pytest tests/unit/components/test_position_monitor.py::TestPositionMonitor::test_balance_tracking
```

---

## 📋 **Test Categories**

### **Component Tests**
- **Position Monitor** - Token and derivative balance tracking
- **Exposure Monitor** - AAVE conversion and net delta calculation
- **Risk Monitor** - LTV, margin, and liquidation risk assessment
- **P&L Calculator** - Balance and attribution P&L calculation
- **Strategy Manager** - Mode detection and orchestration
- **CEX Execution Manager** - Spot and perpetual futures trading
- **OnChain Execution Manager** - AAVE and staking operations
- **Event Logger** - Audit-grade event tracking
- **Data Provider** - Historical data loading and caching

### **Integration Tests**
- **EventDrivenStrategyEngine** - Component coordination
- **API Endpoints** - Backend API integration
- **Component Chain** - Position → Exposure → Risk → P&L flow

### **E2E Tests**
- **Frontend Wizard** - Complete wizard flow
- **Frontend Results** - Results display and interaction
- **Backtest Workflow** - End-to-end backtesting
- **Deployment** - Production deployment validation

---

## 🧪 **Test Requirements**

### **Unit Tests Must Include**
- ✅ Component initialization
- ✅ Core functionality
- ✅ Error handling
- ✅ Edge cases
- ✅ Input validation
- ✅ Output verification

### **Integration Tests Must Include**
- ✅ Component interactions
- ✅ Data flow between components
- ✅ Error propagation
- ✅ Performance requirements
- ✅ Redis messaging
- ✅ Event ordering

### **E2E Tests Must Include**
- ✅ Complete user workflows
- ✅ Frontend-backend integration
- ✅ API endpoint functionality
- ✅ Data persistence
- ✅ Performance benchmarks
- ✅ Error recovery

---

## 📊 **Test Data**

### **Sample Data Files**
- `test_event_log.csv` - Sample event log data
- Mock market data for backtesting
- Sample configuration files
- Test user scenarios

### **Mock Objects**
- Mock data providers
- Mock position monitors
- Mock event loggers
- Mock external APIs

---

## 🔧 **Test Configuration**

### **pytest.ini**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### **conftest.py**
Shared fixtures and test configuration for all tests.

---

## 📈 **Test Coverage Goals**

- **Unit Tests**: 90%+ coverage for all components
- **Integration Tests**: 80%+ coverage for component interactions
- **E2E Tests**: 100% coverage for critical user workflows

---

## 🚨 **Test Failures**

### **Current Status** (October 3, 2025)
- ✅ **Unit Tests**: 9/9 component tests passing (all async issues fixed)
- ✅ **Integration Tests**: 4/4 passing (all async decorators added, data paths fixed)
- ❌ **E2E Tests**: Not yet implemented
- ✅ **Import Paths**: All fixed and working
- ✅ **Data Path Resolution**: Fixed for all test execution directories
- ✅ **Async Test Support**: All tests now properly decorated with @pytest.mark.asyncio

### **Common Issues**
1. **Import Errors** - ✅ FIXED: All import paths corrected
2. **Redis Connection** - Ensure Redis is running
3. **Data Files** - ✅ FIXED: Data path resolution works from any directory
4. **Environment Variables** - Check configuration
5. **Async Tests** - ✅ FIXED: All async tests now have proper decorators
6. **Data Path Resolution** - ✅ FIXED: Integration tests use absolute paths

### **Debugging**
```bash
# Run with verbose output
pytest -v -s

# Run single test with debugging
pytest -v -s tests/unit/components/test_position_monitor.py::TestPositionMonitor::test_balance_tracking

# Check test discovery
pytest --collect-only
```

---

## 📝 **Writing Tests**

### **Test Naming Convention**
- Files: `test_<component_name>.py`
- Classes: `Test<ComponentName>`
- Methods: `test_<functionality>`

### **Test Structure**
```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestComponentName:
    """Test suite for ComponentName."""
    
    @pytest.fixture
    def mock_dependency(self):
        """Create mock dependency."""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_core_functionality(self, mock_dependency):
        """Test core component functionality."""
        # Arrange
        component = ComponentName(mock_dependency)
        
        # Act
        result = await component.some_method()
        
        # Assert
        assert result is not None
        assert result['status'] == 'success'
```

---

## 🎯 **Success Criteria**

Tests are considered successful when:
- ✅ All tests pass
- ✅ Coverage targets met
- ✅ Performance benchmarks met
- ✅ No flaky tests
- ✅ Clear error messages
- ✅ Fast execution time

**Total Test Files**: 18+ test files across all categories
**Target Coverage**: 90%+ for critical components
**Execution Time**: < 5 minutes for full test suite

---

## 🔄 **Next Steps for Testing**

### **Immediate Priorities**
1. ✅ **Async Test Issues** - FIXED: All async tests now working with proper decorators

2. **Create E2E Tests** - Implement comprehensive end-to-end tests
   - Frontend wizard flow tests
   - Complete backtest workflow tests
   - API integration tests

3. **Frontend Testing** - Use Docker setup for frontend testing
   ```bash
   ./deploy/test-frontend.sh
   ```

4. **Test Data Organization** - Consider creating separate test fixtures
   - Move test-specific data to `tests/fixtures/`
   - Keep real data in `data/` for integration tests
   - Create mock data for unit tests

### **Testing Roadmap**
- **Week 1**: ✅ COMPLETE - Fixed async tests, all tests passing
- **Week 2**: Create E2E test framework, implement frontend integration tests
- **Week 3**: Performance testing and optimization
- **Week 4**: Production deployment testing

### **Recent Fixes Applied**
- ✅ **Async Test Decorators**: Added `@pytest.mark.asyncio` to all async test functions
- ✅ **Data Path Resolution**: Fixed integration tests to use absolute paths for data directory
- ✅ **Import Path Corrections**: Updated all import statements after file reorganization
- ✅ **Method Name Fixes**: Corrected test method calls to match actual implementation
- ✅ **Test Structure**: All 13 tests now passing (9 unit + 4 integration)
