"""Tests for Live Trading Service and Backtest Service.

Tests the LiveTradingService and BacktestService orchestration of trading strategies.
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../backend/src'))

from basis_strategy_v1.core.services.live_service import (
    LiveTradingService,
    LiveTradingRequest,
    ERROR_CODES
)
from basis_strategy_v1.core.services.backtest_service import (
    BacktestService,
    BacktestRequest,
    ERROR_CODES as BACKTEST_ERROR_CODES
)


class TestLiveTradingRequest:
    """Test LiveTradingRequest validation and creation."""
    
    def test_create_valid_request(self):
        """Test creating a valid live trading request."""
        request = LiveTradingRequest(
            strategy_name="pure_lending",
            initial_capital=Decimal("100000"),
            share_class="USDT"
        )
        
        assert request.strategy_name == "pure_lending"
        assert request.initial_capital == Decimal("100000")
        assert request.share_class == "USDT"
        assert request.config_overrides == {}
        assert request.risk_limits == {}
        assert request.request_id is not None
    
    def test_validate_valid_request(self):
        """Test validation of a valid request."""
        request = LiveTradingRequest(
            strategy_name="pure_lending",
            initial_capital=Decimal("100000"),
            share_class="USDT"
        )
        
        errors = request.validate()
        assert errors == []
    
    def test_validate_missing_strategy_name(self):
        """Test validation fails with missing strategy name."""
        request = LiveTradingRequest(
            strategy_name="",
            initial_capital=Decimal("100000"),
            share_class="USDT"
        )
        
        errors = request.validate()
        assert "strategy_name is required" in errors
    
    def test_validate_invalid_initial_capital(self):
        """Test validation fails with invalid initial capital."""
        request = LiveTradingRequest(
            strategy_name="pure_lending",
            initial_capital=Decimal("0"),
            share_class="USDT"
        )
        
        errors = request.validate()
        assert "initial_capital must be positive" in errors
    
    def test_validate_invalid_share_class(self):
        """Test validation fails with invalid share class."""
        request = LiveTradingRequest(
            strategy_name="pure_lending",
            initial_capital=Decimal("100000"),
            share_class="BTC"
        )
        
        errors = request.validate()
        assert "share_class must be 'USDT' or 'ETH'" in errors
    
    def test_validate_risk_limits(self):
        """Test validation of risk limits."""
        # Valid risk limits
        request = LiveTradingRequest(
            strategy_name="pure_lending",
            initial_capital=Decimal("100000"),
            share_class="USDT",
            risk_limits={
                "max_drawdown": 0.2,
                "max_position_size": 50000
            }
        )
        
        errors = request.validate()
        assert errors == []
        
        # Invalid max_drawdown
        request.risk_limits["max_drawdown"] = 1.5
        errors = request.validate()
        assert "max_drawdown must be between 0 and 1" in errors
        
        # Invalid max_position_size
        request.risk_limits["max_drawdown"] = 0.2
        request.risk_limits["max_position_size"] = -1000
        errors = request.validate()
        assert "max_position_size must be positive" in errors


class TestLiveTradingService:
    """Test LiveTradingService functionality."""
    
    @pytest.fixture
    def service(self):
        """Create a LiveTradingService instance."""
        return LiveTradingService()
    
    @pytest.fixture
    def valid_request(self):
        """Create a valid live trading request."""
        return LiveTradingRequest(
            strategy_name="pure_lending",
            initial_capital=Decimal("100000"),
            share_class="USDT"
        )
    
    def test_create_request(self, service):
        """Test creating a live trading request."""
        request = service.create_request(
            strategy_name="pure_lending",
            initial_capital=Decimal("100000"),
            share_class="USDT",
            config_overrides={"test": "value"},
            risk_limits={"max_drawdown": 0.2}
        )
        
        assert isinstance(request, LiveTradingRequest)
        assert request.strategy_name == "pure_lending"
        assert request.initial_capital == Decimal("100000")
        assert request.share_class == "USDT"
        assert request.config_overrides == {"test": "value"}
        assert request.risk_limits == {"max_drawdown": 0.2}
    
    @pytest.mark.asyncio
    @patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader')
    @patch('backend.src.basis_strategy_v1.core.services.live_service.EventDrivenStrategyEngine')
    async def test_start_live_trading_success(self, mock_engine_class, mock_config_loader, service, valid_request):
        """Test successful start of live trading."""
        # Mock config loader
        mock_loader = Mock()
        mock_loader.get_complete_config.return_value = {
            'mode': 'pure_lending',
            'share_class': 'USDT',
            'initial_capital': 100000
        }
        mock_config_loader.return_value = mock_loader
        
        # Mock strategy engine
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        
        # Start live trading
        request_id = await service.start_live_trading(valid_request)
        
        # Verify request was stored
        assert request_id in service.running_strategies
        strategy_info = service.running_strategies[request_id]
        assert strategy_info['request'] == valid_request
        assert strategy_info['status'] == 'starting'
        assert strategy_info['strategy_engine'] == mock_engine
        
        # Verify monitoring task was created
        assert request_id in service.monitoring_tasks
    
    @pytest.mark.asyncio
    async def test_start_live_trading_validation_error(self, service):
        """Test start live trading with validation error."""
        invalid_request = LiveTradingRequest(
            strategy_name="",
            initial_capital=Decimal("100000"),
            share_class="USDT"
        )
        
        with pytest.raises(ValueError, match="Invalid request"):
            await service.start_live_trading(invalid_request)
    
    @pytest.mark.asyncio
    @patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader')
    async def test_start_live_trading_config_error(self, mock_config_loader, service, valid_request):
        """Test start live trading with config creation error."""
        # Mock config loader to raise exception
        mock_config_loader.side_effect = Exception("Config error")
        
        with pytest.raises(Exception, match="Config error"):
            await service.start_live_trading(valid_request)
    
    @pytest.mark.asyncio
    async def test_stop_live_trading_success(self, service, valid_request):
        """Test successful stop of live trading."""
        # Add a running strategy
        mock_engine = Mock()
        service.running_strategies[valid_request.request_id] = {
            'request': valid_request,
            'strategy_engine': mock_engine,
            'status': 'running'
        }
        
        # Stop the strategy
        result = await service.stop_live_trading(valid_request.request_id)
        
        assert result is True
        assert valid_request.request_id not in service.running_strategies
        assert valid_request.request_id in service.completed_strategies
        
        # Verify strategy engine was stopped
        mock_engine.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_live_trading_not_found(self, service):
        """Test stop live trading with non-existent request ID."""
        result = await service.stop_live_trading("non-existent-id")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_status_running(self, service, valid_request):
        """Test getting status of running strategy."""
        # Add a running strategy
        service.running_strategies[valid_request.request_id] = {
            'request': valid_request,
            'status': 'running',
            'started_at': datetime.utcnow(),
            'last_heartbeat': datetime.utcnow(),
            'total_trades': 5,
            'total_pnl': 1000.0,
            'current_drawdown': -0.05,
            'risk_breaches': []
        }
        
        status = await service.get_status(valid_request.request_id)
        
        assert status['status'] == 'running'
        assert status['total_trades'] == 5
        assert status['total_pnl'] == 1000.0
        assert status['current_drawdown'] == -0.05
    
    @pytest.mark.asyncio
    async def test_get_status_completed(self, service, valid_request):
        """Test getting status of completed strategy."""
        # Add a completed strategy
        service.completed_strategies[valid_request.request_id] = {
            'request': valid_request,
            'status': 'completed',
            'started_at': datetime.utcnow() - timedelta(hours=1),
            'completed_at': datetime.utcnow(),
            'total_trades': 10,
            'total_pnl': 2000.0,
            'current_drawdown': -0.03,
            'risk_breaches': []
        }
        
        status = await service.get_status(valid_request.request_id)
        
        assert status['status'] == 'completed'
        assert status['total_trades'] == 10
        assert status['total_pnl'] == 2000.0
        assert 'completed_at' in status
    
    @pytest.mark.asyncio
    async def test_get_status_not_found(self, service):
        """Test getting status of non-existent strategy."""
        status = await service.get_status("non-existent-id")
        assert status['status'] == 'not_found'
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, service, valid_request):
        """Test getting performance metrics."""
        # Add a running strategy
        service.running_strategies[valid_request.request_id] = {
            'request': valid_request,
            'strategy_engine': Mock(),
            'total_pnl': 1500.0,
            'total_trades': 5,
            'current_drawdown': -0.05,
            'started_at': datetime.utcnow() - timedelta(hours=2),
            'last_heartbeat': datetime.utcnow()
        }
        
        # Mock strategy engine status
        mock_engine = service.running_strategies[valid_request.request_id]['strategy_engine']
        mock_engine.get_status = AsyncMock(return_value={'mode': 'pure_lending'})
        
        metrics = await service.get_performance_metrics(valid_request.request_id)
        
        assert metrics is not None
        assert metrics['initial_capital'] == 100000.0
        assert metrics['current_value'] == 101500.0  # 100000 + 1500
        assert metrics['total_pnl'] == 1500.0
        assert metrics['return_pct'] == 1.5  # (1500/100000) * 100
        assert metrics['uptime_hours'] > 0
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics_not_found(self, service):
        """Test getting performance metrics for non-existent strategy."""
        metrics = await service.get_performance_metrics("non-existent-id")
        assert metrics is None
    
    @pytest.mark.asyncio
    async def test_check_risk_limits_no_limits(self, service, valid_request):
        """Test risk check with no limits configured."""
        service.running_strategies[valid_request.request_id] = {
            'request': valid_request,
            'current_drawdown': -0.1
        }
        
        result = await service.check_risk_limits(valid_request.request_id)
        
        assert result['status'] == 'no_limits'
        assert 'No risk limits configured' in result['message']
    
    @pytest.mark.asyncio
    async def test_check_risk_limits_within_limits(self, service):
        """Test risk check within limits."""
        request = LiveTradingRequest(
            strategy_name="pure_lending",
            initial_capital=Decimal("100000"),
            share_class="USDT",
            risk_limits={"max_drawdown": 0.2}
        )
        
        service.running_strategies[request.request_id] = {
            'request': request,
            'current_drawdown': -0.1  # 10% drawdown, limit is 20%
        }
        
        result = await service.check_risk_limits(request.request_id)
        
        assert result['status'] == 'within_limits'
        assert result['action_required'] is False
        assert result['breaches'] == []
    
    @pytest.mark.asyncio
    async def test_check_risk_limits_breach_detected(self, service):
        """Test risk check with breach detected."""
        request = LiveTradingRequest(
            strategy_name="pure_lending",
            initial_capital=Decimal("100000"),
            share_class="USDT",
            risk_limits={"max_drawdown": 0.15}
        )
        
        service.running_strategies[request.request_id] = {
            'request': request,
            'current_drawdown': -0.2,  # 20% drawdown, limit is 15%
            'risk_breaches': []
        }
        
        result = await service.check_risk_limits(request.request_id)
        
        assert result['status'] == 'breach_detected'
        assert result['action_required'] is True
        assert len(result['breaches']) == 1
        assert result['breaches'][0]['type'] == 'max_drawdown'
        assert result['breaches'][0]['limit'] == 0.15
        assert result['breaches'][0]['current'] == 0.2
    
    @pytest.mark.asyncio
    async def test_emergency_stop(self, service, valid_request):
        """Test emergency stop functionality."""
        # Add a running strategy
        mock_engine = Mock()
        service.running_strategies[valid_request.request_id] = {
            'request': valid_request,
            'strategy_engine': mock_engine,
            'status': 'running'
        }
        
        # Emergency stop
        result = await service.emergency_stop(valid_request.request_id, "Test emergency")
        
        assert result is True
        assert valid_request.request_id not in service.running_strategies
        assert valid_request.request_id in service.completed_strategies
        
        # Verify emergency stop info was added
        completed_strategy = service.completed_strategies[valid_request.request_id]
        assert 'emergency_stop' in completed_strategy
        assert completed_strategy['emergency_stop']['reason'] == "Test emergency"
    
    @pytest.mark.asyncio
    async def test_get_all_running_strategies(self, service):
        """Test getting all running strategies."""
        # Add multiple running strategies
        request1 = LiveTradingRequest("pure_lending", Decimal("100000"), "USDT")
        request2 = LiveTradingRequest("eth_leveraged", Decimal("50"), "ETH")
        
        service.running_strategies[request1.request_id] = {
            'request': request1,
            'status': 'running',
            'started_at': datetime.utcnow(),
            'last_heartbeat': datetime.utcnow()
        }
        
        service.running_strategies[request2.request_id] = {
            'request': request2,
            'status': 'running',
            'started_at': datetime.utcnow(),
            'last_heartbeat': datetime.utcnow()
        }
        
        strategies = await service.get_all_running_strategies()
        
        assert len(strategies) == 2
        strategy_names = [s['strategy_name'] for s in strategies]
        assert 'pure_lending' in strategy_names
        assert 'eth_leveraged' in strategy_names
    
    @pytest.mark.asyncio
    async def test_health_check(self, service):
        """Test health check functionality."""
        # Add strategies with different health statuses
        request1 = LiveTradingRequest("pure_lending", Decimal("100000"), "USDT")
        request2 = LiveTradingRequest("eth_leveraged", Decimal("50"), "ETH")
        
        # Healthy strategy (recent heartbeat)
        service.running_strategies[request1.request_id] = {
            'request': request1,
            'last_heartbeat': datetime.utcnow()
        }
        
        # Unhealthy strategy (old heartbeat)
        service.running_strategies[request2.request_id] = {
            'request': request2,
            'last_heartbeat': datetime.utcnow() - timedelta(minutes=10)
        }
        
        health = await service.health_check()
        
        assert health['total_strategies'] == 2
        assert health['healthy_strategies'] == 1
        assert health['unhealthy_strategies'] == 1
        assert len(health['strategies']) == 2
        
        # Check individual strategy health
        healthy_strategy = next(s for s in health['strategies'] if s['strategy_name'] == 'pure_lending')
        unhealthy_strategy = next(s for s in health['strategies'] if s['strategy_name'] == 'eth_leveraged')
        
        assert healthy_strategy['is_healthy'] is True
        assert unhealthy_strategy['is_healthy'] is False
    
    def test_map_strategy_to_mode(self, service):
        """Test strategy name to mode mapping."""
        assert service._map_strategy_to_mode("pure_lending") == "pure_lending"
        assert service._map_strategy_to_mode("btc_basis") == "btc_basis"
        assert service._map_strategy_to_mode("eth_leveraged") == "eth_leveraged"
        assert service._map_strategy_to_mode("usdt_market_neutral") == "usdt_market_neutral"
        assert service._map_strategy_to_mode("unknown_strategy") == "pure_lending"  # default
    
    def test_deep_merge(self, service):
        """Test deep merge functionality."""
        base = {
            'level1': {
                'level2': {
                    'value1': 'original',
                    'value2': 'keep'
                }
            },
            'other': 'unchanged'
        }
        
        override = {
            'level1': {
                'level2': {
                    'value1': 'updated'
                }
            },
            'new_key': 'added'
        }
        
        result = service._deep_merge(base, override)
        
        assert result['level1']['level2']['value1'] == 'updated'
        assert result['level1']['level2']['value2'] == 'keep'
        assert result['other'] == 'unchanged'
        assert result['new_key'] == 'added'


class TestErrorCodes:
    """Test error code constants."""
    
    def test_error_codes_defined(self):
        """Test that all error codes are defined."""
        expected_codes = [
            'LT-001', 'LT-002', 'LT-003', 'LT-004',
            'LT-005', 'LT-006', 'LT-007'
        ]
        
        for code in expected_codes:
            assert code in ERROR_CODES
            assert ERROR_CODES[code] is not None
            assert len(ERROR_CODES[code]) > 0


@pytest.mark.asyncio
class TestAsyncIntegration:
    """Test async integration scenarios."""
    
    @pytest.fixture
    def service(self):
        """Create a LiveTradingService instance."""
        return LiveTradingService()
    
    async def test_concurrent_strategy_management(self, service):
        """Test managing multiple strategies concurrently."""
        # Create multiple requests
        requests = [
            LiveTradingRequest(f"strategy_{i}", Decimal("100000"), "USDT")
            for i in range(3)
        ]
        
        # Start all strategies concurrently
        tasks = []
        for request in requests:
            task = asyncio.create_task(service.start_live_trading(request))
            tasks.append(task)
        
        # Wait for all to complete (they will fail due to mocking, but that's OK)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all tasks completed (even if with exceptions)
        assert len(results) == 3
        
        # Verify no strategies are running (due to config errors)
        assert len(service.running_strategies) == 0
    
    async def test_health_check_with_no_strategies(self, service):
        """Test health check with no running strategies."""
        health = await service.health_check()
        
        assert health['total_strategies'] == 0
        assert health['healthy_strategies'] == 0
        assert health['unhealthy_strategies'] == 0
        assert health['strategies'] == []


# ============================================================================
# BACKTEST SERVICE TESTS
# ============================================================================

class TestBacktestRequest:
    """Test BacktestRequest validation and creation."""
    
    def test_create_valid_request(self):
        """Test creating a valid backtest request."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        request = BacktestRequest(
            strategy_name="pure_lending",
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal("100000"),
            share_class="USDT"
        )
        
        assert request.strategy_name == "pure_lending"
        assert request.start_date == start_date
        assert request.end_date == end_date
        assert request.initial_capital == Decimal("100000")
        assert request.share_class == "USDT"
        assert request.config_overrides == {}
        assert request.request_id is not None
    
    def test_validate_valid_request(self):
        """Test validation of a valid request."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        request = BacktestRequest(
            strategy_name="pure_lending",
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal("100000"),
            share_class="USDT"
        )
        
        errors = request.validate()
        assert errors == []
    
    def test_validate_missing_strategy_name(self):
        """Test validation fails with missing strategy name."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        request = BacktestRequest(
            strategy_name="",
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal("100000"),
            share_class="USDT"
        )
        
        errors = request.validate()
        assert "strategy_name is required" in errors
    
    def test_validate_invalid_initial_capital(self):
        """Test validation fails with invalid initial capital."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        request = BacktestRequest(
            strategy_name="pure_lending",
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal("0"),
            share_class="USDT"
        )
        
        errors = request.validate()
        assert "initial_capital must be positive" in errors
    
    def test_validate_invalid_date_range(self):
        """Test validation fails with invalid date range."""
        start_date = datetime(2024, 1, 31)
        end_date = datetime(2024, 1, 1)  # End before start
        
        request = BacktestRequest(
            strategy_name="pure_lending",
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal("100000"),
            share_class="USDT"
        )
        
        errors = request.validate()
        assert "end_date must be after start_date" in errors
    
    def test_validate_invalid_share_class(self):
        """Test validation fails with invalid share class."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        request = BacktestRequest(
            strategy_name="pure_lending",
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal("100000"),
            share_class="BTC"
        )
        
        errors = request.validate()
        assert "share_class must be 'USDT' or 'ETH'" in errors
    
    def test_validate_with_config_overrides(self):
        """Test validation with config overrides."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        request = BacktestRequest(
            strategy_name="pure_lending",
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal("100000"),
            share_class="USDT",
            config_overrides={"target_apy": 0.06}
        )
        
        errors = request.validate()
        assert errors == []
        assert request.config_overrides == {"target_apy": 0.06}


class TestBacktestService:
    """Test BacktestService functionality."""
    
    @pytest.fixture
    def service(self):
        """Create a BacktestService instance."""
        return BacktestService()
    
    @pytest.fixture
    def valid_request(self):
        """Create a valid backtest request."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        return BacktestRequest(
            strategy_name="pure_lending",
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal("100000"),
            share_class="USDT"
        )
    
    def test_create_request(self, service):
        """Test creating a backtest request."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        request = service.create_request(
            strategy_name="pure_lending",
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal("100000"),
            share_class="USDT",
            config_overrides={"target_apy": 0.06}
        )
        
        assert isinstance(request, BacktestRequest)
        assert request.strategy_name == "pure_lending"
        assert request.start_date == start_date
        assert request.end_date == end_date
        assert request.initial_capital == Decimal("100000")
        assert request.share_class == "USDT"
        assert request.config_overrides == {"target_apy": 0.06}
    
    @pytest.mark.asyncio
    @patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader')
    @patch('backend.src.basis_strategy_v1.core.services.backtest_service.EventDrivenStrategyEngine')
    async def test_run_backtest_success(self, mock_engine_class, mock_config_loader, service, valid_request):
        """Test successful backtest execution."""
        # Mock config loader
        mock_loader = Mock()
        mock_loader.get_complete_config.return_value = {
            'mode': 'pure_lending',
            'share_class': 'USDT',
            'initial_capital': 100000,
            'target_apy': 0.05
        }
        mock_config_loader.return_value = mock_loader
        
        # Mock strategy engine
        mock_engine = Mock()
        mock_engine.run_backtest = AsyncMock(return_value={
            'final_value': 105000,
            'total_return': 0.05,
            'annualized_return': 0.05,
            'sharpe_ratio': 1.2,
            'max_drawdown': -0.02,
            'total_trades': 10,
            'total_fees': 100.0
        })
        mock_engine_class.return_value = mock_engine
        
        # Run backtest
        request_id = await service.run_backtest(valid_request)
        
        # Verify request was stored
        assert request_id in service.running_backtests
        backtest_info = service.running_backtests[request_id]
        assert backtest_info['request'] == valid_request
        assert backtest_info['status'] == 'running'
        assert backtest_info['strategy_engine'] == mock_engine
    
    @pytest.mark.asyncio
    async def test_run_backtest_validation_error(self, service):
        """Test backtest with validation error."""
        start_date = datetime(2024, 1, 31)
        end_date = datetime(2024, 1, 1)  # Invalid date range
        
        invalid_request = BacktestRequest(
            strategy_name="pure_lending",
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal("100000"),
            share_class="USDT"
        )
        
        with pytest.raises(ValueError, match="Invalid request"):
            await service.run_backtest(invalid_request)
    
    @pytest.mark.asyncio
    @patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader')
    async def test_run_backtest_config_error(self, mock_config_loader, service, valid_request):
        """Test backtest with config creation error."""
        # Mock config loader to raise exception
        mock_config_loader.side_effect = Exception("Config error")
        
        with pytest.raises(Exception, match="Config error"):
            await service.run_backtest(valid_request)
    
    @pytest.mark.asyncio
    async def test_get_status_running(self, service, valid_request):
        """Test getting status of running backtest."""
        # Add a running backtest
        service.running_backtests[valid_request.request_id] = {
            'request': valid_request,
            'status': 'running',
            'started_at': datetime.utcnow(),
            'progress': 50
        }
        
        status = await service.get_status(valid_request.request_id)
        
        assert status['status'] == 'running'
        assert status['progress'] == 50
        assert 'started_at' in status
    
    @pytest.mark.asyncio
    async def test_get_status_completed(self, service, valid_request):
        """Test getting status of completed backtest."""
        # Add a completed backtest
        service.completed_backtests[valid_request.request_id] = {
            'request_id': valid_request.request_id,
            'strategy_name': 'pure_lending',
            'start_date': valid_request.start_date,
            'end_date': valid_request.end_date,
            'initial_capital': valid_request.initial_capital,
            'final_value': 105000,
            'total_return': 0.05,
            'completed_at': datetime.utcnow()
        }
        
        status = await service.get_status(valid_request.request_id)
        
        assert status['status'] == 'completed'
        assert status['progress'] == 100
        assert 'completed_at' in status
    
    @pytest.mark.asyncio
    async def test_get_status_not_found(self, service):
        """Test getting status of non-existent backtest."""
        status = await service.get_status("non-existent-id")
        assert status['status'] == 'not_found'
    
    @pytest.mark.asyncio
    async def test_get_result_completed(self, service, valid_request):
        """Test getting result of completed backtest."""
        # Add a completed backtest
        result_data = {
            'request_id': valid_request.request_id,
            'strategy_name': 'pure_lending',
            'final_value': 105000,
            'total_return': 0.05,
            'annualized_return': 0.05,
            'sharpe_ratio': 1.2,
            'max_drawdown': -0.02,
            'total_trades': 10,
            'total_fees': 100.0
        }
        service.completed_backtests[valid_request.request_id] = result_data
        
        result = await service.get_result(valid_request.request_id)
        
        assert result == result_data
        assert result['final_value'] == 105000
        assert result['total_return'] == 0.05
    
    @pytest.mark.asyncio
    async def test_get_result_not_found(self, service):
        """Test getting result of non-existent backtest."""
        result = await service.get_result("non-existent-id")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cancel_backtest_success(self, service, valid_request):
        """Test successful backtest cancellation."""
        # Add a running backtest
        service.running_backtests[valid_request.request_id] = {
            'request': valid_request,
            'status': 'running',
            'started_at': datetime.utcnow(),
            'progress': 30
        }
        
        result = await service.cancel_backtest(valid_request.request_id)
        
        assert result is True
        backtest_info = service.running_backtests[valid_request.request_id]
        assert backtest_info['status'] == 'cancelled'
        assert 'completed_at' in backtest_info
    
    @pytest.mark.asyncio
    async def test_cancel_backtest_not_found(self, service):
        """Test cancel backtest with non-existent request ID."""
        result = await service.cancel_backtest("non-existent-id")
        assert result is False
    
    def test_map_strategy_to_mode(self, service):
        """Test strategy name to mode mapping."""
        assert service._map_strategy_to_mode("pure_lending") == "pure_lending"
        assert service._map_strategy_to_mode("btc_basis") == "btc_basis"
        assert service._map_strategy_to_mode("eth_leveraged") == "eth_leveraged"
        assert service._map_strategy_to_mode("usdt_market_neutral") == "usdt_market_neutral"
        assert service._map_strategy_to_mode("usdt_market_neutral_no_leverage") == "usdt_market_neutral_no_leverage"
        assert service._map_strategy_to_mode("eth_staking_only") == "eth_staking_only"
        assert service._map_strategy_to_mode("unknown_strategy") == "pure_lending"  # default
    
    def test_deep_merge(self, service):
        """Test deep merge functionality."""
        base = {
            'level1': {
                'level2': {
                    'value1': 'original',
                    'value2': 'keep'
                }
            },
            'other': 'unchanged'
        }
        
        override = {
            'level1': {
                'level2': {
                    'value1': 'updated'
                }
            },
            'new_key': 'added'
        }
        
        result = service._deep_merge(base, override)
        
        assert result['level1']['level2']['value1'] == 'updated'
        assert result['level1']['level2']['value2'] == 'keep'
        assert result['other'] == 'unchanged'
        assert result['new_key'] == 'added'
    
    def test_validate_apy_vs_target(self, service):
        """Test APY validation against target."""
        # Meets target
        result = service._validate_apy_vs_target(0.06, 0.05)
        assert result['status'] == 'meets_target'
        assert result['actual'] == 0.06
        assert result['target'] == 0.05
        assert abs(result['difference'] - 0.01) < 1e-10  # Handle floating point precision
        
        # Below target
        result = service._validate_apy_vs_target(0.04, 0.05)
        assert result['status'] == 'below_target'
        assert abs(result['difference'] - (-0.01)) < 1e-10  # Handle floating point precision
        
        # No target
        result = service._validate_apy_vs_target(0.06, None)
        assert result['status'] == 'no_target'
    
    def test_validate_drawdown_vs_target(self, service):
        """Test drawdown validation against target."""
        # Within target (both negative)
        result = service._validate_drawdown_vs_target(-0.02, -0.03)
        assert result['status'] == 'within_target'
        assert result['actual'] == -0.02
        assert result['target'] == -0.03
        
        # Exceeds target
        result = service._validate_drawdown_vs_target(-0.04, -0.03)
        assert result['status'] == 'exceeds_target'
        assert abs(result['difference'] - 0.01) < 1e-10  # Handle floating point precision
        
        # No target
        result = service._validate_drawdown_vs_target(-0.02, None)
        assert result['status'] == 'no_target'


class TestBacktestServiceModeCoverage:
    """Test BacktestService with all available modes."""
    
    @pytest.fixture
    def service(self):
        """Create a BacktestService instance."""
        return BacktestService()
    
    @pytest.fixture
    def base_request_params(self):
        """Base parameters for backtest requests."""
        return {
            'start_date': datetime(2024, 1, 1),
            'end_date': datetime(2024, 1, 31),
            'initial_capital': Decimal("100000"),
            'share_class': "USDT"
        }
    
    @pytest.mark.asyncio
    @patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader')
    @patch('backend.src.basis_strategy_v1.core.services.backtest_service.EventDrivenStrategyEngine')
    async def test_pure_lending_mode(self, mock_engine_class, mock_config_loader, service, base_request_params):
        """Test pure lending mode backtest."""
        # Mock config loader
        mock_loader = Mock()
        mock_loader.get_complete_config.return_value = {
            'mode': 'pure_lending',
            'lending_enabled': True,
            'staking_enabled': False,
            'basis_trade_enabled': False,
            'leverage_enabled': False,
            'target_apy': 0.05,
            'max_drawdown': 0.005
        }
        mock_config_loader.return_value = mock_loader
        
        # Mock strategy engine
        mock_engine = Mock()
        mock_engine.run_backtest = AsyncMock(return_value={
            'final_value': 105000,
            'total_return': 0.05,
            'annualized_return': 0.05,
            'max_drawdown': -0.003
        })
        mock_engine_class.return_value = mock_engine
        
        # Create request
        request = service.create_request(
            strategy_name="pure_lending",
            **base_request_params
        )
        
        # Run backtest
        request_id = await service.run_backtest(request)
        
        # Verify
        assert request_id in service.running_backtests
        backtest_info = service.running_backtests[request_id]
        assert backtest_info['request'].strategy_name == "pure_lending"
        assert backtest_info['status'] == 'running'
    
    @pytest.mark.asyncio
    @patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader')
    @patch('backend.src.basis_strategy_v1.core.services.backtest_service.EventDrivenStrategyEngine')
    async def test_btc_basis_mode(self, mock_engine_class, mock_config_loader, service, base_request_params):
        """Test BTC basis trading mode backtest."""
        # Mock config loader
        mock_loader = Mock()
        mock_loader.get_complete_config.return_value = {
            'mode': 'btc_basis',
            'lending_enabled': False,
            'staking_enabled': False,
            'basis_trade_enabled': True,
            'leverage_enabled': False,
            'hedge_venues': ['binance', 'bybit', 'okx'],
            'target_apy': 0.08,
            'max_drawdown': 0.02
        }
        mock_config_loader.return_value = mock_loader
        
        # Mock strategy engine
        mock_engine = Mock()
        mock_engine.run_backtest = AsyncMock(return_value={
            'final_value': 108000,
            'total_return': 0.08,
            'annualized_return': 0.08,
            'max_drawdown': -0.015
        })
        mock_engine_class.return_value = mock_engine
        
        # Create request
        request = service.create_request(
            strategy_name="btc_basis",
            **base_request_params
        )
        
        # Run backtest
        request_id = await service.run_backtest(request)
        
        # Verify
        assert request_id in service.running_backtests
        backtest_info = service.running_backtests[request_id]
        assert backtest_info['request'].strategy_name == "btc_basis"
        assert backtest_info['status'] == 'running'
    
    @pytest.mark.asyncio
    @patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader')
    @patch('backend.src.basis_strategy_v1.core.services.backtest_service.EventDrivenStrategyEngine')
    async def test_eth_leveraged_mode(self, mock_engine_class, mock_config_loader, service, base_request_params):
        """Test ETH leveraged staking mode backtest."""
        # Mock config loader
        mock_loader = Mock()
        mock_loader.get_complete_config.return_value = {
            'mode': 'eth_leveraged',
            'lending_enabled': True,
            'staking_enabled': True,
            'basis_trade_enabled': False,
            'leverage_enabled': True,
            'lst_type': 'weeth',
            'rewards_mode': 'base_eigen',
            'target_apy': 0.20,
            'max_drawdown': 0.04
        }
        mock_config_loader.return_value = mock_loader
        
        # Mock strategy engine
        mock_engine = Mock()
        mock_engine.run_backtest = AsyncMock(return_value={
            'final_value': 120000,
            'total_return': 0.20,
            'annualized_return': 0.20,
            'max_drawdown': -0.03
        })
        mock_engine_class.return_value = mock_engine
        
        # Create request with ETH share class
        request_params = base_request_params.copy()
        request_params['share_class'] = 'ETH'
        request_params['initial_capital'] = Decimal("50")  # ETH amount
        
        request = service.create_request(
            strategy_name="eth_leveraged",
            **request_params
        )
        
        # Run backtest
        request_id = await service.run_backtest(request)
        
        # Verify
        assert request_id in service.running_backtests
        backtest_info = service.running_backtests[request_id]
        assert backtest_info['request'].strategy_name == "eth_leveraged"
        assert backtest_info['request'].share_class == "ETH"
        assert backtest_info['status'] == 'running'
    
    @pytest.mark.asyncio
    @patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader')
    @patch('backend.src.basis_strategy_v1.core.services.backtest_service.EventDrivenStrategyEngine')
    async def test_eth_staking_only_mode(self, mock_engine_class, mock_config_loader, service, base_request_params):
        """Test ETH staking only mode backtest."""
        # Mock config loader
        mock_loader = Mock()
        mock_loader.get_complete_config.return_value = {
            'mode': 'eth_staking_only',
            'lending_enabled': False,
            'staking_enabled': True,
            'basis_trade_enabled': False,
            'leverage_enabled': False,
            'lst_type': 'weeth',
            'rewards_mode': 'base_eigen',
            'target_apy': 0.03,
            'max_drawdown': 0.01
        }
        mock_config_loader.return_value = mock_loader
        
        # Mock strategy engine
        mock_engine = Mock()
        mock_engine.run_backtest = AsyncMock(return_value={
            'final_value': 103000,
            'total_return': 0.03,
            'annualized_return': 0.03,
            'max_drawdown': -0.005
        })
        mock_engine_class.return_value = mock_engine
        
        # Create request with ETH share class
        request_params = base_request_params.copy()
        request_params['share_class'] = 'ETH'
        request_params['initial_capital'] = Decimal("50")  # ETH amount
        
        request = service.create_request(
            strategy_name="eth_staking_only",
            **request_params
        )
        
        # Run backtest
        request_id = await service.run_backtest(request)
        
        # Verify
        assert request_id in service.running_backtests
        backtest_info = service.running_backtests[request_id]
        assert backtest_info['request'].strategy_name == "eth_staking_only"
        assert backtest_info['request'].share_class == "ETH"
        assert backtest_info['status'] == 'running'
    
    @pytest.mark.asyncio
    @patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader')
    @patch('backend.src.basis_strategy_v1.core.services.backtest_service.EventDrivenStrategyEngine')
    async def test_usdt_market_neutral_mode(self, mock_engine_class, mock_config_loader, service, base_request_params):
        """Test USDT market neutral mode backtest."""
        # Mock config loader
        mock_loader = Mock()
        mock_loader.get_complete_config.return_value = {
            'mode': 'usdt_market_neutral',
            'lending_enabled': True,
            'staking_enabled': True,
            'basis_trade_enabled': True,
            'leverage_enabled': True,
            'use_flash_loan': True,
            'hedge_venues': ['binance', 'bybit', 'okx'],
            'target_apy': 0.15,
            'max_drawdown': 0.04
        }
        mock_config_loader.return_value = mock_loader
        
        # Mock strategy engine
        mock_engine = Mock()
        mock_engine.run_backtest = AsyncMock(return_value={
            'final_value': 115000,
            'total_return': 0.15,
            'annualized_return': 0.15,
            'max_drawdown': -0.025
        })
        mock_engine_class.return_value = mock_engine
        
        # Create request
        request = service.create_request(
            strategy_name="usdt_market_neutral",
            **base_request_params
        )
        
        # Run backtest
        request_id = await service.run_backtest(request)
        
        # Verify
        assert request_id in service.running_backtests
        backtest_info = service.running_backtests[request_id]
        assert backtest_info['request'].strategy_name == "usdt_market_neutral"
        assert backtest_info['status'] == 'running'
    
    @pytest.mark.asyncio
    @patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader')
    @patch('backend.src.basis_strategy_v1.core.services.backtest_service.EventDrivenStrategyEngine')
    async def test_usdt_market_neutral_no_leverage_mode(self, mock_engine_class, mock_config_loader, service, base_request_params):
        """Test USDT market neutral no leverage mode backtest."""
        # Mock config loader
        mock_loader = Mock()
        mock_loader.get_complete_config.return_value = {
            'mode': 'usdt_market_neutral_no_leverage',
            'lending_enabled': False,
            'staking_enabled': True,
            'basis_trade_enabled': True,
            'leverage_enabled': False,
            'hedge_venues': ['binance', 'bybit', 'okx'],
            'target_apy': 0.08,
            'max_drawdown': 0.02
        }
        mock_config_loader.return_value = mock_loader
        
        # Mock strategy engine
        mock_engine = Mock()
        mock_engine.run_backtest = AsyncMock(return_value={
            'final_value': 108000,
            'total_return': 0.08,
            'annualized_return': 0.08,
            'max_drawdown': -0.015
        })
        mock_engine_class.return_value = mock_engine
        
        # Create request
        request = service.create_request(
            strategy_name="usdt_market_neutral_no_leverage",
            **base_request_params
        )
        
        # Run backtest
        request_id = await service.run_backtest(request)
        
        # Verify
        assert request_id in service.running_backtests
        backtest_info = service.running_backtests[request_id]
        assert backtest_info['request'].strategy_name == "usdt_market_neutral_no_leverage"
        assert backtest_info['status'] == 'running'


class TestBacktestErrorCodes:
    """Test backtest error code constants."""
    
    def test_error_codes_defined(self):
        """Test that all backtest error codes are defined."""
        expected_codes = [
            'BT-001', 'BT-002', 'BT-003', 'BT-004', 'BT-005'
        ]
        
        for code in expected_codes:
            assert code in BACKTEST_ERROR_CODES
            assert BACKTEST_ERROR_CODES[code] is not None
            assert len(BACKTEST_ERROR_CODES[code]) > 0


@pytest.mark.asyncio
class TestBacktestAsyncIntegration:
    """Test backtest async integration scenarios."""
    
    @pytest.fixture
    def service(self):
        """Create a BacktestService instance."""
        return BacktestService()
    
    async def test_concurrent_backtest_management(self, service):
        """Test managing multiple backtests concurrently."""
        # Create multiple requests
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        requests = [
            service.create_request(f"strategy_{i}", start_date, end_date, Decimal("100000"), "USDT")
            for i in range(3)
        ]
        
        # Start all backtests concurrently
        tasks = []
        for request in requests:
            task = asyncio.create_task(service.run_backtest(request))
            tasks.append(task)
        
        # Wait for all to complete (they will fail due to mocking, but that's OK)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all tasks completed (even if with exceptions)
        assert len(results) == 3
        
        # Verify no backtests are running (due to config errors)
        assert len(service.running_backtests) == 0
    
    async def test_backtest_with_config_overrides(self, service):
        """Test backtest with custom config overrides."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        request = service.create_request(
            strategy_name="pure_lending",
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal("100000"),
            share_class="USDT",
            config_overrides={
                'target_apy': 0.08,
                'max_drawdown': 0.01,
                'lending_enabled': True
            }
        )
        
        # Verify config overrides are preserved
        assert request.config_overrides['target_apy'] == 0.08
        assert request.config_overrides['max_drawdown'] == 0.01
        assert request.config_overrides['lending_enabled'] is True
