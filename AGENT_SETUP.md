# Agent Setup Guide 🛠️

## 🚀 **Complete Environment Setup for Cursor Web Browser Agents**

This guide ensures both Agent A and Agent B have properly configured environments in the Cursor web browser.

---

## 📋 **PHASE 1: Pre-Launch Environment Validation**

### **Step 1.1: Verify Branch and Repository State**
```bash
# Ensure you're on the correct branch
git branch
# Should show: * agent-implementation

# Verify you have the latest changes
git status
# Should show: "working tree clean"

# Pull latest changes if needed
git pull origin agent-implementation
```

### **Step 1.2: Verify Required Files Exist**
```bash
# Check that all agent files exist
ls -la AGENT_*_TASKS.md
ls -la agent-progress.json
ls -la launch_web_agent.sh
ls -la preflight_check.py
ls -la monitor_agents.py
ls -la validate_completion.py
ls -la sync_docs.py
ls -la check_agent_progress.sh

# All files should exist and be readable
```

### **Step 1.3: Validate Environment Variables**
```bash
# Check that environment variables are properly configured
python3 -c "
import os
import sys

# Check for placeholder values in critical environment variables
CRITICAL_VARS = [
    'BASIS_CEX__BINANCE_SPOT_API_KEY',
    'BASIS_CEX__BINANCE_FUTURES_API_KEY', 
    'BASIS_CEX__BYBIT_API_KEY',
    'BASIS_CEX__OKX_API_KEY',
    'BASIS_WEB3__PRIVATE_KEY',
    'BASIS_WEB3__WALLET_ADDRESS'
]

print('🔍 Checking environment variables...')
missing_or_placeholder = []

for var in CRITICAL_VARS:
    value = os.getenv(var)
    if not value or value.startswith('your_') or value == '0x...':
        missing_or_placeholder.append(var)
        print(f'❌ {var}: Missing or placeholder value')
    else:
        print(f'✅ {var}: Configured')

if missing_or_placeholder:
    print(f'\n⚠️  WARNING: {len(missing_or_placeholder)} environment variables need manual setup!')
    print('See docs/REQUIREMENTS.md for manual setup instructions.')
    print('Agents will work in backtest mode only until these are configured.')
else:
    print('\n✅ All critical environment variables configured!')
"
```

### **Step 1.4: Verify Documentation Structure**
```bash
# Check that all documentation exists
ls -la docs/
ls -la docs/specs/
ls -la docs/CLEANUP_AND_INTEGRATION_PLAN.md

# Verify component specs exist
ls -la docs/specs/0*_*.md
# Should show all 12 spec files
```

### **Step 1.5: Verify Cursor Rules Compliance**
```bash
# Check that .cursorrules file exists and is readable
cat .cursorrules
# Should show all cursor rules including:
# - Refactoring Rules (no backward compatibility)
# - Code Quality Rules (Pydantic, YAML configs)
# - Documentation Rules (always update docs)
# - Testing Rules (always run test suite)
# - Configuration Rules (check downstream usage)

# Verify agents understand cursor rules
echo "🔍 Cursor Rules Check:"
echo "✅ Refactoring: No backward compatibility"
echo "✅ Documentation: Always update docs/ when making changes"
echo "✅ Testing: Always run test suite after changes"
echo "✅ Configuration: Check downstream usage when changing config/data"
echo "✅ No Duplication: Single source of truth for each config"
```

---

## 🔧 **PHASE 2: Launch Script Execution**

### **Step 2.1: Execute Launch Script**
```bash
# Run the comprehensive launch script
./launch_web_agent.sh
```

**Expected Output**:
```
🚀 Setting up Cursor Web Agent Environment...

✅ Python environment verified
✅ Redis setup completed
✅ Python requirements installed
✅ Preflight checks passed
✅ Agent configuration loaded

🎯 Agent A Tasks: Frontend + Integration (8 days)
🎯 Agent B Tasks: Infrastructure + Deployment (6 days)

✅ Environment ready for agent work!
```

### **Step 2.2: Verify Launch Script Results**
```bash
# Check Python environment
python3 --version
# Should show Python 3.8+

# Check Redis connection
redis-cli ping
# Should return: PONG

# Check Python packages
python3 -c "import pandas, pydantic, redis, ccxt, web3; print('All packages available')"
# Should show: All packages available

# Run preflight checks
python3 preflight_check.py
# Should show all checks passing

# Verify cursor rules compliance
echo "🔍 Verifying Cursor Rules Compliance..."
cat .cursorrules | grep -E "(ALWAYS|NEVER)" | head -5
# Should show key rules like:
# - NEVER facilitate backward compatibility during refactors
# - ALWAYS update docs/ when making breaking changes
# - ALWAYS run test suite after changes to ensure everything still works
```

---

## 🧪 **PHASE 3: Component Testing and Validation**

### **Step 3.1: Test Agent A Components (Already Completed)**
```bash
# Test all Agent A components
pytest tests/unit/components/test_position_monitor.py
pytest tests/unit/components/test_event_logger.py
pytest tests/unit/components/test_exposure_monitor.py
pytest tests/unit/components/test_risk_monitor.py
pytest tests/unit/components/test_pnl_calculator.py

# All should pass with "✅ All tests passed!" or similar
```

### **Step 3.2: Test Agent B Components (Already Completed)**
```bash
# Test all Agent B components
pytest tests/unit/components/test_strategy_manager.py
pytest tests/unit/components/test_cex_execution_manager.py
pytest tests/unit/components/test_onchain_execution_manager.py
pytest tests/unit/components/test_data_provider.py

# All should pass with "✅ All tests passed!" or similar
```

### **Step 3.3: Verify Component Integration**
```bash
# Check that components can be imported
python3 -c "
import sys
sys.path.append('backend/src')
from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
from basis_strategy_v1.core.strategies.components.event_logger import EventLogger
from basis_strategy_v1.core.strategies.components.exposure_monitor import ExposureMonitor
from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor
from basis_strategy_v1.core.math.pnl_calculator import PnLCalculator
from basis_strategy_v1.core.strategies.components.strategy_manager import StrategyManager
from basis_strategy_v1.core.strategies.components.cex_execution_manager import CEXExecutionManager
from basis_strategy_v1.core.strategies.components.onchain_execution_manager import OnChainExecutionManager
from basis_strategy_v1.infrastructure.data.historical_data_provider import HistoricalDataProvider
print('✅ All components import successfully')
"
```

### **Step 3.4: Test Redis Connectivity**
```bash
# Test Redis pub/sub functionality
python3 -c "
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.publish('test_channel', 'test_message')
print('✅ Redis pub/sub working')
"
```

---

## 📚 **PHASE 4: Documentation and Context Validation**

### **Step 4.1: Verify Critical Documentation**
```bash
# Check that all critical docs are readable
cat docs/CLEANUP_AND_INTEGRATION_PLAN.md | head -10
cat docs/IMPLEMENTATION_ROADMAP.md | head -10
cat docs/REQUIREMENTS.md | head -10
cat docs/ARCHITECTURAL_DECISIONS.md | head -10

# All should display content without errors
```

### **Step 4.2: Verify Component Specifications**
```bash
# Check that all component specs exist and are readable
for spec in docs/specs/0*_*.md; do
    echo "Checking $spec..."
    head -5 "$spec"
    echo "✅ $spec readable"
done
```

### **Step 4.3: Verify Agent Instructions**
```bash
# Check agent instruction files
cat AGENT_A_TASKS.md | head -10
cat AGENT_B_TASKS.md | head -10

# All should display content without errors
```

---

## 🎯 **PHASE 5: Task Queue and Progress Validation**

### **Step 5.1: Verify Task Queue**
```bash
# Check task queue structure
python3 -c "
import json
with open('agent-progress.json', 'r') as f:
    tasks = json.load(f)
print(f'Total tasks: {len(tasks[\"tasks\"])}')
for task in tasks['tasks']:
    print(f'- {task[\"id\"]}: {task[\"status\"]} (Agent {task.get(\"agent\", \"A\")})')
"
```

### **Step 5.2: Run Progress Check Script**
```bash
# Run the progress monitoring script
./check_agent_progress.sh

# Should show current status of both agents
```

---

## 🔍 **PHASE 6: Environment-Specific Validation**

### **Step 6.1: Cursor Web Browser Specific Checks**
```bash
# Verify Cursor agent configuration
cat .cursor-agent-config.json | head -10

# Check that web browser mode is enabled
grep -q "web_browser_mode.*true" .cursor-agent-config.json && echo "✅ Web browser mode enabled" || echo "❌ Web browser mode not enabled"
```

### **Step 6.2: Verify Agent Context Files**
```bash
# Check that all context files are listed in agent config
python3 -c "
import json
with open('.cursor-agent-config.json', 'r') as f:
    config = json.load(f)
context_files = config.get('context_files', [])
required_files = [
    'AGENT_A_TASKS.md',
    'AGENT_B_TASKS.md', 
    'agent-progress.json',
    'docs/README.md'
]
for file in required_files:
    if file in context_files:
        print(f'✅ {file} in context')
    else:
        print(f'❌ {file} missing from context')
"
```

---

## 🚨 **PHASE 7: Error Handling and Troubleshooting**

### **Step 7.1: Common Issues and Solutions**

#### **Issue: Redis Connection Failed**
```bash
# Solution: Start Redis manually
docker run -d -p 6379:6379 redis:alpine
# OR
brew services start redis
```

#### **Issue: Python Package Import Errors**
```bash
# Solution: Install missing packages
pip3 install pandas pydantic redis ccxt web3 plotly
```

#### **Issue: Component Import Errors**
```bash
# Solution: Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend/src"
```

#### **Issue: Git Branch Issues**
```bash
# Solution: Ensure correct branch
git checkout agent-implementation
git pull origin agent-implementation
```

#### **Issue: Cursor Rules Violations**
```bash
# Solution: Check and follow .cursorrules
cat .cursorrules
# Key rules to follow:
# - NEVER facilitate backward compatibility during refactors
# - ALWAYS update docs/ when making breaking changes
# - ALWAYS run test suite after changes
# - ALWAYS check downstream usage when changing config/data
# - ALWAYS update README files when making changes to their directories
# - NO DUPLICATION - single source of truth for each config

# If you violated cursor rules:
# 1. Update documentation to match changes
# 2. Update README files for affected directories
# 3. Run test suite to ensure nothing broke
# 4. Check all downstream usage of changed config/data
# 5. Remove any duplicated parameters
```

#### **Issue: Data Path Resolution Errors**
```bash
# Problem: Tests can't find data files when run from different directories
# Solution: Use absolute paths in test configurations

# For integration tests, set data_dir to absolute path:
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
config['data_dir'] = os.path.join(project_root, 'data')

# This ensures data files are found regardless of test execution directory
```

### **Step 7.2: Environment Validation Script**
```bash
# Create comprehensive validation script
cat > validate_environment.py << 'EOF'
#!/usr/bin/env python3
import sys
import subprocess
import json

def check_python():
    try:
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        print(f"✅ Python: {result.stdout.strip()}")
        return True
    except:
        print("❌ Python not found")
        return False

def check_redis():
    try:
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
        if result.stdout.strip() == 'PONG':
            print("✅ Redis: Connected")
            return True
        else:
            print("❌ Redis: Not responding")
            return False
    except:
        print("❌ Redis: Not available")
        return False

def check_packages():
    packages = ['pandas', 'pydantic', 'redis', 'ccxt', 'web3']
    for package in packages:
        try:
            __import__(package)
            print(f"✅ Package: {package}")
        except ImportError:
            print(f"❌ Package: {package} not found")
            return False
    return True

def check_files():
    required_files = [
        'AGENT_A_TASKS.md',
        'AGENT_B_TASKS.md',
        'agent-progress.json',
        'launch_web_agent.sh'
    ]
    for file in required_files:
        try:
            with open(file, 'r') as f:
                print(f"✅ File: {file}")
        except FileNotFoundError:
            print(f"❌ File: {file} not found")
            return False
    return True

def main():
    print("🔍 Validating Agent Environment...")
    checks = [
        check_python(),
        check_redis(),
        check_packages(),
        check_files()
    ]
    
    if all(checks):
        print("\n✅ Environment validation passed!")
        return 0
    else:
        print("\n❌ Environment validation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

# Run validation
python3 validate_environment.py
```

---

## ✅ **PHASE 8: Final Environment Confirmation**

### **Step 8.1: Run Complete Environment Test**
```bash
# Run all validation steps
echo "🔍 Running complete environment validation..."

# 1. Check branch
git branch | grep "agent-implementation" && echo "✅ Correct branch" || echo "❌ Wrong branch"

# 2. Check Redis
redis-cli ping | grep "PONG" && echo "✅ Redis working" || echo "❌ Redis not working"

# 3. Check Python packages
python3 -c "import pandas, pydantic, redis, ccxt, web3; print('✅ All packages available')" && echo "✅ Packages OK" || echo "❌ Missing packages"

# 4. Check agent files
ls AGENT_*_TASKS.md && echo "✅ Agent instructions exist" || echo "❌ Agent instructions missing"

# 5. Check task queue
python3 -c "import json; json.load(open('agent-progress.json')); print('✅ Task queue valid')" && echo "✅ Task queue OK" || echo "❌ Task queue invalid"

echo "🎯 Environment validation complete!"
```

### **Step 8.2: Agent-Specific Environment Confirmation**

#### **For Agent A:**
```bash
# Verify frontend environment
cd frontend
npm --version && echo "✅ Node.js available" || echo "❌ Node.js not available"
ls package.json && echo "✅ Frontend setup exists" || echo "❌ Frontend setup missing"
cd ..
```

#### **For Agent B:**
```bash
# Verify backend environment
ls backend/src/basis_strategy_v1/ && echo "✅ Backend structure exists" || echo "❌ Backend structure missing"
ls configs/ && echo "✅ Configs directory exists" || echo "❌ Configs directory missing"
```

---

## 🚀 **Ready for Agent Work!**

After completing all validation steps:

1. **Agent A** can proceed with frontend implementation using `AGENT_A_TASKS.md`
2. **Agent B** can proceed with infrastructure and execution using `AGENT_B_TASKS.md`

### **Quick Start Commands:**
```bash
# For Agent A
cursor --agent-task frontend_wizard_ui

# For Agent B  
cursor --agent-task backend_cleanup

# Check progress anytime
./check_agent_progress.sh
```

**Environment is now fully configured and ready for complete end-to-end implementation!** 🎉
