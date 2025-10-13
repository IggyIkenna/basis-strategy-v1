"""
Unit tests for Error Code Registry.

Tests the error code registry component in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from basis_strategy_v1.core.error_codes.error_code_registry import ErrorCodeRegistry


class TestErrorCodeRegistry:
    """Test Error Code Registry component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for error code registry."""
        return {
            'error_codes_file': 'test_error_codes.json',
            'auto_register': True,
            'strict_mode': False
        }
    
    @pytest.fixture
    def mock_error_registry(self, mock_config):
        """Create error code registry with mocked dependencies."""
        registry = ErrorCodeRegistry()
        return registry
    
    def test_initialization(self, mock_config):
        """Test error code registry initialization."""
        registry = ErrorCodeRegistry()
        
        assert registry._error_codes is not None
        assert registry._component_codes is not None
        assert registry._severity_codes is not None
    
    def test_register_error_code(self, mock_error_registry):
        """Test error code registration."""
        error_info = {
            'code': 'TEST-001',
            'message': 'Test error message',
            'severity': 'ERROR',
            'category': 'TEST',
            'description': 'A test error for unit testing'
        }
        
        mock_error_registry.register_error_code(error_info)
        
        assert 'TEST-001' in mock_error_registry.registered_codes
        assert mock_error_registry.registered_codes['TEST-001'] == error_info
    
    def test_register_error_code_duplicate(self, mock_error_registry):
        """Test error code registration with duplicate code."""
        error_info1 = {
            'code': 'TEST-001',
            'message': 'First error message',
            'severity': 'ERROR',
            'category': 'TEST'
        }
        
        error_info2 = {
            'code': 'TEST-001',
            'message': 'Second error message',
            'severity': 'WARNING',
            'category': 'TEST'
        }
        
        # First registration should succeed
        mock_error_registry.register_error_code(error_info1)
        assert mock_error_registry.registered_codes['TEST-001'] == error_info1
        
        # Second registration should overwrite the first
        mock_error_registry.register_error_code(error_info2)
        assert mock_error_registry.registered_codes['TEST-001'] == error_info2
    
    def test_get_error_info(self, mock_error_registry):
        """Test error info retrieval."""
        error_info = {
            'code': 'TEST-001',
            'message': 'Test error message',
            'severity': 'ERROR',
            'category': 'TEST',
            'description': 'A test error for unit testing'
        }
        
        mock_error_registry.register_error_code(error_info)
        
        retrieved_info = mock_error_registry.get_error_info('TEST-001')
        
        assert retrieved_info == error_info
    
    def test_get_error_info_not_found(self, mock_error_registry):
        """Test error info retrieval for non-existent code."""
        retrieved_info = mock_error_registry.get_error_info('NON-EXISTENT')
        
        assert retrieved_info is None
    
    def test_get_error_info_with_default(self, mock_error_registry):
        """Test error info retrieval with default value."""
        default_info = {
            'code': 'UNKNOWN',
            'message': 'Unknown error',
            'severity': 'ERROR',
            'category': 'UNKNOWN'
        }
        
        retrieved_info = mock_error_registry.get_error_info('NON-EXISTENT', default=default_info)
        
        assert retrieved_info == default_info
    
    def test_get_errors_by_category(self, mock_error_registry):
        """Test error retrieval by category."""
        error_info1 = {
            'code': 'TEST-001',
            'message': 'Test error 1',
            'severity': 'ERROR',
            'category': 'TEST'
        }
        
        error_info2 = {
            'code': 'TEST-002',
            'message': 'Test error 2',
            'severity': 'WARNING',
            'category': 'TEST'
        }
        
        error_info3 = {
            'code': 'OTHER-001',
            'message': 'Other error',
            'severity': 'ERROR',
            'category': 'OTHER'
        }
        
        mock_error_registry.register_error_code(error_info1)
        mock_error_registry.register_error_code(error_info2)
        mock_error_registry.register_error_code(error_info3)
        
        test_errors = mock_error_registry.get_errors_by_category('TEST')
        
        assert len(test_errors) == 2
        assert any(error['code'] == 'TEST-001' for error in test_errors)
        assert any(error['code'] == 'TEST-002' for error in test_errors)
        assert not any(error['code'] == 'OTHER-001' for error in test_errors)
    
    def test_get_errors_by_severity(self, mock_error_registry):
        """Test error retrieval by severity."""
        error_info1 = {
            'code': 'TEST-001',
            'message': 'Test error 1',
            'severity': 'ERROR',
            'category': 'TEST'
        }
        
        error_info2 = {
            'code': 'TEST-002',
            'message': 'Test error 2',
            'severity': 'WARNING',
            'category': 'TEST'
        }
        
        error_info3 = {
            'code': 'TEST-003',
            'message': 'Test error 3',
            'severity': 'ERROR',
            'category': 'TEST'
        }
        
        mock_error_registry.register_error_code(error_info1)
        mock_error_registry.register_error_code(error_info2)
        mock_error_registry.register_error_code(error_info3)
        
        error_errors = mock_error_registry.get_errors_by_severity('ERROR')
        
        assert len(error_errors) == 2
        assert any(error['code'] == 'TEST-001' for error in error_errors)
        assert any(error['code'] == 'TEST-003' for error in error_errors)
        assert not any(error['code'] == 'TEST-002' for error in error_errors)
    
    def test_get_all_errors(self, mock_error_registry):
        """Test retrieval of all registered errors."""
        error_info1 = {
            'code': 'TEST-001',
            'message': 'Test error 1',
            'severity': 'ERROR',
            'category': 'TEST'
        }
        
        error_info2 = {
            'code': 'TEST-002',
            'message': 'Test error 2',
            'severity': 'WARNING',
            'category': 'TEST'
        }
        
        mock_error_registry.register_error_code(error_info1)
        mock_error_registry.register_error_code(error_info2)
        
        all_errors = mock_error_registry.get_all_errors()
        
        assert len(all_errors) == 2
        assert any(error['code'] == 'TEST-001' for error in all_errors)
        assert any(error['code'] == 'TEST-002' for error in all_errors)
    
    def test_validate_error_code_format(self, mock_error_registry):
        """Test error code format validation."""
        # Test valid formats
        assert mock_error_registry.validate_error_code_format('TEST-001') is True
        assert mock_error_registry.validate_error_code_format('API-123') is True
        assert mock_error_registry.validate_error_code_format('DB-999') is True
        
        # Test invalid formats
        assert mock_error_registry.validate_error_code_format('INVALID') is False
        assert mock_error_registry.validate_error_code_format('test-001') is False  # lowercase
        assert mock_error_registry.validate_error_code_format('TEST_001') is False  # underscore
        assert mock_error_registry.validate_error_code_format('TEST001') is False  # no dash
        assert mock_error_registry.validate_error_code_format('') is False
        assert mock_error_registry.validate_error_code_format(None) is False
    
    def test_validate_error_info(self, mock_error_registry):
        """Test error info validation."""
        # Test valid error info
        valid_error_info = {
            'code': 'TEST-001',
            'message': 'Test error message',
            'severity': 'ERROR',
            'category': 'TEST'
        }
        
        assert mock_error_registry.validate_error_info(valid_error_info) is True
        
        # Test invalid error info (missing required fields)
        invalid_error_info = {
            'code': 'TEST-001',
            'message': 'Test error message'
            # Missing severity and category
        }
        
        assert mock_error_registry.validate_error_info(invalid_error_info) is False
    
    def test_clear_registry(self, mock_error_registry):
        """Test registry clearing."""
        error_info = {
            'code': 'TEST-001',
            'message': 'Test error message',
            'severity': 'ERROR',
            'category': 'TEST'
        }
        
        mock_error_registry.register_error_code(error_info)
        assert len(mock_error_registry.registered_codes) == 1
        
        mock_error_registry.clear_registry()
        assert len(mock_error_registry.registered_codes) == 0
    
    def test_get_registry_stats(self, mock_error_registry):
        """Test registry statistics."""
        error_info1 = {
            'code': 'TEST-001',
            'message': 'Test error 1',
            'severity': 'ERROR',
            'category': 'TEST'
        }
        
        error_info2 = {
            'code': 'TEST-002',
            'message': 'Test error 2',
            'severity': 'WARNING',
            'category': 'TEST'
        }
        
        error_info3 = {
            'code': 'API-001',
            'message': 'API error',
            'severity': 'ERROR',
            'category': 'API'
        }
        
        mock_error_registry.register_error_code(error_info1)
        mock_error_registry.register_error_code(error_info2)
        mock_error_registry.register_error_code(error_info3)
        
        stats = mock_error_registry.get_registry_stats()
        
        assert stats['total_errors'] == 3
        assert stats['categories'] == {'TEST': 2, 'API': 1}
        assert stats['severities'] == {'ERROR': 2, 'WARNING': 1}
    
    def test_export_registry(self, mock_error_registry):
        """Test registry export."""
        error_info = {
            'code': 'TEST-001',
            'message': 'Test error message',
            'severity': 'ERROR',
            'category': 'TEST'
        }
        
        mock_error_registry.register_error_code(error_info)
        
        exported = mock_error_registry.export_registry()
        
        assert 'TEST-001' in exported
        assert exported['TEST-001'] == error_info
    
    def test_import_registry(self, mock_error_registry):
        """Test registry import."""
        import_data = {
            'TEST-001': {
                'code': 'TEST-001',
                'message': 'Test error message',
                'severity': 'ERROR',
                'category': 'TEST'
            },
            'TEST-002': {
                'code': 'TEST-002',
                'message': 'Another test error',
                'severity': 'WARNING',
                'category': 'TEST'
            }
        }
        
        mock_error_registry.import_registry(import_data)
        
        assert len(mock_error_registry.registered_codes) == 2
        assert 'TEST-001' in mock_error_registry.registered_codes
        assert 'TEST-002' in mock_error_registry.registered_codes
    
    def test_error_handling_invalid_error_info(self, mock_error_registry):
        """Test error handling with invalid error info."""
        # Test with None
        with pytest.raises(ValueError):
            mock_error_registry.register_error_code(None)
        
        # Test with invalid format
        invalid_error_info = {
            'code': 'invalid_format',
            'message': 'Test error message',
            'severity': 'ERROR',
            'category': 'TEST'
        }
        
        with pytest.raises(ValueError):
            mock_error_registry.register_error_code(invalid_error_info)
    
    def test_error_handling_missing_required_fields(self, mock_error_registry):
        """Test error handling with missing required fields."""
        incomplete_error_info = {
            'code': 'TEST-001',
            'message': 'Test error message'
            # Missing severity and category
        }
        
        with pytest.raises(ValueError):
            mock_error_registry.register_error_code(incomplete_error_info)
    
    def test_edge_case_empty_registry(self, mock_error_registry):
        """Test edge case with empty registry."""
        # Test getting errors from empty registry
        all_errors = mock_error_registry.get_all_errors()
        assert len(all_errors) == 0
        
        test_errors = mock_error_registry.get_errors_by_category('TEST')
        assert len(test_errors) == 0
        
        error_errors = mock_error_registry.get_errors_by_severity('ERROR')
        assert len(error_errors) == 0
        
        # Test stats from empty registry
        stats = mock_error_registry.get_registry_stats()
        assert stats['total_errors'] == 0
        assert stats['categories'] == {}
        assert stats['severities'] == {}
    
    def test_edge_case_very_long_error_message(self, mock_error_registry):
        """Test edge case with very long error message."""
        long_message = 'A' * 1000  # Very long message
        
        error_info = {
            'code': 'TEST-001',
            'message': long_message,
            'severity': 'ERROR',
            'category': 'TEST'
        }
        
        # Should handle long messages gracefully
        mock_error_registry.register_error_code(error_info)
        
        retrieved_info = mock_error_registry.get_error_info('TEST-001')
        assert retrieved_info['message'] == long_message
    
    def test_edge_case_special_characters_in_error_info(self, mock_error_registry):
        """Test edge case with special characters in error info."""
        error_info = {
            'code': 'TEST-001',
            'message': 'Error with special chars: !@#$%^&*()',
            'severity': 'ERROR',
            'category': 'TEST',
            'description': 'Error with unicode: 测试错误 🚨'
        }
        
        # Should handle special characters gracefully
        mock_error_registry.register_error_code(error_info)
        
        retrieved_info = mock_error_registry.get_error_info('TEST-001')
        assert retrieved_info['message'] == 'Error with special chars: !@#$%^&*()'
        assert retrieved_info['description'] == 'Error with unicode: 测试错误 🚨'
    
    def test_strict_mode_validation(self):
        """Test strict mode validation."""
        config = {
            'error_codes_file': 'test_error_codes.json',
            'auto_register': True,
            'strict_mode': True
        }
        
        registry = ErrorCodeRegistry(config)
        
        # In strict mode, should validate more strictly
        invalid_error_info = {
            'code': 'TEST-001',
            'message': 'Test error message',
            'severity': 'INVALID_SEVERITY',  # Invalid severity
            'category': 'TEST'
        }
        
        with pytest.raises(ValueError):
            registry.register_error_code(invalid_error_info)
    
    def test_auto_register_behavior(self):
        """Test auto register behavior."""
        config = {
            'error_codes_file': 'test_error_codes.json',
            'auto_register': False,  # Disabled
            'strict_mode': False
        }
        
        registry = ErrorCodeRegistry(config)
        
        # With auto_register disabled, should not automatically register
        error_info = {
            'code': 'TEST-001',
            'message': 'Test error message',
            'severity': 'ERROR',
            'category': 'TEST'
        }
        
        # Should still work when explicitly called
        registry.register_error_code(error_info)
        assert 'TEST-001' in registry.registered_codes
