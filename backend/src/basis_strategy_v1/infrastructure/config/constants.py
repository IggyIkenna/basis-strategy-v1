"""
Configuration constants to avoid circular imports.
"""

from pathlib import Path
import os

# Base directory for the project
_BASE_DIR = Path(__file__).parent.parent.parent.parent.parent.parent

def get_environment() -> str:
    """Get the current environment from environment variables."""
    return os.getenv('BASIS_ENVIRONMENT', 'dev')
