# Simple Documentation Agent Prompt

## Mission
Add implementation status sections to all docs/specs/ files and fix broken links.

## Phase 1: Implementation Status
Read .cursor/docs-specs-implementation-status-instructions.md and add implementation status sections to all 19 files in docs/specs/ based on actual codebase state.

## Phase 2: Fix Broken Links  
Read .cursor/docs-consistency-instructions.md and fix all broken links by redirecting to closest relevant content.

## Validation
Run `python scripts/run_quality_gates.py --docs` after each phase.

Start with Phase 1.

