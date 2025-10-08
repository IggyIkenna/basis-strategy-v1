# MASTER TASK SEQUENCE FOR BACKGROUND AGENTS

## OVERVIEW
This is the complete sequence of tasks to execute from REMAINING_TASKS.md. Execute these tasks in order, one after another, without stopping between tasks.

## TASK SEQUENCE
0. **00_master_task_sequence.md** - This master task sequence (START HERE)
1. **01_docs_codebase_reconciliation.md** - Reconcile docs, tasks, and codebase (CRITICAL)
2. **02_critical_pure_lending_yield_fix.md** - Fix 1166% APY issue (CRITICAL)
3. **03_scripts_directory_quality_gates.md** - Fix 5/14 scripts passing (HIGH)
4. **04_btc_basis_strategy_v1_fix.md** - Fix 8/10 quality gates (HIGH)
5. **05_comprehensive_quality_gates.md** - Run full suite (MEDIUM)
6. **21_consolidate_duplicate_risk_monitors.md** - Remove duplicate risk_monitor.py files (CRITICAL)

## EXECUTION INSTRUCTIONS
1) Read .cursor/tasks/01_docs_codebase_reconciliation.md for comprehensive reconciliation
2) Read .cursor/tasks/06_architecture_compliance_rules.md for architecture requirements
3) Read .cursor/tasks/08_configuration_architecture_guide.md for configuration standards
4) Read .cursor/tasks/09_backtest_vs_live_mode_architecture.md for mode-specific requirements
5) Read .cursor/tasks/10_tight_loop_architecture_requirements.md for tight loop requirements
6) Read .cursor/tasks/11_backtest_mode_quality_gates.md for backtest mode validation
7) Read .cursor/tasks/12_live_trading_quality_gates.md for live trading validation
8) Read .cursor/tasks/13_singleton_pattern_requirements.md for singleton pattern requirements
9) Read .cursor/tasks/14_mode_agnostic_architecture_requirements.md for mode-agnostic requirements
10) Read .cursor/tasks/16_clean_component_architecture_requirements.md for clean component requirements
11) Read .cursor/tasks/17_quality_gate_validation_requirements.md for quality gate validation requirements
12) Read .cursor/tasks/18_generic_vs_mode_specific_architecture.md for generic vs mode-specific requirements
13) Read .cursor/tasks/19_venue_based_execution_architecture.md for venue-based execution requirements
14) Read .cursor/tasks/21_consolidate_duplicate_risk_monitors.md for duplicate file consolidation
15) Read .cursor/rules.json for coding standards and validation rules
16) Read each task file completely before starting
17) Reference docs/ and docs/specs/ as needed for detailed specifications
18) Execute each task in sequence
19) Do not wait for confirmation between tasks
20) Report progress after each task completion
21) **MANDATORY**: Run quality gate validation before moving to next task
22) Continue to next task immediately after success criteria met AND quality gates pass

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
- Docs, tasks, and codebase fully reconciled and consistent
- Pure lending APY: 3-8% (not 1166%)
- Scripts directory: 10/14 passing (70%+)
- BTC basis strategy: 10/10 passing (100%)
- Overall quality gates: 15/24 passing (60%+)

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
