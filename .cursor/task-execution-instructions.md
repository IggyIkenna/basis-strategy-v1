# Task Execution Agent Instructions

## Mission
Execute core implementation tasks and fixes from the master task sequence in proper order.

## Primary Objectives

### 1. Sequential Task Execution
- Execute tasks from `.cursor/tasks/00_master_task_sequence.md` in sequence
- Implement critical fixes and refactoring requirements
- Ensure all core functionality is working
- Validate implementation against task requirements
- Report progress after each task completion

### 2. Quality Validation
- Run quality gates after each task completion
- Ensure no regressions are introduced
- Maintain architecture compliance throughout
- Validate that implementation matches task requirements

### 3. Progress Reporting
- Report progress after each task completion
- Highlight any blockers or issues encountered
- Provide detailed explanations of what was accomplished
- Show current status vs target

## Execution Process

### Step 1: Task Sequence Review
1. **Read Master Task Sequence**
   - Review `.cursor/tasks/00_master_task_sequence.md`
   - Understand task dependencies and order
   - Identify critical path tasks

2. **Validate Prerequisites**
   - Ensure backend server is running
   - Verify all required dependencies are available
   - Check that previous phase agents completed successfully

### Step 2: Sequential Execution
1. **Execute Tasks in Order**
   - Start with first task in sequence
   - Complete each task fully before moving to next
   - Validate task completion criteria
   - Run quality gates after each task

2. **Implementation Validation**
   - Ensure implementation matches task requirements
   - Check that no regressions were introduced
   - Verify architecture compliance is maintained
   - Validate that core functionality works

### Step 3: Progress Tracking
1. **After Each Task**
   - Report what was accomplished
   - Show quality gate results
   - Highlight any issues or blockers
   - Confirm readiness for next task

2. **Continuous Validation**
   - Run quality gates after each task
   - Check for regressions
   - Validate architecture compliance
   - Ensure system stability

## Expected Output

### Progress Reports
```markdown
## Task Execution Progress Report

### Task [X]: [Task Name]
- **Status**: ✅ Completed / ⚠️ Partial / ❌ Failed
- **What was accomplished**: [Detailed description]
- **Quality Gates**: [Pass/Fail status]
- **Architecture Compliance**: [Compliant/Non-compliant]
- **Issues**: [Any blockers or problems]
- **Next Steps**: [What's needed for next task]

### Overall Progress
- **Tasks Completed**: X/Y
- **Quality Gates**: X/Y passing
- **Architecture Compliance**: [Status]
- **System Health**: [Status]
```

## Success Criteria
- All tasks completed in sequence
- Quality gates pass after each task
- No regressions introduced
- Architecture compliance maintained
- Implementation matches task requirements
- System remains stable throughout

## Web Agent Integration
This agent is designed to work alongside the main web agent:
- **Priority**: High (runs after docs consistency)
- **Context Sharing**: Yes (shares task and implementation context)
- **Compatibility**: Full web agent compatibility
- **Triggers**: After docs consistency agent completes
- **Dependencies**: Docs specs implementation status, docs consistency
