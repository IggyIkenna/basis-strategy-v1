# BACKTEST VS LIVE MODE ARCHITECTURE GUIDE

## OVERVIEW
This system operates in two distinct modes: **backtest** and **live**, each with specific considerations and workflows that must be properly handled.

## STARTUP MODE DETERMINATION
All components must be aware of `startup_mode` which can be either:
- **backtest**: Simulated execution with historical data
- **live**: Real execution with external APIs (testnet or production)

## BACKTEST MODE CONSIDERATIONS

### 1. Position Monitor Initialization
- **CRITICAL**: Initialization of position_monitor data via strategy mode is key
- **Strategy mode** tells us what type of capital we are going to get initially for a token
- **Initial capital allocation** must be properly set based on strategy mode
- **No "do nothing" strategy mode** - every strategy must have initial capital and perform actions

### 2. First Runtime Loop
- **CRITICAL**: The first runtime loop is key for setting up desired positions
- **Always something to be done** - there's no "do nothing" strategy mode
- **Required actions on first loop**:
  - Wallet transfers
  - Trades
  - Smart contract actions
- **Bad state indicators**:
  - No initial capital in any token
  - No wallet transfer, trade, or smart contract actions on first runtime loop
- **Quality Gate Requirement**: Add validation to quality gate scripts (backtest mode only)

### 3. Results Generation
- **CSV files**: Generated for analysis
- **HTML plots**: Generated for visualization
- **API download**: Results available for download

### 4. Event Loop Trigger
- **Time-based**: Only trigger for full event loop is time
- **Data granularity**: Restricted to data granularity (currently 1 hour)
- **Simulated execution**: Actions simulated at same timestamp as event loop timestamp
- **Tight Loop Reconciliation**: Each execution instruction triggers tight loop verification

## LIVE MODE CONSIDERATIONS

### 1. Execution Manager
- **Real external APIs**: Dealing with testnet or production APIs
- **Client determination**: Must determine which client needed for which action
- **Environment awareness**: Testnet vs production based on environment
- **Simulation framework**: Use similar framework but call clients in simulation mode

### 2. Time and Execution
- **Time trigger**: Can still be main trigger for event loop
- **Tight Loop Reconciliation**: Each execution instruction triggers tight loop verification
- **Position Reconciliation**: Verifies position updates match execution expectations
- **Real delays**: Things take time to happen, record actual delays
- **Data sync**: In backtest, simulate things happening at same timestamp for easy data sync
- **Logging**: Log each action by each component for traceability

## SHARED ARCHITECTURE: TIGHT LOOP

### Sequential Component Chain (MANDATORY)
**MUST execute in chain sequential triggers without exception**:
1. **position_monitor** → 
2. **exposure_monitor** → 
3. **risk_monitor** → 
4. **pnl_monitor**

### Execution Flow Options
**Option 1: Strategy Manager Path**
- position_monitor → exposure_monitor → risk_monitor → pnl_monitor → **strategy** → execution_managers

**Option 2: Tight Loop Path (Bypass Strategy)**
- position_monitor → exposure_monitor → risk_monitor → pnl_monitor → **execution_managers**
- **When to use**: Strategy has given sequence of execution instructions
- **Example**: Wallet transfer followed by several trade blocks
- **Iteration**: Update position monitor and repeat sequence until completion

### Atomic Transactions
- **Blockchain chain**: Essential one blockchain chain of transactions
- **All or nothing**: Happen at same time or all fail
- **Special handling**: Bypass normal iteration for atomic transactions

### Position and Risk Tracking
- **Always have record**: Position and risk (in all dimensions, not just raw)
- **Risk impact**: Calculate risk impact of position update BEFORE taking further action
- **Applies to both**: Backtest and live modes

## EXECUTION INTERFACE DIFFERENCES

### Backtest Mode
- **Position updates**: Execution components call position monitor to update it/write to it
- **Simulated data**: Use simulated data and responses

### Live Mode
- **Position refresh**: Execution components call position monitor to trigger update/refresh
- **External interfaces**: Position monitor gets data from external interfaces
- **Real data**: Use real API responses and blockchain data

## STATE MANAGEMENT

### Critical Requirement
- **No reset**: All components must maintain state across runs
- **Persistent state**: State must survive between iterations
- **Cross-run continuity**: Position, risk, and P&L data must persist

## ERROR HANDLING

### Backtest Mode
- **Fail fast**: Fail fast and pass failure down codebase
- **Immediate feedback**: Errors should be immediately visible

### Live Mode
- **Retry logic**: Wait 5s, retry with exponential backoff
- **Max attempts**: Maximum 3 attempts
- **Error logging**: Log error and pass failure down after max attempts

## QUALITY GATE REQUIREMENTS

### Backtest Mode Validation
- **Initial capital**: Strategy must have initial capital in at least one token
- **First loop actions**: Must perform wallet transfer, trade, or smart contract actions
- **No "do nothing"**: Strategy cannot be in "do nothing" state
- **Position setup**: Must set up desired positions on first runtime loop

### Live Mode Validation
- **API connectivity**: External APIs must be accessible
- **Client initialization**: All required clients must be properly initialized
- **Environment configuration**: Testnet vs production must be correctly configured

## IMPLEMENTATION REQUIREMENTS

### Component Awareness
- **Startup mode**: All components must be aware of startup_mode
- **Mode-specific logic**: Implement mode-specific logic where needed
- **Shared interfaces**: Use shared interfaces where possible

### Data Flow
- **Tight loop**: Maintain tight loop architecture in both modes
- **Sequential execution**: Ensure sequential component execution
- **State persistence**: Maintain state across all iterations

### Testing
- **Both modes**: Test both backtest and live modes
- **Mode switching**: Test switching between modes
- **State continuity**: Test state persistence across mode switches

## VALIDATION CHECKLIST

### Backtest Mode
- [ ] Position monitor properly initialized with strategy mode capital
- [ ] First runtime loop performs required actions
- [ ] No "do nothing" strategy state
- [ ] Tight loop architecture maintained
- [ ] State persists across iterations
- [ ] Results generated (CSV and HTML)

### Live Mode
- [ ] External APIs properly configured
- [ ] Clients initialized for testnet/production
- [ ] Real delays properly recorded
- [ ] Position monitor refreshes from external interfaces
- [ ] Retry logic implemented for failures
- [ ] State persists across iterations

### Both Modes
- [ ] Tight loop architecture maintained
- [ ] Sequential component execution
- [ ] Position and risk tracking
- [ ] Error handling appropriate for mode
- [ ] State persistence across runs

