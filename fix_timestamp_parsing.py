#!/usr/bin/env python3
"""
Fix timestamp parsing in historical_data_provider.py to handle Unix timestamps properly.
"""

import re

def fix_timestamp_parsing():
    """Fix the _parse_timestamp_robust function to handle Unix timestamps."""
    
    file_path = '/workspace/backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py'
    
    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find and replace the _parse_timestamp_robust function
    old_function = '''def _parse_timestamp_robust(timestamp_series):
    """Robust timestamp parsing that handles various formats."""
    try:
        # First try standard pandas parsing
        return pd.to_datetime(timestamp_series, utc=True)
    except:
        try:
            # Clean up malformed timestamps (remove Z if +00:00 is present)
            cleaned = timestamp_series.str.replace(r'\+00:00Z$', '+00:00', regex=True)
            return pd.to_datetime(cleaned, utc=True)
        except:
            try:
                # Try ISO8601 format
                return pd.to_datetime(timestamp_series, format='ISO8601', utc=True)
            except:
                # Last resort: try mixed format
                return pd.to_datetime(timestamp_series, format='mixed', utc=True)'''
    
    new_function = '''def _parse_timestamp_robust(timestamp_series):
    """Robust timestamp parsing that handles various formats."""
    try:
        # First try standard pandas parsing
        return pd.to_datetime(timestamp_series, utc=True)
    except:
        try:
            # Check if these look like Unix timestamps (10 digits)
            if timestamp_series.dtype in ['int64', 'float64'] and len(str(int(timestamp_series.iloc[0]))) == 10:
                # Unix timestamp in seconds
                return pd.to_datetime(timestamp_series, unit='s', utc=True)
        except:
            pass
        
        try:
            # Clean up malformed timestamps (remove Z if +00:00 is present)
            cleaned = timestamp_series.str.replace(r'\+00:00Z$', '+00:00', regex=True)
            return pd.to_datetime(cleaned, utc=True)
        except:
            try:
                # Try ISO8601 format
                return pd.to_datetime(timestamp_series, format='ISO8601', utc=True)
            except:
                # Last resort: try mixed format
                return pd.to_datetime(timestamp_series, format='mixed', utc=True)'''
    
    # Replace the function
    if old_function in content:
        content = content.replace(old_function, new_function)
        
        # Write the updated content
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("✅ Fixed timestamp parsing function")
        return True
    else:
        print("❌ Could not find the function to replace")
        return False

if __name__ == "__main__":
    fix_timestamp_parsing()