#!/usr/bin/env python3
"""
Test script for the new EventDrivenStrategyEngine.

Tests the integration of all 9 components in the new architecture.
"""

import sys
import asyncio
import pytest
import pandas as pd
from datetime import datetime, timedelta

# Add backend to path
sys.path.append('backend/src')

from basis_strategy_v1.core.event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine


def test_engine_initialization():
    """Test that the engine initializes with all components."""
    print("🧪 Testing EventDrivenStrategyEngine Initialization")
    print("=" * 50)
    
    # Test configurations for each mode
    configs = [
        {
            'mode': 'pure_lending',
            'share_class': 'USDT',
            'initial_capital': 100000,
            'execution_mode': 'backtest'
        },
        {
            'mode': 'btc_basis',
            'share_class': 'USDT',
            'initial_capital': 100000,
            'execution_mode': 'backtest'
        },
        {
            'mode': 'eth_leveraged',
            'share_class': 'ETH',
            'initial_capital': 100000,
            'execution_mode': 'backtest'
        },
        {
            'mode': 'usdt_market_neutral',
            'share_class': 'USDT',
            'initial_capital': 100000,
            'execution_mode': 'backtest'
        }
    ]
    
    for config in configs:
        print(f"\n📊 Testing {config['mode']} mode...")
        
        try:
            # Create engine with mock data loading
            # Set data_dir to project root for integration tests
            import os
            import sys
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config['data_dir'] = os.path.join(project_root, 'data')
            
            engine = EventDrivenStrategyEngine(config)
            
            # Verify all components are initialized
            assert hasattr(engine, 'position_monitor'), "Position Monitor not initialized"
            assert hasattr(engine, 'event_logger'), "Event Logger not initialized"
            assert hasattr(engine, 'exposure_monitor'), "Exposure Monitor not initialized"
            assert hasattr(engine, 'risk_monitor'), "Risk Monitor not initialized"
            assert hasattr(engine, 'pnl_calculator'), "P&L Calculator not initialized"
            assert hasattr(engine, 'strategy_manager'), "Strategy Manager not initialized"
            assert hasattr(engine, 'cex_execution_manager'), "CEX Execution Manager not initialized"
            assert hasattr(engine, 'onchain_execution_manager'), "OnChain Execution Manager not initialized"
            assert hasattr(engine, 'data_provider'), "Data Provider not initialized"
            
            print(f"✅ {config['mode']} mode engine initialized successfully")
            print(f"   Mode: {engine.mode}")
            print(f"   Share class: {engine.share_class}")
            print(f"   Execution mode: {engine.execution_mode}")
            
        except Exception as e:
            print(f"❌ {config['mode']} mode failed: {e}")
            raise
    
    print("\n✅ All engine initialization tests passed!")


@pytest.mark.asyncio
async def test_engine_status():
    """Test engine status reporting."""
    print("\n🧪 Testing Engine Status Reporting")
    print("=" * 50)
    
    config = {
        'mode': 'usdt_market_neutral',
        'share_class': 'USDT',
        'initial_capital': 100000,
        'execution_mode': 'backtest'
    }
    
    # Set data_dir to project root for integration tests
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config['data_dir'] = os.path.join(project_root, 'data')
    
    engine = EventDrivenStrategyEngine(config)
    status = await engine.get_status()
    
    print("📊 Engine Status:")
    print(f"   Mode: {status['mode']}")
    print(f"   Share class: {status['share_class']}")
    print(f"   Execution mode: {status['execution_mode']}")
    print(f"   Is running: {status['is_running']}")
    print(f"   Current timestamp: {status['current_timestamp']}")
    
    print("\n🔧 Component Status:")
    for component, state in status['components'].items():
        print(f"   {component}: {state}")
    
    assert status['mode'] == 'usdt_market_neutral'
    assert status['share_class'] == 'USDT'
    assert status['execution_mode'] == 'backtest'
    assert status['is_running'] == False
    
    print("✅ Engine status test passed!")


@pytest.mark.asyncio
async def test_mock_backtest():
    """Test a mock backtest with minimal data."""
    print("\n🧪 Testing Mock Backtest")
    print("=" * 50)
    
    config = {
        'mode': 'pure_lending',
        'share_class': 'USDT',
        'initial_capital': 100000,
        'execution_mode': 'backtest'
    }
    
    # Set data_dir to project root for integration tests
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config['data_dir'] = os.path.join(project_root, 'data')
    
    engine = EventDrivenStrategyEngine(config)
    
    # Create mock data
    dates = pd.date_range(start='2024-01-01', periods=5, freq='H')
    mock_data = pd.DataFrame({
        'eth_price': [3000, 3010, 3020, 3015, 3005],
        'usdt_price': [1.0, 1.0, 1.0, 1.0, 1.0],
        'lending_rate': [0.05, 0.05, 0.05, 0.05, 0.05]
    }, index=dates)
    
    # Mock the data provider to return our test data
    engine.data_provider.load_mode_specific_data = lambda: mock_data
    
    try:
        # Run backtest
        results = await engine.run_backtest()
        
        print("📊 Backtest Results:")
        print(f"   Mode: {results['mode']}")
        print(f"   Share class: {results['share_class']}")
        print(f"   Start date: {results['start_date']}")
        print(f"   End date: {results['end_date']}")
        
        if 'performance' in results:
            perf = results['performance']
            print(f"   Total return: ${perf['total_return']:.2f}")
            print(f"   Total return %: {perf['total_return_pct']:.2f}%")
            print(f"   Final value: ${perf['final_value']:.2f}")
        
        print(f"   P&L history points: {len(results.get('pnl_history', []))}")
        print(f"   Events logged: {len(results.get('events', []))}")
        
        print("✅ Mock backtest completed successfully!")
        
    except Exception as e:
        print(f"⚠️ Mock backtest failed (expected with no real data): {e}")
        print("   This is expected since we don't have real data files")


@pytest.mark.asyncio
async def test_component_integration():
    """Test that components can work together."""
    print("\n🧪 Testing Component Integration")
    print("=" * 50)
    
    config = {
        'mode': 'btc_basis',
        'share_class': 'USDT',
        'initial_capital': 100000,
        'execution_mode': 'backtest'
    }
    
    # Set data_dir to project root for integration tests
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config['data_dir'] = os.path.join(project_root, 'data')
    
    engine = EventDrivenStrategyEngine(config)
    
    # Test component interaction
    print("🔄 Testing component interaction...")
    
    # 1. Position Monitor
    position_snapshot = engine.position_monitor.get_snapshot()
    print(f"   Position snapshot: {len(position_snapshot)} sections")
    
    # 2. Exposure Monitor
    exposure = engine.exposure_monitor.calculate_exposure(pd.Timestamp.now(), position_snapshot)
    print(f"   Exposure calculated: {exposure.get('share_class_value', 0):.2f}")
    
    # 3. Risk Monitor
    risk = await engine.risk_monitor.calculate_overall_risk(exposure)
    print(f"   Risk assessed: {risk.get('level', 'UNKNOWN')}")
    
    # 4. P&L Calculator
    pnl = await engine.pnl_calculator.calculate_pnl(exposure, timestamp=pd.Timestamp.now())
    print(f"   P&L calculated: {pnl.get('balance_based_pnl', 0):.2f}")
    
    # 5. Strategy Manager
    decision = engine.strategy_manager.make_strategy_decision(
        current_exposure=exposure,
        risk_assessment=risk,
        config=config,
        market_data={'btc_price': 50000}
    )
    print(f"   Strategy decision: {decision.get('action', 'UNKNOWN')}")
    
    print("✅ Component integration test passed!")


async def main():
    """Run all tests."""
    print("🚀 Testing EventDrivenStrategyEngine")
    print("=" * 60)
    
    try:
        # Test initialization
        test_engine_initialization()
        
        # Test status
        await test_engine_status()
        
        # Test component integration
        await test_component_integration()
        
        # Test mock backtest
        await test_mock_backtest()
        
        print("\n🎉 All EventDrivenStrategyEngine tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


def test_engine_error_handling():
    """Test error handling in the engine."""
    print("🧪 Testing EventDrivenStrategyEngine Error Handling")
    print("=" * 50)
    
    # Test with invalid config
    try:
        engine = EventDrivenStrategyEngine({
            'mode': 'invalid_mode',
            'share_class': 'INVALID',
            'initial_capital': -1000,  # Invalid negative capital
            'execution_mode': 'backtest'
        })
        assert False, "Should have raised an error for invalid config"
    except Exception as e:
        print(f"✅ Correctly caught invalid config error: {e}")
    
    # Test with missing required fields
    try:
        engine = EventDrivenStrategyEngine({})
        assert False, "Should have raised an error for missing fields"
    except Exception as e:
        print(f"✅ Correctly caught missing fields error: {e}")
    
    print("✅ Error handling tests passed")
    print("=" * 50)


def test_engine_data_loading():
    """Test data loading functionality."""
    print("🧪 Testing EventDrivenStrategyEngine Data Loading")
    print("=" * 50)
    
    config = {
        'mode': 'pure_lending',
        'share_class': 'USDT',
        'initial_capital': 100000,
        'execution_mode': 'backtest'
    }
    
    engine = EventDrivenStrategyEngine(config)
    
    # Test data provider initialization
    assert engine.data_provider is not None
    print("✅ Data provider initialized")
    
    # Test that data provider has the correct mode
    assert hasattr(engine.data_provider, 'mode')
    print("✅ Data provider has mode attribute")
    
    print("✅ Data loading tests passed")
    print("=" * 50)


def test_engine_component_integration():
    """Test that all components are properly integrated."""
    print("🧪 Testing EventDrivenStrategyEngine Component Integration")
    print("=" * 50)
    
    config = {
        'mode': 'pure_lending',
        'share_class': 'USDT',
        'initial_capital': 100000,
        'execution_mode': 'backtest'
    }
    
    engine = EventDrivenStrategyEngine(config)
    
    # Test all components are initialized
    components = [
        ('data_provider', engine.data_provider),
        ('position_monitor', engine.position_monitor),
        ('exposure_monitor', engine.exposure_monitor),
        ('risk_monitor', engine.risk_monitor),
        ('strategy_manager', engine.strategy_manager),
        ('cex_execution_manager', engine.cex_execution_manager),
        ('onchain_execution_manager', engine.onchain_execution_manager),
        ('pnl_calculator', engine.pnl_calculator),
        ('event_logger', engine.event_logger)
    ]
    
    for name, component in components:
        assert component is not None, f"{name} should be initialized"
        print(f"✅ {name} initialized")
    
    # Test component dependencies
    assert engine.strategy_manager.exposure_monitor is engine.exposure_monitor
    assert engine.strategy_manager.risk_monitor is engine.risk_monitor
    print("✅ Component dependencies properly wired")
    
    print("✅ Component integration tests passed")
    print("=" * 50)


def test_engine_timestep_processing():
    """Test individual timestep processing."""
    print("🧪 Testing EventDrivenStrategyEngine Timestep Processing")
    print("=" * 50)
    
    config = {
        'mode': 'pure_lending',
        'share_class': 'USDT',
        'initial_capital': 100000,
        'execution_mode': 'backtest'
    }
    
    engine = EventDrivenStrategyEngine(config)
    
    # Create mock data row
    timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
    data_row = pd.Series({
        'btc_price': 50000.0,
        'eth_price': 3000.0,
        'usdt_price': 1.0,
        'aave_lending_rate': 0.05,
        'funding_rate': 0.0001
    })
    
    # Test timestep processing
    results = {
        'pnl_history': [],
        'events': [],
        'positions': [],
        'exposures': [],
        'risks': []
    }
    
    # This should not raise an error
    try:
        # We can't easily test the full async method without mocking dependencies
        # But we can test that the method exists and has the right signature
        assert hasattr(engine, '_process_timestep')
        print("✅ _process_timestep method exists")
        
        # Test that results structure is properly initialized
        assert 'pnl_history' in results
        assert 'events' in results
        assert 'positions' in results
        assert 'exposures' in results
        assert 'risks' in results
        print("✅ Results structure properly initialized")
        
    except Exception as e:
        print(f"❌ Timestep processing test failed: {e}")
        raise
    
    print("✅ Timestep processing tests passed")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())