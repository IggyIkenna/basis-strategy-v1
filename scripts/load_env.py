#!/usr/bin/env python3
"""
Environment Variable Loader for Quality Gates

This script loads environment variables from .env files for quality gate execution.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

def load_env_file(env_file_path: str) -> Dict[str, str]:
    """Load environment variables from a .env file."""
    env_vars = {}
    
    if not os.path.exists(env_file_path):
        print(f"Warning: Environment file not found: {env_file_path}")
        return env_vars
    
    with open(env_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                env_vars[key] = value
    
    return env_vars

def set_environment_variables(env_vars: Dict[str, str], overwrite: bool = True) -> None:
    """Set environment variables in the current process."""
    for key, value in env_vars.items():
        if overwrite or key not in os.environ:
            os.environ[key] = value

def load_quality_gates_env() -> None:
    """Load environment variables for quality gates."""
    project_root = Path(__file__).parent.parent
    
    # Load shared environment first
    shared_env_file = project_root / 'configs' / 'env' / 'shared.env'
    shared_vars = load_env_file(str(shared_env_file))
    set_environment_variables(shared_vars, overwrite=False)  # Don't overwrite existing vars
    
    # Load quality gates specific environment (allow overwriting)
    quality_gates_env_file = project_root / 'configs' / 'env' / 'quality-gates.env'
    quality_gates_vars = load_env_file(str(quality_gates_env_file))
    set_environment_variables(quality_gates_vars, overwrite=True)  # Allow overwriting
    
    print(f"✅ Loaded environment variables from:")
    print(f"   - {shared_env_file}")
    print(f"   - {quality_gates_env_file}")

if __name__ == "__main__":
    load_quality_gates_env()
    
    # Print current environment for debugging
    print("\n📋 Current Environment Variables:")
    for key in sorted(os.environ.keys()):
        if key.startswith('BASIS_'):
            print(f"   {key}={os.environ[key]}")
