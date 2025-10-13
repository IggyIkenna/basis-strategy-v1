"""
Unit tests for Live Service.

Tests the live service component in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from basis_strategy_v1.core.services.live_service import LiveTradingService, LiveTradingRequest


class TestLiveTradingRequest:
    """Test LiveTradingRequest dataclass."""
    
    def test_initialization(self):
        """Test LiveTradingRequest initialization."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        assert request.strategy_name == 'pure_lending'
        assert request.initial_capital == Decimal('10000.0')
        assert request.share_class == 'USDT'
        assert request.config_overrides == {}
        assert request.risk_limits == {}
        assert request.request_id is not None
    
    def test_validation_success(self):
        """Test successful request validation."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        errors = request.validate()
        assert len(errors) == 0
    
    def test_validation_missing_strategy_name(self):
        """Test validation with missing strategy name."""
        request = LiveTradingRequest(
            strategy_name='',
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        errors = request.validate()
        assert len(errors) > 0
        assert any('strategy_name is required' in error for error in errors)
    
    def test_validation_invalid_capital(self):
        """Test validation with invalid capital."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('0.0'),  # Zero capital
            share_class='USDT'
        )
        
        errors = request.validate()
        assert len(errors) > 0
        assert any('initial_capital must be positive' in error for error in errors)
    
    def test_validation_missing_share_class(self):
        """Test validation with missing share class."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class=''
        )
        
        errors = request.validate()
        assert len(errors) > 0
        assert any('share_class is required' in error for error in errors)


class TestLiveTradingService:
    """Test Live Trading Service component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for live service."""
        return {
            'execution_mode': 'live',
            'data_dir': 'test_data',
            'results_dir': 'test_results',
            'max_concurrent_strategies': 3
        }
    
    @pytest.fixture
    def mock_live_service(self, mock_config):
        """Create live service with mocked dependencies."""
        with patch('basis_strategy_v1.core.services.live_service.EventDrivenStrategyEngine') as mock_engine:
            with patch('basis_strategy_v1.core.services.live_service.DataProvider') as mock_provider:
                service = LiveTradingService()
                return service
    
    def test_initialization(self, mock_config):
        """Test live service initialization."""
        with patch('basis_strategy_v1.core.services.live_service.EventDrivenStrategyEngine'):
            with patch('basis_strategy_v1.core.services.live_service.DataProvider'):
                service = LiveTradingService()
                
                assert service is not None
    
    def test_create_live_config(self, mock_live_service):
        """Test live configuration creation."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        config = mock_live_service._create_live_config(request)
        
        assert config is not None
        assert config['strategy_name'] == 'pure_lending'
        assert config['initial_capital'] == Decimal('10000.0')
        assert config['share_class'] == 'USDT'
    
    def test_create_live_config_with_overrides(self, mock_live_service):
        """Test live configuration creation with overrides."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class='USDT',
            config_overrides={'max_position_size': 5000.0}
        )
        
        config = mock_live_service._create_live_config(request)
        
        assert config is not None
        assert config['strategy_name'] == 'pure_lending'
        assert config['max_position_size'] == 5000.0
    
    def test_validate_live_request_success(self, mock_live_service):
        """Test successful live request validation."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        errors = mock_live_service._validate_live_request(request)
        assert len(errors) == 0
    
    def test_validate_live_request_failure(self, mock_live_service):
        """Test live request validation failure."""
        request = LiveTradingRequest(
            strategy_name='',
            initial_capital=Decimal('0.0'),
            share_class=''
        )
        
        errors = mock_live_service._validate_live_request(request)
        assert len(errors) > 0
    
    def test_initialize_strategy_engine(self, mock_live_service):
        """Test strategy engine initialization."""
        config = {
            'strategy_name': 'pure_lending',
            'initial_capital': Decimal('10000.0'),
            'share_class': 'USDT'
        }
        
        engine = mock_live_service._initialize_strategy_engine(config)
        
        assert engine is not None
    
    def test_execute_live_trading_success(self, mock_live_service):
        """Test successful live trading execution."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        result = mock_live_service.execute_live_trading(request)
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['strategy_name'] == 'pure_lending'
        assert result['request_id'] == request.request_id
    
    def test_execute_live_trading_validation_failure(self, mock_live_service):
        """Test live trading execution with validation failure."""
        request = LiveTradingRequest(
            strategy_name='',
            initial_capital=Decimal('0.0'),
            share_class=''
        )
        
        result = mock_live_service.execute_live_trading(request)
        
        assert result is not None
        assert result['status'] == 'error'
        assert 'validation' in result['error'].lower()
    
    def test_execute_live_trading_engine_failure(self, mock_live_service):
        """Test live trading execution with engine failure."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        with patch.object(mock_live_service, '_initialize_strategy_engine', side_effect=Exception("Engine failed")):
            result = mock_live_service.execute_live_trading(request)
            
            assert result is not None
            assert result['status'] == 'error'
            assert 'engine' in result['error'].lower()
    
    def test_monitor_live_trading(self, mock_live_service):
        """Test live trading monitoring."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        result = mock_live_service.monitor_live_trading(request.request_id)
        
        assert result is not None
        assert result['status'] == 'monitoring'
        assert result['request_id'] == request.request_id
    
    def test_stop_live_trading(self, mock_live_service):
        """Test live trading stop."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        result = mock_live_service.stop_live_trading(request.request_id)
        
        assert result is not None
        assert result['status'] == 'stopped'
        assert result['request_id'] == request.request_id
    
    def test_get_live_trading_status(self, mock_live_service):
        """Test live trading status retrieval."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        status = mock_live_service.get_live_trading_status(request.request_id)
        
        assert status is not None
        assert status['request_id'] == request.request_id
        assert 'status' in status
    
    def test_get_live_trading_status_not_found(self, mock_live_service):
        """Test live trading status retrieval for non-existent request."""
        status = mock_live_service.get_live_trading_status('non-existent-id')
        
        assert status is None
    
    def test_emergency_stop(self, mock_live_service):
        """Test emergency stop functionality."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        result = mock_live_service.emergency_stop(request.request_id)
        
        assert result is not None
        assert result['status'] == 'emergency_stopped'
        assert result['request_id'] == request.request_id
    
    def test_risk_check(self, mock_live_service):
        """Test risk check functionality."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class='USDT',
            risk_limits={'max_drawdown': 0.1}
        )
        
        risk_result = mock_live_service._risk_check(request)
        
        assert risk_result is not None
        assert risk_result['passed'] is True
    
    def test_risk_check_failure(self, mock_live_service):
        """Test risk check failure."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('1000000.0'),  # Very large amount
            share_class='USDT',
            risk_limits={'max_capital': 100000.0}
        )
        
        risk_result = mock_live_service._risk_check(request)
        
        assert risk_result is not None
        assert risk_result['passed'] is False
    
    def test_environment_check(self, mock_live_service):
        """Test environment check functionality."""
        with patch.dict('os.environ', {'BASIS_LIVE_TRADING__ENABLED': 'true'}):
            result = mock_live_service._environment_check()
            assert result['enabled'] is True
    
    def test_environment_check_disabled(self, mock_live_service):
        """Test environment check when live trading is disabled."""
        with patch.dict('os.environ', {'BASIS_LIVE_TRADING__ENABLED': 'false'}):
            result = mock_live_service._environment_check()
            assert result['enabled'] is False
    
    def test_environment_check_read_only(self, mock_live_service):
        """Test environment check when in read-only mode."""
        with patch.dict('os.environ', {'BASIS_LIVE_TRADING__READ_ONLY': 'true'}):
            result = mock_live_service._environment_check()
            assert result['read_only'] is True
    
    def test_error_handling_invalid_request(self, mock_live_service):
        """Test error handling with invalid request."""
        with pytest.raises(ValueError):
            mock_live_service.execute_live_trading(None)
    
    def test_error_handling_missing_config(self, mock_live_service):
        """Test error handling with missing configuration."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        with patch.object(mock_live_service, '_create_live_config', side_effect=Exception("Config failed")):
            result = mock_live_service.execute_live_trading(request)
            
            assert result is not None
            assert result['status'] == 'error'
    
    def test_edge_case_very_small_capital(self, mock_live_service):
        """Test edge case with very small capital."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('0.01'),
            share_class='USDT'
        )
        
        result = mock_live_service.execute_live_trading(request)
        
        assert result is not None
        assert result['status'] == 'success'
    
    def test_edge_case_very_large_capital(self, mock_live_service):
        """Test edge case with very large capital."""
        request = LiveTradingRequest(
            strategy_name='pure_lending',
            initial_capital=Decimal('1000000.0'),
            share_class='USDT'
        )
        
        result = mock_live_service.execute_live_trading(request)
        
        assert result is not None
        assert result['status'] == 'success'
    
    def test_edge_case_special_characters_in_strategy_name(self, mock_live_service):
        """Test edge case with special characters in strategy name."""
        request = LiveTradingRequest(
            strategy_name='pure_lending_v2.0',
            initial_capital=Decimal('10000.0'),
            share_class='USDT'
        )
        
        result = mock_live_service.execute_live_trading(request)
        
        assert result is not None
        assert result['status'] == 'success'
    
    def test_performance_large_number_of_requests(self, mock_live_service):
        """Test performance with large number of requests."""
        requests = []
        for i in range(100):
            request = LiveTradingRequest(
                strategy_name=f'strategy_{i}',
                initial_capital=Decimal('1000.0'),
                share_class='USDT'
            )
            requests.append(request)
        
        results = []
        for request in requests:
            result = mock_live_service.execute_live_trading(request)
            results.append(result)
        
        assert len(results) == 100
        assert all(result['status'] == 'success' for result in results)
    
    def test_concurrent_live_trading_requests(self, mock_live_service):
        """Test concurrent live trading requests."""
        import asyncio
        
        async def execute_request(request):
            return mock_live_service.execute_live_trading(request)
        
        requests = [
            LiveTradingRequest(
                strategy_name='pure_lending',
                initial_capital=Decimal('10000.0'),
                share_class='USDT'
            ) for _ in range(5)
        ]
        
        async def run_concurrent():
            tasks = [execute_request(req) for req in requests]
            return await asyncio.gather(*tasks)
        
        results = asyncio.run(run_concurrent())
        
        assert len(results) == 5
        assert all(result['status'] == 'success' for result in results)
