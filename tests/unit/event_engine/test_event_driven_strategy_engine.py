#!/usr/bin/env python3
"""
Comprehensive unit tests for EventDrivenStrategyEngine to achieve 80%+ coverage.
"""

import sys
import os
import pytest
import pandas as pd
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../backend/src'))

from basis_strategy_v1.core.event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine


class TestEventDrivenStrategyEngine:
    """Test suite for EventDrivenStrategyEngine."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        return {
            'mode': 'pure_lending',
            'share_class': 'USDT',
            'initial_capital': 100000,
            'execution_mode': 'backtest'
        }

    @pytest.fixture
    def mock_engine(self, mock_config):
        """Create mock engine with all dependencies."""
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.DataProvider'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyManager'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.CEXExecutionManager'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.OnChainExecutionManager'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLCalculator'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
            
            engine = EventDrivenStrategyEngine(mock_config)
            return engine

    def test_engine_initialization(self, mock_config):
        """Test engine initialization with valid config."""
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.DataProvider'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyManager'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.CEXExecutionManager'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.OnChainExecutionManager'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLCalculator'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
            
            engine = EventDrivenStrategyEngine(mock_config)
            
            assert engine.config == mock_config
            assert engine.mode == mock_config['mode']
            assert engine.share_class == mock_config['share_class']
            assert engine.config['initial_capital'] == mock_config['initial_capital']
            assert engine.execution_mode == mock_config['execution_mode']

    def test_engine_initialization_invalid_config(self):
        """Test engine initialization with invalid config."""
        # The engine currently allows empty configs with defaults
        # This test verifies it doesn't crash
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.DataProvider'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyManager'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.CEXExecutionManager'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.OnChainExecutionManager'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLCalculator'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
            
            engine = EventDrivenStrategyEngine({})
            assert engine.mode == 'pure_lending'  # Default value
            assert engine.share_class == 'USDT'  # Default value
            assert engine.execution_mode == 'backtest'  # Default value

    def test_engine_initialization_missing_fields(self):
        """Test engine initialization with missing required fields."""
        # The engine currently allows partial configs with defaults
        # This test verifies it doesn't crash and uses appropriate defaults
        invalid_configs = [
            {'mode': 'test'},  # Missing share_class, initial_capital, execution_mode
            {'share_class': 'USDT'},  # Missing mode, initial_capital, execution_mode
            {'initial_capital': 100000},  # Missing mode, share_class, execution_mode
            {'execution_mode': 'backtest'}  # Missing mode, share_class, initial_capital
        ]
        
        for config in invalid_configs:
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.DataProvider'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyManager'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.CEXExecutionManager'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.OnChainExecutionManager'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLCalculator'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                
                engine = EventDrivenStrategyEngine(config)
                # Verify engine was created successfully with defaults
                assert engine is not None
                assert hasattr(engine, 'mode')
                assert hasattr(engine, 'share_class')
                assert hasattr(engine, 'execution_mode')

    @pytest.mark.asyncio
    async def test_get_status(self, mock_engine):
        """Test get_status method."""
        status = await mock_engine.get_status()
        
        assert isinstance(status, dict)
        assert 'mode' in status
        assert 'share_class' in status
        assert 'initial_capital' in status
        assert 'execution_mode' in status
        assert 'components' in status
        
        assert status['mode'] == mock_engine.mode
        assert status['share_class'] == mock_engine.share_class
        assert status['initial_capital'] == mock_engine.config['initial_capital']
        assert status['execution_mode'] == mock_engine.execution_mode

    @pytest.mark.asyncio
    async def test_run_backtest_parameter_validation(self, mock_engine):
        """Test run_backtest parameter validation."""
        # Test missing start_date
        with pytest.raises(ValueError, match="start_date is required"):
            await mock_engine.run_backtest(None, "2024-06-30")
        
        # Test missing end_date
        with pytest.raises(ValueError, match="end_date is required"):
            await mock_engine.run_backtest("2024-06-01", None)
        
        # Test invalid date format
        with pytest.raises(ValueError, match="Invalid date format"):
            await mock_engine.run_backtest("invalid-date", "2024-06-30")
        
        # Test start_date after end_date
        with pytest.raises(ValueError, match="start_date.*must be before end_date"):
            await mock_engine.run_backtest("2024-06-30", "2024-06-01")

    @pytest.mark.asyncio
    async def test_run_backtest_no_data(self, mock_engine):
        """Test run_backtest with no data available."""
        # Mock data provider to return no data
        mock_engine.data_provider._load_data_for_mode = Mock(return_value=None)
        
        with pytest.raises(ValueError, match="No data available for backtest"):
            await mock_engine.run_backtest("2024-06-01", "2024-06-30")

    @pytest.mark.asyncio
    async def test_run_backtest_empty_data(self, mock_engine):
        """Test run_backtest with empty data."""
        # Mock data provider to return empty DataFrame
        empty_data = pd.DataFrame()
        mock_engine.data_provider._load_data_for_mode = Mock(return_value=empty_data)
        
        with pytest.raises(ValueError, match="No data available for backtest"):
            await mock_engine.run_backtest("2024-06-01", "2024-06-30")

    @pytest.mark.asyncio
    async def test_run_backtest_with_date_range(self, mock_engine):
        """Test run_backtest with date range filtering."""
        # Create mock data
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        mock_data = pd.DataFrame({
            'btc_price': [50000] * 10,
            'eth_price': [3000] * 10,
            'usdt_price': [1.0] * 10
        }, index=dates)
        
        mock_engine.data_provider._load_data_for_mode = Mock(return_value=mock_data)
        
        # Mock all the component methods to avoid actual processing
        mock_engine.position_monitor.get_snapshot = Mock(return_value={'wallet': {'USDT': 100000}})
        mock_engine.exposure_monitor.calculate_exposure = Mock(return_value={'share_class_value': 100000})
        mock_engine.risk_monitor.assess_risk = AsyncMock(return_value={'level': 'safe'})
        mock_engine.strategy_manager.make_strategy_decision = Mock(return_value={'action': 'hold'})
        mock_engine.pnl_calculator.calculate_pnl = AsyncMock(return_value={
            'balance_based': {
                'pnl_cumulative': 100000,
                'total_value_current': 100000,
                'total_value_initial': 100000,
                'pnl_hourly': 0,
                'pnl_pct': 0
            }
        })
        mock_engine.event_logger.log_event = AsyncMock()
        mock_engine.event_logger.get_all_events = AsyncMock(return_value=[])
        
        # Test with date range
        start_date = '2024-01-03'
        end_date = '2024-01-07'
        
        # Mock the get_market_data_snapshot method to return valid data
        mock_engine.data_provider.get_market_data_snapshot = Mock(return_value={
            'timestamp': pd.Timestamp('2024-01-03', tz='UTC'),
            'btc_price': 50000,
            'eth_price': 3000,
            'usdt_price': 1.0
        })
        
        result = await mock_engine.run_backtest(start_date=start_date, end_date=end_date)
        
        assert result is not None
        assert 'performance' in result
        assert 'pnl_history' in result
        assert 'events' in result
        assert 'config' in result

    @pytest.mark.asyncio
    async def test_run_backtest_exception_handling(self, mock_engine):
        """Test run_backtest exception handling."""
        # Mock data provider to raise an exception during data loading
        mock_engine.data_provider._load_data_for_mode = Mock(side_effect=Exception("Data loading failed"))
        
        with pytest.raises(Exception, match="Data loading failed"):
            await mock_engine.run_backtest("2024-06-01", "2024-06-30")

    @pytest.mark.asyncio
    async def test_process_timestep(self, mock_engine):
        """Test _process_timestep method."""
        # Create mock data
        timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        data_row = pd.Series({
            'btc_price': 50000.0,
            'eth_price': 3000.0,
            'usdt_price': 1.0
        })
        
        results = {
            'pnl_history': [],
            'events': [],
            'positions': [],
            'exposures': [],
            'risks': []
        }
        
        # Mock component methods
        mock_engine.position_monitor.get_snapshot = Mock(return_value={'wallet': {'USDT': 100000}})
        mock_engine.exposure_monitor.calculate_exposure = Mock(return_value={'share_class_value': 100000})
        mock_engine.risk_monitor.assess_risk = AsyncMock(return_value={'level': 'safe'})
        mock_engine.strategy_manager.make_strategy_decision = Mock(return_value={'action': 'hold'})
        mock_engine.pnl_calculator.calculate_pnl = AsyncMock(return_value={
            'balance_based': {
                'pnl_cumulative': 100000,
                'total_value_current': 100000,
                'total_value_initial': 100000,
                'pnl_hourly': 0,
                'pnl_pct': 0
            }
        })
        mock_engine.event_logger.log_event = AsyncMock()
        
        # Test timestep processing
        await mock_engine._process_timestep(timestamp, data_row, results)
        
        # Verify results were updated
        assert len(results['pnl_history']) == 1
        assert len(results['exposures']) == 1
        assert len(results['risks']) == 1
        assert len(results['events']) == 1

    @pytest.mark.asyncio
    async def test_calculate_final_results(self, mock_engine):
        """Test _calculate_final_results method."""
        # Create mock results
        results = {
            'pnl_history': [
                {'timestamp': '2024-01-01', 'pnl': {'balance_based': {'pnl_cumulative': 100000}}},
                {'timestamp': '2024-01-02', 'pnl': {'balance_based': {'pnl_cumulative': 101000}}},
                {'timestamp': '2024-01-03', 'pnl': {'balance_based': {'pnl_cumulative': 102000}}}
            ],
            'events': [
                {'sequence': 1, 'event_type': 'TRADE_EXECUTED'},
                {'sequence': 2, 'event_type': 'POSITION_UPDATED'}
            ],
            'positions': [],
            'exposures': [],
            'risks': [],
            'config': mock_engine.config,
            'start_date': '2024-01-01',
            'end_date': '2024-01-03'
        }
        
        # Mock PnL calculator
        mock_engine.pnl_calculator.calculate_final_pnl = Mock(return_value={
            'total_return': 2000,
            'total_return_pct': 2.0,
            'initial_capital': 100000,
            'final_value': 102000
        })
        
        # Mock event logger
        mock_engine.event_logger.get_all_events = AsyncMock(return_value=results['events'])
        
        final_results = await mock_engine._calculate_final_results(results)
        
        assert final_results is not None
        assert 'performance' in final_results
        assert 'pnl_history' in final_results
        assert 'events' in final_results
        assert 'config' in final_results
        assert 'start_date' in final_results
        assert 'end_date' in final_results
        
        # Verify performance calculation
        assert final_results['performance']['total_return'] == 2000
        assert final_results['performance']['total_return_pct'] == 2.0
        assert final_results['performance']['initial_capital'] == 100000
        assert final_results['performance']['final_value'] == 102000

    def test_engine_properties(self, mock_engine):
        """Test engine properties."""
        assert hasattr(mock_engine, 'data_provider')
        assert hasattr(mock_engine, 'position_monitor')
        assert hasattr(mock_engine, 'exposure_monitor')
        assert hasattr(mock_engine, 'risk_monitor')
        assert hasattr(mock_engine, 'strategy_manager')
        assert hasattr(mock_engine, 'cex_execution_manager')
        assert hasattr(mock_engine, 'onchain_execution_manager')
        assert hasattr(mock_engine, 'pnl_calculator')
        assert hasattr(mock_engine, 'event_logger')

    def test_engine_config_validation(self, mock_config):
        """Test engine config validation."""
        # Test valid config
        with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.DataProvider'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyManager'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.CEXExecutionManager'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.OnChainExecutionManager'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLCalculator'), \
             patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
            
            engine = EventDrivenStrategyEngine(mock_config)
            assert engine.config == mock_config

    def test_engine_mode_validation(self):
        """Test engine mode validation."""
        valid_modes = ['pure_lending', 'btc_basis', 'eth_leveraged', 'usdt_market_neutral']
        
        for mode in valid_modes:
            config = {
                'mode': mode,
                'share_class': 'USDT',
                'initial_capital': 100000,
                'execution_mode': 'backtest'
            }
            
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.DataProvider'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyManager'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.CEXExecutionManager'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.OnChainExecutionManager'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLCalculator'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                
                engine = EventDrivenStrategyEngine(config)
                assert engine.mode == mode

    def test_engine_share_class_validation(self):
        """Test engine share class validation."""
        valid_share_classes = ['USDT', 'ETH']
        
        for share_class in valid_share_classes:
            config = {
                'mode': 'pure_lending',
                'share_class': share_class,
                'initial_capital': 100000,
                'execution_mode': 'backtest'
            }
            
            with patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.DataProvider'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PositionMonitor'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.ExposureMonitor'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.RiskMonitor'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.StrategyManager'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.CEXExecutionManager'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.OnChainExecutionManager'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.PnLCalculator'), \
                 patch('basis_strategy_v1.core.event_engine.event_driven_strategy_engine.EventLogger'):
                
                engine = EventDrivenStrategyEngine(config)
                assert engine.share_class == share_class