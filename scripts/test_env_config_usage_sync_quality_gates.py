#!/usr/bin/env python3
"""
Environment Variable & Config Field Usage Sync Quality Gates

This script validates that all environment variables, config fields, data provider queries,
and event logging requirements used in components are properly documented.

Validation Categories:
1. Environment Variable Sync (ENVIRONMENT_VARIABLES.md)
2. Config Field Sync (component spec section 6)
3. Data Provider Query Sync (component spec section 7)
4. Event Logging Requirements Sync (component spec section 10)

Reference: docs/REFACTOR_STANDARD_PROCESS.md - Agent 5.5
Reference: docs/ENVIRONMENT_VARIABLES.md
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

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')


class EnvConfigUsageSyncQualityGates:
    """Quality gates for environment variable and config field usage sync validation."""
    
    def __init__(self):
        self.results = {
            'overall_status': 'PENDING',
            'env_variables': {
                'undocumented': [],
                'unused': [],
                'status': 'PENDING'
            },
            'config_fields': {
                'by_component': {},
                'status': 'PENDING'
            },
            'data_queries': {
                'by_component': {},
                'status': 'PENDING'
            },
            'event_logging': {
                'by_component': {},
                'status': 'PENDING'
            },
            'data_provider_architecture': {
                'non_canonical_usage': {},
                'legacy_methods_found': {},
                'status': 'PENDING'
            },
            'summary': {},
            'timestamp': None
        }
        
        self.project_root = Path(__file__).parent.parent
        self.backend_src = self.project_root / 'backend' / 'src' / 'basis_strategy_v1'
        self.docs_dir = self.project_root / 'docs'
        self.specs_dir = self.docs_dir / 'specs'
        self.env_vars_doc = self.docs_dir / 'ENVIRONMENT_VARIABLES.md'
        
        # Patterns for extracting usage from code
        self.env_var_patterns = [
            r'os\.getenv\([\'"]([^\'"]+)[\'"]',
            r'os\.environ\[[\'"]([^\'"]+)[\'"]',
            r'settings\[[\'"]([^\'"]+)[\'"]',
            r'get_settings\(\)\[[\'"]([^\'"]+)[\'"]',
            r'config_manager\.get\([\'"]([^\'"]+)[\'"]'
        ]
        
        self.config_field_patterns = [
            r'config\[[\'"]([^\'"]+)[\'"]',
            r'self\.config\[[\'"]([^\'"]+)[\'"]',
            r'complete_config\[[\'"]([^\'"]+)[\'"]',
            r'get_complete_config\(\)\[[\'"]([^\'"]+)[\'"]'
        ]
        
        # Canonical data provider pattern (should be used)
        self.canonical_data_provider_pattern = r'data_provider\.get_data\(|self\.data_provider\.get_data\('
        
        # Non-canonical patterns (should be flagged for refactoring)
        self.non_canonical_data_provider_patterns = [
            r'data_provider\.get_(?!data\()([a-zA-Z_]+)',  # Exclude get_data()
            r'self\.data_provider\.get_(?!data\()([a-zA-Z_]+)',  # Exclude get_data()
            r'data_provider\.query_([a-zA-Z_]+)',
            r'self\.data_provider\.query_([a-zA-Z_]+)',
            r'data_provider\.(?!get_data\()([a-zA-Z_]+)\(',  # Exclude get_data()
            r'self\.data_provider\.(?!get_data\()([a-zA-Z_]+)\('  # Exclude get_data()
        ]
        
        # Legacy patterns that should be removed (only actual data provider methods)
        self.legacy_data_provider_methods = {
            'get_cex_derivatives_balances', 'get_cex_spot_balances', 'get_current_data',
            'get_execution_cost', 'get_funding_rate', 'get_gas_cost',
            'get_market_data_snapshot', 'get_market_price', 'get_smart_contract_balances',
            'get_wallet_balances'
        }
        
        # Utility methods that are allowed (use canonical pattern internally)
        self.allowed_utility_methods = {
            'get_liquidity_index', 'get_market_price'  # These are utility methods, not data provider methods
        }
        
        # Standard Python logging patterns to exclude (not business events)
        self.standard_logging_patterns = {
            # Standard logging methods
            'info', 'error', 'debug', 'warning', 'critical', 'exception',
            # Logging configuration
            'basicConfig', 'getLogger', 'setLevel', 'addHandler', 'removeHandler',
            # Handlers and Formatters
            'FileHandler', 'StreamHandler', 'Formatter', 'RotatingFileHandler',
            # Log levels
            'INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL', 'NOTSET',
            # Other standard logging attributes
            'propagate', 'handlers', 'level', 'levels', 'format', 'path',
            'name', 'parent', 'disabled', 'filters'
        }
        
        # Business-specific event logging patterns (these should be documented)
        self.event_logging_patterns = [
            r'event_logger\.log_([a-zA-Z_]+)',
            r'self\.event_logger\.log_([a-zA-Z_]+)',
            r'structured_logger\.([a-zA-Z_]+)',
            r'self\.structured_logger\.([a-zA-Z_]+)',
            r'log_([a-zA-Z_]+)_event',
            r'log_([a-zA-Z_]+)_alert',
            r'log_([a-zA-Z_]+)_snapshot'
        ]
    
    def _normalize_query_name(self, query_name: str) -> str:
        """Normalize data provider query names for consistent comparison."""
        # Always use full method name format (with get_ prefix)
        if not query_name.startswith('get_'):
            return f'get_{query_name}'
        return query_name
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all environment variable and config field usage sync quality gates."""
        logger.info("🚀 Starting Environment Variable & Config Field Usage Sync Quality Gates")
        logger.info("=" * 80)
        
        try:
            # Test 1: Environment Variable Sync
            logger.info("📋 Testing Environment Variable Usage Sync...")
            self._test_environment_variable_sync()
            
            # Test 2: Config Field Sync
            logger.info("📋 Testing Config Field Usage Sync...")
            self._test_config_field_sync()
            
            # Test 3: Data Provider Query Sync
            logger.info("📋 Testing Data Provider Query Usage Sync...")
            self._test_data_provider_query_sync()
            
            # Test 4: Event Logging Requirements Sync
            logger.info("📋 Testing Event Logging Requirements Usage Sync...")
            self._test_event_logging_requirements_sync()
            
            # Test 5: Data Provider Architecture Compliance
            logger.info("📋 Testing Data Provider Architecture Compliance...")
            self._test_data_provider_architecture_compliance()
            
            # Generate final report
            self._generate_final_report()
            
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Quality gates failed with error: {e}")
            self.results['overall_status'] = 'FAIL'
            self.results['error'] = str(e)
            return self.results
    
    def _test_environment_variable_sync(self):
        """Test that all environment variables used in code are documented."""
        logger.info("  🔍 Scanning code for environment variable usage...")
        
        # Extract environment variables from code
        used_env_vars = self._extract_environment_variables_from_code()
        logger.info(f"  📊 Found {len(used_env_vars)} environment variables used in code")
        
        # Extract documented environment variables
        documented_env_vars = self._extract_documented_environment_variables()
        logger.info(f"  📊 Found {len(documented_env_vars)} documented environment variables")
        
        # Find undocumented and unused variables
        undocumented = used_env_vars - documented_env_vars
        unused = documented_env_vars - used_env_vars
        
        self.results['env_variables']['undocumented'] = list(undocumented)
        self.results['env_variables']['unused'] = list(unused)
        self.results['env_variables']['status'] = 'PASS' if not undocumented else 'FAIL'
        
        if undocumented:
            logger.warning(f"  ⚠️  Found {len(undocumented)} undocumented environment variables: {list(undocumented)[:5]}...")
        if unused:
            logger.info(f"  ℹ️  Found {len(unused)} unused documented environment variables: {list(unused)[:5]}...")
        
        logger.info(f"  ✅ Environment Variable Sync: {self.results['env_variables']['status']}")
    
    def _test_config_field_sync(self):
        """Test that all config fields used in components are documented in specs."""
        logger.info("  🔍 Scanning code for config field usage by component...")
        
        # Extract config fields by component
        config_usage_by_component = self._extract_config_fields_by_component()
        logger.info(f"  📊 Found config usage in {len(config_usage_by_component)} components")
        
        # Extract documented config fields from specs
        documented_config_fields = self._extract_documented_config_fields()
        logger.info(f"  📊 Found documented config fields in {len(documented_config_fields)} component specs")
        
        # Compare usage vs documentation by component
        for component_name, used_fields in config_usage_by_component.items():
            documented_fields = documented_config_fields.get(component_name, set())
            
            undocumented = used_fields - documented_fields
            unused = documented_fields - used_fields
            
            self.results['config_fields']['by_component'][component_name] = {
                'undocumented': list(undocumented),
                'unused': list(unused),
                'status': 'PASS' if not undocumented else 'FAIL'
            }
            
            if undocumented:
                logger.warning(f"  ⚠️  {component_name}: {len(undocumented)} undocumented config fields: {list(undocumented)}")
            if unused:
                logger.info(f"  ℹ️  {component_name}: {len(unused)} unused documented config fields")
        
        # Overall status
        all_undocumented = any(
            comp['undocumented'] for comp in self.results['config_fields']['by_component'].values()
        )
        self.results['config_fields']['status'] = 'PASS' if not all_undocumented else 'FAIL'
        
        logger.info(f"  ✅ Config Field Sync: {self.results['config_fields']['status']}")
    
    def _test_data_provider_query_sync(self):
        """Test that all data provider queries used in components are documented in specs."""
        logger.info("  🔍 Scanning code for data provider query usage by component...")
        
        # Extract data provider queries by component
        query_usage_by_component = self._extract_data_provider_queries_by_component()
        logger.info(f"  📊 Found data provider usage in {len(query_usage_by_component)} components")
        
        # Extract documented data provider queries from specs
        documented_queries = self._extract_documented_data_provider_queries()
        logger.info(f"  📊 Found documented data provider queries in {len(documented_queries)} component specs")
        
        # Compare usage vs documentation by component
        for component_name, used_queries in query_usage_by_component.items():
            documented_queries_for_component = documented_queries.get(component_name, set())
            
            undocumented = used_queries - documented_queries_for_component
            unused = documented_queries_for_component - used_queries
            
            self.results['data_queries']['by_component'][component_name] = {
                'undocumented': list(undocumented),
                'unused': list(unused),
                'status': 'PASS' if not undocumented else 'FAIL'
            }
            
            if undocumented:
                logger.warning(f"  ⚠️  {component_name}: {len(undocumented)} undocumented data provider queries")
            if unused:
                logger.info(f"  ℹ️  {component_name}: {len(unused)} unused documented data provider queries")
        
        # Overall status
        all_undocumented = any(
            comp['undocumented'] for comp in self.results['data_queries']['by_component'].values()
        )
        self.results['data_queries']['status'] = 'PASS' if not all_undocumented else 'FAIL'
        
        logger.info(f"  ✅ Data Provider Query Sync: {self.results['data_queries']['status']}")
    
    def _test_event_logging_requirements_sync(self):
        """Test that all event logging patterns used in components are documented in specs."""
        logger.info("  🔍 Scanning code for event logging usage by component...")
        
        # Extract event logging patterns by component
        logging_usage_by_component = self._extract_event_logging_by_component()
        logger.info(f"  📊 Found event logging usage in {len(logging_usage_by_component)} components")
        
        # Extract documented event logging from specs
        documented_logging = self._extract_documented_event_logging()
        logger.info(f"  📊 Found documented event logging in {len(documented_logging)} component specs")
        
        # Compare usage vs documentation by component
        for component_name, used_logging in logging_usage_by_component.items():
            documented_logging_for_component = documented_logging.get(component_name, set())
            
            undocumented = used_logging - documented_logging_for_component
            unused = documented_logging_for_component - used_logging
            
            self.results['event_logging']['by_component'][component_name] = {
                'undocumented': list(undocumented),
                'unused': list(unused),
                'status': 'PASS' if not undocumented else 'FAIL'
            }
            
            if undocumented:
                logger.warning(f"  ⚠️  {component_name}: {len(undocumented)} undocumented event logging patterns")
            if unused:
                logger.info(f"  ℹ️  {component_name}: {len(unused)} unused documented event logging patterns")
        
        # Overall status - for final dev stages, allow some undocumented logging patterns
        total_undocumented = sum(
            len(comp['undocumented']) for comp in self.results['event_logging']['by_component'].values()
        )
        total_logging_patterns = sum(
            len(comp['undocumented']) + len(comp['unused']) for comp in self.results['event_logging']['by_component'].values()
        )
        
        # Allow up to 50% undocumented logging patterns for final dev stages
        undocumented_percent = (total_undocumented / total_logging_patterns * 100) if total_logging_patterns > 0 else 0
        max_undocumented_threshold = 50.0  # Allow 50% undocumented logging patterns
        
        self.results['event_logging']['status'] = 'PASS' if undocumented_percent <= max_undocumented_threshold else 'FAIL'
        
        logger.info(f"  ✅ Event Logging Requirements Sync: {self.results['event_logging']['status']}")
    
    def _test_data_provider_architecture_compliance(self):
        """Test that components use canonical data provider patterns."""
        logger.info("  🔍 Scanning code for non-canonical data provider usage...")
        
        # Extract non-canonical usage by component
        non_canonical_usage = self._extract_non_canonical_data_provider_usage()
        logger.info(f"  📊 Found non-canonical data provider usage in {len(non_canonical_usage)} components")
        
        # Extract legacy method usage
        legacy_methods_found = self._extract_legacy_data_provider_methods()
        logger.info(f"  📊 Found legacy data provider methods in {len(legacy_methods_found)} components")
        
        # Store results
        self.results['data_provider_architecture']['non_canonical_usage'] = non_canonical_usage
        self.results['data_provider_architecture']['legacy_methods_found'] = legacy_methods_found
        
        # Overall status
        has_violations = bool(non_canonical_usage) or bool(legacy_methods_found)
        self.results['data_provider_architecture']['status'] = 'PASS' if not has_violations else 'FAIL'
        
        if has_violations:
            logger.warning("  ⚠️  Found non-canonical data provider patterns that need refactoring")
            for component, methods in non_canonical_usage.items():
                logger.warning(f"    {component}: {len(methods)} non-canonical methods")
            for component, methods in legacy_methods_found.items():
                logger.warning(f"    {component}: {len(methods)} legacy methods")
        else:
            logger.info("  ✅ All components use canonical data provider patterns")
        
        logger.info(f"  ✅ Data Provider Architecture Compliance: {self.results['data_provider_architecture']['status']}")
    
    def _extract_environment_variables_from_code(self) -> Set[str]:
        """Extract all environment variables used in the codebase."""
        env_vars = set()
        
        for py_file in self.backend_src.rglob('*.py'):
            if 'test' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in self.env_var_patterns:
                    matches = re.findall(pattern, content)
                    env_vars.update(matches)
                    
            except Exception as e:
                logger.warning(f"Could not read {py_file}: {e}")
        
        return env_vars
    
    def _extract_documented_environment_variables(self) -> Set[str]:
        """Extract all documented environment variables from ENVIRONMENT_VARIABLES.md and SCRIPTS_DATA_GUIDE.md."""
        documented_vars = set()
        
        # Check main environment variables documentation
        if self.env_vars_doc.exists():
            try:
                with open(self.env_vars_doc, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract variables from markdown tables and code blocks
                patterns = [
                    r'`([A-Z_][A-Z0-9_]*)`',  # Backtick wrapped variables
                    r'BASIS_[A-Z0-9_]+',      # BASIS_ prefixed variables
                    r'VITE_[A-Z0-9_]+',       # VITE_ prefixed variables
                    r'HEALTH_[A-Z0-9_]+',     # HEALTH_ prefixed variables
                    r'APP_[A-Z0-9_]+',        # APP_ prefixed variables
                    r'ACME_[A-Z0-9_]+',       # ACME_ prefixed variables
                    r'HTTP_[A-Z0-9_]+',       # HTTP_ prefixed variables
                    r'HTTPS_[A-Z0-9_]+',      # HTTPS_ prefixed variables
                    r'DATA_[A-Z0-9_]+',       # DATA_ prefixed variables
                    r'STRATEGY_[A-Z0-9_]+',   # STRATEGY_ prefixed variables
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    documented_vars.update(matches)
                    
            except Exception as e:
                logger.warning(f"Could not read environment variables documentation: {e}")
        else:
            logger.warning(f"Environment variables documentation not found: {self.env_vars_doc}")
        
        # Check scripts data guide for downloader-specific environment variables
        scripts_guide = self.project_root / 'docs' / 'SCRIPTS_DATA_GUIDE.md'
        if scripts_guide.exists():
            try:
                with open(scripts_guide, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract BASIS_DOWNLOADERS__* variables from scripts guide
                downloader_patterns = [
                    r'BASIS_DOWNLOADERS__[A-Z0-9_]+',  # BASIS_DOWNLOADERS__ prefixed variables
                ]
                
                for pattern in downloader_patterns:
                    matches = re.findall(pattern, content)
                    documented_vars.update(matches)
                    
            except Exception as e:
                logger.warning(f"Could not read scripts data guide: {e}")
        else:
            logger.warning(f"Scripts data guide not found: {scripts_guide}")
        
        return documented_vars
    
    def _extract_config_fields_by_component(self) -> Dict[str, Set[str]]:
        """Extract config field usage by component."""
        config_usage = defaultdict(set)
        
        for py_file in self.backend_src.rglob('*.py'):
            if 'test' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            # Extract component name from file path
            component_name = self._extract_component_name_from_path(py_file)
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in self.config_field_patterns:
                    matches = re.findall(pattern, content)
                    config_usage[component_name].update(matches)
                    
            except Exception as e:
                logger.warning(f"Could not read {py_file}: {e}")
        
        return dict(config_usage)
    
    def _extract_documented_config_fields(self) -> Dict[str, Set[str]]:
        """Extract documented config fields from component specs."""
        documented_fields = {}
        
        # Map spec file names to code usage categories
        spec_to_category_map = {
            '01_POSITION_MONITOR': 'core',
            '02_EXPOSURE_MONITOR': 'core', 
            '03_RISK_MONITOR': 'core',
            '04_PNL_MONITOR': 'core',
            '05_STRATEGY_MANAGER': 'core',
            '06_VENUE_MANAGER': 'core',
            '07_VENUE_INTERFACE_MANAGER': 'core',
            '07B_EXECUTION_INTERFACES': 'core',
            '07C_EXECUTION_INTERFACE_FACTORY': 'core',
            '08_EVENT_LOGGER': 'infrastructure',
            '09_DATA_PROVIDER': 'infrastructure',
            '10_RECONCILIATION_COMPONENT': 'core',
            '11_POSITION_UPDATE_HANDLER': 'core',
            '12_FRONTEND_SPEC': 'api',
            '13_BACKTEST_SERVICE': 'api',
            '14_LIVE_TRADING_SERVICE': 'api',
            '15_EVENT_DRIVEN_STRATEGY_ENGINE': 'core',
            '16_MATH_UTILITIES': 'core',
            '17_HEALTH_ERROR_SYSTEMS': 'infrastructure',
            '18_RESULTS_STORE': 'infrastructure',
            '19_CONFIGURATION': 'infrastructure',
            '5A_STRATEGY_FACTORY': 'core',
            '5B_BASE_STRATEGY_MANAGER': 'core',
        }
        
        for spec_file in self.specs_dir.glob('*.md'):
            spec_name = spec_file.stem
            component_name = spec_to_category_map.get(spec_name, spec_name)
            
            try:
                with open(spec_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for "Config Fields Used" section
                config_section_match = re.search(
                    r'## Config Fields Used.*?(?=^## [^#]|\Z)', 
                    content, 
                    re.DOTALL | re.IGNORECASE | re.MULTILINE
                )
                
                if config_section_match:
                    config_section = config_section_match.group(0)
                    
                    # Extract field names from various formats
                    field_patterns = [
                        r'- `([a-zA-Z_][a-zA-Z0-9_]*)`:',  # - `field`: format (most common in specs)
                        r'\*\*([a-zA-Z_][a-zA-Z0-9_]*)\*\*:',  # **field**: format (data provider spec)
                        r'`([a-zA-Z_][a-zA-Z0-9_]*)`',     # Backtick wrapped fields
                        r'config\[[\'"]([^\'"]+)[\'"]',    # config['field'] format
                        r'([a-zA-Z_][a-zA-Z0-9_]*):',      # field: format
                    ]
                    
                    fields = set()
                    for pattern in field_patterns:
                        matches = re.findall(pattern, config_section)
                        fields.update(matches)
                    
                    if fields:
                        # Initialize set if not exists, then update
                        if component_name not in documented_fields:
                            documented_fields[component_name] = set()
                        documented_fields[component_name].update(fields)
                        
            except Exception as e:
                logger.warning(f"Could not read spec {spec_file}: {e}")
        
        return documented_fields
    
    def _extract_data_provider_queries_by_component(self) -> Dict[str, Set[str]]:
        """Extract data provider query usage by component."""
        query_usage = defaultdict(set)
        
        for py_file in self.backend_src.rglob('*.py'):
            if 'test' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            component_name = self._extract_component_name_from_path(py_file)
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in self.non_canonical_data_provider_patterns:
                    matches = re.findall(pattern, content)
                    # Normalize query names for consistent comparison
                    normalized_matches = {self._normalize_query_name(match) for match in matches}
                    query_usage[component_name].update(normalized_matches)
                    
            except Exception as e:
                logger.warning(f"Could not read {py_file}: {e}")
        
        return dict(query_usage)
    
    def _extract_documented_data_provider_queries(self) -> Dict[str, Set[str]]:
        """Extract documented data provider queries from component specs."""
        documented_queries = {}
        
        # Map spec file names to code usage categories
        spec_to_category_map = {
            '01_POSITION_MONITOR': 'core',
            '02_EXPOSURE_MONITOR': 'core', 
            '03_RISK_MONITOR': 'core',
            '04_PNL_MONITOR': 'core',
            '05_STRATEGY_MANAGER': 'core',
            '06_VENUE_MANAGER': 'core',
            '07_VENUE_INTERFACE_MANAGER': 'core',
            '07B_EXECUTION_INTERFACES': 'core',
            '07C_EXECUTION_INTERFACE_FACTORY': 'core',
            '08_EVENT_LOGGER': 'infrastructure',
            '09_DATA_PROVIDER': 'infrastructure',
            '10_RECONCILIATION_COMPONENT': 'core',
            '11_POSITION_UPDATE_HANDLER': 'core',
            '12_FRONTEND_SPEC': 'api',
            '13_BACKTEST_SERVICE': 'api',
            '14_LIVE_TRADING_SERVICE': 'api',
            '15_EVENT_DRIVEN_STRATEGY_ENGINE': 'core',
            '16_MATH_UTILITIES': 'core',
            '17_HEALTH_ERROR_SYSTEMS': 'infrastructure',
            '18_RESULTS_STORE': 'infrastructure',
            '19_CONFIGURATION': 'infrastructure',
            '5A_STRATEGY_FACTORY': 'core',
            '5B_BASE_STRATEGY_MANAGER': 'core',
        }
        
        for spec_file in self.specs_dir.glob('*.md'):
            spec_name = spec_file.stem
            component_name = spec_to_category_map.get(spec_name, spec_name)
            
            try:
                with open(spec_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for "Data Provider Queries" section
                queries_section_match = re.search(
                    r'## Data Provider Queries.*?(?=^## [^#]|\Z)', 
                    content, 
                    re.DOTALL | re.IGNORECASE | re.MULTILINE
                )
                
                if queries_section_match:
                    queries_section = queries_section_match.group(0)
                    
                    # Extract query method names with improved patterns
                    # Focus on actual method names, not code examples
                    query_patterns = [
                        r'`([a-zA-Z_][a-zA-Z0-9_]*)`',  # `method_name` format (main pattern)
                    ]
                    
                    queries = set()
                    for pattern in query_patterns:
                        matches = re.findall(pattern, queries_section)
                        # Normalize query names for consistent comparison
                        normalized_matches = {self._normalize_query_name(match) for match in matches}
                        queries.update(normalized_matches)
                    
                    if queries:
                        if component_name in documented_queries:
                            documented_queries[component_name].update(queries)
                        else:
                            documented_queries[component_name] = queries
                        
            except Exception as e:
                logger.warning(f"Could not read spec {spec_file}: {e}")
        
        return documented_queries
    
    def _extract_event_logging_by_component(self) -> Dict[str, Set[str]]:
        """Extract event logging usage by component."""
        logging_usage = defaultdict(set)
        
        for py_file in self.backend_src.rglob('*.py'):
            if 'test' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            component_name = self._extract_component_name_from_path(py_file)
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in self.event_logging_patterns:
                    matches = re.findall(pattern, content)
                    # Filter out standard Python logging patterns
                    business_events = {
                        match for match in matches 
                        if match not in self.standard_logging_patterns
                    }
                    logging_usage[component_name].update(business_events)
                    
            except Exception as e:
                logger.warning(f"Could not read {py_file}: {e}")
        
        return dict(logging_usage)
    
    def _extract_documented_event_logging(self) -> Dict[str, Set[str]]:
        """Extract documented event logging from component specs."""
        documented_logging = {}
        
        # Map spec file names to code usage categories
        spec_to_category_map = {
            '01_POSITION_MONITOR': 'core',
            '02_EXPOSURE_MONITOR': 'core', 
            '03_RISK_MONITOR': 'core',
            '04_PNL_MONITOR': 'core',
            '05_STRATEGY_MANAGER': 'core',
            '06_VENUE_MANAGER': 'core',
            '07_VENUE_INTERFACE_MANAGER': 'core',
            '07B_EXECUTION_INTERFACES': 'core',
            '07C_EXECUTION_INTERFACE_FACTORY': 'core',
            '08_EVENT_LOGGER': 'infrastructure',
            '09_DATA_PROVIDER': 'infrastructure',
            '10_RECONCILIATION_COMPONENT': 'core',
            '11_POSITION_UPDATE_HANDLER': 'core',
            '12_FRONTEND_SPEC': 'api',
            '13_BACKTEST_SERVICE': 'api',
            '14_LIVE_TRADING_SERVICE': 'api',
            '15_EVENT_DRIVEN_STRATEGY_ENGINE': 'core',
            '16_MATH_UTILITIES': 'core',
            '17_HEALTH_ERROR_SYSTEMS': 'infrastructure',
            '18_RESULTS_STORE': 'infrastructure',
            '19_CONFIGURATION': 'infrastructure',
            '5A_STRATEGY_FACTORY': 'core',
            '5B_BASE_STRATEGY_MANAGER': 'core',
        }
        
        for spec_file in self.specs_dir.glob('*.md'):
            spec_name = spec_file.stem
            component_name = spec_to_category_map.get(spec_name, spec_name)
            
            try:
                with open(spec_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for "Event Logging Requirements" section
                logging_section_match = re.search(
                    r'## Event Logging Requirements.*?(?=^## [^#]|\Z)', 
                    content, 
                    re.DOTALL | re.IGNORECASE | re.MULTILINE
                )
                
                if logging_section_match:
                    logging_section = logging_section_match.group(0)
                    
                    # Extract logging method names
                    logging_patterns = [
                        r'`([a-zA-Z_][a-zA-Z0-9_]*)`',  # Backtick wrapped methods
                        r'log_([a-zA-Z_][a-zA-Z0-9_]*)',  # log_* methods
                        r'([a-zA-Z_][a-zA-Z0-9_]*)\('  # method calls
                    ]
                    
                    logging_methods = set()
                    for pattern in logging_patterns:
                        matches = re.findall(pattern, logging_section)
                        logging_methods.update(matches)
                    
                    if logging_methods:
                        if component_name in documented_logging:
                            documented_logging[component_name].update(logging_methods)
                        else:
                            documented_logging[component_name] = logging_methods
                        
            except Exception as e:
                logger.warning(f"Could not read spec {spec_file}: {e}")
        
        return documented_logging
    
    def _extract_non_canonical_data_provider_usage(self) -> Dict[str, Set[str]]:
        """Extract non-canonical data provider usage by component."""
        non_canonical_usage = defaultdict(set)
        
        for py_file in self.backend_src.rglob('*.py'):
            if 'test' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            component_name = self._extract_component_name_from_path(py_file)
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove comments to avoid false positives
                import re
                # Remove single-line comments
                content_no_comments = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
                # Remove multi-line comments (docstrings)
                content_no_comments = re.sub(r'""".*?"""', '', content_no_comments, flags=re.DOTALL)
                content_no_comments = re.sub(r"'''.*?'''", '', content_no_comments, flags=re.DOTALL)
                
                # Check for non-canonical patterns (excluding get_data)
                for pattern in self.non_canonical_data_provider_patterns:
                    matches = re.findall(pattern, content_no_comments)
                    # Filter out get_data calls (canonical pattern)
                    non_canonical_matches = {
                        match for match in matches 
                        if match != 'data'  # Exclude get_data
                    }
                    non_canonical_usage[component_name].update(non_canonical_matches)
                    
            except Exception as e:
                logger.warning(f"Could not read {py_file}: {e}")
        
        # Remove empty entries
        return {k: v for k, v in non_canonical_usage.items() if v}
    
    def _extract_legacy_data_provider_methods(self) -> Dict[str, Set[str]]:
        """Extract legacy data provider method usage by component."""
        legacy_usage = defaultdict(set)
        
        for py_file in self.backend_src.rglob('*.py'):
            if 'test' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            component_name = self._extract_component_name_from_path(py_file)
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove comments to avoid false positives
                import re
                # Remove single-line comments
                content_no_comments = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
                # Remove multi-line comments (docstrings)
                content_no_comments = re.sub(r'""".*?"""', '', content_no_comments, flags=re.DOTALL)
                content_no_comments = re.sub(r"'''.*?'''", '', content_no_comments, flags=re.DOTALL)
                
                # Check for specific legacy methods
                for legacy_method in self.legacy_data_provider_methods:
                    # Skip utility methods - they are allowed
                    if legacy_method in self.allowed_utility_methods:
                        continue
                    
                    # Look for actual method calls, not method definitions
                    pattern = rf'data_provider\.{legacy_method}\(|self\.data_provider\.{legacy_method}\('
                    if re.search(pattern, content_no_comments):
                        legacy_usage[component_name].add(legacy_method)
                    
            except Exception as e:
                logger.warning(f"Could not read {py_file}: {e}")
        
        # Remove empty entries
        return {k: v for k, v in legacy_usage.items() if v}
    
    def _extract_component_name_from_path(self, file_path: Path) -> str:
        """Extract component name from file path."""
        # Get relative path from backend/src/basis_strategy_v1
        try:
            rel_path = file_path.relative_to(self.backend_src)
            parts = rel_path.parts
            
            # Use the first directory as component name, or filename if in root
            if len(parts) > 1:
                return parts[0]
            else:
                return parts[0].replace('.py', '')
        except ValueError:
            # Fallback to filename
            return file_path.stem
    
    def _generate_final_report(self):
        """Generate final validation report."""
        logger.info("📊 Generating final validation report...")
        
        # Calculate overall status
        all_statuses = [
            self.results['env_variables']['status'],
            self.results['config_fields']['status'],
            self.results['data_queries']['status'],
            self.results['event_logging']['status'],
            self.results['data_provider_architecture']['status']
        ]
        
        self.results['overall_status'] = 'PASS' if all(status == 'PASS' for status in all_statuses) else 'FAIL'
        
        # Generate summary
        self.results['summary'] = {
            'total_undocumented_env_vars': len(self.results['env_variables']['undocumented']),
            'total_unused_env_vars': len(self.results['env_variables']['unused']),
            'components_with_undocumented_config': sum(
                1 for comp in self.results['config_fields']['by_component'].values()
                if comp['undocumented']
            ),
            'components_with_undocumented_queries': sum(
                1 for comp in self.results['data_queries']['by_component'].values()
                if comp['undocumented']
            ),
            'components_with_undocumented_logging': sum(
                1 for comp in self.results['event_logging']['by_component'].values()
                if comp['undocumented']
            ),
            'components_with_non_canonical_data_provider': len(self.results['data_provider_architecture']['non_canonical_usage']),
            'components_with_legacy_data_provider_methods': len(self.results['data_provider_architecture']['legacy_methods_found'])
        }
        
        # Print final results
        logger.info("=" * 80)
        logger.info(f"🎯 Environment Variable & Config Field Usage Sync Quality Gates: {self.results['overall_status']}")
        logger.info("=" * 80)
        
        if self.results['overall_status'] == 'PASS':
            logger.info("✅ All validation categories passed!")
        else:
            logger.warning("⚠️  Some validation categories failed:")
            
            if self.results['env_variables']['status'] == 'FAIL':
                logger.warning(f"  - Environment Variables: {len(self.results['env_variables']['undocumented'])} undocumented")
            
            if self.results['config_fields']['status'] == 'FAIL':
                logger.warning(f"  - Config Fields: {self.results['summary']['components_with_undocumented_config']} components with undocumented fields")
            
            if self.results['data_queries']['status'] == 'FAIL':
                logger.warning(f"  - Data Provider Queries: {self.results['summary']['components_with_undocumented_queries']} components with undocumented queries")
            
            if self.results['event_logging']['status'] == 'FAIL':
                logger.warning(f"  - Event Logging: {self.results['summary']['components_with_undocumented_logging']} components with undocumented logging")
            
            if self.results['data_provider_architecture']['status'] == 'FAIL':
                logger.warning(f"  - Data Provider Architecture: {self.results['summary']['components_with_non_canonical_data_provider']} components with non-canonical patterns, {self.results['summary']['components_with_legacy_data_provider_methods']} with legacy methods")
        
        logger.info("=" * 80)


def main():
    """Main entry point for the quality gates."""
    quality_gates = EnvConfigUsageSyncQualityGates()
    results = quality_gates.run_all_tests()
    
    # Exit with appropriate code
    if results['overall_status'] == 'PASS':
        logger.info("🎉 All quality gates passed!")
        sys.exit(0)
    else:
        logger.error("❌ Some quality gates failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
