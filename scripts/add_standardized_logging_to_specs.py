#!/usr/bin/env python3
"""
Script to add standardized logging methods to all component specifications.
"""

import os
import re
from pathlib import Path


STANDARDIZED_LOGGING_METHODS = """
## Standardized Logging Methods

**Note**: These methods are defined in the [Health & Error Systems](HEALTH_ERROR_SYSTEMS.md) spec and should be implemented by all components for consistent logging patterns.

### log_structured_event(timestamp, event_type, level, message, component_name, data=None, correlation_id=None)
Log a structured event with standardized format.

**Parameters**:
- `timestamp`: Event timestamp (pd.Timestamp)
- `event_type`: Type of event (EventType enum)
- `level`: Log level (LogLevel enum)
- `message`: Human-readable message (str)
- `component_name`: Name of the component logging the event (str)
- `data`: Optional structured data dictionary (Dict[str, Any])
- `correlation_id`: Optional correlation ID for tracing (str)

**Returns**: None

### log_component_event(event_type, message, data=None, level=LogLevel.INFO)
Log a component-specific event with automatic timestamp and component name.

**Parameters**:
- `event_type`: Type of event (EventType enum)
- `message`: Human-readable message (str)
- `data`: Optional structured data dictionary (Dict[str, Any])
- `level`: Log level (defaults to INFO)

**Returns**: None

### log_performance_metric(metric_name, value, unit, data=None)
Log a performance metric.

**Parameters**:
- `metric_name`: Name of the metric (str)
- `value`: Metric value (float)
- `unit`: Unit of measurement (str)
- `data`: Optional additional context data (Dict[str, Any])

**Returns**: None

### log_error(error, context=None, correlation_id=None)
Log an error with standardized format.

**Parameters**:
- `error`: Exception object (Exception)
- `context`: Optional context data (Dict[str, Any])
- `correlation_id`: Optional correlation ID for tracing (str)

**Returns**: None

### log_warning(message, data=None, correlation_id=None)
Log a warning with standardized format.

**Parameters**:
- `message`: Warning message (str)
- `data`: Optional context data (Dict[str, Any])
- `correlation_id`: Optional correlation ID for tracing (str)

**Returns**: None
"""


def add_standardized_logging_to_spec(spec_file: str) -> bool:
    """Add standardized logging methods to a component spec file."""
    try:
        with open(spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if standardized logging methods are already present
        if "## Standardized Logging Methods" in content:
            print(f"  ✅ {os.path.basename(spec_file)}: Already has standardized logging methods")
            return True
        
        # Find the Core Methods section
        core_methods_match = re.search(r'(## Core Methods.*?)(?=## |$)', content, re.DOTALL)
        if not core_methods_match:
            print(f"  ❌ {os.path.basename(spec_file)}: No Core Methods section found")
            return False
        
        # Find the end of the Core Methods section
        core_methods_end = core_methods_match.end()
        
        # Look for the next section after Core Methods
        next_section_match = re.search(r'## [A-Z][^#]*', content[core_methods_end:])
        if next_section_match:
            # Insert before the next section
            insert_position = core_methods_end + next_section_match.start()
        else:
            # Insert at the end of the file
            insert_position = len(content)
        
        # Insert the standardized logging methods
        new_content = (
            content[:insert_position] + 
            "\n" + STANDARDIZED_LOGGING_METHODS + "\n" +
            content[insert_position:]
        )
        
        # Write the updated content
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✅ {os.path.basename(spec_file)}: Added standardized logging methods")
        return True
        
    except Exception as e:
        print(f"  ❌ {os.path.basename(spec_file)}: Error - {e}")
        return False


def main():
    """Add standardized logging methods to all component specs."""
    print("🔧 Adding Standardized Logging Methods to Component Specs")
    print("=" * 60)
    
    specs_dir = "docs/specs/"
    if not os.path.exists(specs_dir):
        print(f"❌ Specs directory not found: {specs_dir}")
        return
    
    # Get all spec files
    spec_files = []
    for file in os.listdir(specs_dir):
        if file.endswith('.md') and file.startswith(('0', '1', '2')):
            spec_files.append(os.path.join(specs_dir, file))
    
    spec_files.sort()
    
    success_count = 0
    total_count = len(spec_files)
    
    for spec_file in spec_files:
        if add_standardized_logging_to_spec(spec_file):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY: {success_count}/{total_count} specs updated successfully")
    
    if success_count == total_count:
        print("🎉 All component specs now have standardized logging methods!")
    else:
        print("⚠️  Some specs could not be updated - check the errors above")


if __name__ == "__main__":
    main()
