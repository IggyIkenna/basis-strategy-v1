#!/usr/bin/env python3
"""
Orphaned Tests Checker

Checks for orphaned tests by comparing actual test files in the filesystem
with test references in the quality gates configuration.

This script ensures that:
1. All test files in tests/ are referenced in quality gates config
2. All test references in quality gates config point to existing files
3. No tests are orphaned or missing from the quality gates system
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Set, Dict, Tuple
import argparse


class OrphanedTestsChecker:
    """Checks for orphaned tests in the quality gates system."""
    
    def __init__(self, project_root: str = None):
        """Initialize the checker with project root path."""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.quality_gates_file = self.project_root / "scripts" / "run_quality_gates.py"
        self.tests_dir = self.project_root / "tests"
        
    def get_actual_test_files(self) -> Set[str]:
        """Get all actual test files in the filesystem."""
        test_files = set()
        
        # Get unit tests
        unit_tests_dir = self.tests_dir / "unit"
        if unit_tests_dir.exists():
            for test_file in unit_tests_dir.glob("test_*.py"):
                test_files.add(test_file.name)
        
        # Get integration tests
        integration_tests_dir = self.tests_dir / "integration"
        if integration_tests_dir.exists():
            for test_file in integration_tests_dir.glob("test_*.py"):
                test_files.add(test_file.name)
        
        # Get E2E tests
        e2e_tests_dir = self.tests_dir / "e2e"
        if e2e_tests_dir.exists():
            for test_file in e2e_tests_dir.glob("test_*.py"):
                test_files.add(test_file.name)
        
        return test_files
    
    def get_quality_gates_references(self) -> Set[str]:
        """Get all test file references from quality gates configuration."""
        if not self.quality_gates_file.exists():
            print(f"❌ Quality gates file not found: {self.quality_gates_file}")
            return set()
        
        references = set()
        
        try:
            with open(self.quality_gates_file, 'r') as f:
                content = f.read()
                
            # Extract test references using grep-like logic
            lines = content.split('\n')
            for line in lines:
                if 'tests/unit/' in line or 'tests/integration/' in line or 'tests/e2e/' in line:
                    # Extract filename from path
                    if "'" in line:
                        # Handle quoted strings
                        parts = line.split("'")
                        for part in parts:
                            if part.startswith('tests/'):
                                filename = part.split('/')[-1]
                                if filename.endswith('.py'):
                                    references.add(filename)
                    elif '"' in line:
                        # Handle double-quoted strings
                        parts = line.split('"')
                        for part in parts:
                            if part.startswith('tests/'):
                                filename = part.split('/')[-1]
                                if filename.endswith('.py'):
                                    references.add(filename)
        
        except Exception as e:
            print(f"❌ Error reading quality gates file: {e}")
            return set()
        
        return references
    
    def check_orphaned_tests(self) -> Dict[str, List[str]]:
        """Check for orphaned tests and return results."""
        actual_files = self.get_actual_test_files()
        config_references = self.get_quality_gates_references()
        
        # Find orphaned tests (exist in filesystem but not in config)
        orphaned_tests = actual_files - config_references
        
        # Find missing tests (referenced in config but don't exist)
        missing_tests = config_references - actual_files
        
        # Find properly referenced tests
        properly_referenced = actual_files & config_references
        
        return {
            'orphaned_tests': sorted(list(orphaned_tests)),
            'missing_tests': sorted(list(missing_tests)),
            'properly_referenced': sorted(list(properly_referenced)),
            'total_actual': len(actual_files),
            'total_referenced': len(config_references)
        }
    
    def print_results(self, results: Dict[str, List[str]]) -> bool:
        """Print the orphaned tests check results."""
        print("🔍 ORPHANED TESTS CHECK")
        print("=" * 50)
        
        print(f"📊 SUMMARY:")
        print(f"   Total actual test files: {results['total_actual']}")
        print(f"   Total quality gates references: {results['total_referenced']}")
        print(f"   Properly referenced tests: {len(results['properly_referenced'])}")
        print(f"   Orphaned tests: {len(results['orphaned_tests'])}")
        print(f"   Missing tests: {len(results['missing_tests'])}")
        print()
        
        if results['orphaned_tests']:
            print("❌ ORPHANED TESTS (exist in filesystem but not in quality gates config):")
            for test in results['orphaned_tests']:
                print(f"   - {test}")
            print()
        
        if results['missing_tests']:
            print("❌ MISSING TESTS (referenced in quality gates config but don't exist):")
            for test in results['missing_tests']:
                print(f"   - {test}")
            print()
        
        if not results['orphaned_tests'] and not results['missing_tests']:
            print("✅ ALL TESTS PROPERLY REFERENCED")
            print("   No orphaned or missing tests found.")
            return True
        else:
            print("❌ ORPHANED TESTS FOUND")
            print("   Action required: Update quality gates configuration.")
            return False
    
    def generate_fix_commands(self, results: Dict[str, List[str]]) -> List[str]:
        """Generate commands to fix orphaned tests."""
        commands = []
        
        if results['orphaned_tests']:
            commands.append("# Add orphaned tests to quality gates config:")
            for test in results['orphaned_tests']:
                # Determine which category the test belongs to based on actual file location
                test_path = None
                for test_dir in ['unit', 'integration', 'e2e']:
                    test_file_path = self.tests_dir / test_dir / test
                    if test_file_path.exists():
                        test_path = f"tests/{test_dir}/{test}"
                        break
                
                if test_path:
                    commands.append(f"# Add to quality gates config: '{test_path}'")
                else:
                    commands.append(f"# Test file not found in expected location: {test}")
        
        if results['missing_tests']:
            commands.append("# Remove missing tests from quality gates config:")
            for test in results['missing_tests']:
                commands.append(f"# Remove reference to: {test}")
        
        return commands
    
    def run_check(self, verbose: bool = False) -> bool:
        """Run the complete orphaned tests check."""
        print("🔍 Checking for orphaned tests...")
        print()
        
        results = self.check_orphaned_tests()
        success = self.print_results(results)
        
        if not success and verbose:
            print("🔧 SUGGESTED FIXES:")
            print("-" * 30)
            fix_commands = self.generate_fix_commands(results)
            for command in fix_commands:
                print(command)
            print()
        
        return success


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description="Check for orphaned tests in quality gates system")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed fix suggestions")
    parser.add_argument("--project-root", help="Project root directory (default: auto-detect)")
    
    args = parser.parse_args()
    
    checker = OrphanedTestsChecker(args.project_root)
    success = checker.run_check(verbose=args.verbose)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
