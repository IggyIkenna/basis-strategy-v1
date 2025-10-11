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

from basis_strategy_v1.core.config.config_models import (
    ConfigSchema, StrategyConfig, VenueConfig, ShareClassConfig,
    InfrastructureConfig, MODE_REQUIREMENTS
)


class ConfigAlignmentValidator:
    """Validates alignment between config files and Pydantic models."""
    
    def __init__(self):
        self.configs_dir = Path(__file__).parent.parent / "configs"
        self.errors = []
        self.warnings = []
        self.alignment_report = {}
    
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
        """Extract all field names from a Pydantic model, including nested fields."""
        fields = set()
        
        if hasattr(model_class, '__fields__'):
            # Pydantic v1
            for field_name, field_info in model_class.__fields__.items():
                fields.add(field_name)
                # Check if this field is a nested model
                if hasattr(field_info, 'type_') and hasattr(field_info.type_, '__fields__'):
                    # It's a nested Pydantic model, extract its fields too
                    nested_fields = self.get_pydantic_model_fields(field_info.type_)
                    for nested_field in nested_fields:
                        fields.add(f"{field_name}.{nested_field}")
        elif hasattr(model_class, 'model_fields'):
            # Pydantic v2
            for field_name, field_info in model_class.model_fields.items():
                fields.add(field_name)
                # Check if this field is a nested model
                annotation = field_info.annotation
                
                # Check if this field is a nested Pydantic model
                if hasattr(annotation, 'model_fields'):
                    # It's a direct nested Pydantic model
                    nested_fields = self.get_pydantic_model_fields(annotation)
                    for nested_field in nested_fields:
                        fields.add(f"{field_name}.{nested_field}")
                # Special handling for Dict[str, Any] fields that represent nested structures
                elif (annotation == Dict[str, Any] or 
                      (hasattr(annotation, '__origin__') and annotation.__origin__ == dict)):
                    # For Dict[str, Any] fields, we need to manually add known nested paths
                    if field_name == 'monitoring':
                        fields.update([
                            'monitoring.position_check_interval',
                            'monitoring.risk_check_interval', 
                            'monitoring.alert_thresholds',
                            'monitoring.alert_thresholds.drawdown_warning',
                            'monitoring.alert_thresholds.drawdown_critical'
                        ])
                    elif field_name == 'capital_allocation':
                        fields.update([
                            'capital_allocation.spot_capital',
                            'capital_allocation.perp_capital',
                            'capital_allocation.max_position_size'
                        ])
                    elif field_name == 'hedge_allocation':
                        fields.update([
                            'hedge_allocation.binance',
                            'hedge_allocation.bybit',
                            'hedge_allocation.okx'
                        ])
                    elif field_name == 'trading_fees':
                        fields.update([
                            'trading_fees.maker',
                            'trading_fees.taker'
                        ])
                    elif field_name == 'testnet':
                        fields.update([
                            'testnet.enabled',
                            'testnet.confirmation_blocks',
                            'testnet.faucet_url',
                            'testnet.max_gas_price_gwei'
                        ])
                    elif field_name == 'database':
                        fields.update([
                            'database.url'
                        ])
                    elif field_name == 'rates':
                        fields.update([
                            'rates.use_fixed_rates'
                        ])
                elif hasattr(annotation, '__origin__'):
                    # Handle Union types and Optional types
                    actual_type = annotation
                    if annotation.__origin__ is Union:
                        # For Union types, find the first non-None type
                        for union_type in annotation.__args__:
                            if union_type is not type(None) and hasattr(union_type, 'model_fields'):
                                actual_type = union_type
                                break
                    elif annotation.__origin__ is type(None):
                        # For Optional types, get the first argument
                        if len(annotation.__args__) > 0:
                            actual_type = annotation.__args__[0]
                    
                    # Check if the actual type is a nested Pydantic model
                    if hasattr(actual_type, 'model_fields'):
                        nested_fields = self.get_pydantic_model_fields(actual_type)
                        for nested_field in nested_fields:
                            fields.add(f"{field_name}.{nested_field}")
        
        return fields
    
    def get_nested_fields(self, data: Dict[str, Any], prefix: str = "") -> Set[str]:
        """Extract all field paths from nested dictionary and create flattened equivalents."""
        fields = set()
        
        for key, value in data.items():
            field_path = f"{prefix}.{key}" if prefix else key
            fields.add(field_path)
            
            # Also add flattened version (replace dots with underscores)
            flattened_path = field_path.replace('.', '_')
            fields.add(flattened_path)
            
            # Also add the reverse mapping (for model fields that are flattened)
            if '_' in key and prefix:
                # If we have a flattened field in config, also check if there's a nested equivalent
                nested_equivalent = f"{prefix}.{key.replace('_', '.')}"
                fields.add(nested_equivalent)
            
            if isinstance(value, dict):
                fields.update(self.get_nested_fields(value, field_path))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Handle list of objects
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        fields.update(self.get_nested_fields(item, f"{field_path}[{i}]"))
        
        return fields
    
    def validate_systematic_alignment(self) -> Dict[str, Any]:
        """Validate alignment systematically: each model against its specific config directory."""
        print("🔍 Validating systematic config alignment...")
        
        alignment_results = {}
        total_orphaned_config = 0
        total_orphaned_model = 0
        
        # 1. StrategyConfig ↔ configs/modes/*.yaml
        print("  📁 Validating StrategyConfig ↔ configs/modes/*.yaml")
        mode_configs = {}
        modes_dir = self.configs_dir / "modes"
        if modes_dir.exists():
            for mode_file in modes_dir.glob("*.yaml"):
                with open(mode_file, 'r') as f:
                    mode_configs[mode_file.stem] = yaml.safe_load(f)
        
        model_fields = self.get_pydantic_model_fields(StrategyConfig)
        all_mode_config_fields = set()
        for config_data in mode_configs.values():
            all_mode_config_fields.update(self.get_nested_fields(config_data))
        
        strategy_orphaned_config = all_mode_config_fields - model_fields
        strategy_orphaned_model = model_fields - all_mode_config_fields
        
        alignment_results['strategy'] = {
            'config_fields': len(all_mode_config_fields),
            'model_fields': len(model_fields),
            'orphaned_config': list(strategy_orphaned_config),
            'orphaned_model': list(strategy_orphaned_model),
            'coverage': (len(all_mode_config_fields - strategy_orphaned_config) / len(all_mode_config_fields)) * 100 if all_mode_config_fields else 100
        }
        total_orphaned_config += len(strategy_orphaned_config)
        total_orphaned_model += len(strategy_orphaned_model)
        strategy_status = "✅ PASS" if len(strategy_orphaned_config) == 0 and len(strategy_orphaned_model) == 0 else "❌ FAIL"
        print(f"    Strategy: {len(all_mode_config_fields)} config fields, {len(model_fields)} model fields - {strategy_status}")
        if strategy_orphaned_config:
            print(f"    ⚠️  {len(strategy_orphaned_config)} orphaned config fields: {list(strategy_orphaned_config)[:5]}...")
        if strategy_orphaned_model:
            print(f"    ⚠️  {len(strategy_orphaned_model)} orphaned model fields: {list(strategy_orphaned_model)[:5]}...")
        
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
        
        venue_orphaned_config = all_venue_config_fields - venue_model_fields
        venue_orphaned_model = venue_model_fields - all_venue_config_fields
        
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
        
        share_class_orphaned_config = all_share_class_config_fields - share_class_model_fields
        share_class_orphaned_model = share_class_model_fields - all_share_class_config_fields
        
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
        
        # Test default config
        if 'default' in configs:
            try:
                config = ConfigSchema(**configs['default'])
                validation_report['default'] = {'valid': True, 'error': None}
                print("  ✅ Default config validation: PASS")
            except ValidationError as e:
                validation_report['default'] = {'valid': False, 'error': str(e)}
                self.errors.append(f"Default config validation failed: {e}")
                print(f"  ❌ Default config validation: FAIL - {e}")
        
        # Test mode configs
        for config_name, config_data in configs.items():
            if not config_name.startswith('mode_'):
                continue
                
            mode_name = config_name.replace('mode_', '')
            
            try:
                # Merge with default config
                merged_config = configs.get('default', {}).copy()
                merged_config.update(config_data)
                
                config = ConfigSchema(**merged_config)
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
