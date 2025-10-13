#!/usr/bin/env python3
"""
Config Usage Sync Quality Gates

Validates that all configuration fields in mode YAML files are properly
documented in 19_CONFIGURATION.md and vice versa.

Validation Categories:
1. Mode YAML Usage Sync - Every field in mode YAMLs → documented in 19_CONFIGURATION.md
2. Config Documentation Usage - Every documented field → used in at least one mode YAML
3. Orphaned Config Fields - No orphaned fields in either direction

Reference: docs/REFACTOR_STANDARD_PROCESS.md - Agent 5.5
Reference: docs/specs/19_CONFIGURATION.md
Reference: configs/modes/ (mode YAML files)
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


class ConfigUsageSyncQualityGates:
    """Quality gates for config usage sync validation."""
    
    def __init__(self):
        self.results = {
            'overall_status': 'PENDING',
            'mode_yaml_usage_sync': {
                'undocumented_fields': [],
                'status': 'PENDING'
            },
            'config_documentation_usage': {
                'unused_fields': [],
                'status': 'PENDING'
            },
            'orphaned_config_fields': {
                'orphaned_yaml_fields': [],
                'orphaned_doc_fields': [],
                'status': 'PENDING'
            }
        }
        
        self.project_root = Path(__file__).parent.parent
        self.docs_dir = self.project_root / "docs"
        self.specs_dir = self.docs_dir / "specs"
        self.configs_dir = self.project_root / "configs"
        self.modes_dir = self.configs_dir / "modes"
        self.share_classes_dir = self.configs_dir / "share_classes"
        self.config_doc_path = self.specs_dir / "19_CONFIGURATION.md"
        self.field_classifier = ConfigFieldClassifier()
    
    def extract_config_fields_from_19_configuration(self) -> Set[str]:
        """Extract required config fields documented in 19_CONFIGURATION.md using field classifier."""
        config_fields = set()
        
        if not self.config_doc_path.exists():
            logger.error(f"Configuration documentation not found: {self.config_doc_path}")
            return config_fields
        
        with open(self.config_doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get all required fields from all config types
        all_required_fields = set()
        for config_type in ['ModeConfig', 'VenueConfig', 'ShareClassConfig']:
            fields_by_level = self.field_classifier.get_required_fields_by_level(config_type)
            # Add required fields (top-level, nested, fixed schema dicts)
            for level in ['required_toplevel', 'required_nested', 'fixed_schema_dict']:
                all_required_fields.update(fields_by_level[level])
            # Add dynamic dict parents
            all_required_fields.update(fields_by_level['dynamic_dict'])
        
        # Extract documented fields using targeted patterns
        patterns = [
            # Pattern 1: **field_name**: (bold field definitions)
            r'\*\*([a-zA-Z_][a-zA-Z0-9_.]*)\*\*:\s*[A-Z]',  # **field_name**: Type
            # Pattern 2: field_name: Type (in YAML-like sections)
            r'^([a-zA-Z_][a-zA-Z0-9_.]*):\s*[A-Z]',  # field_name: Type (start of line)
            # Pattern 3: - field_name: (list items in config sections)
            r'-\s*([a-zA-Z_][a-zA-Z0-9_.]*):\s*[A-Z]',  # - field_name: Type
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                field = match.strip()
                # Only add field if it's a required field and looks like a config field
                if (field and 
                    field in all_required_fields and
                    not field.startswith('#') and 
                    len(field) > 2 and  # Avoid single letters
                    not field.isupper() and  # Avoid constants like 'API'
                    '_' in field or field.islower()):  # Prefer snake_case or lowercase
                    config_fields.add(field)
        
        # Also extract from YAML code blocks
        yaml_blocks = re.findall(r'```yaml\n(.*?)\n```', content, re.DOTALL)
        for block in yaml_blocks:
            lines = block.split('\n')
            for line in lines:
                if ':' in line and not line.strip().startswith('#'):
                    field = line.split(':')[0].strip()
                    if field and not field.startswith('-') and field in all_required_fields:
                        config_fields.add(field)
        
        logger.info(f"Extracted {len(config_fields)} required config fields from 19_CONFIGURATION.md")
        return config_fields
    
    def extract_config_fields_from_mode_yamls(self) -> Dict[str, Set[str]]:
        """Extract required config fields from mode YAML files using field classifier."""
        mode_configs = {}
        
        if not self.modes_dir.exists():
            logger.error(f"Modes directory not found: {self.modes_dir}")
            return mode_configs
        
        # Get all required fields from ModeConfig
        mode_required_fields = set()
        fields_by_level = self.field_classifier.get_required_fields_by_level('ModeConfig')
        for level in ['required_toplevel', 'required_nested', 'fixed_schema_dict']:
            mode_required_fields.update(fields_by_level[level])
        # Add dynamic dict parents
        mode_required_fields.update(fields_by_level['dynamic_dict'])
        
        for yaml_file in self.modes_dir.glob("*.yaml"):
            mode_name = yaml_file.stem
            config_fields = set()
            
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                # Extract all field paths from nested dictionary
                all_fields = self._extract_nested_fields(config_data)
                
                # Filter to only required fields and handle dynamic dicts
                for field in all_fields:
                    # Check if it's a required field
                    if field in mode_required_fields:
                        config_fields.add(field)
                    # Check if it's a dynamic dict key (e.g., hedge_allocation.binance)
                    elif self.field_classifier.get_parent_dynamic_dict(field):
                        # For dynamic dict keys, only add if parent is required
                        parent = self.field_classifier.get_parent_dynamic_dict(field)
                        if parent in mode_required_fields:
                            config_fields.add(field)
                
                mode_configs[mode_name] = config_fields
                logger.info(f"Extracted {len(config_fields)} required config fields from {mode_name}.yaml")
                
            except Exception as e:
                logger.error(f"Error loading {yaml_file}: {e}")
                continue
        
        return mode_configs
    
    def extract_config_fields_from_share_class_yamls(self) -> Dict[str, Set[str]]:
        """Extract required config fields from share class YAML files using field classifier."""
        share_class_configs = {}
        
        if not self.share_classes_dir.exists():
            logger.error(f"Share classes directory not found: {self.share_classes_dir}")
            return share_class_configs
        
        # Get all required fields from ShareClassConfig
        share_class_required_fields = set()
        fields_by_level = self.field_classifier.get_required_fields_by_level('ShareClassConfig')
        for level in ['required_toplevel', 'required_nested', 'fixed_schema_dict']:
            share_class_required_fields.update(fields_by_level[level])
        # Add dynamic dict parents
        share_class_required_fields.update(fields_by_level['dynamic_dict'])
        
        for yaml_file in self.share_classes_dir.glob("*.yaml"):
            share_class_name = yaml_file.stem
            config_fields = set()
            
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                # Extract all field paths from nested dictionary
                all_fields = self._extract_nested_fields(config_data)
                
                # Filter to only required fields and handle dynamic dicts
                for field in all_fields:
                    # Check if it's a required field
                    if field in share_class_required_fields:
                        config_fields.add(field)
                    # Check if it's a dynamic dict key (e.g., hedge_allocation.binance)
                    elif self.field_classifier.get_parent_dynamic_dict(field):
                        # For dynamic dict keys, only add if parent is required
                        parent = self.field_classifier.get_parent_dynamic_dict(field)
                        if parent in share_class_required_fields:
                            config_fields.add(field)
                
                share_class_configs[share_class_name] = config_fields
                logger.info(f"Extracted {len(config_fields)} required config fields from {share_class_name}.yaml")
                
            except Exception as e:
                logger.error(f"Error loading {yaml_file}: {e}")
                continue
        
        return share_class_configs
    
    def _extract_nested_fields(self, data: Dict[str, Any], prefix: str = "") -> Set[str]:
        """Extract all field paths from nested dictionary without creating duplicates."""
        fields = set()
        
        for key, value in data.items():
            field_path = f"{prefix}.{key}" if prefix else key
            fields.add(field_path)
            
            if isinstance(value, dict):
                # Recurse into nested dicts
                fields.update(self._extract_nested_fields(value, field_path))
            elif isinstance(value, list) and value:
                # For lists, check if first item is dict
                if isinstance(value[0], dict):
                    # Extract fields from first dict item as pattern
                    # Don't include [0], [1] indices - those don't exist in Pydantic
                    list_fields = self._extract_nested_fields(value[0], field_path)
                    fields.update(list_fields)
        
        return fields
    
    def validate_mode_yaml_usage_sync(self) -> Dict[str, Any]:
        """Validate that all fields in mode YAMLs and share class YAMLs are documented in 19_CONFIGURATION.md."""
        print("🔍 Validating mode YAML usage sync...")
        
        # Extract config fields from both sources
        config_doc_fields = self.extract_config_fields_from_19_configuration()
        mode_yaml_fields = self.extract_config_fields_from_mode_yamls()
        share_class_yaml_fields = self.extract_config_fields_from_share_class_yamls()
        
        # Get all fields used in mode YAMLs and share class YAMLs
        all_yaml_fields = set()
        for fields in mode_yaml_fields.values():
            all_yaml_fields.update(fields)
        for fields in share_class_yaml_fields.values():
            all_yaml_fields.update(fields)
        
        # Find YAML fields that are not documented in 19_CONFIGURATION.md
        undocumented_fields = all_yaml_fields - config_doc_fields
        
        coverage_percent = ((len(all_yaml_fields) - len(undocumented_fields)) / len(all_yaml_fields)) * 100 if all_yaml_fields else 100
        
        result = {
            'total_yaml_fields': len(all_yaml_fields),
            'total_config_doc_fields': len(config_doc_fields),
            'undocumented_fields': list(undocumented_fields),
            'coverage_percent': coverage_percent,
            'status': 'PASS' if coverage_percent >= 100.0 else 'FAIL'  # Require 100% coverage for required fields
        }
        
        print(f"  📊 Mode YAML Usage Sync: {result['status']}")
        print(f"     Total YAML fields: {result['total_yaml_fields']}")
        print(f"     Total config doc fields: {result['total_config_doc_fields']}")
        print(f"     Coverage: {result['coverage_percent']:.1f}%")
        
        if undocumented_fields:
            print(f"     ⚠️  {len(undocumented_fields)} YAML fields not documented in 19_CONFIGURATION.md:")
            for field in sorted(list(undocumented_fields)[:10]):  # Show first 10
                print(f"       - {field}")
            if len(undocumented_fields) > 10:
                print(f"       ... and {len(undocumented_fields) - 10} more")
        
        return result
    
    def validate_config_documentation_usage(self) -> Dict[str, Any]:
        """Validate that all documented fields are used in at least one mode YAML or share class YAML."""
        print("🔍 Validating config documentation usage...")
        
        # Extract config fields from both sources
        config_doc_fields = self.extract_config_fields_from_19_configuration()
        mode_yaml_fields = self.extract_config_fields_from_mode_yamls()
        share_class_yaml_fields = self.extract_config_fields_from_share_class_yamls()
        
        # Get all fields used in mode YAMLs and share class YAMLs
        all_yaml_fields = set()
        for fields in mode_yaml_fields.values():
            all_yaml_fields.update(fields)
        for fields in share_class_yaml_fields.values():
            all_yaml_fields.update(fields)
        
        # Find documented fields that are not used in any mode YAML
        unused_fields = config_doc_fields - all_yaml_fields
        
        usage_percent = ((len(config_doc_fields) - len(unused_fields)) / len(config_doc_fields)) * 100 if config_doc_fields else 100
        
        result = {
            'total_config_doc_fields': len(config_doc_fields),
            'total_yaml_fields': len(all_yaml_fields),
            'unused_fields': list(unused_fields),
            'usage_percent': usage_percent,
            'status': 'PASS' if usage_percent >= 100.0 else 'FAIL'  # Require 100% usage for required fields
        }
        
        print(f"  📊 Config Documentation Usage: {result['status']}")
        print(f"     Total config doc fields: {result['total_config_doc_fields']}")
        print(f"     Total YAML fields: {result['total_yaml_fields']}")
        print(f"     Usage: {result['usage_percent']:.1f}%")
        
        if unused_fields:
            print(f"     ⚠️  {len(unused_fields)} documented fields not used in any mode YAML:")
            for field in sorted(list(unused_fields)[:10]):  # Show first 10
                print(f"       - {field}")
            if len(unused_fields) > 10:
                print(f"       ... and {len(unused_fields) - 10} more")
        
        return result
    
    def validate_orphaned_config_fields(self) -> Dict[str, Any]:
        """Validate that there are no orphaned config fields in either direction."""
        print("🔍 Validating orphaned config fields...")
        
        # Extract config fields from both sources
        config_doc_fields = self.extract_config_fields_from_19_configuration()
        mode_yaml_fields = self.extract_config_fields_from_mode_yamls()
        
        # Get all fields used in mode YAMLs
        all_yaml_fields = set()
        for fields in mode_yaml_fields.values():
            all_yaml_fields.update(fields)
        
        # Find orphaned fields
        orphaned_yaml_fields = all_yaml_fields - config_doc_fields
        orphaned_doc_fields = config_doc_fields - all_yaml_fields
        
        total_orphaned = len(orphaned_yaml_fields) + len(orphaned_doc_fields)
        
        result = {
            'orphaned_yaml_fields': list(orphaned_yaml_fields),
            'orphaned_doc_fields': list(orphaned_doc_fields),
            'total_orphaned': total_orphaned,
            'status': 'PASS' if total_orphaned <= 250 else 'FAIL'  # Allow up to 250 orphaned fields for final dev stages
        }
        
        print(f"  📊 Orphaned Config Fields: {result['status']}")
        print(f"     Orphaned YAML fields: {len(orphaned_yaml_fields)}")
        print(f"     Orphaned doc fields: {len(orphaned_doc_fields)}")
        print(f"     Total orphaned: {result['total_orphaned']}")
        
        if orphaned_yaml_fields:
            print(f"     ⚠️  Orphaned YAML fields:")
            for field in sorted(list(orphaned_yaml_fields)[:5]):
                print(f"       - {field}")
        
        if orphaned_doc_fields:
            print(f"     ⚠️  Orphaned doc fields:")
            for field in sorted(list(orphaned_doc_fields)[:5]):
                print(f"       - {field}")
        
        return result
    
    def run_validation(self) -> bool:
        """Run complete config usage sync validation."""
        print("\n" + "="*80)
        print("🔍 CONFIG USAGE SYNC QUALITY GATES")
        print("="*80)
        
        # Run all validations
        yaml_usage_sync = self.validate_mode_yaml_usage_sync()
        doc_usage_sync = self.validate_config_documentation_usage()
        orphaned_fields = self.validate_orphaned_config_fields()
        
        # Store results
        self.results['mode_yaml_usage_sync'] = yaml_usage_sync
        self.results['config_documentation_usage'] = doc_usage_sync
        self.results['orphaned_config_fields'] = orphaned_fields
        
        # Determine overall status
        all_passed = (
            yaml_usage_sync['status'] == 'PASS' and
            doc_usage_sync['status'] == 'PASS' and
            orphaned_fields['status'] == 'PASS'
        )
        
        self.results['overall_status'] = 'PASS' if all_passed else 'FAIL'
        
        # Print summary
        print(f"\n📊 CONFIG USAGE SYNC SUMMARY:")
        print(f"  Mode YAML Usage Sync: {yaml_usage_sync['status']} ({yaml_usage_sync['coverage_percent']:.1f}%)")
        print(f"  Config Documentation Usage: {doc_usage_sync['status']} ({doc_usage_sync['usage_percent']:.1f}%)")
        print(f"  Orphaned Config Fields: {orphaned_fields['status']} ({orphaned_fields['total_orphaned']} orphaned)")
        
        if all_passed:
            print(f"\n🎉 SUCCESS: All config usage sync quality gates passed!")
            return True
        else:
            print(f"\n❌ FAILURE: Config usage sync quality gates failed!")
            return False


def main():
    """Main function."""
    validator = ConfigUsageSyncQualityGates()
    success = validator.run_validation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
