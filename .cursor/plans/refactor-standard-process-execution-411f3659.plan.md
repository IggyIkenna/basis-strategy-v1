<!-- 411f3659-da09-446d-b0ba-5fec930a6f2f b9a707fe-7642-4511-b0cb-08247edebb66 -->
# Refactor Standard Process Execution Plan

## Context

We're mid-refactor implementing ADR-058 (Unified Order/Trade System). The codebase shows:

- **NEW CODE EXISTS**: All strategies already use `make_strategy_decision() -> List[Order]` (ADR-058 implementation)
- **OLD CODE REMAINS**: `core/components/strategy_manager.py` still references `decide_action()` (legacy)
- **MIXED STATE**: Strategy Manager wrapper exists but delegates to new strategy classes
- **REPO STRUCTURE**: Updated test path is `/Users/ikennaigboaka/Documents/basis-strategy-v1/tests/integration/test_repo_structure_integration.py`

## User Clarifications

1. **Strategy Manager**: Refactor to use unified `List[Order]` system (remove legacy StrategyAction)
2. **Venue-centric specs**: Update specs marked as "Legacy execution-centric" to venue-centric architecture
3. **Implementation gaps**: Validate and document only - DON'T implement if deprecated logic

## Phase 1: Pre-Flight Validation

### 1.1 Verify Test Infrastructure

- Check all quality gate tests exist (skip if missing per user)
- Validate `tests/integration/test_repo_structure_integration.py` exists and works
- Identify which tests from refactor process are actually present

### 1.2 Check Current Refactor State

- Examine `strategy_manager.py` for legacy `decide_action()` and `break_down_action()` usage
- Verify new Order/Trade models exist in `core/models/order.py`
- Check if `StrategyAction` is still referenced anywhere
- Document what's truly deprecated vs what needs updating

## Phase 2: Documentation Foundation (Agents 1-2)

### 2.1 Docs Specs Implementation Status Agent

- Add comprehensive "Current Implementation Status" sections to all `docs/specs/` files
- Document architecture compliance status from `implementation_gap_report.json`
- Mark methods as "DEPRECATED - replaced by ADR-058" where applicable:
  - `break_down_action()` → replaced by `List[Order]` return from strategies
  - `decide_action()` → replaced by `make_strategy_decision()`
- Extract TODO items from codebase for real refactoring needs
- Validate 19-section format compliance

**Expected Outputs**:

- Updated specs with implementation status
- Clear marking of deprecated vs missing functionality
- Validation of which "gaps" are actually legacy code

### 2.2 Docs Consistency Agent

- Validate cross-references between documentation files
- Fix broken internal links
- Ensure architectural principles consistently applied
- Validate 19-section component specification format
- **NEW**: Check Event Logging Requirements and Error Codes sections

## Phase 3: Core Implementation (Agents 3-4)

### 3.1 Strategy Manager Refactor (ADR-058)

**Critical Refactor**: Remove legacy StrategyAction system

**Current State Analysis**:

- `strategy_manager.py` line 133: `action = self.decide_action(...)` ← LEGACY
- All strategy subclasses: `make_strategy_decision() -> List[Order]` ← NEW (CORRECT)
- Need to update wrapper to use new interface

**Refactor Tasks**:

1. **Remove legacy methods** from `strategy_manager.py`:

   - Remove `decide_action()` method
   - Remove `break_down_action()` method
   - Remove any `StrategyAction` references

2. **Update delegation pattern**:

   - Change wrapper to call strategy's `make_strategy_decision()` directly
   - Return `List[Order]` instead of `StrategyAction`
   - Update all callers (Event Engine, tests)

3. **Update VenueManager integration**:

   - Ensure VenueManager accepts `List[Order]`
   - Remove instruction block generation (now handled by orders)
   - Update tight loop to process orders sequentially

4. **Clean up imports and references**:

   - Remove `StrategyAction` imports
   - Remove `execution_instructions` references
   - Validate ADR-058 compliance

### 3.2 Update Venue-Centric Specs

**Specs to Update** (marked as obsolete in TARGET_REPOSITORY_STRUCTURE.md):

- `docs/specs/06_VENUE_MANAGER.md` - Update from execution-centric to venue-centric
- `docs/specs/07_VENUE_INTERFACE_MANAGER.md` - Update terminology and patterns
- `docs/specs/07B_EXECUTION_INTERFACES.md` - Rename to venue interfaces focus

**Changes Required**:

- Replace "Execution Manager" → "Venue Manager" (orchestration focus)
- Replace "Execution Interface" → "Venue Interface" (venue-specific adapters)
- Update architectural diagrams to show venue-centric flow
- Align with `VENUE_ARCHITECTURE.md` canonical patterns

### 3.3 Architecture Compliance Agent

- Scan for rule violations from `.cursor/rules.json`
- Fix hardcoded values, singleton pattern issues
- Ensure mode-agnostic design where appropriate
- Verify configuration loaded from YAML
- **Run post-refactor compliance check**: `test_implementation_gap_quality_gates.py`

## Phase 4: System Validation (Agents 5-6)

### 4.1 Quality Gates Agent

**Approach**: Skip missing tests, run existing ones

**Pre-Execution**:

- List all test files that actually exist
- Cross-reference with quality gate runner configuration
- Document which gates are skipped (test doesn't exist)

**Execution**:

- Run quality gates for existing tests only
- Fix failing gates where possible
- Document unfixable issues with reasoning
- Target: 60%+ overall pass rate (of existing tests)

**Key Quality Gates** (if they exist):

- `test_implementation_gap_quality_gates.py` - Check ADR-058 compliance
- `test_integration_alignment_quality_gates.py` - Validate integration
- `test_env_config_usage_sync_quality_gates.py` - Env var documentation
- Repository structure: `tests/integration/test_repo_structure_integration.py`

### 4.2 Integration Alignment Agent

**Trigger**: ONLY after quality gates pass

- Validate component-to-component workflow alignment
- Verify function call and method signature alignment
- Check links and cross-reference completeness
- Validate 19-section format compliance
- Ensure Event Logging and Error Codes integration
- Target: 100% integration alignment

## Phase 5: Conflict Detection (Agents 7-8)

### 5.1 Docs Logical Inconsistency Detection

- Cross-reference all documentation
- Detect semantic contradictions
- Identify structural inconsistencies
- Generate conflict matrix with canonical source hierarchy
- Output: `DOCS_LOGICAL_INCONSISTENCY_REPORT_[timestamp].md`

### 5.2 Docs Inconsistency Resolution

- Read inconsistency report
- Apply user-approved fixes only
- Update non-canonical docs to match canonical sources
- Validate no new conflicts introduced
- Generate completion report

## Phase 6: Final Validation (Agents 9-10)

### 6.1 Comprehensive Documentation Agent

- Final comprehensive validation across all aspects
- Validate documentation consistency
- Verify integration alignment
- Check configuration alignment
- Ensure canonical architecture compliance

### 6.2 Architecture Compliance Code Scanner

- Scan for ADR violations (especially ADR-058)
- Identify line-by-line violations with file paths
- Generate actionable task reports
- Provide prioritized breakdown
- Create implementation roadmap

## Critical Success Criteria

### Strategy Manager Refactor (ADR-058)

- ✅ All `decide_action()` calls removed
- ✅ All `break_down_action()` calls removed  
- ✅ All `StrategyAction` references removed
- ✅ Wrapper delegates to `make_strategy_decision() -> List[Order]`
- ✅ VenueManager processes `List[Order]` directly
- ✅ All tests updated for new interface

### Venue-Centric Specs

- ✅ Specs use "Venue Manager" not "Execution Manager"
- ✅ Specs use "Venue Interface" not "Execution Interface"
- ✅ Architectural diagrams show venue-centric flow
- ✅ Aligned with VENUE_ARCHITECTURE.md

### Implementation Status

- ✅ All deprecated methods clearly marked
- ✅ New implementations documented
- ✅ No confusion between legacy and current code
- ✅ Implementation gap report updated

### Quality Gates

- ✅ 60%+ pass rate (existing tests only)
- ✅ Repository structure test uses correct path
- ✅ Integration alignment 100%
- ✅ ADR-058 compliance validated

## Validation Commands

```bash
# Pre-flight: Check test availability
ls -la tests/integration/test_repo_structure_integration.py
python scripts/run_quality_gates.py --list

# During refactor: Validate ADR-058 compliance
grep -r "decide_action\|break_down_action\|StrategyAction" backend/src/basis_strategy_v1/core/
grep -r "List\[Order\]" backend/src/basis_strategy_v1/core/

# Post-refactor: Run quality gates
python scripts/test_implementation_gap_quality_gates.py
python scripts/run_quality_gates.py
python tests/integration/test_repo_structure_integration.py

# Final validation
python scripts/test_integration_alignment_quality_gates.py
```

## Risk Mitigation

1. **Breaking Changes**: Strategy Manager refactor is breaking change

   - Mitigation: Update all callers in same commit
   - Validation: Run full test suite after changes

2. **Deprecated Logic**: Risk of implementing obsolete code

   - Mitigation: Document before implementing, get confirmation
   - Validation: Check ADRs and implementation_gap_report.json

3. **Missing Tests**: Some quality gates may not exist

   - Mitigation: Skip gracefully, document what's missing
   - Validation: List available tests before execution

4. **Documentation Drift**: Specs may conflict during refactor

   - Mitigation: Use canonical source hierarchy for resolution
   - Validation: Run inconsistency detection agent

## Timeline Estimate

- Phase 1 (Pre-Flight): 1-2 hours
- Phase 2 (Docs Foundation): 6-9 hours  
- Phase 3 (Core Implementation): 8-12 hours
- Phase 4 (System Validation): 7-10 hours
- Phase 5 (Conflict Detection): 5-7 hours
- Phase 6 (Final Validation): 5-7 hours

**Total**: 32-47 hours (spread across multiple agent runs)

## Notes

- This is a continuation of ongoing ADR-058 refactor
- New code already exists (strategies use Order/Trade)
- Focus is on completing the migration and documentation
- Some "missing" methods are actually deprecated, not gaps
- Repository structure test path updated per codebase

### To-dos

- [ ] Agent 1: Validate all component specs follow 19-section format and create IMPLEMENTATION_REFACTOR_PLAN.md
- [ ] Agent 2: Ensure 100% documentation consistency with working links and canonical structure
- [ ] Agent 3: Run implementation gap analysis and generate prioritized resolution plan
- [ ] Agent 4: Rename existing methods to canonical names and update all callers
- [ ] Agent 5: Create missing canonical methods and implement missing components
- [ ] Agent 6: Fix compliance issues and ensure all components achieve 1.00 compliance score
- [ ] Agent 7: Update Event Engine and Position Update Handler for 100% integration alignment
- [ ] Agent 8: Check for orphaned tests and ensure proper quality gates integration
- [ ] Agent 9: Run all quality gates and fix failures to achieve 75%+ pass rate
- [ ] Agent 10: Final validation of complete refactor success with comprehensive report