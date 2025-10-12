# Repository Structure Validation Agent Instructions

## Mission

Validate that the actual backend repository structure aligns with canonical documentation (specs, architecture docs, patterns) and generate an updated `TARGET_REPOSITORY_STRUCTURE.md` with comprehensive file annotations and migration paths.

## Primary Objectives

1. **Structure Validation**: Compare actual `backend/src/basis_strategy_v1/` structure against canonical specifications
2. **File Annotation**: Generate comprehensive annotations for all files (KEEP/DELETE/UPDATE/MOVE/CREATE)
3. **Migration Documentation**: Provide clear migration paths for all files requiring relocation
4. **Canonical Alignment**: Ensure structure follows specs, patterns, and architecture requirements

## Analysis Process

### Step 1: Load Canonical Sources
- Load all component specifications from `docs/specs/`
- Load `CODE_STRUCTURE_PATTERNS.md` patterns
- Load `REFERENCE_ARCHITECTURE_CANONICAL.md` requirements
- Load `VENUE_ARCHITECTURE.md` patterns
- Build expected structure from canonical sources

### Step 2: Scan Current Structure
- Walk `backend/src/basis_strategy_v1/` directory tree
- Extract all Python files with their locations
- Map actual components to expected locations per specs
- Identify file sizes, modification dates, and relationships

### Step 3: Validate Structure Alignment
- Check if components exist in correct directories per specs
- Identify misplaced files (should be moved)
- Identify missing files (should be created)
- Identify obsolete files (should be deleted)
- Identify files needing updates (architecture compliance)

### Step 4: Generate Annotations
For each file, determine appropriate annotation:
- **[KEEP]**: File correctly located, follows canonical patterns
- **[DELETE]**: Obsolete file, should be removed (with justification)
- **[UPDATE]**: File exists but needs architecture compliance fixes
- **[MOVE]**: File in wrong location, migration path provided
- **[CREATE]**: Missing file required by specs

### Step 5: Document Migration Paths
- Provide detailed migration instructions for all [MOVE] files
- Include import statement updates required
- Document dependencies and affected components
- Provide justification for each migration

## Expected Output

### Updated TARGET_REPOSITORY_STRUCTURE.md
The agent should generate a comprehensive document containing:

1. **Overview**: Purpose and status of the document
2. **Annotation Legend**: Clear explanation of all annotation types
3. **Backend Structure**: Complete directory tree with annotations
4. **Migration Paths**: Detailed instructions for all [MOVE] files
5. **Missing Components**: List of files to create with specifications
6. **Files to Delete**: List of obsolete files with justifications
7. **Validation Results**: Summary of structure alignment findings
8. **Success Criteria**: Checklist of completed validations
9. **Next Steps**: Actionable items for implementing changes

### Quality Gate Integration
- Execute `scripts/test_repo_structure_quality_gates.py`
- Generate JSON results file for integration
- Ensure script is properly integrated into `run_quality_gates.py`

## Success Criteria

### Repository Structure Documentation
- [ ] 100% of backend files annotated with status
- [ ] All [MOVE] files have detailed migration paths
- [ ] All [DELETE] files have clear justifications
- [ ] All [CREATE] files reference appropriate specifications
- [ ] TARGET_REPOSITORY_STRUCTURE.md is comprehensive and actionable

### Quality Gate Integration
- [ ] Repository structure validation script created and functional
- [ ] Script integrated into `run_quality_gates.py` under `repo_structure` category
- [ ] Script generates updated TARGET_REPOSITORY_STRUCTURE.md automatically
- [ ] All validation checks pass (structure alignment, file mapping)

### Canonical Alignment
- [ ] Structure follows all component specifications
- [ ] Directory organization matches CODE_STRUCTURE_PATTERNS.md
- [ ] Architecture compliance with REFERENCE_ARCHITECTURE_CANONICAL.md
- [ ] Venue-specific patterns from VENUE_ARCHITECTURE.md applied

## Key Files to Analyze

### Component Specifications
- `docs/specs/01_POSITION_MONITOR.md`
- `docs/specs/02_EXPOSURE_MONITOR.md`
- `docs/specs/03_RISK_MONITOR.md`
- `docs/specs/04_EXECUTION_MANAGER.md`
- `docs/specs/05_DATA_PROVIDER_FACTORY.md`
- `docs/specs/06_AAVE_ADAPTER.md`
- `docs/specs/07_MORPHO_ADAPTER.md`
- `docs/specs/08_EVENT_LOGGER.md`
- `docs/specs/09_API_CALL_QUEUE.md`
- `docs/specs/11_POSITION_UPDATE_HANDLER.md`
- `docs/specs/5A_STRATEGY_FACTORY.md`
- `docs/specs/5B_BASE_STRATEGY_MANAGER.md`

### Architecture Documentation
- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`
- `docs/CODE_STRUCTURE_PATTERNS.md`
- `docs/VENUE_ARCHITECTURE.md`
- `docs/API_DOCUMENTATION.md`

### Current Structure
- `backend/src/basis_strategy_v1/` (entire directory tree)

## Integration with 9-Agent Process

This agent runs as **Agent 5.6** in Phase 3 (System Validation) after:
- Agent 1: Docs Specs Implementation Status (baseline established)
- Agent 2: Docs Consistency (docs are consistent)
- Agent 5: Quality Gates (system validated)
- Agent 5.5: Env & Config Usage Sync (documentation complete)

Before:
- Agent 6: Integration Alignment (needs clean structure baseline)

## Quality Gate Commands

```bash
# Run repository structure validation
python scripts/test_repo_structure_quality_gates.py

# Run via main quality gate runner
python scripts/run_quality_gates.py --category repo_structure
```

## Notes

- This agent should only run after documentation is clean and consistent
- Focus on file structure alignment, not implementation details
- Provide actionable migration paths, not just identification
- Ensure all annotations are justified with canonical sources
- Generate comprehensive documentation for future reference
