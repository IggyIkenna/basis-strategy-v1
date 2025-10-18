#!/usr/bin/env python3
"""
Quality Gate: Documentation Structure Validation
Validates that all docs/ files (except docs/specs/) have proper structure
and that all docs/specs/ files have implementation status sections.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Set

# 18-Section Standard Format for Component Specs (from COMPONENT_SPECS_INDEX.md template)
REQUIRED_SECTIONS = [
    "Purpose",
    "📚 **Canonical Sources**",  # NEW section name
    "Responsibilities", 
    "State",
    "Component References (Set at Init)",
    "Configuration Parameters",
    "Environment Variables",
    "Config Fields Used",
    "Data Provider Queries",
    "Core Methods",
    "Data Access Pattern",
    "Mode-Aware Behavior",
    "**MODE-AGNOSTIC IMPLEMENTATION EXAMPLE**",  # NEW section
    "Event Logging Requirements",
    "Error Codes",
    "Quality Gates",
    "Integration Points",
    "Current Implementation Status",
    "Related Documentation"
]

def find_docs_files(docs_dir: str = "docs/") -> Tuple[List[str], List[str]]:
    """Find all markdown files in docs/ and docs/specs/ directories."""
    all_docs = []
    specs_docs = []
    
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                if 'specs' in file_path:
                    specs_docs.append(file_path)
                else:
                    all_docs.append(file_path)
    
    return all_docs, specs_docs

def validate_docs_structure(file_path: str) -> Dict:
    """Validate that a docs/ file (not in specs/) has proper structure."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for basic structure elements
        has_title = bool(re.search(r'^#\s+.+', content, re.MULTILINE))
        has_purpose = bool(re.search(r'(purpose|overview|introduction)', content, re.IGNORECASE))
        has_sections = len(re.findall(r'^##\s+', content, re.MULTILINE)) >= 2
        
        # Check for canonical sources reference
        has_canonical_sources = bool(re.search(r'canonical.*source', content, re.IGNORECASE))
        
        return {
            'file': file_path,
            'has_title': has_title,
            'has_purpose': has_purpose,
            'has_sections': has_sections,
            'has_canonical_sources': has_canonical_sources,
            'structure_score': sum([has_title, has_purpose, has_sections, has_canonical_sources])
        }
    
    except Exception as e:
        return {
            'file': file_path,
            'error': str(e),
            'structure_score': 0
        }

def validate_19_section_format(file_path: str) -> Dict:
    """Validate that a docs/specs/ file has all 19 required sections in correct order."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all section headers (## headers)
        section_headers = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
        
        # Check for each required section
        missing_sections = []
        present_sections = []
        
        for section in REQUIRED_SECTIONS:
            # Check if section exists (case-insensitive, flexible matching)
            section_found = False
            for header in section_headers:
                if section.lower() in header.lower() or header.lower() in section.lower():
                    section_found = True
                    present_sections.append(header)
                    break
            
            if not section_found:
                missing_sections.append(section)
        
        # Check section order (approximate - sections should appear in roughly correct order)
        section_order_score = 0
        if len(present_sections) > 0:
            # Simple order check - first few sections should be in order
            first_sections = REQUIRED_SECTIONS[:5]  # Check first 5 sections
            for i, expected_section in enumerate(first_sections):
                for j, present_section in enumerate(present_sections[:5]):
                    if expected_section.lower() in present_section.lower():
                        if j >= i:  # Present section should be at or after expected position
                            section_order_score += 1
                        break
        
        # Check for enhanced sections (Event Logging, Error Codes)
        has_component_specific_log_files = bool(re.search(
            r'logs/events/.*_events\.jsonl', content, re.IGNORECASE
        ))
        has_dual_logging = bool(re.search(
            r'JSON Lines.*CSV Export|CSV.*JSON Lines', content, re.IGNORECASE
        ))
        has_structured_error_handling = bool(re.search(
            r'ComponentError|error_code.*severity', content, re.IGNORECASE
        ))
        has_health_integration = bool(re.search(
            r'health_manager|_health_check|UnifiedHealthManager', content, re.IGNORECASE
        ))
        
        # Calculate overall score
        total_sections = len(REQUIRED_SECTIONS)
        present_count = len(present_sections)
        section_completeness = present_count / total_sections if total_sections > 0 else 0
        
        return {
            'file': file_path,
            'total_required_sections': total_sections,
            'present_sections': present_count,
            'missing_sections': missing_sections,
            'section_completeness': section_completeness,
            'section_order_score': section_order_score,
            'has_component_specific_log_files': has_component_specific_log_files,
            'has_dual_logging': has_dual_logging,
            'has_structured_error_handling': has_structured_error_handling,
            'has_health_integration': has_health_integration,
            'structure_score': (
                section_completeness * 0.4 +  # 40% weight for section presence
                (section_order_score / 5) * 0.2 +  # 20% weight for order
                (0.1 if has_component_specific_log_files else 0) +  # 10% for log files
                (0.1 if has_dual_logging else 0) +  # 10% for dual logging
                (0.1 if has_structured_error_handling else 0) +  # 10% for error handling
                (0.1 if has_health_integration else 0)  # 10% for health integration
            )
        }
    
    except Exception as e:
        return {
            'file': file_path,
            'error': str(e),
            'structure_score': 0
        }

def validate_specs_implementation_status(file_path: str) -> Dict:
    """Validate that a docs/specs/ file has complete structure including implementation status section."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for implementation status section
        has_implementation_status = bool(re.search(
            r'##\s+.*[Ii]mplementation\s+[Ss]tatus', content, re.MULTILINE
        ))
        
        # Check for specific implementation status elements
        has_current_status = bool(re.search(r'[Cc]urrent\s+[Ii]mplementation', content))
        has_architecture_compliance = bool(re.search(r'[Aa]rchitecture\s+[Cc]ompliance', content))
        has_todo_items = bool(re.search(r'[Tt][Oo][Dd][Oo]', content))
        has_quality_gate_status = bool(re.search(r'[Qq]uality\s+[Gg]ate', content))
        has_task_completion = bool(re.search(r'[Tt]ask\s+[Cc]ompletion', content))
        
        # Check for canonical sources reference
        has_canonical_sources = bool(re.search(r'canonical.*source', content, re.IGNORECASE))
        
        # Check for last reviewed date
        has_last_reviewed = bool(re.search(r'[Ll]ast\s+[Rr]eviewed', content))
        
        # Check for 19-section format elements (new format)
        has_purpose_section = bool(re.search(r'##\s+.*[Pp]urpose', content, re.MULTILINE))
        has_canonical_sources_section = bool(re.search(r'##\s+.*[Cc]anonical\s+[Ss]ources', content, re.MULTILINE))
        has_responsibilities_section = bool(re.search(r'##\s+.*[Rr]esponsibilities', content, re.MULTILINE))
        has_state_section = bool(re.search(r'##\s+.*[Ss]tate', content, re.MULTILINE))
        has_config_params_section = bool(re.search(r'##\s+.*[Cc]onfiguration\s+[Pp]arameters', content, re.MULTILINE))
        has_env_vars_section = bool(re.search(r'##\s+.*[Ee]nvironment\s+[Vv]ariables', content, re.MULTILINE))
        has_core_methods_section = bool(re.search(r'##\s+.*[Cc]ore\s+[Mm]ethods', content, re.MULTILINE))
        has_mode_aware_section = bool(re.search(r'##\s+.*[Mm]ode.*[Aa]ware', content, re.MULTILINE))
        has_integration_section = bool(re.search(r'##\s+.*[Ii]ntegration', content, re.MULTILINE))
        has_related_docs_section = bool(re.search(r'##\s+.*[Rr]elated\s+[Dd]ocumentation', content, re.MULTILINE))
        
        implementation_elements = [
            has_implementation_status,
            has_current_status,
            has_architecture_compliance,
            has_todo_items,
            has_quality_gate_status,
            has_task_completion
        ]
        
        structure_elements = [
            has_canonical_sources,
            has_last_reviewed,
            has_purpose_section,
            has_canonical_sources_section,
            has_responsibilities_section,
            has_state_section,
            has_config_params_section,
            has_env_vars_section,
            has_core_methods_section,
            has_mode_aware_section,
            has_integration_section,
            has_related_docs_section
        ]
        
        return {
            'file': file_path,
            'has_implementation_status': has_implementation_status,
            'has_current_status': has_current_status,
            'has_architecture_compliance': has_architecture_compliance,
            'has_todo_items': has_todo_items,
            'has_quality_gate_status': has_quality_gate_status,
            'has_task_completion': has_task_completion,
            'has_canonical_sources': has_canonical_sources,
            'has_last_reviewed': has_last_reviewed,
            'has_purpose_section': has_purpose_section,
            'has_canonical_sources_section': has_canonical_sources_section,
            'has_responsibilities_section': has_responsibilities_section,
            'has_state_section': has_state_section,
            'has_config_params_section': has_config_params_section,
            'has_env_vars_section': has_env_vars_section,
            'has_core_methods_section': has_core_methods_section,
            'has_mode_aware_section': has_mode_aware_section,
            'has_integration_section': has_integration_section,
            'has_related_docs_section': has_related_docs_section,
            'implementation_score': sum(implementation_elements),
            'structure_score': sum(structure_elements),
            'total_implementation_elements': len(implementation_elements),
            'total_structure_elements': len(structure_elements)
        }
    
    except Exception as e:
        return {
            'file': file_path,
            'error': str(e),
            'implementation_score': 0,
            'structure_score': 0,
            'total_implementation_elements': 6,
            'total_structure_elements': 11
        }

def run_quality_gate() -> Dict:
    """Run the documentation structure validation quality gate."""
    print("=== Documentation Structure Validation Quality Gate ===")
    print(f"Timestamp: {subprocess.check_output(['date']).decode().strip()}")
    print()
    
    # Find all docs files
    print("1. Scanning documentation files:")
    all_docs, specs_docs = find_docs_files()
    print(f"Found {len(all_docs)} docs/ files (excluding specs/)")
    print(f"Found {len(specs_docs)} docs/specs/ files")
    print()
    
    # Validate docs/ structure (excluding specs/)
    print("2. Validating docs/ structure (excluding specs/):")
    docs_results = []
    docs_passed = 0
    
    for file_path in all_docs:
        result = validate_docs_structure(file_path)
        docs_results.append(result)
        
        if result.get('structure_score', 0) >= 3:  # At least 3/4 elements
            docs_passed += 1
    
    print(f"Docs structure validation complete: {docs_passed}/{len(all_docs)} passed")
    print()
    
    # Validate docs/specs/ implementation status and structure
    print("3. Validating docs/specs/ implementation status and structure:")
    specs_results = []
    specs_implementation_passed = 0
    specs_structure_passed = 0
    
    for file_path in specs_docs:
        result = validate_specs_implementation_status(file_path)
        specs_results.append(result)
        
        if result.get('implementation_score', 0) >= 4:  # At least 4/6 elements
            specs_implementation_passed += 1
            
        if result.get('structure_score', 0) >= 10:  # At least 10/12 elements
            specs_structure_passed += 1
    
    print(f"Specs implementation status validation complete: {specs_implementation_passed}/{len(specs_docs)} passed")
    print(f"Specs structure validation complete: {specs_structure_passed}/{len(specs_docs)} passed")
    print()
    
    # Validate 19-section format for component specs
    print("4. Validating 19-section standard format for component specs:")
    section_format_results = []
    section_format_passed = 0
    
    for file_path in specs_docs:
        result = validate_19_section_format(file_path)
        section_format_results.append(result)
        
        if result.get('structure_score', 0) >= 0.8:  # At least 80% compliance
            section_format_passed += 1
    
    print(f"18-section format validation complete: {section_format_passed}/{len(specs_docs)} passed")
    print()
    
    # Calculate overall pass rates
    total_docs = len(all_docs) + len(specs_docs)
    total_specs_passed = specs_implementation_passed + specs_structure_passed + section_format_passed
    total_passed = docs_passed + specs_implementation_passed
    
    if total_docs == 0:
        overall_pass_rate = 100
    else:
        overall_pass_rate = (total_passed * 100) // total_docs
    
    # Quality Gate Results
    print("=== Quality Gate Results ===")
    print(f"Total documentation files: {total_docs}")
    print(f"Docs/ files (excluding specs/): {len(all_docs)}")
    print(f"Docs/specs/ files: {len(specs_docs)}")
    print(f"Docs structure passed: {docs_passed}/{len(all_docs)}")
    print(f"Specs implementation status passed: {specs_implementation_passed}/{len(specs_docs)}")
    print(f"Specs structure passed: {specs_structure_passed}/{len(specs_docs)}")
    print(f"18-section format passed: {section_format_passed}/{len(specs_docs)}")
    print(f"Overall pass rate: {overall_pass_rate}%")
    print()
    
    # Quality Gate Decision
    if (docs_passed == len(all_docs) and 
        specs_implementation_passed == len(specs_docs) and 
        specs_structure_passed == len(specs_docs) and
        section_format_passed == len(specs_docs)):
        print("✅ QUALITY GATE PASSED: All documentation structure requirements met")
        print("All documentation files have proper structure, implementation status, and 18-section format")
        return {
            "status": "PASSED",
            "total_docs": total_docs,
            "docs_passed": docs_passed,
            "docs_total": len(all_docs),
            "specs_implementation_passed": specs_implementation_passed,
            "specs_structure_passed": specs_structure_passed,
            "section_format_passed": section_format_passed,
            "specs_total": len(specs_docs),
            "overall_pass_rate": overall_pass_rate,
            "docs_results": docs_results,
            "specs_results": specs_results,
            "section_format_results": section_format_results
        }
    else:
        print("❌ QUALITY GATE FAILED: Documentation structure requirements not met")
        print()
        
        # Show failing docs/ files
        if docs_passed < len(all_docs):
            print("Docs/ files with structure issues:")
            for result in docs_results:
                if result.get('structure_score', 0) < 3:
                    print(f"  {result['file']}: {result.get('structure_score', 0)}/4 elements")
            print()
        
        # Show failing specs/ files - implementation status
        if specs_implementation_passed < len(specs_docs):
            print("Docs/specs/ files missing implementation status:")
            for result in specs_results:
                if result.get('implementation_score', 0) < 4:
                    print(f"  {result['file']}: {result.get('implementation_score', 0)}/6 elements")
            print()
        
        # Show failing specs/ files - structure
        if specs_structure_passed < len(specs_docs):
            print("Docs/specs/ files missing required structure sections:")
            for result in specs_results:
                if result.get('structure_score', 0) < 10:
                    print(f"  {result['file']}: {result.get('structure_score', 0)}/12 elements")
            print()
        
        # Show failing specs/ files - 18-section format
        if section_format_passed < len(specs_docs):
            print("Docs/specs/ files missing 18-section standard format:")
            for result in section_format_results:
                if result.get('structure_score', 0) < 0.8:
                    missing_sections = result.get('missing_sections', [])
                    print(f"  {result['file']}: {result.get('structure_score', 0):.2f} compliance")
                    if missing_sections:
                        print(f"    Missing sections: {', '.join(missing_sections[:5])}{'...' if len(missing_sections) > 5 else ''}")
            print()
        
        print("Required action: Fix documentation structure issues")
        print("Target: 100% documentation structure compliance")
        print(f"Current: {overall_pass_rate}% documentation structure compliance")
        
        return {
            "status": "FAILED",
            "total_docs": total_docs,
            "docs_passed": docs_passed,
            "docs_total": len(all_docs),
            "specs_implementation_passed": specs_implementation_passed,
            "specs_structure_passed": specs_structure_passed,
            "section_format_passed": section_format_passed,
            "specs_total": len(specs_docs),
            "overall_pass_rate": overall_pass_rate,
            "docs_results": docs_results,
            "specs_results": specs_results,
            "section_format_results": section_format_results
        }

if __name__ == "__main__":
    try:
        result = run_quality_gate()
        if result["status"] == "FAILED":
            sys.exit(1)
        else:
            sys.exit(0)
    except Exception as e:
        print(f"Error running quality gate: {e}")
        sys.exit(1)
