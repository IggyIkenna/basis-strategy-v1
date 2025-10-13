# USDT Market Neutral Strategy Specification

**Last Reviewed**: October 13, 2025  
**Status**: 📋 SPECIFICATION - Implementation plan ready

## Purpose

The USDT Market Neutral Strategy provides market-neutral leveraged ETH staking by hedging leveraged ETH exposure with perpetual shorts. This strategy generates amplified yield through leveraged staking while maintaining delta neutrality through CEX hedging.

## 📚 **Canonical Sources**

**This strategy spec aligns with canonical architectural principles**:
- **Strategy Specifications**: [../MODES.md](../MODES.md) - USDT Market Neutral mode definition
- **Architectural Principles**: [../REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles
- **Component Specifications**: [../COMPONENT_SPECS_INDEX.md](../COMPONENT_SPECS_INDEX.md) - All 20 components
- **Configuration**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas

## Strategy Overview

### **Core Concept**
- **Asset**: ETH (staking asset)
- **Share Class**: USDT (market neutral)
- **Yield Source**: Leveraged ETH staking rewards + EIGEN rewards
- **Risk Profile**: Market neutral, leveraged staking + funding risk
- **Capital Allocation**: Split between leveraged ETH staking and CEX hedging per `stake_allocation_eth`

### **Decision Logic**
The USDT Market Neutral Strategy makes decisions based on:
1. **Capital Changes**: New deposits or withdrawals
2. **Position Rebalancing**: Maintain optimal leveraged staking/hedging allocation
3. **Risk Management**: Monitor AAVE health factor and liquidation risk
4. **Delta Management**: Monitor and adjust for delta drift

## Decision-Making Algorithm

### **Input Data Requirements**
```python
{
    'market_data': {
        'eth_price': float,              # Current ETH price
        'lst_price': float,              # LST price (weETH/ETH or wstETH/ETH)
        'aave_eth_borrow_rate': float,   # AAVE ETH borrowing rate
        'eth_perp_prices': Dict[str, float],  # ETH perpetual prices by venue
        'eth_funding_rates': Dict[str, float],  # Funding rates by venue
        'staking_rewards_rate': float,   # Current staking rewards rate
        'eigen_rewards_rate': float      # Current EIGEN rewards rate
    },
    'exposure_data': {
        'total_value_usd': float,        # Total portfolio value in USD
        'eth_balance': float,            # ETH balance
        'lst_balance': float,            # LST balance (weETH/wstETH)
        'aave_debt': float,              # AAVE debt balance
        'usdt_balance': float,           # USDT balance
        'eth_perp_short': float,         # ETH perpetual short position
        'delta_exposure': float          # Current delta exposure
    },
    'risk_assessment': {
        'aave_health_factor': float,     # AAVE health factor
        'current_ltv': float,            # Current loan-to-value ratio
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
- **Action**: Rebalance to maintain optimal leveraged staking/hedging allocation

#### **2. Risk Management Trigger**
- **AAVE Health Factor**: <1.1 triggers position reduction
- **Source**: Centralized from risk monitor via `risk_assessment['aave_health_factor']`

#### **3. Delta Drift Trigger**
- **Delta Drift**: >2% triggers hedge adjustment
- **Source**: Centralized from risk monitor via `risk_assessment['delta_drift']`

### **Decision Logic Flow**

```python
def make_strategy_decision(self, timestamp, trigger_source, market_data, exposure_data, risk_assessment):
    """
    USDT Market Neutral Strategy Decision Logic
    """
    
    # 1. Risk Assessment - Reduce position if health factor too low
    if risk_assessment['aave_health_factor'] < 1.1:
        return self._create_risk_reduction_decision(timestamp, "AAVE health factor too low")
    
    # 2. Delta Drift Check - Adjust hedge if delta drift too high
    if abs(risk_assessment['delta_drift']) > 0.02:  # 2% delta drift threshold
        return self._create_delta_adjustment_decision(timestamp, "Delta drift detected", risk_assessment['delta_drift'])
    
    # 3. Equity Deviation Check - Rebalance if equity changed significantly
    current_equity = exposure_data['total_value_usd']
    equity_deviation = self._calculate_equity_deviation(current_equity)
    
    if equity_deviation > self.config.get('position_deviation_threshold', 0.02):  # 2% default
        return self._create_rebalance_decision(timestamp, "Equity deviation detected", equity_deviation)
    
    # 4. Default: Maintain Current Position
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
        'aave_debt': exposure_data['aave_debt'],
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
    'reasoning': 'Equity deviation detected - rebalancing leveraged staking/hedging allocation',
    'target_positions': {
        'eth_balance': 0.0,  # No idle ETH
        'lst_balance': target_lst_balance,
        'aave_debt': target_aave_debt,
        'usdt_balance': target_usdt_balance,
        'eth_perp_short': target_perp_short
    },
    'execution_instructions': [
        {
            'action_type': 'atomic_leverage',
            'venue': 'instadapp',
            'asset': 'ETH',
            'amount': eth_to_leverage,
            'target_ltv': self.config.get('target_ltv', 0.9),
            'atomic': True
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

### **Risk Reduction Decision**
```python
{
    'action': 'EXIT_PARTIAL',
    'reasoning': 'AAVE health factor too low - reducing leverage',
    'target_positions': {
        'eth_balance': 0.0,
        'lst_balance': reduced_lst_balance,
        'aave_debt': reduced_aave_debt,
        'usdt_balance': exposure_data['usdt_balance'],
        'eth_perp_short': reduced_perp_short
    },
    'execution_instructions': [
        {
            'action_type': 'atomic_unwind',
            'venue': 'instadapp',
            'asset': 'ETH',
            'amount': leverage_to_reduce,
            'atomic': True
        },
        {
            'action_type': 'perp_trade',
            'venue': 'binance',
            'asset': 'ETH',
            'side': 'buy',
            'amount': perp_reduction,
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
- **Leveraged ETH Staking**: `stake_allocation_eth` proportion with target LTV
- **CEX Hedging**: `1 - stake_allocation_eth` proportion for perp shorts
- **USDT Balance**: 0% (no idle USDT)
- **Target Yield**: Leveraged staking rewards + EIGEN rewards

### **Position Calculation**
```python
def calculate_target_positions(self, total_equity, market_data):
    """
    Calculate optimal position allocation for leveraged market neutral staking
    """
    stake_allocation = self.config.get('stake_allocation_eth', 0.5)
    target_ltv = self.config.get('target_ltv', 0.9)
    leverage = target_ltv / (1 - target_ltv)  # e.g., 0.9 / 0.1 = 9x
    
    eth_price = market_data['eth_price']
    
    # Split equity between leveraged staking and hedging
    staking_equity = total_equity * stake_allocation
    hedging_equity = total_equity * (1 - stake_allocation)
    
    # Leveraged staking side
    staking_eth = staking_equity / eth_price
    leveraged_eth = staking_eth * leverage
    borrowed_eth = staking_eth * (leverage - 1)
    
    # Hedging side
    perp_short_amount = hedging_equity / eth_price
    
    return {
        'eth_balance': 0.0,
        'lst_balance': leveraged_eth,  # Leveraged ETH staked
        'aave_debt': borrowed_eth,     # Borrowed amount
        'usdt_balance': 0.0,
        'eth_perp_short': perp_short_amount  # ETH perp short
    }
```

## Risk Management

### **Risk Thresholds**
- **AAVE Health Factor**: Minimum 1.1
- **Target LTV**: 90% (configurable)
- **Liquidation Threshold**: 95%
- **Delta Drift**: Maximum 2% from neutrality

### **Risk Responses**
1. **Health Factor < 1.1**: Immediate leverage reduction
2. **LTV > 95%**: Emergency position reduction
3. **Delta Drift > 2%**: Immediate hedge adjustment

## Execution Patterns

### **Atomic Leverage Execution**
```python
{
    'action_type': 'atomic_leverage',
    'venue': 'instadapp',
    'asset': 'ETH',
    'amount': float,
    'target_ltv': float,
    'atomic': True,
    'steps': [
        'borrow_flash',
        'stake_eth',
        'supply_lst',
        'borrow_aave',
        'repay_flash'
    ]
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
- **Required Data**: ETH prices, LST prices, AAVE rates, perp prices, funding rates, staking rewards
- **Update Frequency**: Real-time for prices and rates, daily for rewards
- **Data Sources**: LST protocols, AAVE, CEX APIs

### **Risk Monitor Integration**
- **Risk Types**: AAVE health factor, LTV ratio, delta drift, LST protocol health
- **Update Frequency**: Every block for health factor, real-time for delta
- **Thresholds**: Configurable per strategy

### **Execution Manager Integration**
- **Execution Venues**: Instadapp (atomic), Lido/EtherFi (staking), AAVE (borrowing), CEX (hedging)
- **Execution Types**: Atomic leverage, perpetual trades
- **Gas Management**: Optimize for cost efficiency
- **Error Handling**: Retry logic, fallback procedures

## Configuration

### **Strategy-Specific Config**
```yaml
component_config:
  strategy_manager:
    strategy_type: "usdt_market_neutral"
    decision_parameters:
      position_deviation_threshold: 0.02  # 2% equity deviation threshold
      stake_allocation_eth: 0.5  # 50% to leveraged staking, 50% to hedging
      target_ltv: 0.9  # 90% target LTV
      max_delta_drift: 0.02  # 2% maximum delta drift
    risk_limits:
      min_aave_health_factor: 1.1
      max_ltv: 0.95
      liquidation_threshold: 0.95
      max_delta_drift: 0.02
    execution_settings:
      lst_type: "weeth"  # or "wsteth"
      staking_protocol: "etherfi"  # or "lido"
      atomic_protocol: "instadapp"
      hedge_venues: ["binance", "bybit", "okx"]
      hedge_allocation_binance: 0.4
      hedge_allocation_bybit: 0.3
      hedge_allocation_okx: 0.3
      gas_price_multiplier: 1.1
      max_gas_price_gwei: 50
      retry_attempts: 3
```

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
- **Leveraged Performance**: Actual vs expected leveraged staking rewards
- **Execution Success Rate**: Successful vs failed executions
- **Risk Metrics**: AAVE health factor, LTV ratio, delta drift, liquidation risk
- **Decision Frequency**: Number of decisions per day

### **Alerts**
- **Risk Threshold Breach**: AAVE health factor < 1.1
- **Execution Failure**: Failed execution attempts
- **Liquidation Risk**: LTV > 95%
- **Delta Drift**: Delta drift > 2%

## Future Enhancements

### **Phase 2 Enhancements**
- **Dynamic Leverage**: Adjust leverage based on market conditions
- **Advanced Delta Management**: Dynamic hedge adjustment based on volatility
- **Multi-Venue Optimization**: Dynamic venue selection for hedging

### **Phase 3 Enhancements**
- **Advanced Analytics**: ML-based leverage and allocation optimization
- **Cross-Asset Hedging**: Multi-asset hedging strategies
- **Options Integration**: Options-based hedging strategies

---

**This specification provides the foundation for implementing the USDT Market Neutral Strategy decision-making logic, maximizing leveraged staking rewards while maintaining delta neutrality.**
