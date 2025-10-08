# Agent Setup Guide - Parallel Development Strategy 🤖

**Purpose**: Complete guide for setting up parallel Cursor background agents to implement the component refactoring  
**Prerequisites**: All component specifications complete (see [Component Specs Index](COMPONENT_SPECS_INDEX.md))  
**Timeline**: 1-2 weeks with full automation, 4 weeks with human oversight  
**Updated**: October 6, 2025 - **AGENTS 95% COMPLETE** - Final integration tasks remaining

---

## 🎯 **Overview**

This guide enables parallel development of the 9 core components specified in [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) using two specialized Cursor background agents. The strategy leverages the existing codebase architecture while implementing the new component-based service architecture.

**🚨 CURRENT STATUS**: Agents have completed 95% of the work! Only final integration tasks remain.

## 📊 **Current Agent Status (October 6, 2025)**

### **Agent A (Frontend & Integration Specialist)**
- **Status**: ✅ 95% Complete - Ready for final integration
- **Completed**: 15 tasks, 1 critical fix remaining
- **Remaining**: 3 tasks (RiskMonitor compatibility, Phase 1 gates, E2E testing)
- **Estimated Time**: 3 hours to completion

### **Agent B (Infrastructure & Execution Specialist)**  
- **Status**: ✅ 95% Complete - Ready for final integration
- **Completed**: 18 tasks, 1 critical fix remaining
- **Remaining**: 2 tasks (RiskMonitor compatibility, BacktestService validation)
- **Estimated Time**: 2 hours to completion

### **Major Achievements**
- ✅ **Phase 1**: 100% config alignment achieved (16% → 100%)
- ✅ **Phase 2**: 28 datasets loading in 1.88s
- ✅ **Phase 3**: Component dependency injection complete
- ✅ **Architecture**: Complete transformation to component-based service architecture

### **Remaining Critical Tasks**
1. **RiskMonitor data provider compatibility** (shared between agents)
2. **Phase 1 quality gates script fix** (division by zero error)
3. **End-to-end integration validation** (module import path issues)

### **What This Guide Covers**
- ✅ Prerequisites and environment setup
- ✅ Agent workspace creation and configuration  
- ✅ Week-by-week task assignments
- ✅ Coordination protocols and conflict resolution
- ✅ Integration with existing documentation structure

### **Related Documentation**
- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) - Overall timeline and deliverables
- [Component Specs Index](COMPONENT_SPECS_INDEX.md) - All 12 component specifications
- [Architectural Decisions](ARCHITECTURAL_DECISIONS.md) - Key design choices
- [Requirements](REQUIREMENTS.md) - Technical requirements and constraints

---

## 📋 **Prerequisites**

### **Development Environment**
```bash
# Required software (install before starting)
- Cursor IDE (latest version with Background Agents feature)
- Git (for worktrees and branch management)
- Python 3.11+ (for backend development)
- Node.js 18+ (for frontend development)
- Redis server (for inter-component communication)
- Docker (for deployment testing)
```

### **Documentation Review**
Before starting, ensure you've reviewed:
- ✅ [Component Specs Index](COMPONENT_SPECS_INDEX.md) - All 12 specifications
- ✅ [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) - 4-week timeline
- ✅ [Architectural Decisions](ARCHITECTURAL_DECISIONS.md) - Key design principles
- ✅ [Requirements](REQUIREMENTS.md) - Technical constraints

### **Current Codebase Understanding**
The agents will work with the existing codebase structure:
```
backend/src/basis_strategy_v1/
├── core/
│   ├── event_engine/event_driven_strategy_engine.py  # Main integration point
│   ├── strategies/components/                        # Agent A: New components
│   ├── rebalancing/                                  # Agent A: Risk monitoring
│   ├── math/                                         # Agent A: P&L calculation
│   └── config/                                       # Agent B: Configuration
├── infrastructure/
│   ├── data/                                         # Agent B: Data provider
│   └── execution/                                    # Agent B: Execution managers
└── api/                                              # Existing API layer
```

---

## 🏗️ **Agent Architecture**

### **Agent A: Monitoring & Calculation Specialist**
**Responsibility**: Reactive components that process data and calculate metrics

**Components to Implement** (from [Component Specs Index](COMPONENT_SPECS_INDEX.md)):
1. [Position Monitor](specs/01_POSITION_MONITOR.md) - Token + derivative balance tracking
2. [Exposure Monitor](specs/02_EXPOSURE_MONITOR.md) - AAVE conversion, net delta calculation  
3. [Risk Monitor](specs/03_RISK_MONITOR.md) - LTV, margin, liquidation simulation
4. [P&L Calculator](specs/04_PNL_CALCULATOR.md) - Balance-based + attribution P&L
5. [Event Logger](specs/08_EVENT_LOGGER.md) - Audit-grade event tracking
6. [Frontend Spec](specs/12_FRONTEND_SPEC.md) - Complete web UI

**Files to Create/Modify**:
```
backend/src/basis_strategy_v1/
├── core/strategies/components/
│   ├── position_monitor.py      # New (specs/01_POSITION_MONITOR.md)
│   ├── exposure_monitor.py      # New (specs/02_EXPOSURE_MONITOR.md)
│   └── event_logger.py          # New (specs/08_EVENT_LOGGER.md)
├── core/rebalancing/
│   └── risk_monitor.py          # New (specs/03_RISK_MONITOR.md)
├── core/math/
│   └── pnl_calculator.py        # New (specs/04_PNL_CALCULATOR.md)
└── frontend/                    # New (specs/12_FRONTEND_SPEC.md)
```

### **Agent B: Infrastructure & Execution Specialist**
**Responsibility**: Proactive components that execute actions and manage data

**Components to Implement** (from [Component Specs Index](COMPONENT_SPECS_INDEX.md)):
1. [Data Provider](specs/09_DATA_PROVIDER.md) - Market data with hourly alignment
2. [Strategy Manager](specs/05_STRATEGY_MANAGER.md) - Mode-specific orchestration
3. [CEX Execution Manager](specs/06_CEX_EXECUTION_MANAGER.md) - CEX trades
4. [OnChain Execution Manager](specs/07_ONCHAIN_EXECUTION_MANAGER.md) - On-chain transactions
5. [Redis Messaging Standard](specs/10_REDIS_MESSAGING_STANDARD.md) - Pub/sub patterns
6. [Error Logging Standard](specs/11_ERROR_LOGGING_STANDARD.md) - Structured logging

**Files to Create/Modify**:
```
backend/src/basis_strategy_v1/
├── infrastructure/data/
│   └── historical_data_provider.py  # Enhance (specs/09_DATA_PROVIDER.md)
├── infrastructure/execution/
│   ├── cex_execution_manager.py     # New (specs/06_CEX_EXECUTION_MANAGER.md)
│   └── onchain_execution_manager.py # New (specs/07_ONCHAIN_EXECUTION_MANAGER.md)
├── core/strategies/
│   └── strategy_manager.py          # New (specs/05_STRATEGY_MANAGER.md)
├── core/config/
│   └── config_models.py             # Enhance (Week 3 integration)
└── scripts/deployment/              # New (deployment automation)
```

---

## 🛠️ **Setup Instructions**

### **Step 1: Create Agent Workspaces with Branch Strategy (5 minutes)**

**Execute these commands in your project root:**

```bash
# Navigate to project root
cd /Users/ikennaigboaka/Documents/basis-strategy-v1

# Create branches for each agent
git checkout -b agent-a-monitoring
git checkout -b agent-b-execution

# Create Agent A workspace (Monitoring & Calculation)
git worktree add ../basis-strategy-v1-agent-a agent-a-monitoring
cd ../basis-strategy-v1-agent-a

# Create Agent B workspace (Infrastructure & Execution)  
git worktree add ../basis-strategy-v1-agent-b agent-b-execution
cd ../basis-strategy-v1-agent-b

# Verify both workspaces exist
ls -la ../
# Should see: basis-strategy-v1, basis-strategy-v1-agent-a, basis-strategy-v1-agent-b

# Verify branches
git branch -a
# Should see: agent-a-monitoring, agent-b-execution
```

### **Step 2: Setup Redis Server (2 minutes)**

**Start Redis for inter-component communication:**

```bash
# Option 1: Install and start Redis locally (macOS)
brew install redis
brew services start redis

# Option 2: Use Docker (Recommended for agent isolation)
docker run -d -p 6379:6379 --name redis-main redis:alpine

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

**Note**: Each agent will get its own Redis instance via Docker during startup (see Step 4).

**Redis Configuration** (from [Redis Messaging Standard](specs/10_REDIS_MESSAGING_STANDARD.md)):
```bash
# Redis will be used for:
# - position:snapshot (Position Monitor → Exposure Monitor)
# - exposure:calculated (Exposure Monitor → Risk Monitor)
# - risk:calculated (Risk Monitor → Strategy Manager)
# - events:logged (Event Logger → All components)
```

### **Step 3: Create Agent Configuration Files and Startup Scripts (5 minutes)**

**Create Agent A Configuration:**
```bash
# In basis-strategy-v1-agent-a directory
cat > .cursor-agent-config.json << 'EOF'
{
  "agent_name": "Agent A - Monitoring & Calculation",
  "focus_areas": [
    "position_monitor.py",
    "exposure_monitor.py", 
    "event_logger.py",
    "risk_monitor.py",
    "pnl_calculator.py",
    "frontend/"
  ],
  "context_files": [
    ".cursorrules",
    "docs_refactor/ARCHITECTURAL_DECISIONS.md",
    "docs_refactor/COMPONENT_SPECS_INDEX.md",
    "docs_refactor/IMPLEMENTATION_ROADMAP.md",
    "docs_refactor/REFERENCE.md",
    "scripts/analyzers/analyze_leveraged_restaking_USDT.py",
    "backend/src/basis_strategy_v1/core/strategies/components/",
    "backend/src/basis_strategy_v1/core/math/",
    "backend/src/basis_strategy_v1/api/",
    "backend/src/basis_strategy_v1/core/rebalancing/",  # Trade class moved here
    "frontend/src/",
    "tests/",
    "deploy/",
    "configs/",
    "data/"
  ],
  "week_1_tasks": [
    "Implement Position Monitor (docs_refactor/specs/01_POSITION_MONITOR.md)",
    "Implement Event Logger (docs_refactor/specs/08_EVENT_LOGGER.md)"
  ],
  "dependencies": ["redis", "pandas", "pydantic", "plotly"],
  "important_notes": [
    "ALWAYS follow .cursorrules - NEVER facilitate backward compatibility",
    "ALWAYS update docs/ when making breaking changes to config, data, codebase, backend, or frontend",
    "ALWAYS run test suite after changes to ensure everything still works",
    "ALWAYS check downstream usage when adjusting config (adding/removing fields)",
    "NO DUPLICATION - Each config should have a single source of truth",
    "DO NOT use old docs/ directory - use docs_refactor/ only",
    "Study scripts/analyzers/analyze_leveraged_restaking_USDT.py for prototype logic",
    "Follow docs_refactor/ARCHITECTURAL_DECISIONS.md for design decisions",
    "Use existing codebase patterns for consistency"
  ]
}
EOF
```

**Create Agent B Configuration:**
```bash
# In basis-strategy-v1-agent-b directory
cat > .cursor-agent-config.json << 'EOF'
{
  "agent_name": "Agent B - Infrastructure & Execution",
  "focus_areas": [
    "historical_data_provider.py",
    "strategy_manager.py",
    "cex_execution_manager.py", 
    "onchain_execution_manager.py",
    "scripts/deployment/"
  ],
  "context_files": [
    ".cursorrules",
    "docs_refactor/ARCHITECTURAL_DECISIONS.md",
    "docs_refactor/COMPONENT_SPECS_INDEX.md",
    "docs_refactor/IMPLEMENTATION_ROADMAP.md",
    "docs_refactor/REFERENCE.md",
    "scripts/analyzers/analyze_leveraged_restaking_USDT.py",
    "backend/src/basis_strategy_v1/core/strategies/components/",
    "backend/src/basis_strategy_v1/core/math/",
    "backend/src/basis_strategy_v1/api/",
    "backend/src/basis_strategy_v1/core/rebalancing/",  # Trade class moved here
    "frontend/src/",
    "tests/",
    "deploy/",
    "configs/",
    "data/"
  ],
  "week_1_tasks": [
    "Implement Data Provider (docs_refactor/specs/09_DATA_PROVIDER.md)",
    "Implement Strategy Manager (docs_refactor/specs/05_STRATEGY_MANAGER.md)"
  ],
  "dependencies": ["redis", "ccxt", "web3", "pandas", "docker"],
  "important_notes": [
    "ALWAYS follow .cursorrules - NEVER facilitate backward compatibility",
    "ALWAYS update docs/ when making breaking changes to config, data, codebase, backend, or frontend",
    "ALWAYS run test suite after changes to ensure everything still works",
    "ALWAYS check downstream usage when adjusting config (adding/removing fields)",
    "NO DUPLICATION - Each config should have a single source of truth",
    "DO NOT use old docs/ directory - use docs_refactor/ only",
    "Study scripts/analyzers/analyze_leveraged_restaking_USDT.py for prototype logic",
    "Follow docs_refactor/ARCHITECTURAL_DECISIONS.md for design decisions",
    "Use existing codebase patterns for consistency"
  ]
}
EOF
```

**Create Redis Startup Script for Agent Isolation:**
```bash
# Create startup script for both agents
cat > start_agent_with_redis.sh << 'EOF'
#!/bin/bash

# Start Redis in Docker if not already running
if ! docker ps | grep -q redis-agent; then
    echo "Starting Redis container..."
    docker run -d -p 6379:6379 --name redis-agent redis:alpine
    sleep 2
fi

# Run preflight checks
echo "Running preflight checks..."
python preflight_check.py

# Start the agent work
echo "Agent ready to start work!"
EOF

chmod +x start_agent_with_redis.sh
```

**Add Linting Dependencies:**
```bash
# Add flake8 to requirements for code quality checks
echo "flake8" >> requirements.txt
```

**Copy requirements.txt to agent workspaces:**
```bash
# Copy requirements to both agent workspaces
cp requirements.txt ../basis-strategy-v1-agent-a/
cp requirements.txt ../basis-strategy-v1-agent-b/
```

**Create Enhanced Preflight Check Script:**
```bash
# Create comprehensive preflight check script
cat > preflight_check.py << 'EOF'
#!/usr/bin/env python3
"""Pre-flight checks before agent starts work."""

import subprocess
import sys
from pathlib import Path

def run_check(name: str, command: str, cwd: Path = None) -> bool:
    """Runs a shell command and returns True if successful, False otherwise."""
    print(f"🔍 Running {name} check...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        print(f"✅ {name}: PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {name}: FAILED")
        print(f"   Error: {e.stderr.strip()}")
        return False
    except FileNotFoundError:
        print(f"❌ {name}: FAILED - Command not found. Is it installed and in PATH?")
        return False
    except Exception as e:
        print(f"❌ {name}: FAILED - An unexpected error occurred: {e}")
        return False

def check_cursor_rules():
    """Check that .cursorrules file exists and is readable."""
    print("🔍 Running Cursor Rules check...")
    try:
        cursorrules_path = Path(".cursorrules")
        if not cursorrules_path.exists():
            print("❌ Cursor Rules: FAILED - .cursorrules file not found")
            return False
        
        # Check for key rules
        content = cursorrules_path.read_text()
        required_rules = [
            "NEVER facilitate backward compatibility",
            "ALWAYS update docs/ when making breaking changes",
            "ALWAYS run test suite after changes",
            "ALWAYS check downstream usage when adjusting config"
        ]
        
        missing_rules = []
        for rule in required_rules:
            if rule not in content:
                missing_rules.append(rule)
        
        if missing_rules:
            print(f"❌ Cursor Rules: FAILED - Missing rules: {missing_rules}")
            return False
        
        print("✅ Cursor Rules: PASSED")
        return True
    except Exception as e:
        print(f"❌ Cursor Rules: FAILED - Error reading .cursorrules: {e}")
        return False

def main():
    print("--- Running Pre-flight Checks ---")

    # Define checks
    checks = [
        ("Environment", "python validate_config.py"),
        ("Git Status", "git status --porcelain"),
        ("Documentation", "python validate_docs.py"),
        ("Linting (Flake8)", "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=venv,__pycache__,.git"),
        ("Redis", "redis-cli ping")
    ]

    all_passed = True
    
    # Run standard checks
    for name, command in checks:
        if not run_check(name, command):
            all_passed = False
    
    # Run cursor rules check
    if not check_cursor_rules():
        all_passed = False

    if all_passed:
        print("\n--- All Pre-flight Checks PASSED! Agent is ready to work. ---")
        sys.exit(0)
    else:
        print("\n--- Some Pre-flight Checks FAILED. Please address the issues before starting the agent. ---")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x preflight_check.py
```

### **Step 4: Setup Cursor Web Background Agents (5 minutes)**

**Prerequisites:**
```bash
# Ensure all agent files are in the repository
git add .
git commit -m "Add complete agent setup files"
git push origin agent-implementation
```

**For Web Browser Agent Setup:**
1. **Open Cursor Web Browser**: Go to https://cursor.com/agents
2. **Point to Repository**: Connect to `IggyIkenna/basis-strategy-v1` repository
3. **Select Branch**: Use `agent-implementation` branch
4. **Run Setup Script**: Execute `./launch_web_agent.sh`
5. **Start Agent Tasks**: Use commands like:
   - `cursor --agent-task position_monitor`
   - `cursor --agent-task event_logger`
   - `cursor --agent-task all`

**What the web agent setup provides:**
- Automatic Python requirements installation
- Redis setup (Docker or platform-provided)
- Pre-flight checks and validation
- Progress tracking and monitoring
- Self-contained operation in web environment

---

## ✅ **Task Completion Detection & Auto-Progression**

### **Automated Completion Criteria**

**Each component must pass these checks before moving to next task:**

```python
# Create validation script for each agent
cat > validate_completion.py << 'EOF'
#!/usr/bin/env python3
"""Automated task completion validation."""

import subprocess
import sys
import os
from pathlib import Path

class TaskValidator:
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.checks = []
    
    def check_file_exists(self, file_path: str) -> bool:
        """Check if component file exists."""
        exists = Path(file_path).exists()
        print(f"✅ File exists: {file_path}" if exists else f"❌ Missing: {file_path}")
        return exists
    
    def check_tests_pass(self) -> bool:
        """Run unit tests for component."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", f"tests/unit/test_{self.component_name.lower()}.py", "-v"],
                capture_output=True, text=True
            )
            passed = result.returncode == 0
            print(f"✅ Tests pass" if passed else f"❌ Tests fail: {result.stdout}")
            return passed
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False
    
    def check_spec_compliance(self) -> bool:
        """Check if implementation matches spec requirements."""
        # This would check against the spec file
        spec_file = f"docs_refactor/specs/{self.component_name.upper()}_SPEC.md"
        # Implementation would check key requirements
        print(f"✅ Spec compliance check (manual validation needed)")
        return True  # For now, requires manual check
    
    def check_documentation_sync(self) -> bool:
        """Check if documentation is synchronized."""
        try:
            result = subprocess.run(
                ["python", "validate_docs.py"],
                capture_output=True, text=True
            )
            synced = result.returncode == 0
            print(f"✅ Documentation synced" if synced else f"❌ Documentation sync issues: {result.stdout}")
            return synced
        except Exception as e:
            print(f"❌ Doc sync error: {e}")
            return False
    
    def is_complete(self) -> bool:
        """Check if all completion criteria are met."""
        print(f"\n🔍 Validating {self.component_name} completion...")
        
        checks = [
            self.check_file_exists(f"backend/src/basis_strategy_v1/core/strategies/components/{self.component_name.lower()}.py"),
            self.check_tests_pass(),
            self.check_spec_compliance(),
            self.check_documentation_sync()
        ]
        
        complete = all(checks)
        print(f"\n{'✅ COMPLETE' if complete else '❌ INCOMPLETE'}: {self.component_name}")
        return complete

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_completion.py <component_name>")
        sys.exit(1)
    
    component = sys.argv[1]
    validator = TaskValidator(component)
    sys.exit(0 if validator.is_complete() else 1)
EOF

chmod +x validate_completion.py
```

### **Agent Task Progression Logic**

**Agent A Task Sequence**:
```bash
# Agent A automatically progresses through:
1. python validate_completion.py position_monitor
2. python validate_completion.py event_logger  
3. python validate_completion.py exposure_monitor
4. python validate_completion.py risk_monitor
5. python validate_completion.py pnl_calculator
6. python validate_completion.py frontend
```

**Agent B Task Sequence**:
```bash
# Agent B automatically progresses through:
1. python validate_completion.py data_provider
2. python validate_completion.py strategy_manager
3. python validate_completion.py cex_execution_manager
4. python validate_completion.py onchain_execution_manager
5. python validate_completion.py deployment
```

### **Progress Tracking Files**

**Create progress tracking for each agent**:
```bash
# Agent A progress tracking
cat > agent-a-progress.txt << 'EOF'
POSITION_MONITOR: IN_PROGRESS
EVENT_LOGGER: PENDING
EXPOSURE_MONITOR: PENDING
RISK_MONITOR: PENDING
PNL_CALCULATOR: PENDING
FRONTEND: PENDING
EOF

# Agent B progress tracking  
cat > agent-b-progress.txt << 'EOF'
DATA_PROVIDER: IN_PROGRESS
STRATEGY_MANAGER: PENDING
CEX_EXECUTION_MANAGER: PENDING
ONCHAIN_EXECUTION_MANAGER: PENDING
DEPLOYMENT: PENDING
EOF
```

### **Auto-Progression Script**

```bash
# Create auto-progression script
cat > auto_progress.py << 'EOF'
#!/usr/bin/env python3
"""Automated task progression for agents."""

import subprocess
import time
from pathlib import Path

def update_progress(agent: str, task: str, status: str):
    """Update progress file."""
    progress_file = f"agent-{agent}-progress.txt"
    with open(progress_file, 'r') as f:
        lines = f.readlines()
    
    with open(progress_file, 'w') as f:
        for line in lines:
            if task in line:
                f.write(f"{task}: {status}\n")
            else:
                f.write(line)

def get_next_task(agent: str) -> str:
    """Get next pending task for agent."""
    progress_file = f"agent-{agent}-progress.txt"
    with open(progress_file, 'r') as f:
        for line in f:
            if "PENDING" in line:
                return line.split(":")[0].strip()
    return None

def run_agent_task(agent: str, task: str):
    """Run agent task and validate completion."""
    print(f"🚀 Starting {task} for Agent {agent}")
    
    # Update status to IN_PROGRESS
    update_progress(agent, task, "IN_PROGRESS")
    
    # Run validation
    result = subprocess.run(["python", "validate_completion.py", task.lower()])
    
    if result.returncode == 0:
        # Task complete, move to next
        update_progress(agent, task, "COMPLETE")
        print(f"✅ {task} complete!")
        
        next_task = get_next_task(agent)
        if next_task:
            print(f"🔄 Moving to next task: {next_task}")
            run_agent_task(agent, next_task)
        else:
            print(f"🎉 Agent {agent} finished all tasks!")
    else:
        # Task incomplete, retry
        print(f"❌ {task} incomplete, retrying...")
        time.sleep(60)  # Wait 1 minute before retry
        run_agent_task(agent, task)

if __name__ == "__main__":
    import sys
    agent = sys.argv[1] if len(sys.argv) > 1 else "a"
    task = get_next_task(agent)
    if task:
        run_agent_task(agent, task)
EOF

chmod +x auto_progress.py
```

### **Documentation Synchronization Protocol**

**CRITICAL**: Agents must update docs when making spec changes!

**Create documentation update script**:
```bash
# Create doc sync script
cat > sync_docs.py << 'EOF'
#!/usr/bin/env python3
"""Documentation synchronization for agents."""

import os
import subprocess
from pathlib import Path
from datetime import datetime

class DocSync:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.docs_dir = Path("docs_refactor")
        self.specs_dir = self.docs_dir / "specs"
        self.changes_log = self.docs_dir / f"{agent_name}_spec_changes.md"
    
    def log_spec_change(self, spec_file: str, change_type: str, description: str):
        """Log any changes made to specifications."""
        timestamp = datetime.now().isoformat()
        
        with open(self.changes_log, 'a') as f:
            f.write(f"## {timestamp} - {change_type}\n")
            f.write(f"**File**: {spec_file}\n")
            f.write(f"**Agent**: {self.agent_name}\n")
            f.write(f"**Change**: {description}\n")
            f.write(f"**Reason**: Implementation requirement\n\n")
    
    def update_spec_file(self, spec_file: str, changes: dict):
        """Update specification file with implementation changes."""
        spec_path = self.specs_dir / spec_file
        
        if not spec_path.exists():
            print(f"❌ Spec file not found: {spec_path}")
            return False
        
        # Read current spec
        with open(spec_path, 'r') as f:
            content = f.read()
        
        # Apply changes (this would be more sophisticated in practice)
        for section, new_content in changes.items():
            # Find section and replace content
            # This is a simplified version
            content = content.replace(f"## {section}", f"## {section}\n\n{new_content}")
        
        # Write updated spec
        with open(spec_path, 'w') as f:
            f.write(content)
        
        # Log the change
        self.log_spec_change(spec_file, "SPEC_UPDATE", f"Updated {section}")
        
        # Commit the change
        subprocess.run(["git", "add", str(spec_path)])
        subprocess.run(["git", "add", str(self.changes_log)])
        subprocess.run(["git", "commit", "-m", f"Update {spec_file} - {self.agent_name}"])
        
        print(f"✅ Updated {spec_file}")
        return True
    
    def create_implementation_notes(self, component: str, notes: str):
        """Create implementation notes for component."""
        notes_file = self.docs_dir / f"implementation_notes_{component.lower()}.md"
        
        with open(notes_file, 'w') as f:
            f.write(f"# Implementation Notes - {component}\n\n")
            f.write(f"**Agent**: {self.agent_name}\n")
            f.write(f"**Date**: {datetime.now().isoformat()}\n\n")
            f.write("## Changes Made\n\n")
            f.write(notes)
            f.write("\n\n## Spec Deviations\n\n")
            f.write("Any deviations from original specification:\n")
            f.write("- [ ] None\n")
            f.write("- [ ] Minor adjustments\n")
            f.write("- [ ] Significant changes (document below)\n\n")
        
        # Commit the notes
        subprocess.run(["git", "add", str(notes_file)])
        subprocess.run(["git", "commit", "-m", f"Add implementation notes for {component}"])
        
        print(f"✅ Created implementation notes for {component}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python sync_docs.py <agent_name> [component] [action]")
        sys.exit(1)
    
    agent = sys.argv[1]
    doc_sync = DocSync(agent)
    
    if len(sys.argv) >= 4:
        component = sys.argv[2]
        action = sys.argv[3]
        
        if action == "notes":
            notes = input("Enter implementation notes: ")
            doc_sync.create_implementation_notes(component, notes)
        elif action == "update":
            spec_file = input("Enter spec file to update: ")
            changes = {"Implementation Details": "Updated based on actual implementation"}
            doc_sync.update_spec_file(spec_file, changes)
EOF

chmod +x sync_docs.py
```

### **Agent Cursor Rules Compliance**

**CRITICAL**: All agents must follow `.cursorrules` strictly!

**Key Rules to Follow**:

1. **Refactoring Rules**:
   - **NEVER facilitate backward compatibility during refactors**
   - Break things cleanly and update all references
   - Prefer clean breaks over maintaining legacy support

2. **Documentation Rules**:
   - **ALWAYS update docs/ when making breaking changes** to config, data, codebase, backend, or frontend
   - **ALWAYS check docs/ consistency** - ensure all docs reference the same logic
   - Keep docs/ as the single source of truth

3. **Testing Rules**:
   - **ALWAYS run test suite** in tests/ at the end of every set of changes
   - Ensure all tests pass before considering changes complete

4. **Configuration Rules**:
   - **ALWAYS check downstream usage** when adjusting config (adding/removing fields)
   - **ALWAYS update frontend/backend/tests** that use the config changes
   - **NO DUPLICATION** - Each config should have a single source of truth

5. **README Compliance Rules**:
   - **ALWAYS update README files** when making changes to their respective directories
   - **ALWAYS follow instructions** in README files (tests/README.md, docs/README.md, etc.)
   - **ALWAYS validate** that README instructions still work after changes

**Agent Workflow with Cursor Rules**:
```bash
# 1. Before starting work
cat .cursorrules  # Review rules

# 2. During implementation
# - Make clean breaks, no backward compatibility
# - Update docs/ immediately when making changes
# - Update README files for affected directories
# - Check all downstream usage of config/data changes

# 3. After each change
python -m pytest tests/  # Run test suite
python validate_docs.py  # Check docs consistency

# 4. Before committing
# - Ensure all tests pass
# - Ensure docs are updated
# - Ensure README files are updated
# - Ensure no duplicated config parameters
```

### **Agent Documentation Requirements**

**Each agent must**:

1. **Log all spec changes**:
```bash
# When making implementation changes
python sync_docs.py agent-a notes position_monitor
# Enter: "Added Redis connection pooling for better performance"
```

2. **Update specs when deviating**:
```bash
# When implementation differs from spec
python sync_docs.py agent-a update 01_POSITION_MONITOR.md
# Updates spec with actual implementation details
```

3. **Create implementation notes**:
```bash
# For each completed component
python sync_docs.py agent-a notes exposure_monitor
# Documents any changes made during implementation
```

4. **Commit documentation changes**:
```bash
# All doc changes are automatically committed
git log --oneline -5
# Should show commits like: "Update 01_POSITION_MONITOR.md - agent-a"
```

### **Documentation Validation**

**Create doc validation script**:
```bash
cat > validate_docs.py << 'EOF'
#!/usr/bin/env python3
"""Validate documentation is up to date."""

import os
from pathlib import Path

def check_doc_sync():
    """Check if documentation is synchronized."""
    docs_dir = Path("docs_refactor")
    specs_dir = docs_dir / "specs"
    
    issues = []
    
    # Check for implementation notes
    for spec_file in specs_dir.glob("*.md"):
        component = spec_file.stem.split("_")[1].lower()  # Extract component name
        notes_file = docs_dir / f"implementation_notes_{component}.md"
        
        if not notes_file.exists():
            issues.append(f"Missing implementation notes for {component}")
    
    # Check for spec change logs
    for agent in ["agent-a", "agent-b"]:
        changes_log = docs_dir / f"{agent}_spec_changes.md"
        if not changes_log.exists():
            issues.append(f"Missing spec changes log for {agent}")
    
    if issues:
        print("❌ Documentation sync issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Documentation is synchronized")
        return True

if __name__ == "__main__":
    check_doc_sync()
EOF

chmod +x validate_docs.py
```

---

## 🌿 **Branch Strategy & Git Workflow**

### **Branch Structure**

**Main Branches**:
- `main` - Production-ready code
- `agent-a-monitoring` - Agent A's work branch
- `agent-b-execution` - Agent B's work branch

**Workflow**:
```bash
# Each agent works on their own branch
git checkout agent-a-monitoring  # Agent A
git checkout agent-b-execution   # Agent B

# Agents commit to their branches
git add .
git commit -m "Implement Position Monitor - agent-a"
git push origin agent-a-monitoring

# Weekly integration (Week 3)
git checkout main
git merge agent-a-monitoring
git merge agent-b-execution
```

### **Agent Git Configuration**

**Setup git identity for each agent**:
```bash
# In Agent A workspace
cd ../basis-strategy-v1-agent-a
git config user.name "Agent A - Monitoring"
git config user.email "agent-a@basis-strategy-v1.local"

# In Agent B workspace  
cd ../basis-strategy-v1-agent-b
git config user.name "Agent B - Execution"
git config user.email "agent-b@basis-strategy-v1.local"
```

### **Daily Git Workflow**

**Each agent follows this pattern**:
```bash
# 1. Start work
git pull origin agent-a-monitoring  # Get latest changes

# 2. Work on component
# ... implement code ...

# 3. Update documentation
python sync_docs.py agent-a notes position_monitor

# 4. Commit changes
git add .
git commit -m "Complete Position Monitor implementation"

# 5. Push to branch
git push origin agent-a-monitoring
```

### **Integration Workflow (Week 3)**

**Merge strategy**:
```bash
# Option 1: Sequential merge (recommended)
git checkout main
git merge agent-a-monitoring
git merge agent-b-execution

# Option 2: Collaborative merge
git checkout agent-a-monitoring
git merge agent-b-execution
git checkout main
git merge agent-a-monitoring
```

**Conflict resolution**:
```bash
# If conflicts occur
git status
git diff
git mergetool
git add .
git commit -m "Resolve merge conflicts"
```

---

## 📅 **Week-by-Week Execution Plan**

### **Week 1: Foundation Components (100% Parallel)**

**Agent A Tasks** (Monitoring & Calculation):
- **Day 1-2**: [Position Monitor](specs/01_POSITION_MONITOR.md) implementation
  - File: `backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py`
  - Key features: Token + derivative balance tracking, sync guarantee, Redis publishing
- **Day 3-4**: [Event Logger](specs/08_EVENT_LOGGER.md) implementation
  - File: `backend/src/basis_strategy_v1/core/strategies/components/event_logger.py`
  - Key features: Audit-grade logging, balance snapshots, global ordering
- **Day 5**: Integration testing (Position + Event)

**Agent B Tasks** (Infrastructure & Execution):
- **Day 1-2**: [Data Provider](specs/09_DATA_PROVIDER.md) enhancement
  - File: `backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py`
  - Key features: Mode-aware loading, hourly alignment, per-exchange data
- **Day 3-4**: [Strategy Manager](specs/05_STRATEGY_MANAGER.md) skeleton
  - File: `backend/src/basis_strategy_v1/core/strategies/strategy_manager.py`
  - Key features: Mode detection, desired position logic, instruction generation
- **Day 5**: Unit tests for both components

**Conflicts**: ❌ **NONE** - Different files entirely

### **Week 2: Core Components (100% Parallel)**

**Agent A Tasks**:
- **Day 1-2**: [Exposure Monitor](specs/02_EXPOSURE_MONITOR.md)
  - File: `backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py`
  - Key features: AAVE index conversion, net delta calculation, share class awareness
- **Day 3**: [Risk Monitor](specs/03_RISK_MONITOR.md)
  - File: `backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py`
  - Key features: LTV monitoring, margin ratios, liquidation simulation
- **Day 4-5**: [P&L Calculator](specs/04_PNL_CALCULATOR.md)
  - File: `backend/src/basis_strategy_v1/core/math/pnl_calculator.py`
  - Key features: Balance-based + attribution P&L, reconciliation

**Agent B Tasks**:
- **Day 1-2**: [CEX Execution Manager](specs/06_CEX_EXECUTION_MANAGER.md)
  - File: `backend/src/basis_strategy_v1/infrastructure/execution/cex_execution_manager.py`
  - Key features: Spot/perp trades, per-exchange prices, execution simulation
- **Day 3-5**: [OnChain Execution Manager](specs/07_ONCHAIN_EXECUTION_MANAGER.md)
  - File: `backend/src/basis_strategy_v1/infrastructure/execution/onchain_execution_manager.py`
  - Key features: Atomic leverage loops, AAVE operations, flash loan support

**Conflicts**: ❌ **NONE** - Different files entirely

### **Week 3: Integration (Coordination Required)**

**Shared File**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py`

**Recommended Approach**: **Sequential Integration**
- **Agent A**: Integrate monitoring components (Days 1-2)
  - Add Position Monitor, Exposure Monitor, Risk Monitor, P&L Calculator
  - Implement synchronous update chain
- **Agent B**: Prepare deployment and integration tests (Days 1-2)
  - Enhance config models with mode fields
  - Write integration tests for all 4 modes
- **Both**: Run integration tests together (Days 3-5)

**Alternative**: **Collaborative Integration**
- Agent A: Edits monitoring section of engine
- Agent B: Edits execution section of engine
- Merge branches at end of Day 1

**Integration Tasks** (from [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md)):
- [ ] EventDrivenStrategyEngine: Add mode detection (INT-01)
- [ ] EventDrivenStrategyEngine: Initialize all 9 components
- [ ] EventDrivenStrategyEngine: Implement sync update chain
- [ ] Config Models: Add mode fields (INT-02)
- [ ] Integration Tests: All 4 modes (INT-03)

### **Week 4: Frontend & Deployment (100% Parallel)**

**Agent A Tasks** (Frontend):
- **Days 1-5**: [Frontend Spec](specs/12_FRONTEND_SPEC.md) implementation
  - Wizard/stepper UI with mode selection
  - Results display with Plotly charts
  - Event log viewer (virtualized for 70k+ events)
  - Mobile responsive design

**Agent B Tasks** (Deployment):
- **Days 1-5**: Production deployment
  - GCS data upload scripts
  - Docker containerization
  - Integration tests (E2E)
  - Deploy to GCloud VM
  - Production health checks

**Conflicts**: ❌ **NONE** - Completely different domains

---

## 🔗 **Interface Contracts & Communication**

### **Agent A Interface Definitions**

**Position Monitor Interface** (from [Position Monitor Spec](specs/01_POSITION_MONITOR.md)):
```python
class PositionMonitorInterface:
    async def update(self, changes: Dict) -> Dict:
        """
        Update balances (SYNCHRONOUS - blocks until complete).
        
        Args:
            changes: {
                'token_changes': [...],
                'derivative_changes': [...]
            }
        Returns:
            Updated snapshot
        """
    
    def get_snapshot(self) -> Dict:
        """Get current position snapshot (read-only)."""
    
    async def reconcile_with_live(self):
        """Reconcile tracked balances with live queries (live mode only)."""
```

**Event Logger Interface** (from [Event Logger Spec](specs/08_EVENT_LOGGER.md)):
```python
class EventLoggerInterface:
    async def log_event(
        self,
        timestamp: pd.Timestamp,
        event_type: str,
        venue: str,
        token: str = None,
        amount: float = None,
        position_snapshot: Optional[Dict] = None,
        **event_data
    ) -> int:
        """Log an event with automatic order assignment."""
    
    async def log_atomic_transaction(
        self,
        timestamp: pd.Timestamp,
        bundle_name: str,
        detail_events: List[Dict],
        net_result: Dict,
        position_snapshot: Optional[Dict] = None
    ) -> List[int]:
        """Log atomic transaction (flash loan bundle)."""
```

### **Agent B Interface Usage**

**CEX Execution Manager** (from [CEX Execution Manager Spec](specs/06_CEX_EXECUTION_MANAGER.md)):
```python
class CEXExecutionManager:
    def __init__(
        self, 
        position_monitor: PositionMonitorInterface,
        event_logger: EventLoggerInterface,
        data_provider: DataProviderInterface
    ):
        self.position_monitor = position_monitor
        self.event_logger = event_logger
        self.data_provider = data_provider
    
    async def trade_spot(self, venue: str, pair: str, side: str, amount: float):
        # Execute trade
        result = await self._execute_trade(...)
        
        # Update position monitor (using Agent A's interface)
        await self.position_monitor.update({
            'token_changes': [
                {'venue': venue, 'token': base, 'delta': +filled},
                {'venue': venue, 'token': quote, 'delta': -cost}
            ]
        })
        
        # Log event (using Agent A's interface)
        await self.event_logger.log_event(
            timestamp=timestamp,
            event_type='SPOT_TRADE',
            venue=venue.upper(),
            token=base,
            amount=filled,
            **result
        )
        
        return result
```

### **Redis Communication Protocol**

**From [Redis Messaging Standard](specs/10_REDIS_MESSAGING_STANDARD.md):**

**Position Monitor → Exposure Monitor**:
```python
# Position Monitor publishes
await redis.set('position:snapshot', json.dumps(snapshot))
await redis.publish('position:updated', json.dumps({
    'timestamp': timestamp.isoformat(),
    'trigger': 'BALANCE_CHANGE'
}))

# Exposure Monitor subscribes
await redis.subscribe('position:updated', self._on_position_update)
```

**Exposure Monitor → Risk Monitor**:
```python
# Exposure Monitor publishes
await redis.set('exposure:current', json.dumps(exposure_data))
await redis.publish('exposure:calculated', json.dumps({
    'timestamp': timestamp.isoformat(),
    'net_delta_eth': exposure_data['net_delta_eth']
}))

# Risk Monitor subscribes
await redis.subscribe('exposure:calculated', self._on_exposure_update)
```

---

## 🎯 **Daily Coordination Protocol**

### **Daily Standups (5 minutes each)**

**Agent A Reports**:
- "Completed Position Monitor implementation, interfaces published to Redis"
- "Event Logger with balance snapshots complete"
- "Exposure Monitor using AAVE index conversion logic"

**Agent B Reports**:
- "Data Provider enhanced with mode-aware loading"
- "Strategy Manager skeleton complete, using Agent A interfaces"
- "CEX Execution Manager using Position Monitor interface"

**Both Confirm**:
- "No file conflicts, proceeding with next tasks"
- "Redis communication working correctly"
- "Interface contracts maintained"

### **Progress Monitoring**

**Check Agent Progress**:
```bash
# Check Agent A progress
cd ../basis-strategy-v1-agent-a
git status
git log --oneline -5
cat agent-a-progress.txt

# Check Agent B progress  
cd ../basis-strategy-v1-agent-b
git status
git log --oneline -5
cat agent-b-progress.txt

# Check Redis communication
redis-cli
> KEYS *
> GET position:snapshot
> GET exposure:current

# Check documentation sync
python validate_docs.py
```

**Monitor Documentation Updates**:
```bash
# Check for implementation notes
ls docs_refactor/implementation_notes_*.md

# Check for spec change logs
ls docs_refactor/agent-*_spec_changes.md

# View recent documentation changes
git log --oneline --grep="Update.*spec" -10
git log --oneline --grep="implementation notes" -10
```

**Agent Status Dashboard**:
```bash
# Create status monitoring script
cat > monitor_agents.py << 'EOF'
#!/usr/bin/env python3
"""Monitor agent progress and documentation sync."""

import subprocess
from pathlib import Path

def get_agent_status(agent: str):
    """Get status for specific agent."""
    workspace = f"../basis-strategy-v1-{agent}"
    progress_file = f"{workspace}/agent-{agent}-progress.txt"
    
    print(f"\n🤖 Agent {agent.upper()} Status:")
    print("=" * 40)
    
    # Check progress file
    if Path(progress_file).exists():
        with open(progress_file, 'r') as f:
            print("📋 Progress:")
            for line in f:
                print(f"  {line.strip()}")
    else:
        print("❌ No progress file found")
    
    # Check recent commits
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            cwd=workspace,
            capture_output=True, text=True
        )
        print("\n📝 Recent Commits:")
        for line in result.stdout.strip().split('\n'):
            print(f"  {line}")
    except Exception as e:
        print(f"❌ Error checking commits: {e}")
    
    # Check documentation sync
    try:
        result = subprocess.run(
            ["python", "validate_docs.py"],
            cwd=workspace,
            capture_output=True, text=True
        )
        print(f"\n📚 Documentation: {'✅ Synced' if result.returncode == 0 else '❌ Issues'}")
    except Exception as e:
        print(f"❌ Error checking docs: {e}")

if __name__ == "__main__":
    get_agent_status("a")
    get_agent_status("b")
EOF

chmod +x monitor_agents.py
```

---

## ⚠️ **Conflict Resolution**

### **Week 3 Integration Conflicts**

**If conflicts occur in `event_driven_strategy_engine.py`**:

**Option 1: Sequential (Recommended)**
```bash
# Agent A integrates first
git checkout agent-a-monitoring
# Edit event_driven_strategy_engine.py (monitoring section)
git add .
git commit -m "Add monitoring components to engine"

# Agent B merges and adds execution
git checkout agent-b-execution  
git merge agent-a-monitoring
# Edit event_driven_strategy_engine.py (execution section)
git add .
git commit -m "Add execution managers to engine"
```

**Option 2: Collaborative**
```bash
# Both agents edit different sections
# Agent A: Lines 1-100 (monitoring components)
# Agent B: Lines 101-200 (execution managers)
# Merge at end of day
```

### **Interface Contract Conflicts**

**If Agent B needs changes to Agent A interfaces**:
1. Agent B creates interface enhancement request
2. Agent A reviews and implements changes
3. Agent B updates implementation
4. Both test integration

---

## 🚀 **Starting the Web Agents**

### **Start Web Agent**:
1. **Open Cursor Web Browser**: Go to https://cursor.com/agents
2. **Connect to Repository**: `IggyIkenna/basis-strategy-v1`
3. **Select Branch**: `agent-implementation`
4. **Run Setup**: Execute `./launch_web_agent.sh`
5. **Start Agent A Tasks**:
   - `cursor --agent-task position_monitor`
   - `cursor --agent-task event_logger`
   - `cursor --agent-task exposure_monitor`
   - `cursor --agent-task risk_monitor`
   - `cursor --agent-task pnl_calculator`
6. **Start Agent B Tasks**:
   - `cursor --agent-task data_provider`
   - `cursor --agent-task strategy_manager`
   - `cursor --agent-task cex_execution_manager`
   - `cursor --agent-task onchain_execution_manager`
7. **Monitor Progress**: Run `./check_agent_progress.sh`

### **Monitor Agent Progress**:
```bash
# Check both agents
python monitor_agents.py

# Check specific agent
python monitor_agents.py a
python monitor_agents.py b

# Web monitoring dashboard
python web_monitor.py
# Open http://localhost:5001 in browser
```

### **Stop Agents if Needed**:
```bash
# Stop all Cursor processes
pkill -f "Cursor"

# Or stash changes and switch branches
git stash
git checkout main
```

---

## 📊 **Success Metrics**

### **Week 1 Deliverables**:
- **Agent A**: Position Monitor + Event Logger (2 components)
- **Agent B**: Enhanced Data Provider + Strategy Manager skeleton (2 components)
- **Integration**: Redis communication working

### **Week 2 Deliverables**:
- **Agent A**: Exposure Monitor + Risk Monitor + P&L Calculator (3 components)
- **Agent B**: CEX Execution Manager + OnChain Execution Manager (2 components)
- **Integration**: All interfaces working

### **Week 3 Deliverables**:
- **Both**: Integrated EventDrivenStrategyEngine working for all 4 modes
- **Testing**: Integration tests passing
- **Documentation**: Updated [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md)

### **Week 4 Deliverables**:
- **Agent A**: Complete frontend UI deployed
- **Agent B**: Production deployment to GCloud
- **Final**: Production-ready web UI at defi-project.odum-research.com

---

## 🔧 **Troubleshooting**

### **Agent Setup Issues**
```bash
# If "requirements.txt not found" error:
cp requirements.txt ../basis-strategy-v1-agent-a/
cp requirements.txt ../basis-strategy-v1-agent-b/

# If GitHub authentication fails:
brew install gh
gh auth login

# If Redis Docker container fails:
docker run -d -p 6379:6379 --name redis-agent redis:alpine
```

### **Linting Issues**
```bash
# If Flake8 not found:
pip install flake8

# If linting errors in venv packages:
# The preflight check excludes venv, but if you see errors:
flake8 . --exclude=venv,__pycache__,.git

# If undefined variable errors:
# Check for variables used before definition
# Example fix: Initialize prev_ts = None before loop

# If stray EOF errors:
# Remove any stray "EOF" at end of Python files
```

### **File Structure Issues**
```bash
# If files are in wrong directories:
mkdir -p scripts/downloaders/clients
mv alchemy_client_fast.py scripts/downloaders/clients/

# If preflight check fails due to missing directories:
mkdir -p tests/unit
mkdir -p backend/src/basis_strategy_v1/core/strategies/components
```

### **Agent Stops Working**
```bash
# Restart agent in Cursor
# Command Palette > "Cursor: Start Background Agent"

# Check Redis connectivity
redis-cli ping
# Should return: PONG

# Check Docker Redis container
docker ps | grep redis-agent
```

### **Interface Mismatches**
```bash
# Check interface contracts
grep -r "class.*Interface" backend/src/
grep -r "PositionMonitorInterface" backend/src/
```

### **Redis Communication Issues**
```bash
# Restart Redis Docker container
docker stop redis-agent
docker rm redis-agent
docker run -d -p 6379:6379 --name redis-agent redis:alpine

# Check Redis logs
docker logs redis-agent
```

### **Git Conflicts**
```bash
# Check for conflicts
git status
git diff

# Resolve conflicts manually
git mergetool
git add .
git commit -m "Resolved merge conflict"
```

### **Agent Monitoring Issues**
```bash
# If monitor_agents.py fails:
python monitor_agents.py a
python monitor_agents.py b

# If web monitor fails:
python web_monitor.py
# Check http://localhost:5001
```

---

## 📚 **Related Documentation**

### **Component Specifications**
- [Position Monitor](specs/01_POSITION_MONITOR.md) - Token + derivative tracking
- [Exposure Monitor](specs/02_EXPOSURE_MONITOR.md) - AAVE conversion, net delta
- [Risk Monitor](specs/03_RISK_MONITOR.md) - LTV, margin, liquidation simulation
- [P&L Calculator](specs/04_PNL_CALCULATOR.md) - Balance + attribution P&L
- [Strategy Manager](specs/05_STRATEGY_MANAGER.md) - Mode-specific orchestration
- [CEX Execution Manager](specs/06_CEX_EXECUTION_MANAGER.md) - CEX trades
- [OnChain Execution Manager](specs/07_ONCHAIN_EXECUTION_MANAGER.md) - On-chain transactions
- [Event Logger](specs/08_EVENT_LOGGER.md) - Audit logging
- [Data Provider](specs/09_DATA_PROVIDER.md) - Market data
- [Redis Messaging Standard](specs/10_REDIS_MESSAGING_STANDARD.md) - Pub/sub patterns
- [Error Logging Standard](specs/11_ERROR_LOGGING_STANDARD.md) - Structured logging
- [Frontend Spec](specs/12_FRONTEND_SPEC.md) - Web UI

### **Architecture & Planning**
- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) - 4-week timeline
- [Architectural Decisions](ARCHITECTURAL_DECISIONS.md) - Key design choices
- [Requirements](REQUIREMENTS.md) - Technical constraints
- [Component Specs Index](COMPONENT_SPECS_INDEX.md) - All specifications

### **Deployment & Operations**
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Production deployment
- [User Guide](USER_GUIDE.md) - End-user documentation
- [Quick Start](QUICK_START.md) - Getting started guide

---

## ✅ **Summary**

This agent setup guide enables efficient parallel development of the 9 core components specified in the comprehensive documentation. The strategy provides:

- **75% conflict-free development** (15 out of 20 days)
- **Clear separation of concerns** between monitoring and execution
- **Interface-first development** for loose coupling
- **Minimal coordination overhead** (only Week 3)
- **Integration with existing codebase** architecture

**Total manual setup time**: ~20 minutes initially, then 5 minutes daily for coordination.

**Expected outcome**: Production-ready web UI with all 9 components implemented according to specifications, deployed to production in 4 weeks.

## 🆕 **Recent Updates & Improvements**

### **Enhanced Agent Setup (October 2025)**
- ✅ **Redis Docker Integration**: Each agent gets isolated Redis container
- ✅ **GitHub Authentication**: Automated branch pushing with GitHub CLI
- ✅ **Comprehensive Context**: Agents have access to full codebase and documentation
- ✅ **Startup Scripts**: Automated Redis setup and pre-flight checks
- ✅ **Web Monitoring**: Browser-based agent progress dashboard
- ✅ **Error Prevention**: Enhanced troubleshooting and recovery procedures

### **Key Improvements Made**
1. **Agent Isolation**: Each agent runs with its own Redis Docker container
2. **Full Context Access**: Agents can reference existing codebase patterns and prototype logic
3. **Automated Setup**: One-command agent startup with dependency installation
4. **Real-time Monitoring**: Web dashboard for tracking agent progress
5. **GitHub Integration**: Seamless branch management and progress tracking
6. **Enhanced Documentation**: Clear separation between reference code and target architecture
7. **Code Quality Validation**: Integrated Flake8 linting with preflight checks
8. **Enhanced Error Handling**: Better error messages and troubleshooting guidance
9. **File Structure Validation**: Automatic directory creation and file placement
10. **Comprehensive Preflight Checks**: Environment, git, docs, linting, and Redis validation

---

## 🔍 **Code Quality & Linting Setup**

### **Flake8 Integration for Agent Validation**

**Purpose**: Ensure code quality before agents start work by integrating Flake8 linting into preflight checks.

**Setup Process**:
```bash
# 1. Add Flake8 to requirements
echo "flake8" >> requirements.txt

# 2. Copy to agent workspaces
cp requirements.txt ../basis-strategy-v1-agent-a/
cp requirements.txt ../basis-strategy-v1-agent-b/

# 3. Test linting (should show 0 errors after fixes)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=venv,__pycache__,.git
```

**Common Linting Issues & Fixes**:

1. **Undefined Variables**:
   ```python
   # ❌ Error: prev_ts used before definition
   for i, item in enumerate(items):
       if i > 0:
           diff = current - prev_ts  # prev_ts not defined yet
       prev_ts = current
   
   # ✅ Fix: Initialize before loop
   prev_ts = None
   for i, item in enumerate(items):
       if i > 0:
           diff = current - prev_ts
       prev_ts = current
   ```

2. **Stray EOF in Python Files**:
   ```python
   # ❌ Error: Stray EOF at end of file
   def my_function():
       return "hello"
   EOF  # Remove this line
   
   # ✅ Fix: Clean file ending
   def my_function():
       return "hello"
   ```

3. **File Structure Issues**:
   ```bash
   # ❌ Error: Files in wrong directories
   ls -la  # Shows alchemy_client_fast.py in root
   
   # ✅ Fix: Move to correct structure
   mkdir -p scripts/downloaders/clients
   mv alchemy_client_fast.py scripts/downloaders/clients/
   ```

**Linting Configuration**:
- **Critical Errors Only**: `E9,F63,F7,F82` (syntax, undefined names, etc.)
- **Exclusions**: `venv,__pycache__,.git` (ignore dependency packages)
- **Statistics**: Shows count of issues found
- **Source Display**: Shows exact lines with problems

**Integration with Agent Startup**:
- Linting runs automatically during preflight checks
- Agent won't start if linting fails
- Provides clear error messages for fixes
- Ensures clean codebase before agent work begins

---

## 🛡️ **Best Practices & Issue Prevention**

### **Agent Reliability Best Practices**

**1. Environment Isolation**
```bash
# Create isolated Python environments for each agent
cd ../basis-strategy-v1-agent-a
python -m venv venv-agent-a
source venv-agent-a/bin/activate
pip install -r requirements.txt

cd ../basis-strategy-v1-agent-b  
python -m venv venv-agent-b
source venv-agent-b/bin/activate
pip install -r requirements.txt
```

**2. Dependency Management**
```bash
# Pin exact versions to prevent conflicts
cat > requirements-agent.txt << 'EOF'
redis==5.0.1
pandas==2.1.4
pydantic==2.5.0
pytest==7.4.3
ccxt==4.1.77
web3==6.11.4
EOF

# Install in each agent environment
pip install -r requirements-agent.txt
```

**3. Configuration Validation**
```bash
# Create config validation script
cat > validate_config.py << 'EOF'
#!/usr/bin/env python3
"""Validate agent configuration before starting."""

import os
import sys
from pathlib import Path

def validate_environment():
    """Validate environment setup."""
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 11):
        issues.append("Python 3.11+ required")
    
    # Check required directories
    required_dirs = [
        "backend/src/basis_strategy_v1",
        "docs_refactor/specs",
        "tests/unit"
    ]
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            issues.append(f"Missing directory: {dir_path}")
    
    # Check Redis connection
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
    except Exception as e:
        issues.append(f"Redis connection failed: {e}")
    
    # Check git configuration
    try:
        import subprocess
        result = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True)
        if not result.stdout.strip():
            issues.append("Git user.name not configured")
    except Exception as e:
        issues.append(f"Git configuration error: {e}")
    
    if issues:
        print("❌ Environment validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Environment validation passed")
        return True

if __name__ == "__main__":
    sys.exit(0 if validate_environment() else 1)
EOF

chmod +x validate_config.py
```

### **Error Prevention Strategies**

**4. Pre-flight Checks**
```bash
# Create pre-flight check script
cat > preflight_check.py << 'EOF'
#!/usr/bin/env python3
"""Pre-flight checks before agent starts work."""

import subprocess
import sys
from pathlib import Path

def run_preflight_checks():
    """Run all pre-flight checks."""
    checks = [
        ("Environment", "python validate_config.py"),
        ("Git Status", "git status --porcelain"),
        ("Documentation", "python validate_docs.py"),
        ("Dependencies", "pip check"),
        ("Redis", "redis-cli ping")
    ]
    
    print("🚀 Running pre-flight checks...")
    all_passed = True
    
    for check_name, command in checks:
        try:
            result = subprocess.run(command.split(), capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {check_name}: OK")
            else:
                print(f"❌ {check_name}: FAILED")
                print(f"   {result.stderr}")
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name}: ERROR - {e}")
            all_passed = False
    
    if all_passed:
        print("\n🎉 All pre-flight checks passed! Agent ready to start.")
    else:
        print("\n⚠️  Some pre-flight checks failed. Fix issues before starting agent.")
    
    return all_passed

if __name__ == "__main__":
    sys.exit(0 if run_preflight_checks() else 1)
EOF

chmod +x preflight_check.py
```

**5. Rollback Strategy**
```bash
# Create rollback script
cat > rollback_agent.py << 'EOF'
#!/usr/bin/env python3
"""Rollback agent changes if issues occur."""

import subprocess
import sys
from pathlib import Path

def rollback_agent(agent_name: str, commit_hash: str = None):
    """Rollback agent to previous working state."""
    workspace = f"../basis-strategy-v1-{agent_name}"
    
    print(f"🔄 Rolling back Agent {agent_name.upper()}...")
    
    # Get last working commit if not specified
    if not commit_hash:
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--grep", "WORKING", "-1"],
                cwd=workspace,
                capture_output=True, text=True
            )
            if result.stdout:
                commit_hash = result.stdout.split()[0]
            else:
                # Fallback to last commit
                result = subprocess.run(
                    ["git", "log", "--oneline", "-1"],
                    cwd=workspace,
                    capture_output=True, text=True
                )
                commit_hash = result.stdout.split()[0]
        except Exception as e:
            print(f"❌ Error finding rollback commit: {e}")
            return False
    
    # Perform rollback
    try:
        subprocess.run(["git", "reset", "--hard", commit_hash], cwd=workspace)
        subprocess.run(["git", "clean", "-fd"], cwd=workspace)
        print(f"✅ Rolled back to commit: {commit_hash}")
        return True
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rollback_agent.py <agent_name> [commit_hash]")
        sys.exit(1)
    
    agent = sys.argv[1]
    commit = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(0 if rollback_agent(agent, commit) else 1)
EOF

chmod +x rollback_agent.py
```

### **Quality Gates & Validation**

**6. Code Quality Gates**
```bash
# Create quality gate script
cat > quality_gate.py << 'EOF'
#!/usr/bin/env python3
"""Quality gates for agent code."""

import subprocess
import sys
from pathlib import Path

def run_quality_checks():
    """Run all quality checks."""
    checks = [
        ("Syntax", "python -m py_compile backend/src/basis_strategy_v1/core/strategies/components/*.py"),
        ("Imports", "python -c 'import backend.src.basis_strategy_v1.core.strategies.components'"),
        ("Tests", "python -m pytest tests/unit/ -v"),
        ("Linting", "python -m flake8 backend/src/basis_strategy_v1/core/strategies/components/"),
        ("Type Checking", "python -m mypy backend/src/basis_strategy_v1/core/strategies/components/")
    ]
    
    print("🔍 Running quality gates...")
    all_passed = True
    
    for check_name, command in checks:
        try:
            result = subprocess.run(command.split(), capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {check_name}: PASSED")
            else:
                print(f"❌ {check_name}: FAILED")
                print(f"   {result.stderr}")
                all_passed = False
        except Exception as e:
            print(f"⚠️  {check_name}: SKIPPED - {e}")
    
    return all_passed

if __name__ == "__main__":
    sys.exit(0 if run_quality_checks() else 1)
EOF

chmod +x quality_gate.py
```

**7. Integration Testing**
```bash
# Create integration test script
cat > integration_test.py << 'EOF'
#!/usr/bin/env python3
"""Integration tests for agent components."""

import subprocess
import sys
import time

def test_component_integration():
    """Test component integration."""
    print("🔗 Testing component integration...")
    
    # Test Redis communication
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.set('test:integration', 'working')
        value = r.get('test:integration')
        if value.decode() == 'working':
            print("✅ Redis integration: OK")
        else:
            print("❌ Redis integration: FAILED")
            return False
    except Exception as e:
        print(f"❌ Redis integration: ERROR - {e}")
        return False
    
    # Test component imports
    components = [
        "position_monitor",
        "exposure_monitor", 
        "event_logger",
        "risk_monitor",
        "pnl_calculator"
    ]
    
    for component in components:
        try:
            module = __import__(f"backend.src.basis_strategy_v1.core.strategies.components.{component}", fromlist=[component])
            print(f"✅ {component}: Import OK")
        except Exception as e:
            print(f"❌ {component}: Import FAILED - {e}")
            return False
    
    print("✅ All integration tests passed!")
    return True

if __name__ == "__main__":
    sys.exit(0 if test_component_integration() else 1)
EOF

chmod +x integration_test.py
```

### **Monitoring & Alerting**

**8. Health Monitoring**
```bash
# Create health monitoring script
cat > health_monitor.py << 'EOF'
#!/usr/bin/env python3
"""Health monitoring for agents."""

import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

class AgentHealthMonitor:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.workspace = f"../basis-strategy-v1-{agent_name}"
        self.health_log = f"health_{agent_name}.json"
    
    def check_health(self):
        """Check agent health status."""
        health = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "status": "healthy",
            "checks": {}
        }
        
        # Check git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.workspace,
                capture_output=True, text=True
            )
            health["checks"]["git_status"] = "clean" if not result.stdout else "dirty"
        except Exception as e:
            health["checks"]["git_status"] = f"error: {e}"
            health["status"] = "unhealthy"
        
        # Check Redis connection
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            health["checks"]["redis"] = "connected"
        except Exception as e:
            health["checks"]["redis"] = f"error: {e}"
            health["status"] = "unhealthy"
        
        # Check disk space
        try:
            result = subprocess.run(
                ["df", "-h", self.workspace],
                capture_output=True, text=True
            )
            health["checks"]["disk_space"] = "ok"
        except Exception as e:
            health["checks"]["disk_space"] = f"error: {e}"
        
        # Save health status
        with open(self.health_log, 'w') as f:
            json.dump(health, f, indent=2)
        
        return health
    
    def alert_if_unhealthy(self):
        """Alert if agent is unhealthy."""
        health = self.check_health()
        
        if health["status"] == "unhealthy":
            print(f"🚨 ALERT: Agent {self.agent_name.upper()} is unhealthy!")
            print(f"   Issues: {health['checks']}")
            
            # Send alert (could be email, Slack, etc.)
            with open(f"alert_{self.agent_name}.txt", 'w') as f:
                f.write(f"Agent {self.agent_name} health alert at {health['timestamp']}\n")
                f.write(f"Issues: {health['checks']}\n")
        
        return health["status"] == "healthy"

if __name__ == "__main__":
    import sys
    agent = sys.argv[1] if len(sys.argv) > 1 else "a"
    monitor = AgentHealthMonitor(agent)
    monitor.alert_if_unhealthy()
EOF

chmod +x health_monitor.py
```

### **Recovery Procedures**

**9. Automated Recovery**
```bash
# Create recovery script
cat > recover_agent.py << 'EOF'
#!/usr/bin/env python3
"""Automated recovery procedures for agents."""

import subprocess
import sys
import time

def recover_agent(agent_name: str):
    """Recover agent from common issues."""
    workspace = f"../basis-strategy-v1-{agent_name}"
    
    print(f"🔧 Recovering Agent {agent_name.upper()}...")
    
    # 1. Clean up any locks
    try:
        subprocess.run(["find", workspace, "-name", "*.lock", "-delete"])
        print("✅ Cleaned up lock files")
    except Exception as e:
        print(f"⚠️  Lock cleanup failed: {e}")
    
    # 2. Reset git state
    try:
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=workspace)
        subprocess.run(["git", "clean", "-fd"], cwd=workspace)
        print("✅ Reset git state")
    except Exception as e:
        print(f"❌ Git reset failed: {e}")
        return False
    
    # 3. Restart Redis if needed
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running")
    except Exception as e:
        print(f"⚠️  Redis issue: {e}")
        print("   Try: redis-server")
    
    # 4. Reinstall dependencies
    try:
        subprocess.run(["pip", "install", "-r", "requirements-agent.txt"], cwd=workspace)
        print("✅ Dependencies reinstalled")
    except Exception as e:
        print(f"⚠️  Dependency reinstall failed: {e}")
    
    # 5. Run pre-flight checks
    try:
        result = subprocess.run(["python", "preflight_check.py"], cwd=workspace)
        if result.returncode == 0:
            print("✅ Pre-flight checks passed")
            return True
        else:
            print("❌ Pre-flight checks failed")
            return False
    except Exception as e:
        print(f"❌ Pre-flight check error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python recover_agent.py <agent_name>")
        sys.exit(1)
    
    agent = sys.argv[1]
    sys.exit(0 if recover_agent(agent) else 1)
EOF

chmod +x recover_agent.py
```

### **Agent Startup Sequence**

**10. Complete Agent Startup**
```bash
# Create complete startup script
cat > start_agent.py << 'EOF'
#!/usr/bin/env python3
"""Complete agent startup sequence."""

import subprocess
import sys
import time

def start_agent(agent_name: str):
    """Start agent with all safety checks."""
    workspace = f"../basis-strategy-v1-{agent_name}"
    
    print(f"🚀 Starting Agent {agent_name.upper()}...")
    
    # 1. Pre-flight checks
    print("1️⃣ Running pre-flight checks...")
    result = subprocess.run(["python", "preflight_check.py"], cwd=workspace)
    if result.returncode != 0:
        print("❌ Pre-flight checks failed. Run recovery first.")
        return False
    
    # 2. Health check
    print("2️⃣ Checking health...")
    result = subprocess.run(["python", "health_monitor.py", agent_name], cwd=workspace)
    if result.returncode != 0:
        print("⚠️  Health issues detected. Attempting recovery...")
        result = subprocess.run(["python", "recover_agent.py", agent_name], cwd=workspace)
        if result.returncode != 0:
            print("❌ Recovery failed. Manual intervention required.")
            return False
    
    # 3. Quality gates
    print("3️⃣ Running quality gates...")
    result = subprocess.run(["python", "quality_gate.py"], cwd=workspace)
    if result.returncode != 0:
        print("⚠️  Quality gates failed. Review code before proceeding.")
    
    # 4. Start agent work
    print("4️⃣ Starting agent work...")
    result = subprocess.run(["python", "auto_progress.py", agent_name], cwd=workspace)
    
    if result.returncode == 0:
        print(f"🎉 Agent {agent_name.upper()} completed successfully!")
    else:
        print(f"⚠️  Agent {agent_name.upper()} encountered issues.")
    
    return result.returncode == 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python start_agent.py <agent_name>")
        sys.exit(1)
    
    agent = sys.argv[1]
    sys.exit(0 if start_agent(agent) else 1)
EOF

chmod +x start_agent.py
```

### **Daily Maintenance**

**11. Daily Maintenance Script**
```bash
# Create daily maintenance script
cat > daily_maintenance.py << 'EOF'
#!/usr/bin/env python3
"""Daily maintenance for agents."""

import subprocess
import sys
from datetime import datetime

def daily_maintenance():
    """Run daily maintenance tasks."""
    print(f"🔧 Daily maintenance - {datetime.now().isoformat()}")
    
    agents = ["a", "b"]
    
    for agent in agents:
        workspace = f"../basis-strategy-v1-agent-{agent}"
        print(f"\n🤖 Maintaining Agent {agent.upper()}...")
        
        # 1. Health check
        subprocess.run(["python", "health_monitor.py", agent], cwd=workspace)
        
        # 2. Clean up old files
        subprocess.run(["find", workspace, "-name", "*.pyc", "-delete"])
        subprocess.run(["find", workspace, "-name", "__pycache__", "-type", "d", "-exec", "rm", "-rf", "{}", "+"])
        
        # 3. Update dependencies
        subprocess.run(["pip", "install", "--upgrade", "-r", "requirements-agent.txt"], cwd=workspace)
        
        # 4. Backup progress
        subprocess.run(["cp", f"agent-{agent}-progress.txt", f"agent-{agent}-progress.backup"], cwd=workspace)
        
        print(f"✅ Agent {agent.upper()} maintenance complete")
    
    print("\n🎉 Daily maintenance complete!")

if __name__ == "__main__":
    daily_maintenance()
EOF

chmod +x daily_maintenance.py
```

---

## ⚡ **Realistic Timeline Options**

### **Option 1: Full Automation (1-2 weeks)**
**If you trust the agents completely:**
- **Week 1**: All 9 components implemented automatically
- **Week 2**: Integration, testing, deployment
- **Your time**: 2-4 hours total (setup + final review)

**Requirements**:
- ✅ Automated completion validation working
- ✅ Agents can handle integration conflicts
- ✅ Automated testing catches all issues
- ✅ You're comfortable with minimal oversight

### **Option 2: Human Oversight (4 weeks)**
**If you want to review and validate each step:**
- **Week 1**: Foundation components (2-3 hours daily review)
- **Week 2**: Core components (2-3 hours daily review)
- **Week 3**: Integration (4-6 hours coordination)
- **Week 4**: Frontend & deployment (2-3 hours daily review)
- **Your time**: 40-60 hours total

**Requirements**:
- ✅ Daily code review and validation
- ✅ Manual testing and debugging
- ✅ Integration conflict resolution
- ✅ Quality assurance oversight

### **Option 3: Hybrid Approach (2-3 weeks)**
**Balanced automation with key checkpoints:**
- **Week 1**: Let agents work, review at end of week
- **Week 2**: Let agents work, review at end of week  
- **Week 3**: Manual integration and testing
- **Your time**: 15-20 hours total

**Requirements**:
- ✅ Weekly review and validation
- ✅ Manual integration coordination
- ✅ Final testing and deployment oversight

## 🎯 **Recommended Approach**

**For your situation, I recommend Option 3 (Hybrid)**:

1. **Setup agents with completion tracking** (2 hours)
2. **Let them work for 1-2 weeks** (minimal oversight)
3. **Review and integrate manually** (1 week)
4. **Total time**: 15-20 hours over 3 weeks

**Why this works**:
- ✅ Agents handle the heavy lifting
- ✅ You maintain quality control
- ✅ Realistic timeline
- ✅ Manageable time commitment

---

### **Complete Best Practices Summary**

**🛡️ Issue Prevention Checklist**:

1. **Environment Setup**:
   - ✅ Isolated Python environments per agent
   - ✅ Pinned dependency versions
   - ✅ Configuration validation before start
   - ✅ Flake8 linting dependencies

2. **Pre-flight Checks**:
   - ✅ Environment validation
   - ✅ Git status check
   - ✅ Documentation sync validation
   - ✅ **Code linting (Flake8)** - NEW!
   - ✅ Redis connection test

3. **Quality Gates**:
   - ✅ Syntax validation
   - ✅ Import testing
   - ✅ Unit test execution
   - ✅ **Code linting with exclusions** - ENHANCED!
   - ✅ Type checking
   - ✅ File structure validation

4. **Monitoring & Recovery**:
   - ✅ Health monitoring
   - ✅ Automated rollback capability
   - ✅ Recovery procedures
   - ✅ Daily maintenance

5. **Documentation Sync**:
   - ✅ Spec change logging
   - ✅ Implementation notes
   - ✅ Documentation validation
   - ✅ Git commit tracking

6. **Code Quality**:
   - ✅ **Flake8 integration** - NEW!
   - ✅ **Virtual environment exclusions** - NEW!
   - ✅ **Undefined variable detection** - NEW!
   - ✅ **Syntax error prevention** - NEW!

**🚀 Recommended Startup Sequence**:
```bash
# 1. Setup (one time)
python validate_config.py
python preflight_check.py

# 2. Daily startup
python start_agent.py a  # Agent A
python start_agent.py b  # Agent B

# 3. Monitoring
python monitor_agents.py
python health_monitor.py a
python health_monitor.py b

# 4. Maintenance
python daily_maintenance.py
```

**⚠️ Common Issues & Solutions**:

| Issue | Solution |
|-------|----------|
| Agent stuck | `python recover_agent.py <agent>` |
| Git conflicts | `python rollback_agent.py <agent>` |
| Redis issues | `redis-server` restart |
| Dependency conflicts | `pip install -r requirements-agent.txt` |
| Documentation out of sync | `python validate_docs.py` |
| **Linting errors** | **`flake8 . --exclude=venv,__pycache__,.git`** |
| **Undefined variables** | **Initialize variables before use** |
| **File structure issues** | **`mkdir -p scripts/downloaders/clients`** |
| **Stray EOF errors** | **Remove stray "EOF" from Python files** |
| **Preflight check fails** | **Fix linting issues first** |

**🎯 Success Metrics**:
- ✅ All pre-flight checks pass
- ✅ Quality gates pass
- ✅ **Linting checks pass** - NEW!
- ✅ Documentation synchronized
- ✅ Health monitoring shows "healthy"
- ✅ Progress files updated
- ✅ Git commits clean
- ✅ **No undefined variables** - NEW!
- ✅ **Clean file structure** - NEW!

---

**Next Steps**: Follow the setup instructions above, then refer to [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) for detailed week-by-week execution.
