"""
Unit tests for Backtest Service.

Tests the backtest service component in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from basis_strategy_v1.core.services.backtest_service import BacktestService, BacktestRequest


class TestBacktestRequest:
    """Test BacktestRequest dataclass."""
    
    def test_initialization(self):
        """Test BacktestRequest initialization."""
        request = BacktestRequest(
            strategy_name='pure_lending',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        assert request.strategy_name == 'pure_lending'
        assert request.start_date == datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert request.end_date == datetime(2024, 1, 31, tzinfo=timezone.utc)
        assert request.initial_capital == Decimal('10000.0')
        assert request.share_class == 'USDT'
        assert request.debug_mode is False
        assert request.config_overrides == {}
        assert request.request_id is not None
    
    def test_validation_success(self):
        """Test successful request validation."""
        request = BacktestRequest(
            strategy_name='pure_lending',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        errors = request.validate()
        assert len(errors) == 0
    
    def test_validation_missing_strategy_name(self):
        """Test validation with missing strategy name."""
        request = BacktestRequest(
            strategy_name='',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        errors = request.validate()
        assert len(errors) > 0
        assert any('strategy_name is required' in error for error in errors)
    
    def test_validation_invalid_date_range(self):
        """Test validation with invalid date range."""
        request = BacktestRequest(
            strategy_name='pure_lending',
            start_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 1, tzinfo=timezone.utc),  # End before start
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        errors = request.validate()
        assert len(errors) > 0
        assert any('end_date must be after start_date' in error for error in errors)
    
    def test_validation_invalid_capital(self):
        """Test validation with invalid capital."""
        request = BacktestRequest(
            strategy_name='pure_lending',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('0.0'),  # Zero capital
            share_class='USDT'
        )
        
        errors = request.validate()
        assert len(errors) > 0
        assert any('initial_capital must be positive' in error for error in errors)
    
    def test_validation_missing_share_class(self):
        """Test validation with missing share class."""
        request = BacktestRequest(
            strategy_name='pure_lending',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('10000.0'),
            share_class=''
        )
        
        errors = request.validate()
        assert len(errors) > 0
        assert any('share_class is required' in error for error in errors)


class TestBacktestService:
    """Test Backtest Service component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for backtest service."""
        return {
            'execution_mode': 'backtest',
            'data_dir': 'test_data',
            'results_dir': 'test_results',
            'max_concurrent_backtests': 5
        }
    
    @pytest.fixture
    def mock_backtest_service(self, mock_config):
        """Create backtest service with mocked dependencies."""
        with patch('basis_strategy_v1.core.services.backtest_service.EventDrivenStrategyEngine') as mock_engine:
            with patch('basis_strategy_v1.core.services.backtest_service.DataProvider') as mock_provider:
                with patch('basis_strategy_v1.core.services.backtest_service.StrategyFactory') as mock_factory:
                    service = BacktestService()
                    return service
    
    def test_initialization(self, mock_config):
        """Test backtest service initialization."""
        with patch('basis_strategy_v1.core.services.backtest_service.EventDrivenStrategyEngine'):
            with patch('basis_strategy_v1.core.services.backtest_service.DataProvider'):
                with patch('basis_strategy_v1.core.services.backtest_service.StrategyFactory'):
                    service = BacktestService()
                    
                    assert service is not None
    
    def test_create_backtest_config(self, mock_backtest_service):
        """Test backtest configuration creation."""
        request = BacktestRequest(
            strategy_name='pure_lending',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        config = mock_backtest_service._create_backtest_config(request)
        
        assert config['strategy_name'] == 'pure_lending'
        assert config['start_date'] == datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert config['end_date'] == datetime(2024, 1, 31, tzinfo=timezone.utc)
        assert config['initial_capital'] == Decimal('10000.0')
        assert config['share_class'] == 'USDT'
        assert config['execution_mode'] == 'backtest'
    
    def test_create_backtest_config_with_overrides(self, mock_backtest_service):
        """Test backtest configuration creation with overrides."""
        request = BacktestRequest(
            strategy_name='pure_lending',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('10000.0'),
            share_class='USDT',
            config_overrides={'risk_tolerance': 'high'}
        )
        
        config = mock_backtest_service._create_backtest_config(request)
        
        assert config['strategy_name'] == 'pure_lending'
        assert config['risk_tolerance'] == 'high'  # Override applied
    
    def test_validate_backtest_request_success(self, mock_backtest_service):
        """Test successful backtest request validation."""
        request = BacktestRequest(
            strategy_name='pure_lending',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        # Should not raise exception
        mock_backtest_service._validate_backtest_request(request)
    
    def test_validate_backtest_request_failure(self, mock_backtest_service):
        """Test backtest request validation failure."""
        request = BacktestRequest(
            strategy_name='',  # Invalid
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        with pytest.raises(ValueError, match="Backtest request validation failed"):
            mock_backtest_service._validate_backtest_request(request)
    
    def test_initialize_strategy_engine(self, mock_backtest_service):
        """Test strategy engine initialization."""
        config = {
            'strategy_name': 'pure_lending',
            'start_date': datetime(2024, 1, 1, tzinfo=timezone.utc),
            'end_date': datetime(2024, 1, 31, tzinfo=timezone.utc),
            'initial_capital': Decimal('10000.0'),
            'share_class': 'USDT',
            'execution_mode': 'backtest'
        }
        
        with patch('basis_strategy_v1.core.services.backtest_service.EventDrivenStrategyEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            
            engine = mock_backtest_service._initialize_strategy_engine(config)
            
            assert engine == mock_engine
            mock_engine_class.assert_called_once()
    
    def test_execute_backtest_success(self, mock_backtest_service):
        """Test successful backtest execution."""
        request = BacktestRequest(
            strategy_name='pure_lending',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        with patch.object(mock_backtest_service, '_validate_backtest_request'):
            with patch.object(mock_backtest_service, '_create_backtest_config') as mock_create_config:
                with patch.object(mock_backtest_service, '_initialize_strategy_engine') as mock_init_engine:
                    with patch.object(mock_backtest_service, '_process_backtest_results') as mock_process:
                        # Mock successful execution
                        mock_engine = Mock()
                        mock_engine.run_backtest.return_value = {'status': 'success', 'pnl': 100.0}
                        mock_init_engine.return_value = mock_engine
                        mock_process.return_value = {'final_pnl': 100.0, 'total_return': 0.01}
                        
                        result = mock_backtest_service.execute_backtest(request)
                        
                        assert result['status'] == 'success'
                        assert result['request_id'] == request.request_id
                        assert 'execution_time' in result
                        assert 'results' in result
    
    def test_execute_backtest_validation_failure(self, mock_backtest_service):
        """Test backtest execution with validation failure."""
        request = BacktestRequest(
            strategy_name='',  # Invalid
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        with patch.object(mock_backtest_service, '_validate_backtest_request') as mock_validate:
            mock_validate.side_effect = ValueError("Validation failed")
            
            result = mock_backtest_service.execute_backtest(request)
            
            assert result['status'] == 'failed'
            assert result['error'] == 'Validation failed'
            assert result['request_id'] == request.request_id
    
    def test_execute_backtest_engine_failure(self, mock_backtest_service):
        """Test backtest execution with engine failure."""
        request = BacktestRequest(
            strategy_name='pure_lending',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        with patch.object(mock_backtest_service, '_validate_backtest_request'):
            with patch.object(mock_backtest_service, '_create_backtest_config'):
                with patch.object(mock_backtest_service, '_initialize_strategy_engine') as mock_init_engine:
                    # Mock engine failure
                    mock_engine = Mock()
                    mock_engine.run_backtest.side_effect = Exception("Engine failed")
                    mock_init_engine.return_value = mock_engine
                    
                    result = mock_backtest_service.execute_backtest(request)
                    
                    assert result['status'] == 'failed'
                    assert 'Engine failed' in result['error']
    
    def test_process_backtest_results(self, mock_backtest_service):
        """Test backtest results processing."""
        raw_results = {
            'status': 'success',
            'pnl': 100.0,
            'trades': [
                {'timestamp': datetime(2024, 1, 15, tzinfo=timezone.utc), 'pnl': 50.0},
                {'timestamp': datetime(2024, 1, 30, tzinfo=timezone.utc), 'pnl': 50.0}
            ],
            'final_balance': 10100.0
        }
        
        processed_results = mock_backtest_service._process_backtest_results(raw_results)
        
        assert processed_results['final_pnl'] == 100.0
        assert processed_results['total_return'] == 0.01  # 100/10000
        assert processed_results['trade_count'] == 2
        assert 'execution_summary' in processed_results
    
    def test_get_backtest_status(self, mock_backtest_service):
        """Test backtest status retrieval."""
        request_id = 'test_request_123'
        
        # Mock active backtest
        mock_backtest_service.active_backtests[request_id] = {
            'status': 'running',
            'start_time': datetime.now(timezone.utc),
            'progress': 50
        }
        
        status = mock_backtest_service.get_backtest_status(request_id)
        
        assert status['request_id'] == request_id
        assert status['status'] == 'running'
        assert status['progress'] == 50
    
    def test_get_backtest_status_not_found(self, mock_backtest_service):
        """Test backtest status retrieval for non-existent request."""
        request_id = 'non_existent_request'
        
        status = mock_backtest_service.get_backtest_status(request_id)
        
        assert status['request_id'] == request_id
        assert status['status'] == 'not_found'
    
    def test_cancel_backtest(self, mock_backtest_service):
        """Test backtest cancellation."""
        request_id = 'test_request_123'
        
        # Mock active backtest
        mock_backtest_service.active_backtests[request_id] = {
            'status': 'running',
            'start_time': datetime.now(timezone.utc),
            'progress': 50
        }
        
        result = mock_backtest_service.cancel_backtest(request_id)
        
        assert result['status'] == 'cancelled'
        assert result['request_id'] == request_id
        assert request_id not in mock_backtest_service.active_backtests
    
    def test_cancel_backtest_not_found(self, mock_backtest_service):
        """Test backtest cancellation for non-existent request."""
        request_id = 'non_existent_request'
        
        result = mock_backtest_service.cancel_backtest(request_id)
        
        assert result['status'] == 'not_found'
        assert result['request_id'] == request_id
    
    def test_get_backtest_history(self, mock_backtest_service):
        """Test backtest history retrieval."""
        # Mock completed backtests
        mock_backtest_service.completed_backtests = [
            {
                'request_id': 'test_1',
                'status': 'success',
                'completed_at': datetime(2024, 1, 1, tzinfo=timezone.utc)
            },
            {
                'request_id': 'test_2',
                'status': 'failed',
                'completed_at': datetime(2024, 1, 2, tzinfo=timezone.utc)
            }
        ]
        
        history = mock_backtest_service.get_backtest_history(limit=10)
        
        assert len(history['backtests']) == 2
        assert history['backtests'][0]['request_id'] == 'test_1'
        assert history['backtests'][1]['request_id'] == 'test_2'
    
    def test_error_handling_invalid_strategy(self, mock_backtest_service):
        """Test error handling with invalid strategy name."""
        request = BacktestRequest(
            strategy_name='invalid_strategy',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        with patch.object(mock_backtest_service, '_validate_backtest_request'):
            with patch.object(mock_backtest_service, '_create_backtest_config'):
                with patch.object(mock_backtest_service, '_initialize_strategy_engine') as mock_init_engine:
                    mock_init_engine.side_effect = ValueError("Invalid strategy")
                    
                    result = mock_backtest_service.execute_backtest(request)
                    
                    assert result['status'] == 'failed'
                    assert 'Invalid strategy' in result['error']
    
    def test_edge_case_very_short_backtest(self, mock_backtest_service):
        """Test edge case with very short backtest period."""
        request = BacktestRequest(
            strategy_name='pure_lending',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 2, tzinfo=timezone.utc),  # 1 day
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        with patch.object(mock_backtest_service, '_validate_backtest_request'):
            with patch.object(mock_backtest_service, '_create_backtest_config'):
                with patch.object(mock_backtest_service, '_initialize_strategy_engine') as mock_init_engine:
                    mock_engine = Mock()
                    mock_engine.run_backtest.return_value = {'status': 'success', 'pnl': 0.0}
                    mock_init_engine.return_value = mock_engine
                    
                    result = mock_backtest_service.execute_backtest(request)
                    
                    assert result['status'] == 'success'
    
    def test_edge_case_very_long_backtest(self, mock_backtest_service):
        """Test edge case with very long backtest period."""
        request = BacktestRequest(
            strategy_name='pure_lending',
            start_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 12, 31, tzinfo=timezone.utc),  # 5 years
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        with patch.object(mock_backtest_service, '_validate_backtest_request'):
            with patch.object(mock_backtest_service, '_create_backtest_config'):
                with patch.object(mock_backtest_service, '_initialize_strategy_engine') as mock_init_engine:
                    mock_engine = Mock()
                    mock_engine.run_backtest.return_value = {'status': 'success', 'pnl': 5000.0}
                    mock_init_engine.return_value = mock_engine
                    
                    result = mock_backtest_service.execute_backtest(request)
                    
                    assert result['status'] == 'success'
    
    def test_edge_case_zero_capital(self, mock_backtest_service):
        """Test edge case with zero initial capital."""
        request = BacktestRequest(
            strategy_name='pure_lending',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            initial_capital=Decimal('0.0'),  # Zero capital
            share_class='USDT'
        )
        
        with patch.object(mock_backtest_service, '_validate_backtest_request') as mock_validate:
            mock_validate.side_effect = ValueError("initial_capital must be positive")
            
            result = mock_backtest_service.execute_backtest(request)
            
            assert result['status'] == 'failed'
            assert 'initial_capital must be positive' in result['error']
