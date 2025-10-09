# Documentation Deviations and Corrections 📋

**Purpose**: Document all deviations found between docs/ and actual codebase src/  
**Status**: 🔄 Additional deviations found and being corrected  
**Updated**: October 6, 2025  
**Last Reviewed**: October 8, 2025  
**Status**: ✅ Aligned with canonical sources (.cursor/tasks/ + MODES.md)

---

## 🔍 **Deviations Found and Corrected**

### **NEW DEVIATIONS FOUND (October 8, 2025)**

### **4. Configuration System Implementation** ✅ RESOLVED

**Issue**: Documentation previously described JSON-based configuration hierarchy but the system uses YAML-based configuration.

**Current Status**:
- ✅ YAML files in `configs/modes/`, `configs/venues/`, `configs/share_classes/` exist and work
- ✅ Configuration system uses YAML files with environment variable overrides
- ✅ `configs/scenarios/` directory correctly removed (scenarios eliminated per canonical architecture)

**Resolution**: All code references updated to use YAML-only configuration system.

### **5. Architectural Violations** 🔄 PARTIALLY RESOLVED

**Issue**: Multiple components violate CANONICAL_ARCHITECTURAL_PRINCIPLES.md requirements.

**Critical Violations Status**:

#### **5.1 Hardcoded Values Violation** ✅ RESOLVED
**Location**: `backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py:872-877`
**Previous Violation**: Hardcoded LTV values instead of using configuration
**Resolution**: LTV values now loaded from YAML configuration files per canonical architecture

#### **5.2 Environment Variable Integration Violations** ✅ RESOLVED
**Locations**: 
- `backend/src/basis_strategy_v1/core/interfaces/onchain_execution_interface.py:1-41`
- `backend/src/basis_strategy_v1/core/interfaces/cex_execution_interface.py:1-41`
- `backend/src/basis_strategy_v1/infrastructure/config/config_manager.py:42-67`

**Previous Violations**:
- Uses hardcoded config keys instead of environment-specific routing
- Missing BASIS_ENVIRONMENT routing for venue credentials
- Missing BASIS_EXECUTION_MODE routing for backtest vs live execution

**Resolution**: Environment-specific credential routing implemented per canonical architecture

#### **5.3 Strategy Manager Architecture Violations** ❌ NOT RESOLVED
**Location**: `backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py:1-42`
**Current Violations**:
- Still uses complex transfer_manager.py (1068 lines) that should be removed
- Missing inheritance-based strategy modes with standardized wrapper actions
- No strategy factory for mode-based instantiation
- Has hardcoded mode checks instead of config-driven parameters

**Required Fix**: Complete refactoring to align with canonical architecture (Task 11: Strategy Manager Refactor)

#### **5.4 Fail-Fast Configuration Violations** ❌ NOT RESOLVED
**Location**: `backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py:332-336`
**Current Violation**: Uses `.get()` patterns with defaults instead of fail-fast approach
```python
# WRONG - uses .get() with defaults
self.aave_ltv_warning = self.config.get('venues', {}).get('aave_ltv_warning', 0.75)
self.aave_ltv_critical = self.config.get('venues', {}).get('aave_ltv_critical', 0.85)
```
**Required Fix**: Use direct config access and let KeyError raise if missing

### **6. NEW ARCHITECTURAL CONFLICTS (October 8, 2025)**

#### **6.1 Component Data Flow Architecture Violations** ❌ NOT RESOLVED
**Issue**: Component specifications show inconsistent data flow patterns that violate canonical architecture.

**Violations Found**:
- **Position Monitor**: Spec shows direct data provider dependency, but canonical architecture requires no external dependencies
- **Exposure Monitor**: Spec shows direct position monitor references, but canonical architecture requires parameter-based data flow
- **Risk Monitor**: Spec shows direct exposure monitor references, but canonical architecture requires parameter-based data flow
- **P&L Calculator**: Spec shows direct exposure monitor references, but canonical architecture requires parameter-based data flow

**Required Fix**: Update all component specifications to use parameter-based data flow (no direct component references)

#### **6.2 Tight Loop Architecture Implementation Gap** ❌ NOT RESOLVED
**Issue**: Component specifications don't properly implement the mandatory tight loop architecture.

**Canonical Requirement**: `position_monitor → exposure_monitor → risk_monitor → pnl_monitor`

**Current Violations**:
- Components show direct method calls instead of sequential chain triggers
- Missing proper Redis pub/sub integration for live mode
- No clear trigger mechanism for tight loop execution
- Components don't await chain completion before proceeding

**Required Fix**: Implement proper tight loop architecture with sequential triggers and chain completion awaiting

#### **6.3 Mode-Agnostic vs Mode-Specific Architecture Confusion** ❌ NOT RESOLVED
**Issue**: Component specifications mix mode-agnostic and mode-specific logic incorrectly.

**Violations**:
- **Position Monitor**: Should be mode-agnostic but spec shows mode-specific logic
- **Exposure Monitor**: Should be mode-agnostic but spec shows mode-specific calculations
- **Risk Monitor**: Should be mode-agnostic but spec shows mode-specific risk types
- **P&L Calculator**: Should be mode-agnostic but spec shows mode-specific P&L components

**Required Fix**: Clarify which components are mode-agnostic vs mode-specific per canonical architecture

#### **6.4 Singleton Pattern Implementation Gap** ❌ NOT RESOLVED
**Issue**: Component specifications don't implement the required singleton pattern.

**Canonical Requirement**: All components must use singleton pattern to ensure single instances across entire run.

**Current Violations**:
- Components show standard class instantiation instead of singleton pattern
- No shared config instance across components
- No shared data provider instance across components
- No synchronized data flows between components

**Required Fix**: Implement singleton pattern for all components with shared instances

#### **6.5 Frontend Implementation Gap** ❌ NOT RESOLVED
**Issue**: Frontend specification shows incomplete implementation status.

**Current Status**:
- ✅ Wizard components fully implemented
- ❌ Results components not implemented (ResultsPage, MetricCard, PlotlyChart, EventLogViewer)
- ❌ Shared components not implemented (Button, Input, Select, etc.)
- ❌ API service not implemented
- ❌ Type definitions not implemented

**Required Fix**: Complete frontend implementation per specification

#### **6.6 Execution Interface Architecture Mismatch** ❌ NOT RESOLVED
**Issue**: Execution interface specifications don't match actual implementation.

**Violations**:
- Spec shows `CEXExecutionManager` and `OnChainExecutionManager` but actual files are `CEXExecutionInterface` and `OnChainExecutionInterface`
- Spec shows complex execution manager logic but interfaces should be simple execution abstractions
- Missing proper integration with EventDrivenStrategyEngine
- Missing proper position update handler integration

**Required Fix**: Align execution interface specifications with actual implementation

### **7. Implementation Status Claims** 🔄 BEING CORRECTED

**Issue**: Multiple documents claim "100% implemented", "fully functional", "production ready" but critical issues remain.

**Actual Status**:
- ✅ Core components implemented (95% complete)
- 🔄 Critical issues: Pure lending yield calculation (1166% APY), quality gates (5/14 passing)
- 🔄 Missing prerequisites: Redis installation requirement not documented
- ❌ **NEW**: Component data flow architecture violations
- ❌ **NEW**: Tight loop architecture implementation gap
- ❌ **NEW**: Mode-agnostic vs mode-specific architecture confusion
- ❌ **NEW**: Singleton pattern implementation gap
- ❌ **NEW**: Frontend implementation gap (results components missing)
- ❌ **NEW**: Execution interface architecture mismatch

**Files Being Updated**:
- `docs/README.md` - Updated status claims
- `docs/INDEX.md` - Updated status claims  
- `docs/QUICK_START.md` - Added prerequisites section
- `docs/START_HERE.md` - Updated status claims
- `docs/WORKFLOW_GUIDE.md` - Updated status claims
- `docs/ARCHITECTURAL_DECISIONS.md` - Updated implementation status

### **6. Agent Setup Documentation** 🔄 BEING CORRECTED

**Issue**: AGENT_SETUP_GUIDE.md describes planned agent setup but agents have already completed 95% of work.

**Actual Status**:
- ✅ Agents have completed 95% of tasks
- ✅ Agent progress tracking files exist (`agent-progress.json`, `agent-b-progress.txt`)
- ✅ Some agent scripts exist (`preflight_check.py`, `validate_completion.py`, etc.)
- ❌ Agent workspaces (`basis-strategy-v1-agent-a`, `basis-strategy-v1-agent-b`) do not exist

**Files Being Updated**:
- `docs/AGENT_SETUP_GUIDE.md` - Updated to reflect current agent status

### **7. Deployment Scripts** 🔄 BEING CORRECTED

**Issue**: DEPLOYMENT_GUIDE.md references data upload script that doesn't exist.

**Actual Status**:
- ✅ Deployment scripts exist in `/workspace/deploy/`
- ❌ `upload_data_to_gcs.sh` script does not exist

**Files Being Updated**:
- `docs/DEPLOYMENT_GUIDE.md` - Marked data upload script as not implemented

## 🔍 **Previously Found and Corrected**

### **1. Component Backend File Paths** ✅ FIXED

**Issue**: Several component specs had incorrect backend file paths.

**Corrections Made**:

| Component | Incorrect Path in Docs | Correct Path in Codebase | Status |
|-----------|----------------------|-------------------------|---------|
| **Strategy Manager** | `core/strategies/strategy_manager.py` | `core/strategies/components/strategy_manager.py` | ✅ Fixed |
| **CEX Execution Manager** | `infrastructure/execution/cex_execution_manager.py` | `core/strategies/components/cex_execution_manager.py` | ✅ Fixed |
| **OnChain Execution Manager** | `infrastructure/execution/onchain_execution_manager.py` | `core/strategies/components/onchain_execution_manager.py` | ✅ Fixed |

**Files Updated**:
- `docs/specs/05_STRATEGY_MANAGER.md`
- `docs/specs/06_CEX_EXECUTION_MANAGER.md`
- `docs/specs/07_ONCHAIN_EXECUTION_MANAGER.md`
- `docs/COMPONENT_SPECS_INDEX.md`

### **2. Configuration Directory References** ✅ VERIFIED CORRECT

**Issue**: Some documentation referenced `configs/scenarios/` but actual implementation uses `configs/modes/`.

**Status**: ✅ **VERIFIED CORRECT**
- Strategy discovery correctly points to `configs/modes/`
- All 6 strategy configs are in `configs/modes/`
- Documentation correctly states scenarios were removed

**Files Verified**:
- `backend/src/basis_strategy_v1/infrastructure/config/strategy_discovery.py` (line 15: `SCENARIOS_DIR = Path("configs/modes")`)
- `configs/modes/` contains 6 strategy files
- `docs/REFERENCE.md` correctly notes scenarios were removed

### **3. Environment Variable Configuration** ✅ VERIFIED CORRECT

**Issue**: Documentation showed `BASIS_ENVIRONMENT=development` but validation requires `dev`.

**Status**: ✅ **VERIFIED CORRECT**
- `backend/env.dev` correctly uses `BASIS_ENVIRONMENT=dev`
- YAML configuration files correctly use environment variables
- Documentation updated to reflect correct values

**Files Verified**:
- `backend/env.dev` (line 3: `BASIS_ENVIRONMENT=dev`)
- YAML configuration files use environment variables correctly
- `docs/ENVIRONMENT_VARIABLES.md` updated with correct values

---

## ✅ **Verification Results**

### **Component Specifications** ✅ ALL ACCURATE
- All 9 component specs match actual implementation
- Method signatures match actual code
- Data structures match actual implementation
- Error codes match actual implementation

### **API Documentation** ✅ ALL ACCURATE
- API routes match actual implementation
- Request/response models match actual code
- Endpoint paths match actual routes
- Response structures match actual models

### **Configuration Documentation** ✅ ALL ACCURATE
- Config structure matches actual directories
- Environment variables match actual files
- Validation rules match actual implementation
- Loading priority matches actual code

### **Data Requirements** ✅ ALL ACCURATE
- Data file structure matches actual directories
- Validation requirements match actual implementation
- Component data access patterns match actual code
- Oracle assumptions match actual implementation

### **Architecture Documentation** ✅ ALL ACCURATE
- Component interaction flow matches actual implementation
- Event-driven engine matches actual code
- Redis messaging patterns match actual implementation
- Error logging standards match actual code

---

## 📊 **Summary**

**Total Deviations Found**: 7
**Total Deviations Fixed**: 3
**Total Deviations In Progress**: 4
**Total Files Updated**: 4

**Accuracy Status**: 🔄 **PARTIALLY ACCURATE**
- ✅ Configuration system documentation matches actual codebase
- ✅ File paths are correct
- ✅ Configuration references are accurate
- ❌ Component specifications have architectural violations
- ❌ Implementation status claims are inaccurate
- ❌ New architectural conflicts discovered

### **New Architectural Conflicts Found**
- ❌ **Component Data Flow Architecture Violations** - Components show direct dependencies instead of parameter-based flow
- ❌ **Tight Loop Architecture Implementation Gap** - Missing proper sequential chain triggers
- ❌ **Mode-Agnostic vs Mode-Specific Architecture Confusion** - Components mix logic incorrectly
- ❌ **Singleton Pattern Implementation Gap** - Components don't use singleton pattern
- ❌ **Frontend Implementation Gap** - Results components not implemented
- ❌ **Execution Interface Architecture Mismatch** - Specs don't match actual implementation

---

## 🎯 **Quality Assurance**

**Verification Method**: Systematic comparison of every docs/ file against actual src/ implementation

**Coverage**:
- ✅ All 12 component specs verified
- ✅ All API documentation verified
- ✅ All configuration documentation verified
- ✅ All architecture documentation verified
- ✅ All data requirements verified
- ✅ All environment variables verified

**Result**: Documentation has architectural violations that need to be corrected.

---

**Next Steps**: 
1. **Complete Strategy Manager Refactor** (Task 11) - Remove transfer_manager.py, implement inheritance-based architecture
2. **Fix Fail-Fast Configuration** - Update risk_monitor.py to use direct config access
3. **Fix Component Data Flow Architecture** - Update all component specs to use parameter-based flow
4. **Implement Tight Loop Architecture** - Add proper sequential chain triggers and Redis pub/sub
5. **Clarify Mode-Agnostic vs Mode-Specific** - Update component specs to clearly separate concerns
6. **Implement Singleton Pattern** - Add singleton pattern to all components
7. **Complete Frontend Implementation** - Implement missing results components
8. **Align Execution Interface Specs** - Update specs to match actual implementation
9. **Update Implementation Status Claims** - Correct all documentation to reflect actual status
10. **Complete Agent Setup Documentation** - Update AGENT_SETUP_GUIDE.md to reflect current state
11. **Verify Quality Gates** - Ensure all quality gates pass after fixes
12. **Update Documentation** - Ensure all docs reflect corrected status