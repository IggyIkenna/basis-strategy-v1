# Web Agent Prompt: Complete Unified Order/Trade System

## Task Overview
Complete the refactoring of basis-strategy-v1 platform to use unified Order/Trade system. Replace StrategyAction + execution_instructions with clean Order/Trade Pydantic models.

## Current Status
- ✅ Order/Trade models created and tested
- ✅ 3 strategies refactored (PureLending, BTCBasis, ETHBasis) 
- ❌ 6 strategies remaining to refactor
- ❌ Execution components need updating
- ❌ Legacy code needs removal

## Your Mission
**Complete all remaining work in this order:**

### 1. Refactor 6 Remaining Strategies
**Files to update:**
- `backend/src/basis_strategy_v1/core/strategies/eth_leveraged_restaking_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/ml_btc_directional_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/ml_usdt_directional_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_no_leverage_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/eth_staking_only_strategy.py`

**For each strategy:**
1. Update imports: add `Order`, `OrderOperation` from `...core.models.order`
2. Add `make_strategy_decision()` method returning `List[Order]`
3. Replace old action methods with `_create_*_orders()` methods
4. Add `_get_asset_price()` method for testing
5. Update `get_strategy_info()` method
6. Create comprehensive unit tests (15+ tests per strategy)

**Special requirements:**
- **ETH Leveraged Restaking**: Use atomic groups for DeFi operations
- **ML Strategies**: Include take_profit and stop_loss support
- **Market Neutral**: Handle both long and short positions

### 2. Update Execution Components
**Files to update:**
- `backend/src/basis_strategy_v1/core/execution/execution_manager.py`
- All files in `backend/src/basis_strategy_v1/core/execution/interfaces/`
- `backend/src/basis_strategy_v1/core/components/strategy_manager.py`

**Changes:**
- Update methods to accept `Order` objects and return `Trade` objects
- Remove old method-like instruction handling
- Add atomic group execution support

### 3. Remove Legacy Code
**Files to delete:**
- `backend/src/basis_strategy_v1/core/instructions/execution_instructions.py`

**Files to update:**
- `backend/src/basis_strategy_v1/core/strategies/base_strategy_manager.py` (remove StrategyAction placeholder)
- `backend/src/basis_strategy_v1/core/strategies/__init__.py` (uncomment strategy imports)
- `backend/src/basis_strategy_v1/core/strategies/strategy_factory.py` (restore STRATEGY_MAP)

### 4. Update Quality Gates
**Files to update (19 scripts):**
- `scripts/test_component_data_flow_architecture_quality_gates.py`
- `scripts/test_component_signature_validation_quality_gates.py`
- `scripts/test_config_implementation_usage_quality_gates.py`
- `scripts/test_docs_structure_validation_quality_gates.py`
- `scripts/test_docs_link_validation_quality_gates.py`
- `scripts/test_env_config_usage_sync_quality_gates.py`
- `scripts/test_implementation_gap_quality_gates.py`
- `scripts/test_mode_agnostic_architecture_quality_gates.py`
- `scripts/test_singleton_pattern_quality_gates.py`
- `scripts/test_reference_architecture_quality_gates.py`
- `scripts/test_strategy_action_config_quality_gates.py`
- `scripts/test_strategy_manager_refactor_quality_gates.py`
- `scripts/test_venue_config_quality_gates.py`
- `scripts/test_data_validation_quality_gates.py`
- `scripts/test_data_provider_canonical_access_quality_gates_simple.py`
- `scripts/test_config_usage_sync_quality_gates.py`
- `scripts/test_config_spec_yaml_sync_quality_gates.py`
- `scripts/test_config_loading_quality_gates.py`
- `scripts/test_config_access_validation_quality_gates.py`

**Changes:** Update to validate Order/Trade models instead of StrategyAction

### 5. Run Master Validation
**Commands to run:**
```bash
# Run all tests
python -m pytest tests/ -v

# Run all quality gates
python scripts/run_quality_gates.py

# Check coverage
python -m pytest tests/ --cov=backend/src/basis_strategy_v1 --cov-report=term
```

## Success Criteria
- [ ] All 6 strategies refactored and tested
- [ ] All execution components updated
- [ ] All legacy code removed
- [ ] All quality gates passing
- [ ] All tests passing (unit, integration, E2E)
- [ ] No references to StrategyAction or execution_instructions remain

## Reference Patterns
Follow the exact patterns from completed strategies:
- `tests/unit/strategies/test_pure_lending_usdt_strategy_refactored.py`
- `tests/unit/strategies/test_btc_basis_strategy_refactored.py`
- `tests/unit/strategies/test_eth_basis_strategy_refactored.py`

## Key Models
- **Order**: `backend/src/basis_strategy_v1/core/models/order.py`
- **Trade**: `backend/src/basis_strategy_v1/core/models/trade.py`

## Atomic Group Example
```python
orders = [
    Order(
        venue='instadapp',
        operation=OrderOperation.FLASH_BORROW,
        amount=1000.0,
        execution_mode='atomic',
        atomic_group_id='flash_001',
        sequence_in_group=1
    ),
    Order(
        venue='instadapp', 
        operation=OrderOperation.SUPPLY,
        amount=1000.0,
        execution_mode='atomic',
        atomic_group_id='flash_001',
        sequence_in_group=2
    )
]
```

## Take Profit/Stop Loss Example
```python
order = Order(
    venue='binance',
    operation=OrderOperation.PERP_TRADE,
    pair='BTCUSDT',
    side='LONG',
    amount=0.1,
    take_profit=55000.0,
    stop_loss=45000.0
)
```

**Complete this task systematically, testing each component as you go. The goal is a fully functional unified Order/Trade system with 100% test coverage and passing quality gates.**
