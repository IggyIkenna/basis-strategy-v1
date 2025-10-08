"""
Create AAVE Risk Parameters JSON
Extracts AAVE risk parameters from the official AAVE v3 parameters CSV and creates a single reference file.
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path

def create_aave_risk_params():
    """Create AAVE risk parameters JSON from official AAVE v3 parameters CSV."""
    
    # Load AAVE v3 parameters from CSV
    csv_path = Path("data/manual_sources/aave_params/aave_current_v3_prams_etherum_mainnet.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"AAVE parameters CSV not found at {csv_path}")
    
    # Read CSV with proper header handling - first column contains parameter names
    df = pd.read_csv(csv_path, header=0)
    # Set the first column (Unnamed: 0) as index to make it easier to access rows by parameter name
    df = df.set_index('Unnamed: 0')
    
    # Extract parameters for key assets
    key_assets = ['WETH', 'wstETH', 'weETH', 'USDT', 'ETH']
    
    # Helper function to extract parameter value from CSV
    def get_param_value(param_name, asset_name):
        """Extract parameter value for a specific asset from CSV."""
        if param_name in df.index and asset_name in df.columns:
            value_str = df.loc[param_name, asset_name]
            if pd.isna(value_str) or value_str == '' or value_str == 'N/A':
                return None
            # Remove % and convert to decimal
            try:
                return float(str(value_str).replace('%', '')) / 100
            except (ValueError, TypeError):
                return None
        return None
    
    # AAVE V3 Risk Parameters (extracted from official CSV)
    risk_params = {
        "metadata": {
            "created": datetime.now().isoformat(),
            "source": "data/manual_sources/aave_params/aave_current_v3_prams_etherum_mainnet.csv",
            "description": "AAVE V3 risk parameters for liquidation and LTV calculations",
            "last_updated": "2025-09-26",
            "version": "aave_v3_current",
            "reference": "https://aave.com/docs/resources/parameters"
        },
        "normal_mode": {
            "description": "Standard mode LTV limits and liquidation thresholds (from official AAVE v3 CSV)",
            "liquidation_thresholds": {
                asset: get_param_value('Liquidation Threshold', asset) 
                for asset in key_assets 
                if get_param_value('Liquidation Threshold', asset) is not None
            },
            "max_ltv_limits": {
                asset: get_param_value('LTV', asset) 
                for asset in key_assets 
                if get_param_value('LTV', asset) is not None
            },
            "liquidation_bonuses": {
                asset: get_param_value('Liquidation Bonus', asset) 
                for asset in key_assets 
                if get_param_value('Liquidation Bonus', asset) is not None
            }
        },
        "emode": {
            "description": "ETH-correlated eMode (Ethereum v3 Core) - applies when both collateral and debt are ETH-correlated",
            "eligible_pairs": ["wstETH_WETH", "weETH_WETH"],
            "liquidation_thresholds": {
                "wstETH_WETH": 0.95,  # 95% liquidation threshold in eMode
                "weETH_WETH": 0.95    # 95% liquidation threshold in eMode
            },
            "max_ltv_limits": {
                "wstETH_WETH": 0.93,  # 93% max LTV in eMode
                "weETH_WETH": 0.93    # 93% max LTV in eMode
            },
            "liquidation_bonus": {
                "wstETH_WETH": 0.01,  # 1% liquidation bonus in eMode
                "weETH_WETH": 0.01    # 1% liquidation bonus in eMode
            }
        },
        "risk_calculation_formula": {
            "description": "HF-based LTV targeting formula used in the system",
            "formula": "LTV_target = LT * (1 - (u + s + β·b)) / HF_target_after",
            "parameters": {
                "LT": "Liquidation Threshold (from above)",
                "u": "max_underlying_move (user risk tolerance)",
                "s": "max_staked_basis_move (user risk tolerance)", 
                "b": "max_spot_perp_basis_move (user risk tolerance)",
                "β": "beta_basis_as_collateral (basis risk weighting)",
                "HF_target_after": "hf_target_after_shock (target health factor)"
            }
        },
        "usage_notes": {
            "normal_mode": "Use for cross-asset borrowing (e.g., USDT collateral → ETH borrow)",
            "emode": "Use for same-underlying borrowing (e.g., wstETH collateral → WETH borrow). NOTE: eMode affects risk parameters (LTV/LT/LB) but NOT interest rates",
            "liquidation_threshold": "LTV level where liquidation occurs",
            "max_ltv": "Maximum LTV for new borrowing (before liquidation threshold)",
            "safety_margin": "Always operate below max_ltv with additional safety buffer",
            "interest_rates": "Interest rates are the same in both normal mode and eMode - only risk parameters change"
        }
    }
    
    # Save to risk_params directory
    output_dir = Path("data/protocol_data/aave/risk_params")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "aave_v3_risk_parameters.json"
    
    with open(output_file, 'w') as f:
        json.dump(risk_params, f, indent=2)
    
    print("🎯 AAVE Risk Parameters Created:")
    print("=" * 50)
    print(f"📄 Output: {output_file}")
    print(f"📊 Normal mode assets: {len(risk_params['normal_mode']['liquidation_thresholds'])}")
    print(f"📊 E-mode pairs: {len(risk_params['emode']['liquidation_thresholds'])}")
    
    print(f"\\n📋 Key Parameters:")
    print(f"   wstETH liquidation threshold: {risk_params['normal_mode']['liquidation_thresholds']['wstETH']:.1%}")
    print(f"   wstETH max LTV: {risk_params['normal_mode']['max_ltv_limits']['wstETH']:.1%}")
    print(f"   wstETH E-mode liquidation: {risk_params['emode']['liquidation_thresholds']['wstETH_WETH']:.1%}")
    print(f"   wstETH E-mode max LTV: {risk_params['emode']['max_ltv_limits']['wstETH_WETH']:.1%}")
    
    return risk_params

if __name__ == "__main__":
    result = create_aave_risk_params()
    print("\\n✅ AAVE risk parameters JSON created successfully!")
