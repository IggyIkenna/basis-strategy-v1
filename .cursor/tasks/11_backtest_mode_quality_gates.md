# BACKTEST MODE QUALITY GATES

## OVERVIEW
Specific quality gates for backtest mode to ensure proper initialization and execution.

## CRITICAL BACKTEST MODE VALIDATIONS

### 1. Position Monitor Initialization
- **Strategy mode capital**: Position monitor must be initialized with proper capital based on strategy mode
- **Initial token allocation**: Must have initial capital in at least one token
- **No empty state**: Position monitor cannot start in empty state

### 2. First Runtime Loop Validation
- **Required actions**: Must perform at least one of:
  - Wallet transfers
  - Trades
  - Smart contract actions
- **No "do nothing"**: Strategy cannot be in "do nothing" state
- **Position setup**: Must set up desired positions on first runtime loop
- **Action execution**: Must execute actions to get into desired position

### 3. Tight Loop Architecture
- **Sequential execution**: position_monitor → exposure_monitor → risk_monitor → pnl_monitor
- **State persistence**: All components maintain state across timesteps
- **No reset**: No component resets state between iterations
- **Proper triggering**: Each component triggers the next in sequence

### 4. State Management
- **Cross-run persistence**: State must persist across all timesteps
- **Position tracking**: Position monitor maintains position state
- **Risk tracking**: Risk monitor maintains risk assessments
- **P&L tracking**: P&L monitor maintains P&L calculations

## QUALITY GATE IMPLEMENTATION

### Validation Script
```python
def validate_backtest_mode():
    """Validate backtest mode specific requirements."""
    
    # 1. Check position monitor initialization
    assert position_monitor.has_initial_capital(), "Position monitor must have initial capital"
    
    # 2. Check first runtime loop actions
    first_loop_actions = get_first_loop_actions()
    assert len(first_loop_actions) > 0, "First runtime loop must perform actions"
    
    # 3. Check tight loop architecture
    assert tight_loop_executes_sequentially(), "Tight loop must execute sequentially"
    
    # 4. Check state persistence
    assert state_persists_across_timesteps(), "State must persist across timesteps"
    
    return True
```

### Integration Points
- **Quality gate scripts**: Add to existing quality gate scripts
- **Backtest mode only**: Only run these validations in backtest mode
- **First loop check**: Run after first runtime loop execution
- **State persistence check**: Run after multiple timesteps

## ERROR CONDITIONS

### Position Monitor Issues
- **Empty initialization**: Position monitor starts with no capital
- **Wrong strategy mode**: Capital allocation doesn't match strategy mode
- **Missing tokens**: No initial capital in any token

### First Runtime Loop Issues
- **No actions**: First loop performs no actions
- **"Do nothing" state**: Strategy is in "do nothing" state
- **No position setup**: Doesn't set up desired positions

### Tight Loop Issues
- **Skipped components**: Components skipped in tight loop
- **State reset**: Components reset state between iterations
- **Improper triggering**: Components don't trigger next in sequence

### State Management Issues
- **State loss**: State lost between timesteps
- **Position loss**: Position data lost between iterations
- **Risk loss**: Risk assessments lost between iterations

## IMPLEMENTATION REQUIREMENTS

### Quality Gate Scripts
- **Add validation**: Add backtest mode validation to quality gate scripts
- **Backtest only**: Only run in backtest mode
- **First loop check**: Check after first runtime loop
- **State persistence check**: Check after multiple timesteps

### Error Handling
- **Fail fast**: Fail fast on backtest mode validation errors
- **Clear messages**: Provide clear error messages for validation failures
- **Actionable feedback**: Provide actionable feedback for fixing issues

### Testing
- **Unit tests**: Test backtest mode validation functions
- **Integration tests**: Test integration with quality gate scripts
- **End-to-end tests**: Test complete backtest mode validation

## VALIDATION CHECKLIST

### Position Monitor
- [ ] Initialized with proper capital based on strategy mode
- [ ] Has initial capital in at least one token
- [ ] Not in empty state
- [ ] Capital allocation matches strategy mode

### First Runtime Loop
- [ ] Performs required actions (wallet transfer, trade, or smart contract)
- [ ] Not in "do nothing" state
- [ ] Sets up desired positions
- [ ] Executes actions to get into desired position

### Tight Loop Architecture
- [ ] Executes sequentially (position → exposure → risk → P&L)
- [ ] All components maintain state
- [ ] No state reset between iterations
- [ ] Proper component triggering

### State Management
- [ ] State persists across all timesteps
- [ ] Position data persists
- [ ] Risk assessments persist
- [ ] P&L calculations persist

## INTEGRATION WITH EXISTING QUALITY GATES

### Scripts to Update
- **test_pure_lending_quality_gates.py**: Add backtest mode validation
- **test_btc_basis_quality_gates.py**: Add backtest mode validation
- **test_tight_loop_quality_gates.py**: Add backtest mode validation
- **run_quality_gates.py**: Add backtest mode validation

### Validation Points
- **After initialization**: Check position monitor initialization
- **After first loop**: Check first runtime loop actions
- **After multiple timesteps**: Check state persistence
- **End of backtest**: Check overall backtest mode compliance

## SUCCESS CRITERIA
- [ ] All backtest mode validations pass
- [ ] Position monitor properly initialized
- [ ] First runtime loop performs required actions
- [ ] Tight loop architecture maintained
- [ ] State persists across all timesteps
- [ ] Quality gate scripts updated with backtest mode validation

