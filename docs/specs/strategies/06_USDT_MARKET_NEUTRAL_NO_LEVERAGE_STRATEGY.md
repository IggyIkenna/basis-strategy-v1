# USDT Market Neutral No Leverage Strategy Specification

**Last Reviewed**: October 13, 2025  
**Status**: 📋 SPECIFICATION - Implementation plan ready

## Purpose

The USDT Market Neutral No Leverage Strategy provides market-neutral ETH staking by hedging ETH exposure with perpetual shorts. This strategy generates yield through staking rewards while maintaining delta neutrality through CEX hedging.

## 📚 **Canonical Sources**

**This strategy spec aligns with canonical architectural principles**:
- **Strategy Specifications**: [../MODES.md](../MODES.md) - USDT Market Neutral No Leverage mode definition
- **Architectural Principles**: [../REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles
- **Component Specifications**: [../COMPONENT_SPECS_INDEX.md](../COMPONENT_SPECS_INDEX.md) - All 20 components
- **Configuration**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas

## Strategy Overview

### **Core Concept**
- **Asset**: ETH (staking asset)
- **Share Class**: USDT (market neutral)
- **Yield Source**: ETH staking rewards + EIGEN rewards
- **Risk Profile**: Market neutral, staking + funding risk
- **Capital Allocation**: Split between ETH staking and CEX hedging per `stake_allocation_eth`

### **Decision Logic**
The USDT Market Neutral No Leverage Strategy makes decisions based on:
1. **Capital Changes**: New deposits or withdrawals
2. **Position Rebalancing**: Maintain optimal staking/hedging allocation
3. **Delta Management**: Monitor and adjust for delta drift
4. **Risk Management**: Monitor staking and funding risks

## Decision-Making Algorithm

### **Input Data Requirements**
```python
{
    'market_data': {
        'eth_price': float,              # Current ETH price
        'lst_price': float,              # LST price (weETH/ETH or wstETH/ETH)
        'eth_perp_prices': Dict[str, float],  # ETH perpetual prices by venue
        'eth_funding_rates': Dict[str, float],  # Funding rates by venue
        'staking_rewards_rate': float,   # Current staking rewards rate
        'eigen_rewards_rate': float      # Current EIGEN rewards rate
    },
    'exposure_data': {
        'total_value_usd': float,        # Total portfolio value in USD
        'eth_balance': float,            # ETH balance
        'lst_balance': float,            # LST balance (weETH/wstETH)
        'usdt_balance': float,           # USDT balance
        'eth_perp_short': float,         # ETH perpetual short position
        'delta_exposure': float          # Current delta exposure
    },
    'risk_assessment': {
        'delta_drift': float,            # Delta drift from neutrality
        'lst_protocol_health': float,    # LST protocol health factor
        'funding_rate_risk': float       # Funding rate risk assessment
    }
}
```

### **Decision Triggers**

#### **1. Equity Deviation Trigger (Primary)**
- **Trigger**: Portfolio equity deviates from last rebalanced state by `position_deviation_threshold`
- **Calculation**: `abs(current_equity - last_rebalanced_equity) / last_rebalanced_equity > position_deviation_threshold`
- **Default Threshold**: 2% (configurable per strategy)
- **Action**: Rebalance to maintain optimal staking/hedging allocation

#### **2. Delta Drift Trigger**
- **Delta Drift**: >2% triggers hedge adjustment
- **Source**: Centralized from risk monitor via `risk_assessment['delta_drift']`

### **Decision Logic Flow**

```python
def make_strategy_decision(self, timestamp, trigger_source, market_data, exposure_data, risk_assessment):
    """
    USDT Market Neutral No Leverage Strategy Decision Logic
    """
    
    # 1. Delta Drift Check - Adjust hedge if delta drift too high
    if abs(risk_assessment['delta_drift']) > 0.02:  # 2% delta drift threshold
        return self._create_delta_adjustment_decision(timestamp, "Delta drift detected", risk_assessment['delta_drift'])
    
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
        'eth_balance': exposure_data['eth_balance'],
        'lst_balance': exposure_data['lst_balance'],
        'usdt_balance': exposure_data['usdt_balance'],
        'eth_perp_short': exposure_data['eth_perp_short']
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
    'reasoning': 'Equity deviation detected - rebalancing staking/hedging allocation',
    'target_positions': {
        'eth_balance': 0.0,  # No idle ETH
        'lst_balance': target_lst_balance,
        'usdt_balance': target_usdt_balance,
        'eth_perp_short': target_perp_short
    },
    'execution_instructions': [
        {
            'action_type': 'stake',
            'venue': 'lido',  # or 'etherfi' based on lst_type
            'asset': 'ETH',
            'amount': eth_to_stake,
            'atomic': False
        },
        {
            'action_type': 'perp_trade',
            'venue': 'binance',
            'asset': 'ETH',
            'side': 'sell',
            'amount': perp_short_delta,
            'atomic': False
        }
    ],
    'risk_override': False,
    'estimated_cost': estimated_trading_costs,
    'priority': 'MEDIUM'
}
```

### **Delta Adjustment Decision**
```python
{
    'action': 'DELTA_ADJUST',
    'reasoning': 'Delta drift detected - adjusting hedge position',
    'target_positions': {
        'eth_balance': 0.0,
        'lst_balance': exposure_data['lst_balance'],
        'usdt_balance': exposure_data['usdt_balance'],
        'eth_perp_short': adjusted_perp_short
    },
    'execution_instructions': [
        {
            'action_type': 'perp_trade',
            'venue': 'binance',
            'asset': 'ETH',
            'side': 'sell' if delta_drift > 0 else 'buy',
            'amount': abs(delta_adjustment),
            'atomic': False
        }
    ],
    'risk_override': False,
    'estimated_cost': estimated_trading_costs,
    'priority': 'HIGH'
}
```

## Position Targets

### **Optimal Allocation**
- **ETH Staking**: `stake_allocation_eth` proportion of equity
- **CEX Hedging**: `1 - stake_allocation_eth` proportion for perp shorts
- **USDT Balance**: 0% (no idle USDT)
- **Target Yield**: Staking rewards + EIGEN rewards

### **Position Calculation**
```python
def calculate_target_positions(self, total_equity, market_data):
    """
    Calculate optimal position allocation for market neutral staking
    """
    stake_allocation = self.config.get('stake_allocation_eth', 0.5)
    eth_price = market_data['eth_price']
    
    # Split equity between staking and hedging
    staking_equity = total_equity * stake_allocation
    hedging_equity = total_equity * (1 - stake_allocation)
    
    eth_amount = staking_equity / eth_price
    perp_short_amount = hedging_equity / eth_price
    
    return {
        'eth_balance': 0.0,
        'lst_balance': eth_amount,  # ETH staked
        'usdt_balance': 0.0,
        'eth_perp_short': perp_short_amount  # ETH perp short
    }
```

## Risk Management

### **Risk Thresholds**
- **Delta Drift**: Maximum 2% from neutrality
- **LST Protocol Health**: Monitor protocol health factor
- **Funding Rate Risk**: Monitor funding rate volatility

### **Risk Responses**
1. **Delta Drift > 2%**: Immediate hedge adjustment
2. **LST Protocol Health < 0.8**: Monitor and potentially exit
3. **Funding Rate Volatility > 5%**: Monitor and potentially reduce position

## Execution Patterns

### **Staking Execution**
```python
{
    'action_type': 'stake',
    'venue': 'lido',  # or 'etherfi'
    'asset': 'ETH',
    'amount': float,
    'atomic': False,
    'target_token': 'wstETH'  # or 'weETH'
}
```

### **Perpetual Trading Execution**
```python
{
    'action_type': 'perp_trade',
    'venue': 'binance',
    'asset': 'ETH',
    'side': 'sell',
    'amount': float,
    'atomic': False,
    'slippage_tolerance': 0.001
}
```

## Integration Points

### **Data Provider Integration**
- **Required Data**: ETH prices, LST prices, perp prices, funding rates, staking rewards
- **Update Frequency**: Real-time for prices and rates, daily for rewards
- **Data Sources**: LST protocols, CEX APIs

### **Risk Monitor Integration**
- **Risk Types**: Delta drift, LST protocol health, funding rate risk
- **Update Frequency**: Real-time for delta, daily for protocol health
- **Thresholds**: Configurable per strategy

### **Execution Manager Integration**
- **Execution Venues**: Lido/EtherFi (staking), Binance/Bybit/OKX (hedging)
- **Execution Types**: Staking, perpetual trades
- **Gas Management**: Optimize for cost efficiency
- **Error Handling**: Retry logic, fallback procedures

## Configuration

### **Strategy-Specific Config**
```yaml
component_config:
  strategy_manager:
    strategy_type: "usdt_market_neutral_no_leverage"
    decision_parameters:
      position_deviation_threshold: 0.02  # 2% equity deviation threshold
      stake_allocation_eth: 0.5  # 50% to staking, 50% to hedging
      max_delta_drift: 0.02  # 2% maximum delta drift
    risk_limits:
      max_delta_drift: 0.02
      min_lst_protocol_health: 0.8
      max_funding_rate_risk: 0.05
    execution_settings:
      lst_type: "weeth"  # or "wsteth"
      staking_protocol: "etherfi"  # or "lido"
      hedge_venues: ["binance", "bybit", "okx"]
      gas_price_multiplier: 1.1
      max_gas_price_gwei: 50
      retry_attempts: 3
```

## Config Fields Used

### Universal Config (All Strategies)
- **mode**: str - Strategy mode name ('usdt_market_neutral_no_leverage')
- **share_class**: str - 'USDT' | 'ETH'
- **asset**: str - Primary asset ('USDT')
- **initial_capital**: float - Starting capital amount
- **environment**: str - 'backtest' | 'live'
- **execution_mode**: str - 'backtest' | 'live'
- **validation_strict**: bool - Strict validation mode

### Strategy-Specific Config
- **market_neutral**: bool - Whether strategy is market neutral
- **allows_hedging**: bool - Whether hedging is allowed
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
- **venues.etherfi.venue_type**: str - Venue type ('defi')
- **venues.etherfi.instruments**: List[str] - Available instruments
- **venues.etherfi.order_types**: List[str] - Available order types
- **venues.binance.venue_type**: str - Venue type ('cex')
- **venues.binance.instruments**: List[str] - Available instruments
- **venues.binance.order_types**: List[str] - Available order types
- **venues.bybit.venue_type**: str - Venue type ('cex')
- **venues.bybit.instruments**: List[str] - Available instruments
- **venues.bybit.order_types**: List[str] - Available order types
- **venues.okx.venue_type**: str - Venue type ('cex')
- **venues.okx.instruments**: List[str] - Available instruments
- **venues.okx.order_types**: List[str] - Available order types

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
- **Staking Performance**: Actual vs expected staking rewards
- **Execution Success Rate**: Successful vs failed executions
- **Risk Metrics**: Delta drift, LST protocol health, funding rate risk
- **Decision Frequency**: Number of decisions per day

### **Alerts**
- **Risk Threshold Breach**: Delta drift > 2%
- **Execution Failure**: Failed execution attempts
- **Funding Rate Deviation**: Funding rate risk > 5%

## Future Enhancements

### **Phase 2 Enhancements**
- **Dynamic Allocation**: Adjust staking/hedging allocation based on market conditions
- **Advanced Delta Management**: Dynamic hedge adjustment based on volatility
- **Multi-Venue Optimization**: Dynamic venue selection for hedging

### **Phase 3 Enhancements**
- **Advanced Analytics**: ML-based allocation optimization
- **Cross-Asset Hedging**: Multi-asset hedging strategies
- **Options Integration**: Options-based hedging strategies

---

**This specification provides the foundation for implementing the USDT Market Neutral No Leverage Strategy decision-making logic, maintaining delta neutrality while maximizing staking rewards.**
