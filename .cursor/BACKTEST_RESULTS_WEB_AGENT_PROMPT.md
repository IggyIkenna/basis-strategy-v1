# Backtest Results Fix - Web Agent Prompt

## Agent Overview
**Task**: Complete the backtest results fix to ensure equity curve data is properly generated and charts display correct backtest timestamps instead of today's date.

**Status**: Partially Complete - Core equity curve collection implemented, needs testing and validation

## Current Progress
✅ **Completed**:
- Added equity_curve_data collection to EventDrivenStrategyEngine.__init__
- Modified _process_timestep to collect equity curve data after P&L calculation
- Updated _calculate_final_results to include equity_curve in performance data
- Fixed chart generation fallback to use backtest dates instead of today
- Updated BacktestService.get_result to include equity_curve in API response

🔄 **In Progress**: Testing and validation

## Remaining Tasks

### 1. Test Equity Curve Data Generation
**Objective**: Verify that equity curve data is properly collected and returned in API responses

**Steps**:
1. Start the backend server: `./platform.sh dev`
2. Run a short backtest:
   ```bash
   curl -X POST "http://localhost:8001/api/v1/backtest/" \
     -H "Content-Type: application/json" \
     -d '{"strategy_name": "pure_lending", "share_class": "USDT", "initial_capital": 100000, "start_date": "2024-05-12T00:00:00Z", "end_date": "2024-05-13T00:00:00Z"}'
   ```
3. Wait for completion and check results:
   ```bash
   curl "http://localhost:8001/api/v1/backtest/{request_id}/result" | jq '.data.equity_curve'
   ```
4. Verify equity curve contains:
   - Multiple data points (not just 2)
   - Correct timestamps (backtest dates, not today)
   - Realistic net_value progression
   - Proper data structure: `[{"timestamp": "...", "net_value": ..., "gross_value": ..., "positions": {...}}]`

### 2. Test Chart Generation
**Objective**: Verify that charts display correct backtest timestamps and data

**Steps**:
1. Check generated HTML files in `results/{request_id}_*/` directory
2. Open equity curve HTML file in browser
3. Verify:
   - X-axis shows backtest date range (2024-05-12 to 2024-05-13)
   - Y-axis shows portfolio value progression (not flat line)
   - Chart title shows correct backtest dates
   - No "today's date" timestamps

### 3. Fix Any Remaining Issues
**Common Issues to Check**:
- Equity curve data is empty or null
- Charts still show today's date
- Flat lines in PnL/equity curves
- Data structure mismatches

**Debugging Steps**:
1. Check server logs: `tail -f logs/api.log`
2. Look for equity curve collection logs
3. Verify data flow: EventDrivenStrategyEngine → BacktestService → API Response
4. Check chart generation logs for fallback usage

### 4. Create Unit Tests
**Objective**: Ensure equity curve functionality is properly tested

**Files to Create**:
- `tests/unit/test_equity_curve_generation.py`
- `tests/integration/test_chart_generation.py`

**Test Cases**:
- Equity curve data collection during backtest
- Chart generation with real equity curve data
- Chart generation fallback with backtest dates
- API response includes equity curve data

### 5. Validate Complete Fix
**Final Validation**:
1. Run full backtest with longer date range
2. Verify summary shows profit AND charts show progression
3. Check all chart types (equity curve, PnL, dashboard)
4. Ensure no flat lines or today's date timestamps
5. Run test suite to ensure no regressions

## Key Files Modified
- `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py`
- `backend/src/basis_strategy_v1/infrastructure/visualization/chart_generator.py`
- `backend/src/basis_strategy_v1/core/services/backtest_service.py`

## Expected Outcomes
- ✅ Backtest results show both correct summary metrics AND correct charts
- ✅ Charts display backtest date range instead of today's date
- ✅ Equity curve shows actual portfolio progression over time
- ✅ No flat lines in PnL, equity curve, or other time series charts
- ✅ Frontend can properly display the results
- ✅ All tests pass including new equity curve tests

## Success Criteria
1. **Functional**: Equity curve data is collected and displayed correctly
2. **Visual**: Charts show realistic data progression with correct timestamps
3. **Technical**: API responses include complete equity curve data
4. **Quality**: Comprehensive test coverage for new functionality

## Debugging Commands
```bash
# Check server status
ps aux | grep uvicorn

# View server logs
tail -f logs/api.log

# Test backtest endpoint
curl -X POST "http://localhost:8001/api/v1/backtest/" -H "Content-Type: application/json" -d '{"strategy_name": "pure_lending", "share_class": "USDT", "initial_capital": 100000, "start_date": "2024-05-12T00:00:00Z", "end_date": "2024-05-13T00:00:00Z"}'

# Check results
curl "http://localhost:8001/api/v1/backtest/{request_id}/result" | jq

# List all results
curl "http://localhost:8001/api/v1/results/" | jq

# Run tests
python -m pytest tests/unit/test_equity_curve_generation.py -v
```

## Notes
- The core fix is implemented but needs thorough testing
- Focus on data flow validation and chart generation
- Ensure both backtest and live modes work correctly
- Consider performance impact of equity curve data collection
- Maintain backward compatibility with existing functionality

## Priority
**HIGH** - This is a critical bug affecting core backtest functionality that makes results unusable for analysis.
