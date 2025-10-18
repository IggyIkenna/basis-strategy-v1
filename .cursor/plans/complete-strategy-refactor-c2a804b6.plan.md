<!-- c2a804b6-4a6f-4162-9bc0-746a26f902a3 c9c9ce21-096c-4818-8c5c-b7e8d692b068 -->
# Complete Strategy Refactor: Config-Driven Position Universe

## Architecture Changes

### Position Subscription Flow

1. Each `configs/modes/*.yaml` defines `component_config.position_monitor.position_subscriptions` listing ALL instruments strategy will touch (including transient positions like flash loans, swaps)
2. Strategy queries available instruments from position_monitor config during init
3. Risk Monitor, Execution Manager, PnL Monitor, Results Store, Position Update Handler all subscribe to same instrument universe
4. Venue configs (`configs/venues/*.yaml`) contain `canonical_instruments` list defining what CAN exist on that venue
5. Pydantic models in `backend/src/basis_strategy_v1/core/models/` validate venue-instrument mappings at runtime

### Dual Registry System

- **Config Registry** (`configs/venues/*.yaml`): Human-readable, defines venue capabilities
- **Code Registry** (`backend/src/basis_strategy_v1/core/models/instruments.py`): Startup/runtime validation, data availability checks

## Files to Modify

### 1. Venue Configs (Add canonical_instruments to all 11 files)

**`configs/venues/binance.yaml`** - Already has `canonical_instruments`, ensure complete

**`configs/venues/aave_v3.yaml`** - Add:

```yaml
# Canonical instruments available on this venue
canonical_instruments:
 - "aave_v3:aToken:aUSDT"
 - "aave_v3:debtToken:debtUSDT"
 - "aave_v3:aToken:aWETH"
 - "aave_v3:debtToken:debtWETH"
 - "aave_v3:aToken:aweETH"
```

**`configs/venues/etherfi.yaml`** - Already has `canonical_instruments`

**`configs/venues/lido.yaml`** - Add:

```yaml
canonical_instruments:
 - "lido:LST:stETH"
 - "lido:LST:wstETH"
```

**`configs/venues/bybit.yaml`** - Add:

```yaml
canonical_instruments:
 - "bybit:BaseToken:USDT"
 - "bybit:Perp:BTCUSDT"
 - "bybit:Perp:ETHUSDT"
```

**`configs/venues/okx.yaml`** - Add:

```yaml
canonical_instruments:
 - "okx:BaseToken:USDT"
 - "okx:Perp:BTCUSDT"
 - "okx:Perp:ETHUSDT"
```

**`configs/venues/morpho.yaml`** - Add if needed

**`configs/venues/instadapp.yaml`** - Add:

```yaml
canonical_instruments:
 - "instadapp:BaseToken:WETH"  # Flash loan intermediary
```

**`configs/venues/uniswap.yaml`** - Add:

```yaml
canonical_instruments:
 - "uniswap:BaseToken:ETH"
 - "uniswap:BaseToken:USDT"
  # Add other swappable tokens
```

**`configs/venues/alchemy.yaml`** - Add:

```yaml
canonical_instruments:
 - "wallet:BaseToken:ETH"
 - "wallet:BaseToken:USDT"
 - "wallet:BaseToken:BTC"
 - "wallet:BaseToken:WETH"
 - "wallet:BaseToken:EIGEN"
 - "wallet:BaseToken:ETHFI"
```

**`configs/venues/ml_inference_api.yaml`** - No instruments needed

### 2. Mode Configs (Fix position_subscriptions in all 10 files)

**`configs/modes/eth_staking_only.yaml`** - Fix line 56:

```yaml
position_subscriptions:
 - "wallet:BaseToken:ETH"
 - "etherfi:LST:weETH"  # FIXED: was etherfi:aToken:weETH
 - "wallet:BaseToken:EIGEN"
 - "wallet:BaseToken:ETHFI"
```

**`configs/modes/eth_leveraged.yaml`** - Fix position_subscriptions to use LST not aToken

**`configs/modes/pure_lending_eth.yaml`** - Ensure includes all AAVE intermediary positions

**`configs/modes/pure_lending_usdt.yaml`** - Ensure includes all AAVE intermediary positions

**`configs/modes/eth_basis.yaml`** - Already looks correct

**`configs/modes/btc_basis.yaml`** - Fix perp keys to use `bybit:Perp:BTCUSDT` not `bybit:PerpPosition:BTC`

**`configs/modes/ml_btc_directional_btc_margin.yaml`** - Add all instruments for ML strategy

**`configs/modes/ml_btc_directional_usdt_margin.yaml`** - Add all instruments for ML strategy

**`configs/modes/usdt_market_neutral.yaml`** - Fix to include staking + hedge instruments

**`configs/modes/usdt_market_neutral_no_leverage.yaml`** - Fix to include simple staking instruments

### 3. Pydantic Models (`backend/src/basis_strategy_v1/core/models/`)

**Create `backend/src/basis_strategy_v1/core/models/venue_validation.py`**:

```python
from pydantic import BaseModel, validator
from typing import List, Dict
from .venues import Venue
from .instruments import INSTRUMENTS, get_instruments_by_venue

class VenueConfig(BaseModel):
    """Pydantic model for venue configuration with instrument validation"""
    venue: str
    type: str
    canonical_instruments: List[str] = []
    
    @validator('venue')
    def validate_venue_exists(cls, v):
        if not Venue.validate_venue(v):
            raise ValueError(f"Unknown venue: {v}")
        return v
    
    @validator('canonical_instruments')
    def validate_instruments_match_venue(cls, v, values):
        """Ensure all instruments actually belong to this venue"""
        venue_name = values.get('venue')
        if not venue_name:
            return v
        
        for instrument_key in v:
            # Parse instrument key
            parts = instrument_key.split(':')
            if len(parts) != 3:
                raise ValueError(f"Invalid instrument key format: {instrument_key}")
            
            venue, pos_type, symbol = parts
            
            # Verify venue matches
            if venue != venue_name:
                raise ValueError(
                    f"Instrument {instrument_key} venue '{venue}' doesn't match config venue '{venue_name}'"
                )
            
            # Verify instrument exists in registry
            if instrument_key not in INSTRUMENTS:
                raise ValueError(
                    f"Instrument {instrument_key} not found in instrument registry. "
                    f"Add to backend/src/basis_strategy_v1/core/models/instruments.py"
                )
        
        return v
```

**Update `backend/src/basis_strategy_v1/core/models/instruments.py`**:

Add helper function:

```python
def get_instruments_by_venue(venue: str) -> List[str]:
    """Get all instrument keys for a specific venue"""
    return [key for key, inst in INSTRUMENTS.items() if inst.venue == venue]

def validate_instrument_for_venue(instrument_key: str, venue: str) -> bool:
    """Validate that an instrument can exist on a given venue"""
    if instrument_key not in INSTRUMENTS:
        return False
    return INSTRUMENTS[instrument_key].venue == venue
```

### 4. Strategy Files (All 10 strategies)

**Pattern for ALL strategies** - Add to `__init__`:

```python
from ...core.models.venues import Venue
from ...core.models.instruments import validate_instrument_key, get_display_name

def __init__(self, config, ...):
    super().__init__(config, data_provider, ...)
    
    # Get available instruments from position_monitor config
    position_config = config.get('component_config', {}).get('position_monitor', {})
    self.available_instruments = position_config.get('position_subscriptions', [])
    
    if not self.available_instruments:
        raise ValueError(
            f"{self.__class__.__name__} requires position_subscriptions in config. "
            "Define all instruments this strategy will use in component_config.position_monitor.position_subscriptions"
        )
    
    # Define required instruments for this strategy
    self.entry_instrument = f"{Venue.WALLET}:BaseToken:ETH"
    self.staking_instrument = f"{Venue.ETHERFI}:LST:weETH"
    
    # Validate all required instruments are in available set
    required_instruments = [self.entry_instrument, self.staking_instrument]
    for instrument in required_instruments:
        validate_instrument_key(instrument)  # Validate exists in registry
        if instrument not in self.available_instruments:
            raise ValueError(
                f"Required instrument {instrument} not in position_subscriptions. "
                f"Add to configs/modes/{mode}.yaml"
            )
    
    logger.info(f"Strategy initialized with {len(self.available_instruments)} available instruments")
    logger.info(f"  Required: {[get_display_name(i) for i in required_instruments]}")
```

**Specific fixes per strategy**:

1. **ETH Staking Only** (`eth_staking_only_strategy.py`):

                        - Change `etherfi:aToken:weETH` → `etherfi:LST:weETH`
                        - Query available instruments from config
                        - Already completed: use Venue enum, validate instruments

2. **ETH Leveraged** (`eth_leveraged_strategy.py`):

                        - Change LST position type from aToken to LST
                        - Query available instruments including flash loan intermediaries
                        - Already completed: use Venue enum

3. **Pure Lending ETH** (`pure_lending_eth_strategy.py`):

                        - Already completed: use Venue enum
                        - Add available instruments check

4. **Pure Lending USDT** (`pure_lending_usdt_strategy.py`):

                        - Already completed: use Venue enum
                        - Add available instruments check

5. **ETH Basis** (`eth_basis_strategy.py`):

                        - Implement from scratch with instrument validation
                        - Query perp + spot instruments from config

6. **BTC Basis** (`btc_basis_strategy.py`):

                        - Fix `bybit:PerpPosition:BTC` → `bybit:Perp:BTCUSDT`
                        - Add available instruments check

7-10. **ML and Market Neutral strategies**: Add instrument validation + available instruments check

### 5. Component Updates

**`backend/src/basis_strategy_v1/core/components/position_monitor.py`**:

Already validates position_subscriptions exist. Add instrument validation:

```python
def _initialize_positions_from_config(self) -> None:
    from ...core.models.instruments import validate_instrument_key
    
    position_config = self.config.get('component_config', {}).get('position_monitor', {})
    position_subs = position_config.get('position_subscriptions', [])
    
    if not position_subs:
        raise ValueError("position_subscriptions required...")
    
    # NEW: Validate all instruments exist in registry
    for position_key in position_subs:
        validate_instrument_key(position_key)
    
    logger.info(f"Pre-initializing {len(position_subs)} validated positions")
    for position_key in position_subs:
        self.simulated_positions[position_key] = 0.0
        self.real_positions[position_key] = 0.0
```

**`backend/src/basis_strategy_v1/core/components/risk_monitor.py`**:

Add instrument access via position_subscriptions

**`backend/src/basis_strategy_v1/core/components/execution_manager.py`**:

Validate order instruments against position_subscriptions

**`backend/src/basis_strategy_v1/core/components/pnl_monitor.py`**:

Subscribe to same position_subscriptions

**`backend/src/basis_strategy_v1/core/components/results_store.py`**:

Subscribe to same position_subscriptions

**`backend/src/basis_strategy_v1/core/components/position_update_handler.py`**:

Subscribe to same position_subscriptions

### 6. Documentation Updates

**`docs/INSTRUMENT_DEFINITIONS.md`** - Add after line 200:

````markdown
## Position Subscription Architecture

### Config-Driven Instrument Universe

All components share a unified instrument universe defined in `component_config.position_monitor.position_subscriptions`:

```yaml
component_config:
  position_monitor:
    position_subscriptions:
   - "wallet:BaseToken:ETH"      # Entry/exit position
   - "etherfi:LST:weETH"          # Staking position
   - "wallet:BaseToken:EIGEN"     # Dust positions
   - "instadapp:BaseToken:WETH"   # Flash loan intermediary
````

**All components** (Strategy, Position Monitor, Risk Monitor, Execution Manager, PnL Monitor, Results Store, Position Update Handler) subscribe to this same list.

### Strategy Access Pattern

Strategies query available instruments during initialization:

```python
position_config = config.get('component_config', {}).get('position_monitor', {})
self.available_instruments = position_config.get('position_subscriptions', [])

# Validate required instruments are available
if self.staking_instrument not in self.available_instruments:
    raise ValueError(f"Required instrument {self.staking_instrument} not in config")
```

### Venue-Instrument Validation

Venues define canonical instruments in `configs/venues/*.yaml`:

```yaml
# configs/venues/etherfi.yaml
canonical_instruments:
 - "etherfi:LST:weETH"
```

Pydantic models enforce venue-instrument mappings to prevent querying instruments that don't exist on a venue.

```

**`docs/specs/01_POSITION_MONITOR.md`** - Update line 130-140 to add instrument validation requirements

**`docs/specs/05_STRATEGY_MANAGER.md`** - Add section on querying available instruments from config

**`docs/REFERENCE_ARCHITECTURE_CANONICAL.md`** - Add section on unified position subscription architecture

## Implementation Order

1. ✅ Create `venues.py` and `instruments.py` (DONE)
2. ✅ Fix ETH Staking Only, ETH Leveraged, Pure Lending ETH, Pure Lending USDT (DONE)
3. Add `canonical_instruments` to all 11 venue configs
4. Create `venue_validation.py` Pydantic models
5. Fix all 10 mode configs `position_subscriptions` 
6. Update Position Monitor to validate instruments
7. Add available instruments check to all 10 strategies
8. Update remaining 6 strategies (ETH Basis, BTC Basis, 2x ML, 2x Market Neutral)
9. Update all 6 components to subscribe to position_subscriptions
10. Update all documentation
11. Run comprehensive tests

## Success Criteria

- ✅ Venue constants created
- ✅ Instrument registry created with data availability
- ✅ 4 strategies use Venue enum and instrument constants
- [ ] All venue configs have `canonical_instruments`
- [ ] All mode configs have correct `position_subscriptions`
- [ ] Pydantic models validate venue-instrument mappings
- [ ] All 10 strategies query `available_instruments` from config
- [ ] All 6 components subscribe to same position_subscriptions
- [ ] Position Monitor validates all instruments at startup
- [ ] Execution Manager validates order instruments
- [ ] All tests pass with instrument validation
- [ ] Documentation reflects config-driven architecture

### To-dos

- [ ] Add canonical_instruments to all 11 venue configs (aave_v3, lido, bybit, okx, morpho, instadapp, uniswap, alchemy)
- [ ] Create backend/src/basis_strategy_v1/core/models/venue_validation.py with Pydantic models
- [ ] Add get_instruments_by_venue() and validate_instrument_for_venue() to instruments.py
- [ ] Fix position_subscriptions in all 10 mode configs (LST not aToken, Perp:BTCUSDT not PerpPosition:BTC)
- [ ] Update Position Monitor _initialize_positions_from_config() to validate all instruments
- [ ] Add available_instruments query to all 10 strategy __init__ methods
- [ ] Implement ETH Basis strategy with config-driven instruments
- [ ] Fix BTC Basis: bybit:Perp:BTCUSDT + add available_instruments check
- [ ] Add instrument validation + SL/TP to both ML strategies
- [ ] Fix both Market Neutral strategies: rename + instrument validation
- [ ] Update Risk Monitor to access instruments via position_subscriptions
- [ ] Update Execution Manager to validate order instruments against position_subscriptions
- [ ] Update PnL Monitor to subscribe to position_subscriptions
- [ ] Update Results Store to subscribe to position_subscriptions
- [ ] Update Position Update Handler to subscribe to position_subscriptions
- [ ] Update INSTRUMENT_DEFINITIONS.md with position subscription architecture section
- [ ] Update docs/specs/01_POSITION_MONITOR.md with instrument validation requirements
- [ ] Update docs/specs/05_STRATEGY_MANAGER.md with available instruments query pattern
- [ ] Update REFERENCE_ARCHITECTURE_CANONICAL.md with unified position subscription architecture
- [ ] Run all unit tests + integration tests + quality gates with instrument validation