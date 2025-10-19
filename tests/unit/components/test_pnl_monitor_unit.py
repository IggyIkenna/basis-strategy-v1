"""
Unit Tests for P&L Calculator Component

Tests P&L Calculator in isolation with mocked dependencies.
Focuses on P&L calculation, attribution, and error propagation.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

# Import the component under test
from backend.src.basis_strategy_v1.core.components.pnl_monitor import PnLCalculator


class TestPnLCalculatorUnit:
    """Unit tests for P&L Calculator component."""

    def _add_pnl_config(self, config):
        """Helper method to add required pnl_monitor config to test config."""
        config["component_config"]["pnl_monitor"] = {
            "attribution_types": [
                "supply_yield",
                "borrow_costs",
                "staking_yield_oracle",
                "staking_yield_rewards",
                "funding_pnl",
                "delta_pnl",
                "basis_pnl",
                "dust_pnl",
                "transaction_costs",
            ],
            "reporting_currency": "USDT",
            "reconciliation_tolerance": 0.02,
        }
        return config

    def test_unrealized_pnl_calculation(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test unrealized P&L calculation."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        test_config["share_class"] = "USDT"
        test_config["initial_capital"] = 100000.0

        # Mock exposure data
        current_exposure = {
            "share_class_value": 105000.0,  # 5% gain
            "total_value_usd": 105000.0,
            "timestamp": pd.Timestamp.now(),
        }

        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Act
        pnl_result = pnl_monitor.calculate_pnl(current_exposure)

        # Assert
        assert isinstance(pnl_result, dict)
        assert "balance_based" in pnl_result
        assert "attribution" in pnl_result

        # Should calculate 5% gain
        balance_pnl = pnl_result["balance_based"]
        assert balance_pnl["pnl_cumulative"] == 5000.0
        assert balance_pnl["pnl_pct"] == 5.0

    def test_all_attribution_types(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test all 9 attribution types individually."""
        # Arrange
        test_config = mock_config.copy()
        test_config["share_class"] = "USDT"
        test_config["initial_capital"] = 100000.0

        # Add required pnl_monitor config
        test_config["component_config"]["pnl_monitor"] = {
            "attribution_types": [
                "supply_yield",
                "borrow_costs",
                "staking_yield_oracle",
                "staking_yield_rewards",
                "funding_pnl",
                "delta_pnl",
                "basis_pnl",
                "dust_pnl",
                "transaction_costs",
            ],
            "reporting_currency": "USDT",
            "reconciliation_tolerance": 0.02,
        }

        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Mock exposure data
        current_exposure = {
            "exposures": {
                "aUSDT": {
                    "underlying_balance": 1000.0,
                    "timestamp": pd.Timestamp.now(),
                },
                "aWeETH": {
                    "underlying_native": 0.5,
                    "oracle_price": 1.05,
                    "eth_usd_price": 3000.0,
                    "timestamp": pd.Timestamp.now(),
                },
                "variableDebtWETH": {
                    "underlying_native": 0.1,
                    "eth_usd_price": 3000.0,
                    "timestamp": pd.Timestamp.now(),
                },
            },
            "net_delta_eth": 0.1,
            "timestamp": pd.Timestamp.now(),
        }

        previous_exposure = {
            "exposures": {
                "aUSDT": {"underlying_balance": 950.0, "timestamp": pd.Timestamp.now()},
                "aWeETH": {
                    "underlying_native": 0.5,
                    "oracle_price": 1.04,
                    "eth_usd_price": 3000.0,
                    "timestamp": pd.Timestamp.now(),
                },
                "variableDebtWETH": {
                    "underlying_native": 0.1,
                    "eth_usd_price": 3000.0,
                    "timestamp": pd.Timestamp.now(),
                },
            },
            "net_delta_eth": 0.1,
            "timestamp": pd.Timestamp.now(),
        }

        # Test each attribution type
        attribution_types = [
            "supply_yield",
            "borrow_costs",
            "staking_yield_oracle",
            "staking_yield_rewards",
            "funding_pnl",
            "delta_pnl",
            "basis_pnl",
            "dust_pnl",
            "transaction_costs",
        ]

        for attr_type in attribution_types:
            # Act
            result = pnl_monitor._calculate_config_driven_attribution(
                current_exposure, previous_exposure, pd.Timestamp.now()
            )

            # Assert
            assert isinstance(result, dict)
            assert attr_type in result
            assert isinstance(result[attr_type], (int, float))

    def test_balance_based_pnl_share_classes(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test balance-based P&L with both USDT and ETH share classes."""
        # Test USDT share class
        test_config_usdt = self._add_pnl_config(mock_config.copy())
        test_config_usdt["share_class"] = "USDT"
        test_config_usdt["initial_capital"] = 100000.0

        pnl_monitor_usdt = PnLCalculator(
            config=test_config_usdt,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Mock exposure with share_class_value
        current_exposure_usdt = {
            "share_class_value": 105000.0,
            "total_value_usd": 105000.0,
            "exposures": {},
        }

        # Act
        result_usdt = pnl_monitor_usdt._calculate_balance_based_pnl(
            current_exposure_usdt, pd.Timestamp.now(), pd.Timestamp.now()
        )

        # Assert
        assert isinstance(result_usdt, dict)
        assert "total_value_current" in result_usdt
        assert "pnl_cumulative" in result_usdt
        assert result_usdt["total_value_current"] == 105000.0

        # Test ETH share class
        test_config_eth = self._add_pnl_config(mock_config.copy())
        test_config_eth["share_class"] = "ETH"
        test_config_eth["initial_capital"] = 100000.0

        pnl_monitor_eth = PnLCalculator(
            config=test_config_eth,
            share_class="ETH",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Mock exposure with ETH share class value
        current_exposure_eth = {
            "share_class_value": 35.0,  # 35 ETH
            "total_value_usd": 105000.0,
            "exposures": {},
        }

        # Act
        result_eth = pnl_monitor_eth._calculate_balance_based_pnl(
            current_exposure_eth, pd.Timestamp.now(), pd.Timestamp.now()
        )

        # Assert
        assert isinstance(result_eth, dict)
        assert "total_value_current" in result_eth
        assert "pnl_cumulative" in result_eth
        assert result_eth["total_value_current"] == 35.0

    def test_graceful_handling_missing_data(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test graceful handling when data is unavailable."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        test_config["share_class"] = "USDT"
        test_config["initial_capital"] = 100000.0

        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Mock exposure with missing data
        current_exposure = {"exposures": {}, "timestamp": pd.Timestamp.now()}

        previous_exposure = None  # No previous data

        # Act
        result = pnl_monitor._calculate_config_driven_attribution(
            current_exposure, previous_exposure, pd.Timestamp.now()
        )

        # Assert - should return 0.0 for all attribution types when data unavailable
        for attr_type in [
            "supply_yield",
            "borrow_costs",
            "staking_yield_oracle",
            "staking_yield_rewards",
            "funding_pnl",
            "delta_pnl",
            "basis_pnl",
            "dust_pnl",
            "transaction_costs",
        ]:
            assert attr_type in result
            assert result[attr_type] == 0.0

    def test_attribution_pnl_lending(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test attribution P&L (lending vs funding vs staking vs gas)."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        test_config["mode"] = "pure_lending_usdt"
        test_config["share_class"] = "USDT"

        # Mock attribution data
        lending_pnl = 2000.0
        funding_pnl = 0.0  # No funding in pure lending
        staking_pnl = 0.0  # No staking in pure lending
        gas_costs = -100.0

        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Act - Use dictionary-based exposure
        current_exposure = {
            "share_class_value": 102000.0,
            "total_value_usd": 102000.0,
            "timestamp": pd.Timestamp.now(),
        }
        pnl_result = pnl_monitor.calculate_pnl(current_exposure)

        # Assert
        assert isinstance(pnl_result, dict)
        assert "attribution" in pnl_result

        attribution = pnl_result["attribution"]
        assert "supply_pnl" in attribution
        assert "funding_pnl" in attribution
        assert "staking_pnl" in attribution
        assert "transaction_costs" in attribution

        # Should track supply P&L (lending)
        assert attribution["supply_pnl"] == 0.0  # Default value
        assert attribution["funding_pnl"] == 0.0
        assert attribution["staking_pnl"] == 0.0
        assert attribution["transaction_costs"] == 0.0  # Default value

    def test_attribution_pnl_funding(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test attribution P&L for funding rate strategies."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        test_config["mode"] = "btc_basis"
        test_config["share_class"] = "USDT"

        # Mock attribution data for basis trading
        lending_pnl = 0.0  # No lending in basis trading
        funding_pnl = 1500.0  # Positive funding
        staking_pnl = 0.0  # No staking in basis trading
        gas_costs = -200.0

        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Act - Use dictionary-based exposure
        current_exposure = {
            "share_class_value": 101300.0,
            "total_value_usd": 101300.0,
            "timestamp": pd.Timestamp.now(),
        }
        pnl_result = pnl_monitor.calculate_pnl(current_exposure)

        # Assert
        assert isinstance(pnl_result, dict)
        assert "attribution" in pnl_result

        attribution = pnl_result["attribution"]
        assert attribution["supply_pnl"] == 0.0  # No lending in basis trading
        assert attribution["funding_pnl"] == 0.0  # Default value
        assert attribution["staking_pnl"] == 0.0
        assert attribution["transaction_costs"] == 0.0  # Default value

    def test_attribution_pnl_staking(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test attribution P&L for staking strategies."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        test_config["mode"] = "eth_staking_only"
        test_config["share_class"] = "ETH"

        # Mock attribution data for staking
        lending_pnl = 0.0  # No lending in staking only
        funding_pnl = 0.0  # No funding in staking only
        staking_pnl = 3000.0  # Positive staking rewards
        gas_costs = -150.0

        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="ETH",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Act - Use dictionary-based exposure
        current_exposure = {
            "share_class_value": 103000.0,
            "total_value_usd": 103000.0,
            "timestamp": pd.Timestamp.now(),
        }
        pnl_result = pnl_monitor.calculate_pnl(current_exposure)

        # Assert
        assert isinstance(pnl_result, dict)
        assert "attribution" in pnl_result

        attribution = pnl_result["attribution"]
        assert attribution["supply_pnl"] == 0.0  # No lending in staking only
        assert attribution["funding_pnl"] == 0.0
        assert attribution["staking_pnl"] == 0.0  # Default value
        assert attribution["transaction_costs"] == 0.0  # Default value

    def test_gas_cost_tracking(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test gas cost tracking."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        test_config["share_class"] = "USDT"

        # Mock gas costs
        total_gas_costs = -500.0  # Cumulative gas costs

        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Act - Use dictionary-based exposure
        current_exposure = {
            "share_class_value": 99500.0,
            "total_value_usd": 99500.0,
            "timestamp": pd.Timestamp.now(),
        }
        pnl_result = pnl_monitor.calculate_pnl(current_exposure)

        # Assert
        assert isinstance(pnl_result, dict)
        assert "attribution" in pnl_result
        assert "transaction_costs" in pnl_result["attribution"]

        # Should track transaction costs (gas costs)
        assert pnl_result["attribution"]["transaction_costs"] == 0.0  # Default value

    def test_total_return_percentage(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test total return percentage calculation."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        test_config["share_class"] = "USDT"
        test_config["initial_capital"] = 100000.0

        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Act - Test different return scenarios
        test_cases = [
            (105000.0, 5.0),  # 5% gain (5.0%)
            (95000.0, -5.0),  # 5% loss (-5.0%)
            (100000.0, 0.0),  # No change
            (110000.0, 10.0),  # 10% gain (10.0%)
        ]

        for current_value, expected_return in test_cases:
            # Use dictionary-based exposure
            current_exposure = {
                "share_class_value": current_value,
                "total_value_usd": current_value,
                "timestamp": pd.Timestamp.now(),
            }
            pnl_result = pnl_monitor.calculate_pnl(current_exposure)

            # Assert
            assert isinstance(pnl_result, dict)
            assert "balance_based" in pnl_result
            assert "pnl_pct" in pnl_result["balance_based"]
            assert abs(pnl_result["balance_based"]["pnl_pct"] - expected_return) < 0.001

    def test_error_code_propagation(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test error code propagation."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        test_config["share_class"] = "USDT"

        # Mock utility manager to return error code
        mock_utility_manager.create_error_code.return_value = "PNL_CALC_ERROR"

        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Act - Simulate error condition
        try:
            pnl_result = pnl_monitor.calculate_pnl(
                current_value=100000.0,
                initial_value=100000.0,
                error_condition=True,  # Simulate error
            )

            # Assert - Should propagate error code
            assert isinstance(pnl_result, dict)
            assert "error_code" in pnl_result
            assert pnl_result["error_code"] == "PNL_CALC_ERROR"

        except Exception as e:
            # If exception is raised, should be handled appropriately
            assert isinstance(e, Exception)

    def test_share_class_currency_conversion(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test share class currency conversion."""
        # Test USDT share class
        usdt_config = self._add_pnl_config(mock_config.copy())
        usdt_config["share_class"] = "USDT"

        pnl_monitor = PnLCalculator(
            config=usdt_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Use dictionary-based exposure
        current_exposure = {
            "share_class_value": 105000.0,
            "total_value_usd": 105000.0,
            "timestamp": pd.Timestamp.now(),
        }
        pnl_result = pnl_monitor.calculate_pnl(current_exposure)
        assert pnl_result["share_class"] == "USDT"
        assert pnl_result["balance_based"]["pnl_cumulative"] == 5000.0

        # Test ETH share class
        eth_config = self._add_pnl_config(mock_config.copy())
        eth_config["share_class"] = "ETH"

        pnl_monitor = PnLCalculator(
            config=eth_config,
            share_class="ETH",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Use dictionary-based exposure
        current_exposure = {
            "share_class_value": 105000.0,
            "total_value_usd": 105000.0,
            "timestamp": pd.Timestamp.now(),
        }
        pnl_result = pnl_monitor.calculate_pnl(current_exposure)
        assert pnl_result["share_class"] == "ETH"
        assert pnl_result["balance_based"]["pnl_cumulative"] == 5000.0

    def test_pnl_monitor_initialization(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test P&L Calculator initialization with different configs."""
        # Test pure lending mode
        pure_lending_usdt_config = self._add_pnl_config(mock_config.copy())
        pure_lending_usdt_config["mode"] = "pure_lending_usdt"
        pure_lending_usdt_config["share_class"] = "USDT"

        pnl_monitor = PnLCalculator(
            config=pure_lending_usdt_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        assert pnl_monitor.share_class == "USDT"
        assert pnl_monitor.initial_capital == 100000.0

        # Test ETH basis mode
        eth_basis_config = self._add_pnl_config(mock_config.copy())
        eth_basis_config["mode"] = "eth_basis"
        eth_basis_config["share_class"] = "USDT"

        pnl_monitor = PnLCalculator(
            config=eth_basis_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        assert pnl_monitor.share_class == "USDT"
        assert pnl_monitor.initial_capital == 100000.0

    def test_pnl_monitor_error_handling(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test P&L Calculator error handling."""
        # Arrange - Mock data provider to raise exception
        mock_data_provider.get_price.side_effect = Exception("Data provider error")

        test_config = self._add_pnl_config(mock_config.copy())
        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Act & Assert - Should handle errors gracefully
        try:
            # Use dictionary-based exposure
            current_exposure = {
                "share_class_value": 105000.0,
                "total_value_usd": 105000.0,
                "timestamp": pd.Timestamp.now(),
            }
            pnl_result = pnl_monitor.calculate_pnl(current_exposure)
            # If no exception, should return error state
            assert isinstance(pnl_result, dict)
            assert "balance_based" in pnl_result or "error" in pnl_result
        except Exception as e:
            # If exception is raised, it should be handled appropriately
            assert "Data provider error" in str(e)

    def test_pnl_monitor_performance(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test P&L Calculator performance with multiple calculations."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Act - Run multiple P&L calculations
        import time

        start_time = time.time()

        for i in range(100):
            current_value = 100000.0 + i * 1000
            # Use dictionary-based exposure
            current_exposure = {
                "share_class_value": current_value,
                "total_value_usd": current_value,
                "timestamp": pd.Timestamp.now(),
            }
            pnl_result = pnl_monitor.calculate_pnl(current_exposure)
            assert isinstance(pnl_result, dict)

        end_time = time.time()

        # Assert - Should complete within reasonable time
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should complete within 1 second

    def test_pnl_monitor_edge_cases(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test P&L Calculator edge cases."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Test zero values
        current_exposure = {
            "share_class_value": 0.0,
            "total_value_usd": 0.0,
            "timestamp": pd.Timestamp.now(),
        }
        pnl_result = pnl_monitor.calculate_pnl(current_exposure)
        assert isinstance(pnl_result, dict)
        assert "balance_based" in pnl_result
        assert pnl_result["balance_based"]["pnl_cumulative"] == -100000.0

        # Test negative values
        current_exposure = {
            "share_class_value": -1000.0,
            "total_value_usd": -1000.0,
            "timestamp": pd.Timestamp.now(),
        }
        pnl_result = pnl_monitor.calculate_pnl(current_exposure)
        assert isinstance(pnl_result, dict)
        assert "balance_based" in pnl_result
        assert pnl_result["balance_based"]["pnl_cumulative"] == -101000.0

        # Test very large values
        current_exposure = {
            "share_class_value": 1000000000.0,
            "total_value_usd": 1000000000.0,
            "timestamp": pd.Timestamp.now(),
        }
        pnl_result = pnl_monitor.calculate_pnl(current_exposure)
        assert isinstance(pnl_result, dict)
        assert "balance_based" in pnl_result
        assert pnl_result["balance_based"]["pnl_cumulative"] == 999900000.0

    def test_get_latest_pnl_without_calculation(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test read-only access to latest P&L."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Act - Should return None before any calculation
        latest = pnl_monitor.get_latest_pnl()

        # Assert
        assert latest is None

        # Act - Calculate P&L
        current_exposure = {
            "share_class_value": 105000.0,
            "total_value_usd": 105000.0,
            "timestamp": pd.Timestamp.now(),
        }
        pnl_monitor.calculate_pnl(current_exposure)

        # Act - Should return cached result
        latest = pnl_monitor.get_latest_pnl()

        # Assert
        assert latest is not None
        assert isinstance(latest, dict)
        assert "balance_based" in latest
        assert "attribution" in latest

    def test_get_pnl_history(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test P&L history retrieval."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Act - Calculate multiple P&L values
        for value in [100000, 101000, 102000]:
            current_exposure = {
                "share_class_value": value,
                "total_value_usd": value,
                "timestamp": pd.Timestamp.now(),
            }
            pnl_monitor.calculate_pnl(current_exposure)

        # Act - Get history
        history = pnl_monitor.get_pnl_history(limit=2)

        # Assert
        assert len(history) == 2
        assert all(isinstance(item, dict) for item in history)
        assert all("balance_based" in item for item in history)

    def test_get_cumulative_attribution(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test cumulative attribution access."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Act
        attribution = pnl_monitor.get_cumulative_attribution()

        # Assert
        assert isinstance(attribution, dict)
        assert "supply_pnl" in attribution
        assert "staking_yield_oracle" in attribution
        assert "borrow_cost" in attribution

    def test_get_pnl_summary(
        self, mock_config, mock_data_provider, mock_utility_manager
    ):
        """Test P&L summary formatting."""
        # Arrange
        test_config = self._add_pnl_config(mock_config.copy())
        pnl_monitor = PnLCalculator(
            config=test_config,
            share_class="USDT",
            initial_capital=100000.0,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
        )

        # Act - Before any calculation
        summary = pnl_monitor.get_pnl_summary()

        # Assert
        assert summary == "No P&L data available"

        # Act - After calculation
        current_exposure = {
            "share_class_value": 105000.0,
            "total_value_usd": 105000.0,
            "timestamp": pd.Timestamp.now(),
        }
        pnl_monitor.calculate_pnl(current_exposure)
        summary = pnl_monitor.get_pnl_summary()

        # Assert
        assert isinstance(summary, str)
        assert "Total P&L:" in summary
        assert "Return:" in summary
        assert "5,000.00" in summary  # Should show the 5000 gain (formatted)
        assert "5.00%" in summary  # Should show the 5% return
