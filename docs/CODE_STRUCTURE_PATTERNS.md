# Code Structure Patterns for Mode-Agnostic Architecture

**Date**: October 11, 2025  
**Purpose**: Complete code structure patterns for all 20 components using config-driven, mode-agnostic architecture  
**Status**: ⭐ **IMPLEMENTATION GUIDE** - Use these patterns when implementing or refactoring components

## 📚 **Canonical Sources**

This guide provides implementation patterns for:
- **REFERENCE_ARCHITECTURE_CANONICAL.md** - Core architectural principles including config-driven architecture
- **19_CONFIGURATION.md** - Complete config schemas with component_config
- **Component Specs (docs/specs/)** - All 20 component specifications (11 core + 9 supporting)

## Component Architecture

**Core Components (11)**: Runtime data/decision/execution flow - most are mode-agnostic
**Supporting Components (9)**: Services, utilities, infrastructure

See COMPONENT_SPECS_INDEX.md for complete component list and organization.

---

## **1. DATA PROVIDER PATTERNS**

### **Base DataProvider Interface**

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd

class BaseDataProvider(ABC):
    """Abstract base class for all data providers"""
    
    def __init__(self, execution_mode: str, config: Dict):
        self.execution_mode = execution_mode
        self.config = config
        self.available_data_types = []  # Set by subclasses
    
    @abstractmethod
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Return standardized data structure.
        
        ALL providers must return data in this exact format:
        {
            'market_data': {
                'prices': {...},
                'rates': {...}
            },
            'protocol_data': {
                'aave_indexes': {...},
                'oracle_prices': {...},
                'perp_prices': {...}
            },
            'staking_data': {...},
            'execution_data': {...}
        }
        """
        pass
    
    @abstractmethod
    def validate_data_requirements(self, data_requirements: List[str]) -> None:
        """
        Validate that this provider can satisfy all data requirements.
        Raises ValueError if any requirements cannot be met.
        """
        pass
    
    @abstractmethod
    def get_timestamps(self, start_date: str, end_date: str) -> List[pd.Timestamp]:
        """Get available timestamps for backtest period"""
        pass
```

### **Mode-Specific DataProvider Example**

```python
class PureLendingDataProvider(BaseDataProvider):
    """Data provider for pure lending mode"""
    
    def __init__(self, execution_mode: str, config: Dict):
        super().__init__(execution_mode, config)
        self.available_data_types = [
            'usdt_prices',
            'aave_lending_rates',
            'aave_indexes',
            'gas_costs',
            'execution_costs'
        ]
    
    def validate_data_requirements(self, data_requirements: List[str]) -> None:
        """Validate that this provider can satisfy all data requirements"""
        missing_requirements = []
        for requirement in data_requirements:
            if requirement not in self.available_data_types:
                missing_requirements.append(requirement)
        
        if missing_requirements:
            raise ValueError(
                f"PureLendingDataProvider cannot satisfy requirements: {missing_requirements}. "
                f"Available: {self.available_data_types}"
            )
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Return standardized data structure"""
        return {
            'market_data': {
                'prices': {
                    'USDT': 1.0,  # Always 1.0
                    'ETH': self._load_eth_price(timestamp)  # For gas calculations
                },
                'rates': {
                    'aave_usdt_supply': self._load_aave_usdt_rate(timestamp)
                }
            },
            'protocol_data': {
                'aave_indexes': {
                    'aUSDT': self._load_aave_usdt_index(timestamp)
                },
                'oracle_prices': {},  # Empty for this mode
                'perp_prices': {}     # Empty for this mode
            },
            'execution_data': {
                'gas_costs': self._load_gas_costs(timestamp),
                'execution_costs': self._load_execution_costs()
            }
        }
    
    def get_timestamps(self, start_date: str, end_date: str) -> List[pd.Timestamp]:
        """Get hourly timestamps for backtest period"""
        return pd.date_range(start=start_date, end=end_date, freq='H', tz='UTC')
```

### **Additional Mode-Specific DataProvider Examples**

#### **BTCBasisDataProvider**
```python
class BTCBasisDataProvider(BaseDataProvider):
    """Data provider for BTC basis trading mode"""
    
    def __init__(self, execution_mode: str, config: Dict):
        super().__init__(execution_mode, config)
        self.available_data_types = [
            'btc_prices', 'btc_futures', 'funding_rates', 'gas_costs', 'execution_costs'
        ]
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        return {
            'market_data': {
                'prices': {
                    'BTC': self._load_btc_price(timestamp),
                    'USDT': 1.0,
                    'ETH': self._load_eth_price(timestamp)
                },
                'rates': {
                    'funding': {
                        'BTC_binance': self._load_btc_funding_rate(timestamp, 'binance'),
                        'BTC_bybit': self._load_btc_funding_rate(timestamp, 'bybit')
                    }
                }
            },
            'protocol_data': {
                'perp_prices': {
                    'BTC_binance': self._load_btc_perp_price(timestamp, 'binance'),
                    'BTC_bybit': self._load_btc_perp_price(timestamp, 'bybit')
                }
            },
            'staking_data': {},  # Empty for basis trading
            'execution_data': {
                'wallet_balances': self._load_wallet_balances(timestamp),
                'cex_spot_balances': self._load_cex_spot_balances(timestamp),
                'cex_derivatives_balances': self._load_cex_derivatives_balances(timestamp),
                'gas_costs': self._load_gas_costs(timestamp),
                'execution_costs': self._load_execution_costs(timestamp)
            }
        }
```

#### **ETHStakingOnlyDataProvider**
```python
class ETHStakingOnlyDataProvider(BaseDataProvider):
    """Data provider for ETH staking only mode"""
    
    def __init__(self, execution_mode: str, config: Dict):
        super().__init__(execution_mode, config)
        self.available_data_types = [
            'eth_prices', 'weeth_prices', 'staking_rewards', 'gas_costs', 'execution_costs'
        ]
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        return {
            'market_data': {
                'prices': {
                    'ETH': self._load_eth_price(timestamp),
                    'weETH': self._load_weeth_price(timestamp),
                    'USDT': 1.0
                }
            },
            'protocol_data': {
                'oracle_prices': {
                    'weETH': self._load_weeth_oracle_price(timestamp)
                }
            },
            'staking_data': {
                'rewards': {
                    'ETH': self._load_eth_staking_rewards(timestamp),
                    'EIGEN': self._load_eigen_rewards(timestamp)
                },
                'apr': {
                    'ETH': self._load_eth_staking_apr(timestamp)
                }
            },
            'execution_data': {
                'wallet_balances': self._load_wallet_balances(timestamp),
                'smart_contract_balances': self._load_smart_contract_balances(timestamp),
                'gas_costs': self._load_gas_costs(timestamp),
                'execution_costs': self._load_execution_costs(timestamp)
            }
        }
```

#### **ETHLeveragedDataProvider**
```python
class ETHLeveragedDataProvider(BaseDataProvider):
    """Data provider for ETH leveraged staking mode"""
    
    def __init__(self, execution_mode: str, config: Dict):
        super().__init__(execution_mode, config)
        self.available_data_types = [
            'eth_prices', 'weeth_prices', 'aave_lending_rates', 'staking_rewards', 
            'eigen_rewards', 'gas_costs', 'execution_costs', 'aave_risk_params'
        ]
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        return {
            'market_data': {
                'prices': {
                    'ETH': self._load_eth_price(timestamp),
                    'weETH': self._load_weeth_price(timestamp),
                    'USDT': 1.0
                },
                'rates': {
                    'aave_eth_supply': self._load_aave_eth_rate(timestamp)
                }
            },
            'protocol_data': {
                'aave_indexes': {
                    'aETH': self._load_aave_eth_index(timestamp),
                    'variableDebtWETH': self._load_aave_variable_debt_eth_index(timestamp)
                },
                'risk_params': {
                    'ltv': self._load_ltv(timestamp),
                    'liquidation_threshold': self._load_liquidation_threshold(timestamp)
                }
            },
            'staking_data': {
                'rewards': {
                    'ETH': self._load_eth_staking_rewards(timestamp)
                },
                'eigen_rewards': {
                    'EIGEN': self._load_eigen_rewards(timestamp)
                }
            },
            'execution_data': {
                'wallet_balances': self._load_wallet_balances(timestamp),
                'smart_contract_balances': self._load_smart_contract_balances(timestamp),
                'gas_costs': self._load_gas_costs(timestamp),
                'execution_costs': self._load_execution_costs(timestamp)
            }
        }
```

### **DataProvider Factory**

```python
class DataProviderFactory:
    """Factory for creating mode-specific data providers"""
    
    @staticmethod
    def create(execution_mode: str, config: Dict) -> BaseDataProvider:
        """
        Create mode-specific data provider based on mode.
        Validates that provider can satisfy all data_requirements.
        """
        mode = config['mode']
        data_requirements = config.get('data_requirements', [])
        
        # Create mode-specific provider
        provider_map = {
            'pure_lending': PureLendingDataProvider,
            'btc_basis': BTCBasisDataProvider,
            'eth_basis': ETHBasisDataProvider,
            'eth_staking_only': ETHStakingOnlyDataProvider,
            'eth_leveraged': ETHLeveragedDataProvider,
            'usdt_market_neutral_no_leverage': USDTMarketNeutralNoLeverageDataProvider,
            'usdt_market_neutral': USDTMarketNeutralDataProvider
        }
        
        if mode not in provider_map:
            raise ValueError(f"Unknown strategy mode: {mode}")
        
        provider = provider_map[mode](execution_mode, config)
        
        # Validate that provider can satisfy all data requirements
        provider.validate_data_requirements(data_requirements)
        
        return provider
```

**ADR Reference**: ADR-053 (DataProvider Factory with validation)

---

## **2. RISK MONITOR PATTERN (Mode-Agnostic)**

### **Complete Class Structure**

```python
class RiskMonitor:
    """Mode-agnostic risk monitor using config-driven behavior"""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                 position_monitor: PositionMonitor, exposure_monitor: ExposureMonitor):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.position_monitor = position_monitor
        self.exposure_monitor = exposure_monitor
        
        # Extract config-driven settings
        self.risk_config = config.get('component_config', {}).get('risk_monitor', {})
        self.enabled_risk_types = self.risk_config.get('enabled_risk_types', [])
        self.risk_limits = self.risk_config.get('risk_limits', {})
        
        # Initialize component-specific state
        self.current_risk_metrics = {}
        self.last_calculation_timestamp = None
        self.risk_history = []
        
        # Validate config
        self._validate_risk_config()
    
    def _validate_risk_config(self):
        """Validate risk monitor configuration"""
        if not self.enabled_risk_types:
            raise ValueError("enabled_risk_types cannot be empty")
        
        valid_risk_types = [
            'ltv_risk', 'liquidation_risk',  # AAVE risks (2 types)
            'cex_margin_ratio', 'delta_risk'  # CEX and delta risks (2 types)
        ]  # Total: 4 core risk types
        
        for risk_type in self.enabled_risk_types:
            if risk_type not in valid_risk_types:
                raise ValueError(f"Invalid risk type: {risk_type}")
    
    def assess_risk(self, exposure_data: Dict, market_data: Dict) -> Dict:
        """
        Assess risk using config-driven risk types.
        MODE-AGNOSTIC - works for all strategy modes.
        """
        risk_metrics = {}
        risk_alerts = {}
        
        # Calculate only enabled risk types
        for risk_type in self.enabled_risk_types:
            try:
                if risk_type == 'protocol_risk':
                    risk_metrics[risk_type] = self._calculate_protocol_risk(exposure_data, market_data)
                
                elif risk_type == 'aave_health_factor':
                    if 'aave_indexes' in market_data.get('protocol_data', {}):
                        risk_metrics[risk_type] = self._calculate_health_factor(exposure_data, market_data)
                    else:
                        risk_metrics[risk_type] = None  # Data not available
                
                elif risk_type == 'cex_margin_ratio':
                    if 'perp_prices' in market_data.get('protocol_data', {}):
                        risk_metrics[risk_type] = self._calculate_margin_ratio(exposure_data, market_data)
                    else:
                        risk_metrics[risk_type] = None
                
                # ... etc for all risk types
            
            except Exception as e:
                logger.error(f"Error calculating {risk_type}: {e}")
                risk_metrics[risk_type] = None
        
        # Apply risk limits from config
        for risk_type, value in risk_metrics.items():
            if value is not None:
                limit_key_min = f"{risk_type}_min"
                limit_key_max = f"{risk_type}_max"
                
                if limit_key_min in self.risk_limits and value < self.risk_limits[limit_key_min]:
                    risk_alerts[risk_type] = f"{risk_type} below minimum: {value} < {self.risk_limits[limit_key_min]}"
                
                if limit_key_max in self.risk_limits and value > self.risk_limits[limit_key_max]:
                    risk_alerts[risk_type] = f"{risk_type} above maximum: {value} > {self.risk_limits[limit_key_max]}"
        
        return {
            'risk_metrics': risk_metrics,
            'risk_alerts': risk_alerts,
            'enabled_risk_types': self.enabled_risk_types,
            'timestamp': exposure_data.get('timestamp')
        }
```

**ADR Reference**: ADR-052 (Config-driven components), ADR-054 (Graceful data handling)

---

## **3. EXPOSURE MONITOR PATTERN (Mode-Agnostic)**

### **Complete Class Structure**

```python
class ExposureMonitor:
    """Mode-agnostic exposure calculation using config-driven asset tracking"""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                 position_monitor: PositionMonitor):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.position_monitor = position_monitor
        
        # Extract exposure-specific config
        self.exposure_config = config.get('component_config', {}).get('exposure_monitor', {})
        self.exposure_currency = self.exposure_config.get('exposure_currency', 'USDT')
        self.track_assets = self.exposure_config.get('track_assets', [])
        self.conversion_methods = self.exposure_config.get('conversion_methods', {})
        
        # Initialize component-specific state
        self.current_exposure = {}
        self.last_calculation_timestamp = None
        self.exposure_history = []
        
        # Validate config
        self._validate_exposure_config()
    
    def _validate_exposure_config(self):
        """Validate exposure monitor config"""
        if not self.track_assets:
            raise ValueError("exposure_monitor.track_assets cannot be empty")
        
        for asset in self.track_assets:
            if asset not in self.conversion_methods:
                raise ValueError(f"Missing conversion method for asset: {asset}")
    
    def calculate_exposure(
        self,
        timestamp: pd.Timestamp,
        position_snapshot: Dict,
        market_data: Dict
    ) -> Dict:
        """
        Calculate exposure using config-driven asset tracking.
        MODE-AGNOSTIC - works for all strategy modes.
        """
        
        # Calculate exposure for each tracked asset
        asset_exposures = {}
        total_exposure = 0.0
        
        for asset in self.track_assets:
            asset_exposure = self._calculate_asset_exposure(
                asset, position_snapshot, market_data, timestamp
            )
            asset_exposures[asset] = asset_exposure
            total_exposure += asset_exposure['exposure_value']
        
        # Calculate net delta (sum of all asset deltas)
        net_delta = sum(exp['delta_exposure'] for exp in asset_exposures.values())
        
        return {
            'timestamp': timestamp,
            'exposure_currency': self.exposure_currency,
            'total_exposure': total_exposure,
            'net_delta': net_delta,
            'asset_exposures': asset_exposures,
            'tracked_assets': self.track_assets
        }
    
    def _calculate_asset_exposure(
        self,
        asset: str,
        position_snapshot: Dict,
        market_data: Dict,
        timestamp: pd.Timestamp
    ) -> Dict:
        """Calculate exposure for a specific asset using config-driven conversion"""
        
        # Get asset balance from position snapshot
        asset_balance = self._get_asset_balance(asset, position_snapshot)
        
        # Get conversion method from config
        conversion_method = self.conversion_methods[asset]
        
        # Convert to exposure currency
        if conversion_method == 'direct':
            exposure_value = asset_balance
            delta_exposure = asset_balance
        
        elif conversion_method == 'usd_price':
            price = market_data['market_data']['prices'].get(asset, 0.0)
            exposure_value = asset_balance * price
            delta_exposure = asset_balance  # Delta is in asset units
        
        elif conversion_method == 'eth_price':
            eth_price = market_data['market_data']['prices'].get('ETH', 0.0)
            exposure_value = asset_balance / eth_price if eth_price > 0 else 0.0
            delta_exposure = -asset_balance  # USDT is short ETH
        
        elif conversion_method == 'oracle_price':
            oracle_price = market_data['protocol_data']['oracle_prices'].get(asset, 0.0)
            underlying_balance = asset_balance * oracle_price
            exposure_value = underlying_balance
            delta_exposure = underlying_balance
        
        elif conversion_method == 'aave_index':
            # Handle AAVE token conversion (CRITICAL!)
            if asset.startswith('a'):  # Collateral token
                index = market_data['protocol_data']['aave_indexes'].get(asset, 0.0)
                underlying_balance = asset_balance * index
                
                # Get underlying token price
                underlying_token = asset[1:]  # Remove 'a' prefix
                if underlying_token in market_data['protocol_data']['oracle_prices']:
                    # LST token - use oracle price
                    oracle_price = market_data['protocol_data']['oracle_prices'][underlying_token]
                    eth_value = underlying_balance * oracle_price
                    exposure_value = eth_value * market_data['market_data']['prices'].get('ETH', 0.0)
                else:
                    # Regular token - use spot price
                    exposure_value = underlying_balance * market_data['market_data']['prices'].get(underlying_token, 0.0)
                
                delta_exposure = underlying_balance
            
            elif asset.startswith('variableDebt'):  # Debt token
                index = market_data['protocol_data']['aave_indexes'].get(asset, 0.0)
                underlying_balance = asset_balance * index
                underlying_token = asset.replace('variableDebt', '')
                exposure_value = underlying_balance * market_data['market_data']['prices'].get(underlying_token, 0.0)
                delta_exposure = -underlying_balance  # Debt is negative delta
        
        elif conversion_method == 'perp_mark_price':
            # Perpetual position value
            venue = self._extract_venue_from_asset(asset)  # e.g., 'binance' from 'binance_ETH_PERP'
            perp_mark = market_data['protocol_data']['perp_prices'].get(f'{venue}_eth_perp', 0.0)
            exposure_value = asset_balance * perp_mark
            delta_exposure = asset_balance  # Perp size is already in asset units
        
        elif conversion_method == 'unwrap':
            # Unwrap KING to EIGEN + ETHFI
            eigen_amount, ethfi_amount = self._unwrap_king(asset_balance)
            eigen_price = market_data['market_data']['prices'].get('EIGEN', 0.0)
            ethfi_price = market_data['market_data']['prices'].get('ETHFI', 0.0)
            exposure_value = (eigen_amount * eigen_price) + (ethfi_amount * ethfi_price)
            delta_exposure = 0.0  # Dust tokens don't contribute to delta
        
        else:
            raise ValueError(f"Unknown conversion method: {conversion_method}")
        
        return {
            'asset': asset,
            'balance': asset_balance,
            'exposure_value': exposure_value,
            'delta_exposure': delta_exposure,
            'conversion_method': conversion_method
        }
    
    def _get_asset_balance(self, asset: str, position_snapshot: Dict) -> float:
        """Get asset balance from position snapshot"""
        total_balance = 0.0
        
        # Check wallet
        if 'wallet' in position_snapshot:
            total_balance += position_snapshot['wallet'].get(asset, 0.0)
        
        # Check CEX accounts
        if 'cex_accounts' in position_snapshot:
            for venue, account in position_snapshot['cex_accounts'].items():
                total_balance += account.get(asset, 0.0)
        
        # Check perp positions
        if asset.endswith('_PERP') and 'perp_positions' in position_snapshot:
            venue = self._extract_venue_from_asset(asset)
            instrument = asset.replace(f'{venue}_', '')
            perp_position = position_snapshot['perp_positions'].get(venue, {}).get(instrument, {})
            total_balance += perp_position.get('size', 0.0)
        
        return total_balance
```

---

## **4. PNL CALCULATOR PATTERN (Mode-Agnostic)**

### **Complete Class Structure**

```python
class PnLCalculator:
    """Mode-agnostic PnL calculation using config-driven attribution"""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                 exposure_monitor: ExposureMonitor):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.exposure_monitor = exposure_monitor
        
        # Extract PnL-specific config
        self.pnl_config = config.get('component_config', {}).get('pnl_calculator', {})
        self.attribution_types = self.pnl_config.get('attribution_types', [])
        self.reporting_currency = self.pnl_config.get('reporting_currency', 'USDT')
        self.reconciliation_tolerance = self.pnl_config.get('reconciliation_tolerance', 0.02)
        
        # Initialize cumulative tracking for each attribution type
        self.cumulative_attributions = {attr_type: 0.0 for attr_type in self.attribution_types}
        
        # Store initial value for balance-based PnL
        self.initial_total_value = None
        
        # Validate config
        self._validate_pnl_config()
    
    def _validate_pnl_config(self):
        """Validate PnL calculator configuration"""
        if not self.attribution_types:
            raise ValueError("attribution_types cannot be empty")
        
        valid_attribution_types = [
            'supply_yield', 'staking_yield_oracle', 'staking_yield_rewards', 'borrow_costs',
            'funding_pnl', 'delta_pnl', 'basis_pnl', 'price_change_pnl', 'transaction_costs'
        ]
        
        for attr_type in self.attribution_types:
            if attr_type not in valid_attribution_types:
                raise ValueError(f"Invalid attribution type: {attr_type}")
    
    def get_current_pnl(
        self,
        current_exposure: Dict,
        previous_exposure: Optional[Dict],
        timestamp: pd.Timestamp,
        period_start: pd.Timestamp
    ) -> Dict:
        """
        Calculate PnL using config-driven attribution system.
        MODE-AGNOSTIC - works for all strategy modes.
        """
        
        # Set initial value if first calculation
        if self.initial_total_value is None:
            self.initial_total_value = current_exposure['share_class_value']
        
        # 1. Balance-Based PnL (source of truth)
        balance_pnl_data = self._calculate_balance_based_pnl(current_exposure, period_start, timestamp)
        
        # 2. Attribution PnL (config-driven breakdown)
        attribution_pnl_data = self._calculate_attribution_pnl(
            current_exposure, previous_exposure, timestamp
        )
        
        # 3. Reconciliation
        reconciliation = self._reconcile_pnl(
            balance_pnl_data, attribution_pnl_data, period_start, timestamp
        )
        
        return {
            'timestamp': timestamp,
            'share_class': self.reporting_currency,
            'balance_based': balance_pnl_data,
            'attribution': attribution_pnl_data,
            'reconciliation': reconciliation
        }
    
    def _calculate_attribution_pnl(
        self,
        current_exposure: Dict,
        previous_exposure: Optional[Dict],
        timestamp: pd.Timestamp
    ) -> Dict:
        """Calculate PnL attribution based on config-driven types"""
        
        if previous_exposure is None:
            return self._zero_attribution()
        
        # Calculate hourly PnL for each configured attribution type
        hourly_attributions = {}
        
        for attr_type in self.attribution_types:
            if attr_type == 'supply_yield':
                hourly_attributions[attr_type] = self._calc_supply_yield_pnl(current_exposure, previous_exposure)
            elif attr_type == 'staking_yield_oracle':
                hourly_attributions[attr_type] = self._calc_staking_yield_oracle_pnl(current_exposure, previous_exposure)
            elif attr_type == 'staking_yield_rewards':
                hourly_attributions[attr_type] = self._calc_staking_yield_rewards_pnl(current_exposure, previous_exposure)
            elif attr_type == 'borrow_costs':
                hourly_attributions[attr_type] = self._calc_borrow_costs_pnl(current_exposure, previous_exposure)
            elif attr_type == 'funding_pnl':
                hourly_attributions[attr_type] = self._calc_funding_pnl(current_exposure, previous_exposure, timestamp)
            elif attr_type == 'delta_pnl':
                hourly_attributions[attr_type] = self._calc_delta_pnl(current_exposure, previous_exposure)
            elif attr_type == 'basis_pnl':
                hourly_attributions[attr_type] = self._calc_basis_pnl(current_exposure, previous_exposure)
            elif attr_type == 'price_change_pnl':
                hourly_attributions[attr_type] = self._calc_price_change_pnl(current_exposure, previous_exposure)
            elif attr_type == 'transaction_costs':
                hourly_attributions[attr_type] = self._calc_transaction_costs_pnl(current_exposure, previous_exposure)
            else:
                # Unknown attribution type, return 0 (graceful handling)
                hourly_attributions[attr_type] = 0.0
        
        # Update cumulative attributions
        for attr_type, hourly_pnl in hourly_attributions.items():
            self.cumulative_attributions[attr_type] += hourly_pnl
        
        # Calculate totals
        hourly_total = sum(hourly_attributions.values())
        cumulative_total = sum(self.cumulative_attributions.values())
        
        return {
            'hourly': hourly_attributions,
            'cumulative': self.cumulative_attributions.copy(),
            'hourly_total': hourly_total,
            'cumulative_total': cumulative_total
        }
    
    def _calc_supply_yield_pnl(self, current_exposure: Dict, previous_exposure: Dict) -> float:
        """Calculate AAVE supply yield PnL"""
        if 'aave_indexes' not in current_exposure.get('protocol_data', {}):
            return 0.0  # No AAVE data available - graceful handling
        
        # Calculate yield from AAVE index growth
        current_indexes = current_exposure['protocol_data']['aave_indexes']
        previous_indexes = previous_exposure.get('protocol_data', {}).get('aave_indexes', {})
        
        total_yield = 0.0
        for token, current_index in current_indexes.items():
            if token.startswith('a'):  # Collateral token
                previous_index = previous_indexes.get(token, current_index)
                index_growth = current_index - previous_index
                
                # Get underlying balance from position
                underlying_balance = self._get_underlying_balance(token, current_exposure)
                yield_pnl = underlying_balance * index_growth
                total_yield += yield_pnl
        
        return total_yield
    
    def _calc_funding_pnl(self, current_exposure: Dict, previous_exposure: Dict, timestamp: pd.Timestamp) -> float:
        """Calculate funding PnL (only at funding times: 0, 8, 16 UTC)"""
        if timestamp.hour not in [0, 8, 16]:
            return 0.0  # Only calculate at funding times
        
        if 'perp_positions' not in current_exposure:
            return 0.0  # No perp positions - graceful handling
        
        total_funding_pnl = 0.0
        for venue, positions in current_exposure['perp_positions'].items():
            for instrument, position in positions.items():
                if position['size'] != 0:
                    # Get funding rate for this venue/instrument
                    funding_rate = self._get_funding_rate(venue, instrument, timestamp)
                    
                    # Calculate funding PnL
                    notional = abs(position['size']) * position['mark_price']
                    funding_pnl = notional * funding_rate * (1 if position['size'] > 0 else -1)
                    total_funding_pnl += funding_pnl
        
        return total_funding_pnl
    
    def _calc_delta_pnl(self, current_exposure: Dict, previous_exposure: Dict) -> float:
        """Calculate delta PnL from unhedged exposure"""
        if 'net_delta' not in current_exposure or 'net_delta' not in previous_exposure:
            return 0.0  # No delta data available - graceful handling
        
        # Calculate delta change
        current_delta = current_exposure['net_delta']
        previous_delta = previous_exposure['net_delta']
        delta_change = current_delta - previous_delta
        
        # Get asset price change
        asset = self.config.get('asset', 'ETH')
        current_price = current_exposure['market_data']['prices'].get(asset, 0.0)
        previous_price = previous_exposure['market_data']['prices'].get(asset, 0.0)
        price_change = current_price - previous_price
        
        # Delta PnL = delta change * price change
        delta_pnl = delta_change * price_change
        
        return delta_pnl
    
    def _zero_attribution(self) -> Dict:
        """Return zero attribution for first calculation"""
        return {
            'hourly': {attr_type: 0.0 for attr_type in self.attribution_types},
            'cumulative': {attr_type: 0.0 for attr_type in self.attribution_types},
            'hourly_total': 0.0,
            'cumulative_total': 0.0
        }
```

---

## **5. STRATEGY MANAGER PATTERN (Mode-Specific)**

### **Base Strategy Manager with Inheritance**

```python
from abc import ABC, abstractmethod

class BaseStrategyManager(ABC):
    """Base class for all strategy managers"""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                 exposure_monitor: ExposureMonitor, risk_monitor: RiskMonitor):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.exposure_monitor = exposure_monitor
        self.risk_monitor = risk_monitor
        
        # Extract strategy-specific config
        self.strategy_config = config.get('component_config', {}).get('strategy_manager', {})
        self.strategy_type = self.strategy_config.get('strategy_type')
        self.available_actions = self.strategy_config.get('actions', [])
        self.rebalancing_triggers = self.strategy_config.get('rebalancing_triggers', [])
        self.position_calculation = self.strategy_config.get('position_calculation', {})
    
    @abstractmethod
    def calculate_target_positions(self, current_exposure: Dict, market_data: Dict) -> Dict:
        """
        Calculate target positions based on strategy type.
        MUST be implemented by each strategy-specific subclass.
        """
        pass
    
    @abstractmethod
    def should_rebalance(self, current_exposure: Dict, current_positions: Dict, trigger: str) -> bool:
        """
        Determine if rebalancing is needed.
        MUST be implemented by each strategy-specific subclass.
        """
        pass

# Mode-specific implementations
class PureLendingStrategyManager(BaseStrategyManager):
    """Strategy manager for pure lending mode"""
    
    def calculate_target_positions(self, current_exposure: Dict, market_data: Dict) -> Dict:
        """Pure lending position calculation"""
        equity = current_exposure['total_exposure']
        
        # All equity to AAVE USDT supply
        return {
            'aave_usdt_supply': equity,
            'wallet_usdt': 0.0
        }
    
    def should_rebalance(self, current_exposure: Dict, current_positions: Dict, trigger: str) -> bool:
        """Check if rebalancing needed for pure lending"""
        if trigger not in self.rebalancing_triggers:
            return False
        
        # Only rebalance on deposits/withdrawals
        return trigger in ['deposit', 'withdrawal']

class BTCBasisStrategyManager(BaseStrategyManager):
    """Strategy manager for BTC basis mode"""
    
    def calculate_target_positions(self, current_exposure: Dict, market_data: Dict) -> Dict:
        """BTC basis position calculation"""
        equity = current_exposure['total_exposure']
        hedge_allocation = self.position_calculation.get('hedge_allocation', {})
        
        # Calculate target BTC spot position
        btc_price = market_data['market_data']['prices']['BTC']
        target_btc_spot = equity / btc_price
        
        # Calculate target perp short positions across venues
        target_perp_shorts = {}
        for venue, allocation in hedge_allocation.items():
            target_perp_shorts[venue] = -target_btc_spot * allocation
        
        return {
            'btc_spot_long': target_btc_spot,
            'btc_perp_shorts': target_perp_shorts
        }
    
    def should_rebalance(self, current_exposure: Dict, current_positions: Dict, trigger: str) -> bool:
        """Check if rebalancing needed for BTC basis"""
        if trigger not in self.rebalancing_triggers:
            return False
        
        # Check delta drift
        if trigger == 'delta_drift':
            delta_risk = current_exposure.get('net_delta', 0.0) / current_exposure.get('total_exposure', 1.0)
            delta_tolerance = self.config.get('delta_tolerance', 0.005)
            return abs(delta_risk) > delta_tolerance
        
        return True  # Always rebalance for deposits/withdrawals
```

### **Strategy Manager Factory**

```python
class StrategyManagerFactory:
    """Factory for creating strategy-specific managers"""
    
    @staticmethod
    def create(config: Dict, data_provider: BaseDataProvider, execution_mode: str,
              exposure_monitor: ExposureMonitor, risk_monitor: RiskMonitor) -> BaseStrategyManager:
        """Create strategy manager based on config"""
        strategy_type = config.get('component_config', {}).get('strategy_manager', {}).get('strategy_type')
        
        strategy_map = {
            'pure_lending': PureLendingStrategyManager,
            'btc_basis': BTCBasisStrategyManager,
            'eth_basis': ETHBasisStrategyManager,
            'eth_staking_only': ETHStakingOnlyStrategyManager,
            'eth_leveraged': ETHLeveragedStrategyManager,
            'usdt_market_neutral_no_leverage': USDTMarketNeutralNoLeverageStrategyManager,
            'usdt_market_neutral': USDTMarketNeutralStrategyManager
        }
        
        if strategy_type not in strategy_map:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        return strategy_map[strategy_type](config, data_provider, execution_mode, exposure_monitor, risk_monitor)
```

---

## **6. EXECUTION MANAGER PATTERN (Config-Driven)**

### **Complete Class Structure**

```python
class VenueManager:
    """Mode-agnostic execution manager using config-driven action mapping"""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                 execution_interface_manager: VenueInterfaceManager):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.execution_interface_manager = execution_interface_manager
        
        # Extract execution-specific config
        self.execution_config = config.get('component_config', {}).get('execution_manager', {})
        self.supported_actions = self.execution_config.get('supported_actions', [])
        self.action_mapping = self.execution_config.get('action_mapping', {})
        
        # Validate config
        self._validate_execution_config()
    
    def _validate_execution_config(self):
        """Validate execution manager configuration"""
        if not self.supported_actions:
            raise ValueError("supported_actions cannot be empty")
        
        if not self.action_mapping:
            raise ValueError("action_mapping cannot be empty")
        
        # Validate that all mapped actions are supported
        for strategy_action, execution_actions in self.action_mapping.items():
            for exec_action in execution_actions:
                if exec_action not in self.supported_actions:
                    raise ValueError(f"Action mapping references unsupported action: {exec_action}")
    
    def execute_strategy_action(self, action_type: str, action_params: Dict) -> Dict:
        """
        Execute strategy action using config-driven mapping.
        MODE-AGNOSTIC - works for all strategy modes.
        """
        
        if action_type not in self.action_mapping:
            raise ValueError(f"Unsupported action type: {action_type}")
        
        # Get action sequence from config
        action_sequence = self.action_mapping[action_type]
        
        # Execute actions in sequence
        results = []
        for action in action_sequence:
            if action not in self.supported_actions:
                raise ValueError(f"Unsupported action: {action}")
            
            result = self._execute_action(action, action_params)
            results.append(result)
        
        return {
            'action_type': action_type,
            'action_sequence': action_sequence,
            'results': results,
            'success': all(r['success'] for r in results)
        }
    
    def _execute_action(self, action: str, params: Dict) -> Dict:
        """Execute individual action via execution interface manager"""
        if action.startswith('aave_'):
            return self.execution_interface_manager.execute_aave_action(action, params)
        elif action.startswith('cex_'):
            return self.execution_interface_manager.execute_cex_action(action, params)
        elif action.startswith('etherfi_'):
            return self.execution_interface_manager.execute_etherfi_action(action, params)
        elif action.startswith('lido_'):
            return self.execution_interface_manager.execute_lido_action(action, params)
        elif action == 'sell_dust':
            return self.execution_interface_manager.execute_dust_action(action, params)
        elif action == 'flash_loan':
            return self.execution_interface_manager.execute_flash_loan_action(action, params)
        else:
            raise ValueError(f"Unknown action type: {action}")
```

---

## **7. EXECUTION INTERFACE MANAGER PATTERN (Mode-Agnostic)**

### **Complete Class Structure**

```python
class VenueInterfaceManager:
    """Mode-agnostic execution interface manager"""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Initialize venue-specific interfaces
        self.venue_interfaces = self._initialize_venue_interfaces()
    
    def _initialize_venue_interfaces(self) -> Dict:
        """Initialize venue interfaces based on config"""
        interfaces = {}
        
        # Get required venues from config
        required_venues = self._get_required_venues()
        
        for venue in required_venues:
            if venue == 'aave':
                interfaces[venue] = AAVEInterface(self.config, self.execution_mode)
            elif venue in ['binance', 'bybit', 'okx']:
                interfaces[venue] = CEXInterface(venue, self.config, self.execution_mode)
            elif venue == 'etherfi':
                interfaces[venue] = EtherFiInterface(self.config, self.execution_mode)
            elif venue == 'lido':
                interfaces[venue] = LidoInterface(self.config, self.execution_mode)
            # ... etc
        
        return interfaces
    
    def _get_required_venues(self) -> List[str]:
        """Determine required venues from config flags"""
        venues = []
        
        if self.config.get('lending_enabled') or self.config.get('borrowing_enabled'):
            venues.append('aave')
        
        if self.config.get('staking_enabled'):
            lst_type = self.config.get('lst_type')
            if lst_type == 'weeth':
                venues.append('etherfi')
            elif lst_type == 'wsteth':
                venues.append('lido')
        
        if self.config.get('basis_trade_enabled'):
            venues.extend(self.config.get('hedge_venues', []))
        
        return list(set(venues))  # Remove duplicates
    
    def execute_aave_action(self, action: str, params: Dict) -> Dict:
        """Execute AAVE action"""
        aave_interface = self.venue_interfaces.get('aave')
        if not aave_interface:
            raise ValueError("AAVE interface not initialized")
        
        if action == 'aave_supply':
            return aave_interface.supply(params['asset'], params['amount'])
        elif action == 'aave_withdraw':
            return aave_interface.withdraw(params['asset'], params['amount'])
        elif action == 'aave_borrow':
            return aave_interface.borrow(params['asset'], params['amount'])
        elif action == 'aave_repay':
            return aave_interface.repay(params['asset'], params['amount'])
        else:
            raise ValueError(f"Unknown AAVE action: {action}")
    
    def execute_cex_action(self, action: str, params: Dict) -> Dict:
        """Execute CEX action"""
        venue = params['venue']
        cex_interface = self.venue_interfaces.get(venue)
        if not cex_interface:
            raise ValueError(f"CEX interface for {venue} not initialized")
        
        if action == 'cex_spot_buy':
            return cex_interface.spot_buy(params['symbol'], params['amount'])
        elif action == 'cex_spot_sell':
            return cex_interface.spot_sell(params['symbol'], params['amount'])
        elif action == 'cex_perp_short':
            return cex_interface.perp_short(params['symbol'], params['amount'])
        elif action == 'cex_perp_close':
            return cex_interface.perp_close(params['symbol'], params['amount'])
        elif action == 'cex_margin_add':
            return cex_interface.margin_add(params['amount'])
        else:
            raise ValueError(f"Unknown CEX action: {action}")
```

---

## **8. RESULTS STORE PATTERN (Config-Driven)**

### **Complete Class Structure**

```python
class ResultsStore:
    """Mode-agnostic results store using config-driven result types"""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Extract results-specific config
        self.results_config = config.get('component_config', {}).get('results_store', {})
        self.result_types = self.results_config.get('result_types', [])
        self.balance_sheet_assets = self.results_config.get('balance_sheet_assets', [])
        self.pnl_attribution_types = self.results_config.get('pnl_attribution_types', [])
        self.delta_tracking_assets = self.results_config.get('delta_tracking_assets', [])
        self.funding_tracking_venues = self.results_config.get('funding_tracking_venues', [])
        self.leverage_tracking = self.results_config.get('leverage_tracking', False)
        self.dust_tracking_tokens = self.results_config.get('dust_tracking_tokens', [])
        
        # Initialize result storage
        self.results = {}
    
    def store_results(self, timestamp: pd.Timestamp, component_data: Dict) -> Dict:
        """
        Store results based on config-driven result types.
        MODE-AGNOSTIC - only stores result types specified in config.
        """
        
        stored_results = {}
        
        for result_type in self.result_types:
            if result_type == 'balance_sheet':
                stored_results[result_type] = self._store_balance_sheet(timestamp, component_data)
            elif result_type == 'pnl_attribution':
                stored_results[result_type] = self._store_pnl_attribution(timestamp, component_data)
            elif result_type == 'risk_metrics':
                stored_results[result_type] = self._store_risk_metrics(timestamp, component_data)
            elif result_type == 'execution_log':
                stored_results[result_type] = self._store_execution_log(timestamp, component_data)
            elif result_type == 'delta_tracking':
                stored_results[result_type] = self._store_delta_tracking(timestamp, component_data)
            elif result_type == 'funding_tracking':
                stored_results[result_type] = self._store_funding_tracking(timestamp, component_data)
            elif result_type == 'leverage_tracking':
                stored_results[result_type] = self._store_leverage_tracking(timestamp, component_data)
            elif result_type == 'dust_tracking':
                stored_results[result_type] = self._store_dust_tracking(timestamp, component_data)
        
        return stored_results
    
    def _store_balance_sheet(self, timestamp: pd.Timestamp, component_data: Dict) -> Dict:
        """Store balance sheet data for configured assets"""
        balance_sheet = {}
        
        for asset in self.balance_sheet_assets:
            # Extract balance data from component data
            balance_sheet[asset] = self._extract_asset_balance(asset, component_data)
        
        return {
            'timestamp': timestamp,
            'assets': balance_sheet,
            'total_value': sum(balance_sheet.values())
        }
    
    def _store_pnl_attribution(self, timestamp: pd.Timestamp, component_data: Dict) -> Dict:
        """Store PnL attribution data for configured types"""
        attribution = {}
        
        for attr_type in self.pnl_attribution_types:
            # Extract attribution data from component data
            attribution[attr_type] = self._extract_attribution_data(attr_type, component_data)
        
        return {
            'timestamp': timestamp,
            'attribution': attribution,
            'total_pnl': sum(attribution.values())
        }
    
    def _store_delta_tracking(self, timestamp: pd.Timestamp, component_data: Dict) -> Optional[Dict]:
        """Store delta tracking data (only for modes that need it)"""
        if not self.delta_tracking_assets:
            return None  # No delta tracking for this mode - graceful handling
        
        delta_data = {}
        for asset in self.delta_tracking_assets:
            delta_data[asset] = self._extract_delta_data(asset, component_data)
        
        return {
            'timestamp': timestamp,
            'delta_data': delta_data,
            'net_delta': sum(delta_data.values())
        }
```

---

## **9. RECONCILIATION COMPONENT PATTERN (Mode-Agnostic)**

### **Complete Class Structure**

```python
class ReconciliationComponent:
    """Mode-agnostic reconciliation component"""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                 position_monitor: PositionMonitor):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.position_monitor = position_monitor
        
        # Reconciliation is the same for all modes
        self.reconciliation_tolerance = 0.01  # 1% tolerance
    
    def reconcile_position(self, expected_position: Dict, actual_position: Dict) -> Dict:
        """
        Reconcile expected vs actual position.
        MODE-AGNOSTIC - same logic for all strategy modes.
        """
        
        reconciliation_results = {}
        
        for asset, expected_amount in expected_position.items():
            actual_amount = actual_position.get(asset, 0.0)
            difference = abs(expected_amount - actual_amount)
            tolerance = abs(expected_amount) * self.reconciliation_tolerance
            
            reconciliation_results[asset] = {
                'expected': expected_amount,
                'actual': actual_amount,
                'difference': difference,
                'tolerance': tolerance,
                'passed': difference <= tolerance
            }
        
        overall_success = all(r['passed'] for r in reconciliation_results.values())
        
        return {
            'success': overall_success,
            'reconciliation_results': reconciliation_results,
            'tolerance': self.reconciliation_tolerance
        }
```

---

## **10. COMPONENT FACTORY PATTERN**

### **Complete ComponentFactory with Full Signatures**

```python
class ComponentFactory:
    """Factory for creating all components with config validation"""
    
    @staticmethod
    def create_all(config: Dict, data_provider: BaseDataProvider, execution_mode: str) -> Dict[str, Any]:
        """
        Create all components with config validation.
        Components created in dependency order to satisfy component references.
        """
        components = {}
        
        # Create components in dependency order
        # 1. Position Monitor (no dependencies on other components)
        components['position_monitor'] = ComponentFactory.create_position_monitor(
            config, data_provider, execution_mode
        )
        
        # 2. Exposure Monitor (depends on position_monitor)
        components['exposure_monitor'] = ComponentFactory.create_exposure_monitor(
            config, data_provider, execution_mode, 
            position_monitor=components['position_monitor']
        )
        
        # 3. Risk Monitor (depends on position_monitor, exposure_monitor)
        components['risk_monitor'] = ComponentFactory.create_risk_monitor(
            config, data_provider, execution_mode,
            position_monitor=components['position_monitor'],
            exposure_monitor=components['exposure_monitor']
        )
        
        # 4. PnL Calculator (depends on exposure_monitor)
        components['pnl_calculator'] = ComponentFactory.create_pnl_calculator(
            config, data_provider, execution_mode,
            exposure_monitor=components['exposure_monitor']
        )
        
        # 5. Execution Interface Manager (no component dependencies)
        components['execution_interface_manager'] = ComponentFactory.create_execution_interface_manager(
            config, data_provider, execution_mode
        )
        
        # 6. Execution Manager (depends on execution_interface_manager)
        components['execution_manager'] = ComponentFactory.create_execution_manager(
            config, data_provider, execution_mode,
            execution_interface_manager=components['execution_interface_manager']
        )
        
        # 7. Strategy Manager (depends on exposure_monitor, risk_monitor) - MODE-SPECIFIC
        components['strategy_manager'] = ComponentFactory.create_strategy_manager(
            config, data_provider, execution_mode,
            exposure_monitor=components['exposure_monitor'],
            risk_monitor=components['risk_monitor']
        )
        
        # 8. Reconciliation Component (depends on position_monitor)
        components['reconciliation_component'] = ComponentFactory.create_reconciliation_component(
            config, data_provider, execution_mode,
            position_monitor=components['position_monitor']
        )
        
        # 9. Results Store (no component dependencies)
        components['results_store'] = ComponentFactory.create_results_store(
            config, data_provider, execution_mode
        )
        
        # 10. Event Logger (no component dependencies)
        components['event_logger'] = ComponentFactory.create_event_logger(
            config, execution_mode
        )
        
        # 11. Position Update Handler (depends on position_monitor, exposure_monitor, risk_monitor, pnl_calculator)
        components['position_update_handler'] = ComponentFactory.create_position_update_handler(
            config, data_provider, execution_mode,
            position_monitor=components['position_monitor'],
            exposure_monitor=components['exposure_monitor'],
            risk_monitor=components['risk_monitor'],
            pnl_calculator=components['pnl_calculator']
        )
        
        return components
    
    @staticmethod
    def create_position_monitor(config: Dict, data_provider: BaseDataProvider, execution_mode: str) -> PositionMonitor:
        """Create Position Monitor - mode-agnostic (only cares about backtest vs live)"""
        # No component config needed - already mode-agnostic
        return PositionMonitor(config, data_provider, execution_mode)
    
    @staticmethod
    def create_exposure_monitor(config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                                position_monitor: PositionMonitor) -> ExposureMonitor:
        """Create Exposure Monitor with config validation"""
        # Extract exposure monitor specific config
        exposure_config = config.get('component_config', {}).get('exposure_monitor', {})
        
        # Validate required config
        required_fields = ['exposure_currency', 'track_assets', 'conversion_methods']
        for field in required_fields:
            if field not in exposure_config:
                raise ValueError(f"Missing required config for exposure_monitor: {field}")
        
        # Validate all tracked assets have conversion methods
        track_assets = exposure_config.get('track_assets', [])
        conversion_methods = exposure_config.get('conversion_methods', {})
        for asset in track_assets:
            if asset not in conversion_methods:
                raise ValueError(f"Missing conversion method for asset: {asset}")
        
        # Create component
        return ExposureMonitor(config, data_provider, execution_mode, position_monitor)
    
    @staticmethod
    def create_risk_monitor(config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                           position_monitor: PositionMonitor, exposure_monitor: ExposureMonitor) -> RiskMonitor:
        """Create Risk Monitor with config validation"""
        # Extract risk monitor specific config
        risk_config = config.get('component_config', {}).get('risk_monitor', {})
        
        # Validate required config
        required_fields = ['enabled_risk_types', 'risk_limits']
        for field in required_fields:
            if field not in risk_config:
                raise ValueError(f"Missing required config for risk_monitor: {field}")
        
        # Validate risk types
        valid_risk_types = [
            'ltv_risk', 'liquidation_risk',  # AAVE risks (2 types)
            'cex_margin_ratio', 'delta_risk'  # CEX and delta risks (2 types)
        ]  # Total: 4 core risk types
        for risk_type in risk_config.get('enabled_risk_types', []):
            if risk_type not in valid_risk_types:
                raise ValueError(f"Invalid risk type: {risk_type}")
        
        # Create component
        return RiskMonitor(config, data_provider, execution_mode, position_monitor, exposure_monitor)
    
    @staticmethod
    def create_pnl_calculator(config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                             exposure_monitor: ExposureMonitor) -> PnLCalculator:
        """Create PnL Calculator with config validation"""
        # Extract PnL calculator specific config
        pnl_config = config.get('component_config', {}).get('pnl_calculator', {})
        
        # Validate required config
        required_fields = ['attribution_types', 'reporting_currency', 'reconciliation_tolerance']
        for field in required_fields:
            if field not in pnl_config:
                raise ValueError(f"Missing required config for pnl_calculator: {field}")
        
        # Validate attribution types
        valid_attribution_types = [
            'supply_yield', 'staking_yield_oracle', 'staking_yield_rewards', 'borrow_costs',
            'funding_pnl', 'delta_pnl', 'basis_pnl', 'price_change_pnl', 'transaction_costs'
        ]
        for attr_type in pnl_config.get('attribution_types', []):
            if attr_type not in valid_attribution_types:
                raise ValueError(f"Invalid attribution type: {attr_type}")
        
        # Create component
        return PnLCalculator(config, data_provider, execution_mode, exposure_monitor)
    
    @staticmethod
    def create_strategy_manager(config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                                exposure_monitor: ExposureMonitor, risk_monitor: RiskMonitor) -> BaseStrategyManager:
        """Create Strategy Manager using StrategyManagerFactory (MODE-SPECIFIC)"""
        # Use StrategyManagerFactory for mode-specific creation
        return StrategyManagerFactory.create(config, data_provider, execution_mode, exposure_monitor, risk_monitor)
    
    @staticmethod
    def create_execution_interface_manager(config: Dict, data_provider: BaseDataProvider, execution_mode: str) -> VenueInterfaceManager:
        """Create Execution Interface Manager - mode-agnostic venue routing"""
        # No component config validation needed - mode-agnostic
        return VenueInterfaceManager(config, data_provider, execution_mode)
    
    @staticmethod
    def create_execution_manager(config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                                 execution_interface_manager: VenueInterfaceManager) -> ExecutionManager:
        """Create Execution Manager with config validation"""
        # Extract execution manager specific config
        exec_config = config.get('component_config', {}).get('execution_manager', {})
        
        # Validate required config
        required_fields = ['supported_actions', 'action_mapping']
        for field in required_fields:
            if field not in exec_config:
                raise ValueError(f"Missing required config for execution_manager: {field}")
        
        # Validate action mapping references supported actions
        action_mapping = exec_config.get('action_mapping', {})
        supported_actions = exec_config.get('supported_actions', [])
        for strategy_action, execution_actions in action_mapping.items():
            for exec_action in execution_actions:
                if exec_action not in supported_actions:
                    raise ValueError(f"Action mapping '{strategy_action}' references unsupported action: {exec_action}")
        
        # Create component
        return ExecutionManager(config, data_provider, execution_mode, execution_interface_manager)
    
    @staticmethod
    def create_reconciliation_component(config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                                        position_monitor: PositionMonitor) -> ReconciliationComponent:
        """Create Reconciliation Component - mode-agnostic"""
        # No component config validation needed - mode-agnostic with simple tolerance
        return ReconciliationComponent(config, data_provider, execution_mode, position_monitor)
    
    @staticmethod
    def create_results_store(config: Dict, data_provider: BaseDataProvider, execution_mode: str) -> ResultsStore:
        """Create Results Store with config validation"""
        # Extract results store specific config
        results_config = config.get('component_config', {}).get('results_store', {})
        
        # Validate required config
        required_fields = ['result_types', 'balance_sheet_assets', 'pnl_attribution_types']
        for field in required_fields:
            if field not in results_config:
                raise ValueError(f"Missing required config for results_store: {field}")
        
        # Validate result types
        valid_result_types = [
            'balance_sheet', 'pnl_attribution', 'risk_metrics', 'execution_log',
            'delta_tracking', 'funding_tracking', 'leverage_tracking', 'dust_tracking'
        ]
        for result_type in results_config.get('result_types', []):
            if result_type not in valid_result_types:
                raise ValueError(f"Invalid result type: {result_type}")
        
        # Create component
        return ResultsStore(config, data_provider, execution_mode)
    
    @staticmethod
    def create_event_logger(config: Dict, execution_mode: str) -> EventLogger:
        """Create Event Logger - mode-agnostic"""
        # No component config needed - mode-agnostic
        return EventLogger(config, execution_mode)
    
    @staticmethod
    def create_position_update_handler(config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                                       position_monitor: PositionMonitor, exposure_monitor: ExposureMonitor,
                                       risk_monitor: RiskMonitor, pnl_calculator: PnLCalculator) -> PositionUpdateHandler:
        """Create Position Update Handler - mode-agnostic tight loop orchestrator"""
        # No component config needed - mode-agnostic
        return PositionUpdateHandler(
            config, data_provider, execution_mode,
            position_monitor, exposure_monitor, risk_monitor, pnl_calculator
        )
```

### **CRITICAL: Config Key Alignment**

**IMPORTANT**: Use `config['mode']` NOT `config['mode']`:

```python
# ✅ CORRECT
mode = config['mode']  # From mode YAML

# ❌ WRONG
mode = config['mode']  # This key doesn't exist in YAML!
```

**Reason**: All mode YAML files use `mode: "pure_lending"`, not `mode:`

**ADR Reference**: ADR-055 (Component factory validation)

---

## **11. CONFIG VALIDATION PATTERNS**

### **ConfigValidator Class**

```python
class ConfigValidator:
    """Validates config completeness and consistency"""
    
    @staticmethod
    def validate_mode_config(config: Dict) -> List[str]:
        """
        Validate that config has all required fields for the mode.
        Returns list of error messages (empty if valid).
        """
        errors = []
        
        # Validate required top-level fields
        required_fields = ['mode', 'share_class', 'asset', 'data_requirements', 'component_config']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Validate data requirements
        data_requirements = config.get('data_requirements', [])
        if not data_requirements:
            errors.append("No data requirements specified")
        
        # Validate component config completeness
        component_config = config.get('component_config', {})
        required_components = ['risk_monitor', 'exposure_monitor', 'pnl_calculator', 'strategy_manager', 'execution_manager', 'results_store']
        for component_name in required_components:
            if component_name not in component_config:
                errors.append(f"Missing component config: {component_name}")
            else:
                errors.extend(ConfigValidator._validate_component_config(component_name, component_config[component_name]))
        
        # Business logic validation
        errors.extend(ConfigValidator._validate_business_logic(config))
        
        return errors
    
    @staticmethod
    def _validate_component_config(component_name: str, component_config: Dict) -> List[str]:
        """Validate component-specific config"""
        errors = []
        
        if component_name == 'risk_monitor':
            if 'enabled_risk_types' not in component_config:
                errors.append("risk_monitor missing enabled_risk_types")
            if 'risk_limits' not in component_config:
                errors.append("risk_monitor missing risk_limits")
        
        elif component_name == 'exposure_monitor':
            if 'exposure_currency' not in component_config:
                errors.append("exposure_monitor missing exposure_currency")
            if 'track_assets' not in component_config:
                errors.append("exposure_monitor missing track_assets")
            if 'conversion_methods' not in component_config:
                errors.append("exposure_monitor missing conversion_methods")
            else:
                # Validate all tracked assets have conversion methods
                track_assets = component_config.get('track_assets', [])
                conversion_methods = component_config['conversion_methods']
                for asset in track_assets:
                    if asset not in conversion_methods:
                        errors.append(f"exposure_monitor missing conversion method for asset: {asset}")
        
        elif component_name == 'pnl_calculator':
            if 'attribution_types' not in component_config:
                errors.append("pnl_calculator missing attribution_types")
            if 'reporting_currency' not in component_config:
                errors.append("pnl_calculator missing reporting_currency")
            if 'reconciliation_tolerance' not in component_config:
                errors.append("pnl_calculator missing reconciliation_tolerance")
        
        elif component_name == 'strategy_manager':
            if 'strategy_type' not in component_config:
                errors.append("strategy_manager missing strategy_type")
            if 'actions' not in component_config:
                errors.append("strategy_manager missing actions")
            if 'rebalancing_triggers' not in component_config:
                errors.append("strategy_manager missing rebalancing_triggers")
            if 'position_calculation' not in component_config:
                errors.append("strategy_manager missing position_calculation")
        
        elif component_name == 'execution_manager':
            if 'supported_actions' not in component_config:
                errors.append("execution_manager missing supported_actions")
            if 'action_mapping' not in component_config:
                errors.append("execution_manager missing action_mapping")
        
        elif component_name == 'results_store':
            if 'result_types' not in component_config:
                errors.append("results_store missing result_types")
            if 'balance_sheet_assets' not in component_config:
                errors.append("results_store missing balance_sheet_assets")
            if 'pnl_attribution_types' not in component_config:
                errors.append("results_store missing pnl_attribution_types")
        
        return errors
    
    @staticmethod
    def _validate_business_logic(config: Dict) -> List[str]:
        """Validate business logic constraints"""
        errors = []
        
        # Validate share_class vs asset consistency
        if config.get('share_class') != config.get('asset'):
            # Cross-currency modes must have hedging
            if not config.get('basis_trade_enabled', False):
                errors.append(f"Mode with share_class={config['share_class']} and asset={config['asset']} must have basis_trade_enabled=true")
        
        # Validate leverage requires borrowing
        if config.get('max_ltv', 0) > 0 and not config.get('borrowing_enabled', False):
            errors.append("max_ltv > 0 requires borrowing_enabled=true")
        
        # Validate staking requires lst_type
        if config.get('staking_enabled', False) and not config.get('lst_type'):
            errors.append("staking_enabled=true requires lst_type")
        
        # Validate hedge allocation sums to 1.0
        if config.get('basis_trade_enabled', False):
            total_allocation = (
                config.get('hedge_allocation_binance', 0.0) +
                config.get('hedge_allocation_bybit', 0.0) +
                config.get('hedge_allocation_okx', 0.0)
            )
            if not (0.99 <= total_allocation <= 1.01):
                errors.append(f"Hedge allocations must sum to 1.0, got {total_allocation}")
        
        return errors
```

---

## **12. SERVICE LAYER PATTERNS**

### **BacktestService with Config-Driven Initialization**

```python
class BacktestService:
    """Backtest service using config-driven architecture"""
    
    def __init__(self, global_config: Dict):
        self.global_config = global_config  # Immutable, validated at startup
    
    async def run_backtest(self, request: BacktestRequest) -> str:
        """
        Complete config-driven initialization flow:
        
        1. Load strategy config
        2. Apply overrides
        3. Validate config
        4. Create data provider (validates data requirements)
        5. Create components (validates component config)
        6. Run backtest
        """
        
        # Step 1: Load config for strategy mode
        config = self._load_strategy_config(request.mode)
        
        # Step 2: Apply config overrides (if any)
        if request.config_overrides:
            config = self._apply_config_overrides(config, request.config_overrides)
        
        # Step 3: Validate complete config
        errors = ConfigValidator.validate_mode_config(config)
        if errors:
            raise ValueError(f"Config validation failed: {errors}")
        
        # Step 4: Create data provider (validates data requirements)
        data_provider = DataProviderFactory.create('backtest', config)
        
        # Step 5: Validate data provider compatibility
        provider_errors = ConfigValidator.validate_data_provider_compatibility(config, data_provider)
        if provider_errors:
            raise ValueError(f"DataProvider validation failed: {provider_errors}")
        
        # Step 6: Load data for backtest period
        data_provider.load_data(request.start_date, request.end_date)
        
        # Step 7: Create components (validates component config)
        components = ComponentFactory.create_all(config, data_provider, 'backtest')
        
        # Step 8: Create event engine and run backtest
        engine = EventDrivenStrategyEngine(config, 'backtest', data_provider, components)
        results = await engine.run_backtest(request.start_date, request.end_date)
        
        return results
```

---

## **13. EVENT DRIVEN STRATEGY ENGINE PATTERN (Unchanged)**

### **Complete Class Structure**

```python
class EventDrivenStrategyEngine:
    """Event driven strategy engine - UNCHANGED by mode-agnostic architecture"""
    
    def __init__(self, config: Dict, execution_mode: str, data_provider: BaseDataProvider, components: Dict):
        self.config = config
        self.execution_mode = execution_mode
        self.data_provider = data_provider
        self.components = components
        self.current_timestamp = None
        self.timestamps = []
    
    def run_backtest(self, start_date: str, end_date: str):
        """Run backtest with config-driven components"""
        self.timestamps = self.data_provider.get_timestamps(start_date, end_date)
        
        for timestamp in self.timestamps:
            self.current_timestamp = timestamp
            self._process_timestep(timestamp)
    
    def _process_timestep(self, timestamp: pd.Timestamp):
        """
        Process single timestep - UNCHANGED sequence.
        Components determine their behavior from config.
        """
        # Same sequence for all modes
        self.components['position_monitor'].update_state(timestamp, 'full_loop')
        self.components['exposure_monitor'].update_state(timestamp, 'full_loop')
        self.components['risk_monitor'].update_state(timestamp, 'full_loop')
        self.components['strategy_manager'].update_state(timestamp, 'full_loop')
        self.components['execution_manager'].update_state(timestamp, 'full_loop')
        self.components['pnl_calculator'].update_state(timestamp, 'full_loop')
        self.components['results_store'].update_state(timestamp, 'full_loop')
```

---

## **14. KEY PATTERNS SUMMARY**

### **Mode-Agnostic Component Pattern**

```python
class ModeAgnosticComponent:
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str, **component_refs):
        # 1. Store references
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # 2. Extract component-specific config
        self.component_config = config.get('component_config', {}).get('component_name', {})
        self.config_param_1 = self.component_config.get('param_1', [])
        self.config_param_2 = self.component_config.get('param_2', {})
        
        # 3. Validate config
        self._validate_config()
    
    def process(self, data: Dict) -> Dict:
        # 4. Use config to drive behavior (NO mode-specific logic!)
        results = {}
        
        for item in self.config_param_1:
            if item in data:
                results[item] = self._process_item(item, data)
            else:
                results[item] = None  # Graceful handling of missing data
        
        return results
```

### **Mode-Specific Component Pattern**

```python
class ModeSpecificComponent(ABC):
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str):
        self.config = config
        self.strategy_type = config.get('component_config', {}).get('component_name', {}).get('strategy_type')
    
    @abstractmethod
    def calculate_strategy_specific_logic(self, data: Dict) -> Dict:
        """Each mode implements differently"""
        pass

class ModeAStrategyManager(ModeSpecificComponent):
    def calculate_strategy_specific_logic(self, data: Dict) -> Dict:
        # Mode A specific logic
        return {...}

class ModeBStrategyManager(ModeSpecificComponent):
    def calculate_strategy_specific_logic(self, data: Dict) -> Dict:
        # Mode B specific logic
        return {...}
```

---

## **Cross-References**

### **Configuration**
- **Full Config Schemas**: [19_CONFIGURATION.md](specs/19_CONFIGURATION.md)
- **Config Validation**: [19_CONFIGURATION.md#config-driven-validation](specs/19_CONFIGURATION.md#config-driven-validation)

### **Architecture**
- **Config-Driven Architecture**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) Section II
- **Reference Architecture**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md)

### **Component Specs**
- All component specs in [docs/specs/](specs/) reference these patterns

---

**Usage**: When implementing or refactoring components, use these exact patterns for consistency across the codebase.


