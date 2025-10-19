#!/usr/bin/env python3
"""
Async I/O Quality Gates

Validates async/await patterns and global event ordering implementation
according to ADR-006 and LOGICAL_EXCEPTIONS_GUIDE.md.

This script ensures:
1. Async I/O operations use asyncio.to_thread for file operations
2. Global event ordering is properly implemented
3. Async patterns follow ADR-006 exceptions
4. Domain events have order fields for audit trails
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class AsyncIOQualityGateValidator:
    """Validates async I/O patterns and global event ordering."""
    
    def __init__(self, source_dir: str = "backend/src"):
        self.source_dir = Path(source_dir)
        self.violations = []
        self.warnings = []
        
    def validate_async_io_patterns(self) -> Dict[str, Any]:
        """Validate async I/O patterns across the codebase."""
        print("🔍 Validating async I/O patterns...")
        
        # Find all Python files
        python_files = list(self.source_dir.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(file_path))
                self._validate_file_async_patterns(file_path, tree)
                
            except Exception as e:
                self.violations.append({
                    'file': str(file_path),
                    'type': 'PARSE_ERROR',
                    'message': f"Failed to parse file: {e}",
                    'line': 0
                })
        
        return {
            'violations': self.violations,
            'warnings': self.warnings,
            'total_files': len(python_files),
            'violation_count': len(self.violations),
            'warning_count': len(self.warnings)
        }
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            '__pycache__',
            '.git',
            'conftest.py',
            'venv',
            '.pytest_cache'
        ]
        
        # Only skip files that start with test_ if they're in specific directories
        file_str = str(file_path)
        if 'test_' in file_str:
            # Skip test files in certain directories but not in tests/unit/
            if any(pattern in file_str for pattern in ['__pycache__', '.git', 'venv', '.pytest_cache']):
                return True
            # Don't skip test files in tests/unit/ directory
            if 'tests/unit/' in file_str:
                return False
        
        return any(pattern in file_str for pattern in skip_patterns)
    
    def _validate_file_async_patterns(self, file_path: Path, tree: ast.AST):
        """Validate async patterns in a single file."""
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                self._validate_async_function(file_path, node)
            elif isinstance(node, ast.Call):
                self._validate_async_call(file_path, node)
            elif isinstance(node, ast.ClassDef):
                self._validate_class_async_patterns(file_path, node)
    
    def _validate_async_function(self, file_path: Path, node: ast.AsyncFunctionDef):
        """Validate async function patterns."""
        # Check if async function is in allowed I/O context
        if not self._is_allowed_async_context(file_path, node):
            self.violations.append({
                'file': str(file_path),
                'type': 'ASYNC_VIOLATION',
                'message': f"Async function '{node.name}' not in allowed I/O context",
                'line': node.lineno
            })
        
        # Check for proper async I/O patterns
        self._check_async_io_usage(file_path, node)
    
    def _validate_async_call(self, file_path: Path, node: ast.Call):
        """Validate async call patterns."""
        # Check for asyncio.to_thread usage
        if self._is_asyncio_to_thread_call(node):
            if not self._is_in_async_context(node):
                self.violations.append({
                    'file': str(file_path),
                    'type': 'ASYNC_CALL_VIOLATION',
                    'message': "asyncio.to_thread must be called from async context",
                    'line': node.lineno
                })
    
    def _validate_class_async_patterns(self, file_path: Path, node: ast.ClassDef):
        """Validate class-level async patterns."""
        # Check for DomainEventLogger global ordering
        if 'DomainEventLogger' in node.name:
            self._validate_global_ordering_implementation(file_path, node)
    
    def _is_allowed_async_context(self, file_path: Path, node: ast.AsyncFunctionDef) -> bool:
        """Check if async function is in allowed context."""
        allowed_contexts = [
            'logging',
            'domain_event_logger',
            'results_store',
            'data_provider',
            'api_call_queue'
        ]
        
        file_str = str(file_path).lower()
        return any(context in file_str for context in allowed_contexts)
    
    def _check_async_io_usage(self, file_path: Path, node: ast.AsyncFunctionDef):
        """Check for proper async I/O usage patterns."""
        # Look for file I/O operations in async functions
        for child in ast.walk(node):
            if isinstance(child, ast.With):
                # Check if using asyncio.to_thread for file operations
                if self._is_file_operation(child):
                    if not self._uses_asyncio_to_thread(child):
                        self.warnings.append({
                            'file': str(file_path),
                            'type': 'ASYNC_IO_WARNING',
                            'message': f"File I/O in async function '{node.name}' should use asyncio.to_thread",
                            'line': child.lineno
                        })
    
    def _is_file_operation(self, node: ast.With) -> bool:
        """Check if with statement is file operation."""
        if isinstance(node.context_expr, ast.Call):
            if isinstance(node.context_expr.func, ast.Name):
                return node.context_expr.func.id == 'open'
        return False
    
    def _uses_asyncio_to_thread(self, node: ast.With) -> bool:
        """Check if node uses asyncio.to_thread."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if self._is_asyncio_to_thread_call(child):
                    return True
        return False
    
    def _is_asyncio_to_thread_call(self, node: ast.Call) -> bool:
        """Check if call is asyncio.to_thread."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return (node.func.value.id == 'asyncio' and 
                       node.func.attr == 'to_thread')
        return False
    
    def _is_in_async_context(self, node: ast.Call) -> bool:
        """Check if call is in async context."""
        # Walk up the AST to find if we're in an async function
        current = node
        while hasattr(current, 'parent'):
            current = current.parent
            if isinstance(current, ast.AsyncFunctionDef):
                return True
        return False
    
    def _validate_global_ordering_implementation(self, file_path: Path, node: ast.ClassDef):
        """Validate global ordering implementation in DomainEventLogger."""
        has_global_order = False
        has_order_lock = False
        has_get_next_order = False
        
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        if target.id == '_global_order':
                            has_global_order = True
                        elif target.id == '_order_lock':
                            has_order_lock = True
            
            elif isinstance(child, ast.AsyncFunctionDef):
                if child.name == '_get_next_global_order':
                    has_get_next_order = True
        
        if not has_global_order:
            self.violations.append({
                'file': str(file_path),
                'type': 'GLOBAL_ORDERING_VIOLATION',
                'message': "DomainEventLogger missing _global_order attribute",
                'line': getattr(node, 'lineno', 0)
            })
        
        if not has_order_lock:
            self.violations.append({
                'file': str(file_path),
                'type': 'GLOBAL_ORDERING_VIOLATION',
                'message': "DomainEventLogger missing _order_lock attribute",
                'line': getattr(node, 'lineno', 0)
            })
        
        if not has_get_next_order:
            self.violations.append({
                'file': str(file_path),
                'type': 'GLOBAL_ORDERING_VIOLATION',
                'message': "DomainEventLogger missing _get_next_global_order method",
                'line': getattr(node, 'lineno', 0)
            })
    
    def validate_domain_event_models(self) -> Dict[str, Any]:
        """Validate domain event models have order fields."""
        print("🔍 Validating domain event models...")
        
        domain_events_file = self.source_dir / "basis_strategy_v1/core/models/domain_events.py"
        
        if not domain_events_file.exists():
            self.violations.append({
                'file': str(domain_events_file),
                'type': 'MISSING_FILE',
                'message': "Domain events file not found",
                'line': 0
            })
            return {'violations': self.violations}
        
        try:
            with open(domain_events_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(domain_events_file))
            self._validate_domain_event_classes(domain_events_file, tree)
            
        except Exception as e:
            self.violations.append({
                'file': str(domain_events_file),
                'type': 'PARSE_ERROR',
                'message': f"Failed to parse domain events file: {e}",
                'line': 0
            })
        
        return {'violations': self.violations}
    
    def _validate_domain_event_classes(self, file_path: Path, tree: ast.AST):
        """Validate domain event classes have order fields."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self._is_domain_event_class(node):
                    self._check_order_field(file_path, node)
    
    def _is_domain_event_class(self, node: ast.ClassDef) -> bool:
        """Check if class is a domain event class."""
        domain_event_classes = [
            'PositionSnapshot',
            'ExposureSnapshot', 
            'RiskAssessment',
            'PnLCalculation',
            'OrderEvent',
            'OperationExecutionEvent',
            'AtomicOperationGroupEvent',
            'ExecutionDeltaEvent',
            'ReconciliationEvent',
            'TightLoopExecutionEvent',
            'EventLoggingOperationEvent',
            'StrategyDecision'
        ]
        return node.name in domain_event_classes
    
    def _check_order_field(self, file_path: Path, node: ast.ClassDef):
        """Check if domain event class has order field."""
        has_order_field = False
        
        for child in node.body:
            if isinstance(child, ast.AnnAssign):
                if isinstance(child.target, ast.Name):
                    if child.target.id == 'order':
                        has_order_field = True
                        break
        
        if not has_order_field:
            self.violations.append({
                'file': str(file_path),
                'type': 'ORDER_FIELD_VIOLATION',
                'message': f"Domain event class '{node.name}' missing order field for audit trails",
                'line': node.lineno
            })

def main():
    """Run async I/O quality gate validation."""
    print("🚀 Running Async I/O Quality Gates...")
    print("=" * 50)
    
    validator = AsyncIOQualityGateValidator()
    
    # Validate async I/O patterns
    async_results = validator.validate_async_io_patterns()
    
    # Validate domain event models
    domain_results = validator.validate_domain_event_models()
    
    # Print results
    print(f"\n📊 Async I/O Validation Results:")
    print(f"   Files processed: {async_results['total_files']}")
    print(f"   Violations: {async_results['violation_count']}")
    print(f"   Warnings: {async_results['warning_count']}")
    
    if validator.violations:
        print(f"\n❌ Violations found:")
        for violation in validator.violations:
            print(f"   {violation['file']}:{violation['line']} - {violation['type']}: {violation['message']}")
    
    if validator.warnings:
        print(f"\n⚠️  Warnings found:")
        for warning in validator.warnings:
            print(f"   {warning['file']}:{warning['line']} - {warning['type']}: {warning['message']}")
    
    if not validator.violations and not validator.warnings:
        print(f"\n✅ All async I/O patterns are valid!")
    
    # Exit with error code if violations found
    if validator.violations:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
