<!-- 813f478f-da12-43d4-8562-ba9df169674d b33d151a-5257-4384-a38b-9a19e53480fc -->
# Architecture Documentation Alignment & Refactoring Plan

## Phase 1: Remove Redundant Flash Loan & Execution Mode Parameters

### 1.1 Update Configuration Files (configs/modes/)

**Files**: All 7 mode configs (btc_basis.yaml, eth_basis.yaml, eth_leveraged.yaml, eth_staking_only.yaml, pure_lending.yaml, usdt_market_neutral.yaml, usdt_market_neutral_no_leverage.yaml)

**Changes**:

- **Remove** `use_flash_loan` parameter from all configs (always true for leveraged staking, not applicable elsewhere)
- **Remove** `unwind_mode` parameter from all configs (always flash loan for unwinding leveraged positions)
- **Keep** `max_leverage_loops` and `min_loop_position_usd` ONLY in leveraged modes (eth_leveraged, usdt_market_neutral) - these are still relevant for atomic flash loan execution

**Rationale**: Flash loans are ALWAYS used for entry/exit in leveraged staking modes. Sequential execution never makes sense - it costs more time and money. Unwinding always requires flash loan because LST is tied up as collateral.

### 1.2 Update Config Models (backend/src/basis_strategy_v1/core/config/config_models.py)

**Changes**:

- Remove `use_flash_loan: Optional[bool]` from StrategyConfig (line ~63)
- Remove `unwind_mode: Optional[str]` from StrategyConfig (line ~64)
- Remove validation for these fields (lines ~176-184)
- Update MODE_REQUIREMENTS to remove these from required/optional fields

### 1.3 Update Strategy Manager (backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py)

**Changes**:

- Remove all references to `use_flash_loan` config checks (lines ~949, ~1229)
- Remove all references to `unwind_mode` config checks (line ~950)
- Always use flash loan for leveraged modes (atomic execution)

---

## Phase 2: Add Position Deviation Tolerance Parameter

### 2.1 Add New Config Parameter

**Files**: All 7 mode configs

**Add**:

```yaml
position_deviation_threshold: 0.02  # 2% deviation from target triggers rebalancing
```

**Description**: Minimum deviation from desired position before strategy manager triggers rebalancing. Prevents infinite small rebalancing operations.

### 2.2 Update Config Models

**File**: backend/src/basis_strategy_v1/core/config/config_models.py

**Add to StrategyConfig**:

```python
position_deviation_threshold: Optional[float] = Field(
    default=0.02, 
    ge=0.0, 
    le=1.0,
    description="Minimum deviation from target position to trigger rebalancing (fraction of target)"
)
```

### 2.3 Reference in Documentation

**Files**: docs/MODES.md, docs/specs/05_STRATEGY_MANAGER.md

**Add sections** explaining how position_deviation_threshold works with reserve_ratio to determine when rebalancing occurs.

---

## Phase 3: Clarify KING Token Handling & Reward Modes

### 3.1 Update ARCHITECTURAL_DECISIONS.md

**Section 9 (line ~554)**: Reward Modes for weETH

**Add**:

```markdown
**KING Token Handling**:
- All weETH rewards (EIGEN, ETHFI) come as KING tokens (composite wrapper)
- KING tokens count as dust and require unwrapping
- See docs/KING_TOKEN_HANDLING_GUIDE.md for unwrapping flow
- No need to track KING price - it's a derivative structure mapping to ETHFI + EIGEN
- When unwrapping, track equivalent ETHFI and EIGEN amounts for P&L attribution
```

### 3.2 Update MODES.md

**Sections**: ETH Leveraged, USDT Market Neutral modes

**Clarify** in "Ad-hoc Actions" that KING tokens are unwrapped and converted, not held long-term.

---

## Phase 4: Update Leverage Loop & Atomic Execution Sections

### 4.1 ARCHITECTURAL_DECISIONS.md Section 10 (line ~582)

**Replace** entire section with:

```markdown
### **10. Leverage Loop Execution** ✅

**Atomic Flash Loan Only**:
- Leveraged staking ALWAYS uses atomic flash loan (single transaction)
- Formula: Target LTV determines leverage ratio
- Entry: `borrow_flash → stake → supply_lst → borrow_aave → repay_flash`
- Exit/Unwind: `borrow_flash → withdraw_lst → swap_to_eth → repay_aave → repay_flash`
- Cost: ~$50 gas vs ~$200 for sequential
- No sequential option - atomic is always superior

**Parameters**:
- `max_leverage_loops`: Maximum iterations (legacy name, now atomic steps)
- `min_loop_position_usd`: Minimum position size threshold
```

### 4.2 ARCHITECTURAL_DECISIONS.md Section 22

**Remove or consolidate** "Atomic vs Sequential Leverage Loops" - redundant with Section 10.

---

## Phase 5: Consolidate & Clarify Rebalancing Logic

### 5.1 ARCHITECTURAL_DECISIONS.md Section 23 (line ~877)

**Replace** with:

```markdown
### **23. Rebalancing Implementation** ✅

**Strategy Manager Actions**:
- Uses 5 standardized actions from docs/MODES.md
- `entry_full`, `entry_partial`, `exit_full`, `exit_partial`, `sell_dust`
- Each breaks down into instruction blocks for Execution Manager

**Triggers**:
1. **Risk-triggered** (Priority 1): Risk Monitor detects warning/critical breach
   - LTV warning/critical (AAVE)
   - Maintenance margin warning/critical (CEX)
   - Strategy Manager unwinds to safe levels FIRST
   - Next loop iteration checks for optimal position
2. **Position-triggered** (Priority 2): Deviation from target exceeds `position_deviation_threshold`
   - Checked after risk is within safe levels
   - Uses reserve balance vs `reserve_ratio` to decide if unwinding needed

**Fast vs Slow Withdrawals**:
- Fast: Uses reserve balance (no unwinding needed)
- Slow: Requires unwinding positions (flash loan for leveraged modes)
- Decision based on: `reserve_balance / total_equity < reserve_ratio`

**No Complex Transfer Manager**:
- Removed per strategy_manager_refactor.md
- Strategy Manager calculates desired state
- Execution Manager handles venue routing
```

### 5.2 Remove Redundant Rebalancing Section

**ARCHITECTURAL_DECISIONS.md lines ~1219-1270**: Remove "Rebalancing Specification" section - redundant with Section 23 and docs/MODES.md.

---

## Phase 6: Clarify Hedging Logic

### 6.1 ARCHITECTURAL_DECISIONS.md Section 11 (line ~598)

**Change**:

```markdown
### **11. Hedging Logic** ✅

**ETH Share Class**:
- Never hedge (directional ETH exposure desired)
- Throw error if `basis_trade_enabled: true` (invalid config)

**USDT Share Class**:
- Always hedge (market-neutral required)
- Auto-enable `basis_trade_enabled` if staking enabled
- Throw error if disabled for staking strategies
```

---

## Phase 7: Fix Output File Structure & Plot Paths

### 7.1 ARCHITECTURAL_DECISIONS.md Section 17 (line ~702)

**Update** to match actual results structure:

```markdown
### **17. Output File Structure** ✅

**By Request ID**:
```

results/{request_id}/

summary.json

hourly_pnl.csv

event_log.csv

balance_sheet.csv

plots/

cumulative_pnl.html

pnl_components.html

delta_neutrality.html

margin_ratios.html

```

**Plots**: Plotly HTML (interactive), served by backend API
```

### 7.2 ARCHITECTURAL_DECISIONS.md Section 28

**Update** plot format section to reference correct paths.

---

## Phase 8: Clarify Margin Ratio Data Sources

### 8.1 ARCHITECTURAL_DECISIONS.md Section 30

**Add/Update**:

````markdown
### **30. Margin Ratio Thresholds** ✅

**Data Sources**:
- **Actual MMR & Liquidation Thresholds**: From `data/market_data/derivatives/risk_params/` (backtest) or queried from exchange APIs (live)
- **Warning Thresholds**: From `configs/venues/*.yaml` with optional strategy mode overrides
- Same pattern as AAVE: `data/protocol_data/aave/risk_params/aave_v3_risk_parameters.json`

**Config Merge**:
```python
# Venue default
venue_config = {
  'margin_warning_threshold': 0.20,
  'margin_critical_threshold': 0.10
}

# Optional mode override
mode_config = {
  'margin_warning_threshold': 0.25  # More conservative
}

# Merged: mode overrides venue default
final_threshold = 0.25
````

**Files**:

- `data/market_data/derivatives/risk_params/binance_margin_requirements.json`
- `data/market_data/derivatives/risk_params/bybit_margin_requirements.json`
- `data/market_data/derivatives/risk_params/okx_margin_requirements.json`
````

---

## Phase 9: Add Component State Logging (Live Trading)

### 9.1 ARCHITECTURAL_DECISIONS.md - Live Trading Section
**Add after line ~1112**:

```markdown
### **Component State Logging**

**All Components** (Position Monitor, Exposure Monitor, Risk Monitor, Strategy Manager, Execution Interfaces):

**Backtest Mode**:
```python
logger.info(f"{component_name}: State before operation", extra={
    'timestamp': timestamp,  # Same as operation timestamp
    'status': 'pending',
    'state_snapshot': self._get_state()
})

# ... operation ...

logger.info(f"{component_name}: State after operation", extra={
    'timestamp': timestamp,  # Same timestamp (simulated)
    'status': 'complete',
    'state_snapshot': self._get_state()
})
````


**Live Mode**:

```python
logger.info(f"{component_name}: State before operation", extra={
    'timestamp': datetime.now(timezone.utc),
    'status': 'pending',
    'state_snapshot': self._get_state()
})

# ... operation ...

logger.info(f"{component_name}: State after operation", extra={
    'timestamp': datetime.now(timezone.utc),  # Different timestamp (real elapsed time)
    'status': 'complete',
    'duration_ms': elapsed_time,
    'state_snapshot': self._get_state()
})
```

**Benefits**:

- Track operation duration in live mode
- Runtime logs show component state changes
- Identical structure in backtest (timestamps same) vs live (timestamps differ)
````

---

## Phase 10: Update Storage Strategy for Live

### 10.1 ARCHITECTURAL_DECISIONS.md - Storage Strategy Section
**Update**:

```markdown
### **Storage Strategy**

**Phase 1 (MVP - Live Trading)**:
- CSV files for simplicity
- Same format as backtest
- Easy debugging and inspection
- Results written to `results/{request_id}/`

**Future (Phase 2+)**:
- Database for scalability
- Time-series optimization
- Query performance for analytics
````


---

## Phase 11: Remove Obsolete Config vs CLI Priority Section

### 11.1 ARCHITECTURAL_DECISIONS.md Section 25

**Check implementation** - if not implemented, remove entire section as it's not a clear use case.

---

## Phase 12: Enhance Validation Philosophy

### 12.1 ARCHITECTURAL_DECISIONS.md Section 26

**Expand** with specific validation checks:

```markdown
### **26. Validation Philosophy** ✅

**Multi-Level Validation Strategy**:

**Level 1: Schema Validation** (Pydantic)
- Field types, ranges, required fields
- Enum validation (mode, asset, lst_type)

**Level 2: Business Logic Validation**
- Share class consistency: `market_neutral` flag matches hedging requirements
- Asset consistency: BTC basis requires BTC asset, ETH modes require ETH asset
- Hedge allocation sums to 1.0
- LST type valid for strategy mode
- Reward mode valid for LST type (wstETH only supports base_only)

**Level 3: Mode-Specific Validation**
- Required fields per mode (MODE_REQUIREMENTS)
- Forbidden fields per mode
- Parameter dependencies (lending+staking requires borrowing or basis_trade for USDT)

**Level 4: Data Availability Validation**
- Required data files exist for backtest date range
- Risk parameters available (AAVE, CEX margin requirements)
- Market data coverage complete

**Level 5: Cross-Component Consistency**
- Venue configs match strategy mode venue requirements
- Warning thresholds < critical thresholds
- Position deviation threshold < 1.0
- Reserve ratio reasonable (0.05 - 0.2 range)

**Implementation**: config_validator.py with comprehensive validation functions
```

---

## Phase 13: Add Quality Gates Requirement

### 13.1 ARCHITECTURAL_DECISIONS.md Section 27

**Add**:

```markdown
### **27. Testing Granularity** ✅

**Quality Gate Requirements**:
- MANDATORY for all components in docs/specs/
- Prevents breaking implementations during iteration
- See docs/QUALITY_GATES.md for gate categories
- Target: 80% unit/integration coverage, 100% e2e coverage

**Component Quality Gates**:
- Each spec in docs/specs/ has corresponding quality gate tests
- Integration tests validate cross-component interactions
- E2E tests validate full backtest flow per strategy mode
```

---

## Phase 14: Remove/Update Documentation Structure Section

### 14.1 ARCHITECTURAL_DECISIONS.md Section 29

**Remove entirely** - structure is already documented in docs/INDEX.md and docs/README.md.

---

## Phase 15: Update Component Data Flow Architecture

### 15.1 ARCHITECTURAL_DECISIONS.md Section 41 (line ~1432)

**Replace** with alignment to canonical patterns:

````markdown
### **41. Component Data Flow Architecture** ✅

**Aligned with Canonical Patterns**:
- **Shared Clock Pattern** (docs/SHARED_CLOCK_PATTERN.md): EventDrivenStrategyEngine owns timestamp, passes to all components
- **Reference-Based Architecture** (docs/REFERENCE_ARCHITECTURE_CANONICAL.md): Components store config, data_provider, other component references at init
- **Request Isolation Pattern** (docs/REQUEST_ISOLATION_PATTERN.md): Fresh instances per backtest/live request

**Data Flow**:
```python
# EventDrivenStrategyEngine manages timestamp
for timestamp in self.timestamps:
    self.current_timestamp = timestamp
    
    # All components receive same timestamp
    self.position_monitor.update_state(timestamp, 'full_loop')
    self.exposure_monitor.update_state(timestamp, 'full_loop') 
    self.risk_monitor.update_state(timestamp, 'full_loop')
    self.pnl_calculator.update_state(timestamp, 'full_loop')
    
    # Components query data with timestamp
    # market_data = self.data_provider.get_data(timestamp)
    # Ensures all components see identical data snapshot
````

**Component References** (stored at init, never passed as runtime params):

```python
class ExampleComponent:
    def __init__(self, config, data_provider, execution_mode, position_monitor=None):
        self.config = config  # Reference, never modified
        self.data_provider = data_provider  # Query with timestamps
        self.execution_mode = execution_mode  # 'backtest' or 'live'
        self.position_monitor = position_monitor  # Reference
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
        # Use stored references directly
        market_data = self.data_provider.get_data(timestamp)
        position = self.position_monitor.get_current_position()
```

**See**: docs/WORKFLOW_GUIDE.md for complete flow, docs/SHARED_CLOCK_PATTERN.md for timestamp management

```

---

## Phase 16: Update Documentation Files

### 16.1 docs/MODES.md Updates

**Sections to update**:

1. Execution Architecture: Remove atomic vs sequential toggle references
2. All mode execution flows: Remove `use_flash_loan` and `unwind_mode` mentions
3. Add `position_deviation_threshold` to Standardized Strategy Manager Architecture
4. Clarify KING token unwrapping in ETH modes
5. Update reserve management to reference `position_deviation_threshold`

### 16.2 docs/specs/05_STRATEGY_MANAGER.md Updates

**Changes**:

1. Remove `use_flash_loan` references from code examples
2. Update rebalancing logic to reference `position_deviation_threshold`
3. Clarify that unwinding always uses flash loan for leveraged modes
4. Add state logging pattern for live trading

### 16.3 docs/specs/12_FRONTEND_SPEC.md Updates

**Changes**:

1. Remove `use_flash_loan` toggle from strategy config step
2. Remove `unwind_mode` selector from strategy config step
3. Add `position_deviation_threshold` slider if advanced mode shown
4. Simplify execution mode documentation

### 16.4 docs/specs/19_CONFIGURATION.md Updates

**Changes**:

1. Update configuration hierarchy to show removed parameters
2. Add `position_deviation_threshold` to mode config fields
3. Document margin ratio threshold loading from data/
4. Add validation for position_deviation_threshold

### 16.5 .cursor/tasks/19_venue_based_execution_architecture.md Updates

**Changes**:

1. Remove flash loan toggle references
2. Clarify that leveraged modes always use atomic execution
3. Update environment configuration examples

---

## Phase 17: Consolidate & Reduce Redundancy

### 17.1 ARCHITECTURAL_DECISIONS.md Consolidation

**Actions**:

1. Merge Sections 10 and 22 (both about leverage loops)
2. Remove redundant rebalancing section (lines ~1219-1270)
3. Remove Section 29 (Documentation Structure - redundant)
4. Remove Section 25 if not implemented (Config vs CLI Priority)
5. Consolidate Live Trading sections into single comprehensive section

**Result**: Reduce from ~1850 lines to ~1600 lines while maintaining technical detail through DRY principle.

---

## Phase 18: Update Validation & Testing

### 18.1 Backend Validation Updates

**Files**:

- backend/src/basis_strategy_v1/infrastructure/config/config_validator.py
- backend/src/basis_strategy_v1/core/config/config_models.py

**Add validations**:

1. Throw error if `basis_trade_enabled: true` for ETH share class modes
2. Validate `position_deviation_threshold` in range [0.001, 0.1]
3. Validate that leveraged modes don't have `use_flash_loan` or `unwind_mode` (deprecated)
4. Validate reserve_ratio in reasonable range [0.05, 0.3]

---

## Implementation Order

Execute phases in sequence to maintain consistency between config → models → docs → code.

### To-dos

- [ ] Remove use_flash_loan and unwind_mode from all 7 mode configs (btc_basis.yaml, eth_basis.yaml, eth_leveraged.yaml, eth_staking_only.yaml, pure_lending.yaml, usdt_market_neutral.yaml, usdt_market_neutral_no_leverage.yaml)
- [ ] Remove use_flash_loan and unwind_mode fields from StrategyConfig in config_models.py, including validators and MODE_REQUIREMENTS
- [ ] Add position_deviation_threshold: 0.02 parameter to all 7 mode configs
- [ ] Add position_deviation_threshold field to StrategyConfig in config_models.py with validation (0.0 to 1.0)
- [ ] Remove use_flash_loan and unwind_mode config checks from strategy_manager.py (lines ~949, ~950, ~1229)
- [ ] Add KING token handling clarification to ARCHITECTURAL_DECISIONS.md section 9 (reward modes)
- [ ] Replace ARCHITECTURAL_DECISIONS.md section 10 with atomic-only leverage loop explanation
- [ ] Remove or consolidate ARCHITECTURAL_DECISIONS.md section 22 (redundant with section 10)
- [ ] Replace ARCHITECTURAL_DECISIONS.md section 23 with consolidated rebalancing logic
- [ ] Remove redundant Rebalancing Specification section from ARCHITECTURAL_DECISIONS.md (lines ~1219-1270)
- [ ] Update ARCHITECTURAL_DECISIONS.md section 11 to throw error instead of auto-disable for hedging
- [ ] Fix output file structure in ARCHITECTURAL_DECISIONS.md section 17 to match results/{request_id}/ pattern
- [ ] Add margin ratio data sources explanation to ARCHITECTURAL_DECISIONS.md section 30
- [ ] Add component state logging pattern to ARCHITECTURAL_DECISIONS.md Live Trading section
- [ ] Update storage strategy section in ARCHITECTURAL_DECISIONS.md to CSV for MVP
- [ ] Check if Config vs CLI Priority is implemented, remove ARCHITECTURAL_DECISIONS.md section 25 if not
- [ ] Expand ARCHITECTURAL_DECISIONS.md section 26 with multi-level validation strategy breakdown
- [ ] Add quality gate requirements to ARCHITECTURAL_DECISIONS.md section 27
- [ ] Remove ARCHITECTURAL_DECISIONS.md section 29 (Documentation Structure - redundant)
- [ ] Replace ARCHITECTURAL_DECISIONS.md section 41 with canonical pattern alignment
- [ ] Update MODES.md Execution Architecture section to remove atomic vs sequential toggle
- [ ] Remove use_flash_loan and unwind_mode from all mode execution flows in MODES.md
- [ ] Add position_deviation_threshold to Standardized Strategy Manager Architecture in MODES.md
- [ ] Clarify KING token unwrapping in ETH mode sections of MODES.md
- [ ] Update reserve management in MODES.md to reference position_deviation_threshold
- [ ] Remove use_flash_loan references and add state logging to docs/specs/05_STRATEGY_MANAGER.md
- [ ] Remove use_flash_loan and unwind_mode UI elements from docs/specs/12_FRONTEND_SPEC.md
- [ ] Update docs/specs/19_CONFIGURATION.md with removed parameters and new position_deviation_threshold
- [ ] Update .cursor/tasks/19_venue_based_execution_architecture.md to remove flash loan toggle references
- [ ] Add validation for basis_trade_enabled error, position_deviation_threshold range, and deprecated params in config_validator.py
- [ ] Search and verify all use_flash_loan and unwind_mode references removed from documentation
- [ ] Verify all doc cross-references updated and section numbers corrected after removals