# MASTER TASK SEQUENCE FOR BACKGROUND AGENTS

## OVERVIEW
This is the complete sequence of tasks to execute based on the 6-day implementation roadmap. Execute these tasks in order by day and priority, starting with foundational infrastructure and building up to complete end-to-end functionality.

**Reference**: `TASK_DOCS_CONFLICT_ANALYSIS_REPORT.md` - Updated conflict analysis (October 10, 2025)  
**Reference**: `docs/DEVIATIONS_AND_CORRECTIONS.md` - Current architectural violations  
**Reference**: `IMPLEMENTATION_TIMELINE.md` - Detailed 6-day roadmap

## 6-DAY IMPLEMENTATION ROADMAP

### Day 1: Foundation - Environment, Config, and Data Loading (8 hours)
1. **01_environment_file_switching.md** - Environment file switching & fail-fast (4 hours)
2. **02_config_loading_validation.md** - Full config loading & validation (4 hours)
3. **03_data_loading_quality_gate.md** - Data loading quality gate (4 hours)

### Day 2: Core Architecture Refactors (12-16 hours)
4. **07_fix_async_await_violations.md** - Fix async/await violations (6-8 hours)
5. **10_reference_based_architecture.md** - Fix reference-based architecture (6-8 hours)
6. **11_singleton_pattern.md** - Enforce singleton pattern (6-8 hours)
7. **06_strategy_manager_refactor.md** - Strategy manager refactor (6-8 hours)
8. **08_mode_agnostic_architecture.md** - Mode-agnostic architecture (6-8 hours)
9. **09_fail_fast_configuration.md** - Fail-fast configuration (6-8 hours)

### Day 3: Component Integration & Quality Gates (12-16 hours)
10. **12_tight_loop_architecture.md** - Tight loop architecture (6-8 hours)
11. **13_consolidate_duplicate_risk_monitors.md** - Consolidate duplicate risk monitors (6-8 hours)
12. **14_component_data_flow_architecture.md** - Component data flow architecture (6-8 hours)
13. **04_complete_api_endpoints.md** - Complete API endpoints (6-8 hours)
14. **05_health_logging_structure.md** - Health checks & structured logging (6-8 hours)

### Day 4: Strategy Mode Validation - Simple to Complex (12-16 hours)
15. **15_pure_lending_quality_gates.md** - Pure lending E2E quality gates (4-5 hours)
16. **16_btc_basis_quality_gates.md** - BTC basis E2E quality gates (4-5 hours)
17. **17_eth_basis_quality_gates.md** - ETH basis E2E quality gates (4-5 hours)

### Day 5: Complex Modes & Component Unit Tests (12-16 hours)
18. **18_usdt_market_neutral_quality_gates.md** - USDT market neutral E2E quality gates (4-5 hours)
19. **19_position_monitor_unit_tests.md** - Position monitor unit tests (8-10 hours)
20. **20_exposure_monitor_unit_tests.md** - Exposure monitor unit tests (8-10 hours)
21. **21_risk_monitor_unit_tests.md** - Risk monitor unit tests (8-10 hours)
22. **22_strategy_manager_unit_tests.md** - Strategy manager unit tests (8-10 hours)
23. **23_pnl_calculator_unit_tests.md** - P&L calculator unit tests (8-10 hours)

### Day 6: Frontend & Live Mode Completion (12-16 hours)
24. **24_frontend_implementation.md** - Frontend implementation (6-8 hours)
25. **25_live_mode_quality_gates.md** - Live mode quality gates (6-8 hours)
26. **26_comprehensive_quality_gates.md** - Comprehensive quality gates (6-8 hours)

### Day 7: Frontend Components & Authentication (12-16 hours)
27. **27_authentication_system.md** - Authentication system implementation (4-6 hours)
28. **28_live_trading_ui.md** - Live trading UI implementation (6-8 hours)
29. **29_shared_utilities.md** - Shared utilities implementation (4-6 hours)

## EXECUTION INSTRUCTIONS
1) **FOLLOW 6-DAY TIMELINE** - Execute tasks in day order (Day 1 → Day 6)
2) **PARALLELIZATION OPPORTUNITIES** - Use multiple background agents where specified
3) Read each task file completely before starting
4) Reference `docs/` and `docs/specs/` as needed for detailed specifications
5) Reference `TASK_DOCS_CONFLICT_ANALYSIS_REPORT.md` for violation details
6) Reference `docs/DEVIATIONS_AND_CORRECTIONS.md` for current architectural violations
7) Reference `IMPLEMENTATION_TIMELINE.md` for detailed roadmap
8) Execute each task in day order with parallelization where possible
9) Do not wait for confirmation between tasks
10) Report progress after each task completion
11) **MANDATORY**: Run quality gate validation before moving to next task
12) Continue to next task immediately after success criteria met AND quality gates pass

## PARALLELIZATION STRATEGY

### High Parallelization Opportunities (Multiple Agents)
- **Day 2, Tasks 7-9**: Strategy manager refactor || Mode-agnostic + Fail-fast config
- **Day 3, Tasks 13-14**: API endpoints || Health/logging
- **Day 5, Tasks 19-23**: All 5 component unit test tasks in parallel
- **Day 6, Tasks 24-25**: Frontend implementation || Live mode

### Sequential Required (File Conflicts)
- **Day 1**: All sequential (config/env foundation)
- **Day 2, Tasks 4-6**: Touch overlapping component files
- **Day 4**: All sequential (iterative validation per mode)

### Estimated Agent-Hours
- **Total Sequential Work**: ~40 hours
- **Total Parallel Work**: ~20 hours
- **With 3-5 Background Agents**: Can complete in **6 calendar days**

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

### Day 1 ✅
- [ ] Environment switching working (dev/staging/prod)
- [ ] Config loading with full validation working
- [ ] All data files validated for all modes

### Day 2 ✅
- [ ] All async/await violations fixed
- [ ] Reference-based architecture implemented
- [ ] Strategy manager refactored with inheritance
- [ ] Mode-agnostic components implemented

### Day 3 ✅
- [ ] Tight loop architecture implemented
- [ ] Duplicate files removed
- [ ] All API endpoints complete
- [ ] Health checks and logging structured

### Day 4 ✅
- [ ] Pure lending E2E passing (3-8% APY)
- [ ] BTC basis E2E passing
- [ ] ETH basis E2E passing

### Day 5 ✅
- [ ] USDT market neutral E2E passing
- [ ] All component unit tests passing
- [ ] 80% unit test coverage achieved

### Day 6 ✅
- [ ] Frontend results components complete
- [ ] Live mode framework complete
- [ ] 20/24 quality gates passing (83%)
- [ ] System ready for staging deployment

### Day 7 ✅
- [ ] Authentication system complete (username: admin)
- [ ] Live trading UI complete
- [ ] Shared utilities and API client complete
- [ ] Full frontend functionality ready

## OVERALL SUCCESS CRITERIA
- [ ] All 29 tasks completed successfully
- [ ] All quality gates passing
- [ ] All tests passing with 80% coverage
- [ ] System ready for production deployment
- [ ] Complete end-to-end functionality validated

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
