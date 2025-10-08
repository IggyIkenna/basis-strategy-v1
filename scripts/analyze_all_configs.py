#!/usr/bin/env python3
"""
Analyze all config files and generate comprehensive Pydantic models.

This script will:
1. Load all config files (JSON and YAML)
2. Extract all unique field paths
3. Generate comprehensive Pydantic models that cover the union of all configs
"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, Set, List
from collections import defaultdict

class ConfigAnalyzer:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.all_fields = defaultdict(set)  # field_path -> set of values/types
        
    def analyze_all_configs(self):
        """Analyze all configuration files."""
        print("🔍 ANALYZING ALL CONFIGURATION FILES")
        print("=" * 60)
        
        # Load all JSON configs
        for json_file in self.config_dir.glob("*.json"):
            print(f"📄 Loading {json_file.name}...")
            with open(json_file, 'r') as f:
                config = json.load(f)
                self._extract_fields(config, prefix=f"json_{json_file.stem}")
        
        # Load all YAML configs in subdirectories
        for subdir in ["modes", "venues", "share_classes"]:
            subdir_path = self.config_dir / subdir
            if subdir_path.exists():
                for yaml_file in subdir_path.glob("*.yaml"):
                    print(f"📄 Loading {subdir}/{yaml_file.name}...")
                    with open(yaml_file, 'r') as f:
                        config = yaml.safe_load(f)
                        self._extract_fields(config, prefix=f"{subdir}_{yaml_file.stem}")
        
        print(f"\n✅ Analyzed {len(self.all_fields)} unique field paths")
        
    def _extract_fields(self, data: Dict[str, Any], prefix: str = "", parent_path: str = ""):
        """Extract all field paths from nested dictionary."""
        if not isinstance(data, dict):
            return
            
        for key, value in data.items():
            field_path = f"{parent_path}.{key}" if parent_path else key
            
            # Store the value type and sample values
            if isinstance(value, dict):
                self.all_fields[field_path].add("dict")
                self._extract_fields(value, prefix, field_path)
            elif isinstance(value, list):
                self.all_fields[field_path].add(f"list[{len(value)} items]")
                if value and isinstance(value[0], dict):
                    # Analyze first dict in list
                    self._extract_fields(value[0], prefix, f"{field_path}[0]")
            else:
                self.all_fields[field_path].add(f"{type(value).__name__}: {value}")
    
    def generate_pydantic_models(self) -> str:
        """Generate comprehensive Pydantic models."""
        print("\n🏗️  GENERATING COMPREHENSIVE PYDANTIC MODELS")
        print("=" * 60)
        
        # Group fields by their top-level category
        categories = defaultdict(list)
        for field_path in sorted(self.all_fields.keys()):
            top_level = field_path.split('.')[0]
            categories[top_level].append(field_path)
        
        models = []
        models.append('"""Comprehensive Configuration Models - Union of all configs."""')
        models.append('')
        models.append('from pydantic import BaseModel, Field')
        models.append('from typing import Dict, List, Optional, Any, Union')
        models.append('from enum import Enum')
        models.append('')
        
        # Generate individual models for each category
        for category, fields in categories.items():
            if category in ['json_default', 'json_local', 'json_production', 'json_staging', 'json_test']:
                continue  # Skip JSON file prefixes
                
            model_name = f"{category.title().replace('_', '')}ConfigUnion"
            models.append(f'class {model_name}(BaseModel):')
            models.append(f'    """Union model for {category} configuration."""')
            models.append('')
            
            # Generate fields for this category
            category_fields = set()
            for field_path in fields:
                if field_path.startswith(f"{category}."):
                    field_name = field_path[len(f"{category}."):]
                    if '.' not in field_name:  # Only top-level fields for now
                        category_fields.add(field_name)
            
            for field_name in sorted(category_fields):
                field_path = f"{category}.{field_name}"
                field_types = self.all_fields[field_path]
                
                # Determine the field type based on observed values
                python_type = self._infer_python_type(field_types)
                models.append(f'    {field_name}: Optional[{python_type}] = Field(default=None, description="From {category} configs")')
            
            models.append('')
        
        # Generate main union model
        models.append('class ConfigUnion(BaseModel):')
        models.append('    """Main union model covering all configuration files."""')
        models.append('')
        
        for category in sorted(categories.keys()):
            if category not in ['json_default', 'json_local', 'json_production', 'json_staging', 'json_test']:
                model_name = f"{category.title().replace('_', '')}ConfigUnion"
                models.append(f'    {category}: Optional[{model_name}] = Field(default=None, description="{category} configuration")')
        
        models.append('')
        
        return '\n'.join(models)
    
    def _infer_python_type(self, field_types: Set[str]) -> str:
        """Infer Python type from observed field types."""
        types = list(field_types)
        
        # Check for common patterns
        if any('dict' in t for t in types):
            return 'Dict[str, Any]'
        elif any('list' in t for t in types):
            return 'List[Any]'
        elif any('bool:' in t for t in types):
            return 'bool'
        elif any('int:' in t for t in types):
            return 'int'
        elif any('float:' in t for t in types):
            return 'float'
        elif any('str:' in t for t in types):
            return 'str'
        else:
            return 'Any'
    
    def print_field_analysis(self):
        """Print detailed field analysis."""
        print("\n📊 FIELD ANALYSIS")
        print("=" * 60)
        
        for field_path in sorted(self.all_fields.keys()):
            types = self.all_fields[field_path]
            print(f"{field_path}:")
            for type_info in sorted(types):
                print(f"  - {type_info}")
            print()

def main():
    config_dir = Path(__file__).parent.parent / "configs"
    analyzer = ConfigAnalyzer(config_dir)
    
    # Analyze all configs
    analyzer.analyze_all_configs()
    
    # Print field analysis
    analyzer.print_field_analysis()
    
    # Generate Pydantic models
    models_code = analyzer.generate_pydantic_models()
    
    # Save to file
    output_file = Path(__file__).parent.parent / "backend" / "src" / "basis_strategy_v1" / "core" / "config" / "config_union_models.py"
    with open(output_file, 'w') as f:
        f.write(models_code)
    
    print(f"💾 Saved comprehensive Pydantic models to: {output_file}")
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()
