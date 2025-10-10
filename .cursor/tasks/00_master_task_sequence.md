# MASTER TASK SEQUENCE FOR BACKGROUND AGENTS

## OVERVIEW
This is the complete sequence of tasks to execute based on the updated TASK_DOCS_CONFLICT_ANALYSIS_REPORT.md. Execute these tasks in order by priority, focusing on HIGH priority architectural violations first.

**Reference**: `TASK_DOCS_CONFLICT_ANALYSIS_REPORT.md` - Updated conflict analysis (October 10, 2025)  
**Reference**: `docs/DEVIATIONS_AND_CORRECTIONS.md` - Current architectural violations

## TASK SEQUENCE (Priority Order)

### HIGH Priority Tasks (Must Fix Before Production)
1. **23_fix_async_await_violations.md** - Fix ADR-006 violations (HIGH)
2. **strategy_manager_refactor.md** - Complete strategy manager refactor (HIGH)
3. **14_mode_agnostic_architecture_requirements.md** - Fix generic vs mode-specific violations (HIGH)

### MEDIUM Priority Tasks (Should Fix Soon)
4. **24_implement_fail_fast_configuration.md** - Implement fail-fast config (MEDIUM)
5. **13_singleton_pattern_requirements.md** - Enforce singleton pattern (MEDIUM)
6. **21_consolidate_duplicate_risk_monitors.md** - Remove duplicate risk monitor (MEDIUM)
7. **10_tight_loop_architecture_requirements.md** - Implement tight loop architecture (MEDIUM)
8. **25_fix_reference_based_architecture_gaps.md** - Fix reference-based architecture (MEDIUM)
9. **26_fix_component_data_flow_architecture.md** - Fix component data flow (MEDIUM)

### LOW Priority Tasks (Can Defer)
10. **27_complete_frontend_implementation.md** - Complete frontend implementation (LOW)

### Legacy Tasks (Review and Update)
11. **01_docs_codebase_reconciliation.md** - Reconcile docs, tasks, and codebase (COMPLETED)
12. **02_critical_pure_lending_yield_fix.md** - Fix 1166% APY issue (REVIEW)
13. **03_scripts_directory_quality_gates.md** - Fix scripts directory quality gates (REVIEW)
14. **04_btc_basis_strategy_v1_fix.md** - Fix BTC basis strategy (REVIEW)
15. **05_comprehensive_quality_gates.md** - Run comprehensive quality gates (REVIEW)

## EXECUTION INSTRUCTIONS
1) **START WITH HIGH PRIORITY TASKS** - Focus on tasks 1-3 (HIGH priority) first
2) Read each task file completely before starting
3) Reference `docs/` and `docs/specs/` as needed for detailed specifications
4) Reference `TASK_DOCS_CONFLICT_ANALYSIS_REPORT.md` for violation details
5) Reference `docs/DEVIATIONS_AND_CORRECTIONS.md` for current architectural violations
6) Execute each task in priority order (HIGH → MEDIUM → LOW)
7) Do not wait for confirmation between tasks
8) Report progress after each task completion
9) **MANDATORY**: Run quality gate validation before moving to next task
10) Continue to next task immediately after success criteria met AND quality gates pass

## ARCHITECTURAL VIOLATION PRIORITIES
- **HIGH**: Async/await violations, Strategy manager refactor, Generic vs mode-specific
- **MEDIUM**: Fail-fast config, Singleton pattern, Duplicate files, Tight loop, Reference-based, Data flow
- **LOW**: Frontend implementation

## CRITICAL ARCHITECTURE RULES
- ❌ NEVER use hardcoded values to fix issues (including config values)
- ✅ ALWAYS use data provider for external data
- ✅ ALWAYS load configuration from YAML files
- ✅ ALWAYS validate configuration through Pydantic models
- ✅ MAINTAIN tight loop architecture (position → exposure → risk → P&L)
- ✅ MAINTAIN component chain architecture
- ✅ ADDRESS root causes, not symptoms
- ✅ USE dynamic data, not static values
- ✅ FOLLOW YAML-based config structure (modes/venues/scenarios)
- ✅ MAINTAIN state across runs (no reset)
- ✅ HANDLE backtest vs live mode differences properly
- ✅ ENSURE first runtime loop performs required actions (backtest mode)
- ✅ VALIDATE all required clients for live trading mode
- ✅ ENSURE client requirements determined by config YAML files
- ✅ USE SINGLE instance of each component across entire run
- ✅ SHARE the SAME config instance across all components
- ✅ SHARE the SAME data provider instance across all components
- ✅ ENSURE synchronized data flows between all components
- ✅ MAKE P&L monitor mode-agnostic for both backtest and live modes
- ✅ CENTRALIZE utility methods for liquidity index, market prices, and conversions
- ✅ USE shared utility methods across all components that need them
- ✅ ACCESS global data states using current event loop timestamp
- ✅ DESIGN components to be naturally clean without needing state clearing
- ✅ FIX root causes instead of using "clean state" hacks
- ✅ ENSURE components are properly initialized with correct state from the start
- ✅ MAKE generic components mode-agnostic (position monitor, P&L attribution, exposure monitor)
- ✅ USE config parameters instead of strategy mode logic (share_class, asset, lst_type, hedge_allocation)
- ✅ KEEP strategy manager and data subscriptions strategy mode specific by nature
- ✅ IMPLEMENT venue-based execution architecture with action type to venue mapping
- ✅ SUPPORT live/testnet/simulation modes for all venue clients
- ✅ USE environment variables to determine venue client modes
- ✅ CONFIGURE required vs optional venues per strategy mode

## PROJECT CONTEXT
- Repository: DeFi yield optimization platform
- Documentation: 42 markdown files in docs/, 13 component specs in docs/specs/
- Backend: 79 Python files in backend/src/basis_strategy_v1/
- Quality Gates: 14 scripts in scripts/ directory
- Current Status: 8/24 quality gates passing (33.3%)

## SUCCESS CRITERIA

### Primary Success Criteria (HIGH Priority)
- [ ] All async/await violations fixed (ADR-006 compliance)
- [ ] Strategy manager refactored with inheritance-based architecture
- [ ] Generic vs mode-specific violations resolved with config-driven parameters

### Secondary Success Criteria (MEDIUM Priority)
- [ ] Fail-fast configuration implemented (no .get() with defaults)
- [ ] Singleton pattern enforced for all 11 components
- [ ] Duplicate risk monitor file removed
- [ ] Tight loop architecture properly implemented
- [ ] Centralized utility manager created
- [ ] Reference-based architecture gaps fixed
- [ ] Component data flow architecture updated

### Tertiary Success Criteria (LOW Priority)
- [ ] Frontend implementation completed
- [ ] All task files updated with correct documentation references
- [ ] No duplicate content across task files (DRY compliance)
- [ ] All references validated and working

## TIMEOUT HANDLING
- 10-minute timeout per command
- If hangs, kill and retry up to 3 times
- Restart backend if needed: ./platform.sh stop-local && ./platform.sh backtest

## ERROR RECOVERY
If you encounter any error:
1) Log the exact error message
2) Check the relevant log files
3) Attempt to fix the error
4) Retry the operation
5) If still failing after 3 attempts, document the issue and continue with next step
6) Do not give up or stop the entire task

## PROGRESS VALIDATION
After each task, validate progress:
1) What was accomplished
2) Current status vs target
3) What needs to be done next
4) Any blockers encountered
5) Estimated completion time
6) Do not proceed without this validation

DO NOT STOP until all tasks are completed. Report progress after each task.
