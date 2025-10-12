# MASTER TASK SEQUENCE FOR BACKGROUND AGENTS

## OVERVIEW
This is the complete sequence of tasks to execute based on the 12-day implementation roadmap. Execute these tasks in order by day and priority, starting with foundational infrastructure and building up to complete end-to-end functionality with 80% test coverage.

**Reference**: `docs/IMPLEMENTATION_GAP_REPORT.md` - Implementation gap analysis (October 11, 2025)  
**Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Canonical architectural principles  
**Reference**: `docs/COMPONENT_SPECS_INDEX.md` - All 20 component specifications  
**Reference**: `docs/QUALITY_GATES.md` - Quality gate validation requirements  
**Reference**: `docs/specs/` - Detailed component implementation guides  
**Reference**: `scripts/test_implementation_gap_quality_gates.py` - Implementation gap detection

## 12-DAY IMPLEMENTATION ROADMAP

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
9. **09_fail_fast_19_CONFIGURATION.md** - Fail-fast configuration (6-8 hours)

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

### Day 5: Complex Modes & Component Alignment (12-16 hours)
18. **18_usdt_market_neutral_quality_gates.md** - USDT market neutral E2E quality gates (4-5 hours)
19. **19_position_monitor_unit_tests.md** - Position monitor alignment & unit tests (8-10 hours)
20. **20_exposure_monitor_unit_tests.md** - Exposure monitor alignment & unit tests (8-10 hours)
21. **21_risk_monitor_unit_tests.md** - Risk monitor alignment & unit tests (8-10 hours)
22. **22_strategy_manager_unit_tests.md** - Strategy manager unit tests (8-10 hours)
23. **23_pnl_calculator_unit_tests.md** - P&L calculator alignment & unit tests (8-10 hours)
32. **32_event_logger_unit_tests.md** - Event logger component testing (4-6 hours)
33. **33_results_store_unit_tests.md** - Results store component testing (4-6 hours)
34. **34_health_system_unit_tests.md** - Health monitoring testing (4-6 hours)
35. **35_api_endpoints_unit_tests.md** - API layer testing (4-6 hours)

### Day 6: Execution Infrastructure & Service Validation (12-16 hours)
24. **30_execution_components_implementation.md** - Execution components implementation (8-10 hours)
25. **26_comprehensive_quality_gates.md** - Service layer & engine validation (6-8 hours)
26. **25_live_mode_quality_gates.md** - Live mode quality gates (6-8 hours)
36. **36_data_flow_position_to_exposure.md** - Position→Exposure workflow (4-6 hours)
37. **37_data_flow_exposure_to_risk.md** - Exposure→Risk workflow (4-6 hours)
38. **38_data_flow_risk_to_strategy.md** - Risk→Strategy workflow (4-6 hours)
39. **39_data_flow_strategy_to_execution.md** - Strategy→Execution workflow (4-6 hours)
40. **40_tight_loop_reconciliation.md** - Tight loop architecture validation (4-6 hours)

### Day 7: Infrastructure & Frontend Completion (12-16 hours)
27. **31_infrastructure_components_completion.md** - Infrastructure components completion (6-8 hours)
28. **24_frontend_implementation.md** - Frontend implementation completion (6-8 hours)
29. **27_authentication_system.md** - Authentication system implementation (4-6 hours)
30. **28_live_trading_ui.md** - Live trading UI implementation (6-8 hours)
41. **41_eth_staking_only_e2e.md** - ETH staking only strategy (4-6 hours)
42. **42_eth_leveraged_staking_e2e.md** - ETH leveraged staking strategy (4-6 hours)
43. **43_usdt_market_neutral_no_leverage_e2e.md** - USDT market neutral without leverage (4-6 hours)

### Day 8: API Routes Unit Tests (12-16 hours)
44. **44_auth_routes_unit_tests.md** - Auth routes testing (4-6 hours)
45. **45_backtest_routes_unit_tests.md** - Backtest API routes (4-6 hours)
46. **46_capital_routes_unit_tests.md** - Capital management routes (4-6 hours)
47. **47_charts_routes_unit_tests.md** - Chart generation routes (4-6 hours)
48. **48_config_routes_unit_tests.md** - Configuration API routes (4-6 hours)
49. **49_health_routes_unit_tests.md** - Health check routes (4-6 hours)
50. **50_live_trading_routes_unit_tests.md** - Live trading routes (4-6 hours)
51. **51_results_routes_unit_tests.md** - Results retrieval routes (4-6 hours)
52. **52_strategies_routes_unit_tests.md** - Strategy listing routes (4-6 hours)

### Day 9: Core Strategies Unit Tests (12-16 hours)
53. **53_btc_basis_strategy_unit_tests.md** - BTC basis strategy testing (4-6 hours)
54. **54_eth_basis_strategy_unit_tests.md** - ETH basis strategy testing (4-6 hours)
55. **55_eth_leveraged_strategy_unit_tests.md** - ETH leveraged strategy testing (4-6 hours)
56. **56_eth_staking_only_strategy_unit_tests.md** - ETH staking only strategy testing (4-6 hours)
57. **57_pure_lending_strategy_unit_tests.md** - Pure lending strategy testing (4-6 hours)
58. **58_strategy_factory_unit_tests.md** - Strategy factory testing (4-6 hours)
59. **59_usdt_market_neutral_strategy_unit_tests.md** - USDT market neutral strategy testing (4-6 hours)
60. **60_usdt_market_neutral_no_leverage_strategy_unit_tests.md** - USDT market neutral no leverage strategy testing (4-6 hours)
61. **61_ml_directional_strategy_unit_tests.md** - ML directional strategy testing (4-6 hours)

### Day 10: Infrastructure Data Provider Unit Tests (12-16 hours)
62. **62_btc_basis_data_provider_unit_tests.md** - BTC basis data provider testing (4-6 hours)
63. **63_data_provider_factory_unit_tests.md** - Data provider factory testing (4-6 hours)
64. **64_config_driven_historical_data_provider_unit_tests.md** - Config driven historical data provider testing (4-6 hours)
65. **65_data_validator_unit_tests.md** - Data validation testing (4-6 hours)
66. **66_eth_basis_data_provider_unit_tests.md** - ETH basis data provider testing (4-6 hours)
67. **67_eth_leveraged_data_provider_unit_tests.md** - ETH leveraged data provider testing (4-6 hours)
68. **68_eth_staking_only_data_provider_unit_tests.md** - ETH staking only data provider testing (4-6 hours)
69. **69_historical_data_provider_unit_tests.md** - Historical data provider testing (4-6 hours)
70. **70_live_data_provider_unit_tests.md** - Live data provider testing (4-6 hours)
71. **71_ml_directional_data_provider_unit_tests.md** - ML directional data provider testing (4-6 hours)
72. **72_pure_lending_data_provider_unit_tests.md** - Pure lending data provider testing (4-6 hours)
73. **73_usdt_market_neutral_data_provider_unit_tests.md** - USDT market neutral data provider testing (4-6 hours)
74. **74_usdt_market_neutral_no_leverage_data_provider_unit_tests.md** - USDT market neutral no leverage data provider testing (4-6 hours)

### Day 11: Core Math & Execution Interfaces Unit Tests (12-16 hours)
75. **75_health_calculator_unit_tests.md** - Health calculator testing (4-6 hours)
76. **76_ltv_calculator_unit_tests.md** - LTV calculator testing (4-6 hours)
77. **77_margin_calculator_unit_tests.md** - Margin calculator testing (4-6 hours)
78. **78_metrics_calculator_unit_tests.md** - Metrics calculator testing (4-6 hours)
79. **79_cex_execution_interface_unit_tests.md** - CEX execution interface testing (4-6 hours)
80. **80_onchain_execution_interface_unit_tests.md** - On-chain execution interface testing (4-6 hours)
81. **81_transfer_execution_interface_unit_tests.md** - Transfer execution interface testing (4-6 hours)

### Day 12: Zero Coverage Components Unit Tests (12-16 hours)
82. **82_venue_adapters_unit_tests.md** - Venue adapters testing (4-6 hours)
83. **83_backtest_service_unit_tests.md** - Backtest service testing (4-6 hours)
84. **84_live_service_unit_tests.md** - Live service testing (4-6 hours)
85. **85_component_health_unit_tests.md** - Component health testing (4-6 hours)
86. **86_unified_health_manager_unit_tests.md** - Unified health manager testing (4-6 hours)
87. **87_utility_manager_unit_tests.md** - Utility manager testing (4-6 hours)
88. **88_error_code_registry_unit_tests.md** - Error code registry testing (4-6 hours)
89. **89_execution_instructions_unit_tests.md** - Execution instructions testing (4-6 hours)
90. **90_reconciliation_component_unit_tests.md** - Reconciliation component testing (4-6 hours)
91. **91_api_call_queue_unit_tests.md** - API call queue testing (4-6 hours)
92. **92_chart_storage_visualization_unit_tests.md** - Chart storage and visualization testing (4-6 hours)

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
- **Day 5, Tasks 19-23**: All 5 component alignment & unit test tasks in parallel
- **Day 6, Tasks 25-26**: Service validation || Live mode quality gates
- **Day 7, Tasks 28-30**: Frontend implementation || Authentication || Live trading UI

### Sequential Required (File Conflicts)
- **Day 1**: All sequential (config/env foundation)
- **Day 2, Tasks 4-6**: Touch overlapping component files
- **Day 4**: All sequential (iterative validation per mode)

### Estimated Agent-Hours
- **Total Sequential Work**: ~45 hours
- **Total Parallel Work**: ~25 hours
- **With 3-5 Background Agents**: Can complete in **7 calendar days**

## IMPLEMENTATION GAP PRIORITIES
- **HIGH**: Component alignment with specs, Execution infrastructure, Service validation
- **MEDIUM**: Infrastructure completion, Quality gate implementation, Test coverage
- **LOW**: Frontend completion, Authentication system

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
- [ ] All monitoring components aligned with specs
- [ ] 80% unit test coverage achieved for core components

### Day 6 ✅
- [ ] Execution infrastructure complete
- [ ] Service layer validation complete
- [ ] Live mode quality gates passing
- [ ] 18/24 quality gates passing (75%)

### Day 7 ✅
- [ ] Infrastructure components complete
- [ ] Frontend implementation complete
- [ ] Authentication system complete (username: admin)
- [ ] Live trading UI complete
- [ ] 20/24 quality gates passing (83%)
- [ ] System ready for staging deployment

## OVERALL SUCCESS CRITERIA
- [ ] All 92 tasks completed successfully
- [ ] All 20 component implementation gaps addressed
- [ ] Quality gates improved from 12/24 to 20/24+ passing
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
