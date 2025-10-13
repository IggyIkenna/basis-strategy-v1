# Implementation Gap Resolution Agent Instructions

## Mission
Use the cleaned `implementation_gap_report.json` to create a comprehensive implementation plan that maps existing methods to canonical specifications and identifies what actually needs to be built vs. what needs to be renamed/refactored.

## Primary Objectives

### 1. Method Mapping Analysis
- **Map existing methods to canonical specs**: Identify which existing methods can fulfill canonical requirements
- **Identify true gaps**: Determine what actually needs to be implemented vs. renamed
- **Preserve working functionality**: Don't break existing working methods unnecessarily

### 2. Implementation Strategy
- **Rename existing methods**: Map existing methods to canonical names where functionality matches
- **Implement missing methods**: Create only the methods that don't have existing equivalents
- **Refactor for compliance**: Update existing methods to match canonical signatures and behavior

### 3. Component-by-Component Plan
- **Position Monitor**: Map 19 existing methods to 3 canonical methods + keep useful extras
- **Exposure Monitor**: Analyze existing vs. canonical methods
- **Risk Monitor**: Map existing methods to canonical requirements
- **All other components**: Follow same pattern

## Analysis Methodology

### Step 1: Method Mapping
For each component in `implementation_gap_report.json`:

1. **Analyze existing methods**:
   - Read the actual implementation file
   - Understand what each existing method does
   - Map functionality to canonical requirements

2. **Identify mappings**:
   - `get_all_positions()` → `get_current_positions()` (if functionality matches)
   - `calculate_positions()` → `get_real_positions()` (if functionality matches)
   - Keep useful methods that aren't in canonical spec

3. **Identify true gaps**:
   - Methods that have no existing equivalent
   - Methods that need significant refactoring to match canonical behavior

### Step 2: Implementation Plan Generation
For each component:

1. **Rename existing methods** (low effort, high value):
   - Update method names to match canonical spec
   - Update method signatures to match canonical spec
   - Update docstrings to match canonical spec

2. **Implement missing methods** (medium effort, high value):
   - Create methods that have no existing equivalent
   - Ensure they follow canonical patterns

3. **Refactor existing methods** (high effort, medium value):
   - Update methods that need behavior changes
   - Ensure they follow canonical patterns

### Step 3: Task Generation
Create specific tasks for each component:

1. **Position Monitor Tasks**:
   - Map `get_all_positions()` to `get_current_positions()`
   - Map `calculate_positions()` to `get_real_positions()`
   - Implement `update_state()` method
   - Keep useful methods like `get_position_summary()`

2. **Exposure Monitor Tasks**:
   - Analyze existing methods vs. canonical requirements
   - Create implementation plan

3. **Risk Monitor Tasks**:
   - Analyze existing methods vs. canonical requirements
   - Create implementation plan

## Success Criteria

### For Each Component:
- ✅ All canonical methods implemented or mapped
- ✅ Existing working functionality preserved
- ✅ Canonical compliance score improved
- ✅ No breaking changes to existing functionality

### Overall:
- ✅ Implementation gap report shows 100% canonical compliance
- ✅ All components follow canonical specifications
- ✅ Existing functionality preserved and enhanced

## Reference Sources

### Canonical Specifications:
- `docs/specs/01_POSITION_MONITOR.md` - Position Monitor canonical spec
- `docs/specs/02_EXPOSURE_MONITOR.md` - Exposure Monitor canonical spec
- `docs/specs/03_RISK_MONITOR.md` - Risk Monitor canonical spec
- All other component specs in `docs/specs/`

### Implementation Files:
- `backend/src/basis_strategy_v1/core/components/position_monitor.py`
- `backend/src/basis_strategy_v1/core/components/exposure_monitor.py`
- `backend/src/basis_strategy_v1/core/components/risk_monitor.py`
- All other component implementation files

### Analysis Data:
- `implementation_gap_report.json` - Current implementation status
- Component specifications - Canonical requirements

## Output

Generate:
1. **Component-by-component implementation plan**
2. **Method mapping documentation**
3. **Specific tasks for each component**
4. **Updated implementation gap report** (after completion)

## Example: Position Monitor Analysis

### Current Status:
- **Canonical methods needed**: 3 (`get_real_positions`, `get_current_positions`, `update_state`)
- **Existing methods**: 19 (including useful ones like `get_position_summary`)
- **Compliance score**: 0.4

### Proposed Mapping:
- `get_all_positions()` → `get_current_positions()` (rename + update signature)
- `calculate_positions()` → `get_real_positions()` (rename + update signature)
- Implement `update_state()` (new method)
- Keep `get_position_summary()` and other useful methods

### Tasks:
1. Rename `get_all_positions()` to `get_current_positions()`
2. Rename `calculate_positions()` to `get_real_positions()`
3. Implement `update_state()` method
4. Update method signatures to match canonical spec
5. Update docstrings to match canonical spec
6. Keep existing useful methods

This approach preserves working functionality while achieving canonical compliance.
