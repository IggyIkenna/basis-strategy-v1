"""
Unit tests for Results Store component.

Tests results storage functionality in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch
import json
from datetime import datetime


class TestResultsStore:
    """Test Results Store component in isolation."""
    
    def test_results_store_initialization(self, mock_config, mock_data_provider):
        """Test results store initializes correctly with config and data provider."""
        from backend.src.basis_strategy_v1.infrastructure.storage.results_store import ResultsStore
        
        results_store = ResultsStore(config=mock_config, data_provider=mock_data_provider)
        
        assert results_store.config == mock_config
        assert results_store.data_provider == mock_data_provider
        assert results_store.storage_path == mock_config.get('results_storage_path', 'results/')
    
    def test_store_backtest_results(self, mock_config, mock_data_provider):
        """Test storing backtest results with proper serialization."""
        from backend.src.basis_strategy_v1.infrastructure.storage.results_store import ResultsStore
        
        results_store = ResultsStore(config=mock_config, data_provider=mock_data_provider)
        
        backtest_results = {
            "strategy_mode": "pure_lending_usdt",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "total_return": 0.05,
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.02,
            "positions": [
                {"timestamp": "2024-01-01T00:00:00Z", "action": "open", "size": 1000.0}
            ]
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.makedirs'):
                result_id = results_store.store_backtest_results(backtest_results)
                
                assert result_id is not None
                mock_file.assert_called_once()
                written_data = json.loads(mock_file().write.call_args[0][0])
                assert written_data["strategy_mode"] == "pure_lending_usdt"
                assert written_data["total_return"] == 0.05
    
    def test_retrieve_backtest_results(self, mock_config, mock_data_provider):
        """Test retrieving backtest results by ID."""
        from backend.src.basis_strategy_v1.infrastructure.storage.results_store import ResultsStore
        
        results_store = ResultsStore(config=mock_config, data_provider=mock_data_provider)
        
        test_results = {
            "strategy_mode": "btc_basis",
            "total_return": 0.08,
            "sharpe_ratio": 1.5
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_results))):
            retrieved_results = results_store.retrieve_backtest_results("test_id")
            
            assert retrieved_results["strategy_mode"] == "btc_basis"
            assert retrieved_results["total_return"] == 0.08
            assert retrieved_results["sharpe_ratio"] == 1.5
    
    def test_store_live_trading_results(self, mock_config, mock_data_provider):
        """Test storing live trading results with real-time data."""
        from backend.src.basis_strategy_v1.infrastructure.storage.results_store import ResultsStore
        
        results_store = ResultsStore(config=mock_config, data_provider=mock_data_provider)
        
        live_results = {
            "strategy_mode": "eth_basis",
            "timestamp": datetime.now().isoformat(),
            "current_pnl": 1250.50,
            "active_positions": 3,
            "daily_trades": 15
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.makedirs'):
                result_id = results_store.store_live_trading_results(live_results)
                
                assert result_id is not None
                mock_file.assert_called_once()
                written_data = json.loads(mock_file().write.call_args[0][0])
                assert written_data["strategy_mode"] == "eth_basis"
                assert written_data["current_pnl"] == 1250.50
    
    def test_list_available_results(self, mock_config, mock_data_provider):
        """Test listing available results with filtering."""
        from backend.src.basis_strategy_v1.infrastructure.storage.results_store import ResultsStore
        
        results_store = ResultsStore(config=mock_config, data_provider=mock_data_provider)
        
        mock_files = [
            "results/pure_lending_usdt_2024-01-01.json",
            "results/btc_basis_2024-01-02.json",
            "results/eth_basis_2024-01-03.json"
        ]
        
        with patch('os.listdir', return_value=mock_files):
            with patch('os.path.isfile', return_value=True):
                results = results_store.list_available_results(strategy_mode="pure_lending_usdt")
                
                assert len(results) == 1
                assert "pure_lending_usdt" in results[0]
    
    def test_delete_results(self, mock_config, mock_data_provider):
        """Test deleting results by ID."""
        from backend.src.basis_strategy_v1.infrastructure.storage.results_store import ResultsStore
        
        results_store = ResultsStore(config=mock_config, data_provider=mock_data_provider)
        
        with patch('os.remove') as mock_remove:
            with patch('os.path.exists', return_value=True):
                success = results_store.delete_results("test_id")
                
                assert success is True
                mock_remove.assert_called_once()
    
    def test_export_results_csv(self, mock_config, mock_data_provider):
        """Test exporting results to CSV format."""
        from backend.src.basis_strategy_v1.infrastructure.storage.results_store import ResultsStore
        
        results_store = ResultsStore(config=mock_config, data_provider=mock_data_provider)
        
        test_results = {
            "positions": [
                {"timestamp": "2024-01-01T00:00:00Z", "action": "open", "size": 1000.0, "price": 3000.0},
                {"timestamp": "2024-01-01T01:00:00Z", "action": "close", "size": 1000.0, "price": 3010.0}
            ]
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.makedirs'):
                csv_path = results_store.export_results_csv("test_id", test_results)
                
                assert csv_path is not None
                mock_file.assert_called_once()
                # Verify CSV headers are written
                written_data = mock_file().write.call_args_list[0][0][0]
                assert "timestamp" in written_data
                assert "action" in written_data
                assert "size" in written_data
                assert "price" in written_data


def mock_open(read_data=None):
    """Mock open function for file operations."""
    mock_file = Mock()
    mock_file.read.return_value = read_data
    mock_file.__enter__.return_value = mock_file
    mock_file.__exit__.return_value = None
    return Mock(return_value=mock_file)
