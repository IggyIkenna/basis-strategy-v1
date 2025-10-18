#!/usr/bin/env python3
"""
Comprehensive fix for config issues based on user feedback.

This script addresses:
1. Remove unnecessary configs from YAML and specs
2. Move configs to correct locations
3. Add missing configs to YAML
4. Update strategy names based on refactor plan
5. Add instrument type mapping to INSTRUMENT_DEFINITIONS.md
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Set

class ConfigIssuesFixer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.configs_dir = self.project_root / "configs"
        self.modes_dir = self.configs_dir / "modes"
        self.docs_dir = self.project_root / "docs"
        self.backend_dir = self.project_root / "backend" / "src" / "basis_strategy_v1"
        
        # Strategy name mapping from refactor plan
        self.strategy_name_mapping = {
            "pure_lending_usdt": "pure_lending_usdt",
            "pure_lending_eth": "pure_lending_eth", 
            "btc_basis": "btc_basis",
            "eth_basis": "eth_basis",
            "eth_leveraged": "eth_leveraged",
            "eth_staking_only": "eth_staking_only",
            "usdt_market_neutral": "usdt_market_neutral",
            "usdt_market_neutral_no_leverage": "usdt_market_neutral_no_leverage",
            "ml_btc_directional_btc_margin": "ml_btc_directional_btc_margin",
            "ml_btc_directional_usdt_margin": "ml_btc_directional_usdt_margin"
        }
        
        # Configs to remove from YAML and specs
        self.configs_to_remove = {
            "component_config.pnl_monitor.reporting_currency",  # Use share_class instead
            "component_config.results_store.balance_sheet_assets",  # Replace with instrument type mapping
            "component_config.results_store.dust_tracking_tokens",  # Move to position_subscriptions
            "component_config.results_store.leverage_tracking",  # Unclear purpose
            "component_config.results_store.pnl_attribution_types",  # Duplicate of pnl_monitor
            "component_config.risk_monitor.risk_limits.liquidation_threshold",  # Use risk data loader
            "component_config.risk_monitor.risk_limits.maintenance_margin_requirement",  # Use risk data loader
            "component_config.risk_monitor.risk_limits.target_margin_ratio",  # Rename to maintenance_margin_ratio
            "component_config.strategy_factory.validation_strict",  # Part of quality gates
            "component_config.strategy_manager.rebalancing_triggers",  # Use deviation thresholds
            "component_config.position_monitor",  # High level field
            "hedge_allocation",  # Legacy, use nested version
            "venues.aave_v3.enabled",  # Remove from all venues
            "venues.alchemy.enabled",
            "venues.binance.enabled", 
            "venues.bybit.enabled",
            "venues.etherfi.enabled",
            "venues.okx.enabled"
        }
        
        # Configs to move to different locations
        self.configs_to_move = {
            "component_config.results_store.delta_tracking_assets": "strategy_config.delta_tracking_asset",
            "component_config.risk_monitor.risk_limits.target_margin_ratio": "component_config.risk_monitor.risk_limits.maintenance_margin_ratio"
        }
        
        # Configs to add to YAML
        self.configs_to_add = {
            "component_config.strategy_factory.timeout": 30,
            "component_config.strategy_manager.actions": ["entry_full", "entry_partial", "exit_partial", "exit_full", "rebalance"],
            "component_config.strategy_manager.position_calculation.hedge_allocation.binance": 0.4,
            "component_config.strategy_manager.position_calculation.hedge_allocation.bybit": 0.3,
            "component_config.strategy_manager.position_calculation.hedge_allocation.okx": 0.3,
            "component_config.risk_monitor.enabled_risk_types": ["health_factor", "ltv_ratio", "liquidation_threshold"],
            "strategy_config.delta_tracking_asset": "USDT"  # Default, can be overridden per strategy
        }
    
    def fix_mode_configs(self):
        """Fix all mode config files."""
        print("🔧 Fixing mode config files...")
        
        for yaml_file in self.modes_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                original_data = config_data.copy()
                
                # Remove unnecessary configs
                self._remove_configs_from_yaml(config_data)
                
                # Move configs to correct locations
                self._move_configs_in_yaml(config_data)
                
                # Add missing configs
                self._add_configs_to_yaml(config_data)
                
                # Add dust_tokens to position_subscriptions
                self._add_dust_tokens_to_position_subscriptions(config_data)
                
                # Add delta_tracking_asset to strategy config
                self._add_delta_tracking_asset(config_data)
                
                # Add hedge allocation for strategies that need it
                self._add_hedge_allocation_if_needed(config_data, yaml_file.stem)
                
                if config_data != original_data:
                    with open(yaml_file, 'w', encoding='utf-8') as f:
                        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
                    print(f"  ✅ Updated {yaml_file}")
                else:
                    print(f"  ℹ️  No changes needed in {yaml_file}")
                    
            except Exception as e:
                print(f"  ❌ Error updating {yaml_file}: {e}")
    
    def _remove_configs_from_yaml(self, config_data: Dict):
        """Remove unnecessary configs from YAML."""
        # Remove from component_config.pnl_monitor
        if "component_config" in config_data and "pnl_monitor" in config_data["component_config"]:
            pnl_config = config_data["component_config"]["pnl_monitor"]
            pnl_config.pop("reporting_currency", None)
        
        # Remove from component_config.results_store
        if "component_config" in config_data and "results_store" in config_data["component_config"]:
            results_config = config_data["component_config"]["results_store"]
            results_config.pop("balance_sheet_assets", None)
            results_config.pop("dust_tracking_tokens", None)
            results_config.pop("leverage_tracking", None)
            results_config.pop("pnl_attribution_types", None)
        
        # Remove from component_config.risk_monitor
        if "component_config" in config_data and "risk_monitor" in config_data["component_config"]:
            risk_config = config_data["component_config"]["risk_monitor"]
            if "risk_limits" in risk_config:
                risk_limits = risk_config["risk_limits"]
                risk_limits.pop("liquidation_threshold", None)
                risk_limits.pop("maintenance_margin_requirement", None)
                risk_limits.pop("target_margin_ratio", None)
        
        # Remove from component_config.strategy_factory
        if "component_config" in config_data and "strategy_factory" in config_data["component_config"]:
            factory_config = config_data["component_config"]["strategy_factory"]
            factory_config.pop("validation_strict", None)
        
        # Remove from component_config.strategy_manager
        if "component_config" in config_data and "strategy_manager" in config_data["component_config"]:
            strategy_config = config_data["component_config"]["strategy_manager"]
            strategy_config.pop("rebalancing_triggers", None)
        
        # Remove high level fields
        config_data.pop("component_config", None)
        config_data.pop("hedge_allocation", None)
        
        # Remove venue enabled flags
        if "venues" in config_data:
            for venue_name in config_data["venues"]:
                if isinstance(config_data["venues"][venue_name], dict):
                    config_data["venues"][venue_name].pop("enabled", None)
    
    def _move_configs_in_yaml(self, config_data: Dict):
        """Move configs to correct locations."""
        # Move delta_tracking_assets to strategy_config.delta_tracking_asset
        if "component_config" in config_data and "results_store" in config_data["component_config"]:
            results_config = config_data["component_config"]["results_store"]
            if "delta_tracking_assets" in results_config:
                delta_asset = results_config.pop("delta_tracking_assets")
                if "strategy_config" not in config_data:
                    config_data["strategy_config"] = {}
                config_data["strategy_config"]["delta_tracking_asset"] = delta_asset
        
        # Rename target_margin_ratio to maintenance_margin_ratio
        if "component_config" in config_data and "risk_monitor" in config_data["component_config"]:
            risk_config = config_data["component_config"]["risk_monitor"]
            if "risk_limits" in risk_config and "target_margin_ratio" in risk_config["risk_limits"]:
                target_ratio = risk_config["risk_limits"].pop("target_margin_ratio")
                risk_config["risk_limits"]["maintenance_margin_ratio"] = target_ratio
    
    def _add_configs_to_yaml(self, config_data: Dict):
        """Add missing configs to YAML."""
        # Ensure component_config exists
        if "component_config" not in config_data:
            config_data["component_config"] = {}
        
        # Add strategy_factory.timeout
        if "strategy_factory" not in config_data["component_config"]:
            config_data["component_config"]["strategy_factory"] = {}
        config_data["component_config"]["strategy_factory"]["timeout"] = 30
        
        # Add strategy_manager.actions
        if "strategy_manager" not in config_data["component_config"]:
            config_data["component_config"]["strategy_manager"] = {}
        config_data["component_config"]["strategy_manager"]["actions"] = [
            "entry_full", "entry_partial", "exit_partial", "exit_full", "rebalance"
        ]
        
        # Add risk_monitor.enabled_risk_types
        if "risk_monitor" not in config_data["component_config"]:
            config_data["component_config"]["risk_monitor"] = {}
        config_data["component_config"]["risk_monitor"]["enabled_risk_types"] = [
            "health_factor", "ltv_ratio", "liquidation_threshold"
        ]
        
        # Add strategy_config.delta_tracking_asset
        if "strategy_config" not in config_data:
            config_data["strategy_config"] = {}
        config_data["strategy_config"]["delta_tracking_asset"] = "USDT"
    
    def _add_dust_tokens_to_position_subscriptions(self, config_data: Dict):
        """Add dust_tokens section to position_subscriptions."""
        if "component_config" not in config_data:
            config_data["component_config"] = {}
        if "position_monitor" not in config_data["component_config"]:
            config_data["component_config"]["position_monitor"] = {}
        if "position_subscriptions" not in config_data["component_config"]["position_monitor"]:
            config_data["component_config"]["position_monitor"]["position_subscriptions"] = []
        
        # Add dust_tokens section
        config_data["component_config"]["position_monitor"]["dust_tokens"] = {
            "dust_instruments": [],  # Strategy-specific dust instruments
            "collection_venues": [],  # Venues to collect dust from
            "transfer_venues": []     # Venues to transfer dust to
        }
    
    def _add_delta_tracking_asset(self, config_data: Dict):
        """Add delta_tracking_asset to strategy config."""
        if "strategy_config" not in config_data:
            config_data["strategy_config"] = {}
        
        # Set based on strategy type
        mode = config_data.get("mode", "")
        if "usdt" in mode.lower():
            config_data["strategy_config"]["delta_tracking_asset"] = "USDT"
        elif "eth" in mode.lower() or "btc" in mode.lower():
            config_data["strategy_config"]["delta_tracking_asset"] = "ETH" if "eth" in mode.lower() else "BTC"
        else:
            config_data["strategy_config"]["delta_tracking_asset"] = "USDT"
    
    def _add_hedge_allocation_if_needed(self, config_data: Dict, mode_name: str):
        """Add hedge allocation for strategies that need it."""
        # Strategies that need hedge allocation (from STRATEGY_MODES.md)
        hedge_strategies = [
            "btc_basis", "eth_basis", "eth_leveraged", 
            "usdt_market_neutral", "usdt_market_neutral_no_leverage"
        ]
        
        if mode_name in hedge_strategies:
            if "component_config" not in config_data:
                config_data["component_config"] = {}
            if "strategy_manager" not in config_data["component_config"]:
                config_data["component_config"]["strategy_manager"] = {}
            if "position_calculation" not in config_data["component_config"]["strategy_manager"]:
                config_data["component_config"]["strategy_manager"]["position_calculation"] = {}
            
            config_data["component_config"]["strategy_manager"]["position_calculation"]["hedge_allocation"] = {
                "binance": 0.4,
                "bybit": 0.3,
                "okx": 0.3
            }
    
    def update_instrument_definitions(self):
        """Add instrument type mapping to INSTRUMENT_DEFINITIONS.md."""
        print("🔧 Updating INSTRUMENT_DEFINITIONS.md...")
        
        instrument_defs_file = self.docs_dir / "INSTRUMENT_DEFINITIONS.md"
        
        try:
            with open(instrument_defs_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add instrument type mapping section
            type_mapping_section = """
## Instrument Type Classification

For PnL aggregation, reporting, plotting, equity calculation, and LTV calculation, instruments are classified by type:

### Type Definitions

- **Asset**: Instruments representing owned value
  - `BaseToken`: Native tokens (USDT, ETH, BTC)
  - `aToken`: AAVE supplied tokens (aUSDT, aETH)
  - `LST`: Liquid staking tokens (stETH, weETH)

- **Debt**: Instruments representing borrowed value
  - `debtToken`: AAVE borrowed tokens (debtUSDT, debtETH)

- **Derivative**: Instruments representing synthetic positions
  - `Perp`: Perpetual futures positions (BTC-PERP, ETH-PERP)

### Type Mapping Function

```python
def get_instrument_type(position_key: str) -> str:
    \"\"\"Get instrument type from position key.\"\"\"
    parts = position_key.split(':')
    if len(parts) != 3:
        return 'unknown'
    
    venue, position_type, symbol = parts
    
    if position_type == 'BaseToken':
        return 'asset'
    elif position_type == 'aToken':
        return 'asset'
    elif position_type == 'LST':
        return 'asset'
    elif position_type == 'debtToken':
        return 'debt'
    elif position_type == 'Perp':
        return 'derivative'
    else:
        return 'unknown'
```

### Usage Examples

- **PnL Aggregation**: Sum PnL by instrument type
- **Equity Calculation**: Assets - Debts + Derivative Value
- **LTV Calculation**: Total Debt / Total Assets
- **Reporting**: Group positions by type for clarity
"""
            
            # Insert after the main content but before any existing sections
            if "## Instrument Type Classification" not in content:
                # Find a good insertion point (after the main content)
                insertion_point = content.find("## Position Key Validation")
                if insertion_point == -1:
                    insertion_point = content.find("## Migration Guide")
                if insertion_point == -1:
                    insertion_point = len(content)
                
                content = content[:insertion_point] + type_mapping_section + "\n" + content[insertion_point:]
                
                with open(instrument_defs_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("  ✅ Added instrument type classification to INSTRUMENT_DEFINITIONS.md")
            else:
                print("  ℹ️  Instrument type classification already exists")
                
        except Exception as e:
            print(f"  ❌ Error updating INSTRUMENT_DEFINITIONS.md: {e}")
    
    def update_specs_to_remove_configs(self):
        """Update specs to remove references to deleted configs."""
        print("🔧 Updating specs to remove deleted config references...")
        
        # Find all spec files
        spec_files = list(self.docs_dir.glob("specs/*.md")) + list(self.docs_dir.glob("specs/strategies/*.md"))
        
        for spec_file in spec_files:
            try:
                with open(spec_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Remove references to deleted configs
                for config_to_remove in self.configs_to_remove:
                    # Remove lines that reference this config
                    lines = content.split('\n')
                    filtered_lines = []
                    for line in lines:
                        if config_to_remove not in line:
                            filtered_lines.append(line)
                    content = '\n'.join(filtered_lines)
                
                if content != original_content:
                    with open(spec_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✅ Updated {spec_file}")
                else:
                    print(f"  ℹ️  No changes needed in {spec_file}")
                    
            except Exception as e:
                print(f"  ❌ Error updating {spec_file}: {e}")
    
    def run_all_fixes(self):
        """Run all config fixes."""
        print("🚀 Starting comprehensive config fixes...")
        print("=" * 60)
        
        self.fix_mode_configs()
        print()
        
        self.update_instrument_definitions()
        print()
        
        self.update_specs_to_remove_configs()
        print()
        
        print("=" * 60)
        print("✅ Comprehensive config fixes completed!")

if __name__ == "__main__":
    fixer = ConfigIssuesFixer()
    fixer.run_all_fixes()
