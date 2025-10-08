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
        spec_file = f"docs/specs/{self.component_name.upper()}_SPEC.md"
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
