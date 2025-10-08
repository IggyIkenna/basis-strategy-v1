# Unified Reference Guide 📚

**Purpose**: Complete reference for configuration, API, events, components, and error handling  
**Status**: Consolidated reference with cross-links to detailed specs  
**Updated**: October 3, 2025

---

## 📚 **Cross-References**

**For detailed implementation**, see:
- **Component data structures** → [specs/](specs/) (individual component specs)
- **AAVE mechanics** → [specs/02_EXPOSURE_MONITOR.md](specs/02_EXPOSURE_MONITOR.md)
- **Execution logic** → [specs/06_CEX_EXECUTION_MANAGER.md](specs/06_CEX_EXECUTION_MANAGER.md), [specs/07_ONCHAIN_EXECUTION_MANAGER.md](specs/07_ONCHAIN_EXECUTION_MANAGER.md)
- **Event structure** → [specs/08_EVENT_LOGGER.md](specs/08_EVENT_LOGGER.md)
- **Error codes** → [specs/11_ERROR_LOGGING_STANDARD.md](specs/11_ERROR_LOGGING_STANDARD.md)

---

## 📋 **Table of Contents**

1. [Configuration Reference](#configuration-reference)
2. [API Reference](#api-reference)
3. [Event Reference](#event-reference)
4. [Component Domain Data Reference](#component-domain-data-reference)
5. [Error Logging Reference](#error-logging-reference)

---

## 📋 **Configuration Reference**

### **Configuration Workflow**

**Important**: Configuration changes require a full system restart. See `docs/CONFIG_WORKFLOW.md` for complete details.

**Configuration Loading Priority**:
1. Environment Variables (BASIS_*) - Highest Priority
2. YAML Configuration Files (configs/modes/, venues/, share_classes/) - Strategy and venue configs
3. JSON Hierarchy (configs/default.json, {environment}.json, local.json) - **DOCUMENTED BUT NOT IMPLEMENTED**

**Note**: Scenario-specific configs (configs/scenarios/*/*.yaml) have been removed as part of the configuration cleanup. All scenario-specific parameters are now handled through mode configs and request overrides.

**Configuration Infrastructure**:
- **Centralized Loading**: All config loaded from `backend/src/basis_strategy_v1/infrastructure/config/`
- **BacktestService Integration**: Uses config infrastructure instead of hardcoded config creation
- **Component Access**: Components receive validated config dicts from infrastructure layer
- **Fail-Fast Validation**: Components use direct config access (no .get() patterns)
- **Health Monitoring**: Components register with config health checker

**Configuration Validation**:
- All configuration is validated at startup
- Components must register and mark themselves healthy
- System fails fast on bad configuration
- See `backend/src/basis_strategy_v1/infrastructure/config/` for validation logic

### **Configuration Structure**

The configuration system uses a hierarchical structure with clear separation of concerns:

```
configs/
├── modes/           # Strategy-specific parameters (6 modes)
├── share_classes/   # Share class definitions (2 classes)
├── venues/          # Venue-specific configurations (8 venues)
├── default.json     # Base configuration
└── local.json       # Local development overrides
```

**Separation of Concerns**:

- **`modes/`**: Strategy-specific parameters (target_apy, max_drawdown, risk params, execution config, data requirements)
  - `btc_basis.yaml` - BTC basis trading with hedging
  - `eth_leveraged.yaml` - ETH leveraged staking with LST rewards
  - `eth_staking_only.yaml` - ETH staking without leverage
  - `pure_lending.yaml` - Simple USDT lending to AAVE
  - `usdt_market_neutral.yaml` - Full leveraged restaking with hedging
  - `usdt_market_neutral_no_leverage.yaml` - Market neutral without leverage
- **`share_classes/`**: Share class definition (supported strategies, currency config, risk profile)
  - `usdt_stable.yaml` - USDT-denominated share class
  - `eth_directional.yaml` - ETH-denominated share class
- **`venues/`**: Venue-specific parameters (API configs, trading parameters, contract addresses)
  - `aave_v3.yaml`, `alchemy.yaml`, `binance.yaml`, `bybit.yaml`, `etherfi.yaml`, `lido.yaml`, `morpho.yaml`, `okx.yaml`

**Example Complete Configuration**:
```yaml
# Merged from: default.json + modes/usdt_market_neutral.yaml + venues/binance.yaml + share_classes/usdt_stable.yaml

# From modes/usdt_market_neutral.yaml (strategy parameters)
mode: "usdt_market_neutral"
description: "USDT market neutral strategy - leveraged staking with hedging"
lending_enabled: true
staking_enabled: true
basis_trade_enabled: true
leverage_enabled: true
share_class: "USDT"
asset: "ETH"
lst_type: "weeth"
rewards_mode: "base_eigen_seasonal"
target_apy: 0.15
max_drawdown: 0.04
use_flash_loan: true
unwind_mode: "fast"
hedge_venues: ["binance", "bybit", "okx"]
hedge_allocation:
  binance: 0.4
  bybit: 0.3
  okx: 0.3
margin_ratio_target: 1.0
max_stake_spread_move: 0.02215
max_leverage_loops: 23
min_loop_position_usd: 10000.0
capital_allocation:
  spot_capital: 0.5
  perp_capital: 0.5
  max_position_size: 0.95
data_requirements:
  - "eth_prices"
  - "weeth_prices"
  - "aave_lending_rates"
  - "staking_rewards"
  - "eigen_rewards"
  - "ethfi_rewards"
  - "funding_rates"
  - "gas_costs"
  - "execution_costs"
  - "aave_risk_params"
  - "lst_market_prices"
monitoring:
  health_check_interval: 60
  position_check_interval: 300
  risk_check_interval: 60
  alert_thresholds:
    drawdown_warning: 0.01
    drawdown_critical: 0.015

# From share_classes/usdt_stable.yaml (share class definition)
base_currency: "USDT"
quote_currency: "USDT"
decimal_places: 6
risk_level: "low_to_medium"
market_neutral: true
allows_hedging: true
supported_strategies:
  - "pure_lending"
  - "btc_basis"
  - "usdt_market_neutral"
  - "usdt_market_neutral_no_leverage"

# From venues/binance.yaml (venue-specific parameters)
venue: "binance"
type: "cex"
description: "Binance centralized exchange configuration"
api_endpoints:
  spot: "https://api.binance.com"
  futures: "https://fapi.binance.com"
  testnet_spot: "https://testnet.binance.vision"
  testnet_futures: "https://testnet.binancefuture.com"
trading_fees:
  spot_maker: 0.001
  spot_taker: 0.001
  futures_maker: 0.0002
  futures_taker: 0.0004
max_position_size_usd: 1000000
min_order_size_usd: 10
max_leverage: 125
supported_assets:
  spot: ["BTC", "ETH", "USDT", "USDC"]
  futures: ["BTCUSDT", "ETHUSDT"]
rate_limits:
  requests_per_minute: 1200
  orders_per_second: 10
```

### **Mode Reference**

| Mode | Share Class | Description | Key Features |
|------|-------------|-------------|--------------|
| `pure_lending` | USDT | Supply USDT to AAVE only | Simple lending, no leverage, no hedging |
| `btc_basis` | USDT | Long BTC spot + short BTC perp | Basis trading with hedging across CEXs |
| `eth_leveraged` | ETH | Leveraged staking (no hedging) | AAVE leverage loops, directional ETH exposure |
| `eth_staking_only` | ETH | Conservative staking only | No leverage, no hedging, just staking |
| `usdt_market_neutral` | USDT | Full leveraged restaking + hedge | AAVE leverage + CEX hedging, market neutral |
| `usdt_market_neutral_no_leverage` | USDT | Market neutral without leverage | Staking + hedging, no AAVE leverage |

### **LST Type Reference**

| Value | Token | Protocol | Rewards |
|-------|-------|----------|---------|
| `weeth` | weETH | EtherFi | Base + optional EIGEN/ETHFI |
| `wsteth` | wstETH | Lido | Base only (no restaking) |

### **Venue Reference**

| Venue | Type | Purpose | Configuration |
|-------|------|---------|---------------|
| `binance` | CEX | Spot/Perp trading, hedging | API keys, trading params, rate limits |
| `bybit` | CEX | Spot/Perp trading, hedging | API keys, trading params, rate limits |
| `okx` | CEX | Spot/Perp trading, hedging | API keys, trading params, rate limits |
| `aave_v3` | DeFi | Lending/borrowing | Pool addresses, eMode params, supported assets |
| `etherfi` | DeFi | ETH staking | Protocol addresses, rewards, staking params |
| `lido` | DeFi | ETH staking | Protocol addresses, rewards, staking params |
| `morpho` | DeFi | Flash loans | Protocol addresses, fees, supported assets |
| `alchemy` | Infrastructure | RPC provider | RPC endpoints, gas settings, enhanced features |

### **Rewards Mode Reference**

| Value | Includes | Data Requirements |
|-------|----------|------------------|
| `base_only` | Oracle price drift only | ✅ Any period (most conservative) |
| `base_eigen` | Oracle + EIGEN weekly | ⚠️ Requires EIGEN distribution data |
| `base_eigen_seasonal` | Oracle + EIGEN + ETHFI airdrops | ⚠️ Requires EIGEN + ETHFI distribution data |

**Explanation**: All strategies can use any rewards mode. The limitation is data availability, not strategy type. If you have EIGEN/ETHFI data for your backtest period, you can use `base_eigen` or `base_eigen_seasonal` with any strategy. The `base_only` mode is simply the most conservative option that works with any data period.

### **Validation Rules**

**Fail-Fast** (No Silent Defaults!):
```python
# ❌ WRONG (silent failure on typo)
lst_type = config.get('lst_type', 'weeth')  # Typo: 'lts_type' → uses 'weeth' silently

# ✅ CORRECT (explicit failure)
lst_type = config['lst_type']  # Typo → KeyError with message
```

**Mode-Specific Validation**:
```python
# USDT + Staking → Requires hedging
if (share_class == 'USDT' and 
    staking_enabled and 
    not basis_trade_enabled):
    raise ValueError("USDT staking requires hedging (set basis_trade_enabled=true)")

# ETH Share Class → No hedging
if share_class == 'ETH' and basis_trade_enabled:
    logger.warning("Auto-disabling hedging for ETH share class")
    basis_trade_enabled = False

# Rewards mode validation (data availability check)
if rewards_mode in ['base_eigen', 'base_eigen_seasonal']:
    # Check if required data is available for the backtest period
    if not data_provider.has_eigen_data(start_date, end_date):
        raise ValueError(f"Rewards mode '{rewards_mode}' requires EIGEN distribution data for period {start_date} to {end_date}")
    if rewards_mode == 'base_eigen_seasonal' and not data_provider.has_ethfi_data(start_date, end_date):
        raise ValueError(f"Rewards mode '{rewards_mode}' requires ETHFI distribution data for period {start_date} to {end_date}")
```

### **Environment Variables**

```bash
# Data
BASIS_DATA__DATA_DIR=./data

# Components (NEW)
BASIS_COMPONENTS__EXECUTION_MODE=backtest
BASIS_COMPONENTS__INCLUDE_BALANCE_SNAPSHOTS=true

# Redis (NEW - required!)
BASIS_REDIS__ENABLED=true
BASIS_REDIS__URL=redis://localhost:6379/0
```

---

## 📡 **API Reference**

**Base URL**: `http://localhost:8001` (dev) or `https://defi-project.odum-research.com` (prod)  
**API Docs**: `/docs` (Swagger UI)

### **POST /api/v1/backtest/**

Submit new backtest request.

**Request**:
```json
{
  "strategy_name": "usdt_market_neutral",
  "start_date": "2024-05-12T00:00:00Z",
  "end_date": "2025-09-18T00:00:00Z",
  "initial_capital": 100000,
  "share_class": "USDT",
  "config_overrides": {
    "mode": "usdt_market_neutral",
    "lst_type": "weeth",
    "rewards_mode": "base_only",
    "use_flash_loan": true,
    "hedge_venues": ["binance", "bybit", "okx"],
    "hedge_allocation": {"binance": 0.33, "bybit": 0.33, "okx": 0.34}
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "request_id": "abc123-def456",
    "status": "pending",
    "strategy_name": "usdt_market_neutral",
    "estimated_time_seconds": 30
  }
}
```

### **GET /api/v1/results/{request_id}**

Get complete backtest results (ENHANCED with component data).

**Response**:
```json
{
  "success": true,
  "data": {
    "request_id": "abc123",
    "mode": "usdt_market_neutral",
    
    "summary": {
      "cumulative_pnl_usd": 1238.83,
      "apy_pct": 8.45,
      "max_drawdown_pct": -2.34,
      
      "balance_based_pnl": 1238.83,
      "attribution_pnl": 1349.84,
      
      "reconciliation": {
        "difference": -111.39,
        "unexplained_pnl": -111.39,
        "tolerance": 166.67,
        "passed": true
      },
      
      "final_health_factor": 1.067,
      "min_margin_ratio": 0.883,
      "avg_net_delta_pct": 0.15
    },
    
    "hourly_pnl": [
      {
        "timestamp": "2024-05-12T00:00:00Z",
        "net_pnl_usd": -246.05,
        "balance_based_pnl": -246.05,
        "attribution_pnl": -246.05,
        "supply_pnl": 0,
        "staking_yield_oracle": 0,
        "staking_yield_rewards": 0,
        "borrow_cost": 0,
        "funding_pnl": 0,
        "delta_pnl": 0,
        "transaction_costs": -246.05,
        "health_factor": 1.045,
        "net_delta_eth": -0.12,
        "erc20_wallet_net_delta_eth": 3.104,
        "cex_wallet_net_delta_eth": -3.224,
        "token_equity_eth": 48.92,
        "binance_margin_ratio": 0.99
      }
    ],
    
    "event_log": [
      {
        "timestamp": "2024-05-12T00:00:00Z",
        "order": 1,
        "event_type": "GAS_FEE_PAID",
        "venue": "ETHEREUM",
        "token": "ETH",
        "amount": 0.0035,
        "gas_units": 100000,
        "gas_price_gwei": 12.5,
        "wallet_balance_after": {...}
      }
    ],
    
    "plots": {
      "cumulative_pnl": "<html>...</html>",
      "delta_neutrality": "<html>...</html>",
      "margin_ratios": "<html>...</html>",
      "balance_sheet": "<html>...</html>"
    }
  }
}
```

### **GET /health/detailed**

Detailed component health (NEW).

**Response**:
```json
{
  "status": "healthy",
  "components": {
    "position_monitor": "ready",
    "exposure_monitor": "ready",
    "risk_monitor": "ready",
    "pnl_calculator": "ready",
    "strategy_manager": "ready",
    "cex_execution_manager": "ready",
    "onchain_execution_manager": "ready",
    "event_logger": "ready",
    "data_provider": "loaded",
    "redis": "connected"
  },
  "data_status": {
    "period": "2024-01-01 to 2025-09-18",
    "modes_supported": ["pure_lending", "btc_basis", "eth_leveraged", "usdt_market_neutral"]
  }
}
```

---

## 📝 **Event Reference**

### **Event Structure**

```python
{
    # Timing
    'timestamp': pd.Timestamp,     # Trigger time (on the hour in backtest)
    'order': int,                  # Global sequence (1, 2, 3...)
    'status': str,                 # 'completed' (backtest), 'pending'/'confirmed' (live)
    
    # Event identification
    'event_type': str,             # 'GAS_FEE_PAID', 'STAKE_DEPOSIT', etc.
    'event_id': Optional[str],     # For live correlation (None in backtest)
    
    # Venue and asset
    'venue': str,                  # 'ETHEREUM', 'AAVE', 'ETHERFI', 'BINANCE', etc.
    'token': str,                  # 'ETH', 'USDT', 'weETH', etc.
    'amount': float,               # Primary amount
    
    # Balance snapshots (optional, for audit)
    'wallet_balance_after': Optional[Dict],      # Full Position Monitor output after event
    'cex_balance_after': Optional[Dict],         # CEX balances after event (subset of wallet_balance_after)
    'aave_position_after': Optional[Dict],       # AAVE derived positions (subset of wallet_balance_after)
    
    # Cost tracking
    'gas_cost_eth': Optional[float],
    'gas_cost_usd': Optional[float],
    'gas_units': Optional[int],
    'gas_price_gwei': Optional[float],
    'execution_cost_usd': Optional[float],
    'execution_cost_bps': Optional[float],
    
    # Transaction details
    'purpose': str,                               # Human-readable description
    'transaction_type': str,                      # Category
    'related_events': Optional[List[int]],        # Order numbers of related events
    'iteration': Optional[int],                   # For loops (1, 2, 3...)
    'parent_event': Optional[int],                # For atomic bundles
    
    # Live trading fields (None in backtest)
    'trigger_timestamp': Optional[pd.Timestamp],  # When decision made
    'completion_timestamp': Optional[pd.Timestamp], # When tx confirmed
    'tx_hash': Optional[str],
    'confirmation_blocks': Optional[int],
    
    # Additional context (mode-specific)
    **extra_data
}
```

### **Event Types**

#### **On-Chain Events**:
- `GAS_FEE_PAID` - Gas payment
- `STAKE_DEPOSIT` - ETH → LST
- `STAKE_WITHDRAWAL` - LST → ETH
- `COLLATERAL_SUPPLIED` - Token → AAVE
- `COLLATERAL_WITHDRAWN` - AAVE → Token
- `LOAN_CREATED` - Borrow from AAVE
- `LOAN_REPAID` - Repay to AAVE
- `VENUE_TRANSFER` - Wallet ↔ CEX

#### **CEX Events**:
- `SPOT_TRADE` - CEX spot trade
- `TRADE_EXECUTED` - Perp trade
- `FUNDING_PAYMENT` - Funding rate payment

#### **Complex Events**:
- `ATOMIC_TRANSACTION` - Wrapper for flash loan bundle
- `FLASH_BORROW` - Flash loan initiation
- `FLASH_REPAID` - Flash loan repayment
- `LEVERAGE_LOOP_ITERATION` - Sequential loop step

#### **Monitoring Events**:
- `HOURLY_RECONCILIATION` - Balance sync
- `PRICE_UPDATE` - Market data update
- `RISK_ALERT` - Risk threshold breached
- `REBALANCE_EXECUTED` - Rebalancing completed

### **Event Ordering**

**FIFO Queue**:
```python
# Simple FIFO queue
# Same timestamp: Use global order (1, 2, 3...)
# Different timestamps: Chronological

events = sorted(events, key=lambda e: (e['timestamp'], e['order']))
```

---

## 🏗️ **Component Domain Data Reference**

### **Component Data Flow Architecture**

**Data Flow Pattern**:
```python
# BacktestService → EventDrivenStrategyEngine
config = self._create_config(request)  # Uses config infrastructure
strategy_engine = EventDrivenStrategyEngine(config)
result = await strategy_engine.run_backtest(
    start_date=request.start_date.isoformat(),
    end_date=request.end_date.isoformat(),
    initial_capital=request.initial_capital  # Pass initial capital
)

# EventDrivenStrategyEngine Data Loading
data = await self.data_provider._load_data_for_mode()  # Correct method name

# Component Data Access Pattern
market_data = data_row.to_dict()  # Current market data for timestamp

# Pass to components that need market data:
exposure = await self.exposure_monitor.calculate_exposure(
    timestamp=timestamp,
    position_snapshot=positions,
    market_data=market_data  # Pass market data
)

risk = await self.risk_monitor.assess_risk(
    exposure=exposure,
    market_data=market_data  # Pass market data for risk calculations
)

# Strategy decisions use exposure + risk + config (no direct market data needed)
decision = await self.strategy_manager.make_strategy_decision(
    exposure=exposure,
    risk=risk,
    config=self.config
)

# PnL calculation only needs exposure (saves own previous state)
pnl = await self.pnl_calculator.calculate_pnl(
    current_exposure=exposure,
    previous_exposure=previous_exposure,
    timestamp=timestamp
)
```

**Config Infrastructure Integration**:
```python
# Backend components use config infrastructure
from ...infrastructure.config.config_loader import get_config_loader
from ...infrastructure.config.health_check import register_component

# Load config
config_loader = get_config_loader()
config = config_loader.get_complete_config(mode=mode)

# Register component for health monitoring
register_component('strategy_manager', ['data_provider', 'risk_monitor'])

# Use config (fail-fast, no .get() patterns)
lst_type = config['lst_type']  # Raises KeyError if missing
```

### **Component Data Requirements**

**DataProvider**: Loads all data in `_load_data_for_mode()`
- Market prices, AAVE rates, LST prices, gas costs, etc.

**PositionMonitor**: Gets initial capital + share class
- Sets USDT or ETH balance based on mode

**ExposureMonitor**: Gets market data for current timestamp
- Calculates current exposure using market prices

**RiskMonitor**: Gets market data for risk calculations
- AAVE risk params, oracle prices, margin calculations

**StrategyManager**: Uses exposure + risk + config
- No direct market data needed (decisions based on current state)

**PnLCalculator**: Uses exposure only
- Saves own previous P&L state, no external data needed

**Execution Managers**: Get market data for pricing
- Check execution against current market prices

### **Position Monitor Data**

**Input: Balance Changes**:
```python
{
    'timestamp': pd.Timestamp('2024-05-12 00:00:00', tz='UTC'),
    'trigger': 'GAS_FEE_PAID',
    'token_changes': [
        {
            'venue': 'WALLET',  # or 'BINANCE', 'BYBIT', 'OKX'
            'token': 'ETH',
            'delta': -0.0035,   # Change (negative = decrease)
            'new_balance': 49.9965,  # New balance after change
            'reason': 'GAS_FEE_PAID'
        }
    ],
    'derivative_changes': [
        {
            'venue': 'binance',
            'instrument': 'ETHUSDT-PERP',
            'action': 'OPEN',  # or 'CLOSE', 'ADJUST'
            'data': {
                'size': -8.562,
                'entry_price': 2920.00,
                'notional_usd': 25000.0
            }
        }
    ]
}
```

**Output: Position Snapshot**:
```python
{
    'timestamp': pd.Timestamp('2024-05-12 00:00:00', tz='UTC'),
    'wallet': {
        'ETH': 49.9965,
        'USDT': 0.0,
        'weETH': 0.0,
        'aWeETH': 95.24,              # CONSTANT scaled balance
        'variableDebtWETH': 88.70     # CONSTANT scaled balance
    },
    'cex_accounts': {
        'binance': {
            'USDT': 24992.50,
            'ETH_spot': 0.0,
            'BTC_spot': 0.0
        }
    },
    'perp_positions': {
        'binance': {
            'ETHUSDT-PERP': {
                'size': -8.562,
                'entry_price': 2920.00,
                'entry_timestamp': '2024-05-12 00:00:00',
                'notional_usd': 25000.0
            }
        }
    }
}
```

### **Exposure Monitor Data**

**Input Parameters**:
```python
# Method signature
def calculate_exposure(
    self, 
    timestamp: pd.Timestamp, 
    position_snapshot: Dict = None, 
    market_data: Dict = None
) -> Dict:

# Market Data Input:
{
    'timestamp': timestamp,
    'eth_usd_price': 3305.20,
    'weeth_liquidity_index': 1.10,
    'weth_borrow_index': 1.08,
    'weeth_eth_oracle': 1.0256,
    'binance_eth_perp_mark': 3305.20,
    'bybit_eth_perp_mark': 3306.15,
    'okx_eth_perp_mark': 3304.80
}

# Position Snapshot Input (from PositionMonitor):
{
    'wallet': {
        'ETH': 49.9965,
        'USDT': 0.0,
        'weETH': 0.0,
        'aWeETH': 95.24,              # CONSTANT scaled balance
        'variableDebtWETH': 88.70     # CONSTANT scaled balance
    },
    'cex_accounts': {...},
    'perp_positions': {...}
}
```

**Output: Exposure Data**:
```python
{
    'timestamp': timestamp,
    'share_class': 'USDT',
    
    'exposures': {
        'aWeETH': {
            'wallet_balance': 95.24,        # Raw wallet balance (scaled)
            'underlying_native': 104.76,    # Underlying weETH (scaled × index)
            'exposure_eth': 107.44,         # ETH equivalent (× oracle)
            'exposure_usd': 355092.00,      # USD equivalent (× ETH price)
            'direction': 'LONG'             # Long ETH exposure
        }
    },
    
    'total_long_eth': 107.44,     # Sum of all long ETH
    'total_short_eth': 112.558,   # Sum of all short ETH
    'net_delta_eth': -5.118,      # Total: Long - Short
    'net_delta_pct': -3.01,       # vs initial position
    
    'total_value_usd': 99753.45,
    'total_value_eth': 30.18,
    'share_class_value': 99753.45
}
```

### **Risk Monitor Data**

**Input Parameters**:
```python
# Method signature
async def assess_risk(
    self, 
    exposure: Dict, 
    market_data: Dict = None
) -> Dict:

# Exposure Input (from ExposureMonitor):
{
    'exposures': {...},
    'total_long_eth': 107.44,
    'total_short_eth': 112.558,
    'net_delta_eth': -5.118,
    'total_value_usd': 99753.45
}

# Market Data Input (for risk calculations):
{
    'eth_usd_price': 3305.20,
    'weeth_eth_oracle': 1.0256,
    'binance_eth_perp_mark': 3305.20,
    'bybit_eth_perp_mark': 3306.15
}
```

**Output: Risk Metrics**:
```python
{
    'timestamp': timestamp,
    
    'aave': {
        'ltv': 0.892,                    # Current LTV (debt / collateral)
        'health_factor': 1.067,          # (LT × collateral) / debt
        'collateral_value_eth': 107.44,
        'debt_value_eth': 95.796,
        'safe_ltv_threshold': 0.91,      # From config
        'liquidation_threshold': 0.95,   # LTV where liquidation happens
        'status': 'SAFE',                # 'SAFE', 'WARNING', 'CRITICAL'
        'warning': False,
        'critical': False
    },
    
    'cex_margin': {
        'binance': {
            'balance_usdt': 24992.50,
            'exposure_usdt': 28299.47,
            'margin_ratio': 0.883,          # balance / exposure
            'required_margin': 4244.92,     # 15% initial margin
            'free_margin': 20747.58,        # balance - required
            'status': 'SAFE',
            'warning': False,
            'critical': False
        }
    },
    
    'delta': {
        'net_delta_eth': -5.118,
        'target_delta_eth': 0.0,
        'delta_drift_eth': -5.118,
        'delta_drift_pct': -3.01,
        'drift_threshold_pct': 5.0,
        'status': 'SAFE',
        'warning': False,
        'critical': False
    },
    
    'overall_status': 'SAFE',
    'any_warnings': False,
    'any_critical_alerts': False,
    'alerts': []
}
```

### **P&L Calculator Data**

**Input Parameters**:
```python
# Method signature
async def calculate_pnl(
    self,
    current_exposure: Dict,
    previous_exposure: Optional[Dict] = None,
    timestamp: pd.Timestamp = None,
    period_start: pd.Timestamp = None
) -> Dict:

# Current Exposure Input (from ExposureMonitor):
{
    'exposures': {...},
    'total_long_eth': 107.44,
    'total_short_eth': 112.558,
    'net_delta_eth': -5.118,
    'total_value_usd': 99753.45,
    'total_value_eth': 30.18
}

# Previous Exposure Input (saved internally):
{
    'total_value_usd': 99507.12,
    'total_value_eth': 29.95,
    'exposures': {...}
}
```

**Output: P&L Data**:
```python
{
    'timestamp': timestamp,
    'share_class': 'USDT',
    
    'balance_based': {
        'total_value_current': 99753.45,
        'total_value_previous': 99507.12,
        'pnl_hourly': 246.33,
        'pnl_cumulative': 1238.45,
        'pnl_pct': 1.238
    },
    
    'attribution': {
        'supply_pnl': 12.34,
        'staking_pnl': 0.0,
        'price_change_pnl': 8.56,
        'borrow_cost': -5.23,
        'funding_pnl': 2.15,
        'delta_pnl': 0.45,
        'transaction_costs': 0.0,
        'pnl_hourly': 18.27,
        
        'cumulative_supply_pnl': 543.21,
        'cumulative_staking_pnl': 0.0,
        'cumulative_price_change_pnl': 382.45,
        'cumulative_borrow_cost': -234.56,
        'cumulative_funding_pnl': 892.45,
        'cumulative_delta_pnl': 12.34,
        'cumulative_transaction_costs': -246.05,
        'pnl_cumulative': 1349.84
    },
    
    'reconciliation': {
        'balance_pnl': 1238.45,
        'attribution_pnl': 1349.84,
        'difference': -111.39,
        'unexplained_pnl': -111.39,
        'tolerance': 166.67,
        'passed': True,
        'diff_pct_of_capital': -0.111
    }
}
```

---

## 🔧 **Configuration Infrastructure Reference**

### **Config Infrastructure Components**

**ConfigLoader** (`config_loader.py`):
- **Purpose**: Centralized loading of all YAML and JSON configs
- **Features**: Caching, environment variable overrides, deep merging
- **Usage**: `get_config_loader().get_complete_config(mode=mode)`

**ConfigValidator** (`config_validator.py`):
- **Purpose**: Validates all configuration files at startup
- **Features**: Business logic validation, environment variable validation
- **Usage**: `validate_configuration()` returns ValidationResult

**HealthChecker** (`health_check.py`):
- **Purpose**: Component health monitoring and config version tracking
- **Features**: Dependency validation, system health status reporting
- **Usage**: `register_component()`, `mark_component_healthy()`

**Settings** (`settings.py`):
- **Purpose**: Legacy compatibility layer and environment-specific config loading
- **Features**: Cached settings access, environment variable processing
- **Usage**: `get_settings()`, `get_setting(key_path)`

**StrategyDiscovery** (`strategy_discovery.py`):
- **Purpose**: Strategy file discovery and validation
- **Features**: Mode-to-file mapping, strategy filtering
- **Usage**: `get_available_strategies()`, `load_strategy_config()`

### **BacktestService Integration**

**Before (Hardcoded)**:
```python
def _create_config(self, request: BacktestRequest) -> Dict[str, Any]:
    # Hardcoded config creation - NOT using config infrastructure
    config = {
        'share_class': request.share_class,
        'initial_capital': float(request.initial_capital),
        'strategy': {
            'mode': mode,
            'lending_enabled': True,
            # ... hardcoded values
        }
    }
    return config
```

**After (Infrastructure Integration)**:
```python
def _create_config(self, request: BacktestRequest) -> Dict[str, Any]:
    """Create configuration using existing config infrastructure."""
    from ...infrastructure.config.config_loader import get_config_loader
    
    # Get config loader
    config_loader = get_config_loader()
    
    # Load base config for the mode
    mode = self._map_strategy_to_mode(request.strategy_name)
    base_config = config_loader.get_complete_config(mode=mode)
    
    # Apply user overrides
    if request.config_overrides:
        base_config = self._deep_merge(base_config, request.config_overrides)
    
    # Add request-specific overrides
    base_config.update({
        'share_class': request.share_class,
        'initial_capital': float(request.initial_capital),
        'backtest': {
            'start_date': request.start_date.isoformat(),
            'end_date': request.end_date.isoformat(),
            'initial_capital': float(request.initial_capital)
        }
    })
    
    return base_config
```

### **Benefits of Config Infrastructure**
- Uses existing YAML configs from `configs/modes/*.yaml`
- Validates config via `config_validator.py`
- Supports environment variable overrides
- Consistent with rest of system
- Eliminates hardcoded config creation
- Health monitoring and validation

---

## ⚠️ **Error Logging Reference**

### **Error Code Structure**

```python
{
    'error_code': 'POSITION_MONITOR_001',
    'component': 'position_monitor',
    'severity': 'ERROR',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'message': 'Balance update failed: insufficient funds',
    'context': {
        'venue': 'binance',
        'token': 'USDT',
        'requested_delta': -1000.0,
        'current_balance': 500.0,
        'timestamp': '2024-05-12T00:00:00Z'
    },
    'stack_trace': '...',
    'recovery_action': 'REJECT_TRANSACTION'
}
```

### **Component Error Codes**

#### **Position Monitor (POSITION_MONITOR_XXX)**
- `POSITION_MONITOR_001` - Balance update failed: insufficient funds
- `POSITION_MONITOR_002` - Invalid venue specified
- `POSITION_MONITOR_003` - Token not supported
- `POSITION_MONITOR_004` - Balance reconciliation failed
- `POSITION_MONITOR_005` - Redis connection lost

#### **Exposure Monitor (EXPOSURE_MONITOR_XXX)**
- `EXPOSURE_MONITOR_001` - Market data missing for timestamp
- `EXPOSURE_MONITOR_002` - AAVE index calculation failed
- `EXPOSURE_MONITOR_003` - Oracle price unavailable
- `EXPOSURE_MONITOR_004` - Net delta calculation overflow

#### **Risk Monitor (RISK_MONITOR_XXX)**
- `RISK_MONITOR_001` - Health factor below 1.0 (liquidation risk)
- `RISK_MONITOR_002` - Margin ratio critical
- `RISK_MONITOR_003` - Delta drift exceeds threshold
- `RISK_MONITOR_004` - Risk calculation timeout

#### **P&L Calculator (PNL_CALCULATOR_XXX)**
- `PNL_CALCULATOR_001` - Reconciliation failed (tolerance exceeded)
- `PNL_CALCULATOR_002` - Attribution calculation error
- `PNL_CALCULATOR_003` - Balance-based P&L calculation failed
- `PNL_CALCULATOR_004` - Historical data missing

#### **Strategy Manager (STRATEGY_MANAGER_XXX)**
- `STRATEGY_MANAGER_001` - Mode detection failed
- `STRATEGY_MANAGER_002` - Desired position calculation error
- `STRATEGY_MANAGER_003` - Instruction generation failed
- `STRATEGY_MANAGER_004` - Rebalancing timeout

#### **CEX Execution Manager (CEX_EXEC_XXX)**
- `CEX_EXEC_001` - Trade execution failed
- `CEX_EXEC_002` - Insufficient margin for trade
- `CEX_EXEC_003` - Exchange API error
- `CEX_EXEC_004` - Price slippage exceeded limit

#### **OnChain Execution Manager (ONCHAIN_EXEC_XXX)**
- `ONCHAIN_EXEC_001` - Transaction failed
- `ONCHAIN_EXEC_002` - Gas estimation failed
- `ONCHAIN_EXEC_003` - Flash loan unavailable
- `ONCHAIN_EXEC_004` - AAVE operation failed

#### **Event Logger (EVENT_LOGGER_XXX)**
- `EVENT_LOGGER_001` - Event serialization failed
- `EVENT_LOGGER_002` - Redis publish failed
- `EVENT_LOGGER_003` - Event order conflict
- `EVENT_LOGGER_004` - Balance snapshot failed

#### **Data Provider (DATA_PROVIDER_XXX)**
- `DATA_PROVIDER_001` - Data file not found
- `DATA_PROVIDER_002` - Invalid timestamp format
- `DATA_PROVIDER_003` - Missing market data
- `DATA_PROVIDER_004` - Data validation failed

### **Error Severity Levels**

| Level | Description | Action |
|-------|-------------|--------|
| `DEBUG` | Detailed information for debugging | Log only |
| `INFO` | General information | Log only |
| `WARNING` | Something unexpected happened | Log + monitor |
| `ERROR` | Error occurred but system continues | Log + alert |
| `CRITICAL` | System cannot continue | Log + alert + stop |

### **Recovery Actions**

| Action | Description |
|--------|-------------|
| `REJECT_TRANSACTION` | Reject the current transaction |
| `RETRY_OPERATION` | Retry the failed operation |
| `FALLBACK_MODE` | Switch to fallback mode |
| `STOP_STRATEGY` | Stop the entire strategy |
| `ALERT_USER` | Send alert to user |
| `LOG_AND_CONTINUE` | Log error and continue |

### **Error Logging Format**

```python
import logging
import json
from datetime import datetime

class ComponentLogger:
    def __init__(self, component_name: str):
        self.component = component_name
        self.logger = logging.getLogger(f"basis_strategy_v1.{component_name}")
    
    def log_error(self, error_code: str, message: str, context: dict = None, 
                  severity: str = "ERROR", recovery_action: str = None):
        """Log structured error with context."""
        
        error_data = {
            'error_code': error_code,
            'component': self.component,
            'severity': severity,
            'message': message,
            'context': context or {},
            'timestamp': datetime.utcnow().isoformat(),
            'recovery_action': recovery_action
        }
        
        # Log to standard logger
        self.logger.error(json.dumps(error_data, indent=2))
        
        # Publish to Redis for monitoring
        if self.redis:
            await self.redis.publish('errors:logged', json.dumps(error_data))
```


### **Parameter Cleanup Summary**

**Removed Unused Parameters**:
- ❌ **stop_loss_pct, take_profit_pct**: Not implemented in backend, removed from all live scenarios
- ❌ **min_apy, max_volatility**: Not implemented in backend, removed from targets sections
- ❌ **max_drawdown in scenarios**: Moved to mode configs, removed duplication

**Kept Implemented Parameters**:
- ✅ **max_position_size**: Used for reserve fund management (keep X% reserves for withdrawals)
- ✅ **target_apy**: Actively used in backtest validation, can override in live scenarios
- ✅ **max_drawdown**: Defined in mode configs, used for risk validation

**Live Scenario Structure Now**:
```yaml
# Risk Management (reserve fund management only)
risk:
  max_position_size: 0.80  # Keep 20% reserves for withdrawals

# Performance Targets (optional live overrides)
targets:
  target_apy: 0.12  # Lower target for live (inherits from mode: 0.15)
```

**Benefits**:
- 🎯 **Only implemented features** - no placeholder parameters
- 🔧 **Clear purpose** - max_position_size for reserve management
- 📊 **No confusion** - removed unimplemented stop/take profit logic
- 🚀 **Cleaner configs** - focused on actual functionality

**Status**: Unified reference complete! ✅
