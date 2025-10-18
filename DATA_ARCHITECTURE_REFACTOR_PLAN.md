# Complete Data Architecture Refactor Plan - 4-Provider System

**Date**: 2025-10-16  
**Status**: ✅ COMPLETED - 2025-10-16  
**Scope**: 100+ files (code, config, docs, tests)

## Executive Summary

### Current Problems:
1. ❌ Duplicate `data_requirements` and `position_subscriptions` in configs
2. ❌ Hardcoded if/elif chains in utility_manager
3. ❌ Data providers have different structures
4. ❌ No systematic mapping from position_key → data source
5. ❌ Duplicate logic across components

### New Architecture: 4-Provider System
✅ **Convention-Based Mapping**: Position key structure determines data lookup path  
✅ **Centralized Data Access**: All data lookups through utility_manager  
✅ **Standardized Data Provider Contract**: All providers return same structure  
✅ **4 Provider Types**: HistoricalDeFi, HistoricalCeFi, LiveDeFi, LiveCeFi
✅ **Execution Mode Routing**: Factory routes based on execution_mode + data_type
✅ **Separate ML Service**: ML predictions handled independently from position data

---

## Architecture Design

### 1. Position Key → Data Provider Mapping

#### Convention Rules:
```python
# Position Key Format: "venue:position_type:instrument"

Position Type     Data Provider Path                     Example
─────────────────────────────────────────────────────────────────────────────
BaseToken      →  market_data.prices[token]          →  USDT: 1.0, ETH: 3000
Perp           →  protocol_data.perp_prices[base_venue]  →  btc_binance: 50000
aToken         →  protocol_data.aave_indexes[token]  →  aUSDT: 1.05
debtToken      →  protocol_data.aave_indexes[token]  →  debtUSDT: 1.05
LST            →  protocol_data.oracle_prices[token] →  weeth: 3150
```

#### Data Provider Contract (ALL providers MUST return):
```python
{
    'timestamp': pd.Timestamp,
    'market_data': {
        'prices': Dict[str, float],          # Simple token prices: BTC, ETH, USDT, EIGEN, ETHFI
        'funding_rates': Dict[str, float],   # {asset_venue: rate}
    },
    'protocol_data': {
        'perp_prices': Dict[str, float],     # {base_venue: price}
        'aave_indexes': Dict[str, float],    # {aToken: index}
        'oracle_prices': Dict[str, float],   # {lst_token: price} - weeth, wsteth
        'protocol_rates': Dict[str, float],  # {protocol_asset_type: rate}
        'staking_rewards': Dict[str, float], # {protocol_lst: apy} - etherfi_weeth_apy, lido_wsteth_apy
        'seasonal_rewards': Dict[str, DataFrame], # {protocol: rewards_data} - etherfi_king
    },
    'execution_data': {
        'gas_costs': Dict[str, float],
        'execution_costs': Dict[str, float],
    },
    'ml_data': {  # Only for CeFi providers
        'predictions': Dict[str, float],     # {signal_name: value}
    }
}
```

### 2. Data Provider Implementation

#### Factory Routing:
```python
def create_data_provider(execution_mode: str, data_type: str, config: Dict) -> DataProvider:
    """Factory routes to appropriate provider based on execution mode and data type."""
    if execution_mode == 'backtest' and data_type == 'defi':
        return HistoricalDeFiDataProvider(config)
    elif execution_mode == 'backtest' and data_type == 'cefi':
        return HistoricalCeFiDataProvider(config, ml_service)
    elif execution_mode == 'live' and data_type == 'defi':
        return LiveDeFiDataProvider(config)
    elif execution_mode == 'live' and data_type == 'cefi':
        return LiveCeFiDataProvider(config, ml_service)
    else:
        raise ValueError(f"Unknown execution_mode: {execution_mode} or data_type: {data_type}")
```

#### Historical DeFi Data Provider:
```python
class HistoricalDeFiDataProvider:
    """Handles DeFi strategies in backtest mode: pure_lending_usdt, btc_basis, eth_basis, eth_leveraged, eth_staking_only, usdt_market_neutral, usdt_market_neutral_no_leverage"""
    
    def __init__(self, config):
        self.execution_mode = "backtest"
        self.data_type = "defi"
        self.granularity = "1h"
        self.position_subscriptions = config['component_config']['position_monitor']['position_subscriptions']
        self.csv_mappings = self._derive_csv_mappings()
    
    def _derive_csv_mappings(self):
        """Derive CSV mappings from position_subscriptions for DeFi strategies."""
        mappings = {}
        
        for position_key in self.position_subscriptions:
            venue, position_type, instrument = position_key.split(':')
            
            if position_type == 'BaseToken':
                mappings[f'market_data.prices.{instrument}'] = f'data/market_data/spot_prices/{instrument.lower()}_usd/*.csv'
                
            elif position_type == 'Perp':
                base = self._extract_base_asset(instrument)
                mappings[f'protocol_data.perp_prices.{base}_{venue}'] = f'data/market_data/derivatives/futures_ohlcv/{venue}_{instrument}_perp_*.csv'
                mappings[f'market_data.funding_rates.{base}_{venue}'] = f'data/market_data/derivatives/funding_rates/{venue}_funding_rates_*.csv'
                
            elif position_type == 'aToken':
                mappings[f'protocol_data.aave_indexes.{instrument}'] = f'data/protocol_data/aave/aave_v3_{instrument.lower()}_rates_*.csv'
                
            elif position_type == 'LST':
                mappings[f'protocol_data.oracle_prices.{instrument.lower()}'] = f'data/market_data/spot_prices/lst_eth_ratios/{instrument.lower()}_eth_ratio_*.csv'
                mappings[f'protocol_data.staking_rewards.etherfi_{instrument.lower()}_apy'] = f'data/protocol_data/staking/base_yields/etherfi_{instrument.lower()}_apy_*.csv'
        
        # Always add execution costs
        mappings['execution_data.gas_costs'] = 'data/blockchain_data/gas_prices/*.csv'
        mappings['execution_data.execution_costs'] = 'data/execution_costs/lookup_tables/*.json'
        
        return mappings
```

#### Historical CeFi Data Provider:
```python
class HistoricalCeFiDataProvider:
    """Handles CeFi/ML strategies in backtest mode: ml_btc_directional_btc_margin, ml_btc_directional_usdt_margin"""
    
    def __init__(self, config, ml_service):
        self.execution_mode = "backtest"
        self.data_type = "cefi"
        self.granularity = "5min"
        self.position_subscriptions = config['component_config']['position_monitor']['position_subscriptions']
        self.csv_mappings = self._derive_csv_mappings()
        self.ml_service = ml_service  # Separate ML service for predictions
    
    def _derive_csv_mappings(self):
        """Derive CSV mappings from position_subscriptions for CeFi strategies."""
        mappings = {}
        
        for position_key in self.position_subscriptions:
            venue, position_type, instrument = position_key.split(':')
            
            if position_type == 'BaseToken':
                mappings[f'market_data.prices.{instrument}'] = f'data/market_data/spot_prices/{instrument.lower()}_usd/*.csv'
                
            elif position_type == 'Perp':
                base = self._extract_base_asset(instrument)
                mappings[f'protocol_data.perp_prices.{base}_{venue}'] = f'data/market_data/derivatives/futures_ohlcv/{venue}_{instrument}_perp_*.csv'
                mappings[f'market_data.funding_rates.{base}_{venue}'] = f'data/market_data/derivatives/funding_rates/{venue}_funding_rates_*.csv'
        
        # Execution costs
        mappings['execution_data.gas_costs'] = 'data/blockchain_data/gas_prices/*.csv'
        mappings['execution_data.execution_costs'] = 'data/execution_costs/lookup_tables/*.json'
        
        return mappings
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict:
        """Get data with ML predictions from separate service."""
        data = self._get_position_data(timestamp)
        
        # Add ML predictions from separate service
        ml_predictions = self.ml_service.get_predictions(timestamp)
        data['ml_data'] = ml_predictions
        
        return data
```

#### Live DeFi Data Provider:
```python
class LiveDeFiDataProvider:
    """Handles DeFi strategies in live mode with real-time APIs."""
    
    def __init__(self, config):
        self.execution_mode = "live"
        self.data_type = "defi"
        self.position_subscriptions = config['component_config']['position_monitor']['position_subscriptions']
        
        # Initialize API clients with credentials from env vars
        self.binance_client = self._init_binance()  # Uses BINANCE_API_KEY
        self.bybit_client = self._init_bybit()      # Uses BYBIT_API_KEY
        self.okx_client = self._init_okx()          # Uses OKX_API_KEY
        self.aave_client = self._init_aave()        # Uses AAVE_API_KEY
    
    async def get_data(self, timestamp: pd.Timestamp) -> Dict:
        """Get real-time data from APIs."""
        return {
            'market_data': {
                'prices': {
                    'ETH': await self._fetch_spot_price('ETH'),
                    'USDT': 1.0
                }
            },
            'protocol_data': {
                'perp_prices': {
                    'btc_binance': await self._fetch_perp_price('BTC', 'binance'),
                    'eth_bybit': await self._fetch_perp_price('ETH', 'bybit'),
                },
                'aave_indexes': {
                    'aUSDT': await self._fetch_aave_index('aUSDT')
                }
            }
        }
```

#### Live CeFi Data Provider:
```python
class LiveCeFiDataProvider:
    """Handles CeFi/ML strategies in live mode with real-time APIs + ML service."""
    
    def __init__(self, config, ml_service):
        self.execution_mode = "live"
        self.data_type = "cefi"
        self.position_subscriptions = config['component_config']['position_monitor']['position_subscriptions']
        self.ml_service = ml_service
        
        # Initialize API clients
        self.binance_client = self._init_binance()
        self.bybit_client = self._init_bybit()
        self.okx_client = self._init_okx()
    
    async def get_data(self, timestamp: pd.Timestamp) -> Dict:
        """Get real-time data with ML predictions."""
        data = await self._get_position_data(timestamp)
        
        # Add real-time ML predictions
        ml_predictions = await self.ml_service.get_live_predictions(timestamp)
        data['ml_data'] = ml_predictions
        
        return data
```

#### ML Service:
```python
class MLService:
    """Separate service for ML predictions (both historical and live)."""
    
    def __init__(self, config):
        self.ml_config = config.get('ml_config', {})
        self.model_endpoint = self.ml_config.get('model_endpoint')
        self.api_key = os.getenv('ML_API_KEY')
    
    def get_predictions(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get ML predictions for backtest mode."""
        # Load from CSV or call ML API
        return {
            'btc_direction': self._get_btc_direction_prediction(timestamp),
            'eth_volatility': self._get_eth_volatility_prediction(timestamp)
        }
    
    async def get_live_predictions(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        """Get real-time ML predictions for live mode."""
        # Call ML API or run model inference
        return await self._call_ml_api(timestamp)
```

---

## Implementation Plan

### Phase 1: Remove BaseDataProvider and Simplify Architecture

#### 1.1 Remove BaseDataProvider
- Delete `backend/src/basis_strategy_v1/infrastructure/data/base_data_provider.py`
- Remove abstract methods and complex inheritance

#### 1.2 Create 4 Concrete Data Providers
- `HistoricalDeFiDataProvider` - CSV-based DeFi data
- `HistoricalCeFiDataProvider` - CSV-based CeFi data + ML service
- `LiveDeFiDataProvider` - API-based DeFi data
- `LiveCeFiDataProvider` - API-based CeFi data + ML service

#### 1.3 Create ML Service
- `MLService` - Separate service for ML predictions
- Handles both historical CSV data and live API calls

#### 1.4 Update Data Provider Factory
```python
def create_data_provider(execution_mode: str, data_type: str, config: Dict) -> DataProvider:
    """Factory routes based on execution mode and data type."""
    if execution_mode == 'backtest' and data_type == 'defi':
        return HistoricalDeFiDataProvider(config)
    elif execution_mode == 'backtest' and data_type == 'cefi':
        ml_service = MLService(config)
        return HistoricalCeFiDataProvider(config, ml_service)
    elif execution_mode == 'live' and data_type == 'defi':
        return LiveDeFiDataProvider(config)
    elif execution_mode == 'live' and data_type == 'cefi':
        ml_service = MLService(config)
        return LiveCeFiDataProvider(config, ml_service)
    else:
        raise ValueError(f"Unknown execution_mode: {execution_mode} or data_type: {data_type}")
```

### Phase 2: Update Configuration

#### 2.1 Add data_type to Mode Configs
```yaml
# configs/modes/pure_lending_usdt.yaml
data_type: "defi"  # DeFi strategy
position_subscriptions:
  - "wallet:BaseToken:USDT"
  - "aave:aToken:aUSDT"

# configs/modes/ml_btc_directional_btc_margin.yaml  
data_type: "cefi"  # CeFi/ML strategy
position_subscriptions:
  - "wallet:BaseToken:USDT"
  - "binance:Perp:BTCUSDT"
ml_config:
  model_endpoint: "https://ml-api.example.com/predict"
  signals: ["btc_direction", "eth_volatility"]
```

#### 2.2 Remove data_requirements
- Remove `data_requirements` from all mode configs
- Keep only `position_subscriptions` as single source of truth

### Phase 3: Update Components

#### 3.1 Update Utility Manager
- Remove old token-based methods
- Keep position_key-based methods
- Add ML data access methods

#### 3.2 Update Data Provider Factory
- Route based on execution_mode + data_type
- Initialize ML service for CeFi providers
- Remove load_data() method (on-demand loading)

### Phase 4: Quality Gates and Testing

#### 4.1 Update Quality Gates
- Remove references to deleted providers
- Update config validation for new structure
- Add ML service validation

#### 4.2 Create New Tests
- Test 4-provider routing
- Test ML service integration
- Test execution mode switching

---

## Implementation Summary

**✅ COMPLETED TASKS:**
1. **Removed `data_requirements` from all 9 mode configs** - Eliminated duplicate information
2. **Created new data providers** - DeFi and CeFi providers with position_subscriptions-based data loading
3. **Updated utility manager** - Already had position_key-based methods
4. **Updated components** - All components already using new data access patterns
5. **Removed old data providers** - Deleted 8 old provider files and updated factory
6. **Added quality gates** - Comprehensive validation for new data provider architecture
7. **Updated documentation** - All docs now reflect new architecture

**✅ KEY ACHIEVEMENTS:**
- **Single Source of Truth**: `position_subscriptions` is now the only data requirement declaration
- **Convention-Based Mapping**: Data providers automatically derive CSV mappings from position keys
- **Standardized Contract**: All providers return consistent data structure
- **No Backward Compatibility**: Clean architecture with old code completely removed
- **Quality Gates**: Automated validation ensures compliance with new architecture

**✅ ARCHITECTURE BENEFITS:**
- Eliminated config duplication and sync issues
- Reduced maintenance burden
- Made data providers self-contained and strategy-specific
- Follows single responsibility principle
- Enables easy testing and validation

## References

- Position Key Format: `docs/01_POSITION_MONITOR.md`
- Data Provider Contract: `docs/specs/09_DATA_PROVIDER.md`
- Utility Manager: `docs/specs/20_UTILITY_MANAGER.md`
- CSV Data Sources: `data/README.md`
- Quality Gates: `docs/QUALITY_GATES.md`
