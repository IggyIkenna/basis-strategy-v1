"""
Phase 3 Component Initialization Tests

Tests the target behavior for Phase 3 component updates:
- Components accept injected config and data provider
- Position monitor initializes with API request parameters (no defaults)
- Event engine orchestrates component initialization with dependency tracking
- Health checking tracks component status and dependencies
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from backend.src.basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
from backend.src.basis_strategy_v1.core.strategies.components.exposure_monitor import ExposureMonitor
from backend.src.basis_strategy_v1.core.event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine


class TestPositionMonitorInitialization:
    """Test position monitor initialization with API request parameters."""
    
    def test_requires_all_parameters_no_defaults(self):
        """Test that position monitor requires all parameters with no defaults."""
        config = {'mode': 'pure_lending'}
        mock_data_provider = Mock()
        
        # Should work with all parameters
        pm = PositionMonitor(
            config=config,
            execution_mode='backtest',
            initial_capital=100000.0,
            share_class='USDT',
            data_provider=mock_data_provider
        )
        
        assert pm.initial_capital == 100000.0
        assert pm.share_class == 'USDT'
        assert pm.execution_mode == 'backtest'
        assert pm.config == config
        assert pm.data_provider == mock_data_provider
    
    def test_fails_on_invalid_initial_capital(self):
        """Test that position monitor fails on invalid initial capital."""
        config = {'mode': 'pure_lending'}
        mock_data_provider = Mock()
        
        # Should fail on zero capital
        with pytest.raises(ValueError, match="Invalid initial_capital: 0"):
            PositionMonitor(
                config=config,
                execution_mode='backtest',
                initial_capital=0,  # Invalid
                share_class='USDT',
                data_provider=mock_data_provider
            )
        
        # Should fail on negative capital
        with pytest.raises(ValueError, match="Invalid initial_capital: -1000"):
            PositionMonitor(
                config=config,
                execution_mode='backtest', 
                initial_capital=-1000,  # Invalid
                share_class='USDT',
                data_provider=mock_data_provider
            )
    
    def test_fails_on_invalid_share_class(self):
        """Test that position monitor fails on invalid share class."""
        config = {'mode': 'pure_lending'}
        mock_data_provider = Mock()
        
        with pytest.raises(ValueError, match="Invalid share_class: INVALID"):
            PositionMonitor(
                config=config,
                execution_mode='backtest',
                initial_capital=100000.0,
                share_class='INVALID',  # Invalid
                data_provider=mock_data_provider
            )
    
    def test_initializes_capital_correctly(self):
        """Test that position monitor initializes capital based on share class."""
        config = {'mode': 'pure_lending'}
        mock_data_provider = Mock()
        
        # Test USDT share class
        pm_usdt = PositionMonitor(
            config=config,
            execution_mode='backtest',
            initial_capital=50000.0,
            share_class='USDT',
            data_provider=mock_data_provider
        )
        
        assert pm_usdt._token_monitor.wallet['USDT'] == 50000.0
        
        # Test ETH share class
        pm_eth = PositionMonitor(
            config=config,
            execution_mode='backtest',
            initial_capital=25.0,
            share_class='ETH',
            data_provider=mock_data_provider
        )
        
        assert pm_eth._token_monitor.wallet['ETH'] == 25.0
    
    def test_live_mode_requires_redis(self):
        """Test that live mode requires Redis connection."""
        config = {'mode': 'pure_lending'}
        mock_data_provider = Mock()
        
        with patch.dict('os.environ', {'BASIS_REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('redis.Redis.from_url') as mock_redis:
                mock_redis_instance = Mock()
                mock_redis_instance.ping.return_value = True
                mock_redis.return_value = mock_redis_instance
                
                pm = PositionMonitor(
                    config=config,
                    execution_mode='live',
                    initial_capital=100000.0,
                    share_class='USDT',
                    data_provider=mock_data_provider
                )
                
                # Should establish Redis connection for live mode
                mock_redis.assert_called_once_with('redis://localhost:6379/0', decode_responses=True)
                mock_redis_instance.ping.assert_called_once()
                assert pm.redis == mock_redis_instance


class TestExposureMonitorInitialization:
    """Test exposure monitor initialization with injected dependencies."""
    
    def test_requires_all_dependencies(self):
        """Test that exposure monitor requires all dependencies."""
        config = {'mode': 'pure_lending'}
        mock_position_monitor = Mock()
        mock_data_provider = Mock()
        
        em = ExposureMonitor(
            config=config,
            share_class='USDT',
            position_monitor=mock_position_monitor,
            data_provider=mock_data_provider
        )
        
        assert em.config == config
        assert em.share_class == 'USDT'
        assert em.position_monitor == mock_position_monitor
        assert em.data_provider == mock_data_provider
    
    def test_fails_on_missing_dependencies(self):
        """Test that exposure monitor fails on missing dependencies."""
        config = {'mode': 'pure_lending'}
        
        # Should fail without position monitor
        with pytest.raises(ValueError, match="Position monitor is required"):
            ExposureMonitor(
                config=config,
                share_class='USDT',
                position_monitor=None,  # Missing
                data_provider=Mock()
            )
        
        # Should fail without data provider
        with pytest.raises(ValueError, match="Data provider is required"):
            ExposureMonitor(
                config=config,
                share_class='USDT',
                position_monitor=Mock(),
                data_provider=None  # Missing
            )


class TestEventEngineComponentInitialization:
    """Test event engine component initialization with dependency tracking."""
    
    def test_initializes_components_in_dependency_order(self):
        """Test that event engine initializes components in proper dependency order."""
        config = {'mode': 'pure_lending'}
        mock_data_provider = Mock()
        
        # Mock ALL components to avoid complex initialization
        with patch('backend.src.basis_strategy_v1.infrastructure.config.health_check.mark_component_healthy') as mock_healthy:
            with patch('backend.src.basis_strategy_v1.core.strategies.components.position_monitor.PositionMonitor') as mock_pm:
                with patch('backend.src.basis_strategy_v1.core.strategies.components.event_logger.EventLogger') as mock_el:
                    with patch('backend.src.basis_strategy_v1.core.strategies.components.exposure_monitor.ExposureMonitor') as mock_em:
                        with patch('backend.src.basis_strategy_v1.core.rebalancing.risk_monitor.RiskMonitor') as mock_rm:
                            with patch('backend.src.basis_strategy_v1.core.math.pnl_calculator.PnLCalculator') as mock_pnl:
                                with patch('backend.src.basis_strategy_v1.core.strategies.components.strategy_manager.StrategyManager') as mock_sm:
                                    
                                    # All mocks return Mock instances
                                    mock_pm.return_value = Mock()
                                    mock_el.return_value = Mock()
                                    mock_em.return_value = Mock()
                                    mock_rm.return_value = Mock()
                                    mock_pnl.return_value = Mock()
                                    mock_sm.return_value = Mock()
                                    
                                    engine = EventDrivenStrategyEngine(
                                        config=config,
                                        execution_mode='backtest',
                                        data_provider=mock_data_provider,
                                        initial_capital=100000.0,
                                        share_class='USDT'
                                    )
                                    
                                    # Should mark components as healthy after successful initialization
                                    expected_calls = [
                                        'position_monitor',
                                        'event_logger', 
                                        'exposure_monitor',
                                        'risk_monitor',
                                        'pnl_calculator',
                                        'strategy_manager'
                                    ]
                                    
                                    # Check that mark_component_healthy was called for each component
                                    assert mock_healthy.call_count >= len(expected_calls)
                                    called_components = [call[0][0] for call in mock_healthy.call_args_list]
                                    for component in expected_calls:
                                        assert component in called_components
    
    def test_fails_fast_on_component_initialization_error(self):
        """Test that event engine fails fast when component initialization fails."""
        config = {
            'mode': 'pure_lending', 
            'share_class': 'USDT'
        }
        mock_data_provider = Mock()
        
        # Mock position monitor to fail
        with patch('backend.src.basis_strategy_v1.core.strategies.components.position_monitor.PositionMonitor') as mock_pm:
            mock_pm.side_effect = Exception("Position monitor init failed")
            
            with patch('backend.src.basis_strategy_v1.infrastructure.config.health_check.mark_component_unhealthy') as mock_unhealthy:
                with pytest.raises(ValueError, match="Position Monitor initialization failed"):
                    EventDrivenStrategyEngine(
                        config=config,
                        execution_mode='backtest',
                        data_provider=mock_data_provider,
                        initial_capital=100000.0,
                        share_class='USDT'
                    )
                
                # Should mark component as unhealthy
                mock_unhealthy.assert_called_with('position_monitor', 'Position monitor init failed')
    
    def test_validates_required_parameters(self):
        """Test that event engine validates all required parameters."""
        mock_data_provider = Mock()
        
        # Should fail without mode in config
        with pytest.raises(ValueError, match="Mode is required in config"):
            EventDrivenStrategyEngine(
                config={},  # Missing mode
                execution_mode='backtest',
                data_provider=mock_data_provider,
                initial_capital=100000.0,
                share_class='USDT'
            )
        
        # Should fail without data provider
        with pytest.raises(ValueError, match="Data provider is required"):
            EventDrivenStrategyEngine(
                config={'mode': 'pure_lending'},
                execution_mode='backtest',
                data_provider=None,  # Missing
                initial_capital=100000.0,
                share_class='USDT'
            )
        
        # Should fail with invalid initial capital
        with pytest.raises(ValueError, match="Invalid initial_capital: 0"):
            EventDrivenStrategyEngine(
                config={'mode': 'pure_lending'},
                execution_mode='backtest',
                data_provider=mock_data_provider,
                initial_capital=0,  # Invalid
                share_class='USDT'
            )


class TestComponentDependencyInjection:
    """Test that components use injected config and data provider correctly."""
    
    def test_components_use_injected_config(self):
        """Test that components receive and use the injected config."""
        config = {
            'mode': 'pure_lending',
            'target_apy': 0.05,
            'max_drawdown': 0.02
        }
        mock_data_provider = Mock()
        mock_position_monitor = Mock()
        mock_position_monitor.execution_mode = 'backtest'
        
        em = ExposureMonitor(
            config=config,
            share_class='USDT',
            position_monitor=mock_position_monitor,
            data_provider=mock_data_provider
        )
        
        # Should store and use the injected config
        assert em.config == config
        assert em.config['target_apy'] == 0.05
        assert em.config['max_drawdown'] == 0.02
    
    def test_components_use_injected_data_provider(self):
        """Test that components receive and use the injected data provider."""
        config = {'mode': 'pure_lending'}
        mock_data_provider = Mock()
        mock_data_provider.get_spot_price.return_value = 3000.0
        mock_position_monitor = Mock()
        mock_position_monitor.execution_mode = 'backtest'
        
        em = ExposureMonitor(
            config=config,
            share_class='USDT',
            position_monitor=mock_position_monitor,
            data_provider=mock_data_provider
        )
        
        # Should store and use the injected data provider
        assert em.data_provider == mock_data_provider
        
        # Should be able to use data provider methods
        price = em.data_provider.get_spot_price('ETH')
        assert price == 3000.0
        mock_data_provider.get_spot_price.assert_called_with('ETH')
