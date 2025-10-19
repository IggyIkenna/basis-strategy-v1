# Agent Quick Reference Card

**For agents completing the 26 cursor tasks**

## Purpose

This document provides a quick reference guide for AI agents working on the Basis Strategy project. It contains critical warnings, key file locations, and essential patterns that agents must follow to maintain architectural integrity and avoid common pitfalls.

## 📚 **Canonical Sources**

**This document aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles including config-driven architecture
- **Target Structure**: [TARGET_REPOSITORY_STRUCTURE.md](TARGET_REPOSITORY_STRUCTURE.md) - Repository organization standards
- **Quality Gates**: [QUALITY_GATES.md](QUALITY_GATES.md) - Validation standards

## 🚨 Critical Warnings

### ❌ DO NOT:
- Recreate deleted files (24 files were removed for architectural reasons)
- Use `from ..config import` (use `from ...infrastructure.config import`)
- Add `async` to internal component methods
- Create duplicate components (use centralized versions)

### ✅ DO:
- Use `StrategyFactory` for all strategy creation
- Follow mode-agnostic patterns (no hardcoded mode checks)
- Use direct config access (fail-fast pattern)
- Reference `TARGET_REPOSITORY_STRUCTURE.md` before making changes

## 📁 Key File Locations

### Config (Single Source of Truth)
```python
# ✅ CORRECT
from ...infrastructure.config.config_manager import get_config_manager
from ...infrastructure.config.models import ConfigSchema

# ❌ WRONG - These are deleted
from ..config import load_and_validate_config
```

### Strategies (Factory Pattern)
```python
# ✅ CORRECT
from ..strategies.strategy_factory import StrategyFactory
from ..strategies.btc_basis_strategy import BTCBasisStrategy

# All 7 strategies must be registered in StrategyFactory.STRATEGY_MAP
```

### Components (Centralized)
```python
# ✅ CORRECT
from ..strategies.components.risk_monitor import RiskMonitor
from ..utilities.utility_manager import UtilityManager
```

## 🗂️ Deleted Files (DO NOT RECREATE)

```
❌ core/config/ (3 files) - Use infrastructure/config instead
❌ core/rebalancing/risk_monitor.py - Use strategies/components/risk_monitor.py
❌ core/rebalancing/transfer_manager.py - Architectural violation
❌ core/strategies/components/ (13 files) - Duplicates removed
```

## 🏗️ Architecture Patterns

### Mode-Agnostic Components
```python
# ✅ CORRECT - Use config parameters
def calculate_positions(self, config):
    asset = config['asset']
    share_class = config['share_class']

# ❌ WRONG - Mode-specific if statements
def calculate_positions(self, mode):
    if mode == 'backtest':
        # backtest logic
    elif mode == 'live':
        # live logic
```

### Fail-Fast Configuration
```python
# ✅ CORRECT - Direct access, fail fast
max_retries = config['max_retry_attempts']

# ❌ WRONG - Silent fallbacks
max_retries = config.get('max_retry_attempts', 3)
```

### Synchronous Internal Methods
```python
# ✅ CORRECT - Synchronous internal methods
def update_positions(self, timestamp):
    # synchronous logic

# ❌ WRONG - Async internal methods
async def update_positions(self, timestamp):
    # async logic
```

## 🧪 Testing Checklist

Before completing any task:
- [ ] All imports use correct paths
- [ ] No deleted files are being recreated
- [ ] Strategy factory includes all 7 strategies
- [ ] Components are mode-agnostic
- [ ] No async in internal methods
- [ ] Fail-fast configuration is used

## 📋 Current Status

### ✅ Completed (Phases 1-6)
- 24 duplicate files deleted
- 8 new components created
- All imports fixed
- Strategy factory with 7 strategies
- Services updated

### 🔄 Remaining (Phase 7)
- Singleton pattern enforcement
- Quality gate updates
- Unit test execution
- Architecture compliance verification

## 🔗 Reference Documents

- **Full Structure**: [TARGET_REPOSITORY_STRUCTURE.md](TARGET_REPOSITORY_STRUCTURE.md)
- **Architecture**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md)
- **Strategies**: [MODES.md](MODES.md)
- **Components**: [specs/](specs/)

---

**Remember**: Always reference the full TARGET_REPOSITORY_STRUCTURE.md before making changes!


