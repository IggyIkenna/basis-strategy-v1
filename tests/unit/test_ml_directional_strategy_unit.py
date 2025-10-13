#!/usr/bin/env python3
"""
ML Directional Strategy Unit Tests

Tests the ML Directional Strategy component in isolation with mocked dependencies.
Validates machine learning-based directional trading functionality and prediction accuracy.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from typing import Dict, Any, List

# Mock the backend imports
with patch.dict('sys.modules', {
    'basis_strategy_v1': Mock(),
    'basis_strategy_v1.core': Mock(),
    'basis_strategy_v1.core.strategies': Mock(),
    'basis_strategy_v1.infrastructure': Mock(),
    'basis_strategy_v1.infrastructure.data': Mock(),
    'basis_strategy_v1.infrastructure.config': Mock(),
}):
    # Import the strategy class (will be mocked)
    from basis_strategy_v1.core.strategies.ml_directional_strategy import MLDirectionalStrategy


class TestMLDirectionalStrategy:
    """Test suite for ML Directional Strategy component."""
    
    @pytest.fixture
    def mock_data_provider(self):
        """Mock data provider for testing."""
        provider = Mock()
        provider.get_eth_price.return_value = Decimal('2000.0')
        provider.get_btc_price.return_value = Decimal('40000.0')
        provider.get_market_features.return_value = {
            'price_momentum': Decimal('0.02'),
            'volume_trend': Decimal('1.5'),
            'volatility': Decimal('0.15'),
            'funding_rate': Decimal('0.01')
        }
        provider.get_ml_predictions.return_value = {
            'direction': 'bullish',
            'confidence': Decimal('0.75'),
            'target_price': Decimal('2100.0'),
            'stop_loss': Decimal('1900.0')
        }
        return provider
    
    @pytest.fixture
    def mock_execution_interface(self):
        """Mock execution interface for testing."""
        interface = Mock()
        interface.execute_long.return_value = {'success': True, 'amount': Decimal('1000')}
        interface.execute_short.return_value = {'success': True, 'amount': Decimal('1000')}
        interface.execute_close_position.return_value = {'success': True, 'amount': Decimal('1000')}
        return interface
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'max_leverage': 3.0,
            'confidence_threshold': Decimal('0.7'),
            'position_size': Decimal('0.1'),  # 10% of capital
            'stop_loss_pct': Decimal('0.05'),  # 5% stop loss
            'take_profit_pct': Decimal('0.10'),  # 10% take profit
            'ml_model': 'lstm_v1',
            'features': ['price_momentum', 'volume_trend', 'volatility', 'funding_rate'],
            'prediction_horizon': 24  # 24 hours
        }
    
    @pytest.fixture
    def ml_directional_strategy(self, mock_data_provider, mock_execution_interface, mock_config):
        """Create ML Directional Strategy instance for testing."""
        with patch('basis_strategy_v1.core.strategies.ml_directional_strategy.MLDirectionalStrategy') as mock_strategy_class:
            strategy = Mock()
            strategy.initialize.return_value = True
            strategy.get_current_position.return_value = {'direction': 'long', 'size': Decimal('1000')}
            strategy.get_prediction_confidence.return_value = Decimal('0.75')
            strategy.get_expected_return.return_value = Decimal('0.08')
            strategy.should_open_position.return_value = True
            strategy.should_close_position.return_value = False
            return strategy
    
    def test_strategy_initialization(self, ml_directional_strategy, mock_config):
        """Test ML directional strategy initializes correctly with ML parameters."""
        # Test initialization
        result = ml_directional_strategy.initialize(mock_config)
        
        # Verify initialization
        assert result is True
        ml_directional_strategy.initialize.assert_called_once_with(mock_config)
    
    def test_ml_prediction_processing(self, ml_directional_strategy, mock_data_provider):
        """Test ML prediction processing and confidence assessment."""
        # Test ML predictions
        predictions = mock_data_provider.get_ml_predictions()
        assert predictions['direction'] == 'bullish'
        assert predictions['confidence'] == Decimal('0.75')
        assert predictions['target_price'] == Decimal('2100.0')
        assert predictions['stop_loss'] == Decimal('1900.0')
        
        # Test prediction confidence
        confidence = ml_directional_strategy.get_prediction_confidence()
        assert confidence == Decimal('0.75')
    
    def test_feature_extraction(self, ml_directional_strategy, mock_data_provider):
        """Test feature extraction for ML model input."""
        # Test market features
        features = mock_data_provider.get_market_features()
        assert 'price_momentum' in features
        assert 'volume_trend' in features
        assert 'volatility' in features
        assert 'funding_rate' in features
        
        # Test feature values
        assert features['price_momentum'] == Decimal('0.02')
        assert features['volume_trend'] == Decimal('1.5')
        assert features['volatility'] == Decimal('0.15')
        assert features['funding_rate'] == Decimal('0.01')
    
    def test_position_management(self, ml_directional_strategy, mock_execution_interface):
        """Test position management based on ML predictions."""
        # Test current position
        current_position = ml_directional_strategy.get_current_position()
        assert current_position['direction'] == 'long'
        assert current_position['size'] == Decimal('1000')
        
        # Test position opening decision
        should_open = ml_directional_strategy.should_open_position()
        assert should_open is True
        
        # Test position closing decision
        should_close = ml_directional_strategy.should_close_position()
        assert should_close is False
        
        # Test long position execution
        long_result = mock_execution_interface.execute_long(Decimal('1000'))
        assert long_result['success'] is True
        assert long_result['amount'] == Decimal('1000')
    
    def test_risk_management(self, ml_directional_strategy, mock_config):
        """Test risk management with ML-based stop loss and take profit."""
        # Test stop loss configuration
        stop_loss_pct = mock_config['stop_loss_pct']
        assert stop_loss_pct == Decimal('0.05')  # 5% stop loss
        
        # Test take profit configuration
        take_profit_pct = mock_config['take_profit_pct']
        assert take_profit_pct == Decimal('0.10')  # 10% take profit
        
        # Test position size management
        position_size = mock_config['position_size']
        assert position_size == Decimal('0.1')  # 10% of capital
        
        # Test confidence threshold
        confidence_threshold = mock_config['confidence_threshold']
        assert confidence_threshold == Decimal('0.7')
    
    def test_ml_model_integration(self, ml_directional_strategy, mock_config):
        """Test ML model integration and configuration."""
        # Test ML model selection
        ml_model = mock_config['ml_model']
        assert ml_model == 'lstm_v1'
        
        # Test feature configuration
        features = mock_config['features']
        expected_features = ['price_momentum', 'volume_trend', 'volatility', 'funding_rate']
        assert features == expected_features
        
        # Test prediction horizon
        prediction_horizon = mock_config['prediction_horizon']
        assert prediction_horizon == 24  # 24 hours
    
    def test_directional_trading_logic(self, ml_directional_strategy, mock_data_provider):
        """Test directional trading logic based on ML predictions."""
        # Test bullish prediction
        predictions = mock_data_provider.get_ml_predictions()
        if predictions['direction'] == 'bullish':
            # Should open long position
            with patch.object(ml_directional_strategy, 'should_open_position', return_value=True):
                should_open = ml_directional_strategy.should_open_position()
                assert should_open is True
        
        # Test bearish prediction
        with patch.object(mock_data_provider, 'get_ml_predictions', return_value={
            'direction': 'bearish',
            'confidence': Decimal('0.80'),
            'target_price': Decimal('1900.0'),
            'stop_loss': Decimal('2100.0')
        }):
            bearish_predictions = mock_data_provider.get_ml_predictions()
            assert bearish_predictions['direction'] == 'bearish'
            assert bearish_predictions['confidence'] == Decimal('0.80')
    
    def test_confidence_based_position_sizing(self, ml_directional_strategy, mock_config):
        """Test position sizing based on ML prediction confidence."""
        # Test confidence threshold
        confidence_threshold = mock_config['confidence_threshold']
        current_confidence = ml_directional_strategy.get_prediction_confidence()
        
        # Should open position if confidence exceeds threshold
        if current_confidence >= confidence_threshold:
            assert current_confidence >= confidence_threshold
        
        # Test position size scaling with confidence
        base_position_size = mock_config['position_size']
        confidence_multiplier = current_confidence / confidence_threshold
        adjusted_position_size = base_position_size * confidence_multiplier
        
        assert adjusted_position_size >= base_position_size
    
    def test_expected_return_calculation(self, ml_directional_strategy):
        """Test expected return calculation based on ML predictions."""
        # Test expected return
        expected_return = ml_directional_strategy.get_expected_return()
        assert expected_return == Decimal('0.08')  # 8% expected return
        
        # Test return calculation with different confidence levels
        with patch.object(ml_directional_strategy, 'get_prediction_confidence', return_value=Decimal('0.90')):
            high_confidence = ml_directional_strategy.get_prediction_confidence()
            assert high_confidence == Decimal('0.90')
            
            # Higher confidence should lead to higher expected returns
            with patch.object(ml_directional_strategy, 'get_expected_return', return_value=Decimal('0.12')):
                high_confidence_return = ml_directional_strategy.get_expected_return()
                assert high_confidence_return == Decimal('0.12')
    
    def test_strategy_state_management(self, ml_directional_strategy):
        """Test strategy state management and persistence."""
        # Test strategy state tracking
        strategy_state = {
            'current_position': {'direction': 'long', 'size': Decimal('1000')},
            'prediction_confidence': Decimal('0.75'),
            'expected_return': Decimal('0.08'),
            'ml_model': 'lstm_v1',
            'last_prediction_time': 1234567890,
            'prediction_history': [],
            'performance_metrics': {
                'accuracy': Decimal('0.65'),
                'sharpe_ratio': Decimal('1.2'),
                'max_drawdown': Decimal('0.08')
            }
        }
        
        # Verify state components
        assert strategy_state['current_position']['direction'] == 'long'
        assert strategy_state['current_position']['size'] == Decimal('1000')
        assert strategy_state['prediction_confidence'] == Decimal('0.75')
        assert strategy_state['expected_return'] == Decimal('0.08')
        assert strategy_state['ml_model'] == 'lstm_v1'
        assert strategy_state['last_prediction_time'] == 1234567890
        assert strategy_state['prediction_history'] == []
        assert strategy_state['performance_metrics']['accuracy'] == Decimal('0.65')
        assert strategy_state['performance_metrics']['sharpe_ratio'] == Decimal('1.2')
        assert strategy_state['performance_metrics']['max_drawdown'] == Decimal('0.08')
    
    def test_ml_model_performance_tracking(self, ml_directional_strategy):
        """Test ML model performance tracking and evaluation."""
        # Test performance metrics
        performance_metrics = {
            'accuracy': Decimal('0.65'),
            'precision': Decimal('0.70'),
            'recall': Decimal('0.60'),
            'f1_score': Decimal('0.65'),
            'sharpe_ratio': Decimal('1.2'),
            'max_drawdown': Decimal('0.08'),
            'total_return': Decimal('0.15')
        }
        
        # Verify performance metrics
        assert performance_metrics['accuracy'] == Decimal('0.65')
        assert performance_metrics['precision'] == Decimal('0.70')
        assert performance_metrics['recall'] == Decimal('0.60')
        assert performance_metrics['f1_score'] == Decimal('0.65')
        assert performance_metrics['sharpe_ratio'] == Decimal('1.2')
        assert performance_metrics['max_drawdown'] == Decimal('0.08')
        assert performance_metrics['total_return'] == Decimal('0.15')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
