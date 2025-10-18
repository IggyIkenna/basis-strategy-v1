#!/usr/bin/env python3
"""
Config Spec YAML Sync Quality Gates

Validates that all configuration fields documented in component specs
are properly referenced in YAML configs and vice versa.

Validation Categories:
1. Spec YAML Sync - Every config in specs → used in YAML configs
2. YAML Spec Sync - Every config in YAML configs → documented in specs
3. Orphaned References - No orphaned references in either direction

Reference: docs/REFACTOR_STANDARD_PROCESS.md - Agent 5.5
Reference: docs/specs/ (component specifications)
Reference: configs/ (YAML configuration files)
"""

import os
import sys
import re
import json
import logging
import yaml
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


class ConfigSpecYamlSyncQualityGates:
    """Quality gates for config spec YAML sync validation."""
    
    def __init__(self):
        self.results = {
            'overall_status': 'PENDING',
            'spec_yaml_sync': {
                'undocumented_in_yaml': [],
                'status': 'PENDING'
            },
            'yaml_spec_sync': {
                'undocumented_in_specs': [],
                'status': 'PENDING'
            },
            'orphaned_references': {
                'orphaned_spec_docs': [],
                'orphaned_yaml_docs': [],
                'status': 'PENDING'
            }
        }
        
        self.project_root = Path(__file__).parent.parent
        self.docs_dir = self.project_root / "docs"
        self.specs_dir = self.docs_dir / "specs"
        self.configs_dir = self.project_root / "configs"
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
            # Metadata fields (not config fields)
            'type', 'venue', 'base_currency',
            # Documentation artifacts (not config fields)
            'example', 'validation',
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
    
    def extract_config_fields_from_specs(self) -> Dict[str, Set[str]]:
        """Extract required config fields from all component specs using line-by-line parsing."""
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
        
        # Scan top-level specs
        for spec_file in self.specs_dir.glob("*.md"):
            if spec_file.name == "19_CONFIGURATION.md":
                continue  # Skip the main config doc
            
            component_name = spec_file.stem
            config_fields = set()
            
            # Simple line-by-line parsing
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
                    # Extract field names from lines with **field_name**:
                    elif in_config_section and '**' in line and ':' in line:
                        match = re.search(r'\*\*([a-zA-Z_][a-zA-Z0-9_.]*)\*\*:', line)
                        if match:
                            field = match.group(1)
                            # Only add if it's a valid config field
                            if (field and 
                                field in all_required_fields and
                                field not in self.EXCLUDE_TERMS and
                                ('.' in field or field in ['mode', 'share_class', 'asset', 'initial_capital', 'candle_interval', 'data_requirements', 'lending_enabled', 'staking_enabled', 'basis_trade_enabled', 'leverage_supported', 'target_apy_range'])):
                                config_fields.add(field)
            
            if config_fields:
                component_configs[component_name] = config_fields
                logger.info(f"Extracted {len(config_fields)} required config fields from {component_name}")
        
        # Scan strategy specs
        strategies_dir = self.specs_dir / "strategies"
        if strategies_dir.exists():
            for strategy_file in strategies_dir.glob("*.md"):
                component_name = strategy_file.stem
                config_fields = set()
                
                # Apply same line-by-line parsing logic to strategy specs
                in_config_section = False
                with open(strategy_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        # Detect start of Config Fields Used section
                        if '## Config Fields Used' in line:
                            in_config_section = True
                            continue
                        # Detect end of section (next ## heading, not ###)
                        elif line.startswith('##') and not line.startswith('###') and in_config_section:
                            break
                        # Extract field names from lines with **field_name**:
                        elif in_config_section and '**' in line and ':' in line:
                            match = re.search(r'\*\*([a-zA-Z_][a-zA-Z0-9_.]*)\*\*:', line)
                            if match:
                                field = match.group(1)
                                # Only add if it's a valid config field
                                if (field and 
                                    field in all_required_fields and
                                    field not in self.EXCLUDE_TERMS and
                                    ('.' in field or field in ['mode', 'share_class', 'asset', 'initial_capital', 'candle_interval', 'data_requirements', 'lending_enabled', 'staking_enabled', 'basis_trade_enabled', 'leverage_supported', 'target_apy_range'])):
                                    config_fields.add(field)
                
                if config_fields:
                    component_configs[component_name] = config_fields
                    logger.info(f"Extracted {len(config_fields)} required config fields from strategy {component_name}")
        
        return component_configs
    
    def extract_config_fields_from_yaml(self) -> Set[str]:
        """Extract config fields from YAML configuration files."""
        yaml_fields = set()
        
        # Top-level parent fields that are meaningless to check (if we have sub-levels, we have the parent)
        TOP_LEVEL_PARENT_FIELDS = {
            'component_config', 'api_contract', 'auth', 'endpoints', 'event_logger', 
            'ml_config', 'venues', 'instruments'
        }
        
        # Metadata and documentation fields that should be excluded from config field validation
        METADATA_FIELDS = {
            'type', 'venue', 'base_currency', 'example', 'validation', 'venue_type'
        }
        
        if not self.configs_dir.exists():
            logger.error(f"Configs directory not found: {self.configs_dir}")
            return yaml_fields
        
        # Get all required fields from all config types
        all_required_fields = set()
        for config_type in ['ModeConfig', 'VenueConfig', 'ShareClassConfig']:
            fields_by_level = self.field_classifier.get_required_fields_by_level(config_type)
            # Add required fields (top-level, nested, fixed schema dicts)
            for level in ['required_toplevel', 'required_nested', 'fixed_schema_dict']:
                all_required_fields.update(fields_by_level[level])
            # Add dynamic dict parents
            all_required_fields.update(fields_by_level['dynamic_dict'])
        
        # Scan all YAML files in configs directory
        for yaml_file in self.configs_dir.rglob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    if config_data:
                        # Special handling for venue configs: prepend "venues.{venue_name}."
                        prefix = ""
                        if yaml_file.parent.name == "venues":
                            # Get venue name from the config itself or filename
                            venue_name = config_data.get('venue', yaml_file.stem)
                            prefix = f"venues.{venue_name}"
                        
                        # Extract all field paths from YAML structure
                        self._extract_yaml_fields(config_data, prefix, yaml_fields, all_required_fields, METADATA_FIELDS)
            except Exception as e:
                logger.warning(f"Failed to parse {yaml_file}: {e}")
        
        logger.info(f"Extracted {len(yaml_fields)} config fields from YAML files")
        return yaml_fields
    
    def _extract_yaml_fields(self, data: Any, prefix: str, fields: Set[str], valid_fields: Set[str], metadata_fields: Set[str]):
        """Recursively extract field paths from YAML data."""
        # Top-level parent fields that are meaningless to check (if we have sub-levels, we have the parent)
        TOP_LEVEL_PARENT_FIELDS = {
            'component_config', 'api_contract', 'auth', 'endpoints', 'event_logger', 
            'ml_config', 'venues', 'instruments'
        }
        
        if isinstance(data, dict):
            for key, value in data.items():
                field_path = f"{prefix}.{key}" if prefix else key
                # Skip top-level parent fields - they're meaningless if we have sub-levels
                if field_path in TOP_LEVEL_PARENT_FIELDS:
                    # Still process children, but don't add the parent field itself
                    if isinstance(value, (dict, list)):
                        self._extract_yaml_fields(value, field_path, fields, valid_fields, metadata_fields)
                    continue
                
                # Skip metadata and documentation fields
                if key in metadata_fields:
                    continue
                    
                # Only add if it's a valid config field
                if (field_path in valid_fields and 
                    field_path not in self.EXCLUDE_TERMS):
                    fields.add(field_path)
                # Recursively process nested structures
                if isinstance(value, (dict, list)):
                    self._extract_yaml_fields(value, field_path, fields, valid_fields, metadata_fields)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    self._extract_yaml_fields(item, prefix, fields, valid_fields, metadata_fields)
    
    def validate_spec_yaml_sync(self) -> Dict[str, Any]:
        """Validate that all config fields in specs are used in YAML configs."""
        print("🔍 Validating spec YAML sync...")
        
        # Extract config fields from both sources
        spec_fields_dict = self.extract_config_fields_from_specs()
        yaml_fields = self.extract_config_fields_from_yaml()
        
        # Get all fields used in specs
        all_spec_fields = set()
        for fields in spec_fields_dict.values():
            all_spec_fields.update(fields)
        
        # Find spec fields that are not used in YAML configs
        undocumented_in_yaml = all_spec_fields - yaml_fields
        
        # Require 100% coverage for required fields
        coverage_percent = ((len(all_spec_fields) - len(undocumented_in_yaml)) / len(all_spec_fields)) * 100 if all_spec_fields else 100
        min_coverage_threshold = 100.0  # Require 100% coverage for required fields
        
        result = {
            'total_spec_fields': len(all_spec_fields),
            'total_yaml_fields': len(yaml_fields),
            'undocumented_in_yaml': list(undocumented_in_yaml),
            'coverage_percent': coverage_percent,
            'status': 'PASS' if coverage_percent >= min_coverage_threshold else 'FAIL'
        }
        
        print(f"  📊 Spec YAML Sync: {result['status']}")
        print(f"     Total spec fields: {result['total_spec_fields']}")
        print(f"     Total YAML fields: {result['total_yaml_fields']}")
        print(f"     Coverage: {result['coverage_percent']:.1f}%")
        
        if undocumented_in_yaml:
            print(f"     ⚠️  {len(undocumented_in_yaml)} spec fields not used in YAML configs:")
            for field in sorted(list(undocumented_in_yaml)):  # Show all fields
                print(f"       - {field}")
        
        return result
    
    def validate_yaml_spec_sync(self) -> Dict[str, Any]:
        """Validate that all config fields in YAML configs are documented in specs."""
        print("🔍 Validating YAML spec sync...")
        
        # Extract config fields from both sources
        spec_fields_dict = self.extract_config_fields_from_specs()
        yaml_fields = self.extract_config_fields_from_yaml()
        
        # Get all fields used in specs
        all_spec_fields = set()
        for fields in spec_fields_dict.values():
            all_spec_fields.update(fields)
        
        # Find YAML fields that are not documented in specs
        undocumented_in_specs = yaml_fields - all_spec_fields
        
        result = {
            'total_yaml_fields': len(yaml_fields),
            'total_spec_fields': len(all_spec_fields),
            'undocumented_in_specs': list(undocumented_in_specs),
            'coverage_percent': ((len(yaml_fields) - len(undocumented_in_specs)) / len(yaml_fields)) * 100 if yaml_fields else 100,
            'status': 'PASS' if len(undocumented_in_specs) == 0 else 'FAIL'
        }
        
        print(f"  📊 YAML Spec Sync: {result['status']}")
        print(f"     Total YAML fields: {result['total_yaml_fields']}")
        print(f"     Total spec fields: {result['total_spec_fields']}")
        print(f"     Coverage: {result['coverage_percent']:.1f}%")
        
        if undocumented_in_specs:
            print(f"     ⚠️  {len(undocumented_in_specs)} YAML fields not documented in specs:")
            for field in sorted(list(undocumented_in_specs)):  # Show all fields
                print(f"       - {field}")
        
        return result
    
    def validate_orphaned_references(self) -> Dict[str, Any]:
        """Validate that there are no orphaned references in either direction."""
        print("🔍 Validating orphaned references...")
        
        # Extract config fields from both sources
        spec_fields_dict = self.extract_config_fields_from_specs()
        yaml_fields = self.extract_config_fields_from_yaml()
        
        # Get all fields used in specs
        all_spec_fields = set()
        for fields in spec_fields_dict.values():
            all_spec_fields.update(fields)
        
        # Find orphaned references
        orphaned_spec_docs = all_spec_fields - yaml_fields
        orphaned_yaml_docs = yaml_fields - all_spec_fields
        
        # Require 0% orphaned references for 100% compliance
        total_fields = len(all_spec_fields) + len(yaml_fields)
        orphaned_percent = (len(orphaned_spec_docs) + len(orphaned_yaml_docs)) / total_fields * 100 if total_fields > 0 else 0
        max_orphaned_threshold = 0.0  # No orphaned references allowed for 100% compliance
        
        result = {
            'orphaned_spec_docs': list(orphaned_spec_docs),
            'orphaned_yaml_docs': list(orphaned_yaml_docs),
            'total_orphaned': len(orphaned_spec_docs) + len(orphaned_yaml_docs),
            'orphaned_percent': orphaned_percent,
            'status': 'PASS' if orphaned_percent <= max_orphaned_threshold else 'FAIL'
        }
        
        print(f"  📊 Orphaned References: {result['status']}")
        print(f"     Orphaned spec docs: {len(orphaned_spec_docs)}")
        print(f"     Orphaned YAML docs: {len(orphaned_yaml_docs)}")
        print(f"     Total orphaned: {result['total_orphaned']}")
        
        if orphaned_spec_docs:
            print(f"     ⚠️  Orphaned spec documentation:")
            for field in sorted(list(orphaned_spec_docs)[:5]):
                print(f"       - {field}")
        
        if orphaned_yaml_docs:
            print(f"     ⚠️  Orphaned YAML documentation:")
            for field in sorted(list(orphaned_yaml_docs)[:5]):
                print(f"       - {field}")
        
        return result
    
    def run_validation(self) -> bool:
        """Run complete config spec YAML sync validation."""
        print("\n" + "="*80)
        print("🔍 CONFIG SPEC YAML SYNC QUALITY GATES")
        print("="*80)
        
        # Run all validations
        spec_yaml_sync = self.validate_spec_yaml_sync()
        yaml_spec_sync = self.validate_yaml_spec_sync()
        orphaned_refs = self.validate_orphaned_references()
        
        # Store results
        self.results['spec_yaml_sync'] = spec_yaml_sync
        self.results['yaml_spec_sync'] = yaml_spec_sync
        self.results['orphaned_references'] = orphaned_refs
        
        # Determine overall status
        all_passed = (
            spec_yaml_sync['status'] == 'PASS' and
            yaml_spec_sync['status'] == 'PASS' and
            orphaned_refs['status'] == 'PASS'
        )
        
        self.results['overall_status'] = 'PASS' if all_passed else 'FAIL'
        
        # Print summary
        print(f"\n📊 CONFIG SPEC YAML SYNC SUMMARY:")
        print(f"  Spec YAML Sync: {spec_yaml_sync['status']} ({spec_yaml_sync['coverage_percent']:.1f}%)")
        print(f"  YAML Spec Sync: {yaml_spec_sync['status']} ({yaml_spec_sync['coverage_percent']:.1f}%)")
        print(f"  Orphaned References: {orphaned_refs['status']} ({orphaned_refs['total_orphaned']} orphaned)")
        
        if all_passed:
            print(f"\n🎉 SUCCESS: All config spec YAML sync quality gates passed!")
            return True
        else:
            print(f"\n❌ FAILURE: Config spec YAML sync quality gates failed!")
            return False


def main():
    """Main function."""
    validator = ConfigSpecYamlSyncQualityGates()
    success = validator.run_validation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
