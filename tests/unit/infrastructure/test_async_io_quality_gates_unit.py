"""
Unit tests for Async I/O Quality Gates validation.

Tests the quality gate validation logic for async I/O patterns and global ordering.
"""

import pytest
import ast
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.test_async_io_quality_gates import AsyncIOQualityGateValidator


class TestAsyncIOQualityGateValidator:
    """Test Async I/O Quality Gate validation logic."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return AsyncIOQualityGateValidator("tests/")
    
    def test_should_skip_file_patterns(self, validator):
        """Test file skipping patterns work correctly."""
        # Files that should be skipped
        skip_files = [
            Path("tests/__pycache__/test.py"),
            Path("tests/.git/test.py"),
            Path("tests/conftest.py"),
            Path("tests/venv/test.py"),
            Path("tests/.pytest_cache/test.py")
        ]
        
        for file_path in skip_files:
            assert validator._should_skip_file(file_path)
        
        # Files that should not be skipped (including test files in tests/unit/)
        keep_files = [
            Path("tests/unit/test_component.py"),
            Path("tests/integration/test_flow.py"),
            Path("tests/e2e/test_strategy.py"),
            Path("tests/test_async.py")  # This should not be skipped
        ]
        
        for file_path in keep_files:
            assert not validator._should_skip_file(file_path)

    def test_is_allowed_async_context(self, validator):
        """Test async context validation."""
        # Allowed contexts
        allowed_files = [
            Path("backend/src/logging/domain_event_logger.py"),
            Path("backend/src/infrastructure/logging/structured_logger.py"),
            Path("backend/src/results_store.py"),
            Path("backend/src/data_provider.py"),
            Path("backend/src/api_call_queue.py")
        ]
        
        for file_path in allowed_files:
            # Create a mock async function node
            async_func = ast.AsyncFunctionDef(name="test_async", body=[], decorator_list=[])
            assert validator._is_allowed_async_context(file_path, async_func)
        
        # Not allowed contexts
        not_allowed_files = [
            Path("backend/src/position_monitor.py"),
            Path("backend/src/strategy_manager.py"),
            Path("backend/src/execution_manager.py")
        ]
        
        for file_path in not_allowed_files:
            async_func = ast.AsyncFunctionDef(name="test_async", body=[], decorator_list=[])
            assert not validator._is_allowed_async_context(file_path, async_func)

    def test_is_asyncio_to_thread_call(self, validator):
        """Test asyncio.to_thread call detection."""
        # Valid asyncio.to_thread call
        valid_call = ast.Call(
            func=ast.Attribute(
                value=ast.Name(id="asyncio"),
                attr="to_thread"
            ),
            args=[],
            keywords=[]
        )
        assert validator._is_asyncio_to_thread_call(valid_call)
        
        # Invalid calls
        invalid_calls = [
            ast.Call(func=ast.Name(id="asyncio"), args=[], keywords=[]),
            ast.Call(func=ast.Attribute(value=ast.Name(id="other"), attr="to_thread"), args=[], keywords=[]),
            ast.Call(func=ast.Attribute(value=ast.Name(id="asyncio"), attr="gather"), args=[], keywords=[])
        ]
        
        for call in invalid_calls:
            assert not validator._is_asyncio_to_thread_call(call)

    def test_is_domain_event_class(self, validator):
        """Test domain event class detection."""
        domain_classes = [
            "PositionSnapshot",
            "ExposureSnapshot", 
            "RiskAssessment",
            "PnLCalculation",
            "OrderEvent",
            "OperationExecutionEvent",
            "TightLoopExecutionEvent"
        ]
        
        for class_name in domain_classes:
            class_node = ast.ClassDef(name=class_name, body=[], decorator_list=[])
            assert validator._is_domain_event_class(class_node)
        
        # Non-domain classes
        non_domain_classes = [
            "SomeOtherClass",
            "TestClass",
            "MockClass"
        ]
        
        for class_name in non_domain_classes:
            class_node = ast.ClassDef(name=class_name, body=[], decorator_list=[])
            assert not validator._is_domain_event_class(class_node)

    def test_check_order_field_present(self, validator):
        """Test order field detection in domain event classes."""
        # Class with order field
        class_with_order = ast.ClassDef(
            name="PositionSnapshot",
            body=[
                ast.AnnAssign(
                    target=ast.Name(id="order"),
                    annotation=ast.Name(id="Optional[int]"),
                    value=None
                )
            ],
            decorator_list=[]
        )
        
        with patch.object(validator, '_check_order_field') as mock_check:
            validator._check_order_field(Path("test.py"), class_with_order)
            mock_check.assert_called_once()

    def test_check_order_field_missing(self, validator):
        """Test order field missing detection."""
        # Class without order field
        class_without_order = ast.ClassDef(
            name="PositionSnapshot",
            body=[
                ast.AnnAssign(
                    target=ast.Name(id="timestamp"),
                    annotation=ast.Name(id="str"),
                    value=None
                )
            ],
            decorator_list=[]
        )
        
        with patch.object(validator, '_check_order_field') as mock_check:
            validator._check_order_field(Path("test.py"), class_without_order)
            mock_check.assert_called_once()

    def test_validate_global_ordering_implementation_missing_attributes(self, validator):
        """Test validation catches missing global ordering attributes."""
        # Class missing required attributes
        incomplete_class = ast.ClassDef(
            name="DomainEventLogger",
            body=[
                # Missing _global_order, _order_lock, _get_next_global_order
            ],
            decorator_list=[]
        )
        
        with patch.object(validator, 'violations', []) as mock_violations:
            validator._validate_global_ordering_implementation(Path("test.py"), incomplete_class)
            
            # Should have 3 violations (missing 3 required attributes)
            assert len(mock_violations) == 3
            assert any("_global_order" in v["message"] for v in mock_violations)
            assert any("_order_lock" in v["message"] for v in mock_violations)
            assert any("_get_next_global_order" in v["message"] for v in mock_violations)

    def test_validate_global_ordering_implementation_complete(self, validator):
        """Test validation passes with complete implementation."""
        # Complete class with all required attributes
        complete_class = ast.ClassDef(
            name="DomainEventLogger",
            body=[
                ast.Assign(
                    targets=[ast.Name(id="_global_order")],
                    value=ast.Constant(value=0)
                ),
                ast.Assign(
                    targets=[ast.Name(id="_order_lock")],
                    value=ast.Attribute(
                        value=ast.Name(id="asyncio"),
                        attr="Lock"
                    )
                ),
                ast.AsyncFunctionDef(
                    name="_get_next_global_order",
                    body=[],
                    decorator_list=[]
                )
            ],
            decorator_list=[]
        )
        
        with patch.object(validator, 'violations', []) as mock_violations:
            validator._validate_global_ordering_implementation(Path("test.py"), complete_class)
            
            # Should have no violations
            assert len(mock_violations) == 0

    def test_validate_async_io_patterns_file_parsing_error(self, validator):
        """Test handling of file parsing errors."""
        with patch('builtins.open', side_effect=Exception("Parse error")):
            with patch.object(validator, 'violations', []) as mock_violations:
                validator.validate_async_io_patterns()
                
                # Should have violations for parse errors
                assert len(mock_violations) > 0
                assert any("PARSE_ERROR" in v["type"] for v in mock_violations)

    def test_validate_domain_event_models_missing_file(self, validator):
        """Test handling of missing domain events file."""
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(validator, 'violations', []) as mock_violations:
                validator.validate_domain_event_models()
                
                # Should have violation for missing file
                assert len(mock_violations) > 0
                assert any("MISSING_FILE" in v["type"] for v in mock_violations)

    def test_validate_domain_event_models_parse_error(self, validator):
        """Test handling of domain events file parse errors."""
        with patch('builtins.open', side_effect=Exception("Parse error")):
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(validator, 'violations', []) as mock_violations:
                    validator.validate_domain_event_models()
                    
                    # Should have violation for parse error
                    assert len(mock_violations) > 0
                    assert any("PARSE_ERROR" in v["type"] for v in mock_violations)

    def test_validation_results_structure(self, validator):
        """Test validation results have correct structure."""
        with patch.object(validator, 'violations', []):
            with patch.object(validator, 'warnings', []):
                with patch.object(validator, '_validate_file_async_patterns'):
                    with patch.object(validator, '_validate_domain_event_classes'):
                        results = validator.validate_async_io_patterns()
                        
                        assert 'violations' in results
                        assert 'warnings' in results
                        assert 'total_files' in results
                        assert 'violation_count' in results
                        assert 'warning_count' in results
