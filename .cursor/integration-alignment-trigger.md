# Integration Alignment Agent Trigger

## Purpose
This document defines when the Integration Alignment Agent should be triggered to ensure optimal timing and resource usage.

## Trigger Conditions

### **Primary Trigger: Quality Gates Pass**
The Integration Alignment Agent should be triggered **ONLY AFTER** the following conditions are met:

1. **Quality Gates Agent completes successfully**
   - All critical quality gates pass (60%+ overall pass rate)
   - Component health validation passes
   - System functionality is validated

2. **Architecture Compliance Agent completes successfully**
   - All architectural principles are followed
   - No hardcoded values remain
   - Configuration is properly loaded from YAML

3. **Task Execution Agent completes successfully**
   - Core implementation tasks are finished
   - Documentation reconciliation is complete
   - Critical fixes are implemented

### **Secondary Triggers: Manual or Scheduled**

#### **Manual Trigger**
```bash
# Trigger integration alignment manually (after quality gates pass)
cursor --agent-mode background --web-browser-mode --agent-config .cursor/integration-alignment-agent.json --instructions .cursor/integration-alignment-instructions.md
```

#### **Scheduled Trigger**
- **Daily**: Run integration alignment check during maintenance windows
- **After Major Changes**: Run after significant code or documentation changes
- **Before Releases**: Run as part of pre-release validation

## Pre-Conditions Check

Before triggering the Integration Alignment Agent, verify:

### **1. Quality Gates Status**
```bash
# Check if quality gates are passing
python3 scripts/run_quality_gates.py --category integration
```

**Required Status**: Integration alignment quality gates should show 90%+ pass rate

### **2. System Health**
```bash
# Check system health
curl -s http://localhost:8001/health/detailed
```

**Required Status**: All components should be healthy

### **3. Documentation Consistency**
```bash
# Check documentation consistency
python3 scripts/test_docs_structure_validation_quality_gates.py
```

**Required Status**: Documentation structure validation should pass

## Integration Alignment Quality Gate

### **Quality Gate Script**
- **File**: `scripts/test_integration_alignment_quality_gates.py`
- **Purpose**: Validates 100% integration alignment across all aspects
- **Categories**: 
  - Component-to-component workflow alignment
  - Function call and method signature alignment
  - Links and cross-reference validation
  - Mode-specific behavior documentation
  - Configuration and environment variable alignment
  - API documentation integration

### **Success Criteria**
- **100% Pass Rate**: All integration alignment checks must pass
- **Comprehensive Coverage**: All component specs must have cross-references
- **Configuration Documentation**: All config parameters must be documented
- **API Integration**: All API endpoints must be referenced
- **Canonical Compliance**: All specs must align with canonical architecture

## Agent Execution Flow

### **1. Pre-Execution Validation**
```bash
# Run integration alignment quality gates first
python3 scripts/test_integration_alignment_quality_gates.py
```

### **2. Agent Execution**
```bash
# Start integration alignment agent
cursor --agent-mode background --web-browser-mode --agent-config .cursor/integration-alignment-agent.json --instructions .cursor/integration-alignment-instructions.md
```

### **3. Post-Execution Validation**
```bash
# Re-run quality gates to verify improvements
python3 scripts/test_integration_alignment_quality_gates.py
```

## Expected Outcomes

### **After Successful Execution**
- **100% Integration Alignment**: All component specs aligned
- **Comprehensive Cross-References**: All components reference each other
- **Configuration Documentation**: All parameters documented
- **API Integration**: All endpoints referenced
- **Quality Gate Pass**: Integration alignment quality gates pass at 100%

### **Quality Gate Metrics**
- **Total Checks**: ~50+ integration alignment checks
- **Pass Rate**: 100% (required for success)
- **Coverage**: All component specs, configuration, API documentation
- **Validation**: Canonical architecture compliance

## Error Handling

### **If Quality Gates Fail**
1. **Do not trigger** Integration Alignment Agent
2. **Fix underlying issues** first
3. **Re-run quality gates** until they pass
4. **Then trigger** Integration Alignment Agent

### **If Integration Alignment Fails**
1. **Review failure details** in quality gate report
2. **Fix specific alignment issues** identified
3. **Re-run integration alignment** quality gates
4. **Continue until 100% pass rate** achieved

## Monitoring and Reporting

### **Quality Gate Reports**
- **Location**: `results/integration_alignment_quality_gates_report.md`
- **Content**: Detailed pass/fail status for each check
- **Format**: Markdown report with specific recommendations

### **Agent Logs**
- **Location**: `backend/logs/` directory
- **Content**: Agent execution logs and results
- **Monitoring**: Check for errors or warnings

## Best Practices

### **Timing**
- **Run after quality gates pass**: Ensures system is stable
- **Run during maintenance windows**: Minimizes disruption
- **Run before releases**: Ensures alignment before deployment

### **Frequency**
- **After major changes**: Code, documentation, or configuration changes
- **Weekly maintenance**: Regular alignment validation
- **Pre-release**: Mandatory alignment check

### **Resource Management**
- **Background mode**: Run agents in background to avoid blocking
- **Web browser mode**: Enable web access for comprehensive validation
- **Timeout handling**: Set appropriate timeouts for long-running operations

## Integration with Other Agents

### **Dependencies**
- **Quality Gates Agent**: Must complete successfully first
- **Architecture Compliance Agent**: Must complete successfully first
- **Task Execution Agent**: Must complete successfully first

### **Outputs**
- **Comprehensive Documentation Agent**: Can run after integration alignment
- **Final Validation**: Integration alignment enables final comprehensive validation

## Success Metrics

### **Immediate Success**
- Integration alignment quality gates pass at 100%
- All component specs have comprehensive cross-references
- All configuration parameters are documented
- All API endpoints are referenced

### **Long-term Success**
- Reduced documentation inconsistencies
- Improved developer experience
- Faster onboarding for new team members
- Higher code quality and maintainability

The Integration Alignment Agent should only run when the system is stable and ready for comprehensive alignment validation, ensuring optimal results and resource usage.
