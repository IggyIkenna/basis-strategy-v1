# CRITICAL FIX: Remove Hardcoded Liquidity Index

## CONTEXT
The onchain_execution_interface.py was fixed with a hardcoded liquidity_index = 1.070100 instead of using the data provider. This is a hack that bypasses the proper architecture and must be fixed.

## ISSUE IDENTIFIED
- Hardcoded value: liquidity_index = 1.070100
- Bypasses data provider integration
- Violates architecture principles
- Only works for specific timestamp (June 1, 2024)

## REQUIRED FIX
1) Remove the hardcoded liquidity_index = 1.070100 from onchain_execution_interface.py
2) The liquidity index should come from the data provider, not be hardcoded
3) The data provider already loads liquidityIndex from data/protocol_data/aave/rates/aave_v3_aave-v3-ethereum_USDT_rates_2024-01-01_2025-09-18_hourly.csv
4) The execution interface should call the data provider to get the correct liquidity index for the current timestamp
5) This should be passed through the component chain: data provider → execution interface → position monitor

## ARCHITECTURE REQUIREMENTS
- Data provider loads liquidity index data at startup
- Execution interface queries data provider for current timestamp's liquidity index
- No hardcoded values should be used
- The fix should work for all timestamps, not just June 1, 2024

## FILES TO MODIFY
- backend/src/basis_strategy_v1/core/interfaces/onchain_execution_interface.py (remove hardcoded value)
- Ensure data provider integration is working properly
- Verify the component chain passes liquidity index correctly

## SUCCESS CRITERIA
- No hardcoded liquidity index values
- Liquidity index comes from data provider
- Works for all timestamps in the backtest period
- Pure lending quality gates still pass
- Architecture is properly maintained

## FORBIDDEN PRACTICES
- ❌ Using hardcoded values
- ❌ Bypassing data provider
- ❌ Using static values instead of dynamic data
- ❌ Fixing issues with "magic numbers"

## REQUIRED PRACTICES
- ✅ Use data provider for all external data
- ✅ Query data provider for current timestamp
- ✅ Pass data through proper component chain
- ✅ Maintain architecture integrity
- ✅ Use dynamic data, not static values

DO NOT use hardcoded values. Use the proper data provider integration.

