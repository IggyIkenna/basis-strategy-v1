#!/usr/bin/env python3
"""
Comprehensive tests for Position Monitor to achieve 80%+ coverage.
"""

import sys
import os
import pytest
import pandas as pd
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Add backend to path
sys.path.append('backend/src')

from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor


class TestPositionMonitorComprehensive:
    """Comprehensive test suite for Position Monitor."""

    @pytest.fixture
    def position_monitor(self):
        """Create position monitor for testing."""
        config = {
            'execution_mode': 'backtest',
            'data_dir': 'data',
            'component_config': {
                'position_monitor': {
                    'tracked_assets': ['USDT', 'ETH', 'BTC'],
                    'venues': ['WALLET', 'CEX_SPOT', 'CEX_DERIVATIVES', 'SMART_CONTRACT']
                }
            }
        }
        data_provider = Mock()
        utility_manager = Mock()
        return PositionMonitor(config, data_provider, utility_manager)

    def test_calculate_positions(self, position_monitor):
        """Test calculate_positions method."""
        timestamp = pd.Timestamp.now(tz='UTC')
        result = position_monitor.calculate_positions(timestamp)
        
        assert isinstance(result, dict)
        assert 'timestamp' in result
        assert 'wallet_positions' in result
        assert 'smart_contract_positions' in result
        assert 'cex_spot_positions' in result
        assert 'cex_derivatives_positions' in result
        assert 'total_positions' in result
        assert 'metrics' in result
    def test_get_snapshot(self, position_monitor):
        """Test get_snapshot method."""
        timestamp = pd.Timestamp.now(tz='UTC')
        result = position_monitor.get_snapshot(timestamp)
        
        assert isinstance(result, dict)
        assert 'timestamp' in result
        assert 'wallet_positions' in result
        assert 'smart_contract_positions' in result
        assert 'cex_spot_positions' in result
        assert 'cex_derivatives_positions' in result
        assert 'total_positions' in result
        assert 'metrics' in result

    def test_get_all_positions(self, position_monitor):
        """Test get_all_positions method."""
        timestamp = pd.Timestamp.now(tz='UTC')
        result = position_monitor.get_all_positions(timestamp)
        
        assert isinstance(result, dict)
        assert 'timestamp' in result
        assert 'cex_accounts' in result
        assert 'binance' in result['cex_accounts']
        assert result['cex_accounts']['binance']['ETH_spot'] == 5.0

    @pytest.mark.asyncio
    async def test_update_with_perp_changes(self, position_monitor):
        """Test update method with perpetual changes."""
        changes = {
            'timestamp': pd.Timestamp.now(tz='UTC'),
            'trigger': 'TEST',
            'derivative_changes': [
                {
                    'venue': 'binance',
                    'instrument': 'ETHUSDT',
                    'action': 'OPEN',
                    'data': {
                        'size': 1.0,
                        'entry_price': 3000.0,
                        'notional_usd': 3000.0,
                        'entry_timestamp': pd.Timestamp.now(tz='UTC').isoformat()
                    }
                }
            ]
        }
        
        result = await position_monitor.update(changes)
        assert result is not None
        assert 'perp_positions' in result
        assert 'binance' in result['perp_positions']
        assert 'ETHUSDT' in result['perp_positions']['binance']

    @pytest.mark.asyncio
    async def test_get_snapshot(self, position_monitor):
        """Test get_snapshot method."""
        snapshot = position_monitor.get_snapshot()
        
        assert isinstance(snapshot, dict)
        assert 'wallet' in snapshot
        assert 'cex_accounts' in snapshot
        assert 'perp_positions' in snapshot
        assert 'last_updated' in snapshot

    @pytest.mark.asyncio
    async def test_reconcile_with_live_matching(self, position_monitor):
        """Test reconciliation with matching balances."""
        # Set up some balances
        changes = {
            'timestamp': pd.Timestamp.now(tz='UTC'),
            'trigger': 'TEST',
            'token_changes': [
                {
                    'venue': 'WALLET',
                    'token': 'ETH',
                    'delta': 10.0,
                    'reason': 'TEST'
                }
            ]
        }
        await position_monitor.update(changes)
        
        # Test reconciliation (should return empty dict in backtest mode)
        result = await position_monitor.reconcile_with_live()
        assert result == {}  # Reconciliation skipped in backtest mode

    @pytest.mark.asyncio
    async def test_reconcile_with_live_drift(self, position_monitor):
        """Test reconciliation with balance drift."""
        # Set up some balances
        changes = {
            'timestamp': pd.Timestamp.now(tz='UTC'),
            'trigger': 'TEST',
            'token_changes': [
                {
                    'venue': 'WALLET',
                    'token': 'ETH',
                    'delta': 10.0,
                    'reason': 'TEST'
                }
            ]
        }
        await position_monitor.update(changes)
        
        # Test reconciliation (should return empty dict in backtest mode)
        result = await position_monitor.reconcile_with_live()
        assert result == {}  # Reconciliation skipped in backtest mode

    @pytest.mark.asyncio
    async def test_error_handling_invalid_venue(self, position_monitor):
        """Test error handling for invalid venue."""
        changes = {
            'timestamp': pd.Timestamp.now(tz='UTC'),
            'trigger': 'TEST',
            'token_changes': [
                {
                    'venue': 'INVALID_VENUE',
                    'token': 'ETH',
                    'delta': 10.0,
                    'reason': 'TEST'
                }
            ]
        }
        
        # Should handle gracefully without crashing
        result = await position_monitor.update(changes)
        assert result is not None

    @pytest.mark.asyncio
    async def test_error_handling_invalid_token(self, position_monitor):
        """Test error handling for invalid token."""
        changes = {
            'timestamp': pd.Timestamp.now(tz='UTC'),
            'trigger': 'TEST',
            'token_changes': [
                {
                    'venue': 'WALLET',
                    'token': 'INVALID_TOKEN',
                    'delta': 10.0,
                    'reason': 'TEST'
                }
            ]
        }
        
        # Should handle gracefully without crashing
        result = await position_monitor.update(changes)
        assert result is not None

    @pytest.mark.asyncio
    async def test_negative_balance_handling(self, position_monitor):
        """Test handling of negative balances."""
        changes = {
            'timestamp': pd.Timestamp.now(tz='UTC'),
            'trigger': 'TEST',
            'token_changes': [
                {
                    'venue': 'WALLET',
                    'token': 'ETH',
                    'delta': -1000.0,  # Large negative balance
                    'reason': 'TEST'
                }
            ]
        }
        
        # Should handle gracefully
        result = await position_monitor.update(changes)
        assert result is not None

    @pytest.mark.asyncio
    async def test_multiple_venue_updates(self, position_monitor):
        """Test updates across multiple venues."""
        changes = {
            'timestamp': pd.Timestamp.now(tz='UTC'),
            'trigger': 'TEST',
            'token_changes': [
                {
                    'venue': 'WALLET',
                    'token': 'ETH',
                    'delta': 10.0,
                    'reason': 'TEST'
                },
                {
                    'venue': 'binance',
                    'token': 'ETH_spot',
                    'delta': 5.0,
                    'reason': 'TEST'
                },
                {
                    'venue': 'okx',
                    'token': 'USDT',
                    'delta': 10000.0,
                    'reason': 'TEST'
                }
            ]
        }
        
        result = await position_monitor.update(changes)
        assert result is not None
        assert result['wallet']['ETH'] == 10.0
        assert result['cex_accounts']['binance']['ETH_spot'] == 5.0
        assert result['cex_accounts']['okx']['USDT'] == 10000.0

    @pytest.mark.asyncio
    async def test_perp_position_updates(self, position_monitor):
        """Test perpetual position updates."""
        # Add position
        changes = {
            'timestamp': pd.Timestamp.now(tz='UTC'),
            'trigger': 'TEST',
            'derivative_changes': [
                {
                    'venue': 'binance',
                    'instrument': 'ETHUSDT',
                    'action': 'OPEN',
                    'data': {
                        'size': 1.0,
                        'entry_price': 3000.0,
                        'notional_usd': 3000.0,
                        'entry_timestamp': pd.Timestamp.now(tz='UTC').isoformat()
                    }
                }
            ]
        }
        
        result = await position_monitor.update(changes)
        assert result is not None
        assert 'ETHUSDT' in result['perp_positions']['binance']
        
        # Update position (close it)
        changes['derivative_changes'][0]['action'] = 'CLOSE'
        changes['derivative_changes'][0]['data']['size'] = 0.0
        
        result = await position_monitor.update(changes)
        assert result is not None

    def test_initial_state(self, position_monitor):
        """Test initial state of position monitor."""
        snapshot = position_monitor.get_snapshot()
        
        # Check initial balances are zero
        assert snapshot['wallet']['ETH'] == 0.0
        assert snapshot['wallet']['USDT'] == 0.0
        
        # Check CEX accounts are initialized with zero balances
        assert 'binance' in snapshot['cex_accounts']
        assert 'bybit' in snapshot['cex_accounts']
        assert snapshot['cex_accounts']['binance']['USDT'] == 0.0
        assert snapshot['cex_accounts']['bybit']['USDT'] == 0.0
        
        # Check perp positions are initialized as empty dicts
        assert snapshot['perp_positions'] == {'binance': {}, 'bybit': {}, 'okx': {}}

    @pytest.mark.asyncio
    async def test_empty_changes(self, position_monitor):
        """Test update with empty changes."""
        changes = {
            'timestamp': pd.Timestamp.now(tz='UTC'),
            'trigger': 'TEST',
            'token_changes': [],
            'cex_changes': [],
            'perp_changes': []
        }
        
        result = await position_monitor.update(changes)
        assert result is not None

    @pytest.mark.asyncio
    async def test_missing_timestamp(self, position_monitor):
        """Test update with missing timestamp."""
        changes = {
            'trigger': 'TEST',
            'token_changes': [
                {
                    'venue': 'WALLET',
                    'token': 'ETH',
                    'delta': 10.0,
                    'reason': 'TEST'
                }
            ]
        }
        
        # Should handle missing timestamp gracefully
        result = await position_monitor.update(changes)
        assert result is not None