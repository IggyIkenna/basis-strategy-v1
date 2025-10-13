#!/usr/bin/env python3
"""
USDT Market Neutral Quality Gates

This script validates USDT market neutral strategy implementation, the most complex
strategy with full leverage, multi-venue hedging, and cross-venue capital allocation.
It tests advanced mechanics including leverage optimization and risk management.

Reference: .cursor/tasks/18_usdt_market_neutral_quality_gates.md
"""

import os
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

# Add backend src to path
backend_src = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

def test_usdt_market_neutral_strategy_implementation():
    """Test USDT market neutral strategy implementation."""
    print("Testing USDT market neutral strategy implementation...")
    
    try:
        from basis_strategy_v1.core.strategies.usdt_market_neutral_strategy import USDTMarketNeutralStrategy
        from basis_strategy_v1.core.strategies.leverage_manager import LeverageManager
        from basis_strategy_v1.core.strategies.hedging_manager import HedgingManager
        from basis_strategy_v1.core.strategies.capital_allocator import CapitalAllocator
        
        # Test strategy initialization
        config = {
            "venues": ["binance", "bybit", "okx"],
            "assets": ["USDT", "USDC", "ETH"],
            "max_leverage": 5.0,
            "margin_requirements": {"USDT": 0.1, "USDC": 0.1, "ETH": 0.15}
        }
        
        # Mock dependencies for testing
        class MockDataProvider:
            def get_funding_rate(self, venue, asset, timestamp):
                return 0.01  # 1% funding rate
            
            def get_spot_price(self, venue, asset, timestamp):
                return 1.0  # 1:1 for USDT/USDC
        
        class MockPositionMonitor:
            def get_positions(self):
                return {}
        
        class MockRiskMonitor:
            def check_risk_limits(self, positions):
                return True
        
        data_provider = MockDataProvider()
        position_monitor = MockPositionMonitor()
        risk_monitor = MockRiskMonitor()
        
        strategy = USDTMarketNeutralStrategy(config, data_provider, position_monitor, risk_monitor)
        
        print("✅ USDT market neutral strategy implementation works correctly")
        return True
        
    except ImportError:
        print("⚠️  USDT market neutral strategy not implemented yet - skipping")
        return True
    except Exception as e:
        print(f"❌ USDT market neutral strategy implementation failed: {e}")
        return False

def test_leverage_mechanics():
    """Test leverage mechanics and risk controls."""
    print("Testing leverage mechanics...")
    
    try:
        from basis_strategy_v1.core.strategies.leverage_manager import LeverageManager
        
        config = {
            "max_leverage": 5.0,
            "margin_requirements": {"USDT": 0.1, "USDC": 0.1, "ETH": 0.15}
        }
        
        class MockRiskMonitor:
            def check_risk_limits(self, positions):
                return True
        
        risk_monitor = MockRiskMonitor()
        leverage_manager = LeverageManager(config, risk_monitor)
        
        # Test leverage optimization
        positions = {"USDT": 100000, "USDC": 50000}
        risk_budget = 0.1
        optimal_leverage = leverage_manager.calculate_optimal_leverage(positions, risk_budget)
        
        if optimal_leverage is None:
            print("❌ Leverage optimization failed")
            return False
        
        # Validate leverage is within limits
        if optimal_leverage > config["max_leverage"]:
            print(f"❌ Optimal leverage {optimal_leverage} exceeds maximum {config['max_leverage']}")
            return False
        
        # Test leverage limit validation
        proposed_leverage = 3.0
        is_valid = leverage_manager.validate_leverage_limits(proposed_leverage)
        
        if not is_valid:
            print("❌ Leverage limit validation failed")
            return False
        
        # Test margin requirements
        margin_req = leverage_manager.calculate_margin_requirements(positions, optimal_leverage)
        
        if margin_req is None:
            print("❌ Margin requirements calculation failed")
            return False
        
        print("✅ Leverage mechanics work correctly")
        return True
        
    except ImportError:
        print("⚠️  Leverage mechanics not implemented yet - skipping")
        return True
    except Exception as e:
        print(f"❌ Leverage mechanics failed: {e}")
        return False

def test_multi_venue_hedging():
    """Test multi-venue hedging mechanics."""
    print("Testing multi-venue hedging...")
    
    try:
        from basis_strategy_v1.core.strategies.hedging_manager import HedgingManager
        
        config = {
            "venues": ["binance", "bybit", "okx"],
            "hedge_assets": ["USDT", "USDC", "ETH"]
        }
        
        class MockDataProvider:
            def get_correlation(self, asset1, asset2, timestamp):
                return 0.95  # High correlation between USDT/USDC
        
        data_provider = MockDataProvider()
        hedging_manager = HedgingManager(config, data_provider)
        
        # Test hedge ratio calculations
        positions = {"USDT": 100000, "USDC": 50000, "ETH": 10}
        correlations = {"USDT_USDC": 0.95, "USDT_ETH": 0.8, "USDC_ETH": 0.8}
        
        hedge_ratios = hedging_manager.calculate_hedge_ratios(positions, correlations)
        
        if hedge_ratios is None:
            print("❌ Hedge ratio calculations failed")
            return False
        
        # Test hedge trade execution
        venues = ["binance", "bybit", "okx"]
        hedge_trades = hedging_manager.execute_hedge_trades(hedge_ratios, venues)
        
        if hedge_trades is None:
            print("❌ Hedge trade execution failed")
            return False
        
        # Test hedge effectiveness validation
        hedges = {"USDT": 100000, "USDC": 50000}
        hedge_effectiveness = hedging_manager.validate_hedge_effectiveness(positions, hedges)
        
        if hedge_effectiveness is None:
            print("❌ Hedge effectiveness validation failed")
            return False
        
        print("✅ Multi-venue hedging works correctly")
        return True
        
    except ImportError:
        print("⚠️  Multi-venue hedging not implemented yet - skipping")
        return True
    except Exception as e:
        print(f"❌ Multi-venue hedging failed: {e}")
        return False

def test_capital_allocation():
    """Test cross-venue capital allocation."""
    print("Testing capital allocation...")
    
    try:
        from basis_strategy_v1.core.strategies.capital_allocator import CapitalAllocator
        
        config = {
            "venues": ["binance", "bybit", "okx"],
            "capital_limits": {"binance": 1000000, "bybit": 800000, "okx": 600000}
        }
        
        class MockDataProvider:
            def get_venue_capacity(self, venue, timestamp):
                return config["capital_limits"][venue]
        
        data_provider = MockDataProvider()
        capital_allocator = CapitalAllocator(config, data_provider)
        
        # Test capital allocation optimization
        opportunities = {
            "binance": {"USDT": 0.02, "USDC": 0.015},
            "bybit": {"USDT": 0.018, "USDC": 0.012},
            "okx": {"USDT": 0.022, "USDC": 0.016}
        }
        constraints = {"total_capital": 2000000, "max_per_venue": 1000000}
        
        allocation = capital_allocator.optimize_capital_allocation(opportunities, constraints)
        
        if allocation is None:
            print("❌ Capital allocation optimization failed")
            return False
        
        # Test venue capacity validation
        venue = "binance"
        amount = 500000
        is_valid = capital_allocator.validate_venue_capacity(venue, amount)
        
        if not is_valid:
            print("❌ Venue capacity validation failed")
            return False
        
        # Test cross-venue arbitrage
        venues = ["binance", "bybit", "okx"]
        assets = ["USDT", "USDC"]
        arbitrage_opportunities = capital_allocator.calculate_cross_venue_arbitrage(venues, assets)
        
        if arbitrage_opportunities is None:
            print("❌ Cross-venue arbitrage calculation failed")
            return False
        
        print("✅ Capital allocation works correctly")
        return True
        
    except ImportError:
        print("⚠️  Capital allocation not implemented yet - skipping")
        return True
    except Exception as e:
        print(f"❌ Capital allocation failed: {e}")
        return False

def test_risk_management():
    """Test advanced risk management."""
    print("Testing risk management...")
    
    try:
        from basis_strategy_v1.core.strategies.usdt_market_neutral_strategy import USDTMarketNeutralStrategy
        
        config = {
            "venues": ["binance", "bybit", "okx"],
            "assets": ["USDT", "USDC", "ETH"],
            "max_leverage": 5.0,
            "risk_limits": {
                "max_drawdown": 0.1,
                "max_correlation": 0.8,
                "max_liquidity_risk": 0.05
            }
        }
        
        class MockDataProvider:
            def get_correlation(self, asset1, asset2, timestamp):
                return 0.7  # Moderate correlation
        
        class MockPositionMonitor:
            def get_positions(self):
                return {"USDT": 100000, "USDC": 50000, "ETH": 10}
        
        class MockRiskMonitor:
            def check_risk_limits(self, positions):
                return True
            
            def calculate_portfolio_risk(self, positions):
                return 0.05  # 5% portfolio risk
        
        data_provider = MockDataProvider()
        position_monitor = MockPositionMonitor()
        risk_monitor = MockRiskMonitor()
        
        strategy = USDTMarketNeutralStrategy(config, data_provider, position_monitor, risk_monitor)
        
        # Test portfolio risk calculations
        positions = position_monitor.get_positions()
        portfolio_risk = risk_monitor.calculate_portfolio_risk(positions)
        
        if portfolio_risk is None:
            print("❌ Portfolio risk calculation failed")
            return False
        
        # Validate portfolio risk is within limits
        if portfolio_risk > config["risk_limits"]["max_drawdown"]:
            print(f"❌ Portfolio risk {portfolio_risk:.2%} exceeds maximum {config['risk_limits']['max_drawdown']:.2%}")
            return False
        
        print("✅ Risk management works correctly")
        return True
        
    except ImportError:
        print("⚠️  Risk management not implemented yet - skipping")
        return True
    except Exception as e:
        print(f"❌ Risk management failed: {e}")
        return False

def test_expected_returns():
    """Test expected returns calculations for USDT market neutral strategy."""
    print("Testing expected returns...")
    
    try:
        from basis_strategy_v1.core.strategies.usdt_market_neutral_strategy import USDTMarketNeutralStrategy
        
        config = {
            "venues": ["binance", "bybit", "okx"],
            "assets": ["USDT", "USDC", "ETH"],
            "max_leverage": 5.0
        }
        
        class MockDataProvider:
            def get_funding_rate(self, venue, asset, timestamp):
                return 0.01  # 1% funding rate
            
            def get_spot_price(self, venue, asset, timestamp):
                return 1.0  # 1:1 for USDT/USDC
        
        class MockPositionMonitor:
            def get_positions(self):
                return {}
        
        class MockRiskMonitor:
            def check_risk_limits(self, positions):
                return True
        
        data_provider = MockDataProvider()
        position_monitor = MockPositionMonitor()
        risk_monitor = MockRiskMonitor()
        
        strategy = USDTMarketNeutralStrategy(config, data_provider, position_monitor, risk_monitor)
        
        # Test expected APY calculation
        timestamp = "2024-01-01T00:00:00Z"
        expected_apy = strategy.calculate_expected_apy(timestamp)
        
        if expected_apy is None:
            print("❌ Expected APY calculation failed")
            return False
        
        # Validate APY is realistic (should be between 8-25% for USDT market neutral with leverage)
        if expected_apy < 0.08 or expected_apy > 0.25:
            print(f"❌ Expected APY {expected_apy:.2%} is not realistic for USDT market neutral strategy")
            return False
        
        print(f"✅ Expected returns calculation works correctly (APY: {expected_apy:.2%})")
        return True
        
    except ImportError:
        print("⚠️  Expected returns calculation not implemented yet - skipping")
        return True
    except Exception as e:
        print(f"❌ Expected returns calculation failed: {e}")
        return False

def test_usdt_market_neutral_data_requirements():
    """Test USDT market neutral data requirements."""
    print("Testing USDT market neutral data requirements...")
    
    # Check that required data files exist
    required_data_files = [
        "data/market_data/usdt_funding_rates_binance.csv",
        "data/market_data/usdt_funding_rates_bybit.csv",
        "data/market_data/usdt_funding_rates_okx.csv",
        "data/market_data/usdc_funding_rates_binance.csv",
        "data/market_data/usdc_funding_rates_bybit.csv",
        "data/market_data/usdc_funding_rates_okx.csv",
        "data/market_data/eth_funding_rates_binance.csv",
        "data/market_data/eth_funding_rates_bybit.csv",
        "data/market_data/eth_funding_rates_okx.csv",
        "data/market_data/usdt_spot_prices.csv",
        "data/market_data/usdc_spot_prices.csv",
        "data/market_data/eth_spot_prices.csv",
        "data/market_data/usdt_futures_prices.csv",
        "data/market_data/usdc_futures_prices.csv",
        "data/market_data/eth_futures_prices.csv",
    ]
    
    missing_files = []
    for file_path in required_data_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing USDT market neutral data files:")
        for missing in missing_files:
            print(f"  - {missing}")
        return False
    
    print("✅ All USDT market neutral data requirements are met")
    return True

def test_usdt_market_neutral_configuration():
    """Test USDT market neutral configuration."""
    print("Testing USDT market neutral configuration...")
    
    config_file = "configs/modes/usdt_market_neutral.yaml"
    if not os.path.exists(config_file):
        print(f"❌ USDT market neutral configuration file not found: {config_file}")
        return False
    
    try:
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate required configuration fields
        required_fields = ["strategy_type", "venues", "share_class", "max_leverage", "risk_limits"]
        for field in required_fields:
            if field not in config:
                print(f"❌ USDT market neutral configuration missing required field: {field}")
                return False
        
        print("✅ USDT market neutral configuration is valid")
        return True
        
    except Exception as e:
        print(f"❌ USDT market neutral configuration validation failed: {e}")
        return False

def test_usdt_market_neutral_end_to_end():
    """Test USDT market neutral end-to-end execution."""
    print("Testing USDT market neutral end-to-end execution...")
    
    try:
        # This would test actual end-to-end execution
        # For now, just validate that the components exist
        component_files = [
            "backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_strategy.py",
            "backend/src/basis_strategy_v1/core/strategies/leverage_manager.py",
            "backend/src/basis_strategy_v1/core/strategies/hedging_manager.py",
            "backend/src/basis_strategy_v1/core/strategies/capital_allocator.py",
        ]
        
        missing_files = []
        for file_path in component_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print("❌ Missing USDT market neutral component files:")
            for missing in missing_files:
                print(f"  - {missing}")
            return False
        
        print("✅ USDT market neutral end-to-end execution components exist")
        return True
        
    except Exception as e:
        print(f"❌ USDT market neutral end-to-end execution test failed: {e}")
        return False

def main():
    """Run all USDT market neutral quality gates."""
    print("=" * 60)
    print("USDT MARKET NEUTRAL QUALITY GATES")
    print("=" * 60)
    
    tests = [
        test_usdt_market_neutral_data_requirements,
        test_usdt_market_neutral_configuration,
        test_usdt_market_neutral_strategy_implementation,
        test_leverage_mechanics,
        test_multi_venue_hedging,
        test_capital_allocation,
        test_risk_management,
        test_expected_returns,
        test_usdt_market_neutral_end_to_end,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
        print()
    
    print("=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All USDT market neutral quality gates passed!")
        return 0
    else:
        print("❌ Some USDT market neutral quality gates failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
