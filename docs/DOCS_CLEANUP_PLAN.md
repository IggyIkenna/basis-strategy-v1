# Documentation Cleanup Plan 🧹

**Created**: October 3, 2025  
**Purpose**: Eliminate duplicate content, save context window, maintain detail through references  
**Status**: READY TO EXECUTE

---

## 🎯 **Cleanup Strategy**

### **Core Principle**
**Component specs (01-13) are the SOURCE OF TRUTH**. All other docs should REFERENCE them, not duplicate their content.

### **What We Keep**
1. **Component Specs** (specs/*.md) - Detailed implementation guides (NO CHANGES)
2. **Architectural Decisions** - Design choices reference
3. **Quick Start Guides** - User-facing docs with minimal duplication

### **What We Clean**
1. **Remove duplicate AAVE mechanics explanations** - Keep in 02_EXPOSURE_MONITOR.md only
2. **Remove duplicate timing model** - Keep in ARCHITECTURAL_DECISIONS.md only
3. **Remove duplicate config explanations** - Keep in CONFIG_WORKFLOW.md only
4. **Consolidate "getting started" content** - One clear entry point
5. **Mark task docs as deprecated** - AGENT_A/B tasks are being deleted

---

## 📋 **Document-by-Document Cleanup**

### **✅ KEEP AS-IS** (Source of Truth - No Changes)

#### **Component Specs** (specs/*.md)
- ✅ `01_POSITION_MONITOR.md` - Complete implementation spec
- ✅ `02_EXPOSURE_MONITOR.md` - **CANONICAL AAVE INDEX SOURCE**
- ✅ `03_RISK_MONITOR.md` - Risk calculations and liquidation simulation
- ✅ `04_PNL_CALCULATOR.md` - P&L reconciliation methods
- ✅ `05_STRATEGY_MANAGER.md` - Mode-specific orchestration
- ✅ `06_CEX_EXECUTION_MANAGER.md` - CEX trading logic
- ✅ `07_ONCHAIN_EXECUTION_MANAGER.md` - Blockchain operations
- ✅ `08_EVENT_LOGGER.md` - Audit logging spec
- ✅ `09_DATA_PROVIDER.md` - Data loading spec
- ✅ `10_REDIS_MESSAGING_STANDARD.md` - Inter-component communication
- ✅ `11_ERROR_LOGGING_STANDARD.md` - Error handling patterns
- ✅ `12_FRONTEND_SPEC.md` - UI specification

**Rationale**: These are implementation specs - agents need full detail here.

---

### **🔧 CONSOLIDATE & REFERENCE**

#### **INDEX.md** → **Slim down to navigation only**
**Current**: 175 lines with status, consolidation history, document lists  
**After**: ~80 lines - pure navigation

**Changes**:
```markdown
# Documentation Index 📚

**Quick Navigation**:
1. **New User?** → [START_HERE.md](START_HERE.md)
2. **Implementing?** → [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) + [REQUIREMENTS.md](REQUIREMENTS.md)
3. **Component Details?** → [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md)
4. **Architecture?** → [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md)
5. **Configuration?** → [CONFIG_WORKFLOW.md](CONFIG_WORKFLOW.md)
6. **API/Events?** → [REFERENCE.md](REFERENCE.md)

**Component Specs**: [specs/](specs/) - 12 detailed implementation guides

**Status**: All specs complete ✅ Ready for implementation

---

*For document updates, see README.md changelog*
```

**Remove**: 
- Consolidation history (belongs in git history)
- Detailed status (belongs in README.md)
- Duplicate doc listings (keep minimal navigation only)

---

#### **README.md** → **Slim to essentials**
**Current**: 367 lines with business context, parallel work details, full doc listings  
**After**: ~150 lines

**Changes**:
1. **Keep**: Business case context (lines 1-44) - essential for understanding project
2. **Keep**: Current status summary - quick status check
3. **Keep**: Quick start navigation
4. **Remove**: Detailed parallel work plan → Reference IMPLEMENTATION_ROADMAP.md instead
5. **Remove**: Duplicate doc listings → Reference INDEX.md
6. **Remove**: Detailed component descriptions → Reference COMPONENT_SPECS_INDEX.md

**Template**:
```markdown
# Component-Based Architecture Documentation 📚

## 💼 **Business Case** (keep as-is, lines 10-44)

## 📊 **Current Status**
- Component Specs: ✅ 12/12 Complete
- Ready to: Begin implementation
- Timeline: 4 weeks to production

## 🚀 **Start Here**
1. New to project? → [START_HERE.md](START_HERE.md) (5 min)
2. Implementing? → [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) (10 min)
3. Need details? → [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md)

## 📚 **Documentation Map**
**See [INDEX.md](INDEX.md) for complete navigation**

**Key Docs**:
- Implementation: [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md), [REQUIREMENTS.md](REQUIREMENTS.md)
- Architecture: [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md)
- Configuration: [CONFIG_WORKFLOW.md](CONFIG_WORKFLOW.md)
- Reference: [REFERENCE.md](REFERENCE.md)
- Components: [specs/](specs/) (12 detailed specs)
```

---

#### **START_HERE.md** → **Remove duplicate examples**
**Current**: 656 lines with AAVE mechanics examples, timing models, data file mappings  
**After**: ~250 lines

**Changes**:
1. **Keep**: Project overview (4 modes, goals)
2. **Keep**: High-level architecture decisions (wallet model, timing constraints)
3. **Remove**: Detailed AAVE mechanics → "See specs/02_EXPOSURE_MONITOR.md for AAVE index details"
4. **Remove**: Data file mappings → "See specs/09_DATA_PROVIDER.md for data file structure"
5. **Remove**: Detailed timing model → "See ARCHITECTURAL_DECISIONS.md for complete timing model"
6. **Remove**: Phase 1-4 weekly breakdown → "See IMPLEMENTATION_ROADMAP.md for timeline"

**Example Replacement**:
```markdown
### **AAVE Position Naming** 🏦
For complete details on AAVE index mechanics and position tracking, see **[specs/02_EXPOSURE_MONITOR.md](specs/02_EXPOSURE_MONITOR.md)** (lines 27-107).

**Quick Summary**:
- Wallet holds: `aWeETH` (constant), `variableDebtWETH` (constant)
- AAVE positions: Derived via liquidity index multiplication
- **CRITICAL**: aToken amounts are NOT 1:1 with supplied tokens!

**Example**: Supply 100 weETH when index=1.05 → Receive 95.24 aWeETH
```

---

#### **COMPONENT_SPECS_INDEX.md** → **Pure component list**
**Current**: 316 lines with component descriptions, dep matrix, file mapping, implementation priority  
**After**: ~120 lines

**Changes**:
1. **Keep**: Component overview list with one-sentence descriptions
2. **Keep**: Component interaction flow diagram
3. **Keep**: Dependency matrix (essential for integration)
4. **Keep**: Backend file mapping
5. **Remove**: Implementation priority details → "See IMPLEMENTATION_ROADMAP.md for week-by-week plan"
6. **Remove**: Config infrastructure details → "See CONFIG_WORKFLOW.md for config integration"
7. **Remove**: Detailed component descriptions → "See individual specs for details"

---

#### **ARCHITECTURAL_DECISIONS.md** → **Keep, mark as canonical**
**Current**: Good structure, but could add references  
**After**: Add "**CANONICAL SOURCE**" markers

**Add at top**:
```markdown
# Architectural Decisions - CANONICAL REFERENCE 🏛️

**Status**: ✅ APPROVED - Single source of truth for all design decisions  
**Usage**: All other docs REFERENCE this file, do not duplicate content

**Cross-References**:
- AAVE mechanics details → See specs/02_EXPOSURE_MONITOR.md
- Implementation order → See IMPLEMENTATION_ROADMAP.md
- Component details → See COMPONENT_SPECS_INDEX.md
```

---

#### **IMPLEMENTATION_ROADMAP.md** → **Consolidate task planning**
**Current**: 983 lines with status, critical fixes, architecture decisions  
**After**: ~400 lines

**Changes**:
1. **Keep**: Current status & critical fixes (lines 10-40)
2. **Keep**: Week-by-week implementation plan
3. **Keep**: Agent A/B parallel work strategy
4. **Remove**: Architecture decisions → "See ARCHITECTURAL_DECISIONS.md"
5. **Remove**: Component descriptions → "See COMPONENT_SPECS_INDEX.md"
6. **Remove**: Duplicate AAVE explanations → Reference specs

**Note**: Since AGENT_A/B_IMPLEMENTATION_TASKS.md are being deleted, add deprecation notice:
```markdown
## 📋 **Task Tracking**

**Note**: Detailed task files (AGENT_A_IMPLEMENTATION_TASKS.md, AGENT_B_IMPLEMENTATION_TASKS.md) 
have been removed. All task information now consolidated in:
- This file: Week-by-week roadmap
- REQUIREMENTS.md: Component-by-component acceptance criteria
```

---

#### **REQUIREMENTS.md** → **Focus on acceptance criteria**
**Current**: 1,003 lines with detailed tasks and component specs  
**After**: ~600 lines

**Changes**:
1. **Keep**: Component implementation tasks (IMPL-01 through IMPL-13)
2. **Keep**: Acceptance criteria for each component
3. **Keep**: Test coverage requirements
4. **Remove**: Duplicate component spec content → "See specs/*.md for implementation details"
5. **Remove**: Duplicate architecture → "See ARCHITECTURAL_DECISIONS.md"
6. **Consolidate**: Reduce task descriptions, focus on acceptance criteria

**Template for each component**:
```markdown
#### **IMPL-01: Position Monitor**
**File**: `backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py`  
**Spec**: **[specs/01_POSITION_MONITOR.md](specs/01_POSITION_MONITOR.md)** ← Full implementation details  
**Owner**: Agent A

**Tasks**: [Brief bullet list]
- Implement TokenBalanceMonitor
- Implement DerivativeBalanceMonitor
- Create PositionMonitor wrapper
- Add Redis publishing
- Live reconciliation

**Acceptance Criteria**: [Specific checklist]
- [ ] All wallet tokens tracked
- [ ] AAVE aToken amounts use liquidity index
- [ ] Perp positions per-exchange
- [ ] Tests pass (80%+ coverage)

**Estimate**: 1.5 days  
**Dependencies**: None
```

---

#### **CONFIG_WORKFLOW.md** → **Keep as config reference**
**Current**: 795 lines - good structure  
**After**: ~500 lines

**Changes**:
1. **Keep**: Configuration workflow guide
2. **Keep**: Validation guide
3. **Keep**: Mode/venue/share class configs
4. **Remove**: BacktestService integration details (too implementation-specific) → "See backend code"
5. **Simplify**: Reduce example configs (show structure only)

---

#### **REFERENCE.md** → **Already consolidated, minimal cleanup**
**Current**: Unified reference (config+API+events)  
**After**: Add cross-references to specs

**Add at top**:
```markdown
# Unified Reference Guide 📚

**Purpose**: Quick reference for config, API, events, components, errors  
**For Implementation Details**: See [specs/](specs/) for component-specific specs

**Cross-References**:
- Component data structures → See individual specs
- AAVE mechanics → specs/02_EXPOSURE_MONITOR.md
- Execution logic → specs/06_CEX_EXECUTION_MANAGER.md, specs/07_ONCHAIN_EXECUTION_MANAGER.md
```

---

### **📋 WORKING DOCUMENTS** (Keep for now, archive after completion)

#### **Agent Task Files** (Active - needed for implementation):
- ✅ `AGENT_A_IMPLEMENTATION_TASKS.md` → Keep as working doc
- ✅ `AGENT_B_IMPLEMENTATION_TASKS.md` → Keep as working doc
- ✅ `CODE_AUDIT_AND_CLEANUP_ANALYSIS.md` → Keep as reference

**Note**: Add header noting these are working documents:
```markdown
# [Title]

**Status**: 🚧 WORKING DOCUMENT - Active implementation tasks  
**Archive After**: Tasks completed and verified  
**See Also**: [IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md) for consolidated plan
```

#### **Files to Mark for Future Deprecation**:
Files that may be consolidated later (but keep for now):
- `CLEANUP_AND_INTEGRATION_PLAN.md` → Content overlaps IMPLEMENTATION_ROADMAP.md
- `REPO_INTEGRATION_PLAN.md` → Content overlaps COMPONENT_SPECS_INDEX.md

**Action**: Add note at top: "**Note**: This content will be consolidated into [LOCATION] after current implementation phase."

---

### **📄 USER-FACING DOCS** (Minimal cleanup)

These are external-facing, keep mostly as-is:

#### **QUICK_START.md**
**Current**: Good structure  
**Changes**: Add "For implementation details, see IMPLEMENTATION_ROADMAP.md" at top

#### **USER_GUIDE.md**
**Current**: Good structure  
**Changes**: Add "For technical details, see specs/" at top

#### **DEPLOYMENT_GUIDE.md**
**Current**: Good structure  
**Changes**: Minimal, maybe add config reference

#### **SCRIPTS_DATA_GUIDE.md**
**Current**: Good structure  
**Changes**: Add "See specs/09_DATA_PROVIDER.md for data requirements"

#### **WALLET_SETUP_GUIDE.md**, **KING_TOKEN_HANDLING_GUIDE.md**, etc.
**Current**: Specific guides  
**Changes**: Add cross-references where relevant

---

## 📊 **Content Reduction Summary**

| Document | Before (lines) | After (lines) | Reduction | Strategy |
|----------|----------------|---------------|-----------|----------|
| INDEX.md | 175 | 80 | -54% | Navigation only |
| README.md | 367 | 150 | -59% | Remove duplicates |
| START_HERE.md | 656 | 250 | -62% | Reference specs |
| COMPONENT_SPECS_INDEX.md | 316 | 120 | -62% | Pure component list |
| IMPLEMENTATION_ROADMAP.md | 983 | 400 | -59% | Remove arch decisions |
| REQUIREMENTS.md | 1,003 | 600 | -40% | Focus on criteria |
| CONFIG_WORKFLOW.md | 795 | 500 | -37% | Simplify examples |
| **Total Core Docs** | **4,295** | **2,100** | **-51%** | |
| **Component Specs** | **6,000** | **6,000** | **0%** | Keep detailed |
| **User Docs** | **~3,000** | **~2,900** | **-3%** | Minimal cleanup |
| **GRAND TOTAL** | **~13,300** | **~11,000** | **-17%** | |

**Result**: ~2,300 lines removed from core docs while maintaining all implementation detail in specs.

---

## 🎯 **Reference Pattern**

### **Instead of duplicating**:
```markdown
### **AAVE Index Mechanics**

AAVE uses index-based growth where:
- aWeETH balance is CONSTANT after supply
- Underlying weETH grows via index
- Index determines how much aWeETH you receive

Example:
At supply (t=0): Supply 100 weETH when index = 1.05
aWeETH_received = 100 / 1.05 = 95.24

At withdrawal (t=n): Index = 1.08
weETH_claimable = 95.24 × 1.08 = 102.86
```

### **Use references**:
```markdown
### **AAVE Index Mechanics**

**CRITICAL**: AAVE uses index-based growth for supply/borrow calculations.

**See [specs/02_EXPOSURE_MONITOR.md](specs/02_EXPOSURE_MONITOR.md)** (lines 27-107) for:
- Complete AAVE index mechanics
- Conversion chain examples
- Why indices are NOT 1:1
- Impact on position tracking

**Quick Summary**: aToken amounts are CONSTANT scaled balances. 
Underlying claimable grows via `underlying = aToken × liquidityIndex`.
```

---

## 🚀 **Execution Plan**

### **Phase 1: Mark Deprecated** (5 min)
1. Add deprecation notice to AGENT_A/B task files
2. Add deprecation notice to CODE_AUDIT_AND_CLEANUP_ANALYSIS.md
3. Note in README.md that these are deprecated

### **Phase 2: Core Docs Cleanup** (30 min)
Execute cleanups in order:
1. INDEX.md → Navigation only
2. README.md → Remove duplicates
3. START_HERE.md → Add references
4. COMPONENT_SPECS_INDEX.md → Slim down
5. IMPLEMENTATION_ROADMAP.md → Remove arch decisions
6. REQUIREMENTS.md → Focus on acceptance criteria

### **Phase 3: Add Cross-References** (15 min)
1. Add "CANONICAL SOURCE" markers to ARCHITECTURAL_DECISIONS.md
2. Add cross-reference sections to docs
3. Update REFERENCE.md with spec references

### **Phase 4: User Docs Touchups** (10 min)
1. Add spec references to QUICK_START.md
2. Add spec references to USER_GUIDE.md
3. Add spec references to DEPLOYMENT_GUIDE.md

### **Total Time**: ~60 minutes

---

## ✅ **Success Criteria**

After cleanup:
- [ ] No duplicate AAVE mechanics explanations (canonical in specs/02_EXPOSURE_MONITOR.md)
- [ ] No duplicate timing model (canonical in ARCHITECTURAL_DECISIONS.md)
- [ ] No duplicate config explanations (canonical in CONFIG_WORKFLOW.md)
- [ ] All docs < 500 lines (except component specs and ARCHITECTURAL_DECISIONS.md)
- [ ] Every doc has clear "See X for details" references
- [ ] Task docs marked as deprecated
- [ ] INDEX.md is pure navigation (~80 lines)
- [ ] README.md is concise overview (~150 lines)
- [ ] Component specs unchanged (still detailed)
- [ ] Agent can find any info in <3 clicks

---

## 📝 **Implementation Notes**

### **What to Keep Duplicated**
Some duplication is okay for:
1. **Quick summaries** in overview docs (1-2 sentences)
2. **Critical warnings** (e.g., "AAVE is NOT 1:1!")
3. **Essential examples** in component specs (source of truth)

### **What to Always Reference**
Always reference specs for:
1. Detailed implementation logic
2. Complete data structures
3. Code examples
4. Test cases
5. Integration patterns

### **Reference Format**
Use this pattern consistently:
```markdown
**See [specs/XX_COMPONENT.md](specs/XX_COMPONENT.md)** for complete details.

**Quick Summary**: [1-2 sentence summary]
```

---

## 🎯 **Final State**

After cleanup, documentation structure will be:

**Navigation** (< 100 lines each):
- INDEX.md - Pure navigation
- README.md - Quick project overview

**Implementation** (moderate length):
- IMPLEMENTATION_ROADMAP.md (~400 lines) - Week-by-week plan
- REQUIREMENTS.md (~600 lines) - Component acceptance criteria
- COMPONENT_SPECS_INDEX.md (~120 lines) - Component list & dependencies

**Reference** (keep detailed):
- ARCHITECTURAL_DECISIONS.md - Design decisions (canonical)
- CONFIG_WORKFLOW.md (~500 lines) - Config guide
- REFERENCE.md - Unified reference (config/API/events)

**Implementation Specs** (keep detailed):
- specs/*.md (12 files, ~6,000 lines total) - SOURCE OF TRUTH

**User Guides** (minimal cleanup):
- QUICK_START.md, USER_GUIDE.md, DEPLOYMENT_GUIDE.md, etc.

**Total**: ~11,000 lines (down from ~13,300, -17%)

---

**Ready to execute?** This plan can be executed in ~1 hour with minimal risk. All details remain accessible through references, but duplicate content is eliminated.

