#!/usr/bin/env python3
"""Validate agent configuration before starting."""

import os
import sys
from pathlib import Path

def validate_environment():
    """Validate environment setup."""
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 11):
        issues.append("Python 3.11+ required")
    
    # Check required directories
    required_dirs = [
        "backend/src/basis_strategy_v1",
        "docs/specs",
        "tests/unit"
    ]
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            issues.append(f"Missing directory: {dir_path}")
    
    # Check Redis connection
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
    except Exception as e:
        issues.append(f"Redis connection failed: {e}")
    
    # Check git configuration
    try:
        import subprocess
        result = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True)
        if not result.stdout.strip():
            issues.append("Git user.name not configured")
    except Exception as e:
        issues.append(f"Git configuration error: {e}")
    
    if issues:
        print("❌ Environment validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Environment validation passed")
        return True

if __name__ == "__main__":
    sys.exit(0 if validate_environment() else 1)
