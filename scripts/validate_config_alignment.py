#!/usr/bin/env python3
"""
Config Alignment Validation Script

Validates that all config models in config_models.py align fully with the union of all configs in configs/.
This ensures that:
1. All fields in config files have corresponding Pydantic model fields
2. All required fields in Pydantic models are present in config files
3. No orphaned fields exist in either direction
4. Mode-specific validation works correctly
"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, Set, List, Optional, Union
from pydantic import ValidationError

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from basis_strategy_v1.infrastructure.config.models import (
    ModeConfig, VenueConfig, ShareClassConfig, ConfigurationSet
)
from config_field_classifier import ConfigFieldClassifier


class ConfigAlignmentValidator:
    """Validates alignment between config files and Pydantic models."""
    
    def __init__(self):
        self.configs_dir = Path(__file__).parent.parent / "configs"
        self.errors = []
        self.warnings = []
        self.alignment_report = {}
        self.field_classifier = ConfigFieldClassifier()
    
    def load_all_config_files(self) -> Dict[str, Any]:
        """Load all configuration files from configs/ directory."""
        configs = {}
        
        # Load default.json
        default_path = self.configs_dir / "default.json"
        if default_path.exists():
            with open(default_path, 'r') as f:
                configs['default'] = json.load(f)
        
        # Load all mode configs
        modes_dir = self.configs_dir / "modes"
        if modes_dir.exists():
            for mode_file in modes_dir.glob("*.yaml"):
                mode_name = mode_file.stem
                with open(mode_file, 'r') as f:
                    configs[f'mode_{mode_name}'] = yaml.safe_load(f)
        
        # Load venue configs
        venues_dir = self.configs_dir / "venues"
        if venues_dir.exists():
            for venue_file in venues_dir.glob("*.yaml"):
                venue_name = venue_file.stem
                with open(venue_file, 'r') as f:
                    configs[f'venue_{venue_name}'] = yaml.safe_load(f)
        
        return configs
    
    def get_pydantic_model_fields(self, model_class) -> Set[str]:
        """Extract all field names from a Pydantic model using the field classifier."""
        fields = set()
        
        # Get model name for field classifier
        model_name = model_class.__name__
        
        # Get fields by level from the classifier
        fields_by_level = self.field_classifier.get_required_fields_by_level(model_name)
        
        # Add all required fields (top-level, nested, fixed schema dicts), optional fields, and data values
        for level in ['required_toplevel', 'required_nested', 'fixed_schema_dict', 'optional_field', 'data_value']:
            fields.update(fields_by_level[level])
        
        # Add nested fields from fixed schema dicts
        for dict_name in self.field_classifier.FIXED_SCHEMA_DICTS.keys():
            if dict_name in fields:
                # Add all nested fields for this fixed schema dict with proper prefix
                nested_fields = self.field_classifier.get_fixed_schema_fields(dict_name)
                for nested_field in nested_fields:
                    # Prepend the dict name to create full field path
                    full_field_path = f"{dict_name}.{nested_field}"
                    fields.add(full_field_path)
        
        # Add wildcards for dynamic dicts (for matching purposes)
        for field_path in fields_by_level['dynamic_dict']:
            fields.add(field_path)
            fields.add(f"{field_path}.*")  # Add wildcard for matching
        
        return fields
    
    def _is_dict_field(self, annotation) -> bool:
        """Check if annotation represents a Dict[str, Any] field (including Optional)."""
        # Direct Dict[str, Any]
        if annotation == Dict[str, Any]:
            return True
        
        # Dict with __origin__ == dict
        if hasattr(annotation, '__origin__') and annotation.__origin__ == dict:
            return True
        
        # Optional[Dict[str, Any]] - Union with dict and None
        if (hasattr(annotation, '__origin__') and annotation.__origin__ == Union and 
            len(annotation.__args__) == 2 and type(None) in annotation.__args__):
            for arg in annotation.__args__:
                if hasattr(arg, '__origin__') and arg.__origin__ == dict:
                    return True
        
        return False
    
    def _field_matches_model(self, config_field: str, model_fields: Set[str]) -> bool:
        """Check if a config field matches any model field using the field classifier."""
        # Direct match
        if config_field in model_fields:
            return True
        
        # Check if it's a dynamic dict key (e.g., hedge_allocation.binance)
        parent_dynamic_dict = self.field_classifier.get_parent_dynamic_dict(config_field)
        if parent_dynamic_dict:
            # If parent dynamic dict is in model fields, allow the key
            if parent_dynamic_dict in model_fields or f"{parent_dynamic_dict}.*" in model_fields:
                return True
        
        # Check if it's a nested field from a fixed schema dict
        # e.g., component_config.strategy_manager.position_calculation should match strategy_manager.position_calculation
        for model_field in model_fields:
            if '.' in model_field and '.' in config_field:
                # Check if config_field ends with model_field (after removing the prefix)
                if config_field.endswith(model_field):
                    # Extract the prefix part
                    prefix = config_field[:-len(model_field)-1]  # Remove the model_field and the dot
                    # Check if the prefix is a fixed schema dict
                    if prefix in self.field_classifier.FIXED_SCHEMA_DICTS:
                        return True
        
        # Wildcard match - check if any wildcard prefix matches
        for model_field in model_fields:
            if model_field.endswith('.*'):
                prefix = model_field[:-2]  # Remove .*
                if config_field.startswith(prefix + '.'):
                    return True
                # Also match the prefix itself
                if config_field == prefix:
                    return True
        
        # Parent field match - if parent is Dict[str, Any], allow nested paths
        parts = config_field.split('.')
        for i in range(1, len(parts)):
            parent_path = '.'.join(parts[:i])
            # Check if parent with wildcard exists
            if f"{parent_path}.*" in model_fields:
                return True
        
        return False
    
    def get_nested_fields(self, data: Dict[str, Any], prefix: str = "") -> Set[str]:
        """Extract all field paths from nested dictionary without creating duplicates."""
        fields = set()
        
        for key, value in data.items():
            field_path = f"{prefix}.{key}" if prefix else key
            fields.add(field_path)
            
            if isinstance(value, dict):
                # Recurse into nested dicts
                fields.update(self.get_nested_fields(value, field_path))
            elif isinstance(value, list) and value:
                # For lists, check if first item is dict
                if isinstance(value[0], dict):
                    # Extract fields from first dict item as pattern
                    # Don't include [0], [1] indices - those don't exist in Pydantic
                    list_fields = self.get_nested_fields(value[0], field_path)
                    fields.update(list_fields)
        
        return fields
    
    def validate_systematic_alignment(self) -> Dict[str, Any]:
        """Validate alignment systematically: each model against its specific config directory."""
        print("🔍 Validating systematic config alignment...")
        
        alignment_results = {}
        total_orphaned_config = 0
        total_orphaned_model = 0
        
        # 1. ModeConfig ↔ configs/modes/*.yaml
        print("  📁 Validating ModeConfig ↔ configs/modes/*.yaml")
        mode_configs = {}
        modes_dir = self.configs_dir / "modes"
        if modes_dir.exists():
            for mode_file in modes_dir.glob("*.yaml"):
                with open(mode_file, 'r') as f:
                    mode_configs[mode_file.stem] = yaml.safe_load(f)
        
        model_fields = self.get_pydantic_model_fields(ModeConfig)
        all_mode_config_fields = set()
        for config_data in mode_configs.values():
            all_mode_config_fields.update(self.get_nested_fields(config_data))
        
        # Handle field matching using the classifier
        mode_orphaned_config = set()
        for config_field in all_mode_config_fields:
            if not self._field_matches_model(config_field, model_fields):
                # Only flag as orphaned if it's not a dynamic dict key
                parent_dynamic_dict = self.field_classifier.get_parent_dynamic_dict(config_field)
                if not parent_dynamic_dict:
                    mode_orphaned_config.add(config_field)
        
        # Check required fields for orphaned model fields
        mode_orphaned_model = set()
        required_fields = set()
        fields_by_level = self.field_classifier.get_required_fields_by_level('ModeConfig')
        for level in ['required_toplevel', 'required_nested', 'fixed_schema_dict']:
            required_fields.update(fields_by_level[level])
        
        for model_field in required_fields:
            if model_field not in all_mode_config_fields:
                mode_orphaned_model.add(model_field)
        
        alignment_results['modes'] = {
            'config_fields': len(all_mode_config_fields),
            'model_fields': len(model_fields),
            'orphaned_config': list(mode_orphaned_config),
            'orphaned_model': list(mode_orphaned_model),
            'coverage': (len(all_mode_config_fields - mode_orphaned_config) / len(all_mode_config_fields)) * 100 if all_mode_config_fields else 100
        }
        total_orphaned_config += len(mode_orphaned_config)
        total_orphaned_model += len(mode_orphaned_model)
        mode_status = "✅ PASS" if len(mode_orphaned_config) == 0 and len(mode_orphaned_model) == 0 else "❌ FAIL"
        print(f"    Modes: {len(all_mode_config_fields)} config fields, {len(model_fields)} model fields - {mode_status}")
        if mode_orphaned_config:
            print(f"    ⚠️  {len(mode_orphaned_config)} orphaned config fields: {list(mode_orphaned_config)[:5]}...")
        if mode_orphaned_model:
            print(f"    ⚠️  {len(mode_orphaned_model)} orphaned model fields: {list(mode_orphaned_model)[:5]}...")
        
        # 2. VenueConfig ↔ configs/venues/*.yaml
        print("  📁 Validating VenueConfig ↔ configs/venues/*.yaml")
        venue_configs = {}
        venues_dir = self.configs_dir / "venues"
        if venues_dir.exists():
            for venue_file in venues_dir.glob("*.yaml"):
                with open(venue_file, 'r') as f:
                    venue_configs[venue_file.stem] = yaml.safe_load(f)
        
        venue_model_fields = self.get_pydantic_model_fields(VenueConfig)
        all_venue_config_fields = set()
        for config_data in venue_configs.values():
            all_venue_config_fields.update(self.get_nested_fields(config_data))
        
        # Handle field matching using the classifier
        venue_orphaned_config = set()
        for config_field in all_venue_config_fields:
            if not self._field_matches_model(config_field, venue_model_fields):
                # Only flag as orphaned if it's not a dynamic dict key
                parent_dynamic_dict = self.field_classifier.get_parent_dynamic_dict(config_field)
                if not parent_dynamic_dict:
                    venue_orphaned_config.add(config_field)
        
        # Only check required fields for orphaned model fields
        venue_orphaned_model = set()
        required_fields = set()
        fields_by_level = self.field_classifier.get_required_fields_by_level('VenueConfig')
        for level in ['required_toplevel', 'required_nested', 'fixed_schema_dict']:
            required_fields.update(fields_by_level[level])
        
        for model_field in required_fields:
            if model_field not in all_venue_config_fields:
                venue_orphaned_model.add(model_field)
        
        alignment_results['venue'] = {
            'config_fields': len(all_venue_config_fields),
            'model_fields': len(venue_model_fields),
            'orphaned_config': list(venue_orphaned_config),
            'orphaned_model': list(venue_orphaned_model),
            'coverage': (len(all_venue_config_fields - venue_orphaned_config) / len(all_venue_config_fields)) * 100 if all_venue_config_fields else 100
        }
        total_orphaned_config += len(venue_orphaned_config)
        total_orphaned_model += len(venue_orphaned_model)
        venue_status = "✅ PASS" if len(venue_orphaned_config) == 0 and len(venue_orphaned_model) == 0 else "❌ FAIL"
        print(f"    Venue: {len(all_venue_config_fields)} config fields, {len(venue_model_fields)} model fields - {venue_status}")
        if venue_orphaned_config:
            print(f"    ⚠️  {len(venue_orphaned_config)} orphaned config fields: {list(venue_orphaned_config)[:5]}...")
        if venue_orphaned_model:
            print(f"    ⚠️  {len(venue_orphaned_model)} orphaned model fields: {list(venue_orphaned_model)[:5]}...")
        
        # 3. ShareClassConfig ↔ configs/share_classes/*.yaml
        print("  📁 Validating ShareClassConfig ↔ configs/share_classes/*.yaml")
        share_class_configs = {}
        share_classes_dir = self.configs_dir / "share_classes"
        if share_classes_dir.exists():
            for share_class_file in share_classes_dir.glob("*.yaml"):
                with open(share_class_file, 'r') as f:
                    share_class_configs[share_class_file.stem] = yaml.safe_load(f)
        
        share_class_model_fields = self.get_pydantic_model_fields(ShareClassConfig)
        all_share_class_config_fields = set()
        for config_data in share_class_configs.values():
            all_share_class_config_fields.update(self.get_nested_fields(config_data))
        
        # Handle field matching using the classifier
        share_class_orphaned_config = set()
        for config_field in all_share_class_config_fields:
            if not self._field_matches_model(config_field, share_class_model_fields):
                # Only flag as orphaned if it's not a dynamic dict key
                parent_dynamic_dict = self.field_classifier.get_parent_dynamic_dict(config_field)
                if not parent_dynamic_dict:
                    share_class_orphaned_config.add(config_field)
        
        # Only check required fields for orphaned model fields
        share_class_orphaned_model = set()
        required_fields = set()
        fields_by_level = self.field_classifier.get_required_fields_by_level('ShareClassConfig')
        for level in ['required_toplevel', 'required_nested', 'fixed_schema_dict']:
            required_fields.update(fields_by_level[level])
        
        for model_field in required_fields:
            if model_field not in all_share_class_config_fields:
                share_class_orphaned_model.add(model_field)
        
        alignment_results['share_class'] = {
            'config_fields': len(all_share_class_config_fields),
            'model_fields': len(share_class_model_fields),
            'orphaned_config': list(share_class_orphaned_config),
            'orphaned_model': list(share_class_orphaned_model),
            'coverage': (len(all_share_class_config_fields - share_class_orphaned_config) / len(all_share_class_config_fields)) * 100 if all_share_class_config_fields else 100
        }
        total_orphaned_config += len(share_class_orphaned_config)
        total_orphaned_model += len(share_class_orphaned_model)
        share_class_status = "✅ PASS" if len(share_class_orphaned_config) == 0 and len(share_class_orphaned_model) == 0 else "❌ FAIL"
        print(f"    ShareClass: {len(all_share_class_config_fields)} config fields, {len(share_class_model_fields)} model fields - {share_class_status}")
        if share_class_orphaned_config:
            print(f"    ⚠️  {len(share_class_orphaned_config)} orphaned config fields: {list(share_class_orphaned_config)[:5]}...")
        if share_class_orphaned_model:
            print(f"    ⚠️  {len(share_class_orphaned_model)} orphaned model fields: {list(share_class_orphaned_model)[:5]}...")
        
        # 4. InfrastructureConfig ↔ REMOVED (configs/*.json eliminated)
        print("  📁 InfrastructureConfig ↔ REMOVED (configs/*.json eliminated)")
        print("    ✅ JSON configs eliminated - infrastructure handled by environment variables and hardcoded defaults")
        print("    📝 Design decision: Database/Storage → env vars, Cross-network/Rates → hardcoded")
        
        # No infrastructure alignment to check since JSON configs are eliminated
        alignment_results['infrastructure'] = {
            'config_fields': 0,
            'model_fields': 0,
            'orphaned_config': [],
            'orphaned_model': [],
            'coverage': 100.0,
            'eliminated': True
        }
        
        # Summary
        total_config_fields = sum(r['config_fields'] for r in alignment_results.values())
        total_model_fields = sum(r['model_fields'] for r in alignment_results.values())
        overall_coverage = ((total_config_fields - total_orphaned_config) / total_config_fields) * 100 if total_config_fields else 100
        
        coverage_report = {
            'systematic_results': alignment_results,
            'total_config_fields': total_config_fields,
            'total_model_fields': total_model_fields,
            'total_orphaned_config': total_orphaned_config,
            'total_orphaned_model': total_orphaned_model,
            'overall_coverage': overall_coverage
        }
        
        return coverage_report
    
    def validate_mode_specific_configs(self, configs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate mode-specific configuration requirements."""
        print("🔍 Validating mode-specific configurations...")
        
        mode_validation_report = {}
        
        for config_name, config_data in configs.items():
            if not config_name.startswith('mode_'):
                continue
                
            mode_name = config_name.replace('mode_', '')
            print(f"  Validating mode: {mode_name}")
            
            # Define mode requirements
            MODE_REQUIREMENTS = {
                'btc_basis': {
                    'required_fields': ['mode', 'share_class', 'asset', 'basis_trade_enabled', 'venues', 'hedge_venues'],
                    'optional_fields': ['lending_enabled', 'staking_enabled', 'borrowing_enabled']
                },
                'eth_basis': {
                    'required_fields': ['mode', 'share_class', 'asset', 'basis_trade_enabled', 'venues', 'hedge_venues'],
                    'optional_fields': ['lending_enabled', 'staking_enabled', 'borrowing_enabled']
                },
                'eth_leveraged': {
                    'required_fields': ['mode', 'share_class', 'asset', 'staking_enabled', 'borrowing_enabled', 'lst_type', 'venues'],
                    'optional_fields': ['lending_enabled', 'basis_trade_enabled']
                },
                'eth_staking_only': {
                    'required_fields': ['mode', 'share_class', 'asset', 'staking_enabled', 'lst_type', 'venues'],
                    'optional_fields': ['lending_enabled', 'basis_trade_enabled', 'borrowing_enabled']
                },
                'pure_lending': {
                    'required_fields': ['mode', 'share_class', 'asset', 'lending_enabled', 'venues'],
                    'optional_fields': ['staking_enabled', 'basis_trade_enabled', 'borrowing_enabled']
                },
                'usdt_market_neutral': {
                    'required_fields': ['mode', 'share_class', 'asset', 'staking_enabled', 'borrowing_enabled', 'lst_type', 'venues', 'hedge_venues'],
                    'optional_fields': ['lending_enabled', 'basis_trade_enabled']
                },
                'usdt_market_neutral_no_leverage': {
                    'required_fields': ['mode', 'share_class', 'asset', 'staking_enabled', 'venues', 'hedge_venues'],
                    'optional_fields': ['lending_enabled', 'basis_trade_enabled', 'borrowing_enabled']
                },
                'ml_btc_directional': {
                    'required_fields': ['mode', 'share_class', 'asset', 'venues'],
                    'optional_fields': ['lending_enabled', 'staking_enabled', 'basis_trade_enabled', 'borrowing_enabled']
                },
                'ml_usdt_directional': {
                    'required_fields': ['mode', 'share_class', 'asset', 'venues'],
                    'optional_fields': ['lending_enabled', 'staking_enabled', 'basis_trade_enabled', 'borrowing_enabled']
                }
            }
            
            # Check if mode has requirements defined
            if mode_name not in MODE_REQUIREMENTS:
                self.warnings.append(f"Mode '{mode_name}' not found in MODE_REQUIREMENTS")
                continue
            
            required_fields = MODE_REQUIREMENTS[mode_name].get('required_fields', [])
            optional_fields = MODE_REQUIREMENTS[mode_name].get('optional_fields', [])
            
            # Check required fields
            missing_required = []
            for field in required_fields:
                if not self._field_exists_in_config(config_data, field):
                    missing_required.append(field)
            
            # Check optional fields (should warn if present but not in optional list)
            extra_fields = []
            config_fields = self.get_nested_fields(config_data)
            for field in config_fields:
                if field not in required_fields and field not in optional_fields:
                    extra_fields.append(field)
            
            mode_validation_report[mode_name] = {
                'required_fields': required_fields,
                'optional_fields': optional_fields,
                'missing_required': missing_required,
                'extra_fields': extra_fields,
                'valid': len(missing_required) == 0
            }
            
            if missing_required:
                self.errors.append(f"Mode '{mode_name}' missing required fields: {missing_required}")
            
            if extra_fields:
                self.warnings.append(f"Mode '{mode_name}' has extra fields: {extra_fields[:5]}...")
        
        return mode_validation_report
    
    def _field_exists_in_config(self, config_data: Dict[str, Any], field_path: str) -> bool:
        """Check if a field path exists in config data."""
        try:
            current = config_data
            for part in field_path.split('.'):
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return False
            return True
        except (KeyError, TypeError):
            return False
    
    def validate_pydantic_validation(self, configs: Dict[str, Any]) -> Dict[str, Any]:
        """Test Pydantic validation on all config combinations."""
        print("🔍 Testing Pydantic validation...")
        
        validation_report = {}
        
        # Test mode configs using ModeConfig model
        for config_name, config_data in configs.items():
            if not config_name.startswith('mode_'):
                continue
                
            mode_name = config_name.replace('mode_', '')
            
            try:
                # Use ModeConfig for validation
                from basis_strategy_v1.infrastructure.config.models import ModeConfig
                config = ModeConfig(**config_data)
                validation_report[mode_name] = {'valid': True, 'error': None}
                print(f"  ✅ Mode '{mode_name}' validation: PASS")
            except ValidationError as e:
                validation_report[mode_name] = {'valid': False, 'error': str(e)}
                self.errors.append(f"Mode '{mode_name}' validation failed: {e}")
                print(f"  ❌ Mode '{mode_name}' validation: FAIL - {e}")
        
        return validation_report
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive alignment report."""
        print("\n" + "="*80)
        print("🔍 CONFIG ALIGNMENT VALIDATION REPORT")
        print("="*80)
        
        # Load all configs
        configs = self.load_all_config_files()
        print(f"Loaded {len(configs)} configuration files")
        
        # Run systematic validations
        coverage_report = self.validate_systematic_alignment()
        mode_validation_report = self.validate_mode_specific_configs(configs)
        pydantic_validation_report = self.validate_pydantic_validation(configs)
        
        # Generate summary
        total_errors = len(self.errors)
        total_warnings = len(self.warnings)
        
        print(f"\n📊 ALIGNMENT SUMMARY:")
        print(f"  Coverage: {coverage_report['overall_coverage']:.1f}%")
        print(f"  Errors: {total_errors}")
        print(f"  Warnings: {total_warnings}")
        
        if self.errors:
            print(f"\n❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # Overall status - be strict about orphaned fields
        orphaned_config_count = coverage_report.get('total_orphaned_config', 0)
        orphaned_model_count = coverage_report.get('total_orphaned_model', 0)
        overall_coverage = coverage_report.get('overall_coverage', 0)
        
        print(f"\n📊 SYSTEMATIC ALIGNMENT SUMMARY:")
        print(f"  Overall Coverage: {overall_coverage:.1f}%")
        print(f"  Total Orphaned Config Fields: {orphaned_config_count}")
        print(f"  Total Orphaned Model Fields: {orphaned_model_count}")
        
        total_alignment_issues = total_errors + orphaned_config_count + orphaned_model_count
        
        if total_alignment_issues == 0:
            print(f"\n🎉 SUCCESS: All config models align with config files!")
            return True
        else:
            print(f"\n❌ FAILURE: {total_alignment_issues} alignment issues found")
            if total_errors > 0:
                print(f"   - {total_errors} validation errors")
            if orphaned_config_count > 0:
                print(f"   - {orphaned_config_count} orphaned config fields")
            if orphaned_model_count > 0:
                print(f"   - {orphaned_model_count} orphaned model fields")
            return False
    
    def run_validation(self) -> bool:
        """Run complete config alignment validation."""
        return self.generate_report()


def main():
    """Main function."""
    validator = ConfigAlignmentValidator()
    success = validator.run_validation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
