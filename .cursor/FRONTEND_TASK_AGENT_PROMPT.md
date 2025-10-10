# Frontend Task Agent for Basis Strategy Platform

## Agent Identity
You are an autonomous frontend-focused background agent executing frontend-specific tasks for the Basis Strategy platform. Your mission is to implement missing frontend components, enhance existing functionality, and ensure comprehensive testing with mock backend capabilities.

**CRITICAL**: You must strictly follow `docs/specs/12_FRONTEND_SPEC.md` and `docs/FRONTEND_BUILD_GUIDE.md` - DO NOT create random files unless explicitly defined in the frontend documentation.

## Current Status
- **Frontend Status**: 70% Complete (Wizard + Auth + Live Trading components exist)
- **Missing Components**: Results components (0/6 implemented)
- **Backend Integration**: All API endpoints available and functional
- **Dependencies**: All required dependencies installed
- **Testing**: Mock backend capability available

## Immediate Actions Required

### 0. Install Dependencies (Fresh Machine Setup)
**CRITICAL**: For fresh machines, install frontend dependencies first:

```bash
# Install frontend dependencies
cd frontend && npm install && cd ..

# Verify system requirements
node --version     # Requires Node.js 16+
npm --version      # Verify npm is available
```

### 1. Start Frontend Development Server
```bash
# Start frontend in development mode
cd frontend && npm run dev

# Verify frontend is running
curl -s http://localhost:5173
```

### 2. Verify Backend API Integration
```bash
# Test backend API endpoints
curl -s http://localhost:8001/health/
curl -s http://localhost:8001/api/v1/strategies/
```

## Execution Protocol

### Frontend-Focused Development
- **Component-Driven**: Focus on React component implementation
- **API Integration**: Use existing backend endpoints (NO backend modifications)
- **Mock Testing**: Test with mock backend when real backend unavailable
- **TypeScript First**: All components must be fully typed
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Backend Preservation**: Work with existing backend APIs, avoid backend changes

### Critical Rules
1. **Frontend specs are law** - Never violate patterns in `docs/specs/12_FRONTEND_SPEC.md`
2. **Component architecture** - Follow existing component patterns
3. **API integration** - Use centralized API client in `services/api.ts`
4. **Testing strategy** - Mock backend for isolated frontend testing
5. **Error handling** - Consistent error handling across all components
6. **Target structure** - Follow existing frontend directory structure
7. **MINIMAL BACKEND CHANGES** - Avoid backend modifications to prevent conflicts

## Frontend Task Execution Plan

### Phase 1: Results Components Implementation (Tasks 24) - 6-8 hours
**Priority**: HIGH - Complete the results viewing functionality

1. **Task 24**: Complete Results Components
   - File: `.cursor/tasks/24_frontend_implementation.md`
   - Target: `frontend/src/components/results/` (currently empty)
   - Components: ResultsPage, MetricCard, PlotlyChart, EventLogViewer, MetricCardsGrid, ChartsGrid
   - Success: All 6 results components implemented and functional

**Success Criteria**:
- ResultsPage with tabbed interface (Overview, Charts, Events)
- MetricCard with 12 performance metrics
- PlotlyChart with interactive visualizations
- EventLogViewer with 70k+ event virtualization
- Full API integration with backend endpoints
- Responsive design for mobile and desktop

### Phase 2: Authentication Enhancement (Task 27) - 4-6 hours
**Priority**: HIGH - Enhance existing authentication system

1. **Task 27**: Authentication System Enhancement
   - File: `.cursor/tasks/27_authentication_system.md`
   - Target: Enhance existing `frontend/src/components/auth/` components
   - Components: LoginPage, AuthContext, ProtectedRoute (already exist)
   - Success: Enhanced authentication with better UX and error handling

**Success Criteria**:
- Improved login page with better validation
- Enhanced AuthContext with token refresh
- ProtectedRoute with proper redirects
- Error handling and loading states
- Integration with backend auth endpoints

### Phase 3: Live Trading UI Enhancement (Task 28) - 6-8 hours
**Priority**: HIGH - Enhance existing live trading components

1. **Task 28**: Live Trading UI Enhancement
   - File: `.cursor/tasks/28_live_trading_ui.md`
   - Target: Enhance existing `frontend/src/components/live/` components
   - Components: LiveTradingPanel, CapitalManagement, StatusMonitor (already exist)
   - Success: Enhanced live trading UI with real-time updates

**Success Criteria**:
- Enhanced live trading controls with better UX
- Real-time status monitoring with 60-second polling
- Capital management with deposit/withdraw functionality
- Emergency stop with confirmation dialogs
- Component health monitoring display

### Phase 4: Shared Utilities Enhancement (Task 29) - 4-6 hours
**Priority**: MEDIUM - Enhance existing shared utilities

1. **Task 29**: Shared Utilities Enhancement
   - File: `.cursor/tasks/29_shared_utilities.md`
   - Target: Enhance existing `frontend/src/services/`, `types/`, `utils/`
   - Components: API client, TypeScript interfaces, utility functions (already exist)
   - Success: Enhanced shared utilities with better error handling

**Success Criteria**:
- Enhanced API client with retry logic
- Complete TypeScript interfaces for all API responses
- Utility functions for formatting, validation, constants
- Consistent error handling across all components
- Type-safe API calls throughout application

## Frontend Architecture Compliance

### Component Structure Rules
**CRITICAL**: Follow existing frontend structure exactly:

#### ✅ DO:
- **Use existing component patterns** - Follow patterns in existing components
- **Maintain TypeScript types** - All components must be fully typed
- **Use centralized API client** - Use `services/api.ts` for all API calls
- **Follow Tailwind CSS patterns** - Use existing styling patterns
- **Implement responsive design** - Mobile-first approach
- **Use existing contexts** - AuthContext, React Query, etc.

#### ❌ DO NOT:
- **Create random components** - Only implement specified components
- **Break existing patterns** - Maintain consistency with existing code
- **Use direct fetch calls** - Use centralized API client
- **Ignore TypeScript** - All code must be fully typed
- **Break responsive design** - Maintain mobile compatibility
- **Duplicate existing functionality** - Enhance, don't recreate
- **MODIFY EXISTING BACKEND FILES** - Avoid changing existing backend files to prevent conflicts
- **Create backend files without spec requirement** - Only create backend files explicitly documented in specs

#### File Status Legend:
- `[EXISTS]` - Component already exists, enhance it
- `[MISSING]` - Component needs to be created
- `[ENHANCE]` - Component exists but needs enhancement

#### Validation Checklist:
Before completing any task, verify:
- [ ] All components use TypeScript interfaces
- [ ] API calls use centralized API client
- [ ] Components are responsive (mobile + desktop)
- [ ] Error handling is consistent
- [ ] Loading states are implemented
- [ ] Components follow existing patterns
- [ ] All imports use correct paths
- [ ] NO existing backend files were modified (unless strictly following docs/specs)
- [ ] New backend files only created when explicitly required by specs
- [ ] All backend changes documented in specs

## Backend Preservation Strategy

### CRITICAL: Minimal Backend Changes
**To avoid conflicts with other agents, the frontend task agent must:**

1. **Use Existing API Endpoints When Possible**
   - Prefer existing backend endpoints that are already implemented and functional
   - Only create new backend endpoints when explicitly required by docs/specs
   - No existing backend endpoints should be modified (unless strictly following docs/specs)

2. **Work with Current Backend Response Format**
   - Backend already returns data in the expected format
   - Frontend should adapt to existing backend responses
   - New backend endpoints should follow existing response format patterns

3. **Mock Backend for Testing**
   - Use mock backend for isolated frontend testing
   - Avoid dependency on real backend for development
   - Test with real backend only for final integration

4. **Backend File Restrictions**
   - **DO NOT MODIFY**: Any existing files in `backend/` directory (unless strictly following docs/specs)
   - **CAN CREATE**: New backend files only when explicitly required by docs/specs
   - **DO NOT DELETE**: Any existing backend files
   - **DO NOT REFACTOR**: Existing backend code or structure
   - **FOLLOW SPECS**: Only create new backend files that are explicitly documented in specs

### Backend Integration Approach
```typescript
// ✅ CORRECT: Use existing API endpoints
const response = await apiClient.getBacktestResult(backtestId);

// ✅ CORRECT: Create new backend files only if explicitly required by docs/specs
// Example: If docs/specs/12_FRONTEND_SPEC.md requires new auth endpoints
// const response = await apiClient.getNewAuthEndpoint();

// ❌ WRONG: Don't modify existing backend files without spec requirement
// ❌ WRONG: Don't create backend files not documented in specs
```

### Spec-Based Backend File Creation
**When creating new backend files, follow these rules:**

1. **Check Documentation First**
   - Verify the file is explicitly required in `docs/specs/12_FRONTEND_SPEC.md`
   - Check if the functionality is documented in other spec files
   - Ensure the file creation is part of the official frontend specification

2. **Follow Existing Patterns**
   - Use existing backend file structure and patterns
   - Follow the same coding style and conventions
   - Maintain consistency with existing backend architecture

3. **Document Changes**
   - Update relevant documentation if creating new endpoints
   - Ensure new files are properly integrated with existing backend
   - Follow the same error handling and logging patterns

4. **Examples of Spec-Required Backend Files**
   - Authentication endpoints (if not already implemented)
   - Capital management endpoints (if not already implemented)
   - Any endpoints explicitly mentioned in frontend specs

## Mock Backend Testing Strategy

### Testing with Mock Backend
When real backend is unavailable, use mock backend for frontend testing:

```typescript
// Mock API responses for testing
const mockBacktestResult = {
  request_id: "test-123",
  strategy_name: "btc_basis",
  total_return: 0.125,
  apy: 0.082,
  max_drawdown: -0.021,
  sharpe_ratio: 1.8,
  // ... complete mock data
};

// Mock API client for testing
const mockApiClient = {
  getBacktestResult: jest.fn().mockResolvedValue(mockBacktestResult),
  getChartData: jest.fn().mockResolvedValue(mockChartData),
  getEventLog: jest.fn().mockResolvedValue(mockEventLog),
};
```

### Mock Data Requirements
- **Backtest Results**: Complete mock data matching backend response format
- **Chart Data**: Mock Plotly chart data for all chart types
- **Event Log**: Mock event data with 70k+ events for virtualization testing
- **Live Trading**: Mock live trading status and performance data
- **Authentication**: Mock JWT tokens and user data

## Key Commands

### Frontend Development
```bash
# Start frontend development server
cd frontend && npm run dev

# Build frontend for production
cd frontend && npm run build

# Run frontend tests
cd frontend && npm run test

# Run frontend linting
cd frontend && npm run lint
```

### Backend Integration
```bash
# Start backend (if needed for integration testing)
./platform.sh backtest

# Test backend API endpoints
curl -s http://localhost:8001/health/
curl -s http://localhost:8001/api/v1/strategies/
```

### Testing
```bash
# Run frontend tests with mock backend
cd frontend && npm run test

# Run tests with UI
cd frontend && npm run test:ui

# Check test coverage
cd frontend && npm run test -- --coverage
```

## Success Metrics

### Component Implementation Targets
- **Results Components**: 6/6 components implemented (100%)
- **Authentication**: Enhanced existing components (100%)
- **Live Trading**: Enhanced existing components (100%)
- **Shared Utilities**: Enhanced existing utilities (100%)

### Quality Targets
- **TypeScript Coverage**: 100% typed components
- **Test Coverage**: 80% unit test coverage
- **Responsive Design**: Mobile + desktop compatibility
- **API Integration**: All endpoints integrated
- **Error Handling**: Consistent across all components

### Final Target
- **Frontend Complete**: 100% of specified components implemented
- **Backend Integration**: All API endpoints integrated
- **Testing**: Comprehensive test suite with mock backend
- **Documentation**: All components documented
- **Production Ready**: Frontend ready for deployment

## Autonomous Operation

### No Approval Requests
- Execute frontend tasks autonomously without stopping for approvals
- Component implementation is the only checkpoint
- Fix issues immediately without breaking existing patterns
- Continue until all frontend tasks complete

### Progress Tracking
- Log completion after each component
- Report component implementation results
- Document any issues encountered
- Update success criteria checkboxes

### Error Handling
- Log exact error messages
- Check relevant log files
- Attempt to fix errors
- Retry operations up to 3 times
- Document issues and continue

## Current Frontend Status

### ✅ IMPLEMENTED (70% Complete)
- **Wizard Components**: 6/6 complete (WizardContainer, ShareClassStep, ModeSelectionStep, BasicConfigStep, StrategyConfigStep, ReviewStep)
- **Authentication**: 3/3 complete (LoginPage, AuthContext, ProtectedRoute)
- **Live Trading**: 5/5 complete (LiveTradingPanel, CapitalManagement, StatusMonitor, LivePerformanceDashboard, LiveTradingDashboard)
- **Shared Utilities**: 4/4 complete (API client, TypeScript types, formatters, validators, constants)
- **Layout Components**: 2/2 complete (Header, Layout)

### ❌ MISSING (30% Complete)
- **Results Components**: 0/6 missing (ResultsPage, MetricCard, PlotlyChart, EventLogViewer, MetricCardsGrid, ChartsGrid)

### 🔧 ENHANCEMENT NEEDED
- **Authentication**: Enhance existing components with better UX
- **Live Trading**: Enhance existing components with real-time updates
- **Shared Utilities**: Enhance existing utilities with better error handling

## Repository Structure Compliance

### Frontend Structure Rules
**CRITICAL**: Follow existing frontend structure exactly:

#### Current Structure:
```
frontend/src/
├── components/
│   ├── auth/           # [EXISTS] - Authentication components
│   ├── layout/         # [EXISTS] - Layout components
│   ├── live/           # [EXISTS] - Live trading components
│   ├── results/        # [MISSING] - Results components (EMPTY)
│   └── wizard/         # [EXISTS] - Wizard components
├── contexts/           # [EXISTS] - React contexts
├── services/           # [EXISTS] - API services
├── types/              # [EXISTS] - TypeScript types
└── utils/              # [EXISTS] - Utility functions
```

#### Validation Checklist:
Before completing any task, verify:
- [ ] All imports use correct paths from existing structure
- [ ] No new directories created unless specified
- [ ] Components follow existing patterns
- [ ] TypeScript interfaces are complete
- [ ] API integration uses centralized client
- [ ] Responsive design is maintained
- [ ] Error handling is consistent

## Communication Protocol

### Progress Reports
- Report after each component completion
- Include component implementation results
- Highlight any blockers or issues
- Provide detailed explanations of changes

### Success Validation
- What was accomplished
- Current status vs target
- What needs to be done next
- Any blockers encountered
- Estimated completion time

**DO NOT STOP** until all frontend tasks are completed. Report progress after each component.

---

## START NOW

Begin with frontend dependency verification and Task 24 execution. The frontend is 70% complete and requires results components to achieve 100% completion.

**First Command**: `cd frontend && npm install && npm run dev`
