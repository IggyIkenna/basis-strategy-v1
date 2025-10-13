#!/usr/bin/env python3
"""
Configuration Field Classifier

Classifies configuration fields into different levels for quality gate validation:
- required_toplevel: Required top-level fields
- required_nested: Required nested object fields  
- fixed_schema_dict: Dict[str, Any] with fixed schema (document all fields)
- dynamic_dict: Dict[str, Any] with truly dynamic keys (document parent only)
- data_value: List fields with data values (document type, not values)

Reference: Config Quality Gates 100% Alignment Plan
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Union, get_origin, get_args
from pydantic import BaseModel

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from basis_strategy_v1.infrastructure.config.models import (
    ModeConfig, VenueConfig, ShareClassConfig
)


class ConfigFieldClassifier:
    """Classifies configuration fields for quality gate validation."""
    
    def __init__(self):
        # Fixed schema dicts - document all nested fields
        self.FIXED_SCHEMA_DICTS = {
            'api_contract': {
                'description': 'API contract specification with fixed request/response schema',
                'fields': [
                    'request_format', 'request_format.method', 'request_format.headers', 
                    'request_format.body', 'response_format', 'response_format.symbol',
                    'response_format.timestamp', 'response_format.signal', 'response_format.confidence',
                    'response_format.stop_loss', 'response_format.take_profit', 'response_format.model_version',
                    # Add wildcards and more nested fields
                    'request_format.*', 'request_format.headers.*', 'request_format.body.*',
                    'response_format.*'
                ]
            },
            'example': {
                'description': 'Example request/response with fixed schema',
                'fields': [
                    'request', 'response', 'request.*', 'response.*',
                    'response.symbol', 'response.timestamp', 'response.signal', 'response.confidence',
                    'response.stop_loss', 'response.take_profit', 'response.model_version'
                ]
            },
            'auth': {
                'description': 'Authentication configuration with fixed fields',
                'fields': ['type', 'token_env_var']
            },
            'validation': {
                'description': 'Response validation configuration with fixed fields',
                'fields': ['require_confidence_score', 'min_confidence', 'valid_signals']
            },
            'ml_config': {
                'description': 'ML model configuration with fixed fields',
                'fields': [
                    'model_registry', 'model_name', 'model_version', 
                    'candle_interval', 'signal_threshold', 'max_position_size',
                    'confidence_threshold', 'retraining_frequency', 'feature_importance_threshold'
                ]
            },
            'venues': {
                'description': 'Venue configuration with fixed venue keys',
                'fields': [
                    'venues', 'venues.aave_v3', 'venues.aave_v3.venue_type', 'venues.aave_v3.enabled', 'venues.aave_v3.instruments', 'venues.aave_v3.order_types',
                    'venues.alchemy', 'venues.alchemy.venue_type', 'venues.alchemy.enabled', 'venues.alchemy.instruments', 'venues.alchemy.order_types',
                    'venues.binance', 'venues.binance.venue_type', 'venues.binance.enabled', 'venues.binance.instruments', 'venues.binance.order_types', 'venues.binance.min_amount',
                    'venues.bybit', 'venues.bybit.venue_type', 'venues.bybit.enabled', 'venues.bybit.instruments', 'venues.bybit.order_types', 'venues.bybit.max_leverage', 'venues.bybit.min_amount',
                    'venues.etherfi', 'venues.etherfi.venue_type', 'venues.etherfi.enabled', 'venues.etherfi.instruments', 'venues.etherfi.order_types',
                    'venues.okx', 'venues.okx.venue_type', 'venues.okx.enabled', 'venues.okx.instruments', 'venues.okx.order_types', 'venues.okx.max_leverage', 'venues.okx.min_amount',
                    # Add wildcards for each venue
                    'venues.aave_v3.*', 'venues.alchemy.*', 'venues.binance.*', 'venues.bybit.*', 'venues.etherfi.*', 'venues.okx.*'
                ]
            },
            'component_config': {
                'description': 'Component-specific configuration with fixed component keys',
                'fields': [
                    'risk_monitor', 'exposure_monitor', 'pnl_calculator', 
                    'strategy_manager', 'execution_manager', 'results_store', 'strategy_factory',
                    'position_monitor',
                    # Add wildcards for each component
                    'component_config.risk_monitor.*', 'component_config.exposure_monitor.*', 'component_config.pnl_calculator.*',
                    'component_config.strategy_manager.*', 'component_config.execution_manager.*', 'component_config.results_store.*', 'component_config.strategy_factory.*',
                    'component_config.position_monitor.*',
                    # Risk monitor fields
                    'component_config.risk_monitor.enabled_risk_types', 'component_config.risk_monitor.risk_limits',
                    'component_config.risk_monitor.risk_limits.target_margin_ratio', 'component_config.risk_monitor.risk_limits.cex_margin_ratio_min',
                    'component_config.risk_monitor.risk_limits.maintenance_margin_requirement', 'component_config.risk_monitor.risk_limits.delta_tolerance',
                    'component_config.risk_monitor.risk_limits.target_ltv', 'component_config.risk_monitor.risk_limits.liquidation_threshold',
                    # Exposure monitor fields
                    'component_config.exposure_monitor.exposure_currency', 'component_config.exposure_monitor.track_assets',
                    'component_config.exposure_monitor.conversion_methods',
                    'component_config.exposure_monitor.conversion_methods.BTC', 'component_config.exposure_monitor.conversion_methods.ETH',
                    'component_config.exposure_monitor.conversion_methods.USDT', 'component_config.exposure_monitor.conversion_methods.aWeETH',
                    'component_config.exposure_monitor.conversion_methods.weETH', 'component_config.exposure_monitor.conversion_methods.KING',
                    'component_config.exposure_monitor.conversion_methods.EIGEN', 'component_config.exposure_monitor.conversion_methods.ETHFI',
                    'component_config.exposure_monitor.conversion_methods.variableDebtWETH', 'component_config.exposure_monitor.conversion_methods.BTC_PERP',
                    'component_config.exposure_monitor.conversion_methods.ETH_PERP',
                    # PnL calculator fields
                    'component_config.pnl_calculator.attribution_types', 'component_config.pnl_calculator.reporting_currency',
                    'component_config.pnl_calculator.reconciliation_tolerance',
                    # Strategy manager fields
                    'component_config.strategy_manager.strategy_type', 'component_config.strategy_manager.actions',
                    'component_config.strategy_manager.rebalancing_triggers', 'component_config.strategy_manager.position_calculation',
                    'component_config.strategy_manager.position_calculation.target_position', 'component_config.strategy_manager.position_calculation.hedge_position',
                    'component_config.strategy_manager.position_calculation.hedge_allocation',
                    'component_config.strategy_manager.position_calculation.hedge_allocation.binance',
                    'component_config.strategy_manager.position_calculation.hedge_allocation.bybit',
                    'component_config.strategy_manager.position_calculation.hedge_allocation.okx',
                    'component_config.strategy_manager.position_calculation.method', 'component_config.strategy_manager.position_calculation.leverage_ratio',
                    # Execution manager fields
                    'component_config.execution_manager.supported_actions', 'component_config.execution_manager.action_mapping',
                    'component_config.execution_manager.action_mapping.entry_full', 'component_config.execution_manager.action_mapping.exit_full',
                    'component_config.execution_manager.action_mapping.entry_partial', 'component_config.execution_manager.action_mapping.exit_partial',
                    'component_config.execution_manager.action_mapping.open_perp_short', 'component_config.execution_manager.action_mapping.open_perp_long',
                    'component_config.execution_manager.action_mapping.close_perp',
                    # Position monitor fields
                    'component_config.position_monitor', 'component_config.position_monitor.fail_on_unknown_asset', 'component_config.position_monitor.track_assets',
                    'component_config.position_monitor.initial_balances', 'component_config.position_monitor.initial_balances.wallet',
                    'component_config.position_monitor.initial_balances.cex_accounts',
                    # Results store fields
                    'component_config.results_store.result_types', 'component_config.results_store.balance_sheet_assets',
                    'component_config.results_store.pnl_attribution_types', 'component_config.results_store.leverage_tracking',
                    'component_config.results_store.delta_tracking_assets', 'component_config.results_store.funding_tracking_venues',
                    'component_config.results_store.dust_tracking_tokens',
                    # Strategy factory fields
                    'component_config.strategy_factory.timeout', 'component_config.strategy_factory.max_retries', 'component_config.strategy_factory.validation_strict'
                ]
            },
            'trading_fees': {
                'description': 'Trading fees configuration with fixed fields',
                'fields': ['maker', 'taker']
            },
            'target_apy_range': {
                'description': 'Target APY range configuration with fixed fields',
                'fields': ['min', 'max']
            },
            'event_logger': {
                'description': 'Event logger configuration with fixed fields',
                'fields': [
                    'log_path', 'log_format', 'log_level', 'event_categories',
                    'event_logging_settings', 'log_retention_policy',
                    'compliance_settings', 'logging_requirements', 'event_filtering',
                    'log_retention_policy.retention_days', 'log_retention_policy.max_file_size_mb',
                    'log_retention_policy.rotation_frequency', 'log_retention_policy.compression_after_days',
                    # Add wildcards for nested configurations
                    'event_categories.*', 'event_logging_settings.*', 'log_retention_policy.*',
                     'logging_requirements.*', 'event_filtering.*'
                ]
            }
        }
        
        # Dynamic dicts - document parent only with example
        self.DYNAMIC_DICTS = {
            'endpoints': {
                'description': 'API endpoints configuration - keys vary by service',
                'example': '{"predictions": "https://api.example.com/predictions", "health": "https://api.example.com/health"}'
            },
            'hedge_allocation': {
                'description': 'Hedge allocation percentages - keys are venue names from hedge_venues',
                'example': '{"binance": 0.4, "bybit": 0.3, "okx": 0.3}'
            },
            'action_mapping': {
                'description': 'Action to venue mapping - keys are action names, values are venue lists',
                'example': '{"entry_full": ["cex_spot_buy", "cex_perp_short"], "exit_full": ["cex_perp_close", "cex_spot_sell"]}'
            },
            'venues': {
                'description': 'Venue configuration - keys are venue names, values are venue-specific configs',
                'example': '{"binance": {"enabled": true, "venue_type": "cex"}, "aave_v3": {"enabled": true, "venue_type": "defi"}}'
            }
        }
    
    def classify_field(self, field_path: str, field_type: type, is_required: bool = True) -> str:
        """
        Classify a configuration field into one of the levels.
        
        Args:
            field_path: Dot-separated field path (e.g., 'component_config.strategy_manager')
            field_type: Python type of the field
            is_required: Whether the field is required (non-Optional)
            
        Returns:
            Classification: 'required_toplevel', 'required_nested', 'fixed_schema_dict', 
                          'dynamic_dict', 'data_value', 'optional_field'
        """
        # Check if it's a fixed schema dict
        for dict_name, config in self.FIXED_SCHEMA_DICTS.items():
            if field_path == dict_name or field_path.startswith(f"{dict_name}."):
                return 'fixed_schema_dict'
        
        # Check if it's a dynamic dict
        for dict_name in self.DYNAMIC_DICTS.keys():
            if field_path == dict_name:
                return 'dynamic_dict'
            # For dynamic dict keys (e.g., hedge_allocation.binance), classify as dynamic
            if field_path.startswith(f"{dict_name}."):
                return 'dynamic_dict'
        
        # Check if it's a list field (data value)
        if self._is_list_field(field_type):
            return 'data_value'
        
        # Check if it's required
        if not is_required:
            return 'optional_field'
        
        # Check nesting level
        if '.' in field_path:
            return 'required_nested'
        else:
            return 'required_toplevel'
    
    def _is_list_field(self, field_type: type) -> bool:
        """Check if field type is a List[T] where T is a primitive type."""
        origin = get_origin(field_type)
        if origin is list:
            args = get_args(field_type)
            if args:
                # Check if it's List[str], List[int], List[float], etc.
                return args[0] in (str, int, float, bool)
        return False
    
    def _is_dict_field(self, annotation) -> bool:
        """Check if annotation represents a Dict[str, Any] field (including Optional)."""
        # Direct Dict[str, Any]
        if annotation == Dict[str, Any]:
            return True
        
        # Dict with __origin__ == dict
        if hasattr(annotation, '__origin__') and annotation.__origin__ == dict:
            return True
        
        # Optional[Dict[str, Any]] - Union with dict and None
        if (hasattr(annotation, '__origin__') and annotation.__origin__ == Union and 
            len(annotation.__args__) == 2 and type(None) in annotation.__args__):
            for arg in annotation.__args__:
                if hasattr(arg, '__origin__') and arg.__origin__ == dict:
                    return True
        
        return False
    
    def get_required_fields_by_level(self, config_type: str) -> Dict[str, List[str]]:
        """
        Get required fields for a config type, classified by level.
        
        Args:
            config_type: 'ModeConfig', 'VenueConfig', or 'ShareClassConfig'
            
        Returns:
            Dictionary mapping level to list of field paths
        """
        if config_type == 'ModeConfig':
            model_class = ModeConfig
        elif config_type == 'VenueConfig':
            model_class = VenueConfig
        elif config_type == 'ShareClassConfig':
            model_class = ShareClassConfig
        else:
            raise ValueError(f"Unknown config type: {config_type}")
        
        fields_by_level = {
            'required_toplevel': [],
            'required_nested': [],
            'fixed_schema_dict': [],
            'dynamic_dict': [],
            'data_value': [],
            'optional_field': []
        }
        
        # Extract fields from Pydantic model
        model_fields = self._extract_model_fields(model_class)
        
        for field_path, field_info in model_fields.items():
            field_type = field_info['type']
            is_required = field_info['required']
            
            classification = self.classify_field(field_path, field_type, is_required)
            fields_by_level[classification].append(field_path)
        
        return fields_by_level
    
    def _extract_model_fields(self, model_class: type) -> Dict[str, Dict[str, Any]]:
        """Extract all fields from a Pydantic model with their types and requirements."""
        fields = {}
        
        if hasattr(model_class, 'model_fields'):
            for field_name, field_info in model_class.model_fields.items():
                annotation = field_info.annotation
                is_required = field_info.is_required()
                
                # Handle the field itself
                fields[field_name] = {
                    'type': annotation,
                    'required': is_required
                }
                
                # Handle nested BaseModel fields
                if hasattr(annotation, 'model_fields'):
                    nested_fields = self._extract_model_fields(annotation)
                    for nested_field, nested_info in nested_fields.items():
                        nested_path = f"{field_name}.{nested_field}"
                        fields[nested_path] = nested_info
                
                # Handle Union types (like Optional)
                elif hasattr(annotation, '__origin__') and annotation.__origin__ is Union:
                    # Find the first non-None type
                    for union_type in annotation.__args__:
                        if union_type is not type(None):
                            if hasattr(union_type, 'model_fields'):
                                nested_fields = self._extract_model_fields(union_type)
                                for nested_field, nested_info in nested_fields.items():
                                    nested_path = f"{field_name}.{nested_field}"
                                    fields[nested_path] = nested_info
                            elif self._is_dict_field(union_type):
                                # Handle Dict[str, Any] fields in Union types
                                if field_name in self.FIXED_SCHEMA_DICTS:
                                    # Add all known fields for fixed schema dicts
                                    for known_field in self.FIXED_SCHEMA_DICTS[field_name]['fields']:
                                        # Always use the field as-is since FIXED_SCHEMA_DICTS already has correct paths
                                        full_path = known_field
                                        fields[full_path] = {
                                            'type': str,  # Assume string type for now
                                            'required': False  # Mark as optional since they're in Dict[str, Any]
                                        }
                            break
                
                # Handle Dict[str, Any] fields - add specific known fields
                elif self._is_dict_field(annotation):
                    if field_name in self.FIXED_SCHEMA_DICTS:
                        # Add all known fields for fixed schema dicts
                        for known_field in self.FIXED_SCHEMA_DICTS[field_name]['fields']:
                            # Always use the field as-is since FIXED_SCHEMA_DICTS already has correct paths
                            full_path = known_field
                            fields[full_path] = {
                                'type': str,  # Assume string type for now
                                'required': False  # Mark as optional since they're in Dict[str, Any]
                            }
        
        return fields
    
    def get_fixed_schema_fields(self, dict_name: str) -> List[str]:
        """Get all fields that should be documented for a fixed schema dict."""
        if dict_name in self.FIXED_SCHEMA_DICTS:
            return self.FIXED_SCHEMA_DICTS[dict_name]['fields']
        return []
    
    def get_dynamic_dict_info(self, dict_name: str) -> Dict[str, str]:
        """Get documentation info for a dynamic dict."""
        if dict_name in self.DYNAMIC_DICTS:
            return self.DYNAMIC_DICTS[dict_name]
        return {}
    
    def is_fixed_schema_dict(self, field_path: str) -> bool:
        """Check if a field path is part of a fixed schema dict."""
        for dict_name in self.FIXED_SCHEMA_DICTS.keys():
            if field_path == dict_name or field_path.startswith(f"{dict_name}."):
                return True
        return False
    
    def is_dynamic_dict(self, field_path: str) -> bool:
        """Check if a field path is part of a dynamic dict."""
        for dict_name in self.DYNAMIC_DICTS.keys():
            if field_path == dict_name or field_path.startswith(f"{dict_name}."):
                return True
        return False
    
    def get_parent_dynamic_dict(self, field_path: str) -> Optional[str]:
        """Get the parent dynamic dict name for a field path."""
        for dict_name in self.DYNAMIC_DICTS.keys():
            if field_path.startswith(f"{dict_name}."):
                return dict_name
        return None


def main():
    """Test the field classifier."""
    classifier = ConfigFieldClassifier()
    
    # Test ModeConfig
    print("=== ModeConfig Fields ===")
    mode_fields = classifier.get_required_fields_by_level('ModeConfig')
    for level, fields in mode_fields.items():
        if fields:
            print(f"\n{level}:")
            for field in fields[:5]:  # Show first 5
                print(f"  - {field}")
            if len(fields) > 5:
                print(f"  ... and {len(fields) - 5} more")
    
    # Test VenueConfig
    print("\n=== VenueConfig Fields ===")
    venue_fields = classifier.get_required_fields_by_level('VenueConfig')
    for level, fields in venue_fields.items():
        if fields:
            print(f"\n{level}:")
            for field in fields[:5]:  # Show first 5
                print(f"  - {field}")
            if len(fields) > 5:
                print(f"  ... and {len(fields) - 5} more")
    
    # Test ShareClassConfig
    print("\n=== ShareClassConfig Fields ===")
    share_class_fields = classifier.get_required_fields_by_level('ShareClassConfig')
    for level, fields in share_class_fields.items():
        if fields:
            print(f"\n{level}:")
            for field in fields[:5]:  # Show first 5
                print(f"  - {field}")
            if len(fields) > 5:
                print(f"  ... and {len(fields) - 5} more")


if __name__ == "__main__":
    main()
