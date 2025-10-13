# BTC Basis Strategy Specification

**Last Reviewed**: October 13, 2025  
**Status**: 📋 SPECIFICATION - Implementation plan ready

## Purpose

The BTC Basis Strategy provides market-neutral BTC basis trading by maintaining equal long spot and short perpetual positions to collect funding rate premiums. This strategy generates yield through funding rate arbitrage while maintaining delta neutrality.

## 📚 **Canonical Sources**

**This strategy spec aligns with canonical architectural principles**:
- **Strategy Specifications**: [../MODES.md](../MODES.md) - BTC Basis mode definition
- **Architectural Principles**: [../REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles
- **Component Specifications**: [../COMPONENT_SPECS_INDEX.md](../COMPONENT_SPECS_INDEX.md) - All 20 components
- **Configuration**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas

## Strategy Overview

### **Core Concept**
- **Asset**: BTC (basis trading asset)
- **Share Class**: USDT (market neutral)
- **Yield Source**: Funding rate premiums from perpetual shorts
- **Risk Profile**: Market neutral, basis trading risk
- **Capital Allocation**: 100% BTC spot long + 100% BTC perp short (delta neutral)

### **Decision Logic**
The BTC Basis Strategy makes decisions based on:
1. **Capital Changes**: New deposits or withdrawals
2. **Position Rebalancing**: Maintain equal spot long and perp short positions
3. **Risk Management**: Monitor maintenance margin and funding rates
4. **Venue Distribution**: Distribute positions across multiple CEX venues

## Decision-Making Algorithm

### **Input Data Requirements**
```python
{
    'market_data': {
        'btc_spot_prices': Dict[str, float],  # BTC spot prices by venue
        'btc_perp_prices': Dict[str, float],  # BTC perpetual prices by venue
        'btc_funding_rates': Dict[str, float],  # Funding rates by venue
        'btc_price': float  # Current BTC price
    },
    'exposure_data': {
        'total_value_usd': float,       # Total portfolio value in USD
        'btc_spot_balance': float,      # BTC spot balance
        'btc_perp_short': float,        # BTC perpetual short position
        'usdt_balance': float           # USDT balance
    },
    'risk_assessment': {
        'maintenance_margin_ratio': float,  # Current maintenance margin ratio
        'funding_rate_risk': float         # Funding rate risk assessment
    }
}
```

### **Decision Triggers**

#### **1. Equity Deviation Trigger (Primary)**
- **Trigger**: Portfolio equity deviates from last rebalanced state by `position_deviation_threshold`
- **Calculation**: `abs(current_equity - last_rebalanced_equity) / last_rebalanced_equity > position_deviation_threshold`
- **Default Threshold**: 2% (configurable per strategy)
- **Action**: Rebalance to maintain equal spot long and perp short positions

#### **2. Risk Management Trigger**
- **Maintenance Margin**: <20% triggers position reduction
- **Source**: Centralized from risk monitor via `risk_assessment['maintenance_margin_ratio']`

### **Decision Logic Flow**

```python
def make_strategy_decision(self, timestamp, trigger_source, market_data, exposure_data, risk_assessment):
    """
    BTC Basis Strategy Decision Logic
    """
    
    # 1. Risk Assessment - Reduce position if maintenance margin too low
    if risk_assessment['maintenance_margin_ratio'] < 0.2:
        return self._create_risk_reduction_decision(timestamp, "Maintenance margin too low")
    
    # 2. Equity Deviation Check - Rebalance if equity changed significantly
    current_equity = exposure_data['total_value_usd']
    equity_deviation = self._calculate_equity_deviation(current_equity)
    
    if equity_deviation > self.config.get('position_deviation_threshold', 0.02):  # 2% default
        return self._create_rebalance_decision(timestamp, "Equity deviation detected", equity_deviation)
    
    # 3. Default: Maintain Current Position
    return self._create_maintain_decision(timestamp, "No action needed")
```

## Decision Output Format

### **Maintain Decision**
```python
{
    'action': 'MAINTAIN_NEUTRAL',
    'reasoning': 'No action needed - optimal position maintained',
    'target_positions': {
        'btc_spot_balance': exposure_data['btc_spot_balance'],
        'btc_perp_short': exposure_data['btc_perp_short'],
        'usdt_balance': exposure_data['usdt_balance']
    },
    'execution_instructions': [],
    'risk_override': False,
    'estimated_cost': 0.0,
    'priority': 'LOW'
}
```

### **Rebalance Decision**
```python
{
    'action': 'REBALANCE',
    'reasoning': 'Equity deviation detected - rebalancing to maintain delta neutrality',
    'target_positions': {
        'btc_spot_balance': target_btc_spot,
        'btc_perp_short': target_btc_perp_short,
        'usdt_balance': 0.0  # No USDT balance needed
    },
    'execution_instructions': [
        {
            'action_type': 'spot_trade',
            'venue': 'binance',
            'asset': 'BTC',
            'side': 'buy',
            'amount': btc_spot_delta,
            'atomic': False
        },
        {
            'action_type': 'perp_trade',
            'venue': 'binance',
            'asset': 'BTC',
            'side': 'sell',
            'amount': btc_perp_delta,
            'atomic': False
        }
    ],
    'risk_override': False,
    'estimated_cost': estimated_trading_costs,
    'priority': 'MEDIUM'
}
```

### **Risk Reduction Decision**
```python
{
    'action': 'EXIT_PARTIAL',
    'reasoning': 'Maintenance margin too low - reducing position size',
    'target_positions': {
        'btc_spot_balance': reduced_btc_spot,
        'btc_perp_short': reduced_btc_perp_short,
        'usdt_balance': 0.0
    },
    'execution_instructions': [
        {
            'action_type': 'spot_trade',
            'venue': 'binance',
            'asset': 'BTC',
            'side': 'sell',
            'amount': btc_spot_reduction,
            'atomic': False
        },
        {
            'action_type': 'perp_trade',
            'venue': 'binance',
            'asset': 'BTC',
            'side': 'buy',
            'amount': btc_perp_reduction,
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
- **BTC Spot Long**: 100% of equity (in BTC terms)
- **BTC Perp Short**: 100% of equity (in BTC terms)
- **USDT Balance**: 0% (no idle USDT)
- **Target Yield**: Funding rate premiums from perpetual shorts

### **Position Calculation**
```python
def calculate_target_positions(self, total_equity, market_data):
    """
    Calculate optimal position allocation for BTC basis trading
    """
    btc_price = market_data['btc_price']
    btc_amount = total_equity / btc_price
    
    return {
        'btc_spot_balance': btc_amount,
        'btc_perp_short': btc_amount,
        'usdt_balance': 0.0
    }
```

## Risk Management

### **Risk Thresholds**
- **Maintenance Margin Ratio**: Minimum 20%
- **Funding Rate Risk**: Monitor funding rate volatility
- **Basis Risk**: Monitor spot-perp basis spreads

### **Risk Responses**
1. **Maintenance Margin < 20%**: Immediate position reduction
2. **Funding Rate Volatility > 5%**: Monitor and potentially reduce position
3. **Basis Spread > 2%**: Monitor for potential arbitrage opportunities

## Execution Patterns

### **Spot Trading Execution**
```python
{
    'action_type': 'spot_trade',
    'venue': 'binance',
    'asset': 'BTC',
    'side': 'buy',
    'amount': float,
    'atomic': False,
    'slippage_tolerance': 0.001
}
```

### **Perpetual Trading Execution**
```python
{
    'action_type': 'perp_trade',
    'venue': 'binance',
    'asset': 'BTC',
    'side': 'sell',
    'amount': float,
    'atomic': False,
    'slippage_tolerance': 0.001
}
```

## Integration Points

### **Data Provider Integration**
- **Required Data**: BTC spot prices, perp prices, funding rates
- **Update Frequency**: Real-time for prices, hourly for funding rates
- **Data Sources**: CEX APIs (Binance, Bybit, OKX)

### **Risk Monitor Integration**
- **Risk Types**: Maintenance margin ratio, funding rate risk, basis risk
- **Update Frequency**: Every block for margin, daily for funding rates
- **Thresholds**: Configurable per strategy

### **Execution Manager Integration**
- **Execution Venues**: Binance (40%), Bybit (30%), OKX (30%)
- **Execution Types**: Spot trades, perpetual trades
- **Gas Management**: Optimize for cost efficiency
- **Error Handling**: Retry logic, fallback procedures

## Configuration

### **Strategy-Specific Config**
```yaml
component_config:
  strategy_manager:
    strategy_type: "btc_basis"
    decision_parameters:
      position_deviation_threshold: 0.02  # 2% equity deviation threshold
    risk_limits:
      min_maintenance_margin_ratio: 0.2
      max_funding_rate_risk: 0.05
    execution_settings:
      hedge_venues: ["binance", "bybit", "okx"]
      hedge_allocation_binance: 0.4
      hedge_allocation_bybit: 0.3
      hedge_allocation_okx: 0.3
      gas_price_multiplier: 1.1
      max_gas_price_gwei: 50
      retry_attempts: 3
```

## Config Fields Used

### Universal Config (All Strategies)
- **mode**: str - Strategy mode name ('btc_basis')
- **share_class**: str - 'USDT' | 'ETH'
- **asset**: str - Primary asset ('BTC')
- **initial_capital**: float - Starting capital amount
- **environment**: str - 'backtest' | 'live'
- **execution_mode**: str - 'backtest' | 'live'
- **validation_strict**: bool - Strict validation mode

### Strategy Validation Fields
- **lending_enabled**: bool - Whether lending is enabled
- **staking_enabled**: bool - Whether staking is enabled
- **basis_trade_enabled**: bool - Whether basis trading is enabled
- **leverage_supported**: bool - Whether leverage is supported
- **target_apy_range**: Dict[str, float] - Target APY range for quality gate validation

### Strategy-Specific Config
- **lending_enabled**: bool - Whether lending is enabled
  - **Usage**: Enables lending functionality
  - **Used in**: Strategy initialization and validation

- **staking_enabled**: bool - Whether staking is enabled
  - **Usage**: Enables staking functionality
  - **Used in**: Strategy initialization and validation

- **basis_trade_enabled**: bool - Whether basis trading is enabled
  - **Usage**: Enables basis trading functionality
  - **Used in**: Strategy initialization and validation

- **leverage_supported**: bool - Whether leverage is supported
  - **Usage**: Indicates if strategy supports leverage
  - **Used in**: Strategy validation and risk management

- **target_apy_range**: Dict[str, float] - Target APY range for quality gate validation
  - **Usage**: Defines min/max APY range for e2e PnL quality gate checks
  - **Example**: {"min": 0.06, "max": 0.10} for 6-10% APY range
  - **Used in**: Quality gate validation and performance monitoring

- **basis_trading_supported**: bool - Whether basis trading is supported
  - **Usage**: Enables basis trading functionality
  - **Used in**: Strategy initialization and validation

- **hedge_allocation_binance**: float - Proportion of hedge on Binance (0.0-1.0)
  - **Usage**: Controls capital allocation to Binance for perp hedging
  - **Example**: 0.4 (40% of hedge on Binance)
  - **Used in**: Execution manager venue routing

- **hedge_allocation_bybit**: float - Proportion of hedge on Bybit (0.0-1.0)
  - **Usage**: Controls capital allocation to Bybit for perp hedging
  - **Example**: 0.3 (30% of hedge on Bybit)
  - **Used in**: Execution manager venue routing

- **hedge_allocation_okx**: float - Proportion of hedge on OKX (0.0-1.0)
  - **Usage**: Controls capital allocation to OKX for perp hedging
  - **Example**: 0.3 (30% of hedge on OKX)
  - **Used in**: Execution manager venue routing

- **hedge_venues**: List[str] - List of venues used for hedging
  - **Usage**: Defines which venues to use for hedging operations
  - **Examples**: ["binance", "bybit", "okx"]
  - **Used in**: Venue selection for hedging

### Venue Configuration
- **venues.binance.venue_type**: str - Venue type ('cex')
- **venues.binance.enabled**: bool - Whether Binance is enabled
- **venues.binance.instruments**: List[str] - Available instruments
- **venues.binance.order_types**: List[str] - Available order types
- **venues.binance.min_amount**: float - Minimum order amount

- **venues.bybit.venue_type**: str - Venue type ('cex')
- **venues.bybit.enabled**: bool - Whether Bybit is enabled
- **venues.bybit.instruments**: List[str] - Available instruments
- **venues.bybit.order_types**: List[str] - Available order types
- **venues.bybit.max_leverage**: float - Maximum leverage
- **venues.bybit.min_amount**: float - Minimum order amount

- **venues.okx.venue_type**: str - Venue type ('cex')
- **venues.okx.enabled**: bool - Whether OKX is enabled
- **venues.okx.instruments**: List[str] - Available instruments
- **venues.okx.order_types**: List[str] - Available order types
- **venues.okx.max_leverage**: float - Maximum leverage
- **venues.okx.min_amount**: float - Minimum order amount

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
- **Funding Rate Performance**: Actual vs expected funding rate collection
- **Execution Success Rate**: Successful vs failed executions
- **Risk Metrics**: Maintenance margin ratio, funding rate risk
- **Decision Frequency**: Number of decisions per day

### **Alerts**
- **Risk Threshold Breach**: Maintenance margin ratio < 20%
- **Execution Failure**: Failed execution attempts
- **Funding Rate Deviation**: Actual funding rate < expected * 0.9

## Future Enhancements

### **Phase 2 Enhancements**
- **Multi-Venue Optimization**: Dynamic venue selection based on funding rates
- **Basis Arbitrage**: Spot-perp basis spread arbitrage
- **Advanced Risk Management**: Dynamic position sizing based on volatility

### **Phase 3 Enhancements**
- **Cross-Asset Basis**: ETH-BTC basis trading
- **Options Integration**: Options-based hedging strategies
- **Advanced Analytics**: ML-based funding rate prediction

---

**This specification provides the foundation for implementing the BTC Basis Strategy decision-making logic, maintaining delta neutrality while collecting funding rate premiums.**
