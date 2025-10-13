"""
Unit tests for Utility Manager.

Tests the utility manager component in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from decimal import Decimal

from basis_strategy_v1.core.utilities.utility_manager import UtilityManager


class TestUtilityManager:
    """Test Utility Manager component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for utility manager."""
        return {
            'precision': 8,
            'default_currency': 'USDT',
            'timezone': 'UTC'
        }
    
    @pytest.fixture
    def mock_utility_manager(self, mock_config):
        """Create utility manager with mocked dependencies."""
        mock_data_provider = Mock()
        manager = UtilityManager(mock_config, mock_data_provider)
        return manager
    
    def test_initialization(self, mock_config):
        """Test utility manager initialization."""
        mock_data_provider = Mock()
        manager = UtilityManager(mock_config, mock_data_provider)
        
        assert manager.config == mock_config
        assert manager.data_provider == mock_data_provider
    
    def test_format_currency(self, mock_utility_manager):
        """Test currency formatting."""
        # Test with default precision
        formatted = mock_utility_manager.format_currency(1234.56789)
        assert formatted == '1234.56789000'
        
        # Test with custom precision
        formatted = mock_utility_manager.format_currency(1234.56789, precision=2)
        assert formatted == '1234.57'
        
        # Test with zero
        formatted = mock_utility_manager.format_currency(0)
        assert formatted == '0.00000000'
        
        # Test with negative number
        formatted = mock_utility_manager.format_currency(-1234.56789)
        assert formatted == '-1234.56789000'
    
    def test_format_percentage(self, mock_utility_manager):
        """Test percentage formatting."""
        # Test with default precision
        formatted = mock_utility_manager.format_percentage(0.123456789)
        assert formatted == '12.34567890%'
        
        # Test with custom precision
        formatted = mock_utility_manager.format_percentage(0.123456789, precision=2)
        assert formatted == '12.35%'
        
        # Test with zero
        formatted = mock_utility_manager.format_percentage(0)
        assert formatted == '0.00000000%'
        
        # Test with negative percentage
        formatted = mock_utility_manager.format_percentage(-0.123456789)
        assert formatted == '-12.34567890%'
    
    def test_calculate_percentage_change(self, mock_utility_manager):
        """Test percentage change calculation."""
        # Test positive change
        change = mock_utility_manager.calculate_percentage_change(100, 110)
        assert change == 0.10  # 10%
        
        # Test negative change
        change = mock_utility_manager.calculate_percentage_change(100, 90)
        assert change == -0.10  # -10%
        
        # Test no change
        change = mock_utility_manager.calculate_percentage_change(100, 100)
        assert change == 0.0
        
        # Test with zero initial value
        change = mock_utility_manager.calculate_percentage_change(0, 100)
        assert change == float('inf')  # Infinite change
    
    def test_round_to_precision(self, mock_utility_manager):
        """Test rounding to precision."""
        # Test with default precision
        rounded = mock_utility_manager.round_to_precision(1234.56789)
        assert rounded == 1234.56789000
        
        # Test with custom precision
        rounded = mock_utility_manager.round_to_precision(1234.56789, precision=2)
        assert rounded == 1234.57
        
        # Test with zero
        rounded = mock_utility_manager.round_to_precision(0)
        assert rounded == 0.0
        
        # Test with negative number
        rounded = mock_utility_manager.round_to_precision(-1234.56789)
        assert rounded == -1234.56789000
    
    def test_validate_amount(self, mock_utility_manager):
        """Test amount validation."""
        # Test valid amounts
        assert mock_utility_manager.validate_amount(100.0) is True
        assert mock_utility_manager.validate_amount(0.001) is True
        assert mock_utility_manager.validate_amount(1000000.0) is True
        
        # Test invalid amounts
        assert mock_utility_manager.validate_amount(-100.0) is False
        assert mock_utility_manager.validate_amount(0.0) is False
        assert mock_utility_manager.validate_amount(None) is False
        assert mock_utility_manager.validate_amount('invalid') is False
    
    def test_validate_percentage(self, mock_utility_manager):
        """Test percentage validation."""
        # Test valid percentages
        assert mock_utility_manager.validate_percentage(0.1) is True  # 10%
        assert mock_utility_manager.validate_percentage(0.0) is True   # 0%
        assert mock_utility_manager.validate_percentage(1.0) is True   # 100%
        
        # Test invalid percentages
        assert mock_utility_manager.validate_percentage(-0.1) is False  # -10%
        assert mock_utility_manager.validate_percentage(1.1) is False   # 110%
        assert mock_utility_manager.validate_percentage(None) is False
        assert mock_utility_manager.validate_percentage('invalid') is False
    
    def test_convert_currency(self, mock_utility_manager):
        """Test currency conversion."""
        # Test same currency conversion
        converted = mock_utility_manager.convert_currency(100.0, 'USDT', 'USDT')
        assert converted == 100.0
        
        # Test with exchange rates
        with patch.object(mock_utility_manager, '_get_exchange_rate', return_value=0.5):
            converted = mock_utility_manager.convert_currency(100.0, 'USDT', 'BTC')
            assert converted == 50.0
        
        # Test reverse conversion
        with patch.object(mock_utility_manager, '_get_exchange_rate', return_value=2.0):
            converted = mock_utility_manager.convert_currency(100.0, 'BTC', 'USDT')
            assert converted == 200.0
    
    def test_get_exchange_rate(self, mock_utility_manager):
        """Test exchange rate retrieval."""
        # Test with mock exchange rates
        mock_utility_manager.exchange_rates = {
            'BTC/USDT': 50000.0,
            'ETH/USDT': 3000.0
        }
        
        rate = mock_utility_manager._get_exchange_rate('BTC', 'USDT')
        assert rate == 50000.0
        
        rate = mock_utility_manager._get_exchange_rate('ETH', 'USDT')
        assert rate == 3000.0
        
        # Test reverse rate
        rate = mock_utility_manager._get_exchange_rate('USDT', 'BTC')
        assert rate == 1.0 / 50000.0
    
    def test_calculate_compound_interest(self, mock_utility_manager):
        """Test compound interest calculation."""
        # Test simple case
        amount = mock_utility_manager.calculate_compound_interest(1000.0, 0.1, 1)  # 10% for 1 year
        assert amount == 1100.0
        
        # Test multiple periods
        amount = mock_utility_manager.calculate_compound_interest(1000.0, 0.1, 2)  # 10% for 2 years
        assert amount == 1210.0
        
        # Test with zero interest
        amount = mock_utility_manager.calculate_compound_interest(1000.0, 0.0, 1)
        assert amount == 1000.0
        
        # Test with zero periods
        amount = mock_utility_manager.calculate_compound_interest(1000.0, 0.1, 0)
        assert amount == 1000.0
    
    def test_calculate_annualized_return(self, mock_utility_manager):
        """Test annualized return calculation."""
        # Test positive return
        annualized = mock_utility_manager.calculate_annualized_return(1000.0, 1100.0, 1)  # 1 year
        assert annualized == 0.10  # 10%
        
        # Test negative return
        annualized = mock_utility_manager.calculate_annualized_return(1000.0, 900.0, 1)  # 1 year
        assert annualized == -0.10  # -10%
        
        # Test multiple years
        annualized = mock_utility_manager.calculate_annualized_return(1000.0, 1210.0, 2)  # 2 years
        assert abs(annualized - 0.10) < 0.001  # Approximately 10%
    
    def test_format_timestamp(self, mock_utility_manager):
        """Test timestamp formatting."""
        timestamp = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        
        # Test default format
        formatted = mock_utility_manager.format_timestamp(timestamp)
        assert '2024-01-15' in formatted
        assert '12:30:45' in formatted
        
        # Test custom format
        formatted = mock_utility_manager.format_timestamp(timestamp, format='%Y-%m-%d')
        assert formatted == '2024-01-15'
    
    def test_parse_timestamp(self, mock_utility_manager):
        """Test timestamp parsing."""
        # Test ISO format
        timestamp_str = '2024-01-15T12:30:45Z'
        parsed = mock_utility_manager.parse_timestamp(timestamp_str)
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 15
        assert parsed.hour == 12
        assert parsed.minute == 30
        assert parsed.second == 45
        
        # Test custom format
        timestamp_str = '2024-01-15'
        parsed = mock_utility_manager.parse_timestamp(timestamp_str, format='%Y-%m-%d')
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 15
    
    def test_generate_uuid(self, mock_utility_manager):
        """Test UUID generation."""
        uuid1 = mock_utility_manager.generate_uuid()
        uuid2 = mock_utility_manager.generate_uuid()
        
        assert uuid1 != uuid2
        assert len(uuid1) == 36  # Standard UUID length
        assert len(uuid2) == 36
    
    def test_hash_string(self, mock_utility_manager):
        """Test string hashing."""
        hash1 = mock_utility_manager.hash_string('test_string')
        hash2 = mock_utility_manager.hash_string('test_string')
        hash3 = mock_utility_manager.hash_string('different_string')
        
        assert hash1 == hash2  # Same input should produce same hash
        assert hash1 != hash3  # Different input should produce different hash
        assert len(hash1) == 64  # SHA-256 hash length
    
    def test_validate_email(self, mock_utility_manager):
        """Test email validation."""
        # Test valid emails
        assert mock_utility_manager.validate_email('test@example.com') is True
        assert mock_utility_manager.validate_email('user.name@domain.co.uk') is True
        
        # Test invalid emails
        assert mock_utility_manager.validate_email('invalid_email') is False
        assert mock_utility_manager.validate_email('@example.com') is False
        assert mock_utility_manager.validate_email('test@') is False
        assert mock_utility_manager.validate_email('') is False
    
    def test_validate_url(self, mock_utility_manager):
        """Test URL validation."""
        # Test valid URLs
        assert mock_utility_manager.validate_url('https://example.com') is True
        assert mock_utility_manager.validate_url('http://example.com/path') is True
        assert mock_utility_manager.validate_url('https://subdomain.example.com:8080/path?param=value') is True
        
        # Test invalid URLs
        assert mock_utility_manager.validate_url('invalid_url') is False
        assert mock_utility_manager.validate_url('ftp://example.com') is False  # Only HTTP/HTTPS
        assert mock_utility_manager.validate_url('') is False
    
    def test_sanitize_string(self, mock_utility_manager):
        """Test string sanitization."""
        # Test with special characters
        sanitized = mock_utility_manager.sanitize_string('test<script>alert("xss")</script>')
        assert '<script>' not in sanitized
        assert 'alert' not in sanitized
        
        # Test with SQL injection attempt
        sanitized = mock_utility_manager.sanitize_string("test'; DROP TABLE users; --")
        assert "DROP TABLE" not in sanitized
        assert "';" not in sanitized
        
        # Test with normal string
        sanitized = mock_utility_manager.sanitize_string('normal_string')
        assert sanitized == 'normal_string'
    
    def test_error_handling_invalid_input(self, mock_utility_manager):
        """Test error handling with invalid input."""
        # Test with None input
        with pytest.raises(ValueError):
            mock_utility_manager.format_currency(None)
        
        with pytest.raises(ValueError):
            mock_utility_manager.calculate_percentage_change(None, 100)
        
        with pytest.raises(ValueError):
            mock_utility_manager.round_to_precision(None)
    
    def test_edge_case_very_small_numbers(self, mock_utility_manager):
        """Test edge case with very small numbers."""
        # Test with very small positive number
        formatted = mock_utility_manager.format_currency(0.00000001)
        assert formatted == '0.00000001'
        
        # Test with very small negative number
        formatted = mock_utility_manager.format_currency(-0.00000001)
        assert formatted == '-0.00000001'
        
        # Test rounding very small numbers
        rounded = mock_utility_manager.round_to_precision(0.00000001, precision=2)
        assert rounded == 0.0
    
    def test_edge_case_very_large_numbers(self, mock_utility_manager):
        """Test edge case with very large numbers."""
        # Test with very large number
        formatted = mock_utility_manager.format_currency(999999999.99999999)
        assert '999999999' in formatted
        
        # Test percentage with very large number
        formatted = mock_utility_manager.format_percentage(999.99999999)
        assert '99999.99999900%' in formatted
    
    def test_edge_case_zero_values(self, mock_utility_manager):
        """Test edge case with zero values."""
        # Test currency formatting with zero
        formatted = mock_utility_manager.format_currency(0.0)
        assert formatted == '0.00000000'
        
        # Test percentage formatting with zero
        formatted = mock_utility_manager.format_percentage(0.0)
        assert formatted == '0.00000000%'
        
        # Test percentage change with zero
        change = mock_utility_manager.calculate_percentage_change(0, 100)
        assert change == float('inf')
    
    def test_edge_case_negative_values(self, mock_utility_manager):
        """Test edge case with negative values."""
        # Test currency formatting with negative
        formatted = mock_utility_manager.format_currency(-100.0)
        assert formatted == '-100.00000000'
        
        # Test percentage formatting with negative
        formatted = mock_utility_manager.format_percentage(-0.1)
        assert formatted == '-10.00000000%'
        
        # Test percentage change with negative
        change = mock_utility_manager.calculate_percentage_change(100, -50)
        assert change == -1.5  # -150%
    
    def test_precision_handling(self, mock_utility_manager):
        """Test precision handling in various operations."""
        # Test with different precision settings
        manager = UtilityManager({'precision': 2})
        
        formatted = manager.format_currency(123.456789)
        assert formatted == '123.46'  # Rounded to 2 decimal places
        
        formatted = manager.format_percentage(0.123456789)
        assert formatted == '12.35%'  # Rounded to 2 decimal places
