# Task: Add Config Integration to 07B_EXECUTION_INTERFACES

**Priority**: MEDIUM
**Component**: 07B_EXECUTION_INTERFACES
**Status**: PARTIALLY IMPLEMENTED
**Created**: October 12, 2025

## Overview
Add config-driven venue timeout and retry settings to existing execution interfaces implementation.

## Implementation Requirements

### Files to Update
- `backend/src/basis_strategy_v1/core/interfaces/base_execution_interface.py`
- `backend/src/basis_strategy_v1/core/interfaces/cex_execution_interface.py`
- `backend/src/basis_strategy_v1/core/interfaces/onchain_execution_interface.py`
- `backend/src/basis_strategy_v1/core/interfaces/transfer_execution_interface.py`

### Configuration Parameters to Add
1. **venue_timeout**: Venue API timeout in seconds (default: 15)
2. **max_retries**: Maximum retry attempts (default: 3)
3. **retry_delay**: Retry delay in seconds (default: 1)
4. **connection_timeout**: Connection timeout in seconds (default: 10)

### Implementation Changes
1. **Base Interface Updates**
   - Add config parameter loading in `__init__`
   - Implement timeout and retry logic
   - Add config validation

2. **Venue-Specific Updates**
   - CEX Interface: Add venue-specific timeout settings
   - OnChain Interface: Add gas price and transaction timeout settings
   - Transfer Interface: Add wallet operation timeout settings

3. **Error Code Standardization**
   - Standardize error codes across all interfaces
   - Add timeout-specific error codes
   - Add retry-specific error codes

### Configuration Schema
```yaml
component_config:
  execution_interfaces:
    venue_timeout: 15
    max_retries: 3
    retry_delay: 1
    connection_timeout: 10
    venue_specific:
      cex:
        order_timeout: 30
        balance_timeout: 10
      onchain:
        gas_timeout: 60
        transaction_timeout: 120
      transfer:
        wallet_timeout: 20
```

## Reference Implementation
- **Spec**: `docs/specs/07B_EXECUTION_INTERFACES.md`
- **Canonical Examples**: `02_EXPOSURE_MONITOR.md`, `03_RISK_MONITOR.md`
- **Architecture**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`

## Success Criteria
- All interfaces use config-driven timeout and retry settings
- Error codes standardized across all interfaces
- Configuration validation implemented
- Unit tests updated for new config parameters
- No hardcoded timeout or retry values
