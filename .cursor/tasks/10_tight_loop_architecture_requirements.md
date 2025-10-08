# TIGHT LOOP ARCHITECTURE REQUIREMENTS

## OVERVIEW
The tight loop architecture is the core of the system, ensuring proper data flow and state management across all components.

## MANDATORY SEQUENTIAL COMPONENT CHAIN
**MUST execute in chain sequential triggers without exception**:

```
position_monitor → exposure_monitor → risk_monitor → pnl_monitor
```

## EXECUTION FLOW PATTERNS

### Pattern 1: Strategy Manager Path
```
position_monitor → exposure_monitor → risk_monitor → pnl_monitor → strategy → execution_managers
```

### Pattern 2: Tight Loop Path (Bypass Strategy)
```
position_monitor → exposure_monitor → risk_monitor → pnl_monitor → execution_managers
```

**When to use Pattern 2**:
- Strategy has given sequence of execution instructions
- Example: Wallet transfer followed by several trade blocks
- Iteration: Update position monitor and repeat sequence until completion

## POSITION MONITOR INTEGRATION

### Backtest Mode
- **Execution components** call position monitor to **update it/write to it**
- **Simulated data** used for updates
- **Direct state modification** by execution interfaces

### Live Mode
- **Execution components** call position monitor to **trigger update/refresh**
- **External interfaces** provide data to position monitor
- **Real-time data** from APIs and blockchain

## ATOMIC TRANSACTIONS

### Special Handling
- **Blockchain chain**: Essential one blockchain chain of transactions
- **All or nothing**: Happen at same time or all fail
- **Bypass iteration**: Skip normal iteration for atomic transactions
- **Complete or rollback**: Entire transaction sequence must complete or fail

## STATE PERSISTENCE REQUIREMENTS

### Critical Requirements
- **No reset**: All components must maintain state across runs
- **Persistent state**: State must survive between iterations
- **Cross-run continuity**: Position, risk, and P&L data must persist
- **Component state**: Each component maintains its own state

### State Management
- **Position monitor**: Maintains position state across all timesteps
- **Exposure monitor**: Maintains exposure calculations
- **Risk monitor**: Maintains risk assessments
- **P&L monitor**: Maintains P&L calculations and history

## ERROR HANDLING IN TIGHT LOOP

### Backtest Mode
- **Fail fast**: Fail fast and pass failure down codebase
- **Immediate feedback**: Errors should be immediately visible
- **Stop execution**: Stop tight loop on critical errors

### Live Mode
- **Retry logic**: Wait 5s, retry with exponential backoff
- **Max attempts**: Maximum 3 attempts
- **Error logging**: Log error and pass failure down after max attempts
- **Continue execution**: Continue tight loop after non-critical errors

## POSITION AND RISK TRACKING

### Always Required
- **Position record**: Always have record of current positions
- **Risk record**: Always have record of current risk (in all dimensions, not just raw)
- **Risk impact**: Calculate risk impact of position update BEFORE taking further action
- **Applies to both**: Backtest and live modes

### Risk Dimensions
- **Raw positions**: Basic position amounts
- **Exposure calculations**: Risk exposure in various dimensions
- **Risk assessments**: Comprehensive risk analysis
- **P&L impact**: Profit and loss implications

## ITERATION LOGIC

### Normal Iteration
1. **Position update**: Update position monitor
2. **Exposure calculation**: Calculate new exposures
3. **Risk assessment**: Assess new risk levels
4. **P&L calculation**: Calculate P&L changes
5. **Strategy decision**: Determine next actions (if using strategy path)
6. **Execution**: Execute next actions
7. **Repeat**: Continue until completion

### Atomic Transaction Iteration
1. **Position update**: Update position monitor
2. **Exposure calculation**: Calculate new exposures
3. **Risk assessment**: Assess new risk levels
4. **P&L calculation**: Calculate P&L changes
5. **Atomic execution**: Execute entire atomic transaction sequence
6. **Complete or rollback**: Either complete all or rollback all
7. **Continue**: Continue with normal iteration

## COMPONENT RESPONSIBILITIES

### Position Monitor
- **State management**: Maintain position state across all timesteps
- **Update handling**: Handle updates from execution interfaces
- **Data persistence**: Persist position data across runs

### Exposure Monitor
- **Exposure calculation**: Calculate risk exposures
- **Trigger**: Triggered after position updates
- **State maintenance**: Maintain exposure state

### Risk Monitor
- **Risk assessment**: Assess risk levels
- **Trigger**: Triggered after exposure updates
- **State maintenance**: Maintain risk state

### P&L Monitor
- **P&L calculation**: Calculate profit and loss
- **Trigger**: Triggered after risk updates
- **State maintenance**: Maintain P&L state

## VALIDATION REQUIREMENTS

### Tight Loop Integrity
- [ ] Sequential component execution maintained
- [ ] No component skipped in chain
- [ ] State properly passed between components
- [ ] Error handling appropriate for mode

### State Persistence
- [ ] All components maintain state across runs
- [ ] No state reset between iterations
- [ ] Position data persists across timesteps
- [ ] Risk and P&L data persists

### Execution Flow
- [ ] Proper execution path selected (strategy vs tight loop)
- [ ] Atomic transactions handled correctly
- [ ] Position updates trigger tight loop
- [ ] Risk impact calculated before further actions

## IMPLEMENTATION STANDARDS

### Code Structure
- **Sequential execution**: Ensure components execute in proper sequence
- **State management**: Implement proper state management
- **Error handling**: Implement appropriate error handling
- **Mode awareness**: Handle backtest vs live mode differences

### Testing Requirements
- **Tight loop testing**: Test tight loop execution
- **State persistence**: Test state persistence across iterations
- **Error handling**: Test error handling in both modes
- **Atomic transactions**: Test atomic transaction handling

## QUALITY GATE INTEGRATION

### Backtest Mode
- **Tight loop execution**: Verify tight loop executes properly
- **State persistence**: Verify state persists across timesteps
- **Position updates**: Verify position updates trigger tight loop
- **Risk calculations**: Verify risk calculations are accurate

### Live Mode
- **Real-time execution**: Verify real-time execution works
- **API integration**: Verify external API integration
- **Error handling**: Verify retry logic and error handling
- **State persistence**: Verify state persists across runs

