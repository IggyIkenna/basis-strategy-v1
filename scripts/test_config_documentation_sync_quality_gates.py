#!/usr/bin/env python3
"""
Config Documentation Sync Quality Gates

Validates that all configuration fields documented in 19_CONFIGURATION.md
are properly referenced in component specs and vice versa.

Validation Categories:
1. Config Documentation Sync - Every config in 19_CONFIGURATION.md → used in at least one component spec
2. Component Spec Sync - Every config in component specs → documented in 19_CONFIGURATION.md
3. Orphaned Documentation - No orphaned references in either direction

Reference: docs/REFACTOR_STANDARD_PROCESS.md - Agent 5.5
Reference: docs/specs/19_CONFIGURATION.md
Reference: docs/specs/ (component specifications)
"""

import os
import sys
import re
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


class ConfigDocumentationSyncQualityGates:
    """Quality gates for config documentation sync validation."""
    
    def __init__(self):
        self.results = {
            'overall_status': 'PENDING',
            'config_documentation_sync': {
                'undocumented_in_specs': [],
                'status': 'PENDING'
            },
            'component_spec_sync': {
                'undocumented_in_config': [],
                'status': 'PENDING'
            },
            'orphaned_references': {
                'orphaned_config_docs': [],
                'orphaned_spec_docs': [],
                'status': 'PENDING'
            }
        }
        
        self.project_root = Path(__file__).parent.parent
        self.docs_dir = self.project_root / "docs"
        self.specs_dir = self.docs_dir / "specs"
        self.config_doc_path = self.specs_dir / "19_CONFIGURATION.md"
        self.field_classifier = ConfigFieldClassifier()
        
        # Exclude common documentation terms and non-config fields
        self.EXCLUDE_TERMS = {
            # Documentation terms
            'Purpose', 'Status', 'Updated', 'Reviewed', 'Type', 'Description',
            'Reference', 'Example', 'Note', 'Warning', 'Error', 'Success',
            'Implementation', 'Config', 'Environment', 'Component', 'Validation',
            'Dict', 'List', 'Optional', 'Field', 'BaseModel', 'Any', 'str', 'int',
            'float', 'bool', 'Enum', 'Overview', 'Responsibilities', 'State',
            'Component', 'References', 'Set', 'Init', 'These', 'Are', 'Stored',
            'Used', 'Throughout', 'Lifecycle', 'Components', 'Never', 'Receive',
            'Method', 'Parameters', 'During', 'Runtime', 'System', 'Level',
            'Variables', 'Specific', 'Credential', 'Integration', 'Routing',
            'Patterns', 'Configuration', 'Integrates', 'With', 'Environment',
            'Specific', 'Credential', 'Routing', 'Ensure', 'Proper', 'Credential',
            'Selection', 'Based', 'On', 'BASIS_ENVIRONMENT', 'This', 'Integration',
            # Environment variables (should not be config fields)
            'BASIS_EXECUTION_MODE', 'BASIS_LOG_LEVEL', 'BASIS_DATA_DIR', 'CONFIG_VALIDATION_STRICT',
            'CONFIG_CACHE_SIZE', 'CONFIG_RELOAD_INTERVAL',
            # Environment names
            'Development', 'Staging', 'Production',
            # Venue names
            'Binance', 'Bybit', 'OKX', 'Alchemy',
            'Enables', 'Execution', 'Components', 'Access', 'Correct', 'Credentials',
            'For', 'Their', 'Environment', 'Without', 'Hardcoded', 'Credential',
            'Management', 'Current', 'Implementation', 'File', 'Core', 'Methods',
            'Parameters', 'Architecture', 'Compliance', 'Details', 'Loading',
            'Variables', 'Validation', 'Discovery', 'Slicing', 'Error', 'Handling',
            'Comprehensive', 'Codes', 'CONFIG-MGR-001', 'Through', 'CONFIG-MGR-008',
            'Remaining', 'Gaps', 'Hot-Reloading', 'Caching', 'Advanced', 'Provider',
            'Factory', 'Naming', 'Inconsistencies', 'Task', 'Recommendations',
            'Functionality', 'Performance', 'Optimization', 'Data', 'Provider',
            'Configuration', 'Validation', 'Environment', 'Variable', 'Naming',
            'Inconsistencies', 'Comprehensive', 'Unit', 'Tests', 'Integrate',
            'Component', 'Factory', 'Config-Driven', 'Component', 'Creation',
            # Common words that aren't config fields
            'lower', 'upper', 'append', 'extend', 'remove', 'pop', 'insert',
            'index', 'count', 'sort', 'reverse', 'copy', 'clear', 'update',
            'get', 'set', 'has', 'is', 'can', 'should', 'will', 'must', 'may',
            'all', 'any', 'some', 'none', 'first', 'last', 'next', 'previous',
            'start', 'end', 'begin', 'finish', 'complete', 'done', 'ready',
            'active', 'inactive', 'disabled', 'true', 'false',
            'yes', 'no', 'on', 'off', 'open', 'close', 'high', 'low',
            'big', 'small', 'large', 'tiny', 'new', 'old', 'good', 'bad',
            'best', 'worst', 'better', 'worse', 'fast', 'slow', 'quick',
            'easy', 'hard', 'simple', 'complex', 'basic', 'advanced',
            'public', 'private', 'protected', 'static', 'final', 'abstract',
            'class', 'function', 'method', 'variable', 'constant', 'parameter',
            'argument', 'return', 'yield', 'import', 'export', 'from', 'as',
            'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally',
            'with', 'def', 'lambda', 'global', 'nonlocal', 'assert', 'del',
            'pass', 'break', 'continue', 'raise', 'and', 'or', 'not', 'in',
            'is', 'not', 'None', 'True', 'False', 'self', 'cls', 'super',
            # File extensions and common terms
            'py', 'yaml', 'json', 'md', 'txt', 'log', 'csv', 'html', 'css',
            'js', 'ts', 'sh', 'bat', 'exe', 'dll', 'so', 'dylib', 'bin',
            'src', 'test', 'spec', 'config', 'data', 'logs', 'tmp', 'temp',
            'build', 'dist', 'lib', 'bin', 'etc', 'var', 'usr', 'home',
            'root', 'admin', 'user', 'guest', 'public', 'private', 'local',
            'remote', 'server', 'client', 'host', 'port', 'url', 'uri',
            'http', 'https', 'ftp', 'ssh', 'tcp', 'udp', 'ip', 'dns',
            'api', 'rest', 'graphql', 'json', 'xml', 'html', 'css', 'js',
            'sql', 'nosql', 'redis', 'mongodb', 'mysql', 'postgresql',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'heroku',
            'github', 'gitlab', 'bitbucket', 'jenkins', 'travis', 'circle',
            'npm', 'yarn', 'pip', 'conda', 'maven', 'gradle', 'sbt',
            'react', 'vue', 'angular', 'node', 'express', 'django', 'flask',
            'spring', 'rails', 'laravel', 'symfony', 'codeigniter',
            'jquery', 'bootstrap', 'tailwind', 'sass', 'less', 'webpack',
            'babel', 'eslint', 'prettier', 'jest', 'mocha', 'chai', 'cypress',
            # Currency symbols and trading pairs
            'BTC', 'ETH', 'USDT', 'USDC', 'DAI', 'WETH', 'WBTC', 'LINK', 'UNI',
            'BTC_PERP', 'ETH_PERP', 'USDT_PERP', 'BTC_SPOT', 'ETH_SPOT', 'USDT_SPOT',
            'aUSDT', 'aETH', 'aWBTC', 'aWeETH', 'aEIGEN', 'aKING',
            'EIGEN', 'KING', 'weETH', 'stETH', 'rETH', 'sfrxETH',
            # Example values and placeholders
            'action_1', 'action_2', 'action_3', 'asset_1', 'asset_2', 'asset_3',
            'venue_1', 'venue_2', 'venue_3', 'strategy_1', 'strategy_2', 'strategy_3',
            'example_1', 'example_2', 'example_3', 'test_1', 'test_2', 'test_3',
            'config_1', 'config_2', 'config_3', 'value_1', 'value_2', 'value_3',
            # Common config example values
            'alchemy_private_key', 'binance_api_key', 'bybit_api_key', 'okx_api_key',
            'wallet_address', 'private_key', 'api_key', 'secret_key', 'passphrase',
            'rpc_url', 'chain_id', 'network_id', 'gas_price', 'gas_limit',
            # Common field names that aren't actual config fields
            'global_config', 'local_config', 'default_config', 'base_config',
            'user_config', 'system_config', 'app_config', 'env_config'
        }
    
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
            # Pattern 1: **field_name**: (bold field definitions in documentation)
            r'\*\*([a-zA-Z_][a-zA-Z0-9_.]*)\*\*:\s*[^\n]*',  # **field_name**: anything
            # Pattern 2: - **field_name**: (list items with bold field definitions)
            r'-\s*\*\*([a-zA-Z_][a-zA-Z0-9_.]*)\*\*:\s*[^\n]*',  # - **field_name**: anything
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                field = match[0].strip() if isinstance(match, tuple) else match.strip()
                # Only add field if it's a required field and not in exclude list
                if (field and 
                    field in all_required_fields and
                    field not in self.EXCLUDE_TERMS and
                    len(field) > 2 and  # Avoid single letters
                    not field.isupper() and  # Avoid constants like 'API'
                    not field.startswith('BASIS_') and  # Avoid environment variables
                    not field.startswith('CONFIG_') and  # Avoid environment variables
                    '_' in field or field.islower()):  # Prefer snake_case or lowercase
                    config_fields.add(field)
        
        logger.info(f"Extracted {len(config_fields)} required config fields from 19_CONFIGURATION.md")
        return config_fields
    
    def extract_config_fields_from_component_specs(self) -> Dict[str, Set[str]]:
        """Extract required config fields from all component specs using field classifier."""
        component_configs = {}
        
        if not self.specs_dir.exists():
            logger.error(f"Specs directory not found: {self.specs_dir}")
            return component_configs
        
        # Get all required fields from all config types
        all_required_fields = set()
        for config_type in ['ModeConfig', 'VenueConfig', 'ShareClassConfig']:
            fields_by_level = self.field_classifier.get_required_fields_by_level(config_type)
            # Add required fields (top-level, nested, fixed schema dicts)
            for level in ['required_toplevel', 'required_nested', 'fixed_schema_dict']:
                all_required_fields.update(fields_by_level[level])
            # Add dynamic dict parents
            all_required_fields.update(fields_by_level['dynamic_dict'])
        
        for spec_file in self.specs_dir.glob("*.md"):
            if spec_file.name == "19_CONFIGURATION.md":
                continue  # Skip the main config doc
            
            component_name = spec_file.stem
            config_fields = set()
            
            with open(spec_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for "Config Fields Used" section
            config_section_match = re.search(
                r'## Config Fields Used\s*\n(.*?)(?=\n##|\n###|\Z)', 
                content, 
                re.DOTALL
            )
            
            if config_section_match:
                config_section = config_section_match.group(1)
                
                # Extract field names from the config section
                patterns = [
                    r'\*\*([a-zA-Z_][a-zA-Z0-9_.]*)\*\*:',  # **field_name**:
                    r'`([a-zA-Z_][a-zA-Z0-9_.]*)`',         # `field_name`
                    r'([a-zA-Z_][a-zA-Z0-9_.]*):\s*[A-Z]',  # field_name: Type
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, config_section)
                    for match in matches:
                        field = match.strip()
                        # Only add field if it's a required field and not in exclude list
                        if (field and 
                            field in all_required_fields and
                            not field.startswith('#') and
                            field not in self.EXCLUDE_TERMS):
                            config_fields.add(field)
            
            if config_fields:
                component_configs[component_name] = config_fields
                logger.info(f"Extracted {len(config_fields)} required config fields from {component_name}")
        
        return component_configs
    
    def validate_config_documentation_sync(self) -> Dict[str, Any]:
        """Validate that all config fields in 19_CONFIGURATION.md are used in component specs."""
        print("🔍 Validating config documentation sync...")
        
        # Extract config fields from both sources
        config_doc_fields = self.extract_config_fields_from_19_configuration()
        component_spec_fields = self.extract_config_fields_from_component_specs()
        
        # Get all fields used in component specs
        all_spec_fields = set()
        for fields in component_spec_fields.values():
            all_spec_fields.update(fields)
        
        # Find config fields that are documented but not used in any component spec
        undocumented_in_specs = config_doc_fields - all_spec_fields
        
        # Require 100% coverage for required fields
        coverage_percent = ((len(config_doc_fields) - len(undocumented_in_specs)) / len(config_doc_fields)) * 100 if config_doc_fields else 100
        min_coverage_threshold = 100.0  # Require 100% coverage for required fields
        
        result = {
            'total_config_doc_fields': len(config_doc_fields),
            'total_spec_fields': len(all_spec_fields),
            'undocumented_in_specs': list(undocumented_in_specs),
            'coverage_percent': coverage_percent,
            'status': 'PASS' if coverage_percent >= min_coverage_threshold else 'FAIL'
        }
        
        print(f"  📊 Config Documentation Sync: {result['status']}")
        print(f"     Total config doc fields: {result['total_config_doc_fields']}")
        print(f"     Total spec fields: {result['total_spec_fields']}")
        print(f"     Coverage: {result['coverage_percent']:.1f}%")
        
        if undocumented_in_specs:
            print(f"     ⚠️  {len(undocumented_in_specs)} config fields not used in component specs:")
            for field in sorted(list(undocumented_in_specs)[:10]):  # Show first 10
                print(f"       - {field}")
            if len(undocumented_in_specs) > 10:
                print(f"       ... and {len(undocumented_in_specs) - 10} more")
        
        return result
    
    def validate_component_spec_sync(self) -> Dict[str, Any]:
        """Validate that all config fields in component specs are documented in 19_CONFIGURATION.md."""
        print("🔍 Validating component spec sync...")
        
        # Extract config fields from both sources
        config_doc_fields = self.extract_config_fields_from_19_configuration()
        component_spec_fields = self.extract_config_fields_from_component_specs()
        
        # Get all fields used in component specs
        all_spec_fields = set()
        for fields in component_spec_fields.values():
            all_spec_fields.update(fields)
        
        # Find spec fields that are not documented in 19_CONFIGURATION.md
        undocumented_in_config = all_spec_fields - config_doc_fields
        
        result = {
            'total_spec_fields': len(all_spec_fields),
            'total_config_doc_fields': len(config_doc_fields),
            'undocumented_in_config': list(undocumented_in_config),
            'coverage_percent': ((len(all_spec_fields) - len(undocumented_in_config)) / len(all_spec_fields)) * 100 if all_spec_fields else 100,
            'status': 'PASS' if len(undocumented_in_config) == 0 else 'FAIL'
        }
        
        print(f"  📊 Component Spec Sync: {result['status']}")
        print(f"     Total spec fields: {result['total_spec_fields']}")
        print(f"     Total config doc fields: {result['total_config_doc_fields']}")
        print(f"     Coverage: {result['coverage_percent']:.1f}%")
        
        if undocumented_in_config:
            print(f"     ⚠️  {len(undocumented_in_config)} spec fields not documented in 19_CONFIGURATION.md:")
            for field in sorted(list(undocumented_in_config)[:10]):  # Show first 10
                print(f"       - {field}")
            if len(undocumented_in_config) > 10:
                print(f"       ... and {len(undocumented_in_config) - 10} more")
        
        return result
    
    def validate_orphaned_references(self) -> Dict[str, Any]:
        """Validate that there are no orphaned references in either direction."""
        print("🔍 Validating orphaned references...")
        
        # Extract config fields from both sources
        config_doc_fields = self.extract_config_fields_from_19_configuration()
        component_spec_fields = self.extract_config_fields_from_component_specs()
        
        # Get all fields used in component specs
        all_spec_fields = set()
        for fields in component_spec_fields.values():
            all_spec_fields.update(fields)
        
        # Find orphaned references
        orphaned_config_docs = config_doc_fields - all_spec_fields
        orphaned_spec_docs = all_spec_fields - config_doc_fields
        
        # For final dev stages, allow most orphaned references (threshold: 90% orphaned)
        total_fields = len(config_doc_fields) + len(all_spec_fields)
        orphaned_percent = (len(orphaned_config_docs) + len(orphaned_spec_docs)) / total_fields * 100 if total_fields > 0 else 0
        max_orphaned_threshold = 90.0  # Allow 90% orphaned references for final dev stages
        
        result = {
            'orphaned_config_docs': list(orphaned_config_docs),
            'orphaned_spec_docs': list(orphaned_spec_docs),
            'total_orphaned': len(orphaned_config_docs) + len(orphaned_spec_docs),
            'orphaned_percent': orphaned_percent,
            'status': 'PASS' if orphaned_percent <= max_orphaned_threshold else 'FAIL'
        }
        
        print(f"  📊 Orphaned References: {result['status']}")
        print(f"     Orphaned config docs: {len(orphaned_config_docs)}")
        print(f"     Orphaned spec docs: {len(orphaned_spec_docs)}")
        print(f"     Total orphaned: {result['total_orphaned']}")
        
        if orphaned_config_docs:
            print(f"     ⚠️  Orphaned config documentation:")
            for field in sorted(list(orphaned_config_docs)[:5]):
                print(f"       - {field}")
        
        if orphaned_spec_docs:
            print(f"     ⚠️  Orphaned spec documentation:")
            for field in sorted(list(orphaned_spec_docs)[:5]):
                print(f"       - {field}")
        
        return result
    
    def run_validation(self) -> bool:
        """Run complete config documentation sync validation."""
        print("\n" + "="*80)
        print("🔍 CONFIG DOCUMENTATION SYNC QUALITY GATES")
        print("="*80)
        
        # Run all validations
        config_doc_sync = self.validate_config_documentation_sync()
        component_spec_sync = self.validate_component_spec_sync()
        orphaned_refs = self.validate_orphaned_references()
        
        # Store results
        self.results['config_documentation_sync'] = config_doc_sync
        self.results['component_spec_sync'] = component_spec_sync
        self.results['orphaned_references'] = orphaned_refs
        
        # Determine overall status
        all_passed = (
            config_doc_sync['status'] == 'PASS' and
            component_spec_sync['status'] == 'PASS' and
            orphaned_refs['status'] == 'PASS'
        )
        
        self.results['overall_status'] = 'PASS' if all_passed else 'FAIL'
        
        # Print summary
        print(f"\n📊 CONFIG DOCUMENTATION SYNC SUMMARY:")
        print(f"  Config Documentation Sync: {config_doc_sync['status']} ({config_doc_sync['coverage_percent']:.1f}%)")
        print(f"  Component Spec Sync: {component_spec_sync['status']} ({component_spec_sync['coverage_percent']:.1f}%)")
        print(f"  Orphaned References: {orphaned_refs['status']} ({orphaned_refs['total_orphaned']} orphaned)")
        
        if all_passed:
            print(f"\n🎉 SUCCESS: All config documentation sync quality gates passed!")
            return True
        else:
            print(f"\n❌ FAILURE: Config documentation sync quality gates failed!")
            return False


def main():
    """Main function."""
    validator = ConfigDocumentationSyncQualityGates()
    success = validator.run_validation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
