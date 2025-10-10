#!/usr/bin/env python3
"""
Integration Alignment Quality Gates

Purpose: Validate 100% integration alignment across component specifications, 
         API documentation, configuration systems, and canonical architectural principles.

Status: ✅ IMPLEMENTED
Updated: January 6, 2025
Last Reviewed: January 6, 2025
Status: ✅ Aligned with canonical architectural principles
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class IntegrationAlignmentQualityGates:
    """Quality gates for integration alignment validation."""
    
    def __init__(self):
        self.project_root = project_root
        self.docs_dir = self.project_root / "docs"
        self.specs_dir = self.docs_dir / "specs"
        self.configs_dir = self.project_root / "configs"
        self.results = {
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "warnings": 0,
            "details": []
        }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all integration alignment quality gates."""
        print("🚀 Running Integration Alignment Quality Gates...")
        
        # Phase 1: Component-to-Component Workflow Alignment
        self.check_component_workflow_alignment()
        
        # Phase 2: Function Call and Method Signature Alignment
        self.check_method_signature_alignment()
        
        # Phase 3: Links and Cross-Reference Validation
        self.check_cross_reference_completeness()
        
        # Phase 4: Mode-Specific Behavior Documentation
        self.check_mode_specific_behavior()
        
        # Phase 5: Configuration and Environment Variable Alignment
        self.check_configuration_alignment()
        
        # Phase 6: API Documentation Integration
        self.check_api_documentation_integration()
        
        return self.results
    
    def check_component_workflow_alignment(self):
        """Phase 1: Validate component-to-component workflow alignment."""
        print("📋 Phase 1: Component-to-Component Workflow Alignment")
        
        # Check for canonical architecture compliance
        self._check_file_contains(
            "docs/REFERENCE_ARCHITECTURE_CANONICAL.md",
            "Component References (Set at Init)",
            "Canonical architecture compliance"
        )
        
        # Check tight loop architecture
        self._check_file_contains(
            "docs/WORKFLOW_GUIDE.md",
            "Tight Loop Architecture",
            "Tight loop architecture documentation"
        )
        
        # Check component specs have proper structure
        spec_files = list(self.specs_dir.glob("*.md"))
        for spec_file in spec_files:
            if spec_file.name.startswith("01_") or spec_file.name.startswith("02_"):
                self._check_file_contains(
                    f"docs/specs/{spec_file.name}",
                    "Component References (Set at Init)",
                    f"Component references in {spec_file.name}"
                )
    
    def check_method_signature_alignment(self):
        """Phase 2: Validate function call and method signature alignment."""
        print("📋 Phase 2: Function Call and Method Signature Alignment")
        
        # Check canonical method signatures
        spec_files = list(self.specs_dir.glob("*.md"))
        for spec_file in spec_files:
            if spec_file.name.startswith("0"):
                self._check_file_contains(
                    f"docs/specs/{spec_file.name}",
                    "update_state(timestamp: pd.Timestamp",
                    f"Canonical method signature in {spec_file.name}"
                )
        
        # Check synchronous execution patterns
        self._check_file_contains(
            "docs/REFERENCE_ARCHITECTURE_CANONICAL.md",
            "Synchronous Component Execution",
            "Synchronous execution documentation"
        )
    
    def check_cross_reference_completeness(self):
        """Phase 3: Validate links and cross-reference completeness."""
        print("📋 Phase 3: Links and Cross-Reference Validation")
        
        # Check comprehensive cross-references in component specs
        spec_files = list(self.specs_dir.glob("*.md"))
        for spec_file in spec_files:
            if spec_file.name.startswith("0"):
                self._check_file_contains(
                    f"docs/specs/{spec_file.name}",
                    "Component Integration",
                    f"Comprehensive cross-references in {spec_file.name}"
                )
        
        # Check cross-reference format consistency
        for spec_file in spec_files:
            if spec_file.name.startswith("0"):
                self._check_file_contains(
                    f"docs/specs/{spec_file.name}",
                    "[.*]\(.*\.md\)",
                    f"Cross-reference format in {spec_file.name}",
                    use_regex=True
                )
    
    def check_mode_specific_behavior(self):
        """Phase 4: Validate mode-specific behavior documentation."""
        print("📋 Phase 4: Mode-Specific Behavior Documentation")
        
        # Check BASIS_EXECUTION_MODE usage
        spec_files = list(self.specs_dir.glob("*.md"))
        for spec_file in spec_files:
            if spec_file.name.startswith("0"):
                self._check_file_contains(
                    f"docs/specs/{spec_file.name}",
                    "BASIS_EXECUTION_MODE",
                    f"Execution mode documentation in {spec_file.name}"
                )
        
        # Check mode-aware vs mode-agnostic documentation
        self._check_file_contains(
            "docs/REFERENCE_ARCHITECTURE_CANONICAL.md",
            "Mode-Agnostic Architecture",
            "Mode-agnostic architecture documentation"
        )
    
    def check_configuration_alignment(self):
        """Phase 5: Validate configuration and environment variable alignment."""
        print("📋 Phase 5: Configuration and Environment Variable Alignment")
        
        # Check configuration parameter documentation
        spec_files = list(self.specs_dir.glob("*.md"))
        for spec_file in spec_files:
            if spec_file.name.startswith("0"):
                self._check_file_contains(
                    f"docs/specs/{spec_file.name}",
                    "Configuration Parameters",
                    f"Configuration documentation in {spec_file.name}"
                )
        
        # Check environment variable documentation
        for spec_file in spec_files:
            if spec_file.name.startswith("0"):
                self._check_file_contains(
                    f"docs/specs/{spec_file.name}",
                    "Environment Variables",
                    f"Environment variable documentation in {spec_file.name}"
                )
        
        # Check YAML configuration references
        self._check_file_contains(
            "docs/specs/CONFIGURATION.md",
            "YAML Configuration",
            "YAML configuration documentation"
        )
        
        # Check environment variable definitions
        self._check_file_contains(
            "docs/ENVIRONMENT_VARIABLES.md",
            "BASIS_EXECUTION_MODE",
            "Environment variable definitions"
        )
    
    def check_api_documentation_integration(self):
        """Phase 6: Validate API documentation integration."""
        print("📋 Phase 6: API Documentation Integration")
        
        # Check API documentation exists
        self._check_file_exists(
            "docs/API_DOCUMENTATION.md",
            "API documentation file"
        )
        
        # Check API endpoint references in component specs
        spec_files = list(self.specs_dir.glob("*.md"))
        api_related_specs = ["13_BACKTEST_SERVICE.md", "14_LIVE_TRADING_SERVICE.md", "15_EVENT_DRIVEN_STRATEGY_ENGINE.md"]
        
        for spec_file in spec_files:
            if spec_file.name in api_related_specs:
                self._check_file_contains(
                    f"docs/specs/{spec_file.name}",
                    "API Integration",
                    f"API integration documentation in {spec_file.name}"
                )
        
        # Check cross-references to API documentation
        for spec_file in spec_files:
            if spec_file.name in api_related_specs:
                self._check_file_contains(
                    f"docs/specs/{spec_file.name}",
                    "API_DOCUMENTATION.md",
                    f"API documentation cross-reference in {spec_file.name}"
                )
    
    def _check_file_exists(self, file_path: str, description: str):
        """Check if a file exists."""
        self.results["total_checks"] += 1
        full_path = self.project_root / file_path
        
        if full_path.exists():
            self.results["passed_checks"] += 1
            self.results["details"].append(f"✅ {description}: File exists")
        else:
            self.results["failed_checks"] += 1
            self.results["details"].append(f"❌ {description}: File missing - {file_path}")
    
    def _check_file_contains(self, file_path: str, pattern: str, description: str, use_regex: bool = False):
        """Check if a file contains a specific pattern."""
        self.results["total_checks"] += 1
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            self.results["failed_checks"] += 1
            self.results["details"].append(f"❌ {description}: File missing - {file_path}")
            return
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if use_regex:
                if re.search(pattern, content):
                    self.results["passed_checks"] += 1
                    self.results["details"].append(f"✅ {description}: Pattern found")
                else:
                    self.results["failed_checks"] += 1
                    self.results["details"].append(f"❌ {description}: Pattern not found - {pattern}")
            else:
                if pattern in content:
                    self.results["passed_checks"] += 1
                    self.results["details"].append(f"✅ {description}: Pattern found")
                else:
                    self.results["failed_checks"] += 1
                    self.results["details"].append(f"❌ {description}: Pattern not found - {pattern}")
        except Exception as e:
            self.results["failed_checks"] += 1
            self.results["details"].append(f"❌ {description}: Error reading file - {str(e)}")
    
    def generate_report(self) -> str:
        """Generate quality gates report."""
        total = self.results["total_checks"]
        passed = self.results["passed_checks"]
        failed = self.results["failed_checks"]
        warnings = self.results["warnings"]
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        report = f"""
# Integration Alignment Quality Gates Report

## Summary
- **Total Checks**: {total}
- **Passed**: {passed}
- **Failed**: {failed}
- **Warnings**: {warnings}
- **Pass Rate**: {pass_rate:.1f}%

## Status
"""
        
        if pass_rate >= 100:
            report += "✅ **PASS** - 100% integration alignment achieved\n"
        elif pass_rate >= 90:
            report += "⚠️ **PARTIAL** - Minor integration alignment issues\n"
        else:
            report += "❌ **FAIL** - Significant integration alignment issues\n"
        
        report += "\n## Detailed Results\n"
        for detail in self.results["details"]:
            report += f"- {detail}\n"
        
        return report

def main():
    """Main execution function."""
    print("🚀 Starting Integration Alignment Quality Gates...")
    
    # Initialize quality gates
    qg = IntegrationAlignmentQualityGates()
    
    # Run all checks
    results = qg.run_all_checks()
    
    # Generate report
    report = qg.generate_report()
    print(report)
    
    # Write report to file
    report_file = project_root / "results" / "integration_alignment_quality_gates_report.md"
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Report written to: {report_file}")
    
    # Return exit code based on results
    total = results["total_checks"]
    passed = results["passed_checks"]
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    if pass_rate >= 100:
        print("✅ Integration Alignment Quality Gates: PASS")
        return 0
    elif pass_rate >= 90:
        print("⚠️ Integration Alignment Quality Gates: PARTIAL")
        return 1
    else:
        print("❌ Integration Alignment Quality Gates: FAIL")
        return 2

if __name__ == "__main__":
    sys.exit(main())
