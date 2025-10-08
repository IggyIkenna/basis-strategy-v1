# Workflow Guide - Complete System Architecture 🏗️

**Purpose**: Visual roadmap of all workflows, environments, and strategy modes  
**Status**: ✅ COMPLETE - Comprehensive system documentation (core components implemented, critical issues remain)  
**Updated**: January 6, 2025

---

## 📚 **Key References**

- **Component Details** → [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md)
- **Architecture Decisions** → [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md)
- **Configuration** → [CONFIG_WORKFLOW.md](CONFIG_WORKFLOW.md)
- **Implementation Status** → [REPO_INTEGRATION_PLAN.md](REPO_INTEGRATION_PLAN.md)

---

## 🎯 **System Overview**

The Basis Strategy system is a **component-based, event-driven architecture** that seamlessly switches between backtest and live modes while maintaining the same execution interfaces and data flow patterns.

### **Core Architecture Principles**
- **Component-Based**: 9 core components with clear responsibilities
- **Event-Driven**: Synchronous event chain with audit logging
- **Mode-Agnostic**: Same interfaces for backtest and live execution
- **Fail-Fast**: Explicit configuration with no hidden defaults
- **Audit-Grade**: Complete event trail with balance snapshots

---

## 🔄 **High-Level System Workflow**

```mermaid
graph TB
    subgraph "Configuration Layer"
        A[Config Loading] --> B[Environment Detection]
        B --> C[Mode Selection]
        C --> D[Strategy Configuration]
    end
    
    subgraph "Data Layer"
        E[Data Provider] --> F{Execution Mode?}
        F -->|Backtest| G[Historical CSV Data]
        F -->|Live| H[Real-time APIs]
    end
    
    subgraph "Event Engine"
        I[EventDrivenStrategyEngine] --> J[Component Initialization]
        J --> K[Event Loop]
    end
    
    subgraph "Event Chain"
        L[Position Monitor] --> M[Exposure Monitor]
        M --> N[Risk Monitor]
        N --> O[P&L Calculator]
        O --> P[Strategy Manager]
    end
    
    subgraph "Execution Layer"
        Q[Execution Interfaces] --> R{Interface Type?}
        R -->|CEX| S[CEX Execution Interface]
        R -->|OnChain| T[OnChain Execution Interface]
        R -->|Transfer| U[Transfer Execution Interface]
    end
    
    subgraph "Logging Layer"
        V[Event Logger] --> W[Redis Pub/Sub]
        V --> X[Audit Trail]
    end
    
    A --> E
    E --> I
    I --> L
    P --> Q
    Q --> V
    
    style A fill:#e1f5fe
    style E fill:#f3e5f5
    style I fill:#e8f5e8
    style L fill:#fff3e0
    style Q fill:#fce4ec
    style V fill:#f1f8e9
```

---

## 🏗️ **Environment & Configuration Workflow**

### **Configuration Loading Hierarchy**

```mermaid
graph TD
    A[System Start] --> B[Load Base JSON Configs]
    B --> C[Load Environment JSON Configs]
    C --> D[Load Local JSON Configs]
    D --> E[Load YAML Mode Configs]
    E --> F[Load YAML Venue Configs]
    F --> G[Load YAML Share Class Configs]
    G --> H[Load Environment Variables]
    H --> I[Validate Configuration]
    I --> J{Valid?}
    J -->|Yes| K[Initialize Components]
    J -->|No| L[Fail Fast with Error]
    
    style B fill:#ffcccc
    style C fill:#ffcccc
    style D fill:#ffcccc
    style E fill:#ccffcc
    style F fill:#ccffcc
    style G fill:#ccffcc
    style H fill:#ffffcc
    style I fill:#ccffcc
    
    style A fill:#e3f2fd
    style K fill:#e8f5e8
    style L fill:#ffebee
```

**Note**: JSON base configuration files (`default.json`, `{environment}.json`, `local.json`) are documented but not implemented. The system currently uses YAML-based configuration only.

### **Configuration Files Structure**

| File | Purpose | Environment | Priority | Status |
|------|---------|-------------|----------|---------|
| YAML Configs | Mode/Venue/Share Class | Current implementation | ✅ Implemented | ✅ Working |
| JSON Hierarchy | Base/Environment/Local | Documented but missing | ❌ Not implemented | ❌ Missing |
| `env.unified` | Application variables | All | 4 | ✅ Working |
| `deploy/.env*` | Deployment variables | Specific | 5 (highest) | ✅ Working |

**Implementation Note**: The configuration loader attempts to load JSON files first, but they don't exist. The system falls back to YAML-only configuration successfully.

### **Code References**
- **Config Loading**: `backend/src/basis_strategy_v1/infrastructure/config/settings.py:get_settings()`
- **Environment Detection**: `backend/src/basis_strategy_v1/infrastructure/config/settings.py:detect_strategy_mode()`
- **Validation**: `backend/src/basis_strategy_v1/infrastructure/config/config_validator.py`

---

## 📊 **Data Provider Workflow**

### **Data Loading by Strategy Mode**

```mermaid
graph TD
    A[DataProvider.__init__] --> B{Execution Mode?}
    B -->|backtest| C[Load Historical Data]
    B -->|live| D[Initialize LiveDataProvider]
    
    C --> E{Strategy Mode?}
    E -->|pure_lending| F[Load USDT AAVE Rates]
    E -->|btc_basis| G[Load BTC Spot + Futures]
    E -->|eth_leveraged| H[Load ETH + LST Data]
    E -->|usdt_market_neutral| I[Load ETH + LST + CEX Data]
    
    F --> J[Load Gas Costs]
    G --> J
    H --> J
    I --> J
    J --> K[Validate Data Alignment]
    K --> L[Data Ready]
    
    D --> M[Configure Live APIs]
    M --> N[Initialize WebSocket Connections]
    N --> L
    
    style A fill:#e1f5fe
    style C fill:#f3e5f5
    style D fill:#f3e5f5
    style L fill:#e8f5e8
```

### **Data Requirements by Mode**

| Mode | Required Data | Files |
|------|---------------|-------|
| **pure_lending** | USDT AAVE rates, gas costs | `aave_v3_aave-v3-ethereum_USDT_rates_*.csv` |
| **btc_basis** | BTC spot, futures, funding | `binance_BTCUSDT_spot_*.csv`, `binance_BTCUSDT_futures_*.csv` |
| **eth_leveraged** | ETH prices, LST data, AAVE rates | `binance_ETHUSDT_spot_*.csv`, `curve_weETHWETH_*.csv` |
| **usdt_market_neutral** | All ETH data + CEX futures | All above + `bybit_ETHUSDT_futures_*.csv` |

### **Code References**
- **Historical Data**: `backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py:_load_data_for_mode()`
- **Live Data**: `backend/src/basis_strategy_v1/infrastructure/data/live_data_provider.py:get_market_data_snapshot()`
- **Data Validation**: `backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py:_validate_timestamps()`

---

## ⚙️ **Event Engine Initialization Workflow**

### **Component Initialization Sequence**

```mermaid
graph TD
    A[EventDrivenStrategyEngine.__init__] --> B[Load Configuration]
    B --> C[Detect Mode & Share Class]
    C --> D[Initialize DataProvider]
    D --> E[Initialize PositionMonitor]
    E --> F[Initialize EventLogger]
    F --> G[Initialize ExposureMonitor]
    G --> H[Initialize RiskMonitor]
    H --> I[Initialize PnLCalculator]
    I --> J[Initialize StrategyManager]
    J --> K[Initialize CEXExecutionManager]
    K --> L[Initialize OnChainExecutionManager]
    L --> M[Create Execution Interfaces]
    M --> N[Set Interface Dependencies]
    N --> O[Engine Ready]
    
    style A fill:#e3f2fd
    style O fill:#e8f5e8
```

### **Execution Interface Creation**

```mermaid
graph TD
    A[ExecutionInterfaceFactory.create_all_interfaces] --> B[Create CEXExecutionInterface]
    B --> C[Create OnChainExecutionInterface]
    C --> D[Create TransferExecutionInterface]
    D --> E[Set Dependencies]
    E --> F[Connect Transfer Interface]
    F --> G[Interfaces Ready]
    
    style A fill:#e1f5fe
    style G fill:#e8f5e8
```

### **Code References**
- **Engine Init**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py:_initialize_components()`
- **Interface Factory**: `backend/src/basis_strategy_v1/core/interfaces/execution_interface_factory.py:create_all_interfaces()`
- **Dependencies**: `backend/src/basis_strategy_v1/core/interfaces/execution_interface_factory.py:set_interface_dependencies()`

---

## 🔄 **Event Chain Workflow**

### **Synchronous Event Processing**

```mermaid
graph TD
    A[Market Data Update] --> B[Position Monitor]
    B --> C[Get Position Snapshot]
    C --> D[Exposure Monitor]
    D --> E[Calculate Exposure]
    E --> F[Risk Monitor]
    F --> G[Assess Risk]
    G --> H[P&L Calculator]
    H --> I[Calculate P&L]
    I --> J{Needs Action?}
    J -->|Yes| K[Strategy Manager]
    J -->|No| L[Log Event]
    K --> M[Generate Instructions]
    M --> N[Execute Instructions]
    N --> O[Update Positions]
    O --> L
    L --> P[Event Logger]
    P --> Q[Redis Pub/Sub]
    P --> R[Audit Trail]
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
    style D fill:#fff3e0
    style F fill:#fff3e0
    style H fill:#fff3e0
    style K fill:#e8f5e8
    style P fill:#f1f8e9
```

### **Event Chain Methods**

| Component | Method | Purpose | Input | Output |
|-----------|--------|---------|-------|--------|
| **Position Monitor** | `get_snapshot()` | Get current positions | None | Position dict |
| **Exposure Monitor** | `calculate_exposure()` | Convert to share class | timestamp, position, market_data | Exposure dict |
| **Risk Monitor** | `assess_risk()` | Calculate risk metrics | exposure, market_data | Risk dict |
| **P&L Calculator** | `calculate_pnl()` | Calculate performance | exposure, timestamp | P&L dict |
| **Strategy Manager** | `make_strategy_decision()` | Generate instructions | exposure, risk | Instructions list |

### **Code References**
- **Event Processing**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py:_process_timestep()`
- **Position Monitor**: `backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py:get_snapshot()`
- **Exposure Monitor**: `backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py:calculate_exposure()`
- **Risk Monitor**: `backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py:assess_risk()`

---

## 🚀 **Execution Workflow**

### **Execution Interface Selection**

```mermaid
graph TD
    A[Strategy Decision] --> B{Instruction Type?}
    B -->|CEX Trade| C[CEXExecutionInterface]
    B -->|OnChain Op| D[OnChainExecutionInterface]
    B -->|Cross-Venue Transfer| E[TransferExecutionInterface]
    
    C --> F{Execution Mode?}
    D --> F
    E --> F
    
    F -->|backtest| G[Simulate Execution]
    F -->|live| H[Real Execution]
    
    G --> I[Update Position Monitor]
    H --> I
    I --> J[Log Event]
    J --> K[Return Result]
    
    style A fill:#e3f2fd
    style C fill:#fce4ec
    style D fill:#fce4ec
    style E fill:#fce4ec
    style G fill:#fff3e0
    style H fill:#e8f5e8
```

**Implementation Note**: Execution managers are implemented as interfaces (`CEXExecutionInterface`, `OnChainExecutionInterface`, `TransferExecutionInterface`) rather than separate manager classes. The interfaces are created by `ExecutionInterfaceFactory` and handle both backtest simulation and live execution.

### **Cross-Venue Transfer Workflow**

```mermaid
graph TD
    A[Transfer Instruction] --> B[TransferExecutionInterface]
    B --> C[CrossVenueTransferManager]
    C --> D[Plan Transfer Steps]
    D --> E[Validate Safety]
    E --> F{Valid?}
    F -->|No| G[Return Error]
    F -->|Yes| H[Execute Steps]
    
    H --> I{Step Type?}
    I -->|CEX| J[CEXExecutionInterface]
    I -->|OnChain| K[OnChainExecutionInterface]
    
    J --> L[Execute Step]
    K --> L
    L --> M[Wait for Completion]
    M --> N{More Steps?}
    N -->|Yes| I
    N -->|No| O[Return Success]
    
    style A fill:#e3f2fd
    style C fill:#e8f5e8
    style G fill:#ffebee
    style O fill:#e8f5e8
```

### **Code References**
- **Execution Routing**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py:_execute_strategy_decision()`
- **Transfer Interface**: `backend/src/basis_strategy_v1/core/interfaces/transfer_execution_interface.py:execute_transfer()`
- **Transfer Manager**: `backend/src/basis_strategy_v1/core/rebalancing/transfer_manager.py:execute_optimal_transfer()`

---

## 📝 **Event Logging Workflow**

### **Event Logging Chain**

```mermaid
graph TD
    A[Event Occurs] --> B[EventLogger.log_event]
    B --> C[Assign Global Order]
    C --> D[Create Event Object]
    D --> E[Add Position Snapshot]
    E --> F[Store in Memory]
    F --> G{Execution Mode?}
    G -->|backtest| H[Store Locally]
    G -->|live| I[Publish to Redis]
    I --> J[Redis Subscribers]
    J --> K[Real-time Monitoring]
    H --> L[Audit Trail]
    K --> L
    
    style A fill:#e3f2fd
    style B fill:#f1f8e9
    style L fill:#e8f5e8
```

**Implementation Note**: Redis is only used in the Event Logger component for live mode. Other components use direct method calls for communication, not Redis pub/sub as described in the Redis Messaging Standard.

### **Event Structure**

```json
{
  "timestamp": "2024-06-01T12:00:00Z",
  "order": 12345,
  "event_type": "ATOMIC_LEVERAGE_ENTRY",
  "venue": "AAVE",
  "token": "weETH",
  "amount": 100.0,
  "status": "completed",
  "wallet_balance_after": {...},
  "cex_balance_after": {...},
  "aave_position_after": {...}
}
```

### **Code References**
- **Event Logging**: `backend/src/basis_strategy_v1/core/strategies/components/event_logger.py:log_event()`
- **Redis Publishing**: `backend/src/basis_strategy_v1/core/strategies/components/event_logger.py:_publish_event()`
- **Position Snapshots**: `backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py:get_snapshot()`

---

## 🔄 **Backtest vs Live Mode Workflows**

### **Backtest Mode Workflow**

```mermaid
graph TD
    A[Backtest Start] --> B[Load Historical Data]
    B --> C[Initialize Engine]
    C --> D[Set Date Range]
    D --> E[Loop Through Timestamps]
    E --> F[Get Market Data Snapshot]
    F --> G[Process Timestep]
    G --> H[Execute Strategy Decision]
    H --> I[Log Events]
    I --> J{More Timestamps?}
    J -->|Yes| E
    J -->|No| K[Calculate Final Results]
    K --> L[Return Backtest Results]
    
    style A fill:#e3f2fd
    style B fill:#f3e5f5
    style L fill:#e8f5e8
```

### **Live Mode Workflow**

```mermaid
graph TD
    A[Live Start] --> B[Initialize LiveDataProvider]
    B --> C[Connect to APIs]
    C --> D[Initialize Engine]
    D --> E[Start Event Loop]
    E --> F[Get Current Market Data]
    F --> G[Process Current Timestep]
    G --> H[Execute Strategy Decision]
    H --> I[Log Events]
    I --> J[Wait for Next Cycle]
    J --> K{Still Running?}
    K -->|Yes| F
    K -->|No| L[Stop Execution]
    
    style A fill:#e3f2fd
    style B fill:#f3e5f5
    style E fill:#e8f5e8
    style L fill:#ffebee
```

### **Code References**
- **Backtest**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py:run_backtest()`
- **Live**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py:run_live()`
- **Timestep Processing**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py:_process_timestep()`

---

## 🎯 **Strategy Mode Workflows**

### **Pure Lending Mode**

```mermaid
graph TD
    A[Pure Lending Start] --> B[Supply USDT to AAVE]
    B --> C[Monitor AAVE Position]
    C --> D[Calculate Supply Interest]
    D --> E[Log Interest Events]
    E --> F[Update P&L]
    F --> G[Continue Monitoring]
    
    style A fill:#e3f2fd
    style B fill:#e8f5e8
    style G fill:#e8f5e8
```

### **BTC Basis Mode**

```mermaid
graph TD
    A[BTC Basis Start] --> B[Buy BTC Spot]
    B --> C[Short BTC Perp]
    C --> D[Monitor Funding Rates]
    D --> E[Calculate Basis P&L]
    E --> F[Rebalance if Needed]
    F --> G[Log Trading Events]
    G --> H[Continue Monitoring]
    
    style A fill:#e3f2fd
    style B fill:#e8f5e8
    style C fill:#e8f5e8
    style H fill:#e8f5e8
```

### **ETH Leveraged Mode**

```mermaid
graph TD
    A[ETH Leveraged Start] --> B[Stake ETH to LST]
    B --> C[Supply LST to AAVE]
    C --> D[Borrow ETH from AAVE]
    D --> E[Stake Borrowed ETH]
    E --> F[Repeat Leverage Loop]
    F --> G[Monitor LTV]
    G --> H{Need Rebalance?}
    H -->|Yes| I[Adjust Leverage]
    H -->|No| J[Continue Monitoring]
    I --> J
    
    style A fill:#e3f2fd
    style B fill:#e8f5e8
    style C fill:#e8f5e8
    style D fill:#e8f5e8
    style E fill:#e8f5e8
    style J fill:#e8f5e8
```

### **USDT Market Neutral Mode**

```mermaid
graph TD
    A[USDT Market Neutral Start] --> B[Buy ETH Spot]
    B --> C[Stake ETH to LST]
    C --> D[Supply LST to AAVE]
    D --> E[Borrow ETH from AAVE]
    E --> F[Short ETH Perps]
    F --> G[Monitor Delta Exposure]
    G --> H{Delta Neutral?}
    H -->|No| I[Rebalance Hedge]
    H -->|Yes| J[Continue Monitoring]
    I --> J
    
    style A fill:#e3f2fd
    style B fill:#e8f5e8
    style C fill:#e8f5e8
    style D fill:#e8f5e8
    style E fill:#e8f5e8
    style F fill:#e8f5e8
    style J fill:#e8f5e8
```

### **Code References**
- **Strategy Manager**: `backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py:make_strategy_decision()`
- **Mode Detection**: `backend/src/basis_strategy_v1/infrastructure/config/settings.py:detect_strategy_mode()`
- **Mode Configs**: `configs/modes/*.yaml`

---

## 🔧 **Error Handling & Monitoring Workflow**

### **Error Handling Chain**

```mermaid
graph TD
    A[Error Occurs] --> B[Log Error with Code]
    B --> C{Error Type?}
    C -->|Config Error| D[Fail Fast]
    C -->|Data Error| E[Retry with Fallback]
    C -->|Execution Error| F[Rollback Transaction]
    C -->|Risk Error| G[Emergency Stop]
    
    D --> H[Return Error to User]
    E --> I[Continue with Available Data]
    F --> J[Log Rollback Event]
    G --> K[Close All Positions]
    
    style A fill:#ffebee
    style D fill:#ffebee
    style H fill:#ffebee
    style I fill:#e8f5e8
    style J fill:#fff3e0
    style K fill:#ffebee
```

### **Code References**
- **Error Codes**: `backend/src/basis_strategy_v1/core/strategies/components/event_logger.py:ERROR_CODES`
- **Config Validation**: `backend/src/basis_strategy_v1/infrastructure/config/config_validator.py`
- **Risk Monitoring**: `backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py:assess_risk()`

---

## 📊 **Performance Monitoring Workflow**

### **Real-time Monitoring**

```mermaid
graph TD
    A[System Running] --> B[Health Checker]
    B --> C[Monitor Components]
    C --> D[Check Data Freshness]
    D --> E[Monitor Risk Metrics]
    E --> F[Check Execution Status]
    F --> G[Update Dashboard]
    G --> H[Alert if Issues]
    H --> I[Continue Monitoring]
    
    style A fill:#e3f2fd
    style B fill:#f1f8e9
    style G fill:#e8f5e8
    style H fill:#fff3e0
```

### **Code References**
- **Health Checker**: `backend/src/basis_strategy_v1/infrastructure/config/health_check.py`
- **Monitoring**: `backend/src/basis_strategy_v1/infrastructure/monitoring/health.py`
- **Metrics**: `backend/src/basis_strategy_v1/infrastructure/monitoring/metrics.py`

---

## 🎯 **Key Workflow Patterns**

### **1. Configuration → Data → Engine → Execution**
```
Config Loading → Data Provider → Event Engine → Execution Interfaces → Event Logging
```

### **2. Event Chain Pattern**
```
Position → Exposure → Risk → P&L → Strategy → Execution → Logging
```

### **3. Mode Switching Pattern**
```
Same Interface → Different Implementation → Same Result Format
```

### **4. Cross-Venue Transfer Pattern**
```
Plan → Validate → Execute Steps → Wait → Complete → Log
```

---

## 🚀 **Getting Started with Workflows**

### **1. Understanding the System**
1. Read this workflow guide
2. Review component specifications
3. Examine configuration files
4. Run infrastructure tests

### **2. Running a Backtest**
1. Configure strategy mode
2. Set date range
3. Initialize engine
4. Run backtest
5. Analyze results

### **3. Setting Up Live Trading**
1. Configure API keys
2. Set execution mode to 'live'
3. Initialize live data provider
4. Start event loop
5. Monitor execution

### **4. Debugging Issues**
1. Check configuration validation
2. Verify data availability
3. Review event logs
4. Check component health
5. Monitor error codes

---

## 🔍 **Implementation vs Documentation Discrepancies**

### **Current Implementation Status**

**✅ Implemented and Working**:
- All 9 core components exist and function
- YAML-based configuration system
- Event-driven architecture with synchronous communication
- Execution interfaces (not separate manager classes)
- Event Logger with Redis support for live mode
- Error code system
- Frontend wizard components
- Transfer manager for cross-venue operations

**❌ Documented but Not Implemented**:
- JSON configuration hierarchy (`default.json`, `{environment}.json`, `local.json`)
- Redis pub/sub communication between all components (only Event Logger uses Redis)
- Separate execution manager classes (implemented as interfaces instead)

**🔄 Partially Implemented**:
- Configuration loading attempts JSON first, falls back to YAML successfully
- Redis messaging standard only applies to Event Logger, not all components

### **Future Improvements to Match Documentation**

1. **Complete JSON Configuration System**:
   - Create `configs/default.json` with base configuration
   - Create environment-specific JSON files (`dev.json`, `staging.json`, `prod.json`)
   - Create `configs/local.json` for local overrides
   - Update configuration loader to use JSON hierarchy as documented

2. **Implement Full Redis Messaging**:
   - Add Redis pub/sub to all components for live mode
   - Implement channel naming conventions as documented
   - Add Redis state caching for all components
   - Maintain synchronous fallback for backtest mode

3. **Separate Execution Manager Classes**:
   - Create separate `CEXExecutionManager` and `OnChainExecutionManager` classes
   - Keep execution interfaces for abstraction
   - Update Strategy Manager to use manager classes instead of interfaces

**Status**: Workflow guide updated to reflect actual implementation! Core system working with documented discrepancies noted. ✅

*Last Updated: October 6, 2025*
