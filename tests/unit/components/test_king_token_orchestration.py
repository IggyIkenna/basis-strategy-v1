"""
Test KING Token Orchestration Functionality

Tests the StrategyManager's KING token detection and orchestration functionality.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, AsyncMock
import sys
import os

# Add backend to path
sys.path.append('/workspace/backend/src')

from basis_strategy_v1.core.strategies.components.strategy_manager import StrategyManager


class TestKingTokenOrchestration:
    """Test KING token orchestration functionality."""
    
    @pytest.fixture
    def strategy_manager(self):
        """Create StrategyManager for testing."""
        config = {
            'strategy': {
                'share_class': 'USDT',
                'asset': 'ETH',
                'lst_type': 'weeth'
            },
            'backtest': {
                'initial_capital': 100000.0
            }
        }
        
        # Mock components
        exposure_monitor = Mock()
        risk_monitor = Mock()
        
        return StrategyManager(config, exposure_monitor, risk_monitor)
    
    @pytest.mark.asyncio
    async def test_king_balance_below_threshold(self, strategy_manager):
        """Test that KING balance below threshold returns None."""
        position_snapshot = {
            'wallet': {
                'KING': 1.0,  # $1.0 value (below $300 threshold)
                'ETH': 1.0,
                'USDT': 1000.0
            }
        }
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        
        result = await strategy_manager.handle_king_token_management(position_snapshot, timestamp)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_king_balance_above_threshold(self, strategy_manager):
        """Test that KING balance above threshold generates unwrap instruction."""
        position_snapshot = {
            'wallet': {
                'KING': 5000.0,  # $5000 value (above $3000 threshold)
                'ETH': 1.0,
                'USDT': 1000.0
            }
        }
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        
        result = await strategy_manager.handle_king_token_management(position_snapshot, timestamp)
        
        assert result is not None
        assert result['type'] == 'UNWRAP_AND_SELL_KING'
        assert result['priority'] == 2
        assert len(result['actions']) == 1
        
        action = result['actions'][0]
        assert action['action'] == 'unwrap_and_sell_king_tokens'
        assert action['executor'] == 'onchain_execution_manager'
        assert action['params']['king_balance'] == 5000.0
        assert action['params']['timestamp'] == timestamp
        
        metadata = result['metadata']
        assert metadata['king_balance'] == 5000.0
        assert metadata['king_value_usd'] == 5000.0
        assert metadata['threshold_usd'] == 3000.0  # 0.01 * 3000 * 100
        assert metadata['trigger'] == 'KING_THRESHOLD_EXCEEDED'
    
    @pytest.mark.asyncio
    async def test_no_king_balance(self, strategy_manager):
        """Test that no KING balance returns None."""
        position_snapshot = {
            'wallet': {
                'ETH': 1.0,
                'USDT': 1000.0
                # No KING balance
            }
        }
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        
        result = await strategy_manager.handle_king_token_management(position_snapshot, timestamp)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_zero_king_balance(self, strategy_manager):
        """Test that zero KING balance returns None."""
        position_snapshot = {
            'wallet': {
                'KING': 0.0,  # Zero balance
                'ETH': 1.0,
                'USDT': 1000.0
            }
        }
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        
        result = await strategy_manager.handle_king_token_management(position_snapshot, timestamp)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_negative_king_balance(self, strategy_manager):
        """Test that negative KING balance returns None."""
        position_snapshot = {
            'wallet': {
                'KING': -10.0,  # Negative balance
                'ETH': 1.0,
                'USDT': 1000.0
            }
        }
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        
        result = await strategy_manager.handle_king_token_management(position_snapshot, timestamp)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_exactly_at_threshold(self, strategy_manager):
        """Test that KING balance exactly at threshold returns None."""
        position_snapshot = {
            'wallet': {
                'KING': 3000.0,  # Exactly $3000 (at threshold)
                'ETH': 1.0,
                'USDT': 1000.0
            }
        }
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        
        result = await strategy_manager.handle_king_token_management(position_snapshot, timestamp)
        
        # Should return None because it's not > threshold (it's == threshold)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_just_above_threshold(self, strategy_manager):
        """Test that KING balance just above threshold generates instruction."""
        position_snapshot = {
            'wallet': {
                'KING': 3000.01,  # Just above $3000 threshold
                'ETH': 1.0,
                'USDT': 1000.0
            }
        }
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        
        result = await strategy_manager.handle_king_token_management(position_snapshot, timestamp)
        
        assert result is not None
        assert result['type'] == 'UNWRAP_AND_SELL_KING'
        assert result['metadata']['king_balance'] == 3000.01
        assert result['metadata']['king_value_usd'] == 3000.01
    
    @pytest.mark.asyncio
    async def test_missing_wallet_section(self, strategy_manager):
        """Test that missing wallet section returns None."""
        position_snapshot = {
            'cex_accounts': {
                'binance': {'USDT': 1000.0}
            }
            # No wallet section
        }
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        
        result = await strategy_manager.handle_king_token_management(position_snapshot, timestamp)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_empty_wallet_section(self, strategy_manager):
        """Test that empty wallet section returns None."""
        position_snapshot = {
            'wallet': {}  # Empty wallet
        }
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        
        result = await strategy_manager.handle_king_token_management(position_snapshot, timestamp)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_instruction_structure(self, strategy_manager):
        """Test that generated instruction has correct structure."""
        position_snapshot = {
            'wallet': {
                'KING': 10000.0,  # Well above threshold
                'ETH': 1.0,
                'USDT': 1000.0
            }
        }
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        
        result = await strategy_manager.handle_king_token_management(position_snapshot, timestamp)
        
        # Verify instruction structure
        assert isinstance(result, dict)
        assert 'priority' in result
        assert 'type' in result
        assert 'actions' in result
        assert 'metadata' in result
        
        # Verify actions structure
        assert isinstance(result['actions'], list)
        assert len(result['actions']) == 1
        
        action = result['actions'][0]
        assert 'action' in action
        assert 'params' in action
        assert 'executor' in action
        
        # Verify metadata structure
        metadata = result['metadata']
        assert 'king_balance' in metadata
        assert 'king_value_usd' in metadata
        assert 'threshold_usd' in metadata
        assert 'trigger' in metadata
    
    @pytest.mark.asyncio
    async def test_error_handling(self, strategy_manager):
        """Test error handling with invalid input."""
        # Test with None input
        result = await strategy_manager.handle_king_token_management(None, pd.Timestamp('2024-01-01', tz='UTC'))
        assert result is None
        
        # Test with invalid timestamp
        position_snapshot = {'wallet': {'KING': 500.0}}
        result = await strategy_manager.handle_king_token_management(position_snapshot, None)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])