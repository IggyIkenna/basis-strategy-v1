"""
Centralized Pricing Validation Test

Validates that all components use UtilityManager for pricing instead of direct data access.
This test scans the codebase to ensure no components are bypassing the centralized pricing system.
"""

import pytest
import ast
import os
from pathlib import Path
from typing import List, Set, Tuple


class CentralizedPricingValidator:
    """Validates that components use centralized pricing patterns."""
    
    def __init__(self, codebase_root: str):
        self.codebase_root = Path(codebase_root)
        self.violations: List[Tuple[str, int, str]] = []
    
    def scan_file(self, file_path: Path) -> List[Tuple[str, int, str]]:
        """Scan a single Python file for pricing violations."""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Subscript):
                    # Check for direct data access patterns
                    if self._is_direct_data_access(node):
                        line_num = node.lineno
                        violation = f"Direct data access: {ast.unparse(node)}"
                        violations.append((str(file_path), line_num, violation))
                
                elif isinstance(node, ast.Call):
                    # Check for non-canonical data provider calls
                    if self._is_non_canonical_data_call(node):
                        line_num = node.lineno
                        violation = f"Non-canonical data call: {ast.unparse(node)}"
                        violations.append((str(file_path), line_num, violation))
        
        except Exception as e:
            # Skip files that can't be parsed
            pass
        
        return violations
    
    def _is_direct_data_access(self, node: ast.Subscript) -> bool:
        """Check if node represents direct data access that should use UtilityManager."""
        if not isinstance(node.value, ast.Subscript):
            return False
        
        # Check for patterns like data['market_data']['prices']['BTC']
        if isinstance(node.value.value, ast.Name) and node.value.value.id == 'data':
            if isinstance(node.value.slice, ast.Constant):
                if node.value.slice.value in ['market_data', 'protocol_data']:
                    if isinstance(node.slice, ast.Constant):
                        if node.slice.value in ['prices', 'funding_rates', 'aave_indexes', 'oracle_prices']:
                            return True
        
        return False
    
    def _is_non_canonical_data_call(self, node: ast.Call) -> bool:
        """Check if node represents non-canonical data provider calls."""
        if isinstance(node.func, ast.Attribute):
            if hasattr(node.func, 'value') and isinstance(node.func.value, ast.Name):
                if node.func.value.id == 'data_provider':
                    # Check for old method calls that should use UtilityManager
                    if node.func.attr in ['get_market_price', 'get_funding_rate', 'get_liquidity_index', 'get_oracle_price']:
                        return True
        
        return False
    
    def scan_codebase(self) -> List[Tuple[str, int, str]]:
        """Scan entire codebase for pricing violations."""
        all_violations = []
        
        # Scan core components
        core_path = self.codebase_root / "backend" / "src" / "basis_strategy_v1" / "core"
        for py_file in core_path.rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue  # Skip test files
            
            violations = self.scan_file(py_file)
            all_violations.extend(violations)
        
        return all_violations


class TestCentralizedPricingValidation:
    """Test that validates centralized pricing usage across the codebase."""
    
    def setup_method(self):
        """Set up the validator."""
        self.validator = CentralizedPricingValidator(".")
    
    def test_no_direct_data_access_in_core_components(self):
        """Test that core components don't access data directly."""
        violations = self.validator.scan_codebase()
        
        # Filter out violations that are acceptable (like in data providers themselves)
        filtered_violations = []
        for file_path, line_num, violation in violations:
            # Skip data provider files (they're allowed to access data directly)
            if "data_provider" in file_path or "data_validator" in file_path:
                continue
            
            # Skip utility manager (it's the centralized access point)
            if "utility_manager" in file_path:
                continue
            
            filtered_violations.append((file_path, line_num, violation))
        
        if filtered_violations:
            violation_messages = []
            for file_path, line_num, violation in filtered_violations:
                violation_messages.append(f"{file_path}:{line_num} - {violation}")
            
            pytest.fail(f"Found direct data access violations:\n" + "\n".join(violation_messages))
    
    def test_components_use_utility_manager_methods(self):
        """Test that components use UtilityManager methods for pricing."""
        # This test verifies that components are using the correct method names
        # We'll check for the presence of UtilityManager method calls
        
        core_path = Path("backend/src/basis_strategy_v1/core")
        utility_manager_usage = []
        
        for py_file in core_path.rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for UtilityManager method usage
                if "utility_manager" in content:
                    if any(method in content for method in [
                        "get_price_for_position_key",
                        "get_liquidity_index", 
                        "get_funding_rate",
                        "get_oracle_price",
                        "get_market_price"
                    ]):
                        utility_manager_usage.append(str(py_file))
            
            except Exception:
                pass
        
        # We should find UtilityManager usage in key components
        assert len(utility_manager_usage) > 0, "No UtilityManager usage found in core components"
    
    def test_data_structure_uses_uppercase_keys(self):
        """Test that data structure uses uppercase keys consistently."""
        # This test verifies the data structure format
        # We'll check the data provider files to ensure they use uppercase keys
        
        data_provider_path = Path("backend/src/basis_strategy_v1/infrastructure/data")
        uppercase_usage = []
        lowercase_violations = []
        
        for py_file in data_provider_path.rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for uppercase key usage
                if "'BTC'" in content or '"BTC"' in content:
                    uppercase_usage.append(str(py_file))
                
                # Check for lowercase violations (should not exist)
                if "'btc'" in content or '"btc"' in content:
                    if "BTC" not in content:  # Allow if uppercase version also exists
                        lowercase_violations.append(str(py_file))
            
            except Exception:
                pass
        
        # Should find uppercase usage in data providers
        assert len(uppercase_usage) > 0, "No uppercase key usage found in data providers"
        
        # Should not find lowercase violations
        if lowercase_violations:
            pytest.fail(f"Found lowercase key violations in: {lowercase_violations}")
    
    def test_oracle_prices_use_base_quote_format(self):
        """Test that oracle prices use BASE/QUOTE format."""
        # Check data provider files for BASE/QUOTE format usage
        data_provider_path = Path("backend/src/basis_strategy_v1/infrastructure/data")
        base_quote_usage = []
        
        for py_file in data_provider_path.rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for BASE/QUOTE format
                if "/" in content and ("weETH/USD" in content or "wstETH/ETH" in content):
                    base_quote_usage.append(str(py_file))
            
            except Exception:
                pass
        
        # Should find BASE/QUOTE format usage
        assert len(base_quote_usage) > 0, "No BASE/QUOTE format found in data providers"
    
    def test_venue_keys_use_asset_venue_format(self):
        """Test that venue-specific keys use ASSET_venue format."""
        # Check for venue key format
        data_provider_path = Path("backend/src/basis_strategy_v1/infrastructure/data")
        venue_format_usage = []
        
        for py_file in data_provider_path.rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for ASSET_venue format
                if "BTC_binance" in content or "ETH_bybit" in content:
                    venue_format_usage.append(str(py_file))
            
            except Exception:
                pass
        
        # Should find venue format usage
        assert len(venue_format_usage) > 0, "No ASSET_venue format found in data providers"


if __name__ == '__main__':
    pytest.main([__file__])
