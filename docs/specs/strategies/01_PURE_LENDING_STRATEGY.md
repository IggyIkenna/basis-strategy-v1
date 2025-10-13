# Pure Lending Strategy Specification

**Last Reviewed**: October 13, 2025  
**Status**: 📋 SPECIFICATION - Implementation plan ready

## Purpose

The Pure Lending Strategy provides a simple, low-risk yield generation strategy by lending USDT on AAVE and earning supply yield. This strategy serves as the foundation for more complex strategies and demonstrates the basic decision-making patterns.

## 📚 **Canonical Sources**

**This strategy spec aligns with canonical architectural principles**:
- **Strategy Specifications**: [../MODES.md](../MODES.md) - Pure Lending mode definition
- **Architectural Principles**: [../REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles
- **Component Specifications**: [../COMPONENT_SPECS_INDEX.md](../COMPONENT_SPECS_INDEX.md) - All 20 components
- **Configuration**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas

## Strategy Overview

### **Core Concept**
- **Asset**: USDT (share class currency)
- **Yield Source**: AAVE USDT supply yield
- **Risk Profile**: Low risk, stable yield
- **Capital Allocation**: 100% USDT → AAVE lending
- **Hedging**: None required (no directional exposure)

### **Decision Logic**
The Pure Lending Strategy makes decisions based on:
1. **Capital Changes**: New deposits or withdrawals
2. **Yield Optimization**: Rebalancing to maximize yield
3. **Risk Management**: Monitoring AAVE health factors
4. **Liquidity Management**: Maintaining sufficient liquidity for withdrawals

## Decision-Making Algorithm

### **Input Data Requirements**
```python
{
    'market_data': {
        'aave_usdt_supply_rate': float,  # Current USDT supply rate on AAVE
        'aave_usdt_borrow_rate': float,  # Current USDT borrow rate on AAVE
        'usdt_price': float             # USDT price (should be ~1.0)
    },
    'exposure_data': {
        'total_value_usd': float,       # Total portfolio value in USD
        'usdt_balance': float,          # USDT balance in wallet
        'ausdt_balance': float          # aUSDT balance (lent on AAVE)
    },
    'risk_assessment': {
        'aave_health_factor': float     # AAVE protocol health (centralized from risk monitor)
    }
}
```

### **Decision Triggers**

#### **1. Equity Deviation Trigger (Primary)**
- **Trigger**: Portfolio equity deviates from last rebalanced state by `position_deviation_threshold`
- **Calculation**: `abs(current_equity - last_rebalanced_equity) / last_rebalanced_equity > position_deviation_threshold`
- **Default Threshold**: 2% (configurable per strategy)
- **Action**: Rebalance to optimal allocation (100% AAVE lending)

#### **2. Risk Management Trigger**
- **AAVE Health Factor**: <1.5 triggers immediate exit to wallet
- **Source**: Centralized from risk monitor via `risk_assessment['aave_health_factor']`

### **Decision Logic Flow**

```python
def make_strategy_decision(self, timestamp, trigger_source, market_data, exposure_data, risk_assessment):
    """
    Pure Lending Strategy Decision Logic
    """
    
    # 1. Risk Assessment - Exit if AAVE health factor too low
    if risk_assessment['aave_health_factor'] < 1.5:
        return self._create_risk_exit_decision(timestamp, "AAVE health factor too low")
    
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
        'usdt_wallet': exposure_data['usdt_balance'],
        'ausdt_aave': exposure_data['ausdt_balance']
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
    'reasoning': 'Equity deviation detected - rebalancing to optimal allocation',
    'target_positions': {
        'usdt_wallet': 0.0,  # No wallet balance needed for pure lending
        'ausdt_aave': current_equity  # All equity goes to AAVE lending
    },
    'execution_instructions': [
        {
            'action_type': 'lend',
            'venue': 'aave',
            'asset': 'USDT',
            'amount': current_equity - exposure_data['ausdt_balance'],  # Difference to lend
            'atomic': False
        }
    ],
    'risk_override': False,
    'estimated_cost': estimated_gas_cost,
    'priority': 'MEDIUM'
}
```

### **Risk Exit Decision**
```python
{
    'action': 'EXIT',
    'reasoning': 'AAVE health factor too low - exiting to preserve capital',
    'target_positions': {
        'usdt_wallet': exposure_data['total_value_usd'],
        'ausdt_aave': 0.0
    },
    'execution_instructions': [
        {
            'action_type': 'withdraw',
            'venue': 'aave',
            'asset': 'USDT',
            'amount': exposure_data['ausdt_balance'],
            'atomic': False
        }
    ],
    'risk_override': True,
    'estimated_cost': estimated_gas_cost,
    'priority': 'CRITICAL'
}
```

## Position Targets

### **Optimal Allocation**
- **AAVE Lending**: 100% of total equity
- **Wallet Liquidity**: 0% (pure lending strategy)
- **Target Yield**: Maximize AAVE USDT supply rate

### **Position Calculation**
```python
def calculate_target_positions(self, total_equity, market_data):
    """
    Calculate optimal position allocation for pure lending
    """
    # All equity goes to AAVE lending (pure lending strategy)
    return {
        'usdt_wallet': 0.0,
        'ausdt_aave': total_equity
    }
```

## Risk Management

### **Risk Thresholds**
- **AAVE Health Factor**: Minimum 1.5 (from risk monitor)

### **Risk Responses**
1. **Health Factor < 1.5**: Immediate exit to wallet (withdraw all from AAVE)

## Execution Patterns

### **Lending Execution**
```python
{
    'action_type': 'lend',
    'venue': 'aave',
    'asset': 'USDT',
    'amount': float,
    'atomic': False,
    'gas_estimate': float,
    'slippage_tolerance': 0.001
}
```

### **Withdrawal Execution**
```python
{
    'action_type': 'withdraw',
    'venue': 'aave',
    'asset': 'USDT',
    'amount': float,
    'atomic': False,
    'gas_estimate': float,
    'slippage_tolerance': 0.001
}
```

## Integration Points

### **Data Provider Integration**
- **Required Data**: AAVE rates, USDT price, protocol health
- **Update Frequency**: Real-time for rates, hourly for health
- **Data Sources**: AAVE subgraph, price oracles

### **Risk Monitor Integration**
- **Risk Types**: AAVE health factor, liquidity risk, concentration risk
- **Update Frequency**: Every block for health factor, daily for others
- **Thresholds**: Configurable per strategy

### **Execution Manager Integration**
- **Execution Venues**: AAVE V3
- **Execution Types**: Lending, withdrawal
- **Gas Management**: Optimize for cost efficiency
- **Error Handling**: Retry logic, fallback procedures

## Configuration

### **Strategy-Specific Config**
```yaml
component_config:
  strategy_manager:
    strategy_type: "pure_lending"
    decision_parameters:
      position_deviation_threshold: 0.02  # 2% equity deviation threshold
    risk_limits:
      min_aave_health_factor: 1.5
    execution_settings:
      gas_price_multiplier: 1.1
      max_gas_price_gwei: 50
      retry_attempts: 3
```

## Config Fields Used

### Universal Config (All Strategies)
- **mode**: str - Strategy mode name ('pure_lending')
- **share_class**: str - 'USDT' | 'ETH'
- **asset**: str - Primary asset ('USDT')
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
  - **Example**: {"min": 0.04, "max": 0.06} for 4-6% APY range
  - **Used in**: Quality gate validation and performance monitoring

- **max_drawdown**: float - Maximum drawdown threshold
  - **Usage**: Risk management threshold for strategy
  - **Used in**: Risk monitoring and position sizing

- **max_ltv**: float - Maximum loan-to-value ratio
  - **Usage**: Maximum LTV for lending positions
  - **Used in**: Position sizing and risk management

- **position_deviation_threshold**: float - Position deviation threshold
  - **Usage**: Triggers rebalancing when equity deviates
  - **Default**: 0.02 (2%)
  - **Used in**: Rebalancing decision logic

### Venue Configuration
- **venues.aave_v3.venue_type**: str - Venue type ('defi')
- **venues.aave_v3.enabled**: bool - Whether AAVE v3 is enabled
- **venues.aave_v3.instruments**: List[str] - Available instruments
- **venues.aave_v3.order_types**: List[str] - Available order types

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
- **Yield Performance**: Actual vs expected yield from AAVE
- **Execution Success Rate**: Successful vs failed executions
- **Risk Metrics**: AAVE health factor
- **Decision Frequency**: Number of decisions per day

### **Alerts**
- **Risk Threshold Breach**: AAVE health factor < 1.5
- **Execution Failure**: Failed execution attempts

## Future Enhancements

### **Phase 2 Enhancements**
- **Multi-Venue Lending**: Compound, Morpho integration
- **Yield Optimization**: Dynamic venue selection
- **Liquidity Management**: Automated liquidity optimization

### **Phase 3 Enhancements**
- **Risk Hedging**: Insurance protocol integration
- **Yield Strategies**: Curve pool integration
- **Advanced Analytics**: ML-based yield prediction

---

**This specification provides the foundation for implementing the Pure Lending Strategy decision-making logic, serving as a template for other strategy implementations.**
