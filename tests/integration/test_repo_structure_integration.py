#!/usr/bin/env python3
"""
Repository Structure Validation Quality Gates

This script validates that the actual backend repository structure aligns with
canonical documentation (specs, architecture docs, patterns) and generates an
updated TARGET_REPOSITORY_STRUCTURE.md with file annotations (KEEP/DELETE/UPDATE/MOVE/CREATE).

Usage:
    python scripts/test_repo_structure_quality_gates.py
"""

import os
import sys
import json
import glob
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from datetime import datetime
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class RepositoryStructureValidator:
    """Validates repository structure against canonical documentation."""
    
    def __init__(self):
        self.project_root = project_root.parent  # Go up one level from tests/ to project root
        self.backend_root = self.project_root / "backend" / "src" / "basis_strategy_v1"
        self.docs_root = self.project_root / "docs"
        self.specs_root = self.docs_root / "specs"
        
        # Results storage
        self.structure_alignment = {
            'correct_files': [],
            'misplaced_files': [],
            'missing_files': [],
            'obsolete_files': [],
            'files_needing_update': []
        }
        
        # Canonical sources
        self.component_specs = {}
        self.expected_structure = {}
        self.patterns = {}
        
    def load_canonical_sources(self) -> None:
        """Load all canonical documentation sources."""
        print("Loading canonical documentation sources...")
        
        # Load component specs
        self._load_component_specs()
        
        # Load CODE_STRUCTURE_PATTERNS.md
        self._load_code_structure_patterns()
        
        # Load REFERENCE_ARCHITECTURE_CANONICAL.md
        self._load_reference_architecture()
        
        # Build expected structure from canonical sources
        self._build_expected_structure()
        
    def _load_component_specs(self) -> None:
        """Load all component specifications."""
        if not self.specs_root.exists():
            print(f"Warning: Specs directory not found: {self.specs_root}")
            return
            
        for spec_file in self.specs_root.glob("*.md"):
            try:
                with open(spec_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract component name and expected location
                lines = content.split('\n')
                component_name = None
                expected_location = None
                
                for line in lines:
                    if line.startswith('# ') and 'Component' in line:
                        component_name = line.replace('# ', '').replace(' Component', '').strip()
                    elif 'Expected Location:' in line or 'File Location:' in line:
                        expected_location = line.split(':', 1)[1].strip()
                        
                if component_name:
                    self.component_specs[component_name.lower()] = {
                        'name': component_name,
                        'file': spec_file.name,
                        'expected_location': expected_location,
                        'content': content
                    }
                    
            except Exception as e:
                print(f"Error loading spec {spec_file}: {e}")
                
    def _load_code_structure_patterns(self) -> None:
        """Load CODE_STRUCTURE_PATTERNS.md."""
        patterns_file = self.docs_root / "CODE_STRUCTURE_PATTERNS.md"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self.patterns['code_structure'] = f.read()
            except Exception as e:
                print(f"Error loading CODE_STRUCTURE_PATTERNS.md: {e}")
        else:
            print(f"Warning: CODE_STRUCTURE_PATTERNS.md not found: {patterns_file}")
            
    def _load_reference_architecture(self) -> None:
        """Load REFERENCE_ARCHITECTURE_CANONICAL.md."""
        arch_file = self.docs_root / "REFERENCE_ARCHITECTURE_CANONICAL.md"
        if arch_file.exists():
            try:
                with open(arch_file, 'r', encoding='utf-8') as f:
                    self.patterns['reference_architecture'] = f.read()
            except Exception as e:
                print(f"Error loading REFERENCE_ARCHITECTURE_CANONICAL.md: {e}")
        else:
            print(f"Warning: REFERENCE_ARCHITECTURE_CANONICAL.md not found: {arch_file}")
            
    def _build_expected_structure(self) -> None:
        """Build expected structure from canonical sources."""
        # Based on canonical patterns, specs, and API documentation, define expected structure
        self.expected_structure = {
            # Core components (from specs)
            'core/components/': {
                'position_monitor.py': '01_POSITION_MONITOR.md',
                'exposure_monitor.py': '02_EXPOSURE_MONITOR.md', 
                'risk_monitor.py': '03_RISK_MONITOR.md',
                'position_update_handler.py': '11_POSITION_UPDATE_HANDLER.md',
                'strategy_manager.py': '05_STRATEGY_MANAGER.md',
                '__init__.py': 'Required for package'
            },
            # Strategy components (from specs and modes)
            'core/strategies/': {
                'base_strategy_manager.py': '5B_BASE_STRATEGY_MANAGER.md',
                'strategy_factory.py': '5A_STRATEGY_FACTORY.md',
                'pure_lending_strategy.py': 'MODES.md',
                'btc_basis_strategy.py': 'MODES.md',
                'eth_basis_strategy.py': 'MODES.md',
                'eth_staking_only_strategy.py': 'MODES.md',
                'eth_leveraged_strategy.py': 'MODES.md',
                'usdt_market_neutral_no_leverage_strategy.py': 'MODES.md',
                'usdt_market_neutral_strategy.py': 'MODES.md',
                '__init__.py': 'Required for package'
            },
            # Execution components (from specs)
            'core/execution/': {
                'venue_manager.py': '06_VENUE_MANAGER.md',
                'venue_interface_manager.py': '07_VENUE_INTERFACE_MANAGER.md',
                'wallet_transfer_executor.py': 'Required for execution',
                '__init__.py': 'Required for package'
            },
            # Core interfaces (from specs)
            'core/interfaces/': {
                'base_execution_interface.py': '07A_VENUE_INTERFACES.md',
                'base_position_interface.py': '07A_VENUE_INTERFACES.md',
                'cex_execution_interface.py': '07A_VENUE_INTERFACES.md',
                'cex_position_interface.py': '07A_VENUE_INTERFACES.md',
                'dex_execution_interface.py': '07A_VENUE_INTERFACES.md',
                'venue_interface_factory.py': '07B_VENUE_INTERFACE_FACTORY.md',
                'onchain_execution_interface.py': '07A_VENUE_INTERFACES.md',
                'onchain_position_interface.py': '07A_VENUE_INTERFACES.md',
                'transfer_execution_interface.py': '07A_VENUE_INTERFACES.md',
                'transfer_position_interface.py': '07A_VENUE_INTERFACES.md',
                '__init__.py': 'Required for package'
            },
            # Core math components (from specs)
            'core/math/': {
                'pnl_calculator.py': '04_PNL_CALCULATOR.md - P&L calculation',
                'health_calculator.py': '17_HEALTH_ERROR_SYSTEMS.md - Health calculations',
                'ltv_calculator.py': 'WORKFLOW_GUIDE.md - LTV calculations',
                'margin_calculator.py': 'WORKFLOW_GUIDE.md - Margin calculations',
                'metrics_calculator.py': 'API_DOCUMENTATION.md - Metrics calculation',
                '__init__.py': 'Required for package'
            },
            # Core event engine (from specs)
            'core/event_engine/': {
                'event_driven_strategy_engine.py': '15_EVENT_DRIVEN_STRATEGY_ENGINE.md',
                '__init__.py': 'Required for package'
            },
            # Core services (from specs)
            'core/services/': {
                'backtest_service.py': '13_BACKTEST_SERVICE.md',
                'live_service.py': '14_LIVE_TRADING_SERVICE.md',
                '__init__.py': 'Required for package'
            },
            # Core reconciliation (from specs)
            'core/reconciliation/': {
                'reconciliation_component.py': '10_RECONCILIATION_COMPONENT.md',
                '__init__.py': 'Required for package'
            },
            # Core health systems (from specs)
            'core/health/': {
                'component_health.py': '17_HEALTH_ERROR_SYSTEMS.md',
                'unified_health_manager.py': '17_HEALTH_ERROR_SYSTEMS.md',
                '__init__.py': 'Required for package'
            },
            # Core error codes (from specs)
            'core/error_codes/': {
                'error_code_registry.py': '17_HEALTH_ERROR_SYSTEMS.md',
                'exceptions.py': '17_HEALTH_ERROR_SYSTEMS.md',
                '__init__.py': 'Required for package'
            },
            # Core instructions (from specs)
            'core/instructions/': {
                'execution_instructions.py': 'WORKFLOW_GUIDE.md - Execution instructions',
                '__init__.py': 'Required for package'
            },
            # Core utilities (from specs)
            'core/utilities/': {
                'utility_manager.py': '16_MATH_UTILITIES.md - Utility management',
                '__init__.py': 'Required for package'
            },
            # Core rebalancing (from specs)
            'core/rebalancing/': {
                '__init__.py': 'Required for package'
            },
            # Infrastructure data (from specs)
            'infrastructure/data/': {
                'data_provider_factory.py': '05_DATA_PROVIDER_FACTORY.md',
                'base_data_provider.py': '09_DATA_PROVIDER.md',
                'btc_basis_data_provider.py': '09_DATA_PROVIDER.md',
                'config_driven_historical_data_provider.py': '09_DATA_PROVIDER.md',
                'data_validator.py': '09_DATA_PROVIDER.md',
                'eth_basis_data_provider.py': '09_DATA_PROVIDER.md',
                'eth_leveraged_data_provider.py': '09_DATA_PROVIDER.md',
                'eth_staking_only_data_provider.py': '09_DATA_PROVIDER.md',
                'historical_data_provider.py': '09_DATA_PROVIDER.md',
                'live_data_provider.py': '09_DATA_PROVIDER.md',
                'ml_directional_data_provider.py': '09_DATA_PROVIDER.md',
                'pure_lending_data_provider.py': '09_DATA_PROVIDER.md',
                'usdt_market_neutral_data_provider.py': '09_DATA_PROVIDER.md',
                'usdt_market_neutral_no_leverage_data_provider.py': '09_DATA_PROVIDER.md',
                '__init__.py': 'Required for package'
            },
            # Infrastructure logging (from specs)
            'infrastructure/logging/': {
                'event_logger.py': '08_EVENT_LOGGER.md',
                'structured_logger.py': 'Required for logging',
                '__init__.py': 'Required for package'
            },
            # Infrastructure API (from specs)
            'infrastructure/api/': {
                'api_call_queue.py': '09_API_CALL_QUEUE.md',
                '__init__.py': 'Required for package'
            },
            # Infrastructure config (from specs)
            'infrastructure/config/': {
                'config_loader.py': '19_CONFIGURATION.md - Configuration loading',
                'config_manager.py': '19_CONFIGURATION.md - Configuration management',
                'config_validator.py': '19_CONFIGURATION.md - Configuration validation',
                'environment_loader.py': 'ENVIRONMENT_VARIABLES.md - Environment variable loading',
                'models.py': '19_CONFIGURATION.md - Configuration models',
                '__init__.py': 'Required for package'
            },
            # Infrastructure health (from specs)
            'infrastructure/health/': {
                'health_checker.py': '17_HEALTH_ERROR_SYSTEMS.md',
                '__init__.py': 'Required for package'
            },
            # Infrastructure monitoring (from specs)
            'infrastructure/monitoring/': {
                'logging.py': 'API_DOCUMENTATION.md - Logging and monitoring',
                'metrics.py': 'API_DOCUMENTATION.md - Metrics collection',
                '__init__.py': 'Required for package'
            },
            # Infrastructure persistence (from specs)
            'infrastructure/persistence/': {
                'async_results_store.py': '18_RESULTS_STORE.md - Async results storage',
                'result_store.py': '18_RESULTS_STORE.md - Results storage',
                '__init__.py': 'Required for package'
            },
            # Infrastructure storage (from specs)
            'infrastructure/storage/': {
                'chart_storage.py': 'API_DOCUMENTATION.md - Charts Endpoints section',
                '__init__.py': 'Required for package'
            },
            # Infrastructure visualization (from specs)
            'infrastructure/visualization/': {
                'chart_generator.py': 'API_DOCUMENTATION.md - Charts Endpoints section',
                '__init__.py': 'Required for package'
            },
            # Venue adapters (from venue architecture and configs)
            'venue_adapters/': {
                'aave_adapter.py': 'docs/VENUE_ARCHITECTURE.md - AAVE V3 lending/borrowing integration',
                'morpho_adapter.py': 'docs/VENUE_ARCHITECTURE.md - Morpho flash loan integration',
                'alchemy_adapter.py': 'docs/VENUE_ARCHITECTURE.md - Alchemy RPC provider integration',
                'binance_adapter.py': 'docs/VENUE_ARCHITECTURE.md - Binance CEX trading integration',
                'bybit_adapter.py': 'docs/VENUE_ARCHITECTURE.md - Bybit CEX trading integration',
                'etherfi_adapter.py': 'docs/VENUE_ARCHITECTURE.md - EtherFi liquid staking integration',
                'instadapp_adapter.py': 'docs/VENUE_ARCHITECTURE.md - Instadapp atomic transaction middleware integration',
                'lido_adapter.py': 'docs/VENUE_ARCHITECTURE.md - Lido liquid staking integration',
                'ml_inference_api_adapter.py': 'docs/VENUE_ARCHITECTURE.md - ML inference API integration',
                'okx_adapter.py': 'docs/VENUE_ARCHITECTURE.md - OKX CEX trading integration',
                'uniswap_adapter.py': 'docs/VENUE_ARCHITECTURE.md - Uniswap DEX trading integration',
                '__init__.py': 'Required for package'
            },
            # API components (from API documentation)
            'api/': {
                '__init__.py': 'Required for package',
                'dependencies.py': 'API_DOCUMENTATION.md - API dependencies and DI',
                'health.py': 'API_DOCUMENTATION.md - Health Endpoints section',
                'main.py': 'API_DOCUMENTATION.md - API Overview section'
            },
            'api/middleware/': {
                '__init__.py': 'Required for package',
                'correlation.py': 'API_DOCUMENTATION.md - Request correlation middleware'
            },
            'api/models/': {
                '__init__.py': 'Required for package',
                'requests.py': 'API_DOCUMENTATION.md - Request/Response models',
                'responses.py': 'API_DOCUMENTATION.md - Request/Response models'
            },
            'api/routes/': {
                '__init__.py': 'Required for package',
                'auth.py': 'API_DOCUMENTATION.md - Authentication Endpoints section',
                'backtest.py': 'API_DOCUMENTATION.md - Backtest Endpoints section',
                'capital.py': 'API_DOCUMENTATION.md - Capital Management Endpoints section',
                'charts.py': 'API_DOCUMENTATION.md - Charts Endpoints section',
                'config.py': 'API_DOCUMENTATION.md - Configuration endpoints',
                'health.py': 'API_DOCUMENTATION.md - Health Endpoints section',
                'live_trading.py': 'API_DOCUMENTATION.md - Live Trading Endpoints section',
                'results.py': 'API_DOCUMENTATION.md - Results & Export Endpoints section',
                'strategies.py': 'API_DOCUMENTATION.md - Strategy Information Endpoints section'
            },
            # Root packages
            'core/': {
                '__init__.py': 'Required for package'
            },
            'infrastructure/': {
                '__init__.py': 'Required for package'
            },
            # Root package files
            '': {
                '__init__.py': 'Required for package',
                '__version__.py': 'Package version information'
            }
        }
        
    def scan_current_structure(self) -> Dict[str, Any]:
        """Scan current backend directory structure."""
        print("Scanning current backend structure...")
        
        current_files = {}
        
        if not self.backend_root.exists():
            print(f"Error: Backend directory not found: {self.backend_root}")
            return current_files
            
        for py_file in self.backend_root.rglob("*.py"):
            rel_path = py_file.relative_to(self.backend_root)
            current_files[str(rel_path)] = {
                'absolute_path': str(py_file),
                'relative_path': str(rel_path),
                'size': py_file.stat().st_size,
                'modified': datetime.fromtimestamp(py_file.stat().st_mtime)
            }
            
        return current_files
    
    def _validate_venue_centric_naming(self, current_files: Dict[str, Any]) -> None:
        """Validate venue-centric naming conventions."""
        print("Validating venue-centric naming conventions...")
        
        # Check for legacy execution-centric files that should be venue-centric
        legacy_files = [
            'core/interfaces/execution_interface_factory.py',
            'core/execution/execution_interface_manager.py', 
            'core/execution/execution_manager.py'
        ]
        
        for legacy_file in legacy_files:
            if legacy_file in current_files:
                self.structure_alignment['obsolete_files'].append({
                    'path': legacy_file,
                    'reason': 'Legacy execution-centric naming - should be venue-centric',
                    'status': 'obsolete'
                })
        
        # Check for venue-centric files that should exist
        venue_centric_files = [
            'core/interfaces/venue_interface_factory.py',
            'core/execution/venue_interface_manager.py',
            'core/execution/venue_manager.py'
        ]
        
        for venue_file in venue_centric_files:
            if venue_file not in current_files:
                self.structure_alignment['missing_files'].append({
                    'expected_path': venue_file,
                    'spec': 'Venue-centric architecture requirement',
                    'status': 'missing'
                })
        
        # Check for legacy spec files that should be venue-centric
        legacy_specs = [
            'docs/specs/06_EXECUTION_MANAGER.md',
            'docs/specs/07_EXECUTION_INTERFACE_MANAGER.md',
            'docs/specs/07B_EXECUTION_INTERFACES.md',
            'docs/specs/07C_EXECUTION_INTERFACE_FACTORY.md'
        ]
        
        for legacy_spec in legacy_specs:
            spec_path = str(self.project_root / legacy_spec)
            if os.path.exists(spec_path):
                self.structure_alignment['obsolete_files'].append({
                    'path': legacy_spec,
                    'reason': 'Legacy execution-centric spec - should be venue-centric',
                    'status': 'obsolete'
                })
        
        # Check for venue-centric spec files that should exist
        venue_centric_specs = [
            'docs/specs/06_VENUE_MANAGER.md',
            'docs/specs/07_VENUE_INTERFACE_MANAGER.md',
            'docs/specs/07A_VENUE_INTERFACES.md',
            'docs/specs/07B_VENUE_INTERFACE_FACTORY.md'
        ]
        
        for venue_spec in venue_centric_specs:
            spec_path = str(self.project_root / venue_spec)
            if not os.path.exists(spec_path):
                self.structure_alignment['missing_files'].append({
                    'expected_path': venue_spec,
                    'spec': 'Venue-centric architecture requirement',
                    'status': 'missing'
                })
        
    def validate_structure_alignment(self, current_files: Dict[str, Any]) -> None:
        """Validate current structure against expected structure."""
        print("Validating structure alignment...")
        
        # Validate venue-centric naming conventions
        self._validate_venue_centric_naming(current_files)
        
        # Build expected file paths
        expected_file_paths = {}
        for dir_path, files in self.expected_structure.items():
            for file_name, spec_ref in files.items():
                if dir_path == '':
                    # Root files
                    expected_path = file_name
                else:
                    # Files in subdirectories
                    expected_path = f"{dir_path.rstrip('/')}/{file_name}"
                expected_file_paths[expected_path] = spec_ref
        
        # Check each expected file
        for expected_path, spec_ref in expected_file_paths.items():
            if expected_path in current_files:
                self.structure_alignment['correct_files'].append({
                    'path': expected_path,
                    'spec': spec_ref,
                    'status': 'correct'
                })
            else:
                # Check if file exists elsewhere (more comprehensive search)
                found_elsewhere = False
                file_name = expected_path.split('/')[-1]
                
                for current_path in current_files:
                    if current_path.endswith(file_name):
                        # Skip if this is the exact expected path (already handled above)
                        if current_path == expected_path:
                            continue
                            
                        # Only check for specific known moves, not generic __init__.py files
                        if file_name == '__init__.py':
                            # For __init__.py files, only check if they're in the exact expected location
                            if current_path == expected_path:
                                found_elsewhere = True
                                break
                            # Skip generic __init__.py matching - too many false positives
                            continue
                            
                        # Check if it's in a nested components directory that should be moved
                        if ('/components/' in current_path and 
                            expected_path.startswith('core/components/') and
                            not current_path.startswith('core/components/')):
                            self.structure_alignment['misplaced_files'].append({
                                'current_path': current_path,
                                'expected_path': expected_path,
                                'spec': spec_ref,
                                'status': 'misplaced'
                            })
                            found_elsewhere = True
                            break
                        # Check if it's in strategies directory but should be elsewhere
                        elif (current_path.startswith('core/strategies/') and 
                              not expected_path.startswith('core/strategies/') and
                              current_path != expected_path):
                            self.structure_alignment['misplaced_files'].append({
                                'current_path': current_path,
                                'expected_path': expected_path,
                                'spec': spec_ref,
                                'status': 'misplaced'
                            })
                            found_elsewhere = True
                            break
                        # Check if it's in wrong infrastructure subdirectory
                        elif (current_path.startswith('infrastructure/') and 
                              expected_path.startswith('infrastructure/') and
                              current_path != expected_path):
                            self.structure_alignment['misplaced_files'].append({
                                'current_path': current_path,
                                'expected_path': expected_path,
                                'spec': spec_ref,
                                'status': 'misplaced'
                            })
                            found_elsewhere = True
                            break
                            
                if not found_elsewhere:
                    self.structure_alignment['missing_files'].append({
                        'expected_path': expected_path,
                        'spec': spec_ref,
                        'status': 'missing'
                    })
                        
        # Check for obsolete files (files that exist but aren't in expected structure)
        # First, get all files that are already marked as misplaced
        misplaced_paths = {info['current_path'] for info in self.structure_alignment['misplaced_files']}
        
        for current_path in current_files:
            if current_path not in expected_file_paths and current_path not in misplaced_paths:
                # Check if it's a legitimate file (not __init__.py in unexpected places)
                if not (current_path.endswith('__init__.py') and 
                       any(current_path.startswith(exp_dir) for exp_dir in self.expected_structure.keys())):
                    # Check if it's a duplicate or obsolete file
                    file_name = current_path.split('/')[-1]
                    is_duplicate = False
                    is_obsolete = False
                    
                    # Only mark as duplicate/obsolete if we're certain
                    if file_name == 'strategy_manager.py' and 'base_strategy_manager.py' in expected_file_paths:
                        is_duplicate = True
                    elif file_name == 'data_provider.py' and 'data_provider_factory.py' in expected_file_paths:
                        is_duplicate = True
                    elif file_name == 'data_subscriptions.py':
                        is_obsolete = True  # Obsolete, replaced by config-driven approach
                    # Check for other potential issues
                    elif file_name.endswith('_test.py') or file_name.endswith('_tests.py'):
                        # Test files should be in tests/ directory, not in src/
                        is_obsolete = True
                    elif file_name == 'test_*.py' or file_name.startswith('test_'):
                        # Test files in wrong location
                        is_obsolete = True
                    # Don't mark other files as obsolete - they might be legitimate components
                    # that aren't in our expected structure but should be kept
                    # Based on WORKFLOW_GUIDE.md, most components are legitimate and should be preserved
                    
                    if is_duplicate:
                        self.structure_alignment['obsolete_files'].append({
                            'path': current_path,
                            'status': 'obsolete',
                            'reason': 'Duplicate file - superseded by newer implementation'
                        })
                    elif is_obsolete:
                        self.structure_alignment['obsolete_files'].append({
                            'path': current_path,
                            'status': 'obsolete',
                            'reason': 'Obsolete - replaced by config-driven approach'
                        })
                    # Don't add to obsolete_files if we're not sure - better to keep files than delete them
                    
    def generate_target_structure_doc(self) -> str:
        """Generate updated TARGET_REPOSITORY_STRUCTURE.md content."""
        print("Generating updated TARGET_REPOSITORY_STRUCTURE.md...")
        
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine overall status
        total_issues = (len(self.structure_alignment['misplaced_files']) + 
                       len(self.structure_alignment['missing_files']) + 
                       len(self.structure_alignment['obsolete_files']))
        
        status = "✅ PASS" if total_issues == 0 else "❌ NEEDS ATTENTION"
        
        content = f"""# Target Repository Structure

**Last Updated**: {current_date}
**Purpose**: Current vs. target repository structure with migration annotations
**Status**: Generated by Repository Structure Validation Agent

## Overview

This document maps the current backend repository structure against canonical specifications and provides annotations for required changes.

## Annotation Legend

- **[KEEP]**: File correctly located, follows canonical patterns
- **[DELETE]**: Obsolete file, should be removed (reason provided)
- **[UPDATE]**: File needs architecture compliance updates
- **[MOVE]**: File in wrong location, migration path provided
- **[CREATE]**: Missing file required by specs

## Validation Results

### Structure Alignment Summary

- **Correct Files**: {len(self.structure_alignment['correct_files'])}
- **Misplaced Files**: {len(self.structure_alignment['misplaced_files'])}
- **Missing Files**: {len(self.structure_alignment['missing_files'])}
- **Obsolete Files**: {len(self.structure_alignment['obsolete_files'])}

**Overall Status**: {status}

### Detailed Results

#### Correct Files ({len(self.structure_alignment['correct_files'])})
"""
        
        # Group correct files by directory for better organization
        correct_files_by_dir = {}
        for file_info in self.structure_alignment['correct_files']:
            dir_path = '/'.join(file_info['path'].split('/')[:-1]) if '/' in file_info['path'] else ''
            if dir_path not in correct_files_by_dir:
                correct_files_by_dir[dir_path] = []
            correct_files_by_dir[dir_path].append(file_info)
        
        for dir_path in sorted(correct_files_by_dir.keys()):
            if dir_path:
                content += f"\n**{dir_path}/**\n"
            for file_info in sorted(correct_files_by_dir[dir_path], key=lambda x: x['path']):
                content += f"- `{file_info['path']}` - {file_info['spec']}\n"
        
        if self.structure_alignment['misplaced_files']:
            content += f"""
#### Misplaced Files ({len(self.structure_alignment['misplaced_files'])})
"""
            for file_info in self.structure_alignment['misplaced_files']:
                content += f"- `{file_info['current_path']}` → `{file_info['expected_path']}` - {file_info['spec']}\n"
        
        if self.structure_alignment['missing_files']:
            content += f"""
#### Missing Files ({len(self.structure_alignment['missing_files'])})
"""
            for file_info in self.structure_alignment['missing_files']:
                content += f"- `{file_info['expected_path']}` - {file_info['spec']}\n"
        
        if self.structure_alignment['obsolete_files']:
            content += f"""
#### Obsolete Files ({len(self.structure_alignment['obsolete_files'])})
"""
            for file_info in self.structure_alignment['obsolete_files']:
                reason = file_info.get('reason', 'Should be reviewed for deletion')
                content += f"- `{file_info['path']}` - {reason}\n"
            
        content += f"""
## Summary

This structure validation was performed on {current_date} and shows the current state of the repository structure against canonical specifications.

**Status**: {status}

**Total Files Analyzed**: {len(self.structure_alignment['correct_files']) + len(self.structure_alignment['misplaced_files']) + len(self.structure_alignment['missing_files']) + len(self.structure_alignment['obsolete_files'])}

**Next Steps**: {'Repository structure is correctly aligned with canonical specifications. No changes needed.' if total_issues == 0 else 'Review the misplaced, missing, and obsolete files listed above and take appropriate action.'}
"""
        
        return content

    def run_validation(self) -> Dict[str, Any]:
        """Run the complete validation process."""
        try:
            print("Starting repository structure validation...")
            
            # Load canonical sources
            self.load_canonical_sources()
            
            # Scan current structure
            current_files = self.scan_current_structure()
            
            # Validate structure alignment
            self.validate_structure_alignment(current_files)
            
            # Generate updated target structure document
            target_structure_content = self.generate_target_structure_doc()
            target_structure_path = self.docs_root / "TARGET_REPOSITORY_STRUCTURE.md"
            
            with open(target_structure_path, 'w', encoding='utf-8') as f:
                f.write(target_structure_content)
            
            print(f"Updated TARGET_REPOSITORY_STRUCTURE.md written to: {target_structure_path}")
            
            # Determine overall status
            total_issues = (len(self.structure_alignment['misplaced_files']) + 
                           len(self.structure_alignment['missing_files']) + 
                           len(self.structure_alignment['obsolete_files']))
            
            overall_status = 'PASS' if total_issues == 0 else 'FAIL'
            
            print(f"Validation complete. Status: {overall_status}")
            print(f"Total issues found: {total_issues}")
            print(f"Correct files: {len(self.structure_alignment['correct_files'])}")
            print(f"Misplaced files: {len(self.structure_alignment['misplaced_files'])}")
            print(f"Missing files: {len(self.structure_alignment['missing_files'])}")
            print(f"Obsolete files: {len(self.structure_alignment['obsolete_files'])}")
            
            return {
                'overall_status': overall_status,
                'structure_alignment': self.structure_alignment,
                'target_structure_updated': True,
                'report_path': str(target_structure_path),
                'total_issues': total_issues,
                'summary': {
                    'correct_files': len(self.structure_alignment['correct_files']),
                    'misplaced_files': len(self.structure_alignment['misplaced_files']),
                    'missing_files': len(self.structure_alignment['missing_files']),
                    'obsolete_files': len(self.structure_alignment['obsolete_files'])
                }
            }
            
        except Exception as e:
            print(f"Error during validation: {e}")
            return {
                'overall_status': 'ERROR',
                'error': str(e),
                'structure_alignment': self.structure_alignment,
                'target_structure_updated': False,
                'report_path': None
            }

def main():
    """Main entry point for repository structure validation."""
    print("Repository Structure Validation Quality Gates")
    print("=" * 50)
    
    validator = RepositoryStructureValidator()
    result = validator.run_validation()
    
    # Write results to JSON file for quality gate integration
    results_file = project_root / "results" / "repo_structure_validation_results.json"
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
        
    print(f"Results written to: {results_file}")
    
    # Exit with appropriate code
    if result['overall_status'] == 'PASS':
        print("✅ Repository structure validation PASSED")
        print("QUALITY GATE PASSED: Repository structure validation completed successfully")
        sys.exit(0)
    elif result['overall_status'] == 'FAIL':
        print("❌ Repository structure validation FAILED")
        sys.exit(1)
    else:
        print("⚠️ Repository structure validation ERROR")
        sys.exit(2)

if __name__ == "__main__":
    main()
