# ETH Leveraged Strategy Specification

**Last Reviewed**: October 13, 2025  
**Status**: 📋 SPECIFICATION - Implementation plan ready

## Purpose

The ETH Leveraged Strategy provides leveraged ETH staking through LST collateral and AAVE borrowing to amplify staking rewards. This strategy uses atomic flash loans to create leveraged positions while taking directional ETH exposure.

## 📚 **Canonical Sources**

**This strategy spec aligns with canonical architectural principles**:
- **Strategy Specifications**: [../MODES.md](../MODES.md) - ETH Leveraged mode definition
- **Architectural Principles**: [../REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles
- **Component Specifications**: [../COMPONENT_SPECS_INDEX.md](../COMPONENT_SPECS_INDEX.md) - All 20 components
- **Configuration**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas

## Strategy Overview

### **Core Concept**
- **Asset**: ETH (staking asset)
- **Share Class**: ETH (directional strategy)
- **Yield Source**: Leveraged staking rewards + EIGEN rewards
- **Risk Profile**: Leveraged ETH exposure, liquidation risk
- **Capital Allocation**: Leveraged ETH staking via LST + AAVE borrowing

### **Decision Logic**
The ETH Leveraged Strategy makes decisions based on:
1. **Capital Changes**: New deposits or withdrawals
2. **Position Rebalancing**: Maintain optimal leveraged position
3. **Risk Management**: Monitor LTV and liquidation risk
4. **Dust Management**: Convert KING tokens to ETH when threshold exceeded

## Decision-Making Algorithm

### **Input Data Requirements**
```python
{
    'market_data': {
        'eth_price': float,              # Current ETH price
        'lst_price': float,              # LST price (weETH/ETH or wstETH/ETH)
        'aave_eth_borrow_rate': float,   # AAVE ETH borrowing rate
        'staking_rewards_rate': float,   # Current staking rewards rate
        'eigen_rewards_rate': float      # Current EIGEN rewards rate
    },
    'exposure_data': {
        'total_value_usd': float,        # Total portfolio value in USD
        'eth_balance': float,            # ETH balance
        'lst_balance': float,            # LST balance (weETH/wstETH)
        'aave_debt': float,              # AAVE debt balance
        'king_balance': float            # KING token balance (dust)
    },
    'risk_assessment': {
        'aave_health_factor': float,     # AAVE health factor
        'current_ltv': float,            # Current loan-to-value ratio
        'lst_protocol_health': float     # LST protocol health factor
    }
}
```

### **Decision Triggers**

#### **1. Equity Deviation Trigger (Primary)**
- **Trigger**: Portfolio equity deviates from last rebalanced state by `position_deviation_threshold`
- **Calculation**: `abs(current_equity - last_rebalanced_equity) / last_rebalanced_equity > position_deviation_threshold`
- **Default Threshold**: 2% (configurable per strategy)
- **Action**: Rebalance to maintain optimal leveraged position

#### **2. Risk Management Trigger**
- **AAVE Health Factor**: <1.1 triggers position reduction
- **Source**: Centralized from risk monitor via `risk_assessment['aave_health_factor']`

#### **3. Dust Management Trigger**
- **KING Token Threshold**: >0.01 ETH worth triggers conversion
- **Action**: Convert KING tokens to ETH and stake

### **Decision Logic Flow**

```python
def make_strategy_decision(self, timestamp, trigger_source, market_data, exposure_data, risk_assessment):
    """
    ETH Leveraged Strategy Decision Logic
    """
    
    # 1. Risk Assessment - Reduce position if health factor too low
    if risk_assessment['aave_health_factor'] < 1.1:
        return self._create_risk_reduction_decision(timestamp, "AAVE health factor too low")
    
    # 2. Dust Management - Convert KING tokens if threshold exceeded
    king_value_eth = exposure_data['king_balance'] * market_data['eth_price']
    if king_value_eth > 0.01:  # 0.01 ETH threshold
        return self._create_dust_conversion_decision(timestamp, "KING token threshold exceeded")
    
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
        'king_balance': exposure_data['king_balance']
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
    'reasoning': 'Equity deviation detected - rebalancing leveraged position',
    'target_positions': {
        'eth_balance': 0.0,  # No idle ETH
        'lst_balance': target_lst_balance,
        'aave_debt': target_aave_debt,
        'king_balance': 0.0  # No KING tokens
    },
    'execution_instructions': [
        {
            'action_type': 'atomic_leverage',
            'venue': 'instadapp',
            'asset': 'ETH',
            'amount': eth_to_leverage,
            'target_ltv': self.config.get('target_ltv', 0.9),
            'atomic': True
        }
    ],
    'risk_override': False,
    'estimated_cost': estimated_gas_cost,
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
        'king_balance': 0.0
    },
    'execution_instructions': [
        {
            'action_type': 'atomic_unwind',
            'venue': 'instadapp',
            'asset': 'ETH',
            'amount': leverage_to_reduce,
            'atomic': True
        }
    ],
    'risk_override': True,
    'estimated_cost': estimated_gas_cost,
    'priority': 'HIGH'
}
```

## Position Targets

### **Optimal Allocation**
- **Leveraged ETH Staking**: Target LTV-based leverage (e.g., 9x at 90% LTV)
- **ETH Balance**: 0% (no idle ETH)
- **KING Balance**: 0% (converted to ETH when threshold exceeded)
- **Target Yield**: Leveraged staking rewards + EIGEN rewards

### **Position Calculation**
```python
def calculate_target_positions(self, total_equity, market_data):
    """
    Calculate optimal position allocation for leveraged ETH staking
    """
    target_ltv = self.config.get('target_ltv', 0.9)
    leverage = target_ltv / (1 - target_ltv)  # e.g., 0.9 / 0.1 = 9x
    
    eth_price = market_data['eth_price']
    total_eth = total_equity / eth_price
    
    return {
        'eth_balance': 0.0,
        'lst_balance': total_eth * leverage,  # Leveraged staking
        'aave_debt': total_eth * (leverage - 1),  # Borrowed amount
        'king_balance': 0.0
    }
```

## Risk Management

### **Risk Thresholds**
- **AAVE Health Factor**: Minimum 1.1
- **Target LTV**: 90% (configurable)
- **Liquidation Threshold**: 95%
- **Dust Threshold**: 0.01 ETH worth of KING tokens

### **Risk Responses**
1. **Health Factor < 1.1**: Immediate leverage reduction
2. **LTV > 95%**: Emergency position reduction
3. **KING Token Threshold > 0.01 ETH**: Convert to ETH and stake

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

### **Atomic Unwind Execution**
```python
{
    'action_type': 'atomic_unwind',
    'venue': 'instadapp',
    'asset': 'ETH',
    'amount': float,
    'atomic': True,
    'steps': [
        'repay_aave',
        'withdraw_lst',
        'unstake_eth',
        'repay_flash'
    ]
}
```

## Integration Points

### **Data Provider Integration**
- **Required Data**: ETH prices, LST prices, AAVE rates, staking rewards, EIGEN rewards
- **Update Frequency**: Real-time for prices and rates, daily for rewards
- **Data Sources**: LST protocols, AAVE, price oracles

### **Risk Monitor Integration**
- **Risk Types**: AAVE health factor, LTV ratio, LST protocol health
- **Update Frequency**: Every block for health factor, real-time for LTV
- **Thresholds**: Configurable per strategy

### **Execution Manager Integration**
- **Execution Venues**: Instadapp (atomic), Lido/EtherFi (staking), AAVE (borrowing)
- **Execution Types**: Atomic leverage, atomic unwind, dust conversion
- **Gas Management**: Optimize for cost efficiency
- **Error Handling**: Retry logic, fallback procedures

## Configuration

### **Strategy-Specific Config**
```yaml
component_config:
  strategy_manager:
    strategy_type: "eth_leveraged"
    decision_parameters:
      position_deviation_threshold: 0.02  # 2% equity deviation threshold
      target_ltv: 0.9  # 90% target LTV
      dust_threshold_eth: 0.01  # 0.01 ETH dust threshold
    risk_limits:
      min_aave_health_factor: 1.1
      max_ltv: 0.95
      liquidation_threshold: 0.95
    execution_settings:
      lst_type: "weeth"  # or "wsteth"
      staking_protocol: "etherfi"  # or "lido"
      atomic_protocol: "instadapp"
      gas_price_multiplier: 1.1
      max_gas_price_gwei: 50
      retry_attempts: 3
```

## Config Fields Used

### Universal Config (All Strategies)
- **mode**: str - Strategy mode name ('eth_leveraged')
- **share_class**: str - 'USDT' | 'ETH'
- **asset**: str - Primary asset ('ETH')
- **initial_capital**: float - Starting capital amount
- **environment**: str - 'backtest' | 'live'
- **execution_mode**: str - 'backtest' | 'live'
- **validation_strict**: bool - Strict validation mode

### Strategy-Specific Config
- **leverage_enabled**: bool - Whether leverage is enabled
- **leverage_supported**: bool - Whether leverage is supported
- **max_leverage**: float - Maximum leverage ratio
- **staking_supported**: bool - Whether staking is supported
- **stake_allocation_percentage**: float - Percentage of capital allocated to staking
  - **Usage**: Defines proportion of capital allocated to ETH staking operations
  - **Examples**: 0.5 (50% of capital for staking)
  - **Used in**: Capital allocation and position sizing logic

### Venue Configuration
- **venues.etherfi.venue_type**: str - Venue type ('defi')
- **venues.etherfi.instruments**: List[str] - Available instruments
- **venues.etherfi.order_types**: List[str] - Available order types
- **venues.alchemy.venue_type**: str - Venue type ('defi')
- **venues.alchemy.instruments**: List[str] - Available instruments
- **venues.alchemy.order_types**: List[str] - Available order types

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
- **Leveraged Performance**: Actual vs expected leveraged staking rewards
- **Execution Success Rate**: Successful vs failed executions
- **Risk Metrics**: AAVE health factor, LTV ratio, liquidation risk
- **Decision Frequency**: Number of decisions per day

### **Alerts**
- **Risk Threshold Breach**: AAVE health factor < 1.1
- **Execution Failure**: Failed execution attempts
- **Liquidation Risk**: LTV > 95%

## Future Enhancements

### **Phase 2 Enhancements**
- **Dynamic Leverage**: Adjust leverage based on market conditions
- **Advanced Risk Management**: Dynamic position sizing based on volatility
- **Multi-Protocol Leverage**: Cross-protocol leverage strategies

### **Phase 3 Enhancements**
- **Advanced Analytics**: ML-based leverage optimization
- **Risk Hedging**: Options-based ETH price hedging
- **Cross-Asset Leverage**: Multi-asset leverage strategies

---

**This specification provides the foundation for implementing the ETH Leveraged Strategy decision-making logic, maximizing leveraged staking rewards while managing liquidation risk.**
