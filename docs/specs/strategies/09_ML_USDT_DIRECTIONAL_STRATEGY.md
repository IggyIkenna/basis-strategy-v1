# ML USDT Directional Strategy Specification

**Last Reviewed**: October 13, 2025  
**Status**: 📋 SPECIFICATION - Implementation plan ready

## Purpose

The ML USDT Directional Strategy provides ML-driven directional USDT trading using 5-minute interval signals to generate long/short positions. This strategy uses machine learning predictions for entry/exit signals while taking full directional USDT exposure.

## 📚 **Canonical Sources**

**This strategy spec aligns with canonical architectural principles**:
- **Strategy Specifications**: [../MODES.md](../MODES.md) - ML USDT Directional mode definition
- **Architectural Principles**: [../REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles
- **Component Specifications**: [../COMPONENT_SPECS_INDEX.md](../COMPONENT_SPECS_INDEX.md) - All 20 components
- **Configuration**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas

## Strategy Overview

### **Core Concept**
- **Asset**: USDT (trading asset)
- **Share Class**: USDT (directional strategy)
- **Yield Source**: ML-driven directional trading profits
- **Risk Profile**: High directional USDT exposure, ML prediction risk
- **Capital Allocation**: 100% USDT perp position based on ML signals

### **Decision Logic**
The ML USDT Directional Strategy makes decisions based on:
1. **ML Signal Changes**: New ML predictions every 5 minutes
2. **Position Management**: Entry/exit based on ML signals
3. **Risk Management**: Stop-loss and take-profit orders
4. **Signal Confidence**: Only trade when confidence exceeds threshold

## Decision-Making Algorithm

### **Input Data Requirements**
```python
{
    'market_data': {
        'btc_price': float,              # Current BTC price (for USDT-margined BTC perps)
        'btc_perp_price': float,         # BTC perpetual price
        'btc_ohlcv_5min': Dict,          # 5-minute OHLCV data
        'btc_volume': float              # Current volume
    },
    'exposure_data': {
        'total_value_usd': float,        # Total portfolio value in USD
        'usdt_balance': float,           # USDT balance
        'btc_perp_position': float,      # BTC perpetual position (USDT-margined)
        'btc_balance': float             # BTC balance
    },
    'ml_predictions': {
        'signal': str,                   # 'long', 'short', 'neutral'
        'confidence': float,             # ML confidence (0-1)
        'sd': float,                     # Standard deviation for SL/TP calculation
        'timestamp': int                 # Prediction timestamp
    }
}
```

### **Decision Triggers**

#### **1. ML Signal Trigger (Primary)**
- **Trigger**: New ML signal with confidence > `signal_threshold`
- **Calculation**: `ml_predictions['confidence'] > signal_threshold`
- **Default Threshold**: 0.70 (higher threshold for USDT)
- **Action**: Enter/exit position based on ML signal

#### **2. Risk Management Trigger**
- **Stop Loss**: Price hits stop-loss level
- **Take Profit**: Price hits take-profit level
- **Action**: Exit position immediately

### **Decision Logic Flow**

```python
def make_strategy_decision(self, timestamp, trigger_source, market_data, exposure_data, risk_assessment):
    """
    ML USDT Directional Strategy Decision Logic
    """
    
    # Get ML predictions from data provider
    ml_predictions = self._get_ml_predictions(market_data)
    
    # 1. Risk Management - Exit if stop-loss or take-profit hit
    current_price = market_data['btc_price']  # BTC price for USDT-margined BTC perps
    current_position = exposure_data['btc_perp_position']
    
    if current_position != 0:  # Have a position
        # Calculate stop-loss and take-profit from standard deviation
        stop_loss, take_profit = self._calculate_stop_loss_take_profit(
            current_price, ml_predictions['sd'], ml_predictions['signal']
        )
        
        if current_position > 0 and current_price <= stop_loss:
            return self._create_exit_decision(timestamp, "Stop loss hit")
        elif current_position > 0 and current_price >= take_profit:
            return self._create_exit_decision(timestamp, "Take profit hit")
        elif current_position < 0 and current_price >= stop_loss:
            return self._create_exit_decision(timestamp, "Stop loss hit")
        elif current_position < 0 and current_price <= take_profit:
            return self._create_exit_decision(timestamp, "Take profit hit")
    
    # 2. ML Signal Check - Enter/exit based on ML signal
    if ml_predictions['confidence'] > self.config.get('signal_threshold', 0.70):
        signal = ml_predictions['signal']
        
        if signal == 'long' and current_position <= 0:
            return self._create_long_decision(timestamp, "ML long signal", ml_predictions['confidence'])
        elif signal == 'short' and current_position >= 0:
            return self._create_short_decision(timestamp, "ML short signal", ml_predictions['confidence'])
        elif signal == 'neutral' and current_position != 0:
            return self._create_exit_decision(timestamp, "ML neutral signal")
    
    # 3. Default: Maintain Current Position
    return self._create_maintain_decision(timestamp, "No action needed")

def _calculate_stop_loss_take_profit(self, current_price: float, sd: float, signal: str) -> Tuple[float, float]:
    """
    Calculate stop-loss and take-profit levels based on standard deviation.
    
    Args:
        current_price: Current BTC price
        sd: Standard deviation (as decimal, e.g., 0.02 for 2%)
        signal: Trading signal ('long', 'short', 'neutral')
        
    Returns:
        Tuple of (stop_loss, take_profit)
    """
    if signal == 'long':
        stop_loss = current_price * (1 - 2 * sd)    # 2x SD stop loss
        take_profit = current_price * (1 + 3 * sd)  # 3x SD take profit
    elif signal == 'short':
        stop_loss = current_price * (1 + 2 * sd)    # 2x SD stop loss
        take_profit = current_price * (1 - 3 * sd)  # 3x SD take profit
    else:  # neutral
        stop_loss = 0.0
        take_profit = 0.0
    
    return stop_loss, take_profit
```

## Decision Output Format

### **Maintain Decision**
```python
{
    'action': 'MAINTAIN_NEUTRAL',
    'reasoning': 'No action needed - optimal position maintained',
    'target_positions': {
        'usdt_balance': exposure_data['usdt_balance'],
        'usdt_perp_position': exposure_data['usdt_perp_position'],
        'btc_balance': exposure_data['btc_balance']
    },
    'execution_instructions': [],
    'risk_override': False,
    'estimated_cost': 0.0,
    'priority': 'LOW'
}
```

### **Long Decision**
```python
{
    'action': 'ENTER_LONG',
    'reasoning': 'ML long signal with high confidence',
    'target_positions': {
        'usdt_balance': 0.0,
        'usdt_perp_position': target_long_position,
        'btc_balance': 0.0
    },
    'execution_instructions': [
        {
            'action_type': 'perp_trade',
            'venue': 'binance',
            'asset': 'USDT',
            'side': 'buy',
            'amount': target_long_position,
            'atomic': False,
            'take_profit': ml_predictions['take_profit'],
            'stop_loss': ml_predictions['stop_loss']
        }
    ],
    'risk_override': False,
    'estimated_cost': estimated_trading_costs,
    'priority': 'HIGH'
}
```

### **Short Decision**
```python
{
    'action': 'ENTER_SHORT',
    'reasoning': 'ML short signal with high confidence',
    'target_positions': {
        'usdt_balance': 0.0,
        'usdt_perp_position': target_short_position,
        'btc_balance': 0.0
    },
    'execution_instructions': [
        {
            'action_type': 'perp_trade',
            'venue': 'binance',
            'asset': 'USDT',
            'side': 'sell',
            'amount': abs(target_short_position),
            'atomic': False,
            'take_profit': ml_predictions['take_profit'],
            'stop_loss': ml_predictions['stop_loss']
        }
    ],
    'risk_override': False,
    'estimated_cost': estimated_trading_costs,
    'priority': 'HIGH'
}
```

### **Exit Decision**
```python
{
    'action': 'EXIT_POSITION',
    'reasoning': 'Exit signal triggered',
    'target_positions': {
        'usdt_balance': 0.0,
        'usdt_perp_position': 0.0,
        'btc_balance': 0.0
    },
    'execution_instructions': [
        {
            'action_type': 'perp_trade',
            'venue': 'binance',
            'asset': 'USDT',
            'side': 'sell' if current_position > 0 else 'buy',
            'amount': abs(current_position),
            'atomic': False
        }
    ],
    'risk_override': True,
    'estimated_cost': estimated_trading_costs,
    'priority': 'HIGH'
}
```

## Position Targets

### **Optimal Allocation**
- **USDT Perp Position**: 100% of equity based on ML signal
- **USDT Balance**: 0% (no idle USDT)
- **BTC Balance**: 0% (no idle BTC)
- **Target Yield**: ML-driven trading profits

### **Position Calculation**
```python
def calculate_target_positions(self, total_equity, market_data, ml_predictions):
    """
    Calculate optimal position allocation for ML USDT directional trading
    """
    usdt_price = market_data['usdt_price']
    usdt_amount = total_equity / usdt_price
    
    if ml_predictions['signal'] == 'long':
        return {
            'usdt_balance': 0.0,
            'usdt_perp_position': usdt_amount,  # Long position
            'btc_balance': 0.0
        }
    elif ml_predictions['signal'] == 'short':
        return {
            'usdt_balance': 0.0,
            'usdt_perp_position': -usdt_amount,  # Short position
            'btc_balance': 0.0
        }
    else:  # neutral
        return {
            'usdt_balance': 0.0,
            'usdt_perp_position': 0.0,
            'btc_balance': 0.0
        }
```

## Risk Management

### **Risk Thresholds**
- **Signal Confidence**: Minimum 0.70 to trade (higher than BTC)
- **Stop Loss**: Dynamic based on ML predictions
- **Take Profit**: Dynamic based on ML predictions
- **Position Size**: 100% of equity per signal

### **Risk Responses**
1. **Stop Loss Hit**: Immediate position exit
2. **Take Profit Hit**: Immediate position exit
3. **Low Confidence**: No trading action
4. **Neutral Signal**: Exit current position

## Execution Patterns

### **Perpetual Trading Execution**
```python
{
    'action_type': 'perp_trade',
    'venue': 'binance',
    'asset': 'USDT',
    'side': 'buy',  # or 'sell'
    'amount': float,
    'atomic': False,
    'take_profit': float,
    'stop_loss': float,
    'slippage_tolerance': 0.001
}
```

## Integration Points

### **Data Provider Integration**
- **Required Data**: USDT prices, perp prices, OHLCV data, ML predictions
- **Update Frequency**: Real-time for prices, 5-minute for ML signals
- **Data Sources**: CEX APIs, ML prediction service

### **Risk Monitor Integration**
- **Risk Types**: ML prediction accuracy, position risk, liquidation risk
- **Update Frequency**: Real-time for position risk, 5-minute for ML accuracy
- **Thresholds**: Configurable per strategy

### **Execution Manager Integration**
- **Execution Venues**: Binance (perpetual trading)
- **Execution Types**: Perpetual trades with TP/SL orders
- **Gas Management**: Optimize for cost efficiency
- **Error Handling**: Retry logic, fallback procedures

## Configuration

### **Strategy-Specific Config**
```yaml
component_config:
  strategy_manager:
    strategy_type: "ml_usdt_directional"
    decision_parameters:
      signal_threshold: 0.70  # Higher threshold for USDT
      max_position_size: 1.0  # 100% of equity per signal
      trading_interval: 300   # 5-minute trading interval
    risk_limits:
      max_drawdown: 0.20  # 20% maximum drawdown
      stop_loss_buffer: 0.02  # 2% stop loss buffer
    execution_settings:
      venue: "binance"
      asset: "USDT"
      gas_price_multiplier: 1.1
      max_gas_price_gwei: 50
      retry_attempts: 3
```

## Config Fields Used

### Universal Config (All Strategies)
- **mode**: str - Strategy mode name ('ml_usdt_directional')
- **share_class**: str - 'USDT' | 'ETH'
- **asset**: str - Primary asset ('USDT')
- **initial_capital**: float - Starting capital amount
- **environment**: str - 'backtest' | 'live'
- **execution_mode**: str - 'backtest' | 'live'
- **validation_strict**: bool - Strict validation mode

### ML Configuration
- **ml_config.model_registry**: str - ML model registry location
- **ml_config.model_name**: str - ML model name
- **ml_config.model_version**: str - ML model version
- **ml_config.candle_interval**: str - Candle interval for ML predictions
- **ml_config.signal_threshold**: float - Confidence threshold for trading signals
- **ml_config.max_position_size**: float - Maximum position size as fraction of equity

### Strategy-Specific Config
  - **Usage**: Controls capital allocation to Binance for perp hedging
  - **Example**: 0.4 (40% of hedge on Binance)
  - **Used in**: Execution manager venue routing

  - **Usage**: Controls capital allocation to Bybit for perp hedging
  - **Example**: 0.3 (30% of hedge on Bybit)
  - **Used in**: Execution manager venue routing

  - **Usage**: Controls capital allocation to OKX for perp hedging
  - **Example**: 0.3 (30% of hedge on OKX)
  - **Used in**: Execution manager venue routing

### Venue Configuration
- **venues.binance.venue_type**: str - Venue type ('cex')
- **venues.binance.instruments**: List[str] - Available instruments
- **venues.binance.order_types**: List[str] - Available order types

### Component Configuration
- **component_config.strategy_manager.strategy_type**: str - Strategy type
- **component_config.strategy_manager.actions**: List[str] - Available actions
- **component_config.strategy_manager.position_calculation**: Dict - Position calculation config
- **component_config.risk_monitor.risk_limits**: Dict - Risk limit configuration
- **component_config.execution_manager.action_mapping**: Dict - Action mapping configuration

## Testing Requirements

### **Unit Tests**
- Decision logic for each trigger type
- Position calculation accuracy
- Risk assessment validation
- Execution instruction generation

### **Integration Tests**
- End-to-end decision workflow
- Execution manager integration
- Risk monitor integration
- Data provider integration

### **Performance Tests**
- Decision latency < 100ms
- Memory usage < 50MB
- CPU usage < 10% during decision making

## Monitoring & Alerting

### **Key Metrics**
- **ML Performance**: Actual vs expected ML prediction accuracy
- **Execution Success Rate**: Successful vs failed executions
- **Risk Metrics**: Position risk, drawdown, ML confidence
- **Decision Frequency**: Number of decisions per day

### **Alerts**
- **Risk Threshold Breach**: Drawdown > 20%
- **Execution Failure**: Failed execution attempts
- **ML Confidence Drop**: ML confidence < 0.5

## Future Enhancements

### **Phase 2 Enhancements**
- **Dynamic Position Sizing**: Adjust position size based on ML confidence
- **Advanced Risk Management**: Dynamic stop-loss and take-profit levels
- **Multi-Asset ML**: Extend to other assets

### **Phase 3 Enhancements**
- **Advanced Analytics**: ML-based risk management
- **Cross-Asset Trading**: Multi-asset ML strategies
- **Real-Time Learning**: Adaptive ML models

---

**This specification provides the foundation for implementing the ML USDT Directional Strategy decision-making logic, maximizing ML-driven trading profits while managing directional risk.**
