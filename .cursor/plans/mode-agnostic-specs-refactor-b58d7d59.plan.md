<!-- b58d7d59-10d1-4def-9586-7810ac4c225e c43be371-aab6-46f6-b3df-b70218726e8e -->
# Mode-Agnostic Architecture Specification Refactor

## Overview

Refactor 8 component specifications (`05_STRATEGY_MANAGER.md`, `07A_EXECUTION_INTERFACES.md`, `13_BACKTEST_SERVICE.md`, `14_LIVE_TRADING_SERVICE.md`, `15_EVENT_DRIVEN_STRATEGY_ENGINE.md`, `5A_STRATEGY_FACTORY.md`, `07B_VENUE_INTERFACE_FACTORY.md`, `05B_BASE_STRATEGY_MANAGER.md`) to implement config-driven, mode-agnostic architecture per AGENT_REFACTOR_PROMPT_MODE_AGNOSTIC.md.

## Key Decisions

1. **Config Changes**: Document needed config fields in specs, note as "pending YAML updates" - do NOT modify YAML files
2. **Strategy Manager**: Keep both patterns - config-driven parameters + inheritance for mode-specific logic
3. **Factory Implementation**: Add complete factory code with all 7 modes mapped

## Files to Update (8 specs)

### Group 1: Strategy Components (3 files)

- `docs/specs/05_STRATEGY_MANAGER.md` - Add config-driven + inheritance pattern
- `docs/specs/5A_STRATEGY_FACTORY.md` - Complete factory with 7 mode mappings
- `docs/specs/05B_BASE_STRATEGY_MANAGER.md` - Abstract base class + 3 concrete examples

### Group 2: Execution Components (1 file)

- `docs/specs/07A_EXECUTION_INTERFACES.md` - Clarify mode-agnostic venue execution

### Group 3: Services (2 files)

- `docs/specs/13_BACKTEST_SERVICE.md` - Factory-based initialization pattern
- `docs/specs/14_LIVE_TRADING_SERVICE.md` - Factory-based initialization pattern

### Group 4: Engine & Factory (2 files)

- `docs/specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md` - Add factory orchestration note
- `docs/specs/07B_VENUE_INTERFACE_FACTORY.md` - Complete factory with venue mappings

## Implementation Approach

### Phase 1: Update Strategy Manager Specs (3 files)

**Files**: `05_STRATEGY_MANAGER.md`, `05B_BASE_STRATEGY_MANAGER.md`, `5A_STRATEGY_FACTORY.md`

#### For `05_STRATEGY_MANAGER.md`:

1. Update "Config-Driven Behavior" section:

   - Show config-driven parameters (strategy_type, actions, rebalancing_triggers, position_calculation)
   - Keep inheritance-based architecture section
   - Add table showing both patterns work together

2. Add complete "MODE-AGNOSTIC IMPLEMENTATION EXAMPLE" section:

   - BaseStrategyManager abstract class code
   - Config extraction in **init**
   - Abstract methods (calculate_target_position, validate_action, get_rebalancing_condition)

3. Add 3 concrete strategy examples:

   - PureLendingStrategy (simplest)
   - BTCBasisStrategy (medium complexity)
   - USDTMarketNeutralStrategy (most complex)

4. Document needed config fields:

   - Add note: "**Config Requirements** (pending YAML updates): These config fields are needed but not yet in mode YAML files"
   - List new fields needed for component_config.strategy_manager

#### For `05B_BASE_STRATEGY_MANAGER.md`:

1. Expand "Abstract Methods" section with full signatures
2. Add complete BaseStrategyManager class code:

   - Full **init** with config extraction
   - Config validation method
   - Wrapper action methods
   - Abstract method definitions

3. Add 3 concrete implementation examples:

   - PureLendingStrategy with config-driven parameters
   - BTCBasisStrategy with multi-venue logic
   - ETHLeveragedStrategy with LTV management

4. Add "Config-Driven Parameters" section showing how inheritance + config work together

#### For `5A_STRATEGY_FACTORY.md`:

1. Replace minimal factory with complete implementation:

   - Add STRATEGY_MAP with all 7 modes mapped
   - Complete create_strategy() method
   - validate_mode() method
   - get_available_modes() method

2. Add dependency injection pattern code
3. Add integration example with EventDrivenStrategyEngine
4. Document needed config validation

### Phase 2: Update Execution Interface Specs (2 files)

**Files**: `07A_EXECUTION_INTERFACES.md`, `07B_VENUE_INTERFACE_FACTORY.md`

#### For `07A_EXECUTION_INTERFACES.md`:

1. Strengthen "Config-Driven Behavior" section:

   - Emphasize mode-agnostic execution
   - Add table showing same execution logic for all modes

2. Clarify "Key Principle" section:

   - Execution Interfaces are purely execution
   - NO mode-specific logic
   - NO strategy-specific execution behavior

3. Update examples to show venue-specific, not mode-specific

#### For `07B_VENUE_INTERFACE_FACTORY.md`:

1. Add complete INTERFACE_MAP with all venues:

   - CEX: binance, bybit, okx, hyperliquid
   - DEX: uniswap, curve
   - OnChain: aave, morpho, lido, etherfi, instadapp

2. Add complete factory methods:

   - create_all_interfaces()
   - create_interface()
   - set_interface_dependencies()
   - validate_venue()
   - get_available_venues()

3. Add integration example with EventDrivenStrategyEngine

### Phase 3: Update Service Specs (2 files)

**Files**: `13_BACKTEST_SERVICE.md`, `14_LIVE_TRADING_SERVICE.md`

#### For both service specs:

1. Update "Config-Driven Behavior" section:

   - Show factory-based initialization
   - Add DataProviderFactory usage
   - Add ComponentFactory usage

2. Add complete initialization sequence code:

   - Load config for mode
   - Apply config_overrides
   - Validate config using ConfigValidator
   - Create DataProvider using DataProviderFactory
   - Validate data_provider compatibility
   - Create components using ComponentFactory

3. Add config override support documentation
4. Document needed config validation

### Phase 4: Update Engine Spec (1 file)

**Files**: `15_EVENT_DRIVEN_STRATEGY_ENGINE.md`

#### For `15_EVENT_DRIVEN_STRATEGY_ENGINE.md`:

1. Add "Factory Integration" section:

   - Show how engine uses factories
   - DataProviderFactory for data
   - StrategyFactory for strategies
   - ExecutionInterfaceFactory for interfaces
   - ComponentFactory for other components

2. Update initialization sequence to show factory usage
3. Add note that orchestration is unchanged - only initialization uses factories

## Standard Updates for All Specs

### For Each Spec File:

1. **Verify 19-section structure** matches COMPONENT_SPEC_TEMPLATE.md
2. **Update "Configuration Parameters" section**:

   - Show component_config.[component_name] structure
   - Add table with all 7 modes
   - Note pending YAML updates where needed

3. **Add/Update "MODE-AGNOSTIC IMPLEMENTATION EXAMPLE" section**:

   - Complete class code from CODE_STRUCTURE_PATTERNS.md
   - Config validation
   - Graceful data handling
   - ComponentFactory pattern

4. **Cross-reference updates**:

   - Link to 19_CONFIGURATION.md
   - Link to CODE_STRUCTURE_PATTERNS.md
   - Link to MODE_AGNOSTIC_ARCHITECTURE_GUIDE.md

5. **Check against TASK_DOCS_CONFLICT_ANALYSIS_REPORT.md**:

   - Ensure no documented violations
   - Align with architectural principles

## Config Documentation Pattern

For any new config fields identified:

```markdown
### **Config Requirements** 

**Status**: ⚠️ Pending YAML Updates

The following config fields are needed in `component_config.[component_name]` but not yet present in mode YAML files:

| Field | Type | Description | Required For |
|-------|------|-------------|--------------|
| `new_field_1` | [Type] | [Description] | All modes |
| `new_field_2` | [Type] | [Description] | Modes with X |

**Action Required**: Add these fields to mode YAML files in `configs/modes/*.yaml`
```

## Validation Checklist

After completing all updates, verify:

- [ ] All 8 specs follow 19-section structure
- [ ] Config-driven architecture documented in each spec
- [ ] Complete code structures added (not minimal examples)
- [ ] All 7 modes referenced in tables
- [ ] Factory patterns complete with all mode/venue mappings
- [ ] Config requirements documented (marked "pending YAML")
- [ ] Cross-references valid
- [ ] No conflicts with TASK_DOCS_CONFLICT_ANALYSIS_REPORT.md
- [ ] Inheritance + config-driven patterns work together (Strategy Manager)
- [ ] Graceful data handling shown in examples

## Success Criteria

1. **Architectural Alignment**: All specs align with MODE_AGNOSTIC_ARCHITECTURE_GUIDE.md
2. **Complete Implementation**: Factory code complete with all 7 modes/venues mapped
3. **Config Documentation**: All needed config fields documented, marked as pending
4. **Code Structure**: Complete code from CODE_STRUCTURE_PATTERNS.md, not minimal examples
5. **Dual Pattern**: Strategy Manager shows both config-driven + inheritance working together
6. **Cross-References**: All links to 19_CONFIGURATION.md, CODE_STRUCTURE_PATTERNS.md valid
7. **No Hallucination**: All content traceable to canonical sources