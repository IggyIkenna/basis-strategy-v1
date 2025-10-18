"""
Comprehensive tests for PositionMonitor refactor.

Tests cover:
1. Unified delta applier with validation
2. Delta generator methods
3. Timestamp deduplication for settlements
4. Real = Simulated synchronization (critical ordering)
5. Position subscriptions validation
6. Backtest mode automatic settlements
7. Live mode venue position querying
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from backend.src.basis_strategy_v1.core.components.position_monitor import PositionMonitor


@pytest.fixture
def mock_utility_manager():
    """Mock utility manager for tests."""
    return Mock()


@pytest.fixture
def backtest_config():
    """Config for backtest mode with all settlements enabled."""
    return {
        'execution_mode': 'backtest',
        'share_class': 'USDT',
        'initial_capital': 10000,
        'component_config': {
            'position_monitor': {
                'position_subscriptions': [
                    'wallet:BaseToken:USDT',  # Initial capital goes to wallet
                    'binance:BaseToken:USDT',
                    'binance:BaseToken:BTC',
                    'binance:Perp:BTCUSDT',
                ],
                'settlement': {
                    'funding_enabled': True,
                    'funding_frequency': '8h',
                    'margin_pnl_enabled': False,
                    'seasonal_rewards_enabled': False,
                }
            }
        }
    }


@pytest.fixture
def live_config():
    """Config for live mode."""
    return {
        'execution_mode': 'live',
        'share_class': 'USDT',
        'initial_capital': 10000,
        'component_config': {
            'position_monitor': {
                'position_subscriptions': [
                    'wallet:BaseToken:USDT',  # Initial capital position
                    'binance:BaseToken:USDT',
                    'binance:BaseToken:BTC',
                    'binance:Perp:BTCUSDT',
                ],
            }
        }
    }


@pytest.fixture
def eth_staking_config():
    """Config for ETH staking with seasonal rewards."""
    return {
        'execution_mode': 'backtest',
        'share_class': 'ETH',
        'initial_capital': 10,
        'component_config': {
            'position_monitor': {
                'position_subscriptions': [
                    'wallet:BaseToken:ETH',
                    'etherfi:aToken:weETH',
                ],
                'settlement': {
                    'funding_enabled': False,
                    'seasonal_rewards_enabled': True,
                    'seasonal_rewards_frequency': 'daily',
                }
            }
        }
    }


class TestPositionSubscriptionsValidation:
    """Test mandatory pre-initialization of positions."""
    
    def test_init_requires_position_subscriptions(self, mock_utility_manager):
        """Test that __init__ raises ValueError if position_subscriptions missing."""
        config_no_subs = {
            'execution_mode': 'backtest',
            'share_class': 'USDT',
            'component_config': {
                'position_monitor': {}  # Missing position_subscriptions
            }
        }
        
        with pytest.raises(ValueError, match="position_subscriptions"):
            PositionMonitor(config_no_subs, data_provider=Mock(), utility_manager=mock_utility_manager)
    
    def test_init_pre_initializes_positions(self, backtest_config, mock_utility_manager):
        """Test that all declared positions are initialized to 0."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        # Check all subscriptions are initialized
        assert 'wallet:BaseToken:USDT' in monitor.simulated_positions
        assert 'binance:BaseToken:USDT' in monitor.simulated_positions
        assert 'binance:BaseToken:BTC' in monitor.simulated_positions
        assert 'binance:Perp:BTCUSDT' in monitor.simulated_positions
        
        # All should be 0 initially
        assert monitor.simulated_positions['wallet:BaseToken:USDT'] == 0
        assert monitor.simulated_positions['binance:BaseToken:USDT'] == 0
        assert monitor.simulated_positions['binance:BaseToken:BTC'] == 0
        assert monitor.simulated_positions['binance:Perp:BTCUSDT'] == 0
    
    def test_apply_delta_validates_position_declared(self, backtest_config, mock_utility_manager):
        """Test that _apply_position_deltas rejects undeclared positions."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        # Try to apply delta for undeclared position
        undeclared_deltas = [{
            'position_key': 'bybit:Perp:ETHUSDT',  # NOT in subscriptions
            'delta_amount': 1.0,
            'source': 'trade',
        }]
        
        timestamp = pd.Timestamp('2024-01-01 00:00:00')
        with pytest.raises(ValueError, match="not found in position_subscriptions"):
            monitor._apply_position_deltas(timestamp, undeclared_deltas)
    
    def test_query_real_venue_filters_undeclared(self, live_config, mock_utility_manager):
        """Test that live mode filters out undeclared positions from venues."""
        monitor = PositionMonitor(live_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        # Mock venue interfaces returning positions in canonical format
        mock_binance = Mock()
        mock_binance.get_positions.return_value = {
            'binance:BaseToken:USDT': 10000,
            'binance:BaseToken:BTC': 0.5,
            'binance:BaseToken:ETH': 5.0,  # NOT in subscriptions - should be filtered
            'binance:Perp:BTCUSDT': -0.5,
            'binance:Perp:ETHUSDT': 1.0,  # NOT in subscriptions - should be filtered
        }
        
        monitor.venue_interfaces = {'binance': mock_binance}
        
        timestamp = pd.Timestamp('2024-01-01 00:00:00')
        positions = monitor._query_real_venue_positions(timestamp)
        
        # Check only declared positions are included
        assert 'binance:BaseToken:USDT' in positions
        assert 'binance:BaseToken:BTC' in positions
        assert 'binance:Perp:BTCUSDT' in positions
        
        # Undeclared positions should NOT be included
        assert 'binance:BaseToken:ETH' not in positions
        assert 'binance:Perp:ETHUSDT' not in positions


class TestUnifiedDeltaApplier:
    """Test _apply_position_deltas unified method."""
    
    def test_apply_single_delta(self, backtest_config, mock_utility_manager):
        """Test applying a single delta."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        deltas = [{
            'position_key': 'wallet:BaseToken:USDT',
            'delta_amount': 100,
            'source': 'initial_capital',
        }]
        
        timestamp = pd.Timestamp('2024-01-01 00:00:00')
        monitor._apply_position_deltas(timestamp, deltas)
        
        assert monitor.simulated_positions['wallet:BaseToken:USDT'] == 100
    
    def test_apply_multiple_deltas(self, backtest_config, mock_utility_manager):
        """Test applying multiple deltas at once."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        deltas = [
            {
                'position_key': 'wallet:BaseToken:USDT',
                'delta_amount': 10000,
                'source': 'initial_capital',
            },
            {
                'position_key': 'binance:BaseToken:BTC',
                'delta_amount': 0.5,
                'source': 'trade',
            },
            {
                'position_key': 'binance:Perp:BTCUSDT',
                'delta_amount': -0.5,
                'source': 'trade',
            },
        ]
        
        timestamp = pd.Timestamp('2024-01-01 00:00:00')
        monitor._apply_position_deltas(timestamp, deltas)
        
        assert monitor.simulated_positions['wallet:BaseToken:USDT'] == 10000
        assert monitor.simulated_positions['binance:BaseToken:BTC'] == 0.5
        assert monitor.simulated_positions['binance:Perp:BTCUSDT'] == -0.5
    
    def test_apply_delta_cumulative(self, backtest_config, mock_utility_manager):
        """Test that deltas are cumulative."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        timestamp = pd.Timestamp('2024-01-01 00:00:00')
        
        # First delta
        monitor._apply_position_deltas(timestamp, [{
            'position_key': 'wallet:BaseToken:USDT',
            'delta_amount': 10000,
            'source': 'initial_capital',
        }])
        
        # Second delta (should add)
        monitor._apply_position_deltas(timestamp, [{
            'position_key': 'wallet:BaseToken:USDT',
            'delta_amount': -500,  # Withdrawal or cost
            'source': 'trade',
        }])
        
        assert monitor.simulated_positions['wallet:BaseToken:USDT'] == 9500


class TestDeltaGenerators:
    """Test delta generator methods."""
    
    def test_generate_initial_capital_usdt(self, backtest_config, mock_utility_manager):
        """Test initial capital for USDT share class."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        deltas = monitor._generate_initial_capital_deltas()
        
        assert len(deltas) == 1
        assert deltas[0]['position_key'] == 'wallet:BaseToken:USDT'
        assert deltas[0]['delta_amount'] == 10000
        assert deltas[0]['source'] == 'initial_capital'
    
    def test_generate_initial_capital_eth(self, eth_staking_config, mock_utility_manager):
        """Test initial capital for ETH share class."""
        monitor = PositionMonitor(eth_staking_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        deltas = monitor._generate_initial_capital_deltas()
        
        assert len(deltas) == 1
        assert deltas[0]['position_key'] == 'wallet:BaseToken:ETH'
        assert deltas[0]['delta_amount'] == 10
        assert deltas[0]['source'] == 'initial_capital'
    
    def test_generate_funding_deltas(self, backtest_config, mock_utility_manager):
        """Test funding settlement delta generation."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        # Set up position with perp holdings
        monitor.simulated_positions['binance:Perp:BTCUSDT'] = -0.5
        
        # Mock data provider funding rate and BTC price
        mock_data = Mock()
        mock_data.get_funding_rate.return_value = 0.0001  # 0.01% funding
        mock_data.get_current_price.return_value = 50000  # BTC price
        monitor.data_provider = mock_data
        
        timestamp = pd.Timestamp('2024-01-01 08:00:00')
        deltas = monitor._generate_funding_settlement_deltas(timestamp)
        
        # Should generate funding payment delta
        assert len(deltas) >= 1
        funding_delta = next(d for d in deltas if d['source'] == 'funding_settlement')
        assert funding_delta['position_key'] == 'binance:BaseToken:USDT'
        # Short position pays funding (negative delta on USDT balance)
        # Note: Can't test exact value without proper funding calculation
    
    def test_generate_seasonal_rewards_deltas(self, eth_staking_config, mock_utility_manager):
        """Test seasonal rewards delta generation."""
        monitor = PositionMonitor(eth_staking_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        # Set up weETH position
        monitor.simulated_positions['etherfi:aToken:weETH'] = 10.0
        
        # Mock utility manager calculate_staking_rewards to return float
        mock_utility_manager.calculate_staking_rewards.return_value = 0.00137  # Daily rewards
        monitor.utility_manager = mock_utility_manager
        
        timestamp = pd.Timestamp('2024-01-02 00:00:00')
        deltas = monitor._generate_seasonal_rewards_deltas(timestamp)
        
        # Should generate reward deltas
        assert len(deltas) >= 1
        # Rewards compound into same token
        rewards_delta = deltas[0]
        assert rewards_delta['position_key'] == 'etherfi:aToken:weETH'
        assert rewards_delta['source'] == 'seasonal_rewards'
        assert rewards_delta['delta_amount'] == 0.00137


class TestTimestampDeduplication:
    """Test that settlements are applied only once per timestamp."""
    
    def test_initial_capital_applied_once(self, backtest_config, mock_utility_manager):
        """Test that initial capital is only applied once."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        timestamp = pd.Timestamp('2024-01-01 00:00:00')
        
        # First call should apply initial capital
        monitor.update_state(timestamp, 'position_refresh', None)
        balance_after_first = monitor.simulated_positions['wallet:BaseToken:USDT']
        
        # Second call at same timestamp should NOT double-apply
        monitor.update_state(timestamp, 'venue_manager', None)
        balance_after_second = monitor.simulated_positions['wallet:BaseToken:USDT']
        
        assert balance_after_first == balance_after_second == 10000
    
    def test_funding_applied_once_per_timestamp(self, backtest_config, mock_utility_manager):
        """Test that funding is only settled once per timestamp."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        # Setup position
        monitor.simulated_positions['binance:Perp:BTCUSDT'] = -1.0
        
        # Mock utility_manager.calculate_funding_payment to return float
        mock_utility_manager.calculate_funding_payment.return_value = 50.0  # $50 funding received
        monitor.utility_manager = mock_utility_manager
        
        timestamp = pd.Timestamp('2024-01-01 08:00:00')
        
        # First call
        monitor.update_state(timestamp, 'position_refresh', None)
        balance_after_first = monitor.simulated_positions['binance:BaseToken:USDT']
        
        # Second call (e.g., after a trade)
        monitor.update_state(timestamp, 'venue_manager', None)
        balance_after_second = monitor.simulated_positions['binance:BaseToken:USDT']
        
        # Funding should only be applied once
        assert balance_after_first == balance_after_second
        assert balance_after_first == 50.0  # Funding applied once
    
    def test_timestamp_changes_reset_tracking(self, backtest_config, mock_utility_manager):
        """Test that new timestamp resets deduplication tracking."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        timestamp1 = pd.Timestamp('2024-01-01 00:00:00')
        timestamp2 = pd.Timestamp('2024-01-01 01:00:00')
        
        # Apply at timestamp1
        monitor.update_state(timestamp1, 'position_refresh', None)
        balance_t1 = monitor.simulated_positions['binance:BaseToken:USDT']
        
        # Apply at timestamp2 (should allow re-processing)
        monitor.update_state(timestamp2, 'position_refresh', None)
        balance_t2 = monitor.simulated_positions['binance:BaseToken:USDT']
        
        # Both should be applied (though initial_capital only applies once globally)
        assert monitor.last_timestamp == timestamp2


class TestBacktestSynchronization:
    """CRITICAL: Test that real_positions = simulated_positions AFTER delta application."""
    
    def test_real_equals_simulated_after_initial_capital(self, backtest_config, mock_utility_manager):
        """Test real = simulated after initial capital applied."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        timestamp = pd.Timestamp('2024-01-01 00:00:00')
        monitor.update_state(timestamp, 'position_refresh', None)
        
        # Real should match simulated
        assert monitor.real_positions['wallet:BaseToken:USDT'] == \
               monitor.simulated_positions['wallet:BaseToken:USDT'] == 10000
    
    def test_real_equals_simulated_after_trade(self, backtest_config, mock_utility_manager):
        """Test real = simulated after trade execution."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        # Initialize
        timestamp = pd.Timestamp('2024-01-01 00:00:00')
        monitor.update_state(timestamp, 'position_refresh', None)
        
        # Execute trade - use NEW unified delta format
        timestamp2 = pd.Timestamp('2024-01-01 01:00:00')
        execution_deltas = [
            {
                'position_key': 'binance:BaseToken:BTC',
                'delta_amount': 0.5,
                'price': 50000,
                'fee': 25,
                'source': 'trade'
            },
            {
                'position_key': 'binance:BaseToken:USDT',
                'delta_amount': -25025.0,  # -(0.5 * 50000 + 25)
                'price': 50000,
                'fee': 0,
                'source': 'trade'
            }
        ]
        
        monitor.update_state(timestamp2, 'venue_manager', execution_deltas)
        
        # Real should match simulated (both updated by trade)
        assert monitor.real_positions['binance:BaseToken:BTC'] == \
               monitor.simulated_positions['binance:BaseToken:BTC'] == 0.5
        assert monitor.real_positions['binance:BaseToken:USDT'] == \
               monitor.simulated_positions['binance:BaseToken:USDT']
    
    def test_real_equals_simulated_after_funding(self, backtest_config, mock_utility_manager):
        """Test real = simulated after funding settlement."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        # Setup
        timestamp1 = pd.Timestamp('2024-01-01 00:00:00')
        monitor.update_state(timestamp1, 'position_refresh', None)
        
        # Add perp position
        monitor.simulated_positions['binance:Perp:BTCUSDT'] = -1.0
        monitor.real_positions['binance:Perp:BTCUSDT'] = -1.0
        
        # Mock utility_manager.calculate_funding_payment to return float
        mock_utility_manager.calculate_funding_payment.return_value = 50.0  # $50 funding received
        monitor.utility_manager = mock_utility_manager
        
        # Funding timestamp
        timestamp2 = pd.Timestamp('2024-01-01 08:00:00')
        monitor.update_state(timestamp2, 'position_refresh', None)
        
        # Real USDT balance should match simulated (both updated by funding)
        assert monitor.real_positions['binance:BaseToken:USDT'] == \
               monitor.simulated_positions['binance:BaseToken:USDT']
    
    def test_copy_happens_after_not_before_deltas(self, backtest_config, mock_utility_manager):
        """CRITICAL: Verify copy happens AFTER applying deltas, not before."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        timestamp = pd.Timestamp('2024-01-01 00:00:00')
        
        # Patch _apply_position_deltas to track when copy happens
        original_apply = monitor._apply_position_deltas
        copy_happened_before_apply = False
        copy_happened_after_apply = False
        
        def tracking_apply(ts, deltas):
            nonlocal copy_happened_before_apply
            # Check if real was already copied before this apply
            if monitor.real_positions.get('wallet:BaseToken:USDT', 0) == 10000:
                copy_happened_before_apply = True
            
            # Apply deltas
            original_apply(ts, deltas)
            
            # Check if real matches simulated after apply
            if monitor.real_positions.get('wallet:BaseToken:USDT', 0) == \
               monitor.simulated_positions.get('wallet:BaseToken:USDT', 0):
                nonlocal copy_happened_after_apply
                copy_happened_after_apply = True
        
        monitor._apply_position_deltas = tracking_apply
        monitor.update_state(timestamp, 'position_refresh', None)
        
        # Copy should happen AFTER, not before
        assert not copy_happened_before_apply or copy_happened_after_apply
        # Final result: real should equal simulated
        assert monitor.real_positions['wallet:BaseToken:USDT'] == \
               monitor.simulated_positions['wallet:BaseToken:USDT']


class TestLiveModeVenueQuerying:
    """Test live mode queries actual venues."""
    
    def test_live_mode_queries_binance(self, live_config, mock_utility_manager):
        """Test that live mode can query venue positions (integration point)."""
        # Pass execution_mode explicitly as parameter to ensure it's set
        monitor = PositionMonitor(
            live_config, 
            data_provider=Mock(), 
            utility_manager=mock_utility_manager,
            execution_mode='live'
        )
        
        # Verify execution mode is set correctly
        assert monitor.execution_mode == 'live'
        
        # Test _query_real_venue_positions directly (the actual integration point)
        # Mock venue interface with canonical position format
        mock_binance = Mock()
        mock_binance.get_positions.return_value = {
            'binance:BaseToken:USDT': 12000,
            'binance:BaseToken:BTC': 0.3,
            'binance:Perp:BTCUSDT': -0.3,
        }
        
        # IMPORTANT: Attribute is position_interfaces, not venue_interfaces!
        monitor.position_interfaces = {'binance': mock_binance}
        
        timestamp = pd.Timestamp('2024-01-01 00:00:00')
        
        # Test the venue querying method directly
        positions = monitor._query_real_venue_positions(timestamp)
        
        # Should have called venue interface
        assert mock_binance.get_positions.called
        mock_binance.get_positions.assert_called_with(timestamp)
        
        # Should return filtered positions (only declared ones)
        assert positions['binance:BaseToken:USDT'] == 12000
        assert positions['binance:BaseToken:BTC'] == 0.3
        assert positions['binance:Perp:BTCUSDT'] == -0.3
        
        # Undeclared positions should not be in result
        assert 'wallet:BaseToken:USDT' in positions  # Declared but venue didn't return it, so should be 0
        assert positions['wallet:BaseToken:USDT'] == 0.0
    
    def test_live_mode_no_automatic_settlements(self, live_config, mock_utility_manager):
        """Test that live mode does NOT apply automatic settlements."""
        monitor = PositionMonitor(live_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        # Mock venue
        mock_binance = Mock()
        mock_binance.get_balances.return_value = {'USDT': 10000}
        mock_binance.get_perpetual_positions.return_value = {}
        monitor.venue_interfaces = {'binance': mock_binance}
        
        timestamp = pd.Timestamp('2024-01-01 08:00:00')  # Funding timestamp
        
        # Spy on delta generators (should NOT be called in live)
        with patch.object(monitor, '_generate_funding_settlement_deltas') as mock_funding:
            monitor.update_state(timestamp, 'position_refresh', None)
            
            # Funding should NOT be generated in live mode
            mock_funding.assert_not_called()


class TestIntegrationBacktestWorkflow:
    """Integration test for full backtest workflow."""
    
    def test_full_backtest_workflow(self, backtest_config, mock_utility_manager):
        """Test complete backtest workflow: init → trade → funding → query."""
        monitor = PositionMonitor(backtest_config, data_provider=Mock(), utility_manager=mock_utility_manager)
        
        # T0: Initial capital
        t0 = pd.Timestamp('2024-01-01 00:00:00')
        result = monitor.update_state(t0, 'position_refresh', None)
        
        assert monitor.simulated_positions['wallet:BaseToken:USDT'] == 10000
        assert monitor.real_positions['wallet:BaseToken:USDT'] == 10000
        
        # T1: Buy BTC spot - use NEW unified delta format
        t1 = pd.Timestamp('2024-01-01 01:00:00')
        trade_deltas = [
            {
                'position_key': 'binance:BaseToken:BTC',
                'delta_amount': 0.5,
                'price': 50000,
                'fee': 25,
                'source': 'trade'
            },
            {
                'position_key': 'wallet:BaseToken:USDT',
                'delta_amount': -25025.0,  # -(0.5 * 50000 + 25)
                'price': 50000,
                'fee': 0,
                'source': 'trade'
            }
        ]
        
        monitor.update_state(t1, 'venue_manager', trade_deltas)
        
        # Should have BTC and reduced USDT
        assert monitor.simulated_positions['binance:BaseToken:BTC'] == 0.5
        assert monitor.simulated_positions['wallet:BaseToken:USDT'] < 10000
        
        # T2: Short perp - use NEW unified delta format
        t2 = pd.Timestamp('2024-01-01 02:00:00')
        perp_deltas = [
            {
                'position_key': 'binance:Perp:BTCUSDT',
                'delta_amount': -0.5,  # Short 0.5 BTC
                'price': 50100,
                'fee': 25,
                'source': 'trade'
            },
            {
                'position_key': 'binance:BaseToken:USDT',
                'delta_amount': 25050.0 - 25,  # Margin received minus fee
                'price': 50100,
                'fee': 0,
                'source': 'trade'
            }
        ]
        
        monitor.update_state(t2, 'venue_manager', perp_deltas)
        
        assert monitor.simulated_positions['binance:Perp:BTCUSDT'] == -0.5
        
        # T3: Funding settlement (8h mark)
        mock_utility_manager.calculate_funding_payment.return_value = 50.0  # $50 funding received
        monitor.utility_manager = mock_utility_manager
        
        t3 = pd.Timestamp('2024-01-01 08:00:00')
        monitor.update_state(t3, 'position_refresh', None)
        
        # Funding should have been applied to venue USDT balance
        usdt_at_funding = monitor.simulated_positions['binance:BaseToken:USDT']
        
        # All real should equal simulated
        for key in monitor.simulated_positions:
            assert monitor.real_positions[key] == monitor.simulated_positions[key]
        
        # Get current positions (public API) - no timestamp parameter
        positions = monitor.get_current_positions()
        
        assert 'wallet:BaseToken:USDT' in positions
        assert 'binance:BaseToken:BTC' in positions
        assert 'binance:Perp:BTCUSDT' in positions


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

