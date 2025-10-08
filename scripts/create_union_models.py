#!/usr/bin/env python3
"""
Create practical union Pydantic models for config alignment.

This script creates comprehensive models that cover all fields found in configs.
"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, Set, List
from collections import defaultdict

def load_all_configs():
    """Load all configuration files and return unified structure."""
    config_dir = Path(__file__).parent.parent / "configs"
    all_configs = {}
    
    # Load JSON configs
    for json_file in config_dir.glob("*.json"):
        with open(json_file, 'r') as f:
            all_configs[f"json_{json_file.stem}"] = json.load(f)
    
    # Load YAML configs
    for subdir in ["modes", "venues", "share_classes"]:
        subdir_path = config_dir / subdir
        if subdir_path.exists():
            for yaml_file in subdir_path.glob("*.yaml"):
                with open(yaml_file, 'r') as f:
                    all_configs[f"{subdir}_{yaml_file.stem}"] = yaml.safe_load(f)
    
    return all_configs

def extract_all_fields(configs: Dict[str, Dict[str, Any]]) -> Set[str]:
    """Extract all unique field paths from all configs."""
    all_fields = set()
    
    def extract_from_dict(data, prefix=""):
        if not isinstance(data, dict):
            return
        for key, value in data.items():
            field_path = f"{prefix}.{key}" if prefix else key
            all_fields.add(field_path)
            if isinstance(value, dict):
                extract_from_dict(value, field_path)
    
    for config_name, config_data in configs.items():
        extract_from_dict(config_data)
    
    return all_fields

def infer_field_type(configs: Dict[str, Dict[str, Any]], field_path: str) -> str:
    """Infer the Python type for a field based on observed values."""
    values = []
    
    def get_nested_value(data, path):
        keys = path.split('.')
        current = data
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return None
    
    for config_data in configs.values():
        value = get_nested_value(config_data, field_path)
        if value is not None:
            values.append(value)
    
    if not values:
        return "Any"
    
    # Analyze types
    types = set(type(v).__name__ for v in values)
    
    if len(types) == 1:
        type_name = list(types)[0]
        if type_name == 'dict':
            return "Dict[str, Any]"
        elif type_name == 'list':
            return "List[Any]"
        elif type_name == 'bool':
            return "bool"
        elif type_name == 'int':
            return "int"
        elif type_name == 'float':
            return "float"
        elif type_name == 'str':
            return "str"
        elif type_name == 'NoneType':
            return "Optional[Any]"
    
    # Mixed types or complex cases
    if 'dict' in types:
        return "Dict[str, Any]"
    elif 'list' in types:
        return "List[Any]"
    elif 'bool' in types and len(types) <= 2:
        return "bool"
    elif {'int', 'float'}.intersection(types):
        return "Union[int, float]"
    else:
        return "Any"

def generate_comprehensive_models(configs: Dict[str, Dict[str, Any]]) -> str:
    """Generate comprehensive Pydantic models."""
    all_fields = extract_all_fields(configs)
    
    # Group fields by category
    infrastructure_fields = []
    strategy_fields = []
    venue_fields = []
    share_class_fields = []
    mode_fields = []
    
    for field in sorted(all_fields):
        if any(field.startswith(prefix) for prefix in ['api', 'cache', 'database', 'redis', 'storage', 'cross_network', 'testnet']):
            infrastructure_fields.append(field)
        elif field in ['mode', 'asset', 'share_class', 'lending_enabled', 'staking_enabled', 'basis_trade_enabled', 
                      'borrowing_enabled', 'enable_market_impact', 'use_flash_loan', 'unwind_mode', 'hedge_venues', 
                      'hedge_allocation', 'capital_allocation', 'data_requirements', 'monitoring', 'rewards_mode',
                      'lst_type', 'max_leverage_loops', 'min_loop_position_usd', 'margin_ratio_target', 
                      'max_stake_spread_move', 'max_ltv', 'liquidation_threshold', 'target_apy', 'max_drawdown']:
            strategy_fields.append(field)
        elif field in ['venue', 'type', 'network', 'service', 'trading_fees', 'max_leverage', 'min_order_size_usd',
                      'min_stake_amount', 'unstaking_period']:
            venue_fields.append(field)
        elif field in ['base_currency', 'quote_currency', 'decimal_places', 'description', 'allows_hedging',
                      'basis_trading_supported', 'leverage_supported', 'staking_supported', 'market_neutral',
                      'risk_level', 'supported_strategies']:
            share_class_fields.append(field)
        else:
            # Put remaining fields in infrastructure
            infrastructure_fields.append(field)
    
    models = []
    models.append('"""Comprehensive Configuration Models - Union of all configs."""')
    models.append('')
    models.append('from pydantic import BaseModel, Field')
    models.append('from typing import Dict, List, Optional, Any, Union')
    models.append('from enum import Enum')
    models.append('')
    
    # Generate InfrastructureConfigUnion
    models.append('class InfrastructureConfigUnion(BaseModel):')
    models.append('    """Union model covering all infrastructure configuration fields."""')
    models.append('')
    for field in sorted(infrastructure_fields):
        if '.' not in field:  # Only top-level fields for now
            field_type = infer_field_type(configs, field)
            models.append(f'    {field}: Optional[{field_type}] = Field(default=None, description="Infrastructure config field")')
    models.append('')
    
    # Generate StrategyConfigUnion
    models.append('class StrategyConfigUnion(BaseModel):')
    models.append('    """Union model covering all strategy configuration fields."""')
    models.append('')
    for field in sorted(strategy_fields):
        if '.' not in field:  # Only top-level fields for now
            field_type = infer_field_type(configs, field)
            models.append(f'    {field}: Optional[{field_type}] = Field(default=None, description="Strategy config field")')
    models.append('')
    
    # Generate VenueConfigUnion
    models.append('class VenueConfigUnion(BaseModel):')
    models.append('    """Union model covering all venue configuration fields."""')
    models.append('')
    for field in sorted(venue_fields):
        if '.' not in field:  # Only top-level fields for now
            field_type = infer_field_type(configs, field)
            models.append(f'    {field}: Optional[{field_type}] = Field(default=None, description="Venue config field")')
    models.append('')
    
    # Generate ShareClassConfigUnion
    models.append('class ShareClassConfigUnion(BaseModel):')
    models.append('    """Union model covering all share class configuration fields."""')
    models.append('')
    for field in sorted(share_class_fields):
        if '.' not in field:  # Only top-level fields for now
            field_type = infer_field_type(configs, field)
            models.append(f'    {field}: Optional[{field_type}] = Field(default=None, description="Share class config field")')
    models.append('')
    
    # Generate main ConfigUnion
    models.append('class ConfigUnion(BaseModel):')
    models.append('    """Main union model covering all configuration files."""')
    models.append('')
    models.append('    infrastructure: Optional[InfrastructureConfigUnion] = Field(default=None, description="Infrastructure configuration")')
    models.append('    strategy: Optional[StrategyConfigUnion] = Field(default=None, description="Strategy configuration")')
    models.append('    venue: Optional[VenueConfigUnion] = Field(default=None, description="Venue configuration")')
    models.append('    share_class: Optional[ShareClassConfigUnion] = Field(default=None, description="Share class configuration")')
    models.append('')
    
    # Add nested field models for complex structures
    nested_fields = [f for f in all_fields if '.' in f]
    if nested_fields:
        models.append('# Nested field models')
        for field in sorted(set(f.split('.')[0] for f in nested_fields)):
            if field not in ['api', 'cache', 'database', 'redis', 'storage', 'monitoring', 'trading_fees', 'hedge_allocation', 'capital_allocation']:
                continue
            
            models.append(f'class {field.title()}ConfigNested(BaseModel):')
            models.append(f'    """Nested model for {field} configuration."""')
            models.append('')
            
            # Find all nested fields for this category
            for nested_field in sorted(nested_fields):
                if nested_field.startswith(f"{field}."):
                    field_name = nested_field[len(f"{field}."):]
                    if '.' not in field_name:  # Only one level deep
                        field_type = infer_field_type(configs, nested_field)
                        models.append(f'    {field_name}: Optional[{field_type}] = Field(default=None, description="Nested {field} field")')
            models.append('')
    
    return '\n'.join(models)

def main():
    print("🔍 Creating comprehensive union Pydantic models...")
    
    # Load all configs
    configs = load_all_configs()
    print(f"📄 Loaded {len(configs)} configuration files")
    
    # Generate models
    models_code = generate_comprehensive_models(configs)
    
    # Save to file
    output_file = Path(__file__).parent.parent / "backend" / "src" / "basis_strategy_v1" / "core" / "config" / "config_union_models.py"
    with open(output_file, 'w') as f:
        f.write(models_code)
    
    print(f"💾 Saved comprehensive union models to: {output_file}")
    print("✅ Complete!")

if __name__ == "__main__":
    main()
