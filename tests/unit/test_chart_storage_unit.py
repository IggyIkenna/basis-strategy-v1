"""
Unit tests for Chart Storage.

Tests the chart storage component in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import json

from basis_strategy_v1.infrastructure.storage.chart_storage import ChartStorageManager


class TestChartStorageManager:
    """Test Chart Storage Manager component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for chart storage."""
        return {
            'storage_path': '/tmp/charts',
            'max_file_size': 10485760,  # 10MB
            'compression': True,
            'cache_size': 100
        }
    
    @pytest.fixture
    def mock_chart_storage(self, mock_config):
        """Create chart storage with mocked dependencies."""
        with patch('basis_strategy_v1.infrastructure.storage.chart_storage.Path'):
            storage = ChartStorageManager(
                base_dir=mock_config['storage_path'],
                max_results=mock_config['max_file_size'],
                max_age_days=30
            )
            return storage
    
    def test_initialization(self, mock_config):
        """Test chart storage initialization."""
        with patch('basis_strategy_v1.infrastructure.storage.chart_storage.Path') as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.mkdir = Mock()
            mock_path.return_value = mock_path_instance
            
            storage = ChartStorageManager(
                base_dir=mock_config['storage_path'],
                max_results=mock_config['max_file_size'],
                max_age_days=30
            )
            
            assert storage.max_results == mock_config['max_file_size']
            assert storage.max_age_days == 30
    
    def test_store_chart_data(self, mock_chart_storage):
        """Test chart data storage."""
        chart_id = 'test_chart_123'
        chart_data = {
            'type': 'line',
            'data': [{'x': 1, 'y': 100}, {'x': 2, 'y': 200}],
            'metadata': {'title': 'Test Chart', 'created_at': datetime.now(timezone.utc).isoformat()}
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_json_dump:
                result = mock_chart_storage.store_chart_data(chart_id, chart_data)
                
                assert result['status'] == 'success'
                assert result['chart_id'] == chart_id
                assert result['file_path'] is not None
                mock_file.assert_called_once()
                mock_json_dump.assert_called_once()
    
    def test_retrieve_chart_data(self, mock_chart_storage):
        """Test chart data retrieval."""
        chart_id = 'test_chart_123'
        chart_data = {
            'type': 'line',
            'data': [{'x': 1, 'y': 100}, {'x': 2, 'y': 200}],
            'metadata': {'title': 'Test Chart'}
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(chart_data))):
            with patch('os.path.exists', return_value=True):
                retrieved_data = mock_chart_storage.retrieve_chart_data(chart_id)
                
                assert retrieved_data == chart_data
    
    def test_retrieve_chart_data_not_found(self, mock_chart_storage):
        """Test chart data retrieval when chart not found."""
        chart_id = 'non_existent_chart'
        
        with patch('os.path.exists', return_value=False):
            retrieved_data = mock_chart_storage.retrieve_chart_data(chart_id)
            
            assert retrieved_data is None
    
    def test_delete_chart_data(self, mock_chart_storage):
        """Test chart data deletion."""
        chart_id = 'test_chart_123'
        
        with patch('os.path.exists', return_value=True):
            with patch('os.remove') as mock_remove:
                result = mock_chart_storage.delete_chart_data(chart_id)
                
                assert result['status'] == 'success'
                assert result['chart_id'] == chart_id
                mock_remove.assert_called_once()
    
    def test_delete_chart_data_not_found(self, mock_chart_storage):
        """Test chart data deletion when chart not found."""
        chart_id = 'non_existent_chart'
        
        with patch('os.path.exists', return_value=False):
            result = mock_chart_storage.delete_chart_data(chart_id)
            
            assert result['status'] == 'not_found'
            assert result['chart_id'] == chart_id
    
    def test_list_charts(self, mock_chart_storage):
        """Test chart listing."""
        mock_files = ['chart1.json', 'chart2.json', 'chart3.json']
        
        with patch('os.listdir', return_value=mock_files):
            with patch('os.path.isfile', return_value=True):
                charts = mock_chart_storage.list_charts()
                
                assert len(charts) == 3
                assert 'chart1' in charts
                assert 'chart2' in charts
                assert 'chart3' in charts
    
    def test_list_charts_with_filter(self, mock_chart_storage):
        """Test chart listing with filter."""
        mock_files = ['chart1.json', 'chart2.json', 'other_file.txt']
        
        with patch('os.listdir', return_value=mock_files):
            with patch('os.path.isfile', return_value=True):
                charts = mock_chart_storage.list_charts(filter_func=lambda x: x.startswith('chart'))
                
                assert len(charts) == 2
                assert 'chart1' in charts
                assert 'chart2' in charts
                assert 'other_file' not in charts
    
    def test_get_chart_metadata(self, mock_chart_storage):
        """Test chart metadata retrieval."""
        chart_id = 'test_chart_123'
        chart_data = {
            'type': 'line',
            'data': [{'x': 1, 'y': 100}],
            'metadata': {
                'title': 'Test Chart',
                'created_at': '2024-01-01T00:00:00Z',
                'author': 'test_user'
            }
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(chart_data))):
            with patch('os.path.exists', return_value=True):
                metadata = mock_chart_storage.get_chart_metadata(chart_id)
                
                assert metadata == chart_data['metadata']
    
    def test_get_chart_metadata_not_found(self, mock_chart_storage):
        """Test chart metadata retrieval when chart not found."""
        chart_id = 'non_existent_chart'
        
        with patch('os.path.exists', return_value=False):
            metadata = mock_chart_storage.get_chart_metadata(chart_id)
            
            assert metadata is None
    
    def test_update_chart_metadata(self, mock_chart_storage):
        """Test chart metadata update."""
        chart_id = 'test_chart_123'
        original_data = {
            'type': 'line',
            'data': [{'x': 1, 'y': 100}],
            'metadata': {
                'title': 'Original Title',
                'created_at': '2024-01-01T00:00:00Z'
            }
        }
        
        new_metadata = {
            'title': 'Updated Title',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-02T00:00:00Z'
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(original_data))):
            with patch('os.path.exists', return_value=True):
                with patch('json.dump') as mock_json_dump:
                    result = mock_chart_storage.update_chart_metadata(chart_id, new_metadata)
                    
                    assert result['status'] == 'success'
                    assert result['chart_id'] == chart_id
                    mock_json_dump.assert_called_once()
    
    def test_compress_chart_data(self, mock_chart_storage):
        """Test chart data compression."""
        chart_data = {
            'type': 'line',
            'data': [{'x': i, 'y': i * 100} for i in range(1000)],  # Large dataset
            'metadata': {'title': 'Large Chart'}
        }
        
        compressed_data = mock_chart_storage._compress_data(chart_data)
        
        assert len(compressed_data) < len(json.dumps(chart_data))
        assert isinstance(compressed_data, bytes)
    
    def test_decompress_chart_data(self, mock_chart_storage):
        """Test chart data decompression."""
        original_data = {
            'type': 'line',
            'data': [{'x': i, 'y': i * 100} for i in range(1000)],
            'metadata': {'title': 'Large Chart'}
        }
        
        compressed_data = mock_chart_storage._compress_data(original_data)
        decompressed_data = mock_chart_storage._decompress_data(compressed_data)
        
        assert decompressed_data == original_data
    
    def test_validate_chart_data(self, mock_chart_storage):
        """Test chart data validation."""
        # Test valid chart data
        valid_data = {
            'type': 'line',
            'data': [{'x': 1, 'y': 100}],
            'metadata': {'title': 'Test Chart'}
        }
        
        assert mock_chart_storage._validate_chart_data(valid_data) is True
        
        # Test invalid chart data (missing required fields)
        invalid_data = {
            'type': 'line'
            # Missing data and metadata
        }
        
        assert mock_chart_storage._validate_chart_data(invalid_data) is False
    
    def test_get_storage_stats(self, mock_chart_storage):
        """Test storage statistics."""
        mock_files = ['chart1.json', 'chart2.json', 'chart3.json']
        
        with patch('os.listdir', return_value=mock_files):
            with patch('os.path.isfile', return_value=True):
                with patch('os.path.getsize', return_value=1024):
                    stats = mock_chart_storage.get_storage_stats()
                    
                    assert stats['total_charts'] == 3
                    assert stats['total_size'] == 3072  # 3 * 1024
                    assert stats['average_size'] == 1024
    
    def test_cleanup_old_charts(self, mock_chart_storage):
        """Test cleanup of old charts."""
        mock_files = ['chart1.json', 'chart2.json', 'chart3.json']
        
        with patch('os.listdir', return_value=mock_files):
            with patch('os.path.isfile', return_value=True):
                with patch('os.path.getmtime', side_effect=[1000, 2000, 3000]):  # Different modification times
                    with patch('os.remove') as mock_remove:
                        result = mock_chart_storage.cleanup_old_charts(max_age_days=1)
                        
                        assert result['status'] == 'success'
                        assert result['deleted_count'] >= 0
                        # Should remove files older than 1 day (assuming current time > 2000)
    
    def test_error_handling_invalid_chart_id(self, mock_chart_storage):
        """Test error handling with invalid chart ID."""
        # Test with None
        with pytest.raises(ValueError):
            mock_chart_storage.store_chart_data(None, {})
        
        # Test with empty string
        with pytest.raises(ValueError):
            mock_chart_storage.store_chart_data('', {})
        
        # Test with invalid characters
        with pytest.raises(ValueError):
            mock_chart_storage.store_chart_data('invalid/chart/id', {})
    
    def test_error_handling_invalid_chart_data(self, mock_chart_storage):
        """Test error handling with invalid chart data."""
        # Test with None
        with pytest.raises(ValueError):
            mock_chart_storage.store_chart_data('test_chart', None)
        
        # Test with invalid data structure
        with pytest.raises(ValueError):
            mock_chart_storage.store_chart_data('test_chart', 'invalid_data')
    
    def test_error_handling_file_operations(self, mock_chart_storage):
        """Test error handling during file operations."""
        chart_id = 'test_chart_123'
        chart_data = {'type': 'line', 'data': [], 'metadata': {}}
        
        # Test file write error
        with patch('builtins.open', side_effect=IOError("Write failed")):
            result = mock_chart_storage.store_chart_data(chart_id, chart_data)
            
            assert result['status'] == 'error'
            assert 'Write failed' in result['error']
        
        # Test file read error
        with patch('builtins.open', side_effect=IOError("Read failed")):
            with patch('os.path.exists', return_value=True):
                retrieved_data = mock_chart_storage.retrieve_chart_data(chart_id)
                
                assert retrieved_data is None
    
    def test_edge_case_very_large_chart_data(self, mock_chart_storage):
        """Test edge case with very large chart data."""
        # Create very large dataset
        large_data = {
            'type': 'line',
            'data': [{'x': i, 'y': i * 100} for i in range(100000)],  # 100k points
            'metadata': {'title': 'Very Large Chart'}
        }
        
        # Should handle large data gracefully
        with patch('builtins.open', mock_open()):
            with patch('json.dump'):
                result = mock_chart_storage.store_chart_data('large_chart', large_data)
                
                assert result['status'] == 'success'
    
    def test_edge_case_empty_chart_data(self, mock_chart_storage):
        """Test edge case with empty chart data."""
        empty_data = {
            'type': 'line',
            'data': [],
            'metadata': {'title': 'Empty Chart'}
        }
        
        # Should handle empty data gracefully
        with patch('builtins.open', mock_open()):
            with patch('json.dump'):
                result = mock_chart_storage.store_chart_data('empty_chart', empty_data)
                
                assert result['status'] == 'success'
    
    def test_edge_case_special_characters_in_chart_id(self, mock_chart_storage):
        """Test edge case with special characters in chart ID."""
        # Test with valid special characters
        chart_id = 'chart_with_underscores_and_numbers_123'
        chart_data = {'type': 'line', 'data': [], 'metadata': {}}
        
        with patch('builtins.open', mock_open()):
            with patch('json.dump'):
                result = mock_chart_storage.store_chart_data(chart_id, chart_data)
                
                assert result['status'] == 'success'
    
    def test_cache_functionality(self, mock_chart_storage):
        """Test chart data caching."""
        chart_id = 'cached_chart'
        chart_data = {'type': 'line', 'data': [], 'metadata': {}}
        
        # Store chart data
        with patch('builtins.open', mock_open()):
            with patch('json.dump'):
                mock_chart_storage.store_chart_data(chart_id, chart_data)
        
        # Retrieve from cache (should not hit file system)
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(chart_data))) as mock_file:
                retrieved_data = mock_chart_storage.retrieve_chart_data(chart_id)
                
                # Should not call open if data is cached
                # Note: This test assumes caching is implemented
                assert retrieved_data == chart_data


def mock_open(read_data=None):
    """Mock open function for testing."""
    from unittest.mock import mock_open as _mock_open
    return _mock_open(read_data=read_data)
