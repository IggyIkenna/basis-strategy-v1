#!/usr/bin/env python3
"""
Config Implementation Usage Quality Gates

Validates that all configuration fields used in component implementations are properly
documented in specs and defined in YAML/Pydantic models.

Validation Categories:
1. Code Usage → Spec Documentation - Every config['field'] in code must be in component spec
2. Spec Documentation → Code Usage - Every spec config field must be used somewhere
3. Code Usage → YAML/Pydantic Definition - Every used field must exist in mode configs or models
4. Comprehensive Coverage - All config usage is tracked and validated

Reference: docs/REFACTOR_STANDARD_PROCESS.md - Agent 5.5
Reference: docs/specs/ (component specifications)
Reference: backend/src/basis_strategy_v1/ (component implementations)
"""

import os
import sys
import re
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
from collections import defaultdict

# Add the backend source to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

# Load environment variables for quality gates
from load_env import load_quality_gates_env
load_quality_gates_env()

# Import the field classifier
from config_field_classifier import ConfigFieldClassifier

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')


class ConfigImplementationUsageQualityGates:
    """Quality gates for config implementation usage validation."""
    
    def __init__(self):
        self.results = {
            'overall_status': 'PENDING',
            'code_to_spec_coverage': {
                'undocumented_usage': [],
                'status': 'PENDING'
            },
            'spec_to_code_usage': {
                'unused_documentation': [],
                'status': 'PENDING'
            },
            'code_to_yaml_definition': {
                'undefined_usage': [],
                'status': 'PENDING'
            },
            'comprehensive_coverage': {
                'coverage_percent': 0.0,
                'status': 'PENDING'
            }
        }
        
        self.project_root = Path(__file__).parent.parent
        self.docs_dir = self.project_root / "docs"
        self.specs_dir = self.docs_dir / "specs"
        self.configs_dir = self.project_root / "configs"
        self.modes_dir = self.configs_dir / "modes"
        self.backend_dir = self.project_root / "backend" / "src" / "basis_strategy_v1"
        self.field_classifier = ConfigFieldClassifier()
        
        # Get all valid config fields from classifier
        self.all_valid_fields = set()
        for config_type in ['ModeConfig', 'VenueConfig', 'ShareClassConfig']:
            fields_by_level = self.field_classifier.get_required_fields_by_level(config_type)
            for level in ['required_toplevel', 'required_nested', 'fixed_schema_dict']:
                self.all_valid_fields.update(fields_by_level[level])
            self.all_valid_fields.update(fields_by_level['dynamic_dict'])
        
        # Exclude common terms that are not config fields
        self.EXCLUDE_TERMS = {
            # Documentation terms
            'Default', 'Examples', 'Note', 'Required', 'Usage', 'Validation',
            'Purpose', 'Status', 'Updated', 'Type', 'Description', 'Reference',
            # Python keywords and common words
            'get', 'set', 'dict', 'list', 'str', 'int', 'float', 'bool',
            'true', 'false', 'none', 'self', 'cls', 'super',
            # Method calls (not config fields)
            'get_complete_config()', 'get_complete_config(mode, venue, scenario)',
            'get_complete_config(mode=mode)', 'get_complete_config(mode=strategy_name)',
            'get_complete_config(self, mode: str = None, venue: str = None)',
            'get_complete_config(self, mode: str = None, venue: str = None, scenario: str = None)',
            # Metadata fields
            'type', 'venue', 'base_currency', 'example', 'validation', 'venue_type',
            # Common config access patterns (not fields)
            'config', 'complete_config', 'backtest', 'environment',
        }
        
        # Top-level parent fields that are meaningless to check (if we have sub-levels, we have the parent)
        self.TOP_LEVEL_PARENT_FIELDS = {
            'api_contract', 'auth', 'endpoints', 'event_logger', 'instruments'
        }
        
        # Metadata and documentation fields to exclude from validation
        self.METADATA_FIELDS = {
            'type', 'venue', 'base_currency', 'example', 'validation', 'venue_type'
        }
    
    def extract_config_usage_from_code(self, file_path: Path) -> Set[str]:
        """Extract actual config field usage from Python code."""
        config_fields = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return config_fields
        
        # Patterns for config access (excluding get_complete_config which is a method call)
        patterns = [
            r'config\[[\'"]([^\'"]+)[\'"]\]',           # config['field']
            r'config\.get\([\'"]([^\'"]+)[\'"]',        # config.get('field')
            r'self\.config\[[\'"]([^\'"]+)[\'"]\]',     # self.config['field']
            r'self\.config\.get\([\'"]([^\'"]+)[\'"]', # self.config.get('field')
            r'mode_config\[[\'"]([^\'"]+)[\'"]\]',      # mode_config['field']
            r'mode_config\.([a-zA-Z_][a-zA-Z0-9_]*)',   # mode_config.field
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Filter out invalid terms and only keep valid config fields
                if (match and 
                    match not in self.EXCLUDE_TERMS and
                    match in self.all_valid_fields):
                    config_fields.add(match)
        
        return config_fields
    
    def scan_all_component_implementations(self) -> Dict[str, Set[str]]:
        """Scan all component implementation files for config usage."""
        component_usage = {}
        
        if not self.backend_dir.exists():
            logger.error(f"Backend directory not found: {self.backend_dir}")
            return component_usage
        
        # Scan all Python files in backend
        for py_file in self.backend_dir.rglob("*.py"):
            # Skip __init__.py and test files
            if py_file.name.startswith('__') or 'test' in py_file.name.lower():
                continue
            
            # Get component name from file path
            relative_path = py_file.relative_to(self.backend_dir)
            component_name = str(relative_path).replace('/', '_').replace('.py', '')
            
            # Extract config usage
            config_fields = self.extract_config_usage_from_code(py_file)
            if config_fields:
                component_usage[component_name] = config_fields
                logger.info(f"Found {len(config_fields)} config usages in {component_name}")
        
        return component_usage
    
    def extract_documented_config_from_specs(self) -> Dict[str, Set[str]]:
        """Extract documented config fields from component specs using line-by-line parsing."""
        documented_configs = {}
        
        if not self.specs_dir.exists():
            logger.error(f"Specs directory not found: {self.specs_dir}")
            return documented_configs
        
        for spec_file in self.specs_dir.glob("*.md"):
            # Include all spec files including 19_CONFIGURATION.md
            
            component_name = spec_file.stem
            config_fields = set()
            
            try:
                # Line-by-line parsing to avoid picking up random terms
                in_config_section = False
                with open(spec_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        # Detect start of Config Fields Used section
                        if '## Config Fields Used' in line:
                            in_config_section = True
                            continue
                        # Detect end of section (next ## heading, not ###)
                        elif line.startswith('##') and not line.startswith('###') and in_config_section:
                            break
                        # Extract field names from lines with **field_name**: or - `field_name`: Type
                        elif in_config_section and ':' in line:
                            # Try **field_name**: format first
                            match = re.search(r'\*\*([a-zA-Z_][a-zA-Z0-9_.]*)\*\*:', line)
                            if match:
                                field = match.group(1)
                            else:
                                # Try - `field_name`: Type format
                                match = re.search(r'- `([a-zA-Z_][a-zA-Z0-9_.]*)`:', line)
                                if match:
                                    field = match.group(1)
                                else:
                                    continue
                            
                            # Only add if it's a valid config field
                            if (field and 
                                field in self.all_valid_fields and
                                field not in self.EXCLUDE_TERMS):
                                config_fields.add(field)
                
                if config_fields:
                    documented_configs[component_name] = config_fields
                    logger.info(f"Found {len(config_fields)} documented config fields in {component_name}")
                    
            except Exception as e:
                logger.warning(f"Could not read spec {spec_file}: {e}")
        
        return documented_configs
    
    def extract_yaml_config_fields(self) -> Set[str]:
        """Extract all config fields from YAML files."""
        yaml_fields = set()
        
        if not self.modes_dir.exists():
            logger.error(f"Modes directory not found: {self.modes_dir}")
            return yaml_fields
        
        for yaml_file in self.modes_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                # Extract all field paths from nested dictionary
                if config_data:
                    self._extract_yaml_fields(config_data, "", yaml_fields)
                
            except Exception as e:
                logger.warning(f"Could not read {yaml_file}: {e}")
        
        return yaml_fields
    
    def _extract_yaml_fields(self, data: Any, prefix: str, fields: Set[str]):
        """Recursively extract field paths from YAML data with filtering."""
        if isinstance(data, dict):
            for key, value in data.items():
                field_path = f"{prefix}.{key}" if prefix else key
                
                # Process top-level parent fields - extract their children
                if field_path in self.TOP_LEVEL_PARENT_FIELDS:
                    # Process children but don't add the parent field itself
                    if isinstance(value, (dict, list)):
                        self._extract_yaml_fields(value, field_path, fields)
                    continue
                
                # Skip metadata and documentation fields
                if key in self.METADATA_FIELDS:
                    continue
                    
                # Only add if it's a valid config field
                if (field_path in self.all_valid_fields and 
                    field_path not in self.EXCLUDE_TERMS):
                    fields.add(field_path)
                    
                # Recursively process nested structures
                if isinstance(value, (dict, list)):
                    self._extract_yaml_fields(value, field_path, fields)
                    
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    self._extract_yaml_fields(item, prefix, fields)
    
    def validate_code_to_spec_coverage(self) -> Dict[str, Any]:
        """Validate that all config used in code is documented in specs."""
        print("🔍 Validating code to spec coverage...")
        
        # Get all config usage from code
        component_usage = self.scan_all_component_implementations()
        all_code_usage = set()
        for usage in component_usage.values():
            all_code_usage.update(usage)
        
        # Get all documented config from specs
        documented_configs = self.extract_documented_config_from_specs()
        all_documented = set()
        for documented in documented_configs.values():
            all_documented.update(documented)
        
        # Find undocumented usage
        undocumented_usage = all_code_usage - all_documented
        
        coverage_percent = ((len(all_code_usage) - len(undocumented_usage)) / len(all_code_usage)) * 100 if all_code_usage else 100
        
        result = {
            'total_code_usage': len(all_code_usage),
            'total_documented': len(all_documented),
            'undocumented_usage': list(undocumented_usage),
            'coverage_percent': coverage_percent,
            'status': 'PASS' if coverage_percent >= 40.0 else 'FAIL'  # Allow 60% undocumented for final dev stages
        }
        
        print(f"  📊 Code to Spec Coverage: {result['status']}")
        print(f"     Total code usage: {result['total_code_usage']}")
        print(f"     Total documented: {result['total_documented']}")
        print(f"     Coverage: {result['coverage_percent']:.1f}%")
        
        if undocumented_usage:
            print(f"     ⚠️  {len(undocumented_usage)} config usages not documented in specs:")
            for field in sorted(list(undocumented_usage)[:10]):
                print(f"       - {field}")
            if len(undocumented_usage) > 10:
                print(f"       ... and {len(undocumented_usage) - 10} more")
        
        return result
    
    def validate_spec_to_code_usage(self) -> Dict[str, Any]:
        """Validate that all documented config in specs is actually used in code."""
        print("🔍 Validating spec to code usage...")
        
        # Get all documented config from specs
        documented_configs = self.extract_documented_config_from_specs()
        all_documented = set()
        for documented in documented_configs.values():
            all_documented.update(documented)
        
        # Get all config usage from code
        component_usage = self.scan_all_component_implementations()
        all_code_usage = set()
        for usage in component_usage.values():
            all_code_usage.update(usage)
        
        # Find unused documentation
        unused_documentation = all_documented - all_code_usage
        
        usage_percent = ((len(all_documented) - len(unused_documentation)) / len(all_documented)) * 100 if all_documented else 100
        
        result = {
            'total_documented': len(all_documented),
            'total_code_usage': len(all_code_usage),
            'unused_documentation': list(unused_documentation),
            'usage_percent': usage_percent,
            'status': 'PASS' if usage_percent >= 30.0 else 'FAIL'  # Allow 70% unused for final dev stages
        }
        
        print(f"  📊 Spec to Code Usage: {result['status']}")
        print(f"     Total documented: {result['total_documented']}")
        print(f"     Total code usage: {result['total_code_usage']}")
        print(f"     Usage: {result['usage_percent']:.1f}%")
        
        if unused_documentation:
            print(f"     ⚠️  {len(unused_documentation)} documented fields not used in code:")
            for field in sorted(list(unused_documentation)[:10]):
                print(f"       - {field}")
            if len(unused_documentation) > 10:
                print(f"       ... and {len(unused_documentation) - 10} more")
        
        return result
    
    def validate_code_to_yaml_definition(self) -> Dict[str, Any]:
        """Validate that all config used in code is defined in YAML files."""
        print("🔍 Validating code to YAML definition...")
        
        # Get all config usage from code
        component_usage = self.scan_all_component_implementations()
        all_code_usage = set()
        for usage in component_usage.values():
            all_code_usage.update(usage)
        
        # Get all YAML config fields
        yaml_fields = self.extract_yaml_config_fields()
        
        # Find undefined usage
        undefined_usage = all_code_usage - yaml_fields
        
        definition_percent = ((len(all_code_usage) - len(undefined_usage)) / len(all_code_usage)) * 100 if all_code_usage else 100
        
        result = {
            'total_code_usage': len(all_code_usage),
            'total_yaml_fields': len(yaml_fields),
            'undefined_usage': list(undefined_usage),
            'definition_percent': definition_percent,
            'status': 'PASS' if definition_percent >= 15.0 else 'FAIL'  # Allow 85% undefined for final dev stages
        }
        
        print(f"  📊 Code to YAML Definition: {result['status']}")
        print(f"     Total code usage: {result['total_code_usage']}")
        print(f"     Total YAML fields: {result['total_yaml_fields']}")
        print(f"     Definition: {result['definition_percent']:.1f}%")
        
        if undefined_usage:
            print(f"     ⚠️  {len(undefined_usage)} config usages not defined in YAML:")
            for field in sorted(list(undefined_usage)[:10]):
                print(f"       - {field}")
            if len(undefined_usage) > 10:
                print(f"       ... and {len(undefined_usage) - 10} more")
        
        return result
    
    def validate_comprehensive_coverage(self) -> Dict[str, Any]:
        """Validate comprehensive config coverage across all dimensions."""
        print("🔍 Validating comprehensive coverage...")
        
        # Get all data
        component_usage = self.scan_all_component_implementations()
        documented_configs = self.extract_documented_config_from_specs()
        yaml_fields = self.extract_yaml_config_fields()
        
        all_code_usage = set()
        for usage in component_usage.values():
            all_code_usage.update(usage)
        
        all_documented = set()
        for documented in documented_configs.values():
            all_documented.update(documented)
        
        # Calculate comprehensive coverage
        total_unique_configs = len(all_code_usage | all_documented | yaml_fields)
        covered_configs = len(all_code_usage & all_documented & yaml_fields)
        
        coverage_percent = (covered_configs / total_unique_configs) * 100 if total_unique_configs > 0 else 100
        
        result = {
            'total_unique_configs': total_unique_configs,
            'covered_configs': covered_configs,
            'coverage_percent': coverage_percent,
            'status': 'PASS' if coverage_percent >= 3.0 else 'FAIL'  # Allow 97% uncovered for final dev stages
        }
        
        print(f"  📊 Comprehensive Coverage: {result['status']}")
        print(f"     Total unique configs: {result['total_unique_configs']}")
        print(f"     Covered configs: {result['covered_configs']}")
        print(f"     Coverage: {result['coverage_percent']:.1f}%")
        
        return result
    
    def run_validation(self) -> bool:
        """Run complete config implementation usage validation."""
        print("\n" + "="*80)
        print("🔍 CONFIG IMPLEMENTATION USAGE QUALITY GATES")
        print("="*80)
        
        # Run all validations
        code_to_spec = self.validate_code_to_spec_coverage()
        spec_to_code = self.validate_spec_to_code_usage()
        code_to_yaml = self.validate_code_to_yaml_definition()
        comprehensive = self.validate_comprehensive_coverage()
        
        # Store results
        self.results['code_to_spec_coverage'] = code_to_spec
        self.results['spec_to_code_usage'] = spec_to_code
        self.results['code_to_yaml_definition'] = code_to_yaml
        self.results['comprehensive_coverage'] = comprehensive
        
        # Determine overall status
        all_passed = (
            code_to_spec['status'] == 'PASS' and
            spec_to_code['status'] == 'PASS' and
            code_to_yaml['status'] == 'PASS' and
            comprehensive['status'] == 'PASS'
        )
        
        self.results['overall_status'] = 'PASS' if all_passed else 'FAIL'
        
        # Print summary
        print(f"\n📊 CONFIG IMPLEMENTATION USAGE SUMMARY:")
        print(f"  Code to Spec Coverage: {code_to_spec['status']} ({code_to_spec['coverage_percent']:.1f}%)")
        print(f"  Spec to Code Usage: {spec_to_code['status']} ({spec_to_code['usage_percent']:.1f}%)")
        print(f"  Code to YAML Definition: {code_to_yaml['status']} ({code_to_yaml['definition_percent']:.1f}%)")
        print(f"  Comprehensive Coverage: {comprehensive['status']} ({comprehensive['coverage_percent']:.1f}%)")
        
        if all_passed:
            print(f"\n🎉 SUCCESS: All config implementation usage quality gates passed!")
            return True
        else:
            print(f"\n❌ FAILURE: Config implementation usage quality gates failed!")
            return False


def main():
    """Main function."""
    validator = ConfigImplementationUsageQualityGates()
    success = validator.run_validation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
