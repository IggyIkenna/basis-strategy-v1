# Venue-Centric Architecture Refactoring - Agent Planning Tasks

## Context

Complete architectural refactoring to venue-centric naming and structure. **NO backward compatibility** - clean break with old naming. Remove all old references, code, and documentation. Maintain canonical architecture and code principles throughout.

## Agent Planning Tasks

### **TASK 1: Factory Renaming & Core Refactoring**

**Objective**: Rename `ExecutionInterfaceFactory` to `VenueInterfaceFactory` and update all references

**Files to Rename**:
- `backend/src/basis_strategy_v1/core/interfaces/execution_interface_factory.py` → `venue_interface_factory.py`

**Files to Update**:
- All imports in components that use the factory
- All test files that reference the factory
- All documentation that references the factory
- All quality gate scripts
- All `.cursor/` task files

**Key Changes**:
```python
# REMOVE all references to ExecutionInterfaceFactory
# REPLACE with VenueInterfaceFactory
# UPDATE method names to be venue-centric
# REMOVE old error codes, ADD new venue-centric error codes
```

**Validation**:
- All tests pass
- All quality gates pass
- No references to old factory name remain
- All imports work correctly

---

### **TASK 2: Manager Consolidation**

**Objective**: Rename and consolidate execution managers to venue-centric architecture

**Files to Rename**:
- `backend/src/basis_strategy_v1/core/execution/execution_interface_manager.py` → `venue_interface_manager.py`
- `backend/src/basis_strategy_v1/core/execution/execution_manager.py` → `venue_manager.py`

**Files to Update**:
- All components that use these managers
- All test files
- All documentation
- All quality gate scripts
- All `.cursor/` task files

**Key Changes**:
```python
# REMOVE all references to ExecutionInterfaceManager
# REMOVE all references to ExecutionManager
# REPLACE with VenueInterfaceManager and VenueManager
# UPDATE method names to be venue-centric
# REMOVE old error codes, ADD new venue-centric error codes
```

**Validation**:
- All tests pass
- All quality gates pass
- No references to old manager names remain
- All imports work correctly

---

### **TASK 3: Spec Reorganization**

**Objective**: Reorganize specification files to reflect venue-centric architecture

**Files to Rename**:
- `docs/specs/06_VENUE_MANAGER.md` → `06_VENUE_MANAGER.md`
- `docs/specs/07_VENUE_INTERFACE_MANAGER.md` → `07_VENUE_INTERFACE_MANAGER.md`
- `docs/specs/07B_EXECUTION_INTERFACES.md` → `07A_VENUE_INTERFACES.md`
- `docs/specs/07C_EXECUTION_INTERFACE_FACTORY.md` → `07B_VENUE_INTERFACE_FACTORY.md`

**Files to Update**:
- All cross-references between specs
- All documentation links
- All README files
- All task files in `.cursor/tasks/`
- All quality gate scripts
- All architectural documentation

**Key Changes**:
```markdown
# REMOVE all references to old spec names
# REPLACE with new venue-centric spec names
# UPDATE all cross-references
# UPDATE all links
# REMOVE old spec content, REPLACE with venue-centric content
```

**Validation**:
- All spec links work correctly
- All cross-references are updated
- No references to old spec names remain
- All documentation is consistent

---

### **TASK 4: Component Refactoring**

**Objective**: Update all components to use new venue-centric architecture

**Components to Update**:
- `PositionMonitor` - update factory reference
- `EventDrivenStrategyEngine` - update factory and manager references
- All execution-related components
- All test files
- All quality gate scripts

**Key Changes**:
```python
# REMOVE all imports of old classes
# REPLACE with new venue-centric imports
# UPDATE all method calls to use new names
# REMOVE old error handling, ADD new venue-centric error handling
# UPDATE all logging to use new names
```

**Validation**:
- All components work with new architecture
- All tests pass
- All quality gates pass
- No references to old component names remain

---

### **TASK 5: Test File Reorganization**

**Objective**: Rename and update all test files to reflect new architecture

**Files to Rename**:
- `tests/unit/test_execution_interface_factory.py` → `test_venue_interface_factory.py`
- `tests/unit/test_execution_interface_manager.py` → `test_venue_interface_manager.py`
- `tests/unit/test_execution_manager.py` → `test_venue_manager.py`
- `tests/integration/test_execution_interface_factory_extensions.py` → `test_venue_interface_factory_extensions.py`

**Files to Update**:
- All test class names
- All test method names
- All test descriptions
- All test imports
- All test fixtures
- All test data

**Key Changes**:
```python
# REMOVE all references to old class names in tests
# REPLACE with new venue-centric class names
# UPDATE all test method names
# UPDATE all test descriptions
# REMOVE old test data, ADD new venue-centric test data
```

**Validation**:
- All tests pass
- All test names reflect new architecture
- All test descriptions are updated
- No references to old class names remain

---

### **TASK 6: Quality Gate Updates**

**Objective**: Update all quality gate scripts to use new architecture

**Files to Update**:
- `scripts/test_implementation_gap_quality_gates.py`
- All other quality gate scripts
- All compliance checks
- All architectural validation

**Key Changes**:
```python
# REMOVE all references to old class names in quality gates
# REPLACE with new venue-centric class names
# UPDATE all compliance checks
# UPDATE all architectural validation
# REMOVE old quality gate logic, ADD new venue-centric logic
```

**Validation**:
- All quality gates pass
- All compliance checks work
- All architectural validation passes
- No references to old class names remain

---

### **TASK 7: Documentation Updates**

**Objective**: Update all documentation to reflect new architecture

**Files to Update**:
- All README files
- All architectural documentation
- All component specifications
- All workflow guides
- All ADRs
- All `.cursor/` task files
- All `.cursor/` plan files

**Key Changes**:
```markdown
# REMOVE all references to old class names in documentation
# REPLACE with new venue-centric class names
# UPDATE all examples
# UPDATE all diagrams
# REMOVE old documentation content, REPLACE with venue-centric content
```

**Validation**:
- All documentation links work
- All examples use new names
- All diagrams are updated
- No references to old class names remain

---

### **TASK 8: Agent Task Updates**

**Objective**: Update all `.cursor/` files to use new architecture

**Files to Update**:
- All `.cursor/tasks/` files
- All `.cursor/plans/` files
- All agent instructions
- All refactoring prompts

**Key Changes**:
```markdown
# REMOVE all references to old class names in agent tasks
# REPLACE with new venue-centric class names
# UPDATE all task descriptions
# UPDATE all plan references
# REMOVE old task content, REPLACE with venue-centric content
```

**Validation**:
- All agent tasks work with new architecture
- All task descriptions are updated
- All plan references are correct
- No references to old class names remain

---

## Implementation Order

1. **TASK 1**: Factory Renaming & Core Refactoring
2. **TASK 2**: Manager Consolidation
3. **TASK 3**: Spec Reorganization
4. **TASK 4**: Component Refactoring
5. **TASK 5**: Test File Reorganization
6. **TASK 6**: Quality Gate Updates
7. **TASK 7**: Documentation Updates
8. **TASK 8**: Agent Task Updates

## Success Criteria

- **100% Test Coverage**: All tests pass with new architecture
- **100% Quality Gate Compliance**: All quality gates pass
- **100% Documentation Consistency**: All links and references work
- **100% Agent Task Updates**: All `.cursor/` files updated
- **0% Old References**: No references to old class names remain
- **Architectural Clarity**: Clear, consistent venue-centric naming throughout

## Critical Principles

1. **NO Backward Compatibility**: Remove all old references completely
2. **Clean Break**: No legacy support or compatibility layers
3. **Canonical Architecture**: Maintain all architectural principles
4. **Code Quality**: Maintain all code quality standards
5. **Comprehensive Updates**: Update everything, leave nothing behind
6. **Validation**: Verify everything works after each task

This refactoring will create a clean, venue-centric architecture with no legacy baggage.