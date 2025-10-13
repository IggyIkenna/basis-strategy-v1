"""
Unit tests for Reconciliation Component.

Tests the reconciliation component in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from basis_strategy_v1.core.reconciliation.reconciliation_component import (
    ReconciliationComponent,
    ComponentError
)


class TestComponentError:
    """Test ComponentError exception class."""
    
    def test_initialization(self):
        """Test ComponentError initialization."""
        error = ComponentError(
            error_code="REC-001",
            message="Test error",
            component="reconciliation",
            severity="HIGH"
        )
        
        assert error.error_code == "REC-001"
        assert str(error) == "Test error"
        assert error.component == "reconciliation"
        assert error.severity == "HIGH"
        assert error.original_exception is None
    
    def test_initialization_with_original_exception(self):
        """Test ComponentError initialization with original exception."""
        original_exception = ValueError("Original error")
        error = ComponentError(
            error_code="REC-001",
            message="Test error",
            component="reconciliation",
            severity="HIGH",
            original_exception=original_exception
        )
        
        assert error.error_code == "REC-001"
        assert str(error) == "Test error"
        assert error.component == "reconciliation"
        assert error.severity == "HIGH"
        assert error.original_exception == original_exception
    
    def test_string_representation(self):
        """Test ComponentError string representation."""
        error = ComponentError(
            error_code="REC-001",
            message="Test error",
            component="reconciliation",
            severity="HIGH"
        )
        
        error_str = str(error)
        assert "REC-001" in error_str
        assert "Test error" in error_str
        assert "reconciliation" in error_str
        assert "HIGH" in error_str


class TestReconciliationComponent:
    """Test Reconciliation Component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for reconciliation component."""
        return {
            'reconciliation_enabled': True,
            'tolerance_threshold': 0.01,
            'max_retries': 3,
            'timeout': 30
        }
    
    @pytest.fixture
    def mock_position_monitor(self):
        """Mock position monitor."""
        monitor = Mock()
        monitor.get_positions.return_value = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        return monitor
    
    @pytest.fixture
    def mock_event_logger(self):
        """Mock event logger."""
        logger = Mock()
        logger.log_event.return_value = None
        return logger
    
    @pytest.fixture
    def mock_health_manager(self):
        """Mock health manager."""
        manager = Mock()
        manager.health_check.return_value = {'status': 'healthy'}
        return manager
    
    @pytest.fixture
    def mock_reconciliation_component(self, mock_config, mock_position_monitor, mock_event_logger, mock_health_manager):
        """Create reconciliation component with mocked dependencies."""
        component = ReconciliationComponent(
            config=mock_config,
            execution_mode='backtest',
            position_monitor=mock_position_monitor,
            event_logger=mock_event_logger,
            health_manager=mock_health_manager
        )
        return component
    
    def test_initialization(self, mock_config, mock_position_monitor, mock_event_logger, mock_health_manager):
        """Test reconciliation component initialization."""
        component = ReconciliationComponent(
            config=mock_config,
            execution_mode='backtest',
            position_monitor=mock_position_monitor,
            event_logger=mock_event_logger,
            health_manager=mock_health_manager
        )
        
        assert component.config == mock_config
        assert component.execution_mode == 'backtest'
        assert component.position_monitor == mock_position_monitor
        assert component.event_logger == mock_event_logger
        assert component.health_manager == mock_health_manager
    
    def test_singleton_pattern(self, mock_config, mock_position_monitor, mock_event_logger, mock_health_manager):
        """Test that ReconciliationComponent follows singleton pattern."""
        component1 = ReconciliationComponent(
            config=mock_config,
            execution_mode='backtest',
            position_monitor=mock_position_monitor,
            event_logger=mock_event_logger,
            health_manager=mock_health_manager
        )
        
        component2 = ReconciliationComponent(
            config=mock_config,
            execution_mode='live',
            position_monitor=mock_position_monitor,
            event_logger=mock_event_logger,
            health_manager=mock_health_manager
        )
        
        assert component1 is component2
    
    def test_reconcile_positions_success(self, mock_reconciliation_component):
        """Test successful position reconciliation."""
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        result = mock_reconciliation_component.reconcile_positions(simulated_positions, real_positions)
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['reconciled'] is True
        assert result['differences'] == []
    
    def test_reconcile_positions_with_differences(self, mock_reconciliation_component):
        """Test position reconciliation with differences."""
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 950.0, 'ETH': 1.0}  # Different USDT amount
        }
        
        result = mock_reconciliation_component.reconcile_positions(simulated_positions, real_positions)
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['reconciled'] is False
        assert len(result['differences']) > 0
    
    def test_reconcile_positions_within_tolerance(self, mock_reconciliation_component):
        """Test position reconciliation within tolerance."""
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.05, 'ETH': 1.0}  # Small difference within tolerance
        }
        
        result = mock_reconciliation_component.reconcile_positions(simulated_positions, real_positions)
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['reconciled'] is True
        assert len(result['differences']) == 0
    
    def test_reconcile_positions_outside_tolerance(self, mock_reconciliation_component):
        """Test position reconciliation outside tolerance."""
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 900.0, 'ETH': 1.0}  # Large difference outside tolerance
        }
        
        result = mock_reconciliation_component.reconcile_positions(simulated_positions, real_positions)
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['reconciled'] is False
        assert len(result['differences']) > 0
    
    def test_reconcile_positions_missing_keys(self, mock_reconciliation_component):
        """Test position reconciliation with missing keys."""
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            # Missing 'wallet' key
        }
        
        result = mock_reconciliation_component.reconcile_positions(simulated_positions, real_positions)
        
        assert result is not None
        assert result['status'] == 'error'
        assert 'missing' in result['error'].lower()
    
    def test_reconcile_positions_invalid_input(self, mock_reconciliation_component):
        """Test position reconciliation with invalid input."""
        with pytest.raises(ValueError):
            mock_reconciliation_component.reconcile_positions(None, {})
    
    def test_reconcile_positions_invalid_input_type(self, mock_reconciliation_component):
        """Test position reconciliation with invalid input type."""
        with pytest.raises(ValueError):
            mock_reconciliation_component.reconcile_positions("invalid", {})
    
    def test_validate_position_structure(self, mock_reconciliation_component):
        """Test position structure validation."""
        valid_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        result = mock_reconciliation_component._validate_position_structure(valid_positions)
        assert result is True
    
    def test_validate_position_structure_invalid(self, mock_reconciliation_component):
        """Test position structure validation with invalid structure."""
        invalid_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            # Missing 'onchain_positions' and 'wallet'
        }
        
        result = mock_reconciliation_component._validate_position_structure(invalid_positions)
        assert result is False
    
    def test_validate_position_structure_none(self, mock_reconciliation_component):
        """Test position structure validation with None input."""
        result = mock_reconciliation_component._validate_position_structure(None)
        assert result is False
    
    def test_validate_position_structure_empty(self, mock_reconciliation_component):
        """Test position structure validation with empty input."""
        result = mock_reconciliation_component._validate_position_structure({})
        assert result is False
    
    def test_calculate_position_differences(self, mock_reconciliation_component):
        """Test position difference calculation."""
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 950.0, 'ETH': 1.0}
        }
        
        differences = mock_reconciliation_component._calculate_position_differences(simulated_positions, real_positions)
        
        assert differences is not None
        assert isinstance(differences, list)
        assert len(differences) > 0
    
    def test_calculate_position_differences_no_differences(self, mock_reconciliation_component):
        """Test position difference calculation with no differences."""
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        differences = mock_reconciliation_component._calculate_position_differences(simulated_positions, real_positions)
        
        assert differences is not None
        assert isinstance(differences, list)
        assert len(differences) == 0
    
    def test_calculate_position_differences_with_tolerance(self, mock_reconciliation_component):
        """Test position difference calculation with tolerance."""
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.05, 'ETH': 1.0}  # Small difference within tolerance
        }
        
        differences = mock_reconciliation_component._calculate_position_differences(simulated_positions, real_positions)
        
        assert differences is not None
        assert isinstance(differences, list)
        assert len(differences) == 0  # Should be within tolerance
    
    def test_calculate_position_differences_outside_tolerance(self, mock_reconciliation_component):
        """Test position difference calculation outside tolerance."""
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 900.0, 'ETH': 1.0}  # Large difference outside tolerance
        }
        
        differences = mock_reconciliation_component._calculate_position_differences(simulated_positions, real_positions)
        
        assert differences is not None
        assert isinstance(differences, list)
        assert len(differences) > 0  # Should be outside tolerance
    
    def test_is_within_tolerance(self, mock_reconciliation_component):
        """Test tolerance check."""
        # Within tolerance
        result = mock_reconciliation_component._is_within_tolerance(1000.0, 1000.05, 0.01)
        assert result is True
        
        # Outside tolerance
        result = mock_reconciliation_component._is_within_tolerance(1000.0, 900.0, 0.01)
        assert result is False
        
        # Exactly at tolerance
        result = mock_reconciliation_component._is_within_tolerance(1000.0, 1010.0, 0.01)
        assert result is True
    
    def test_is_within_tolerance_zero_values(self, mock_reconciliation_component):
        """Test tolerance check with zero values."""
        # Both zero
        result = mock_reconciliation_component._is_within_tolerance(0.0, 0.0, 0.01)
        assert result is True
        
        # One zero, one small
        result = mock_reconciliation_component._is_within_tolerance(0.0, 0.005, 0.01)
        assert result is True
        
        # One zero, one large
        result = mock_reconciliation_component._is_within_tolerance(0.0, 100.0, 0.01)
        assert result is False
    
    def test_is_within_tolerance_negative_values(self, mock_reconciliation_component):
        """Test tolerance check with negative values."""
        # Both negative
        result = mock_reconciliation_component._is_within_tolerance(-1000.0, -1000.05, 0.01)
        assert result is True
        
        # One negative, one positive
        result = mock_reconciliation_component._is_within_tolerance(-1000.0, 1000.0, 0.01)
        assert result is False
    
    def test_log_reconciliation_event(self, mock_reconciliation_component):
        """Test reconciliation event logging."""
        differences = [
            {
                'venue': 'wallet',
                'asset': 'USDT',
                'simulated': 1000.0,
                'real': 950.0,
                'difference': -50.0
            }
        ]
        
        mock_reconciliation_component._log_reconciliation_event(differences)
        
        # Verify event logger was called
        mock_reconciliation_component.event_logger.log_event.assert_called_once()
    
    def test_log_reconciliation_event_no_differences(self, mock_reconciliation_component):
        """Test reconciliation event logging with no differences."""
        differences = []
        
        mock_reconciliation_component._log_reconciliation_event(differences)
        
        # Verify event logger was called
        mock_reconciliation_component.event_logger.log_event.assert_called_once()
    
    def test_log_reconciliation_event_no_logger(self, mock_config, mock_position_monitor, mock_health_manager):
        """Test reconciliation event logging without event logger."""
        component = ReconciliationComponent(
            config=mock_config,
            execution_mode='backtest',
            position_monitor=mock_position_monitor,
            event_logger=None,
            health_manager=mock_health_manager
        )
        
        differences = [
            {
                'venue': 'wallet',
                'asset': 'USDT',
                'simulated': 1000.0,
                'real': 950.0,
                'difference': -50.0
            }
        ]
        
        # Should not raise exception
        component._log_reconciliation_event(differences)
    
    def test_health_check(self, mock_reconciliation_component):
        """Test health check functionality."""
        result = mock_reconciliation_component.health_check()
        
        assert result is not None
        assert 'status' in result
        assert 'component' in result
        assert result['component'] == 'reconciliation'
        assert result['status'] in ['healthy', 'unhealthy']
    
    def test_health_check_with_health_manager(self, mock_reconciliation_component):
        """Test health check with health manager."""
        result = mock_reconciliation_component.health_check()
        
        assert result is not None
        assert 'status' in result
        assert 'component' in result
        assert result['component'] == 'reconciliation'
    
    def test_health_check_without_health_manager(self, mock_config, mock_position_monitor, mock_event_logger):
        """Test health check without health manager."""
        component = ReconciliationComponent(
            config=mock_config,
            execution_mode='backtest',
            position_monitor=mock_position_monitor,
            event_logger=mock_event_logger,
            health_manager=None
        )
        
        result = component.health_check()
        
        assert result is not None
        assert 'status' in result
        assert 'component' in result
        assert result['component'] == 'reconciliation'
    
    def test_error_handling_invalid_config(self, mock_position_monitor, mock_event_logger, mock_health_manager):
        """Test error handling with invalid config."""
        with pytest.raises(ValueError):
            ReconciliationComponent(
                config=None,
                execution_mode='backtest',
                position_monitor=mock_position_monitor,
                event_logger=mock_event_logger,
                health_manager=mock_health_manager
            )
    
    def test_error_handling_invalid_execution_mode(self, mock_config, mock_position_monitor, mock_event_logger, mock_health_manager):
        """Test error handling with invalid execution mode."""
        with pytest.raises(ValueError):
            ReconciliationComponent(
                config=mock_config,
                execution_mode='invalid_mode',
                position_monitor=mock_position_monitor,
                event_logger=mock_event_logger,
                health_manager=mock_health_manager
            )
    
    def test_error_handling_missing_position_monitor(self, mock_config, mock_event_logger, mock_health_manager):
        """Test error handling with missing position monitor."""
        with pytest.raises(ValueError):
            ReconciliationComponent(
                config=mock_config,
                execution_mode='backtest',
                position_monitor=None,
                event_logger=mock_event_logger,
                health_manager=mock_health_manager
            )
    
    def test_edge_case_very_small_differences(self, mock_reconciliation_component):
        """Test edge case with very small differences."""
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0001, 'ETH': 1.0}  # Very small difference
        }
        
        result = mock_reconciliation_component.reconcile_positions(simulated_positions, real_positions)
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['reconciled'] is True  # Should be within tolerance
    
    def test_edge_case_very_large_differences(self, mock_reconciliation_component):
        """Test edge case with very large differences."""
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000000.0, 'ETH': 1.0}  # Very large difference
        }
        
        result = mock_reconciliation_component.reconcile_positions(simulated_positions, real_positions)
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['reconciled'] is False  # Should be outside tolerance
        assert len(result['differences']) > 0
    
    def test_edge_case_missing_assets(self, mock_reconciliation_component):
        """Test edge case with missing assets."""
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0}  # Missing ETH
        }
        
        result = mock_reconciliation_component.reconcile_positions(simulated_positions, real_positions)
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['reconciled'] is False
        assert len(result['differences']) > 0
    
    def test_edge_case_extra_assets(self, mock_reconciliation_component):
        """Test edge case with extra assets."""
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {'USDT': 1000.0, 'ETH': 1.0, 'BTC': 0.1}  # Extra BTC
        }
        
        result = mock_reconciliation_component.reconcile_positions(simulated_positions, real_positions)
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['reconciled'] is False
        assert len(result['differences']) > 0
    
    def test_performance_large_position_sets(self, mock_reconciliation_component):
        """Test performance with large position sets."""
        # Create large position sets
        simulated_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {f'TOKEN_{i}': 1000.0 for i in range(1000)}
        }
        
        real_positions = {
            'cex_derivatives_positions': {},
            'cex_spot_positions': {},
            'onchain_positions': {},
            'wallet': {f'TOKEN_{i}': 1000.0 for i in range(1000)}
        }
        
        result = mock_reconciliation_component.reconcile_positions(simulated_positions, real_positions)
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['reconciled'] is True
        assert len(result['differences']) == 0
    
    def test_concurrent_reconciliation_requests(self, mock_reconciliation_component):
        """Test concurrent reconciliation requests."""
        import asyncio
        
        async def reconcile_positions():
            simulated_positions = {
                'cex_derivatives_positions': {},
                'cex_spot_positions': {},
                'onchain_positions': {},
                'wallet': {'USDT': 1000.0, 'ETH': 1.0}
            }
            
            real_positions = {
                'cex_derivatives_positions': {},
                'cex_spot_positions': {},
                'onchain_positions': {},
                'wallet': {'USDT': 1000.0, 'ETH': 1.0}
            }
            
            return mock_reconciliation_component.reconcile_positions(simulated_positions, real_positions)
        
        async def run_concurrent():
            tasks = [reconcile_positions() for _ in range(10)]
            return await asyncio.gather(*tasks)
        
        results = asyncio.run(run_concurrent())
        
        assert len(results) == 10
        assert all(result['status'] == 'success' for result in results)
        assert all(result['reconciled'] is True for result in results)
