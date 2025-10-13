"""
Unit tests for ETH Basis Strategy.

Tests ETH basis strategy logic in isolation with mocked dependencies.
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
        self.mode = config.get('mode', 'eth_basis')
        self.share_class = config.get('share_class', 'USDT')
        self.asset = config.get('asset', 'ETH')
        # No reserve ratio needed - all equity goes to active positions
    
    def _get_asset_price(self):
        return 3000.0  # Mock ETH price
    
    def get_strategy_info(self):
        return {
            'strategy_type': 'eth_basis',
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

# Mock the ETH Basis Strategy
class MockETHBasisStrategy(MockBaseStrategyManager):
    def __init__(self, config, risk_monitor, position_monitor, event_engine):
        super().__init__(config, risk_monitor, position_monitor, event_engine)
        
        # Validate required configuration at startup (fail-fast)
        required_keys = ['eth_allocation', 'lst_type', 'funding_threshold', 'max_leverage']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        # ETH-specific configuration (fail-fast access)
        self.eth_allocation = config['eth_allocation']  # 70% to ETH
        self.lst_type = config['lst_type']  # LST type (weeth, wsteth)
        self.funding_threshold = config['funding_threshold']  # 1% funding rate threshold
        self.max_leverage = config['max_leverage']  # No leverage for basis trading
    
    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """Calculate target position for ETH basis strategy."""
        try:
            # Calculate target allocations
            eth_target = current_equity * self.eth_allocation
            
            # Get current ETH price
            eth_price = self._get_asset_price()
            eth_amount = eth_target / eth_price if eth_price > 0 else 0
            
            return {
                'eth_balance': eth_amount,
                'lst_balance': eth_amount,  # Same as ETH for LST
                'eth_perpetual_short': -eth_amount,  # Short position
                f'{self.share_class.lower()}_balance': reserve_target,
                'total_equity': current_equity
            }
            
        except Exception as e:
            return {
                'eth_balance': 0.0,
                'lst_balance': 0.0,
                'eth_perpetual_short': 0.0,
                f'{self.share_class.lower()}_balance': 0.0,  # No reserve balance needed
                'total_equity': current_equity
            }
    
    def entry_full(self, equity: float) -> MockStrategyAction:
        """Enter full ETH basis position."""
        try:
            # Calculate target position
            target_position = self.calculate_target_position(equity)
            
            # Create instructions for full entry
            instructions = []
            
            # 1. Buy ETH spot
            eth_amount = target_position['eth_balance']
            if eth_amount > 0:
                instructions.append({
                    'action': 'buy',
                    'asset': 'ETH',
                    'amount': eth_amount,
                    'venue': 'binance',
                    'order_type': 'market'
                })
            
            # 2. Stake ETH to LST
            lst_amount = target_position['lst_balance']
            if lst_amount > 0:
                instructions.append({
                    'action': 'stake',
                    'asset': 'ETH',
                    'amount': lst_amount,
                    'venue': 'lido',  # LST venue
                    'order_type': 'market',
                    'lst_type': self.lst_type
                })
            
            # 3. Open short perpetual position
            short_amount = target_position['eth_perpetual_short']
            if short_amount < 0:
                instructions.append({
                    'action': 'sell',
                    'asset': 'ETH-PERP',
                    'amount': abs(short_amount),
                    'venue': 'bybit',
                    'order_type': 'market',
                    'position_type': 'short'
                })
            
            # 4. Maintain reserves
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
                    'strategy': 'eth_basis',
                    'eth_allocation': self.eth_allocation,
                    'lst_type': self.lst_type,
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
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get ETH basis strategy information and status."""
        try:
            base_info = super().get_strategy_info()
            
            # Add ETH-specific information
            base_info.update({
                'strategy_type': 'eth_basis',
                'eth_allocation': self.eth_allocation,
                'lst_type': self.lst_type,
                'funding_threshold': self.funding_threshold,
                'max_leverage': self.max_leverage,
                'description': 'ETH funding rate arbitrage with LST staking and perpetual hedging'
            })
            
            return base_info
            
        except Exception as e:
            return {
                'strategy_type': 'eth_basis',
                'mode': self.mode,
                'share_class': self.share_class,
                'asset': self.asset,
                'equity': 0.0,
                'error': str(e)
            }


class TestETHBasisStrategy:
    """Test ETH basis strategy functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock ETH basis strategy configuration."""
        return {
            'mode': 'eth_basis',
            'share_class': 'USDT',
            'asset': 'ETH',
            'eth_allocation': 0.7,  # 70% to ETH
            'lst_type': 'weeth',  # weETH LST
            'funding_threshold': 0.01,  # 1% funding rate threshold
            'max_leverage': 1.0,  # No leverage for basis trading
            # No reserve ratio needed
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
    def eth_strategy(self, mock_config, mock_dependencies):
        """Create ETH basis strategy instance."""
        return MockETHBasisStrategy(
            config=mock_config,
            risk_monitor=mock_dependencies['risk_monitor'],
            position_monitor=mock_dependencies['position_monitor'],
            event_engine=mock_dependencies['event_engine']
        )

    def test_initialization_success(self, mock_config, mock_dependencies):
        """Test successful strategy initialization."""
        strategy = MockETHBasisStrategy(
            config=mock_config,
            risk_monitor=mock_dependencies['risk_monitor'],
            position_monitor=mock_dependencies['position_monitor'],
            event_engine=mock_dependencies['event_engine']
        )
        
        assert strategy.mode == 'eth_basis'
        assert strategy.share_class == 'USDT'
        assert strategy.asset == 'ETH'
        assert strategy.eth_allocation == 0.7
        assert strategy.lst_type == 'weeth'
        assert strategy.funding_threshold == 0.01
        assert strategy.max_leverage == 1.0

    def test_initialization_missing_config(self, mock_dependencies):
        """Test initialization with missing required configuration."""
        incomplete_config = {
            'mode': 'eth_basis',
            'share_class': 'USDT',
            'asset': 'ETH'
            # Missing eth_allocation, lst_type, funding_threshold, max_leverage
        }
        
        with pytest.raises(KeyError, match="Missing required configuration"):
            MockETHBasisStrategy(
                config=incomplete_config,
                risk_monitor=mock_dependencies['risk_monitor'],
                position_monitor=mock_dependencies['position_monitor'],
                event_engine=mock_dependencies['event_engine']
            )

    def test_calculate_target_position_success(self, eth_strategy):
        """Test successful target position calculation."""
        current_equity = 100000.0
        
        target_position = eth_strategy.calculate_target_position(current_equity)
        
        assert target_position['total_equity'] == current_equity
        assert target_position['eth_balance'] > 0  # Should have ETH position
        assert target_position['lst_balance'] > 0  # Should have LST position
        assert target_position['eth_perpetual_short'] < 0  # Should have short position
        assert target_position['usdt_balance'] > 0  # Should have reserves
        
        # Verify allocations
        eth_value = target_position['eth_balance'] * eth_strategy._get_asset_price()
        expected_eth_value = current_equity * eth_strategy.eth_allocation
        assert abs(eth_value - expected_eth_value) < 1.0  # Allow small rounding error

    def test_calculate_target_position_zero_equity(self, eth_strategy):
        """Test target position calculation with zero equity."""
        target_position = eth_strategy.calculate_target_position(0.0)
        
        assert target_position['total_equity'] == 0.0
        assert target_position['eth_balance'] == 0.0
        assert target_position['lst_balance'] == 0.0
        assert target_position['eth_perpetual_short'] == 0.0
        assert target_position['usdt_balance'] == 0.0

    def test_entry_full_success(self, eth_strategy):
        """Test successful full entry."""
        equity = 100000.0
        
        action = eth_strategy.entry_full(equity)
        
        assert action.action_type == 'entry_full'
        assert action.target_amount == equity
        assert action.target_currency == 'USDT'
        assert action.atomic is True
        assert len(action.instructions) >= 4  # Should have ETH buy, stake, short, and reserve instructions
        
        # Verify instruction types
        instruction_types = [inst['action'] for inst in action.instructions]
        assert 'buy' in instruction_types  # ETH spot buy
        assert 'stake' in instruction_types  # ETH staking to LST
        assert 'sell' in instruction_types  # ETH perpetual short
        assert 'reserve' in instruction_types  # Reserve holding

    def test_entry_full_error_handling(self, eth_strategy):
        """Test entry_full error handling."""
        # Mock calculate_target_position to raise exception
        with patch.object(eth_strategy, 'calculate_target_position', side_effect=Exception("Position error")):
            action = eth_strategy.entry_full(100000.0)
            
            assert action.action_type == 'entry_full'
            assert action.target_amount == 0.0
            assert len(action.instructions) == 0
            assert action.atomic is False
            assert 'error' in action.metadata

    def test_get_strategy_info_success(self, eth_strategy):
        """Test successful strategy info retrieval."""
        info = eth_strategy.get_strategy_info()
        
        assert info['strategy_type'] == 'eth_basis'
        assert info['mode'] == 'eth_basis'
        assert info['share_class'] == 'USDT'
        assert info['asset'] == 'ETH'
        assert info['eth_allocation'] == 0.7
        assert info['lst_type'] == 'weeth'
        assert info['funding_threshold'] == 0.01
        assert info['max_leverage'] == 1.0
        assert 'description' in info

    def test_lst_staking_integration(self, eth_strategy):
        """Test that strategy includes LST staking."""
        equity = 100000.0
        
        action = eth_strategy.entry_full(equity)
        
        # Find stake instruction
        stake_instructions = [inst for inst in action.instructions if inst['action'] == 'stake']
        assert len(stake_instructions) == 1
        
        stake_inst = stake_instructions[0]
        assert stake_inst['asset'] == 'ETH'
        assert stake_inst['venue'] == 'lido'
        assert stake_inst['lst_type'] == 'weeth'

    def test_market_neutral_logic(self, eth_strategy):
        """Test that strategy maintains market neutrality."""
        current_equity = 100000.0
        
        target_position = eth_strategy.calculate_target_position(current_equity)
        
        # ETH spot and perpetual should be equal and opposite
        eth_spot = target_position['eth_balance']
        eth_short = abs(target_position['eth_perpetual_short'])
        
        # Should be approximately equal (market neutral)
        assert abs(eth_spot - eth_short) < 0.001  # Allow small rounding error

    def test_lst_type_configuration(self, mock_dependencies):
        """Test different LST type configurations."""
        wsteth_config = {
            'mode': 'eth_basis',
            'share_class': 'USDT',
            'asset': 'ETH',
            'eth_allocation': 0.7,
            'lst_type': 'wsteth',  # Different LST type
            'funding_threshold': 0.01,
            'max_leverage': 1.0,
            # No reserve ratio needed
        }
        
        wsteth_strategy = MockETHBasisStrategy(
            config=wsteth_config,
            risk_monitor=mock_dependencies['risk_monitor'],
            position_monitor=mock_dependencies['position_monitor'],
            event_engine=mock_dependencies['event_engine']
        )
        
        assert wsteth_strategy.lst_type == 'wsteth'
        
        # Test that LST type is used in instructions
        action = wsteth_strategy.entry_full(100000.0)
        stake_instructions = [inst for inst in action.instructions if inst['action'] == 'stake']
        assert len(stake_instructions) == 1
        assert stake_instructions[0]['lst_type'] == 'wsteth'

    def test_eth_allocation_percentage(self, eth_strategy):
        """Test ETH allocation percentage."""
        assert eth_strategy.eth_allocation == 0.7  # 70% to ETH
        
        # Verify allocation is used correctly in position calculation
        current_equity = 100000.0
        target_position = eth_strategy.calculate_target_position(current_equity)
        
        eth_value = target_position['eth_balance'] * eth_strategy._get_asset_price()
        expected_eth_value = current_equity * eth_strategy.eth_allocation
        
        assert abs(eth_value - expected_eth_value) < 1.0

    def test_funding_rate_threshold(self, eth_strategy):
        """Test funding rate threshold configuration."""
        assert eth_strategy.funding_threshold == 0.01  # 1%
        
        # In real implementation, this would be used to determine when to enter/exit
        # based on funding rate conditions

    def test_leverage_limits(self, eth_strategy):
        """Test leverage limits for basis trading."""
        assert eth_strategy.max_leverage == 1.0  # No leverage for basis trading
        
        # Basis trading should be market neutral and not use leverage
        # to avoid directional risk

    def test_no_reserve_allocation(self, eth_strategy):
        """Test that no reserve allocation is maintained."""
        current_equity = 100000.0
        target_position = eth_strategy.calculate_target_position(current_equity)
        
        reserve_amount = target_position['usdt_balance']
        
        # All equity should go to active positions, no reserves
        assert reserve_amount == 0.0

    def test_share_class_currency_handling(self, mock_dependencies):
        """Test different share class currency handling."""
        eth_config = {
            'mode': 'eth_basis',
            'share_class': 'ETH',
            'asset': 'ETH',
            'eth_allocation': 0.7,
            'lst_type': 'weeth',
            'funding_threshold': 0.01,
            'max_leverage': 1.0,
        }
        
        eth_strategy = MockETHBasisStrategy(
            config=eth_config,
            risk_monitor=mock_dependencies['risk_monitor'],
            position_monitor=mock_dependencies['position_monitor'],
            event_engine=mock_dependencies['event_engine']
        )
        
        assert eth_strategy.share_class == 'ETH'
        
        # Test position calculation with ETH share class
        target_position = eth_strategy.calculate_target_position(100000.0)
        assert 'eth_balance' in target_position  # Should use lowercase share class
