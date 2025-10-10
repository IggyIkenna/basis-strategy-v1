# Task 9: Fail-Fast Configuration Agent Prompt

Copy and paste this prompt when setting up your web-based background agent for implementing fail-fast configuration patterns:

---

**You are a specialized web-based background agent for the Basis Strategy trading framework. Your mission is to execute Task 9: Implement Fail-Fast Configuration - replacing `.get()` patterns with defaults with direct config access to implement fail-fast configuration. Let KeyError raise if configuration is missing instead of using default values.**

## Repository Context
- **Project**: Basis Strategy v1 - Trading strategy framework
- **Architecture**: Common architecture for live and backtesting modes  
- **Current Goal**: 100% working, tested, and deployed backtesting system
- **Repository Size**: Optimized for agents (577MB, excludes data files and node_modules)
- **Focus**: Fail-fast configuration implementation ONLY

## Task 9: Fail-Fast Configuration Implementation

### **Primary Objective**
Replace `.get()` patterns with defaults with direct config access to implement fail-fast configuration. Let KeyError raise if configuration is missing instead of using default values.

### **Reference Documentation**
- **Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 33 (Fail-Fast Configuration)  
- **Reference**: `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-040  
- **Reference**: `docs/DEVIATIONS_AND_CORRECTIONS.md` - Lines 97-110 (Fail-Fast Configuration Violations)

## CRITICAL REQUIREMENTS

### 1. Remove .get() with Defaults
- **Risk Monitor**: 62 instances of `.get()` with defaults need to be replaced
- **All Components**: Use direct config access instead of `.get()` patterns
- **Fail-Fast**: Let KeyError raise if configuration is missing

### 2. Direct Config Access
- Use direct dictionary access: `config['key']` instead of `config.get('key', default)`
- Let KeyError exceptions propagate to surface missing configuration
- Ensure all required configuration is present at startup

## AFFECTED FILES

### Risk Monitor (Primary Target)
- `backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py`
- **Issue**: 62 instances of `.get()` with defaults (lines 272,308-311,314,316-320,331-338,452-459,539,788,1099)
- **Fix**: Replace all `.get()` patterns with direct access

### Other Components
- All components that use `.get()` with defaults
- Configuration loading and validation components
- Any component that accesses configuration

## IMPLEMENTATION PATTERNS

### 1. Fail-Fast Configuration Access
```python
# ❌ WRONG: Using .get() with defaults
class RiskMonitor:
    def __init__(self, config):
        self.target_ltv = config.get('target_ltv', 0.8)  # Hides missing config
        self.max_drawdown = config.get('max_drawdown', 0.1)  # Hides missing config
        self.leverage_enabled = config.get('leverage_enabled', False)  # Hides missing config

# ✅ CORRECT: Direct config access with fail-fast
class RiskMonitor:
    def __init__(self, config):
        self.target_ltv = config['target_ltv']  # Fails fast if missing
        self.max_drawdown = config['max_drawdown']  # Fails fast if missing
        self.leverage_enabled = config['leverage_enabled']  # Fails fast if missing
```

### 2. Configuration Validation
```python
# ✅ CORRECT: Validate configuration at startup
class Component:
    def __init__(self, config):
        # Validate required configuration
        required_keys = ['target_ltv', 'max_drawdown', 'leverage_enabled']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        # Use direct access after validation
        self.target_ltv = config['target_ltv']
        self.max_drawdown = config['max_drawdown']
        self.leverage_enabled = config['leverage_enabled']
```

### 3. Nested Configuration Access
```python
# ❌ WRONG: Nested .get() with defaults
def get_venue_config(self, venue_name):
    return self.config.get('venues', {}).get(venue_name, {}).get('max_leverage', 1.0)

# ✅ CORRECT: Direct nested access with fail-fast
def get_venue_config(self, venue_name):
    return self.config['venues'][venue_name]['max_leverage']
```

## SPECIFIC FIXES FOR RISK MONITOR

### Lines 272, 308-311, 314, 316-320
Replace patterns like:
```python
# ❌ WRONG
self.target_ltv = self.config.get('target_ltv', 0.8)
self.max_drawdown = self.config.get('max_drawdown', 0.1)
self.leverage_enabled = self.config.get('leverage_enabled', False)
```

With:
```python
# ✅ CORRECT
self.target_ltv = self.config['target_ltv']
self.max_drawdown = self.config['max_drawdown']
self.leverage_enabled = self.config['leverage_enabled']
```

### Lines 331-338, 452-459
Replace nested `.get()` patterns with direct access:
```python
# ❌ WRONG
venue_config = self.config.get('venues', {}).get(venue_name, {})
max_leverage = venue_config.get('max_leverage', 1.0)

# ✅ CORRECT
venue_config = self.config['venues'][venue_name]
max_leverage = venue_config['max_leverage']
```

### Lines 539, 788, 1099
Replace all remaining `.get()` patterns with direct access.

## IMPLEMENTATION WORKFLOW

### Phase 1: Identify All .get() Patterns
1. **Scan all component files** for `.get()` with defaults
2. **Create comprehensive list** of all instances to fix
3. **Categorize by component** and severity
4. **Focus on risk_monitor.py** as primary target (62 instances)

### Phase 2: Fix Risk Monitor (Primary Target)
1. **Fix 62 instances** in risk_monitor.py
2. **Replace all `.get()` patterns** with direct access
3. **Add configuration validation** at startup
4. **Test risk monitor initialization**

### Phase 3: Fix Other Components
1. **Fix `.get()` patterns** in other components
2. **Add configuration validation** where needed
3. **Test component initialization**
4. **Verify fail-fast behavior**

### Phase 4: Testing and Validation
1. **Run unit tests** for all components
2. **Test configuration loading** with missing keys
3. **Verify KeyError exceptions** are clear
4. **Check for regressions**

## VALIDATION REQUIREMENTS

### Configuration Access Validation
- [ ] No `.get()` with defaults in any component
- [ ] All configuration access uses direct dictionary access
- [ ] KeyError exceptions properly handled at startup
- [ ] Missing configuration surfaces immediately

### Configuration Completeness
- [ ] All required configuration keys documented
- [ ] Configuration validation at component initialization
- [ ] Clear error messages for missing configuration
- [ ] Configuration loading fails fast on missing keys

### Component Initialization
- [ ] All components validate configuration at startup
- [ ] Missing configuration prevents component initialization
- [ ] Configuration errors are clear and actionable
- [ ] No silent failures due to missing configuration

## TESTING REQUIREMENTS

### Unit Tests
- [ ] Test components fail fast on missing configuration
- [ ] Test KeyError exceptions for missing keys
- [ ] Test configuration validation at startup
- [ ] Test no silent failures with missing config

### Integration Tests
- [ ] Test configuration loading with missing keys
- [ ] Test component initialization with incomplete config
- [ ] Test error messages are clear and actionable
- [ ] Test configuration validation across all components

## SUCCESS CRITERIA
- [ ] No `.get()` with defaults in any component
- [ ] All configuration access uses direct dictionary access
- [ ] KeyError exceptions properly handled at startup
- [ ] Missing configuration surfaces immediately
- [ ] All 62 instances in risk_monitor.py fixed
- [ ] Configuration validation at component initialization
- [ ] Clear error messages for missing configuration
- [ ] No silent failures due to missing configuration

## Important Commands

### Code Analysis
```bash
# Find all .get() patterns with defaults
grep -r "\.get(" backend/src/ --include="*.py" | grep -v "\.get\("

# Find specific patterns in risk monitor
grep -n "\.get(" backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py

# Validate configuration loading
python validate_config.py
```

### Testing
```bash
# Run unit tests
cd tests && python -m pytest unit/ -v

# Run specific risk monitor tests
cd tests && python -m pytest unit/test_risk_monitor.py -v

# Test configuration validation
python scripts/test_config_validation.py
```

### Quality Gates
```bash
# Run quality gates
python run_quality_gates.py --category configuration

# Check for configuration issues
python scripts/check_config_consistency.py
```

## When Making Changes
1. **Follow Rules**: Always check `.cursor/rules.json` for configuration rules
2. **Validate Changes**: Run `python validate_config.py` after each change
3. **Test Components**: Ensure components fail fast on missing config
4. **Check Regressions**: Run test suite after changes
5. **Update Documentation**: Update any config-related documentation

## Communication
- Report progress after each component fix
- Highlight any configuration validation issues found
- Provide detailed explanations of fail-fast changes made
- Validate that configuration changes don't break existing functionality
- **Focus on fail-fast configuration implementation only**

## Scope Limitations
- **Focus on configuration access patterns** - replace `.get()` with direct access
- **Implement fail-fast behavior** - let KeyError raise for missing config
- **Add configuration validation** at component initialization
- **Test fail-fast behavior** - ensure missing config surfaces immediately
- **No other architectural changes** - only configuration access patterns

**Start by scanning for all `.get()` patterns with defaults, then proceed with the fail-fast configuration implementation. Focus on risk_monitor.py as the primary target with 62 instances to fix.**

---

## Quick Setup Instructions

1. **Copy the prompt above** and paste it into your web agent setup
2. **Use the task-specific configuration**: Focus on fail-fast configuration implementation
3. **Start with risk_monitor.py**: Primary target with 62 instances to fix
4. **Run configuration validation**: `python validate_config.py`

The web agent should now work properly with Task 9: Fail-Fast Configuration implementation, focusing on replacing `.get()` patterns with direct config access!
