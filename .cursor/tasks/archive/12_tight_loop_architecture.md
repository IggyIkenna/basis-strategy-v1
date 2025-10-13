# TIGHT LOOP ARCHITECTURE REQUIREMENTS

**Last Updated**: October 10, 2025  
**Status**: ✅ CRITICAL REDEFINITION - Complete architectural change

## OVERVIEW

The tight loop architecture has been completely redefined. The tight loop is now the execution reconciliation pattern that ensures position updates are verified before proceeding to the next instruction. This is a fundamental change from the previous monitoring cascade approach.

**Reference**: `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-001 Tight Loop Architecture Redefinition  
**Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 4 (Tight Loop Architecture)  
**Reference**: `docs/specs/01_POSITION_MONITOR.md` - Component specification  
**Reference**: `docs/specs/11_POSITION_UPDATE_HANDLER.md` - Component specification

## NEW TIGHT LOOP DEFINITION

**TIGHT LOOP** = Execution Reconciliation Pattern

```
execution sends instruction → position_monitor updates → verify reconciliation → next instruction
```

### Key Principles

- **Execution manager sends ONE instruction at a time**
- **Position monitor updates** (simulated in backtest, queried in live)
- **Execution manager verifies position matches expected state**
- **Move to next instruction ONLY after reconciliation**
- **Happens WITHIN the full loop for each execution instruction**
- **Ensures no race conditions via sequential execution**

## FULL LOOP PATTERN

**FULL LOOP** = Time-Based Workflow with Embedded Tight Loops

```
time trigger (60s) → strategy decision → [tight loop 1] → [tight loop 2] → ... → [tight loop N] → complete
```

Where each `[tight loop]` = execution → position_monitor → reconciliation

### Full Loop Characteristics

- **Runs every 60 seconds** (configurable)
- **Strategy manager generates execution instructions**
- **EACH instruction triggers a tight loop** (execution → position → reconciliation)
- **Tight loops happen WITHIN the full loop**
- **No concurrency** - sequential execution ensures no race conditions

## DEPRECATED MONITORING CASCADE

**OLD CONCEPT** (NO LONGER USED):

```
position_monitor → exposure_monitor → risk_monitor → pnl_monitor
```

### Why Deprecated

- **Nothing triggers this cascade anymore**
- **Exposure, risk, and pnl monitors may still exist as components**
- **But they are NOT called in a cascade after each position update**
- **They may be called independently for reporting/analytics purposes**
- **NOT part of the execution flow**

## TIGHT LOOP EXECUTION FLOW

### Single Instruction Flow

1. **Execution Manager** sends instruction to venue
2. **Position Monitor** updates (simulated in backtest, queried in live)
3. **Reconciliation Check** verifies position matches expected state
4. **Next Instruction** only after successful reconciliation

### Multiple Instructions Flow

```
Full Loop Start (60s trigger)
├── Strategy Decision
├── Instruction 1
│   ├── Tight Loop 1: execution → position → reconciliation
│   └── Wait for reconciliation
├── Instruction 2
│   ├── Tight Loop 2: execution → position → reconciliation
│   └── Wait for reconciliation
├── Instruction N
│   ├── Tight Loop N: execution → position → reconciliation
│   └── Wait for reconciliation
└── Full Loop Complete
```

## POSITION MONITOR INTEGRATION

### Backtest Mode
- **Execution components** call position monitor to **update it/write to it**
- **Simulated data** used for updates
- **Direct state modification** by execution interfaces
- **Stateful**: Cannot recover after restart

### Live Mode
- **Execution components** call position monitor to **trigger update/refresh**
- **External interfaces** provide data to position monitor
- **Real-time data** from APIs and blockchain
- **Stateless**: Can recover after restart by querying venue positions

## THREE-WAY VENUE INTERACTION

Each venue has three distinct interaction types:

### A. Market Data Feed (Public)
- **Backtest**: Historical CSV data loaded at startup
- **Live**: Real-time API connections with heartbeat tests
- **Component**: DataProvider
- **No credentials needed for backtest**

### B. Order Handling (Private, Credentials in Live Only)
- **Backtest**: Simulated execution, always returns success
- **Live**: Real order submission, await confirmation
- **Component**: Execution interfaces
- **Startup test**: Verify API connection (no actual order)

### C. Position Updates (Private, Credentials in Live Only)
- **Backtest**: Position monitor updates via simulation
- **Live**: Position monitor queries venue for actual positions
- **Component**: Position Monitor
- **Part of tight loop reconciliation**

## ATOMIC TRANSACTIONS

### Special Handling
- **Blockchain chain**: Essential one blockchain chain of transactions
- **All or nothing**: Happen at same time or all fail
- **Tight loop per transaction**: Each transaction in the chain gets its own tight loop
- **Complete or rollback**: Entire transaction sequence must complete or fail

### Atomic Transaction Flow
```
Atomic Transaction Start
├── Transaction 1
│   ├── Tight Loop 1: execution → position → reconciliation
│   └── Wait for reconciliation
├── Transaction 2
│   ├── Tight Loop 2: execution → position → reconciliation
│   └── Wait for reconciliation
├── Transaction N
│   ├── Tight Loop N: execution → position → reconciliation
│   └── Wait for reconciliation
└── Atomic Transaction Complete
```

## STATE PERSISTENCE REQUIREMENTS

### Critical Requirements
- **No reset**: All components must maintain state across runs
- **Persistent state**: State must survive between iterations
- **Cross-run continuity**: Position, risk, and P&L data must persist
- **Component state**: Each component maintains its own state

### State Management
- **Position monitor**: Maintains position state across all timesteps
- **Exposure monitor**: May exist independently for reporting
- **Risk monitor**: May exist independently for reporting
- **P&L monitor**: May exist independently for reporting

## ERROR HANDLING IN TIGHT LOOP

### Backtest Mode
- **Fail fast**: Fail fast and pass failure down codebase
- **Immediate feedback**: Errors should be immediately visible
- **Stop execution**: Stop tight loop on critical errors
- **Stateful**: Cannot recover after restart

### Live Mode
- **Retry logic**: Wait 5s, retry with exponential backoff
- **Max attempts**: Maximum 3 attempts
- **Error logging**: Log error and pass failure down after max attempts
- **Continue execution**: Continue tight loop after non-critical errors
- **Stateless**: Can recover after restart by querying venue positions

## RECONCILIATION REQUIREMENTS

### Position Reconciliation
- **Verify position matches expected state** after each instruction
- **Compare actual vs expected** position changes
- **Fail if mismatch** detected
- **Retry on failure** (live mode only)

### Reconciliation Failure Handling
- **Backtest**: Stop execution immediately
- **Live**: Retry with exponential backoff, then fail after max attempts
- **Health check**: Mark component as unhealthy on persistent failures

## COMPONENT RESPONSIBILITIES

### Execution Manager
- **Send instructions** to appropriate venues
- **Trigger tight loop** for each instruction
- **Verify reconciliation** before next instruction
- **Handle retry logic** in live mode

### Position Monitor
- **Update position state** based on instruction results
- **Provide position data** for reconciliation checks
- **Maintain position history** across runs
- **Handle venue queries** in live mode

### Strategy Manager
- **Generate execution instructions** based on market conditions
- **Coordinate with execution manager** for instruction delivery
- **Not directly involved** in tight loop execution

## VALIDATION REQUIREMENTS

### Tight Loop Integrity
- [ ] Sequential instruction execution maintained
- [ ] Position reconciliation verified after each instruction
- [ ] No instruction skipped in sequence
- [ ] Error handling appropriate for mode

### State Persistence
- [ ] All components maintain state across runs
- [ ] No state reset between iterations
- [ ] Position data persists across timesteps
- [ ] Component state survives restarts (live mode)

### Execution Flow
- [ ] Tight loop happens for each instruction
- [ ] Full loop contains multiple tight loops
- [ ] Atomic transactions handled correctly
- [ ] Position updates trigger reconciliation
- [ ] No monitoring cascade triggered

## IMPLEMENTATION STANDARDS

### Code Structure
- **Sequential execution**: Ensure instructions execute in proper sequence
- **Reconciliation checks**: Implement position verification after each instruction
- **Error handling**: Implement appropriate error handling for each mode
- **Mode awareness**: Handle backtest vs live mode differences

### Testing Requirements
- **Tight loop testing**: Test tight loop execution for each instruction
- **Reconciliation testing**: Test position reconciliation verification
- **State persistence**: Test state persistence across iterations
- **Error handling**: Test error handling in both modes
- **Atomic transactions**: Test atomic transaction handling

## QUALITY GATE INTEGRATION

### Backtest Mode
- [ ] Tight loop executes for each instruction
- [ ] Position reconciliation works correctly
- [ ] State persists across timesteps
- [ ] Position updates are accurate

### Live Mode
- [ ] Real-time execution works
- [ ] API integration functions
- [ ] Error handling and retry logic work
- [ ] State persistence across runs
- [ ] Position queries work correctly

## CONFIGURATION REQUIREMENTS

### Retry Logic Configuration
- **Max attempts**: Configurable per strategy mode
- **Retry delay**: Exponential backoff settings
- **Timeout settings**: Per venue and operation type
- **Circuit breaker**: Failure threshold settings

### Venue Configuration
- **Static venue data**: Order constraints, trading parameters
- **Environment credentials**: API keys, endpoints (dev/staging/prod)
- **Strategy subscriptions**: Which venues each strategy uses

## COMMUNICATION ARCHITECTURE

### Direct Function Calls
- **No Redis**: All communication via direct function calls
- **No pub/sub**: No message passing between components
- **Single-threaded**: No concurrency issues
- **Sequential execution**: Tight loop ensures proper ordering

### Component Integration
- **Execution Manager** → **Position Monitor**: Direct function calls
- **Position Monitor** → **Execution Manager**: Direct function calls
- **Strategy Manager** → **Execution Manager**: Direct function calls
- **No intermediate messaging**: All direct integration

---

**Source**: Canonical tight loop architecture requirements
**Canonical Reference**: This document defines the new tight loop architecture
**Last Updated**: January 6, 2025