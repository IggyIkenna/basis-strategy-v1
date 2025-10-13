#!/usr/bin/env python3
"""
Script to remove orphaned config fields from 19_CONFIGURATION.md
"""

import re
from pathlib import Path

# Fields that should be KEPT (used in YAML or code)
KEEP_FIELDS = {
    'max_drawdown', 'max_ltv', 'position_deviation_threshold',
    'supported_strategies', 'target_apy_range', 'ml_config.model_name', 
    'ml_config.model_version', 'ml_config.signal_threshold', 'ml_config.confidence_threshold',
    'stake_allocation_eth', 'venues', 'component_config', 'data_requirements',
    'execution_mode', 'log_level', 'initial_capital', 'delta_tolerance',
    'funding_threshold', 'hedge_venues', 'hedge_allocation_bybit', 'hedge_allocation_binance',
    'hedge_allocation_okx', 'leverage_enabled', 'max_leverage', 'rewards_mode',
    'base_currency', 'type', 'description', 'decimal_places', 'risk_level',
    'market_neutral', 'allows_hedging', 'leverage_supported', 'staking_supported',
    'basis_trading_supported', 'validation_strict', 'environment', 'instruments',
    'max_position_size', 'signal_threshold', 'model_name', 'model_registry', 'model_version',
    'candle_interval', 'resolution', 'ml_config', 'ml_config.candle_interval',
    'ml_config.model_registry', 'component_config.risk_monitor.risk_limits.delta_tolerance',
    'component_config.risk_monitor.risk_limits.liquidation_threshold',
    'component_config.risk_monitor.risk_limits.maintenance_margin_requirement',
    'component_config.risk_monitor.risk_limits.target_margin_ratio',
    'component_config.strategy_manager.actions',
    'component_config.strategy_manager.position_calculation',
    'component_config.strategy_manager.position_calculation.hedge_allocation',
    'component_config.strategy_manager.position_calculation.hedge_position',
    'component_config.strategy_manager.position_calculation.leverage_ratio',
    'component_config.strategy_manager.position_calculation.method',
    'component_config.strategy_manager.position_calculation.target_position',
    'component_config.strategy_manager.rebalancing_triggers',
    'component_config.strategy_manager.strategy_type',
    'component_config.execution_manager.action_mapping.entry_full',
    'component_config.execution_manager.action_mapping.exit_full',
    'component_config.exposure_monitor.conversion_methods',
    'component_config.pnl_calculator.attribution_types',
    'component_config.results_store.balance_sheet_assets',
    'component_config.strategy_factory.timeout',
    'risk_monitor', 'exposure_monitor', 'pnl_calculator', 'strategy_manager',
    'execution_manager', 'results_store'
}

# Fields that should be REMOVED (truly orphaned)
REMOVE_FIELDS = {
    'component', 'code', 'severity', 'message', 'resolution', 'dynamic_dict', 'data_value',
    'healthy', 'degraded', 'unhealthy', 'config_settings', 'system_settings'
}

def remove_orphaned_fields():
    """Remove orphaned config fields from 19_CONFIGURATION.md"""
    
    config_file = Path("docs/specs/19_CONFIGURATION.md")
    
    if not config_file.exists():
        print(f"File not found: {config_file}")
        return
    
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove fields that are clearly orphaned
    for field in REMOVE_FIELDS:
        # Pattern to match field definitions like "- **field_name**: description"
        pattern = rf'- \*\*{re.escape(field)}\*\*:.*\n'
        content = re.sub(pattern, '', content)
        
        # Pattern to match field definitions like "**field_name**: description"
        pattern = rf'\*\*{re.escape(field)}\*\*:.*\n'
        content = re.sub(pattern, '', content)
    
    # Write back the cleaned content
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Removed orphaned fields: {REMOVE_FIELDS}")
    print(f"Kept important fields: {len(KEEP_FIELDS)} fields")

if __name__ == "__main__":
    remove_orphaned_fields()
