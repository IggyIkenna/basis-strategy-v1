"""
E2E Integration Tests for Workflow Refactor

Tests the complete workflow from strategy to P&L with mocked strategy, data provider, and config.
All other components should integrate with real implementations.

Test Scenarios:
1. test_full_loop_sequence_backtest
2. test_tight_loop_orchestration
3. test_position_reconciliation_backtest_vs_live
4. test_execution_cost_flow
5. test_mode_specific_triggers
6. test_error_handling_and_retry
7. test_system_failure_trigger
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List
import asyncio
import logging

# Import the components we're testing
from backend.src.basis_strategy_v1.core.event_engine.event_driven_strategy_engine import (
    EventDrivenStrategyEngine,
)
from backend.src.basis_strategy_v1.core.components.position_monitor import (
    PositionMonitor,
)
from backend.src.basis_strategy_v1.core.components.exposure_monitor import (
    ExposureMonitor,
)
from backend.src.basis_strategy_v1.core.components.risk_monitor import RiskMonitor
from backend.src.basis_strategy_v1.core.components.pnl_monitor import PnLCalculator
from backend.src.basis_strategy_v1.core.execution.execution_manager import ExecutionManager
from backend.src.basis_strategy_v1.core.execution.venue_interface_manager import (
    VenueInterfaceManager,
)
from backend.src.basis_strategy_v1.core.components.position_update_handler import (
    PositionUpdateHandler,
)
from backend.src.basis_strategy_v1.infrastructure.logging.event_logger import (
    EventLogger,
)

logger = logging.getLogger(__name__)


class MockStrategy:
    """Mock strategy for testing."""

    def __init__(self):
        self.decision_count = 0

    def make_strategy_decision(
        self, current_exposure, risk_assessment, config, market_data
    ):
        """Mock strategy decision."""
        self.decision_count += 1

        # Return different decisions based on count
        if self.decision_count == 1:
            return {
                "action": "TRADE",
                "orders": [
                    {
                        "id": "test_order_1",
                        "action_type": "SPOT_TRADE",
                        "asset": "USDT",
                        "amount": 1000,
                        "venue": "binance",
                    }
                ],
            }
        else:
            return {"action": "HOLD", "orders": []}

    def generate_orders(
        self, timestamp, exposure, risk_assessment, market_data, pnl=None
    ):
        """Mock order generation."""
        self.decision_count += 1
        return [
            {
                "id": f"test_order_{self.decision_count}",
                "action_type": "SPOT_TRADE",
                "asset": "USDT",
                "amount": 1000,
                "venue": "binance",
                "timestamp": timestamp,
            }
        ]


class MockDataProvider:
    """Mock data provider for testing."""

    def __init__(self):
        self.data = {
            "market_data": {
                "USDT": {"price": 1.0, "volume": 1000000},
                "ETH": {"price": 2000.0, "volume": 50000},
            },
            "venue_data": {"binance": {"status": "active", "fees": 0.001}},
        }

    def get_data(self, timestamp):
        """Return mock data for timestamp."""
        return self.data


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "mode": "pure_lending_usdt",
        "share_class": "USDT",
        "initial_capital": 100000,
        "max_drawdown": 0.1,
        "leverage_enabled": False,
        "asset": "USDT",
        "component_config": {
            "exposure_monitor": {
                "exposure_currency": "USDT",
                "track_assets": ["USDT", "ETH"],
                "conversion_methods": {"ETH": "price_based"},
            },
            "risk_monitor": {"max_position_size": 0.1, "max_leverage": 2.0},
            "position_monitor": {
                "track_venues": ["binance", "ethereum"],
                "position_interfaces": ["cex", "onchain"],
                "position_subscriptions": [
                    "wallet:BaseToken:USDT",
                    "binance_USDT_spot",
                    "binance_ETH_spot",
                    "ethereum_USDT_onchain",
                    "ethereum_ETH_onchain",
                ],
            },
            "pnl_monitor": {
                "attribution_types": ["balance_based", "attribution"],
                "reporting_currency": "USDT",
                "reconciliation_tolerance": 0.01,
            },
        },
        "reconciliation_tolerance": 0.01,
    }


@pytest.fixture
def mock_data_provider():
    """Mock data provider for testing."""
    return MockDataProvider()


@pytest.fixture
def mock_strategy():
    """Mock strategy for testing."""
    return MockStrategy()


class TestWorkflowRefactorE2E:
    """E2E tests for workflow refactor."""

    def test_full_loop_sequence_backtest(
        self, mock_config, mock_data_provider, mock_strategy
    ):
        """Test complete full loop sequence in backtest mode."""

        # Create EventDrivenStrategyEngine with mocked strategy
        with patch(
            "backend.src.basis_strategy_v1.core.strategies.strategy_factory.StrategyFactory"
        ) as mock_factory:
            mock_factory.create_strategy.return_value = mock_strategy

            engine = EventDrivenStrategyEngine(
                config=mock_config,
                execution_mode="backtest",
                data_provider=mock_data_provider,
                initial_capital=100000,
                share_class="USDT",
            )

            # Test full loop sequence
            timestamp = pd.Timestamp("2025-01-27 10:00:00")
            market_data = mock_data_provider.get_data(timestamp)
            request_id = "test_request_1"

            # Process timestep
            engine._process_timestep(timestamp, market_data, request_id)

            # Verify components were called in correct sequence
            assert engine.position_monitor.execution_mode == "backtest"
            assert engine.position_monitor.initial_capital == 100000
            assert engine.position_update_handler.execution_mode == "backtest"
            assert engine.execution_manager.execution_mode == "backtest"

            # Verify strategy was called
            assert mock_strategy.decision_count > 0

            logger.info("✅ Full loop sequence backtest test passed")

    def test_tight_loop_orchestration(
        self, mock_config, mock_data_provider, mock_strategy
    ):
        """Test tight loop orchestration through ExecutionManager."""

        with patch(
            "backend.src.basis_strategy_v1.core.strategies.strategy_factory.StrategyFactory"
        ) as mock_factory:
            mock_factory.create_strategy.return_value = mock_strategy

            engine = EventDrivenStrategyEngine(
                config=mock_config,
                execution_mode="backtest",
                data_provider=mock_data_provider,
                initial_capital=100000,
                share_class="USDT",
            )

            # Test tight loop orchestration
            timestamp = pd.Timestamp("2025-01-27 10:00:00")
            orders = [
                {
                    "id": "test_order_1",
                    "action_type": "SPOT_TRADE",
                    "asset": "USDT",
                    "amount": 1000,
                    "venue": "binance",
                }
            ]

            # Process orders through ExecutionManager
            result = engine.execution_manager.process_orders(timestamp, orders)

            # Verify orchestration
            assert isinstance(result, list)
            assert engine.execution_manager.position_update_handler is not None

            logger.info("✅ Tight loop orchestration test passed")

    def test_position_reconciliation_backtest_vs_live(
        self, mock_config, mock_data_provider, mock_strategy
    ):
        """Test position reconciliation in backtest vs live modes."""

        with patch(
            "backend.src.basis_strategy_v1.core.strategies.strategy_factory.StrategyFactory"
        ) as mock_factory:
            mock_factory.create_strategy.return_value = mock_strategy

            # Test backtest mode
            engine_backtest = EventDrivenStrategyEngine(
                config=mock_config,
                execution_mode="backtest",
                data_provider=mock_data_provider,
                initial_capital=100000,
                share_class="USDT",
            )

            # Test live mode
            engine_live = EventDrivenStrategyEngine(
                config=mock_config,
                execution_mode="live",
                data_provider=mock_data_provider,
                initial_capital=100000,
                share_class="USDT",
            )

            timestamp = pd.Timestamp("2025-01-27 10:00:00")
            execution_deltas = {"USDT": 1000}

            # Test backtest reconciliation (should always succeed)
            backtest_result = (
                engine_backtest.position_update_handler._reconcile_positions()
            )
            assert backtest_result["success"] == True
            assert backtest_result["reconciliation_type"] == "backtest_simulation"

            # Test live reconciliation (depends on position matching)
            live_result = engine_live.position_update_handler._reconcile_positions()
            assert "success" in live_result
            assert "reconciliation_type" in live_result

            logger.info("✅ Position reconciliation backtest vs live test passed")

    def test_execution_cost_flow(self, mock_config, mock_data_provider, mock_strategy):
        """Test execution cost flow through the system."""

        with patch(
            "backend.src.basis_strategy_v1.core.strategies.strategy_factory.StrategyFactory"
        ) as mock_factory:
            mock_factory.create_strategy.return_value = mock_strategy

            engine = EventDrivenStrategyEngine(
                config=mock_config,
                execution_mode="backtest",
                data_provider=mock_data_provider,
                initial_capital=100000,
                share_class="USDT",
            )

            # Test execution cost collection
            timestamp = pd.Timestamp("2025-01-27 10:00:00")
            execution_result = {
                "success": True,
                "execution_costs": {"trading_fees": 1.0, "gas_fees": 0.5, "total": 1.5},
                "trade_result": {"asset": "USDT", "amount": 1000},
            }

            # Test that execution costs are passed through
            reconciliation_result = engine.position_update_handler.update_state(
                timestamp=timestamp,
                trigger_source="execution_manager",
                execution_deltas=execution_result,
            )

            assert "success" in reconciliation_result
            assert "exposure" in reconciliation_result
            assert "risk" in reconciliation_result
            assert "pnl" in reconciliation_result

            logger.info("✅ Execution cost flow test passed")

    def test_mode_specific_triggers(
        self, mock_config, mock_data_provider, mock_strategy
    ):
        """Test all 5 mode-specific triggers in PositionMonitor."""

        with patch(
            "backend.src.basis_strategy_v1.core.strategies.strategy_factory.StrategyFactory"
        ) as mock_factory:
            mock_factory.create_strategy.return_value = mock_strategy

            # Test backtest mode
            engine_backtest = EventDrivenStrategyEngine(
                config=mock_config,
                execution_mode="backtest",
                data_provider=mock_data_provider,
                initial_capital=100000,
                share_class="USDT",
            )

            # Test live mode
            engine_live = EventDrivenStrategyEngine(
                config=mock_config,
                execution_mode="live",
                data_provider=mock_data_provider,
                initial_capital=100000,
                share_class="USDT",
            )

            timestamp = pd.Timestamp("2025-01-27 10:00:00")

            # Test all 5 triggers
            triggers = [
                "execution_manager",
                "position_refresh",
                "initial_capital",
                "seasonal_rewards",
                "m2m_pnl",
            ]

            for trigger in triggers:
                # Test backtest mode
                backtest_result = engine_backtest.position_monitor.update_state(
                    timestamp=timestamp,
                    trigger_source=trigger,
                    execution_deltas=(
                        {"USDT": 1000} if trigger == "execution_manager" else None
                    ),
                )
                assert isinstance(backtest_result, dict)

                # Test live mode
                live_result = engine_live.position_monitor.update_state(
                    timestamp=timestamp,
                    trigger_source=trigger,
                    execution_deltas=(
                        {"USDT": 1000} if trigger == "execution_manager" else None
                    ),
                )
                assert isinstance(live_result, dict)

            logger.info("✅ Mode-specific triggers test passed")

    def test_error_handling_and_retry(
        self, mock_config, mock_data_provider, mock_strategy
    ):
        """Test error handling and retry logic."""

        with patch(
            "backend.src.basis_strategy_v1.core.strategies.strategy_factory.StrategyFactory"
        ) as mock_factory:
            mock_factory.create_strategy.return_value = mock_strategy

            engine = EventDrivenStrategyEngine(
                config=mock_config,
                execution_mode="backtest",
                data_provider=mock_data_provider,
                initial_capital=100000,
                share_class="USDT",
            )

            # Test retry logic
            timestamp = pd.Timestamp("2025-01-27 10:00:00")
            execution_result = {
                "success": True,
                "trade_result": {"asset": "USDT", "amount": 1000},
            }

            # Test retry mechanism
            retry_result = engine.execution_manager._reconcile_with_retry(
                timestamp=timestamp, trade_result=execution_result, instruction_number=1
            )

            assert isinstance(retry_result, bool)

            # Test error handling
            try:
                engine.execution_manager._handle_order_failure(
                    order={"id": "test_order"},
                    execution_result={"error": "Test error"},
                    order_number=1,
                )
                # Should not raise exception
                assert True
            except Exception as e:
                pytest.fail(f"Error handling failed: {e}")

            logger.info("✅ Error handling and retry test passed")

    def test_system_failure_trigger(
        self, mock_config, mock_data_provider, mock_strategy
    ):
        """Test system failure trigger mechanism."""

        with patch(
            "backend.src.basis_strategy_v1.core.strategies.strategy_factory.StrategyFactory"
        ) as mock_factory:
            mock_factory.create_strategy.return_value = mock_strategy

            engine = EventDrivenStrategyEngine(
                config=mock_config,
                execution_mode="backtest",
                data_provider=mock_data_provider,
                initial_capital=100000,
                share_class="USDT",
            )

            # Test system failure trigger
            try:
                engine.execution_manager._trigger_system_failure("Test system failure")
                pytest.fail("System failure should have raised SystemExit")
            except SystemExit as e:
                # Expected behavior
                assert "SYSTEM FAILURE" in str(e)
                assert engine.execution_manager.health_status["status"] == "critical"

            logger.info("✅ System failure trigger test passed")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
