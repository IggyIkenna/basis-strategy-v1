#!/usr/bin/env python3
"""Validate documentation is up to date."""

import os
from pathlib import Path

def check_doc_sync():
    """Check if documentation is synchronized."""
    docs_dir = Path("docs")
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
