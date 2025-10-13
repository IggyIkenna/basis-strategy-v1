⚠️ **WARNING: OUTDATED PATTERNS - DO NOT USE FOR IMPLEMENTATION**

**Date**: October 11, 2025  
**Status**: 🔴 **SUPERSEDED** - This file contains conversation notes with OUTDATED code patterns

**USE THESE INSTEAD** (Correct, up-to-date versions):
- ✅ **CODE_STRUCTURE_PATTERNS.md** - SINGLE SOURCE OF TRUTH for all code structures
- ✅ **19_CONFIGURATION.md** - Complete config schemas for all 7 modes
- ✅ **MODE_AGNOSTIC_ARCHITECTURE_GUIDE.md** - Architectural approach
- ✅ **AGENT_REFACTOR_PROMPT_MODE_AGNOSTIC.md** - Complete refactor instructions

**KNOWN ISSUES IN THIS FILE**:
1. ❌ Uses `config['mode']` - CORRECT is `config['mode']`
2. ❌ Uses `BaseDataProvider` type - CORRECT is `BaseDataProvider`
3. ❌ Missing component references in __init__ signatures
4. ❌ Missing graceful data handling in calculation methods
5. ❌ Missing config validation in __init__

**KEEP THIS FILE FOR**:
- Historical conversation notes
- Problem statement context

**DO NOT USE THIS FILE FOR**:
- Implementation patterns (use CODE_STRUCTURE_PATTERNS.md)
- Config structures (use 19_CONFIGURATION.md)
- Component signatures (use CODE_STRUCTURE_PATTERNS.md)

---

**ORIGINAL USER NOTES BELOW** (contains outdated patterns):

---



5. Config-Driven Component Initialization
Components are initialized with their specific config requirements:

class ComponentFactory:
    """Creates components with config-driven behavior"""
    
    @staticmethod
    def create_risk_monitor(config: Dict, data_provider: DataProvider, execution_mode: str) -> RiskMonitor:
        # Extract risk monitor specific config
        risk_config = config.get('component_config', {}).get('risk_monitor', {})
        
        # Validate required config
        required_fields = ['enabled_risk_types', 'risk_limits']
        for field in required_fields:
            if field not in risk_config:
                raise ValueError(f"Missing required config for risk_monitor: {field}")
        
        return RiskMonitor(config, data_provider, execution_mode)
    
    @staticmethod
    def create_exposure_monitor(config: Dict, data_provider: DataProvider, execution_mode: str) -> ExposureMonitor:
        # Extract exposure monitor specific config
        exposure_config = config.get('component_config', {}).get('exposure_monitor', {})
        
        # Validate required config
        required_fields = ['exposure_currency', 'track_assets']
        for field in required_fields:
            if field not in exposure_config:
                raise ValueError(f"Missing required config for exposure_monitor: {field}")
        
        return ExposureMonitor(config, data_provider, execution_mode)

you said 

class ConfigValidator:
    """Validates config completeness and consistency"""
    
    @staticmethod
    def validate_mode_config(config: Dict) -> List[str]:
        """Validate that config has all required fields for the mode"""
        errors = []
        
        # Validate required top-level fields
        required_fields = ['mode', 'share_class', 'asset', 'data_requirements']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Validate data requirements are reasonable
        data_requirements = config.get('data_requirements', [])
        if not data_requirements:
            errors.append("No data requirements specified")
        
        # Validate component config completeness
        component_config = config.get('component_config', {})
        for component_name, component_config in component_config.items():
            errors.extend(ConfigValidator._validate_component_config(component_name, component_config))
        
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
        
        return errors


you said 

class PureLendingDataProvider(DataProvider):
    """Data provider for pure lending mode"""
    
    def __init__(self, execution_mode: str, config: Dict):
        self.execution_mode = execution_mode
        self.config = config
        self.available_data_types = [
            'aave_usdt_rates',
            'aave_usdt_indexes', 
            'eth_usd_prices'
        ]
    
    def validate_data_requirements(self, data_requirements: List[str]):
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
                    'USDT': 1.0,
                    'ETH': self._get_eth_price(timestamp)
                },
                'rates': {
                    'aave_usdt_supply': self._get_aave_usdt_rate(timestamp)
                }
            },
            'protocol_data': {
                'aave_indexes': {
                    'aUSDT': self._get_aave_usdt_index(timestamp)
                }
            }
        }


you said 

class DataProviderFactory:
    """Creates data providers based on config requirements"""
    
    @staticmethod
    def create(execution_mode: str, config: Dict) -> DataProvider:
        mode = config['mode']
        data_requirements = config.get('data_requirements', [])
        
        # Create mode-specific data provider
        if mode == 'pure_lending':
            provider = PureLendingDataProvider(execution_mode, config)
        elif mode == 'btc_basis':
            provider = BTCBasisDataProvider(execution_mode, config)
        elif mode == 'eth_leveraged':
            provider = ETHLeveragedDataProvider(execution_mode, config)
        else:
            raise ValueError(f"Unknown strategy mode: {mode}")
        
        # Validate that provider can satisfy data requirements
        provider.validate_data_requirements(data_requirements)
        
        return provider

you said 

class RiskMonitor:
    """Mode-agnostic risk assessment using config-driven behavior"""
    
    def __init__(self, config: Dict, data_provider: DataProvider, execution_mode: str):
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Extract component-specific config
        self.risk_config = config.get('component_config', {}).get('risk_monitor', {})
        self.enabled_risk_types = self.risk_config.get('enabled_risk_types', [])
        self.risk_limits = self.risk_config.get('risk_limits', {})
    
    def assess_risk(self, exposure_data, market_data):
        risk_metrics = {}
        
        # Use config to determine what risks to calculate
        for risk_type in self.enabled_risk_types:
            if risk_type == 'aave_health_factor':
                risk_metrics[risk_type] = self._calculate_health_factor(exposure_data, market_data)
            elif risk_type == 'cex_margin_ratio':
                risk_metrics[risk_type] = self._calculate_margin_ratio(exposure_data, market_data)
            # ... etc
        
        return risk_metrics

        
        # Apply risk limits from config
        risk_alerts = self._check_risk_limits(risk_metrics, self.risk_limits)
        
        return {
            'risk_metrics': risk_metrics,
            'risk_alerts': risk_alerts,
            'enabled_risk_types': self.enabled_risk_types
        }




class PnLCalculator:
    """Mode-agnostic PnL calculation using config-driven attribution"""
    
    def __init__(self, config: Dict, data_provider: DataProvider, execution_mode: str):
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Extract PnL-specific config
        self.pnl_config = config.get('component_config', {}).get('pnl_calculator', {})
        self.attribution_types = self.pnl_config.get('attribution_types', [])
        self.reporting_currency = self.pnl_config.get('reporting_currency', 'USDT')
        self.reconciliation_tolerance = self.pnl_config.get('reconciliation_tolerance', 0.02)
        
        # Initialize cumulative tracking for each attribution type
        self.cumulative_attributions = {attr_type: 0.0 for attr_type in self.attribution_types}
        
        # Store initial value for balance-based PnL
        self.initial_total_value = None
    
    def calculate_pnl(
        self,
        current_exposure: Dict,
        previous_exposure: Optional[Dict],
        timestamp: pd.Timestamp,
        period_start: pd.Timestamp
    ) -> Dict:
        """Calculate PnL using config-driven attribution system"""
        
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
            # First calculation, no PnL yet
            return self._zero_attribution()
        
        # Calculate hourly PnL for each configured attribution type
        hourly_attributions = {}
        
        for attr_type in self.attribution_types:
            if attr_type == 'supply_yield':
                hourly_attributions[attr_type] = self._calc_supply_yield_pnl(
                    current_exposure, previous_exposure
                )
            elif attr_type == 'staking_yield_oracle':
                hourly_attributions[attr_type] = self._calc_staking_yield_oracle_pnl(
                    current_exposure, previous_exposure
                )
            elif attr_type == 'staking_yield_rewards':
                hourly_attributions[attr_type] = self._calc_staking_yield_rewards_pnl(
                    current_exposure, previous_exposure
                )
            elif attr_type == 'borrow_costs':
                hourly_attributions[attr_type] = self._calc_borrow_costs_pnl(
                    current_exposure, previous_exposure
                )
            elif attr_type == 'funding_pnl':
                hourly_attributions[attr_type] = self._calc_funding_pnl(
                    current_exposure, previous_exposure, timestamp
                )
            elif attr_type == 'delta_pnl':
                hourly_attributions[attr_type] = self._calc_delta_pnl(
                    current_exposure, previous_exposure
                )
            elif attr_type == 'transaction_costs':
                hourly_attributions[attr_type] = self._calc_transaction_costs_pnl(
                    current_exposure, previous_exposure
                )
            else:
                # Unknown attribution type, return 0
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
    
    def _zero_attribution(self) -> Dict:
        """Return zero attribution for first calculation"""
        return {
            'hourly': {attr_type: 0.0 for attr_type in self.attribution_types},
            'cumulative': {attr_type: 0.0 for attr_type in self.attribution_types},
            'hourly_total': 0.0,
            'cumulative_total': 0.0
        }

you said 

class ExposureMonitor:
    """Mode-agnostic exposure calculation using config-driven asset tracking"""
    
    def __init__(self, config: Dict, data_provider: DataProvider, execution_mode: str):
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Extract exposure-specific config
        self.exposure_config = config.get('component_config', {}).get('exposure_monitor', {})
        self.exposure_currency = self.exposure_config.get('exposure_currency', 'USDT')
        self.track_assets = self.exposure_config.get('track_assets', [])
        self.conversion_methods = self.exposure_config.get('conversion_methods', {})
        
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
        """Calculate exposure using config-driven asset tracking"""
        
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
        elif conversion_method == 'oracle_price':
            oracle_price = market_data['protocol_data']['oracle_prices'].get(asset, 0.0)
            exposure_value = asset_balance * oracle_price
            delta_exposure = asset_balance
        elif conversion_method == 'aave_index':
            # Handle AAVE token conversion
            if asset.startswith('a'):  # Collateral token
                index = market_data['protocol_data']['aave_indexes'].get(asset, 0.0)
                underlying_balance = asset_balance * index
                exposure_value = underlying_balance * market_data['market_data']['prices'].get(asset[1:], 0.0)
                delta_exposure = underlying_balance
            elif asset.startswith('variableDebt'):  # Debt token
                index = market_data['protocol_data']['aave_indexes'].get(asset, 0.0)
                underlying_balance = asset_balance * index
                exposure_value = underlying_balance * market_data['market_data']['prices'].get(asset.replace('variableDebt', ''), 0.0)
                delta_exposure = -underlying_balance  # Debt is negative delta
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
        # This would search through wallet, CEX accounts, etc.
        # Implementation depends on position snapshot structure
        total_balance = 0.0
        
        # Check wallet
        if 'wallet' in position_snapshot:
            total_balance += position_snapshot['wallet'].get(asset, 0.0)
        
        # Check CEX accounts
        if 'cex_accounts' in position_snapshot:
            for venue, account in position_snapshot['cex_accounts'].items():
                total_balance += account.get(asset, 0.0)
        
        return total_balance


you said 

class PnLCalculator:
    """Mode-agnostic PnL calculation with config-driven attribution methods"""
    
    def _calc_supply_yield_pnl(self, current_exposure: Dict, previous_exposure: Dict) -> float:
        """Calculate AAVE supply yield PnL"""
        if 'aave_indexes' not in current_exposure.get('protocol_data', {}):
            return 0.0  # No AAVE data available
        
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
            return 0.0  # No perp positions
        
        total_funding_pnl = 0.0
        for venue, positions in current_exposure['perp_positions'].items():
            for instrument, position in positions.items():
                if position['size'] != 0:  # Has position
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
            return 0.0  # No delta data available
        
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


you said for pnl vlalidation


class ConfigValidator:
    """Validate config for PnL and Exposure components"""
    
    @staticmethod
    def validate_pnl_config(pnl_config: Dict) -> List[str]:
        """Validate PnL calculator config"""
        errors = []
        
        if 'attribution_types' not in pnl_config:
            errors.append("pnl_calculator missing attribution_types")
        elif not pnl_config['attribution_types']:
            errors.append("pnl_calculator.attribution_types cannot be empty")
        
        if 'reporting_currency' not in pnl_config:
            errors.append("pnl_calculator missing reporting_currency")
        elif pnl_config['reporting_currency'] not in ['USDT', 'ETH']:
            errors.append("pnl_calculator.reporting_currency must be USDT or ETH")
        
        if 'reconciliation_tolerance' not in pnl_config:
            errors.append("pnl_calculator missing reconciliation_tolerance")
        elif not 0 < pnl_config['reconciliation_tolerance'] < 1:
            errors.append("pnl_calculator.reconciliation_tolerance must be between 0 and 1")
        
        return errors
    
    @staticmethod
    def validate_exposure_config(exposure_config: Dict) -> List[str]:
        """Validate exposure monitor config"""
        errors = []
        
        if 'exposure_currency' not in exposure_config:
            errors.append("exposure_monitor missing exposure_currency")
        elif exposure_config['exposure_currency'] not in ['USDT', 'ETH']:
            errors.append("exposure_monitor.exposure_currency must be USDT or ETH")
        
        if 'track_assets' not in exposure_config:
            errors.append("exposure_monitor missing track_assets")
        elif not exposure_config['track_assets']:
            errors.append("exposure_monitor.track_assets cannot be empty")
        
        if 'conversion_methods' not in exposure_config:
            errors.append("exposure_monitor missing conversion_methods")
        else:
            track_assets = exposure_config.get('track_assets', [])
            conversion_methods = exposure_config['conversion_methods']
            for asset in track_assets:
                if asset not in conversion_methods:
                    errors.append(f"exposure_monitor missing conversion method for asset: {asset}")
        
        return errors


you said for strategy manager 

class StrategyManager:
    """Mode-specific strategy manager using config-driven behavior"""
    
    def __init__(self, config: Dict, data_provider: DataProvider, execution_mode: str):
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Extract strategy-specific config
        self.strategy_config = config.get('component_config', {}).get('strategy_manager', {})
        self.strategy_type = self.strategy_config.get('strategy_type')
        self.available_actions = self.strategy_config.get('actions', [])
        self.rebalancing_triggers = self.strategy_config.get('rebalancing_triggers', [])
        self.position_calculation = self.strategy_config.get('position_calculation', {})
        
        # Initialize strategy-specific logic
        self._initialize_strategy_logic()
    
    def _initialize_strategy_logic(self):
        """Initialize strategy-specific logic based on config"""
        if self.strategy_type == 'pure_lending':
            self._init_pure_lending_logic()
        elif self.strategy_type == 'btc_basis':
            self._init_btc_basis_logic()
        elif self.strategy_type == 'eth_leveraged':
            self._init_eth_leveraged_logic()
        # ... etc
    
    def calculate_target_positions(self, current_exposure: Dict, market_data: Dict) -> Dict:
        """Calculate target positions based on strategy type"""
        if self.strategy_type == 'pure_lending':
            return self._calculate_pure_lending_positions(current_exposure, market_data)
        elif self.strategy_type == 'btc_basis':
            return self._calculate_btc_basis_positions(current_exposure, market_data)
        # ... etc
    
    def _calculate_pure_lending_positions(self, current_exposure: Dict, market_data: Dict) -> Dict:
        """Pure lending position calculation"""
        target_position = self.position_calculation.get('target_position')
        max_position = self.position_calculation.get('max_position')
        
        # Calculate desired AAVE USDT supply position
        equity = current_exposure['total_exposure']
        target_supply = equity  # All equity to AAVE
        
        return {
            'aave_usdt_supply': target_supply,
            'wallet_usdt': 0.0  # No wallet balance needed
        }
    
    def _calculate_btc_basis_positions(self, current_exposure: Dict, market_data: Dict) -> Dict:
        """BTC basis position calculation"""
        equity = current_exposure['total_exposure']
        hedge_allocation = self.position_calculation.get('hedge_allocation', {})
        
        # Calculate target BTC spot position
        target_btc_spot = equity / market_data['market_data']['prices']['BTC']
        
        # Calculate target perp short positions across venues
        target_perp_shorts = {}
        for venue, allocation in hedge_allocation.items():
            target_perp_shorts[venue] = -target_btc_spot * allocation
        
        return {
            'btc_spot_long': target_btc_spot,
            'btc_perp_shorts': target_perp_shorts
        }

for execution

class VenueManager:
    """Mode-agnostic execution manager using config-driven action mapping"""
    
    def __init__(self, config: Dict, data_provider: DataProvider, execution_mode: str):
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Extract execution-specific config
        self.execution_config = config.get('component_config', {}).get('execution_manager', {})
        self.supported_actions = self.execution_config.get('supported_actions', [])
        self.action_mapping = self.execution_config.get('action_mapping', {})
        
        # Initialize execution interface manager
        self.execution_interface_manager = ExecutionInterfaceManager(config, data_provider, execution_mode)
    
    def execute_strategy_action(self, action_type: str, action_params: Dict) -> Dict:
        """Execute strategy action using config-driven mapping"""
        
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
        """Execute individual action"""
        if action.startswith('aave_'):
            return self.execution_interface_manager.execute_aave_action(action, params)
        elif action.startswith('cex_'):
            return self.execution_interface_manager.execute_cex_action(action, params)
        else:
            raise ValueError(f"Unknown action type: {action}")

fro execution interface 

class ExecutionInterfaceManager:
    """Mode-agnostic execution interface manager"""
    
    def __init__(self, config: Dict, data_provider: DataProvider, execution_mode: str):
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
            # ... etc
        
        return interfaces
    
    def execute_aave_action(self, action: str, params: Dict) -> Dict:
        """Execute AAVE action"""
        aave_interface = self.venue_interfaces['aave']
        
        if action == 'aave_supply':
            return aave_interface.supply(params['asset'], params['amount'])
        elif action == 'aave_withdraw':
            return aave_interface.withdraw(params['asset'], params['amount'])
        else:
            raise ValueError(f"Unknown AAVE action: {action}")
    
    def execute_cex_action(self, action: str, params: Dict) -> Dict:
        """Execute CEX action"""
        venue = params['venue']
        cex_interface = self.venue_interfaces[venue]
        
        if action == 'cex_spot_buy':
            return cex_interface.spot_buy(params['symbol'], params['amount'])
        elif action == 'cex_perp_short':
            return cex_interface.perp_short(params['symbol'], params['amount'])
        else:
            raise ValueError(f"Unknown CEX action: {action}")


fro reconciliation 


class ReconciliationComponent:
    """Mode-agnostic reconciliation component"""
    
    def __init__(self, config: Dict, data_provider: DataProvider, execution_mode: str):
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Reconciliation is the same for all modes
        self.reconciliation_tolerance = 0.01  # 1% tolerance
    
    def reconcile_position(self, expected_position: Dict, actual_position: Dict) -> Dict:
        """Reconcile expected vs actual position"""
        
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


for results store 

class ResultsStore:
    """Mode-agnostic results store using config-driven result types"""
    
    def __init__(self, config: Dict, data_provider: DataProvider, execution_mode: str):
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Extract results-specific config
        self.results_config = config.get('component_config', {}).get('results_store', {})
        self.result_types = self.results_config.get('result_types', [])
        self.balance_sheet_assets = self.results_config.get('balance_sheet_assets', [])
        self.pnl_attribution_types = self.results_config.get('pnl_attribution_types', [])
        
        # Initialize result storage
        self.results = {}
    
    def store_results(self, timestamp: pd.Timestamp, component_data: Dict) -> Dict:
        """Store results based on config-driven result types"""
        
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
    
    def _store_delta_tracking(self, timestamp: pd.Timestamp, component_data: Dict) -> Dict:
        """Store delta tracking data (only for modes that need it)"""
        delta_assets = self.results_config.get('delta_tracking_assets', [])
        
        if not delta_assets:
            return None  # No delta tracking needed for this mode
        
        delta_data = {}
        for asset in delta_assets:
            delta_data[asset] = self._extract_delta_data(asset, component_data)
        
        return {
            'timestamp': timestamp,
            'delta_data': delta_data,
            'net_delta': sum(delta_data.values())
        }

fro event driven system 


# UNCHANGED: Component workflow sequence
class EventDrivenStrategyEngine:
    def _process_timestep(self, timestamp: pd.Timestamp):
        # Same sequence, same method calls
        self.components['position_monitor'].update_state(timestamp, 'full_loop')
        self.components['exposure_monitor'].update_state(timestamp, 'full_loop')
        self.components['risk_monitor'].update_state(timestamp, 'full_loop')
        self.components['strategy_manager'].update_state(timestamp, 'full_loop')
        self.components['execution_manager'].update_state(timestamp, 'full_loop')
        self.components['pnl_calculator'].update_state(timestamp, 'full_loop')
        self.components['results_store'].update_state(timestamp, 'full_loop')

for api docs making sure we have config overrides 

# BEFORE: Mode-specific API docs
/backtest/pure_lending:
  description: "Run pure lending backtest"
  parameters:
    - name: mode
      enum: ["pure_lending"]

# AFTER: Config-driven API docs
/backtest:
  description: "Run backtest with config-driven strategy"
  parameters:
    - name: mode
      enum: ["pure_lending", "btc_basis", "eth_leveraged", "usdt_market_neutral"]
    - name: config_overrides
      type: object
      description: "Optional config overrides"

for backtest service

# BEFORE: Mode-specific service initialization
class BacktestService:
    async def run_backtest(self, request: BacktestRequest) -> str:
        if request.mode == 'pure_lending':
            data_provider = PureLendingDataProvider('backtest', config)
        elif request.mode == 'btc_basis':
            data_provider = BTCBasisDataProvider('backtest', config)

# AFTER: Config-driven service initialization
class BacktestService:
    async def run_backtest(self, request: BacktestRequest) -> str:
        # Load config for strategy mode
        config = self._load_strategy_config(request.mode)
        
        # Apply config overrides
        if request.config_overrides:
            config = self._apply_config_overrides(config, request.config_overrides)
        
        # Create data provider using factory
        data_provider = DataProviderFactory.create('backtest', config)
        
        # Create components using factory
        components = ComponentFactory.create_all(config, data_provider, 'backtest')

veent logegr statys the same and so do math utilities 