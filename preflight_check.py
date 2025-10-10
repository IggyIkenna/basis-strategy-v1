#!/usr/bin/env python3
"""Pre-flight checks before agent starts work."""

import subprocess
import sys
from pathlib import Path

def run_preflight_checks():
    """Run all pre-flight checks."""
    checks = [
        ("Environment", "python3 validate_config.py"),
        ("Git Status", "git status --porcelain"),
        ("Documentation", "python3 validate_docs.py"),
        ("Linting (Flake8)", "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=venv,__pycache__,.git"),
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
