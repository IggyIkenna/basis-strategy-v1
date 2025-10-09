# Component Spec: Strategy Manager 🎯

**Component**: Strategy Manager  
**Responsibility**: Mode-specific orchestration and rebalancing decisions  
**Priority**: ⭐⭐⭐ CRITICAL (Brain of the system)  
**Backend File**: `backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py` ✅ **CORRECT**  
**Last Reviewed**: October 8, 2025  
**Status**: ✅ Aligned with canonical sources (.cursor/tasks/ + MODES.md)

---

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [CANONICAL_ARCHITECTURAL_PRINCIPLES.md](../CANONICAL_ARCHITECTURAL_PRINCIPLES.md) - Consolidated from all .cursor/tasks/
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Task Specifications**: `.cursor/tasks/` - Individual task specifications

---

## 🎯 **Purpose**

Mode-specific strategy brain that determines desired positions and generates rebalancing instructions.

**Key Principles**:
- **Unified interface**: Same methods for all position changes (initial, rebalancing, deposits, withdrawals)
- **Mode-specific logic**: Desired position different per mode (if/else on mode)
- **Actual vs Desired**: Compare current exposure to target, generate instructions to close gap
- **Instruction generation**: Creates tasks for execution managers

**Data Flow Integration**:
- **Input**: Receives `exposure`, `risk`, and `market_data` as parameters
- **Method**: `make_strategy_decision(exposure, risk, market_data, config)`
- **Market Data Integration**: Requires real-time market data for price-sensitive decisions
- **Data Sources**: 
  - Exposure from ExposureMonitor
  - Risk from RiskMonitor  
  - Market data from DataProvider (live mode) or historical data (backtest mode)
  - Config from engine

**Handles**:
- Initial position setup (t=0)
- Deposits/withdrawals (user adds/removes capital)
- Rebalancing (risk-triggered)
- Unwinding (exit strategy)

---

## 📊 **Data Structures**

### **Input**: Current State + Market Data

```python
{
    'exposure': {...},  # From Exposure Monitor
    'risk': {...},      # From Risk Monitor
    'market_data': {    # From Data Provider
        'eth_usd_price': 3300.50,
        'btc_usd_price': 45000.25,
        'aave_usdt_apy': 0.08,
        'perp_funding_rates': {
            'binance': {'ETHUSDT-PERP': 0.0001},
            'bybit': {'ETHUSDT-PERP': 0.0002},
            'okx': {'ETHUSDT-PERP': 0.0003}
        },
        'gas_price_gwei': 25.5,
        'timestamp': timestamp
    },
    'timestamp': timestamp,
    'mode': 'usdt_market_neutral'
}
```

### **Output**: Instructions

```python
{
    'timestamp': timestamp,
    'trigger': 'MARGIN_CRITICAL',  # What caused this
    'mode': 'usdt_market_neutral',
    
    # Desired vs Actual
    'current_state': {
        'aave_ltv': 0.89,
        'net_delta_eth': -5.12,
        'margin_ratio_binance': 0.18  # CRITICAL!
    },
    'desired_state': {
        'aave_ltv': 0.91,
        'net_delta_eth': 0.0,
        'margin_ratio_target': 1.0  # Back to 100%
    },
    'gaps': {
        'aave_ltv_gap': +0.02,      # Can increase
        'delta_gap_eth': +5.12,      # Need to short more
        'margin_deficit_usd': 9124.50  # Need to add margin
    },
    
    # Generated instructions
    'instructions': [
        {
            'priority': 1,
            'type': 'ADD_MARGIN_TO_CEX',
            'venue': 'binance',
            'amount_usd': 9124.50,
            'actions': [
                {
                    'step': 1,
                    'action': 'ATOMIC_DELEVERAGE_AAVE',
                    'executor': 'OnChainExecutionManager',
                    'params': {'amount_usd': 9124.50, 'mode': 'atomic'}
                },
                {
                    'step': 2,
                    'action': 'TRANSFER_ETH_TO_CEX',
                    'executor': 'OnChainExecutionManager',
                    'params': {'venue': 'binance', 'amount_eth': 2.76}
                },
                {
                    'step': 3,
                    'action': 'SELL_ETH_SPOT',
                    'executor': 'CEXExecutionManager',
                    'params': {'venue': 'binance', 'amount_eth': 2.76}
                },
                {
                    'step': 4,
                    'action': 'REDUCE_PERP_SHORT',
                    'executor': 'CEXExecutionManager',
                    'params': {'venue': 'binance', 'amount_eth': 2.76}
                }
            ]
        }
    ]
}
```

---

## 💻 **Core Functions**

```python
class StrategyManager:
    """Mode-specific strategy orchestration."""
    
    def __init__(self, mode, config, exposure_monitor, risk_monitor):
        self.mode = mode
        self.config = config
        self.exposure_monitor = exposure_monitor
        self.risk_monitor = risk_monitor
        
        # Initial capital (for delta calculations)
        self.initial_capital = config['backtest']['initial_capital']
        self.share_class = config['strategy']['share_class']
        
        # Redis
        self.redis = redis.Redis()
        self.redis.subscribe('risk:calculated', self._on_risk_update)
    
    async def handle_position_change(
        self,
        change_type: str,
        params: Dict,
        current_exposure: Dict,
        risk_metrics: Dict,
        market_data: Dict
    ) -> Dict:
        """
        Unified handler for ALL position changes.
        
        Args:
            change_type: 'INITIAL_SETUP', 'DEPOSIT', 'WITHDRAWAL', 'REBALANCE'
            params: Type-specific parameters
            current_exposure: Current exposure from monitor
            risk_metrics: Current risks from monitor
            market_data: Real-time market data (prices, funding rates, gas)
        
        Returns:
            Instructions for execution managers
        """
        # Get desired position (mode-specific!)
        desired = self._get_desired_position(change_type, params, current_exposure, market_data)
        
        # Calculate gap
        gap = self._calculate_gap(current_exposure, desired)
        
        # Generate instructions to close gap
        instructions = self._generate_instructions(gap, change_type, market_data)
        
        return {
            'trigger': change_type,
            'current_state': self._extract_current_state(current_exposure),
            'desired_state': desired,
            'gaps': gap,
            'instructions': instructions
        }
    
    def _get_desired_position(
        self,
        change_type: str,
        params: Dict,
        current_exposure: Dict,
        market_data: Dict
    ) -> Dict:
        """
        Get desired position (MODE-SPECIFIC!).
        
        This is THE key function - different per mode!
        """
        if self.mode == 'pure_lending':
            return self._desired_pure_lending(change_type, params, market_data)
        
        elif self.mode == 'btc_basis':
            return self._desired_btc_basis(change_type, params, current_exposure, market_data)
        
        elif self.mode == 'eth_leveraged':
            return self._desired_eth_leveraged(change_type, params, current_exposure, market_data)
        
        elif self.mode == 'usdt_market_neutral':
            return self._desired_usdt_market_neutral(change_type, params, current_exposure, market_data)
        
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
    
    # ===== MODE-SPECIFIC DESIRED POSITION FUNCTIONS =====
    
    def _desired_pure_lending(self, change_type, params, market_data):
        """Pure lending: All capital in AAVE USDT."""
        if change_type == 'INITIAL_SETUP':
            return {
                'aave_usdt_supplied': self.initial_capital,
                'target_delta_eth': 0,
                'target_perp_positions': {},
                'aave_apy': market_data.get('aave_usdt_apy', 0.08)
            }
        
        elif change_type == 'DEPOSIT':
            return {
                'aave_usdt_supplied': 'INCREASE',  # Add to AAVE
                'deposit_amount': params['amount'],
                'aave_apy': market_data.get('aave_usdt_apy', 0.08)
            }
        
        # No rebalancing needed for pure lending
        return {}
    
    def _desired_btc_basis(self, change_type, params, current_exposure, market_data):
        """BTC basis: Long spot, short perp (market-neutral)."""
        if change_type == 'INITIAL_SETUP':
            # Initial BTC amount
            btc_price = market_data['btc_usd_price']
            capital_for_spot = self.initial_capital * 0.5
            btc_amount = capital_for_spot / btc_price
            
            return {
                'btc_spot': btc_amount,
                'btc_perp_short': -btc_amount,  # Equal short
                'target_delta_btc': 0,  # Market-neutral
                'cex_venue': self.config['strategy']['hedge_venues'][0],  # Single venue
                'btc_price': btc_price,
                'funding_rate': market_data['perp_funding_rates'][self.config['strategy']['hedge_venues'][0]].get('BTCUSDT-PERP', 0)
            }
        
        elif change_type == 'REBALANCE':
            # Maintain market neutrality
            current_btc_spot = current_exposure.get('btc_spot', 0)
            return {
                'btc_perp_short': -current_btc_spot,  # Match spot
                'target_delta_btc': 0,
                'btc_price': market_data['btc_usd_price'],
                'funding_rate': market_data['perp_funding_rates'][self.config['strategy']['hedge_venues'][0]].get('BTCUSDT-PERP', 0)
            }
        
        return {}
    
    def _desired_eth_leveraged(self, change_type, params, current_exposure, market_data):
        """
        ETH leveraged staking.
        
        Two sub-modes:
        - ETH share class: Long ETH, no hedge
        - USDT share class: Hedged with perps
        """
        if change_type == 'INITIAL_SETUP':
            if self.share_class == 'ETH':
                # No hedging, directional ETH
                return {
                    'aave_ltv': self.config['strategy']['target_ltv'],  # e.g., 0.91
                    'target_delta_eth': self.initial_capital,  # Stay long ETH
                    'target_perp_positions': {},  # No hedging!
                    'eth_price': market_data['eth_usd_price'],
                    'gas_price': market_data['gas_price_gwei']
                }
            
            else:  # USDT share class
                # Need hedging
                eth_price = market_data['eth_usd_price']
                capital_for_staking = self.initial_capital * 0.5
                eth_amount = capital_for_staking / eth_price
                
                return {
                    'aave_ltv': 0.91,
                    'target_delta_eth': 0,  # Market-neutral
                    'initial_eth_to_stake': eth_amount,
                    'target_perp_short_total': -eth_amount,  # Hedge
                    'eth_price': eth_price,
                    'gas_price': market_data['gas_price_gwei'],
                    'funding_rates': market_data['perp_funding_rates']
                }
        
        elif change_type == 'REBALANCE':
            # Maintain target LTV and delta
            if self.share_class == 'ETH':
                return {
                    'aave_ltv': 0.91,
                    'target_delta_eth': 'MAINTAIN',  # Don't change (directional)
                    'eth_price': market_data['eth_usd_price'],
                    'gas_price': market_data['gas_price_gwei']
                }
            else:  # USDT
                # Hedge should match AAVE net position
                aave_net_eth = current_exposure['erc20_wallet_net_delta_eth']
                return {
                    'aave_ltv': 0.91,
                    'target_delta_eth': 0,
                    'target_perp_short_total': -aave_net_eth,
                    'eth_price': market_data['eth_usd_price'],
                    'gas_price': market_data['gas_price_gwei'],
                    'funding_rates': market_data['perp_funding_rates']
                }
        
        return {}
    
    def _desired_usdt_market_neutral(self, change_type, params, current_exposure, market_data):
        """
        USDT market-neutral (most complex).
        
        Always maintain:
        - AAVE LTV: 0.91
        - Net delta: 0
        - Perp short = AAVE net long
        """
        aave_net_eth = current_exposure['erc20_wallet_net_delta_eth']
        
        if change_type == 'INITIAL_SETUP':
            eth_price = market_data['eth_usd_price']
            capital_for_staking = self.initial_capital * 0.5
            eth_to_stake = capital_for_staking / eth_price
            
            return {
                'aave_ltv': 0.91,
                'target_delta_eth': 0,
                'initial_eth_to_stake': eth_to_stake,
                'target_perp_short_total': -eth_to_stake,
                'hedge_allocation': self.config['strategy']['hedge_allocation'],
                'eth_price': eth_price,
                'gas_price': market_data['gas_price_gwei'],
                'funding_rates': market_data['perp_funding_rates'],
                'aave_apy': market_data.get('aave_usdt_apy', 0.08)
            }
        
        elif change_type == 'REBALANCE':
            return {
                'aave_ltv': 0.91,
                'target_delta_eth': 0,
                'target_perp_short_total': -aave_net_eth,  # Match AAVE
                'target_margin_ratio': 1.0,  # Full capital utilization
                'eth_price': market_data['eth_usd_price'],
                'gas_price': market_data['gas_price_gwei'],
                'funding_rates': market_data['perp_funding_rates']
            }
        
        elif change_type == 'DEPOSIT':
            # New capital: Split 50/50 (staking / hedge)
            return {
                'add_to_aave': params['amount'] * 0.5,
                'add_to_cex_margin': params['amount'] * 0.5,
                'eth_price': market_data['eth_usd_price'],
                'gas_price': market_data['gas_price_gwei']
            }
        
        return {}
```

---

## 🔧 **Instruction Generation**

```python
def _generate_instructions(self, gap: Dict, trigger_type: str, market_data: Dict) -> List[Dict]:
    """
    Generate execution instructions to close gap.
    
    Instructions are prioritized and sequenced.
    """
    instructions = []
    
    # Priority 1: Margin critical (prevent CEX liquidation)
    if 'margin_deficit_usd' in gap and gap['margin_deficit_usd'] > 1000:
        instructions.append(self._gen_add_margin_instruction(gap, market_data))
    
    # Priority 2: AAVE LTV critical (prevent AAVE liquidation)
    if 'aave_ltv_excess' in gap and gap['aave_ltv_excess'] > 0.02:
        instructions.append(self._gen_reduce_ltv_instruction(gap, market_data))
    
    # Priority 3: Delta drift (maintain market neutrality)
    if 'delta_gap_eth' in gap and abs(gap['delta_gap_eth']) > 2.0:
        instructions.append(self._gen_adjust_delta_instruction(gap, market_data))
    
    return instructions

def _gen_add_margin_instruction(self, gap: Dict, market_data: Dict) -> Dict:
    """
    Generate instruction to add margin to CEX.
    
    Flow:
    1. Atomic deleverage AAVE (free up ETH)
    2. Transfer ETH to CEX
    3. Sell ETH for USDT (spot)
    4. Reduce perp short (proportionally)
    """
    amount_usd = gap['margin_deficit_usd']
    venue = gap['critical_venue']  # Which exchange needs margin
    
    return {
        'priority': 1,
        'type': 'ADD_MARGIN_TO_CEX',
        'venue': venue,
        'amount_usd': amount_usd,
        'actions': [
            {
                'step': 1,
                'action': 'ATOMIC_DELEVERAGE_AAVE',
                'executor': 'OnChainExecutionManager',
                'params': {
                    'amount_usd': amount_usd,
                    'mode': 'atomic' if self.config['strategy']['use_flash_loan'] else 'sequential',
                    'unwind_mode': self.config['strategy'].get('unwind_mode', 'fast')  # fast or slow
                }
            },
            {
                'step': 2,
                'action': 'TRANSFER_ETH_TO_CEX',
                'executor': 'OnChainExecutionManager',
                'params': {
                    'venue': venue,
                    'amount_eth': amount_usd / market_data['eth_usd_price']
                }
            },
            {
                'step': 3,
                'action': 'SELL_ETH_SPOT',
                'executor': 'CEXExecutionManager',
                'params': {
                    'venue': venue,
                    'amount_eth': amount_usd / market_data['eth_usd_price']
                }
            },
            {
                'step': 4,
                'action': 'REDUCE_PERP_SHORT',
                'executor': 'CEXExecutionManager',
                'params': {
                    'venue': venue,
                    'instrument': 'ETHUSDT-PERP',
                    'amount_eth': amount_usd / market_data['eth_usd_price']
                }
            }
        ]
    }
```

---

## 🔄 **Mode-Specific Desired Positions**

### **Pure USDT Lending**

```python
desired_position = {
    'aave_usdt_supplied': initial_capital,  # All capital in AAVE
    'target_delta_eth': 0,                  # No ETH exposure
    'target_perp_positions': {},            # No derivatives
    'rebalancing_needed': False             # Never rebalances (simple!)
}
```

### **BTC Basis**

```python
desired_position = {
    'btc_spot': initial_btc_amount,           # Long BTC spot
    'btc_perp_short': -initial_btc_amount,    # Short BTC perp (equal)
    'target_delta_btc': 0,                    # Market-neutral
    'cex_venue': 'binance',                   # Single venue (cross-margin)
    'rebalancing_trigger': 'delta_drift > 3%'  # Adjust hedge if drift
}
```

### **ETH Leveraged** (ETH share class)

```python
desired_position = {
    'aave_ltv': 0.91,                         # Leverage target
    'target_delta_eth': initial_capital_eth,  # Stay long ETH (directional!)
    'target_perp_positions': {},              # No hedging
    'rebalancing_trigger': 'ltv_drift or hf_low'  # Only AAVE risk
}
```

### **ETH Leveraged** (USDT share class)

```python
desired_position = {
    'aave_ltv': 0.91,
    'target_delta_eth': 0,                    # Market-neutral
    'target_perp_short_total': -aave_net_eth, # Hedge AAVE position
    'hedge_allocation': {'binance': 0.33, 'bybit': 0.33, 'okx': 0.34},
    'rebalancing_trigger': 'ltv_drift or delta_drift or margin_low'
}
```

### **USDT Market-Neutral** (Most Complex)

```python
desired_position = {
    'aave_ltv': 0.91,
    'target_delta_eth': 0,
    'target_perp_short_total': -aave_net_eth,
    'target_perp_allocation': {
        'binance': aave_net_eth * 0.33,
        'bybit': aave_net_eth * 0.33,
        'okx': aave_net_eth * 0.34
    },
    'target_margin_ratio': 1.0,  # 100% margin (full capital utilization)
    'rebalancing_triggers': [
        'margin_ratio < 20% (URGENT)',
        'delta_drift > 5% (WARNING)',
        'ltv > 90% (CRITICAL)'
    ]
}
```

---

## 🚨 **Rebalancing Logic** (From FINAL_FIXES_SPECIFICATION.md)

### **Triggers**

```python
def check_rebalancing_needed(self, risk_metrics: Dict) -> Optional[str]:
    """Check if rebalancing needed."""
    
    # Priority 1: Margin critical (prevent CEX liquidation)
    if risk_metrics['cex_margin']['any_critical']:
        return 'MARGIN_CRITICAL'
    
    if risk_metrics['cex_margin']['min_margin_ratio'] < self.margin_warning_threshold:
        return 'MARGIN_WARNING'
    
    # Priority 2: Delta drift (maintain market neutrality)
    if risk_metrics['delta']['critical']:
        return 'DELTA_DRIFT_CRITICAL'
    
    if risk_metrics['delta']['warning']:
        return 'DELTA_DRIFT_WARNING'
    
    # Priority 3: AAVE LTV (prevent AAVE liquidation)
    if risk_metrics['aave']['critical']:
        return 'AAVE_LTV_CRITICAL'
    
    if risk_metrics['aave']['warning']:
        return 'AAVE_LTV_WARNING'
    
    # No rebalancing needed
    return None
```

### **Rebalancing Actions**

**Margin Support** (Most Common):
```python
# When ETH rises:
# - Perps lose money (shorts losing)
# - CEX margin depletes
# - Need to add margin

# Solution:
1. Reduce AAVE position (atomic deleverage via flash loan)
2. Free ETH from AAVE
3. Send ETH to CEX
4. Sell ETH for USDT (add to margin)
5. Reduce perp short (proportionally, maintain delta neutrality)

# Cost: ~$30-50 per rebalance (atomic mode)
```

**Delta Adjustment**:
```python
# When AAVE position grows from yields:
# - AAVE net ETH increases
# - Perp short stays same
# - Net delta drifts positive

# Solution:
1. Open additional perp shorts (no AAVE change)
2. Use existing CEX margin
3. Restore delta to 0

# Cost: ~$10-20 (just perp execution costs)
```

**Emergency Deleverage**:
```python
# When health factor too low:
# - AAVE at risk of liquidation
# - Reduce position significantly

# Solution:
1. Atomic deleverage AAVE (large amount)
2. Don't touch perps (accept delta exposure)
3. Preserve AAVE safety > maintain delta neutrality

# Cost: ~$30-50 + accept delta risk
```

---

## 🚀 **Live Trading Data Flow**

### **Real-Time Market Data Requirements**

```python
# Live Trading Mode - Data Provider Integration
class LiveDataProvider:
    """Real-time market data for live trading."""
    
    async def get_market_snapshot(self) -> Dict[str, Any]:
        """Get current market data snapshot."""
        return {
            # Core prices
            'eth_usd_price': await self.get_eth_price(),
            'btc_usd_price': await self.get_btc_price(),
            
            # AAVE rates
            'aave_usdt_apy': await self.get_aave_usdt_rate(),
            'aave_eth_apy': await self.get_aave_eth_rate(),
            
            # Perpetual funding rates (critical for basis strategies)
            'perp_funding_rates': {
                'binance': await self.get_binance_funding_rates(),
                'bybit': await self.get_bybit_funding_rates(),
                'okx': await self.get_okx_funding_rates()
            },
            
            # Gas prices (for on-chain operations)
            'gas_price_gwei': await self.get_current_gas_price(),
            'gas_price_fast_gwei': await self.get_fast_gas_price(),
            
            # LST prices (for staking strategies)
            'lst_prices': {
                'wsteth_usd': await self.get_wsteth_price(),
                'reth_usd': await self.get_reth_price(),
                'sfrxeth_usd': await self.get_sfrxeth_price()
            },
            
            'timestamp': datetime.utcnow(),
            'data_age_seconds': 0  # Real-time data
        }
```

### **Live vs Backtest Data Differences**

| **Aspect** | **Backtest Mode** | **Live Mode** |
|------------|-------------------|---------------|
| **Data Source** | Historical CSV files | Real-time APIs |
| **Latency** | Instant (pre-loaded) | 100-500ms per call |
| **Data Age** | Historical timestamps | Current timestamp |
| **Funding Rates** | Historical averages | Real-time rates |
| **Gas Prices** | Historical averages | Current network state |
| **Price Updates** | Per timestep | Continuous |
| **Error Handling** | Fail-fast | Retry with fallbacks |

### **Live Trading Deployment Considerations**

```python
# Live Trading Configuration
LIVE_TRADING_CONFIG = {
    'data_provider': {
        'type': 'live',
        'refresh_interval_seconds': 30,  # Update every 30s
        'max_data_age_seconds': 60,      # Reject data older than 1min
        'fallback_sources': ['primary', 'secondary', 'tertiary'],
        'rate_limits': {
            'binance': 1200,  # requests per minute
            'bybit': 120,
            'okx': 20
        }
    },
    
    'execution': {
        'slippage_tolerance': 0.005,     # 0.5% max slippage
        'gas_price_multiplier': 1.2,     # 20% above current gas
        'max_gas_price_gwei': 100,       # Emergency gas limit
        'execution_timeout_seconds': 300 # 5min max execution time
    },
    
    'risk_management': {
        'max_position_size_usd': 1000000,
        'emergency_stop_loss_pct': 0.15,  # 15% max loss
        'heartbeat_timeout_seconds': 300, # 5min heartbeat timeout
        'circuit_breaker_enabled': True
    }
}
```

### **Live Trading Deployment Mechanics**

#### **1. Environment Setup**
```bash
# Production environment variables
export TRADING_MODE=live
export DATA_PROVIDER_MODE=live
export EXECUTION_MODE=live
export RISK_MODE=strict

# API credentials (encrypted)
export BINANCE_API_KEY=encrypted_key
export BINANCE_API_SECRET=encrypted_secret
export BYBIT_API_KEY=encrypted_key
export BYBIT_API_SECRET=encrypted_secret

# Wallet configuration
export WALLET_PRIVATE_KEY=encrypted_key
export WALLET_ADDRESS=0x...
```

#### **2. Service Orchestration**
```python
# Live Trading Service Architecture
class LiveTradingOrchestrator:
    """Orchestrates live trading execution."""
    
    def __init__(self):
        self.data_provider = LiveDataProvider()
        self.strategy_manager = StrategyManager()
        self.execution_managers = {
            'cex': CEXExecutionManager(),
            'onchain': OnChainExecutionManager()
        }
        self.risk_monitor = LiveRiskMonitor()
        self.heartbeat_monitor = HeartbeatMonitor()
    
    async def run_live_trading_loop(self):
        """Main live trading loop."""
        while self.is_running:
            try:
                # 1. Get fresh market data
                market_data = await self.data_provider.get_market_snapshot()
                
                # 2. Check if data is fresh enough
                if market_data['data_age_seconds'] > 60:
                    logger.warning("Market data too old, skipping cycle")
                    continue
                
                # 3. Get current exposure and risk
                exposure = await self.exposure_monitor.get_current_exposure()
                risk = await self.risk_monitor.get_current_risk()
                
                # 4. Make strategy decision with live data
                decision = await self.strategy_manager.handle_position_change(
                    change_type='REBALANCE',
                    params={},
                    current_exposure=exposure,
                    risk_metrics=risk,
                    market_data=market_data  # ← Live data!
                )
                
                # 5. Execute if needed
                if decision['instructions']:
                    await self.execute_instructions(decision['instructions'])
                
                # 6. Update heartbeat
                await self.heartbeat_monitor.update_heartbeat()
                
            except Exception as e:
                logger.error(f"Live trading loop error: {e}")
                await self.emergency_stop()
            
            # Wait for next cycle
            await asyncio.sleep(30)  # 30-second cycles
```

#### **3. Deployment Differences**

| **Component** | **Backtest** | **Live Trading** |
|---------------|--------------|------------------|
| **Data Provider** | CSV file reader | Real-time API client |
| **Execution** | Simulated | Real blockchain/CEX |
| **Risk Monitoring** | Historical validation | Real-time circuit breakers |
| **Error Handling** | Fail-fast | Retry + fallback |
| **Logging** | File-based | Real-time monitoring |
| **Monitoring** | Basic metrics | Full observability stack |

---

## 🔗 **Integration**

### **Triggered By**:
- Risk Monitor updates (via Redis `risk:calculated`)
- User actions (deposit, withdrawal)
- Hourly checks (scheduled)

### **Uses Data From**:
- **Exposure Monitor** ← Current exposure
- **Risk Monitor** ← Risk metrics
- **Config** ← Targets, thresholds, mode

### **Issues Instructions To**:
- **CEX Execution Manager** ← CEX trades
- **OnChain Execution Manager** ← On-chain transactions

### **Redis**:

**Subscribes**:
- `risk:calculated` → Check if rebalancing needed

**Publishes**:
- `strategy:instructions` (channel) → Notify execution managers
- `strategy:rebalancing` (key) → Current rebalancing plan

---

## 🧪 **Testing**

```python
def test_initial_setup_usdt_market_neutral():
    """Test initial position for USDT market-neutral mode."""
    manager = StrategyManager('usdt_market_neutral', config, ...)
    
    desired = manager._get_desired_position(
        'INITIAL_SETUP',
        {'eth_price': 3300},
        current_exposure={}
    )
    
    # Should want:
    # - 0.91 LTV on AAVE
    # - 0 net delta
    # - Perp shorts to hedge
    assert desired['aave_ltv'] == 0.91
    assert desired['target_delta_eth'] == 0
    assert desired['target_perp_short_total'] < 0  # Short

def test_rebalancing_instruction_generation():
    """Test rebalancing instruction generation."""
    gap = {
        'margin_deficit_usd': 9124.50,
        'critical_venue': 'binance'
    }
    
    manager = StrategyManager('usdt_market_neutral', config, ...)
    instruction = manager._gen_add_margin_instruction(gap)
    
    # Should have 4 actions
    assert len(instruction['actions']) == 4
    assert instruction['actions'][0]['action'] == 'ATOMIC_DELEVERAGE_AAVE'
    assert instruction['actions'][1]['action'] == 'TRANSFER_ETH_TO_CEX'
    assert instruction['actions'][2]['action'] == 'SELL_ETH_SPOT'
    assert instruction['actions'][3]['action'] == 'REDUCE_PERP_SHORT'

def test_mode_determines_hedging():
    """Test mode-specific hedging logic."""
    # ETH share class: No hedging
    manager_eth = StrategyManager('eth_leveraged', config_eth, ...)
    desired_eth = manager_eth._desired_eth_leveraged('INITIAL_SETUP', {}, {})
    assert desired_eth['target_perp_positions'] == {}
    
    # USDT share class: Always hedge
    manager_usdt = StrategyManager('eth_leveraged', config_usdt, ...)
    desired_usdt = manager_usdt._desired_eth_leveraged('INITIAL_SETUP', {'eth_price': 3300}, {})
    assert desired_usdt['target_perp_short_total'] < 0
```

---

## 🎯 **Success Criteria**

- [ ] Mode detection works correctly
- [ ] Desired position correct for each mode
- [ ] Handles initial setup same as rebalancing (unified approach)
- [ ] Generates correct instructions for gaps
- [ ] Prioritizes margin critical > delta drift > LTV
- [ ] ETH share class never hedges
- [ ] USDT share class always hedges
- [ ] Instructions include all steps for execution
- [ ] Supports fast vs slow unwinding modes
- [ ] Publishes to execution managers via Redis

---

**Status**: Specification complete! ✅


