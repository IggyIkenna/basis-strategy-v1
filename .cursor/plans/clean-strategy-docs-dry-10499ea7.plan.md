<!-- 10499ea7-8379-4ca5-bdbd-3a387da9d9c5 79eb03a7-0123-4596-bcb5-923a957b6364 -->
# Clean Up Strategy Documentation - DRY & Terminology Updates

## Overview

Remove all duplicate content from strategy specs, perform global terminology updates using command-line tools, and customize execution flows for each strategy's unique model while preserving all technical details.

## Phase 1: Global Terminology Updates (Command Line)

Use `sed` for bulk replacements across all documentation files to save context tokens.

### 1.1 Update VenueManager → ExecutionManager

```bash
# Strategy specs
find docs/specs/strategies -name "*.md" -exec sed -i '' 's/VenueManager/ExecutionManager/g' {} +
find docs/specs/strategies -name "*.md" -exec sed -i '' 's/venue_manager/execution_manager/g' {} +

# Component specs
find docs/specs -maxdepth 1 -name "*.md" -exec sed -i '' 's/VenueManager/ExecutionManager/g' {} +
find docs/specs -maxdepth 1 -name "*.md" -exec sed -i '' 's/venue_manager/execution_manager/g' {} +

# Root docs
find docs -maxdepth 1 -name "*.md" -exec sed -i '' 's/VenueManager/ExecutionManager/g' {} +
find docs -maxdepth 1 -name "*.md" -exec sed -i '' 's/venue_manager/execution_manager/g' {} +
```

### 1.2 Update Trade → ExecutionHandshake

```bash
# Replace Trade class/model references
find docs/specs -name "*.md" -exec sed -i '' 's/class Trade(/class ExecutionHandshake(/g' {} +
find docs/specs -name "*.md" -exec sed -i '' 's/return Trade/return ExecutionHandshake/g' {} +
find docs/specs -name "*.md" -exec sed -i '' 's/Trade,/ExecutionHandshake,/g' {} +
find docs/specs -name "*.md" -exec sed -i '' 's/Trade object/ExecutionHandshake object/g' {} +
find docs/specs -name "*.md" -exec sed -i '' 's/\[Trade\]/[ExecutionHandshake]/g' {} +
find docs/specs -name "*.md" -exec sed -i '' 's/List\[Trade\]/List[ExecutionHandshake]/g' {} +
```

### 1.3 Verify Changes

```bash
# Count remaining occurrences (should be 0 or minimal)
grep -r "VenueManager\|venue_manager" docs/specs --count
grep -r "class Trade\|return Trade" docs/specs --count
```

## Phase 2: Remove Duplicate Sections (Manual - 9 Strategy Specs)

Each strategy spec has duplicate sections that need consolidation:

### 2.1 Pure Lending Strategy (01_PURE_LENDING_STRATEGY.md)

**Duplicates to remove:**

- Lines 352-387: Remove duplicate "Responsibilities" section (keep lines 35-43)
- Lines 362-369: Remove duplicate "State" section (keep lines 44-52)
- Lines 371-377: Remove duplicate "Component References" section (keep lines 54-61)
- Lines 379-387: Remove duplicate "Environment Variables" section (keep lines 63-70)
- Lines 389-396: Remove duplicate "Data Provider Queries" section (keep lines 147-155)

**Keep:** Lines 1-351 (original content) + Lines 723-783 (new Expected Deltas + Execution Flow sections)

### 2.2 BTC Basis Strategy (02_BTC_BASIS_STRATEGY.md)

**Pattern:** Same duplicate pattern as Pure Lending

- Remove duplicate Responsibilities, State, Component References, Environment Variables sections
- Keep original sections + new Expected Deltas/Execution Flow

### 2.3 ETH Basis Strategy (03_ETH_BASIS_STRATEGY.md)

**Pattern:** Same duplicate pattern

- Consolidate duplicate sections
- Preserve strategy-specific execution patterns

### 2.4 ETH Staking Only Strategy (04_ETH_STAKING_ONLY_STRATEGY.md)

**Pattern:** Same duplicate pattern

- Focus on staking-specific execution model
- Remove generic execution flow if not applicable

### 2.5 ETH Leveraged Strategy (05_ETH_LEVERAGED_STRATEGY.md)

**Pattern:** Same duplicate pattern (seen in file review)

- Lines 276-314: Remove duplicate Responsibilities/State/Component References/Environment Variables
- Keep atomic flash loan execution details unique to this strategy

### 2.6-2.9 Remaining Strategies

Apply same pattern to:

- 06_USDT_MARKET_NEUTRAL_NO_LEVERAGE_STRATEGY.md
- 07_USDT_MARKET_NEUTRAL_STRATEGY.md
- 08_ML_BTC_DIRECTIONAL_STRATEGY.md
- 09_ML_USDT_DIRECTIONAL_STRATEGY.md

## Phase 3: Customize Execution Flow Sections

For each strategy, customize the generic "Execution Flow" section to reflect its unique model from MODES.md:

### 3.1 Pure Lending Execution Flow

```markdown
## Execution Flow

Pure Lending uses simple sequential execution:

1. Strategy Manager calculates target AAVE position based on equity
2. Generates supply/withdraw Orders with expected_deltas
3. ExecutionManager processes order
4. AAVE venue interface executes supply/withdraw
5. Returns ExecutionHandshake with actual_deltas (aToken amounts)
6. PositionUpdateHandler reconciles expected vs actual
7. Position Monitor updates positions

**No atomic operations needed** - single venue (AAVE) operations only.
```

### 3.2 Basis Trading Execution Flow (BTC/ETH)

```markdown
## Execution Flow

Basis strategies use coordinated spot + perp execution:

1. Strategy Manager calculates delta-neutral position
2. Generates paired Orders: spot buy + perp short
3. ExecutionManager processes sequentially (not atomic)
4. Binance/Bybit/OKX interfaces execute trades
5. Returns ExecutionHandshakes with fills
6. PositionUpdateHandler reconciles both legs
7. Risk Monitor validates delta neutrality

**Sequential but coordinated** - spot and perp must both succeed for delta neutrality.
```

### 3.3 ETH Staking Only Execution Flow

```markdown
## Execution Flow

ETH Staking uses simple staking operations:

1. Strategy Manager calculates target LST allocation
2. Generates stake/unstake Orders
3. ExecutionManager processes order
4. Lido/EtherFi interface executes stake/unstake
5. Returns ExecutionHandshake with LST amounts
6. PositionUpdateHandler reconciles conversion rates
7. Position Monitor tracks LST positions

**Simple staking flow** - no leverage, no hedging, single venue operations.
```

### 3.4 ETH Leveraged Execution Flow

```markdown
## Execution Flow

ETH Leveraged uses atomic flash loan execution via Instadapp:

1. Strategy Manager calculates leveraged staking target
2. Generates atomic Order with flash loan steps
3. ExecutionManager routes to Instadapp
4. Atomic execution: flash borrow → stake → supply to AAVE → borrow → repay flash
5. Returns ExecutionHandshake with final LST + debt positions
6. PositionUpdateHandler reconciles entire atomic operation
7. Risk Monitor validates health factor

**Atomic operations required** - multi-step flash loan for leverage efficiency.
```

### 3.5 Market Neutral Execution Flow

```markdown
## Execution Flow

Market Neutral uses split allocation with coordination:

1. Strategy Manager splits equity (stake_allocation_percentage)
2. Generates Orders: ETH staking + perp hedges
3. ExecutionManager processes sequentially
4. LST venue + CEX interfaces execute
5. Returns ExecutionHandshakes for both legs
6. PositionUpdateHandler reconciles staking + hedges
7. Risk Monitor validates delta neutrality

**Split allocation** - coordinates on-chain staking with CEX hedging.
```

## Phase 4: Update Last Reviewed Dates

Update all strategy specs with current date (October 17, 2025):

```bash
find docs/specs/strategies -name "*.md" -exec sed -i '' 's/Last Reviewed\*\*: October [0-9]*, 2025/Last Reviewed**: October 17, 2025/g' {} +
```

## Phase 5: Validation

### 5.1 Check for Remaining Issues

```bash
# No duplicate section headers
grep -n "^## Responsibilities$" docs/specs/strategies/*.md | head -20
grep -n "^## State$" docs/specs/strategies/*.md | head -20

# No old terminology
grep -r "VenueManager\|venue_manager" docs/specs/strategies
grep -r "class Trade\|return Trade" docs/specs/strategies

# Verify Expected Deltas sections exist
grep -n "^## Expected Deltas Calculation$" docs/specs/strategies/*.md
```

### 5.2 Manual Review Checklist

- [ ] Each strategy has ONE Responsibilities section
- [ ] Each strategy has ONE State section
- [ ] Each strategy has ONE Component References section
- [ ] Each strategy has ONE Environment Variables section
- [ ] Execution Flow reflects strategy-specific model from MODES.md
- [ ] All technical details preserved (no information loss)
- [ ] Expected Deltas Calculation section present with strategy-specific examples
- [ ] All VenueManager → ExecutionManager
- [ ] All Trade → ExecutionHandshake
- [ ] Last Reviewed date is October 17, 2025

## Implementation Order

1. ✅ Phase 1: Run all sed commands for terminology updates (fastest, bulk changes)
2. ✅ Phase 2: Manually remove duplicate sections from all 9 strategy specs (preserves technical detail)
3. ✅ Phase 3: Customize Execution Flow sections per strategy (aligns with MODES.md)
4. ✅ Phase 4: Update dates
5. ✅ Phase 5: Validation and verification

## Success Criteria

1. **DRY Principle**: Zero duplicate sections within each strategy spec
2. **Terminology**: 100% VenueManager→ExecutionManager, Trade→ExecutionHandshake
3. **Strategy-Specific**: Each Execution Flow reflects unique model from MODES.md
4. **Technical Completeness**: All original technical details preserved
5. **Consistency**: All dates updated, all formatting consistent

### To-dos

- [ ] Run sed commands for global VenueManager→ExecutionManager and Trade→ExecutionHandshake replacements
- [ ] Remove duplicate sections (Responsibilities, State, Component References, Environment Variables) from all 9 strategy specs
- [ ] Customize Execution Flow sections for each strategy's unique model per MODES.md
- [ ] Update Last Reviewed dates to October 17, 2025 across all strategy specs
- [ ] Run validation checks and manual review checklist