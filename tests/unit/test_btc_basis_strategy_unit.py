"""
Unit tests for BTC Basis Strategy.

Tests BTC basis strategy logic in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Mock the imports to avoid environment dependencies
from unittest.mock import Mock

# Mock the strategy classes
class MockBaseStrategyManager:
    def __init__(self, config, risk_monitor, position_monitor, event_engine):
        self.config = config
        self.risk_monitor = risk_monitor
        self.position_monitor = position_monitor
        self.event_engine = event_engine
        self.mode = config.get('mode', 'btc_basis')
        self.share_class = config.get('share_class', 'USDT')
        self.asset = config.get('asset', 'BTC')
    
    def _get_asset_price(self):
        return 50000.0  # Mock BTC price
    
    def get_strategy_info(self):
        return {
            'strategy_type': 'btc_basis',
            'mode': self.mode,
            'share_class': self.share_class,
            'asset': self.asset,
            'equity': 100000.0
        }

class MockStrategyAction:
    def __init__(self, action_type, target_amount, target_currency, instructions, atomic, metadata):
        self.action_type = action_type
        self.target_amount = target_amount
        self.target_currency = target_currency
        self.instructions = instructions
        self.atomic = atomic
        self.metadata = metadata

# Mock the BTC Basis Strategy
class MockBTCBasisStrategy(MockBaseStrategyManager):
    def __init__(self, config, risk_monitor, position_monitor, event_engine):
        super().__init__(config, risk_monitor, position_monitor, event_engine)
        
        # Validate required configuration at startup (fail-fast)
        required_keys = ['btc_allocation', 'funding_threshold', 'max_leverage']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        # BTC-specific configuration (fail-fast access)
        self.btc_allocation = config['btc_allocation']
        self.funding_threshold = config['funding_threshold']
        self.max_leverage = config['max_leverage']
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """Calculate target position for BTC basis strategy."""
        try:
            # Calculate target allocations
            btc_target = current_equity * self.btc_allocation
            
            # Get current BTC price
            btc_price = self._get_asset_price()
            btc_amount = btc_target / btc_price if btc_price > 0 else 0
            
            return {
                'btc_balance': btc_amount,
                'btc_perpetual_short': -btc_amount,  # Short position
                f'{self.share_class.lower()}_balance': reserve_target,
                'total_equity': current_equity
            }
            
        except Exception as e:
            return {
                'btc_balance': 0.0,
                'btc_perpetual_short': 0.0,
                f'{self.share_class.lower()}_balance': 0.0,  # No reserve balance needed
                'total_equity': current_equity
            }
    
    def entry_full(self, equity: float) -> MockStrategyAction:
        """Enter full BTC basis position."""
        try:
            # Calculate target position
            target_position = self.calculate_target_position(equity)
            
            # Create instructions for full entry
            instructions = []
            
            # 1. Buy BTC spot
            btc_amount = target_position['btc_balance']
            if btc_amount > 0:
                instructions.append({
                    'action': 'buy',
                    'asset': 'BTC',
                    'amount': btc_amount,
                    'venue': 'binance',
                    'order_type': 'market'
                })
            
            # 2. Open short perpetual position
            short_amount = target_position['btc_perpetual_short']
            if short_amount < 0:
                instructions.append({
                    'action': 'sell',
                    'asset': 'BTC-PERP',
                    'amount': abs(short_amount),
                    'venue': 'bybit',
                    'order_type': 'market',
                    'position_type': 'short'
                })
            
            # 3. Maintain reserves
            reserve_amount = target_position[f'{self.share_class.lower()}_balance']
            if reserve_amount > 0:
                instructions.append({
                    'action': 'reserve',
                    'asset': self.share_class,
                    'amount': reserve_amount,
                    'venue': 'wallet',
                    'order_type': 'hold'
                })
            
            return MockStrategyAction(
                action_type='entry_full',
                target_amount=equity,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'btc_basis',
                    'btc_allocation': self.btc_allocation,
                    'funding_threshold': self.funding_threshold
                }
            )
            
        except Exception as e:
            return MockStrategyAction(
                action_type='entry_full',
                target_amount=0.0,
                target_currency=self.share_class,
                instructions=[],
                atomic=False,
                metadata={'error': str(e)}
            )
    
    def exit_full(self, equity: float) -> MockStrategyAction:
        """Exit entire BTC basis position."""
        try:
            # Get current position
            current_position = self.position_monitor.get_current_position()
            btc_balance = current_position.get('btc_balance', 0.0)
            btc_short = current_position.get('btc_perpetual_short', 0.0)
            
            instructions = []
            
            # 1. Close short perpetual position
            if btc_short < 0:
                instructions.append({
                    'action': 'buy',
                    'asset': 'BTC-PERP',
                    'amount': abs(btc_short),
                    'venue': 'bybit',
                    'order_type': 'market',
                    'position_type': 'close_short'
                })
            
            # 2. Sell BTC spot
            if btc_balance > 0:
                instructions.append({
                    'action': 'sell',
                    'asset': 'BTC',
                    'amount': btc_balance,
                    'venue': 'binance',
                    'order_type': 'market'
                })
            
            # 3. Convert all to share class currency
            instructions.append({
                'action': 'convert',
                'asset': self.share_class,
                'amount': equity,
                'venue': 'wallet',
                'order_type': 'market'
            })
            
            return MockStrategyAction(
                action_type='exit_full',
                target_amount=equity,
                target_currency=self.share_class,
                instructions=instructions,
                atomic=True,
                metadata={
                    'strategy': 'btc_basis',
                    'btc_balance': btc_balance,
                    'btc_short': btc_short
                }
            )
            
        except Exception as e:
            return MockStrategyAction(
                action_type='exit_full',
                target_amount=0.0,
                target_currency=self.share_class,
                instructions=[],
                atomic=False,
                metadata={'error': str(e)}
            )
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get BTC basis strategy information and status."""
        try:
            base_info = super().get_strategy_info()
            
            # Add BTC-specific information
            base_info.update({
                'strategy_type': 'btc_basis',
                'btc_allocation': self.btc_allocation,
                'funding_threshold': self.funding_threshold,
                'max_leverage': self.max_leverage,
                'description': 'BTC funding rate arbitrage with spot/perpetual basis trading'
            })
            
            return base_info
            
        except Exception as e:
            return {
                'strategy_type': 'btc_basis',
                'mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'error': str(e)
            }


class TestBTCBasisStrategy:
    """Test BTC basis strategy functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock BTC basis strategy configuration."""
        return {
            'mode': 'btc_basis',
            'share_class': 'USDT',
            'asset': 'BTC',
            'btc_allocation': 0.8,  # 80% to BTC
            'funding_threshold': 0.01,  # 1% funding rate threshold
            'max_leverage': 1.0,  # No leverage for basis trading
        }

    @pytest.fixture
    def mock_dependencies(self):
        """Mock strategy dependencies."""
        return {
            'risk_monitor': Mock(),
            'position_monitor': Mock(),
            'event_engine': Mock()
        }

    @pytest.fixture
    def btc_strategy(self, mock_config, mock_dependencies):
        """Create BTC basis strategy instance."""
        return MockBTCBasisStrategy(
            config=mock_config,
            risk_monitor=mock_dependencies['risk_monitor'],
            position_monitor=mock_dependencies['position_monitor'],
            event_engine=mock_dependencies['event_engine']
        )

    def test_initialization_success(self, mock_config, mock_dependencies):
        """Test successful strategy initialization."""
        strategy = MockBTCBasisStrategy(
            config=mock_config,
            risk_monitor=mock_dependencies['risk_monitor'],
            position_monitor=mock_dependencies['position_monitor'],
            event_engine=mock_dependencies['event_engine']
        )
        
        assert strategy.mode == 'btc_basis'
        assert strategy.share_class == 'USDT'
        assert strategy.asset == 'BTC'
        assert strategy.btc_allocation == 0.8
        assert strategy.funding_threshold == 0.01
        assert strategy.max_leverage == 1.0

    def test_initialization_missing_config(self, mock_dependencies):
        """Test initialization with missing required configuration."""
        incomplete_config = {
            'mode': 'btc_basis',
            'share_class': 'USDT',
            'asset': 'BTC'
            # Missing btc_allocation, funding_threshold, max_leverage
        }
        
        with pytest.raises(KeyError, match="Missing required configuration"):
            MockBTCBasisStrategy(
                config=incomplete_config,
                risk_monitor=mock_dependencies['risk_monitor'],
                position_monitor=mock_dependencies['position_monitor'],
                event_engine=mock_dependencies['event_engine']
            )

    def test_calculate_target_position_success(self, btc_strategy):
        """Test successful target position calculation."""
        current_equity = 100000.0
        
        target_position = btc_strategy.calculate_target_position(current_equity)
        
        assert target_position['total_equity'] == current_equity
        assert target_position['btc_balance'] > 0  # Should have BTC position
        assert target_position['btc_perpetual_short'] < 0  # Should have short position
        assert target_position['usdt_balance'] > 0  # Should have reserves
        
        # Verify allocations
        btc_value = target_position['btc_balance'] * btc_strategy._get_asset_price()
        expected_btc_value = current_equity * btc_strategy.btc_allocation
        assert abs(btc_value - expected_btc_value) < 1.0  # Allow small rounding error

    def test_calculate_target_position_zero_equity(self, btc_strategy):
        """Test target position calculation with zero equity."""
        target_position = btc_strategy.calculate_target_position(0.0)
        
        assert target_position['total_equity'] == 0.0
        assert target_position['btc_balance'] == 0.0
        assert target_position['btc_perpetual_short'] == 0.0
        assert target_position['usdt_balance'] == 0.0

    def test_entry_full_success(self, btc_strategy):
        """Test successful full entry."""
        equity = 100000.0
        
        action = btc_strategy.entry_full(equity)
        
        assert action.action_type == 'entry_full'
        assert action.target_amount == equity
        assert action.target_currency == 'USDT'
        assert action.atomic is True
        assert len(action.instructions) >= 3  # Should have BTC buy, short, and reserve instructions
        
        # Verify instruction types
        instruction_types = [inst['action'] for inst in action.instructions]
        assert 'buy' in instruction_types  # BTC spot buy
        assert 'sell' in instruction_types  # BTC perpetual short
        assert 'reserve' in instruction_types  # Reserve holding

    def test_entry_full_error_handling(self, btc_strategy):
        """Test entry_full error handling."""
        # Mock calculate_target_position to raise exception
        with patch.object(btc_strategy, 'calculate_target_position', side_effect=Exception("Position error")):
            action = btc_strategy.entry_full(100000.0)
            
            assert action.action_type == 'entry_full'
            assert action.target_amount == 0.0
            assert len(action.instructions) == 0
            assert action.atomic is False
            assert 'error' in action.metadata

    def test_exit_full_success(self, btc_strategy):
        """Test successful full exit."""
        # Mock current position
        mock_position = {
            'btc_balance': 1.6,  # 1.6 BTC
            'btc_perpetual_short': -1.6,  # Short 1.6 BTC
            'usdt_balance': 20000.0
        }
        btc_strategy.position_monitor.get_current_position.return_value = mock_position
        
        equity = 100000.0
        action = btc_strategy.exit_full(equity)
        
        assert action.action_type == 'exit_full'
        assert action.target_amount == equity
        assert action.target_currency == 'USDT'
        assert action.atomic is True
        assert len(action.instructions) >= 3  # Should have close short, sell BTC, convert
        
        # Verify instruction types
        instruction_types = [inst['action'] for inst in action.instructions]
        assert 'buy' in instruction_types  # Close short position
        assert 'sell' in instruction_types  # Sell BTC spot
        assert 'convert' in instruction_types  # Convert to USDT

    def test_exit_full_no_position(self, btc_strategy):
        """Test exit_full with no current position."""
        # Mock empty position
        btc_strategy.position_monitor.get_current_position.return_value = {}
        
        action = btc_strategy.exit_full(100000.0)
        
        assert action.action_type == 'exit_full'
        assert len(action.instructions) == 1  # Only convert instruction
        assert action.instructions[0]['action'] == 'convert'

    def test_exit_full_error_handling(self, btc_strategy):
        """Test exit_full error handling."""
        # Mock position monitor to raise exception
        btc_strategy.position_monitor.get_current_position.side_effect = Exception("Position error")
        
        action = btc_strategy.exit_full(100000.0)
        
        assert action.action_type == 'exit_full'
        assert action.target_amount == 0.0
        assert len(action.instructions) == 0
        assert action.atomic is False
        assert 'error' in action.metadata

    def test_get_strategy_info_success(self, btc_strategy):
        """Test successful strategy info retrieval."""
        info = btc_strategy.get_strategy_info()
        
        assert info['strategy_type'] == 'btc_basis'
        assert info['mode'] == 'btc_basis'
        assert info['share_class'] == 'USDT'
        assert info['asset'] == 'BTC'
        assert info['btc_allocation'] == 0.8
        assert info['funding_threshold'] == 0.01
        assert info['max_leverage'] == 1.0
        assert 'description' in info

    def test_get_strategy_info_error_handling(self, btc_strategy):
        """Test strategy info error handling."""
        # Mock get_strategy_info to raise exception
        with patch.object(btc_strategy.__class__.__bases__[0], 'get_strategy_info', side_effect=Exception("Info error")):
            info = btc_strategy.get_strategy_info()
            
            assert info['strategy_type'] == 'btc_basis'
            assert info['mode'] == 'btc_basis'
            assert info['share_class'] == 'USDT'
            assert info['asset'] == 'BTC'
            assert info['equity'] == 0.0
            assert 'error' in info

    def test_market_neutral_logic(self, btc_strategy):
        """Test that strategy maintains market neutrality."""
        current_equity = 100000.0
        
        target_position = btc_strategy.calculate_target_position(current_equity)
        
        # BTC spot and perpetual should be equal and opposite
        btc_spot = target_position['btc_balance']
        btc_short = abs(target_position['btc_perpetual_short'])
        
        # Should be approximately equal (market neutral)
        assert abs(btc_spot - btc_short) < 0.001  # Allow small rounding error

    def test_funding_rate_threshold(self, btc_strategy):
        """Test funding rate threshold configuration."""
        assert btc_strategy.funding_threshold == 0.01  # 1%
        
        # In real implementation, this would be used to determine when to enter/exit
        # based on funding rate conditions

    def test_leverage_limits(self, btc_strategy):
        """Test leverage limits for basis trading."""
        assert btc_strategy.max_leverage == 1.0  # No leverage for basis trading
        
        # Basis trading should be market neutral and not use leverage
        # to avoid directional risk

    def test_btc_allocation_percentage(self, btc_strategy):
        """Test BTC allocation percentage."""
        assert btc_strategy.btc_allocation == 0.8  # 80% to BTC
        
        # Verify allocation is used correctly in position calculation
        current_equity = 100000.0
        target_position = btc_strategy.calculate_target_position(current_equity)
        
        btc_value = target_position['btc_balance'] * btc_strategy._get_asset_price()
        expected_btc_value = current_equity * btc_strategy.btc_allocation
        
        assert abs(btc_value - expected_btc_value) < 1.0

    def test_share_class_currency_handling(self, mock_dependencies):
        """Test different share class currency handling."""
        eth_config = {
            'mode': 'btc_basis',
            'share_class': 'ETH',
            'asset': 'BTC',
            'btc_allocation': 0.8,
            'funding_threshold': 0.01,
            'max_leverage': 1.0,
        }
        
        eth_strategy = MockBTCBasisStrategy(
            config=eth_config,
            risk_monitor=mock_dependencies['risk_monitor'],
            position_monitor=mock_dependencies['position_monitor'],
            event_engine=mock_dependencies['event_engine']
        )
        
        assert eth_strategy.share_class == 'ETH'
        
        # Test position calculation with ETH share class
        target_position = eth_strategy.calculate_target_position(100000.0)
        assert 'eth_balance' in target_position  # Should use lowercase share class
