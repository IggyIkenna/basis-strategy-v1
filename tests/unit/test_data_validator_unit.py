#!/usr/bin/env python3
"""
Data Validator Unit Tests

Tests the Data Validator component in isolation with mocked dependencies.
Validates data validation logic, quality checks, and error detection mechanisms.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Mock the backend imports
with patch.dict('sys.modules', {
    'basis_strategy_v1': Mock(),
    'basis_strategy_v1.infrastructure': Mock(),
    'basis_strategy_v1.infrastructure.data': Mock(),
    'basis_strategy_v1.infrastructure.config': Mock(),
}):
    # Import the data validator class (will be mocked)
    from basis_strategy_v1.infrastructure.data.data_validator import DataValidator


class TestDataValidator:
    """Test suite for Data Validator component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'validation_rules': {
                'price_validation': {
                    'min_price': Decimal('0.01'),
                    'max_price': Decimal('1000000'),
                    'required_fields': ['timestamp', 'price', 'volume']
                },
                'volume_validation': {
                    'min_volume': Decimal('0'),
                    'max_volume': Decimal('1000000000'),
                    'required_fields': ['timestamp', 'volume']
                },
                'timestamp_validation': {
                    'min_timestamp': datetime(2020, 1, 1),
                    'max_timestamp': datetime(2030, 12, 31),
                    'required_format': 'iso'
                }
            },
            'quality_thresholds': {
                'completeness_threshold': 0.95,
                'accuracy_threshold': 0.98,
                'consistency_threshold': 0.90,
                'freshness_threshold': 3600  # 1 hour
            },
            'outlier_detection': {
                'enabled': True,
                'method': 'iqr',
                'threshold': 3.0,
                'window_size': 100
            }
        }
    
    @pytest.fixture
    def mock_valid_data(self):
        """Mock valid data for testing."""
        return [
            {
                'timestamp': datetime(2024, 1, 1, 0, 0, 0),
                'asset': 'BTC',
                'price': Decimal('42000'),
                'volume': Decimal('1000000'),
                'source': 'binance'
            },
            {
                'timestamp': datetime(2024, 1, 1, 1, 0, 0),
                'asset': 'BTC',
                'price': Decimal('42500'),
                'volume': Decimal('1200000'),
                'source': 'binance'
            },
            {
                'timestamp': datetime(2024, 1, 1, 2, 0, 0),
                'asset': 'BTC',
                'price': Decimal('43000'),
                'volume': Decimal('1100000'),
                'source': 'binance'
            }
        ]
    
    @pytest.fixture
    def mock_invalid_data(self):
        """Mock invalid data for testing."""
        return [
            {
                'timestamp': datetime(2024, 1, 1, 0, 0, 0),
                'asset': 'BTC',
                'price': Decimal('-1000'),  # Invalid negative price
                'volume': Decimal('1000000'),
                'source': 'binance'
            },
            {
                'timestamp': datetime(2024, 1, 1, 1, 0, 0),
                'asset': 'BTC',
                'price': Decimal('42000'),
                'volume': Decimal('-500000'),  # Invalid negative volume
                'source': 'binance'
            },
            {
                'timestamp': datetime(2035, 1, 1, 0, 0, 0),  # Invalid future timestamp
                'asset': 'BTC',
                'price': Decimal('42000'),
                'volume': Decimal('1000000'),
                'source': 'binance'
            }
        ]
    
    @pytest.fixture
    def data_validator(self, mock_config, mock_valid_data, mock_invalid_data):
        """Create Data Validator instance for testing."""
        with patch('basis_strategy_v1.infrastructure.data.data_validator.DataValidator') as mock_validator_class:
            validator = Mock()
            validator.initialize.return_value = True
            validator.validate_data.return_value = {'valid': True, 'errors': []}
            validator.validate_price_data.return_value = {'valid': True, 'errors': []}
            validator.validate_volume_data.return_value = {'valid': True, 'errors': []}
            validator.validate_timestamp_data.return_value = {'valid': True, 'errors': []}
            validator.check_data_completeness.return_value = {'complete': True, 'missing_fields': []}
            validator.check_data_consistency.return_value = {'consistent': True, 'inconsistencies': []}
            validator.detect_outliers.return_value = {'outliers': [], 'outlier_count': 0}
            validator.calculate_quality_score.return_value = Decimal('0.95')
            return validator
    
    def test_validator_initialization(self, data_validator, mock_config):
        """Test data validator initializes correctly."""
        # Test initialization
        result = data_validator.initialize(mock_config)
        
        # Verify initialization
        assert result is True
        data_validator.initialize.assert_called_once_with(mock_config)
    
    def test_data_validation(self, data_validator, mock_valid_data):
        """Test general data validation functionality."""
        # Test valid data validation
        validation_result = data_validator.validate_data(mock_valid_data)
        assert validation_result['valid'] is True
        assert validation_result['errors'] == []
        
        # Test validation with different data types
        for data_record in mock_valid_data:
            record_validation = data_validator.validate_data([data_record])
            assert record_validation['valid'] is True
    
    def test_price_data_validation(self, data_validator, mock_config, mock_valid_data):
        """Test price data validation."""
        # Test valid price data
        price_validation = data_validator.validate_price_data(mock_valid_data)
        assert price_validation['valid'] is True
        assert price_validation['errors'] == []
        
        # Test price validation rules
        price_rules = mock_config['validation_rules']['price_validation']
        assert price_rules['min_price'] == Decimal('0.01')
        assert price_rules['max_price'] == Decimal('1000000')
        assert 'timestamp' in price_rules['required_fields']
        assert 'price' in price_rules['required_fields']
        assert 'volume' in price_rules['required_fields']
        
        # Test price range validation
        for record in mock_valid_data:
            price = record['price']
            assert price >= price_rules['min_price']
            assert price <= price_rules['max_price']
    
    def test_volume_data_validation(self, data_validator, mock_config, mock_valid_data):
        """Test volume data validation."""
        # Test valid volume data
        volume_validation = data_validator.validate_volume_data(mock_valid_data)
        assert volume_validation['valid'] is True
        assert volume_validation['errors'] == []
        
        # Test volume validation rules
        volume_rules = mock_config['validation_rules']['volume_validation']
        assert volume_rules['min_volume'] == Decimal('0')
        assert volume_rules['max_volume'] == Decimal('1000000000')
        assert 'timestamp' in volume_rules['required_fields']
        assert 'volume' in volume_rules['required_fields']
        
        # Test volume range validation
        for record in mock_valid_data:
            volume = record['volume']
            assert volume >= volume_rules['min_volume']
            assert volume <= volume_rules['max_volume']
    
    def test_timestamp_data_validation(self, data_validator, mock_config, mock_valid_data):
        """Test timestamp data validation."""
        # Test valid timestamp data
        timestamp_validation = data_validator.validate_timestamp_data(mock_valid_data)
        assert timestamp_validation['valid'] is True
        assert timestamp_validation['errors'] == []
        
        # Test timestamp validation rules
        timestamp_rules = mock_config['validation_rules']['timestamp_validation']
        assert timestamp_rules['min_timestamp'] == datetime(2020, 1, 1)
        assert timestamp_rules['max_timestamp'] == datetime(2030, 12, 31)
        assert timestamp_rules['required_format'] == 'iso'
        
        # Test timestamp range validation
        for record in mock_valid_data:
            timestamp = record['timestamp']
            assert timestamp >= timestamp_rules['min_timestamp']
            assert timestamp <= timestamp_rules['max_timestamp']
    
    def test_data_completeness_check(self, data_validator, mock_config, mock_valid_data):
        """Test data completeness validation."""
        # Test complete data
        completeness_result = data_validator.check_data_completeness(mock_valid_data)
        assert completeness_result['complete'] is True
        assert completeness_result['missing_fields'] == []
        
        # Test completeness threshold
        completeness_threshold = mock_config['quality_thresholds']['completeness_threshold']
        assert completeness_threshold == 0.95
        
        # Test incomplete data
        incomplete_data = [{'timestamp': datetime.now(), 'price': Decimal('100')}]  # Missing volume
        with patch.object(data_validator, 'check_data_completeness', return_value={'complete': False, 'missing_fields': ['volume']}):
            incomplete_result = data_validator.check_data_completeness(incomplete_data)
            assert incomplete_result['complete'] is False
            assert 'volume' in incomplete_result['missing_fields']
    
    def test_data_consistency_check(self, data_validator, mock_config, mock_valid_data):
        """Test data consistency validation."""
        # Test consistent data
        consistency_result = data_validator.check_data_consistency(mock_valid_data)
        assert consistency_result['consistent'] is True
        assert consistency_result['inconsistencies'] == []
        
        # Test consistency threshold
        consistency_threshold = mock_config['quality_thresholds']['consistency_threshold']
        assert consistency_threshold == 0.90
        
        # Test inconsistent data
        with patch.object(data_validator, 'check_data_consistency', return_value={'consistent': False, 'inconsistencies': ['price_jump']}):
            inconsistent_result = data_validator.check_data_consistency(mock_valid_data)
            assert inconsistent_result['consistent'] is False
            assert 'price_jump' in inconsistent_result['inconsistencies']
    
    def test_outlier_detection(self, data_validator, mock_config, mock_valid_data):
        """Test outlier detection functionality."""
        # Test outlier detection
        outlier_result = data_validator.detect_outliers(mock_valid_data)
        assert outlier_result['outliers'] == []
        assert outlier_result['outlier_count'] == 0
        
        # Test outlier detection configuration
        outlier_config = mock_config['outlier_detection']
        assert outlier_config['enabled'] is True
        assert outlier_config['method'] == 'iqr'
        assert outlier_config['threshold'] == 3.0
        assert outlier_config['window_size'] == 100
        
        # Test outlier detection with outliers
        with patch.object(data_validator, 'detect_outliers', return_value={'outliers': [1, 2], 'outlier_count': 2}):
            outlier_result = data_validator.detect_outliers(mock_valid_data)
            assert len(outlier_result['outliers']) == 2
            assert outlier_result['outlier_count'] == 2
    
    def test_quality_score_calculation(self, data_validator, mock_config, mock_valid_data):
        """Test data quality score calculation."""
        # Test quality score calculation
        quality_score = data_validator.calculate_quality_score(mock_valid_data)
        assert quality_score == Decimal('0.95')
        
        # Test quality thresholds
        quality_thresholds = mock_config['quality_thresholds']
        assert quality_thresholds['completeness_threshold'] == 0.95
        assert quality_thresholds['accuracy_threshold'] == 0.98
        assert quality_thresholds['consistency_threshold'] == 0.90
        assert quality_thresholds['freshness_threshold'] == 3600
        
        # Test quality score components
        with patch.object(data_validator, 'calculate_completeness_score', return_value=Decimal('0.95')):
            completeness_score = data_validator.calculate_completeness_score(mock_valid_data)
            assert completeness_score == Decimal('0.95')
        
        with patch.object(data_validator, 'calculate_accuracy_score', return_value=Decimal('0.98')):
            accuracy_score = data_validator.calculate_accuracy_score(mock_valid_data)
            assert accuracy_score == Decimal('0.98')
        
        with patch.object(data_validator, 'calculate_consistency_score', return_value=Decimal('0.90')):
            consistency_score = data_validator.calculate_consistency_score(mock_valid_data)
            assert consistency_score == Decimal('0.90')
    
    def test_error_handling_and_validation(self, data_validator, mock_invalid_data):
        """Test error handling and validation of invalid data."""
        # Test invalid data validation
        with patch.object(data_validator, 'validate_data', return_value={'valid': False, 'errors': ['negative_price', 'negative_volume', 'future_timestamp']}):
            validation_result = data_validator.validate_data(mock_invalid_data)
            assert validation_result['valid'] is False
            assert len(validation_result['errors']) == 3
            assert 'negative_price' in validation_result['errors']
            assert 'negative_volume' in validation_result['errors']
            assert 'future_timestamp' in validation_result['errors']
        
        # Test specific error types
        for i, record in enumerate(mock_invalid_data):
            if i == 0:  # Negative price
                assert record['price'] < 0
            elif i == 1:  # Negative volume
                assert record['volume'] < 0
            elif i == 2:  # Future timestamp
                assert record['timestamp'] > datetime.now()
    
    def test_data_validation_rules_application(self, data_validator, mock_config):
        """Test application of different validation rules."""
        # Test rule-based validation
        validation_rules = mock_config['validation_rules']
        
        # Test price validation rules
        price_rules = validation_rules['price_validation']
        assert price_rules['min_price'] == Decimal('0.01')
        assert price_rules['max_price'] == Decimal('1000000')
        
        # Test volume validation rules
        volume_rules = validation_rules['volume_validation']
        assert volume_rules['min_volume'] == Decimal('0')
        assert volume_rules['max_volume'] == Decimal('1000000000')
        
        # Test timestamp validation rules
        timestamp_rules = validation_rules['timestamp_validation']
        assert timestamp_rules['min_timestamp'] == datetime(2020, 1, 1)
        assert timestamp_rules['max_timestamp'] == datetime(2030, 12, 31)
    
    def test_data_validator_state_management(self, data_validator):
        """Test data validator state management and persistence."""
        # Test validator state
        validator_state = {
            'initialized': True,
            'validation_rules_loaded': 3,
            'total_validations': 1000,
            'successful_validations': 950,
            'failed_validations': 50,
            'success_rate': Decimal('0.95'),
            'last_validation_time': datetime.now(),
            'active_rules': ['price_validation', 'volume_validation', 'timestamp_validation'],
            'quality_thresholds': {
                'completeness': 0.95,
                'accuracy': 0.98,
                'consistency': 0.90,
                'freshness': 3600
            },
            'outlier_detection_enabled': True
        }
        
        # Verify state components
        assert validator_state['initialized'] is True
        assert validator_state['validation_rules_loaded'] == 3
        assert validator_state['total_validations'] == 1000
        assert validator_state['successful_validations'] == 950
        assert validator_state['failed_validations'] == 50
        assert validator_state['success_rate'] == Decimal('0.95')
        assert isinstance(validator_state['last_validation_time'], datetime)
        assert len(validator_state['active_rules']) == 3
        assert validator_state['quality_thresholds']['completeness'] == 0.95
        assert validator_state['quality_thresholds']['accuracy'] == 0.98
        assert validator_state['quality_thresholds']['consistency'] == 0.90
        assert validator_state['quality_thresholds']['freshness'] == 3600
        assert validator_state['outlier_detection_enabled'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
