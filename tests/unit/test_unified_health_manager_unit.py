"""
Unit tests for Unified Health Manager.

Tests the unified health manager component in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta

from basis_strategy_v1.core.health.unified_health_manager import UnifiedHealthManager


class TestUnifiedHealthManager:
    """Test Unified Health Manager component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for unified health manager."""
        return {
            'health_check_interval': 30,
            'timeout': 10,
            'max_retries': 3,
            'mode': 'backtest'
        }
    
    @pytest.fixture
    def mock_health_manager(self, mock_config):
        """Create unified health manager with mocked dependencies."""
        with patch('basis_strategy_v1.core.health.unified_health_manager.ComponentHealthChecker'):
            with patch('basis_strategy_v1.core.health.unified_health_manager.PositionMonitorHealthChecker'):
                with patch('basis_strategy_v1.core.health.unified_health_manager.DataProviderHealthChecker'):
                    with patch('basis_strategy_v1.core.health.unified_health_manager.RiskMonitorHealthChecker'):
                        with patch('basis_strategy_v1.core.health.unified_health_manager.EventLoggerHealthChecker'):
                            with patch('basis_strategy_v1.core.health.unified_health_manager.system_health_aggregator'):
                                manager = UnifiedHealthManager()
                                return manager
    
    def test_initialization(self, mock_config):
        """Test unified health manager initialization."""
        with patch('basis_strategy_v1.core.health.unified_health_manager.ComponentHealthChecker'):
            with patch('basis_strategy_v1.core.health.unified_health_manager.PositionMonitorHealthChecker'):
                with patch('basis_strategy_v1.core.health.unified_health_manager.DataProviderHealthChecker'):
                    with patch('basis_strategy_v1.core.health.unified_health_manager.RiskMonitorHealthChecker'):
                        with patch('basis_strategy_v1.core.health.unified_health_manager.EventLoggerHealthChecker'):
                            with patch('basis_strategy_v1.core.health.unified_health_manager.system_health_aggregator'):
                                manager = UnifiedHealthManager()
                                
                                assert manager is not None
                                assert manager.start_time is not None
                                assert manager.last_check_timestamp is None
    
    def test_singleton_pattern(self, mock_config):
        """Test that UnifiedHealthManager follows singleton pattern."""
        with patch('basis_strategy_v1.core.health.unified_health_manager.ComponentHealthChecker'):
            with patch('basis_strategy_v1.core.health.unified_health_manager.PositionMonitorHealthChecker'):
                with patch('basis_strategy_v1.core.health.unified_health_manager.DataProviderHealthChecker'):
                    with patch('basis_strategy_v1.core.health.unified_health_manager.RiskMonitorHealthChecker'):
                        with patch('basis_strategy_v1.core.health.unified_health_manager.EventLoggerHealthChecker'):
                            with patch('basis_strategy_v1.core.health.unified_health_manager.system_health_aggregator'):
                                manager1 = UnifiedHealthManager()
                                manager2 = UnifiedHealthManager()
                                
                                assert manager1 is manager2
    
    def test_basic_health_check(self, mock_health_manager):
        """Test basic health check functionality."""
        result = mock_health_manager.basic_health_check()
        
        assert result is not None
        assert 'status' in result
        assert 'timestamp' in result
        assert 'uptime' in result
        assert result['status'] in ['healthy', 'unhealthy']
    
    def test_detailed_health_check(self, mock_health_manager):
        """Test detailed health check functionality."""
        result = mock_health_manager.detailed_health_check()
        
        assert result is not None
        assert 'status' in result
        assert 'timestamp' in result
        assert 'uptime' in result
        assert 'components' in result
        assert 'system' in result
        assert result['status'] in ['healthy', 'unhealthy']
    
    def test_health_check_backtest_mode(self, mock_health_manager):
        """Test health check in backtest mode."""
        result = mock_health_manager.health_check(mode='backtest')
        
        assert result is not None
        assert 'status' in result
        assert 'mode' in result
        assert result['mode'] == 'backtest'
    
    def test_health_check_live_mode(self, mock_health_manager):
        """Test health check in live mode."""
        result = mock_health_manager.health_check(mode='live')
        
        assert result is not None
        assert 'status' in result
        assert 'mode' in result
        assert result['mode'] == 'live'
    
    def test_health_check_with_timeout(self, mock_health_manager):
        """Test health check with timeout."""
        result = mock_health_manager.health_check(timeout=5)
        
        assert result is not None
        assert 'status' in result
        assert 'execution_time' in result
        assert result['execution_time'] < 5.0
    
    def test_health_check_with_retries(self, mock_health_manager):
        """Test health check with retries."""
        result = mock_health_manager.health_check(max_retries=2)
        
        assert result is not None
        assert 'status' in result
        assert 'retries' in result
        assert result['retries'] <= 2
    
    def test_component_health_check(self, mock_health_manager):
        """Test component health check functionality."""
        result = mock_health_manager._check_component_health()
        
        assert result is not None
        assert 'status' in result
        assert 'components' in result
        assert isinstance(result['components'], dict)
    
    def test_system_health_check(self, mock_health_manager):
        """Test system health check functionality."""
        result = mock_health_manager._check_system_health()
        
        assert result is not None
        assert 'status' in result
        assert 'cpu' in result
        assert 'memory' in result
        assert 'disk' in result
    
    def test_health_aggregation(self, mock_health_manager):
        """Test health aggregation functionality."""
        component_health = {'status': 'healthy', 'components': {}}
        system_health = {'status': 'healthy', 'cpu': 50.0, 'memory': 60.0}
        
        result = mock_health_manager._aggregate_health(component_health, system_health)
        
        assert result is not None
        assert 'status' in result
        assert 'components' in result
        assert 'system' in result
        assert result['status'] == 'healthy'
    
    def test_health_aggregation_unhealthy(self, mock_health_manager):
        """Test health aggregation with unhealthy components."""
        component_health = {'status': 'unhealthy', 'components': {}}
        system_health = {'status': 'healthy', 'cpu': 50.0, 'memory': 60.0}
        
        result = mock_health_manager._aggregate_health(component_health, system_health)
        
        assert result is not None
        assert result['status'] == 'unhealthy'
    
    def test_uptime_calculation(self, mock_health_manager):
        """Test uptime calculation."""
        uptime = mock_health_manager._calculate_uptime()
        
        assert uptime is not None
        assert isinstance(uptime, float)
        assert uptime >= 0
    
    def test_health_check_error_handling(self, mock_health_manager):
        """Test health check error handling."""
        with patch.object(mock_health_manager, '_check_component_health', side_effect=Exception("Component check failed")):
            result = mock_health_manager.detailed_health_check()
            
            assert result is not None
            assert result['status'] == 'unhealthy'
            assert 'error' in result
    
    def test_health_check_timeout_handling(self, mock_health_manager):
        """Test health check timeout handling."""
        with patch.object(mock_health_manager, '_check_component_health', side_effect=asyncio.TimeoutError("Timeout")):
            result = mock_health_manager.detailed_health_check()
            
            assert result is not None
            assert result['status'] == 'unhealthy'
            assert 'timeout' in result['error'].lower()
    
    def test_health_check_retry_logic(self, mock_health_manager):
        """Test health check retry logic."""
        call_count = 0
        
        def mock_check():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return {'status': 'healthy'}
        
        with patch.object(mock_health_manager, '_check_component_health', side_effect=mock_check):
            result = mock_health_manager.detailed_health_check()
            
            assert result is not None
            assert result['status'] == 'healthy'
            assert call_count == 3
    
    def test_health_check_max_retries_exceeded(self, mock_health_manager):
        """Test health check when max retries are exceeded."""
        with patch.object(mock_health_manager, '_check_component_health', side_effect=Exception("Persistent failure")):
            result = mock_health_manager.detailed_health_check()
            
            assert result is not None
            assert result['status'] == 'unhealthy'
            assert 'retries' in result
            assert result['retries'] == 3
    
    def test_health_check_performance(self, mock_health_manager):
        """Test health check performance."""
        start_time = time.time()
        result = mock_health_manager.basic_health_check()
        end_time = time.time()
        
        assert result is not None
        assert 'execution_time' in result
        assert result['execution_time'] < 1.0  # Should be fast
        assert (end_time - start_time) < 1.0
    
    def test_health_check_memory_usage(self, mock_health_manager):
        """Test health check memory usage."""
        result = mock_health_manager.detailed_health_check()
        
        assert result is not None
        assert 'system' in result
        assert 'memory' in result['system']
        assert isinstance(result['system']['memory'], (int, float))
    
    def test_health_check_cpu_usage(self, mock_health_manager):
        """Test health check CPU usage."""
        result = mock_health_manager.detailed_health_check()
        
        assert result is not None
        assert 'system' in result
        assert 'cpu' in result['system']
        assert isinstance(result['system']['cpu'], (int, float))
    
    def test_health_check_disk_usage(self, mock_health_manager):
        """Test health check disk usage."""
        result = mock_health_manager.detailed_health_check()
        
        assert result is not None
        assert 'system' in result
        assert 'disk' in result['system']
        assert isinstance(result['system']['disk'], (int, float))
    
    def test_health_check_timestamp(self, mock_health_manager):
        """Test health check timestamp."""
        result = mock_health_manager.basic_health_check()
        
        assert result is not None
        assert 'timestamp' in result
        assert isinstance(result['timestamp'], str)
        
        # Verify timestamp is recent
        timestamp = datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        time_diff = abs((now - timestamp).total_seconds())
        assert time_diff < 60  # Within 1 minute
    
    def test_health_check_mode_awareness(self, mock_health_manager):
        """Test health check mode awareness."""
        backtest_result = mock_health_manager.health_check(mode='backtest')
        live_result = mock_health_manager.health_check(mode='live')
        
        assert backtest_result is not None
        assert live_result is not None
        assert backtest_result['mode'] == 'backtest'
        assert live_result['mode'] == 'live'
    
    def test_health_check_component_exclusion(self, mock_health_manager):
        """Test health check component exclusion based on mode."""
        backtest_result = mock_health_manager.health_check(mode='backtest')
        live_result = mock_health_manager.health_check(mode='live')
        
        assert backtest_result is not None
        assert live_result is not None
        
        # Backtest mode should exclude live-only components
        if 'components' in backtest_result:
            assert 'live_trading' not in backtest_result['components']
        
        # Live mode should include all components
        if 'components' in live_result:
            assert 'live_trading' in live_result['components']
    
    def test_health_check_concurrent_requests(self, mock_health_manager):
        """Test health check with concurrent requests."""
        import asyncio
        
        async def run_health_check():
            return mock_health_manager.basic_health_check()
        
        async def run_concurrent():
            tasks = [run_health_check() for _ in range(10)]
            return await asyncio.gather(*tasks)
        
        results = asyncio.run(run_concurrent())
        
        assert len(results) == 10
        assert all(result['status'] in ['healthy', 'unhealthy'] for result in results)
    
    def test_health_check_edge_case_empty_components(self, mock_health_manager):
        """Test health check edge case with empty components."""
        with patch.object(mock_health_manager, '_check_component_health', return_value={'status': 'healthy', 'components': {}}):
            result = mock_health_manager.detailed_health_check()
            
            assert result is not None
            assert result['status'] == 'healthy'
            assert 'components' in result
            assert result['components'] == {}
    
    def test_health_check_edge_case_missing_system_info(self, mock_health_manager):
        """Test health check edge case with missing system info."""
        with patch.object(mock_health_manager, '_check_system_health', return_value={'status': 'healthy'}):
            result = mock_health_manager.detailed_health_check()
            
            assert result is not None
            assert result['status'] == 'healthy'
            assert 'system' in result
    
    def test_health_check_edge_case_invalid_mode(self, mock_health_manager):
        """Test health check edge case with invalid mode."""
        result = mock_health_manager.health_check(mode='invalid_mode')
        
        assert result is not None
        assert result['status'] == 'unhealthy'
        assert 'error' in result
