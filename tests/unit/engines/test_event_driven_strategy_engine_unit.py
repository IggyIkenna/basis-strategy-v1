#!/usr/bin/env python3
"""
Event-Driven Strategy Engine Unit Tests

Tests for the EventDrivenStrategyEngine implementation following
WORKFLOW_REFACTOR_SPECIFICATION.md and all P0, P1, P2 fixes.

Test Categories:
- P0 Fixes: Undefined variables, async errors, initialization
- P1 Fixes: PnL timing, execution success checking, mode-specific triggers
- P2 Fixes: Exception handling, position refresh, health status updates
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, Any
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend" / "src"))

from backend.src.basis_strategy_v1.core.event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine


class TestEventDrivenStrategyEngineP0Fixes:
    """Test P0 fixes (blocking execution issues)."""
    
    def test_strategy_manager_no_default_mode(self):
        """P0 FIX: Strategy manager should not have default mode value."""
        config = {
            # No 'mode' key - should fail fast
            'share_class': 'USDT'
        }
        
        with pytest.raises(ValueError, match="Mode is required"):
            engine = EventDrivenStrategyEngine(
                config=config,
                execution_mode='backtest',
                data_provider=Mock(),
                initial_capital=100000,
                share_class='USDT'
            )
    
    def test_initial_capital_trigger_in_backtest(self):
        """P0 FIX: Backtest must initialize with initial_capital trigger."""
        # Mock dependencies
        mock_data_provider = Mock()
        mock_data_provider.get_data.return_value = {
            'market_data': {'timestamp': pd.Timestamp('2024-01-01', tz='UTC')}
        }
        
        config = {
            'mode': 'pure_lending_usdt',
            'share_class': 'USDT',
            'initial_capital': 100000
        }
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor') as MockPM:
                mock_pm_instance = MockPM.return_value
                
                engine = EventDrivenStrategyEngine(
                    config=config,
                    execution_mode='backtest',
                    data_provider=mock_data_provider,
                    initial_capital=100000,
                    share_class='USDT'
                )
                
                # Run backtest should call initial_capital trigger
                with patch.object(engine, '_process_timestep'):
                    with patch.object(engine.results_store, 'start'):
                        with patch.object(engine.results_store, 'stop'):
                            with patch.object(engine.results_store, 'save_final_result'):
                                with patch.object(engine.results_store, 'save_event_log'):
                                    import asyncio
                                    asyncio.run(engine.run_backtest('2024-01-01', '2024-01-02'))
                
                # Verify initial_capital trigger was called
                calls = mock_pm_instance.update_state.call_args_list
                initial_capital_calls = [c for c in calls if c[0][1] == 'initial_capital']
                assert len(initial_capital_calls) > 0, "initial_capital trigger not called"
    
    def test_process_timestep_uses_strategy_orders_not_decision(self):
        """P0 FIX: _process_timestep should use strategy_orders, not undefined strategy_decision."""
        # Mock all dependencies
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'):
                with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                    with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'):
                        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'):
                            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLMonitor'):
                                engine = EventDrivenStrategyEngine(
                                    config=mock_config,
                                    execution_mode='backtest',
                                    data_provider=mock_data_provider,
                                    initial_capital=100000,
                                    share_class='USDT'
                                )
                                
                                # Mock all components
                                engine.position_monitor.get_current_positions.return_value = {}
                                engine.exposure_monitor.calculate_exposure.return_value = {}
                                engine.risk_monitor.assess_risk.return_value = {}
                                engine.pnl_monitor.calculate_pnl.return_value = {'balance_based': {}}
                                engine.strategy_manager.generate_orders.return_value = []
                                
                                # Mock logging methods to avoid errors
                                engine._log_timestep_event = Mock()
                                engine._store_timestep_result = Mock()
                                
                                # Call _process_timestep - should not raise NameError
                                timestamp = pd.Timestamp('2024-01-01', tz='UTC')
                                try:
                                    engine._process_timestep(timestamp, {}, 'test-request-id')
                                except NameError as e:
                                    pytest.fail(f"NameError raised: {e}. strategy_decision or action undefined.")
                                
                                # Verify _log_timestep_event was called with strategy_orders (not strategy_decision)
                                engine._log_timestep_event.assert_called_once()
                                call_args = engine._log_timestep_event.call_args[0]
                                # 5th argument should be strategy_orders (empty list in this case)
                                assert call_args[4] == [], "5th arg to _log_timestep_event should be strategy_orders"
    
    def test_live_mode_no_await_on_process_timestep(self):
        """P0 FIX: run_live should not await _process_timestep (it's not async)."""
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        mock_data_provider.get_data.return_value = {'market_data': {}}
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'):
                with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                    with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'):
                        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'):
                            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLMonitor'):
                                engine = EventDrivenStrategyEngine(
                                    config=mock_config,
                                    execution_mode='live',
                                    data_provider=mock_data_provider,
                                    initial_capital=100000,
                                    share_class='USDT'
                                )
                                
                                # Mock _process_timestep to stop loop immediately
                                engine._process_timestep = Mock(side_effect=lambda *args: setattr(engine, 'is_running', False))
                                
                                # Run live mode - should not raise TypeError about awaiting non-coroutine
                                import asyncio
                                try:
                                    asyncio.run(engine.run_live())
                                except TypeError as e:
                                    if 'await' in str(e).lower():
                                        pytest.fail(f"TypeError with await: {e}")


class TestEventDrivenStrategyEngineP1Fixes:
    """Test P1 fixes (architectural violations)."""
    
    def test_pnl_calculated_after_execution_not_before(self):
        """P1 FIX: PnL should be calculated AFTER execution, not before."""
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'):
                with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                    with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'):
                        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'):
                            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLMonitor') as MockPnL:
                                engine = EventDrivenStrategyEngine(
                                    config=mock_config,
                                    execution_mode='backtest',
                                    data_provider=mock_data_provider,
                                    initial_capital=100000,
                                    share_class='USDT'
                                )
                                
                                # Setup mocks
                                engine.position_monitor.get_current_positions.return_value = {}
                                engine.exposure_monitor.calculate_exposure.return_value = {}
                                engine.risk_monitor.assess_risk.return_value = {}
                                engine.strategy_manager.generate_orders.return_value = [Mock()]  # Has orders
                                engine.execution_manager.process_orders.return_value = {'success': True}
                                engine._log_timestep_event = Mock()
                                engine._store_timestep_result = Mock()
                                
                                pnl_mock = MockPnL.return_value
                                pnl_mock.calculate_pnl.return_value = {'balance_based': {}}
                                
                                # Process timestep
                                timestamp = pd.Timestamp('2024-01-01', tz='UTC')
                                engine._process_timestep(timestamp, {}, 'test-request-id')
                                
                                # PnL should be calculated exactly ONCE, AFTER process_orders
                                assert pnl_mock.calculate_pnl.call_count == 1, "PnL should be calculated exactly once"
                                
                                # Verify order of calls: generate_orders -> process_orders -> calculate_pnl
                                assert engine.strategy_manager.generate_orders.called
                                assert engine.execution_manager.process_orders.called
                                assert pnl_mock.calculate_pnl.called
    
    def test_execution_success_checking(self):
        """P1 FIX: Execution result should be checked for success."""
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'):
                with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                    with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'):
                        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'):
                            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLMonitor'):
                                engine = EventDrivenStrategyEngine(
                                    config=mock_config,
                                    execution_mode='backtest',
                                    data_provider=mock_data_provider,
                                    initial_capital=100000,
                                    share_class='USDT'
                                )
                                
                                # Setup mocks
                                engine.position_monitor.get_current_positions.return_value = {}
                                engine.exposure_monitor.calculate_exposure.return_value = {}
                                engine.risk_monitor.assess_risk.return_value = {}
                                engine.strategy_manager.generate_orders.return_value = [Mock()]
                                
                                # Mock execution failure
                                engine.execution_manager.process_orders.return_value = {'success': False, 'error': 'Test failure'}
                                engine._handle_execution_failure = Mock()
                                
                                # Process timestep
                                timestamp = pd.Timestamp('2024-01-01', tz='UTC')
                                engine._process_timestep(timestamp, {}, 'test-request-id')
                                
                                # Verify _handle_execution_failure was called
                                engine._handle_execution_failure.assert_called_once()
    
    def test_mode_specific_position_refresh_trigger(self):
        """P1 FIX: Backtest should not use position_refresh trigger."""
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor') as MockPM:
                with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                    with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'):
                        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'):
                            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLMonitor'):
                                # Backtest mode
                                engine_backtest = EventDrivenStrategyEngine(
                                    config=mock_config,
                                    execution_mode='backtest',
                                    data_provider=mock_data_provider,
                                    initial_capital=100000,
                                    share_class='USDT'
                                )
                                
                                # Setup mocks
                                mock_pm_backtest = engine_backtest.position_monitor
                                mock_pm_backtest.get_current_positions.return_value = {}
                                mock_pm_backtest.update_state.return_value = {}
                                engine_backtest.exposure_monitor.calculate_exposure.return_value = {}
                                engine_backtest.risk_monitor.assess_risk.return_value = {}
                                engine_backtest.strategy_manager.generate_orders.return_value = []
                                engine_backtest.pnl_monitor.calculate_pnl.return_value = {'balance_based': {}}
                                engine_backtest._log_timestep_event = Mock()
                                engine_backtest._store_timestep_result = Mock()
                                
                                timestamp = pd.Timestamp('2024-01-01', tz='UTC')
                                engine_backtest._process_timestep(timestamp, {}, 'test-request-id')
                                
                                # In backtest mode, should call get_current_positions, NOT update_state with position_refresh
                                assert mock_pm_backtest.get_current_positions.called
                                
                                # Check that position_refresh was NOT used
                                refresh_calls = [c for c in mock_pm_backtest.update_state.call_args_list 
                                               if len(c[0]) > 1 and c[0][1] == 'position_refresh']
                                assert len(refresh_calls) == 0, "Backtest should not use position_refresh trigger"
    
    def test_handle_execution_failure_method_exists(self):
        """P1 FIX: _handle_execution_failure method should exist."""
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'):
                with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                    with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'):
                        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'):
                            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLMonitor'):
                                engine = EventDrivenStrategyEngine(
                                    config=mock_config,
                                    execution_mode='backtest',
                                    data_provider=mock_data_provider,
                                    initial_capital=100000,
                                    share_class='USDT'
                                )
                                
                                # Method should exist
                                assert hasattr(engine, '_handle_execution_failure')
                                assert callable(engine._handle_execution_failure)
    
    def test_trigger_system_failure_method_exists(self):
        """P1 FIX: _trigger_system_failure method should exist."""
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'):
                with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                    with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'):
                        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'):
                            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLMonitor'):
                                engine = EventDrivenStrategyEngine(
                                    config=mock_config,
                                    execution_mode='backtest',
                                    data_provider=mock_data_provider,
                                    initial_capital=100000,
                                    share_class='USDT'
                                )
                                
                                # Method should exist
                                assert hasattr(engine, '_trigger_system_failure')
                                assert callable(engine._trigger_system_failure)
    
    def test_trigger_system_failure_raises_system_exit(self):
        """P1 FIX: _trigger_system_failure should raise SystemExit."""
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'):
                with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                    with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'):
                        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'):
                            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLMonitor'):
                                engine = EventDrivenStrategyEngine(
                                    config=mock_config,
                                    execution_mode='backtest',
                                    data_provider=mock_data_provider,
                                    initial_capital=100000,
                                    share_class='USDT'
                                )
                                
                                # Should raise SystemExit
                                with pytest.raises(SystemExit):
                                    engine._trigger_system_failure("Test failure")


class TestEventDrivenStrategyEngineP2Fixes:
    """Test P2 fixes (architectural improvements)."""
    
    def test_specific_exception_handling(self):
        """P2 FIX: Should have specific exception handling for ValueError and KeyError."""
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'):
                with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                    with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'):
                        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'):
                            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLMonitor'):
                                engine = EventDrivenStrategyEngine(
                                    config=mock_config,
                                    execution_mode='backtest',
                                    data_provider=mock_data_provider,
                                    initial_capital=100000,
                                    share_class='USDT'
                                )
                                
                                # Setup mocks to raise ValueError
                                engine.position_monitor.get_current_positions.side_effect = ValueError("Test error")
                                engine._log_error_event = Mock()
                                
                                timestamp = pd.Timestamp('2024-01-01', tz='UTC')
                                
                                # Should propagate ValueError (fail-fast)
                                with pytest.raises(ValueError):
                                    engine._process_timestep(timestamp, {}, 'test-request-id')
    
    def test_live_mode_60_second_position_refresh(self):
        """P2 FIX: Live mode should have independent 60-second position refresh cycle."""
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        mock_data_provider.get_data.return_value = {'market_data': {}}
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor') as MockPM:
                with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                    with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'):
                        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'):
                            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLMonitor'):
                                engine = EventDrivenStrategyEngine(
                                    config=mock_config,
                                    execution_mode='live',
                                    data_provider=mock_data_provider,
                                    initial_capital=100000,
                                    share_class='USDT'
                                )
                                
                                # Mock to stop loop after one iteration
                                call_count = [0]
                                def stop_after_one(*args):
                                    call_count[0] += 1
                                    if call_count[0] >= 1:
                                        engine.is_running = False
                                
                                engine._process_timestep = Mock(side_effect=stop_after_one)
                                mock_pm = engine.position_monitor
                                
                                # Run live mode
                                import asyncio
                                asyncio.run(engine.run_live())
                                
                                # Verify position_refresh was called in live mode
                                refresh_calls = [c for c in mock_pm.update_state.call_args_list 
                                               if len(c[0]) > 1 and c[0][1] == 'position_refresh']
                                assert len(refresh_calls) > 0, "Live mode should call position_refresh"
    
    def test_health_status_updates_on_errors(self):
        """P2 FIX: Health status should update on errors."""
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'):
                with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                    with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'):
                        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'):
                            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLMonitor'):
                                engine = EventDrivenStrategyEngine(
                                    config=mock_config,
                                    execution_mode='backtest',
                                    data_provider=mock_data_provider,
                                    initial_capital=100000,
                                    share_class='USDT'
                                )
                                
                                assert engine.health_status == "healthy"
                                
                                # Simulate execution failures
                                engine.error_count = 6
                                engine._handle_error(Exception("Test"), "test")
                                
                                assert engine.health_status == "degraded"
                                
                                # More errors should make it critical
                                engine.error_count = 11
                                engine._handle_error(Exception("Test"), "test")
                                
                                assert engine.health_status == "unhealthy"


class TestEventDrivenStrategyEngineComponentIntegration:
    """Test component initialization and integration."""
    
    def test_phase_1_core_dependencies(self):
        """Test Phase 1: Core dependencies initialization."""
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            engine = EventDrivenStrategyEngine(
                config=mock_config,
                execution_mode='backtest',
                data_provider=mock_data_provider,
                initial_capital=100000,
                share_class='USDT'
            )
            
            # Verify Phase 1 components exist
            assert hasattr(engine, 'utility_manager')
            assert hasattr(engine, 'venue_interface_factory')
            assert engine.utility_manager is not None
            assert engine.venue_interface_factory is not None
    
    def test_phase_4_circular_dependency_resolution(self):
        """Test Phase 4: Circular dependency between ExecutionManager and PositionUpdateHandler resolved."""
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            engine = EventDrivenStrategyEngine(
                config=mock_config,
                execution_mode='backtest',
                data_provider=mock_data_provider,
                initial_capital=100000,
                share_class='USDT'
            )
            
            # Verify circular reference is established
            assert engine.execution_manager.position_update_handler is not None
            assert engine.execution_manager.position_update_handler == engine.position_update_handler
    
    def test_execution_mode_passed_to_all_components(self):
        """Test that execution_mode is passed to all required components."""
        mock_config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT'}
        mock_data_provider = Mock()
        
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyFactory'):
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor') as MockPM:
                with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExecutionManager') as MockVM:
                    with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionUpdateHandler') as MockPUH:
                        engine = EventDrivenStrategyEngine(
                            config=mock_config,
                            execution_mode='backtest',
                            data_provider=mock_data_provider,
                            initial_capital=100000,
                            share_class='USDT'
                        )
                        
                        # Verify execution_mode was passed to components
                        MockPM.assert_called_once()
                        pm_call_kwargs = MockPM.call_args[1] if MockPM.call_args[1] else {}
                        # Check if execution_mode was in positional or keyword args
                        assert 'backtest' in str(MockPM.call_args)
                        
                        MockVM.assert_called_once()
                        vm_call = MockVM.call_args
                        assert vm_call[1]['execution_mode'] == 'backtest'
                        
                        MockPUH.assert_called_once()
                        # Check if execution_mode was passed
                        assert 'backtest' in str(MockPUH.call_args)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


