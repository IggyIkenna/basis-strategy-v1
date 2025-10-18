<!-- ee7dbf9c-5182-4f73-a387-2d2f0321057e a84a8bee-df06-4c83-9c34-cf31d55efb2b -->
# Complete Pending Strategy Refactor Tasks

## Phase 1: Documentation Updates

### 1.1 Update Component Specs with Position Subscriptions

Update all 7 component specifications to document the position subscriptions access pattern:

**Files to update:**

- `docs/specs/01_POSITION_MONITOR.md` (lines 130-140)
- `docs/specs/05_STRATEGY_MANAGER.md`
- `docs/specs/03_RISK_MONITOR.md`
- `docs/specs/04_EXECUTION_MANAGER.md`
- `docs/specs/02_PNL_MONITOR.md`
- `docs/specs/09_RESULTS_STORE.md`
- `docs/specs/10_POSITION_UPDATE_HANDLER.md`

**Pattern to add:**

````markdown
## Position Subscriptions Access

This component subscribes to the unified position universe via config:

```python
position_config = config.get('component_config', {}).get('position_monitor', {})
self.position_subscriptions = position_config.get('position_subscriptions', [])
````

All instruments are pre-validated by Position Monitor at startup.

````

### 1.2 Update STRATEGY_MODES.md

Update `docs/STRATEGY_MODES.md` for all 10 strategies:

**Changes needed:**
1. **ML Strategies Section** - Add ML SL/TP documentation (reference the implementation in ml_btc_directional_btc_margin_strategy.py and ml_btc_directional_usdt_margin_strategy.py)
2. **USDT Market Neutral Strategies** - Update names:
   - Old: "USDT Market Neutral (Leveraged)" → New: "USDT ETH Staking Hedged Leveraged"
   - Old: "USDT Market Neutral (No Leverage)" → New: "USDT ETH Staking Hedged Simple"
3. **Dust Handling** - Clarify for each strategy:
   - Active dust handling: ETH strategies (convert EIGEN/ETHFI to ETH/USDT)
   - Pass-through: Basis strategies, Pure Lending, ML strategies

## Phase 2: Comprehensive Testing (All 10 Strategies)

Create test files for all 10 strategies achieving 80%+ coverage:

### 2.1 Unit Tests (10+ tests per strategy)

**Create for each strategy:**
`tests/unit/strategies/test_{strategy_name}_unit.py`

**Required tests (10+ per strategy):**
1. `test_init_validates_required_instruments` - Validates position_subscriptions requirement
2. `test_init_validates_instruments_in_registry` - Validates instruments exist in registry
3. `test_generate_orders_entry_full` - Tests entry_full order generation
4. `test_create_entry_full_orders` - Tests _create_entry_full_orders method
5. `test_create_entry_partial_orders` - Tests _create_entry_partial_orders method
6. `test_create_exit_full_orders` - Tests _create_exit_full_orders method
7. `test_create_exit_partial_orders` - Tests _create_exit_partial_orders method
8. `test_create_dust_sell_orders` - Tests _create_dust_sell_orders method
9. `test_calculate_target_position` - Tests calculate_target_position method
10. `test_order_operation_id_format` - Validates operation_id format (unix microseconds)
11. `test_order_has_required_fields` - Validates all Order fields present

**ML Strategy-specific tests (add 3 more):**
12. `test_calculate_stop_loss_take_profit_long` - Tests SL/TP for LONG
13. `test_calculate_stop_loss_take_profit_short` - Tests SL/TP for SHORT
14. `test_sd_floor_cap` - Tests SD flooring and capping

**Strategy list:**
- eth_staking_only_strategy
- eth_leveraged_strategy
- pure_lending_eth_strategy
- pure_lending_usdt_strategy
- eth_basis_strategy
- btc_basis_strategy
- ml_btc_directional_btc_margin_strategy
- ml_btc_directional_usdt_margin_strategy
- usdt_eth_staking_hedged_leveraged_strategy
- usdt_eth_staking_hedged_simple_strategy

### 2.2 Integration Tests

**Create for each strategy:**
`tests/integration/strategies/test_{strategy_name}_integration.py`

**Required tests:**
1. `test_strategy_position_monitor_integration` - Verifies shared position universe
2. `test_order_position_tracking` - Verifies orders update positions correctly
3. `test_component_chain` - Tests strategy → position → exposure → risk → pnl flow

### 2.3 E2E Tests

**Create for each strategy:**
`tests/e2e/strategies/test_{strategy_name}_e2e.py`

**Required test:**
1. `test_full_cycle_entry_exit` - Tests complete cycle: entry → hold → exit

### 2.4 Test Coverage Validation

After all tests, run coverage check:
```bash
pytest --cov=backend/src/basis_strategy_v1/core/strategies --cov-report=term-missing --cov-report=html
````

**Target:** 80%+ coverage for each strategy file

## Implementation Notes

- Use existing test fixtures from `tests/conftest.py`
- Mock data_provider.get_ml_prediction() for ML strategies
- Use realistic test data (assume ETH starts in wallet with initial equity)
- Verify all Order fields: operation_id, expected_deltas, source/target venues/tokens
- ML tests must verify take_profit and stop_loss are calculated from signal SD

### To-dos

- [ ] Update 7 component specs with position subscriptions access pattern
- [ ] Update STRATEGY_MODES.md for all 10 strategies (ML SL/TP, naming, dust handling)
- [ ] Create unit tests for eth_staking_only_strategy (10+ tests)
- [ ] Create unit tests for eth_leveraged_strategy (10+ tests)
- [ ] Create unit tests for pure_lending_eth_strategy (10+ tests)
- [ ] Create unit tests for pure_lending_usdt_strategy (10+ tests)
- [ ] Create unit tests for eth_basis_strategy (10+ tests)
- [ ] Create unit tests for btc_basis_strategy (10+ tests)
- [ ] Create unit tests for ml_btc_directional_btc_margin_strategy (13+ tests including SL/TP)
- [ ] Create unit tests for ml_btc_directional_usdt_margin_strategy (13+ tests including SL/TP)
- [ ] Create unit tests for usdt_eth_staking_hedged_leveraged_strategy (10+ tests)
- [ ] Create unit tests for usdt_eth_staking_hedged_simple_strategy (10+ tests)
- [ ] Create integration tests for all 10 strategies (3 tests each)
- [ ] Create e2e tests for all 10 strategies (1 test each)
- [ ] Run pytest coverage and validate 80%+ for all strategies