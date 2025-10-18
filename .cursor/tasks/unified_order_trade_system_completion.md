# Unified Order/Trade System Completion - Web Agent Task

**Status**: Ready for Implementation  
**Created**: October 13, 2025  
**Priority**: High  
**Estimated Time**: 2-3 days  

## Overview

Complete the refactoring of the basis-strategy-v1 platform to use the unified Order/Trade system. This task involves refactoring remaining strategies, updating execution components, removing legacy code, updating documentation, and running comprehensive quality gates.

## Context

The platform is being refactored from a complex multi-abstraction system (StrategyAction + execution_instructions) to a unified Order/Trade system using Pydantic models. This provides a cleaner, more maintainable interface for all trading operations.

**Completed Work**:
- ✅ Order and Trade Pydantic models created with full validation
- ✅ BaseStrategyManager updated to return List[Order]
- ✅ PureLendingStrategy refactored (8/8 tests passing)
- ✅ BTCBasisStrategy refactored (13/13 tests passing)
- ✅ ETHBasisStrategy refactored (18/18 tests passing)
- ✅ Reference Architecture and ADR documentation updated

## Remaining Tasks

### Phase 1: Strategy Refactoring (Priority: High)

#### 1.1 Refactor Remaining Strategies
**Files to Update**:
- `backend/src/basis_strategy_v1/core/strategies/eth_leveraged_restaking_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/ml_btc_directional_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/ml_usdt_directional_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_no_leverage_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/eth_staking_only_strategy.py`

**Pattern to Follow**:
1. Update imports to include `Order`, `OrderOperation`
2. Add `make_strategy_decision()` method returning `List[Order]`
3. Replace old action methods with new `_create_*_orders()` methods
4. Add `_get_asset_price()` method for testing
5. Update `get_strategy_info()` method
6. Create comprehensive unit tests (follow pattern from existing refactored strategies)

**Special Considerations**:
- **ETH Leveraged Restaking**: Use atomic groups for complex DeFi operations
- **ML Strategies**: Include take_profit and stop_loss support
- **Market Neutral Strategies**: Handle both long and short positions

#### 1.2 Create Strategy Tests
**Files to Create**:
- `tests/unit/strategies/test_eth_leveraged_restaking_strategy_refactored.py`
- `tests/unit/strategies/test_ml_btc_directional_strategy_refactored.py`
- `tests/unit/strategies/test_ml_usdt_directional_strategy_refactored.py`
- `tests/unit/strategies/test_usdt_market_neutral_strategy_refactored.py`
- `tests/unit/strategies/test_usdt_market_neutral_no_leverage_strategy_refactored.py`
- `tests/unit/strategies/test_eth_staking_only_strategy_refactored.py`

**Test Requirements**:
- Minimum 15 tests per strategy
- Cover all decision scenarios (entry, exit, rebalance, maintain)
- Test all order creation methods
- Test exception handling
- Test atomic groups (where applicable)
- Test take_profit/stop_loss (for ML strategies)

### Phase 2: Execution Component Updates (Priority: High)

#### 2.1 Update VenueManager
**File**: `backend/src/basis_strategy_v1/core/execution/venue_manager.py`

**Changes Required**:
1. Update `_send_instruction()` method to accept `Order` objects
2. Remove old method-like instruction handling (`open_perp_long`, `open_perp_short`, etc.)
3. Add support for atomic group execution
4. Return `List[Trade]` instead of instruction results
5. Update all venue interface calls to use Order/Trade models

#### 2.2 Update Venue Interfaces
**Files to Update**:
- All files in `backend/src/basis_strategy_v1/core/execution/interfaces/`

**Changes Required**:
1. Update method signatures to accept `Order` objects
2. Return `Trade` objects instead of raw results
3. Add support for atomic group execution
4. Update error handling to use Trade model

#### 2.3 Update Strategy Manager
**File**: `backend/src/basis_strategy_v1/core/components/strategy_manager.py`

**Changes Required**:
1. Remove `_convert_strategy_action_to_instructions()` method
2. Update `make_strategy_decision()` to pass through `List[Order]`
3. Remove StrategyAction handling
4. Update logging to use Order/Trade models

### Phase 3: Legacy Code Removal (Priority: Medium)

#### 3.1 Remove Legacy Files
**Files to Delete**:
- `backend/src/basis_strategy_v1/core/instructions/execution_instructions.py`
- Any other files containing StrategyAction or execution_instructions

#### 3.2 Clean Up Imports
**Files to Update**:
- All strategy files
- All execution component files
- All test files

**Changes Required**:
1. Remove imports of `StrategyAction`
2. Remove imports of `execution_instructions`
3. Add imports of `Order`, `OrderOperation`, `Trade` where needed

#### 3.3 Remove StrategyAction Placeholder
**File**: `backend/src/basis_strategy_v1/core/strategies/base_strategy_manager.py`

**Changes Required**:
1. Remove temporary `StrategyAction` placeholder class
2. Clean up any remaining references

#### 3.4 Uncomment Strategy Imports
**Files to Update**:
- `backend/src/basis_strategy_v1/core/strategies/__init__.py`
- `backend/src/basis_strategy_v1/core/strategies/strategy_factory.py`

**Changes Required**:
1. Uncomment all strategy imports
2. Restore `STRATEGY_MAP` in strategy_factory.py
3. Ensure all strategies are properly imported

### Phase 4: Documentation Updates (Priority: Medium)

#### 4.1 Update Component Specifications
**Files to Update**:
- `docs/specs/05_STRATEGY_MANAGER.md`
- `docs/specs/5B_BASE_STRATEGY_MANAGER.md`
- `docs/specs/06_VENUE_MANAGER.md`
- `docs/specs/07_VENUE_INTERFACE_MANAGER.md`
- All individual strategy specification files

**Changes Required**:
1. Update method signatures to use Order/Trade models
2. Remove references to StrategyAction and execution_instructions
3. Add documentation for atomic group execution
4. Update examples to use new models

#### 4.2 Update Configuration Documentation
**Files to Update**:
- `docs/specs/19_CONFIGURATION.md`
- All mode configuration files in `configs/modes/`

**Changes Required**:
1. Update configuration examples to use Order/Trade models
2. Remove references to legacy instruction types
3. Add documentation for atomic group configuration

#### 4.3 Create Model Documentation
**Files to Create**:
- `docs/specs/ORDER_MODEL.md`
- `docs/specs/TRADE_MODEL.md`

**Content Required**:
1. Complete model documentation with all fields
2. Usage examples for each operation type
3. Atomic group execution examples
4. Validation rules and error handling

### Phase 5: Quality Gate Updates (Priority: High)

#### 5.1 Update Quality Gate Scripts
**Files to Update** (All 19 scripts listed below):
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

**Changes Required**:
1. Update to validate Order/Trade models instead of StrategyAction
2. Add validation for atomic group execution
3. Update strategy interface validation
4. Add validation for take_profit/stop_loss in ML strategies
5. Update venue interface validation

#### 5.2 Create New Quality Gate Scripts
**Files to Create**:
- `scripts/test_order_model_validation_quality_gates.py`
- `scripts/test_trade_model_validation_quality_gates.py`
- `scripts/test_atomic_group_execution_quality_gates.py`
- `scripts/test_strategy_order_interface_quality_gates.py`

### Phase 6: Testing and Validation (Priority: High)

#### 6.1 Update Existing Tests
**Files to Update**:
- All integration tests in `tests/integration/`
- All E2E tests in `tests/e2e/`

**Changes Required**:
1. Update to use Order/Trade models
2. Remove StrategyAction references
3. Add tests for atomic group execution
4. Add tests for take_profit/stop_loss

#### 6.2 Run Comprehensive Test Suite
**Commands to Run**:
```bash
# Unit tests
python -m pytest tests/unit/ -v --tb=short

# Integration tests
python -m pytest tests/integration/ -v --tb=short

# E2E tests
python -m pytest tests/e2e/ -v --tb=short

# All tests with coverage
python -m pytest tests/ --cov=backend/src/basis_strategy_v1 --cov-report=html --cov-report=term
```

#### 6.3 Run All Quality Gates
**Commands to Run**:
```bash
# Run all quality gates
python scripts/run_quality_gates.py

# Run specific categories
python scripts/run_quality_gates.py --category strategy
python scripts/run_quality_gates.py --category execution
python scripts/run_quality_gates.py --category docs
```

### Phase 7: Final Validation (Priority: High)

#### 7.1 Manual Review Checklist
- [ ] All strategies return `List[Order]`
- [ ] All execution components process `List[Order]` and return `List[Trade]`
- [ ] No references to StrategyAction or execution_instructions remain
- [ ] All tests pass (unit, integration, E2E)
- [ ] All quality gates pass
- [ ] Documentation is updated and consistent
- [ ] Atomic group execution works correctly
- [ ] Take_profit/stop_loss work in ML strategies
- [ ] Backtest and live modes work correctly

#### 7.2 Performance Validation
- [ ] No performance regressions in strategy execution
- [ ] Memory usage is reasonable
- [ ] Test execution time is acceptable

## Implementation Guidelines

### Code Quality Standards
1. **Follow existing patterns**: Use the same patterns established in refactored strategies
2. **Comprehensive testing**: Minimum 15 tests per strategy, 80%+ coverage
3. **Error handling**: Robust exception handling with proper logging
4. **Documentation**: Update all relevant documentation
5. **Validation**: Use Pydantic validation throughout

### Testing Strategy
1. **Unit tests first**: Test each component in isolation
2. **Integration tests**: Test component interactions
3. **E2E tests**: Test complete workflows
4. **Quality gates**: Validate architecture compliance

### Atomic Group Execution
For strategies requiring atomic execution (like ETH Leveraged Restaking):
```python
# Example atomic group
orders = [
    Order(
        venue='instadapp',
        operation=OrderOperation.FLASH_BORROW,
        amount=1000.0,
        execution_mode='atomic',
        atomic_group_id='flash_loan_001',
        sequence_in_group=1,
        # ... other fields
    ),
    Order(
        venue='instadapp',
        operation=OrderOperation.SUPPLY,
        amount=1000.0,
        execution_mode='atomic',
        atomic_group_id='flash_loan_001',
        sequence_in_group=2,
        # ... other fields
    )
]
```

### Take Profit/Stop Loss (ML Strategies)
For ML strategies requiring risk management:
```python
# Example with TP/SL
order = Order(
    venue='binance',
    operation=OrderOperation.PERP_TRADE,
    pair='BTCUSDT',
    side='LONG',
    amount=0.1,
    take_profit=55000.0,
    stop_loss=45000.0,
    # ... other fields
)
```

## Success Criteria

1. **All strategies refactored**: 6 remaining strategies converted to Order/Trade system
2. **All tests passing**: 100% test pass rate across unit, integration, and E2E tests
3. **All quality gates passing**: 100% quality gate pass rate
4. **No legacy code**: Complete removal of StrategyAction and execution_instructions
5. **Documentation updated**: All specs and documentation reflect new system
6. **Performance maintained**: No performance regressions
7. **Atomic execution working**: Complex DeFi operations execute atomically
8. **Risk management working**: Take profit/stop loss work in ML strategies

## Risk Mitigation

1. **Incremental approach**: Refactor one strategy at a time
2. **Comprehensive testing**: Test each refactored component thoroughly
3. **Quality gates**: Run quality gates after each major change
4. **Documentation**: Keep documentation updated throughout
5. **Rollback plan**: Keep git commits small and focused for easy rollback

## Timeline

- **Day 1**: Complete strategy refactoring (6 strategies)
- **Day 2**: Update execution components and remove legacy code
- **Day 3**: Update documentation, quality gates, and final validation

## Notes

- Follow the established patterns from PureLendingStrategy, BTCBasisStrategy, and ETHBasisStrategy
- Ensure all changes are backward compatible during transition
- Use the existing test patterns and quality gate structure
- Maintain the same level of error handling and logging
- Keep git commits focused and well-documented

This task represents the completion of a major architectural improvement that will significantly enhance the maintainability and clarity of the trading system.
