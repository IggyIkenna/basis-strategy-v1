# Agent Startup Prompt for Basis Strategy Refactor

## 🎯 **Mission Overview**

You are a specialized refactor agent for the Basis Strategy project. Your mission is to execute the **Refactor Standard Process** using the new 19-section documentation structure and implementation gap detection quality gates.

## 📋 **Current Status & Context**

### **Project State**
- **Documentation Structure**: 92% compliant (19/23 specs follow 19-section format)
- **Implementation Success Rate**: 9.5% (significant work needed)
- **Quality Gates**: New docs validation gates are working and identifying real gaps
- **Canonical Examples**: `02_EXPOSURE_MONITOR.md` and `03_RISK_MONITOR.md` are the "perfect" reference implementations

### **Key Files to Reference**
- **Agent Instructions**: `.cursor/REFACTOR_WEB_AGENT_PROMPT.md` - Complete 9-agent chain workflow
- **Canonical Examples**: `docs/specs/02_EXPOSURE_MONITOR.md`, `docs/specs/03_RISK_MONITOR.md`
- **Template**: `docs/COMPONENT_SPEC_TEMPLATE.md` - 19-section standardized format
- **Quality Gates**: `tests/test_implementation_gap_quality_gates.py` - Implementation gap detection
- **Task Sequence**: `.cursor/tasks/00_master_task_sequence.md` - Complete task roadmap

## 🚀 **Your First Actions**

### **Step 1: Run Quality Gates to Get Current State**
```bash
# Run the new docs validation quality gates
python scripts/run_quality_gates.py --category docs_validation

# Run implementation gap analysis
python tests/test_implementation_gap_quality_gates.py

# Run detailed gap analysis (REMOVED - was generating useless report)
# python tests/analyze_implementation_gaps.py
```

### **Step 2: Review the Gap Reports**
- Check `implementation_gap_report.json` for detailed component analysis
- Review `docs/IMPLEMENTATION_GAP_REPORT.md` for markdown summary
- Focus on **HIGH priority gaps** first (14 components with missing implementations)

### **Step 3: Start with Agent 1: Docs Specs Implementation Status**
Based on `.cursor/REFACTOR_WEB_AGENT_PROMPT.md`, begin with:

1. **Validate 19-section structure** for all component specs
2. **Use canonical examples** (`02_EXPOSURE_MONITOR`, `03_RISK_MONITOR`) as templates
3. **Generate task files** for missing implementations identified by quality gates
4. **Update implementation status** sections in all specs

## 🎯 **Success Criteria**

Your work is successful when you achieve:
- **Documentation Structure**: 100% of specs follow 19-section format
- **Implementation Alignment**: ≥80% implementation gap closure
- **Quality Gates**: 75%+ pass rate including docs validation
- **Canonical Compliance**: All components follow canonical patterns

## 📚 **Critical References**

### **Canonical Examples (Study These First)**
- `docs/specs/02_EXPOSURE_MONITOR.md` - Perfect example of 19-section structure
- `docs/specs/03_RISK_MONITOR.md` - Perfect example of mode-agnostic implementation

### **Quality Gate Results (Current Gaps)**
- **14 HIGH Priority**: Missing implementations (04_PNL_CALCULATOR, 07B_EXECUTION_INTERFACES, etc.)
- **4 MEDIUM Priority**: Compliance issues (01_POSITION_MONITOR, 02_EXPOSURE_MONITOR, etc.)
- **3 LOW Priority**: Minor issues (03_RISK_MONITOR, 06_EXECUTION_MANAGER, etc.)

### **Agent Workflow**
Follow the 9-agent chain from `.cursor/REFACTOR_WEB_AGENT_PROMPT.md`:
1. **Agent 1**: Docs Specs Implementation Status (Priority: Highest)
2. **Agent 2**: Docs Consistency (Priority: High)
3. **Agent 3**: Task Execution (Priority: High)
4. **Agent 4**: Architecture Compliance (Priority: High)
5. **Agent 5**: Quality Gates (Priority: High)
6. **Agent 6**: Integration Alignment (Priority: Medium)
7. **Agent 7**: Frontend Implementation (Priority: Medium)
8. **Agent 8**: Live Mode Validation (Priority: Low)
9. **Agent 9**: Final Quality Gates (Priority: Low)

## 🔧 **Key Commands**

```bash
# Start backend for testing
./platform.sh backtest

# Run quality gates
python scripts/run_quality_gates.py --category docs_validation
python scripts/run_quality_gates.py --category components
python scripts/run_quality_gates.py --category integration

# Run specific gap analysis
python tests/test_implementation_gap_quality_gates.py
# python tests/analyze_implementation_gaps.py  # REMOVED - was generating useless report

# Check current quality gate status
python scripts/run_quality_gates.py --list-categories
```

## ⚠️ **Important Notes**

1. **Always reference canonical examples** when implementing new components
2. **Use 19-section structure** for all component specifications
3. **Run quality gates frequently** to track progress
4. **Generate task files** for implementation gaps you identify
5. **Follow the agent sequence** - don't skip ahead to later agents
6. **Update documentation first**, then implement code changes

## 🎯 **Your Immediate Next Steps**

1. **Run the quality gates** to get current state
2. **Study the canonical examples** (`02_EXPOSURE_MONITOR`, `03_RISK_MONITOR`)
3. **Start with Agent 1** from the refactor prompt
4. **Focus on HIGH priority gaps** first
5. **Generate task files** for missing implementations

## 📞 **Support Resources**

- **Complete Agent Instructions**: `.cursor/REFACTOR_WEB_AGENT_PROMPT.md`
- **Task Sequence**: `.cursor/tasks/00_master_task_sequence.md`
- **Architecture Guide**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`
- **Quality Gates**: `scripts/run_quality_gates.py`

---

**Ready to start? Begin with Step 1 above and follow the 9-agent chain workflow!** 🚀
