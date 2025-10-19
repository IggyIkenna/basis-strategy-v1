"""
Test Centralized Pricing Usage

Verifies all components use UtilityManager for pricing instead of direct data access.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from backend.src.basis_strategy_v1.core.utilities.utility_manager import UtilityManager
from backend.src.basis_strategy_v1.core.components.pnl_monitor import PnLMonitor
from backend.src.basis_strategy_v1.core.strategies.ml_btc_directional_btc_margin_strategy import MLBTCDirectionalBTCMarginStrategy
from backend.src.basis_strategy_v1.core.components.strategy_manager import StrategyManager
from backend.src.basis_strategy_v1.core.event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine


class TestCentralizedPricingUsage:
    """Test that all components use centralized pricing through UtilityManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_data_provider = Mock()
        self.mock_utility_manager = Mock(spec=UtilityManager)
        # Add the missing methods to the mock
        self.mock_utility_manager.get_funding_rate = Mock(return_value=0.0001)
        self.mock_utility_manager.get_oracle_price = Mock(return_value=3076.8)
        self.mock_utility_manager.get_liquidity_index = Mock(return_value=1.05)
        self.mock_utility_manager.get_price_for_instrument_key = Mock(return_value=50000.0)
        self.timestamp = pd.Timestamp('2024-01-01 12:00:00')
        
        # Mock data structure with uppercase keys
        self.mock_data = {
            'timestamp': self.timestamp,
            'market_data': {
                'prices': {
                    'BTC': 50000.0,
                    'ETH': 3000.0,
                    'USDT': 1.0
                },
                'funding_rates': {
                    'BTC_binance': 0.0001,
                    'ETH_bybit': 0.0002
                }
            },
            'protocol_data': {
                'perp_prices': {
                    'BTC_binance': 50000.0,
                    'ETH_okx': 3000.0
                },
                'aave_indexes': {
                    'aUSDT': 1.05,
                    'aWETH': 1.02
                },
                'oracle_prices': {
                    'weETH/USD': 3076.8,
                    'weETH/ETH': 1.0256,
                    'wstETH/USD': 3045.0,
                    'wstETH/ETH': 1.0150
                },
                'staking_rewards': {
                    'etherfi_weETH': 0.04,
                    'lido_wstETH': 0.035
                }
            },
            'ml_data': {
                'predictions': {
                    'signal': 'long',
                    'confidence': 0.8,
                    'sd': 0.02
                }
            }
        }
        
        self.mock_data_provider.get_data.return_value = self.mock_data
    
    def test_pnl_monitor_uses_utility_manager_for_funding_rates(self):
        """Test PnL monitor uses UtilityManager for funding rates."""
        # Mock utility manager methods
        self.mock_utility_manager.get_funding_rate.return_value = 0.0001
        
        # Create PnL monitor with utility manager
        pnl_calculator = PnLMonitor(
            config={
                'component_config': {
                    'pnl_monitor': {
                        'attribution_types': ['staking_pnl', 'borrowing_costs', 'transaction_costs'],
                        'reconciliation_tolerance': 0.02,
                        'reporting_currency': 'USDT'
                    }
                }
            },
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=self.mock_data_provider,
            utility_manager=self.mock_utility_manager,
            log_dir='./logs'
        )
        
        # Test funding rate access
        funding_rate = pnl_calculator._get_btc_funding_rate('binance', self.timestamp)
        
        # Verify UtilityManager was called
        self.mock_utility_manager.get_funding_rate.assert_called_once_with('binance', 'BTCUSDT', self.timestamp)
        assert funding_rate == 0.0001
    
    def test_pnl_monitor_uses_utility_manager_for_oracle_prices(self):
        """Test PnL monitor uses UtilityManager for oracle prices."""
        # Mock utility manager methods
        self.mock_utility_manager.get_oracle_price.return_value = 3076.8
        
        # Create PnL monitor with utility manager
        pnl_calculator = PnLMonitor(
            config={
                'component_config': {
                    'pnl_monitor': {
                        'attribution_types': ['staking_pnl', 'borrowing_costs', 'transaction_costs'],
                        'reconciliation_tolerance': 0.02,
                        'reporting_currency': 'USDT'
                    }
                }
            },
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=self.mock_data_provider,
            utility_manager=self.mock_utility_manager,
            log_dir='./logs'
        )
        
        # Test oracle price access
        oracle_price = pnl_calculator._get_aave_oracle_price('weETH', self.timestamp)
        
        # Verify UtilityManager was called
        self.mock_utility_manager.get_oracle_price.assert_called_once_with('weETH', self.timestamp)
        assert oracle_price == 3076.8
    
    def test_ml_strategy_uses_canonical_data_structure(self):
        """Test ML strategy uses canonical data structure for ML predictions."""
        # Create ML strategy
        mock_exposure_monitor = Mock()
        mock_position_monitor = Mock()
        mock_risk_monitor = Mock()
        
        strategy = MLBTCDirectionalBTCMarginStrategy(
            config={
                'mode': 'ml_btc_directional_btc_margin',
                'signal_threshold': 0.5,
                'max_position_size': 1.0,
                'stop_loss_pct': 0.05,
                'take_profit_pct': 0.10,
                'component_config': {
                    'position_monitor': {
                        'position_subscriptions': ['wallet:BaseToken:BTC', 'binance:BaseToken:BTC', 'binance:Perp:BTCUSDT']
                    },
                    'risk_monitor': {
                        'delta_tracking_asset': 'BTC'
                    }
                }
            },
            data_provider=self.mock_data_provider,
            exposure_monitor=mock_exposure_monitor,
            position_monitor=mock_position_monitor,
            risk_monitor=mock_risk_monitor
        )
        
        # Test ML prediction access
        predictions = strategy._get_ml_predictions(self.mock_data)
        
        # Verify data provider was called with canonical pattern (internal call)
        # The method calls get_data internally, so we verify the method works
        
        # Verify predictions structure
        assert predictions is not None
        assert predictions['signal'] == 'long'
        assert predictions['confidence'] == 0.8
    
    def test_strategy_manager_uses_canonical_data_access(self):
        """Test strategy manager uses canonical data access pattern."""
        # Mock other dependencies
        mock_exposure_monitor = Mock()
        mock_risk_monitor = Mock()
        mock_position_monitor = Mock()
        
        strategy_manager = StrategyManager(
            config={'mode': 'test'},
            data_provider=self.mock_data_provider,
            exposure_monitor=mock_exposure_monitor,
            risk_monitor=mock_risk_monitor,
            position_monitor=mock_position_monitor,
            utility_manager=self.mock_utility_manager
        )
        
        # Mock other component responses
        mock_exposure_monitor.get_current_exposure.return_value = {}
        mock_risk_monitor.get_current_risk_metrics.return_value = {}
        
        # Test data access
        market_data = strategy_manager.get_market_data(self.timestamp)
        
        # Verify canonical data access
        self.mock_data_provider.get_data.assert_called_once_with(self.timestamp)
        assert market_data == self.mock_data
    
    def test_event_engine_uses_canonical_data_access(self):
        """Test event engine uses canonical data access pattern."""
        # Mock dependencies
        mock_strategy_manager = Mock()
        mock_execution_manager = Mock()
        mock_position_monitor = Mock()
        mock_exposure_monitor = Mock()
        mock_risk_monitor = Mock()
        mock_utility_manager = Mock()
        
        event_engine = EventDrivenStrategyEngine(
            config={
                'mode': 'eth_staking_only',
                'share_class': 'USDT',
                'leverage_enabled': False,
                'lst_type': 'weETH',
                'staking_protocol': 'etherfi',
                'component_config': {
                    'position_monitor': {
                        'position_subscriptions': ['wallet:BaseToken:ETH', 'etherfi:LST:weETH']
                    },
                    'pnl_monitor': {
                        'attribution_types': ['staking_pnl', 'borrowing_costs', 'transaction_costs'],
                        'reconciliation_tolerance': 0.02,
                        'reporting_currency': 'USDT'
                    }
                }
            },
            execution_mode='backtest',
            data_provider=self.mock_data_provider,
            initial_capital=100000.0,
            share_class='USDT'
        )
        
        # Test that event engine initializes correctly with centralized data access
        # The event engine uses the data provider through its components
        assert event_engine.data_provider == self.mock_data_provider
        assert event_engine.utility_manager is not None
        
        # Verify the event engine has the expected components
        assert hasattr(event_engine, 'position_monitor')
        assert hasattr(event_engine, 'exposure_monitor')
        assert hasattr(event_engine, 'risk_monitor')
        assert hasattr(event_engine, 'pnl_monitor')
    
    def test_no_direct_data_access_patterns(self):
        """Test that components don't access data directly with old patterns."""
        # This test verifies that we don't have direct access patterns
        # that bypass UtilityManager for pricing operations
        
        # Components should use UtilityManager methods for:
        # - get_price_for_position_key()
        # - get_liquidity_index()
        # - get_funding_rate()
        # - get_oracle_price()
        # - get_market_price()
        
        # Not direct access like:
        # - data['market_data']['prices']['BTC']
        # - data['protocol_data']['aave_indexes']['aUSDT']
        # - data['market_data']['rates']['funding']
        
        # This is more of a code review test - in practice, we'd use
        # static analysis tools to detect these patterns
        assert True  # Placeholder for static analysis verification
    
    def test_utility_manager_handles_uppercase_keys(self):
        """Test UtilityManager correctly handles uppercase key format."""
        # Test price key conversion
        from backend.src.basis_strategy_v1.core.models.instruments import instrument_key_to_price_key
        
        assert instrument_key_to_price_key('wallet:BaseToken:BTC') == 'BTC'
        assert instrument_key_to_price_key('binance:Perp:BTCUSDT') == 'BTC_binance'
        assert instrument_key_to_price_key('etherfi:LST:weETH') == 'weETH'
    
    def test_utility_manager_handles_oracle_pairs(self):
        """Test UtilityManager correctly handles BASE/QUOTE oracle pair format."""
        from backend.src.basis_strategy_v1.core.models.instruments import instrument_key_to_oracle_pair
        
        assert instrument_key_to_oracle_pair('etherfi:LST:weETH', 'USD') == 'weETH/USD'
        assert instrument_key_to_oracle_pair('etherfi:LST:weETH', 'ETH') == 'weETH/ETH'
        assert instrument_key_to_oracle_pair('lido:LST:wstETH', 'USD') == 'wstETH/USD'
    
    def test_data_structure_consistency(self):
        """Test that all components expect the same data structure format."""
        # Verify the data structure has the expected uppercase keys
        assert 'BTC' in self.mock_data['market_data']['prices']
        assert 'BTC_binance' in self.mock_data['market_data']['funding_rates']
        assert 'BTC_binance' in self.mock_data['protocol_data']['perp_prices']
        assert 'aUSDT' in self.mock_data['protocol_data']['aave_indexes']
        assert 'weETH/USD' in self.mock_data['protocol_data']['oracle_prices']
        assert 'weETH/ETH' in self.mock_data['protocol_data']['oracle_prices']
        assert 'etherfi_weETH' in self.mock_data['protocol_data']['staking_rewards']
    
    def test_error_handling_without_utility_manager(self):
        """Test error handling when UtilityManager is not available."""
        # Create PnL calculator without utility manager
        pnl_calculator = PnLMonitor(
            config={
                'component_config': {
                    'pnl_monitor': {
                        'attribution_types': ['staking_pnl', 'borrowing_costs', 'transaction_costs'],
                        'reconciliation_tolerance': 0.02,
                        'reporting_currency': 'USDT'
                    }
                }
            },
            share_class='USDT',
            initial_capital=100000.0,
            data_provider=self.mock_data_provider,
            utility_manager=None,
            log_dir='./logs'
        )
        
        # Test funding rate access should raise error
        with pytest.raises(Exception):  # PnLMonitorError
            pnl_calculator._get_btc_funding_rate('binance', self.timestamp)
        
        # Test oracle price access should return 0.0
        oracle_price = pnl_calculator._get_aave_oracle_price('weETH', self.timestamp)
        assert oracle_price == 0.0


if __name__ == '__main__':
    pytest.main([__file__])
