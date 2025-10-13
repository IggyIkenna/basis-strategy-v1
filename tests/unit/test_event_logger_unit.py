"""
Unit tests for Event Logger component.

Tests event logging functionality in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime


class TestEventLogger:
    """Test Event Logger component in isolation."""
    
    def test_event_logger_initialization(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test event logger initializes correctly with config and data provider."""
        from backend.src.basis_strategy_v1.infrastructure.logging.event_logger import EventLogger
        
        event_logger = EventLogger(config=mock_config, data_provider=mock_data_provider, utility_manager=mock_utility_manager)
        
        assert event_logger.config == mock_config
        assert event_logger.data_provider == mock_data_provider
        assert event_logger.log_level == mock_config.get('log_level', 'INFO')
    
    def test_log_strategy_event(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test logging strategy events with proper formatting."""
        from backend.src.basis_strategy_v1.infrastructure.logging.event_logger import EventLogger
        
        event_logger = EventLogger(config=mock_config, data_provider=mock_data_provider, utility_manager=mock_utility_manager)
        
        with patch('backend.src.basis_strategy_v1.infrastructure.logging.event_logger.logger') as mock_logger:
            event_logger.log_strategy_event(
                event_type="position_opened",
                strategy_mode="pure_lending",
                details={"position_size": 1000.0, "asset": "USDT"}
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "position_opened" in call_args
            assert "pure_lending" in call_args
            assert "1000.0" in call_args
    
    def test_log_error_event(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test logging error events with stack traces."""
        from backend.src.basis_strategy_v1.infrastructure.logging.event_logger import EventLogger
        
        event_logger = EventLogger(config=mock_config, data_provider=mock_data_provider, utility_manager=mock_utility_manager)
        
        with patch('backend.src.basis_strategy_v1.infrastructure.logging.event_logger.logger') as mock_logger:
            try:
                raise ValueError("Test error")
            except ValueError as e:
                event_logger.log_error_event(
                    error=e,
                    context="test_context",
                    component="test_component"
                )
            
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "ValueError" in call_args
            assert "Test error" in call_args
            assert "test_context" in call_args
    
    def test_log_performance_metrics(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test logging performance metrics with timing data."""
        from backend.src.basis_strategy_v1.infrastructure.logging.event_logger import EventLogger
        
        event_logger = EventLogger(config=mock_config, data_provider=mock_data_provider, utility_manager=mock_utility_manager)
        
        with patch('backend.src.basis_strategy_v1.infrastructure.logging.event_logger.logger') as mock_logger:
            event_logger.log_performance_metrics(
                operation="strategy_execution",
                duration_ms=150.5,
                memory_usage_mb=45.2,
                additional_metrics={"positions_processed": 10}
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "strategy_execution" in call_args
            assert "150.5" in call_args
            assert "45.2" in call_args
            assert "10" in call_args
    
    def test_log_audit_trail(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test logging audit trail events for compliance."""
        from backend.src.basis_strategy_v1.infrastructure.logging.event_logger import EventLogger
        
        event_logger = EventLogger(config=mock_config, data_provider=mock_data_provider, utility_manager=mock_utility_manager)
        
        with patch('backend.src.basis_strategy_v1.infrastructure.logging.event_logger.logger') as mock_logger:
            event_logger.log_audit_trail(
                action="config_change",
                user="system",
                details={"old_value": "dev", "new_value": "staging"},
                timestamp=datetime.now()
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "config_change" in call_args
            assert "system" in call_args
            assert "dev" in call_args
            assert "staging" in call_args
    
    def test_log_health_status(self, mock_config, mock_data_provider, mock_utility_manager):
        """Test logging health status events."""
        from backend.src.basis_strategy_v1.infrastructure.logging.event_logger import EventLogger
        
        event_logger = EventLogger(config=mock_config, data_provider=mock_data_provider, utility_manager=mock_utility_manager)
        
        with patch('backend.src.basis_strategy_v1.infrastructure.logging.event_logger.logger') as mock_logger:
            event_logger.log_health_status(
                component="position_monitor",
                status="healthy",
                metrics={"uptime_seconds": 3600, "memory_usage": 0.75}
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "position_monitor" in call_args
            assert "healthy" in call_args
            assert "3600" in call_args
