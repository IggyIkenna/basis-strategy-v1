#!/usr/bin/env python3
"""
Script to add StandardizedLoggingMixin to all components.
"""

import os
import re
from pathlib import Path

def add_standardized_logging_to_component(file_path: str) -> bool:
    """Add StandardizedLoggingMixin to a component file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already has StandardizedLoggingMixin
        if 'StandardizedLoggingMixin' in content:
            return False  # Already has it
        
        # Add import
        import_pattern = r'from typing import Dict, List, Any, Optional\nimport logging\nimport pandas as pd\nfrom datetime import datetime\n'
        import_replacement = '''from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType
'''
        
        if re.search(import_pattern, content):
            content = re.sub(import_pattern, import_replacement, content)
        else:
            # Try alternative import pattern
            alt_pattern = r'from typing import Dict, List, Any, Optional\nimport logging\nimport pandas as pd\n'
            alt_replacement = '''from typing import Dict, List, Any, Optional
import logging
import pandas as pd

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType
'''
            if re.search(alt_pattern, content):
                content = re.sub(alt_pattern, alt_replacement, content)
            else:
                # Add import after existing imports
                lines = content.split('\n')
                import_end = 0
                for i, line in enumerate(lines):
                    if line.startswith('from ') or line.startswith('import '):
                        import_end = i
                
                lines.insert(import_end + 1, '')
                lines.insert(import_end + 2, 'from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType')
                content = '\n'.join(lines)
        
        # Add mixin to class definition
        class_pattern = r'class (\w+):\s*\n\s*"""'
        class_replacement = r'class \1(StandardizedLoggingMixin):\n    """'
        content = re.sub(class_pattern, class_replacement, content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to add standardized logging to all components."""
    components_dir = "backend/src/basis_strategy_v1/core"
    
    # Find all Python files in components directory
    component_files = []
    for root, dirs, files in os.walk(components_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                file_path = os.path.join(root, file)
                component_files.append(file_path)
    
    print("🔧 Adding Standardized Logging Mixin to Components")
    print("=" * 60)
    
    updated_count = 0
    total_count = 0
    
    for component_file in sorted(component_files):
        total_count += 1
        if add_standardized_logging_to_component(component_file):
            print(f"  ✅ {os.path.basename(component_file)}: Added StandardizedLoggingMixin")
            updated_count += 1
        else:
            print(f"  ✅ {os.path.basename(component_file)}: Already has StandardizedLoggingMixin")
    
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY: {updated_count}/{total_count} components updated successfully")
    if updated_count < total_count:
        print("⚠️  Some components could not be updated - check the errors above")

if __name__ == "__main__":
    main()
