# ETH Staking Only Strategy Specification

**Last Reviewed**: October 13, 2025  
**Status**: 📋 SPECIFICATION - Implementation plan ready

## Purpose

The ETH Staking Only Strategy provides unleveraged ETH staking through liquid staking tokens (LST) to collect base staking rewards and EIGEN rewards. This strategy takes directional ETH exposure while generating yield through staking.

## 📚 **Canonical Sources**

**This strategy spec aligns with canonical architectural principles**:
- **Strategy Specifications**: [../MODES.md](../MODES.md) - ETH Staking Only mode definition
- **Architectural Principles**: [../REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles
- **Component Specifications**: [../COMPONENT_SPECS_INDEX.md](../COMPONENT_SPECS_INDEX.md) - All 20 components
- **Configuration**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas

## Strategy Overview

### **Core Concept**
- **Asset**: ETH (staking asset)
- **Share Class**: ETH (directional strategy)
- **Yield Source**: Base staking rewards + EIGEN rewards
- **Risk Profile**: Directional ETH exposure, staking risk
- **Capital Allocation**: 100% ETH staked via LST (weETH/wstETH)

### **Decision Logic**
The ETH Staking Only Strategy makes decisions based on:
1. **Capital Changes**: New deposits or withdrawals
2. **Position Rebalancing**: Maintain optimal staking position
3. **Dust Management**: Convert KING tokens to ETH when threshold exceeded
4. **Reward Collection**: Collect and compound staking rewards

## Decision-Making Algorithm

### **Input Data Requirements**
```python
{
    'market_data': {
        'eth_price': float,              # Current ETH price
        'lst_price': float,              # LST price (weETH/ETH or wstETH/ETH)
        'staking_rewards_rate': float,   # Current staking rewards rate
        'eigen_rewards_rate': float      # Current EIGEN rewards rate
    },
    'exposure_data': {
        'total_value_usd': float,        # Total portfolio value in USD
        'eth_balance': float,            # ETH balance
        'lst_balance': float,            # LST balance (weETH/wstETH)
        'king_balance': float            # KING token balance (dust)
    },
    'risk_assessment': {
        'lst_protocol_health': float     # LST protocol health factor
    }
}
```

### **Decision Triggers**

#### **1. Equity Deviation Trigger (Primary)**
- **Trigger**: Portfolio equity deviates from last rebalanced state by `position_deviation_threshold`
- **Calculation**: `abs(current_equity - last_rebalanced_equity) / last_rebalanced_equity > position_deviation_threshold`
- **Default Threshold**: 2% (configurable per strategy)
- **Action**: Rebalance to maintain optimal staking position

#### **2. Dust Management Trigger**
- **KING Token Threshold**: >0.01 ETH worth triggers conversion
- **Action**: Convert KING tokens to ETH and stake

### **Decision Logic Flow**

```python
def make_strategy_decision(self, timestamp, trigger_source, market_data, exposure_data, risk_assessment):
    """
    ETH Staking Only Strategy Decision Logic
    """
    
    # 1. Dust Management - Convert KING tokens if threshold exceeded
    king_value_eth = exposure_data['king_balance'] * market_data['eth_price']
    if king_value_eth > 0.01:  # 0.01 ETH threshold
        return self._create_dust_conversion_decision(timestamp, "KING token threshold exceeded")
    
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
    'reasoning': 'Equity deviation detected - rebalancing staking position',
    'target_positions': {
        'eth_balance': 0.0,  # No idle ETH
        'lst_balance': target_lst_balance,
        'king_balance': 0.0  # No KING tokens
    },
    'execution_instructions': [
        {
            'action_type': 'stake',
            'venue': 'lido',  # or 'etherfi' based on lst_type
            'asset': 'ETH',
            'amount': eth_to_stake,
            'atomic': False
        }
    ],
    'risk_override': False,
    'estimated_cost': estimated_gas_cost,
    'priority': 'MEDIUM'
}
```

### **Dust Conversion Decision**
```python
{
    'action': 'SELL_DUST',
    'reasoning': 'KING token threshold exceeded - converting to ETH',
    'target_positions': {
        'eth_balance': 0.0,
        'lst_balance': target_lst_balance,
        'king_balance': 0.0
    },
    'execution_instructions': [
        {
            'action_type': 'convert',
            'venue': 'etherfi',
            'asset': 'KING',
            'amount': exposure_data['king_balance'],
            'target_asset': 'ETH',
            'atomic': False
        },
        {
            'action_type': 'stake',
            'venue': 'etherfi',
            'asset': 'ETH',
            'amount': converted_eth_amount,
            'atomic': False
        }
    ],
    'risk_override': False,
    'estimated_cost': estimated_gas_cost,
    'priority': 'LOW'
}
```

## Position Targets

### **Optimal Allocation**
- **ETH Staked**: 100% of equity (via LST)
- **ETH Balance**: 0% (no idle ETH)
- **KING Balance**: 0% (converted to ETH when threshold exceeded)
- **Target Yield**: Base staking rewards + EIGEN rewards

### **Position Calculation**
```python
def calculate_target_positions(self, total_equity, market_data):
    """
    Calculate optimal position allocation for ETH staking
    """
    eth_price = market_data['eth_price']
    eth_amount = total_equity / eth_price
    
    return {
        'eth_balance': 0.0,
        'lst_balance': eth_amount,  # All ETH staked
        'king_balance': 0.0
    }
```

## Risk Management

### **Risk Thresholds**
- **LST Protocol Health**: Monitor protocol health factor
- **Dust Threshold**: 0.01 ETH worth of KING tokens

### **Risk Responses**
1. **LST Protocol Health < 0.8**: Monitor and potentially exit
2. **KING Token Threshold > 0.01 ETH**: Convert to ETH and stake

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

### **Dust Conversion Execution**
```python
{
    'action_type': 'convert',
    'venue': 'etherfi',
    'asset': 'KING',
    'amount': float,
    'target_asset': 'ETH',
    'atomic': False
}
```

## Integration Points

### **Data Provider Integration**
- **Required Data**: ETH prices, LST prices, staking rewards, EIGEN rewards
- **Update Frequency**: Real-time for prices, daily for rewards
- **Data Sources**: LST protocols (Lido, EtherFi)

### **Risk Monitor Integration**
- **Risk Types**: LST protocol health, dust accumulation
- **Update Frequency**: Daily for protocol health, real-time for dust
- **Thresholds**: Configurable per strategy

### **Execution Manager Integration**
- **Execution Venues**: Lido (wstETH) or EtherFi (weETH)
- **Execution Types**: Staking, unstaking, dust conversion
- **Gas Management**: Optimize for cost efficiency
- **Error Handling**: Retry logic, fallback procedures

## Configuration

### **Strategy-Specific Config**
```yaml
component_config:
  strategy_manager:
    strategy_type: "eth_staking_only"
    decision_parameters:
      position_deviation_threshold: 0.02  # 2% equity deviation threshold
      dust_threshold_eth: 0.01  # 0.01 ETH dust threshold
    risk_limits:
      min_lst_protocol_health: 0.8
    execution_settings:
      lst_type: "weeth"  # or "wsteth"
      staking_protocol: "etherfi"  # or "lido"
      gas_price_multiplier: 1.1
      max_gas_price_gwei: 50
      retry_attempts: 3
```

## Config Fields Used

### Universal Config (All Strategies)
- **mode**: str - Strategy mode name ('eth_staking_only')
- **share_class**: str - 'USDT' | 'ETH'
- **asset**: str - Primary asset ('ETH')
- **initial_capital**: float - Starting capital amount
- **environment**: str - 'backtest' | 'live'
- **execution_mode**: str - 'backtest' | 'live'
- **validation_strict**: bool - Strict validation mode

### Strategy-Specific Config
- **staking_supported**: bool - Whether staking is supported
- **rewards_mode**: str - Rewards calculation mode
- **stake_allocation_eth**: float - ETH allocation for staking

### Venue Configuration
- **venues.etherfi.venue_type**: str - Venue type ('defi')
- **venues.etherfi.enabled**: bool - Whether EtherFi is enabled
- **venues.etherfi.instruments**: List[str] - Available instruments
- **venues.etherfi.order_types**: List[str] - Available order types
- **venues.alchemy.venue_type**: str - Venue type ('defi')
- **venues.alchemy.enabled**: bool - Whether Alchemy is enabled
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
- **Staking Performance**: Actual vs expected staking rewards
- **Execution Success Rate**: Successful vs failed executions
- **Risk Metrics**: LST protocol health, dust accumulation
- **Decision Frequency**: Number of decisions per day

### **Alerts**
- **Risk Threshold Breach**: LST protocol health < 0.8
- **Execution Failure**: Failed execution attempts
- **Dust Accumulation**: KING token balance > threshold

## Future Enhancements

### **Phase 2 Enhancements**
- **Multi-LST Strategy**: Dynamic LST selection based on rewards
- **Advanced Dust Management**: Automated dust conversion optimization
- **Reward Optimization**: Dynamic reward collection timing

### **Phase 3 Enhancements**
- **Cross-Protocol Staking**: Multi-protocol staking strategies
- **Advanced Analytics**: ML-based staking reward prediction
- **Risk Hedging**: Options-based ETH price hedging

---

**This specification provides the foundation for implementing the ETH Staking Only Strategy decision-making logic, maximizing staking rewards while managing directional ETH exposure.**
