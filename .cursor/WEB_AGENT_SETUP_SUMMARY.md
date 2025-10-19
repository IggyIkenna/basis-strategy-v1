# Web Agent Setup Summary for 26-Step Build Plan

## Overview
Your `.cursor` setup has been optimized for autonomous execution of the 26-step build plan. The web agent can now execute all tasks systematically across 6 days to achieve 20/24 quality gates passing (83%) and 80% unit test coverage.

## Created Files

### 1. Web Agent Build Executor Instructions
**File**: `.cursor/web-agent-build-executor.md`
- **Purpose**: Comprehensive execution instructions for the web agent
- **Content**: Day-by-day task breakdown, quality gate protocol, success criteria
- **Usage**: Primary instruction document for autonomous execution

### 2. Web Agent Configuration
**File**: `.cursor/web-agent-config-build.json`
- **Purpose**: Optimized configuration for build plan execution
- **Content**: Build plan context, execution phases, success metrics
- **Usage**: Configuration file for web agent context

### 3. Entry Point Script
**File**: `start-build-agent.sh`
- **Purpose**: Autonomous execution script with progress tracking
- **Content**: Day-by-day execution, quality gate management, logging
- **Usage**: `./start-build-agent.sh start` for full execution

### 4. Web Agent Prompt
**File**: `WEB_AGENT_PROMPT.md`
- **Purpose**: Direct prompt for web agent execution
- **Content**: Immediate actions, task protocols, success criteria
- **Usage**: Copy-paste prompt for web agent

## Current Status Analysis

### Quality Gates Status
- **Current**: 1/16 passing (6.2%) - CRITICAL FAILURE
- **Target**: 20/24 passing (83%)
- **Critical Issues**: Backend not running, async/await violations, strategy manager needs refactor

### Backend Status
- **Issue**: Connection timeout on localhost:8001
- **Solution**: Use `./platform.sh backtest` to start backend
- **Verification**: `curl -s http://localhost:8001/health/`

## Execution Options

### Option 1: Autonomous Script Execution
```bash
# Full autonomous execution
./start-build-agent.sh start

# Individual day execution
./start-build-agent.sh day1
./start-build-agent.sh day2
# ... etc

# Status checking
./start-build-agent.sh status
./start-build-agent.sh health
```

### Option 2: Web Agent with Prompt
Use the `WEB_AGENT_PROMPT.md` content as a direct prompt for a web agent. The prompt includes:
- Immediate actions required
- Day-by-day execution plan
- Quality gate protocols
- Success criteria
- Error handling procedures

### Option 3: Manual Task Execution
Follow the instructions in `.cursor/web-agent-build-executor.md` to execute tasks manually with quality gate validation.

## 6-Day Execution Plan

### Day 1: Foundation (8 hours)
- Task 01: Environment file switching & fail-fast validation
- Task 02: Config loading & validation with Pydantic
- Task 03: Data loading quality gate for all modes

### Day 2: Core Architecture (12-16 hours)
- Task 07: Fix async/await violations (18 methods across 5 files)
- Task 10: Reference-based architecture implementation
- Task 11: Singleton pattern enforcement
- Task 06: Strategy manager refactor (DELETE transfer_manager.py)
- Task 08: Mode-agnostic architecture
- Task 09: Fail-fast configuration (62 .get() instances)

### Day 3: Integration (12-16 hours)
- Task 12: Tight loop architecture implementation
- Task 13: Consolidate duplicate risk monitors
- Task 14: Component data flow architecture
- Task 04: Complete API endpoints
- Task 05: Health & logging structure

### Day 4: Strategy Validation (12-16 hours)
- Task 15: Pure lending E2E (fix 1166% APY → 3-8%)
- Task 16: BTC basis E2E validation
- Task 17: ETH basis E2E validation

### Day 5: Complex Modes & Unit Tests (12-16 hours)
- Task 18: USDT market neutral E2E
- Tasks 19-23: Component unit tests (80% coverage each)

### Day 6: Frontend & Live Mode (12-16 hours)
- Task 24: Frontend implementation
- Task 25: Live mode framework
- Task 26: Comprehensive quality gates

## Key Features

### Autonomous Execution
- No approval requests between tasks
- Quality gates are the only checkpoints
- Automatic error handling and retry logic
- Progress tracking and logging

### Quality Gate Driven Development
- Each task has specific quality gate validation
- Failures are fixed without breaking canonical patterns
- Comprehensive quality gate reporting
- Target: 20/24 passing (83%)

### Server Management
- Automatic backend startup in backtest mode
- Health monitoring and verification
- Automatic restart on failures
- Port management and conflict resolution

### Progress Tracking
- JSON-based progress logging
- Real-time status reporting
- Task completion tracking
- Success criteria validation

## Critical Rules

### Canonical Pattern Preservation
- Reference sections are law - never violate patterns in task Reference sections
- ADR compliance - all fixes must follow Architectural Decision Records
- No backward compatibility - break cleanly, update all references

### Error Handling
- 10-minute timeout per command
- Max 3 retry attempts
- Restart backend if needed
- Document and continue (don't stop for approvals)

### Server Management
- Use `./platform.sh backtest` to start backend
- Use `./platform.sh stop` before restarting
- Restart server before long-running tests
- Check server status with `ps aux | grep python` if needed

## Success Metrics

### Daily Targets
- **Day 1**: Environment + config + data foundation ✅
- **Day 2**: Core architecture violations fixed ✅
- **Day 3**: Component integration complete ✅
- **Day 4**: 3 strategy modes E2E passing ✅
- **Day 5**: Complex strategy + 80% unit coverage ✅
- **Day 6**: Frontend + live mode + 20/24 gates passing ✅

### Final Target
- **26/26 tasks completed** (100%)
- **20/24 quality gates passing** (83%)
- **80% unit test coverage**
- **4/4 strategy modes E2E working**
- **System ready for staging deployment**

## Usage Instructions

### For Autonomous Execution
1. Run `./start-build-agent.sh start` for full execution
2. Monitor progress in `logs/build-progress.json`
3. Check logs in `logs/build-agent.log`
4. Use `./start-build-agent.sh status` for current status

### For Web Agent
1. Copy content from `WEB_AGENT_PROMPT.md`
2. Use as prompt for web agent
3. Agent will execute tasks autonomously
4. Monitor progress through quality gate results

### For Manual Execution
1. Follow instructions in `.cursor/web-agent-build-executor.md`
2. Execute tasks day by day
3. Run quality gates after each task
4. Document progress and results

## Files Created

| File | Purpose | Usage |
|------|---------|-------|
| `.cursor/web-agent-build-executor.md` | Execution instructions | Primary instruction document |
| `.cursor/web-agent-config-build.json` | Agent configuration | Web agent context |
| `start-build-agent.sh` | Autonomous script | `./start-build-agent.sh start` |
| `WEB_AGENT_PROMPT.md` | Direct prompt | Copy-paste for web agent |
| `.cursor/WEB_AGENT_SETUP_SUMMARY.md` | This summary | Reference document |

## Next Steps

1. **Start Backend**: `./platform.sh backtest`
2. **Verify Health**: `curl -s http://localhost:8001/health/`
3. **Begin Execution**: Choose one of the execution options above
4. **Monitor Progress**: Use status commands and log files
5. **Complete All 26 Tasks**: Achieve 20/24 quality gates passing

The setup is now ready for autonomous execution of your 26-step build plan. The web agent can execute all tasks systematically to achieve the target quality gate status and test coverage.
