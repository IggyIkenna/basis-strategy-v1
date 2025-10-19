"""
Integration tests for execution flow.

Tests complete Order → ExecutionHandshake → reconciliation flow.
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation
from backend.src.basis_strategy_v1.core.models.execution import ExecutionStatus
from backend.src.basis_strategy_v1.core.models.venues import Venue

class TestExecutionFlow:
    """Test complete execution flow integration."""
    
    def test_order_to_handshake_cex(self, real_execution_manager, test_timestamp):
        """Test CEX order execution flow."""
        # Create CEX spot trade order
        order = Order(
            operation_id="test_cex_spot_001",
            venue=Venue.BINANCE,
            operation=OrderOperation.SPOT_TRADE,
            pair="BTC/USDT",
            side="BUY",
            amount=0.5,
            price=50000.0,
            order_type="limit",
            source_venue=Venue.WALLET,
            target_venue=Venue.BINANCE,
            source_token="USDT",
            target_token="BTC",
            expected_deltas={
                f"{Venue.WALLET}:BaseToken:USDT": -25000.0,
                f"{Venue.BINANCE}:BaseToken:BTC": 0.5,
            },
            execution_mode="sequential",
            strategy_intent="entry_full",
            strategy_id="btc_basis",
        )
        
        # Execute order
        handshakes = real_execution_manager.process_orders(test_timestamp, [order])
        
        # Verify execution
        assert len(handshakes) == 1
        handshake = handshakes[0]
        
        assert handshake.was_successful(), f"CEX order failed: {handshake.error_message}"
        assert handshake.operation_id == "test_cex_spot_001"
        assert handshake.status == ExecutionStatus.CONFIRMED
        assert handshake.simulated == True  # Backtest mode
        
        # Verify execution details
        assert handshake.execution_details is not None
        assert "executed_price" in handshake.execution_details
        assert "executed_amount" in handshake.execution_details
        assert handshake.execution_details["executed_amount"] == 0.5
        
        # Verify position deltas
        assert len(handshake.actual_deltas) > 0
        assert f"{Venue.BINANCE}:BaseToken:BTC" in handshake.actual_deltas
        assert handshake.actual_deltas[f"{Venue.BINANCE}:BaseToken:BTC"] == 0.5
        
        # Verify timing
        assert handshake.submitted_at is not None
        assert handshake.executed_at is not None
        assert handshake.executed_at >= handshake.submitted_at
    
    def test_order_to_handshake_defi(self, real_execution_manager, test_timestamp):
        """Test DeFi order execution flow."""
        # Create DeFi supply order
        order = Order(
            operation_id="test_defi_supply_001",
            venue=Venue.AAVE_V3,
            operation=OrderOperation.SUPPLY,
            token_in="USDT",
            token_out="aUSDT",
            amount=10000.0,
            source_venue=Venue.WALLET,
            target_venue=Venue.AAVE_V3,
            source_token="USDT",
            target_token="aUSDT",
            expected_deltas={
                f"{Venue.WALLET}:BaseToken:USDT": -10000.0,
                f"{Venue.AAVE_V3}:aToken:aUSDT": 9900.0,  # With liquidity index
            },
            execution_mode="sequential",
            strategy_intent="entry_full",
            strategy_id="pure_lending_usdt",
        )
        
        # Execute order
        handshakes = real_execution_manager.process_orders(test_timestamp, [order])
        
        # Verify execution
        assert len(handshakes) == 1
        handshake = handshakes[0]
        
        assert handshake.was_successful(), f"DeFi order failed: {handshake.error_message}"
        assert handshake.operation_id == "test_defi_supply_001"
        assert handshake.status == ExecutionStatus.CONFIRMED
        assert handshake.simulated == True  # Backtest mode
        
        # Verify execution details
        assert handshake.execution_details is not None
        assert "liquidity_index" in handshake.execution_details or "conversion_rate" in handshake.execution_details
        
        # Verify position deltas
        assert len(handshake.actual_deltas) > 0
        assert f"{Venue.AAVE_V3}:aToken:aUSDT" in handshake.actual_deltas
        assert handshake.actual_deltas[f"{Venue.AAVE_V3}:aToken:aUSDT"] > 0
        
        # Verify fees
        assert handshake.fee_amount >= 0
        assert handshake.fee_currency in ["USDT", "ETH", "WETH"]
    
    def test_failed_order_handling(self, real_execution_manager, test_timestamp):
        """Test failed order execution handling."""
        # Create order that will fail (invalid venue)
        order = Order(
            operation_id="test_failed_order_001",
            venue="INVALID_VENUE",
            operation=OrderOperation.SPOT_TRADE,
            pair="BTC/USDT",
            side="BUY",
            amount=0.5,
            source_venue=Venue.WALLET,
            target_venue="INVALID_VENUE",
            source_token="USDT",
            target_token="BTC",
            expected_deltas={},
            execution_mode="sequential",
            strategy_intent="entry_full",
            strategy_id="test",
        )
        
        # Execute order
        handshakes = real_execution_manager.process_orders(test_timestamp, [order])
        
        # Verify execution
        assert len(handshakes) == 1
        handshake = handshakes[0]
        
        assert handshake.was_failed(), f"Order should have failed but succeeded"
        assert handshake.operation_id == "test_failed_order_001"
        assert handshake.status == ExecutionStatus.FAILED
        assert handshake.error_code is not None
        assert handshake.error_message is not None
        assert "INVALID_VENUE" in handshake.error_message or "venue" in handshake.error_message.lower()
        
        # Verify no position deltas on failure
        assert len(handshake.actual_deltas) == 0
        
        # Verify timing
        assert handshake.submitted_at is not None
        assert handshake.executed_at is None  # Failed orders don't have executed_at

class TestExecutionFlowEdgeCases:
    """Test execution flow edge cases."""
    
    def test_empty_order_list(self, real_execution_manager, test_timestamp):
        """Test empty order list handling."""
        handshakes = real_execution_manager.process_orders(test_timestamp, [])
        assert len(handshakes) == 0
    
    def test_multiple_orders_sequential(self, real_execution_manager, test_timestamp):
        """Test multiple sequential orders."""
        orders = [
            Order(
                operation_id="test_sequential_001",
                venue=Venue.ETHERFI,
                operation=OrderOperation.STAKE,
                token_in="WETH",
                token_out="weETH",
                amount=1.0,
                source_venue=Venue.WALLET,
                target_venue=Venue.ETHERFI,
                source_token="WETH",
                target_token="weETH",
                expected_deltas={
                    f"{Venue.WALLET}:BaseToken:WETH": -1.0,
                    f"{Venue.ETHERFI}:LST:weETH": 0.95,
                },
                execution_mode="sequential",
                strategy_intent="entry_partial",
                strategy_id="eth_leveraged",
            ),
            Order(
                operation_id="test_sequential_002",
                venue=Venue.AAVE_V3,
                operation=OrderOperation.SUPPLY,
                token_in="weETH",
                token_out="aweETH",
                amount=0.95,
                source_venue=Venue.ETHERFI,
                target_venue=Venue.AAVE_V3,
                source_token="weETH",
                target_token="aweETH",
                expected_deltas={
                    f"{Venue.ETHERFI}:LST:weETH": -0.95,
                    f"{Venue.AAVE_V3}:aToken:aweETH": 0.95,
                },
                execution_mode="sequential",
                strategy_intent="entry_partial",
                strategy_id="eth_leveraged",
            ),
        ]
        
        handshakes = real_execution_manager.process_orders(test_timestamp, orders)
        
        # Verify both orders executed
        assert len(handshakes) == 2
        assert all(h.was_successful() for h in handshakes)
        
        # Verify order sequence
        assert handshakes[0].operation_id == "test_sequential_001"
        assert handshakes[1].operation_id == "test_sequential_002"
        
        # Verify timing sequence
        assert handshakes[0].submitted_at <= handshakes[1].submitted_at
    
    def test_mixed_success_failure(self, real_execution_manager, test_timestamp):
        """Test mixed success and failure in order list."""
        orders = [
            Order(
                operation_id="test_mixed_001",
                venue=Venue.ETHERFI,
                operation=OrderOperation.STAKE,
                token_in="WETH",
                token_out="weETH",
                amount=1.0,
                source_venue=Venue.WALLET,
                target_venue=Venue.ETHERFI,
                source_token="WETH",
                target_token="weETH",
                expected_deltas={
                    f"{Venue.WALLET}:BaseToken:WETH": -1.0,
                    f"{Venue.ETHERFI}:LST:weETH": 0.95,
                },
                execution_mode="sequential",
                strategy_intent="entry_partial",
                strategy_id="eth_leveraged",
            ),
            Order(
                operation_id="test_mixed_002",
                venue="INVALID_VENUE",
                operation=OrderOperation.SUPPLY,
                token_in="weETH",
                token_out="aweETH",
                amount=0.95,
                source_venue=Venue.ETHERFI,
                target_venue="INVALID_VENUE",
                source_token="weETH",
                target_token="aweETH",
                expected_deltas={},
                execution_mode="sequential",
                strategy_intent="entry_partial",
                strategy_id="eth_leveraged",
            ),
        ]
        
        handshakes = real_execution_manager.process_orders(test_timestamp, orders)
        
        # Verify both orders processed
        assert len(handshakes) == 2
        
        # First should succeed, second should fail
        assert handshakes[0].was_successful()
        assert handshakes[1].was_failed()
        
        # Verify error handling
        assert handshakes[1].error_code is not None
        assert handshakes[1].error_message is not None

class TestExecutionFlowReconciliation:
    """Test execution flow reconciliation."""
    
    def test_position_delta_application(self, real_execution_manager, test_timestamp):
        """Test that position deltas are applied correctly."""
        # Create order with specific deltas
        order = Order(
            operation_id="test_delta_001",
            venue=Venue.BINANCE,
            operation=OrderOperation.SPOT_TRADE,
            pair="ETH/USDT",
            side="BUY",
            amount=2.0,
            price=3000.0,
            order_type="market",
            source_venue=Venue.WALLET,
            target_venue=Venue.BINANCE,
            source_token="USDT",
            target_token="ETH",
            expected_deltas={
                f"{Venue.WALLET}:BaseToken:USDT": -6000.0,
                f"{Venue.BINANCE}:BaseToken:ETH": 2.0,
            },
            execution_mode="sequential",
            strategy_intent="entry_full",
            strategy_id="eth_basis",
        )
        
        handshakes = real_execution_manager.process_orders(test_timestamp, [order])
        
        # Verify execution
        assert len(handshakes) == 1
        handshake = handshakes[0]
        assert handshake.was_successful()
        
        # Verify deltas match expected (within tolerance)
        actual_deltas = handshake.actual_deltas
        expected_deltas = order.expected_deltas
        
        for instrument, expected_delta in expected_deltas.items():
            assert instrument in actual_deltas, f"Missing delta for {instrument}"
            actual_delta = actual_deltas[instrument]
            
            # Allow for small differences due to fees/slippage
            tolerance = abs(expected_delta) * 0.01  # 1% tolerance
            assert abs(actual_delta - expected_delta) <= tolerance, \
                f"Delta mismatch for {instrument}: expected {expected_delta}, got {actual_delta}"
