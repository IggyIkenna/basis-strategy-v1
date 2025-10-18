# Complete Strategy Refactor with Unified Position Subscriptions

## Overview

Refactor all 10 strategies to use **unified position subscription system** where all components subscribe to the same instrument universe defined in `component_config.position_monitor.position_subscriptions`. Implement venue-to-instrument mapping through Pydantic models and ensure uniform position access across all components.

## Critical Architecture Changes

### 1. Unified Position Subscription System

**All components must subscribe to the same instrument universe** defined in strategy configs:

```yaml
# configs/modes/eth_staking_only.yaml
component_config:
  position_monitor:
    position_subscriptions:
      - "wallet:BaseToken:ETH"
      - "etherfi:LST:weETH"
      - "wallet:BaseToken:EIGEN"  # Dust
      - "wallet:BaseToken:ETHFI"  # Dust
```

**Components that subscribe to position_subscriptions:**
- Position Monitor (primary)
- Exposure Monitor
- Risk Monitor  
- Execution Manager
- PnL Monitor
- Results Store
- Position Update Handler

### 2. Venue-to-Instrument Mapping in configs/venues/*.yaml

**Update all venue configs** to include canonical instruments:

```yaml
# configs/venues/etherfi.yaml
venue: "etherfi"
type: "defi"
canonical_instruments:
  - "etherfi:LST:weETH"
  - "etherfi:LST:stETH"  # If supported

# configs/venues/binance.yaml  
venue: "binance"
type: "cex"
canonical_instruments:
  - "binance:BaseToken:USDT"
  - "binance:BaseToken:BTC"
  - "binance:BaseToken:ETH"
  - "binance:Perp:BTCUSDT"
  - "binance:Perp:ETHUSDT"
```

### 3. Pydantic Models for Venue Validation

**Create venue validation models** to enforce instrument-venue mapping:

```python
# backend/src/basis_strategy_v1/core/models/venue_config.py
from pydantic import BaseModel, validator
from typing import List
from .instruments import validate_instrument_key, get_instruments_by_venue

class VenueConfig(BaseModel):
    venue: str
    type: str  # "cex", "defi", "infrastructure"
    canonical_instruments: List[str]
    
    @validator('canonical_instruments')
    def validate_instruments_exist(cls, v, values):
        """Validate all instruments exist in registry and match venue"""
        venue = values.get('venue')
        for instrument in v:
            validate_instrument_key(instrument)
            # Verify instrument belongs to this venue
            if not instrument.startswith(f"{venue}:"):
                raise ValueError(f"Instrument {instrument} does not belong to venue {venue}")
        return v
    
    def get_available_instruments(self) -> List[str]:
        """Get instruments available on this venue"""
        return self.canonical_instruments
```

### 4. Strategy Position Querying Pattern

**All strategies query available instruments** from position monitor config:

```python
# In strategy __init__
def __init__(self, config: Dict[str, Any], ...):
    # Get position subscriptions from config
    position_subscriptions = config['component_config']['position_monitor']['position_subscriptions']
    
    # Validate all instruments exist and are available
    for instrument in position_subscriptions:
        validate_instrument_key(instrument)
    
    # Store for use in order generation
    self.available_instruments = position_subscriptions
    
    # Define strategy-specific instrument mappings
    self.entry_instrument = self._find_instrument("wallet:BaseToken:ETH")
    self.staking_instrument = self._find_instrument("etherfi:LST:weETH")
    
def _find_instrument(self, pattern: str) -> str:
    """Find instrument matching pattern in available instruments"""
    for instrument in self.available_instruments:
        if pattern in instrument:
            return instrument
    raise ValueError(f"No instrument found matching pattern: {pattern}")
```

## Implementation Plan

### Phase 1: Infrastructure Updates

1. **Update configs/venues/*.yaml** (11 files)
   - Add `canonical_instruments` to each venue config
   - Map all instruments from `instruments.py` to their venues

2. **Create VenueConfig Pydantic model**
   - `backend/src/basis_strategy_v1/core/models/venue_config.py`
   - Validation for venue-instrument mapping
   - Helper methods for instrument queries

3. **Update all 10 strategy configs**
   - Add `position_subscriptions` to `component_config.position_monitor`
   - Define complete instrument universe for each strategy

### Phase 2: Component Updates

4. **Update Position Monitor**
   - Use `position_subscriptions` from config
   - Validate all instruments at initialization
   - Provide instrument querying methods

5. **Update all subscribing components**
   - Exposure Monitor: Query position monitor for available instruments
   - Risk Monitor: Subscribe to same position universe
   - Execution Manager: Validate orders against available instruments
   - PnL Monitor: Track PnL for subscribed instruments only
   - Results Store: Store results for subscribed instruments only
   - Position Update Handler: Update positions for subscribed instruments only

### Phase 3: Strategy Updates

6. **Update all 10 strategies**
   - Remove hardcoded instrument definitions
   - Query available instruments from position monitor config
   - Use `_find_instrument()` pattern for instrument discovery
   - Validate all `expected_deltas` use available instruments only

### Phase 4: Documentation & Testing

7. **Update documentation**
   - INSTRUMENT_DEFINITIONS.md: Add unified position subscription section
   - REFERENCE_ARCHITECTURE_CANONICAL.md: Document position subscription patterns
   - All strategy specs: Update with position subscription examples

8. **Update tests**
   - Mock position subscriptions in all strategy tests
   - Test venue-instrument validation
   - Test instrument discovery patterns

## Files to Modify

### Config Files (21 files)
- `configs/venues/*.yaml` (11 files) - Add canonical_instruments
- `configs/modes/*.yaml` (10 files) - Add position_subscriptions

### Model Files (2 files)
- `backend/src/basis_strategy_v1/core/models/venue_config.py` (new)
- `backend/src/basis_strategy_v1/core/models/instruments.py` (update validation)

### Component Files (7 files)
- `backend/src/basis_strategy_v1/core/monitors/position_monitor.py`
- `backend/src/basis_strategy_v1/core/monitors/exposure_monitor.py`
- `backend/src/basis_strategy_v1/core/monitors/risk_monitor.py`
- `backend/src/basis_strategy_v1/core/execution/execution_manager.py`
- `backend/src/basis_strategy_v1/core/monitors/pnl_monitor.py`
- `backend/src/basis_strategy_v1/core/storage/results_store.py`
- `backend/src/basis_strategy_v1/core/handlers/position_update_handler.py`

### Strategy Files (10 files)
- All strategy implementations updated to query position subscriptions

### Documentation Files (5 files)
- `docs/INSTRUMENT_DEFINITIONS.md`
- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`
- `docs/specs/05_STRATEGY_MANAGER.md`
- `docs/specs/05B_BASE_STRATEGY_MANAGER.md`
- All 10 strategy spec files

## Success Criteria

1. **Unified Position Access**: All components subscribe to same instrument universe
2. **Venue Validation**: Pydantic models enforce venue-instrument mapping
3. **Config-Driven**: All instrument discovery via position_subscriptions
4. **No Hardcoding**: Strategies query available instruments dynamically
5. **Validation**: All instruments validated at component initialization
6. **Consistency**: Same position keys used across all components
7. **Documentation**: Complete documentation of position subscription patterns

## Benefits

- **Single Source of Truth**: Position subscriptions defined once in config
- **Type Safety**: Pydantic validation prevents invalid venue-instrument combinations
- **Maintainability**: Easy to add/remove instruments by updating configs
- **Consistency**: All components use same instrument universe
- **Validation**: Fail-fast on invalid instrument configurations
- **Flexibility**: Easy to support new venues and instruments

## Implementation Order

1. Update venue configs with canonical_instruments
2. Create VenueConfig Pydantic model
3. Update all strategy configs with position_subscriptions
4. Update Position Monitor to use position_subscriptions
5. Update all other components to query position monitor
6. Update all strategies to use dynamic instrument discovery
7. Update documentation and tests
8. Run comprehensive validation

This approach ensures uniform position access across all components while maintaining type safety and configuration-driven flexibility.
